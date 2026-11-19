"""Native, verified Recorder projection for owned official HGT products."""

from __future__ import annotations

import asyncio
import math
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from functools import partial

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticData, StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    get_metadata,
)
from homeassistant.components.recorder.tasks import SynchronizeTask
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .hgt_ogd import MAX_POINTS, UNIT, HgtError, HgtProducts, project_hgt, statistic_ids


def product_metadata(station: str, period: str) -> dict:
    """Unknown compound unit has no temperature-offset converter."""
    return {
        "statistic_id": statistic_ids(station)[period],
        "source": DOMAIN,
        "name": f"MeteoSwiss {station.upper()} HGT 12/20 {period}",
        "unit_of_measurement": UNIT,
        "unit_class": None,
        "mean_type": StatisticMeanType.NONE,
        "has_sum": True,
    }


async def async_metadata(hass: HomeAssistant, stations: set[str]) -> dict:
    instance = get_instance(hass)
    async with asyncio.timeout(30):
        if not await asyncio.shield(instance.async_db_ready):
            raise HgtError("recorder_unavailable")
        ids = {v for station in stations for v in statistic_ids(station).values()}
        result = (
            await instance.async_add_executor_job(
                partial(get_metadata, hass, statistic_ids=ids)
            )
            if ids
            else {}
        )
    if not result.keys() <= ids:
        raise HgtError("statistics_conflict")
    for _, meta in result.values():
        if any(
            meta.get(k) != v
            for k, v in {
                "source": DOMAIN,
                "mean_type": StatisticMeanType.NONE,
                "has_sum": True,
                "unit_class": None,
                "unit_of_measurement": UNIT,
            }.items()
        ):
            raise HgtError("statistics_conflict")
    return deepcopy(result)


async def async_clear_owned(
    hass: HomeAssistant, ids: list[str], *, start: datetime | None = None
) -> None:
    """Wait for exact native deletion; only a full cleanup removes metadata."""
    done = asyncio.Event()
    kwargs = (
        {}
        if start is None
        else {"start_time": start, "end_time": start + timedelta(hours=1)}
    )
    get_instance(hass).async_clear_statistics(
        ids, **kwargs, on_done=lambda: hass.loop.call_soon_threadsafe(done.set)
    )
    async with asyncio.timeout(30):
        await done.wait()


async def async_wait_for_writes(hass: HomeAssistant) -> None:
    """Read absence only after every already-queued native write has committed."""
    committed = hass.loop.create_future()
    get_instance(hass).queue_task(SynchronizeTask(committed))
    async with asyncio.timeout(30):
        await asyncio.shield(committed)


async def _rows(hass: HomeAssistant, ids: set[str]) -> dict[str, list[dict]]:
    def read():
        result = {}
        for statistic_id in sorted(ids):
            rows = get_last_statistics(
                hass, MAX_POINTS + 1, statistic_id, False, {"state", "sum"}
            ).get(statistic_id, [])
            if len(rows) > MAX_POINTS:
                raise HgtError("statistics_conflict")
            result[statistic_id] = sorted(rows, key=lambda r: r["start"])
        return result

    return await get_instance(hass).async_add_executor_job(read)


def _equal(actual: dict, expected: StatisticData) -> bool:
    return all(
        actual.get(k) is not None
        and math.isclose(actual[k], expected[k], rel_tol=1e-12, abs_tol=1e-6)
        for k in ("state", "sum")
    )


def _plan_product(
    station: str,
    period: str,
    values: dict,
    projected: list[StatisticData],
    rows: list[dict],
    metadata: dict,
) -> tuple:
    """Distinguish an explicit source withdrawal from an incomplete file."""
    statistic_id = statistic_ids(station)[period]
    actual = {datetime.fromtimestamp(r["start"], UTC): r for r in rows}
    if len(actual) > MAX_POINTS or not actual.keys() <= values.keys():
        raise HgtError("source_incomplete")
    desired = {r["start"]: r for r in projected}
    dirty = [
        r
        for start, r in desired.items()
        if start not in actual or not _equal(actual[start], r)
    ]
    meta = product_metadata(station, period)
    if statistic_id in metadata:
        meta["name"] = metadata[statistic_id][1]["name"]
    return statistic_id, sorted(actual.keys() - desired.keys()), dirty, meta


async def async_import_products(
    hass: HomeAssistant, station: str, products: HgtProducts, metadata: dict
) -> dict:
    """Upsert corrections and withdraw exact missing slots; verify every result."""
    ids = statistic_ids(station)
    existing = await _rows(hass, set(ids.values()))
    expected = {period: project_hgt(values) for period, values in products.items()}
    plans = [
        _plan_product(
            station,
            period,
            values,
            expected[period],
            existing.get(ids[period], []),
            metadata,
        )
        for period, values in products.items()
    ]
    if await async_metadata(hass, {station}) != metadata:
        raise HgtError("statistics_conflict")
    # Validate every product before queuing any mutation. Only exact owned
    # hourly slots can be withdrawn; an incomplete source never erases history.
    for statistic_id, withdrawals, dirty, meta in plans:
        for start in withdrawals:
            await async_clear_owned(hass, [statistic_id], start=start)
        for offset in range(0, len(dirty), 500):
            async_add_external_statistics(hass, meta, dirty[offset : offset + 500])
    # The convenience barrier can return early once the worker has dequeued
    # the last import, before that running task commits. Always queue Core's
    # commit-before synchronization task behind every submitted product.
    await async_wait_for_writes(hass)
    verified = await _rows(hass, set(ids.values()))
    for period, desired in expected.items():
        rows = verified.get(ids[period], [])
        if len(rows) != len(desired) or any(
            r["start"] != v["start"].timestamp() or not _equal(r, v)
            for r, v in zip(rows, desired, strict=True)
        ):
            raise HgtError("write_not_verified")
    latest = expected["daily"][-1]
    return {
        "latest_value": latest["state"],
        "source_day": latest["start"].date().isoformat(),
        "statistic_ids": {p: ids[p] for p in expected if expected[p]},
        "imported_points": {p: len(v) for p, v in expected.items()},
        "missing_points": {
            p: sum(
                v is None
                for d, v in values.items()
                if expected[p] and d >= expected[p][0]["start"]
            )
            for p, values in products.items()
        },
        "statistics_status": "ready",
    }
