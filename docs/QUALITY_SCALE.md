# Quality evidence through Gold

**Current review, 18 November 2026:** published and bounded-accepted b7 at signed
`9ea96fc5a5306342eef0aa73ae50cc95bb844fb4` passed all ten head and nine
actual-merge checks on HA 2026.11.0/2026.11.2. Its index reported 26 automated
verifications, 16 documented review judgments and nine reasoned exemptions.
The overall documentation review then found a missed structural judgment:
`MeteoSwissHgtCoordinator` was a ninth real coordinator defined outside
`coordinator.py`. The official common-modules rule provides no exemption for
that placement. A passing evidence checker did not establish that human review.

The [canonical coordinator correction](COORDINATOR_CANONICAL_COMPLETION.md)
prepares one actual class definition in `coordinator.py` and an explicit
compatibility re-export at the old path. The corrective source also adds the
missing calculated-HGT Swiss-midnight state callback; native tests must cover
its registered state and lifecycle. Its own source review, native checks
and trusted head/actual-merge gates must succeed before the assessment can be
closed and stable 8.3.5 packaged. The [dated record](RELEASE_EVIDENCE_8.3.5.md)
retains the real b7 results, publication and bounded sight report. Those
operator scopes remain closed; no repeated migration or observation window is
needed; the new HGT clock receives its own native regression evidence.

