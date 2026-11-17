"""Registered warning states follow published validity without another fetch."""

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.components.binary_sensor import DATA_COMPONENT
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from ha_helpers import MockConfigEntry, async_fire_time_changed

from custom_components.meteoswiss.alerts import WeatherAlert
from custom_components.meteoswiss.binary_sensor import ALERT_SENSOR_DESCRIPTIONS
from custom_components.meteoswiss import binary_sensor as warning_platform
from custom_components.meteoswiss.const import DOMAIN

NOW = datetime(2026, 11, 17, 12, tzinfo=UTC)
START = NOW + timedelta(minutes=1)
END = NOW + timedelta(minutes=2)


def alert(alert_id="published", *, start=START, end=END, level=3, outlook=False):
    return WeatherAlert(
        alert_id=alert_id,
        warn_type=0,
        warn_type_name="Wind",
        warn_level=level,
        warn_level_name=f"Level {level}",
        title=alert_id,
        description="",
        valid_from=start,
        valid_to=end,
        outlook=outlook,
    )


@pytest.fixture
async def installed_warnings(hass, enable_custom_integrations, freezer):
    """Keep native setup/platform/unload, replacing only external source work."""
    freezer.move_to(NOW)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "data_source": "meteoswiss",
        },
        pref_disable_polling=True,
    )
    entry.add_to_hass(hass)
    with ExitStack() as stack:
        stack.enter_context(patch(
            "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
            return_value={},
        ))
        mocks = {}
        for name, data in {
            "MeteoSwissDataUpdateCoordinator": {"temperature": 12},
            "MeteoSwissStationConditionCoordinator": {},
            "MeteoSwissForecastCoordinator": [],
            "MeteoSwissAlertsCoordinator": [alert()],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            mocks[name] = stack.enter_context(patch(
                f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                return_value=data,
            ))
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        ids = {
            description.key: registry.async_get_entity_id(
                "binary_sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{description.key}"
            )
            for description in ALERT_SENSOR_DESCRIPTIONS
        }
        assert all(ids.values())
        entities = {
            key: hass.data[DATA_COMPONENT].get_entity(entity_id)
            for key, entity_id in ids.items()
        }
        yield entry, ids, entities, mocks["MeteoSwissAlertsCoordinator"]
        if entry.state is ConfigEntryState.LOADED:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()


async def advance(hass, freezer, instant):
    freezer.move_to(instant)
    async_fire_time_changed(hass, instant)
    await hass.async_block_till_done()


def states(hass, ids):
    return {key: hass.states.get(entity_id).state for key, entity_id in ids.items()}


async def test_published_start_and_inclusive_end_update_registered_states_without_fetch(
    hass, installed_warnings, freezer
):
    entry, ids, _, source_mock = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    calls = source_mock.await_count
    assert source._unsub_refresh is None
    assert states(hass, ids) == {
        "any_alert": "off", "critical_alert": "off", "upcoming_alert": "on"
    }
    await advance(hass, freezer, START)
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "on", "upcoming_alert": "off"
    }
    attrs = hass.states.get(ids["any_alert"]).attributes
    assert attrs["active_alerts_count"] == 1
    assert attrs["upcoming_alerts_count"] == 0
    assert attrs["next_alert_start"] is None
    await advance(hass, freezer, END)
    assert hass.states.get(ids["any_alert"]).state == "on"
    await advance(hass, freezer, END + timedelta(microseconds=1))
    assert set(states(hass, ids).values()) == {"off"}
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 0
    assert source_mock.await_count == calls


