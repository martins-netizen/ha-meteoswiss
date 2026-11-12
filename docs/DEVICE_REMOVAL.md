# Remove an empty retired service group

**Availability:** unreleased development follow-up to the shared-diagnostic
lifecycle fix. Published stable 8.3.4 does not include this approval policy.
This is a bounded manual path, not automatic cleanup or a completed registry audit.

## Use the existing device page

An empty leftover group can remain associated with a current entry while its
identifier refers to an entry that no longer exists. The integration allows
Home Assistant's normal device-page **Delete** confirmation only for that
unambiguous, empty service record. Startup, refresh, reload and settings changes
never automatically remove a device.

Current weather, forecast/HGT, warnings, modelled pollen/AQ, measured pollen and
both shared diagnostic groups remain protected. A provider outage or disabled
entity/device does not establish that a group is obsolete. Use the existing
entry's settings to change its source or location.

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

The module joins the existing full line/branch gate. Dependency locks,
security floors, four-language catalogues and supported HA versions retain
their requirements. Release, operator acceptance and a production historical
inventory remain separate. The broader [stale-device assessment](GOLD_APPLICABILITY.md)
stays partial; this path does not complete Gold or justify the single-device exception.
