"""Native entry, entity, translation, sharing, station-change and removal tests."""

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from ha_helpers import MockConfigEntry
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from test_hgt_ogd_recorder import products
from test_hgt_ogd_source import NOW
from test_provider_device_metadata import make_entry
from test_provider_device_metadata import provider_sources as provider_sources

from custom_components.meteoswiss import hgt_ogd_manager as mgr
from custom_components.meteoswiss import hgt_ogd_recorder as rec
from custom_components.meteoswiss import repairs
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.diagnostics import async_get_config_entry_diagnostics
from custom_components.meteoswiss.hgt_ogd import (
    HgtError,
    MeteoSwissHgtClient,
    statistic_ids,
)
from custom_components.meteoswiss.hgt_ogd_coordinator import MeteoSwissHgtCoordinator
from custom_components.meteoswiss.sensor import MeteoSwissMeasuredHgtSensor

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / DOMAIN


@pytest.fixture
def source_data(provider_sources, freezer):
    freezer.move_to(NOW)
    with (
        patch.object(
            MeteoSwissHgtClient, "async_fetch", return_value=products()
        ) as fetch,
        patch(
            "custom_components.meteoswiss.coordinator.MeteoSwissHourlyPrecipitationCoordinator._async_update_data",
            return_value={},
        ),
    ):
        yield fetch


def live(hass, entry):
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_heating_degree_days_observed"
    )
    return hass.data[DATA_COMPONENT].get_entity(entity_id)


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_native_observed_entity_uses_translated_name_and_distinct_identity(
    recorder_mock, hass, enable_custom_integrations, source_data, language
):
    await hass.config.async_update(language=language)
    entry = make_entry(hass, "meteoswiss")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    sensor = live(hass, entry)
    source_data.assert_awaited_once()
    assert sensor.native_value == 19.1 and sensor.available
    assert (
        sensor.state_class is None
        and sensor.device_class is None
        and sensor.native_unit_of_measurement == "°C·d"
    )
    catalog = json.loads((COMPONENT / "translations" / f"{language}.json").read_text())
    assert sensor.name == catalog["entity"]["sensor"]["hgt_measured"]["name"]
    saved = er.async_get(hass).async_get(sensor.entity_id)
    assert (
        saved.translation_key == "hgt_measured" and saved.original_name == sensor.name
    )
    forecast = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_heating_degree_days"
    )
    assert forecast != sensor.entity_id
    assert sensor.extra_state_attributes["value_type"] == "observation"
    assert sensor.extra_state_attributes["reference_time_zone"] == "UTC"
    assert sensor.extra_state_attributes["statistic_ids"] == statistic_ids("klo")
    assert sensor.device_info["identifiers"] == {(DOMAIN, entry.entry_id)}
    texts = await async_get_translations(hass, language, "issues", {DOMAIN})
    for issue in [mgr.CLEANUP_ISSUE, mgr.BLOCKED_ISSUE, "hgt_ogd_import_blocked"]:
        assert texts[f"component.{DOMAIN}.issues.{issue}.title"]
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    summary = diagnostics["coordinators"]["hgt_ogd_coordinator"]
    assert (
        summary["name"] == "hgt_ogd_coordinator" and summary["data"]["type"] == "dict"
    )
    assert "klo_hgt" not in repr(diagnostics) and "19.1" not in repr(diagnostics)
    session = entry.runtime_data.session
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    manager = mgr.get_hgt_manager(hass)
    assert not manager.users and not manager.clients and not manager.snapshots
    assert not session.closed