async def test_overlapping_windows_update_each_state_and_shared_attributes(
    hass, installed_warnings, freezer
):
    entry, ids, entities, source_mock = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    source.async_set_updated_data([
        alert("first", start=None, end=END, level=2),
        alert("critical", start=START, end=NOW + timedelta(minutes=3)),
        alert("last", start=END, end=NOW + timedelta(minutes=4), level=2),
        alert("outlook", start=NOW + timedelta(seconds=30), outlook=True),
    ])
    await hass.async_block_till_done()
    calls = source_mock.await_count
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "off", "upcoming_alert": "on"
    }
    for entity_id in ids.values():
        attrs = hass.states.get(entity_id).attributes
        assert (attrs["active_alerts_count"], attrs["upcoming_alerts_count"]) == (1, 2)
        assert attrs["next_alert_start"] == START.isoformat()
    await advance(hass, freezer, START)
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "on", "upcoming_alert": "on"
    }
    attrs = hass.states.get(ids["any_alert"]).attributes
    assert (attrs["active_alerts_count"], attrs["upcoming_alerts_count"]) == (2, 1)
    assert attrs["next_alert_start"] == END.isoformat()
    await advance(hass, freezer, END)
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 3
    assert hass.states.get(ids["upcoming_alert"]).state == "off"
    await advance(hass, freezer, END + timedelta(microseconds=1))
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 2
    await advance(hass, freezer, NOW + timedelta(minutes=3, microseconds=1))
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "off", "upcoming_alert": "off"
    }
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 1
    await advance(hass, freezer, NOW + timedelta(minutes=4, microseconds=1))
    assert set(states(hass, ids).values()) == {"off"}
    assert all(entity._cancel_timer is None for entity in entities.values())
    assert source_mock.await_count == calls


@pytest.mark.parametrize("data,expected", [
    (None, "unknown"),
    ([], "off"),
    ([alert(outlook=True)], "off"),
    ([alert(start=None, end=NOW - timedelta(seconds=1))], "off"),
])
async def test_missing_empty_outlook_and_expired_data_cancel_boundary_clock(
    hass, installed_warnings, freezer, data, expected
):
    entry, ids, entities, source_mock = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    source.async_set_updated_data(data)
    await hass.async_block_till_done()
    assert set(states(hass, ids).values()) == {expected}
    assert all(entity._cancel_timer is None for entity in entities.values())
    saved = {entity_id: hass.states.get(entity_id) for entity_id in ids.values()}
    calls = source_mock.await_count
    await advance(hass, freezer, END + timedelta(seconds=1))
    assert {entity_id: hass.states.get(entity_id) for entity_id in ids.values()} == saved
    assert source_mock.await_count == calls


async def test_missing_bounds_keep_existing_semantics_and_only_known_boundaries(
    hass, installed_warnings, freezer
):
    entry, ids, entities, _ = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    source.async_set_updated_data([
        alert("missing-start", start=None, end=START, level=2),
        alert("missing-end", start=START, end=None),
    ])
    await hass.async_block_till_done()
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "off", "upcoming_alert": "on"
    }
    await advance(hass, freezer, START)
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 2
    await advance(hass, freezer, START + timedelta(microseconds=1))
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "on", "upcoming_alert": "off"
    }
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 1
    assert all(entity._cancel_timer is None for entity in entities.values())
    source.async_set_updated_data([
        alert("unbounded", start=None, end=None),
        alert("last-instant", start=None, end=datetime.max.replace(tzinfo=UTC)),
    ])
    await hass.async_block_till_done()
    assert hass.states.get(ids["any_alert"]).attributes["active_alerts_count"] == 2
    assert all(entity._cancel_timer is None for entity in entities.values())


async def test_source_failure_cancels_retained_window_and_recovery_rearms_clock(
    hass, installed_warnings, freezer
):
    entry, ids, entities, source_mock = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    source.async_set_update_error(UpdateFailed("warnings unavailable"))
    await hass.async_block_till_done()
    assert set(states(hass, ids).values()) == {"unavailable"}
    assert all(entity._cancel_timer is None for entity in entities.values())
    saved = {entity_id: hass.states.get(entity_id) for entity_id in ids.values()}
    calls = source_mock.await_count
    await advance(hass, freezer, START)
    assert {entity_id: hass.states.get(entity_id) for entity_id in ids.values()} == saved
    source.async_set_updated_data([alert("recovered", start=END)])
    await hass.async_block_till_done()
    assert all(entity._cancel_timer is not None for entity in entities.values())
    assert states(hass, ids) == {
        "any_alert": "off", "critical_alert": "off", "upcoming_alert": "on"
    }
    await advance(hass, freezer, END)
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "on", "upcoming_alert": "off"
    }
    await advance(hass, freezer, END + timedelta(microseconds=1))
    assert set(states(hass, ids).values()) == {"off"}
    assert source_mock.await_count == calls


