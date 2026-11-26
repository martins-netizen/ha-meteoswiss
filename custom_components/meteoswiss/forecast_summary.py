"""Scalar forecasts and matching hourly windows without HA state or IO."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Literal

from .weather_data import FORECAST_TIME_ZONE, forecast_datetime, weather_number

ForecastMetric = Literal[
    "maximum_temperature", "minimum_temperature", "precipitation", "probability",
    "shortwave_radiation", "diffuse_radiation", "wind_gust_speed",
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


def _daily_value(
    rows: list[Any], target: date, metric: ForecastMetric
) -> tuple[float | None, dict[str, Any]]:
    """Use a validated whole-day value and retain its aggregation provenance."""
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
            details = {}
            if row.get("daily_aggregation") in (
                "provider_daily",
                "hourly_calendar_day",
            ):
                details["aggregation"] = row["daily_aggregation"]
                details["day_hours"] = row.get("daily_hours")
            return value, details
    return None, {}


def _hourly_values(
    rows: list[Any], expected: set[datetime], field: str, maximum: float | None = None
) -> dict[datetime, float]:
    """Select valid values by physical interval end, including midnight."""
    values: dict[datetime, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        end = forecast_datetime(row.get("datetime"))
        if end is not None and end in expected:
            value = weather_number(row.get(field), 0, maximum)
            if value is not None:
                values[end] = value
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


def _hourly_outlook(
    rows: list[Any], now: datetime, field: str, attributes: dict[str, Any]
) -> tuple[float | None, dict[str, Any]]:
    """Summarize the current clock hour and 23 following physical hour buckets."""
    hour = timedelta(hours=1)
    start = now.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    ends = [start + i * hour for i in range(1, 25)]
    values = _hourly_values(rows, set(ends), field)
    # UTC arithmetic keeps both Swiss 02:00 hours separate on the autumn change.
    boundaries = [stamp.astimezone(FORECAST_TIME_ZONE).isoformat() for stamp in [start, *ends]]
    attributes.update(
        window_start=boundaries[0],
        window_end=boundaries[-1],
        expected_hours=len(ends),
        valid_hours=len(values),
        coverage_complete=len(values) == len(ends),
    )
    attributes["hourly_forecast"] = [
        {"start": boundaries[i], "end": boundaries[i + 1], "value": values.get(end)}
        for i, end in enumerate(ends)
    ]
    if field == "wind_gust_speed":
        attributes.update(hourly_forecast_unit="km/h", peak_start=None, peak_end=None)
        if len(values) != len(ends):
            return None, attributes
        # Ties, including a completely calm day, use the earliest interval.
        index = max(range(len(ends)), key=lambda i: values[ends[i]])
        attributes.update(peak_start=boundaries[index], peak_end=boundaries[index + 1])
        return values[ends[index]], attributes

    return values.get(ends[0]), attributes


def summarize_forecast(
    rows: list[Any], now: datetime, day_offset: int, metric: ForecastMetric
) -> tuple[float | None, dict[str, Any]]:
    """Summarize native daily fields or complete, correctly aligned hour buckets."""
    fetched = forecast_snapshot_time(rows)
    attributes: dict[str, Any] = {
        "value_type": "forecast",
        "source": FORECAST_ATTRIBUTION,
        "fetched_at": fetched.isoformat() if fetched else None,
    }
    if metric in ("shortwave_radiation", "diffuse_radiation", "wind_gust_speed"):
        return _hourly_outlook(rows, now, metric, attributes)
    today = now.astimezone(FORECAST_TIME_ZONE).date()
    target = today + timedelta(days=day_offset)
    attributes.update(forecast_date=target.isoformat(), forecast_period="full_day")
    if metric != "probability":
        value, details = _daily_value(rows, target, metric)
        return value, {**attributes, **details}

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
    values = _hourly_values(rows, expected, "precipitation_probability", 100)
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
