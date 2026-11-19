"""Verify historical series ownership against the native registry and Recorder."""

from datetime import timedelta
from functools import partial
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import async_import_statistics, get_metadata
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.helpers import entity_registry as er

from custom_components.meteoswiss import forecast_statistics, statistics_archive, wind_statistics
from custom_components.meteoswiss.forecast_statistics import async_prepare_hgt_statistics
from custom_components.meteoswiss.wind_statistics import async_prepare_wind_statistics
from ha_helpers import async_recorder_block_till_done
from test_entity_warning_contracts import NOW, fixed_clock, installed_entities
from test_wind_recorder_contract import metadata, rows


@pytest.fixture(
    params=[
        (async_prepare_hgt_statistics, "hgt_forecast_archive", "°C·d"),
        (async_prepare_wind_statistics, "wind_arithmetic", "°"),
    ],
    ids=["hgt", "wind"],
)
def migration(request):
    return request.param


def register(registry, entity_id, platform="meteoswiss"):
    entry = registry.async_get_or_create(
        "sensor", platform, entity_id, suggested_object_id=entity_id.removeprefix("sensor.")
    )
    assert entry.entity_id == entity_id
    return entry


async def seed_history(hass, statistic_id, unit):
    async_import_statistics(
        hass,
        {
            "statistic_id": statistic_id, "source": "recorder", "name": None,
            "unit_of_measurement": unit, "unit_class": None,
            "mean_type": StatisticMeanType.ARITHMETIC, "has_sum": False,
        },
        [{"start": NOW - timedelta(hours=1), "mean": 12.0, "min": 7.0, "max": 17.0}],
    )
    await async_recorder_block_till_done(hass)


@pytest.mark.parametrize("conflict", ["source", "saved_archive", "empty_destination"])
async def test_retained_registry_history_blocks_ambiguous_archive(
    recorder_mock, hass, fixed_clock, migration, conflict
):
    prepare, prefix, unit = migration
    registry = er.async_get(hass)
    source = "sensor.historical_series"
    if conflict == "source":
        register(registry, source, "other")
        registry.async_remove(source)
    owner = register(registry, source)
    archive = f"sensor.meteoswiss_{prefix}_{owner.id}"
    if conflict != "source":
        register(registry, archive, "other")
        registry.async_remove(archive)
    statistic_id = archive if conflict == "saved_archive" else source
    await seed_history(hass, statistic_id, unit)
    ids = {source, archive}
    before = await metadata(hass, ids)
    with patch.object(statistics_archive, "async_update_statistics_metadata") as rename:
        result = await prepare(hass, source, owner.id)
    assert not result.ready and result.archive_id is None
    rename.assert_not_called()
    assert await metadata(hass, ids) == before
    assert (await rows(hass, ids, NOW - timedelta(hours=2), NOW))[statistic_id][0]["mean"] == 12.0


@pytest.mark.parametrize("change", ["reassigned_source", "registered_archive", "live_archive"])
async def test_ownership_changes_during_first_recorder_read(
    recorder_mock, hass, fixed_clock, migration, change
):
    prepare, prefix, unit = migration
    registry = er.async_get(hass)
    source = "sensor.historical_series"
    owner = register(registry, source)
    archive = f"sensor.meteoswiss_{prefix}_{owner.id}"
    await seed_history(hass, source, unit)
    ids = {source, archive}
    before = await metadata(hass, ids)
    recorder = get_instance(hass)
    run = recorder.async_add_executor_job

    async def change_ownership(job, *args):
        result = await run(job, *args)
        if isinstance(job, partial) and job.func is get_metadata:
            if change == "reassigned_source":
                registry.async_remove(source)
                register(registry, source, "other")
            elif change == "registered_archive":
                register(registry, archive, "other")
            else:
                hass.states.async_set(archive, "8")
        return result

    with (
        patch.object(recorder, "async_add_executor_job", side_effect=change_ownership),
        patch.object(statistics_archive, "async_update_statistics_metadata") as rename,
    ):
        result = await prepare(hass, source, owner.id)
    assert not result.ready and result.archive_id is None
    rename.assert_not_called()
    assert await metadata(hass, ids) == before


