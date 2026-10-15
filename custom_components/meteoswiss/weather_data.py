"""Time and condition contract shared by forecast producers and entities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from .const import WMO_WEATHER_CODES

FORECAST_TIME_ZONE = ZoneInfo("Europe/Zurich")


def forecast_datetime(value: int | float | str | None) -> datetime | None:
    """Normalize provider Unix seconds or legacy local strings to aware UTC.

    New requests use Unix seconds: the two 02:00 hours at the autumn DST
    transition remain distinct. Naive legacy strings refer to Europe/Zurich,
    never to the operating system's local time.
    """
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, UTC)
        if not isinstance(value, str):
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=FORECAST_TIME_ZONE)
        return parsed.astimezone(UTC)
    except (ValueError, OverflowError, OSError):
        return None


def weather_condition(code: int | None, is_day: bool | None = None) -> str | None:
    """Unknown input stays unknown; provider daylight distinguishes night."""
    condition = WMO_WEATHER_CODES.get(code)
    if condition == "sunny" and is_day is False:
        return "clear-night"
    return condition


def validate_observation_time(
    data: dict, max_age: timedelta = timedelta(hours=1)
) -> None:
    """A successful download must not make stale measurements current."""
    timestamp = forecast_datetime(data.get("last_update"))
    now = datetime.now(UTC)
    if (
        timestamp is None
        or now - timestamp > max_age
        or timestamp - now > timedelta(minutes=10)
    ):
        raise ValueError("Observation timestamp is missing, stale or in the future")
