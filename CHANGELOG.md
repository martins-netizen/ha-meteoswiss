# Changelog

## [Unreleased]

No additional runtime changes beyond the accepted 8.3.0 package below.

## [8.3.0] — promotion of accepted b4

Prepared24 October 2026 from published/accepted b4 at
**a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5**. Only two component version files
change;37 other component files, HACS and workflows match. [Release notes](docs/RELEASE_8.3.0.md)
cover the complete changes since 8.2.0 and the [stable update](docs/ACCEPTANCE_8.3.0.md).
Publication is established by the actual GitHub release, not this heading.

- Ship postcode/town/POI selection, named forecast devices, eight forecast
  sensors, complete Swiss calendar-day handling and a shared location dialog.
- Retain the station-local model condition, measured numeric values, source
  boundaries, lifecycle/privacy/HTTP corrections and four languages accepted in b4.
- Update current setup/migration/roles/quality documentation; preserve historical
  beta notes and all prior publication scripts.
- Add stable Publisher V1.3 with accepted-source, prior-publication, immutable-tag,
  exact-check, latest-stable and read-only retry guards.

## [8.3.0b2] — forecast display test candidate

Prepared 24 October 2026 from regularly merged PR #61,
**781ba3a41fafc2e8dd5bc5f867f55c646c4a2412**. Only the two component version
fields differ from that reviewed source; 36 other component files, HACS metadata
and workflows match. Publication and practical acceptance remain separate.
See [release notes](docs/RELEASE_8.3.0b2.md) and [focused acceptance](docs/ACCEPTANCE_8.3.0b2.md).

- Prepare Publisher V1.1 from the successfully used V1.0. It creates only b2 as
  a prerelease, preserves the published b1 tag and latest stable 8.2.0, and keeps
  the exact-source/check/receipt/no-rewrite guards. Reuse failure cases for both
  publisher profiles independently of the current root version.

- Separate selected-place forecasts from the existing current-condition device.
  Reuse the HGT device identity for a translated, location-labelled forecast
  group containing the eight existing scalars, HGT and a new forecast-only
  weather entity. Retain existing unique/entity IDs, custom names and options.
- Use only ICON model values for the forecast weather entity's current hour;
  missing/failed forecasts never fall back to station measurements. Reuse the
  existing coordinator without an extra request/cache/poller.
- After an explicit catalogue selection, the original weather entity exposes
  current conditions without hourly/daily forecast features. Select the new
  forecast entity for those cards/actions. Legacy base entries keep their
  combined interface for compatibility. See [display and migration](docs/FORECAST_DISPLAY.md).
- Record successful 8.3.0b1 publication and the operator-reported display issue;
  keep the published tag, original notes and baseline test protocol unchanged.

## [8.3.0b1] — location and forecast test candidate

**Packaging prepared on 24 October 2026; publication and focused HA acceptance
are separate steps.** [Candidate notes](docs/RELEASE_8.3.0b1.md) define scope and
limits. Runtime/source is reviewed PR #59 at
4c8169206fdcb8688a438c16a93f867a633a344f: only manifest/module versions differ;
36 other component files, CH/HACS metadata and workflows remain identical.

- Prepare the candidate-specific check/publish helper and its mocked refusal,
  provenance, immutable-tag, stable-preservation and uncertain-write tests.
  Publication is prerelease-only and does not contact Home Assistant.
- Prepare the targeted existing-temporary-HA acceptance checklist; retain
  completed clean-install, restore and stable-update evidence.

- Correct daily forecast fallback: require every expected Swiss calendar hour,
  with rain/probability assigned to the preceding hour and next-midnight bucket.
  Do not publish partial hours as whole-day extrema, totals or probability.
- Withhold native daily aggregates whose fixed-offset provider bucket does not
  match both Swiss midnights around DST. Preserve usable hourly forecasts;
  missing scalar daily values and HGT remain unknown rather than shifted.
- Request optional UV timestamps as Unix seconds; reject missing, future or
  stale timestamps without taking valid AQ/pollen down. Keep real zero and a
  valid response with a missing individual UV value distinct from outage.
