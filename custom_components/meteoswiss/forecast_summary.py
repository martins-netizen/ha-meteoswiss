"""Scalar forecasts and matching hourly windows without HA state or IO."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Literal

from .weather_data import FORECAST_TIME_ZONE, forecast_datetime, weather_number

ForecastMetric = Literal[
    "maximum_temperature", "minimum_temperature", "precipitation", "probability"
]
FORECAST_MAX_AGE = timedelta(hours=3)
FORECAST_FUTURE_SKEW = timedelta(minutes=10)
FORECAST_ATTRIBUTION = "MeteoSwiss ICON Seamless via Open-Meteo"


def forecast_snapshot_time(data: Any) -> datetime | None:
    """Use the snapshot's first supplied retrieval time, never a model hour."""
    if not isinstance(data, list):
        return None
    for row in data:
        if isinstance(row, dict) and row.get("fetched_at") is not None:
            return forecast_datetime(row["fetched_at"])
    return None


def forecast_is_fresh(data: Any, now: datetime) -> bool:
    """A new scalar entity requires a valid, current retrieval timestamp."""
    stamp = forecast_snapshot_time(data)
    return (
        stamp is not None
        and now - stamp <= FORECAST_MAX_AGE
        and stamp - now <= FORECAST_FUTURE_SKEW
    )


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time.min, FORECAST_TIME_ZONE).astimezone(UTC)


def _daily_value(rows: list[Any], target: date, metric: ForecastMetric) -> float | None:
    """Use a native whole-day value; never sum a partial hourly series."""
    field = {
        "maximum_temperature": "daily_temperature_max",
        "minimum_temperature": "daily_temperature_min",
        "precipitation": "daily_precipitation",
    }[metric]
    for row in rows:
        if not isinstance(row, dict) or row.get("local_date") != target.isoformat():
            continue
        value = weather_number(row.get(field), 0 if metric == "precipitation" else None)
        if value is not None:
            return value
    return None


def _probability_values(
    rows: list[Any], expected: set[datetime]
) -> dict[datetime, float]:
    """Select valid values by physical interval end, including midnight."""
    values: dict[datetime, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        end = forecast_datetime(row.get("datetime"))
        probability = weather_number(row.get("precipitation_probability"), 0, 100)
        if end is not None and end in expected and probability is not None:
            values[end] = probability
    return values


def _peak_periods(values: dict[datetime, float], peak: float) -> list[dict[str, str]]:
    """Merge adjacent ties while retaining every separate maximum window."""
    periods: list[dict[str, datetime]] = []
    for end, probability in sorted(values.items()):
        if probability != peak:
            continue
        start = end - timedelta(hours=1)
        if periods and periods[-1]["end"] == start:
            periods[-1]["end"] = end
        else:
            periods.append({"start": start, "end": end})
    return [
        {
            key: stamp.astimezone(FORECAST_TIME_ZONE).isoformat()
            for key, stamp in period.items()
        }
        for period in periods
    ]


def summarize_forecast(
    rows: list[Any], now: datetime, day_offset: int, metric: ForecastMetric
) -> tuple[float | None, dict[str, Any]]:
    """Summarize native daily fields or complete, correctly aligned hour buckets."""
    today = now.astimezone(FORECAST_TIME_ZONE).date()
    target = today + timedelta(days=day_offset)
    fetched = forecast_snapshot_time(rows)
    attributes: dict[str, Any] = {
        "value_type": "forecast",
        "forecast_date": target.isoformat(),
        "forecast_period": "full_day",
        "source": FORECAST_ATTRIBUTION,
        "fetched_at": fetched.isoformat() if fetched else None,
    }
    if metric != "probability":
        return _daily_value(rows, target, metric), attributes

    first = _midnight(target)
    last = _midnight(target + timedelta(days=1))
    if target == today:
        first = max(
            first, now.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        )
        attributes["forecast_period"] = "remaining_hours"
    expected = {
        first + timedelta(hours=i + 1)
        for i in range(int((last - first).total_seconds() // 3600))
    }
    values = _probability_values(rows, expected)
    complete = len(values) == len(expected)
    attributes.update(
        expected_hours=len(expected),
        valid_hours=len(values),
        coverage_complete=complete,
        peak_start=None,
        peak_end=None,
        peak_periods=[],
    )
    # A partial series cannot establish the maximum of the promised period.
    if not complete:
        return None, attributes
    peak = max(values.values())
    if peak == 0:
        return peak, attributes
    attributes["peak_periods"] = _peak_periods(values, peak)
    attributes["peak_start"] = attributes["peak_periods"][0]["start"]
    attributes["peak_end"] = attributes["peak_periods"][0]["end"]
    return peak, attributes
