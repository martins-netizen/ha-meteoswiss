# Native entity-name coverage

**Review:** 12 November 2026, after service-group naming PR #105. This follow-up
adds native tests and documentation; component files, catalogues, dependencies,
workflows and published stable 8.3.4 are unchanged.

The official Gold [entity-translations rule](https://contributors.home-assistant.io/core/quality-scale/entity-translations/)
concerns entity names supplied through HA's translation mechanism. A suitable
device-class name is also supported. An entity with no own name can inherit its
device's name. This review checks the integration's actual registered entities,
rather than inferring coverage from equal JSON key counts.

## Complete exposed-name inventory

Each configured provider registers the following layout when all source roles
are configured. Two optional diagnostics are disabled on first registration.
Missing provider values do not remove the corresponding named entities.

| Family | Registry entries per configured provider | Naming contract |
|---|---:|---|
| Current observations | 12 | Native sensor keys; Open-Meteo uses `precipitation_modelled` while retaining the precipitation identity. |
| Scalar forecasts | 8 | Separate today/tomorrow names for temperature extrema, rain and probability. |
| Air quality and UV | 5 | Native sensor names, retaining provider provenance. |
| Modelled pollen | 5 | Native names; technical pollen types and level attributes remain compatible. |
| Measured pollen | 7 | Native measured-pollen names, distinct from modelled values. |
| Forecast heating degree days | 1 | Native name retaining its forecast meaning. |
| Optional diagnostic helpers | 2 | Native names with retained activation choices. |
| Warning binary sensors | 3 | Native entity names; existing on/off state translations remain separate. |
| Current and forecast weather | 2 | No own name; each inherits its translated service-device name. |
| **Total** | **45** | **40 sensors, three binary sensors and two weather entities.** |

Across both providers, the inventory uses 41 distinct sensor name keys and three
binary-sensor keys. Four legacy sensor keys remain in all catalogues:
`soil_temperature_5cm`, `soil_temperature_10cm`, `soil_temperature_20cm` and
`season_heating_degree_days`. They do not imply active entities or a supported
seasonal forecast accumulator. No key or entity is removed by this review.

## Native evidence

[The complete-name tests](../tests/test_entity_name_translations.py) use real HA
setup, registry and entity platforms, replacing only provider I/O. For each
provider and DE/EN/FR/IT they verify every exposed translation key, HA-loaded
label, registry original name, live entity name and visible friendly name.
The weather entities are checked explicitly for device-name inheritance.
An inventory guard distinguishes active provider keys from the four legacy keys.

Full language round trips retain all 45 registry identities, entity/device
bindings, personal names, icons, aliases, areas, labels, hidden choices and
sensor precision. Enabled, user-disabled and integration-disabled cases are
covered both with and without personal names. HA's normal setup/reload owns
rendering; no language listener or peer-source reload is introduced.

The existing [diagnostic-name tests](DIAGNOSTIC_TRANSLATIONS.md) and
[service-group tests](SERVICE_GROUP_TRANSLATIONS.md) retain their own source,
privacy and temporary Recorder evidence. This follow-up adds no database access
or migration and does not repeat operator installation or acceptance.

## Applicability and remaining boundaries

Technical attribute keys/values, provider brands and raw station/postcode text
remain API contracts. Translating `level_name`, diagnostic state formats or
provider-supplied warning content would need a separate compatibility design.
Authoritative multilingual place aliases are a separate provider-data task;
their absence is not a missing entity-name key. Browser-specific language
behaviour is not independently exercised by these backend tests.

The project records automated engineering evidence for every exposed entity
name. Release/operator UI acceptance of the unreleased naming changes remains
open. Device lifecycle, wind-statistics acceptance, independent security review
and the overall [Gold assessment](QUALITY_SCALE.md) remain separate. Custom
integrations have no official HA quality tier.
