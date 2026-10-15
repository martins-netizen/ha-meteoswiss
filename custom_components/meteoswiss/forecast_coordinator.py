"""Forecast coordinator using Open-Meteo API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cache import get_forecast_cache
from .const import DEFAULT_API_TIMEOUT
from .retry import async_retry_with_backoff
from .weather_data import FORECAST_TIME_ZONE, forecast_datetime, weather_condition

_LOGGER = logging.getLogger(__name__)

# Open-Meteo API
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


class MeteoSwissForecastCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Class to manage fetching forecast data from Open-Meteo API."""

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

    def _map_open_meteo_condition(self, weather_code: int | None, is_night: bool = False) -> str | None:
        """Map a known provider code without manufacturing a clear sky."""
        return weather_condition(weather_code, is_day=not is_night)

    @async_retry_with_backoff(max_attempts=3)
    async def _fetch_open_meteo_forecast(self) -> list[dict[str, Any]]:
        """Fetch forecast from Open-Meteo API with retries."""
        if self._latitude is None or self._longitude is None:
            raise UpdateFailed("No coordinates available for Open-Meteo")

        if self._session is None:
            raise RuntimeError("No session provided")

        url = (
            f"{OPEN_METEO_BASE_URL}"
            f"?latitude={self._latitude}"
            f"&longitude={self._longitude}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,windspeed_10m,winddirection_10m,weather_code,is_day,snowfall,freezing_level_height"
            f"&forecast_hours=120"
            f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,precipitation_probability_max"
            f"&models=meteoswiss_icon_seamless"
            f"&timezone=Europe/Zurich&timeformat=unixtime"
        )

        _LOGGER.debug("Fetching from Open-Meteo: %s", url)

        async with self._session.get(url, timeout=DEFAULT_API_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json()
        if not isinstance(data, dict):
            raise ValueError("Expected a forecast response object")

        forecast_data = []
        hourly = data.get("hourly", {})

        if not hourly:
            raise UpdateFailed("Open-Meteo API returned no hourly data")

        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        humidity = hourly.get("relative_humidity_2m", [])
        precip_prob = hourly.get("precipitation_probability", [])
        precip = hourly.get("precipitation", [])
        wind_speed = hourly.get("windspeed_10m", [])
        wind_dir = hourly.get("winddirection_10m", [])
        weather_codes = hourly.get("weather_code", [])
        daylight = hourly.get("is_day", [])
        snowfall = hourly.get("snowfall", [])
        freezing_level = hourly.get("freezing_level_height", [])

        # Native calendar-day extrema from Open-Meteo. These remain complete
        # for the current day even though hourly data starts at the current hour.
        daily = data.get("daily", {})
        daily_times = daily.get("time", [])
        daily_max_temps = daily.get("temperature_2m_max", [])
        daily_min_temps = daily.get("temperature_2m_min", [])
        daily_mean_temps = daily.get("temperature_2m_mean", [])
        daily_precip = daily.get("precipitation_sum", [])
        daily_precip_prob = daily.get("precipitation_probability_max", [])
        daily_extrema: dict[str, dict[str, float | None]] = {}
        # Open-Meteo daily buckets use the response's fixed offset, even
        # across DST. Preserve their date labels; hourly timestamps use IANA.
        provider_offset = data.get("utc_offset_seconds")
        daily_zone = (
            timezone(timedelta(seconds=provider_offset))
            if isinstance(provider_offset, (int, float)) else FORECAST_TIME_ZONE
        )
        for i, day in enumerate(daily_times):
            day_time = forecast_datetime(day)
            if day_time is None:
                raise ValueError("Invalid daily forecast timestamp")
            daily_extrema[day_time.astimezone(daily_zone).date().isoformat()] = {
                "temperature_max": (
                    daily_max_temps[i] if i < len(daily_max_temps) else None
                ),
                "temperature_min": (
                    daily_min_temps[i] if i < len(daily_min_temps) else None
                ),
                "precipitation": daily_precip[i] if i < len(daily_precip) else None,
                "precipitation_probability": daily_precip_prob[i] if i < len(daily_precip_prob) else None,
                "temperature_mean": (
                    daily_mean_temps[i] if i < len(daily_mean_temps) else None
                ),
            }

        fetched_at = datetime.now(timezone.utc).isoformat()
        for i in range(min(120, len(times))):
            code = weather_codes[i] if i < len(weather_codes) else None
            timestamp = forecast_datetime(times[i])
            if timestamp is None:
                raise ValueError("Invalid hourly forecast timestamp")
            day = timestamp.astimezone(FORECAST_TIME_ZONE).date().isoformat()
            daily_values = daily_extrema.get(day, {})
            is_day = bool(daylight[i]) if i < len(daylight) and daylight[i] is not None else None

            entry = {
                "datetime": timestamp.isoformat(),
                "local_date": day,
                "fetched_at": fetched_at,
                "source": "meteoswiss_icon_seamless_via_open_meteo",
                "weather_code": code,
                "is_day": is_day,
                "daily_precipitation": daily_values.get("precipitation"),
                "daily_precipitation_probability": daily_values.get("precipitation_probability"),
                "temperature": temps[i] if i < len(temps) else None,
                "daily_temperature_max": daily_values.get("temperature_max"),
                "daily_temperature_min": daily_values.get("temperature_min"),
                "daily_temperature_mean": daily_values.get("temperature_mean"),
                "humidity": humidity[i] if i < len(humidity) else None,
                "precipitation_probability": precip_prob[i] if i < len(precip_prob) else None,
                "precipitation": precip[i] if i < len(precip) else None,
                "wind_speed": wind_speed[i] if i < len(wind_speed) else None,
                "wind_direction": wind_dir[i] if i < len(wind_dir) else None,
                "condition": weather_condition(code, is_day),
                "snowfall": snowfall[i] if i < len(snowfall) else None,
                "freezing_level_height": freezing_level[i] if i < len(freezing_level) else None,
            }
            forecast_data.append(entry)

        _LOGGER.debug("Fetched %d hours of forecast from Open-Meteo", len(forecast_data))
        return forecast_data

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch forecast data from Open-Meteo API with caching."""
        # Circuit breaker check
        if self._circuit_open_until and datetime.now(timezone.utc) < self._circuit_open_until:
            raise UpdateFailed("Circuit breaker open — API temporarily unavailable")

        _LOGGER.debug("Fetching forecast from Open-Meteo API")

        # Get cache
        cache = get_forecast_cache()
        cache_key = f"forecast:v2:icon-seamless:{self._latitude},{self._longitude}"

        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            _LOGGER.debug("Using cached forecast data")
            return cached_data

        try:
            data = await self._fetch_open_meteo_forecast()

            # Cache the result
            cache.set(cache_key, data)

            # Circuit breaker: reset on success
            self._consecutive_failures = 0
            self._circuit_open_until = None

            _LOGGER.debug("Successfully updated forecast from Open-Meteo")
            return data
        except (aiohttp.ClientError, TimeoutError, ValueError, UpdateFailed) as err:
            _LOGGER.error("Error fetching Open-Meteo forecast: %s", err)
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = datetime.now(timezone.utc) + timedelta(minutes=5)
                _LOGGER.warning(
                    "Circuit breaker opened after %d consecutive failures",
                    self._consecutive_failures,
                )
            raise UpdateFailed("Failed to fetch Open-Meteo forecast") from err

    @property
    def data_source(self) -> str:
        """Return which API was used to fetch data."""
        return "open-meteo"

    async def async_close(self) -> None:
        """Close is handled centrally by the integration setup."""
        # Session is shared and closed in async_unload_entry
        pass
