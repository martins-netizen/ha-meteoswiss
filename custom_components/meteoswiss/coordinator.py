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
from homeassistant.util import dt as dt_util

from .alerts import MeteoSwissAlertsAPI, WeatherAlert
from .cache import get_current_weather_cache, get_forecast_cache
from .const import (
    API_BASE,
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
from .forecast import IconForecastClient, IconForecastError
from .http import MAX_CSV_BYTES, OGD_HOST, async_get_bytes, async_get_json
from .openmeteo import OpenMeteoCurrentClient, OpenMeteoCurrentError
from .pollen_meteoswiss import (
    InvalidMeasuredPollenData,
    MeasuredPollenUnavailable,
    MeteoSwissPollenClient,
)
from .pollen_openmeteo import OpenMeteoPollenClient, OpenMeteoPollenError
from .pollen_openmeteo import _has_current_values as _pollen_has_current_values
from .pollen_openmeteo import _is_current_hour as _pollen_is_current_hour
from .precipitation import HOURLY_UPDATE_INTERVAL, MeteoSwissHourlyPrecipitationClient
from .precipitation_recorder import (
    HourlyPrecipitationDataMissing,
    HourlyPrecipitationMetadataError,
    HourlyPrecipitationQueueError,
    HourlyPrecipitationURLsMissing,
    MeteoSwissPrecipitationImporter,
)
from .retry import async_retry_with_backoff
from .weather_data import parse_reference_timestamp as _parse_reference_timestamp
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
            data = await async_get_json(self._session, url, host=OGD_HOST)

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
            content = (
                await async_get_bytes(
                    self._session, csv_url, host=OGD_HOST, max_bytes=MAX_CSV_BYTES
                )
            ).decode("cp1252")

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


class MeteoSwissAlertsCoordinator(DataUpdateCoordinator[list[WeatherAlert]]):
    """Class to manage fetching MeteoSwiss alerts."""

    def __init__(
        self,
        hass: HomeAssistant,
        alerts_api: MeteoSwissAlertsAPI,
        update_interval: int = 600,
        warning_labels: dict | None = None,
    ) -> None:
        """Initialize."""
        self._alerts_api = alerts_api
        self.warning_labels = warning_labels or {}
        self.last_successful_update: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_alerts",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> list[WeatherAlert]:
        """Fetch alerts from MeteoSwiss App API."""
        _LOGGER.debug("Fetching MeteoSwiss alerts")

        try:
            alerts = await self._alerts_api.get_alerts(self._alerts_api.postal_code)
        except (aiohttp.ClientError, TimeoutError, ValueError, UnicodeError):
            raise UpdateFailed("Weather warnings could not be updated") from None

        self.last_successful_update = dt_util.utcnow()

        _LOGGER.debug("Successfully fetched %d MeteoSwiss alerts", len(alerts))

        return alerts

    async def async_close(self) -> None:
        """Close alerts API session."""
        await self._alerts_api.close()


class MeteoSwissPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Schedule measured pollen and translate source failures for HA."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str = "PBE",
        update_interval: int = 3600,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.client = MeteoSwissPollenClient(station_id, session=session)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_pollen_meteoswiss",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Preserve HA source failure versus missing-value semantics."""
        try:
            return await self.client.async_get_data()
        except MeasuredPollenUnavailable:
            raise UpdateFailed("Measured pollen source unavailable") from None
        except InvalidMeasuredPollenData:
            raise UpdateFailed("No valid measured pollen values") from None


class OpenMeteoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Schedule modelled current observations and preserve HA acceptance state."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        update_interval: int,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self._session = session
        self.client = OpenMeteoCurrentClient(latitude, longitude, session)
        self.weather_code = None

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
            name=f"{DOMAIN}_openmeteo",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Commit only valid, current data; HA logs failure/recovery transitions."""
        if self._circuit_open_until and datetime.now(UTC) < self._circuit_open_until:
            raise UpdateFailed("Circuit breaker open — API temporarily unavailable")
        try:
            cache = get_current_weather_cache()
            cache_key = f"openmeteo:v2:{self.latitude},{self.longitude}"
            cached = cache.get(cache_key)
            data = cached if cached is not None else await self.client.async_get_data()
            if not isinstance(data, dict):
                raise TypeError("Invalid current weather data")
            validate_observation_time(data)
            self._consecutive_failures = 0
            self._circuit_open_until = None
            self.weather_code = data.get("weather_code")
            # Reusing a cache hit must not extend its original TTL.
            if cached is None:
                cache.set(cache_key, data)
            return data
        except (
            OpenMeteoCurrentError,
            aiohttp.ClientError,
            TimeoutError,
            ValueError,
            TypeError,
            UnicodeError,
            RuntimeError,
        ):
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = datetime.now(UTC) + timedelta(minutes=5)
            # Raw HTTP causes may contain coordinates, even in HA's debug log.
            raise UpdateFailed("Failed to fetch Open-Meteo current weather") from None

    async def async_close(self) -> None:
        """The borrowed session is owned and closed by Home Assistant."""


class MeteoSwissForecastCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Schedule ICON forecasts and retain HA cache/availability lifecycle."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        post_code: str | None = None,
        update_interval: int = 3600,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self._station_id = station_id.lower() if station_id else None
        self._latitude = latitude
        self._longitude = longitude
        self._post_code = post_code
        self._session = session
        self.client = IconForecastClient(latitude, longitude, session)

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until: datetime | None = None

        if latitude is None or longitude is None:
            _LOGGER.warning(
                "No coordinates provided for Open-Meteo forecast. "
                "Forecast will not be available."
            )

        super().__init__(
            hass,
            _LOGGER,
            name="meteoswiss_forecast",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch forecast data from Open-Meteo API with caching."""
        # Circuit breaker check
        if self._circuit_open_until and datetime.now(UTC) < self._circuit_open_until:
            raise UpdateFailed("Circuit breaker open — API temporarily unavailable")

        _LOGGER.debug("Fetching forecast from Open-Meteo API")

        # Get cache
        cache = get_forecast_cache()
        cache_key = f"forecast:v3:icon-seamless:{self._latitude},{self._longitude}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            _LOGGER.debug("Using cached forecast data")
            self._consecutive_failures = 0
            self._circuit_open_until = None
            return cached_data

        try:
            data = await self.client.async_get_data()

            # Cache the result
            cache.set(cache_key, data)

            # Circuit breaker: reset on success
            self._consecutive_failures = 0
            self._circuit_open_until = None

            _LOGGER.debug("Successfully updated forecast from Open-Meteo")
            return data
        except (
            IconForecastError,
            aiohttp.ClientError,
            TimeoutError,
            TypeError,
            ValueError,
            UpdateFailed,
        ):
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = datetime.now(UTC) + timedelta(minutes=5)
            # HA logs availability transitions. Suppress raw HTTP exception chains,
            # including coordinate URLs, even when coordinator debug logs are on.
            raise UpdateFailed("Failed to fetch Open-Meteo forecast") from None

    @property
    def data_source(self) -> str:
        """Return which API was used to fetch data."""
        return "open-meteo"

    async def async_close(self) -> None:
        """Close is handled centrally by the integration setup."""


class OpenMeteoPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Schedule modelled pollen/AQ and retain independent optional UV status."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        update_interval: int = 1800,  # 30 minutes default
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self._session = session
        self.client = OpenMeteoPollenClient(latitude, longitude, session)
        self._uv_last_update_success: bool | None = None

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
            name=f"{DOMAIN}_pollen",
            update_interval=timedelta(seconds=update_interval),
        )

    def _log_uv_availability(self, available: bool) -> None:
        """Log each optional-source outage and recovery once, without URLs."""
        if self._uv_last_update_success is available:
            return
        if not available:
            _LOGGER.warning("Optional UV response unavailable")
        elif self._uv_last_update_success is False:
            _LOGGER.info("Optional UV response recovered")
        self._uv_last_update_success = available

    async def _async_update_data(self) -> dict[str, Any]:
        """Share a validated current-hour cache and log only HA transitions."""
        cache = get_current_weather_cache()
        cache_key = f"pollen:{self.latitude},{self.longitude}"
        data = cache.get(cache_key)
        if data is not None:
            if _pollen_is_current_hour(
                data.get("last_update")
            ) and _pollen_has_current_values(data):
                self._log_uv_availability(data.get("uv_available", True))
                return data
            cache.invalidate(cache_key)
        try:
            data = await self.client.async_get_data()
        except OpenMeteoPollenError:
            raise UpdateFailed("Pollen and air quality source unavailable") from None
        self._log_uv_availability(data["uv_available"])
        cache.set(cache_key, data, ttl=1800.0)
        return data


class MeteoSwissHourlyPrecipitationCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Schedule official hourly/archive imports and translate failures for HA."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        session: aiohttp.ClientSession,
        *,
        asset_periods: tuple[str, ...] = ("now",),
        update_interval: timedelta = HOURLY_UPDATE_INTERVAL,
        lookback_months: int | None = None,
    ) -> None:
        """Initialize the hourly precipitation coordinator."""
        self.station_id = station_id.lower()
        self._session = session
        self._asset_periods = asset_periods
        self._lookback_months = lookback_months
        self.client = MeteoSwissHourlyPrecipitationClient(
            station_id, session, asset_periods=asset_periods
        )
        self.importer = MeteoSwissPrecipitationImporter(
            hass,
            self.client,
            asset_periods=asset_periods,
            lookback_months=lookback_months,
        )
        self.statistic_id = self.importer.statistic_id
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_hourly_precipitation_{'_'.join(asset_periods)}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Keep each former failure category and HA availability message."""
        try:
            return await self.importer.async_import()
        except HourlyPrecipitationMetadataError:
            raise UpdateFailed("Hourly precipitation metadata unavailable") from None
        except HourlyPrecipitationURLsMissing:
            raise UpdateFailed("Could not find hourly precipitation URLs") from None
        except HourlyPrecipitationDataMissing:
            raise UpdateFailed("No valid hourly precipitation data") from None
        except HourlyPrecipitationQueueError:
            raise UpdateFailed(
                "Could not queue hourly precipitation statistics"
            ) from None
