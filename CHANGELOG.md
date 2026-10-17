# Changelog

## Unreleased — quality baseline, publication gaps and pollen availability

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
- Reject pollen/AQ feeds without valid current concentrations, preserve valid
  zeros/partial values, and keep optional UV failures local to that value.
- Bind forecast pollen sensors to coordinator availability/listener lifecycle;
  read AQ and measured pollen values directly on initial add and later updates.
- Use UTC seconds for pollen/AQ hours (including autumn DST) and invalidate a
  previous-hour cache entry even when its transport TTL has not expired.
- Test real HA entity failure/recovery, bounded transport retries, cancellation
  and safe logging; enforce full line/branch coverage for both pollen clients.

All notable changes to this project will be documented in this file.

---

## [8.2.0b1] — prepared, not released

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
