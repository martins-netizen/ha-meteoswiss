# Diagnostic defaults and virtual service metadata

**Status:** Released in [8.3.4b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4b1) on 7 November 2026. The operator confirmed normal operation on HA Core 2026.11.0 / HA OS 18.4; see the [bounded evidence](RELEASE_EVIDENCE_8.3.4b1.md). Stable 8.3.3 remains latest stable. [Stable 8.3.4 packaging](RELEASE_8.3.4.md) retains this accepted runtime and is prepared for review; publication/update remain pending.

## Two optional diagnostic helpers

The shared station-catalogue and cache-statistics entities are troubleshooting
tools. Their values and large technical attributes are not required for ordinary
weather, warning, forecast, pollen or air-quality entities. On first registration
only, both helpers set `entity_registry_enabled_default=False` and retain their
diagnostic category.

| Unique ID | Purpose | New registration |
|---|---|---|
| `meteoswiss_stations_map` | Station catalogue count, status and optional map attributes | Disabled |
| `meteoswiss_cache_stats` | Technical cache hit/miss summary | Disabled |

These are unique IDs, not guaranteed entity IDs. Existing registry entries keep
their enabled/disabled choice, entity ID, personal name and icon. A legacy
enabled helper is not disabled during an update or reload; a user-disabled
helper is not enabled. Users can enable either helper in its entity settings.

Disabled helpers do not poll or publish states. Provider coordinators still
own the weather data and required station metadata. In particular, the station
condition coordinator resolves its own catalogue through `get_stations_map`;
it does not depend on the optional catalogue entity being enabled. The existing
redacted integration diagnostics remain available independently of these helpers.

## Seven virtual device groups

These groups organise data services in HA rather than user-owned physical
devices. Each `DeviceInfo` now explicitly sets `DeviceEntryType.SERVICE`.
Identifiers are retained, including the deliberate distinction between current
weather and ICON forecasts. The [provider-metadata follow-up](PROVIDER_METADATA.md), included in the same beta,
corrects the alternative current source's labels without creating another group.

| Group | Existing identifier suffix | Manufacturer | Existing model label |
|---|---|---|---|
| Observed/current weather | Entry ID | MeteoSwiss or Open-Meteo, matching the selected current source | SwissMetNet or Weather Forecast API |
| Forecasts and HGT | `calculated_<entry_id>` | MeteoSwiss | ICON Seamless via Open-Meteo |
| Modelled pollen and air quality | `pollen_<entry_id>` | Open-Meteo | Air Quality API |
| Measured pollen | `ms_pollen_<entry_id>` | MeteoSwiss | Pollen Station |
| Warnings | `alerts_<entry_id>` | MeteoSwiss | Alerts |
| Shared station catalogue | `stations_map` | MeteoSwiss | SwissMetNet |
| Shared cache statistics | `cache_stats` | MeteoSwiss | Intelligent Caching |

Every identifier remains paired with the `meteoswiss` domain. These model labels
describe existing source/grouping metadata, not newly asserted hardware models.
No hardware revision, firmware version or serial number is invented. Personal
device names and device IDs survive the service-metadata update and reload.

The initial diagnostic-defaults change retained all legacy provider labels.
The follow-up now labels the alternative current source as Open-Meteo, including
its current-data attribution. It retains the same device/unique identifiers and
personal names; provider selection and other source groups do not change.
Published stable 8.3.3 still has the old labels. The quality assessment remains
bounded rather than claiming a complete metadata audit.

## Regression scope

Native HA tests run for the current 2026.11.0 and minimum 2026.8.3 environments
with both MeteoSwiss and Open-Meteo configurations. They check:

- Fresh diagnostic entries are registered disabled and perform no polling.
- Ordinary weather, measured pollen, temperature and warning entities stay
  enabled and publish states.
- All seven service groups have manufacturer/model metadata.
- Existing enabled, user-disabled and integration-disabled choices, personal
  entity names/icons, IDs and device-name overrides survive setup and reload.
- Manual enablement reuses the same entity/device IDs and allows polling.
- An explicitly enabled catalogue entity still handles outage and recovery;
  existing source tests continue to exercise independent station metadata.

Device lookups in these tests are scoped to the owning configuration entry,
avoiding the registry lookup deprecated in HA 2026.11.

The [quality matrix](QUALITY_SCALE.md) records bounded engineering evidence.
This change does not complete all Gold requirements or assert an official tier,
and it performs no installation, release publication or manual device test.

## Primary guidance

- [Optional/noisy entity defaults](https://contributors.home-assistant.io/core/quality-scale/entity-disabled-by-default/)
- [Device metadata and services](https://contributors.home-assistant.io/core/quality-scale/devices/)
