"""Regression tests for published MeteoSwiss alerts that start later."""

from __future__ import annotations

from datetime import datetime, timezone

from custom_components.meteoswiss.alerts import WeatherAlert
from custom_components.meteoswiss.binary_sensor import (
    ALERT_SENSOR_DESCRIPTIONS,
    _alert_state_attributes,
)


def _alert(
    alert_id: str,
    *,
    valid_from: datetime | None,
    valid_to: datetime | None,
    outlook: bool = False,
) -> WeatherAlert:
    """Create a compact weather alert for timing tests."""
    return WeatherAlert(
        alert_id=alert_id,
        warn_type=4,
        warn_type_name="Wind",
        warn_level=2,
        warn_level_name="Level 2",
        title=alert_id,
        description="",
        valid_from=valid_from,
        valid_to=valid_to,
        outlook=outlook,
    )


def _freeze_now(monkeypatch) -> None:
    """Freeze alert timing at 2026-09-05 08:00 UTC."""
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            value = cls(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
            return value if tz is None else value.astimezone(tz)

    monkeypatch.setattr(
        "custom_components.meteoswiss.alerts.datetime",
        FrozenDateTime,
    )


def test_future_published_alert_is_upcoming_but_not_active(monkeypatch) -> None:
    """A warning may be visible before its validity window starts."""
    _freeze_now(monkeypatch)
    alert = _alert(
        "future",
        valid_from=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
    )

    assert alert.is_upcoming() is True
    assert alert.is_active() is False
    assert alert.to_sensor_state() == "upcoming"


def test_active_expired_and_outlook_alerts_are_not_upcoming(monkeypatch) -> None:
    """Upcoming must mean a real published warning with a future start."""
    _freeze_now(monkeypatch)

    active = _alert(
        "active",
        valid_from=datetime(2026, 9, 5, 7, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 9, 0, tzinfo=timezone.utc),
    )
    expired = _alert(
        "expired",
        valid_from=datetime(2026, 9, 5, 6, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 7, 0, tzinfo=timezone.utc),
    )
    outlook = _alert(
        "outlook",
        valid_from=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
        outlook=True,
    )

    assert active.is_upcoming() is False
    assert expired.is_upcoming() is False
    assert outlook.is_upcoming() is False


def test_alert_attributes_keep_active_and_upcoming_separate(monkeypatch) -> None:
    """Entity attributes expose future alerts without changing active alerts."""
    _freeze_now(monkeypatch)

    active = _alert(
        "active",
        valid_from=datetime(2026, 9, 5, 7, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 9, 0, tzinfo=timezone.utc),
    )
    later = _alert(
        "later",
        valid_from=datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 15, 0, tzinfo=timezone.utc),
    )
    next_alert = _alert(
        "next",
        valid_from=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
        valid_to=datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc),
    )

    attrs = _alert_state_attributes([later, active, next_alert])

    assert attrs["active_alerts_count"] == 1
    assert [item["alert_id"] for item in attrs["alerts"]] == ["active"]
    assert attrs["upcoming_alerts_count"] == 2
    assert [item["alert_id"] for item in attrs["upcoming_alerts"]] == [
        "next",
        "later",
    ]
    assert attrs["next_alert_start"] == "2026-09-05T10:00:00+00:00"


def test_upcoming_binary_sensor_description_exists() -> None:
    """The integration exposes a dedicated binary sensor for advance warning."""
    description = next(
        item for item in ALERT_SENSOR_DESCRIPTIONS if item.key == "upcoming_alert"
    )

    assert description.alert_timing == "upcoming"
    assert description.translation_key == "upcoming_alert"
