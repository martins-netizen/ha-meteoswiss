"""Owned HGT histories stay shared, visible and consent-bound across lifecycle."""

import asyncio
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from ha_helpers import MockConfigEntry
from homeassistant.config_entries import ConfigEntryDisabler
from homeassistant.helpers import issue_registry as ir
from test_hgt_ogd_recorder import products
from test_hgt_ogd_source import NOW

from custom_components.meteoswiss import hgt_ogd_manager as mgr
from custom_components.meteoswiss import hgt_ogd_recorder as rec
from custom_components.meteoswiss import repairs
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.hgt_ogd import HgtError


@pytest.fixture
def manager(hass, monkeypatch):
    monkeypatch.setattr(mgr, "async_wait_for_writes", AsyncMock())
    item = mgr.get_hgt_manager(hass)
    item.store = SimpleNamespace(
        async_load=AsyncMock(return_value=None),
        async_save=AsyncMock(),
        async_remove=AsyncMock(),
    )
    return item


def entry(hass, station="klo", source="meteoswiss", disabled=False):
    item = MockConfigEntry(
        domain=DOMAIN,
        data={"station_id": station, "data_source": source},
        disabled_by=ConfigEntryDisabler.USER if disabled else None,
    )
    item.add_to_hass(hass)
    return item


def meta(station="klo"):
    data = rec.product_metadata(station, "daily")
    return {data["statistic_id"]: (1, data)}


async def test_owner_store_only_station_codes_and_empty_store_removed(manager):
    assert mgr.get_hgt_manager(manager.hass) is manager
    manager.store.async_load.return_value = {"stations": ["KLO", "ber"]}
    await manager.async_load()
    await manager.async_load()
    assert manager.known == {"klo", "ber"}
    manager.store.async_load.assert_awaited_once()
    await manager._save({"klo"})
    manager.store.async_save.assert_awaited_once_with({"stations": ["klo"]})
    await manager._save(set())
    manager.store.async_remove.assert_awaited_once()
    assert manager.known == set()


@pytest.mark.parametrize(
    "stored",
    [
        [],
        {},
        {"stations": None},
        {"stations": "klo"},
        {"stations": [None]},
        {"stations": ["../"]},
        {"stations": ["klo"], "payload": "unexpected"},
        {"stations": ["klo"] * 501},
    ],
)
async def test_malformed_ownership_never_guesses_existing_history(manager, stored):
    manager.store.async_load.return_value = stored
    with pytest.raises(HgtError, match="ownership_unavailable"):
        await manager.async_load()
    assert not manager.loaded and manager.known == set()
    manager.store.async_save.assert_not_awaited()


@pytest.mark.parametrize("operation", ["load", "save", "remove"])
async def test_storage_failure_is_quiet_and_preserves_owner_snapshot(
    manager, operation
):
    manager.known = {"klo"}
    getattr(manager.store, f"async_{operation}").side_effect = OSError(
        "private_path_marker"
    )
    with pytest.raises(HgtError, match="^ownership_unavailable$"):
        if operation == "load":
            await manager.async_load()
        else:
            await manager._save({"ber"} if operation == "save" else set())
    assert manager.known == {"klo"}


async def test_disabled_peers_keep_station_active_and_only_valid_station_sources_count(
    manager, hass
):
    active = entry(hass, "KLO", disabled=True)
    entry(hass, "ber", source="openmeteo")
    entry(hass, "../")
    assert manager.active_stations() == {"klo"}
    assert manager.active_stations(active.entry_id) == set()


