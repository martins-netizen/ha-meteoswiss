"""Shared, bounded station catalogue and public geographic metadata."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import math
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

import aiohttp

from .cache import get_stations_cache
from .const import DEFAULT_API_TIMEOUT, STATIONS_METADATA_URL
from .http import MAX_CATALOGUE_BYTES, OGD_HOST, async_get_bytes
from .retry import async_retry_with_backoff
from .weather_data import weather_number

_LOGGER = logging.getLogger(__name__)
CATALOGUE_TTL = 86400.0
CATALOGUE_RETRY_DELAY = 300.0


@dataclass(frozen=True)
class WeatherStation:
    """Public station metadata; incomplete coordinates do not invent a point."""

    station_id: str
    name: str
    latitude: float | None
    longitude: float | None
    altitude: float | None = None
    canton: str | None = None
    start_date: str | None = None

    @property
    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_geojson_feature(self) -> dict:
        return {
            "type": "Feature",
            "properties": {
                key: value
                for key, value in self.to_dict().items()
                if key not in ("latitude", "longitude")
            },
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            }
            if self.has_coordinates
            else None,
        }


def _parse_station_catalogue(content: bytes) -> dict[str, WeatherStation]:
    """Read named provider columns, documented cp1252 or explicit UTF-8 BOM."""
    if len(content) > MAX_CATALOGUE_BYTES:
        raise ValueError("Station catalogue exceeds size limit")
    encoding = "utf-8-sig" if content.startswith(b"\xef\xbb\xbf") else "cp1252"
    rows = csv.reader(io.StringIO(content.decode(encoding)), delimiter=";", strict=True)
    headers = [name.strip().lower() for name in next(rows, [])]
    aliases = {
        "id": ("station_abbr", "station", "id"),
        "name": ("station_name", "name"),
        "canton": ("station_canton", "canton"),
        "latitude": ("station_coordinates_wgs84_lat", "lat", "latitude"),
        "longitude": ("station_coordinates_wgs84_lon", "lon", "longitude"),
        "altitude": ("station_height_masl", "altitude"),
        "start_date": ("station_data_since", "start_date"),
    }
    columns = {
        key: next((name for name in names if name in headers), None)
        for key, names in aliases.items()
    }
    if (
        not columns["id"]
        or not columns["name"]
        or len(set(filter(None, headers))) != len(list(filter(None, headers)))
    ):
        raise ValueError("Invalid station catalogue columns")
    stations = {}
    for parts in rows:
        if not parts or len(parts) > len(headers):
            continue
        values = dict(
            zip(headers, parts + [""] * (len(headers) - len(parts)), strict=True)
        )
        fields = {
            key: values.get(column, "").strip() for key, column in columns.items()
        }
        if not fields["id"] or not fields["name"]:
            continue
        latitude = weather_number(fields["latitude"], -90, 90)
        longitude = weather_number(fields["longitude"], -180, 180)
        if (
            fields["latitude"]
            and latitude is None
            or fields["longitude"]
            and longitude is None
        ):
            continue
        if latitude is None or longitude is None:
            latitude = longitude = None
        station = WeatherStation(
            station_id=fields["id"].upper(),
            name=fields["name"],
            latitude=latitude,
            longitude=longitude,
            altitude=weather_number(fields["altitude"]),
            canton=fields["canton"] or None,
            start_date=fields["start_date"] or None,
        )
        key = station.station_id.lower()
        if key in stations and stations[key] != station:
            raise ValueError("Conflicting duplicate station identifier")
        stations[key] = station
    if not stations:
        raise ValueError("Station catalogue contains no valid stations")
    return stations


def parse_station_catalogue(content: bytes) -> dict[str, WeatherStation]:
    """Invalid CSV is a payload failure, never a transient transport retry."""
    try:
        return _parse_station_catalogue(content)
    except csv.Error:
        raise ValueError("Malformed station catalogue CSV") from None


class MeteoSwissStationsMap:
    """Entry-independent catalogue with explicit stale/unavailable status."""

    def __init__(self) -> None:
        self._stations: dict[str, WeatherStation] = {}
        self._lock = asyncio.Lock()
        self._expires_at = 0.0
        self._retry_at = 0.0
        self.last_update_success: bool | None = None
        self.last_successful_update: str | None = None
        self.last_exception: str | None = None

    @property
    def data_status(self) -> str:
        if not self._stations:
            return "unavailable"
        return (
            "current"
            if self.last_update_success and time.monotonic() < self._expires_at
            else "stale"
        )

    def get_status(self) -> dict:
        return {
            "data_status": self.data_status,
            "station_count": len(self._stations),
            "last_update_success": self.last_update_success,
            "last_successful_update": self.last_successful_update,
            "last_exception": self.last_exception,
        }

    @async_retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    async def _async_download(self, session: aiohttp.ClientSession) -> bytes:
        return await async_get_bytes(
            session, STATIONS_METADATA_URL, host=OGD_HOST, max_bytes=MAX_CATALOGUE_BYTES
        )

    async def _async_content(self, session: aiohttp.ClientSession | None) -> bytes:
        async with asyncio.timeout(DEFAULT_API_TIMEOUT.total):
            if session is not None:
                return await self._async_download(session)
            async with aiohttp.ClientSession() as owned_session:
                return await self._async_download(owned_session)

    def _accept(self, snapshot: dict) -> dict[str, WeatherStation]:
        if self.last_update_success is False:
            _LOGGER.info("Weather station catalogue recovered")
        self._stations = dict(snapshot["stations"])
        self.last_successful_update = snapshot["last_successful_update"]
        self._expires_at = snapshot["expires_at"]
        self.last_update_success = True
        self.last_exception = None
        self._retry_at = 0.0
        return dict(self._stations)

    async def load_stations(
        self, session: aiohttp.ClientSession | None = None, *, retry: bool = False
    ) -> dict[str, WeatherStation]:
        """Refresh after 24 hours; preserve/label last good metadata on failure."""
        async with self._lock:
            cache = get_stations_cache()
            key = cache.make_key("station-catalogue:v2", STATIONS_METADATA_URL)
            cached = cache.get(key)
            if cached is not None and time.monotonic() < cached["expires_at"]:
                return self._accept(cached)
            if not retry and time.monotonic() < self._retry_at:
                return dict(self._stations)
            try:
                stations = parse_station_catalogue(await self._async_content(session))
            except (
                aiohttp.ClientError,
                TimeoutError,
                UnicodeError,
                ValueError,
                csv.Error,
            ) as err:
                if self.last_update_success is not False:
                    _LOGGER.warning("Weather station catalogue unavailable")
                self.last_update_success = False
                self.last_exception = type(err).__name__
                self._retry_at = time.monotonic() + CATALOGUE_RETRY_DELAY
                return dict(self._stations)
            snapshot = {
                "stations": stations,
                "last_successful_update": datetime.now(UTC).isoformat(),
                "expires_at": time.monotonic() + CATALOGUE_TTL,
            }
            cache.set(key, snapshot, ttl=CATALOGUE_TTL)
            return self._accept(snapshot)

    def get_station(self, station_id: str) -> WeatherStation | None:
        return self._stations.get(station_id.lower())

    def get_all_stations(self) -> list[WeatherStation]:
        return sorted(self._stations.values(), key=lambda station: station.name)

    def get_stations_by_canton(self, canton: str) -> list[WeatherStation]:
        return [
            station
            for station in self.get_all_stations()
            if station.canton and station.canton.casefold() == canton.casefold()
        ]

    def get_nearby_stations(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 50.0,
        limit: int = 10,
    ) -> list[tuple[WeatherStation, float]]:
        latitude = weather_number(latitude, -90, 90)
        longitude = weather_number(longitude, -180, 180)
        max_distance_km = weather_number(max_distance_km, 0)
        if (
            latitude is None
            or longitude is None
            or max_distance_km is None
            or isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 0
        ):
            raise ValueError("Invalid nearby station search bounds")
        found = []
        for station in self.get_all_stations():
            if not station.has_coordinates:
                continue
            distance = self._calculate_distance(
                latitude, longitude, station.latitude, station.longitude
            )
            if distance <= max_distance_km:
                found.append((station, distance))
        return sorted(found, key=lambda item: item[1])[:limit]

    @staticmethod
    def _calculate_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
        a = (
            math.sin((lat2 - lat1) / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        )
        return 6371 * 2 * math.asin(math.sqrt(max(0.0, min(1.0, a))))

    def to_geojson(self) -> dict:
        return {
            "type": "FeatureCollection",
            "features": [
                station.to_geojson_feature() for station in self.get_all_stations()
            ],
        }

    def to_picture_elements_config(
        self, *, image: str | None = None, entity_id: str | None = None
    ) -> dict | None:
        """Generate a north-up map only with an explicitly supplied image/entity."""
        if not image or not entity_id:
            return None
        elements = []
        for station in self.get_all_stations():
            if not station.has_coordinates:
                continue
            x = max(0, min(100, (station.longitude - 5.9) / (10.5 - 5.9) * 100))
            y = max(0, min(100, (47.8 - station.latitude) / (47.8 - 45.8) * 100))
            elements.append(
                {
                    "type": "state-label",
                    "entity": entity_id,
                    "style": {
                        "top": f"{y}%",
                        "left": f"{x}%",
                        "transform": "translate(-50%, -50%)",
                    },
                    "title": f"{station.name} ({station.station_id})",
                }
            )
        return {"type": "picture-elements", "image": image, "elements": elements[:50]}


_stations_map: MeteoSwissStationsMap | None = None


async def get_stations_map(
    session: aiohttp.ClientSession | None = None,
    *,
    load: bool = True,
    retry: bool = False,
) -> MeteoSwissStationsMap:
    global _stations_map
    if _stations_map is None:
        _stations_map = MeteoSwissStationsMap()
    if load:
        await _stations_map.load_stations(session=session, retry=retry)
    return _stations_map
