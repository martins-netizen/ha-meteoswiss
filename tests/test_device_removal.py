"""Native device-page removal with retained active groups, choices and history."""

from datetime import UTC, datetime, timedelta
from functools import partial
from unittest.mock import Mock, patch

import attr
import pytest
from homeassistant.components.config.device_registry import _async_remove_device
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.config_entries import ConfigEntryDisabler, ConfigEntryState
from homeassistant.core import CoreState
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component
from ha_helpers import MockConfigEntry, async_wait_recording_done

from custom_components.meteoswiss import async_remove_config_entry_device
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.device_removal import (
    DeviceRemovalStatus as Status,
    async_device_removal_status,
)
from test_provider_device_metadata import make_entry, provider_sources

RETIRED_IDS = ("0123456789abcdef0123456789abcdef", "01JAAAAAAAAAAAAAAAAAAAAAAA")
PREFIXES = ("", "calculated_", "alerts_", "pollen_", "ms_pollen_")


@pytest.fixture(params=("meteoswiss", "openmeteo"))
async def loaded_entry(hass, enable_custom_integrations, provider_sources, request):
    assert await async_setup_component(hass, DOMAIN, {})
    entry = make_entry(hass, request.param)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry
    if entry.state is ConfigEntryState.LOADED:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


def retired_device(hass, entry, key=None, **kwargs):
    return dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, key or "calculated_" + RETIRED_IDS[0])},
        entry_type=dr.DeviceEntryType.SERVICE,
        name="Retained service shell", **kwargs,
    )


def snapshot(hass):
    return (
        dict((d.id, d) for d in dr.async_get(hass).devices),
        dict(er.async_get(hass).entities),
        {s.entity_id: (s.state, dict(s.attributes)) for s in hass.states.async_all()},
    )


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("old_id", RETIRED_IDS)
async def test_known_empty_retired_groups_are_classified_without_mutation(
    hass, loaded_entry, prefix, old_id
):
    device = retired_device(hass, loaded_entry, prefix + old_id)
    before = snapshot(hass)
    devices, entities = dr.async_get(hass), er.async_get(hass)
    with patch.object(devices, "async_remove_device", wraps=devices.async_remove_device) as remove, \
         patch.object(entities, "async_remove", wraps=entities.async_remove) as remove_entity:
        assert async_device_removal_status(hass, loaded_entry, device) is Status.EMPTY_RETIRED_GROUP
        assert await async_remove_config_entry_device(hass, loaded_entry, device)
        remove.assert_not_called()
        remove_entity.assert_not_called()
    assert snapshot(hass) == before


async def test_native_admin_websocket_removes_only_the_confirmed_empty_shell(
    hass, loaded_entry, hass_ws_client
):
    assert loaded_entry.supports_remove_device
    assert await async_setup_component(hass, "config", {})
    client = await hass_ws_client(hass)
    devices = dr.async_get(hass)
    device = retired_device(hass, loaded_entry)
    devices.async_update_device(device.id, name_by_user="My unused shell")
    before = snapshot(hass)
    await client.send_json({"id": 1, "type": "config/device_registry/remove", "device_id": device.id})
    assert (await client.receive_json())["success"]
    await hass.async_block_till_done()
    after = snapshot(hass)
    assert devices.async_get(device.id) is None
    assert after[0] == {key: value for key, value in before[0].items() if key != device.id}
    assert after[1:] == before[1:]
    current = devices.async_get_device_by_identifier(
        (DOMAIN, loaded_entry.entry_id), loaded_entry.entry_id)
    await client.send_json({"id": 2, "type": "config/device_registry/remove", "device_id": current.id})
    assert not (await client.receive_json())["success"]
    await hass.async_block_till_done()
    assert snapshot(hass) == after


@pytest.mark.parametrize("mode", ["normal", "source_error", "devices_disabled", "entities_disabled"])
async def test_all_seven_current_groups_and_personal_choices_remain_protected(
    hass, loaded_entry, mode
):
    devices, entities = dr.async_get(hass), er.async_get(hass)
    groups = dr.async_entries_for_config_entry(devices, loaded_entry.entry_id)
    assert len(groups) == 7
    for group in groups:
        devices.async_update_device(group.id, name_by_user="Personal group", labels={"retained"})
        if mode == "devices_disabled":
            devices.async_update_device(group.id, disabled_by=dr.DeviceEntryDisabler.USER)
    if mode == "entities_disabled":
        for entity in er.async_entries_for_config_entry(entities, loaded_entry.entry_id):
            entities.async_update_entity(entity.entity_id, disabled_by=er.RegistryEntryDisabler.USER)
        await hass.async_block_till_done()
    if mode == "source_error":
        loaded_entry.runtime_data.coordinator.async_set_update_error(ValueError("synthetic provider failure"))
        await hass.async_block_till_done()
    before = snapshot(hass)
    for group in groups:
        current = devices.async_get(group.id)
        assert not await async_remove_config_entry_device(hass, loaded_entry, current)
    assert snapshot(hass) == before


