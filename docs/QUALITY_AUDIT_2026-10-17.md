# Bronze/Silver audit of 17 October 2026

**Document version:** 1.1 · **English edition:** 21 October 2026
**Original status:** Q1 assessment complete; implementation gaps remained.
**Reviewed commit:** `6d743546c8d0187a8bc91f870e8c50b3e7294147` on development.
Runtime, translations and tests matched `9c50b6b`.

This is a historical rule-by-rule assessment, not the current deployment status.
Later warning/icon, UV and oak corrections have landed, runtime acceptance and
beta publication are complete, and the operator confirmed the HACS source switch.
A clean first install remains open. Consult [release readiness](RELEASE_READINESS.md)
and the updated [quality matrix](QUALITY_SCALE.md) before treating a historical
finding below as still unresolved.

At the original baseline, field help, configurable polling, common module layout,
optional UV behaviour and four under-covered modules prevented a complete
Silver self-assessment. This assessed development, not a newly installed HA version.

The [official rules](https://contributors.home-assistant.io/core/quality-scale/rules/)
contain twenty Bronze and ten Silver rules. **Evidenced** refers to observed
code/test/documentation evidence. **Partial/open** identifies a missing item.
**Exempt** uses a rule-specific applicability justification. Applying Core rules
does not award a custom/HACS integration an official tier. Fork documentation
is assessed without claiming inclusion in the official Core documentation.

## Bronze: all twenty rules

| Rule | Assessment at the original baseline | Evidence and remaining work |
|---|---|---|
| [action-setup](https://contributors.home-assistant.io/core/quality-scale/action-setup/) | Exempt | No integration-specific actions/services in __init__.py or active platforms. weather.get_forecasts is a HA platform action. |
| [appropriate-polling](https://contributors.home-assistant.io/core/quality-scale/appropriate-polling/) | Partial/open | Bounded coordinator polling; observations at least 600 seconds. Config flow exposes update_interval, while the rule expects a developer-chosen interval. Decide compatibility of legacy values before changing it. |
| [brands](https://contributors.home-assistant.io/core/quality-scale/brands/) | Partial/open | Local HACS icons exist and were checked. The specified home-assistant/brands/core_integrations/meteoswiss path returned 404 on the review date. Local assets are not that external Core evidence; no unreviewed brand PR or official badge. |
| [common-modules](https://contributors.home-assistant.io/core/quality-scale/common-modules/) | Partial/open | const.py, runtime_data.py and weather_data.py share contracts. No common entity.py yet; coordinators also live in platform/source modules. Review repeated basics/layout without rebuilding source boundaries. |
| [config-flow](https://contributors.home-assistant.io/core/quality-scale/config-flow/) | Partial/open | Native setup/options, validation and duplicate protection exist. Visible fields lacked data_description in all four languages. Review selectors, data/options and interval together. |
| [config-flow-test-coverage](https://contributors.home-assistant.io/core/quality-scale/config-flow-test-coverage/) | Evidenced | tests/test_config_flow.py covers both sources, correctable errors, catalogue retry, total timeout/cancellation, old/new duplicates and identity-preserving options. Config flow has 100% lines/branches, enforced in CI. |
| [dependency-transparency](https://contributors.home-assistant.io/core/quality-scale/dependency-transparency/) | Exempt | Manifest requirements are empty: no extra Python runtime dependencies. HA-provided libraries belong to HA. Internet/provider dependencies are documented separately and are not this rule. |
| [docs-actions](https://contributors.home-assistant.io/core/quality-scale/docs-actions/) | Exempt | No custom actions; USAGE.md explains the standard HA forecast action. |
| [docs-conditions](https://contributors.home-assistant.io/core/quality-scale/docs-conditions/) | Exempt | No integration/device-specific conditions; USAGE.md references normal HA state conditions. |
| [docs-high-level-description](https://contributors.home-assistant.io/core/quality-scale/docs-high-level-description/) | Evidenced | README explains benefits, data families, provenance and limits, with entry points for newcomers and experienced users. |
| [docs-installation-instructions](https://contributors.home-assistant.io/core/quality-scale/docs-installation-instructions/) | Evidenced; practice separate | README, getting-started, migration and USAGE.md describe setup/source switch. At that date practical HACS/user acceptance was not complete. |
| [docs-removal-instructions](https://contributors.home-assistant.io/core/quality-scale/docs-removal-instructions/) | Evidenced | USAGE.md covers entry/entities/HACS software and dependent dashboards/automations without instructing history deletion. |
| [docs-triggers](https://contributors.home-assistant.io/core/quality-scale/docs-triggers/) | Exempt | No custom integration/device triggers. USAGE.md explains normal state/numeric triggers. |
| [entity-event-setup](https://contributors.home-assistant.io/core/quality-scale/entity-event-setup/) | Evidenced | CoordinatorEntity owns listeners. The extra weather forecast listener is subscribed on addition and removed with async_on_remove; lifecycle/WebSocket tests verify refresh and cleanup. |
| [entity-unique-id](https://contributors.home-assistant.io/core/quality-scale/entity-unique-id/) | Evidenced | Active families use entry-based or intentionally shared diagnostic IDs. Complete setup/reload/unload and registered warning/measurement tests verify stable mapping. |
| [has-entity-name](https://contributors.home-assistant.io/core/quality-scale/has-entity-name/) | Evidenced | All nine active entity classes across sensor/weather/binary-sensor/pollen platforms set _attr_has_entity_name = True. |
| [runtime-data](https://contributors.home-assistant.io/core/quality-scale/runtime-data/) | Evidenced | Typed MeteoSwissConfigEntry/MeteoSwissRuntimeData; only shared diagnostic ownership remains domain-global. |
| [test-before-configure](https://contributors.home-assistant.io/core/quality-scale/test-before-configure/) | Evidenced | Both providers check the real observation coordinator before save, within a 30-second total timeout. Tests cover success, correctable errors, timeout and cancellation. |
| [test-before-setup](https://contributors.home-assistant.io/core/quality-scale/test-before-setup/) | Evidenced | First coordinator refresh precedes platform setup and supports HA retry. Optional sources do not block valid observations. The initial-failure test verifies session/runtime ownership. |
| [unique-config-entry](https://contributors.home-assistant.io/core/quality-scale/unique-config-entry/) | Evidenced | Provider/station/coordinate/warning-postcode guards plus HA unique-ID checks, including old entries without unique IDs. Duplicate tests avoid unnecessary requests. |

## Silver: all ten rules

| Rule | Assessment at the original baseline | Evidence and remaining work |
|---|---|---|
| [action-exceptions](https://contributors.home-assistant.io/core/quality-scale/action-exceptions/) | Exempt | No custom integration actions; reassess if introduced. |
| [config-entry-unloading](https://contributors.home-assistant.io/core/quality-scale/config-entry-unloading/) | Evidenced | HA platform teardown, managed tasks/listeners and HA-owned session. Real-Recorder reliability tests cover both providers, reload, stable IDs and all polling listeners removed. Startup tests cancel optional child refreshes. |
| [docs-configuration-parameters](https://contributors.home-assistant.io/core/quality-scale/docs-configuration-parameters/) | Evidenced | USAGE.md explains interval and independent measured-pollen station, effects and Configure entry point. Missing field help was a separate Bronze gap. |
| [docs-installation-parameters](https://contributors.home-assistant.io/core/quality-scale/docs-installation-parameters/) | Evidenced | Source, observation station, warning postcode, coordinates, interval, limits and forecast location are documented. A station entry's postcode does not automatically select its forecast point. |
| [entity-unavailable](https://contributors.home-assistant.io/core/quality-scale/entity-unavailable/) | Partial/open | Registered entities cover main-source failure/recovery. Optional UV formerly returned None for both outage and missing data while inheriting successful AQ availability. Separate UV state and catalogue-cache diagnostic semantics were required. UV has since been corrected; see current matrix. |
| [integration-owner](https://contributors.home-assistant.io/core/quality-scale/integration-owner/) | Evidenced | @martins-netizen is manifest codeowner and active maintainer. Public Issues/forms and private reporting were verified on 17 October. |
| [log-when-unavailable](https://contributors.home-assistant.io/core/quality-scale/log-when-unavailable/) | Partial/open | Private transition logs exist for observations, warnings, forecasts and pollen/AQ. The separate UV request originally had only debug errors, no transition state/log. Later UV correction must be assessed against its own evidence. |
| [parallel-updates](https://contributors.home-assistant.io/core/quality-scale/parallel-updates/) | Evidenced | sensor.py uses 1 for polling diagnostics; coordinator-driven weather/binary/pollen platforms use 0. Zero means no entity semaphore limit, not zero network calls. No custom device actions. |
| [reauthentication-flow](https://contributors.home-assistant.io/core/quality-scale/reauthentication-flow/) | Exempt | Current public providers need no account/credentials. |
| [test-coverage](https://contributors.home-assistant.io/core/quality-scale/test-coverage/) | Open | Aggregate 99.0517% does not satisfy >95% per module. camera.py, hydro.py, slf.py and version.py were at 0%; no exemption/exclusion is justified solely by the aggregate. |

## Original evidence and limits

All seven [PR #25](https://github.com/martins-netizen/ha-meteoswiss/pull/25)
checks passed. After regular squash merge to 6d74354,
[CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/39043774226),
[CodeQL](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/39043774225)
and [HACS](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/39043774217)
passed. CI used HA 2026.8.3 and 2026.10.1.

An additional existing HA 2026.10.2 run, with official dependency constraints,
passed 762 tests. Re-read coverage contained 2379/2408 statements and 650/650
branches, combined 99.0516678%. Only const.py (98.5075%) and the four listed
modules were below 100%. No identical full suite was rerun merely for these
documentation edits; code equality and recorded runs were the stated evidence,
not new live acceptance.

Relevant regressions include
[config flow](../tests/test_config_flow.py),
[reliability](../tests/test_reliability.py),
[warning contracts](../tests/test_entity_warning_contracts.py),
[weather](../tests/test_weather_entity.py),
[pollen](../tests/test_pollen_sources.py),
[precipitation](../tests/test_precipitation_sources.py) and
[station logging](../tests/test_station_logging.py).
They exercise recovery, registry/statistic identity, Recorder upserts,
session ownership, listener cleanup and private error output.

### Mapping the UV finding to the installed version

The same UV gap already existed in **V1.5 / 567a5e4**. Comparing
pollen_coordinator_openmeteo.py and sensor.py with 6d74354 showed identical files.
It was newly recognised, not introduced by a later candidate. This was the
failure/status path; a currently displayed UV value was not thereby invalid.
The old behaviour exposed unknown rather than independently evidenced
unavailability on a UV-only request failure while retaining healthy AQ.
Subsequent corrections are recorded separately.

## Original targeted implementation work after R0

1. Add translated data_description help for actual fields in DE/EN/FR/IT.
   Explain source, measurement station, warning postcode and forecast coordinates.
   Remove ordinary user polling-interval configuration only after deciding how
   existing custom values migrate; do not silently change provider load.
2. Distinguish a successful UV response without a value from transport/payload
   failure and recovery. Isolate UV while retaining healthy AQ/pollen; add private
   once-per-transition logs and registered entity tests. This item later landed.
3. Review references before deciding the scope of inactive radar/hydro/SLF files.
   Historical comments about unavailable APIs are not current evidence.
   Shared-feed flood/avalanche warnings are independent. Retain version consistency;
   avoid meaningless imports solely to improve percentages.
4. Review repeated device info/attribution/base properties and introduce a
   suitable small common entity/coordinator building block without merging sources.
5. Separate local HACS branding from external Core-brand evidence; do not imply
   an official tier.

Runtime PRs need targeted regressions and required CI. Work order and compatibility
are tracked in the [development plan](NEXT_RELEASE_PLAN.md).

## Historical warning-state UX finding

The 17 October screenshot showed the German UI labels “Sicher/Unsicher”
(safe/unsafe), caused by SAFETY device class on all three warning sensors.
An inactive warning sensor does not establish general safety. This was a
presentation finding, not proof that boolean warning logic was wrong.

| Sensor | Intended off label | Intended on label |
|---|---|---|
| Weather warning | No active warning | Warning active |
| Critical warning | No critical warning | Critical warning active |
| Upcoming warning | No upcoming warning | Warning announced |

The original proposal was a separate translated UX change using existing
translation keys, which HA's frontend prioritises over device class.
Retain on/off, thresholds, IDs and automations; never turn unknown/unavailable
into “no warning”. Supply all four UI languages and visually check the device
page. Later implementation/acceptance records supersede the original pending state.

Sources: [HA binary sensors](https://www.home-assistant.io/integrations/binary_sensor/)
and [frontend state display](https://github.com/home-assistant/frontend/blob/dev/src/common/entity/compute_state_display.ts).
Gold translation/device-class rules remain separately assessed.

### Historical pollen findings and source comparison

The second screenshot also concerned installed V1.5. binary_sensor.py,
sensor.py and pollen_meteoswiss.py matched between 567a5e4 and 6d74354.
These were not observations of an already installed V1.7.

- **Hazel icon:** sensor.py used mdi:branch. The official
  [MaterialDesign catalogue](https://github.com/Templarian/MaterialDesign/tree/master/svg)
  had no branch.svg (404), while tree-outline.svg existed. A valid icon and
  actual display needed separate checking; this correction later landed.
- **Measured coverage:** the Zürich PZH hourly dataset and official metadata
  contained seven species: alder, birch, hazel, beech, ash, oak and grass.
  The original fork read six, making oak an evidenced extension. Its unused
  POLLEN_PARAM_MAP also used kaqueth0, while the documented oak column is
  kaquerh0. The oak addition later landed.
- **Ragweed and mugwort:** neither the read PZH hourly CSV nor parameter metadata
  contained these species. Existing Open-Meteo entities are modelled, not station
  observations. The 2024 climate report described separate manual ragweed
  observations and then-missing automatic identification of both species;
  this is not proof of a current real-time measurement service.
- **Later classification review:** diagnostic grouping and units supplied only
  as attributes were intentionally retained legacy contracts in that audit.
  Assess better presentation separately; do not hide unit/statistic/registry
  migration inside an icon fix. Later normal-sensor grouping and acceptance
  are recorded in current documents.

Evidence:
[compact source probe](evidence/pollen_source_2026-10-17.json),
[PZH CSV](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pzh/ogd-pollen_pzh_h_now.csv),
[parameters](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/ogd-pollen_meta_parameters.csv),
[inventory](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/ogd-pollen_meta_datainventory.csv),
[2024 climate report](https://www.meteoschweiz.admin.ch/dam/jcr%3Afd79265c-bd1c-4229-ae8d-ea69184d94b8/Klimareport-2024-de.pdf).
