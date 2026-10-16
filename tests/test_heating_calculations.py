"""Swiss HGT boundaries, missing data and season-helper contracts."""

from datetime import date

import pytest

from custom_components.meteoswiss.calc import (
    calculate_heating_degree_days,
    compute_season_hgt,
    get_heating_season_start_date,
    is_in_heating_season,
)


@pytest.mark.parametrize(
    "temperature,expected",
    [
        (None, None),
        (-5, 25),
        (0, 20),
        (11.9, 8.1),
        (12, 8),
        (12.01, 0),
        (20, 0),
        (float("nan"), None),
        (float("inf"), None),
        (-float("inf"), None),
        (True, None),
        (False, None),
    ],
)
def test_hgt_12_20_keeps_zero_and_rejects_non_measurements(temperature, expected):
    assert calculate_heating_degree_days(temperature) == expected


@pytest.mark.parametrize(
    "day,in_season,start",
    [
        ("2026-01-01", True, "2025-10-01"),
        ("2026-04-30", True, "2025-10-01"),
        ("2026-05-01", False, "2025-10-01"),
        ("2026-09-30", False, "2025-10-01"),
        ("2026-10-01", True, "2026-10-01"),
        ("2026-12-31", True, "2026-10-01"),
    ],
)
def test_season_boundary_helpers(day, in_season, start, freezer):
    parsed = date.fromisoformat(day)
    assert is_in_heating_season(parsed) is in_season
    assert get_heating_season_start_date(parsed).isoformat() == start
    freezer.move_to(day + "T12:00:00+00:00")
    assert is_in_heating_season() is in_season
    assert get_heating_season_start_date().isoformat() == start


def test_season_total_ignores_future_old_invalid_and_missing_days(freezer):
    freezer.move_to("2026-10-16T10:00:00+00:00")
    result = compute_season_hgt(
        [
            {"date": "2026-09-30", "temperature_mean": -5},
            {"date": "2026-10-17", "temperature_mean": -5},
            {"date": "", "temperature_mean": 5},
            {"date": "bad", "temperature_mean": 5},
            {"date": "2026-10-02", "temperature_mean": None},
            {"date": "2026-10-03", "temperature_mean": "bad"},
            {"date": "2026-10-04", "temperature_mean": "nan"},
            {"date": "2026-10-05", "temperature_mean": "inf"},
            {"date": "2026-10-06", "temperature_mean": True},
            {"date": "2026-10-01", "temperature_mean": "12"},
            {"date": "2026-10-15T00:00:00+00:00", "temperature_mean": 14},
            {"date": "2026-10-16", "temperature_mean": 0},
        ]
    )
    assert result == {
        "season_start": "2026-10-01",
        "season_hgt": 28,
        "days_counted": 3,
        "today_hgt": 20,
    }


def test_no_valid_days_does_not_invent_observed_heating_days(freezer):
    freezer.move_to("2026-02-01T12:00:00+00:00")
    assert compute_season_hgt([]) == {
        "season_start": "2025-10-01",
        "season_hgt": 0,
        "days_counted": 0,
        "today_hgt": 0,
    }
