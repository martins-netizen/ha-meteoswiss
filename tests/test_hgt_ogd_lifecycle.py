"""Native entry, entity, translation, sharing, station-change and removal tests."""

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from ha_helpers import MockConfigEntry, async_fire_time_changed
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
    assert issue.is_fixable and issue.translation_placeholders is None
    flow = await repairs.async_create_fix_flow(
        hass, mgr.CLEANUP_ISSUE, {"kind": mgr.CLEANUP_ISSUE}
    )
    flow.hass = hass
    form = await flow.async_step_init({})
    assert form["type"] == "form"
    assert form["description_placeholders"]["statistic_ids"].splitlines() == sorted(
        statistic_ids("klo").values()
    )
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
        patch.object(coordinator.manager, "async_sync_issue", new_callable=AsyncMock) as sync,
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_update_data()
    sync.assert_not_awaited()
    await entry._async_process_on_unload(hass)


@pytest.mark.parametrize("existing_history", [False, True])
async def test_native_timer_recovers_failed_import_then_resumes_six_hour_polling(
    recorder_mock, hass, enable_custom_integrations, source_data, freezer,
    existing_history,
):
    """Exercise Core's real timer, entity availability and native Recorder rows."""
    entry = make_entry(hass, "meteoswiss")
    ids = set(statistic_ids("klo").values())
    if existing_history:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert live(hass, entry).available
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
    before = await rec._rows(hass, ids)
    original = mgr.async_import_products
    attempts = 0

    async def first_attempt_times_out(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("private_provider_marker")
        return await original(*args, **kwargs)

    with patch.object(mgr, "async_import_products", side_effect=first_attempt_times_out):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        sensor = live(hass, entry)
        coordinator = entry.runtime_data.hgt_ogd_coordinator
        assert not sensor.available and hass.states.get(sensor.entity_id).state == "unavailable"
        assert attempts == 1 and coordinator.update_interval == timedelta(hours=6)
        assert await rec._rows(hass, ids) == before

        early = NOW + timedelta(seconds=58)
        freezer.move_to(early)
        async_fire_time_changed(hass, early)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert attempts == 1 and not sensor.available

        retry = NOW + timedelta(seconds=62)
        freezer.move_to(retry)
        async_fire_time_changed(hass, retry)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert attempts == 2 and sensor.available
        assert hass.states.get(sensor.entity_id).state == "19.1"
        assert sensor.extra_state_attributes["statistics_status"] == "ready"
        after = await rec._rows(hass, ids)
        assert all(after.values())
        if existing_history:
            assert after == before

        before_regular = NOW + timedelta(hours=5)
        freezer.move_to(before_regular)
        async_fire_time_changed(hass, before_regular)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert attempts == 2

        regular = retry + timedelta(hours=6, seconds=2)
        freezer.move_to(regular)
        async_fire_time_changed(hass, regular)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert attempts == 3 and sensor.available
        assert await rec._rows(hass, ids) == after
        assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("failure", [HgtError("source_unavailable"), OSError("private_provider_marker")])
async def test_transient_retry_backoff_is_bounded_and_resets_after_success(hass, failure):
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = MeteoSwissHgtCoordinator(hass, entry, "klo", None)
    with (
        patch.object(coordinator.manager, "async_refresh", side_effect=failure) as refresh,
        patch.object(coordinator.manager, "async_sync_issue", new_callable=AsyncMock),
    ):
        for expected in [60, 120, 240, 480, 900, 900]:
            with pytest.raises(UpdateFailed) as error:
                await coordinator._async_update_data()
            assert error.value.retry_after == expected
            assert error.value.translation_key == "hgt_ogd_unavailable"
            assert "private_provider_marker" not in str(error.value)
        refresh.side_effect = None
        refresh.return_value = {"statistics_status": "ready"}
        assert await coordinator._async_update_data() == {"statistics_status": "ready"}
        refresh.side_effect = failure
        with pytest.raises(UpdateFailed) as error:
            await coordinator._async_update_data()
        assert error.value.retry_after == 60
    await entry._async_process_on_unload(hass)


@pytest.mark.parametrize("reason", ["statistics_conflict", "ownership_unavailable"])
async def test_ownership_conflicts_keep_repair_and_normal_interval(hass, reason):
    entry = MockConfigEntry(domain=DOMAIN)
    coordinator = MeteoSwissHgtCoordinator(hass, entry, "klo", None)
    with (
        patch.object(coordinator.manager, "async_refresh", side_effect=HgtError(reason)),
        patch.object(coordinator.manager, "async_sync_issue", new_callable=AsyncMock),
    ):
        with pytest.raises(UpdateFailed) as error:
            await coordinator._async_update_data()
    assert error.value.retry_after is None
    assert coordinator.update_interval == timedelta(hours=6)
    assert ir.async_get(hass).async_get_issue(DOMAIN, coordinator.issue_id) is not None
    await entry._async_process_on_unload(hass)


async def test_native_unload_cancels_pending_retry_without_recreating_statistics(
    recorder_mock, hass, enable_custom_integrations, source_data, freezer,
):
    entry = make_entry(hass, "meteoswiss")
    with patch.object(mgr, "async_import_products", side_effect=TimeoutError) as attempt:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        coordinator = entry.runtime_data.hgt_ogd_coordinator
        assert not live(hass, entry).available
        assert attempt.await_count == 1 and coordinator._unsub_refresh is not None
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert not coordinator._listeners and coordinator._unsub_refresh is None
        later = NOW + timedelta(minutes=20)
        freezer.move_to(later)
        async_fire_time_changed(hass, later)
        await hass.async_block_till_done(wait_background_tasks=True)
        attempt.assert_awaited_once()
        assert await rec.async_metadata(hass, {"klo"}) == {}


async def test_native_disabled_polling_does_not_start_a_retry_loop(
    recorder_mock, hass, enable_custom_integrations, source_data, freezer,
):
    entry = make_entry(hass, "meteoswiss")
    hass.config_entries.async_update_entry(entry, pref_disable_polling=True)
    with patch.object(mgr, "async_import_products", side_effect=TimeoutError) as attempt:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        coordinator = entry.runtime_data.hgt_ogd_coordinator
        assert not live(hass, entry).available and coordinator._unsub_refresh is None
        later = NOW + timedelta(minutes=20)
        freezer.move_to(later)
        async_fire_time_changed(hass, later)
        await hass.async_block_till_done(wait_background_tasks=True)
        attempt.assert_awaited_once()
        assert await hass.config_entries.async_unload(entry.entry_id)


async def test_native_peer_retries_share_one_verified_station_import(
    recorder_mock, hass, enable_custom_integrations, source_data, freezer,
):
    one = make_entry(hass, "meteoswiss")
    original = mgr.async_import_products
    attempts = 0

    async def first_attempt_times_out(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError
        return await original(*args, **kwargs)

    with patch.object(mgr, "async_import_products", side_effect=first_attempt_times_out):
        assert await hass.config_entries.async_setup(one.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        two = make_entry(hass, "meteoswiss")
        assert await hass.config_entries.async_setup(two.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert not live(hass, one).available and not live(hass, two).available
        # The second entry respects the manager's failed-attempt cooldown.
        assert attempts == 1 and source_data.await_count == 1
        retry = NOW + timedelta(seconds=62)
        freezer.move_to(retry)
        async_fire_time_changed(hass, retry)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert live(hass, one).available and live(hass, two).available
        assert attempts == 2 and source_data.await_count == 2
        assert len(await rec.async_metadata(hass, {"klo"})) == 3
        assert await hass.config_entries.async_unload(one.entry_id)
        assert await hass.config_entries.async_unload(two.entry_id)


async def test_cancelled_initial_import_retains_ownership_until_queued_writes_commit(
    recorder_mock, hass, source_data,
):
    """A retired station must stay attributable when native writes outlive cancellation."""
    from threading import Event

    from ha_helpers import async_recorder_block_till_done
    from homeassistant.components.recorder.tasks import ImportStatisticsTask, SynchronizeTask

    entry = make_entry(hass, "meteoswiss")
    coordinator = MeteoSwissHgtCoordinator(hass, entry, "klo", None)
    manager = coordinator.manager
    started, release = asyncio.Event(), Event()
    cleanup_barrier = asyncio.Event()
    cancelling = False
    original = ImportStatisticsTask.run
    original_queue = recorder_mock.queue_task

    def run(task, recorder):
        if task.metadata["statistic_id"].endswith("klo_hgt_12_20_daily"):
            hass.loop.call_soon_threadsafe(started.set)
            assert release.wait(5), "Test failed to release the native writer"
        return original(task, recorder)

    def queue(task):
        if cancelling and isinstance(task, SynchronizeTask):
            cleanup_barrier.set()
        original_queue(task)

    with (
        patch.object(ImportStatisticsTask, "run", run),
        patch.object(recorder_mock, "queue_task", queue),
    ):
        task = asyncio.create_task(coordinator._async_update_data())
        barrier_waiter = asyncio.create_task(cleanup_barrier.wait())
        try:
            async with asyncio.timeout(3):
                await started.wait()
            assert manager.known == {"klo"}
            assert await rec.async_metadata(hass, {"klo"}) == {}
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "station_id": "ber"}
            )
            cancelling = True
            task.cancel()
            done, _ = await asyncio.wait(
                (task, barrier_waiter), timeout=3,
                return_when=asyncio.FIRST_COMPLETED,
            )
            assert done, "Cancellation neither completed nor waited for native commit"
            known_before_commit = manager.known.copy()
        finally:
            release.set()
            barrier_waiter.cancel()
            await asyncio.gather(barrier_waiter, return_exceptions=True)
        with pytest.raises(asyncio.CancelledError):
            await task
        await async_recorder_block_till_done(hass)

    try:
        assert len(await rec.async_metadata(hass, {"klo"})) == 3
        assert known_before_commit == {"klo"}
        assert manager.known == {"klo"}
        plan = await manager.async_retired_plan()
        assert plan.stations == ("klo",) and len(plan.metadata) == 3
    finally:
        await entry._async_process_on_unload(hass)


async def test_final_native_removal_waits_for_queued_initial_import_before_cleanup(
    recorder_mock, hass, enable_custom_integrations, source_data,
):
    """Removing the final entry also clears imports queued before native unload."""
    from threading import Event

    from homeassistant.components.recorder.tasks import ImportStatisticsTask, SynchronizeTask

    entry = make_entry(hass, "meteoswiss")
    started, release = asyncio.Event(), Event()
    cleanup_barrier = asyncio.Event()
    removing = False
    original_run = ImportStatisticsTask.run
    original_queue = recorder_mock.queue_task

    def run(task, recorder):
        if task.metadata["statistic_id"].endswith("klo_hgt_12_20_daily"):
            hass.loop.call_soon_threadsafe(started.set)
            assert release.wait(5), "Test failed to release the native writer"
        return original_run(task, recorder)

    def queue(task):
        if removing and isinstance(task, SynchronizeTask):
            cleanup_barrier.set()
        original_queue(task)

    with (
        patch.object(ImportStatisticsTask, "run", run),
        patch.object(recorder_mock, "queue_task", queue),
    ):
        try:
            assert await hass.config_entries.async_setup(entry.entry_id)
            async with asyncio.timeout(3):
                await started.wait()
            manager = mgr.get_hgt_manager(hass)
            assert manager.known == {"klo"}
            assert await rec.async_metadata(hass, {"klo"}) == {}
            removing = True
            removal = asyncio.create_task(
                hass.config_entries.async_remove(entry.entry_id)
            )
            barrier_waiter = asyncio.create_task(cleanup_barrier.wait())
            try:
                done, _ = await asyncio.wait(
                    (removal, barrier_waiter), timeout=3,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                assert done, "Removal neither completed nor waited for native commit"
                known_before_commit = manager.known.copy()
            finally:
                barrier_waiter.cancel()
                await asyncio.gather(barrier_waiter, return_exceptions=True)
        finally:
            release.set()
        assert await removal
    await hass.async_block_till_done(wait_background_tasks=True)
    assert known_before_commit == {"klo"}
    assert await rec.async_metadata(hass, {"klo"}) == {}
    assert manager.known == set() and await manager.store.async_load() is None
    assert not manager.users and not manager.clients and not manager.snapshots
    assert ir.async_get(hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE) is None


async def test_slow_queued_import_does_not_hold_native_unload_cancellation(
    recorder_mock, hass, source_data, caplog,
):
    """The entry's ten-second guard must not wait for the thirty-second DB barrier."""
    from threading import Event

    from ha_helpers import async_recorder_block_till_done
    from homeassistant.components.recorder.tasks import ImportStatisticsTask

    entry = make_entry(hass, "meteoswiss")
    coordinator = MeteoSwissHgtCoordinator(hass, entry, "klo", None)
    manager = coordinator.manager
    started, release = asyncio.Event(), Event()
    original_run = ImportStatisticsTask.run
    original_wait = asyncio.wait

    def run(task, recorder):
        if task.metadata["statistic_id"].endswith("klo_hgt_12_20_daily"):
            hass.loop.call_soon_threadsafe(started.set)
            assert release.wait(5), "Test failed to release the native writer"
        return original_run(task, recorder)

    async def unload_guard(tasks, *, timeout):
        assert timeout == 10
        # Exercise Core's real pending-task guard without sleeping ten seconds.
        return await original_wait(tasks, timeout=0)

    with patch.object(ImportStatisticsTask, "run", run):
        task = entry.async_create_background_task(
            hass, coordinator._async_update_data(), "HGT blocked native import"
        )
        try:
            async with asyncio.timeout(3):
                await started.wait()
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "station_id": "ber"}
            )
            with patch("homeassistant.config_entries.asyncio.wait", unload_guard):
                await entry._async_process_on_unload(hass)
            assert task.cancelled()
            assert manager.known == {"klo"}
            assert "did not complete in time" not in caplog.text
        finally:
            release.set()
        await async_recorder_block_till_done(hass)
    plan = await manager.async_retired_plan()
    assert plan.stations == ("klo",) and len(plan.metadata) == 3