@pytest.mark.parametrize("kind", ["enabled", "user_disabled", "integration_disabled", "hidden", "foreign", "cross_entry"])
async def test_any_entity_binding_blocks_a_retired_shell(hass, loaded_entry, kind):
    device = retired_device(hass, loaded_entry)
    owner = loaded_entry
    if kind == "cross_entry":
        owner = MockConfigEntry(domain=DOMAIN)
        owner.add_to_hass(hass)
    bound = er.async_get(hass).async_get_or_create(
        "sensor", "other" if kind == "foreign" else DOMAIN, "retained_history_target",
        config_entry=owner, device_id=device.id,
        disabled_by=(er.RegistryEntryDisabler.USER if kind == "user_disabled" else
                     er.RegistryEntryDisabler.INTEGRATION if kind == "integration_disabled" else None),
    )
    if kind == "hidden":
        er.async_get(hass).async_update_entity(bound.entity_id, hidden_by=er.RegistryEntryHider.USER)
    assert async_device_removal_status(hass, loaded_entry, device) is Status.ENTITY_BINDINGS
    assert not await async_remove_config_entry_device(hass, loaded_entry, device)


@pytest.mark.parametrize("kind", ["child", "via", "duplicate", "child_duplicate"])
async def test_linked_and_cross_entry_ambiguous_devices_remain(hass, loaded_entry, kind):
    device = retired_device(hass, loaded_entry)
    devices = dr.async_get(hass)
    other = MockConfigEntry(domain=DOMAIN)
    other.add_to_hass(hass)
    if kind == "child":
        devices.async_get_or_create_child(config_entry_id=loaded_entry.entry_id,
            parent_device_id=device.id, identifiers={(DOMAIN, "retained_child")})
    elif kind == "via":
        devices.async_get_or_create(config_entry_id=other.entry_id,
            identifiers={(DOMAIN, "retained_peer")}, via_device_id=device.id)
    elif kind == "duplicate":
        retired_device(hass, other)
    else:
        parent = devices.async_get_or_create(config_entry_id=other.entry_id,
            identifiers={(DOMAIN, "retained_parent")})
        devices.async_get_or_create_child(config_entry_id=other.entry_id,
            parent_device_id=parent.id, identifiers=device.identifiers)
    before = snapshot(hass)
    assert async_device_removal_status(hass, loaded_entry, device) is (
        Status.DEVICE_LINKS if kind in {"child", "via"} else Status.AMBIGUOUS_IDENTIFIER)
    assert not await async_remove_config_entry_device(hass, loaded_entry, device)
    assert snapshot(hass) == before


@pytest.mark.parametrize("kind", ["unknown", "malformed", "foreign_namespace", "multiple", "empty"])
async def test_unknown_or_malformed_identifiers_are_never_guessed(hass, loaded_entry, kind):
    device = retired_device(hass, loaded_entry)
    identifiers = {
        "unknown": {(DOMAIN, "old_station_location")},
        "malformed": {(DOMAIN, "calculated_" + "Z" * 26)},
        "foreign_namespace": {("other", RETIRED_IDS[0])},
        "multiple": {(DOMAIN, RETIRED_IDS[0]), (DOMAIN, "other_role")},
        "empty": set(),
    }[kind]
    if kind == "empty":
        # Corrupt reads are injected; no unsupported registry write is needed.
        current = attr.evolve(device, identifiers=identifiers)
        with patch.object(dr.async_get(hass), "async_get", return_value=current):
            assert async_device_removal_status(hass, loaded_entry, current) is Status.UNKNOWN_GROUP
    else:
        current = dr.async_get(hass).async_update_device(device.id, new_identifiers=identifiers)
        assert async_device_removal_status(hass, loaded_entry, current) is Status.UNKNOWN_GROUP


@pytest.mark.parametrize("state", [ConfigEntryState.NOT_LOADED, ConfigEntryState.SETUP_ERROR,
                                    ConfigEntryState.SETUP_IN_PROGRESS, ConfigEntryState.LOADED])
@pytest.mark.parametrize("old_domain", [DOMAIN, "other"])
async def test_a_still_existing_embedded_entry_is_retained_in_every_state(hass, loaded_entry, state, old_domain):
    old = MockConfigEntry(domain=old_domain, entry_id=RETIRED_IDS[0], state=state,
                          disabled_by=ConfigEntryDisabler.USER)
    old.add_to_hass(hass)
    device = retired_device(hass, loaded_entry)
    assert async_device_removal_status(hass, loaded_entry, device) is Status.ENTRY_STILL_EXISTS


