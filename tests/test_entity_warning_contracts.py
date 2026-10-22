"""Warning validation/privacy and registered sensor lifecycle contracts."""

from __future__ import annotations

import asyncio
import logging
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.alerts import (
    METEOSWISS_APP_API_URL,
    MeteoSwissAlertsAPI,
    WeatherAlert,
)
from custom_components.meteoswiss.binary_sensor import (
    ALERT_SENSOR_DESCRIPTIONS,
    MeteoSwissAlertsBinarySensor,
    MeteoSwissAlertsBinarySensorDescription,
)
from custom_components.meteoswiss.coordinator import MeteoSwissAlertsCoordinator
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.pollen_sensor import async_setup_entry as setup_pollen
from custom_components.meteoswiss.sensor import (
    SENSOR_DESCRIPTIONS,
    MeteoSwissHeatingDegreeDaysSensor,
    _daily_mean_for_date,
    _remove_legacy_season_hgt_entity,
)
from custom_components.meteoswiss.sensor import (
    async_setup_entry as setup_sensors,
)

NOW = datetime(2026, 10, 16, 10, tzinfo=UTC)


@pytest.fixture(autouse=True)
def fixed_clock(freezer):
    freezer.move_to(NOW)


def warning(**values):
    return {"warnType": 5, "warnLevel": 2, "text": "Ground frost", **values}


def test_hgt_reads_existing_forecast_before_next_update(hass):
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="hgt",
        config_entry=MockConfigEntry(domain=DOMAIN),
    )
    coordinator.data = [{"local_date": "2026-10-16", "daily_temperature_mean": 0}]
    entity = MeteoSwissHeatingDegreeDaysSensor(
        coordinator, MockConfigEntry(domain=DOMAIN)
    )
    assert entity.native_value == 20
    assert entity.extra_state_attributes["daily_mean_temperature"] == 0


@pytest.mark.parametrize("value", [True, False, 2.8])
async def test_invalid_warning_level_is_not_coerced(hass, aioclient_mock, value):
    aioclient_mock.get(
        METEOSWISS_APP_API_URL, json={"warnings": warning(warnLevel=value)}
    )
    api = MeteoSwissAlertsAPI(async_get_clientsession(hass))
    with pytest.raises(ValueError):
        await api.get_alerts("9997")


def test_zero_warning_end_is_epoch_not_missing():
    alert = MeteoSwissAlertsAPI()._parse_alerts(
        {"warnings": warning(validTo=0)}, "9997"
    )[0]
    assert alert.valid_to == datetime(1970, 1, 1, tzinfo=UTC)
    assert alert.is_active() is False


async def test_warning_request_logs_omit_postcode_and_raw_payload(
    hass, aioclient_mock, caplog
):
    aioclient_mock.get(
        METEOSWISS_APP_API_URL,
        json={"warnings": warning(warnLevel="private_provider_marker")},
    )
    api = MeteoSwissAlertsAPI(async_get_clientsession(hass))
    with (
        caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss.alerts"),
        pytest.raises(ValueError),
    ):
        await api.get_alerts("9997")
    logs = "\n".join(
        logging.Formatter().format(record)
        for record in caplog.records
        if record.name.startswith("custom_components.meteoswiss")
    )
    assert "9997" not in logs
    assert "private_provider_marker" not in logs


@pytest.mark.parametrize(
    "fields",
    [
        {"warnLevel": 0},
        {"warnLevel": 6},
        {"warnLevel": None},
        {"warnType": True},
        {"warnType": 4.5},
        {"warnType": -1},
        {"validFrom": True},
        {"validFrom": "bad"},
        {"validFrom": float("nan")},
        {"validFrom": 1e30},
        {"validTo": False},
        {"validTo": float("inf")},
        {"validFrom": 2000, "validTo": 1000},
        {"outlook": "false"},
        {"text": {}},
    ],
)
def test_malformed_published_warning_invalidates_feed(fields):
    api = MeteoSwissAlertsAPI()
    # One good item cannot make a malformed second warning disappear.
    with pytest.raises(ValueError):
        api._parse_alerts({"warnings": [warning(), warning(**fields)]}, "9997")


def test_warning_bounds_are_utc_and_unknown_types_remain_visible():
    alert = MeteoSwissAlertsAPI()._parse_alerts(
        {"warnings": warning(warnType="99", warnLevel="3", validFrom=0)}, "9997"
    )[0]
    assert alert.alert_id == "9997_3_99_0"
    assert alert.warn_type_name == "Unknown (99)"
    assert alert.is_critical()
    assert alert.valid_from == datetime(1970, 1, 1, tzinfo=UTC)
    assert alert.to_dict()["valid_from"] == "1970-01-01T00:00:00+00:00"
    assert alert.to_dict()["valid_to"] is None


