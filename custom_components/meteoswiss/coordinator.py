"""Data update coordinator for MeteoSwiss."""

from __future__ import annotations

import csv
import io
import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_current_weather_cache
from .const import (
    API_BASE,
    DEFAULT_API_TIMEOUT,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
    SENSOR_DEW_POINT,
    SENSOR_FOEHN_INDEX,
    SENSOR_GLOBAL_RADIATION,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_SNOW_DEPTH,
    SENSOR_SUNSHINE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_GUST,
    SENSOR_WIND_SPEED,
    STAC_COLLECTION,
)
from .retry import async_retry_with_backoff
from .weather_data import validate_observation_time

_LOGGER = logging.getLogger(__name__)

# MeteoSwiss CSV parameter IDs (10-minute granularity)
# These are the column headers in the CSV files from data.geo.admin.ch
PARAM_TEMPERATURE = "tre200s0"  # Lufttemperatur 2m über Boden; Momentanwert (°C)
PARAM_HUMIDITY = "ure200s0"  # Relative Luftfeuchtigkeit 2m über Boden (%)
PARAM_WIND_SPEED = "fu3010z0"  # Windgeschwindigkeit; Zehnminutenmittel (km/h)
PARAM_WIND_DIR = "dkl010z0"  # Windrichtung; Zehnminutenmittel (°)
PARAM_PRESSURE = "pp0qffs0"  # Luftdruck reduziert auf Meeresniveau QFF (hPa)
PARAM_PRECIPITATION = "rre150z0"  # Niederschlag; Zehnminutensumme (mm)
PARAM_GUST_1S = "fu3010z1"  # Böenspitze (Sekundenböe); Maximum (km/h)
PARAM_GUST_3S = "fu3010z3"  # Böenspitze (3-Sekundenböe); Maximum (km/h)
PARAM_SUNSHINE = "sre000z0"  # Sonnenscheindauer; Zehnminutensumme (min)
PARAM_GLOBAL_RAD = "gre000z0"  # Globalstrahlung; Zehnminutenmittel (W/m²)
PARAM_SNOW_DEPTH = "htoauts0"  # Gesamtschneehöhe; Momentanwert (cm)
PARAM_DEW_POINT = "tde200s0"  # Taupunkt 2m über Boden; Momentanwert (°C)
PARAM_FOEHN_INDEX = "wcc006s0"  # Föhnindex; Momentanwert (Code)