- Move bounded observation CSV decoding/selection into HA's executor, preserving
  measurement selection, freshness, private failures and entity/statistic IDs.
- Reconcile release/setup/source/quality documentation with merged POI dialogs,
  completed HACS acceptance and the overall release review. Add a public
  private-reporting policy; keep 8.2.0 and historical release tags unchanged.

- Add explicit forecast-location setup and reconfiguration in DE/EN/FR/IT:
  search the official catalogue locally by postcode or town/POI, choose a
  labelled point without preselection, then confirm after an ICON check.
  Preserve other source locations/options/IDs; cancel/keep never writes a
  location, and an explicit reset restores the original base coordinates.
  Save selected coordinates/provenance offline, request known catalogue
  altitude and separate height-aware cache entries. Document unchanged provider
  place names and the Murten/Morat alias limitation. Candidate acceptance remains.


- Add the bounded official forecast-point catalogue foundation: immutable
  type/ID identity and provenance, strict Latin1 CSV acceptance, local
  postcode/name/POI candidate search and a lazy borrowed-session client.
  Preserve ambiguity, enforce size/time/retry limits, coalesce fetches and
  retain old metadata explicitly on failure without labelling it fresh.
  The saved-location and translated-dialog packages now consume this foundation;
  existing entries retain their location until a deliberate confirmed change.

- Split hourly/archive precipitation into a pure source client/parser, explicit
  Recorder projection/import adapter and the actual HA coordinator in
  coordinator.py. Preserve hourly/weekly schedules, lookback, ordered corrections,
  statistics metadata/IDs, partial imports and all four availability errors.
  Keep source and executor cancellation private and non-queuing. All seven
  genuine coordinators are canonical; the agreed POI feature remains before
  release packaging.

- Separate modelled pollen/AQ and optional UV requests into pollen_openmeteo.py,
  composed by the real HA coordinator in coordinator.py. Preserve current-hour
  selection, four-attempt AQ retry, shared 30-minute cache/TTL, zero/partial
  values and independent UV availability. Suppress raw source exception chains,
  propagate cancellation/setup errors and retain all entity/lifecycle contracts.
  Keep the agreed POI feature in the next-release scope before packaging.

- Add eight numeric forecast sensors for today/tomorrow: native whole-day
  maximum/minimum temperature and precipitation, plus the highest hourly
  precipitation probability with every tied time window. Reuse the existing
  ICON forecast request. Handle missing/incomplete data, source expiry, Swiss
  midnight/DST and listener cleanup; bundle names in DE/EN/FR/IT. Keep forecast
  values separate from measured statistics. See docs/FORECAST_SENSORS.md.

- Separate the ICON client into forecast.py and define its actual HA coordinator
  in coordinator.py. Retain model, retry, cache, schedule and weather contracts.

- Separate the alternative Open-Meteo current-weather client from HA coordination.
  Keep cache TTL/freshness, failure pause, retries, partial/zero values, session
  ownership and entity identities. Define the real coordinator in coordinator.py
  and retain source parsing in openmeteo.py.

- Remove arbitrary path arguments from the local coverage checker. Read only
  repository-root coverage.json, reject symbolic links, and preserve every
  coverage threshold. Use Bash conditional expressions consistently in all
  three historical release helpers; their embedded publication logic is unchanged.

- Separate the measured-pollen CSV client from its HA coordinator. Keep the
  canonical coordinator in coordinator.py, with the same schedule, source-error
  messages, station choice, payload/history and entity identities. Reuse the
  unchanged UTC reference-time parser from weather_data.py for observations,
  measured pollen and hourly precipitation, avoiding a circular dependency.
  The client owns no session and exposes payload-free source errors; HA maps
  them to its existing unavailable/recovery behaviour. Four placement gaps remained at that step.

- Mark the optional station-catalogue diagnostic unavailable after expiry or a
  failed refresh instead of presenting retained metadata as current. Preserve
  last-good metadata, expose its count/status in redacted diagnostics without
  network access, and recover on a successful refresh. Keep identity and
  registry preferences unchanged. Move the warning coordinator out of the
  binary-sensor platform into coordinator.py with identical class behaviour.
  Record the remaining source-coordinator placement gaps explicitly.

