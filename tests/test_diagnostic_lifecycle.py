"""Native multi-entry ownership, retained identity and failure boundaries."""

from contextlib import ExitStack
import asyncio
from datetime import UTC, datetime, timedelta
from functools import partial
from unittest.mock import Mock, patch

import attr
import pytest
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.config_entries import ConfigEntryDisabler, ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component
from homeassistant.exceptions import HomeAssistantError
from ha_helpers import async_wait_recording_done

from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss import PLATFORMS
from custom_components.meteoswiss.diagnostic_lifecycle import DATA_SHARED_DIAGNOSTICS
from custom_components.meteoswiss.repair_issues import SHARED_DIAGNOSTICS_BLOCKED
from test_diagnostic_defaults import (
    DIAGNOSTICS, config_entry, diagnostic_entries, quiet_sources,
)

DISABLED = [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION]


def entity_snapshot(entity):
    return (entity.id, entity.entity_id, entity.unique_id, entity.device_id,
            entity.name, entity.icon, entity.aliases, entity.area_id,
            entity.hidden_by, entity.options, entity.labels, entity.disabled_by)


def device_snapshot(device):
    return (device.id, device.identifiers, device.name_by_user, device.area_id,
            device.labels, device.disabled_by)


def seed(hass, entry, disabled, device_disabled=None):
    entities, devices = er.async_get(hass), dr.async_get(hass)
    area = ar.async_get(hass).async_create("Weather technical")
    label = lr.async_get(hass).async_create("Weather diagnostics")
    for key in DIAGNOSTICS:
        device = devices.async_get_or_create(
            config_entry_id=entry.entry_id, identifiers={(DOMAIN, key)},
            name="MeteoSwiss " + key, manufacturer="MeteoSwiss",
        )
        devices.async_update_device(device.id, name_by_user="My " + key,
            area_id=area.id, labels={label.label_id}, disabled_by=device_disabled)
        entity = entities.async_get_or_create(
            "sensor", DOMAIN, f"{DOMAIN}_{key}", config_entry=entry,
            device_id=device.id, suggested_object_id="retained_" + key,
            disabled_by=disabled,
        )
        entities.async_update_entity(entity.entity_id, name="Personal " + key,
            icon="mdi:star", aliases={"Alias " + key}, area_id=area.id,
            hidden_by=er.RegistryEntryHider.USER, labels={label.label_id})
        entities.async_update_entity_options(entity.entity_id, "sensor", {"display_precision": 1})


async def pair(hass, source, disabled, reverse=False):
    assert await async_setup_component(hass, DOMAIN, {})
    first = config_entry(hass, source)
    second = config_entry(hass, "openmeteo" if source == "meteoswiss" else "meteoswiss")
    seed(hass, first, disabled)
    initial = [entity_snapshot(entity) for entity in diagnostic_entries(hass)]
    devices = [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
               for entity in diagnostic_entries(hass)]
    for entry in ((second, first) if reverse else (first, second)):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return first, second, initial, devices


