# Fixed service groups: lifecycle evidence

**Reviewed baseline:** `cc4f494694609af28fd27c46c475a8270d3858ab`
(published 8.3.5b6 source). This follow-up adds native lifecycle tests and this
contract; it changes no runtime, requests, device identifiers or deletion policy.

The integration represents configured public weather services. A source
response supplies measurements, forecasts or warnings for an existing role; it
does not enumerate user-owned appliances that can appear or disappear. Station
and forecast catalogues provide choices for an explicit settings transaction.
A newly listed station is not automatically another Home Assistant device.

## The complete current topology

The first five service groups belong to each config entry. The last two exist
once per integration and have one runtime owner. All seven use native
`DeviceEntryType.SERVICE` records in the `meteoswiss` namespace.

| Role | Device identifier | What a source or settings change does |
|---|---|---|
| Current weather | `<entry_id>` | Station or Open-Meteo coordinates change the data and default display metadata. Optional measured HGT belongs to the MeteoSwiss measurement-station group. |
| Forecast/HGT | `calculated_<entry_id>` | Forecast-point changes reuse the group for forecasts and calculated forecast HGT; measured station HGT is separate. |
| Warnings | `alerts_<entry_id>` | Postcode changes reuse the group. An empty warning list is a valid result. |
| Modelled pollen and air quality | `pollen_<entry_id>` | The existing base location selects data for the same role. |
| Measured pollen | `ms_pollen_<entry_id>` | Pollen-station changes reuse the group. |
| Station catalogue | `stations_map` | A shared diagnostic role, initially disabled; catalogue rows are data. |
| Cache statistics | `cache_stats` | A shared diagnostic role, initially disabled. |

Optional sources register their entities before the background initial refresh.
Failure or recovery changes availability and values in the registered roles;
it does not determine which service groups exist. Disabling a diagnostic entity
also preserves its native registry record and user choice.

## Gold rule assessment

The current [dynamic-devices rule](https://contributors.home-assistant.io/core/quality-scale/dynamic-devices/)
requires newly appearing devices to be added without an integration reload. Its
single-fixed-device exception does not literally describe these seven groups.
The applicable lifecycle is assessed directly instead: the complete per-entry
role set already exists after setup, source results do not change that set,
and the two shared roles can move into an already loaded peer without a peer
reload or source refresh. There is no additional provider-owned device inventory
to poll or synthesize.

The [stale-devices rule](https://contributors.home-assistant.io/core/quality-scale/stale-devices/)
distinguishes an authoritative removed-device inventory from cases requiring a
manual removal hook. Source outages, a missing optional value and settings
changes do not retire these configured service roles. Native config-entry
removal retires its five local groups. Shared groups transfer to a loaded peer
before the old owner is removed; their existing entity and device IDs remain.
The final owner's removal leaves no current service groups.

For historical records, the existing
[manual removal contract](DEVICE_REMOVAL.md) remains narrow:
`async_remove_config_entry_device` approves only an unambiguous empty known
retired shell referring to an entry that no longer exists. Current, shared,
disabled, bound, linked, unknown and ambiguous records remain protected. The
native UI/Recorder regressions verify that approved shell removal retains
history. This follow-up neither widens that permission nor guesses at unknown
historical ownership.

Together these are reviewable evidence for the current fixed service topology,
rather than a blanket single-device exemption. A production historical registry
inventory is not claimed. Custom integrations have no formal Home Assistant
quality-tier award; the project's complete assessment remains in the
[quality matrix](QUALITY_SCALE.md).

## Native regression evidence

[test_fixed_service_topology.py](../tests/test_fixed_service_topology.py)
exercises the real Home Assistant config-entry, platform, flow-manager, entity
registry and device registry implementations. It replaces provider work,
diagnostic value updates and external settings validation; it uses the existing
captured forecast catalogue fixture rather than a fabricated device inventory.

| Cases | Native behavior checked |
|---|---|
| Both current providers | Optional initial failure, recovery and another failure preserve all seven role IDs and all entity bindings. Current weather remains usable. No entity or device removal is requested. Unload clears coordinator listeners and the shared runtime owner. |
| Both providers through Configure and Reconfigure | Station or coordinates, warning postcode, pollen station and forecast point change together, then return to the base selection. Each confirmed transaction reloads once. All seven IDs, entity bindings, disabled/hidden choices, personal names, icons, aliases and entity options survive; no entity or device deletion occurs. Old coordinators lose listeners and the borrowed session remains open. |
| Both shared-owner provider orders | Removing an owner transfers its live shared helpers to an already loaded peer with the same entity/device IDs, without peer reload or refresh. Core removes the departed entry's five groups; the peer retains exactly seven. Removing the final entry clears the remaining current groups and shared runtime owner. |

The focused file passes all eight cases on native Python 3.14.10 with Home
Assistant 2026.11.0 and 2026.11.2 (five existing dependency deprecation warnings
in each run). This is focused evidence, not a new full-suite result.

These eight cases complement the broader refusal, native admin UI and Recorder
tests in [test_device_removal.py](../tests/test_device_removal.py), the ownership
failure and pending-setup tests in
[test_diagnostic_lifecycle.py](../tests/test_diagnostic_lifecycle.py), and the
existing provider metadata and forecast-selection tests. They do not substitute
for those established ownership boundaries.

Reassess this contract when adding a dynamically created group, a hub/account
device inventory or a discoverable appliance. Such a change needs native
hot-addition and authoritative removal behavior, identity preservation and
appropriate shared-ownership tests.
