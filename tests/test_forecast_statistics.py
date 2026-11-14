"""HGT history defaults, conflicts, cancellation and native lifecycle evidence."""
import asyncio
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType as Mean
from homeassistant.core import CoreState
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss import forecast_statistics as fs, statistics_archive as archive_helper
from custom_components.meteoswiss.const import DOMAIN
from test_entity_warning_contracts import NOW, fixed_clock, installed_entities
from test_provider_device_metadata import provider_sources, make_entry
from test_wind_statistics import initially_stopped

EID='sensor.retained_hgt'
RID='b'*32
ARCHIVE='sensor.meteoswiss_hgt_forecast_archive_'+RID


def meta(**changes):
    return dict(source='recorder',unit_of_measurement='°C·d',mean_type=Mean.ARITHMETIC,
                has_sum=False,statistic_id=EID,**changes)


@pytest.fixture
async def fake_recorder():
    ready=asyncio.get_running_loop().create_future();ready.set_result(True)
    instance=SimpleNamespace(async_db_ready=ready,async_add_executor_job=AsyncMock(),
                            test_hass=SimpleNamespace(config=SimpleNamespace(components={'recorder'}),loop=asyncio.get_running_loop(),states=SimpleNamespace(get=lambda _:None),data={},async_create_background_task=lambda coro,name:asyncio.create_task(coro,name=name)),
                            registry=SimpleNamespace(async_get=lambda _:None))
    with patch.object(fs,'get_instance',return_value=instance),patch.object(fs.er,'async_get',return_value=instance.registry):yield instance


async def test_no_recorder_has_no_metadata_or_refresh_work():
    hass=SimpleNamespace(config=SimpleNamespace(components=set()))
    assert await fs.async_prepare_hgt_statistics(hass,EID,RID)==fs.ForecastStatisticsResult(True)
    await fs.async_refresh_statistics_issues(hass)


@pytest.mark.parametrize('current,archive,ready,archived',[
    (None,None,True,False),(None,(1,meta()),True,True),
    ((1,{**meta(),'mean_type':Mean.NONE}),None,False,False),
    ((1,{**meta(),'mean_type':Mean.CIRCULAR}),None,False,False),
    ((1,{**meta(),'source':'other'}),None,False,False),
    ((1,{**meta(),'unit_of_measurement':'°C'}),None,False,False),
    ((1,{**meta(),'has_sum':True}),None,False,False),
    ((1,meta()),(2,meta()),False,False),
    (None,(1,{**meta(),'source':'other'}),False,False),
    (None,(1,{**meta(),'unit_of_measurement':'°C'}),False,False),
    (None,(1,{**meta(),'mean_type':Mean.CIRCULAR}),False,False),
    (None,(1,{**meta(),'has_sum':True}),False,False),
])
async def test_current_and_destination_are_never_overwritten(fake_recorder,current,archive,ready,archived):
    existing={}
    if current:existing[EID]=current
    if archive:existing[ARCHIVE]=archive
    fake_recorder.async_add_executor_job.return_value=existing
    with patch.object(archive_helper,'async_update_statistics_metadata') as rename:
        result=await fs.async_prepare_hgt_statistics(fake_recorder.test_hass,EID,RID)
    assert result==fs.ForecastStatisticsResult(ready,ARCHIVE if archived else None)
    rename.assert_not_called()


@pytest.mark.parametrize('after',[
    {ARCHIVE:(3,{**meta(),'statistic_id':ARCHIVE})}, {}, {EID:(3,meta())},
    {ARCHIVE:(4,{**meta(),'statistic_id':ARCHIVE})},
    {ARCHIVE:(3,{**meta(),'statistic_id':ARCHIVE,'name':'changed'})},
])
async def test_rename_completion_requires_same_row_and_all_metadata(fake_recorder,after):
    fake_recorder.async_add_executor_job.side_effect=[{EID:(3,meta())},after]
    def finish(*args,**kwargs):kwargs['on_done']();kwargs['on_done']()
    with patch.object(archive_helper,'async_update_statistics_metadata',side_effect=finish) as rename:
        result=await fs.async_prepare_hgt_statistics(fake_recorder.test_hass,EID,RID)
    assert result.ready is (after=={ARCHIVE:(3,{**meta(),'statistic_id':ARCHIVE})})
    rename.assert_called_once()


