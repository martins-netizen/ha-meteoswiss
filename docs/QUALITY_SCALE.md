# Quality evidence and remaining work

**Runtime assessment:** 24 October 2026. **Documentation updated:** 10 November 2026.
**Scope:** the 8.3 runtime accepted as
published b4 at **a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5**. Stable packaging
changes only two component version files. The operator confirmed b3 calendar-day
values/shared station changes and positive b4 operation; screenshots show distinct
station/forecast devices. [Readiness](RELEASE_READINESS.md) retains evidence limits.

We use the [Home Assistant rules](https://contributors.home-assistant.io/core/quality-scale/rules/)
to guide engineering work and record the evidence for each applicable rule.
Home Assistant's [custom-integration guidance](https://contributors.home-assistant.io/marketplace/guides/integrations/#keep-up-with-home-assistant)
states that custom integrations have no official tiers. Bronze, Silver and
Gold therefore organise this project's self-assessment and remaining work;
they are not pending official awards. `quality_scale` is deliberately absent
from the manifest. Assess the underlying rules too, rather than relying on one
coverage percentage or a working reconfiguration flow.

[HACS catalogue admission](HACS_ACCEPTANCE.md#hacs-catalogue-admission) was completed
on 24 October 2026. That distribution/review milestone is separate from the
engineering assessment below and from an operator's actual HA update.

**Evidence** below means code, automated tests or current documentation exists
within the stated scope. **Open/partial** identifies a remaining requirement.
**Exempt** gives its applicability reason. Operator acceptance is recorded
separately from automated evidence. On 25 October the operator confirmed the
successful production update from 8.2 to stable 8.3; see [HACS evidence](HACS_ACCEPTANCE.md).

**Accepted 8.3.1b1 follow-up:** the repair-issues row additionally records the
[saved-location repair notice](REPAIRS.md), native lifecycle tests and the
operator-confirmed version/visual check on 26 October. The feature is not in
8.3.0. Stable [8.3.1](RELEASE_8.3.1.md) was published on 26 October, retaining
the accepted b1 runtime. Actual installation is separate evidence; no full
Gold completion is claimed.

**Accepted published 8.3.2b1 shared-settings follow-up:** the reconfiguration and configuration
documentation rows below additionally describe the complete native Reconfigure
route in this development tree. It shares Configure's transaction and preserves
the original setup confirmation. Automated manager/lifecycle tests cover both
routes and providers. The operator reported all five
[focused HA steps](ACCEPTANCE_8.3.2b1.md) positive on **Core 2026.10.4**.
This closes the requested existing-entry acceptance, without an independent
registry/statistic audit or separate UTM inspection. Stable
[8.3.2](RELEASE_8.3.2.md) was published on 28 October, retaining that runtime.
On 30 October the operator confirmed the actual stable HACS download, restart
and working operation. [Release evidence](RELEASE_EVIDENCE_8.3.2.md) separates
that short update report from the earlier five-step Core 2026.10.4 acceptance.
Earlier 8.3/8.3.1 evidence keeps its own scope; full Gold is still incomplete.

**Accepted published 8.3.3b1 icon/error follow-up:** release **429321251**
was published on **30 October 2026 at 17:42:37 UTC** from
**d9fbc3fd49220b0ecc019d2babe0c173c46986f5**. The operator reported icons/personal
choices and normal operation OK on **HA Core 2026.10.4 / HA OS 18.4**;
see the [bounded acceptance](ACCEPTANCE_8.3.3b1.md). All 19 exception keys are
loaded by native tests in DE/EN/FR/IT; no manual exercise of every failure is
claimed. [Stable 8.3.3](RELEASE_8.3.3.md), release **429354633**, was published
on **30 October at 18:21:55 UTC** with those 39 non-version component files
unchanged. The operator subsequently confirmed **8.3.3 installed and normal
operation OK**, closing the [short stable update](ACCEPTANCE_8.3.3.md).
The [release evidence](RELEASE_EVIDENCE_8.3.3.md) separates these reports from
automated coverage; no new Core/Python security claim is inferred. Full Gold
remains incomplete.

**Reading the result:** all applicable technical Bronze rules and applicable
Silver rules have recorded evidence below. Bundled branding follows the custom
integration/HACS route; the separate Core branding requirement is not assessed.
Gold has
explicit open/partial rules and reasoned discovery exemptions. The
[README summary](../README.md#quality-goals-bronze-silver-and-gold) is intentionally
short; these tables retain the qualifications and release scope.

**Published 8.3.4b1:** release **437718127** was published on **7 November 2026
at 17:12:54 UTC** from regularly merged packaging PR #90 at
**1e5c5d1a7fc1c18d520e99189ae4dd5894621706**. It retains #88/#89 runtime
apart from two version fields. Diagnostic defaults/service metadata and
current-provider provenance are released in this beta. The operator confirmed
normal operation on **HA Core 2026.11.0 / HA OS 18.4**, closing the agreed
short check. The [bounded evidence](RELEASE_EVIDENCE_8.3.4b1.md) does not
claim an independent registry audit or separate manual alternative-source
inspection. Gold rows remain bounded; stable 8.3.4 subsequently retained this
accepted runtime unchanged apart from its two version fields.

**Published stable 8.3.4:** [release 437853341](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4)
is latest stable, independently verified after publication on **7 November 2026
at 21:24:27 UTC** from **f4479897023fa35d7c2fcb4c4859c4de8861fdda**.
It retains that accepted beta runtime with two version changes and the same
39 other component files. It offers official-package HA 2026.11 compatibility
evidence, cleaner first setup and clearer source metadata. See
[publication evidence](RELEASE_EVIDENCE_8.3.4.md); the short actual stable update
is distinct from publication. PR #92 HGT behaviour and remaining Gold rules stay
outside this package.

## Bronze: twenty rules

| Rule | Assessment | Repository evidence or remaining boundary |
|---|---|---|
| `action-setup` | Exempt | No custom integration actions. `weather.get_forecasts` belongs to HA's weather platform. |
| `appropriate-polling` | Evidence | Developer-selected 600-second observation default/minimum; source-specific forecast, warning, pollen and archive schedules. New setup/options no longer expose an interval. Legacy intervals survive without a new UI knob. See API_SOURCES.md and options migration tests. |
| `brands` | Custom-integration asset evidence; Core route not assessed | Valid bundled HACS PNGs are present and catalogue admission is complete. The separate home-assistant/brands requirement concerns the Core rule; it is not an outstanding route to an official tier for this custom integration. |
| `common-modules` | Evidence | All eight real coordinator classes are in coordinator.py; shared bases are in entity.py and runtime ownership is typed. Source separation is substantive for ICON/current/AQ/pollen/precipitation, not alias-only placement. The legacy station adapter remains in its coordinator, with executor CSV parsing. |
| `config-flow` | Evidence | Native setup/options and Reconfigure. Published 8.3.2b1 offers the complete settings transaction through both existing-entry routes. Four-language fields/help; source selector; explicit pollen choice and point search/selection/confirmation. Current source and warning/forecast/pollen purposes stay distinct. |
| `config-flow-test-coverage` | Evidence | Full line/branch gate. Real flow-manager tests cover both providers, errors, retries, duplicate guards, translations, cancel/keep/reset and loaded-entry reconfiguration. |
| `dependency-transparency` | Exempt | Manifest requirements are empty; there is no separately distributed extra runtime library. HA-provided dependencies and public data/service dependencies are documented. |
| `docs-actions` | Exempt | No custom actions. USAGE.md explains the standard HA forecast service. |
| `docs-conditions` | Exempt | No integration/device-specific conditions; ordinary state/numeric conditions remain available. |
| `docs-high-level-description` | Evidence | README and GETTING_STARTED.md explain benefits, source provenance, independent project status and limits. |
| `docs-installation-instructions` | Evidence | Separate new-install and migration/update paths; explicit released target, HACS refresh, backup, restart and retained HA entry. Practical 8.2.0 acceptance is recorded, not reopened. |
| `docs-removal-instructions` | Evidence | USAGE.md covers entry and HACS removal, dependent consumers and Recorder retention. |
| `docs-triggers` | Exempt | No integration/device-specific triggers; normal HA triggers are documented. |
| `entity-event-setup` | Evidence | Coordinator listeners and forecast clocks attach on addition and unsubscribe on removal. Loaded HA/Recorder and WebSocket tests cover cleanup, optional-task cancellation and refreshes. |
| `entity-unique-id` | Evidence | Stable entry/family IDs and intentional shared diagnostic IDs; registry/Recorder reload tests. Retired current-hour and seasonal HGT entities are documented exceptions. |
| `has-entity-name` | Evidence | Common entity bases provide contextual naming to all active classes; metadata tests cover grouping and retained identities. |
| `runtime-data` | Evidence | MeteoSwissRuntimeData and typed ConfigEntry own coordinators/session/target; one typed domain lifecycle object coordinates shared diagnostics without peer reloads; see SHARED_DIAGNOSTIC_LIFECYCLE.md. |
| `test-before-configure` | Evidence | Actual current-source validation before entry creation; selected catalogue point checked using IconForecastClient before commit, with bounded failure/retry/cancellation. |
| `test-before-setup` | Evidence | Initial current-source refresh before platforms. Optional sources cannot block valid observations; required failure remains retryable with the HA-owned session intact. |
| `unique-config-entry` | Evidence | Provider/station/base-coordinate/warning-postcode guards include old entries without IDs and concurrent flows. A forecast-only change is deliberately not a new entry identity. |

## Silver: ten rules

| Rule | Assessment | Repository evidence or remaining boundary |
|---|---|---|
| `action-exceptions` | Exempt | No custom actions; reassess if added. |
| `config-entry-unloading` | Evidence | Native platform unload/reload; entry-managed tasks/listeners, Recorder import listeners, stable IDs and borrowed session ownership tested for both providers. |
| `docs-configuration-parameters` | Evidence | One Configure dialog stages measured pollen, weather station/base coordinates, forecast point and warning postcode. Published 8.3.2b1 exposes the same transaction through Reconfigure, with version-qualified guides. Source checks, atomic cancel/confirm, hidden legacy intervals and station-specific archives are documented. |
| `docs-installation-parameters` | Evidence | GETTING_STARTED.md and FORECAST_LOCATION_SETUP.md cover 8.3 setup and location fields, point purposes, height, ambiguity and confirmation. |
| `entity-unavailable` | Evidence | Registered HA states cover observation, forecast, warnings, pollen/AQ, optional UV and catalogue failure/recovery. Valid zero, missing field and failed source remain distinct. The review adds UV timestamp rejection and honest incomplete/DST daily values. |
| `integration-owner` | Evidence | @martins-netizen is manifest codeowner; active repository, Issues, issue forms and SECURITY.md provide support/reporting routes. Private-reporting activation was operator-confirmed; no independent settings audit is inferred. |
| `log-when-unavailable` | Evidence | Coordinator transition logs avoid repeated outages, raw coordinate/postcode URLs and payloads; separate cached UV status has its own outage/recovery transition. Tests inspect formatted error chains too. |
| `parallel-updates` | Evidence | sensor.py uses 1 for diagnostic polling; coordinator-driven weather/binary/pollen platforms use 0. These values do not assert zero network requests. |
| `reauthentication-flow` | Exempt | No provider accounts or credentials. |
| `test-coverage` | Evidence | Stable 8.3.2 actual-merge CI passes **1,983 tests plus 83 subtests** on each HA 2026.8.3/2026.10.1. Coverage **3,516/3,517 statements, 974/974 branches**, combined **99.977733%**; full flow coverage and all stricter gates/four exclusions remain. Local HA 2026.10.3 regression evidence is separate. See RELEASE_EVIDENCE_8.3.2.md and RELEASE_READINESS.md for version/security boundaries. These are pytest results, not a SonarCloud coverage import. |

The original audit's interval, field-help, common-layout, UV/catalogue and
per-module coverage findings are implemented in the reviewed tree. Their old
wording must not be read as new work to repeat. The rule matrix preserves the
scope of each technical result, the custom branding route and the remaining
engineering work.

## Gold: bounded assessment of all twenty-one rules

| Rule | Assessment | Current evidence or next decision |
|---|---|---|
| `devices` | Bounded automated evidence delivered in stable 8.3.4; first shipped in 8.3.4b1 | All seven virtual groups declare `DeviceEntryType.SERVICE`. Current weather/sensors now label and attribute Open-Meteo separately from SwissMetNet; other groups retain their provenance. Native setup/reload tests preserve device IDs, personal names and entity registry choices. See PROVIDER_METADATA.md and DIAGNOSTIC_DEFAULTS.md; released in beta 8.3.4b1, not included in stable 8.3.3 and not a complete historical metadata audit. |
| `diagnostics` | Evidence | Safe unloaded-entry exports, status/timestamps, aggregate cache counts and whole saved-location redaction; no raw payload or network load. |
| `discovery` | Exempt; applicability reviewed | Public weather selection is a manually configured service without a discoverable local appliance, bus or account-owned device inventory. GOLD_APPLICABILITY.md links the official exception, source/config-flow evidence and reassessment triggers. Catalogue search is data selection, not network discovery. |
| `discovery-update-info` | Exempt; applicability reviewed | No discovered device host/IP is stored to update; provider DNS and explicit station/forecast settings are separate concerns. GOLD_APPLICABILITY.md records the official exception and its service-specific reason. |
| `docs-data-update` | Evidence | API_SOURCES.md distinguishes polling, cache, publication and measurement intervals; documents time/freshness and failure limits. |
| `docs-examples` | Evidence | COORDINATOR_EXAMPLES.md, standard forecast usage and escaped warning-card example. Examples do not actuate devices. |
| `docs-known-limitations` | Evidence | Provider availability, fixed-offset daily fields, interval completeness, separate warning postcode, name aliases and unimplemented feeds are explicit. |
| `docs-supported-devices` | Evidence | Public station metadata, the verified pollen list and source/geography limits replace an invented fixed hardware list. |
| `docs-supported-functions` | Evidence | SENSORS.md, FORECAST_SENSORS.md and source guide describe active families and retired entities. |
| `docs-troubleshooting` | Evidence | USAGE.md covers missing data, outages, metadata refresh and retained-entry recovery. |
| `docs-use-cases` | Evidence | README/getting-started plus ordinary forecast sensors/cards/automations and independent source examples. |
| `dynamic-devices` | Partial; bounded fixed-group evidence | The seven virtual service groups, including two shared diagnostic groups, are defined by the integration rather than enumerated from a hub/account inventory. Native setup/reload/station-change tests retain their IDs and bindings. The official single-fixed-device exception does not literally cover this layout; no blanket exemption or dynamic-addition test is claimed. See GOLD_APPLICABILITY.md. |
| `entity-category` | Evidence | Diagnostic helpers stay diagnostic; measured/modelled pollen and AQ stay ordinary sensors, with registry tests. |
| `entity-device-class` | Bounded unreleased Foehn/HGT/wind evidence; release/operator acceptance open | SENSOR_METADATA.md records why the numeric Foehn code and forecast HGT `°C·d` have no fitting standard class. HGT no longer enters measurement statistics; old rows/history remain. WIND_STATISTICS_MIGRATION.md implements HA wind/circular classes only after archiving and verifying older arithmetic metadata/rows. Native Recorder tests cover both mean algorithms, retained identities, conflicts, lifecycle and preserving rollback. Published stable 8.3.4 retains the earlier metadata. This bounded source evidence does not complete Gold. |
| `entity-disabled-by-default` | Automated evidence delivered in stable 8.3.4; first shipped in 8.3.4b1 | Only newly registered station-catalogue and cache-statistics helpers start disabled. Native HA tests cover both providers, no disabled-helper polling, retained enabled/user-disabled/integration-disabled choices, names/icons/IDs, reload and manual enablement. Ordinary environmental entities remain enabled. See DIAGNOSTIC_DEFAULTS.md; released in beta 8.3.4b1, not included in stable 8.3.3. The short operation report does not independently exercise fresh registration. |
| `entity-translations` | Automated name coverage for every exposed entity; release/operator acceptance open | ENTITY_NAME_TRANSLATIONS.md inventories all 45 registered entities per provider: 40 sensors, three warning binary sensors and two weather entities inheriting their device names. Native DE/EN/FR/IT tests cover 41 sensor keys across providers and three warning keys, all activation choices, personal names and retained registry bindings through full language round trips. Four inactive legacy keys remain explicitly identified. DIAGNOSTIC_TRANSLATIONS.md and SERVICE_GROUP_TRANSLATIONS.md retain their privacy/Recorder evidence. Technical compatibility strings and authoritative place aliases are separate scopes, not missing entity-name keys. The unreleased naming changes still need release/operator UI acceptance; overall Gold remains incomplete. |
| `exception-translations` | Automated evidence in accepted published 8.3.3b1 | EXCEPTION_TRANSLATIONS.md records all 21 UpdateFailed sites using 19 keys in DE/EN/FR/IT. Native HA tests load every message; safe causes, retry/availability and recovery remain. The operator reported normal operation, without manually triggering all failures. Stable 8.3.3 now delivers this runtime and its actual installation/operation is operator-confirmed; no manual exercise of all errors is claimed. |
| `icon-translations` | Automated and reported focused evidence in accepted published 8.3.3b1 | ICON_TRANSLATIONS.md maps all 24 previous custom icons to icons.json, retaining device-class defaults and personal registry overrides. Native HA tests cover key linkage and override persistence after reload; Hassfest validates the schema. The operator reported icons/personal choices OK on Core 2026.10.4 / HA OS 18.4 within the acceptance scope. Stable 8.3.3 now delivers the same runtime and its actual installation/operation is operator-confirmed. |
| `reconfiguration-flow` | Automated and reported focused evidence in accepted 8.3.2b1 | Native Reconfigure and Configure share the complete weather station/base-coordinate, measured-pollen, forecast and warning-postcode transaction. Tests cover both providers/routes, explicit confirmation, cancellation at each stage, source retry with retained choices, duplicate/concurrent-edit rejection, translations and retained entity IDs with a single loaded-entry reload. The original setup confirmation remains separate. This extends stable 8.3.1's forecast-only shortcut. The operator reported all five configured-source steps positive on Core 2026.10.4; no separate registry audit or manual test of every provider is inferred. |
| `repair-issues` | Evidence in accepted 8.3.1b1 | Invalid offline saved forecast selections raise a translated entry-specific notice linking to the existing settings. Confirmed correction/reset clears it; cancellation/failed validation retains it. Reloads preserve ignored state; disablement/removal cleans up that entry. Provider outages create no configuration notice. Native entry/settings and four-language tests cover these boundaries; the operator confirmed the requested version/visual check, without a separately reported deliberate-corruption test. Stable 8.3.1 retains that runtime. |
| `stale-devices` | Partial; bounded station-change, shared-lifecycle and unreleased manual-removal evidence | Native station round trips retain all seven groups and bindings; shared-diagnostic handoff preserves IDs or reports a repair. DEVICE_REMOVAL.md adds user-confirmed native removal only for an unambiguous empty service shell whose known identifier refers to a non-existing entry. Current/disabled/shared/bound/linked/ambiguous records are protected; native UI and Recorder tests retain active choices/history. Source-history review establishes identifier forms, not production orphans. No automatic cleanup, independent historical inventory, blanket single-device exception or completed Gold is claimed; see GOLD_APPLICABILITY.md and PROVIDER_METADATA.md. |

The Gold engineering checklist therefore remains incomplete. Strict typing
and the async/source-library requirements associated with Platinum need their
own evidence too. These improvement goals are separate from packaging an
agreed feature release.

## Reproduce and distinguish history

The [complete test-lock advisory check](DEPENDENCY_ADVISORIES.md) supplements
security floors and the existing regression/coverage gates. Its network queries
run in an isolated CI job and daily/manual workflow; both HA fixtures retain
offline uv. Active advisories and unknown results block the required aggregate.
This supply-chain control does not complete any still-open Gold acceptance.
PR #107's initial SonarCloud security gate failed. Explicit TLS verification
and removal of arbitrary report paths address its two findings; all ten checks
must pass on the corrected head before a merge can be approved.

Use the [local compatibility checks](../DEVELOPMENT.md#local-compatibility-checks)
in a separate isolated environment for each supported HA fixture. This shared
recipe checks Python and pip before downloads, constrains and verifies certifi,
requires offline uv, and retains the full translation and line/branch coverage
checks. An existing historical test environment is not evidence that the current
security baseline passes.

The [overall review](RELEASE_REVIEW_2026-10-24.md) records the additional component-only
installation simulation, link checks, regressions and exact scope. Required PR
and post-merge checks must pass on the exact commit; local results do not prove
an unrun hosted check or a manual HACS installation.

The [17 October audit](QUALITY_AUDIT_2026-10-17.md) and
[dated implementation record](QUALITY_PROGRESS_2026-10-22.md) retain the previous
baselines. The original 68-test/54.78% snapshot and later 762-/786-/967-test
numbers are history, not the current suite or a demand to repeat completed
acceptance. See RELEASE_READINESS.md for completed publication/catalogue results
and the separately recorded operator-update scope.
