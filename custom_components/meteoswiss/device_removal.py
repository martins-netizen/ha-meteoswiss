"""Read-only approval for explicitly removing an empty, retired service group."""

from __future__ import annotations

from enum import StrEnum
import re

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN
from .runtime_data import MeteoSwissConfigEntry

# These five identifier forms are present in the reviewed source history.
# Accept HA's legacy UUID hex and current ULID entry IDs, never location names.
_ENTRY_GROUP = re.compile(
    r"(?:(?:calculated|alerts|pollen|ms_pollen)_)?"
    r"(?P<entry_id>[0-9a-f]{32}|[0-7][0-9A-HJKMNP-TV-Z]{25})"
)


class DeviceRemovalStatus(StrEnum):
    """Technical classifications; no personal registry values are exposed."""

    ENTRY_NOT_READY = "entry_not_ready"
    DEVICE_PROTECTED = "device_protected"
    UNKNOWN_GROUP = "unknown_group"
    ENTRY_STILL_EXISTS = "entry_still_exists"
    ENTITY_BINDINGS = "entity_bindings"
    DEVICE_LINKS = "device_links"
    AMBIGUOUS_IDENTIFIER = "ambiguous_identifier"
    EMPTY_RETIRED_GROUP = "empty_retired_group"


@callback
def async_device_removal_status(
    hass: HomeAssistant,
    entry: MeteoSwissConfigEntry,
    device: dr.AnyDeviceEntry,
) -> DeviceRemovalStatus:
    """Classify without changing registries, state, history or source polling.

    HA calls the approval hook only after the user's device-page confirmation.
    No await separates this final snapshot from HA's native removal operation.
    Unknown or still-bound records always remain protected.
    """
    if (
        hass.is_stopping
        or entry.domain != DOMAIN
        or hass.config_entries.async_get_entry(entry.entry_id) is not entry
        or entry.state is not ConfigEntryState.LOADED
        or entry.disabled_by is not None
    ):
        return DeviceRemovalStatus.ENTRY_NOT_READY

    devices = dr.async_get(hass)
    if not _is_retirable_device(devices, entry, device):
        return DeviceRemovalStatus.DEVICE_PROTECTED
    if len(device.identifiers) != 1:
        return DeviceRemovalStatus.UNKNOWN_GROUP
    namespace, identifier = next(iter(device.identifiers))
    match = _ENTRY_GROUP.fullmatch(identifier) if namespace == DOMAIN else None
    if match is None:
        return DeviceRemovalStatus.UNKNOWN_GROUP
    if hass.config_entries.async_get_entry(match["entry_id"]) is not None:
        return DeviceRemovalStatus.ENTRY_STILL_EXISTS
    if er.async_entries_for_device(
        er.async_get(hass), device.id, include_disabled_entities=True
    ):
        return DeviceRemovalStatus.ENTITY_BINDINGS
    if dr.async_entries_for_parent_device(devices, device.id) or any(
        other.via_device_id == device.id for other in devices.devices
    ):
        return DeviceRemovalStatus.DEVICE_LINKS
    if len(devices.async_get_devices(identifiers=device.identifiers)) != 1 or any(
        child.identifiers & device.identifiers for child in devices.child_devices
    ):
        return DeviceRemovalStatus.AMBIGUOUS_IDENTIFIER
    return DeviceRemovalStatus.EMPTY_RETIRED_GROUP


@callback
def _is_retirable_device(
    devices: dr.DeviceRegistry,
    entry: MeteoSwissConfigEntry,
    device: dr.AnyDeviceEntry,
) -> bool:
    """Require the current, entry-owned main service record with no split/link."""
    return (
        isinstance(device, dr.DeviceEntry)
        and devices.async_get(
            device.id, include_child_devices=False, include_composite_devices=False
        ) is device
        and device.config_entry_id == entry.entry_id
        and device.config_subentry_id is None
        and device.entry_type is dr.DeviceEntryType.SERVICE
        and device.disabled_by is None
        and device.composite_device_id is None
        and not device.has_composite_identifiers
        and not device.connections
        and device.via_device_id is None
    )