def assert_kept(hass, owner, entities, devices, disabled):
    shared = hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS]
    assert shared.owner == owner.entry_id
    current = diagnostic_entries(hass)
    assert [entity_snapshot(entity) for entity in current] == entities
    assert [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
            for entity in current] == devices
    assert all(entity.config_entry_id == owner.entry_id for entity in current)
    assert all(dr.async_get(hass).async_get(entity.device_id).config_entry_id == owner.entry_id
               for entity in current)
    for entity in current:
        assert (hass.data[DATA_COMPONENT].get_entity(entity.entity_id) is not None) is (disabled is None)
    weather = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{DOMAIN}_{owner.entry_id}_temperature")
    assert hass.states.get(weather).state == "12"
    assert owner.state is ConfigEntryState.LOADED


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled", DISABLED)
@pytest.mark.parametrize("action", ["unload", "disable", "remove", "reload"])
async def test_owner_departure_hands_off_without_peer_reload_or_lost_choices(
    hass, enable_custom_integrations, quiet_sources, source, disabled, action
):
    first, second, entities, devices = await pair(hass, source, disabled)
    peer_runtime = second.runtime_data
    with ExitStack() as stack:
        calls = [stack.enter_context(patch.object(
            coordinator, "async_refresh", wraps=coordinator.async_refresh))
                 for coordinator in (peer_runtime.coordinator, peer_runtime.forecast_coordinator,
                    peer_runtime.alerts_coordinator, peer_runtime.pollen_coordinator,
                    peer_runtime.meteoswiss_pollen_coordinator)]
        if action == "unload":
            assert await hass.config_entries.async_unload(first.entry_id)
        elif action == "disable":
            await hass.config_entries.async_set_disabled_by(first.entry_id, ConfigEntryDisabler.USER)
        elif action == "remove":
            assert (await hass.config_entries.async_remove(first.entry_id))["require_restart"] is False
        else:
            assert await hass.config_entries.async_reload(first.entry_id)
        await hass.async_block_till_done()
        assert second.runtime_data is peer_runtime
        for refresh in calls:
            refresh.assert_not_awaited()
    assert_kept(hass, second, entities, devices, disabled)
    if action == "reload":
        assert await hass.config_entries.async_unload(first.entry_id)
    assert await hass.config_entries.async_unload(second.entry_id)
    assert DATA_SHARED_DIAGNOSTICS not in hass.data[DOMAIN]


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled", DISABLED)
async def test_reverse_startup_keeps_both_registry_identities_and_personal_choices(
    hass, enable_custom_integrations, quiet_sources, source, disabled
):
    first, second, entities, devices = await pair(hass, source, disabled, reverse=True)
    assert_kept(hass, second, entities, devices, disabled)
    assert (await hass.config_entries.async_remove(first.entry_id))["require_restart"] is False
    await hass.async_block_till_done()
    assert_kept(hass, second, entities, devices, disabled)
    assert await hass.config_entries.async_unload(second.entry_id)


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled", DISABLED)
async def test_nonowner_removal_leaves_owner_and_helpers_unchanged(
    hass, enable_custom_integrations, quiet_sources, source, disabled
):
    first, second, entities, devices = await pair(hass, source, disabled)
    original = [hass.data[DATA_COMPONENT].get_entity(entity.entity_id)
                for entity in diagnostic_entries(hass)]
    assert (await hass.config_entries.async_remove(second.entry_id))["require_restart"] is False
    await hass.async_block_till_done()
    assert_kept(hass, first, entities, devices, disabled)
    assert [hass.data[DATA_COMPONENT].get_entity(entity.entity_id)
            for entity in diagnostic_entries(hass)] == original
    assert await hass.config_entries.async_unload(first.entry_id)


@pytest.mark.parametrize("disabled", DISABLED)
async def test_user_disabled_service_groups_stay_disabled_across_handoff(
    hass, enable_custom_integrations, quiet_sources, disabled
):
    assert await async_setup_component(hass, DOMAIN, {})
    first, second = config_entry(hass, "meteoswiss"), config_entry(hass, "openmeteo")
    seed(hass, first, disabled, dr.DeviceEntryDisabler.USER)
    for entry in (first, second):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    before = [entity_snapshot(entity) for entity in diagnostic_entries(hass)]
    devices_before = [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
                      for entity in diagnostic_entries(hass)]
    assert (await hass.config_entries.async_remove(first.entry_id))["require_restart"] is False
    await hass.async_block_till_done()
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices_before
    assert all(entity.config_entry_id == second.entry_id for entity in diagnostic_entries(hass))
    assert all(hass.data[DATA_COMPONENT].get_entity(entity.entity_id) is None
               for entity in diagnostic_entries(hass))
    for update in quiet_sources:
        update.assert_not_awaited()
    assert await hass.config_entries.async_unload(second.entry_id)