async def test_claim_after_queue_blocks_completion_and_retry_reads_the_same_row(
    recorder_mock, hass, fixed_clock, migration
):
    prepare, prefix, unit = migration
    registry = er.async_get(hass)
    source = "sensor.historical_series"
    owner = register(registry, source)
    archive = f"sensor.meteoswiss_{prefix}_{owner.id}"
    await seed_history(hass, source, unit)
    ids = {source, archive}
    row_id, original = (await metadata(hass, ids))[source]
    native_rename = statistics_archive.async_update_statistics_metadata

    def claim_after_queue(*args, **kwargs):
        native_rename(*args, **kwargs)
        hass.states.async_set(archive, "8")

    with patch.object(statistics_archive, "async_update_statistics_metadata", side_effect=claim_after_queue):
        blocked = await prepare(hass, source, owner.id)
    assert not blocked.ready and blocked.archive_id is None
    assert await metadata(hass, ids) == {archive: (row_id, dict(original, statistic_id=archive))}
    hass.states.async_remove(archive)
    with patch.object(statistics_archive, "async_update_statistics_metadata") as rename:
        retried = await prepare(hass, source, owner.id)
    assert retried.ready and retried.archive_id == archive
    rename.assert_not_called()
    assert (await rows(hass, ids, NOW - timedelta(hours=2), NOW))[archive][0]["mean"] == 12.0


@pytest.mark.parametrize("metric,stage", [
    ("wind_direction", "start"), ("wind_direction", "recorder"),
    ("heating_degree_days", "start"), ("heating_degree_days", "recorder"),
    ("heating_degree_days", "issue_refresh"),
])
async def test_sensor_does_not_publish_migration_results_for_a_replacement(
    hass, installed_entities, metric, stage
):
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", "meteoswiss", f"meteoswiss_{installed_entities.entry_id}_{metric}"
    )
    sensor = hass.data[DATA_COMPONENT].get_entity(entity_id)
    if metric == "wind_direction":
        await sensor._statistics_task
        module, prepare = wind_statistics, "async_prepare_wind_statistics"
        run_sensor, result = sensor._prepare_statistics, wind_statistics.WindStatisticsResult(True)
    else:
        await sensor._hgt_statistics_task
        module, prepare = forecast_statistics, "async_prepare_hgt_statistics"
        run_sensor, result = sensor._prepare_hgt_statistics, forecast_statistics.ForecastStatisticsResult(True)
    replacement = register(registry, "sensor.replacement", "other")
    lookup = registry.async_get
    reassigned = stage == "start"

    def lookup_after_reassignment(requested_id):
        return replacement if reassigned and requested_id == entity_id else lookup(requested_id)

    async def prepare_series(*args):
        nonlocal reassigned
        reassigned = stage == "recorder"
        return result

    async def refresh(*args):
        nonlocal reassigned
        reassigned = stage == "issue_refresh"

    with (
        patch.object(registry, "async_get", side_effect=lookup_after_reassignment),
        patch.object(module, prepare, new_callable=AsyncMock, side_effect=prepare_series) as migration_call,
        patch.object(forecast_statistics, "async_refresh_statistics_issues", side_effect=refresh),
        patch.object(registry, "async_update_entity") as update_registry,
        patch.object(sensor, "async_write_ha_state") as publish,
    ):
        await run_sensor()
    assert reassigned
    assert migration_call.await_count == (0 if stage == "start" else 1)
    assert publish.call_count == (0 if stage == "start" else 1)
    update_registry.assert_not_called()


async def test_detached_sensor_does_not_adopt_the_name_left_in_the_registry(hass, installed_entities):
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", "meteoswiss", f"meteoswiss_{installed_entities.entry_id}_wind_direction"
    )
    sensor = hass.data[DATA_COMPONENT].get_entity(entity_id)
    await sensor._statistics_task
    with (
        patch.object(sensor, "registry_entry", None),
        patch.object(wind_statistics, "async_prepare_wind_statistics") as prepare,
        patch.object(sensor, "async_write_ha_state") as publish,
    ):
        await sensor._prepare_statistics()
    prepare.assert_not_awaited()
    publish.assert_not_called()
