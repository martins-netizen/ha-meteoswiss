"""User-confirmed removal of obsolete HGT forecasts across upgrade paths."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import partial
import logging

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import get_metadata
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.start import async_at_started

from .const import DOMAIN
from .forecast_statistics import async_refresh_statistics_issues
from .runtime_data import MeteoSwissConfigEntry

ISSUE = "hgt_legacy_cleanup"
SIGNAL = "meteoswiss_hgt_statistics_cleaned"
_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class HgtCleanupPlan:
    """An exact ownership and metadata snapshot, never a wildcard deletion."""

    bindings: tuple[tuple[str, str, str], ...]
    metadata: dict


def _bindings(hass: HomeAssistant, entry_id: str) -> tuple[tuple[str, str, str], ...]:
    registry = er.async_get(hass)
    owned = []
    # Tombstones retain the identity of retired season entities and renamed or
    # deleted daily forecast entities; never reconstruct IDs from display names.
    for item in (*registry.entities.values(), *registry.deleted_entities.values()):
        if item.config_entry_id != entry_id or item.platform != DOMAIN:
            continue
        if item.unique_id == f"{DOMAIN}_{entry_id}_heating_degree_days":
            owned.append((item.entity_id, item.id, "daily"))
        elif item.unique_id == f"{DOMAIN}_{entry_id}_season_hgt":
            owned.append((item.entity_id, item.id, "season"))
    return tuple(sorted(set(owned)))


async def async_plan_cleanup(hass: HomeAssistant, entry_id: str) -> HgtCleanupPlan:
    """Find only attributable old forecast series, including disabled entities."""
    if "recorder" not in hass.config.components:
        return HgtCleanupPlan((), {})
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ValueError("entry_unavailable")
    instance = get_instance(hass)
    async with asyncio.timeout(30):
        if not await asyncio.shield(instance.async_db_ready):
            raise ValueError("recorder_not_ready")
        bindings = _bindings(hass, entry_id)
        ids = {}
        registry = er.async_get(hass)
        for entity_id, registry_id, kind in bindings:
            active = registry.async_get(entity_id)
            if active is not None and active.id != registry_id:
                raise ValueError("entity_identity_conflict")
            state = hass.states.get(entity_id)
            if state is not None and state.attributes.get("state_class") is not None:
                raise ValueError("forecast_statistics_still_enabled")
            ids[entity_id] = kind
            if kind == "daily":
                archive = f"sensor.meteoswiss_hgt_forecast_archive_{registry_id}"
                if registry.async_get(archive) is not None or hass.states.get(archive) is not None:
                    raise ValueError("archive_identity_conflict")
                ids[archive] = kind
        records = await instance.async_add_executor_job(
            partial(get_metadata, hass, statistic_ids=set(ids))
        ) if ids else {}
        if not records.keys() <= ids.keys():
            raise ValueError("unexpected_statistics")
        for statistic_id, (_, meta) in records.items():
            compatible = (
                meta["source"] == "recorder"
                and meta["unit_of_measurement"] == "°C·d"
                and (
                    ids[statistic_id] == "season"
                    or (meta["mean_type"] == StatisticMeanType.ARITHMETIC and not meta["has_sum"])
                )
            )
            if not compatible:
                raise ValueError("statistics_metadata_conflict")
        if _bindings(hass, entry_id) != bindings:
            raise ValueError("ownership_changed")
        return HgtCleanupPlan(bindings, records)


@callback
def async_clear_cleanup_issue(hass: HomeAssistant, entry_id: str) -> None:
    """Remove only the completed or unloaded entry's migration issue."""
    ir.async_delete_issue(hass, DOMAIN, f"{ISSUE}_{entry_id}")


async def async_check_cleanup(hass: HomeAssistant, entry_id: str) -> None:
    """Show a deliberate deletion choice; a diagnostic failure is not success."""
    try:
        plan = await async_plan_cleanup(hass, entry_id)
    except Exception as err:
        _LOGGER.warning("HGT cleanup inspection failed (%s)", type(err).__name__)
        ir.async_create_issue(
            hass, DOMAIN, f"{ISSUE}_{entry_id}",
            is_fixable=False, is_persistent=False, severity=ir.IssueSeverity.WARNING,
            translation_key="hgt_legacy_cleanup_blocked",
        )
        return
    if not plan.metadata:
        async_clear_cleanup_issue(hass, entry_id)
        return
    ir.async_create_issue(
        hass, DOMAIN, f"{ISSUE}_{entry_id}",
        is_fixable=True, is_persistent=False, severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE, data={"entry_id": entry_id},
        translation_placeholders={"statistic_ids": "\n".join(sorted(plan.metadata))},
    )


@callback
def async_setup_cleanup(hass: HomeAssistant, entry: MeteoSwissConfigEntry) -> None:
    """Inspect after registration even if the forecast sensor is disabled."""
    @callback
    def started(_hass: HomeAssistant) -> None:
        entry.async_create_background_task(
            hass, async_check_cleanup(hass, entry.entry_id), "MeteoSwiss HGT upgrade cleanup"
        )

    entry.async_on_unload(async_at_started(hass, started))
    entry.async_on_unload(lambda: async_clear_cleanup_issue(hass, entry.entry_id))


async def async_confirm_cleanup(
    hass: HomeAssistant, entry_id: str, expected: HgtCleanupPlan
) -> None:
    """Native queued full-series deletion, completion barrier and readback.

    No time range means Core removes metadata and cascades to all hourly and
    short-term rows. Keep the native queued operation alive across UI closure.
    """
    async def finish() -> None:
        before = await async_plan_cleanup(hass, entry_id)
        if before != expected:
            raise ValueError("cleanup_target_changed")
        if before.metadata:
            done = asyncio.Event()
            get_instance(hass).async_clear_statistics(
                sorted(before.metadata),
                on_done=lambda: hass.loop.call_soon_threadsafe(done.set),
            )
            async with asyncio.timeout(30):
                await done.wait()
            after = await async_plan_cleanup(hass, entry_id)
            if after.bindings != before.bindings or after.metadata:
                raise ValueError("cleanup_not_verified")
        await async_refresh_statistics_issues(hass)
        async_clear_cleanup_issue(hass, entry_id)
        async_dispatcher_send(hass, SIGNAL, entry_id)

    task = hass.async_create_background_task(finish(), "MeteoSwiss confirmed HGT cleanup")
    await asyncio.shield(task)