async def test_replaced_snapshot_rejects_a_canceled_already_queued_callback(
    hass, installed_warnings, freezer
):
    entry, ids, entities, source_mock = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    with patch.object(warning_platform, "async_track_point_in_utc_time", wraps=
                      warning_platform.async_track_point_in_utc_time) as track:
        source.async_set_updated_data([alert("old")])
        await hass.async_block_till_done()
        queued_actions = [call.args[1] for call in track.call_args_list]
        assert len(queued_actions) == 3
        source.async_set_updated_data([
            alert("replacement", start=END, end=NOW + timedelta(minutes=3))
        ])
        await hass.async_block_till_done()
        active_timers = {key: entity._cancel_timer for key, entity in entities.items()}
        track.reset_mock()
        with ExitStack() as stack:
            writes = [stack.enter_context(patch.object(entity, "async_write_ha_state"))
                      for entity in entities.values()]
            for action in queued_actions:
                action(START)
            assert all(not write.called for write in writes)
        track.assert_not_called()
        assert {key: entity._cancel_timer for key, entity in entities.items()} == active_timers
    calls = source_mock.await_count
    await advance(hass, freezer, START)
    assert states(hass, ids) == {
        "any_alert": "off", "critical_alert": "off", "upcoming_alert": "on"
    }
    await advance(hass, freezer, END)
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "on", "upcoming_alert": "off"
    }
    assert source_mock.await_count == calls


async def test_entity_removal_cancels_queued_callback_without_affecting_siblings(
    hass, installed_warnings, freezer
):
    entry, ids, entities, _ = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    removed = entities["any_alert"]
    with patch.object(warning_platform, "async_track_point_in_utc_time", wraps=
                      warning_platform.async_track_point_in_utc_time) as track:
        source.async_set_updated_data([alert("new")])
        await hass.async_block_till_done()
        action = next(call.args[1] for call in track.call_args_list
                      if call.args[1].func.__self__ is removed)
        await hass.data[DATA_COMPONENT].async_remove_entity(ids["any_alert"])
        assert removed._cancel_timer is None
        removed_state = hass.states.get(ids["any_alert"])
        assert removed_state is None or removed_state.state == "unavailable"
        track.reset_mock()
        with patch.object(removed, "async_write_ha_state") as write:
            action(START)
            write.assert_not_called()
        track.assert_not_called()
    assert len(source._listeners) == 2
    await advance(hass, freezer, START)
    assert hass.data[DATA_COMPONENT].get_entity(ids["any_alert"]) is None
    assert hass.states.get(ids["any_alert"]) == removed_state
    assert hass.states.get(ids["critical_alert"]).state == "on"
    assert hass.states.get(ids["upcoming_alert"]).state == "off"


async def test_unload_reload_retains_ids_and_old_callbacks_cannot_rearm(
    hass, installed_warnings, freezer
):
    entry, ids, entities, source_mock = installed_warnings
    source = entry.runtime_data.alerts_coordinator
    with patch.object(warning_platform, "async_track_point_in_utc_time", wraps=
                      warning_platform.async_track_point_in_utc_time) as track:
        source.async_set_updated_data([alert("before-unload")])
        await hass.async_block_till_done()
        actions = [call.args[1] for call in track.call_args_list]
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not source._listeners
        assert all(entity._cancel_timer is None for entity in entities.values())
        saved = {entity_id: hass.states.get(entity_id) for entity_id in ids.values()}
        track.reset_mock()
        with ExitStack() as stack:
            writes = [stack.enter_context(patch.object(entity, "async_write_ha_state"))
                      for entity in entities.values()]
            for action in actions:
                action(START)
            assert all(not write.called for write in writes)
        track.assert_not_called()
    calls = source_mock.await_count
    await advance(hass, freezer, NOW + timedelta(seconds=30))
    assert {entity_id: hass.states.get(entity_id) for entity_id in ids.values()} == saved
    assert source_mock.await_count == calls
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert {description.key: registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{description.key}"
    ) for description in ALERT_SENSOR_DESCRIPTIONS} == ids
    assert all(hass.data[DATA_COMPONENT].get_entity(ids[key]) is not entity
               for key, entity in entities.items())
    with ExitStack() as stack:
        writes = [stack.enter_context(patch.object(entity, "async_write_ha_state"))
                  for entity in entities.values()]
        for action in actions:
            action(START)
        assert all(not write.called for write in writes)
    calls = source_mock.await_count
    await advance(hass, freezer, START)
    assert states(hass, ids) == {
        "any_alert": "on", "critical_alert": "on", "upcoming_alert": "off"
    }
    assert source_mock.await_count == calls
