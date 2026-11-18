"""Check the native HTTP envelope as well as the integration's own snapshot."""

import asyncio
from copy import deepcopy
from datetime import timedelta
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from ha_helpers import MockConfigEntry
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.redact import REDACTED
from homeassistant.setup import async_setup_component

from custom_components.meteoswiss import hgt_ogd_manager as manager_module
from custom_components.meteoswiss import repairs
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.diagnostics import async_get_config_entry_diagnostics
from custom_components.meteoswiss.hgt_ogd import statistic_ids
from custom_components.meteoswiss.runtime_data import MeteoSwissRuntimeData


def private_entry(hass, *, disabled=False, add_to_hass=True):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "data_source": "openmeteo",
            "station_id": "LUG",
            "latitude": 47.451234,
            "longitude": 8.561234,
            "polen_station_code": "PRIVATE_LEGACY_LOCATION",
            "PRIVATE_UNKNOWN_KEY": {"token": "PRIVATE_UNKNOWN_VALUE"},
        },
        options={"pollen_station": "PZH", "private_token": "PRIVATE_OPTION"},
        disabled_by=ConfigEntryDisabler.USER if disabled else None,
    )
    if add_to_hass:
        entry.add_to_hass(hass)
    return entry


@pytest.mark.parametrize("loaded", [False, True])
@pytest.mark.parametrize(
    "interval,expected",
    [
        (600, 600),
        (3600.5, 3600.5),
        (True, "invalid"),
        (599, "invalid"),
        ("600", "invalid"),
        (float("nan"), "invalid"),
        (float("inf"), "invalid"),
        (10**500, "invalid"),
        ({"PRIVATE_INTERVAL": "PRIVATE_VALUE"}, "invalid"),
    ],
)
async def test_typed_config_summary_omits_unknown_values_and_private_key_names(
    hass, loaded, interval, expected
):
    original = private_entry(hass, add_to_hass=False)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**original.data, "data_source": "PRIVATE_SOURCE_47.451234", "update_interval": interval},
        options={**original.options, "data_source": ["PRIVATE_OPTION_SOURCE"], "update_interval": interval},
    )
    if loaded:
        coordinator = SimpleNamespace(
            last_update_success=False,
            update_interval=timedelta(seconds=600),
            data={"private_payload": "PRIVATE_BODY"},
            last_exception=ValueError("PRIVATE_ERROR_URL_47.451234"),
        )
        entry.runtime_data = MeteoSwissRuntimeData(
            coordinator=coordinator, data_source="PRIVATE_RUNTIME_SOURCE", session=None
        )
    result = await async_get_config_entry_diagnostics(hass, entry)
    data, options = result["config_entry"]["data"], result["config_entry"]["options"]
    assert data["polen_station_code"] == REDACTED
    assert data["latitude"] == data["longitude"] == REDACTED
    assert options["pollen_station"] == REDACTED
    assert data["data_source"] == options["data_source"] == "unknown"
    assert data["update_interval"] == options["update_interval"] == expected
    rendered = json.dumps(result)
    assert "PRIVATE_" not in rendered
    assert "47.451234" not in rendered and "8.561234" not in rendered


def create_old_notice(hass):
    ir.async_create_issue(
        hass, DOMAIN, manager_module.CLEANUP_ISSUE,
        is_fixable=True, is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=manager_module.CLEANUP_ISSUE,
        data={"kind": manager_module.CLEANUP_ISSUE},
        translation_placeholders={"statistic_ids": "\n".join(statistic_ids("klo").values())},
    )
    ir.async_ignore_issue(hass, DOMAIN, manager_module.CLEANUP_ISSUE, True)
    return ir.async_get(hass).async_get_issue(DOMAIN, manager_module.CLEANUP_ISSUE)


async def reload_old_notice(hass, hass_storage):
    """Simulate a stored pre-upgrade registry in this disposable HA instance."""
    old = create_old_notice(hass)
    ir.async_create_issue(
        hass, DOMAIN, "unrelated_notice",
        is_fixable=False, is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="unrelated_notice",
        data={"retained": "unrelated-data"},
        translation_placeholders={"retained": "unrelated-placeholder"},
    )
    before = deepcopy(old.to_json())
    unrelated = deepcopy(ir.async_get(hass).async_get_issue(DOMAIN, "unrelated_notice").to_json())
    hass_storage[ir.STORAGE_KEY] = {
        "version": ir.STORAGE_VERSION_MAJOR,
        "minor_version": ir.STORAGE_VERSION_MINOR,
        "key": ir.STORAGE_KEY,
        "data": {"issues": [before, unrelated]},
    }
    # This models cold reload in the test only. Production never reloads Core's
    # registry or replaces unsaved issues from another integration.
    await ir.async_load(hass)
    assert ir.async_get(hass).async_get_issue(DOMAIN, manager_module.CLEANUP_ISSUE).translation_placeholders
    return before, unrelated


async def download(hass, hass_client, entry):
    assert await async_setup_component(hass, "diagnostics", {})
    await hass.async_block_till_done()
    client = await hass_client()
    response = await client.get(f"/api/diagnostics/config_entry/{entry.entry_id}")
    return response


