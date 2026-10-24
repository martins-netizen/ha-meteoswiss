"""Calendar days must survive both clock changes without inventing missing data."""

from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from custom_components.meteoswiss.forecast import IconForecastClient
from custom_components.meteoswiss.forecast_summary import summarize_forecast

ZONE = ZoneInfo("Europe/Zurich")


def response(now, day, offset):
    first = datetime.fromisoformat(day).replace(tzinfo=ZONE).astimezone(UTC)
    last = (
        (datetime.fromisoformat(day) + timedelta(days=1))
        .replace(tzinfo=ZONE)
        .astimezone(UTC)
    )
    start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=25)
    stamps = [start + timedelta(hours=i) for i in range(145)]
    hourly = {
        "time": [int(stamp.timestamp()) for stamp in stamps],
        "temperature_2m": [
            -9
            if stamp == first + timedelta(hours=2)
            else 17
            if stamp == first + timedelta(hours=3)
            else 80
            if stamp == last
            else 5
            for stamp in stamps
        ],
        "precipitation": [
            999 if stamp == first else 7 if stamp == last else 1 for stamp in stamps
        ],
        "precipitation_probability": [
            100 if stamp == first else 30 if stamp == last else 10 for stamp in stamps
        ],
    }
    provider_start = datetime.fromisoformat(day).replace(
        tzinfo=timezone(timedelta(seconds=offset))
    )
    return (
        {
            "utc_offset_seconds": offset,
            "hourly": hourly,
            "daily": {
                "time": [int(provider_start.timestamp())],
                "temperature_2m_max": [1000],
                "temperature_2m_min": [-1000],
                "temperature_2m_mean": [0],
                "precipitation_sum": [9999],
                "precipitation_probability_max": [100],
            },
        },
        first,
        last,
    )


@pytest.mark.parametrize(
    "now,day,offset,hours",
    [
        ("2026-03-28T10:20:00+00:00", "2026-03-29", 3600, 23),
        ("2026-03-29T20:20:00+00:00", "2026-03-29", 7200, 23),
        ("2026-03-28T10:20:00+00:00", "2026-03-30", 3600, 24),
        ("2026-10-24T10:20:00+00:00", "2026-10-25", 7200, 25),
        ("2026-10-25T22:20:00+00:00", "2026-10-25", 3600, 25),
        ("2026-10-24T10:20:00+00:00", "2026-10-26", 7200, 24),
    ],
)
def test_complete_swiss_day_includes_both_fold_hours_and_correct_rain_midnight(
    freezer, now, day, offset, hours
):
    now = datetime.fromisoformat(now)
    freezer.move_to(now)
    data, _, _ = response(now, day, offset)
    rows = IconForecastClient(47.2, 9.3).parse_response(data)
    assert len(rows) == 120
    assert datetime.fromisoformat(rows[0]["datetime"]) == now.replace(minute=0)
    assert datetime.fromisoformat(rows[-1]["datetime"]) == now.replace(
        minute=0
    ) + timedelta(hours=119)
    target = next(row for row in rows if row["local_date"] == day)
    assert target["daily_temperature_max"] == 17
    assert target["daily_temperature_min"] == -9
    assert target["daily_temperature_mean"] == pytest.approx(5 - 2 / hours)
    assert target["daily_precipitation"] == hours + 6
    assert target["daily_precipitation_probability"] == 30
    day_offset = (datetime.fromisoformat(day).date() - now.astimezone(ZONE).date()).days
    value, attrs = summarize_forecast(rows, now, day_offset, "precipitation")
    assert value == hours + 6
    assert attrs["aggregation"] == "hourly_calendar_day"
    assert attrs["day_hours"] == hours


@pytest.mark.parametrize(
    "key,invalid,missing_fields",
    [
        (
            "temperature_2m",
            None,
            (
                "daily_temperature_max",
                "daily_temperature_min",
                "daily_temperature_mean",
            ),
        ),
        (
            "temperature_2m",
            True,
            (
                "daily_temperature_max",
                "daily_temperature_min",
                "daily_temperature_mean",
            ),
        ),
        ("precipitation", None, ("daily_precipitation",)),
        ("precipitation", -1, ("daily_precipitation",)),
        ("precipitation", float("nan"), ("daily_precipitation",)),
        ("precipitation_probability", 101, ("daily_precipitation_probability",)),
    ],
)
def test_a_missing_hour_invalidates_only_its_own_day_metric(
    freezer, key, invalid, missing_fields
):
    now = datetime(2026, 10, 24, 10, 20, tzinfo=UTC)
    freezer.move_to(now)
    data, first, _ = response(now, "2026-10-25", 7200)
    index = data["hourly"]["time"].index(int((first + timedelta(hours=1)).timestamp()))
    data["hourly"][key][index] = invalid
    rows = IconForecastClient(47.2, 9.3).parse_response(data)
    target = next(row for row in rows if row["local_date"] == "2026-10-25")
    assert all(target[field] is None for field in missing_fields)
    assert (
        target["daily_precipitation"] is None
        if key == "precipitation"
        else target["daily_precipitation"] == 31
    )
    assert (
        target["daily_temperature_max"] is None
        if key == "temperature_2m"
        else target["daily_temperature_max"] == 17
    )


def test_incomplete_history_cannot_be_replaced_by_wrong_native_day(freezer):
    now = datetime(2026, 10, 25, 12, 20, tzinfo=UTC)
    freezer.move_to(now)
    data, first, _ = response(now, "2026-10-25", 3600)
    missing = data["hourly"]["time"].index(
        int((first + timedelta(hours=1)).timestamp())
    )
    for series in data["hourly"].values():
        del series[missing]
    rows = IconForecastClient(47.2, 9.3).parse_response(data)
    today = next(row for row in rows if row["local_date"] == "2026-10-25")
    assert today["daily_temperature_max"] is None
    assert today["daily_precipitation"] is None


def test_aligned_native_daily_values_remain_preferred(freezer):
    now = datetime(2026, 10, 24, 10, 20, tzinfo=UTC)
    freezer.move_to(now)
    data, _, _ = response(now, "2026-10-24", 7200)
    rows = IconForecastClient(47.2, 9.3).parse_response(data)
    today = rows[0]
    assert today["daily_temperature_max"] == 1000
    assert today["daily_precipitation"] == 9999
    assert today["daily_aggregation"] == "provider_daily"
    assert today["daily_hours"] == 24


def test_zero_and_negative_day_values_are_not_missing(freezer):
    now = datetime(2026, 10, 24, 10, 20, tzinfo=UTC)
    freezer.move_to(now)
    data, _, _ = response(now, "2026-10-25", 7200)
    data["hourly"]["temperature_2m"] = [-2] * 145
    data["hourly"]["precipitation"] = [0] * 145
    data["hourly"]["precipitation_probability"] = [0] * 145
    rows = IconForecastClient(47.2, 9.3).parse_response(data)
    target = next(row for row in rows if row["local_date"] == "2026-10-25")
    assert target["daily_temperature_max"] == target["daily_temperature_min"] == -2
    assert target["daily_temperature_mean"] == -2
    assert (
        target["daily_precipitation"] == target["daily_precipitation_probability"] == 0
    )
