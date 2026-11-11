"""Preserve arithmetic wind statistics before starting circular statistics."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import partial

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_update_statistics_metadata,
    get_metadata,
)
from homeassistant.core import HomeAssistant


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

        done = hass.loop.create_future()

        def complete() -> None:
            if not done.done():
                done.set_result(None)

        # Recorder invokes on_done from its worker thread.
        async_update_statistics_metadata(
            hass,
            entity_id,
            new_statistic_id=archive_id,
            on_done=lambda: hass.loop.call_soon_threadsafe(complete),
        )
        await done
        after = await read()
        saved = after.get(archive_id)
        if entity_id in after or saved is None or saved[0] != current[0]:
            return WindStatisticsResult(False)
        expected = {
            key: archive_id if key == "statistic_id" else value
            for key, value in meta.items()
        }
        if saved[1] != expected:
            return WindStatisticsResult(False)
        return WindStatisticsResult(True, archive_id)