@pytest.mark.parametrize("change", ["owner", "entry_type", "disabled", "connection", "via", "child", "subentry"])
async def test_only_unlinked_main_service_records_of_the_live_owner_are_candidates(
    hass, loaded_entry, change
):
    devices = dr.async_get(hass)
    other = MockConfigEntry(domain=DOMAIN)
    other.add_to_hass(hass)
    if change == "owner":
        device = retired_device(hass, other)
    elif change == "child":
        parent = retired_device(hass, loaded_entry, "retained_parent")
        device = devices.async_get_or_create_child(config_entry_id=loaded_entry.entry_id,
            parent_device_id=parent.id, identifiers={(DOMAIN, RETIRED_IDS[0])})
    elif change == "subentry":
        device = retired_device(hass, loaded_entry)
        broken = attr.evolve(device, config_subentry_id="retained_subentry")
        with patch.object(devices, "async_get", return_value=broken):
            assert async_device_removal_status(hass, loaded_entry, broken) is Status.DEVICE_PROTECTED
        return
    else:
        device = retired_device(hass, loaded_entry)
        changes = {
            "entry_type": {"entry_type": None},
            "disabled": {"disabled_by": dr.DeviceEntryDisabler.USER},
            "connection": {"new_connections": {("mac", "00:00:00:00:00:01")}},
            "via": {"via_device_id": retired_device(hass, other, "retained_parent").id},
        }
        device = devices.async_update_device(device.id, **changes[change])
    assert async_device_removal_status(hass, loaded_entry, device) is Status.DEVICE_PROTECTED


@pytest.mark.parametrize("change", ["composite", "unreconciled"])
async def test_legacy_split_metadata_is_never_treated_as_empty_retired_ownership(
    hass, loaded_entry, change
):
    devices = dr.async_get(hass)
    device = retired_device(hass, loaded_entry)
    # Split markers are migration-owned; inject a retained read snapshot instead
    # of writing them through private registry methods.
    broken = attr.evolve(device, **({"has_composite_identifiers": True}
        if change == "unreconciled" else {"composite_device_id": "retained_composite"}))
    with patch.object(devices, "async_get", return_value=broken):
        assert async_device_removal_status(hass, loaded_entry, broken) is Status.DEVICE_PROTECTED


async def test_stale_registry_snapshot_or_missing_record_cannot_be_authorized(hass, loaded_entry):
    devices = dr.async_get(hass)
    old = retired_device(hass, loaded_entry)
    current = devices.async_update_device(old.id, name_by_user="Changed concurrently")
    assert async_device_removal_status(hass, loaded_entry, old) is Status.DEVICE_PROTECTED
    assert async_device_removal_status(hass, loaded_entry, current) is Status.EMPTY_RETIRED_GROUP
    devices.async_remove_device(current.id)
    assert async_device_removal_status(hass, loaded_entry, current) is Status.DEVICE_PROTECTED


@pytest.mark.parametrize("case", ["not_registered", "foreign_domain", "unloaded", "disabled", "stopping"])
async def test_missing_or_unready_entry_context_is_rejected(hass, loaded_entry, case):
    entry = loaded_entry
    device = retired_device(hass, entry)
    if case == "not_registered":
        entry = MockConfigEntry(domain=DOMAIN, state=ConfigEntryState.LOADED)
    elif case == "foreign_domain":
        entry = MockConfigEntry(domain="other", state=ConfigEntryState.LOADED)
        entry.add_to_hass(hass)
    elif case == "unloaded":
        assert await hass.config_entries.async_unload(entry.entry_id)
    elif case == "disabled":
        await hass.config_entries.async_set_disabled_by(entry.entry_id, ConfigEntryDisabler.USER)
    else:
        prior = hass.state
        hass.set_state(CoreState.stopping)
        try:
            assert async_device_removal_status(hass, entry, device) is Status.ENTRY_NOT_READY
        finally:
            hass.set_state(prior)
        return
    assert async_device_removal_status(hass, entry, device) is Status.ENTRY_NOT_READY


async def test_registry_read_failure_never_falls_back_to_allow(hass, loaded_entry):
    device = retired_device(hass, loaded_entry)
    with patch.object(dr.async_get(hass), "async_get", side_effect=RuntimeError("synthetic read failure")):
        with pytest.raises(RuntimeError, match="synthetic read failure"):
            await async_remove_config_entry_device(hass, loaded_entry, device)
    assert dr.async_get(hass).async_get(device.id) is device


async def test_removal_preserves_recorder_rows_and_current_weather_identity(
    recorder_mock, hass, loaded_entry, freezer
):
    now = datetime(2026, 11, 12, 12, tzinfo=UTC)
    freezer.move_to(now)
    device = retired_device(hass, loaded_entry)
    entities = er.async_get(hass)
    old = entities.async_get_or_create("sensor", DOMAIN, "retired_row_target",
        config_entry=loaded_entry, device_id=device.id)
    hass.states.async_set(old.entity_id, "17")
    await async_wait_recording_done(hass)
    entities.async_remove(old.entity_id)
    await hass.async_block_till_done()
    before = snapshot(hass)
    connection = Mock()
    await _async_remove_device(hass, connection, {"id": 1, "device_id": device.id})
    assert connection.send_message.call_args.args[0]["success"]
    await hass.async_block_till_done()
    assert snapshot(hass)[1:] == before[1:]
    freezer.move_to(now + timedelta(minutes=1))
    await async_wait_recording_done(hass)
    history = await hass.async_add_executor_job(partial(
        get_significant_states, hass, now - timedelta(seconds=1),
        now + timedelta(minutes=2), entity_ids=[old.entity_id]))
    assert "17" in {row.state for row in history[old.entity_id]}