- Schedule new observation entries automatically at 600 seconds and remove the
  polling field from setup/Configure in all four languages. Migrate existing
  intervals from entry data into options without changing the effective value;
  existing options take precedence. Preserve hidden legacy/other options when
  changing the measured-pollen station, together with entry/entity identities.
  Config schema 1.2 remains readable by stable 8.2.0; no release is implied.

- Share entity naming/attribution and repeated weather/AQ device metadata while
  retaining all nine family identity, grouping and lifecycle contracts. Report
  the declared integration version separately from the config-entry format in
  redacted diagnostics. Enforce above-95% coverage for every integration module
  while retaining the existing stricter source/flow and aggregate gates.

- Explain every setup/options field in DE/EN/FR/IT, localise the native weather
  source selector, and keep canonical English strings in sync. Clarify the
  independent observation, forecast, warning and measured-pollen locations;
  retain saved source keys, intervals and existing-entry behaviour.

- Remove unused camera/hydrology/SLF placeholders after checking imports and
  active platforms. Keep all active entities, the shared flood/avalanche warning
  feed and separately installed radar integrations unchanged.

- Analyze external-fork pull requests with the unprivileged CodeQL PR workflow;
  restrict upload permission to its analysis job and document actual-run checks
  for the first external contribution. Preserve pinned actions and branch rules.

- Bound every active HTTP source by its own HTTPS destination, refuse redirects,
  and enforce streaming wire/decompressed limits. Preserve official decade
  precipitation archives with a separate budget and retain source/identity/
  availability contracts. See [source hardening](docs/HTTP_SOURCE_HARDENING.md).

## [8.2.0] — first stable maintained-fork release

Published on **22 October 2026 at 08:52:40 Europe/Zurich**, immutable tag at
`5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5`. See
[release notes](docs/RELEASE_8.2.0.md) and [current readiness](docs/RELEASE_READINESS.md).

- Promote the operator-tested Beta2 component code without functional changes;
  only manifest/module versions become 8.2.0. Preserve HACS branch hiding,
  workflows and both immutable beta tags.
- Record the completed Beta2 new-setup/data check alongside the completed
  Beta1 runtime, HACS first installation and isolated restore evidence.
- Reconcile README/setup/migration, exact evidence and known security/quality
  limits. Keep POI, Silver/Gold and independent usability work separate.
- Derive guarded stable publisher V1.2 from Beta Publisher V1.1: read-only
  --check, exact approved protected merge, unchanged source/HACS/workflows,
  both beta tags and successful GitHub Actions checks; no HA access.

## [8.2.0b2] — pollen setup test candidate

Published on 22 October 2026 at 07:12:40 Europe/Zurich. See
[beta notes and acceptance](docs/RELEASE_8.2.0b2.md).

### Changed

- Require an explicit measured-pollen station during initial setup for both
  weather sources. Save it in the same options used by Configure, retain it
  across weather-source retries, and explain the independent measurement and
  forecast locations in DE/EN/FR/IT. Existing entries retain their settings;
  the legacy Luzern fallback is unchanged. This change is not in 8.2.0b1.
- Verify the measured-pollen choices against official station metadata and
  hourly STAC assets. Remove unsupported BLR, retain the 15 verified stations
  even during temporary data gaps, and document the real Zürich/current and
  Luzern/stale samples with offline regressions.
- Keep postcode guidance focused on the four-digit Swiss postal code in all
  four UI languages; remove the unnecessary internal App-code explanation.
- Hide default-branch downloads in the candidate HACS manifest, without
  changing the immutable first beta tag. Add guarded publisher V1.1 for the
  version-only package and the focused HA onboarding check.

### Documentation

- Maintain GitHub project documentation in English, including setup, migration,
  acceptance, quality reviews and development plans. Keep multilingual HA UI
  catalogues and quoted source evidence unchanged. Old guide paths redirect
  to their canonical English replacements.
