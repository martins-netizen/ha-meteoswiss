"""Time and condition contract shared by forecast producers and entities."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .const import WMO_WEATHER_CODES

FORECAST_TIME_ZONE = ZoneInfo("Europe/Zurich")


def forecast_datetime(value: object) -> datetime | None:
    """Normalize provider Unix seconds or legacy local strings to aware UTC.

    New requests use Unix seconds: the two 02:00 hours at the autumn DST
    transition remain distinct. Naive legacy strings refer to Europe/Zurich,
    never to the operating system's local time.
    """
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, UTC)
        if not isinstance(value, str):
            return None
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=FORECAST_TIME_ZONE)
        return parsed.astimezone(UTC)
    except (ValueError, OverflowError, OSError):
        return None


def known_weather_code(raw: object) -> int | None:
    """Return only integral codes present in the WMO condition table."""
    value = weather_number(raw)
    return int(value) if value in WMO_WEATHER_CODES else None


def weather_condition(code: object, is_day: bool | None = None) -> str | None:
    """Unknown input stays unknown; provider daylight distinguishes night."""
    known_code = known_weather_code(code)
    if known_code is None:
        return None
    condition = WMO_WEATHER_CODES[known_code]
    if condition == "sunny" and is_day is False:
        return "clear-night"
    return condition


class StaleObservationError(ValueError):
    """A current-weather sample exceeds its allowed age."""

    def __init__(self, age: timedelta) -> None:
        self.age_minutes = age // timedelta(minutes=1)
        super().__init__("Observation timestamp is too old")


def validate_observation_time(
    data: Mapping[str, object], max_age: timedelta = timedelta(hours=1)
) -> None:
    """A successful download must not make stale measurements current."""
    timestamp = forecast_datetime(data.get("last_update"))
    now = datetime.now(UTC)
    if timestamp is None or timestamp - now > timedelta(minutes=10):
        raise ValueError("Observation timestamp is missing or in the future")
    age = now - timestamp
    if age > max_age:
        raise StaleObservationError(age)


def weather_number(
    raw: Any, minimum: float | None = None, maximum: float | None = None
) -> float | None:
    """Shared finite-number contract; missing values never become zero."""
    if raw is None or isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError, OverflowError):
        return None
    if (
        not math.isfinite(value)
        or minimum is not None
        and value < minimum
        or maximum is not None
        and value > maximum
    ):
        return None
    return value


def parse_reference_timestamp(value: str | None) -> datetime | None:
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
