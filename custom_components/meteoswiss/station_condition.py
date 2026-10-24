"""Small ICON condition request for one observation station, without forecasts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .http import FORECAST_HOST, async_get_json
from .retry import async_retry_with_backoff
from .weather_data import forecast_datetime, weather_condition, weather_number

STATION_CONDITION_SOURCE = "meteoswiss_icon_seamless_via_open_meteo"
STATION_CONDITION_INTERVAL = 600
STATION_CONDITION_URL = "https://api.open-meteo.com/v1/forecast"


class StationConditionError(Exception):
    """No safe, current station condition; never include a URL or payload."""


def current_station_condition(data: Any) -> str | None:
    """A cached model hour must still cover now; zero is a valid weather code."""
    if not isinstance(data, dict) or not isinstance(data.get("is_day"), bool):
        return None
    stamp = forecast_datetime(data.get("time"))
    until = forecast_datetime(data.get("valid_until"))
    fetched = forecast_datetime(data.get("fetched_at"))
    now = datetime.now(UTC)
    if (
        stamp is None
        or until is None
        or fetched is None
        or not stamp <= now < until
        or until - stamp > timedelta(hours=1)
        or now - fetched > timedelta(minutes=20)
        or fetched > now + timedelta(minutes=5)
    ):
        return None
    return weather_condition(data.get("weather_code"), data["is_day"])


class StationConditionClient:
    """Borrow HA's session and request only code/daylight at the station point."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        session: aiohttp.ClientSession | None,
        *,
        elevation: float | None = None,
    ) -> None:
        self.latitude = weather_number(latitude, -90, 90)
        self.longitude = weather_number(longitude, -180, 180)
        self.elevation = weather_number(elevation)
        if (
            self.latitude is None
            or self.longitude is None
            or elevation is not None
            and self.elevation is None
        ):
            raise ValueError("Invalid station condition location")
        self._session = session

    @async_retry_with_backoff(max_attempts=3)
    async def _async_request(self) -> Any:
        if self._session is None:
            raise RuntimeError("No session provided")
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": "weather_code,is_day",
            "models": "meteoswiss_icon_seamless",
            "forecast_days": 1,
            "timezone": "UTC",
            "timeformat": "unixtime",
        }
        if self.elevation is not None:
            params["elevation"] = self.elevation
        return await async_get_json(
            self._session, STATION_CONDITION_URL, params=params, host=FORECAST_HOST
        )

    async def async_get_data(self) -> dict[str, Any]:
        """Invalid payloads are not retried; cancellations propagate to HA."""
        try:
            data = await self._async_request()
            if not isinstance(data, dict) or not isinstance(data.get("current"), dict):
                raise TypeError("No current model condition")
            current = data["current"]
            stamp = forecast_datetime(current.get("time"))
            interval = weather_number(current.get("interval"), 1, 3600)
            daylight = weather_number(current.get("is_day"))
            if stamp is None or interval is None or daylight not in (0, 1):
                raise ValueError("Invalid condition interval")
            result = {
                "time": stamp.isoformat(),
                "valid_until": (stamp + timedelta(seconds=interval)).isoformat(),
                "fetched_at": datetime.now(UTC).isoformat(),
                "weather_code": weather_number(current.get("weather_code")),
                "is_day": bool(daylight),
            }
            if current_station_condition(result) is None:
                raise ValueError("No current condition")
            return result
        except (
            aiohttp.ClientError,
            TimeoutError,
            ValueError,
            TypeError,
            UnicodeError,
            RuntimeError,
        ):
            raise StationConditionError() from None
