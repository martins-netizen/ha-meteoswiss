"""Bounded Open-Meteo current-weather client, independent of HA coordination."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .const import (
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_SPEED,
    WMO_WEATHER_CODES,
)
from .http import FORECAST_HOST, async_get_json
from .retry import async_retry_with_backoff
from .weather_data import (
    forecast_datetime,
    weather_condition,
    weather_number,
)

# Open-Meteo API
OPENMETEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# WMO code descriptions (condition comes from const.WMO_WEATHER_CODES)
WMO_CODE_DESCRIPTIONS: dict[int, dict[str, str]] = {
    0: {"condition": "clear", "description": "Clear sky"},
    1: {"condition": "mainly_clear", "description": "Mainly clear"},
    2: {"condition": "partly_cloudy", "description": "Partly cloudy"},
    3: {"condition": "overcast", "description": "Overcast"},
    45: {"condition": "fog", "description": "Fog"},
    48: {"condition": "fog", "description": "Depositing rime fog"},
    51: {"condition": "light_rain", "description": "Light drizzle"},
    53: {"condition": "light_rain", "description": "Moderate drizzle"},
    55: {"condition": "light_rain", "description": "Dense drizzle"},
    56: {"condition": "light_rain", "description": "Light freezing drizzle"},
    57: {"condition": "light_rain", "description": "Dense freezing drizzle"},
    61: {"condition": "rain", "description": "Slight rain"},
    63: {"condition": "rain", "description": "Moderate rain"},
    65: {"condition": "rain", "description": "Heavy rain"},
    66: {"condition": "rain", "description": "Light freezing rain"},
    67: {"condition": "rain", "description": "Heavy freezing rain"},
    71: {"condition": "snow", "description": "Slight snow fall"},
    73: {"condition": "snow", "description": "Moderate snow fall"},
    75: {"condition": "snow", "description": "Heavy snow fall"},
    77: {"condition": "snow", "description": "Snow grains"},
    80: {"condition": "showers", "description": "Slight rain showers"},
    81: {"condition": "showers", "description": "Moderate rain showers"},
    82: {"condition": "showers", "description": "Violent rain showers"},
    85: {"condition": "showers", "description": "Slight snow showers"},
    86: {"condition": "showers", "description": "Heavy snow showers"},
    95: {"condition": "lightning", "description": "Thunderstorm"},
    96: {"condition": "lightning", "description": "Thunderstorm with slight hail"},
    99: {"condition": "lightning", "description": "Thunderstorm with heavy hail"},
}


def _code(raw: Any) -> int | None:
    """Only known integral WMO codes can describe the weather."""
    value = weather_number(raw)
    return int(value) if value in WMO_WEATHER_CODES else None


class OpenMeteoCurrentError(Exception):
    """The current-weather source failed; no request/payload in the message."""


class OpenMeteoCurrentClient:
    """Fetch and parse current data; HA applies freshness to fetched/cached data."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.latitude = latitude
        self.longitude = longitude
        self._session = session

    def get_weather_condition(self, code: int | None) -> str:
        """Get HA weather condition from WMO code."""
        if code is None:
            return "unknown"
        return WMO_WEATHER_CODES.get(code, "unknown")

    def get_weather_description(self, code: int | None) -> str:
        """Get weather description from WMO code."""
        if code is None:
            return "Unknown"

        weather_info = WMO_CODE_DESCRIPTIONS.get(code, {"description": "Unknown"})
        return weather_info["description"]

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_request(self) -> Any:
        """Retry transport failures only, without logging private request URLs."""
        if self._session is None:
            raise RuntimeError("No session provided")
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,"
                "wind_direction_10m,precipitation,weather_code,is_day,uv_index"
            ),
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code",
            "forecast_hours": 24,
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timezone": "Europe/Zurich",
            "timeformat": "unixtime",
        }
        return await async_get_json(
            self._session, OPENMETEO_BASE_URL, params=params, host=FORECAST_HOST
        )

    async def async_get_data(self) -> dict[str, Any]:
        """Return parsed observations or a source error without private details."""
        try:
            return self.parse_response(await self._async_request())
        except (
            aiohttp.ClientError,
            TimeoutError,
            ValueError,
            TypeError,
            UnicodeError,
            RuntimeError,
        ):
            raise OpenMeteoCurrentError from None

    def parse_response(self, data: Any) -> dict[str, Any]:
        """Keep valid individual values; reject an empty current source."""
        if not isinstance(data, dict) or not isinstance(data.get("current"), dict):
            raise TypeError("Invalid current weather response")
        current = data["current"]
        raw_time = current.get("time")
        timestamp = forecast_datetime(raw_time)
        if timestamp is None:
            raise ValueError("Invalid current weather timestamp")
        result = {
            SENSOR_TEMPERATURE: weather_number(current.get("temperature_2m")),
            SENSOR_HUMIDITY: weather_number(
                current.get("relative_humidity_2m"), 0, 100
            ),
            SENSOR_WIND_SPEED: weather_number(current.get("wind_speed_10m"), 0),
            SENSOR_WIND_DIRECTION: weather_number(
                current.get("wind_direction_10m"), 0, 360
            ),
            SENSOR_PRECIPITATION: weather_number(current.get("precipitation"), 0),
            SENSOR_PRESSURE: weather_number(current.get("pressure_msl"), 0),
            "uv_index": weather_number(current.get("uv_index"), 0),
        }
        if all(value is None for value in result.values()):
            raise ValueError("No usable current weather values")
        code = _code(current.get("weather_code"))
        is_day = weather_number(current.get("is_day"), 0, 1)
        result.update(
            weather_code=code,
            weather_condition=weather_condition(
                code, is_day=bool(is_day) if is_day in (0, 1) else None
            ),
            weather_description=self.get_weather_description(code),
            last_update=timestamp.isoformat(),
            # Current precipitation is the provider's backwards-looking interval
            # amount, NOT an hourly total or a precipitation rate.
            precipitation_interval_seconds=weather_number(current.get("interval"), 1),
            hourly_forecast=self._parse_hourly(data.get("hourly")),
        )
        return result

    def _parse_hourly(self, hourly: Any) -> list[dict[str, Any]]:
        """Optional legacy preview must never invalidate current observations.

        HA weather forecasts use the independent ICON Seamless coordinator.
        Keep this preview bounded to the next 24 UTC hours without falling
        back to midnight when the current hour is missing.
        """
        if not isinstance(hourly, dict):
            return []
        keys = (
            "time",
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "weather_code",
        )
        if any(not isinstance(hourly.get(key, []), list) for key in keys):
            return []
        now_hour = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        end = now_hour + timedelta(hours=24)
        result = []
        previous = None
        for index, raw_time in enumerate(hourly.get("time", [])):
            timestamp = forecast_datetime(raw_time)
            if (
                timestamp is None
                or timestamp.minute
                or timestamp.second
                or timestamp.microsecond
                or previous is not None
                and timestamp <= previous
            ):
                return []
            previous = timestamp
            if not now_hour <= timestamp < end:
                continue
            values = {
                key: hourly.get(key, [])[index]
                if index < len(hourly.get(key, []))
                else None
                for key in keys[1:]
            }
            temperature = weather_number(values["temperature_2m"])
            if temperature is None:
                continue
            code = _code(values["weather_code"])
            result.append(
                {
                    "datetime": timestamp.isoformat(),
                    "temperature": temperature,
                    "humidity": weather_number(values["relative_humidity_2m"], 0, 100),
                    "precipitation_probability": weather_number(
                        values["precipitation_probability"], 0, 100
                    ),
                    "weather_code": code,
                    "condition": self.get_weather_condition(code),
                }
            )
        return result
