# Quality roadmap and evidence

## Current follow-up — 23 October 2026

Stable 8.2.0 is published, and its HACS update is operator-confirmed. The clean
first installation/isolated restore and Beta2 setup are complete within their
[recorded scope](HACS_ACCEPTANCE.md); no new independent runtime comparison
is inferred from the update confirmation. The dated account below remains
historical.

Unreleased [shared HTTP hardening](HTTP_SOURCE_HARDENING.md) adds fixed
per-source destinations and bounded wire/decompressed reads, with preserved
archive budgets and failure semantics. The transport joins the existing strict
100% line/branch gates. A focused next-package HA acceptance remains separate;
this change alone does not close all Bronze/Silver rules. Placeholder cleanup,
translated field help and shared entity metadata are now documented separately.
The version metadata's real diagnostic consumer closes its coverage gap; every
module exceeds 95%, enforced alongside existing stricter gates. Polling/UI
defaults and the legacy options bridge are now implemented with real
reload/registry tests. Remaining coordinator placement and the
location/reconfiguration contract remain on the plan.

## Historical acceptance update — 20 October 2026

The live candidate is `8.2.0b1` at
`0086b956d44b7144b242c5d5c1881d0b0650e524`. Local verification recorded 786
passing tests on both HA 2026.8.3 and 2026.10.2, with 99.051% combined
line/branch coverage. The exact accepted commit also passed its six post-merge
checks (including HA 2026.10.1, HACS validation, Hassfest and CodeQL).

Its deployed 24-hour observation completed on 20 October 2026. Registry
identity, personal settings, warning consumers and hourly rain statistics
matched expectations. One isolated optional UV failure recovered on the next
scheduled refresh; the failure remained local to UV. Forecast pollen's Sensors
grouping is visually confirmed, and all twelve pollen categories were checked
in the registry. Earlier dated entries below describe their earlier baselines.

The first GitHub beta was published on 20 October 2026. The operator then
confirmed the HACS 2.0.5 source switch, downloaded 8.2.0b1 version, restart and
positive initial visual check. A clean first HACS installation remains open;
no new independent post-switch file/registry/statistic comparison or executed
rollback is claimed. See the [HACS evidence record](HACS_ACCEPTANCE.md).

These findings do not close unrelated Bronze/Silver gaps or award an official
HA quality tier. The [beta notes](RELEASE_8.2.0b1.md) state those limits; no new
runtime or HA deployment is required for documentation-only changes whose
component files match the accepted commit. The [current release checklist](RELEASE_READINESS.md)
separates stable-release gates from the later Silver/Gold and location backlog.

This is a self-assessment against the current
[Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/).
It is not an official HA rating, HACS certification or release approval. HACS
installability/default listing is a separate assessment. The manifest deliberately
contains no `quality_scale` claim. Live acceptance and a tested fork release
remain separate gates after code review and CI.

