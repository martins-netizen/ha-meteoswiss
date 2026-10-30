# Quality evidence and remaining work

**Runtime assessment:** 24 October 2026. **Documentation updated:** 30 October 2026.
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

**Reading the result:** all applicable technical Bronze rules and applicable
Silver rules have recorded evidence below. Bundled branding follows the custom
integration/HACS route; the separate Core branding requirement is not assessed.
Gold has
explicit open/partial rules and proposed exemptions requiring review. The
[README summary](../README.md#quality-goals-bronze-silver-and-gold) is intentionally
short; these tables retain the qualifications and release scope.

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
| `runtime-data` | Evidence | MeteoSwissRuntimeData and typed ConfigEntry own coordinators/session/target; domain globals only coordinate shared diagnostics. |
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
| `devices` | Partial | Stable weather, warning, measured pollen, AQ and diagnostic grouping is tested; audit completeness of legacy manufacturer/model metadata separately. |
| `diagnostics` | Evidence | Safe unloaded-entry exports, status/timestamps, aggregate cache counts and whole saved-location redaction; no raw payload or network load. |
| `discovery` | Exemption candidate | This is a manually selected public cloud service, not a discoverable local device. Record the rule-specific applicability reason in this engineering assessment. |
| `discovery-update-info` | Exemption candidate | No discovered network address; assess with discovery above. |
| `docs-data-update` | Evidence | API_SOURCES.md distinguishes polling, cache, publication and measurement intervals; documents time/freshness and failure limits. |
| `docs-examples` | Evidence | COORDINATOR_EXAMPLES.md, standard forecast usage and escaped warning-card example. Examples do not actuate devices. |
| `docs-known-limitations` | Evidence | Provider availability, fixed-offset daily fields, interval completeness, separate warning postcode, name aliases and unimplemented feeds are explicit. |
| `docs-supported-devices` | Evidence | Public station metadata, the verified pollen list and source/geography limits replace an invented fixed hardware list. |
| `docs-supported-functions` | Evidence | SENSORS.md, FORECAST_SENSORS.md and source guide describe active families and retired entities. |
| `docs-troubleshooting` | Evidence | USAGE.md covers missing data, outages, metadata refresh and retained-entry recovery. |
| `docs-use-cases` | Evidence | README/getting-started plus ordinary forecast sensors/cards/automations and independent source examples. |
| `dynamic-devices` | Exemption candidate | The selected sources expose a fixed entity set; no newly discovered physical devices are enumerated. |
| `entity-category` | Evidence | Diagnostic helpers stay diagnostic; measured/modelled pollen and AQ stay ordinary sensors, with registry tests. |
| `entity-device-class` | Partial | Numeric metadata and HA conversion tests exist; review legacy Foehn/code and derived HGT metadata before a complete Gold assertion. |
| `entity-disabled-by-default` | Open | Legacy diagnostic defaults are retained. Decide new-install defaults separately without changing existing user registry choices. |
| `entity-translations` | Partial | Four complete 200-key UI catalogues in stable 8.3.2 and ordinary entity translations exist; strings.json matches English. Legacy diagnostic/device/attribute compatibility names remain; authoritative provider place-name aliases are separate future work. |
| `exception-translations` | Partial | Setup/selection errors are translated; remaining fixed HA update-error messages have not all moved to translated exceptions. |
| `icon-translations` | Implemented candidate, not released | Unreleased ICON_TRANSLATIONS.md maps all 24 previous custom icons to icons.json, retaining device-class defaults and user registry overrides. Native HA tests cover translation-key linkage and custom-icon persistence after reload; Hassfest validates the schema. Stable 8.3.2 keeps its previous code icons until a later tested release. |
| `reconfiguration-flow` | Automated and reported focused evidence in accepted 8.3.2b1 | Native Reconfigure and Configure share the complete weather station/base-coordinate, measured-pollen, forecast and warning-postcode transaction. Tests cover both providers/routes, explicit confirmation, cancellation at each stage, source retry with retained choices, duplicate/concurrent-edit rejection, translations and retained entity IDs with a single loaded-entry reload. The original setup confirmation remains separate. This extends stable 8.3.1's forecast-only shortcut. The operator reported all five configured-source steps positive on Core 2026.10.4; no separate registry audit or manual test of every provider is inferred. |
| `repair-issues` | Evidence in accepted 8.3.1b1 | Invalid offline saved forecast selections raise a translated entry-specific notice linking to the existing settings. Confirmed correction/reset clears it; cancellation/failed validation retains it. Reloads preserve ignored state; disablement/removal cleans up that entry. Provider outages create no configuration notice. Native entry/settings and four-language tests cover these boundaries; the operator confirmed the requested version/visual check, without a separately reported deliberate-corruption test. Stable 8.3.1 retains that runtime. |
| `stale-devices` | Open | Review removal of obsolete grouping after measured-pollen station changes without deleting wanted registry/history data. |

The Gold engineering checklist therefore remains incomplete. Strict typing
and the async/source-library requirements associated with Platinum need their
own evidence too. These improvement goals are separate from packaging an
agreed feature release.

## Reproduce and distinguish history

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
