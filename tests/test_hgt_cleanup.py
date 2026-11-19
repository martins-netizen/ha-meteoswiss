"""Upgrade inventories, real native deletion and explicit repair consent."""

import asyncio
from datetime import timedelta
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.db_schema import Statistics, StatisticsShortTerm, StatisticsMeta
from homeassistant.components.recorder.models import StatisticMeanType as Mean
from homeassistant.components.recorder.statistics import async_import_statistics, get_metadata
from homeassistant.components.recorder.tasks import StatisticsTask
from homeassistant.components.repairs import issue_handler
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component
from ha_helpers import MockConfigEntry, async_recorder_block_till_done, async_wait_recording_done

from custom_components.meteoswiss import hgt_cleanup as hc, hgt_ogd_recorder, repairs
from custom_components.meteoswiss.const import DOMAIN
from test_entity_warning_contracts import NOW, fixed_clock
from test_entity_warning_contracts import installed_entities
from test_provider_device_metadata import provider_sources


@pytest.fixture
def entry(hass):
    item=MockConfigEntry(domain=DOMAIN);item.add_to_hass(hass)
    return item


def registered(hass, entry, key='heating_degree_days', disabled=False):
    return er.async_get(hass).async_get_or_create('sensor',DOMAIN,f'{DOMAIN}_{entry.entry_id}_{key}',
        config_entry=entry,disabled_by=er.RegistryEntryDisabler.USER if disabled else None)


def metadata(statistic_id, **changes):
    return {'source':'recorder','statistic_id':statistic_id,'name':None,
            'unit_of_measurement':'°C·d','unit_class':None,'mean_type':Mean.ARITHMETIC,'has_sum':False,**changes}


@pytest.fixture
async def fake_recorder(hass):
    hass.config.components.add('recorder')
    ready=hass.loop.create_future();ready.set_result(True)
    instance=SimpleNamespace(async_db_ready=ready,async_add_executor_job=AsyncMock(return_value={}),async_clear_statistics=lambda *a,**k:None)
    with (
        patch.object(hc, 'get_instance', return_value=instance),
        patch.object(hgt_ogd_recorder, 'get_instance', return_value=instance),
    ):
        yield instance


async def test_missing_recorder_needs_no_database(hass):
    assert await hc.async_plan_cleanup(hass,'missing')==hc.HgtCleanupPlan((),{})
    await hc.async_check_cleanup(hass,'missing')


@pytest.mark.parametrize('foreign',[False,True])
async def test_missing_or_foreign_entry_is_refused(hass,fake_recorder,foreign):
    item=MockConfigEntry(domain='other');item.add_to_hass(hass)
    with pytest.raises(ValueError,match='entry_unavailable'):
        await hc.async_plan_cleanup(hass,item.entry_id if foreign else 'missing')


async def test_unavailable_database_is_not_empty_success(hass,entry,fake_recorder):
    fake_recorder.async_db_ready=hass.loop.create_future();fake_recorder.async_db_ready.set_result(False)
    with pytest.raises(ValueError,match='recorder_not_ready'):await hc.async_plan_cleanup(hass,entry.entry_id)


@pytest.mark.parametrize('disabled',[False,True])
async def test_daily_season_disabled_and_tombstone_ownership(hass,entry,fake_recorder,disabled):
    daily=registered(hass,entry,disabled=disabled)
    season=registered(hass,entry,'season_hgt');er.async_get(hass).async_remove(season.entity_id)
    unrelated=registered(hass,entry,'wind_direction')
    foreign=MockConfigEntry(domain=DOMAIN);foreign.add_to_hass(hass);registered(hass,foreign)
    archive='sensor.meteoswiss_hgt_forecast_archive_'+daily.id
    fake_recorder.async_add_executor_job.return_value={
        daily.entity_id:(1,metadata(daily.entity_id)),archive:(2,metadata(archive)),
        season.entity_id:(3,metadata(season.entity_id,has_sum=True,mean_type=Mean.NONE))}
    plan=await hc.async_plan_cleanup(hass,entry.entry_id)
    assert {b[2] for b in plan.bindings}=={'daily','season'}
    assert len(plan.metadata)==3 and unrelated.entity_id not in plan.metadata
    await hc.async_check_cleanup(hass,entry.entry_id)
    issue=ir.async_get(hass).async_get_issue(DOMAIN,f'{hc.ISSUE}_{entry.entry_id}')
    assert issue.is_fixable and issue.data=={'entry_id':entry.entry_id}


