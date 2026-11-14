"""Preserve arithmetic wind statistics before starting circular statistics."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import partial

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    get_metadata,
)
from homeassistant.core import HomeAssistant

from .statistics_archive import async_archive_statistics


@dataclass(frozen=True, slots=True)
class WindStatisticsResult:
    """Only a verified empty/circular target may start circular statistics."""

    ready: bool
    archive_id: str | None = None


async def async_prepare_wind_statistics(
    hass: HomeAssistant, entity_id: str, registry_id: str
) -> WindStatisticsResult:
    """Rename only the old metadata ID; keep its FK and every statistic row.

    The caller owns lifecycle/cancellation and keeps state_class unset until
    this completes. Never change an algorithm in place, delete rows, use SQL,
    replace an occupied destination or rename the entity/registry entry.
    """
    if "recorder" not in hass.config.components:
        return WindStatisticsResult(True)
    instance = get_instance(hass)
    archive_id = f"sensor.meteoswiss_wind_arithmetic_{registry_id}"
    ids = {entity_id, archive_id}

    async def read():
        return await instance.async_add_executor_job(
            partial(get_metadata, hass, statistic_ids=ids)
        )

    async with asyncio.timeout(30):
        if not await asyncio.shield(instance.async_db_ready):
            return WindStatisticsResult(False)
        before = await read()
        current, archive = before.get(entity_id), before.get(archive_id)
        if archive and (
            archive[1]["source"] != "recorder"
            or archive[1]["unit_of_measurement"] != "°"
            or archive[1]["mean_type"] != StatisticMeanType.ARITHMETIC
            or archive[1]["has_sum"]
        ):
            return WindStatisticsResult(False)
        if current is None:
            return WindStatisticsResult(True, archive_id if archive else None)
        meta = current[1]
        if (
            meta["source"] != "recorder"
            or meta["unit_of_measurement"] != "°"
            or meta["has_sum"]
        ):
            return WindStatisticsResult(False)
        if meta["mean_type"] == StatisticMeanType.CIRCULAR:
            return WindStatisticsResult(True, archive_id if archive else None)
        if meta["mean_type"] != StatisticMeanType.ARITHMETIC or archive:
            return WindStatisticsResult(False)

        verified = await async_archive_statistics(
            hass, entity_id, archive_id, current, read
        )
        return WindStatisticsResult(verified, archive_id if verified else None)