async def test_shared_inflight_snapshot_owner_persisted_before_write_and_refresh_interval(
    manager,
):
    manager.register("one", "klo", None)
    manager.register("two", "klo", None)
    client = manager.clients["klo"]
    client.async_fetch = AsyncMock(return_value=products())
    result = {"latest_value": 19.1}

    async def import_owned(*args):
        assert manager.known == {"klo"}
        manager.store.async_save.assert_awaited_once()
        return result

    with (
        patch.object(mgr, "async_metadata", return_value={}),
        patch.object(mgr, "async_import_products", side_effect=import_owned) as write,
    ):
        values = await asyncio.gather(
            manager.async_refresh("klo", NOW), manager.async_refresh("klo", NOW)
        )
        assert values == [result, result] and write.await_count == 1
        client.async_fetch.assert_awaited_once()
        await manager.async_refresh("klo", NOW + timedelta(hours=6))
        assert write.await_count == 2
    manager.release("one", "klo")
    assert manager.clients["klo"] is client
    manager.release("two", "klo")
    manager.release("missing", "klo")
    assert (
        not manager.users
        and not manager.clients
        and not manager.snapshots
        and not manager.failures
    )


@pytest.mark.parametrize("conflict", ["preexisting", "capacity"])
async def test_unclaimed_or_too_many_profiles_cannot_be_overwritten(manager, conflict):
    manager.register("one", "klo", None)
    manager.clients["klo"].async_fetch = AsyncMock(return_value=products())
    await manager.async_load()
    if conflict == "capacity":
        manager.known = {str(n) for n in range(500)}
    with (
        patch.object(
            mgr,
            "async_metadata",
            return_value=meta() if conflict == "preexisting" else {},
        ),
        patch.object(mgr, "async_import_products", new_callable=AsyncMock) as write,
    ):
        with pytest.raises(HgtError, match="statistics_conflict"):
            await manager.async_refresh("klo", NOW)
        with pytest.raises(HgtError, match="source_unavailable"):
            await manager.async_refresh("klo", NOW + timedelta(seconds=29))
    write.assert_not_awaited()
    manager.store.async_save.assert_not_awaited()


async def test_cancel_after_claim_keeps_provenance_for_native_cleanup(manager):
    manager.register("one", "klo", None)
    manager.clients["klo"].async_fetch = AsyncMock(return_value=products())
    with (
        patch.object(mgr, "async_metadata", return_value={}),
        patch.object(mgr, "async_import_products", side_effect=asyncio.CancelledError),
    ):
        with pytest.raises(asyncio.CancelledError):
            await manager.async_refresh("klo", NOW)
    assert manager.known == {"klo"} and not manager.failures


@pytest.mark.parametrize("failure", [False, True])
async def test_unloaded_last_owner_cannot_repopulate_memory_cache(manager, failure):
    manager.register("one", "klo", None)

    async def fetch(*args):
        manager.release("one", "klo")
        if failure:
            raise OSError("private_source_marker")
        return products()

    manager.clients["klo"].async_fetch = fetch
    with (
        patch.object(mgr, "async_metadata", return_value={}),
        patch.object(mgr, "async_import_products", return_value={}),
    ):
        if failure:
            with pytest.raises(OSError):
                await manager.async_refresh("klo", NOW)
        else:
            assert await manager.async_refresh("klo", NOW) == {}
    assert not manager.clients and not manager.snapshots and not manager.failures


async def test_retired_station_visible_and_active_peer_protected(manager, hass):
    manager.store.async_load.return_value = {"stations": ["klo", "ber"]}
    item = entry(hass, "ber", disabled=True)
    with patch.object(mgr, "async_metadata", return_value=meta()) as inspect:
        plan = await manager.async_retired_plan()
        assert plan.stations == ("klo",)
        inspect.assert_awaited_once_with(hass, {"klo"})
        await manager.async_sync_issue()
    issue = ir.async_get(hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE)
    assert (
        issue.is_fixable
        and issue.is_persistent
        and issue.translation_placeholders is None
    )
    with patch.object(manager, "async_retired_plan", return_value=plan):
        flow = await repairs.async_create_fix_flow(
            hass, mgr.CLEANUP_ISSUE, {"kind": mgr.CLEANUP_ISSUE}
        )
        flow.hass = hass
        form = await flow.async_step_init()
    assert form["description_placeholders"]["statistic_ids"] == next(iter(meta()))
    assert manager.active_stations(item.entry_id) == set()


