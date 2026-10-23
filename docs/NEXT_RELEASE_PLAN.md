# Next development: location selection, Silver and Gold

**Plan version:** 1.22 · **Updated:** 23 October 2026
**Status:** Approved catalogue-based location implementation; dated catalogue audit complete, selection and compatibility acceptance remain open.
This document does not approve a new feature, installation or release.

## Next feature release: agreed scope on 23 October 2026

The operator explicitly includes both remaining architecture boundaries and
location/POI selection in the next release. Do not freeze the scope at the
forecast sensors alone. The sequence is modelled pollen/AQ/UV separation,
hourly/archive precipitation separation, then official-catalogue location search
and compatible selection/reconfiguration. Both architecture boundaries are now
integrated through PRs #54 and #55. This planning branch is reconciled with that
development baseline. POI implementation remains open before the candidate.
The first implementation package now provides the bounded official catalogue
client, immutable point/selection provenance and deterministic local search;
see the [catalogue contract](FORECAST_LOCATION_CATALOGUE.md). The second package
adds [offline saved-selection routing](SAVED_FORECAST_LOCATION.md), explicit
catalogue-height requests and height-aware cache identity. Translated HA flows
and focused compatibility acceptance remain open.
Only then freeze features, reconcile release documentation, package a reviewed
candidate and perform focused acceptance in the existing temporary HA.

Use the official MeteoSwiss forecast-point catalogue for postcode/town/POI
selection, with explicit result choice and coordinate/altitude provenance.
Keep ICON Seamless as the forecast source and App v3 warnings at a separately
confirmed warning postcode. Catalogue adoption is not permission to silently
switch to processed OGD forecasts or infer warning coverage for a mountain POI.
Existing entries retain their location meaning and identities until an explicit
change. The proposed version is 8.3.0, initially 8.3.0b1; nothing is published.
The broader Silver/Gold matrix remains a separate evidence claim, not a new
unbounded prerequisite for every release step. A next-day release estimate for
the smaller forecast-only scope no longer applies.

## Current position

The first beta, its deployed HA 2026.10.2 acceptance and the operator-confirmed
HACS source switch are complete. The temporary clean first installation and
isolated restore were confirmed on 21 October; Beta2 new setup with other
locations and observations was confirmed on 22 October.
[Release readiness](RELEASE_READINESS.md) is the current release checklist.
The historical candidate sequence below does not reopen completed acceptance.

The MeteoSwiss **App v3 warning API remains in use until further notice**.
Keep the confirmed warning postcode separate from forecast location, observation
station and measured-pollen station. Replacing warnings with MeteoGate/MeteoAlarm
is outside the present scope.

Prioritise the official OGD local-forecast point catalogue for location/POI
investigation. Catalogue selection and adopting processed local forecasts are
separate decisions; do not silently replace the existing ICON Seamless source.
The [bounded local-forecast plan](LOCAL_FORECAST_PLAN.md) defines the
catalogue, resource and compatibility evidence needed before implementation.
A working App-POI catalogue endpoint is not a prerequisite for that OGD route.
The 21 October download verifies **5816 unique type/ID pairs**, including
**631 POIs** and all four comparison places. Four duplicate station pairs are
fully identical; 86 bare IDs span multiple types. The plan records hashes,
coordinates, catalogue heights and a proposed result display. Catalogue-backed
selection uses the existing ICON forecast source. Processed OGD forecast
payload/resource evaluation is a separate future decision; actual selection UX and practical
compatibility acceptance remain open for this release. Height/request/cache
semantics are now defined and regression-tested in the second package.
Selecting a forecast POI does not establish point-specific warning coverage;
a separately confirmed warning postcode can remain supported.

## HACS default-list submission gate

