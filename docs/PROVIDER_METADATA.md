# Current-weather provenance and station-group preservation

**Status:** Delivered in published [stable 8.3.4](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4), the current normal update target, on 7 November 2026. See [publication evidence](RELEASE_EVIDENCE_8.3.4.md). The behaviour first shipped in 8.3.4b1; its operator-confirmed normal operation on HA Core 2026.11.0 / HA OS 18.4 remains [bounded beta evidence](RELEASE_EVIDENCE_8.3.4b1.md). Stable retains that runtime unchanged apart from two version fields.

## Correct the selected current source

The current-weather entity and ordinary current-value sensors share the same
entry-owned service group. The selected `data_source` now determines its
default labels and their attribution:

| Current source | Default group name | Manufacturer | Model | Attribution |
|---|---|---|---|---|
| MeteoSwiss, including legacy entries without a source field | MeteoSwiss followed by station name | MeteoSwiss | SwissMetNet | Source: MeteoSwiss |
| Open-Meteo | Open-Meteo Current Weather | Open-Meteo | Weather Forecast API | Source: Open-Meteo Weather Forecast API (modelled current conditions) |

The alternative source uses the existing `/v1/forecast` client for modelled
current conditions. Its data must not be labelled as SwissMetNet observations.
The source selector, requests, refresh timing, numeric values and units do not
change. The separate ICON forecast/HGT, measured pollen, modelled pollen/AQ,
warning and diagnostic groups keep their own provenance and identifiers.

An upgrade refreshes default device metadata on the same `(meteoswiss, entry_id)`
identifier. It does not remove or recreate entities/devices. HA retains existing
entity IDs, personal names/icons/aliases, enabled/disabled choices and personal
device names. Default group names can affect freshly generated entity IDs for
new installations; existing registry identities remain the authority.

## Pollen-station changes: reuse instead of cleanup

Measured pollen groups use `ms_pollen_<entry_id>`, not a station-specific device
ID. The configured station changes the group's default label and coordinator,
while the group and all entity bindings remain the same. Both Configure and
Reconfigure have native HA tests for Zurich → Bern → Zurich with both current
providers. They check all seven device IDs/identifiers and all registered entity
IDs/bindings, retained personal names/icons/aliases/display precision,
hidden/disabled choices, new station labels and the selected coordinator.
Neither entity removal nor device removal is called.

These tested station changes do not accumulate obsolete groups. Adding a
deletion pass for them would create unnecessary risk. This is a bounded
regression result, not an inventory of a real installation or a proof that no
older version ever left orphaned groups. Historical orphan handling remains a
separate review; this change does not delete user registry or Recorder data.

## Validation and release boundary

`test_provider_device_metadata.py` adds 18 cases for the current/minimum HA
fixtures: eight source/family metadata cases, six native existing-registration
setup/reload cases and four native pollen-station round trips. The Open-Meteo
metadata regression fails against the previous source before the correction.
The original source, diagnostic-default and entity-identity tests remain active.
No validation gate, warning rule, dependency pin or advertised HA minimum changes.

The operator-confirmed normal operation closes the agreed short beta check.
A separate manual alternative-source inspection was not reported; the native
source/registry tests above remain the evidence for that path. No production
source switch, repeated acceptance or device deletion is requested. Publication
and the bounded operator report remain separate from automated tests.
Remaining entity classes, historical obsolete-group questions and rule-specific
exemption review prevent a complete Gold claim.