- Reconcile completed beta publication and the operator-confirmed HACS source
  switch, clean first installation and recovery rehearsal. Track stable
  release gates separately from later POI/OGD and Silver/Gold development.
- Clarify that official rainfall source timestamps mark interval ends while
  HA statistic records use interval starts in UTC.

## [8.2.0b1] — first maintained-fork prerelease

This is a beta for explicit testing. Install only a published GitHub prerelease;
a branch or tag alone is not a completed release. See the
[release notes and known limits](docs/RELEASE_8.2.0b1.md).

### Acceptance — 20 October 2026

- The deployed `8.2.0b1` runtime at `0086b956d44b7144b242c5d5c1881d0b0650e524`
  completed its own 24-hour observation period on HA 2026.10.2. Code hashes,
  retained entity/statistic identities, personal settings and consumers matched
  the expected installation. Hourly rain statistics progressed without missing
  expected complete hours.
- The isolated optional UV request failure was correctly shown as unavailable
  and recovered on the next scheduled refresh. Other checked data stayed
  available. Forecast pollen is visually confirmed under Sensors; all twelve
  pollen categories were verified in the registry.

- At publication, clean first HACS installation and a source-switch rehearsal
  were not complete. The operator subsequently confirmed the HACS 2.0.5 switch,
  download, restart and initial visual success on 20 October. A clean first
  installation and isolated restore were subsequently confirmed on 21 October;
  see [current evidence and remaining setup finding](docs/HACS_ACCEPTANCE.md).
  No default-store listing or official HA tier is claimed.
- Add a guarded Mac publication helper. It checks the exact protected
  branch commit, unchanged accepted runtime/workflows, versions, CI and
  existing tags/releases before creating only the requested prerelease.
  Repeating it verifies an existing matching release without overwriting it.

### Changes

- Show modelled Open-Meteo and measured MeteoSwiss pollen under **Sensors** on
  device pages instead of **Diagnostic**. Existing entities update their category
  on setup/reload without changing their IDs, values or personal settings;
  technical cache and station-catalogue helpers remain diagnostic entities.

- **Breaking change before the first maintained beta:** retire the locally
  derived `precipitation_current_hour` sensor and its calculation. Only that
  entry's retired entity is removed on setup/reload; Recorder is not purged.
  Review dashboard/automation references before updating. Official hourly
  precipitation statistics and independently created helpers remain intact.
- Name measured station rain **Precipitation (10 minutes)** and alternative
  Open-Meteo rain **Precipitation (modelled interval)** in DE/EN/FR/IT. Keep
  existing precipitation unique/entity IDs and user display settings. Expose
  the measured 600-second interval and explain measurement-end timestamps,
  the station files' 20-minute publication cycle and official hourly totals.

- The original beta added beginner installation/migration guides in German;
  the current development documentation is English. Distinguish HACS
  software replacement from preserving the existing Home Assistant entry.
- Correct legacy sensor/source/roadmap documentation: verified warning codes,
  HGT 12/20, retired season/soil entities, actual source locations and honest
  coverage/release limits. No runtime files change in this documentation work.
- Prepare local 256/512 px brand icons, structured fork issue forms and an
  explicit HACS/release checklist without changing runtime code or deploying HA.
- Validate exact PR/push commits with the official digest-pinned HACS tool,
  read-only permissions and no ignored checks or automatic comments.
- Keep only current supported HACS manifest keys and distinguish the maintained
  fork's HACS display name. Branch-download hiding remains a release-promotion step.
- Move the warning client to App v3, which includes the captured Kloten drought
  warning missing from v1; never silently fall back to the incomplete old feed.
- Verify all thirteen warning families against signed Android app 3.6.0: use
  0 for Wind, 4 for Slippery Roads, 5 for Frost and prepare 6 for Thaw. Ship
  DE/EN/FR/IT labels together and preserve event text, levels, bounds and IDs.
  Document the required dashboard/awning filter review before installation.
- Remove station identifiers, raw CSV fields and source URLs from observation
  logs, including debug-level HTTP exception chains. Let the coordinator report
  unavailable/recovery transitions once; keep expected decoding failures quiet.