async def test_native_shared_series_station_change_consent_and_final_removal_leave_no_archive(
    recorder_mock, hass, enable_custom_integrations, source_data
):
    one = make_entry(hass, "meteoswiss")
    assert await hass.config_entries.async_setup(one.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    two = make_entry(hass, "meteoswiss")
    assert await hass.config_entries.async_setup(two.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert source_data.await_count == 1
    manager = mgr.get_hgt_manager(hass)
    assert manager.users["klo"] == {one.entry_id, two.entry_id}
    await hass.config_entries.async_remove(one.entry_id)
    assert len(await rec.async_metadata(hass, {"klo"})) == 3
    assert manager.users["klo"] == {two.entry_id}
    old = live(hass, two)
    saved = er.async_get(hass).async_update_entity(
        old.entity_id, name="My measured HGT", icon="mdi:star"
    )
    hass.config_entries.async_update_entry(two, data={**two.data, "station_id": "ber"})
    assert await hass.config_entries.async_reload(two.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    current = live(hass, two)
    assert current.unique_id == old.unique_id and current.entity_id == old.entity_id
    assert er.async_get(hass).async_get(current.entity_id).name == saved.name
    assert current.extra_state_attributes["statistic_ids"] == statistic_ids("ber")
    assert set(manager.known) == {"klo", "ber"}
    issue = ir.async_get(hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE)
    assert issue.is_fixable and all(
        "klo" in s for s in issue.translation_placeholders["statistic_ids"].splitlines()
    )
    flow = await repairs.async_create_fix_flow(
        hass, mgr.CLEANUP_ISSUE, {"kind": mgr.CLEANUP_ISSUE}
    )
    flow.hass = hass
    assert (await flow.async_step_init({}))["type"] == "form"
    assert len(await rec.async_metadata(hass, {"klo"})) == 3
    assert (await flow.async_step_confirm({}))["type"] == "create_entry"
    assert (
        await rec.async_metadata(hass, {"klo"}) == {}
        and len(await rec.async_metadata(hass, {"ber"})) == 3
    )
    await hass.config_entries.async_remove(two.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert not await rec.async_metadata(hass, {"klo", "ber"})
    assert manager.known == set() and await manager.store.async_load() is None
    assert not manager.users and not manager.clients and not manager.snapshots
    assert ir.async_get(hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE) is None


async def test_live_sensor_disabled_does_not_stop_authoritative_statistic_polling(
    recorder_mock, hass, enable_custom_integrations, source_data
):
    entry = make_entry(hass, "meteoswiss")
    registry = er.async_get(hass)
    saved = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{DOMAIN}_{entry.entry_id}_heating_degree_days_observed",
        config_entry=entry,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(saved.entity_id) is None
    coordinator = entry.runtime_data.hgt_ogd_coordinator
    assert coordinator._listeners and coordinator.update_interval == timedelta(hours=6)
    assert len(await rec.async_metadata(hass, {"klo"})) == 3
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not coordinator._listeners


@pytest.mark.parametrize("source", ["openmeteo", "invalid"])
async def test_provider_or_invalid_identity_cannot_create_measured_hgt(
    recorder_mock, hass, enable_custom_integrations, source_data, source
):
    entry = make_entry(hass, "openmeteo" if source == "openmeteo" else "meteoswiss")
    if source == "invalid":
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "station_id": "../"}
        )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert entry.runtime_data.hgt_ogd_coordinator is None
    source_data.assert_not_awaited()
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(
    "age,successful,data_present,available,status",
    [
        (1, True, True, True, "ready"),
        (2, True, True, True, "ready"),
        (3, True, True, False, "delayed"),
        (0, True, True, False, "delayed"),
        (-1, True, True, False, "delayed"),
        (1, False, True, False, "unavailable"),
        (1, True, False, False, "initializing"),
    ],
)
def test_latest_observed_day_cannot_present_future_or_stale_value(
    hass, freezer, age, successful, data_present, available, status
):
    freezer.move_to(NOW)
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = DataUpdateCoordinator(
        hass, logging.getLogger(__name__), name="hgt", config_entry=entry
    )
    coordinator.last_update_success = successful
    coordinator.data = (
        {
            "latest_value": 19.1,
            "source_day": (NOW - timedelta(days=age)).date().isoformat(),
            "statistics_status": "ready",
            "private_source_marker": "must-not-export",
        }
        if data_present
        else None
    )
    sensor = MeteoSwissMeasuredHgtSensor(coordinator, entry, "Example station")
    assert sensor.available is available and sensor.native_value == (
        19.1 if available else None
    )
    assert sensor.extra_state_attributes["statistics_status"] == status
    assert "private_source_marker" not in repr(sensor.extra_state_attributes)


@pytest.mark.parametrize(
    "failure,issue",
    [
        (HgtError("statistics_conflict"), True),
        (HgtError("ownership_unavailable"), True),
        (HgtError("source_incomplete"), False),
        (OSError("private_provider_marker"), False),
    ],
)
async def test_update_errors_use_localized_fixed_categories_without_private_details(
    hass, failure, issue
):
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = MeteoSwissHgtCoordinator(hass, entry, "klo", None)
    with (
        patch.object(coordinator.manager, "async_refresh", side_effect=failure),
        patch.object(
            coordinator.manager, "async_sync_issue", new_callable=AsyncMock
        ) as sync,
    ):
        with pytest.raises(UpdateFailed) as error:
            await coordinator._async_update_data()
    assert error.value.translation_key == (
        "hgt_ogd_conflict" if issue else "hgt_ogd_unavailable"
    )
    assert error.value.__cause__ is None and "private_provider_marker" not in str(
        error.value
    )
    sync.assert_awaited_once()
    assert (
        ir.async_get(hass).async_get_issue(DOMAIN, coordinator.issue_id) is not None
    ) is issue
    await entry._async_process_on_unload(hass)
    assert (
        not coordinator.manager.users
        and ir.async_get(hass).async_get_issue(DOMAIN, coordinator.issue_id) is None
    )


async def test_coordinator_success_clears_only_own_issue_and_cancellation_propagates(
    hass,
):
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = MeteoSwissHgtCoordinator(hass, entry, "klo", None)
    with (
        patch.object(coordinator.manager, "async_refresh", return_value={"value": 1}),
        patch.object(coordinator.manager, "async_sync_issue", new_callable=AsyncMock),
    ):
        assert await coordinator._async_update_data() == {"value": 1}
    with (
        patch.object(
            coordinator.manager, "async_refresh", side_effect=asyncio.CancelledError
        ),
        patch.object(coordinator.manager, "async_sync_issue", new_callable=AsyncMock),
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_update_data()
    await entry._async_process_on_unload(hass)
