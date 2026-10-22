"""Measured pollen client using MeteoSwiss measured pollen data (ogd-pollen).

Fetches measured pollen concentrations from the stations' hourly CSV assets
in the public MeteoSwiss ogd-pollen collection on data.geo.admin.ch.

The current hourly CSV schema supplies birch, alder, hazel, beech, ash, grasses
and oak. Modelled mugwort/ragweed entities belong to the separate Open-Meteo
source; this measured client must not invent unsupported hourly columns.

Data source: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .http import MAX_CSV_BYTES, OGD_HOST, async_get_bytes
from .retry import async_retry_with_backoff
from .weather_data import parse_reference_timestamp

# STAC API for pollen collection
POLLEN_STAC_COLLECTION_URL = (
    "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen"
)
POLLEN_DATA_BASE_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen"

# Hourly measurement end times, 20-minute publication and up to two-hour asset
# caching need their own policy, independent of the 10-minute weather feed.
# Four hours is our conservative acceptance window, not a provider SLA.
MAX_MEASUREMENT_AGE = timedelta(hours=4)
MAX_MEASUREMENT_FUTURE_SKEW = timedelta(minutes=10)

# Authoritative hourly column mapping, including oak (kaquerh0).
# See ogd-pollen_meta_parameters.csv in the same public OGD collection.
POLLEN_CSV_COLUMNS: dict[str, str] = {
    "birch": "kabetuh0",
    "alder": "kaalnuh0",
    "hazel": "kacoryh0",
    "beech": "kafaguh0",
    "ash": "kafraxh0",
    "grass": "khpoach0",
    "oak": "kaquerh0",
}
POLLEN_TRACKED = list(POLLEN_CSV_COLUMNS)


def _count(raw: str | None) -> int | None:
    """Zero is a measurement; blank, invalid and negative counts are missing."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


class MeasuredPollenUnavailable(Exception):
    """The measured-pollen transport could not supply a valid response."""


class InvalidMeasuredPollenData(Exception):
    """The response has no usable measurement for the requested station/time."""


class MeteoSwissPollenClient:
    """Fetch and validate measured pollen without an HA coordinator/runtime."""

    def __init__(
        self,
        station_id: str = "PBE",
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.station_id = station_id.lower()
        self._session = session

    async def async_get_data(self) -> dict[str, Any]:
        """Return validated values or a payload-free source exception."""
        try:
            content = await self._async_fetch_csv()
        except (aiohttp.ClientError, TimeoutError, ValueError):
            raise MeasuredPollenUnavailable from None
        data = self.parse_csv(content)
        if not data:
            raise InvalidMeasuredPollenData
        return data

    @async_retry_with_backoff(max_attempts=3)
    async def _async_fetch_csv(self) -> str:
        """Retry only transient transport failures, before parsing the payload."""
        if self._session is None:
            raise RuntimeError("No aiohttp session provided to MeteoSwissPollenClient")
        url = f"{POLLEN_DATA_BASE_URL}/{self.station_id}/ogd-pollen_{self.station_id}_h_now.csv"
        return (
            await async_get_bytes(
                self._session, url, host=OGD_HOST, max_bytes=MAX_CSV_BYTES
            )
        ).decode("cp1252")

    def parse_csv(self, csv_text: str) -> dict[str, Any]:
        """Validate station/time and retain the existing output/history format."""
        rows = list(csv.DictReader(io.StringIO(csv_text), delimiter=";"))
        if not rows:
            return {}
        latest = rows[-1]
        timestamp = (latest.get("reference_timestamp") or "").strip()
        station = (latest.get("station_abbr") or "").strip().lower()
        measurement_time = parse_reference_timestamp(timestamp)
        if station != self.station_id or measurement_time is None:
            return {}
        age = datetime.now(UTC) - measurement_time
        if age > MAX_MEASUREMENT_AGE or age < -MAX_MEASUREMENT_FUTURE_SKEW:
            return {}
        result: dict[str, Any] = {
            "station_id": self.station_id.upper(),
            "last_update": timestamp,
            "source": "MeteoSwiss ogd-pollen",
        }
        for pollen_key, column in POLLEN_CSV_COLUMNS.items():
            result[pollen_key] = {
                "current": _count(latest.get(column)),
                "unit": "No/m³",
                "source": "MeteoSwiss measured",
                "history_24h": [_count(row.get(column)) for row in rows[-24:]],
            }
        return (
            result
            if any(result[key]["current"] is not None for key in POLLEN_TRACKED)
            else {}
        )