def _parse_reference_timestamp(value: str | None) -> datetime | None:
    """Parse a MeteoSwiss reference timestamp as UTC."""
    timestamp = (value or "").strip()
    if not timestamp:
        return None

    try:
        return datetime.strptime(timestamp, "%d.%m.%Y %H:%M").replace(tzinfo=UTC)
    except ValueError:
        pass

    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class MeteoSwissDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from MeteoSwiss API."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        update_interval: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.station_id = station_id.lower()  # STAC API uses lowercase
        self._session = session

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until: datetime | None = None

        # Ensure minimum update interval
        if update_interval < MIN_UPDATE_INTERVAL:
            _LOGGER.warning(
                "Update interval %s is below minimum %s, using minimum",
                update_interval,
                MIN_UPDATE_INTERVAL,
            )
            update_interval = MIN_UPDATE_INTERVAL

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_get_station_data_url(self) -> str | None:
        """Fetch the 10-minute CSV URL for the station."""
        if self._session is None:
            raise RuntimeError("No session provided")

        try:
            url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
            _LOGGER.debug("Fetching station metadata")
            async with self._session.get(url, timeout=DEFAULT_API_TIMEOUT) as response:
                response.raise_for_status()

                data = await response.json()

                # Find the t_now.csv asset (most recent 10-min data)
                if not isinstance(data, dict) or not isinstance(
                    data.get("assets", {}), dict
                ):
                    raise TypeError("Invalid station metadata")
                assets = data.get("assets", {})
                asset_key = f"ogd-smn_{self.station_id}_t_now.csv"

                if asset_key in assets:
                    asset = assets[asset_key]
                    if (
                        not isinstance(asset, dict)
                        or not isinstance(asset.get("href"), str)
                        or not asset["href"].strip()
                    ):
                        raise ValueError("Invalid station asset")
                    csv_url = asset["href"]
                    _LOGGER.debug("Selected station measurement asset")
                    return csv_url

                # Fallback to t_recent.csv if t_now.csv not available
                asset_key = f"ogd-smn_{self.station_id}_t_recent.csv"
                if asset_key in assets:
                    asset = assets[asset_key]
                    if (
                        not isinstance(asset, dict)
                        or not isinstance(asset.get("href"), str)
                        or not asset["href"].strip()
                    ):
                        raise ValueError("Invalid station asset")
                    csv_url = asset["href"]
                    _LOGGER.debug("Selected station measurement asset")
                    return csv_url

                _LOGGER.debug("Station metadata has no current or recent asset")
                return None

        except (aiohttp.ClientError, TimeoutError):
            raise
        except (ValueError, TypeError, csv.Error):
            _LOGGER.debug("Station source decoding failed")
            return None

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_download_and_parse_csv(
        self, csv_url: str
    ) -> dict[str, Any] | None:
        """Download CSV and parse the latest values."""
        if self._session is None:
            raise RuntimeError("No session provided")

        try:
            _LOGGER.debug("Fetching station measurements")
            async with self._session.get(
                csv_url, timeout=DEFAULT_API_TIMEOUT
            ) as response:
                response.raise_for_status()

                content = await response.text(encoding="cp1252")

            _LOGGER.debug("CSV content length: %d chars", len(content))

            # Select the latest complete observation from all published rows;
            # sparse optional values can still use the bounded recent history.
            all_rows = list(csv.DictReader(io.StringIO(content), delimiter=";"))

            if not all_rows:
                _LOGGER.debug("CSV has no data rows")
                return None

            if any(
                (row.get("station_abbr") or "").strip().lower() != self.station_id
                for row in all_rows
            ):
                raise UpdateFailed("CSV contains a different or missing station")

            # The provider may publish a final partial row (often rain=0
            # with all instantaneous observations still blank).
            # Select the newest *measured* row as a whole: never mix current
            # and older individual values to conceal a real missing field.
            measured_parameters = (
                PARAM_TEMPERATURE,
                PARAM_HUMIDITY,
                PARAM_WIND_SPEED,
                PARAM_WIND_DIR,
                PARAM_PRESSURE,
                PARAM_PRECIPITATION,
                PARAM_GUST_1S,
                PARAM_GUST_3S,
                PARAM_SUNSHINE,
                PARAM_GLOBAL_RAD,
                PARAM_SNOW_DEPTH,
                PARAM_DEW_POINT,
                PARAM_FOEHN_INDEX,
            )
            instantaneous_parameters = (
                PARAM_TEMPERATURE,
                PARAM_HUMIDITY,
                PARAM_WIND_SPEED,
                PARAM_WIND_DIR,
                PARAM_PRESSURE,
                PARAM_GUST_1S,
                PARAM_GUST_3S,
                PARAM_GLOBAL_RAD,
                PARAM_DEW_POINT,
            )
            # Rain-only stations must still work. Prefer instantaneous
            # columns only if this file actually reports any of them.
            anchor_parameters = (
                instantaneous_parameters
                if any(
                    (row.get(key) or "").strip()
                    for row in all_rows
                    for key in instantaneous_parameters
                )
                else measured_parameters
            )
            newest_first = list(reversed(all_rows))
            observation_index = next(
                (
                    index
                    for index, row in enumerate(newest_first)
                    if any((row.get(key) or "").strip() for key in anchor_parameters)
                ),
                None,
            )
            if observation_index is None:
                raise UpdateFailed("CSV contains no measured observations")
            recent_rows = newest_first[observation_index : observation_index + 5]
            result = self._parse_csv_row_with_fallback(recent_rows)
            measured_keys = (
                SENSOR_TEMPERATURE,
                SENSOR_HUMIDITY,
                SENSOR_WIND_SPEED,
                SENSOR_WIND_DIRECTION,
                SENSOR_PRESSURE,
                SENSOR_PRECIPITATION,
                SENSOR_WIND_GUST,
                SENSOR_SUNSHINE,
                SENSOR_GLOBAL_RADIATION,
                SENSOR_SNOW_DEPTH,
                SENSOR_DEW_POINT,
                SENSOR_FOEHN_INDEX,
            )
            if not any(result.get(key) is not None for key in measured_keys):
                raise UpdateFailed("CSV contains no valid measured observations")
            result["source_status"] = (
                "partial_update" if observation_index else "current"
            )
            result["pending_rows"] = observation_index
            _LOGGER.debug("Decoded %d station CSV rows", len(all_rows))
            return result

        except (UpdateFailed, aiohttp.ClientError, TimeoutError):
            raise
        except (ValueError, TypeError, csv.Error):
            _LOGGER.debug("Station source decoding failed")
            return None

    def _parse_csv_row_with_fallback(
        self, row_dicts: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Parse CSV rows into normalized data, using fallback for empty values."""
        if not row_dicts:
            return {}
        # Parse newest row first, then fill missing values from older rows
        result = self._parse_csv_row(row_dicts[0])

        # Parameters that might be empty in newest row but available in older rows
        fallback_params = [
            PARAM_FOEHN_INDEX,
            PARAM_SNOW_DEPTH,
        ]
        param_to_sensor = {
            PARAM_FOEHN_INDEX: SENSOR_FOEHN_INDEX,
            PARAM_SNOW_DEPTH: SENSOR_SNOW_DEPTH,
        }

        for param_key in fallback_params:
            sensor_key = param_to_sensor[param_key]
            if result.get(sensor_key) is None:
                for older_row in row_dicts[1:]:
                    val = (older_row.get(param_key) or "").strip()
                    if val:
                        try:
                            number = float(val)
                            if not math.isfinite(number):
                                continue
                            if sensor_key == SENSOR_FOEHN_INDEX:
                                result[sensor_key] = int(float(val))
                            else:
                                result[sensor_key] = float(val)
                            _LOGGER.debug(
                                "Optional measurement fallback used for %s", sensor_key
                            )
                            break
                        except (ValueError, TypeError, OverflowError):
                            pass

        return result

    def _parse_csv_row(self, row: dict[str, str]) -> dict[str, Any]:
        """Parse a CSV row into normalized data."""
        if not isinstance(row, dict) or any(
            value is not None and not isinstance(value, str) for value in row.values()
        ):
            _LOGGER.debug("Invalid station CSV row shape")
            return {}
        result = {
            SENSOR_TEMPERATURE: None,
            SENSOR_HUMIDITY: None,
            SENSOR_WIND_SPEED: None,
            SENSOR_WIND_DIRECTION: None,
            SENSOR_PRECIPITATION: None,
            "precipitation_interval_seconds": 600,
            SENSOR_PRESSURE: None,
            SENSOR_WIND_GUST: None,
            SENSOR_DEW_POINT: None,
            SENSOR_SUNSHINE: None,
            SENSOR_GLOBAL_RADIATION: None,
            SENSOR_SNOW_DEPTH: None,
            SENSOR_FOEHN_INDEX: None,
            "last_update": None,
        }

        # Parse temperature (in °C)
        temp_value = row.get(PARAM_TEMPERATURE)
        if temp_value and temp_value.strip():
            try:
                result[SENSOR_TEMPERATURE] = float(temp_value)
                _LOGGER.debug("Parsed temperature")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse temperature")

        # Parse humidity (in %)
        hum_value = row.get(PARAM_HUMIDITY)
        if hum_value and hum_value.strip():
            try:
                result[SENSOR_HUMIDITY] = float(hum_value)
                _LOGGER.debug("Parsed humidity")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse humidity")

        # Parse wind speed (in km/h)
        wind_value = row.get(PARAM_WIND_SPEED)
        if wind_value and wind_value.strip():
            try:
                result[SENSOR_WIND_SPEED] = float(wind_value)
                _LOGGER.debug("Parsed wind speed")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse wind speed")

        # Parse wind direction (in degrees)
        dir_value = row.get(PARAM_WIND_DIR)
        if dir_value and dir_value.strip():
            try:
                result[SENSOR_WIND_DIRECTION] = int(float(dir_value))
                _LOGGER.debug("Parsed wind direction")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse wind direction")

        # Parse pressure (in hPa)
        press_value = row.get(PARAM_PRESSURE)
        if press_value and press_value.strip():
            try:
                result[SENSOR_PRESSURE] = float(press_value)
                _LOGGER.debug("Parsed pressure")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse pressure")

        # Parse precipitation (in mm)
        precip_value = row.get(PARAM_PRECIPITATION)
        if precip_value and precip_value.strip():
            try:
                result[SENSOR_PRECIPITATION] = float(precip_value)
                _LOGGER.debug("Parsed precipitation")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse precipitation")

        # Parse wind gust (1-second, in km/h)
        gust_value = row.get(PARAM_GUST_1S)
        if gust_value and gust_value.strip():
            try:
                result[SENSOR_WIND_GUST] = float(gust_value)
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse wind gust")

        # Parse sunshine duration (10-min sum, in minutes)
        sun_value = row.get(PARAM_SUNSHINE)
        if sun_value and sun_value.strip():
            try:
                result[SENSOR_SUNSHINE] = float(sun_value)
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse sunshine")

        # Parse global radiation (W/m²)
        rad_value = row.get(PARAM_GLOBAL_RAD)
        if rad_value and rad_value.strip():
            try:
                result[SENSOR_GLOBAL_RADIATION] = float(rad_value)
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse global radiation")

        # Parse snow depth (cm)
        snow_value = row.get(PARAM_SNOW_DEPTH)
        if snow_value and snow_value.strip():
            try:
                result[SENSOR_SNOW_DEPTH] = float(snow_value)
                _LOGGER.debug("Parsed snow depth")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse snow depth")

        # Parse foehn index (code)
        foehn_value = row.get(PARAM_FOEHN_INDEX)
        if foehn_value and foehn_value.strip():
            try:
                result[SENSOR_FOEHN_INDEX] = int(float(foehn_value))
                _LOGGER.debug("Parsed foehn index")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse foehn index")

        # Parse soil temperatures — removed (most stations don't measure)
        # (parsing block removed)

        # Dew point: use measured value if available, otherwise calculate via Magnus formula
        dew_measured = row.get(PARAM_DEW_POINT)
        if dew_measured and dew_measured.strip():
            try:
                result[SENSOR_DEW_POINT] = round(float(dew_measured), 1)
                _LOGGER.debug("Using measured dew point")
            except (ValueError, TypeError, OverflowError):
                _LOGGER.debug("Could not parse measured dew point")

        # Non-finite values must not leak into HA or poison derived values.
        for key, value in result.items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                result[key] = None

        # Fallback: calculate dew point from temperature and humidity using Magnus formula
        if result[SENSOR_DEW_POINT] is None:
            temp = result.get(SENSOR_TEMPERATURE)
            hum = result.get(SENSOR_HUMIDITY)
            if temp is not None and hum is not None:
                try:
                    # Magnus formula
                    a = 17.625
                    b = 243.04
                    alpha = ((a * temp) / (b + temp)) + math.log(max(hum, 1.0) / 100.0)
                    dew = (b * alpha) / (a - alpha)
                    if math.isfinite(dew):
                        result[SENSOR_DEW_POINT] = round(dew, 1)
                    _LOGGER.debug("Calculated dew point (Magnus)")
                except (ValueError, ZeroDivisionError, OverflowError):
                    _LOGGER.debug("Dew point cannot be derived from this measurement")

        # Preserve measurement time. A malformed timestamp must never
        # be replaced with "now", which would hide stale source data.
        reference = _parse_reference_timestamp(row.get("reference_timestamp"))
        result["last_update"] = reference.isoformat() if reference else None

        # Log final result
        _LOGGER.debug("Station measurements decoded")

        return result

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API with caching."""
        # Circuit breaker check
        if self._circuit_open_until and datetime.now(UTC) < self._circuit_open_until:
            raise UpdateFailed("Circuit breaker open — API temporarily unavailable")

        try:
            _LOGGER.debug("Fetching data for station observations")

            # Get cache
            cache = get_current_weather_cache()
            cache_key = f"station:{self.station_id}"

            # Try cache first
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                _LOGGER.debug("Using cached data for station observations")
                validate_observation_time(cached_data)
                self._consecutive_failures = 0
                self._circuit_open_until = None
                return cached_data

            _LOGGER.debug("Cache miss, fetching fresh data for station observations")

            # Get CSV URL
            csv_url = await self._async_get_station_data_url()

            if csv_url is None:
                _LOGGER.debug("Failed to find station data URL")
                raise UpdateFailed("Could not find station data URL")

            _LOGGER.debug("Fetching station measurements")

            # Download and parse CSV
            parsed_data = await self._async_download_and_parse_csv(csv_url)

            if parsed_data is None:
                _LOGGER.debug("Parsed data is None!")
                raise UpdateFailed("Failed to parse station data: parsed_data is None")

            if not parsed_data:
                _LOGGER.debug("Parsed data is empty!")
                raise UpdateFailed("Failed to parse station data: parsed_data is empty")

            _LOGGER.debug("Station measurements decoded")

            validate_observation_time(parsed_data)
            self._last_update = datetime.now(UTC)

            # Circuit breaker: reset on success
            self._consecutive_failures = 0
            self._circuit_open_until = None

            # Cache result
            cache.set(cache_key, parsed_data)
            _LOGGER.debug("Cached data for station observations (TTL: 600s)")

            return parsed_data

        except (UpdateFailed, aiohttp.ClientError, TimeoutError, ValueError) as err:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = datetime.now(UTC) + timedelta(minutes=5)
                _LOGGER.debug(
                    "Station source circuit paused after %d failures",
                    self._consecutive_failures,
                )
            if isinstance(err, UpdateFailed):
                raise err from None
            raise UpdateFailed("Weather data source unavailable") from None

    async def async_close(self) -> None:
        """Close is handled centrally by the integration setup."""
        # Home Assistant owns and closes the borrowed shared session.
