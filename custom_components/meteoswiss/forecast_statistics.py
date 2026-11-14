"""Retire old HGT forecast statistics without deleting their data."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import partial

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    get_metadata,
    update_statistics_issues,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .statistics_archive import async_archive_statistics

_ISSUE_REFRESH_TASK = "meteoswiss_statistics_issue_refresh_task"


@dataclass(frozen=True, slots=True)
class ForecastStatisticsResult:
    """Only a verified archival transition may be reported as complete."""

    ready: bool
    archive_id: str | None = None


async def async_refresh_statistics_issues(hass: HomeAssistant) -> None:
    """Serialize Core refreshes without tying shared work to an entry's life."""
    if "recorder" in hass.config.components:
        previous = hass.data.get(_ISSUE_REFRESH_TASK)

        async def refresh() -> bool:
            if previous is not None:
                await asyncio.shield(previous)
            try:
                await get_instance(hass).async_add_executor_job(
                    partial(update_statistics_issues, hass)
                )
            except Exception:
                return False
            return True

        task = hass.async_create_background_task(
            refresh(), "MeteoSwiss statistics repair refresh"
        )
        hass.data[_ISSUE_REFRESH_TASK] = task

        def completed(finished):
            if hass.data.get(_ISSUE_REFRESH_TASK) is finished:
                hass.data.pop(_ISSUE_REFRESH_TASK)

        task.add_done_callback(completed)
        async with asyncio.timeout(30):
            if not await asyncio.shield(task):
                raise RuntimeError("statistics_issue_refresh_failed")


async def async_prepare_hgt_statistics(
    hass: HomeAssistant, entity_id: str, registry_id: str
) -> ForecastStatisticsResult:
    """Move compatible old metadata once; retain its PK and every linked row.

    HGT stays a forecast with no measurement state class. No replacement sensor,
    new statistic, SQL, deletion, conversion, import or backfill is introduced.
    """
    if "recorder" not in hass.config.components:
        return ForecastStatisticsResult(True)
    instance = get_instance(hass)
    archive_id = f"sensor.meteoswiss_hgt_forecast_archive_{registry_id}"
    if hass.states.get(archive_id) is not None or er.async_get(hass).async_get(archive_id) is not None:
        return ForecastStatisticsResult(False)

    async def read():
        return await instance.async_add_executor_job(
            partial(get_metadata, hass, statistic_ids={entity_id, archive_id})
        )

    def compatible(record):
        meta = record[1]
        return (
            meta["source"] == "recorder"
            and meta["unit_of_measurement"] == "°C·d"
            and meta["mean_type"] == StatisticMeanType.ARITHMETIC
            and not meta["has_sum"]
        )

    async with asyncio.timeout(30):
        if not await asyncio.shield(instance.async_db_ready):
            return ForecastStatisticsResult(False)
        before = await read()
        current, archive = before.get(entity_id), before.get(archive_id)
        if archive and not compatible(archive):
            return ForecastStatisticsResult(False)
        if current is None:
            return ForecastStatisticsResult(True, archive_id if archive else None)
        if not compatible(current) or archive:
            return ForecastStatisticsResult(False)
        verified = await async_archive_statistics(
            hass, entity_id, archive_id, current, read
        )
        return ForecastStatisticsResult(verified, archive_id if verified else None)
