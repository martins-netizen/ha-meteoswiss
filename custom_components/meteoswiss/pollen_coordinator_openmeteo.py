"""Pollen data coordinator using Open-Meteo Air Quality API."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_current_weather_cache
from .const import DOMAIN, MIN_UPDATE_INTERVAL
from .http import AIR_QUALITY_HOST, FORECAST_HOST, async_get_json
from .retry import async_retry_with_backoff
from .weather_data import forecast_datetime

_LOGGER = logging.getLogger(__name__)

# Open-Meteo Air Quality API
OPENMETEO_AQ_BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Pollen types
POLLEN_ALDER = "alder_pollen"
POLLEN_BIRCH = "birch_pollen"
POLLEN_GRASS = "grass_pollen"
POLLEN_MUGWORT = "mugwort_pollen"
POLLEN_RAGWEED = "ragweed_pollen"

# Air quality parameters (Open-Meteo AQ API)
AQ_PM25 = "pm2_5"
AQ_PM10 = "pm10"
AQ_NO2 = "nitrogen_dioxide"
AQ_O3 = "ozone"

# Open-Meteo Forecast API for UV index
OPENMETEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Pollen types list
POLLEN_TYPES = [
    POLLEN_ALDER,
    POLLEN_BIRCH,
    POLLEN_GRASS,
    POLLEN_MUGWORT,
    POLLEN_RAGWEED,
]

# Air quality parameter list
AQ_PARAMETERS = [
    AQ_PM25,
    AQ_PM10,
    AQ_NO2,
    AQ_O3,
]


def _number(value: Any) -> float | None:
    """Only finite non-negative concentrations/UV values are observations."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _has_current_values(data: dict[str, Any]) -> bool:
    return any(
        isinstance(data.get(key), dict)
        and _number(data[key].get("current")) is not None
        for key in POLLEN_TYPES
    ) or any(
        _number(data.get(key)) is not None
        for key in ("pm25", "pm10", "nitrogen_dioxide", "ozone")
    )


def _is_current_hour(value: Any) -> bool:
    timestamp = forecast_datetime(value)
    now = datetime.now(timezone.utc)
    return timestamp is not None and timestamp <= now < timestamp + timedelta(hours=1)


class OpenMeteoPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching pollen data from Open-Meteo Air Quality API."""

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

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_fetch_data(self) -> dict[str, Any]:
        """Fetch AQ/pollen; UV is optional and cannot rescue an invalid feed."""
        if self._session is None:
            raise RuntimeError(
                "No aiohttp session provided to OpenMeteoPollenCoordinator"
            )
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "hourly": ",".join(POLLEN_TYPES + AQ_PARAMETERS),
            "forecast_days": 5,
            "timezone": "Europe/Zurich",
            "timeformat": "unixtime",
        }
        payload = await async_get_json(
            self._session, OPENMETEO_AQ_BASE_URL, params=params, host=AIR_QUALITY_HOST
        )
        result = self._parse_response(payload)
        if not result:
            raise ValueError("No valid current pollen or air quality values")
        result["uv_index"], result["uv_available"] = await self._async_fetch_uv()
        return result

    async def _async_fetch_uv(self) -> tuple[float | None, bool]:
        """Separate a failed UV source from a valid response with no value."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": "uv_index",
            "timezone": "Europe/Zurich",
        }
        try:
            payload = await async_get_json(
                self._session, OPENMETEO_FORECAST_URL, params=params, host=FORECAST_HOST
            )
        except (aiohttp.ClientError, TimeoutError, ValueError):
            # The source state is published atomically with the AQ result.
            # Do not expose coordinate-bearing URLs or raw exception chains.
            return None, False
        if not isinstance(payload, dict) or not isinstance(
            payload.get("current"), dict
        ):
            return None, False
        return _number(payload["current"].get("uv_index")), True

    def _log_uv_availability(self, available: bool) -> None:
        """Log each optional-source outage and recovery once, without URLs."""
        if self._uv_last_update_success is available:
            return
        if not available:
            _LOGGER.warning("Optional UV response unavailable")
        elif self._uv_last_update_success is False:
            _LOGGER.info("Optional UV response recovered")
        self._uv_last_update_success = available

    def _parse_response(self, data: Any) -> dict[str, Any]:
        """Preserve missing fields, require at least one actual current value."""
        if not isinstance(data, dict) or not isinstance(data.get("hourly"), dict):
            return {}
        hourly = data["hourly"]
        times = hourly.get("time")
        if not isinstance(times, list):
            return {}
        index = next(
            (i for i, value in enumerate(times) if _is_current_hour(value)), None
        )
        if index is None:
            return {}
        result = {key: None for key in POLLEN_TYPES}
        result.update(
            {
                "pm25": None,
                "pm10": None,
                "nitrogen_dioxide": None,
                "ozone": None,
                "uv_index": None,
                "last_update": forecast_datetime(times[index]).isoformat(),
            }
        )
        for pollen_type in POLLEN_TYPES:
            values = hourly.get(pollen_type)
            if not isinstance(values, list) or not values:
                continue
            result[pollen_type] = {
                "current": _number(values[index]) if index < len(values) else None,
                "unit": "Grains/m³",
                "forecast": [_number(value) for value in values[index : index + 24]],
            }
        for parameter in AQ_PARAMETERS:
            values = hourly.get(parameter)
            if not isinstance(values, list) or index >= len(values):
                continue
            key = "pm25" if parameter == AQ_PM25 else parameter
            value = _number(values[index])
            result[key] = round(value, 1) if value is not None else None
        return result if _has_current_values(result) else {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Share a validated current-hour cache and log only HA transitions."""
        cache = get_current_weather_cache()
        cache_key = f"pollen:{self.latitude},{self.longitude}"
        data = cache.get(cache_key)
        if data is not None:
            if _is_current_hour(data.get("last_update")) and _has_current_values(data):
                self._log_uv_availability(data.get("uv_available", True))
                return data
            cache.invalidate(cache_key)
        try:
            data = await self._async_fetch_data()
        except (aiohttp.ClientError, TimeoutError, ValueError):
            raise UpdateFailed("Pollen and air quality source unavailable") from None
        self._log_uv_availability(data["uv_available"])
        cache.set(cache_key, data, ttl=1800.0)
        return data