@pytest.mark.parametrize("departure", ["unload", "remove"])
@pytest.mark.parametrize("completion", ["success", "error", "cancel"])
async def test_pending_peer_retains_registry_before_owner_cleanup(
    hass, enable_custom_integrations, quiet_sources, departure, completion
):
    assert await async_setup_component(hass, DOMAIN, {})
    first = config_entry(hass, "meteoswiss")
    seed(hass, first, None)
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    before = [entity_snapshot(entity) for entity in diagnostic_entries(hass)]
    devices_before = [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
                      for entity in diagnostic_entries(hass)]
    second = config_entry(hass, "openmeteo")
    ready, finish = asyncio.Event(), asyncio.Event()
    forward = hass.config_entries.async_forward_entry_setups

    async def hold(entry, platforms):
        await forward(entry, platforms)
        ready.set()
        await finish.wait()
        if completion == "error":
            raise HomeAssistantError("injected setup failure")

    with patch.object(hass.config_entries, "async_forward_entry_setups", side_effect=hold):
        task = asyncio.create_task(hass.config_entries.async_setup(second.entry_id))
        await asyncio.wait_for(ready.wait(), 10)
        if departure == "unload":
            assert await hass.config_entries.async_unload(first.entry_id)
        else:
            assert (await hass.config_entries.async_remove(first.entry_id))["require_restart"] is False
        assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
        assert all(entity.config_entry_id == second.entry_id for entity in diagnostic_entries(hass))
        assert all(hass.data[DATA_COMPONENT].get_entity(entity.entity_id) is None
                   for entity in diagnostic_entries(hass))
        if completion == "cancel":
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        else:
            finish.set()
            assert await task is (completion == "success")
    await hass.async_block_till_done()
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices_before
    if completion == "success":
        assert_kept(hass, second, before, devices_before, None)
        assert await hass.config_entries.async_unload(second.entry_id)
    else:
        if departure == "unload":
            assert all(entity.config_entry_id == first.entry_id for entity in diagnostic_entries(hass))
        assert await hass.config_entries.async_unload_platforms(second, PLATFORMS)
        assert await hass.config_entries.async_reload(second.entry_id)
        await hass.async_block_till_done()
        assert_kept(hass, second, before, devices_before, None)
        assert await hass.config_entries.async_unload(second.entry_id)


async def test_loaded_peer_can_reclaim_from_pending_registration(
    hass, enable_custom_integrations, quiet_sources
):
    assert await async_setup_component(hass, DOMAIN, {})
    first = config_entry(hass, "meteoswiss")
    seed(hass, first, None)
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    before = [entity_snapshot(entity) for entity in diagnostic_entries(hass)]
    devices_before = [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
                      for entity in diagnostic_entries(hass)]
    second = config_entry(hass, "openmeteo")
    ready, finish = asyncio.Event(), asyncio.Event()
    forward = hass.config_entries.async_forward_entry_setups

    async def hold(entry, platforms):
        await forward(entry, platforms)
        if entry.entry_id == second.entry_id:
            ready.set()
            await finish.wait()

    with patch.object(hass.config_entries, "async_forward_entry_setups", side_effect=hold):
        task = asyncio.create_task(hass.config_entries.async_setup(second.entry_id))
        await asyncio.wait_for(ready.wait(), 10)
        assert await hass.config_entries.async_unload(first.entry_id)
        assert await hass.config_entries.async_reload(first.entry_id)
        await hass.async_block_till_done(wait_background_tasks=False)
        assert_kept(hass, first, before, devices_before, None)
        finish.set()
        assert await task
    await hass.async_block_till_done()
    assert_kept(hass, first, before, devices_before, None)
    assert await hass.config_entries.async_unload(second.entry_id)
    assert await hass.config_entries.async_unload(first.entry_id)


