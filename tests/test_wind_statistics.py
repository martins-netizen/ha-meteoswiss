"""Data-preserving wind statistics and failure/lifecycle boundaries."""

import asyncio
from functools import partial
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import DATA_COMPONENT, SensorStateClass
from homeassistant.components.recorder.models import StatisticMeanType as Mean
from homeassistant.core import CoreState
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss import wind_statistics as ws
from custom_components.meteoswiss.sensor import (
    MeteoSwissWindDirectionSensor, SENSOR_DESCRIPTIONS,
)
from custom_components.meteoswiss.const import DOMAIN, SENSOR_WIND_DIRECTION, SENSOR_WIND_SPEED
from test_entity_warning_contracts import NOW, fixed_clock, installed_entities
from test_wind_recorder_contract import seed, rows, metadata, angle_window
from test_provider_device_metadata import provider_sources, make_entry

EID="sensor.retained_wind"
RID="a"*32
ARCHIVE="sensor.meteoswiss_wind_arithmetic_"+RID


def meta(mean=Mean.ARITHMETIC, **extra):
    return dict(source="recorder", unit_of_measurement="°", has_sum=False,
                mean_type=mean, statistic_id=EID, **extra)


@pytest.fixture
async def fake_recorder():
    ready=asyncio.get_running_loop().create_future()
    ready.set_result(True)
    instance=SimpleNamespace(async_db_ready=ready,async_add_executor_job=AsyncMock(),
        test_hass=SimpleNamespace(config=SimpleNamespace(components={"recorder"}),loop=asyncio.get_running_loop()))
    with patch.object(ws,"get_instance",return_value=instance):
        yield instance


async def test_no_recorder_needs_no_database():
    hass=SimpleNamespace(config=SimpleNamespace(components=set()),loop=asyncio.get_running_loop())
    result=await ws.async_prepare_wind_statistics(hass,EID,RID)
    assert result==ws.WindStatisticsResult(True)


@pytest.mark.parametrize("current,archive,ready,has_archive",[
    (None,None,True,False),
    (None,(1,meta()),True,True),
    ((2,meta(Mean.CIRCULAR)),None,True,False),
    ((2,meta(Mean.CIRCULAR)),(1,meta()),True,True),
    ((1,meta(Mean.NONE)),None,False,False),
    ((1,dict(meta(),source="other")),None,False,False),
    ((1,dict(meta(),unit_of_measurement="rad")),None,False,False),
    ((1,dict(meta(),has_sum=True)),None,False,False),
    ((2,meta()),(1,meta()),False,False),
    (None,(1,dict(meta(),source="other")),False,False),
    (None,(1,dict(meta(),unit_of_measurement="rad")),False,False),
    (None,(1,meta(Mean.CIRCULAR)),False,False),
    (None,(1,dict(meta(),has_sum=True)),False,False),
])
async def test_existing_metadata_is_never_overwritten(fake_recorder,current,archive,ready,has_archive):
    existing={}
    if current: existing[EID]=current
    if archive: existing[ARCHIVE]=archive
    fake_recorder.async_add_executor_job.return_value=existing
    with patch.object(ws,"async_update_statistics_metadata") as rename:
        result=await ws.async_prepare_wind_statistics(fake_recorder.test_hass,EID,RID)
    assert result==ws.WindStatisticsResult(ready,ARCHIVE if has_archive else None)
    rename.assert_not_called()


async def test_failed_database_start_never_queues_a_write(fake_recorder):
    fake_recorder.async_db_ready=asyncio.get_running_loop().create_future()
    fake_recorder.async_db_ready.set_result(False)
    assert await ws.async_prepare_wind_statistics(fake_recorder.test_hass,EID,RID)==ws.WindStatisticsResult(False)
    fake_recorder.async_add_executor_job.assert_not_called()


@pytest.mark.parametrize("after",[
    {ARCHIVE:(3,dict(meta(),statistic_id=ARCHIVE))},
    {EID:(3,meta())},
    {},
    {ARCHIVE:(4,dict(meta(),statistic_id=ARCHIVE))},
    {ARCHIVE:(3,dict(meta(),statistic_id=ARCHIVE,mean_type=Mean.CIRCULAR))},
])
async def test_queue_completion_requires_verified_identity_and_metadata(fake_recorder,after):
    before={EID:(3,meta())}
    fake_recorder.async_add_executor_job.side_effect=[before,after]
    def finish(*args,**kwargs):
        kwargs["on_done"]()
        kwargs["on_done"]()  # Duplicate/late completion is harmless.
    with patch.object(ws,"async_update_statistics_metadata",side_effect=finish) as rename:
        result=await ws.async_prepare_wind_statistics(fake_recorder.test_hass,EID,RID)
    expected=after=={ARCHIVE:(3,dict(meta(),statistic_id=ARCHIVE))}
    assert result.ready is expected
    rename.assert_called_once()