@pytest.mark.parametrize('field,value',[('source','foreign'),('unit_of_measurement','°C'),('has_sum',True),('mean_type',Mean.CIRCULAR)])
async def test_conflicting_metadata_cannot_be_deleted(hass,entry,fake_recorder,field,value):
    daily=registered(hass,entry)
    fake_recorder.async_add_executor_job.return_value={daily.entity_id:(1,metadata(daily.entity_id,**{field:value}))}
    with pytest.raises(ValueError,match='statistics_metadata_conflict'):await hc.async_plan_cleanup(hass,entry.entry_id)


@pytest.mark.parametrize('occupied',['registry','state'])
async def test_archive_collision_is_refused(hass,entry,fake_recorder,occupied):
    daily=registered(hass,entry);archive='sensor.meteoswiss_hgt_forecast_archive_'+daily.id
    if occupied=='state':hass.states.async_set(archive,'1')
    else:er.async_get(hass).async_get_or_create('sensor','foreign','foreign',suggested_object_id=archive.split('.')[1])
    with pytest.raises(ValueError,match='archive_identity_conflict'):await hc.async_plan_cleanup(hass,entry.entry_id)


async def test_forecast_measurement_customisation_must_be_fixed_first(hass,entry,fake_recorder):
    daily=registered(hass,entry);hass.states.async_set(daily.entity_id,'1',{'state_class':'measurement'})
    with pytest.raises(ValueError,match='forecast_statistics_still_enabled'):await hc.async_plan_cleanup(hass,entry.entry_id)
    await hc.async_check_cleanup(hass,entry.entry_id)
    issue=ir.async_get(hass).async_get_issue(DOMAIN,f'{hc.ISSUE}_{entry.entry_id}')
    assert not issue.is_fixable


async def test_deleted_entity_reused_by_another_owner_is_refused(hass,entry,fake_recorder):
    old=registered(hass,entry);registry=er.async_get(hass);registry.async_remove(old.entity_id)
    registry.async_get_or_create('sensor','foreign','foreign',suggested_object_id=old.entity_id.split('.')[1])
    with pytest.raises(ValueError,match='entity_identity_conflict'):await hc.async_plan_cleanup(hass,entry.entry_id)


@pytest.mark.parametrize(
    ("target_kind", "conflict"),
    [
        ("entity", "entity_identity_conflict"),
        ("archive", "archive_identity_conflict"),
        ("measurement", "forecast_statistics_still_enabled"),
        ("archive_state", "archive_identity_conflict"),
    ],
)
async def test_confirm_refuses_foreign_reuse_during_metadata_read(
    hass, entry, fake_recorder, target_kind, conflict
):
    """A newly occupied ID must not be deleted under an older confirmation."""
    registry = er.async_get(hass)
    daily = registered(hass, entry)
    registry.async_remove(daily.entity_id)
    target = (
        daily.entity_id if target_kind in {"entity", "measurement"}
        else f"sensor.meteoswiss_hgt_forecast_archive_{daily.id}"
    )
    records = {target: (1, metadata(target))}
    fake_recorder.async_add_executor_job.return_value = records
    expected = await hc.async_plan_cleanup(hass, entry.entry_id)
    cleared = []

    def clear(ids, **kwargs):
        cleared.extend(ids)
        kwargs["on_done"]()

    async def read(_job):
        if target_kind == "measurement":
            hass.states.async_set(target, "0", {"state_class": "measurement"})
        elif target_kind == "archive_state":
            hass.states.async_set(target, "0")
        else:
            registry.async_get_or_create(
                "sensor", "foreign", "later", suggested_object_id=target.split(".", 1)[1]
            )
        return records

    fake_recorder.async_clear_statistics = clear
    fake_recorder.async_add_executor_job.side_effect = read
    with pytest.raises(ValueError, match=conflict):
        await hc.async_confirm_cleanup(hass, entry.entry_id, expected)
    assert cleared == []


@pytest.mark.parametrize("target_kind", ["entity", "archive"])
async def test_removed_foreign_owner_blocks_only_an_existing_conflicting_series(
    hass, entry, fake_recorder, target_kind
):
    """A second tombstone proves the same ID also belonged to another entity."""
    registry = er.async_get(hass)
    daily = registered(hass, entry)
    registry.async_remove(daily.entity_id)
    archive = f"sensor.meteoswiss_hgt_forecast_archive_{daily.id}"
    target = daily.entity_id if target_kind == "entity" else archive
    other = archive if target_kind == "entity" else daily.entity_id
    foreign = registry.async_get_or_create(
        "sensor", "foreign", "previous", suggested_object_id=target.split(".", 1)[1]
    )
    registry.async_remove(foreign.entity_id)
    fake_recorder.async_add_executor_job.return_value = {other: (2, metadata(other))}
    plan = await hc.async_plan_cleanup(hass, entry.entry_id)
    assert set(plan.metadata) == {other}

    fake_recorder.async_add_executor_job.return_value = {target: (1, metadata(target))}
    with pytest.raises(ValueError, match="identity_conflict"):
        await hc.async_plan_cleanup(hass, entry.entry_id)