The checklist covers **all 51 rules through Gold**: 20 Bronze, 10 Silver and
21 Gold. The [official tiers](https://contributors.home-assistant.io/core/quality-scale/tiers/)
require every lower-tier rule too. This fork remains a **custom integration**;
there is no official Gold award or `quality_scale: gold` manifest claim.
Platinum's strict typing and dependency architecture are separate goals.

The [machine-readable evidence index](quality_rules.json) is authoritative for
exact source/document references, supporting pytest selectors, applicability
and bounded rationale. The [CI contract](GOLD_EVIDENCE_CONTRACT.md) consumes
fresh JUnit and coverage from the existing single complete native run. It
refuses pending rules and missing, skipped or failed required evidence. The
unchanged strict per-module coverage gate still applies.

## How to read the assessment

| Evidence | What is established | What is not inferred |
|---|---|---|
| Native contract + review | The mapped behavior passes in the current run; its applicability and limits are recorded. | An official tier, every deployment or every unreported parameter case. |
| Reviewed source or guide | A structural or documentation judgment with concrete references. Listed supporting tests must pass too. | That automation itself performed a human review. |
| Reasoned exemption | The requirement does not apply for the recorded service-specific reason. | A missing capability implemented by changing a label. |
| Custom branding route | Bundled assets and Marketplace/HACS catalogue admission. | A separate Core branding submission. |

Approved #129 supplied native contracts and reproduced diagnostics/time-boundary
fixes. The later canonical-placement finding requires the explicit correction
and source gates above before claiming closure of every rule. Historical production
orphan inventories, manual exercise of every error and four separate browser
language rounds are not invented additional Gold prerequisites. Their absence
is not hidden: existing operator reports retain their narrower observed scope.

## Bronze: 20 rules

| Rule | Evidence | Contract and reference |
|---|---|---|
| `action-setup` | Reasoned exemption | The integration registers no custom actions. [Evidence](USAGE.md). |
| `appropriate-polling` | Native contract + review | Source-specific intervals and developer-owned observation polling are retained without a new setup/options interval control. [Evidence](API_SOURCES.md). |
| `brands` | Custom branding route | Bundled HACS assets and catalogue admission follow the custom integration route; the separate Core brands submission is not claimed. [Evidence](HACS_ACCEPTANCE.md). |
| `common-modules` | Corrective source review pending | The b7 review missed the ninth HGT coordinator outside the canonical module. The prepared correction places all nine definitions in `coordinator.py`, with only a compatibility re-export at the old path. No exemption is claimed. [Inventory](COORDINATOR_LAYOUT_REVIEW.md) and [source gates](COORDINATOR_CANONICAL_COMPLETION.md). |
| `config-flow` | Native contract + review | Native setup and existing-entry dialogs validate both providers and preserve entry identity on confirmation. [Evidence](GETTING_STARTED.md). |
| `config-flow-test-coverage` | Native contract + review | The existing full line/branch config-flow gate is retained alongside real flow-manager success, errors, cancellation and duplicate contracts. [Evidence](GOLD_EVIDENCE_CONTRACT.md). |
| `dependency-transparency` | Reasoned exemption | The manifest has no additional distributed runtime requirements. [Evidence](API_SOURCES.md). |
| `docs-actions` | Reasoned exemption | No integration-specific actions exist. [Evidence](USAGE.md). |
| `docs-conditions` | Reasoned exemption | No integration or device-specific condition exists. [Evidence](USAGE.md). |
| `docs-high-level-description` | Reviewed source or guide | The introduction describes purpose, independent project ownership, provider provenance and geographical/service limitations. [Evidence](../README.md). |
| `docs-installation-instructions` | Reviewed source or guide | Installation, retained-entry updates, backups and restart requirements are documented separately from runtime acceptance. [Evidence](GETTING_STARTED.md). |
| `docs-removal-instructions` | Reviewed source or guide | Removal instructions distinguish entry removal, package removal, dependent consumers and retained Recorder history. [Evidence](USAGE.md). |
| `docs-triggers` | Reasoned exemption | No integration or device-specific trigger exists. [Evidence](USAGE.md). |
| `entity-event-setup` | Native contract + review | Entity-owned coordinator subscriptions and time callbacks must attach on addition and be canceled on removal, including disabled polling. [Evidence](GOLD_EVIDENCE_CONTRACT.md). |
| `entity-unique-id` | Native contract + review | All active family identities and shared diagnostic identities survive native language/settings reloads and ownership changes. [Evidence](ENTITY_NAME_TRANSLATIONS.md). |
| `has-entity-name` | Native contract + review | Native registry and runtime names are resolved in each supported language and retain contextual device naming. [Evidence](ENTITY_NAME_TRANSLATIONS.md). |
| `runtime-data` | Native contract + review | Typed entry data owns coordinators and the borrowed session; shared helper handoff does not reload the peer entry. [Evidence](SHARED_DIAGNOSTIC_LIFECYCLE.md). |
| `test-before-configure` | Native contract + review | The actual current-source and selected forecast point are validated before committing a new configuration. [Evidence](FORECAST_LOCATION_SETUP.md). |
| `test-before-setup` | Native contract + review | A required initial current-source failure remains retryable and leaves the Home Assistant-owned HTTP session open. [Evidence](API_SOURCES.md). |
| `unique-config-entry` | Native contract + review | Duplicate identities include legacy entries and concurrent flows; a forecast-only selection is intentionally not a separate entry. [Evidence](GETTING_STARTED.md). |

## Silver: 10 rules

| Rule | Evidence | Contract and reference |
|---|---|---|
| `action-exceptions` | Reasoned exemption | There are no integration-specific actions that could need action exception translation. [Evidence](USAGE.md). |
| `config-entry-unloading` | Native contract + review | Native unload/reload releases entry callbacks and shared ownership while retaining registry identities and the borrowed session. [Evidence](SHARED_DIAGNOSTIC_LIFECYCLE.md). |
| `docs-configuration-parameters` | Reviewed source or guide | The complete Configure/Reconfigure transaction and separate station, forecast, warning and pollen purposes are documented. [Evidence](CALENDAR_AND_LOCATION_SETTINGS.md). |
| `docs-installation-parameters` | Reviewed source or guide | Setup parameters explain provider selection, station/base location, explicit pollen station and verified forecast point selection. [Evidence](GETTING_STARTED.md). |
| `entity-unavailable` | Native contract + review | Native states distinguish source failure, missing measurements, real zero and data expiry; warning/forecast expiry continues between requests. [Evidence](API_SOURCES.md). |
| `integration-owner` | Reviewed source or guide | The public owner and reporting routes are explicit. [Evidence](../SECURITY.md). |
| `log-when-unavailable` | Native contract + review | Handwritten optional-source outage/recovery logs use the official INFO level and one transition per state change, with sensitive values omitted. [Evidence](API_SOURCES.md). |
| `parallel-updates` | Reviewed source or guide | Diagnostic polling uses a bounded platform semaphore; coordinator-driven entities do not individually poll providers. [Evidence](API_SOURCES.md). |
| `reauthentication-flow` | Reasoned exemption | The public data providers require no user credentials, account or authentication token. [Evidence](API_SOURCES.md). |
| `test-coverage` | Native contract + review | The single native suite produces fresh branch coverage for every component module; existing per-module, aggregate and stricter full-coverage gates remain required. [Evidence](../DEVELOPMENT.md). |

## Gold: 21 rules

| Rule | Evidence | Contract and reference |
|---|---|---|
| `devices` | Native contract + review | All seven virtual service roles retain their identities and provider provenance through setup, settings changes and shared-owner removal. [Evidence](PROVIDER_METADATA.md). |
| `diagnostics` | Native contract + review | The actual native diagnostics response must omit sensitive registry issue placeholders as well as integration data for loaded and unloaded entries. [Evidence](GOLD_EVIDENCE_CONTRACT.md). |
| `discovery` | Reasoned exemption | The manually configured public weather service has no discoverable local appliance, bus or account-owned device inventory. [Evidence](GOLD_APPLICABILITY.md). |
| `discovery-update-info` | Reasoned exemption | No discovered host or address is stored. [Evidence](GOLD_APPLICABILITY.md). |
| `docs-data-update` | Reviewed source or guide | Documentation distinguishes request schedules, provider publication, caching, observed timestamps and expiry rather than promising an unattested refresh cadence. [Evidence](API_SOURCES.md). |
| `docs-examples` | Reviewed source or guide | Examples cover standard forecasts, read-only cards and escaped warnings. [Evidence](COORDINATOR_EXAMPLES.md). |
| `docs-known-limitations` | Reviewed source or guide | Known source geography, completeness, timestamp, archive and metadata limitations are explicit without claiming every provider measurement is present. [Evidence](API_SOURCES.md). |
| `docs-supported-devices` | Reviewed source or guide | The supported service/station families and their geography replace a fictional physical hardware compatibility list. [Evidence](POLLEN_STATIONS.md). |
| `docs-supported-functions` | Reviewed source or guide | Current observation, forecast, warning, pollen, air-quality and HGT functions are documented with retired entities distinguished. [Evidence](SENSORS.md). |
| `docs-troubleshooting` | Reviewed source or guide | Troubleshooting covers source outages, missing data, selected-location recovery, metadata refresh and repair confirmation. [Evidence](USAGE.md). |
| `docs-use-cases` | Reviewed source or guide | Getting-started use cases and ordinary Home Assistant examples explain distinct providers and weather families without actuating external devices. [Evidence](../README.md). |
| `dynamic-devices` | Native contract + review | The reviewed service has seven integration-defined roles and no dynamic upstream device inventory. [Evidence](FIXED_SERVICE_TOPOLOGY.md). |
| `entity-category` | Native contract + review | Diagnostic helpers are categorized and disabled by default; measured/modelled weather, pollen and air-quality values remain ordinary entities. [Evidence](SENSOR_METADATA.md). |
| `entity-device-class` | Native contract + review | An independent quantity inventory checks every native class, unit and state class; no unsuitable Home Assistant class is invented for Foehn, pollen, UV or degree days. [Evidence](SENSOR_METADATA.md). |
| `entity-disabled-by-default` | Native contract + review | Only the two diagnostic helpers are disabled on a new entry; all ordinary values stay enabled and existing user choices are preserved. [Evidence](SENSOR_METADATA.md). |
| `entity-translations` | Native contract + review | Every active base entity name resolves through native Home Assistant translations in four languages; observed HGT is checked independently with real Recorder. [Evidence](ENTITY_NAME_TRANSLATIONS.md). |
| `exception-translations` | Native contract + review | All actual update-failure keys resolve through Home Assistant in the four supported languages without raw provider error details. [Evidence](EXCEPTION_TRANSLATIONS.md). |
| `icon-translations` | Native contract + review | Frontend icon resolution follows existing translation keys and personal registry icons survive native reload. [Evidence](ICON_TRANSLATIONS.md). |
| `reconfiguration-flow` | Native contract + review | Both existing-entry routes use one atomic native transaction, retain identity and discard all staged changes on cancellation or concurrency conflict. [Evidence](CALENDAR_AND_LOCATION_SETTINGS.md). |
| `repair-issues` | Native contract + review | Known persistent configuration and HGT ownership problems have native translated repairs; a source outage never becomes a configuration repair and opening a repair cannot authorize deletion. [Evidence](REPAIRS.md). |
| `stale-devices` | Native contract + review | Current role ownership is maintained through real registry lifecycle. [Evidence](FIXED_SERVICE_TOPOLOGY.md). |

## Device, metadata and privacy closure

The [fixed service topology](FIXED_SERVICE_TOPOLOGY.md) verifies all seven
integration-defined roles through optional failure/recovery, source settings and
shared ownership handoff. [Applicability](GOLD_APPLICABILITY.md) records a
direct fixed-service review, not the literal single-device exemption. Native
device-page removal tests keep the [existing conservative policy](DEVICE_REMOVAL.md).
No new device discovery API or deletion permission is introduced.

The independent metadata inventory checks every base entity and optional
observed HGT using actual HA registry/runtime values. The existing native
[name tests](ENTITY_NAME_TRANSLATIONS.md) cover four languages and retained
personal choices. Foehn codes, forecast HGT and compound measured HGT retain
[their quantity-specific metadata](SENSOR_METADATA.md); no class is invented.

[Diagnostics](DIAGNOSTICS_PRIVACY_BOUNDARY.md) are checked through HA's actual
HTTP envelope, including persisted issue metadata. [Warning clocks](WARNING_STATE_CLOCK.md)
and [forecast clocks](WEATHER_FORECAST_STATE_CLOCK.md) publish time-only state
changes without source requests; [optional-source logs](OUTAGE_LOG_LEVELS.md)
retain one INFO message per outage/recovery transition.

## Security and release boundaries

[Privacy/security boundaries](GOLD_SECURITY_BOUNDARIES.md) distinguish this
engineering review from provider retention, host security, owner-authenticated
settings inventories, independent offensive testing and external certification.
Existing hash locks, full dependency-advisory checks, offline uv, pinned actions,
Hassfest, least-privilege CI and strict coverage remain. Unknown audit outcomes
are failures, not empty alert lists.

The [b6 publication record](RELEASE_EVIDENCE_8.3.5b6.md), accepted b3 cleanup
and bounded b5/b6 reports remain separate historical facts. The
[b7 package record](RELEASE_EVIDENCE_8.3.5b7.md) and
[short installed check](ACCEPTANCE_8.3.5b7.md) do not reopen those reports,
delete production statistics or promote a stable release. Use the [catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for published availability. The [b6 baseline assessment](QUALITY_SCALE_B6_BASELINE.md)
preserves the earlier tables and all dated metrics without rewriting history.
