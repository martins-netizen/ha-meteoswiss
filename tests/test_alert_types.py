"""Regression tests for MeteoSwiss warning type names."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from custom_components.meteoswiss.alerts import MeteoSwissAlertsAPI
from custom_components.meteoswiss.binary_sensor import _alert_state_attributes
from custom_components.meteoswiss.localization import _load_warning_labels


@pytest.mark.parametrize(
    "code,name,de",
    [
        (0, "Wind", "Wind"),
        (1, "Thunderstorm", "Gewitter"),
        (2, "Rain", "Regen"),
        (3, "Snow", "Schnee"),
        (4, "Slippery Roads", "Strassenglätte"),
        (5, "Ground Frost", "Bodenfrost"),
        (7, "Heat", "Hitze"),
        (8, "Avalanches", "Lawinen"),
        (9, "Earthquakes", "Erdbeben"),
        (10, "Forest Fire", "Waldbrand"),
        (11, "Flood", "Hochwasser"),
        (12, "Drought", "Trockenheit"),
    ],
)
def test_proposed_warning_codes_and_all_languages_are_consistent(code, name, de):
    """Check candidate consistency, not external semantic proof of the numbers."""
    alert = MeteoSwissAlertsAPI()._parse_alerts(
        {"warnings": {"warnType": code, "warnLevel": 2}}, "8302"
    )[0]
    assert alert.warn_type == code
    assert alert.warn_type_name == name
    labels = _load_warning_labels()
    assert labels["de"]["types"][str(code)] == de
    for language in ("de", "en", "fr", "it"):
        assert labels[language]["types"][str(code)]


@pytest.fixture
def ground_frost_warning() -> dict:
    """Use fields observed in the public App API on 2026-10-11.

    Source: https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz=830200
    The warning is valid on 2026-10-12 from 00:00 to 06:00 UTC.
    """
    return {
        "warnType": 5,
        "warnLevel": 2,
        "text": "Lowest temperatures near ground: 0 to -4 degrees (moderate ground frost)",
        "validFrom": 1791763200000,
        "validTo": 1791784800000,
        "outlook": False,
    }


@pytest.mark.parametrize("as_list", [False, True])
def test_parse_ground_frost_warning(ground_frost_warning, as_list) -> None:
    """Recognize ground frost in both supported warning response formats."""
    warnings = [ground_frost_warning] if as_list else ground_frost_warning

    alerts = MeteoSwissAlertsAPI()._parse_alerts({"warnings": warnings}, "8302")

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.warn_type == 5
    assert alert.warn_type_name == "Ground Frost"
    assert alert.title == "Ground Frost - Level 2 - Moderate danger"
    assert alert.warn_level == 2
    assert alert.is_critical() is False
    assert alert.description == ground_frost_warning["text"]
    assert alert.alert_id == "8302_2_5_1791763200000"
    assert alert.valid_from == datetime(2026, 10, 12, tzinfo=UTC)
    assert alert.valid_to == datetime(2026, 10, 12, 6, tzinfo=UTC)
    assert alert.outlook is False


@pytest.mark.parametrize(
    ("hour", "attribute", "sensor_state"),
    [(23, "upcoming_alerts", "upcoming"), (1, "alerts", "warning")],
)
def test_ground_frost_name_reaches_alert_attributes(
    ground_frost_warning, monkeypatch, hour, attribute, sensor_state
) -> None:
    """Expose the name in upcoming and active dashboard attributes."""

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            day = 11 if hour == 23 else 12
            value = cls(2026, 10, day, hour, tzinfo=UTC)
            return value if tz is None else value.astimezone(tz)

    monkeypatch.setattr("custom_components.meteoswiss.alerts.datetime", FrozenDateTime)
    alerts = MeteoSwissAlertsAPI()._parse_alerts(
        {"warnings": [ground_frost_warning]}, "8302"
    )

    attrs = _alert_state_attributes(alerts)

    assert len(attrs[attribute]) == 1
    assert attrs[attribute][0]["warn_type_name"] == "Ground Frost"
    assert attrs[attribute][0]["title"] == "Ground Frost - Level 2 - Moderate danger"
    assert attrs[attribute][0]["warn_level"] == 2
    assert attrs[attribute][0]["valid_from"] == "2026-10-12T00:00:00+00:00"
    assert attrs[attribute][0]["valid_to"] == "2026-10-12T06:00:00+00:00"
    other_attribute = "alerts" if attribute == "upcoming_alerts" else "upcoming_alerts"
    assert attrs[other_attribute] == []
    assert alerts[0].to_sensor_state() == sensor_state


@pytest.mark.parametrize("code", [6, 99])
def test_parse_unrecognized_warning_type(ground_frost_warning, code) -> None:
    """Keep a genuinely unknown warning visible with its numeric type."""
    warning = {**ground_frost_warning, "warnType": code}

    alerts = MeteoSwissAlertsAPI()._parse_alerts({"warnings": [warning]}, "8302")

    assert len(alerts) == 1
    assert alerts[0].warn_type == code
    assert alerts[0].warn_type_name == f"Unknown ({code})"
    assert alerts[0].title == f"Unknown ({code}) - Level 2 - Moderate danger"
    assert alerts[0].warn_level == 2
