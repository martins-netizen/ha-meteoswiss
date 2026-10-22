"""Captured v3 source and distinct warning-family regression contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.meteoswiss.alerts import MeteoSwissAlertsAPI
from custom_components.meteoswiss.binary_sensor import (
    _alert_state_attributes,
)
from custom_components.meteoswiss.coordinator import MeteoSwissAlertsCoordinator
from custom_components.meteoswiss.localization import _load_warning_labels

V3_URL = "https://app-prod-ws.meteoswiss-app.ch/v3/plzDetail?plz=830200"


@pytest.fixture
def kloten_v3():
    """Public warning fields captured on 17 October 2026, not invented alerts."""
    return json.loads(
        (Path(__file__).parent / "fixtures/warnings_v3_830200.json").read_text()
    )["response"]


async def test_v3_adds_drought_without_losing_existing_forest_fire(
    hass, aioclient_mock, freezer, kloten_v3
):
    freezer.move_to("2026-10-17T06:20:09+00:00")
    aioclient_mock.get(V3_URL, json=kloten_v3)
    api = MeteoSwissAlertsAPI(async_get_clientsession(hass))

    alerts = await api.get_alerts("8302")

    assert [(a.warn_type, a.warn_level) for a in alerts] == [(12, 4), (10, 2)]
    assert [a.warn_type_name for a in alerts] == ["Drought", "Forest Fire"]
    assert alerts[0].is_active() and alerts[0].is_critical()
    assert alerts[1].is_active() and not alerts[1].is_critical()
    assert all(a.valid_to is None for a in alerts)
    assert alerts[1].alert_id == "8302_2_10_1791800094000"
    for alert, source in zip(alerts, kloten_v3["warnings"], strict=True):
        assert alert.description == source["text"]
        assert alert.valid_from.timestamp() * 1000 == source["validFrom"]
    attrs = _alert_state_attributes(alerts)
    assert attrs["active_alerts_count"] == 2
    assert sum(a["warn_level"] >= 3 for a in attrs["alerts"]) == 1
    assert attrs["upcoming_alerts"] == []
    assert len(aioclient_mock.mock_calls) == 1
    assert str(aioclient_mock.mock_calls[0][1]) == V3_URL


async def test_v3_failure_never_falls_back_to_incomplete_v1(
    hass, aioclient_mock, kloten_v3
):
    api = MeteoSwissAlertsAPI(async_get_clientsession(hass))
    api.postal_code = "8302"
    coordinator = MeteoSwissAlertsCoordinator(hass, api)
    aioclient_mock.get(V3_URL, json=kloten_v3)
    await coordinator.async_refresh()
    saved = coordinator.data
    assert coordinator.last_update_success and saved
    aioclient_mock.clear_requests()
    # A permanent v3 failure must not select the otherwise available old feed.
    aioclient_mock.get(V3_URL, status=404)
    aioclient_mock.get(
        "https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz=830200",
        json={"warnings": [kloten_v3["warnings"][1]]},
    )
    await coordinator.async_refresh()
    assert coordinator.data == saved
    assert coordinator.last_update_success is False
    assert len(aioclient_mock.mock_calls) == 1
    assert str(aioclient_mock.mock_calls[0][1]) == V3_URL
    aioclient_mock.clear_requests()
    aioclient_mock.get(V3_URL, json={"warnings": []})
    await coordinator.async_refresh()
    assert coordinator.last_update_success and coordinator.data == []


def test_thaw_is_ready_but_never_inferred_from_other_warnings(kloten_v3):
    api = MeteoSwissAlertsAPI()
    assert all(a.warn_type != 6 for a in api._parse_alerts(kloten_v3, "8302"))
    # Synthetic contract: the app catalogue includes this type; live issuance
    # was not observed. Recognize it only when the provider actually sends it.
    alert = api._parse_alerts(
        {"warnings": [{"warnType": 6, "warnLevel": 3, "text": "Thaw detail"}]},
        "8302",
    )[0]
    assert alert.warn_type_name == "Thaw"
    assert alert.description == "Thaw detail"
    assert alert.is_critical()
    labels = _load_warning_labels()
    assert {lang: labels[lang]["types"]["6"] for lang in labels} == {
        "de": "Tauwetter", "en": "Thaw", "fr": "Dégel", "it": "Disgelo"
    }


@pytest.mark.parametrize(
    "code,name,detail",
    [
        (0, "Wind", "Sturm: starke Böen"),
        (1, "Thunderstorm", "Gewitter mit Hagel"),
        (2, "Rain", "Starkregen: grosse Niederschlagsmengen"),
        (3, "Snow", "Schneefall: grosse Neuschneemengen"),
    ],
)
@pytest.mark.parametrize("level", [2, 4])
def test_weather_family_is_separate_from_severity_and_event_text(
    freezer, code, name, detail, level
):
    freezer.move_to("2026-10-17T06:20:09+00:00")
    alerts = MeteoSwissAlertsAPI()._parse_alerts(
        {"warnings": [
            {"warnType": code, "warnLevel": level, "text": detail,
             "validFrom": 1792214400000, "validTo": 1792220400000},
            {"warnType": code, "warnLevel": level, "text": detail,
             "validFrom": 1792224000000},
        ]}, "8302"
    )
    active, upcoming = alerts
    assert active.warn_type_name == upcoming.warn_type_name == name
    assert active.description == upcoming.description == detail
    assert active.to_sensor_state() == ("warning" if level == 2 else "critical")
    assert upcoming.to_sensor_state() == "upcoming"
    attrs = _alert_state_attributes(alerts)
    assert attrs["alerts"][0]["warn_type"] == code
    assert attrs["upcoming_alerts"][0]["description"] == detail
    assert sum(a["warn_level"] >= 3 for a in attrs["alerts"]) == (1 if level == 4 else 0)