Checked against the [current inclusion rules](https://www.hacs.xyz/docs/publish/include/)
on 23 October 2026. The maintained fork is not in the retrieved hacs/default
integration list. PR #35 integrated **country: CH** in hacs.json; it must be present
in the next released HACS manifest too. Do not rewrite the immutable 8.2.0 release.

After the agreed POI implementation and candidate acceptance, rerun HACS without
ignores and Hassfest, then publish the reviewed stable release before submitting
an owner-authored, editable, alphabetical addition to hacs/default. Recheck
branding, manifest, licence, active repository and Core-domain eligibility at
submission time. Explain the fork origin and shared domain transparently;
the published rules do not impose a blanket ban on forks. HACS review is still
required and can take months. Passing our checks or completing HA quality-tier
work is not acceptance into the default list.

## Baseline and quality claims

The original 17 October baseline was development `137e41d`, with runtime
matching `9c50b6b`. The [dated review](REVIEW_2026-10-17.md) and
[quality matrix](QUALITY_SCALE.md) retain evidence.

The [HA quality tiers](https://contributors.home-assistant.io/core/quality-scale/tiers/)
build on each other. They are an engineering benchmark for this custom/HACS
fork, not an official award. Passing HACS validation is separate. Only a
complete rule-by-rule assessment can justify a documented self-assessment of
applicable Silver requirements; exceptions need their specified justification.
This plan adds no quality-scale manifest value or badge.

## Historical first implementation step

Plan V1.0 landed through [PR #25](https://github.com/martins-netizen/ha-meteoswiss/pull/25)
on 17 October as `6d74354`, with successful PR/post-merge checks.
The [Q1 audit](QUALITY_AUDIT_2026-10-17.md) covers all twenty Bronze and ten
Silver rules. Its original gaps were field help/interval design, common module
layout, optional UV behaviour, external brand evidence and four under-covered
modules. The then-current 762 tests and 99.0517% aggregate did not close them.

The [bounded P0 probe](POI_FEASIBILITY.md) demonstrated public swisstopo search
and the existing ICON forecast for a summit, pass, hut and Kloten control.
It also found ambiguous names and differing default heights. The historical
App endpoint, full warning coverage and definitive altitude source were not
fully evidenced; P0 was not accepted as complete.

The V1.5 fixes and oak were approved for a later candidate without changing
the then-running V1.5 observation. Location/POI work remained separate.

## Historical approved test-candidate scope

On 17 October, four bounded changes were approved together: understandable
DE/EN/FR/IT warning states, a valid hazel icon, isolated UV outage/recovery state,
and measured oak from the verified seventh hourly OGD column.
Development/tests/regular merges could proceed during V1.5 observation.
Deployment followed its completion and the separate HA 2026.10.2 update.

Installer V1.8 replaced V1.7 in that original plan; its actual later installation
needed its own acceptance. It is historical, not today's recommended installer.
Flow/architecture/POI work was deferred.

Warning/icon changes landed in [PR #27](https://github.com/martins-netizen/ha-meteoswiss/pull/27),
UV state/logging in [PR #28](https://github.com/martins-netizen/ha-meteoswiss/pull/28).
Oak tests covered zero/missing values, legacy CSV and identity-preserving reload.
That intermediate candidate passed 779 tests on HA 2026.8.3/2026.10.1/2026.10.2,
99.0572% combined coverage, 100% lines/branches in three affected modules and
92 keys per language. Those figures are historical, not the latest 786-test
accepted runtime.

## Work order and decision gates

| Package | Scope | Completion criterion | Dependency |
|---|---|---|---|
| R0: release | Exact candidate, paired warning consumers, recovery, runtime and HACS evidence | Completed first-install/restore/Beta2 setup evidence and exact stable packaging reconciled in RELEASE_READINESS.md | Keep new POIs out of the accepted beta. |
| Q1: Bronze/Silver audit | Every applicable rule with code/test/practice evidence | Complete gap list without blanket “done” claims | Dated audit complete; update evidence as changes land. |
| S1: close Silver | Source behaviour, lifecycle, module coverage and understandable fields | All applicable Bronze/Silver requirements evidenced; justified exceptions | Q1; small scoped PRs separate from release-only changes. |
| P0: location feasibility | Official catalogue, identities, point forecasts and explicit warning boundary | Summit/pass/hut plus postcode control; supported data and limits established | Read-only investigation can run independently of R0. |
| P1: location/UX contract | Shared search, purpose text and compatible location data | Dialog design, data contract and migration cases reviewed | P0; plan Gold reconfiguration consistently. |
| P2: location feature | Confirmed scope with translations, tests and help; included in the next feature release | New/existing entries and affected data families accepted | Completed first release, bounded architecture/lifecycle work and P1; full Silver/Gold tier evidence remains separate. |
| G1: Gold | Reconfiguration, presentation, diagnostics, actionable repairs and docs | Full Gold matrix plus Bronze/Silver evidence | S1 and the shared P1/P2 location contract. |

Planning and bounded source checks can proceed now. Do not mix production
changes into a running acceptance window. Set firm feature versions/dates only
after prerequisites are evidenced. P0 may conclude “not currently viable”;
Silver and Gold can still proceed independently of POIs.

## Q1/S1: concrete Silver work

Use the [official rules](https://contributors.home-assistant.io/core/quality-scale/rules/)
as the checklist. These work packages do not claim completed compliance.

| Area | Starting evidence / next check |
|---|---|
| Bronze prerequisite | Reconcile all twenty rules. Unreleased field help/source translations and unused-placeholder cleanup are recorded in the dated follow-up; shared metadata and polling/options migration now have bounded evidence; warning coordinator placement and catalogue diagnostic availability are corrected; measured pollen, alternative current conditions and ICON forecasts now have separate clients/canonical coordinators with a shared timestamp parser; all seven real coordinators are canonical after the precipitation source/Recorder split; final UX and broader rule evidence remain open. Local HACS brand files are not Core-brands inclusion. |
| action-exceptions | Justified exemption while no integration actions exist; reassess if introduced. |
| config-entry-unloading | Retain Recorder/reload/unload tests; check remaining tasks, pollers and listeners by family. |
| docs-configuration-parameters, docs-installation-parameters | Explain purpose, source and effects; separate forecast, observation, warning and measured-pollen locations. |
| entity-unavailable | Check missing field, outage, stale data and recovery for observations, forecasts, warnings, pollen, AQ/UV, statistics and diagnostics independently. |
| integration-owner | Maintain current ownership, fork support and confidential reporting evidence. |
| log-when-unavailable | Once-per-transition logs for all active sources; protect coordinates, location IDs, payloads and raw error chains even at debug. |
| parallel-updates | Reconcile platform limits with actual concurrent requests; avoid additional overlapping refreshes. |
| reauthentication-flow | Document the exemption for credential-free public sources; do not invent login merely for a checklist. |
| test-coverage | More than 95% per module, preserving stricter existing branch/flow gates. |

In the original 762-test baseline, combined coverage was 99.0517%, but
camera.py, hydro.py, slf.py and version.py were at 0%; const.py was 98.51%.
The [22 October follow-up](QUALITY_PROGRESS_2026-10-22.md) removes unused
camera/hydro/SLF placeholders after checking references and active platforms.
The later metadata follow-up gives version.py a real diagnostic consumer,
adds shared entity metadata, and evidences above-95% coverage for every module.
Keep version/manifest/tool consistency and add no meaningless imports, tests or
exclusions solely for a percentage. Remaining Bronze prerequisites still need
rule-specific evidence. Shared-feed avalanche/flood warnings remain
supported independently of the removed standalone-product placeholders.

No wholesale architectural rewrite is planned. Retain source separation and
HA-owned sessions. The shared entity metadata follow-up preserves nine existing
device/identity contracts. The [coordinator placement review](COORDINATOR_LAYOUT_REVIEW.md)
now inventories all seven coordinators, moves warnings out of the platform, and
closes its seven-class placement inventory after the measured-pollen,
alternative-current, ICON-forecast, modelled-pollen/AQ/UV and precipitation
source/importer extractions and shared UTC parser move. The next package is
the agreed location/POI contract and implementation. Catalogue diagnostic
expiry/failure/recovery is implemented and tested separately from source freshness.
Use the
[expected module layout](https://contributors.home-assistant.io/core/quality-scale/common-modules/)
rather than equating central constants with full compliance.

## F1: forecast summary sensors (implemented candidate)

Hourly and daily forecasts are already supplied by the existing weather entity
through [weather.get_forecasts](https://www.home-assistant.io/integrations/weather/).
The calculated daily heating-degree-day sensor is also forecast-derived.
The implemented, unreleased candidate supports today and tomorrow: maximum/
minimum temperature, native full-day precipitation sum, and the highest hourly
precipitation probability with its matching interval(s). The
[forecast sensor guide](FORECAST_SENSORS.md) documents the eight numeric sensors,
attributes, missing-data behaviour and ordinary-card/automation use.

Temperature extrema and precipitation sums describe the complete target
calendar day, including elapsed hours today. They remain predictions, not
observed daily records; today's maximum/minimum may already have occurred.
Label that distinction in translated help rather than presenting them as
remaining-day extrema. Never reconstruct a full-day value from only the
remaining rolling hours when the native daily field is absent.

For today's probability, use the ongoing and upcoming hourly intervals; for
tomorrow use the complete target local day. Calculate the peak value and its
time windows from the same valid hourly rows. Do not attach a future time to
a provider daily maximum that may have occurred in an already elapsed hour.
[Provider hourly semantics](https://open-meteo.com/en/docs) specify the preceding
hour: a value timestamped 15:00 applies to 14:00–15:00, not 15:00–16:00.
Group adjacent tied peak intervals and retain distinct equally high windows.
A zero peak has no uniquely useful peak time; absent probabilities remain
unknown. Incomplete interval coverage must be explicit, not a full-day claim.

Keep the probability state numeric in percent and expose timezone-aware peak
start/end metadata for dashboards to render e.g. “80% between 14:00 and 15:00”.
Retain all tied windows without replacing numeric states with combined text.
Reuse the existing ICON coordinator and request; add no duplicate HTTP fetch
or full forecast-list state attribute. Use Europe/Zurich target dates, source
and retrieval time. Missing fields are unknown; an unavailable/stale source
is unavailable. Check local-midnight rollover, changing remaining-day windows,
23/25-hour DST days and end-of-day interval assignment, entity identity,
HA-owned listener cleanup and DE/EN/FR/IT names. These cases now have regression
evidence; the candidate still requires review and separate runtime acceptance.
Avoid treating changing forecast targets as measured historical totals.

## P0/P1: location purpose and compatibility

Use one name/postcode search followed by explicit selection. Display supported
category and verified altitude; users should not enter internal App IDs.

| Planned field | Help at the field |
|---|---|
| **Weather forecast location** | Where should the forecast apply? Search by postcode, town, summit, pass or mountain hut. |
| **Observation station** | This station supplies measured temperature, wind and rain. It may differ from the forecast location. |
| **Natural-hazard warning location** | Available weather/natural-hazard warnings are requested for this separately confirmed location. |

A valid shared location can be suggested, but differing warning assignment
must be visible and confirmed. Explain the independent measured-pollen station.
Field help belongs in translated HA dialogs, not only README text.

The signed Android 3.6.0 package's embedded catalogue 181 contained 623 POIs:
335 summits, 205 huts and 83 passes, with IDs/aliases, Swiss grid coordinates,
altitudes and four-language categories. This is a static starting snapshot,
not proof of current coverage. [swisstopo documents](https://www.swisstopo.admin.ch/en/faq-swisstopo-application-base-map)
selected MeteoSwiss mountain forecasts. One App catalogue request returned
403; no current full App-POI fetch was established. The public OGD investigation
does not require that endpoint to start working.

For each example, verify identifier, coordinate system, altitude, time and
forecast fields. Test empty/broken/stale catalogues and unsupported data.
Old bare region numbers do not prove warning coverage; do not silently select
a neighbouring postcode. A separately confirmed warning postcode is an explicit
supported boundary, not an all-clear for an unsupported point. Clarify data
rights; ship neither APKs nor decompiled third-party code.

The location contract separates type, provider identity, display name,
coordinates/CRS, altitude/provenance and supported data. POI IDs are not postcodes;
never append `00` indiscriminately. Forecast and warning clients use separate
adapters. Adopting processed App/OGD point forecasts is an explicit source choice.

Existing station entries currently forecast at HA's home coordinates while the
configured postcode selects warnings. Preserve that behaviour during migration.
Do not reinterpret old warning postcodes as forecast choices or change global
HA coordinates. A measurement-station change needs an explicit time-series
meaning check; never merge different station histories silently. Unchanged
sources retain IDs, statistics and personal settings. Decide duplicates,
recovery and contract changes before flow implementation.

## G1: Gold packages

Track all twenty-one Gold rules individually; “existing” still means “verify”.

| Rules | Intended evidence |
|---|---|
| devices, dynamic-devices, stale-devices | Source grouping and stable identities; review catalogue changes without unrequested deletion of historic entities. Assess dynamic-device applicability individually. |
| diagnostics | Useful redacted source/location state without private places/raw data; exercise HA's actual download route. |
| discovery, discovery-update-info | Justified applicability/exemptions for a public cloud service. Location search is not network-device discovery. |
| entity-category, entity-device-class, entity-disabled-by-default | Correct classification and sensible defaults while preserving existing user choices. |
| entity-translations, exception-translations, icon-translations | Review hardcoded names/errors/icons, including station/cache diagnostics and warnings. Consistent DE/EN/FR/IT field help and future icons.json; language files alone do not prove Gold. |
| reconfiguration-flow | Prefilled validated editing of existing entries, source identity, duplicates, statistics meaning and reload. Options alone do not prove this rule; share P1's contract. |
| repair-issues | Translated actionable configuration repairs, removed after resolution. Temporary provider outages use availability/logging. |
| docs-data-update, docs-examples, docs-known-limitations, docs-supported-devices, docs-supported-functions, docs-troubleshooting, docs-use-cases | Update/source semantics, supported data/locations, limits, examples, troubleshooting and use cases. New users exercise setup/migration; experienced users inspect attributes/contracts. |

## Security and maintenance

The first unreleased security follow-up implements shared HTTPS/destination
validation, redirect refusal and streaming wire/decompressed size limits for all
active sources. See [scope, real archive sizes and required focused HA acceptance](HTTP_SOURCE_HARDENING.md).
Any future POI catalogue must adopt an equivalently bounded transport. Keep timeouts, cancellation and
conservative caching; redact search terms from logs/diagnostics.
The separate CI follow-up enables CodeQL analysis for external-fork PRs on the
unprivileged pull_request event, with job-scoped upload permission and no
repository secrets supplied to public forks. See the [fork review boundary and
first-external-run evidence still required](CODEQL_FORK_REVIEW.md). Keep these
changes separate from runtime release packaging and the later Silver/Gold work.

## Suggested PR order

| Order | Scope | Review criterion |
|---|---|---|
| 1 | Rule matrix and Bronze gaps | Status, evidence, gap or justified exemption for every rule. |
| 2 | Scoped layout/placeholder/coverage work | References checked, no feature loss, >95% per module and stricter existing gates retained. |
| 3 | Remaining Silver outage/recovery/lifecycle paths | Reproduced regression before fix; appropriate passing tests afterwards. |
| 4 | Confirmed location contract and adapter | P0 evidence, typed identity, privacy and failures. |
| 5 | Shared search, purpose text and reconfiguration | Native HA flows, compatibility and DE/EN/FR/IT. |
| 6 | Remaining Gold display/diagnostics/repairs/docs | Complete matrix and practical user walkthrough. |

Split work further when useful. Runtime PRs need meaningful regressions and
supported-HA checks; check the then-current HA patch before release. Use regular
PRs into protected development, retaining tests, Analyze Python and HACS
validation. Documentation-only merges do not need HA reinstallation.

No second permanent operator HA environment is assumed. Prepare temporary
isolated first-install/recovery checks; automated HA/Recorder/flow tests already
supply scoped evidence. The operator's source switch, clean first installation, isolated restore and
focused Beta2 setup/data run are complete within their documented scope. Do not actuate production devices for testing.
