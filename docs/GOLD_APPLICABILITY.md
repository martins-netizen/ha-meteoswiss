# Gold applicability: discovery and service-group lifecycle

**Review version:** 1.0 · **Reviewed:** 10 November 2026
**Scope:** development after HGT PR #92, commit
`4e86e0653aa8218edc4b725bc029cc54d0552458`.

This records the project's engineering assessment against the current Home
Assistant rules. Custom integrations have no official quality tiers. A reasoned
exemption describes applicability; it does not implement a missing capability or
complete Gold. This documentation review changes no component or HA registry.

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

## Seven virtual groups need a separate lifecycle assessment

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

The official [dynamic-devices rule](https://contributors.home-assistant.io/core/quality-scale/dynamic-devices/)
requires devices appearing after setup to be added without reloading. Its
documented exception concerns a single fixed device that shares the config
entry's lifetime. Our seven groups, including shared diagnostics, do not fit
that literal exception. The matrix therefore records **bounded fixed-group
evidence**, leaving the overall rule partial for review; it does not turn the
former exemption candidate into a blanket exemption.

The same single-device exception appears in
[stale-devices](https://contributors.home-assistant.io/core/quality-scale/stale-devices/).
That rule also remains partial. Current station changes reuse the groups, but
historical orphaned groups have not been independently inventoried. The
integration does not implement a dedicated `async_remove_config_entry_device`
approval policy. No automatic cleanup, deletion permission, registry migration
or production inventory is introduced by this assessment.

## Evidence and remaining boundaries

Existing native HA tests in
[test_provider_device_metadata.py](../tests/test_provider_device_metadata.py)
exercise both current providers, setup/reload and Configure/Reconfigure pollen
station round trips. They retain all seven device IDs and entity bindings,
personal names, icons, aliases, hidden/disabled choices and display precision;
the station-change tests prohibit entity/device removal calls.
[test_diagnostic_defaults.py](../tests/test_diagnostic_defaults.py) additionally
covers retained diagnostic registration choices and enabling the existing
helpers. This is automated evidence, not a fresh manual registry audit or a
test of a newly paired device. [Provider evidence](PROVIDER_METADATA.md)
retains its original release and operator-acceptance boundaries.

Reassess these decisions when adding a discoverable device, stored network
address, hub/account inventory or dynamically created service group. Such work
needs identity, hot-addition, removal and shared-ownership tests. Existing
registry choices and Recorder history must remain part of that review.

The [Gold matrix](QUALITY_SCALE.md) keeps device classes/wind statistics,
entity translations and historical stale-device handling open. This assessment
does not raise the overall engineering result to completed Gold.