async def test_unavailable_database_never_queues_a_rename(fake_recorder):
    fake_recorder.async_db_ready=asyncio.get_running_loop().create_future();fake_recorder.async_db_ready.set_result(False)
    assert not (await fs.async_prepare_hgt_statistics(fake_recorder.test_hass,EID,RID)).ready
    fake_recorder.async_add_executor_job.assert_not_called()


@pytest.mark.parametrize('occupied',['live','registered'])
async def test_another_entity_cannot_become_the_archive(fake_recorder,occupied):
    if occupied=='live':fake_recorder.test_hass.states.get=lambda _:object()
    else:fake_recorder.registry.async_get=lambda _:object()
    assert not (await fs.async_prepare_hgt_statistics(fake_recorder.test_hass,EID,RID)).ready
    fake_recorder.async_add_executor_job.assert_not_called()


async def test_cancellation_does_not_cancel_recorder_readiness(fake_recorder):
    ready=asyncio.get_running_loop().create_future();fake_recorder.async_db_ready=ready
    task=asyncio.create_task(fs.async_prepare_hgt_statistics(fake_recorder.test_hass,EID,RID))
    await asyncio.sleep(0);task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert not ready.cancelled();ready.set_result(True)


async def test_timeout_does_not_cancel_recorder_readiness(fake_recorder):
    ready=asyncio.get_running_loop().create_future();fake_recorder.async_db_ready=ready
    native=asyncio.timeout
    with patch.object(fs.asyncio,'timeout',side_effect=lambda _:native(0)):
        with pytest.raises(TimeoutError):await fs.async_prepare_hgt_statistics(fake_recorder.test_hass,EID,RID)
    assert not ready.cancelled();ready.set_result(True)


async def test_native_issue_refresh_has_a_deadline(fake_recorder):
    blocked=asyncio.Event()
    async def wait(*args):await blocked.wait()
    fake_recorder.async_add_executor_job.side_effect=wait
    native=asyncio.timeout
    with patch.object(fs.asyncio,'timeout',side_effect=lambda _:native(0)):
        with pytest.raises(TimeoutError):await fs.async_refresh_statistics_issues(fake_recorder.test_hass)
    task=fake_recorder.test_hass.data[fs._ISSUE_REFRESH_TASK]
    assert not task.cancelled()
    blocked.set();assert await task
    await asyncio.sleep(0)
    assert fs._ISSUE_REFRESH_TASK not in fake_recorder.test_hass.data


async def test_refresh_order_survives_requester_cancellation(fake_recorder):
    entered=asyncio.Event();release=asyncio.Event();order=[]
    async def run(*args):
        index=len([i for i in order if i.startswith('start')])+1
        order.append(f'start{index}')
        if index==1:entered.set();await release.wait()
        order.append(f'end{index}')
    fake_recorder.async_add_executor_job.side_effect=run
    first=asyncio.create_task(fs.async_refresh_statistics_issues(fake_recorder.test_hass))
    await entered.wait()
    second=asyncio.create_task(fs.async_refresh_statistics_issues(fake_recorder.test_hass))
    await asyncio.sleep(0)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):await first
    assert order==['start1']
    release.set();await second;await asyncio.sleep(0)
    assert order==['start1','end1','start2','end2']
    assert fs._ISSUE_REFRESH_TASK not in fake_recorder.test_hass.data


async def test_core_refresh_failure_is_sanitized_and_retryable(fake_recorder):
    fake_recorder.async_add_executor_job.side_effect=RuntimeError('private credential/path')
    with pytest.raises(RuntimeError,match='^statistics_issue_refresh_failed$'):
        await fs.async_refresh_statistics_issues(fake_recorder.test_hass)
    fake_recorder.async_add_executor_job.side_effect=None
    await fs.async_refresh_statistics_issues(fake_recorder.test_hass)


def hgt(hass,entry):
    eid=er.async_get(hass).async_get_entity_id('sensor',DOMAIN,f'{DOMAIN}_{entry.entry_id}_heating_degree_days')
    return hass.data[DATA_COMPONENT].get_entity(eid)