@pytest.mark.parametrize("completion", ["error", "cancel"])
async def test_failed_cold_start_never_moves_previous_registry_owner(
    hass, enable_custom_integrations, quiet_sources, completion
):
    assert await async_setup_component(hass, DOMAIN, {})
    previous = config_entry(hass, "meteoswiss")
    seed(hass, previous, er.RegistryEntryDisabler.USER)
    before = [entity_snapshot(entity) for entity in diagnostic_entries(hass)]
    second = config_entry(hass, "openmeteo")
    forward = hass.config_entries.async_forward_entry_setups

    async def fail(entry, platforms):
        await forward(entry, platforms)
        if completion == "cancel":
            raise asyncio.CancelledError
        raise HomeAssistantError("injected setup failure")

    with patch.object(hass.config_entries, "async_forward_entry_setups", side_effect=fail):
        # HA translates an internally raised CancelledError into failed setup;
        # actual caller cancellation is exercised by the pending-peer tests.
        assert await hass.config_entries.async_setup(second.entry_id) is False
    await hass.async_block_till_done()
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert all(entity.config_entry_id == previous.entry_id for entity in diagnostic_entries(hass))
    assert DATA_SHARED_DIAGNOSTICS not in hass.data[DOMAIN]
    assert await hass.config_entries.async_unload_platforms(second, PLATFORMS)


@pytest.mark.parametrize("legacy", ["entity_only", "device_only"])
async def test_unambiguous_incomplete_legacy_pair_keeps_existing_identity(
    hass, enable_custom_integrations, quiet_sources, legacy
):
    assert await async_setup_component(hass, DOMAIN, {})
    previous = config_entry(hass, "meteoswiss")
    target = config_entry(hass, "openmeteo")
    entities, devices = er.async_get(hass), dr.async_get(hass)
    before = []
    for key in DIAGNOSTICS:
        if legacy == "entity_only":
            old = entities.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}_{key}",
                config_entry=previous, suggested_object_id="retained_"+key,
                disabled_by=er.RegistryEntryDisabler.USER)
        else:
            old = devices.async_get_or_create(config_entry_id=previous.entry_id,
                identifiers={(DOMAIN, key)}, name="Retained helper group")
        before.append(old.id)
    assert await hass.config_entries.async_setup(target.entry_id)
    await hass.async_block_till_done()
    current = diagnostic_entries(hass)
    assert [entity.id if legacy == "entity_only" else entity.device_id for entity in current] == before
    assert all(entity.config_entry_id == target.entry_id for entity in current)
    assert await hass.config_entries.async_unload(target.entry_id)


async def test_ambiguous_unbound_legacy_devices_are_retained_without_new_helpers(
    hass, enable_custom_integrations, quiet_sources
):
    assert await async_setup_component(hass, DOMAIN, {})
    first, second = config_entry(hass, "meteoswiss"), config_entry(hass, "openmeteo")
    devices = dr.async_get(hass)
    for entry in (first, second):
        devices.async_get_or_create(config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "stations_map")}, name="Retained helper group")
    before = {device.id: device for device in devices.async_get_devices()}
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.async_block_till_done()
    assert diagnostic_entries(hass) == [None, None]
    assert all(devices.async_get(device_id) == device for device_id, device in before.items())
    assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is not None
    assert await hass.config_entries.async_unload(second.entry_id)