The [next-release plan](NEXT_RELEASE_PLAN.md) coordinates the remaining
Bronze/Silver work, a separately validated POI/location feature and the Gold
backlog. It is planning, not a completed tier assessment. The HA project treats
[custom integrations separately](https://contributors.home-assistant.io/core/quality-scale/tiers/#custom);
following its rules does not award this HACS fork an official Silver/Gold tier.

The [complete dated Bronze/Silver audit](QUALITY_AUDIT_2026-10-17.md) evaluates
all 30 rules individually and records the exact code/test baseline. It is the
current detailed finding; the tables below remain a concise overview. The
[bounded POI probe](POI_FEASIBILITY.md) records successful public location/ICON
requests and the remaining warning/height requirements.

## First-stage Bronze assessment

| Rule | Evidence / applicability |
|---|---|
| `action-setup` | Exempt: no integration-specific actions are registered. |
| `appropriate-polling` | Unreleased setup/Configure no longer exposes polling; new observations use a developer-selected 600 seconds. Schema 1.2 preserves installed intervals as a documented compatibility bridge, with options precedence and existing coordinator minimum guards. Source-specific schedules remain unchanged. This bridge is not a blanket exemption or complete Bronze claim; provider-wide interval review and eventual legacy policy remain explicit. |
| `brands` | Local `custom_components/meteoswiss/brand/icon.png` (256 px) and `icon@2x.png` (512 px), with reproducible original artwork. Domain retained; no HA/provider logo or official-product claim. See [publication requirements](PUBLISHING.md). Partial for the separate Core rule: the expected `home-assistant/brands/core_integrations/meteoswiss` path returned 404 on 17 October 2026. |
| `common-modules` | Unreleased entity.py centralizes entity/coordinator metadata and the genuinely duplicated weather/AQ device definitions across all nine families. Primary observations retain coordinator.py; typed runtime/source boundaries remain intact. Fixed identity/metadata contracts pass before and after the refactor; Warning coordinator now also lives in coordinator.py, removing setup/runtime dependence on binary_sensor.py. Measured pollen now has a source client and canonical coordinator with the shared UTC parser in weather_data.py. Alternative current conditions and ICON forecasts also have separate source clients and canonical coordinators. The bounded placement review inventories two remaining source-module findings; see the [placement review](COORDINATOR_LAYOUT_REVIEW.md). The full common-modules rule remains partial. |
| `config-flow-test-coverage` | 100% lines and branches in `config_flow.py`, including options, errors/recovery and legacy/current duplicates; CI enforces it. |
| `config-flow` | Native user/options flow; no YAML setup. Unreleased development adds DE/EN/FR/IT help for all remaining actual field occurrences, a native translated source selector and canonical English strings.json. HA translation-loader regressions and full flow coverage pass. Schema 1.2 moves only legacy polling data to options without value/identity changes; Configure merges its pollen choice into existing options. Real reload/registry/Recorder regressions cover this. Final selector/UX and remaining prerequisites stay separate; see the dated follow-up. |
| `dependency-transparency` | Exempt for the current integration: `manifest.json` has no extra Python `requirements`. Public provider/location dependencies are separately documented; that is not the criterion of this rule. |
| `docs-actions`, `docs-triggers`, `docs-conditions` | Exempt: no integration-specific actions, triggers or conditions. Usage still explains standard HA entity automations and forecast functions. |
| `docs-high-level-description` | README lists data families, scope and fork provenance. |
| `docs-installation-instructions` | README routes new/existing users to separate English step-by-step guides; usage is the technical reference. First beta publication and the operator-confirmed HACS 2.0.5 source switch are complete. A clean first install and an independent newcomer usability walkthrough remain open; see HACS_ACCEPTANCE.md. |
| `docs-removal-instructions` | Usage documents entry/component removal and effects on consumers/history. |
| `entity-event-setup` | CoordinatorEntity manages observations and forecast pollen; weather forecast subscription belongs to entity add/remove lifecycle. Tests verify pollen listeners are removed on unload. |
| `entity-unique-id` | Existing entry-based and shared diagnostic IDs retained; reload test checks registry mapping stability. |
| `has-entity-name` | Enabled on active entities, including the main weather entity with its device name. |
| `runtime-data` | Typed `MeteoSwissConfigEntry` and dataclass; shared diagnostic ownership flags alone remain domain-global. |
| `test-before-configure` | Both providers validate the observation coordinator before saving, within a 30-second total timeout. |
| `test-before-setup` | Required observation first refresh precedes platform setup; optional families refresh separately. |
| `unique-config-entry` | Source/location/postcode guards cover old entries without unique IDs and HA unique-ID checks. |

These are code/documentation findings to be confirmed in PR checks and the live
acceptance of the reviewed commit. They do not mark the existing installed
snapshot as having acquired these changes.

## Silver gaps and next implementation order

| Rule | Current assessment / next action |
|---|---|
| `action-exceptions` | Exempt: no integration-specific service actions. |
| `config-entry-unloading` | Native unload/reload; tests verify HA session ownership, replaced runtime state, stable entity IDs and removed observation/forecast listeners. Real-Recorder entry lifecycles cover both providers and remove the listener-backed hourly/archive importers on reload/unload; cancelling optional startup cancels every inflight child refresh. |
| `docs-configuration-parameters`, `docs-installation-parameters` | Usage includes provider selection, intervals, coordinates, warning postcode and measured pollen station. |
| `entity-unavailable` | Observations/warnings and both pollen/AQ clients have failure/recovery tests, including registered pollen/AQ entity states. All-empty current pollen/AQ payloads fail; partial responses retain unknown fields. Measured pollen rejects age over four hours or future skew over ten minutes on refresh. Both weather forecast services return empty lists on forecast failure and recover, while valid observations remain available. Alternative Open-Meteo current conditions have registered weather/temperature entity outage and recovery tests; invalid individual measurements stay unknown and an all-empty source fails. Registered weather attributes use native HA properties and unit conversion; forecast subscribers receive fresh/empty/recovered payloads, including through HA WebSocket. The optional UV gap is now fixed: a failed request/shape makes only UV unavailable, a successful response with no valid value stays unknown. Registered failure/cache/recovery tests keep AQ/pollen healthy and preserve UV identity. Unreleased catalogue diagnostic now becomes unavailable on expiry/failure while retaining last-good metadata; no-snapshot state is not a healthy zero. Registered HA-state and recovery tests verify it, and safe diagnostic count/status remains accessible without IO. Cache counters remain available as local metrics. This closes the identified catalogue gap; whole-rule and later package acceptance remain separate. |
| `integration-owner` | `@martins-netizen` in manifest. Repository Issues and private vulnerability reporting are verified enabled on 17 October 2026. Bundled issue forms provide a fork-specific support route. |
| `log-when-unavailable` | Pollen/AQ, measured pollen and the ICON forecast client use coordinator transition logs. Forecast failures suppress raw coordinate URLs/HTTP exception chains even in debug logs; repeated failure and recovery are tested. The alternative Open-Meteo current client also suppresses coordinate URLs/raw error chains and tests repeated failure and recovery. The station observation client now uses the same once-per-transition logging; selected station IDs, CSV values, asset URLs and expected HTTP error chains stay absent even in debug logs. The separate UV request now has a cached source flag and once-per-outage/recovery logs. Registered tests cover transport, timeout, invalid JSON/shape, cache reuse and private error chains. No complete Silver claim follows from this individual fix. |
| `parallel-updates` | Explicit platform limits: sensor 1 for diagnostic polling, coordinator-driven weather/binary sensor 0; no device actions. |
| `reauthentication-flow` | Exempt: the public APIs require no credentials. |
| `test-coverage` | Evidenced for unreleased development: every module exceeds 95%; entity.py/version.py have real consumers and full coverage, const.py is 98.51%, all others 100%. CI enforces the per-module floor plus stricter existing gates; a synthetic low module cannot hide behind the aggregate. Local supported-HA runs pass 967 tests/14 subtests, 99.968% combined. This single rule does not establish full Silver. |

The starting snapshot had 68 passing tests and 54.78% combined line/branch
coverage (58.50% lines, 40.42% branches). Config flow was 33.79% combined.
CI now measures **all** integration modules, prints per-module coverage and
requires full config-flow, both pollen-client, ICON forecast-client, alternative
Open-Meteo current-client, weather-entity, shared weather-data, hourly
precipitation, HGT utility, cache, diagnostics, station-catalogue, warning-parser,
warning-entity, numeric-sensor, pollen-sensor, config-entry setup, retry and station
coordinator line/branch coverage. The combined integration floor is 99.0%
(raised from 98.5%, previously 98%, 95%, 89%, 86%, 80%, 71%, 67% and initially 60%). This
floor prevents regressions at this stage; it is not a substitute for Silver.
Unreleased development explicitly removes unused camera/SLF/hydrology
placeholders after a reference/platform review; it does not exclude their
uncovered lines from an otherwise retained feature. The version module now has a meaningful diagnostic consumer and full coverage.
All modules exceed 95%; no coverage exclusion or lowered gate is added.
See [current follow-up evidence](QUALITY_PROGRESS_2026-10-22.md). Current exact results are in the
PR and each CI job's summary.

Station CSV parsing, zero/non-finite values, sparse fallback, source failures and
recovery are covered. Hourly imports include a real Recorder roundtrip proving
stable statistic identity, repeat-import upserts and corrected hour values;
archive failures preserve valid subsets and never queue all-invalid data.
HGT tests cover 12/20 thresholds, season boundaries and missing/invalid entries.

The alternative current-weather client now has full line/branch coverage: valid
zero/negative temperatures, invalid individual numbers, optional preview isolation,
observation freshness, bounded retries, cache TTL, circuit recovery, private logs
and registered HA entity states are tested on both supported HA versions. The
source client now lives in openmeteo.py, composed by the actual coordinator in
coordinator.py. Request/parser logic is retained; HA still owns cache age/TTL,
circuit recovery, current-data acceptance and session lifecycle. The independent
ICON source client is now separated in forecast.py, with its genuine coordinator
also in coordinator.py. Two source coordinator-placement findings remain; this does not complete common-modules.

The weather entity and shared number/time contract have full line/branch
coverage. Native observations, HA unit conversion, service responses and actual
WebSocket forecast subscriptions are tested. Aggregation covers full native
daily extrema, missing/gapped rain, Swiss midnight and 23/25-hour DST days.
Original regression tests reproduce missing weather attributes and a forecast
subscriber receiving no refresh before the fix.

Cache, diagnostics and the shared station catalogue have full line/branch
coverage. Tests reproduce the exact TTL boundary, the provider-column parser
failure and diagnostics on an unloaded entry before the fixes. Catalogue tests
cover cache expiry, concurrent loads, stale/failure/recovery, total timeout,
manual retry, cancellation, session ownership and geographic exports. Diagnostics
omit raw dictionary keys/names/cache values and expose only safe status/time
metadata. The parser was additionally checked against the live public catalogue
on 16 October 2026 (159 stations, including KLO).

Warning parser and all active sensor platforms have full line/branch coverage.
Registered binary sensors preserve identity across active/upcoming, malformed-feed
failure and empty-feed recovery. HGT reads preloaded forecasts immediately and
uses the Swiss calendar day; optional missing families and empty observations
remain unknown. Invalid levels, boolean/fractional codes, epoch-zero bounds,
total timeout, cancellation and private error chains have regression coverage.
Only compatibility shims below the declared minimum HA are removed; existing
air-quality unit spelling and effective diagnostic entity categories are kept.

Config-entry setup and transport retries also have full line/branch coverage.
Real-Recorder setup/reload/unload exercises both current-weather providers,
station hourly/archive polling without entity listeners, stable registry IDs,
HA-owned sessions, optional-task cancellation and independent legacy-coordinate
fallbacks (including valid zero coordinates). Regression tests reproduce ignored
HTTP-date Retry-After values, non-finite delays and repeated permanent URL/TLS
errors before the fix. RFC 9110 seconds and HTTP-date pauses are now respected
within the retry sequence. A pause longer than the configured maximum stops
that sequence; the next coordinator refresh still follows its normal schedule.
This is not a persistent cross-refresh provider cooldown. Attempt counts,
delay caps, outer total timeouts and cancellation are preserved. Header/error
contents are never logged by the retry helper.

Station observation logs also have regression coverage for private source URLs,
selected station identifiers, invalid numeric fields and once-per-transition
failure/recovery. Malformed metadata/row shapes are handled explicitly;
unexpected programming errors are no longer swallowed as an empty source.
Existing measurement selection, missing/zero values and timestamps are retained.
The complete station coordinator has full line/branch coverage on both supported
HA versions, with the same full-module CI gate and a 99.0% overall floor.

The warning catalogue is now verified against the signed Android app 3.6.0,
including the direct raw-code indexing path. Captured v3/v5 drought data also
explains a missing v1 warning. See [source evidence and migration](WARNING_CODES.md).
Tests cover the actual v3 capture, all thirteen labels, prepared Thaw handling,
unknown future codes, event details and absence of a silent v1 fallback.
Existing HA consumers still require review of the legacy `4 = Wind` conflict
before deployment. Source/privacy review of station observations is covered by
failure/recovery and malformed-source regressions. Inactive placeholders and
the remaining per-module gaps remain open.

Continue with the remaining flow, catalogue-diagnostic, module-layout, branding and per-module gaps
from the dated audit. Public support,
warning-consumer migration, live acceptance and release/HACS
validation remain separate gates. Raise coverage as these changes land.
Gold/Platinum work follows this measured baseline, rather than adding labels.

## Targeted follow-ups after the dated audit

Warning state labels in DE/EN/FR/IT and the hazel icon are corrected. The
optional UV source has isolated availability and private transition logs.
Measured oak uses the verified `kaquerh0` hourly column, with partial/legacy CSV
handling and stable existing identities. The combined local candidate passes
779 tests on HA 2026.8.3, 2026.10.1 and 2026.10.2; combined coverage is 99.0572 %.
All three changed runtime modules retain 100 % line/branch coverage. These
results do not close the remaining individual-module and Bronze/Silver gaps.
Actual installation/visual checks and the candidate's own 24-hour observation
remain pending.

## Reproduce

```sh
python -m pip install -r requirements_test.txt
pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
python scripts/check_translations.py
```

Repeat in an isolated environment with `requirements_test_min.txt`. The first
fork prerelease and its runtime acceptance are now complete; publication
requirements and the still-open clean first install are tracked in PUBLISHING.md
and RELEASE_READINESS.md. Default-list submission remains separate. Historical
entries above do not reopen completed acceptance work.
