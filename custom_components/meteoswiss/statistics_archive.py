"""Shared native rename/readback boundary for retained historical statistics."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from homeassistant.components.recorder.statistics import async_update_statistics_metadata
from homeassistant.core import HomeAssistant


async def async_archive_statistics(
    hass: HomeAssistant,
    entity_id: str,
    archive_id: str,
    current: tuple[int, dict],
    read: Callable[[], Awaitable[dict]],
) -> bool:
    """Require the same metadata PK and fields after the queued native rename.

    Callers validate source, units, algorithm and destination before calling.
    Core also refuses an occupied destination, including a concurrent collision.
    """
    done = hass.loop.create_future()

    def complete() -> None:
        if not done.done():
            done.set_result(None)

    async_update_statistics_metadata(
        hass, entity_id, new_statistic_id=archive_id,
        on_done=lambda: hass.loop.call_soon_threadsafe(complete),
    )
    await done
    after = await read()
    saved = after.get(archive_id)
    if entity_id in after or saved is None or saved[0] != current[0]:
        return False
    expected = {
        key: archive_id if key == "statistic_id" else value
        for key, value in current[1].items()
    }
    return saved[1] == expected
