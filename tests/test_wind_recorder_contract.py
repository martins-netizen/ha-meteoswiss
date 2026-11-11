"""Native Recorder contracts for incompatible mean algorithms and rollback."""

from datetime import timedelta
from functools import partial

import pytest
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_import_statistics,
    async_update_statistics_metadata,
    get_metadata,
    statistics_during_period,
)
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.helpers import entity_registry as er
from ha_helpers import async_recorder_block_till_done, async_wait_recording_done
from test_entity_warning_contracts import NOW, fixed_clock, installed_entities

from custom_components.meteoswiss.const import DOMAIN


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
