# Remove an empty retired service group

**Availability:** included in the published 8.3.5b6 test package, together with
the shared-diagnostic lifecycle fix. Published stable 8.3.4 does not include
this approval policy. The source candidate adds lifecycle evidence and updated
documentation; the bounded manual policy itself is unchanged.

## Use the existing device page

An empty leftover group can remain associated with a current entry while its
identifier refers to an entry that no longer exists. The integration allows
Home Assistant's normal device-page **Delete** confirmation only for that
unambiguous, empty service record. Startup, refresh, reload and settings changes
never automatically remove a device.

Current weather, forecast/HGT, warnings, modelled pollen/AQ, measured pollen and
both shared diagnostic groups remain protected. A provider outage or disabled
entity/device does not establish that a group is obsolete. Use the existing
entry's settings to change its configured station or location.

HA discovers removal support per integration, so Delete may also appear on a
protected group. HA refuses the request when the record fails the checks below.
It does not replace the group, move its entities, erase history or reload a peer.
Retain a refused group and review ownership/bindings; do not remove entities or
history to make it eligible. A [shared-ownership repair](SHARED_DIAGNOSTIC_LIFECYCLE.md#ownership-repair)
is separate; this path cannot delete either shared helper or clear its repair.

## Exact approval boundary

All checks must hold when HA calls the hook after the user's confirmation:

| Check | Required result |
|---|---|
| Entry | The same registered MeteoSwiss entry, loaded and enabled; HA is not stopping. |
| Snapshot | Current native main-device record owned by that entry, with service type, no subentry or retained composite/split metadata. |
| Connections | Device enabled, no hardware connections or upstream device link. |
| Identifier | Exactly one `meteoswiss` identifier in a reviewed entry-group form, with a recognised legacy UUID-hex/current ULID entry ID. |
| Embedded entry | No entry with that ID exists, including disabled, unloaded, failed or other-domain entries. |
| Entities | No registered entity, including disabled/hidden, foreign-platform or cross-entry bindings. |
| Relationships | No child device or main device links through this device. |
| Uniqueness | No other main/child device carries the identifier. |

The source-defined forms are `<entry_id>`, `calculated_<entry_id>`,
`alerts_<entry_id>`, `pollen_<entry_id>` and `ms_pollen_<entry_id>`.
`stations_map` and `cache_stats` do not match and always remain protected.
Unknown/malformed identifiers, ambiguous records and stale snapshots are
refused; a registry-read exception cannot fall back to approval.

The classifier is synchronous and read-only. The async hook has no await,
registry write, coordinator operation or provider request. HA performs native
removal only after confirmation and a successful final classification. The
policy never directly removes an entity or Recorder data.

## Evidence and limits

The reachable history reviewed here contains **97 relevant revisions and 130
distinct source blobs** across the five active entity modules (`entity.py`,
`sensor.py`, `weather.py`, `binary_sensor.py`, `pollen_sensor.py`). Parsed
identifier expressions reduce to the five entry-scoped forms and two shared
keys above; no additional historical family was established. This bounded
source review proves neither a production orphan nor a scan of every removed
module or external copy.

[Native tests](../tests/test_device_removal.py) cover both providers, all five
forms and both ID formats; admin device-page WebSocket removal; all seven
protected current groups and personal choices; disabled/foreign/cross-entry
entities; retained entries in different states; links/children/duplicates;
split/corrupt read snapshots; unready/shutdown contexts and read failures. A
real temporary Recorder database retains historical rows after removing an
eligible shell; current weather identities and values remain unchanged.

The module remains in the existing full line/branch gate. Dependency locks,
security floors, four-language catalogues and supported HA versions retain
their requirements. A production historical registry inventory is not claimed.

The [fixed service-topology evidence](FIXED_SERVICE_TOPOLOGY.md) adds eight
native cases on HA 2026.11.0 and 2026.11.2. They verify all seven groups across
optional source failure/recovery, complete Configure/Reconfigure selection
round trips and removal of both shared-owner provider orders. Source changes
retain the groups; native entry removal retires its five local groups, hands
shared groups to a loaded peer without its reload or refresh, and clears the
current groups after the final entry. These tests add no removal permission.

The [lifecycle applicability review](GOLD_APPLICABILITY.md) now records the
dynamic/stale rules as met for that fixed service model and this conservative
manual fallback. It does not use the literal single-fixed-device exception for
seven groups, extend the classifier to unknown historical records or require
an invented provider inventory. A future dynamic device model needs a new
identity, hot-addition and removal assessment.

The [Gold evidence contract](GOLD_EVIDENCE_CONTRACT.md) and
[completion review](GOLD_COMPLETION_REVIEW.md) separate the engineering source
candidate from approved merges, package publication and actual installed
operator evidence. This manual path alone is not complete Gold; custom
integrations have no formal Home Assistant tier award. Existing published b6
acceptance retains its own scope.