async def test_inventory_does_not_accept_extra_metadata_or_changed_registry(hass,entry,fake_recorder):
    registered(hass,entry)
    fake_recorder.async_add_executor_job.return_value={'sensor.foreign':(1,metadata('sensor.foreign'))}
    with pytest.raises(ValueError,match='unexpected_statistics'):await hc.async_plan_cleanup(hass,entry.entry_id)
    fake_recorder.async_add_executor_job.return_value={}
    real=hc._bindings
    with patch.object(hc,'_bindings',side_effect=[real(hass,entry.entry_id),()]):
        with pytest.raises(ValueError,match='ownership_changed'):await hc.async_plan_cleanup(hass,entry.entry_id)


async def test_setup_schedules_inspection_and_unload_removes_only_own_issue(hass,entry):
    with patch.object(hc,'async_at_started') as start,patch.object(entry,'async_on_unload') as unload,patch.object(entry,'async_create_background_task') as task:
        hc.async_setup_cleanup(hass,entry)
        with patch.object(hc,'async_check_cleanup',new_callable=AsyncMock) as check:
            start.call_args.args[1](hass)
            task.call_args.args[1].close()
            assert task.call_args.args[2]=='MeteoSwiss HGT upgrade cleanup'
        unload.call_args_list[1].args[0]()


@pytest.mark.parametrize('after_kind',['success','rows_remain','binding_changed'])
async def test_native_queue_completion_and_readback_required(hass,entry,fake_recorder,after_kind):
    plan=hc.HgtCleanupPlan((('sensor.a','a'*32,'daily'),),{'sensor.a':(1,metadata('sensor.a'))})
    after=hc.HgtCleanupPlan(plan.bindings,{}) if after_kind=='success' else plan if after_kind=='rows_remain' else hc.HgtCleanupPlan((),{})
    seen=[]
    def clear(ids,**kwargs):seen.append(ids);kwargs['on_done']()
    fake_recorder.async_clear_statistics=clear
    with patch.object(hc,'async_plan_cleanup',side_effect=[plan,after]),patch.object(hc,'async_refresh_statistics_issues',new_callable=AsyncMock) as refresh:
        if after_kind=='success':
            await hc.async_confirm_cleanup(hass,entry.entry_id,plan);refresh.assert_awaited_once()
        else:
            with pytest.raises(ValueError,match='cleanup_not_verified'):await hc.async_confirm_cleanup(hass,entry.entry_id,plan)
            refresh.assert_not_awaited()
    assert seen==[['sensor.a']]


async def test_changed_consent_snapshot_does_not_submit_delete(hass,entry,fake_recorder):
    with patch.object(hc,'async_plan_cleanup',return_value=hc.HgtCleanupPlan((),{})):
        with pytest.raises(ValueError,match='cleanup_target_changed'):
            await hc.async_confirm_cleanup(hass,entry.entry_id,hc.HgtCleanupPlan((),{'sensor.x':(1,{})}))


async def test_empty_confirm_is_idempotent(hass,entry,fake_recorder):
    with patch.object(hc,'async_refresh_statistics_issues',new_callable=AsyncMock):
        await hc.async_confirm_cleanup(hass,entry.entry_id,hc.HgtCleanupPlan((),{}))


@pytest.mark.parametrize('data',[None,{}, {'entry_id':'missing'}])
async def test_fix_flow_cannot_bind_arbitrary_issue(hass,data):
    with pytest.raises(ValueError):await repairs.async_create_fix_flow(hass,'foreign_issue',data)


@pytest.mark.parametrize('foreign',[False,True])
async def test_fix_flow_cannot_bind_missing_or_foreign_entry(hass,foreign):
    item=MockConfigEntry(domain='foreign');item.add_to_hass(hass);eid=item.entry_id if foreign else 'missing'
    with pytest.raises(ValueError,match='entry_unavailable'):
        await repairs.async_create_fix_flow(hass,f'{hc.ISSUE}_{eid}',{'entry_id':eid})