@pytest.mark.parametrize('outcome',[fs.ForecastStatisticsResult(False),RuntimeError('private database path')])
async def test_native_sensor_surfaces_real_conflict_without_exposing_paths(hass,installed_entities,caplog,outcome):
    sensor=hgt(hass,installed_entities)
    mock=AsyncMock(side_effect=outcome) if isinstance(outcome,Exception) else AsyncMock(return_value=outcome)
    with patch.object(fs,'async_prepare_hgt_statistics',mock):await sensor._prepare_hgt_statistics()
    assert sensor.state_class is None
    assert sensor.extra_state_attributes['hgt_statistics_status']=='blocked'
    issue=ir.async_get(hass).async_get_issue(DOMAIN,'hgt_statistics_blocked_'+installed_entities.entry_id)
    assert issue and not issue.is_fixable and issue.data is None and not issue.is_persistent
    assert 'private database path' not in caplog.text
    with patch.object(fs,'async_prepare_hgt_statistics',return_value=fs.ForecastStatisticsResult(True)):
        await sensor._prepare_hgt_statistics()
    assert ir.async_get(hass).async_get_issue(DOMAIN,'hgt_statistics_blocked_'+installed_entities.entry_id) is None


async def test_failed_native_refresh_is_not_reported_as_completed(hass,installed_entities,caplog):
    sensor=hgt(hass,installed_entities)
    with patch.object(fs,'async_prepare_hgt_statistics',return_value=fs.ForecastStatisticsResult(True,ARCHIVE)),patch.object(fs,'async_refresh_statistics_issues',side_effect=RuntimeError('private path')):
        await sensor._prepare_hgt_statistics()
    assert sensor.extra_state_attributes['hgt_statistics_status']=='blocked'
    assert sensor.extra_state_attributes['forecast_statistics_archive']==ARCHIVE
    assert 'private path' not in caplog.text


async def test_missing_registry_identity_never_creates_a_replacement(hass,installed_entities):
    sensor=hgt(hass,installed_entities)
    with patch.object(er.async_get(hass),'async_get',return_value=None),patch.object(fs,'async_prepare_hgt_statistics',new_callable=AsyncMock) as prepare:
        await sensor._prepare_hgt_statistics()
    prepare.assert_not_called()


async def test_hgt_startup_is_deferred_and_unload_cancels_the_owned_task(initially_stopped,hass,enable_custom_integrations,provider_sources):
    entry=make_entry(hass,'meteoswiss');started=asyncio.Event();blocked=asyncio.Event()
    async def prepare(*args):started.set();await blocked.wait();return fs.ForecastStatisticsResult(True)
    with patch.object(fs,'async_prepare_hgt_statistics',side_effect=prepare):
        assert hass.state is CoreState.not_running
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done();sensor=hgt(hass,entry)
        assert not started.is_set()
        await hass.async_start();await started.wait()
        assert sensor.extra_state_attributes['hgt_statistics_status']=='pending'
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert sensor._hgt_statistics_task.cancelled()
        assert ir.async_get(hass).async_get_issue(DOMAIN,'hgt_statistics_blocked_'+entry.entry_id) is None


async def test_wind_refresh_error_does_not_change_verified_algorithm(hass,installed_entities,caplog):
    eid=er.async_get(hass).async_get_entity_id('sensor',DOMAIN,f'{DOMAIN}_{installed_entities.entry_id}_wind_direction')
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    with patch.object(fs,'async_refresh_statistics_issues',side_effect=RuntimeError('private path')):
        await sensor._prepare_statistics()
    assert sensor.state_class=='measurement_angle' and sensor._wind_statistics_status=='ready'
    assert 'private path' not in caplog.text


@pytest.mark.parametrize('language',['en','de','fr','it'])
async def test_native_hgt_conflict_text_is_available(hass,installed_entities,language):
    texts=await async_get_translations(hass,language,'issues',{DOMAIN})
    prefix='component.meteoswiss.issues.hgt_statistics_blocked.'
    assert texts[prefix+'title'] and len(texts[prefix+'description'])>100
    assert '{entity' not in texts[prefix+'description']