@pytest.mark.parametrize(
    "start,end,outlook,expected",
    [
        (None, None, False, "warning"),
        (-1, 1, False, "warning"),
        (1, 2, False, "upcoming"),
        (-2, -1, False, "clear"),
        (1, 2, True, "outlook"),
    ],
)
def test_warning_state_respects_time_and_outlook(start, end, outlook, expected):
    alert = WeatherAlert(
        "id",
        5,
        "Ground Frost",
        2,
        "Moderate",
        "title",
        "",
        valid_from=NOW + timedelta(hours=start) if start is not None else None,
        valid_to=NOW + timedelta(hours=end) if end is not None else None,
        outlook=outlook,
    )
    assert alert.to_sensor_state() == expected
    if outlook:
        assert alert.is_active() is False
    alert.warn_level = 3
    assert alert.to_sensor_state() == (
        "critical" if expected == "warning" else expected
    )


def test_impossible_future_window_is_never_upcoming():
    alert = WeatherAlert(
        "id",
        5,
        "Ground Frost",
        2,
        "Moderate",
        "title",
        "",
        valid_from=NOW + timedelta(hours=2),
        valid_to=NOW + timedelta(hours=1),
    )
    assert not alert.is_upcoming()


async def test_warning_session_lifetime_missing_input_and_total_timeout(hass, freezer):
    with pytest.raises(RuntimeError, match="No session"):
        await MeteoSwissAlertsAPI().get_alerts("9997")
    session = async_get_clientsession(hass)
    api = MeteoSwissAlertsAPI(session)
    with pytest.raises(ValueError, match="postal code"):
        await api.get_alerts("")
    await api.close()
    assert not session.closed
    with (
        patch(
            "custom_components.meteoswiss.alerts.DEFAULT_API_TIMEOUT",
            aiohttp.ClientTimeout(total=0.001),
        ),
        patch.object(api, "_fetch_and_parse_alerts", side_effect=lambda *_: None),
    ):
        # Use an actual suspended coroutine: the outer deadline must cancel it.
        async def suspended(*_):
            await asyncio.Event().wait()

        api._fetch_and_parse_alerts.side_effect = suspended
        hass.loop.call_soon(freezer.tick, 0.01)
        with pytest.raises(TimeoutError):
            await api.get_alerts("9997")
        api._fetch_and_parse_alerts.assert_awaited_once()


async def test_programming_errors_and_cancellation_remain_visible(hass):
    api = MeteoSwissAlertsAPI(async_get_clientsession(hass))
    with (
        patch.object(api, "_get_warn_type_name", side_effect=RuntimeError("bug")),
        pytest.raises(RuntimeError, match="bug"),
    ):
        api._parse_alerts({"warnings": warning()}, "9997")
    with (
        patch.object(
            api, "_fetch_and_parse_alerts", side_effect=asyncio.CancelledError
        ),
        pytest.raises(asyncio.CancelledError),
    ):
        await api.get_alerts("9997")


@pytest.mark.parametrize(
    "error",
    [
        aiohttp.ClientConnectionError("private_connection_marker"),
        ValueError("private_payload_marker"),
        UnicodeError("private_encoding_marker"),
    ],
)
async def test_warning_failure_logs_only_once_and_recovers(hass, caplog, error):
    api = SimpleNamespace(
        postal_code="9997", get_alerts=AsyncMock(return_value=[]), close=AsyncMock()
    )
    coordinator = MeteoSwissAlertsCoordinator(hass, api)
    with caplog.at_level(logging.DEBUG, logger=coordinator.logger.name):
        await coordinator.async_refresh()
        api.get_alerts.side_effect = error
        for _ in range(2):
            await coordinator.async_refresh()
        api.get_alerts.side_effect = None
        await coordinator.async_refresh()
    records = [r for r in caplog.records if r.name == coordinator.logger.name]
    logs = "\n".join(logging.Formatter().format(r) for r in records)
    assert "private_" not in logs
    assert "9997" not in logs
    assert sum(r.levelno == logging.ERROR for r in records) == 1
    assert "Fetching" in logs and "recovered" in logs
    assert coordinator.last_update_success and coordinator.data == []
    await coordinator.async_close()
    api.close.assert_awaited_once()