async def test_opening_repair_is_not_consent_even_with_core_init_payload(hass,entry):
    flow=await repairs.async_create_fix_flow(hass,f'{hc.ISSUE}_{entry.entry_id}',{'entry_id':entry.entry_id})
    flow.hass=hass
    with patch.object(repairs,'async_plan_cleanup',return_value=hc.HgtCleanupPlan((),{})),patch.object(repairs,'async_confirm_cleanup',new_callable=AsyncMock) as clear:
        result=await flow.async_step_init({'issue_id':f'{hc.ISSUE}_{entry.entry_id}'})
        assert result['type']=='form';clear.assert_not_awaited()
        result=await flow.async_step_confirm({})
        assert result['type']=='create_entry';clear.assert_awaited_once()


async def test_repair_error_does_not_finish_or_repeat_write(hass,entry):
    flow=repairs.HgtCleanupRepairFlow(entry.entry_id);flow.hass=hass
    with patch.object(repairs,'async_plan_cleanup',side_effect=RuntimeError('private failure')):
        result=await flow.async_step_confirm()
    assert result['errors']=={'base':'cleanup_not_verified'}
    with patch.object(repairs,'async_plan_cleanup',return_value=hc.HgtCleanupPlan((),{})),patch.object(repairs,'async_confirm_cleanup',side_effect=TimeoutError) as clear:
        result=await flow.async_step_confirm({})
    assert result['type']=='form' and clear.await_count==1


async def test_native_repairs_manager_requires_confirmation_and_refreshes_live_attribute(
    recorder_mock,hass,installed_entities
):
    entry=installed_entities
    registry=er.async_get(hass)
    entity_id=registry.async_get_entity_id('sensor',DOMAIN,f'{DOMAIN}_{entry.entry_id}_heating_degree_days')
    registered=registry.async_get(entity_id)
    archive='sensor.meteoswiss_hgt_forecast_archive_'+registered.id
    from homeassistant.components.sensor import DATA_COMPONENT
    sensor=hass.data[DATA_COMPONENT].get_entity(entity_id)
    if task := getattr(sensor,'_hgt_statistics_task',None):
        await task
    sensor._hgt_statistics_task=None
    sensor._hgt_statistics_archive=archive
    sensor.async_write_ha_state()
    async_import_statistics(hass,metadata(archive),[{'start':NOW-timedelta(days=365),'mean':12.5,'min':12.5,'max':12.5}])
    await async_recorder_block_till_done(hass)
    await hc.async_check_cleanup(hass,entry.entry_id)
    assert await async_setup_component(hass,'repairs',{})
    manager=hass.data['repairs']['flow_manager']
    issue_id=f'{hc.ISSUE}_{entry.entry_id}'
    result=await manager.async_init(DOMAIN,context={'issue_id':issue_id})
    assert result['type']=='form' and archive in result['description_placeholders']['statistic_ids']
    before=await get_instance(hass).async_add_executor_job(partial(get_metadata,hass,statistic_ids={archive}))
    assert archive in before
    result=await manager.async_configure(result['flow_id'],{})
    assert result['type']=='create_entry'
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN,issue_id) is None
    state=hass.states.get(entity_id)
    assert state.attributes['forecast_statistics_archive'] is None
    assert state.attributes['hgt_legacy_cleanup_required'] is False
    sensor._hgt_statistics_task=hass.async_create_background_task(asyncio.sleep(10),'test old HGT waiter')
    async_dispatcher_send(hass,hc.SIGNAL,entry.entry_id)
    await asyncio.sleep(0)
    assert sensor._hgt_statistics_task.cancelled()
    async_dispatcher_send(hass,hc.SIGNAL,'another_entry')
    await hass.async_block_till_done()
    assert registry.async_get(entity_id).id==registered.id


async def test_confirm_survives_ui_cancellation_after_native_queue(hass,entry,fake_recorder):
    plan=hc.HgtCleanupPlan((),{'sensor.a':(1,metadata('sensor.a'))})
    queued=asyncio.Event();callbacks=[]
    def clear(ids,**kwargs):callbacks.append(kwargs['on_done']);queued.set()
    fake_recorder.async_clear_statistics=clear
    with patch.object(hc,'async_plan_cleanup',side_effect=[plan,hc.HgtCleanupPlan((),{})]),patch.object(hc,'async_refresh_statistics_issues',new_callable=AsyncMock) as refresh:
        caller=asyncio.create_task(hc.async_confirm_cleanup(hass,entry.entry_id,plan))
        await queued.wait();caller.cancel()
        with pytest.raises(asyncio.CancelledError):await caller
        callbacks[0]()
        await hass.async_block_till_done(wait_background_tasks=True)
        refresh.assert_awaited_once()