async def test_reactivation_during_inventory_refuses_stale_plan(manager, hass):
    manager.store.async_load.return_value = {"stations": ["klo"]}

    async def inspect(*args):
        entry(hass)
        return meta()

    with patch.object(mgr, "async_metadata", side_effect=inspect):
        with pytest.raises(HgtError, match="cleanup_target_changed"):
            await manager.async_retired_plan()


async def test_retired_empty_profiles_pruned_and_store_gone(manager):
    manager.store.async_load.return_value = {"stations": ["klo"]}
    with patch.object(mgr, "async_metadata", return_value={}):
        await manager.async_sync_issue()
    assert manager.known == set()
    manager.store.async_remove.assert_awaited_once()
    assert ir.async_get(manager.hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE) is None


async def test_failed_inventory_is_a_visible_nonfixable_issue(manager):
    manager.store.async_load.side_effect = OSError("private_owner_path")
    await manager.async_sync_issue()
    issue = ir.async_get(manager.hass).async_get_issue(DOMAIN, mgr.BLOCKED_ISSUE)
    assert issue is not None and not issue.is_fixable


async def test_issue_sync_waits_for_a_retired_station_refresh(manager, hass):
    item = entry(hass)
    manager.store.async_load.return_value = {"stations": ["klo"]}
    manager.register(item.entry_id, "klo", None)
    fetching, release = asyncio.Event(), asyncio.Event()

    async def fetch(*args):
        fetching.set()
        await release.wait()
        return products()

    manager.clients["klo"].async_fetch = fetch
    with (
        patch.object(mgr, "async_metadata", return_value={}),
        patch.object(mgr, "async_import_products", return_value={}) as write,
    ):
        refresh = asyncio.create_task(manager.async_refresh("klo", NOW))
        await fetching.wait()
        hass.config_entries.async_update_entry(
            item, data={**item.data, "station_id": "ber"}
        )
        sync = asyncio.create_task(manager.async_sync_issue())
        await asyncio.sleep(0)
        assert not sync.done() and manager.known == {"klo"}
        release.set()
        await refresh
        await sync
    write.assert_awaited_once()
    assert manager.known == set()


async def test_new_retired_station_during_lock_acquisition_cannot_be_pruned(manager):
    manager.store.async_load.return_value = {"stations": ["klo"]}
    await manager.async_load()
    lock = manager.locks.setdefault("klo", asyncio.Lock())
    await lock.acquire()
    sync = asyncio.create_task(manager.async_sync_issue())
    await asyncio.sleep(0)
    manager.known.add("ber")
    lock.release()
    with patch.object(mgr, "async_metadata", return_value={}):
        await sync
    assert manager.known == {"klo", "ber"}
    manager.store.async_remove.assert_not_awaited()
    assert ir.async_get(manager.hass).async_get_issue(DOMAIN, mgr.BLOCKED_ISSUE)


async def test_unconfirmed_commit_cannot_prune_empty_retired_provenance(manager):
    manager.store.async_load.return_value = {"stations": ["klo"]}
    with (
        patch.object(mgr, "async_wait_for_writes", side_effect=TimeoutError),
        patch.object(mgr, "async_metadata", new_callable=AsyncMock) as inspect,
    ):
        await manager.async_sync_issue()
    inspect.assert_not_awaited()
    manager.store.async_remove.assert_not_awaited()
    assert manager.known == {"klo"}
    assert ir.async_get(manager.hass).async_get_issue(DOMAIN, mgr.BLOCKED_ISSUE)