@pytest.mark.parametrize("state", ["loaded", "unloaded", "disabled"])
async def test_startup_scrubs_old_persistent_notice_before_native_http_snapshot(
    hass, hass_client, hass_storage, enable_custom_integrations, state
):
    entry = private_entry(hass, disabled=state == "disabled")
    before, unrelated = await reload_old_notice(hass, hass_storage)

    async def setup_entry(_hass, item):
        item.runtime_data = MeteoSwissRuntimeData(
            coordinator=None, data_source="openmeteo", session=None
        )
        return True

    with (
        patch("custom_components.meteoswiss.async_setup_entry", new=setup_entry),
        patch("custom_components.meteoswiss.async_unload_entry", return_value=True),
        patch("custom_components.meteoswiss.stations_map.MeteoSwissStationsMap._async_content") as source,
        patch("custom_components.meteoswiss.hgt_ogd_manager.HgtOgdManager.async_load") as owners,
        patch("custom_components.meteoswiss.hgt_ogd_manager.async_metadata") as recorder,
        patch.object(ir.async_get(hass), "async_load", side_effect=AssertionError("do not reload Core registry")),
    ):
        if state == "disabled":
            # A cold disabled-only domain has no diagnostics platform to export.
            missing = await download(hass, hass_client, entry)
            assert missing.status == 404
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        if state == "unloaded":
            assert await hass.config_entries.async_unload(entry.entry_id)
        response = await download(hass, hass_client, entry)
        assert response.status == 200
        payload = await response.json()
        source.assert_not_called()
        owners.assert_not_called()
        recorder.assert_not_called()
    issue = ir.async_get(hass).async_get_issue(DOMAIN, manager_module.CLEANUP_ISSUE)
    expected = {**before, "translation_placeholders": None}
    assert issue.to_json() == expected
    assert ir.async_get(hass).async_get_issue(DOMAIN, "unrelated_notice").to_json() == unrelated
    assert expected in payload["issues"]
    assert unrelated in payload["issues"]
    rendered = json.dumps(payload)
    # The downloaded entry uses LUG. Core includes even domain notices about a
    # different, retired station (KLO) in this same HTTP response.
    for secret in (*statistic_ids("klo").values(), "PRIVATE_", "47.451234", "8.561234"):
        assert secret not in rendered


async def test_normal_manager_resync_clears_old_placeholders_and_keeps_exact_consent(
    hass, hass_client, enable_custom_integrations
):
    entry = private_entry(hass, disabled=True)
    assert await async_setup_component(hass, DOMAIN, {})
    before = deepcopy(create_old_notice(hass).to_json())
    manager = manager_module.get_hgt_manager(hass)
    manager.loaded = True
    manager.known = {"klo"}
    ids = statistic_ids("klo")
    plan = manager_module.HgtRetiredPlan(("klo",), {value: {} for value in ids.values()})
    with patch.object(manager, "async_retired_plan", return_value=plan):
        await manager.async_sync_issue()
        issue = ir.async_get(hass).async_get_issue(DOMAIN, manager_module.CLEANUP_ISSUE)
        assert issue.to_json() == {**before, "translation_placeholders": None}
        flow = await repairs.async_create_fix_flow(
            hass, manager_module.CLEANUP_ISSUE, {"kind": manager_module.CLEANUP_ISSUE}
        )
        flow.hass = hass
        with patch.object(manager, "async_confirm_cleanup") as confirm:
            form = await flow.async_step_init()
        confirm.assert_not_called()
        assert form["description_placeholders"]["statistic_ids"].splitlines() == sorted(ids.values())
    response = await download(hass, hass_client, entry)
    assert response.status == 200
    assert "klo_hgt_12_20" not in json.dumps(await response.json())


@pytest.mark.parametrize("kind", ["missing", "nonpersistent", "already_minimal"])
async def test_metadata_scrub_leaves_unmatched_notices_unchanged(hass, kind):
    if kind != "missing":
        ir.async_create_issue(
            hass, DOMAIN, manager_module.CLEANUP_ISSUE,
            is_fixable=True, is_persistent=kind != "nonpersistent",
            severity=ir.IssueSeverity.WARNING,
            translation_key=manager_module.CLEANUP_ISSUE,
            translation_placeholders={"retained": "nonpersistent"} if kind == "nonpersistent" else None,
        )
    before = deepcopy(ir.async_get(hass).issues)
    with patch.object(ir, "async_create_issue") as replace:
        manager_module.async_clear_retired_issue_placeholders(hass)
    replace.assert_not_called()
    assert ir.async_get(hass).issues == before


async def test_cancelled_diagnostics_propagates_without_source_or_recorder_io(hass):
    entry = private_entry(hass)
    before = deepcopy(ir.async_get(hass).issues)
    waiting = asyncio.Event()

    async def cached_catalogue(*, load):
        assert load is False
        waiting.set()
        await asyncio.Future()

    with (
        patch("custom_components.meteoswiss.diagnostics.get_stations_map", side_effect=cached_catalogue),
        patch("custom_components.meteoswiss.stations_map.MeteoSwissStationsMap._async_content") as source,
        patch("custom_components.meteoswiss.hgt_ogd_manager.HgtOgdManager.async_load") as owners,
        patch("custom_components.meteoswiss.hgt_ogd_manager.async_metadata") as recorder,
    ):
        task = asyncio.create_task(async_get_config_entry_diagnostics(hass, entry))
        await waiting.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        source.assert_not_called()
        owners.assert_not_called()
        recorder.assert_not_called()
    assert ir.async_get(hass).issues == before