async def test_timed_out_write_is_not_assumed_success_or_resubmitted(hass,entry,fake_recorder):
    plan=hc.HgtCleanupPlan((),{'sensor.a':(1,metadata('sensor.a'))})
    native=asyncio.timeout;submitted=[]
    fake_recorder.async_clear_statistics=lambda ids,**kw:submitted.append(ids)
    with patch.object(hc,'async_plan_cleanup',return_value=plan),patch.object(hc.asyncio,'timeout',side_effect=lambda _:native(0)):
        with pytest.raises(TimeoutError):await hc.async_confirm_cleanup(hass,entry.entry_id,plan)
    assert submitted==[['sensor.a']]


@pytest.mark.parametrize('language',['de','en','fr','it'])
async def test_cleanup_translation_and_confirmation_available(hass,enable_custom_integrations,language):
    text=await async_get_translations(hass,language,'issues',{DOMAIN})
    base='component.meteoswiss.issues.hgt_legacy_cleanup.'
    assert '{statistic_ids}' in text[base+'fix_flow.step.confirm.description']
    assert text[base+'fix_flow.error.cleanup_not_verified']


@pytest.mark.parametrize('archived',[False,True])
async def test_real_recorder_full_deletion_cascades_all_periods_and_preserves_controls(
    recorder_mock,hass,entry,freezer,archived
):
    assert await async_setup_component(hass,'sensor',{})
    daily=registered(hass,entry,disabled=True)
    current=daily.entity_id
    archive='sensor.meteoswiss_hgt_forecast_archive_'+daily.id
    target=archive if archived else current
    control='sensor.control_temperature'
    for eid,unit,value in [(current,'°C·d',12.5),(control,'°C',7.0)]:
        hass.states.async_set(eid,str(value),{'unit_of_measurement':unit,'state_class':'measurement'})
    freezer.move_to(NOW+timedelta(minutes=6));await async_wait_recording_done(hass)
    get_instance(hass).queue_task(StatisticsTask(NOW,False));await async_recorder_block_till_done(hass)
    hass.states.async_set(current,'18.8',{'unit_of_measurement':'°C·d','value_type':'forecast'})
    for eid,unit,value in [(target,'°C·d',12.5),(control,'°C',7.0)]:
        async_import_statistics(hass,metadata(eid,unit_of_measurement=unit),[
            {'start':NOW-timedelta(days=365),'mean':value,'min':value,'max':value}])
    await async_recorder_block_till_done(hass)
    if archived:
        # The migration renamed the original metadata and its short-term rows.
        get_instance(hass).async_clear_statistics([archive])
        await async_recorder_block_till_done(hass)
        from homeassistant.components.recorder.statistics import async_update_statistics_metadata
        async_update_statistics_metadata(hass,current,new_statistic_id=archive)
        await async_recorder_block_till_done(hass)
        async_import_statistics(hass,metadata(archive),[{'start':NOW-timedelta(days=365),'mean':12.5,'min':12.5,'max':12.5}])
        await async_recorder_block_till_done(hass)
    instance=get_instance(hass)
    def snapshot():
        with instance.get_session() as session:
            meta={m.statistic_id:m.id for m in session.query(StatisticsMeta).all()}
            return {key:(pk,session.query(Statistics).filter_by(metadata_id=pk).count(),
                         session.query(StatisticsShortTerm).filter_by(metadata_id=pk).count()) for key,pk in meta.items()}
    before=await instance.async_add_executor_job(snapshot)
    assert before[target][1:] == (1,1) and before[control][1:] == (1,1)
    plan=await hc.async_plan_cleanup(hass,entry.entry_id)
    assert set(plan.metadata)=={target}
    await hc.async_confirm_cleanup(hass,entry.entry_id,plan)
    after=await instance.async_add_executor_job(snapshot)
    assert target not in after and after[control]==before[control]
    def no_orphans():
        with instance.get_session() as session:
            return (session.query(Statistics).filter_by(metadata_id=before[target][0]).count(),
                    session.query(StatisticsShortTerm).filter_by(metadata_id=before[target][0]).count())
    assert await instance.async_add_executor_job(no_orphans)==(0,0)
    assert hass.states.get(current).state=='18.8'
    assert not (await hc.async_plan_cleanup(hass,entry.entry_id)).metadata