@pytest.mark.parametrize("code", [0, 4])
def test_warning_type_and_level_filters_do_not_suppress_other_entities(hass, code):
    coordinator = MeteoSwissAlertsCoordinator(hass, SimpleNamespace())
    entry = MockConfigEntry(domain=DOMAIN)
    entity = MeteoSwissAlertsBinarySensor(
        coordinator,
        entry,
        MeteoSwissAlertsBinarySensorDescription(
            key="test", warn_level=3, warn_type=code
        ),
        "9997",
    )
    assert entity.is_on is None
    coordinator.data = []
    assert entity.is_on is False
    api = MeteoSwissAlertsAPI()
    for fields in [
        {"warnType": code, "validFrom": (NOW.timestamp() + 3600) * 1000},
        {"warnType": code, "warnLevel": 2},
        {"warnType": 5, "warnLevel": 3},
    ]:
        coordinator.data = api._parse_alerts({"warnings": warning(**fields)}, "9997")
        assert entity.is_on is False
    coordinator.data = api._parse_alerts(
        {"warnings": warning(warnType=code, warnLevel=3)}, "9997"
    )
    assert entity.is_on is True


@pytest.fixture
async def installed_entities(hass, enable_custom_integrations, aioclient_mock, caplog):
    caplog.set_level(logging.DEBUG, logger="custom_components.meteoswiss")
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "private_station_marker",
            "postal_code": "9997",
        },
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(METEOSWISS_APP_API_URL, json={"warnings": []})
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {
                "temperature": 0,
                "precipitation": 0.2,
                "last_update": NOW.isoformat(),
            },
            "forecast_coordinator.MeteoSwissForecastCoordinator": [
                {"local_date": "2026-10-16", "daily_temperature_mean": 0}
            ],
            "pollen_coordinator_openmeteo.OpenMeteoPollenCoordinator": {},
            "pollen_meteoswiss.MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        yield entry
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


async def test_registered_alerts_fail_recover_and_keep_identity(
    hass, installed_entities, aioclient_mock
):
    entry = installed_entities
    registry = er.async_get(hass)
    entity_ids = {
        description.key: registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{description.key}"
        )
        for description in ALERT_SENSOR_DESCRIPTIONS
    }
    assert all(entity_ids.values())
    coordinator = entry.runtime_data.alerts_coordinator
    assert all(hass.states.get(eid).state == "off" for eid in entity_ids.values())
    now_ms = NOW.timestamp() * 1000
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        METEOSWISS_APP_API_URL,
        json={
            "warnings": [
                warning(warnLevel=3, validFrom=now_ms - 1000, validTo=now_ms + 1000),
                warning(validFrom=now_ms + 3600000, validTo=now_ms + 7200000),
                warning(outlook=True),
            ]
        },
    )
    await coordinator.async_refresh()
    assert all(hass.states.get(eid).state == "on" for eid in entity_ids.values())
    attrs = hass.states.get(entity_ids["any_alert"]).attributes
    assert attrs["active_alerts_count"] == 1
    assert attrs["upcoming_alerts_count"] == 1
    saved = coordinator.data
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        METEOSWISS_APP_API_URL, json={"warnings": warning(warnLevel=True)}
    )
    await coordinator.async_refresh()
    assert coordinator.data == saved
    assert all(
        hass.states.get(eid).state == "unavailable" for eid in entity_ids.values()
    )
    assert coordinator.last_update_success is False
    aioclient_mock.clear_requests()
    aioclient_mock.get(METEOSWISS_APP_API_URL, json={"warnings": []})
    await coordinator.async_refresh()
    assert all(hass.states.get(eid).state == "off" for eid in entity_ids.values())
    assert entity_ids == {
        key: registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{key}"
        )
        for key in entity_ids
    }


async def test_registered_measurement_empty_data_and_hgt_date_rollover(
    hass, installed_entities, freezer
):
    entry = installed_entities
    registry = er.async_get(hass)

    def entity_id(key):
        return registry.async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{key}"
        )

    temperature, hgt = entity_id("temperature"), entity_id("heating_degree_days")
    assert hass.states.get(temperature).state == "0"
    assert hass.states.get(hgt).state == "20.0"
    entry.runtime_data.coordinator.async_set_updated_data({})
    assert hass.states.get(temperature).state == "unknown"
    assert hass.states.get(temperature).attributes["measurement_time"] is None
    forecast = entry.runtime_data.forecast_coordinator
    forecast.async_set_updated_data([])
    assert hass.states.get(hgt).state == "unknown"
    forecast.async_set_updated_data(
        [{"local_date": "2026-10-16", "daily_temperature_mean": 12}]
    )
    assert hass.states.get(hgt).state == "8.0"
    freezer.move_to("2026-10-16T22:10:00+00:00")
    forecast.async_set_updated_data(
        [
            {"local_date": "2026-10-16", "daily_temperature_mean": 12},
            {"local_date": "2026-10-17", "daily_temperature_mean": 0},
        ]
    )
    assert hass.states.get(hgt).state == "20.0"
    forecast.async_set_updated_data(
        [{"local_date": "2026-10-17", "daily_temperature_mean": None}]
    )
    assert hass.states.get(hgt).state == "unknown"
    assert hass.states.get(hgt).attributes["method"] == "HGT 12/20"