async def test_cancel_does_not_cancel_recorders_shared_ready_future(fake_recorder):
    pending=asyncio.get_running_loop().create_future()
    fake_recorder.async_db_ready=pending
    task=asyncio.create_task(ws.async_prepare_wind_statistics(fake_recorder.test_hass,EID,RID))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    assert not pending.cancelled()
    pending.set_result(True)


async def test_native_sensor_archives_before_angle_then_reloads_idempotently(
    recorder_mock,hass,enable_custom_integrations,provider_sources,freezer
):
    entry=make_entry(hass,"meteoswiss")
    registry=er.async_get(hass)
    uid=f"{DOMAIN}_{entry.entry_id}_wind_direction"
    created=registry.async_get_or_create("sensor",DOMAIN,uid,config_entry=entry,suggested_object_id="retained_wind")
    eid=created.entity_id
    saved=registry.async_update_entity(eid,name="Retained wind",icon="mdi:compass",aliases={"Wind alias"})
    await seed(hass,eid)
    before=await metadata(hass,{eid})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    assert isinstance(sensor,MeteoSwissWindDirectionSensor)
    await sensor._statistics_task
    archive="sensor.meteoswiss_wind_arithmetic_"+saved.id
    assert sensor.state_class==SensorStateClass.MEASUREMENT_ANGLE
    assert hass.states.get(eid).attributes["arithmetic_statistics_archive"]==archive
    assert (await metadata(hass,{archive}))[archive][0]==before[eid][0]
    assert (await rows(hass,{archive},NOW.replace(hour=9),NOW))[archive][0]["mean"]==180
    await angle_window(hass,freezer,eid)
    assert (await metadata(hass,{eid}))[eid][1]["mean_type"]==Mean.CIRCULAR
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    await sensor._prepare_statistics()
    assert sensor.state_class==SensorStateClass.MEASUREMENT_ANGLE
    current=registry.async_get(eid)
    assert (current.id,current.unique_id,current.name,current.icon,current.aliases)==(saved.id,saved.unique_id,saved.name,saved.icon,saved.aliases)
    assert (await metadata(hass,{archive}))[archive][0]==before[eid][0]
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_sensor_background_task_completes_with_ha_running(hass,installed_entities):
    entry=installed_entities
    eid=er.async_get(hass).async_get_entity_id("sensor",DOMAIN,f"{DOMAIN}_{entry.entry_id}_wind_direction")
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    await hass.async_start()
    await hass.async_block_till_done()
    await sensor._statistics_task
    assert sensor.state_class==SensorStateClass.MEASUREMENT_ANGLE
    assert hass.states.get(eid).attributes["wind_statistics_status"]=="ready"


@pytest.mark.parametrize("outcome",[ws.WindStatisticsResult(False),RuntimeError("private database path")])
async def test_sensor_keeps_measurements_but_blocks_statistics_on_failure(hass,installed_entities,caplog,outcome):
    entry=installed_entities
    eid=er.async_get(hass).async_get_entity_id("sensor",DOMAIN,f"{DOMAIN}_{entry.entry_id}_wind_direction")
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    mock=AsyncMock(side_effect=outcome) if isinstance(outcome,Exception) else AsyncMock(return_value=outcome)
    with patch.object(ws,"async_prepare_wind_statistics",mock): await sensor._prepare_statistics()
    assert sensor.state_class is None
    assert hass.states.get(eid).attributes["wind_statistics_status"]=="blocked"
    assert "private database path" not in caplog.text


async def test_removed_registry_entry_is_not_recreated(hass,installed_entities):
    entry=installed_entities
    eid=er.async_get(hass).async_get_entity_id("sensor",DOMAIN,f"{DOMAIN}_{entry.entry_id}_wind_direction")
    sensor=hass.data[DATA_COMPONENT].get_entity(eid)
    with patch.object(er.async_get(hass),"async_get",return_value=None),patch.object(ws,"async_prepare_wind_statistics",new_callable=AsyncMock) as prepare:
        await sensor._prepare_statistics()
    prepare.assert_not_called()


async def test_timeout_leaves_shared_recorder_readiness_intact(fake_recorder):
    pending = asyncio.get_running_loop().create_future()
    fake_recorder.async_db_ready = pending
    native_timeout = asyncio.timeout
    with patch.object(ws.asyncio, "timeout", side_effect=lambda _: native_timeout(0)):
        with pytest.raises(TimeoutError):
            await ws.async_prepare_wind_statistics(fake_recorder.test_hass, EID, RID)
    assert not pending.cancelled()
    pending.set_result(True)
    fake_recorder.async_add_executor_job.assert_not_called()


