"""Calendar-day predictions, preceding-hour probability and source freshness."""

from datetime import UTC, datetime, time, timedelta

import pytest

from custom_components.meteoswiss.forecast_summary import (
    forecast_is_fresh,
    forecast_snapshot_time,
    summarize_forecast,
)
from custom_components.meteoswiss.weather_data import FORECAST_TIME_ZONE

NOW = datetime(2026, 10, 23, 10, 20, tzinfo=UTC)


def forecast_rows(now=NOW, days=3, probability=10):
    day = now.astimezone(FORECAST_TIME_ZONE).date()
    first = datetime.combine(day, time.min, FORECAST_TIME_ZONE).astimezone(UTC)
    last = datetime.combine(
        day + timedelta(days=days), time.min, FORECAST_TIME_ZONE
    ).astimezone(UTC)
    rows = []
    end = first + timedelta(hours=1)
    while end <= last:
        local_day = end.astimezone(FORECAST_TIME_ZONE).date()
        offset = (local_day - day).days
        rows.append(
            {
                "datetime": end.isoformat(),
                "fetched_at": now.isoformat(),
                "local_date": local_day.isoformat(),
                "temperature": 99,
                "daily_temperature_max": 12 + offset,
                "daily_temperature_min": -2 + offset,
                "daily_precipitation": float(offset),
                "precipitation_probability": probability,
            }
        )
        end += timedelta(hours=1)
    return rows


@pytest.mark.parametrize("offset", [0, 1])
@pytest.mark.parametrize(
    "metric,expected",
    [
        ("maximum_temperature", 12),
        ("minimum_temperature", -2),
        ("precipitation", 0),
    ],
)
def test_native_calendar_values_do_not_use_remaining_hour_extrema(
    offset, metric, expected
):
    rows = forecast_rows()
    value, attrs = summarize_forecast([None, {}, *rows], NOW, offset, metric)
    assert value == expected + offset
    assert attrs["forecast_period"] == "full_day"
    assert attrs["forecast_date"] == f"2026-10-{23 + offset}"
    assert attrs["value_type"] == "forecast"
    assert attrs["fetched_at"] == NOW.isoformat()


@pytest.mark.parametrize(
    "invalid", [None, True, "broken", float("nan"), float("inf"), -1]
)
def test_missing_invalid_daily_rain_is_not_replaced_by_zero_or_hourly_sum(invalid):
    rows = forecast_rows()
    for row in rows:
        row["daily_precipitation"] = invalid
        row["precipitation"] = 10
    value, _ = summarize_forecast(rows, NOW, 0, "precipitation")
    assert value is None


def test_missing_native_daily_fields_are_unknown_even_with_hourly_temperatures():
    rows = [{"local_date": "2026-10-23", "temperature": 35}]
    assert summarize_forecast(rows, NOW, 0, "maximum_temperature")[0] is None
    assert summarize_forecast(rows, NOW, 1, "minimum_temperature")[0] is None


def test_today_ignores_elapsed_peak_and_merges_only_adjacent_tied_windows():
    rows = forecast_rows()
    for row in rows:
        local = datetime.fromisoformat(row["datetime"]).astimezone(FORECAST_TIME_ZONE)
        if local.date().isoformat() == "2026-10-23":
            row["precipitation_probability"] = {9: 95, 15: 80, 16: 80, 19: 80}.get(
                local.hour, 10
            )
    value, attrs = summarize_forecast(
        [None, {"datetime": "bad"}, *rows], NOW, 0, "probability"
    )
    assert value == 80
    assert attrs["expected_hours"] == attrs["valid_hours"] == 12
    assert attrs["coverage_complete"]
    assert attrs["forecast_period"] == "remaining_hours"
    assert attrs["peak_periods"] == [
        {"start": "2026-10-23T14:00:00+02:00", "end": "2026-10-23T16:00:00+02:00"},
        {"start": "2026-10-23T18:00:00+02:00", "end": "2026-10-23T19:00:00+02:00"},
    ]
    assert attrs["peak_start"] == attrs["peak_periods"][0]["start"]
    assert attrs["peak_end"] == attrs["peak_periods"][0]["end"]