@pytest.mark.parametrize("disabled", DISABLED)
async def test_failed_native_unload_retains_owner_objects_and_choices(
    hass, enable_custom_integrations, quiet_sources, disabled
):
    first, second, entities, devices = await pair(hass, "meteoswiss", disabled)
    shared = hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS]
    objects = [hass.data[DATA_COMPONENT].get_entity(entity.entity_id)
               for entity in diagnostic_entries(hass)]
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=False):
        assert await hass.config_entries.async_unload(first.entry_id) is False
    assert shared.owner == first.entry_id
    assert set(shared.platforms) == {first.entry_id, second.entry_id}
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == entities
    assert [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices
    assert [hass.data[DATA_COMPONENT].get_entity(entity.entity_id)
            for entity in diagnostic_entries(hass)] == objects
    # Remove platform timers for the disposable test, without forging the
    # FAILED_UNLOAD entry state or asserting that HA can retry it normally.
    assert await hass.config_entries.async_unload_platforms(first, PLATFORMS)
    assert await hass.config_entries.async_unload(second.entry_id)
    await hass.async_stop(force=True)
    assert DATA_SHARED_DIAGNOSTICS not in hass.data[DOMAIN]


async def test_shutdown_skips_takeover_and_releases_all_platform_callbacks(
    hass, enable_custom_integrations, quiet_sources
):
    # An entry may finish releasing during the stop event before the shared
    # stop handler runs. This must not elect or poll the remaining peer.
    release_order = []

    @callback
    def release_during_stop(_event):
        release_order.append(bool(shared.platforms) and hass.is_stopping)
        shared.async_release(first.entry_id)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, release_during_stop)
    first, second, entities, devices = await pair(hass, "meteoswiss", None)
    shared = hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS]
    with patch.object(shared.platforms[second.entry_id], "add_entities") as add:
        await hass.async_stop(force=True)
        add.assert_not_called()
    assert release_order == [True]
    assert shared.platforms == {}
    assert DATA_SHARED_DIAGNOSTICS not in hass.data[DOMAIN]
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == entities
    assert [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices
    for entry in (first, second):
        assert await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


@pytest.mark.parametrize("fault", [
    "subentry_record", "missing_device", "missing_owner", "device_subentry",
    "split_owner",
])
async def test_unexpected_registry_read_stops_transfer_without_rewriting_records(
    hass, enable_custom_integrations, quiet_sources, fault
):
    first, second, before, devices_before = await pair(hass, "meteoswiss", None)
    entities, devices = er.async_get(hass), dr.async_get(hass)
    original = diagnostic_entries(hass)[0]
    get_entity, get_device = entities.async_get, devices.async_get

    def entity_read(entity_id):
        value = get_entity(entity_id)
        if entity_id == original.entity_id:
            if fault == "split_owner":
                return attr.evolve(value, config_entry_id=second.entry_id)
            return attr.evolve(value, config_subentry_id="unsupported_legacy_subentry")
        return value

    def device_read(device_id, **kwargs):
        if device_id == original.device_id and kwargs.get("include_composite_devices") is False:
            value = get_device(device_id, **kwargs)
            if fault == "missing_owner":
                return attr.evolve(value, config_entry_id="missing_owner_marker")
            if fault == "device_subentry":
                return attr.evolve(value, config_subentry_id="unsupported_legacy_subentry")
            return None
        return get_device(device_id, **kwargs)

    with ExitStack() as stack:
        if fault in ("subentry_record", "split_owner"):
            stack.enter_context(patch.object(entities, "async_get", side_effect=entity_read))
        else:
            stack.enter_context(patch.object(devices, "async_get", side_effect=device_read))
        assert await hass.config_entries.async_unload(first.entry_id)
        await hass.async_block_till_done()
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert [device_snapshot(devices.async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices_before
    assert hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS].owner is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is not None
    assert await hass.config_entries.async_reload(first.entry_id)
    await hass.async_block_till_done()
    assert_kept(hass, second, before, devices_before, None)
    assert await hass.config_entries.async_unload(first.entry_id)
    assert await hass.config_entries.async_unload(second.entry_id)


@pytest.mark.parametrize("successful_writes", [0, 1])
async def test_persistent_registry_error_exposes_repair_and_preserves_records(
    hass, enable_custom_integrations, quiet_sources, caplog, successful_writes
):
    first, second, before, devices_before = await pair(hass, "meteoswiss", None)
    entities, devices = er.async_get(hass), dr.async_get(hass)
    original = diagnostic_entries(hass)
    update = entities.async_update_entity
    count = 0

    def failing(*args, **kwargs):
        nonlocal count
        if "config_entry_id" in kwargs:
            count += 1
            if count > successful_writes:
                raise ValueError("private_persistent_error_marker")
        return update(*args, **kwargs)

    with patch.object(entities, "async_update_entity", side_effect=failing):
        assert await hass.config_entries.async_unload(first.entry_id)
        await hass.async_block_till_done()
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert [device_snapshot(devices.async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices_before
    assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is not None
    assert "private_persistent_error_marker" not in caplog.text
    assert second.state is ConfigEntryState.LOADED
    assert hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS].owner is None
    # Only this disposable test repairs the injected inconsistent ownership.
    # Runtime code must not pretend a failed rollback succeeded or guess a fix.
    for entity in original:
        entities.async_update_entity(entity.entity_id, config_entry_id=first.entry_id)
    assert await hass.config_entries.async_reload(first.entry_id)
    await hass.async_block_till_done()
    assert_kept(hass, second, before, devices_before, None)
    assert await hass.config_entries.async_unload(first.entry_id)
    assert await hass.config_entries.async_unload(second.entry_id)


async def test_native_recorder_retains_old_rows_and_history_target_after_handoff(
    recorder_mock, hass, enable_custom_integrations, quiet_sources, freezer
):
    now = datetime(2026, 11, 12, 10, tzinfo=UTC)
    freezer.move_to(now)
    first, second, before, devices_before = await pair(hass, "meteoswiss", None)
    target = diagnostic_entries(hass)[1].entity_id
    entity = hass.data[DATA_COMPONENT].get_entity(target)
    freezer.move_to(now + timedelta(minutes=1))
    entity._attr_native_value = "25.0% hit rate"
    entity.async_write_ha_state()
    await async_wait_recording_done(hass)

    async def history():
        data = await hass.async_add_executor_job(partial(
            get_significant_states, hass, now - timedelta(seconds=1),
            now + timedelta(minutes=4), entity_ids=[target]))
        return [(item.state, item.last_changed, dict(item.attributes)) for item in data[target]]

    old_rows = await history()
    freezer.move_to(now + timedelta(minutes=2))
    assert (await hass.config_entries.async_remove(first.entry_id))["require_restart"] is False
    await hass.async_block_till_done()
    assert_kept(hass, second, before, devices_before, None)
    freezer.move_to(now + timedelta(minutes=3))
    current = hass.data[DATA_COMPONENT].get_entity(target)
    current._attr_native_value = "75.0% hit rate"
    current.async_write_ha_state()
    await async_wait_recording_done(hass)
    after = await history()
    assert old_rows and all(row in after for row in old_rows)
    assert {row[0] for row in after} >= {"25.0% hit rate", "75.0% hit rate"}
    assert await hass.config_entries.async_unload(second.entry_id)


async def test_duplicate_platform_registration_cannot_replace_a_live_callback(
    hass, enable_custom_integrations, quiet_sources
):
    first, second, entities, devices = await pair(hass, "meteoswiss", None)
    shared = hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS]
    registration = shared.platforms[first.entry_id]
    add, factory = Mock(), Mock()
    shared.async_register(first, add, factory)
    assert shared.platforms[first.entry_id] is registration
    add.assert_not_called()
    factory.assert_not_called()
    assert_kept(hass, first, entities, devices, None)
    assert await hass.config_entries.async_unload(second.entry_id)
    assert await hass.config_entries.async_unload(first.entry_id)
    shared.async_release(first.entry_id)  # Late duplicate cleanup is harmless.


@pytest.mark.parametrize("kind", ["device_collision", "foreign_entity", "extra_identifier", "child_device"])
async def test_ambiguous_groups_are_not_moved_removed_or_silently_merged(
    hass, enable_custom_integrations, quiet_sources, kind
):
    first, second, _, _ = await pair(hass, "meteoswiss", None)
    entities, devices = er.async_get(hass), dr.async_get(hass)
    original = diagnostic_entries(hass)[0]
    if kind == "device_collision":
        devices.async_get_or_create(config_entry_id=second.entry_id,
            identifiers={(DOMAIN, "stations_map")}, name="Retained older group")
    elif kind == "foreign_entity":
        entities.async_get_or_create("sensor", DOMAIN, "retained_unrelated_sensor",
            config_entry=first, device_id=original.device_id)
    elif kind == "extra_identifier":
        devices.async_update_device(original.device_id,
            new_identifiers={(DOMAIN, "stations_map"), (DOMAIN, "retained_other_role")})
    else:
        devices.async_get_or_create_child(config_entry_id=first.entry_id,
            identifiers={(DOMAIN, "retained_child")}, parent_device_id=original.device_id,
            name="Retained child")
    snapshots = [entity_snapshot(entity) for entity in diagnostic_entries(hass)]
    before = {device.id: device for device in devices.async_get_devices()}
    with patch.object(devices, "async_remove_device", wraps=devices.async_remove_device) as remove:
        assert await hass.config_entries.async_unload(first.entry_id)
        await hass.async_block_till_done()
        remove.assert_not_called()
    assert hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS].owner is None
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == snapshots
    assert {device.id: device for device in devices.async_get_devices()} == before
    issue = ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED)
    assert issue is not None and issue.translation_key == SHARED_DIAGNOSTICS_BLOCKED
    assert second.state is ConfigEntryState.LOADED
    # Returning the original owner is safe, even when a different entry has a
    # historical device with the same scoped identifier.
    if kind == "device_collision":
        assert await hass.config_entries.async_reload(first.entry_id)
        await hass.async_block_till_done()
        assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is None
        assert hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS].owner == first.entry_id
        assert await hass.config_entries.async_unload(first.entry_id)
    assert await hass.config_entries.async_unload(second.entry_id)


