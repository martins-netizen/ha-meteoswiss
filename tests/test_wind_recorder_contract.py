"""Native Recorder contracts for incompatible mean algorithms and rollback."""

from datetime import timedelta
from functools import partial
from unittest.mock import patch

import pytest
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.db_schema import (
    Statistics,
    StatisticsMeta,
    StatisticsShortTerm,
)
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    async_update_statistics_metadata,
    get_metadata,
    statistics_during_period,
    update_statistics_issues,
)
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.components.recorder.util import session_scope
from homeassistant.components.sensor import DATA_COMPONENT, SensorStateClass
from homeassistant.components.sensor.recorder import STATE_CLASS_REMOVED_ISSUE
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.setup import async_setup_component
from sqlalchemy import select
from ha_helpers import async_recorder_block_till_done, async_wait_recording_done
from test_entity_warning_contracts import NOW, fixed_clock, installed_entities
from test_provider_device_metadata import make_entry, provider_sources

from custom_components.meteoswiss import statistics_archive
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.repair_issues import WIND_STATISTICS_BLOCKED
from custom_components.meteoswiss.sensor import MeteoSwissWindDirectionSensor


async def metadata(hass, ids):
    return await hass.async_add_executor_job(partial(get_metadata, hass, statistic_ids=ids))


async def rows(hass, ids, start, end, period="hour"):
    return await hass.async_add_executor_job(
        statistics_during_period, hass, start, end, ids, period, None, {"mean"}
    )


async def seed(hass, entity_id, mean=180):
    async_import_statistics(hass, {
        "statistic_id": entity_id, "source": "recorder", "name": None,
        "unit_of_measurement": "°", "unit_class": None,
        "mean_type": StatisticMeanType.ARITHMETIC, "has_sum": False,
    }, [{"start": NOW-timedelta(hours=1), "mean": mean, "min": 10, "max": 350}])
    await async_recorder_block_till_done(hass)


async def angle_window(hass, freezer, entity_id):
    attrs = {"unit_of_measurement": "°", "device_class": "wind_direction", "state_class": "measurement_angle"}
    hass.states.async_set(entity_id, "350", attrs)
    freezer.move_to(NOW+timedelta(minutes=2, seconds=30))
    hass.states.async_set(entity_id, "10", attrs)
    freezer.move_to(NOW+timedelta(minutes=6))
    await async_wait_recording_done(hass)
    get_instance(hass).queue_task(StatisticsTask(NOW, False))
    await async_recorder_block_till_done(hass)


async def test_direct_mean_change_keeps_old_rows_but_stops_new_statistics(
    recorder_mock, hass, installed_entities, freezer
):
    eid=er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_{installed_entities.entry_id}_wind_direction")
    await seed(hass,eid)
    await angle_window(hass,freezer,eid)
    assert (await rows(hass,{eid},NOW,None,"5minute")).get(eid,[]) == []
    assert (await rows(hass,{eid},NOW-timedelta(hours=1),NOW))[eid][0]["mean"] == 180


async def test_archive_retains_metadata_row_and_new_angles_compile_with_same_entity_id(
    recorder_mock, hass, installed_entities, freezer
):
    registry=er.async_get(hass)
    uid=f"{DOMAIN}_{installed_entities.entry_id}_wind_direction"
    eid=registry.async_get_entity_id("sensor",DOMAIN,uid)
    kept=registry.async_update_entity(eid,name="Retained wind",icon="mdi:compass",aliases={"Wind alias"})
    archive="sensor.meteoswiss_wind_arithmetic_"+kept.id
    await seed(hass,eid)
    old=await metadata(hass,{eid})
    old_rows=await rows(hass,{eid},NOW-timedelta(hours=1),NOW)
    async_update_statistics_metadata(hass,eid,new_statistic_id=archive)
    await async_recorder_block_till_done(hass)
    archived=await metadata(hass,{archive})
    assert archived[archive][0] == old[eid][0]
    assert archived[archive][1]["mean_type"] == StatisticMeanType.ARITHMETIC
    assert (await rows(hass,{archive},NOW-timedelta(hours=1),NOW))[archive] == old_rows[eid]
    assert not await metadata(hass,{eid})
    await angle_window(hass,freezer,eid)
    new=(await rows(hass,{eid},NOW,None,"5minute"))[eid]
    assert len(new)==1
    assert min(abs(new[0]["mean"]),abs(360-new[0]["mean"])) < 0.001
    assert (await metadata(hass,{eid}))[eid][1]["mean_type"] == StatisticMeanType.CIRCULAR
    assert registry.async_get_entity_id("sensor",DOMAIN,uid)==eid
    current=registry.async_get(eid)
    assert (current.id,current.device_id,current.name,current.icon,current.aliases)==(kept.id,kept.device_id,"Retained wind","mdi:compass",{"Wind alias"})
    assert (await rows(hass,{archive},NOW-timedelta(hours=1),NOW))[archive] == old_rows[eid]