def test_midnight_timestamp_probability_belongs_to_the_preceding_day():
    rows = forecast_rows(probability=0)
    for row in rows:
        local = datetime.fromisoformat(row["datetime"]).astimezone(FORECAST_TIME_ZONE)
        if local.isoformat() == "2026-10-24T00:00:00+02:00":
            row["precipitation_probability"] = 100
        if local.isoformat() == "2026-10-25T00:00:00+02:00":
            row["precipitation_probability"] = 80
    value, attrs = summarize_forecast(rows, NOW, 1, "probability")
    assert value == 80
    assert attrs["expected_hours"] == attrs["valid_hours"] == 24
    assert attrs["forecast_period"] == "full_day"
    assert attrs["peak_periods"] == [
        {"start": "2026-10-24T23:00:00+02:00", "end": "2026-10-25T00:00:00+02:00"}
    ]


@pytest.mark.parametrize(
    "now,hours",
    [
        (datetime(2026, 3, 28, 10, 20, tzinfo=UTC), 23),
        (datetime(2026, 10, 24, 10, 20, tzinfo=UTC), 25),
    ],
)
def test_dst_days_use_physical_hour_intervals_with_explicit_offsets(now, hours):
    value, attrs = summarize_forecast(forecast_rows(now), now, 1, "probability")
    assert value == 10
    assert attrs["expected_hours"] == attrs["valid_hours"] == hours
    period = attrs["peak_periods"][0]
    assert (
        datetime.fromisoformat(period["end"]) - datetime.fromisoformat(period["start"])
    ).total_seconds() == hours * 3600
    assert period["start"][-6:] != period["end"][-6:]


@pytest.mark.parametrize("invalid", [None, True, "bad", -1, 101, float("nan")])
def test_partial_probability_cannot_claim_a_known_period_maximum(invalid):
    rows = forecast_rows()
    rows[-3]["precipitation_probability"] = 100  # Outside today's window.
    target = next(row for row in rows if row["datetime"] == "2026-10-23T11:00:00+00:00")
    target["precipitation_probability"] = invalid
    value, attrs = summarize_forecast(rows, NOW, 0, "probability")
    assert value is None
    assert not attrs["coverage_complete"]
    assert attrs["valid_hours"] == attrs["expected_hours"] - 1
    assert attrs["peak_periods"] == []


def test_zero_probability_has_no_arbitrary_peak_time_and_empty_data_is_unknown():
    value, attrs = summarize_forecast(
        forecast_rows(probability=0), NOW, 0, "probability"
    )
    assert value == 0
    assert attrs["peak_start"] is attrs["peak_end"] is None
    assert attrs["peak_periods"] == []
    value, attrs = summarize_forecast([], NOW, 1, "probability")
    assert value is None
    assert attrs["valid_hours"] == 0


@pytest.mark.parametrize(
    "data", [None, {}, [], [None, {}], [{"fetched_at": True}], [{"fetched_at": "bad"}]]
)
def test_absent_or_invalid_snapshot_time_is_not_current(data):
    assert forecast_snapshot_time(data) is None
    assert not forecast_is_fresh(data, NOW)


@pytest.mark.parametrize(
    "age,fresh",
    [
        (timedelta(hours=3), True),
        (timedelta(hours=3, microseconds=1), False),
        (timedelta(minutes=-10), True),
        (timedelta(minutes=-10, microseconds=-1), False),
    ],
)
def test_freshness_uses_retrieval_time_with_exact_age_and_future_limits(age, fresh):
    rows = [{"fetched_at": (NOW - age).isoformat()}]
    assert forecast_is_fresh(rows, NOW) is fresh
