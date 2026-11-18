# Gold applicability: discovery and service-group lifecycle

**Review version:** 1.1 · **Reviewed:** 17 November 2026
**Scope:** published 8.3.5b6 baseline
`cc4f494694609af28fd27c46c475a8270d3858ab` and the source candidate's new native
fixed-topology evidence. Version 1.0 assessed the earlier development baseline
`4e86e0653aa8218edc4b725bc029cc54d0552458` on 10 November.

This records the project's engineering assessment against the current Home
Assistant rules. Custom integrations have no official quality tiers. Discovery
exceptions and the reviewed lifecycle behavior below are separate decisions.
This documentation and test follow-up changes no component or HA registry.

## Discovery: two rules do not apply to this service

The [manifest](../custom_components/meteoswiss/manifest.json) declares a
`service` integration using `cloud_polling`. Users select the current source,
station or coordinates, forecast point, pollen station and warning postcode in
the [config flow](../custom_components/meteoswiss/config_flow.py). These public
weather services expose data catalogues, rather than a local device or bus that
can announce the user's chosen service to Home Assistant.

| Rule | Project assessment | Reason and evidence |
|---|---|---|
| [discovery](https://contributors.home-assistant.io/core/quality-scale/discovery/) | Exempt | HA permits an exception when the service cannot be discovered. There is no discoverable local appliance, account-owned device inventory or discovery protocol for the configured public weather selection. The manifest has no discovery declarations; setup starts with `async_step_user`, then the explicit MeteoSwiss/Open-Meteo and location-selection steps. This code evidence supports the service-specific reason; an absent discovery handler alone would not justify an exemption. |
| [discovery-update-info](https://contributors.home-assistant.io/core/quality-scale/discovery-update-info/) | Exempt | HA exempts integrations whose devices cannot be discovered. This integration has no discovered device host/IP stored in its config entry to refresh. Normal provider DNS resolution is handled by the HTTP client. Changing a station or forecast target is an explicit settings transaction, not rediscovery of a device address. |

Station-catalogue refresh and forecast-point search are data selection features.
They must not be presented as network discovery. The
[source guide](API_SOURCES.md) records their requests and schedules; this review
adds no network scanning, new requests, permissions or configuration fields.

## Seven virtual groups have a fixed service lifecycle

The integration exposes a fixed service-group layout. These are the existing
device-registry identifiers, with `<entry_id>` denoting the HA config entry:

| Group | Identifier in the `meteoswiss` namespace | Ownership |
|---|---|---|
| Current weather | `<entry_id>` | Config entry; labels follow the selected current provider. |
| Forecast/HGT | `calculated_<entry_id>` | Config entry; labels follow its forecast target. |
| Warnings | `alerts_<entry_id>` | Config entry. |
| Modelled pollen/air quality | `pollen_<entry_id>` | Config entry. |
| Measured pollen | `ms_pollen_<entry_id>` | Config entry; station changes retain the identifier. |
| Station catalogue | `stations_map` | Shared diagnostic group, not a station-specific device. |
| Cache statistics | `cache_stats` | Shared diagnostic group, not a station-specific device. |

[Shared metadata](../custom_components/meteoswiss/entity.py),
[sensors](../custom_components/meteoswiss/sensor.py),
[warnings](../custom_components/meteoswiss/binary_sensor.py) and
[pollen entities](../custom_components/meteoswiss/pollen_sensor.py) define this
layout. Configured sources do not enumerate appliances newly paired to a hub or
added to a cloud account. A new catalogue station becomes a selectable data
source; it does not automatically become another HA device.

## Lifecycle rules: reviewed behavior for the current model

Both official lifecycle rules document an exception for one fixed device with
the same lifetime as its config entry. The seven groups here do not fit that
literal exception. Their current behavior is reviewed directly against the
rules, with the complete [fixed-topology contract](FIXED_SERVICE_TOPOLOGY.md)
and native lifecycle evidence.

| Rule | Project assessment | Behavior and evidence |
|---|---|---|
| [dynamic-devices](https://contributors.home-assistant.io/core/quality-scale/dynamic-devices/) | Reviewed; met for the current fixed service model | The complete role set is registered during setup, before optional source results. Failure, recovery and catalogue changes do not introduce another device role. Shared diagnostic helpers can be added to an already loaded peer during ownership handoff, retaining registry IDs without a peer reload or source refresh. There is no hub/account inventory to enumerate. |
| [stale-devices](https://contributors.home-assistant.io/core/quality-scale/stale-devices/) | Reviewed; met for the current fixed service model and conservative manual fallback | Station, coordinates, postcode, pollen and forecast-point changes reuse the roles and their bindings. Core removes the departing entry's five local groups; shared groups transfer to a loaded peer and disappear with the final entry. The native manual-removal hook covers attributable empty retired shells while protecting current, bound and ambiguous records. Source outages do not establish removal. |

The [native removal policy](DEVICE_REMOVAL.md) and
[shared-diagnostic lifecycle](SHARED_DIAGNOSTIC_LIFECYCLE.md) are included in the
published 8.3.5b6 test package. The shared lifecycle has an explicit runtime
owner and registry-preserving handoff. Changed startup order retains device
IDs, and ambiguous legacy ownership blocks only the optional helpers with a
repair instead of deleting or merging records.

Manual `async_remove_config_entry_device` approval remains limited to an
unambiguous empty service shell whose reviewed identifier refers to an entry
that no longer exists. Current/shared groups, disabled or linked devices and
every registered entity binding remain protected. This evidence follow-up
does not widen that approval, add automatic cleanup or change Recorder history.

This closes the former partial lifecycle assessment for the supported fixed
service model. It establishes neither a production orphan inventory nor a
blanket exemption for future device models. Unknown historical records retain
their conservative ownership protection; inventing an external inventory or
guessing at deletion would not strengthen this contract.

## Native evidence and release boundaries

The new eight cases in
[test_fixed_service_topology.py](../tests/test_fixed_service_topology.py)
pass on native Home Assistant 2026.11.0 and 2026.11.2. Both current providers
retain all seven groups through optional initial failure, recovery and another
failure. Configure and Reconfigure round trips change the configured station
or coordinates, warning postcode, pollen station and forecast point while preserving
all IDs, bindings and user choices, with no entity/device deletion. Native
entry removal transfers live shared helpers to an already loaded peer without
its reload or refresh, retires the removed entry's five local groups, and
clears current groups after the final entry is removed.

Existing native HA tests in
[test_provider_device_metadata.py](../tests/test_provider_device_metadata.py)
exercise both current providers, setup/reload and Configure/Reconfigure pollen
station round trips. They retain all seven device IDs and entity bindings,
personal names, icons, aliases, hidden/disabled choices and display precision;
the station-change tests prohibit entity/device removal calls.
[test_diagnostic_defaults.py](../tests/test_diagnostic_defaults.py) additionally
covers retained diagnostic registration choices and enabling the existing
helpers. [test_diagnostic_lifecycle.py](../tests/test_diagnostic_lifecycle.py)
covers pending setup, disabled records, registry conflicts, rollback and
Recorder history during handoff. The
[native device-removal tests](../tests/test_device_removal.py) cover the real
admin UI path, refusal cases and retained Recorder history. These are automated
fixed-service lifecycle proofs, rather than a test of a newly paired appliance
or a production historical registry audit.

The [Gold evidence contract](GOLD_EVIDENCE_CONTRACT.md) records the source and
test links checked by CI. The [completion review](GOLD_COMPLETION_REVIEW.md)
and [quality matrix](QUALITY_SCALE.md) record the complete engineering source
assessment. Candidate source evidence does not establish that its PRs have
merged, that a new package has been published or that the candidate has passed
installed operator checks. Existing [provider evidence](PROVIDER_METADATA.md)
and published b6 evidence retain their own acceptance scope. No official
Home Assistant tier or independent certification is claimed.

Reassess these decisions when adding a discoverable device, stored network
address, hub/account inventory or dynamically created service group. Such work
needs identity, hot-addition, removal and shared-ownership tests. Existing
registry choices and Recorder history must remain part of that review.