@pytest.mark.parametrize("failed_write", [1, 2, 3, 4])
async def test_registry_move_error_rolls_back_all_retained_records(
    hass, enable_custom_integrations, quiet_sources, failed_write, caplog
):
    first, second, before, devices_before = await pair(hass, "meteoswiss", None)
    entities, devices = er.async_get(hass), dr.async_get(hass)
    update_entity = entities.async_update_entity
    count = 0

    def entity_write(*args, **kwargs):
        nonlocal count
        if "config_entry_id" in kwargs:
            count += 1
            if count == failed_write:
                raise ValueError("private_exception_marker")
        return update_entity(*args, **kwargs)

    with patch.object(entities, "async_update_entity", side_effect=entity_write):
        assert await hass.config_entries.async_unload(first.entry_id)
        await hass.async_block_till_done()
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert [device_snapshot(devices.async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices_before
    assert all(entity.config_entry_id == first.entry_id for entity in diagnostic_entries(hass))
    assert all(devices.async_get(entity.device_id).config_entry_id == first.entry_id
               for entity in diagnostic_entries(hass))
    assert "private_exception_marker" not in caplog.text
    assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is not None
    assert await hass.config_entries.async_reload(first.entry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is None
    assert_kept(hass, second, before, devices_before, None)
    assert await hass.config_entries.async_unload(first.entry_id)
    assert await hass.config_entries.async_unload(second.entry_id)


async def test_add_callback_error_blocks_only_helpers_and_keeps_registry_choices(
    hass, enable_custom_integrations, quiet_sources, caplog
):
    first, second, before, devices_before = await pair(hass, "meteoswiss", None)
    shared = hass.data[DOMAIN][DATA_SHARED_DIAGNOSTICS]
    with patch.object(shared.platforms[second.entry_id], "add_entities",
                      side_effect=ValueError("private_callback_marker")):
        assert await hass.config_entries.async_unload(first.entry_id)
        await hass.async_block_till_done()
    assert shared.owner is None
    assert [entity_snapshot(entity) for entity in diagnostic_entries(hass)] == before
    assert [device_snapshot(dr.async_get(hass).async_get(entity.device_id))
            for entity in diagnostic_entries(hass)] == devices_before
    assert second.state is ConfigEntryState.LOADED
    assert ir.async_get(hass).async_get_issue(DOMAIN, SHARED_DIAGNOSTICS_BLOCKED) is not None
    assert "private_callback_marker" not in caplog.text
    assert await hass.config_entries.async_reload(second.entry_id)
    await hass.async_block_till_done()
    assert_kept(hass, second, before, devices_before, None)
    assert await hass.config_entries.async_unload(second.entry_id)


@pytest.mark.parametrize("language", ["de", "en", "fr", "it"])
async def test_ownership_repair_has_complete_native_translations(
    hass, enable_custom_integrations, quiet_sources, language
):
    await hass.config.async_update(language=language)
    first = config_entry(hass, "meteoswiss")
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    translations = await async_get_translations(hass, language, "issues", {DOMAIN})
    for field in ("title", "description"):
        assert translations[f"component.{DOMAIN}.issues.{SHARED_DIAGNOSTICS_BLOCKED}.{field}"]
    assert await hass.config_entries.async_unload(first.entry_id)
