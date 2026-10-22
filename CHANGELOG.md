# Changelog

## [Unreleased]

## [8.2.0] — first stable maintained-fork candidate

Prepared stable package; not yet published. See [release notes](docs/RELEASE_8.2.0.md)
and [current readiness](docs/RELEASE_READINESS.md).

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