- Validate station asset/row shapes and retain unexpected programming errors.
  Enforce full station-coordinator coverage and a 99.0% integration floor.

- Respect Retry-After HTTP dates as well as seconds during bounded retries;
  ignore malformed delay values and fail immediately on invalid URLs/TLS errors.
- Cover complete setup/reload/unload with and without Recorder, both current
  weather providers, zero/legacy coordinates and optional-refresh cancellation.
  Enforce full setup/retry coverage and raise the combined floor to 98.5%.
- Keep typed config-entry runtime state and entity-owned forecast listeners.
- Validate both setup providers, handle retryable form errors, and prevent
  duplicate legacy and current location entries.
- Skip trailing partial station publication rows while retaining measurement
  time, age limits, missing-field semantics, zero values and historical IDs.
- Add observation freshness/source attributes and failure/recovery regressions.
- Enforce full config-flow line/branch coverage; report all module coverage in
  both supported HA environments. Document remaining Silver and release gates.
- Clarify setup/settings text in all four bundled languages.
- Reject malformed warning postcodes in both setup paths, keep the form
  correctable and explain the required four-digit value in all four languages.
- Reject pollen/AQ feeds without valid current concentrations, preserve valid
  zeros/partial values, and keep optional UV failures local to that value.
- Bind forecast pollen sensors to coordinator availability/listener lifecycle;
  read AQ and measured pollen values directly on initial add and later updates.
- Use UTC seconds for pollen/AQ hours (including autumn DST) and invalidate a
  previous-hour cache entry even when its transport TTL has not expired.
- Test real HA entity failure/recovery, bounded transport retries, cancellation
  and safe logging; enforce full line/branch coverage for both pollen clients.

### Earlier candidate corrections

- Preserve unavailable warning feeds as failures; never turn HTTP errors,
  timeouts or malformed warning lists into an all-clear.
- Use HA-owned HTTP sessions, bounded request timeouts and transient retries.
- Align forecast conditions, daylight and UTC timestamps; preserve repeated
  DST hours, native daily totals and the forecast-only meaning of HGT.
- Reject stale observation times and retain unknown measurements as unknown.
- Select current-hour pollen/AQ values instead of midnight/future substitutes.
- Ship complete en/de/fr/it catalogues with reusable warning labels and an
  optional shared button-card template. Existing codes, IDs and history remain.
- Document architecture, source contracts, minimum/current HA tests, release
  procedure and live acceptance. Remove the unverified Platinum claim.

---

## [8.0.0] — 2026-07-31

### Tier 3 — Full Documentation, Code Polish, Production Ready

This is the final major release. The integration is feature-complete, fully documented, and ready for promotion.

### Added
- **Professional README** — complete rewrite with badges, feature table, sensor reference, FAQ, comparison, installation guide
- **docs/SENSORS.md** — full sensor documentation (all entities, units, sources, update intervals)
- **docs/API_SOURCES.md** — data source documentation (APIs, URLs, rate limits, attribution)
- **ROADMAP.md** — updated with all completed features (v6.0.0–v8.0.0) and future ideas
- **Binary sensor translations** — `any_alert`, `critical_alert` keys added to all 4 languages (de/en/fr/it)
- **Forecast pollen translations** — `pollen_birch`, `pollen_alder`, `pollen_grass`, `pollen_mugwort`, `pollen_ambrosia` keys added to all 4 languages
- `quality_scale: platinum` in manifest.json
- `iot_class: cloud_polling` in hacs.json

### Changed
- Version bumped to 8.0.0
- Removed `Platform.CAMERA` from active platforms (camera is placeholder, not functional)
- Inline `import traceback` replaced with `_LOGGER.exception()` in pollen coordinator
- Consolidated duplicate `dataclass` import in sensor.py

### Fixed
- **Undefined type hint** — `PollenMeasurement` replaced with `Any` in pollen_sensor.py
- **Unused import** — `json` removed from sensor.py
- **Unused imports** — `CONF_POSTAL_CODE` removed from openmeteo_coordinator.py and pollen_coordinator_openmeteo.py
- All translation gaps closed — every entity has translations in all 4 Swiss national languages