@pytest.mark.parametrize("mutation", ["reactivated", "metadata", "readback"])
async def test_cleanup_snapshot_and_absence_are_rechecked(manager, hass, mutation):
    manager.store.async_load.return_value = {"stations": ["klo"]}
    expected = mgr.HgtRetiredPlan(("klo",), meta())
    if mutation == "reactivated":
        entry(hass)
    with (
        patch.object(
            mgr, "async_metadata", return_value=meta() if mutation != "metadata" else {}
        ),
        patch.object(mgr, "async_clear_owned", new_callable=AsyncMock) as clear,
    ):
        with pytest.raises(
            HgtError,
            match="cleanup_not_verified"
            if mutation == "readback"
            else "cleanup_target_changed",
        ):
            await manager.async_confirm_cleanup(expected)
    assert clear.await_count == (1 if mutation == "readback" else 0)
    manager.store.async_remove.assert_not_awaited()


async def test_confirmed_cleanup_survives_ui_cancellation_and_retains_new_owner(
    manager,
):
    manager.store.async_load.return_value = {"stations": ["klo"]}
    entry(manager.hass, "ber")
    expected = mgr.HgtRetiredPlan(("klo",), meta())
    queued = asyncio.Event()
    release = asyncio.Event()

    async def clear(*args):
        queued.set()
        await release.wait()
        # An unrelated station can be claimed while this deletion is queued.
        async with manager.state_lock:
            await manager._save(manager.known | {"ber"})

    with (
        patch.object(mgr, "async_metadata", side_effect=[meta(), {}, {}]),
        patch.object(mgr, "async_clear_owned", side_effect=clear),
    ):
        task = asyncio.create_task(manager.async_confirm_cleanup(expected))
        await queued.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()
        await manager.hass.async_block_till_done(wait_background_tasks=True)
    assert manager.known == {"ber"}


async def test_empty_cleanup_is_idempotent(manager):
    await manager.async_confirm_cleanup(mgr.HgtRetiredPlan((), {}))
    assert manager.known == set()


async def test_native_repair_init_is_not_consent_and_failed_confirmation_stays_open(
    manager, hass
):
    manager.async_retired_plan = AsyncMock(
        return_value=mgr.HgtRetiredPlan(("klo",), meta())
    )
    manager.async_confirm_cleanup = AsyncMock()
    flow = await repairs.async_create_fix_flow(
        hass, mgr.CLEANUP_ISSUE, {"kind": mgr.CLEANUP_ISSUE}
    )
    flow.hass = hass
    form = await flow.async_step_init({"issue_id": mgr.CLEANUP_ISSUE})
    assert form["type"] == "form"
    manager.async_confirm_cleanup.assert_not_awaited()
    manager.async_confirm_cleanup.side_effect = TimeoutError("private_marker")
    form = await flow.async_step_confirm({})
    assert form["errors"] == {"base": "cleanup_not_verified"}
    manager.async_retired_plan.side_effect = OSError("private_marker")
    form = await flow.async_step_confirm()
    assert form["description_placeholders"] == {"statistic_ids": ""}


@pytest.mark.parametrize("remaining", [False, True])
async def test_final_native_entry_removal_has_no_unreachable_custom_repair(
    manager, hass, remaining
):
    if remaining:
        entry(hass, "ber")
    manager.async_sync_issue = AsyncMock()
    manager.async_retired_plan = AsyncMock(return_value=mgr.HgtRetiredPlan((), {}))
    manager.async_confirm_cleanup = AsyncMock()
    await manager.async_entry_removed("departed")
    assert manager.async_confirm_cleanup.await_count == (0 if remaining else 1)


async def test_final_removal_failure_keeps_nonfixable_evidence_and_never_generic_confirmation(
    manager,
):
    manager.async_sync_issue = AsyncMock()
    manager.async_retired_plan = AsyncMock(side_effect=HgtError("statistics_conflict"))
    ir.async_create_issue(
        manager.hass,
        DOMAIN,
        mgr.CLEANUP_ISSUE,
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=mgr.CLEANUP_ISSUE,
    )
    await manager.async_entry_removed("departed")
    assert ir.async_get(manager.hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE) is None
    issue = ir.async_get(manager.hass).async_get_issue(DOMAIN, mgr.BLOCKED_ISSUE)
    assert issue.is_persistent and not issue.is_fixable
