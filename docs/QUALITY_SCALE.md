# Quality roadmap and evidence

This is a self-assessment against the current
[Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/).
It is not an official HA rating, HACS certification or release approval. HACS
installability/default listing is a separate assessment. The manifest deliberately
contains no `quality_scale` claim. Live acceptance and a tested fork release
remain separate gates after code review and CI.

## First-stage Bronze assessment

| Rule | Evidence / applicability |
|---|---|
| `action-setup` | Exempt: no integration-specific actions are registered. |
| `appropriate-polling` | Coordinators own bounded provider intervals; minimum observation interval 600 seconds. |
| `brands` | Existing `meteoswiss` assets in [HA brands](https://github.com/home-assistant/brands/tree/master/custom_integrations/meteoswiss); domain retained. |
| `common-modules` | Shared constants, time contract and entity descriptions are centralized. |
| `config-flow-test-coverage` | 100% lines and branches in `config_flow.py`, including options, errors/recovery and legacy/current duplicates; CI enforces it. |
| `config-flow` | Native user/options flow; no YAML setup. |
| `dependency-transparency` | README/usage describe public third-party services, networking, locations and the account-free setup. |
| `docs-actions`, `docs-triggers`, `docs-conditions` | Usage describes standard HA entity automation/forecast functions and the absence of custom actions/device automation extensions. |
| `docs-high-level-description` | README lists data families, scope and fork provenance. |
| `docs-installation-instructions` | README + usage document prerequisites, approved installation route and setup. Actual first HACS release remains pending. |
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
| `entity-unavailable` | Observations/warnings and both pollen/AQ clients have failure/recovery tests, including registered pollen/AQ entity states. All-empty current pollen/AQ payloads fail; partial responses retain unknown fields. Measured pollen rejects age over four hours or future skew over ten minutes on refresh. Both weather forecast services return empty lists on forecast failure and recover, while valid observations remain available. Alternative Open-Meteo current conditions have registered weather/temperature entity outage and recovery tests; invalid individual measurements stay unknown and an all-empty source fails. Registered weather attributes use native HA properties and unit conversion; forecast subscribers receive fresh/empty/recovered payloads, including through HA WebSocket. Remaining optional per-entity paths still require review; full rule remains pending. |
| `integration-owner` | `@martins-netizen` in manifest. Repository Issues are currently disabled: enable a usable fork-specific support route before public release. |
| `log-when-unavailable` | Pollen/AQ, measured pollen and the ICON forecast client use coordinator transition logs. Forecast failures suppress raw coordinate URLs/HTTP exception chains even in debug logs; repeated failure and recovery are tested. The alternative Open-Meteo current client also suppresses coordinate URLs/raw error chains and tests repeated failure and recovery. The station observation client now uses the same once-per-transition logging; selected station IDs, CSV values, asset URLs and expected HTTP error chains stay absent even in debug logs. Pending for the full integration until the remaining active-family audit is complete. |
| `parallel-updates` | Explicit platform limits: sensor 1 for diagnostic polling, coordinator-driven weather/binary sensor 0; no device actions. |
| `reauthentication-flow` | Exempt: the public APIs require no credentials. |
| `test-coverage` | Pending. [Above 95% for every module](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/) is required; a passing flow or global average is insufficient. |

The starting snapshot had 68 passing tests and 54.78% combined line/branch
coverage (58.50% lines, 40.42% branches). Config flow was 33.79% combined.
CI now measures **all** integration modules, prints per-module coverage and
requires full config-flow, both pollen-client, ICON forecast-client, alternative
Open-Meteo current-client, weather-entity, shared weather-data, hourly
precipitation, HGT utility, cache, diagnostics, station-catalogue, warning-parser,
warning-entity, numeric-sensor, pollen-sensor, config-entry setup and retry line/branch
coverage. The station coordinator has
separate minimums of 95% for lines and branches. The combined integration floor
is 98.5% (raised from 98%, previously 95%, 89%, 86%, 80%, 71%, 67% and initially 60%). This
floor prevents regressions at this stage; it is not a substitute for Silver.
Unused camera/SLF/hydrology placeholders remain visible in the denominator.
They must be explicitly removed in a reviewed scope or covered; no exclusions
are introduced just to improve the metric. Current exact results are in the
PR and each CI job's summary.

Station CSV parsing, zero/non-finite values, sparse fallback, source failures and
recovery are covered. Hourly imports include a real Recorder roundtrip proving
stable statistic identity, repeat-import upserts and corrected hour values;
archive failures preserve valid subsets and never queue all-invalid data.
HGT tests cover 12/20 thresholds, season boundaries and missing/invalid entries.

The alternative current-weather client now has full line/branch coverage: valid
zero/negative temperatures, invalid individual numbers, optional preview isolation,
observation freshness, bounded retries, cache TTL, circuit recovery, private logs
and registered HA entity states are tested on both supported HA versions.

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

The full warning-name/number catalogue is a separate verification gate, including
the legacy `4 = Wind` conflict. No new numeric meanings are approved by these
tests. The official portal's named hazard families alone cannot prove the old
App API numeric identifiers. Source/privacy review of station observations is now covered by failure/recovery
and malformed-source regressions. Inactive placeholders and the remaining
per-module gaps remain open.

Continue with source/logging rules across every active family. Public support,
numeric warning-code verification, live acceptance and release/HACS
validation remain separate gates. Raise coverage as these changes land.
Gold/Platinum work follows this measured baseline, rather than adding labels.

## Reproduce

```sh
python -m pip install -r requirements_test.txt
pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
python scripts/check_translations.py
```

Repeat in an isolated environment with `requirements_test_min.txt`. HACS
validator/default-list submission, signed-off live acceptance and the first
fork prerelease remain release tasks, not effects of this development PR.
