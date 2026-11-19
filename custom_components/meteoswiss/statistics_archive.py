"""Shared native rename/readback boundary for retained historical statistics."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Collection

from homeassistant.components.recorder.models import StatisticMetaData
from homeassistant.components.recorder.statistics import async_update_statistics_metadata
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

type ArchiveMetadata = dict[str, tuple[int, StatisticMetaData]]


def archive_identities_match(
    hass: HomeAssistant,
    entity_id: str,
    registry_id: str,
    archive_id: str,
    series_ids: Collection[str],
) -> bool:
    """Check ownership on the HA loop after reading the relevant Recorder rows."""
    registry = er.async_get(hass)
    owner = registry.async_get(entity_id)
    if (
        owner is None
        or owner.id != registry_id
        or registry.async_get(archive_id) is not None
        or hass.states.get(archive_id) is not None
    ):
        return False
    if not series_ids:
        return True
    # Recorder stores no registry UUID. An old claim on the destination would
    # also make a newly moved row ambiguous on the next startup.
    return not any(
        old.entity_id == archive_id
        or (entity_id in series_ids and old.entity_id == entity_id and old.id != registry_id)
        for old in registry.deleted_entities.values()
    )


async def async_archive_statistics(
    hass: HomeAssistant,
    entity_id: str,
    archive_id: str,
    registry_id: str,
    current: tuple[int, StatisticMetaData],
    read: Callable[[], Awaitable[ArchiveMetadata]],
) -> bool:
    """Require the same metadata PK and fields after the queued native rename.

    Callers validate source, units, algorithm and destination before calling.
    Core also refuses an occupied destination, including a concurrent collision.
    """
    done: asyncio.Future[None] = hass.loop.create_future()

    def complete() -> None:
        if not done.done():
            done.set_result(None)

    def on_done() -> None:
        hass.loop.call_soon_threadsafe(complete)

    async_update_statistics_metadata(
        hass, entity_id, new_statistic_id=archive_id,
        on_done=on_done,
    )
    await done
    after = await read()
    saved = after.get(archive_id)
    if entity_id in after or saved is None or saved[0] != current[0]:
        return False
    expected = current[1].copy()
    expected["statistic_id"] = archive_id
    return saved[1] == expected and archive_identities_match(
        hass, entity_id, registry_id, archive_id, {entity_id, archive_id}
    )
