"""One owner for the two shared helpers, using native HA registry moves."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN
from .repair_issues import async_sync_shared_diagnostics_issue
from .runtime_data import MeteoSwissConfigEntry

if TYPE_CHECKING:
    from homeassistant.components.sensor import SensorEntity
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

_LOGGER = logging.getLogger(__name__)
DATA_SHARED_DIAGNOSTICS = "shared_diagnostics"
DIAGNOSTIC_KEYS = ("stations_map", "cache_stats")
type DiagnosticFactory = Callable[[], tuple[SensorEntity, SensorEntity]]


@dataclass(slots=True)
class _Platform:
    entry: MeteoSwissConfigEntry
    add_entities: AddConfigEntryEntitiesCallback
    factory: DiagnosticFactory
    unsubscribe: Callable[[], None]
    added: bool = False


class _OwnershipConflict(Exception):
    """Retained registry data does not identify one safe transfer."""


class SharedDiagnostics:
    """Serialize claims in callbacks, with no await inside a registry move.

    A pending platform can retain the registry records while setup finishes.
    Helper objects are added only after its entry reaches LOADED. HA calls the
    unload callback for successful unload and failed/cancelled setup alike.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.owner: str | None = None
        self._parked_from: str | None = None
        self.platforms: dict[str, _Platform] = {}
        self._unsubscribe_stop = hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self._async_shutdown
        )

    @callback
    def _async_shutdown(self, _event: Event) -> None:
        """HA shutdown does not necessarily unload every config entry."""
        self.owner = None
        self._parked_from = None
        for platform in self.platforms.values():
            platform.unsubscribe()
        self.platforms.clear()
        self.hass.data[DOMAIN].pop(DATA_SHARED_DIAGNOSTICS, None)
        async_sync_shared_diagnostics_issue(self.hass, False)

    @callback
    def async_register(
        self,
        entry: MeteoSwissConfigEntry,
        add_entities: AddConfigEntryEntitiesCallback,
        factory: DiagnosticFactory,
    ) -> None:
        """Retain the actual platform callback until this entry unloads."""
        if entry.entry_id in self.platforms:
            return
        unsubscribe = entry.async_on_state_change(self._async_ready)
        self.platforms[entry.entry_id] = _Platform(
            entry, add_entities, factory, unsubscribe
        )
        entry.async_on_unload(lambda: self.async_release(entry.entry_id))
        self._async_ready()

    @callback
    def async_release(self, entry_id: str) -> None:
        """Hand off after platform unload; never reload a peer coordinator."""
        platform = self.platforms.pop(entry_id, None)
        if platform is None:
            return
        platform.unsubscribe()
        departed_owner = (
            self._async_release_owner(entry_id) if self.owner == entry_id else None
        )
        if not self.platforms:
            self._unsubscribe_stop()
            self.hass.data[DOMAIN].pop(DATA_SHARED_DIAGNOSTICS, None)
            async_sync_shared_diagnostics_issue(self.hass, False)
            return
        self._async_ready()
        if departed_owner is not None and self.owner is None and not self.hass.is_stopping:
            self._async_park_pending(departed_owner)

    @callback
    def _async_release_owner(self, entry_id: str) -> str:
        """Restore a failed pending claim when the prior entry still exists."""
        departed_owner = self._parked_from or entry_id
        if self._parked_from is not None:
            prior = self.hass.config_entries.async_get_entry(self._parked_from)
            if prior is not None:
                self._async_move_registry(prior)
        self.owner = None
        self._parked_from = None
        return departed_owner

    @callback
    def _async_park_pending(self, departed_owner: str) -> None:
        """Retain records before HA removes an owner; start no helper polling."""
        for target_id, target in self.platforms.items():
            if (target.entry.state is ConfigEntryState.SETUP_IN_PROGRESS
                    and target.entry.disabled_by is None
                    and self._async_move_registry(target.entry)):
                self.owner = target_id
                self._parked_from = departed_owner
                break

    @callback
    def _async_ready(self) -> None:
        """Elect one registered, enabled platform and add only on LOADED."""
        if self.hass.is_stopping:
            return
        if self.owner is None or not self.platforms[self.owner].added:
            self._async_elect_loaded()
        if self.owner is None:
            return
        self._async_add_owner(self.platforms[self.owner])

    @callback
    def _async_elect_loaded(self) -> None:
        """Prefer a fully loaded peer over temporary retention ownership."""
        for entry_id, platform in self.platforms.items():
            if (platform.entry.disabled_by is not None
                    or platform.entry.state is not ConfigEntryState.LOADED):
                continue
            if self._async_move_registry(platform.entry):
                self.owner = entry_id
                self._parked_from = None
                break

    @callback
    def _async_add_owner(self, platform: _Platform) -> None:
        """Use only the elected platform's existing callback, once loaded."""
        if platform.added or platform.entry.state is not ConfigEntryState.LOADED:
            return
        try:
            entities = platform.factory()
            platform.add_entities(entities)
        except Exception:
            # Do not include user names, saved locations or exception messages.
            self.owner = None
            self._async_block("Could not register shared diagnostic helpers")
            return
        platform.added = True
        async_sync_shared_diagnostics_issue(self.hass, False)

    @callback
    def _async_plan(
        self, target: MeteoSwissConfigEntry
    ) -> list[tuple[er.RegistryEntry | None, dr.DeviceEntry | None]]:
        """Accept only known helper records with unambiguous device ownership."""
        entities = er.async_get(self.hass)
        plan = []
        for key in DIAGNOSTIC_KEYS:
            unique_id = f"{DOMAIN}_{key}"
            entity_id = entities.async_get_entity_id("sensor", DOMAIN, unique_id)
            entity = entities.async_get(entity_id) if entity_id is not None else None
            if entity is not None and entity.config_subentry_id is not None:
                raise _OwnershipConflict
            device = self._async_find_device(key, entity)
            if device is not None:
                self._async_validate_device(key, entity, device, target)
            plan.append((entity, device))
        return plan

    @callback
    def _async_find_device(
        self, key: str, entity: er.RegistryEntry | None
    ) -> dr.DeviceEntry | None:
        """Prefer the bound device; do not guess between unbound old groups."""
        devices = dr.async_get(self.hass)
        if entity is not None and entity.device_id is not None:
            device = devices.async_get(
                entity.device_id, include_child_devices=False,
                include_composite_devices=False,
            )
            if device is None:
                raise _OwnershipConflict
            return device
        matches = devices.async_get_devices(identifiers={(DOMAIN, key)})
        if len(matches) > 1:
            raise _OwnershipConflict
        return matches[0] if matches else None

    @callback
    def _async_validate_device(
        self, key: str, entity: er.RegistryEntry | None,
        device: dr.DeviceEntry, target: MeteoSwissConfigEntry,
    ) -> None:
        """Protect unrelated entities, children, identifiers and scoped owners."""
        entities, devices = er.async_get(self.hass), dr.async_get(self.hass)
        owner = self.hass.config_entries.async_get_entry(device.config_entry_id)
        bound = er.async_entries_for_device(
            entities, device.id, include_disabled_entities=True
        )
        target_device = devices.async_get_device_by_identifier(
            (DOMAIN, key), target.entry_id
        )
        if owner is None or owner.domain != DOMAIN:
            raise _OwnershipConflict
        if device.config_subentry_id is not None:
            raise _OwnershipConflict
        if device.identifiers != {(DOMAIN, key)}:
            raise _OwnershipConflict
        if dr.async_entries_for_parent_device(devices, device.id):
            raise _OwnershipConflict
        if any(item.platform != DOMAIN or item.unique_id != f"{DOMAIN}_{key}"
               for item in bound):
            raise _OwnershipConflict
        if target_device is not None and target_device.id != device.id:
            raise _OwnershipConflict
        if entity is not None and entity.config_entry_id != device.config_entry_id:
            raise _OwnershipConflict

    @callback
    def _async_move_registry(self, target: MeteoSwissConfigEntry) -> bool:
        """Preflight both helpers; restore native snapshots on a failed move."""
        try:
            plan = self._async_plan(target)
        except Exception:
            self._async_block("Shared diagnostic registry ownership is ambiguous")
            return False
        entity_moves = [entity for entity, _ in plan if entity is not None
                        and entity.config_entry_id != target.entry_id]
        device_moves = [device for _, device in plan if device is not None
                        and device.config_entry_id != target.entry_id]
        try:
            self._async_apply_registry(entity_moves, device_moves, target.entry_id)
        except Exception:
            try:
                self._async_restore_registry(entity_moves, device_moves)
            except Exception:
                self._async_block("Shared diagnostic registry rollback needs review")
                return False
            self._async_block("Shared diagnostic registry transfer was rolled back")
            return False
        return True

    @callback
    def _async_apply_registry(
        self, entity_moves: list[er.RegistryEntry],
        device_moves: list[dr.DeviceEntry], target_id: str,
    ) -> None:
        """Move entities before device cleanup, without any intervening await."""
        entities, devices = er.async_get(self.hass), dr.async_get(self.hass)
        for entity in entity_moves:
            entities.async_update_entity(entity.entity_id, config_entry_id=target_id)
        for device in device_moves:
            devices.async_update_device(device.id, new_config_entry_id=target_id)
        # Re-derive CONFIG_ENTRY/DEVICE disablement against the moved device,
        # retaining explicit USER/INTEGRATION choices.
        for entity in entity_moves:
            entities.async_update_entity(entity.entity_id, config_entry_id=target_id)

    @callback
    def _async_restore_registry(
        self, entity_moves: list[er.RegistryEntry], device_moves: list[dr.DeviceEntry]
    ) -> None:
        """Restore native snapshots in the same event-safe order."""
        entities, devices = er.async_get(self.hass), dr.async_get(self.hass)
        for entity in entity_moves:
            entities.async_update_entity(entity.entity_id,
                                         config_entry_id=entity.config_entry_id)
        for device in device_moves:
            devices.async_update_device(device.id,
                new_config_entry_id=device.config_entry_id,
                disabled_by=device.disabled_by)
        for entity in entity_moves:
            entities.async_update_entity(entity.entity_id,
                config_entry_id=entity.config_entry_id, disabled_by=entity.disabled_by)

    @callback
    def _async_block(self, message: str) -> None:
        """Fail only the optional helpers, with a message-free local repair."""
        _LOGGER.warning(message)
        async_sync_shared_diagnostics_issue(self.hass, True)


@callback
def async_register_shared_diagnostics(
    hass: HomeAssistant,
    entry: MeteoSwissConfigEntry,
    add_entities: AddConfigEntryEntitiesCallback,
    factory: DiagnosticFactory,
) -> None:
    """Use one typed domain coordinator, not global per-sensor added flags."""
    data = hass.data.setdefault(DOMAIN, {})
    if (shared := data.get(DATA_SHARED_DIAGNOSTICS)) is None:
        shared = data[DATA_SHARED_DIAGNOSTICS] = SharedDiagnostics(hass)
    shared.async_register(entry, add_entities, factory)