### Code Quality
- Zero undefined names
- Zero unused imports
- All entities have translation keys
- Consistent logging (debug for routine, warning for recoverable, error for failures)
- Proper `CoordinatorEntity` pattern throughout

---

## [7.0.1] — 2026-07-31

### Removed
- `diagnostics.py` — used `platform.diagnostics` which doesn't exist in HA. Removed to prevent import errors.

---

## [7.0.0] — 2026-07-31

### Tier 2 — Major Features

### Added
- **SLF Avalanche Bulletin placeholder** (`slf.py`) — documented all tested APIs, ready for future implementation
- **BAFU Hydrological Data placeholder** (`hydro.py`) — documented all tested APIs, ready for future implementation
- **Precipitation Radar camera placeholder** (`camera.py`) — documented all tested WMS/TMS endpoints
- **MeteoSwiss measured pollen** (`pollen_meteoswiss.py`) — hourly measured pollen from 16 Swiss stations via ogd-pollen STAC API
- **MeteoSwiss pollen sensors** — 6 measured pollen types (birch, alder, hazel, beech, ash, grass) with 24h history
- **Air quality sensors** — PM2.5, PM10, NO₂, O₃ from Open-Meteo Air Quality API
- **Heating degree days** (Heizgradtage) — SIA 381/3 calculation with daily and seasonal sensors
- **Snow depth sensor** — `htoauts0` from SwissMetNet
- **Foehn index sensor** — `wcc006s0`, uniquely Swiss
- **Soil temperature sensors** — 5 cm, 10 cm, 20 cm depth
- **Measured dew point** — `tde200s0` with Magnus formula fallback
- **Forecast extensions** — snowfall, freezing level height added to forecast coordinator
- **Pollen station selection** — 16 stations configurable in options flow

### Changed
- Pollen coordinator extended to fetch air quality parameters alongside pollen
- Config flow options expanded with pollen station picker
- Forecast coordinator now fetches snowfall and freezing level height

---

## [6.1.0] — 2026-07-31

### Added
- API timeout: 30s default on all requests (was 5min unset default)
- Circuit breaker: after 5 consecutive failures, pauses updates for 5 minutes

### Changed
- WMO weather code mapping centralized in `const.py` (removed 3 duplicate copies)
- Binary sensor migrated to `CoordinatorEntity` pattern (HA best practice)

---

## [6.0.1] — 2026-07-31

### Fixed
- Pollen coordinator now uses shared aiohttp session (session leak)
- Stations CSV loader uses shared session instead of creating orphan connections
- Forecast listener properly unregistered via `async_on_unload`

### Removed
- Dead code: `pollen.py` and `pollen_coordinator.py` (276 lines of unused HTML scraping)
- `aiohttp` from `requirements` (ships with Home Assistant Core)

### Changed
- Pollen coordinator logging from `info` to `debug` (reduces log spam)
- Minimum Home Assistant version: `2024.7.0` (WeatherEntityFeature requirement)

---

## [6.0.0] — 2026-07-31

### Stable Release — Clean Start

All previous versions (v5.0.5 – v5.2.2) have been removed. v6.0.0 is a fresh beginning.

### Fixed (Critical)
- **Shared session leak** — `alerts.py` and pollen coordinators closed the shared aiohttp session, killing all other coordinators with `RuntimeError: Session is closed`
- **Orphan session creation** — Coordinator fallbacks created sessions that were never closed (socket/FD leak)
- **Forecast listener leak** — Weather entity subscribed to forecast coordinator but never unsubscribed on unload

### Fixed (High)
- **Naive datetime** — `datetime.now()` replaced with timezone-aware `datetime.now(timezone.utc)` in alert logic
- **Traceback spam** — `import traceback; _LOGGER.error(traceback.format_exc())` replaced with `_LOGGER.exception()` across 5 files

### Removed
- Dead `VERSION` constant from `const.py`
- All legacy Git tags and GitHub releases (v5.0.5 – v5.2.2)
- Legacy documentation

### Added
- Fresh README with full feature documentation
- Proper device info, entity categories, and attribution

