"""Real native external statistics: backfill, change, corrections and consent."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from ha_helpers import async_recorder_block_till_done
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.helpers import issue_registry as ir
from test_hgt_ogd_source import NOW

from custom_components.meteoswiss import hgt_ogd as hgt
from custom_components.meteoswiss import hgt_ogd_manager as mgr
from custom_components.meteoswiss import hgt_ogd_recorder as rec
from custom_components.meteoswiss.const import DOMAIN

DAY1 = datetime(2026, 11, 11, tzinfo=UTC)


def products():
    return {
        "daily": {
            DAY1: 83,
            DAY1 + timedelta(days=1): 0,
            DAY1 + timedelta(days=2): None,
            DAY1 + timedelta(days=3): 191,
        },
        "monthly": {
            datetime(1950, 3, 1, tzinfo=UTC): 4598,
            datetime(2026, 10, 1, tzinfo=UTC): 2169,
        },
        "annual": {
            datetime(1951, 1, 1, tzinfo=UTC): 35302,
            datetime(2025, 1, 1, tzinfo=UTC): 30578,
        },
    }


async def import_products(hass, data=None, station="klo"):
    return await rec.async_import_products(
        hass, station, data or products(), await rec.async_metadata(hass, {station})
    )


async def read_rows(hass, ids):
    return await rec._rows(hass, set(ids))


async def test_real_backfill_has_independent_official_products_and_first_period_change(
    recorder_mock, hass
):
    ids = hgt.statistic_ids("klo")
    result = await import_products(hass)
    assert result == {
        "latest_value": 19.1,
        "source_day": "2026-11-14",
        "statistic_ids": ids,
        "imported_points": {"daily": 3, "monthly": 2, "annual": 2},
        "missing_points": {"daily": 1, "monthly": 0, "annual": 0},
        "statistics_status": "ready",
    }
    rows = await read_rows(hass, ids.values())
    assert [r["state"] for r in rows[ids["daily"]]] == [8.3, 0, 19.1]
    assert [r["sum"] for r in rows[ids["daily"]]] == [8.3, 8.3, 27.4]
    assert (
        rows[ids["monthly"]][0]["start"] == datetime(1950, 3, 1, tzinfo=UTC).timestamp()
    )
    assert (
        rows[ids["annual"]][0]["start"] == datetime(1951, 1, 1, tzinfo=UTC).timestamp()
    )
    changes = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        DAY1,
        DAY1 + timedelta(days=4),
        {ids["daily"]},
        "hour",
        None,
        {"change"},
    )
    assert [r["change"] for r in changes[ids["daily"]]] == pytest.approx([8.3, 0, 19.1])
    for product, graph_period in [("monthly", "month"), ("annual", "year")]:
        values = products()[product]
        graph = await get_instance(hass).async_add_executor_job(
            statistics_during_period,
            hass,
            min(values),
            NOW,
            {ids[product]},
            graph_period,
            None,
            {"change"},
        )
        assert [row["change"] for row in graph[ids[product]]] == pytest.approx(
            [amount / 10 for amount in values.values()]
        )
    meta = await rec.async_metadata(hass, {"klo"})
    assert all(
        m["unit_class"] is None
        and m["mean_type"] == rec.StatisticMeanType.NONE
        and m["has_sum"]
        for _, m in meta.values()
    )
    with patch.object(
        rec, "async_add_external_statistics", wraps=rec.async_add_external_statistics
    ) as queue:
        assert await import_products(hass) == result
    queue.assert_not_called()
    assert await read_rows(hass, ids.values()) == rows


async def test_real_correction_withdrawal_and_renaming_preserve_unrelated_data(
    recorder_mock, hass
):
    ids = hgt.statistic_ids("klo")
    await import_products(hass)
    other = rec.product_metadata("ber", "daily")
    async_add_external_statistics(hass, other, [{"start": DAY1, "state": 7, "sum": 7}])
    renamed = rec.product_metadata("klo", "daily") | {"name": "My observed HGT"}
    async_add_external_statistics(hass, renamed, hgt.project_hgt(products()["daily"]))
    await async_recorder_block_till_done(hass)
    before_other = await read_rows(hass, [other["statistic_id"]])
    data = products()
    data["daily"][DAY1] = 100
    data["daily"][DAY1 + timedelta(days=1)] = None
    data["daily"][DAY1 + timedelta(days=2)] = 20
    await import_products(hass, data)
    rows = (await read_rows(hass, [ids["daily"]]))[ids["daily"]]
    assert [r["state"] for r in rows] == [10, 2, 19.1]
    assert [r["sum"] for r in rows] == [10, 12, 31.1]
    assert (await rec.async_metadata(hass, {"klo"}))[ids["daily"]][1][
        "name"
    ] == "My observed HGT"
    assert await read_rows(hass, [other["statistic_id"]]) == before_other
    # A truncated source cannot imply withdrawal of the unseen old rows.
    del data["daily"][DAY1]
    with pytest.raises(hgt.HgtError, match="source_incomplete"):
        await import_products(hass, data)
    assert (await read_rows(hass, [ids["daily"]]))[ids["daily"]] == rows


async def test_native_retired_repair_no_implicit_consent_and_all_owned_data_removed(
    recorder_mock, hass, enable_custom_integrations
):
    manager = mgr.get_hgt_manager(hass)
    await manager.async_load()
    await manager._save({"klo"})
    await import_products(hass)
    other = rec.product_metadata("ber", "daily")
    async_add_external_statistics(hass, other, [{"start": DAY1, "state": 7, "sum": 7}])
    await async_recorder_block_till_done(hass)
    before_other = await read_rows(hass, [other["statistic_id"]])
    await manager.async_sync_issue()
    issue = ir.async_get(hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE)
    assert issue.is_persistent and issue.is_fixable
    from homeassistant.setup import async_setup_component

    hass.config.components.add(DOMAIN)
    assert await async_setup_component(hass, "repairs", {})
    flow_manager = hass.data["repairs"]["flow_manager"]
    form = await flow_manager.async_init(
        DOMAIN, context={"issue_id": mgr.CLEANUP_ISSUE}
    )
    assert form["type"] == "form" and set(
        form["description_placeholders"]["statistic_ids"].splitlines()
    ) == set(hgt.statistic_ids("klo").values())
    assert len(await rec.async_metadata(hass, {"klo"})) == 3
    result = await flow_manager.async_configure(form["flow_id"], {})
    assert result["type"] == "create_entry"
    assert await rec.async_metadata(hass, {"klo"}) == {}
    assert all(
        not rows
        for rows in (await read_rows(hass, hgt.statistic_ids("klo").values())).values()
    )
    assert manager.known == set() and await manager.store.async_load() is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, mgr.CLEANUP_ISSUE) is None
    assert await read_rows(hass, [other["statistic_id"]]) == before_other


@pytest.mark.parametrize(
    "changed",
    ["source", "unit_of_measurement", "unit_class", "mean_type", "has_sum", "extra_id"],
)
async def test_foreign_metadata_cannot_be_mutated(hass, changed):
    ready = hass.loop.create_future()
    ready.set_result(True)
    data = rec.product_metadata("klo", "daily")
    data[changed] = "foreign"
    key = data["statistic_id"] if changed != "extra_id" else "foreign:other"
    instance = SimpleNamespace(
        async_db_ready=ready,
        async_add_executor_job=AsyncMock(return_value={key: (1, data)}),
    )
    with patch.object(rec, "get_instance", return_value=instance):
        with pytest.raises(hgt.HgtError, match="statistics_conflict"):
            await rec.async_metadata(hass, {"klo"})


async def test_not_ready_database_and_empty_ids(hass):
    ready = hass.loop.create_future()
    ready.set_result(False)
    instance = SimpleNamespace(async_db_ready=ready, async_add_executor_job=AsyncMock())
    with patch.object(rec, "get_instance", return_value=instance):
        with pytest.raises(hgt.HgtError, match="recorder_unavailable"):
            await rec.async_metadata(hass, {"klo"})
        ready = hass.loop.create_future()
        ready.set_result(True)
        instance.async_db_ready = ready
        assert await rec.async_metadata(hass, set()) == {}
    instance.async_add_executor_job.assert_not_awaited()


async def test_native_queue_callback_required_and_wait_is_cancellable(hass):
    callbacks = []
    instance = SimpleNamespace(
        async_clear_statistics=lambda ids, **kw: callbacks.append(kw)
    )
    with patch.object(rec, "get_instance", return_value=instance):
        task = asyncio.create_task(
            rec.async_clear_owned(hass, ["meteoswiss:klo_hgt_12_20_daily"])
        )
        await asyncio.sleep(0)
        assert not task.done() and "start_time" not in callbacks[0]
        callbacks[0]["on_done"]()
        await task
        task = asyncio.create_task(
            rec.async_clear_owned(hass, ["meteoswiss:klo_hgt_12_20_daily"], start=DAY1)
        )
        await asyncio.sleep(0)
        assert callbacks[1]["end_time"] == DAY1 + timedelta(hours=1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


async def test_bounded_read_and_all_product_preflight_before_mutation(hass):
    instance = SimpleNamespace(
        async_add_executor_job=AsyncMock(side_effect=lambda f: f())
    )
    with (
        patch.object(rec, "get_instance", return_value=instance),
        patch.object(rec, "MAX_POINTS", 1),
        patch.object(
            rec,
            "get_last_statistics",
            return_value={
                "meteoswiss:klo_hgt_12_20_daily": [{"start": 1}, {"start": 2}]
            },
        ),
    ):
        with pytest.raises(hgt.HgtError, match="statistics_conflict"):
            await rec._rows(hass, {"meteoswiss:klo_hgt_12_20_daily"})
    rows = {
        hgt.statistic_ids("klo")["annual"]: [
            {
                "start": datetime(1950, 1, 1, tzinfo=UTC).timestamp(),
                "state": 1,
                "sum": 1,
            }
        ]
    }
    with (
        patch.object(rec, "get_instance"),
        patch.object(rec, "_rows", return_value=rows),
        patch.object(rec, "async_add_external_statistics") as queue,
    ):
        with pytest.raises(hgt.HgtError, match="source_incomplete"):
            await rec.async_import_products(hass, "klo", products(), {})
    queue.assert_not_called()


@pytest.mark.parametrize("bad_readback", [True, False])
async def test_mutated_metadata_or_unverified_readback_cannot_report_success(
    hass, bad_readback
):
    instance = SimpleNamespace(queue_task=lambda task: task.future.set_result(None))
    with (
        patch.object(rec, "get_instance", return_value=instance),
        patch.object(rec, "_rows", side_effect=[{}, {}]),
        patch.object(
            rec,
            "async_metadata",
            return_value={} if bad_readback else {"foreign": (1, {})},
        ),
        patch.object(rec, "async_add_external_statistics") as queue,
    ):
        with pytest.raises(
            hgt.HgtError,
            match="write_not_verified" if bad_readback else "statistics_conflict",
        ):
            await rec.async_import_products(hass, "klo", products(), {})
        assert queue.call_count == (3 if bad_readback else 0)


async def test_equal_length_changed_values_do_not_pass_readback(hass):
    expected = {
        hgt.statistic_ids("klo")[p]: [
            {"start": r["start"].timestamp(), "state": r["state"], "sum": r["sum"]}
            for r in hgt.project_hgt(v)
        ]
        for p, v in products().items()
    }
    expected[hgt.statistic_ids("klo")["daily"]][0]["state"] = None
    instance = SimpleNamespace(queue_task=lambda task: task.future.set_result(None))
    with (
        patch.object(rec, "get_instance", return_value=instance),
        patch.object(rec, "_rows", side_effect=[{}, expected]),
        patch.object(rec, "async_metadata", return_value={}),
        patch.object(rec, "async_add_external_statistics"),
    ):
        with pytest.raises(hgt.HgtError, match="write_not_verified"):
            await rec.async_import_products(hass, "klo", products(), {})


async def test_disappearing_interior_source_date_does_not_authorize_deletion(
    recorder_mock, hass
):
    await import_products(hass)
    before = await read_rows(hass, hgt.statistic_ids("klo").values())
    data = products()
    del data["daily"][DAY1 + timedelta(days=1)]
    with pytest.raises(hgt.HgtError, match="source_incomplete"):
        await import_products(hass, data)
    assert await read_rows(hass, hgt.statistic_ids("klo").values()) == before


async def test_real_multidecade_import_uses_bounded_batches_and_exact_cumulative_tenths(
    recorder_mock, hass
):
    first = datetime(1976, 1, 1, tzinfo=UTC)
    count = (DAY1 - first).days
    data = products()
    data["daily"] = {first + timedelta(days=n): n % 100 for n in range(count)}
    with patch.object(
        rec, "async_add_external_statistics", wraps=rec.async_add_external_statistics
    ) as queue:
        result = await import_products(hass, data)
    assert result["imported_points"]["daily"] == count
    assert all(len(call.args[2]) <= 500 for call in queue.call_args_list)
    rows = (await read_rows(hass, [hgt.statistic_ids("klo")["daily"]]))[
        hgt.statistic_ids("klo")["daily"]
    ]
    assert len(rows) == count and rows[0]["start"] == first.timestamp()
    assert rows[-1]["sum"] == sum(n % 100 for n in range(count)) / 10
    old_ids = {m[0] for m in (await rec.async_metadata(hass, {"klo"})).values()}
    await rec.async_clear_owned(hass, list(hgt.statistic_ids("klo").values()))
    # Metadata-only lookups could hide orphans: inspect the native physical
    # tables read-only as well, without adding a production SQL writer.
    from homeassistant.components.recorder.db_schema import (
        Statistics,
        StatisticsMeta,
        StatisticsShortTerm,
    )
    from homeassistant.components.recorder.util import session_scope
    from sqlalchemy import func, select

    def remaining():
        with session_scope(hass=hass, read_only=True) as session:
            return [
                session.scalar(
                    select(func.count())
                    .select_from(table)
                    .where(
                        (
                            table.id if table is StatisticsMeta else table.metadata_id
                        ).in_(old_ids)
                    )
                )
                for table in (Statistics, StatisticsShortTerm, StatisticsMeta)
            ]

    assert await get_instance(hass).async_add_executor_job(remaining) == [0, 0, 0]


async def test_running_final_native_import_needs_unconditional_commit_barrier(
    recorder_mock, hass
):
    from threading import Event

    from homeassistant.components.recorder.tasks import ImportStatisticsTask

    instance = get_instance(hass)
    started, release = asyncio.Event(), Event()
    original = ImportStatisticsTask.run

    def run(task, recorder):
        if task.metadata["statistic_id"].endswith("_annual"):
            hass.loop.call_soon_threadsafe(started.set)
            assert release.wait(5), "Test failed to release the native writer"
        return original(task, recorder)

    with (
        patch.object(ImportStatisticsTask, "run", run),
        patch.object(
            instance, "async_get_commit_future", return_value=None
        ) as shortcut,
    ):
        task = asyncio.create_task(import_products(hass))
        try:
            async with asyncio.timeout(3):
                await started.wait()
            was_pending = not task.done()
        finally:
            release.set()
        result = await task
        assert was_pending
        shortcut.assert_not_called()
        assert result["statistics_status"] == "ready"
        assert (
            len(
                (await rec._rows(hass, {hgt.statistic_ids("klo")["annual"]}))[
                    hgt.statistic_ids("klo")["annual"]
                ]
            )
            == 2
        )