@pytest.mark.parametrize("value", [True, False, "bad", "nan", float("inf"), None])
def test_hgt_rejects_invalid_means_without_losing_other_day(value):
    rows = [
        {"datetime": "bad", "daily_temperature_mean": 1},
        {"local_date": "2026-10-16", "daily_temperature_mean": value},
        {"local_date": "2026-10-17", "daily_temperature_mean": 0},
    ]
    assert _daily_mean_for_date(rows, "2026-10-16") is None
    assert _daily_mean_for_date(rows, "2026-10-17") == 0


async def test_optional_sensor_platforms_skip_missing_families(hass, caplog):
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="sensor",
        config_entry=MockConfigEntry(domain=DOMAIN),
    )
    entry = MockConfigEntry(domain=DOMAIN)
    entry.runtime_data = SimpleNamespace(
        coordinator=coordinator,
        pollen_coordinator=None,
        forecast_coordinator=None,
        meteoswiss_pollen_coordinator=None,
    )
    hass.data[DOMAIN] = {
        "stations_map_sensor_added": True,
        "cache_stats_sensor_added": True,
    }
    entities = []
    await setup_sensors(hass, entry, entities.extend)
    assert len(entities) == len(SENSOR_DESCRIPTIONS)
    assert all(entity.native_value is None for entity in entities)
    await setup_pollen(hass, entry, entities.extend)
    assert len(entities) == len(SENSOR_DESCRIPTIONS)
    assert "Pollen coordinator not found" in caplog.text
    entry.runtime_data.pollen_coordinator = coordinator
    await setup_pollen(hass, entry, entities.extend)
    assert len(entities) == len(SENSOR_DESCRIPTIONS) + 5


async def test_legacy_season_cleanup_preserves_current_hgt_identity(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    legacy = registry.async_get_or_create(
        "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_season_hgt", config_entry=entry
    )
    current = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{DOMAIN}_{entry.entry_id}_heating_degree_days",
        config_entry=entry,
    )
    _remove_legacy_season_hgt_entity(hass, entry)
    assert registry.async_get(legacy.entity_id) is None
    assert registry.async_get(current.entity_id) == current
    _remove_legacy_season_hgt_entity(hass, entry)


async def test_entry_platform_logs_omit_location(hass, installed_entities, caplog):
    logs = "\n".join(
        logging.Formatter().format(record)
        for record in caplog.records
        if record.name.startswith("custom_components.meteoswiss")
    )
    assert "private_station_marker" not in logs
    assert "9997" not in logs


async def test_failed_unload_preserves_shared_diagnostic_ownership(hass):
    from custom_components.meteoswiss import async_unload_entry

    entry = MockConfigEntry(domain=DOMAIN)
    ownership = {
        "diagnostic_owner": entry.entry_id,
        "stations_map_sensor_added": True,
        "cache_stats_sensor_added": True,
    }
    hass.data[DOMAIN] = dict(ownership)
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=False
    ):
        assert await async_unload_entry(hass, entry) is False
    assert hass.data[DOMAIN] == ownership


@pytest.mark.parametrize("family", ["pollen", "measured"])
async def test_optional_source_exception_chains_are_private(hass, caplog, family):
    from custom_components.meteoswiss.cache import clear_all_caches
    from custom_components.meteoswiss.pollen_coordinator_openmeteo import (
        OpenMeteoPollenCoordinator,
    )
    from custom_components.meteoswiss.pollen_meteoswiss import (
        MeteoSwissPollenCoordinator,
    )

    clear_all_caches()
    if family == "pollen":
        source = OpenMeteoPollenCoordinator(hass, 47.451234, 8.561234)
        method = "_async_fetch_data"
    else:
        source = MeteoSwissPollenCoordinator(hass, "PLZ")
        method = "_async_fetch_csv"
    with (
        patch.object(
            source,
            method,
            side_effect=aiohttp.ClientConnectionError(
                "private_source_marker latitude=47.451234"
            ),
        ),
        caplog.at_level(logging.DEBUG, logger=source.logger.name),
    ):
        await source.async_refresh()
        await source.async_refresh()
    records = [record for record in caplog.records if record.name == source.logger.name]
    logs = "\n".join(logging.Formatter().format(record) for record in records)
    assert "private_source_marker" not in logs
    assert "latitude=" not in logs
    assert sum(record.levelno == logging.ERROR for record in records) == 1
    clear_all_caches()