async def test_cancel_after_queued_rename_accepts_late_worker_completion(fake_recorder):
    queued = asyncio.Event()
    completed = None
    fake_recorder.async_add_executor_job.return_value = {EID: (3, meta())}

    def enqueue(*args, **kwargs):
        nonlocal completed
        completed = kwargs["on_done"]
        queued.set()

    with patch.object(ws, "async_update_statistics_metadata", side_effect=enqueue):
        task = asyncio.create_task(
            ws.async_prepare_wind_statistics(fake_recorder.test_hass, EID, RID)
        )
        await queued.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        completed()
        await asyncio.sleep(0)
    assert fake_recorder.async_add_executor_job.await_count == 1


@pytest.mark.parametrize("speed,direction,expected", [
    (0, 90, None), (0.0, 0, None), (5, 0, 0), (5, 360, 360),
    (5, 350, 350), (None, 90, 90), (5, None, None), (5, True, None),
    (5, float("nan"), None), (5, float("inf"), None),
    (5, -1, None), (5, 361, None), (5, "invalid", None),
])
async def test_calm_and_invalid_direction_do_not_create_false_north(
    hass, installed_entities, speed, direction, expected
):
    eid = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{DOMAIN}_{installed_entities.entry_id}_wind_direction"
    )
    sensor = hass.data[DATA_COMPONENT].get_entity(eid)
    sensor.coordinator.async_set_updated_data({
        SENSOR_WIND_SPEED: speed, SENSOR_WIND_DIRECTION: direction,
    })
    assert sensor.native_value == expected
    if expected is None:
        assert hass.states.get(eid).state == "unknown"
    else:
        assert float(hass.states.get(eid).state) == expected


async def test_blocked_repair_clears_on_success_and_unload(hass, installed_entities):
    entry = installed_entities
    registry = er.async_get(hass)
    eid = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_wind_direction"
    )
    sensor = hass.data[DATA_COMPONENT].get_entity(eid)
    issues = ir.async_get(hass)
    issue_id = f"wind_statistics_blocked_{entry.entry_id}"
    with patch.object(ws, "async_prepare_wind_statistics", new_callable=AsyncMock) as prepare:
        prepare.return_value = ws.WindStatisticsResult(False)
        await sensor._prepare_statistics()
        issue = issues.async_get_issue(DOMAIN, issue_id)
        assert issue is not None and issue.severity == ir.IssueSeverity.WARNING
        assert not issue.is_fixable and not issue.is_persistent
        assert issue.data is None and issue.translation_placeholders is None
        assert issue.learn_more_url.endswith("/docs/WIND_STATISTICS_MIGRATION.md")
        assert registry.async_get(eid).capabilities is None
        prepare.return_value = ws.WindStatisticsResult(True)
        await sensor._prepare_statistics()
        assert issues.async_get_issue(DOMAIN, issue_id) is None
        assert registry.async_get(eid).capabilities["state_class"] == "measurement_angle"
        prepare.return_value = ws.WindStatisticsResult(False)
        await sensor._prepare_statistics()
        assert issues.async_get_issue(DOMAIN, issue_id) is not None
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert issues.async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_wind_repair_text_is_loaded_by_ha(hass, installed_entities, language):
    texts = await async_get_translations(hass, language, "issues", {DOMAIN})
    prefix = "component.meteoswiss.issues.wind_statistics_blocked."
    assert texts[prefix + "title"]
    assert len(texts[prefix + "description"]) > 100
    assert "{entity" not in texts[prefix + "description"]


@pytest.fixture
def initially_stopped():
    # The official test factory defaults to running. Request a genuinely stopped
    # instance rather than mutating a running Core's state behind its lifecycle.
    from pytest_homeassistant import plugins
    with patch.object(plugins, "async_test_home_assistant", partial(
        plugins.async_test_home_assistant, initial_state=CoreState.not_running
    )):
        yield


async def test_startup_is_deferred_and_unload_cancels_pending_preparation(
    initially_stopped, hass, enable_custom_integrations, provider_sources
):
    entry = make_entry(hass, "meteoswiss")
    started = asyncio.Event()
    blocked = asyncio.Event()

    async def prepare(*args):
        started.set()
        await blocked.wait()
        return ws.WindStatisticsResult(True)

    with patch.object(ws, "async_prepare_wind_statistics", side_effect=prepare):
        assert hass.state is CoreState.not_running
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        eid = er.async_get(hass).async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_wind_direction"
        )
        sensor = hass.data[DATA_COMPONENT].get_entity(eid)
        assert not started.is_set() and sensor.state_class is None
        await hass.async_start()
        await started.wait()
        assert sensor._wind_statistics_status == "pending"
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert sensor._statistics_task.cancelled()
        assert ir.async_get(hass).async_get_issue(
            DOMAIN, f"wind_statistics_blocked_{entry.entry_id}"
        ) is None