async def test_occupied_archive_does_not_overwrite_either_series(
    recorder_mock,hass,installed_entities
):
    eid=er.async_get(hass).async_get_entity_id("sensor",DOMAIN,f"{DOMAIN}_{installed_entities.entry_id}_wind_direction")
    archive="sensor.existing_wind_arithmetic_archive"
    await seed(hass,eid,180)
    await seed(hass,archive,90)
    before=await metadata(hass,{eid,archive})
    async_update_statistics_metadata(hass,eid,new_statistic_id=archive)
    await async_recorder_block_till_done(hass)
    assert await metadata(hass,{eid,archive}) == before
    values=await rows(hass,{eid,archive},NOW-timedelta(hours=1),NOW)
    assert values[eid][0]["mean"]==180 and values[archive][0]["mean"]==90


async def test_rollback_can_preserve_both_algorithms_under_separate_ids(
    recorder_mock,hass,installed_entities,freezer
):
    eid=er.async_get(hass).async_get_entity_id("sensor",DOMAIN,f"{DOMAIN}_{installed_entities.entry_id}_wind_direction")
    archive="sensor.old_arithmetic_wind_archive"
    circular="sensor.new_circular_wind_archive"
    await seed(hass,eid)
    old_id=(await metadata(hass,{eid}))[eid][0]
    async_update_statistics_metadata(hass,eid,new_statistic_id=archive)
    await async_recorder_block_till_done(hass)
    await angle_window(hass,freezer,eid)
    new_id=(await metadata(hass,{eid}))[eid][0]
    assert new_id != old_id
    async_update_statistics_metadata(hass,eid,new_statistic_id=circular)
    await async_recorder_block_till_done(hass)
    async_update_statistics_metadata(hass,archive,new_statistic_id=eid)
    await async_recorder_block_till_done(hass)
    final=await metadata(hass,{eid,archive,circular})
    assert archive not in final
    assert final[eid][0]==old_id and final[eid][1]["mean_type"]==StatisticMeanType.ARITHMETIC
    assert final[circular][0]==new_id and final[circular][1]["mean_type"]==StatisticMeanType.CIRCULAR


def recorder_snapshot(hass, metadata_ids):
    """Read the physical rows, including keys, means and weights, for both series."""
    with session_scope(hass=hass, read_only=True) as session:
        return {
            model.__tablename__: session.execute(
                select(model.__table__)
                .where(
                    (model.id if model is StatisticsMeta else model.metadata_id).in_(
                        metadata_ids
                    )
                )
                .order_by(model.id)
            ).tuples().all()
            for model in (StatisticsMeta, Statistics, StatisticsShortTerm)
        }


