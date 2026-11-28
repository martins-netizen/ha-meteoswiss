"""Shared native rename/readback boundary for retained historical statistics."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Collection
from enum import Enum, auto

from homeassistant.components.recorder.models import StatisticMetaData
from homeassistant.components.recorder.statistics import async_update_statistics_metadata
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

type ArchiveMetadata = dict[str, tuple[int, StatisticMetaData]]


class ArchiveIdentity(Enum):
    """Registry ownership of the source and proposed archive IDs."""

    MATCH = auto()
    DELETED_ARCHIVE_CLAIM = auto()
    CONFLICT = auto()


def archive_identity_status(
    hass: HomeAssistant,
    entity_id: str,
    registry_id: str,
    archive_id: str,
    series_ids: Collection[str],
) -> ArchiveIdentity:
    """Distinguish an old claim on the archive alone from other conflicts."""
    registry = er.async_get(hass)
    owner = registry.async_get(entity_id)
    if (
        owner is None
        or owner.id != registry_id
        or registry.async_get(archive_id) is not None
        or hass.states.get(archive_id) is not None
    ):
        return ArchiveIdentity.CONFLICT
    if not series_ids:
        return ArchiveIdentity.MATCH
    # Recorder metadata does not store the registry UUID of a series owner.
    identity = ArchiveIdentity.MATCH
    for old in registry.deleted_entities.values():
        if old.entity_id == entity_id and old.id != registry_id and entity_id in series_ids:
            return ArchiveIdentity.CONFLICT
        if old.entity_id == archive_id:
            identity = ArchiveIdentity.DELETED_ARCHIVE_CLAIM
    return identity


def archive_identities_match(
    hass: HomeAssistant,
    entity_id: str,
    registry_id: str,
    archive_id: str,
    series_ids: Collection[str],
) -> bool:
    """Require an unambiguous source and archive for a rename or readback."""
    return (
        archive_identity_status(hass, entity_id, registry_id, archive_id, series_ids)
        is ArchiveIdentity.MATCH
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
