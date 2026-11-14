"""Prove native HGT preservation and repair refresh before adopting a default."""
from datetime import timedelta
from functools import partial

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.db_schema import Statistics, StatisticsShortTerm
from homeassistant.components.recorder.statistics import (
    async_import_statistics, async_update_statistics_metadata, update_statistics_issues, validate_statistics,
)
from homeassistant.components.recorder.util import session_scope
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.components.sensor.recorder import STATE_CLASS_REMOVED_ISSUE
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from ha_helpers import async_recorder_block_till_done
from test_entity_warning_contracts import NOW, fixed_clock, installed_entities
from test_wind_recorder_contract import metadata, rows
from sqlalchemy import select


async def test_native_archival_retains_rows_and_really_clears_hgt_repair(
    recorder_mock, hass, installed_entities
):
    entry=installed_entities
    registered=er.async_get(hass).async_get(
        er.async_get(hass).async_get_entity_id('sensor','meteoswiss',f'meteoswiss_{entry.entry_id}_heating_degree_days')
    )
    eid=registered.entity_id
    archive='sensor.meteoswiss_hgt_forecast_archive_'+registered.id
    hass.states.async_set(eid,'16.4',{'unit_of_measurement':'°C·d','value_type':'forecast'})
    async_import_statistics(hass,{
        'statistic_id':eid,'source':'recorder','name':None,'unit_of_measurement':'°C·d','unit_class':None,
        'mean_type':StatisticMeanType.ARITHMETIC,'has_sum':False,
    },[{'start':NOW-timedelta(hours=1),'mean':16.4,'min':15.0,'max':17.0}])
    await async_recorder_block_till_done(hass)
    old_meta=await metadata(hass,{eid})
    old_rows=await rows(hass,{eid},NOW-timedelta(hours=2),NOW)
    await get_instance(hass).async_add_executor_job(partial(update_statistics_issues,hass))
    await hass.async_block_till_done()
    issues=ir.async_get(hass)
    assert issues.async_get_issue('sensor',f'{STATE_CLASS_REMOVED_ISSUE}_{eid}') is not None
    async_update_statistics_metadata(hass,eid,new_statistic_id=archive)
    await async_recorder_block_till_done(hass)
    await get_instance(hass).async_add_executor_job(partial(update_statistics_issues,hass))
    await hass.async_block_till_done()
    assert issues.async_get_issue('sensor',f'{STATE_CLASS_REMOVED_ISSUE}_{eid}') is None
    assert (await metadata(hass,{archive}))[archive][0]==old_meta[eid][0]
    assert not await metadata(hass,{eid})
    assert (await rows(hass,{archive},NOW-timedelta(hours=2),NOW))[archive]==old_rows[eid]
    assert hass.states.get(eid).attributes.get('state_class') is None
    assert hass.states.get(archive) is None


async def test_real_sensor_default_preserves_every_long_and_short_term_field_and_other_repairs(
    recorder_mock, hass, installed_entities, freezer
):
    entry=installed_entities;registry=er.async_get(hass)
    eid=registry.async_get_entity_id('sensor','meteoswiss',f'meteoswiss_{entry.entry_id}_heating_degree_days')
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    await sensor._hgt_statistics_task
    saved=registry.async_update_entity(eid,name='Retained forecast',icon='mdi:history',aliases={'Forecast alias'})
    archive='sensor.meteoswiss_hgt_forecast_archive_'+saved.id
    for statistic_id,unit in [(eid,'°C·d'),('sensor.unrelated_legacy_statistics','°')]:
        async_import_statistics(hass,{
            'statistic_id':statistic_id,'source':'recorder','name':None,'unit_of_measurement':unit,'unit_class':None,
            'mean_type':StatisticMeanType.ARITHMETIC,'has_sum':False,
        },[{'start':NOW-timedelta(hours=1),'mean':16.4,'min':15.0,'max':17.0}])
    hass.states.async_set('sensor.unrelated_legacy_statistics','16.4',{'unit_of_measurement':'°'})
    await async_recorder_block_till_done(hass)
    before=await metadata(hass,{eid});metadata_id=before[eid][0]

    def seed_short():
        # Fixture-only native model insertion, never integration SQL or data editing.
        with session_scope(hass=hass) as session:
            session.add(StatisticsShortTerm.from_stats(metadata_id,{
                'start':NOW-timedelta(minutes=10),'mean':16.3,'mean_weight':300.0,'min':15.1,'max':17.2,
            },now_timestamp=NOW.timestamp()))

    def snapshot():
        with session_scope(hass=hass,read_only=True) as session:
            return {model.__tablename__:[dict(row) for row in session.execute(
                select(model.__table__).where(model.metadata_id==metadata_id).order_by(model.id)
            ).mappings()] for model in (Statistics,StatisticsShortTerm)}

    await get_instance(hass).async_add_executor_job(seed_short)
    old_rows=await get_instance(hass).async_add_executor_job(snapshot)
    assert all(len(group)==1 for group in old_rows.values())
    sensor.async_write_ha_state()
    await get_instance(hass).async_add_executor_job(partial(update_statistics_issues,hass))
    await hass.async_block_till_done()
    issues=ir.async_get(hass)
    hgt_issue=f'{STATE_CLASS_REMOVED_ISSUE}_{eid}'
    other_issue=f'{STATE_CLASS_REMOVED_ISSUE}_sensor.unrelated_legacy_statistics'
    assert issues.async_get_issue('sensor',hgt_issue) and issues.async_get_issue('sensor',other_issue)

    await sensor._prepare_hgt_statistics()
    assert sensor.extra_state_attributes['hgt_statistics_status']=='ready'
    assert sensor.extra_state_attributes['forecast_statistics_archive']==archive
    assert issues.async_get_issue('sensor',hgt_issue) is None
    assert issues.async_get_issue('sensor',other_issue) is not None
    final=await metadata(hass,{eid,archive})
    assert eid not in final and final[archive][0]==metadata_id
    assert final[archive][1]=={k:archive if k=='statistic_id' else v for k,v in before[eid][1].items()}
    assert await get_instance(hass).async_add_executor_job(snapshot)==old_rows
    current=registry.async_get(eid)
    assert (current.id,current.unique_id,current.name,current.icon,current.aliases)==(saved.id,saved.unique_id,saved.name,saved.icon,saved.aliases)
    assert sensor.state_class is None and sensor.device_class is None
    assert hass.states.get(archive) is None and registry.async_get(archive) is None
    validation=await get_instance(hass).async_add_executor_job(partial(validate_statistics,hass))
    assert eid not in validation
    # Advanced Statistics can label a historical ID without a live sensor;
    # this is not the resolved persistent state-class Repair.
    assert archive in validation
    await sensor._prepare_hgt_statistics()
    assert (await metadata(hass,{archive}))[archive][0]==metadata_id
    assert await get_instance(hass).async_add_executor_job(snapshot)==old_rows
    freezer.move_to(NOW+timedelta(minutes=6))
    sensor.async_write_ha_state()
    get_instance(hass).queue_task(StatisticsTask(NOW,False))
    await async_recorder_block_till_done(hass)
    assert not await metadata(hass,{eid})
    assert await get_instance(hass).async_add_executor_job(snapshot)==old_rows
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    reloaded=hass.data[DATA_COMPONENT].get_entity(eid)
    await reloaded._hgt_statistics_task
    assert reloaded.extra_state_attributes['hgt_statistics_status']=='ready'
    assert (await metadata(hass,{archive}))[archive][0]==metadata_id
    assert await get_instance(hass).async_add_executor_job(snapshot)==old_rows