@pytest.mark.parametrize(
    "deleted_claims,live_archive,has_circular_series,ready",
    [
        pytest.param((), False, True, True, id="verified-archive"),
        pytest.param(("unrelated",), False, True, True, id="unrelated-deleted-entity"),
        pytest.param(("archive",), False, True, True, id="deleted-archive-claim"),
        pytest.param(("sensor",), False, True, False, id="previous-active-id-owner"),
        pytest.param(("sensor", "archive"), False, True, False, id="both-deleted-claims"),
        pytest.param(("archive",), True, True, False, id="archive-still-live"),
        pytest.param(("archive",), False, False, False, id="no-existing-circular-series"),
    ],
)
async def test_existing_circular_statistics_and_archived_series_ownership(
    recorder_mock, hass, enable_custom_integrations, provider_sources, freezer,
    deleted_claims, live_archive, has_circular_series, ready,
):
    entry = make_entry(hass, DOMAIN)
    registry = er.async_get(hass)

    def delete_foreign_owner(object_id):
        foreign = registry.async_get_or_create(
            "sensor", "foreign", object_id, suggested_object_id=object_id,
        )
        assert foreign.entity_id == f"sensor.{object_id}"
        registry.async_remove(foreign.entity_id)
        assert registry.async_get(foreign.entity_id) is None

    object_id = "retained_wind"
    if "sensor" in deleted_claims:
        delete_foreign_owner(object_id)
    owner = registry.async_get_or_create(
        "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_wind_direction",
        config_entry=entry, suggested_object_id=object_id,
    )
    sensor_id = owner.entity_id
    assert sensor_id == f"sensor.{object_id}"
    archive_object_id = f"meteoswiss_wind_arithmetic_{owner.id}"
    archive_id = f"sensor.{archive_object_id}"
    if "archive" in deleted_claims:
        delete_foreign_owner(archive_object_id)
    if "unrelated" in deleted_claims:
        delete_foreign_owner("unrelated_deleted_wind")
    if live_archive:
        hass.states.async_set(archive_id, "218")
    claim_ids = {
        "sensor": sensor_id, "archive": archive_id, "unrelated": "sensor.unrelated_deleted_wind"
    }
    assert {old.entity_id for old in registry.deleted_entities.values()} == {
        claim_ids[claim] for claim in deleted_claims
    }

    assert await async_setup_component(hass, "sensor", {})
    await seed(hass, archive_id, 218)
    if has_circular_series:
        await angle_window(hass, freezer, sensor_id)
        circular_metadata = (await metadata(hass, {sensor_id}))[sensor_id][1]
        async_import_statistics(
            hass, circular_metadata,
            [{"start": NOW - timedelta(hours=1), "mean": 352, "mean_weight": 3600}],
        )
        await async_recorder_block_till_done(hass)

    ids = {sensor_id, archive_id}
    before = await metadata(hass, ids)
    assert before[archive_id][1]["mean_type"] == StatisticMeanType.ARITHMETIC
    if has_circular_series:
        assert before[sensor_id][1]["mean_type"] == StatisticMeanType.CIRCULAR
    metadata_ids = {item[0] for item in before.values()}
    instance = get_instance(hass)
    snapshot = await instance.async_add_executor_job(recorder_snapshot, hass, metadata_ids)
    assert len(snapshot["statistics"]) == (2 if has_circular_series else 1)
    assert len(snapshot["statistics_short_term"]) == int(has_circular_series)

    issues = ir.async_get(hass)
    core_issue_id = f"{STATE_CLASS_REMOVED_ISSUE}_{sensor_id}"
    archive_claim_only = ready and "archive" in deleted_claims
    if archive_claim_only:
        # Recreate Core's old warning from a numeric state without a state class.
        hass.states.async_set(sensor_id, "350", {"unit_of_measurement": "°"})
        await instance.async_add_executor_job(partial(update_statistics_issues, hass))
        await hass.async_block_till_done()
        assert issues.async_get_issue("sensor", core_issue_id) is not None
    if has_circular_series:
        assert hass.states.async_remove(sensor_id)

    with patch.object(statistics_archive, "async_update_statistics_metadata") as rename:
        for load in (hass.config_entries.async_setup, hass.config_entries.async_reload):
            assert await load(entry.entry_id)
            await hass.async_block_till_done()
            sensor = hass.data[DATA_COMPONENT].get_entity(sensor_id)
            assert isinstance(sensor, MeteoSwissWindDirectionSensor)
            await sensor._statistics_task
            assert sensor.state_class == (SensorStateClass.MEASUREMENT_ANGLE if ready else None)
            if archive_claim_only:
                assert issues.async_get_issue("sensor", core_issue_id) is None

            sensor.coordinator.async_set_updated_data({"wind_speed": 8, "wind_direction": 350})
            await hass.async_block_till_done()
            state = hass.states.get(sensor_id)
            assert float(state.state) == 350
            assert state.attributes["wind_statistics_status"] == ("ready" if ready else "blocked")
            assert state.attributes["arithmetic_statistics_archive"] == (
                archive_id if ready and not archive_claim_only else None
            )

            await instance.async_add_executor_job(partial(update_statistics_issues, hass))
            await hass.async_block_till_done()
            core_repair = issues.async_get_issue("sensor", core_issue_id)
            assert (core_repair is not None) == (has_circular_series and not ready)
            wind_repair = issues.async_get_issue(DOMAIN, f"{WIND_STATISTICS_BLOCKED}_{entry.entry_id}")
            assert (wind_repair is None) == ready
            assert registry.async_get(sensor_id).id == owner.id
            assert await metadata(hass, ids) == before
            assert await instance.async_add_executor_job(recorder_snapshot, hass, metadata_ids) == snapshot

    rename.assert_not_called()
    if archive_claim_only:
        next_window = NOW + timedelta(minutes=10)
        for offset, direction in ((0, 340), (150, 20)):
            freezer.move_to(next_window + timedelta(seconds=offset))
            sensor.coordinator.async_set_updated_data({"wind_speed": 8, "wind_direction": direction})
        freezer.move_to(next_window + timedelta(minutes=6))
        await async_wait_recording_done(hass)
        instance.queue_task(StatisticsTask(next_window, False))
        await async_recorder_block_till_done(hass)
        new_angles = (await rows(hass, {sensor_id}, next_window, None, "5minute"))[sensor_id]
        assert len(new_angles) == 1
        mean = new_angles[0]["mean"]
        assert min(abs(mean), abs(360 - mean)) < 0.001
        assert await metadata(hass, ids) == before
    assert await hass.config_entries.async_unload(entry.entry_id)
