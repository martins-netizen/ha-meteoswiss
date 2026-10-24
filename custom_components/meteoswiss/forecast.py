"""Bounded MeteoSwiss ICON forecast source, independent of HA coordination."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, time, timedelta, timezone
from itertools import pairwise
from typing import Any

import aiohttp

from .http import FORECAST_HOST, async_get_json
from .retry import async_retry_with_backoff
from .weather_data import (
    FORECAST_TIME_ZONE,
    forecast_datetime,
    weather_condition,
    weather_number,
)

_LOGGER = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_HOURS = 120
CALENDAR_PAST_HOURS = 25


def _series(block: dict[str, Any], key: str) -> list[Any]:
    """Missing series remain missing; an invalid container is not a forecast."""
    values = block.get(key, [])
    if not isinstance(values, list):
        raise TypeError("Invalid forecast series")
    return values


def _value(
    values: list[Any],
    index: int,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    """Keep finite numeric values, including zero and negative temperatures."""
    return weather_number(
        values[index] if index < len(values) else None, minimum, maximum
    )


def _timestamp(raw: Any) -> datetime:
    """Provider timestamps must be valid and must not be boolean numbers."""
    value = forecast_datetime(raw)
    if value is None:
        raise ValueError("Invalid forecast timestamp")
    return value


def _calendar_hourly_values(
    hourly: dict[str, Any], timestamps: list[datetime], first: datetime, last: datetime
) -> dict[str, Any]:
    """Aggregate a complete Swiss day; rain timestamps end the preceding hour."""
    hours = int((last - first).total_seconds() // 3600)
    instants = {first + timedelta(hours=i) for i in range(hours)}
    interval_ends = {stamp + timedelta(hours=1) for stamp in instants}

    def complete(key: str, expected: set[datetime], minimum=None, maximum=None):
        series = _series(hourly, key)
        values = {
            stamp: _value(series, i, minimum, maximum)
            for i, stamp in enumerate(timestamps)
            if stamp in expected
        }
        if values.keys() != expected or any(v is None for v in values.values()):
            return []
        return list(values.values())

    temperatures = complete("temperature_2m", instants)
    rain = complete("precipitation", interval_ends, 0)
    probabilities = complete("precipitation_probability", interval_ends, 0, 100)
    return {
        "temperature_max": max(temperatures) if temperatures else None,
        "temperature_min": min(temperatures) if temperatures else None,
        "temperature_mean": sum(temperatures) / hours if temperatures else None,
        "precipitation": sum(rain) if rain else None,
        "precipitation_probability": max(probabilities) if probabilities else None,
        "aggregation": "hourly_calendar_day",
        "hours": hours,
    }


class IconForecastError(Exception):
    """The forecast source failed; no request or payload in the message."""


class IconForecastClient:
    """Fetch and validate ICON forecasts using a borrowed HTTP session."""

    def __init__(
        self,
        latitude: float | None,
        longitude: float | None,
        session: aiohttp.ClientSession | None = None,
        *,
        elevation: float | None = None,
    ) -> None:
        self._latitude = latitude
        self._longitude = longitude
        self._session = session
        self.elevation = weather_number(elevation)
        if elevation is not None and self.elevation is None:
            raise ValueError("Invalid forecast elevation")

    async def async_get_data(self) -> list[dict[str, Any]]:
        """Return a valid rolling forecast; keep raw errors out of tracebacks."""
        try:
            return await self._fetch_forecast()
        except (aiohttp.ClientError, TimeoutError, TypeError, ValueError):
            raise IconForecastError() from None

    def map_condition(
        self, weather_code: int | None, is_night: bool = False
    ) -> str | None:
        """Map a known provider code without manufacturing a clear sky."""
        return weather_condition(weather_code, is_day=not is_night)

    async def _fetch_forecast(self) -> list[dict[str, Any]]:
        """Fetch and validate once; only transport failures are retried."""
        if self._latitude is None or self._longitude is None:
            raise ValueError("No coordinates available for Open-Meteo")

        if self._session is None:
            raise RuntimeError("No session provided")

        url = (
            f"{OPEN_METEO_BASE_URL}"
            f"?latitude={self._latitude}"
            f"&longitude={self._longitude}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,windspeed_10m,winddirection_10m,weather_code,is_day,snowfall,freezing_level_height"
            f"&forecast_hours={FORECAST_HOURS}&past_hours={CALENDAR_PAST_HOURS}"
            f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,precipitation_probability_max"
            f"&models=meteoswiss_icon_seamless"
            f"&timezone=Europe/Zurich&timeformat=unixtime"
        )

        if self.elevation is not None:
            url += f"&elevation={self.elevation}"
        return self.parse_response(await self._async_fetch_payload(url))

    @async_retry_with_backoff(max_attempts=3)
    async def _async_fetch_payload(self, url: str) -> Any:
        """Retry transient HTTP failures without logging the location URL."""
        return await async_get_json(self._session, url, host=FORECAST_HOST)

    def parse_response(self, data: Any) -> list[dict[str, Any]]:
        """Normalize a usable rolling forecast without manufacturing values."""
        if not isinstance(data, dict):
            raise TypeError("Expected a forecast response object")

        forecast_data = []
        hourly = data.get("hourly", {})

        if not isinstance(hourly, dict):
            raise TypeError("Invalid hourly forecast object")

        times = _series(hourly, "time")
        timestamps = [
            _timestamp(raw) for raw in times[: FORECAST_HOURS + CALENDAR_PAST_HOURS]
        ]
        if not timestamps or any(a >= b for a, b in pairwise(timestamps)):
            raise ValueError("Forecast times are empty or out of order")
        now = datetime.now(UTC)
        if (
            timestamps[0] > now + timedelta(hours=1)
            or timestamps[-1] + timedelta(hours=1) <= now
        ):
            raise ValueError("Forecast does not cover the requested rolling period")
        temps = _series(hourly, "temperature_2m")
        humidity = _series(hourly, "relative_humidity_2m")
        precip_prob = _series(hourly, "precipitation_probability")
        precip = _series(hourly, "precipitation")
        wind_speed = _series(hourly, "windspeed_10m")
        wind_dir = _series(hourly, "winddirection_10m")
        weather_codes = _series(hourly, "weather_code")
        daylight = _series(hourly, "is_day")
        snowfall = _series(hourly, "snowfall")
        freezing_level = _series(hourly, "freezing_level_height")

        # Native calendar-day extrema from Open-Meteo. These remain complete
        # for the current day even though hourly data starts at the current hour.
        daily = data.get("daily", {})
        if not isinstance(daily, dict):
            raise TypeError("Invalid daily forecast object")
        daily_times = _series(daily, "time")
        daily_max_temps = _series(daily, "temperature_2m_max")
        daily_min_temps = _series(daily, "temperature_2m_min")
        daily_mean_temps = _series(daily, "temperature_2m_mean")
        daily_precip = _series(daily, "precipitation_sum")
        daily_precip_prob = _series(daily, "precipitation_probability_max")
        daily_extrema: dict[str, dict[str, Any]] = {}
        # Open-Meteo daily buckets use the response's fixed offset, even
        # across DST. Preserve their date labels; hourly timestamps use IANA.
        provider_offset = data.get("utc_offset_seconds")
        daily_zone = FORECAST_TIME_ZONE
        if provider_offset is not None:
            offset = _value([provider_offset], 0)
            if offset is None or abs(offset) >= 86400:
                raise ValueError("Invalid forecast UTC offset")
            daily_zone = timezone(timedelta(seconds=offset))
        for i, day in enumerate(daily_times):
            day_time = _timestamp(day)
            local_day = day_time.astimezone(daily_zone).date()
            if provider_offset is not None:
                first = datetime.combine(local_day, time.min, FORECAST_TIME_ZONE)
                last = datetime.combine(
                    local_day + timedelta(days=1), time.min, FORECAST_TIME_ZONE
                )
                # A provider's fixed 24-hour bucket may not be a Swiss day.
                # Rebuild only these mismatched buckets from the same response,
                # with a complete independent coverage check for each field.
                if day_time != first.astimezone(UTC) or day_time + timedelta(
                    days=1
                ) != last.astimezone(UTC):
                    daily_extrema[local_day.isoformat()] = _calendar_hourly_values(
                        hourly, timestamps, first.astimezone(UTC), last.astimezone(UTC)
                    )
                    continue
            daily_extrema[local_day.isoformat()] = {
                "temperature_max": _value(daily_max_temps, i),
                "temperature_min": _value(daily_min_temps, i),
                "precipitation": _value(daily_precip, i, 0),
                "precipitation_probability": _value(daily_precip_prob, i, 0, 100),
                "temperature_mean": _value(daily_mean_temps, i),
                "aggregation": "provider_daily",
                "hours": 24,
            }

        fetched_at = datetime.now(UTC).isoformat()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        projection = [i for i, stamp in enumerate(timestamps) if stamp >= current_hour][
            :FORECAST_HOURS
        ]
        for i in projection:
            raw_code = _value(weather_codes, i, 0)
            code = (
                int(raw_code)
                if raw_code is not None and raw_code.is_integer()
                else None
            )
            timestamp = timestamps[i]
            day = timestamp.astimezone(FORECAST_TIME_ZONE).date().isoformat()
            daily_values = daily_extrema.get(day, {})
            day_value = _value(daylight, i, 0, 1)
            is_day = bool(day_value) if day_value in (0, 1) else None

            entry = {
                "datetime": timestamp.isoformat(),
                "local_date": day,
                "fetched_at": fetched_at,
                "source": "meteoswiss_icon_seamless_via_open_meteo",
                "weather_code": code,
                "is_day": is_day,
                "daily_precipitation": daily_values.get("precipitation"),
                "daily_precipitation_probability": daily_values.get(
                    "precipitation_probability"
                ),
                "temperature": _value(temps, i),
                "daily_temperature_max": daily_values.get("temperature_max"),
                "daily_temperature_min": daily_values.get("temperature_min"),
                "daily_temperature_mean": daily_values.get("temperature_mean"),
                "daily_aggregation": daily_values.get("aggregation"),
                "daily_hours": daily_values.get("hours"),
                "humidity": _value(humidity, i, 0, 100),
                "precipitation_probability": _value(precip_prob, i, 0, 100),
                "precipitation": _value(precip, i, 0),
                "wind_speed": _value(wind_speed, i, 0),
                "wind_direction": _value(wind_dir, i, 0, 360),
                "condition": weather_condition(code, is_day),
                "snowfall": _value(snowfall, i, 0),
                "freezing_level_height": _value(freezing_level, i),
            }
            forecast_data.append(entry)

        if not any(row["temperature"] is not None for row in forecast_data):
            raise ValueError("Forecast contains no usable hourly temperature")
        _LOGGER.debug(
            "Fetched %d hours of forecast from Open-Meteo", len(forecast_data)
        )
        return forecast_data
