# Bronze/Silver follow-up — 22 October 2026

**Record version:** 1.6. **Scope:** unreleased development after stable 8.2.0.
The [dated original audit](QUALITY_AUDIT_2026-10-17.md) remains historical.
This document records individual improvements, not an official HA quality tier.

## Bound coverage input and normalize release-helper conditions

The coverage gate no longer passes an optional command-line pathname into a
file read. It accepts no arguments, uses only the repository-root coverage.json
and rejects an existing symbolic link. All coverage assertions remain identical.
Replace all 13 simple Bash `[` tests in the three historical release helpers
with `[[ ... ]]`, preserving their embedded Python payloads byte for byte.

Direct tool regressions exercise working-directory independence, path/symlink
refusal, all existing categories of coverage failure, and help/invalid/accepted
mode argument handling before any external command. Existing mocked publisher
regressions retain their release/refusal/retry contracts. See the
[maintenance procedure](MAINTENANCE.md#local-tool-input-boundaries).
The integration source, workflows, dependencies, tags and released 8.2.0 are
unchanged. A SonarQube Cloud reanalysis/quality-gate result is separate evidence;
no alert is dismissed or excluded by this correction.

Both local environments (HA 2026.8.3 and 2026.10.2) pass **972 tests and
53 subtests**, including all existing mocked publisher regressions. The five
new tool tests add 39 subcases; the four coverage-input tests produce 11
failures against the previous checker and pass after the fix. Integration
coverage remains **99.968%**, with **676/676 branches**, all stricter gates and
every module above 95%. AST comparison confirms unchanged coverage assertions;
all three publisher Python payloads are byte-identical. Bash syntax, bundled
translations/version and the new documentation link/anchor also pass. CI keeps
its existing HA 2026.8.3/2026.10.1 matrix.

## Remove unused product placeholders

Review found no imports/callers of `camera.py`, `hydro.py`, `slf.py` or
`MeteoSwissRadarCamera` outside those files. Active platform forwarding lists
only sensor, weather and binary_sensor; `Platform.CAMERA` was already removed
in earlier history. No service, config flow or test registers these placeholders.
The camera never returned an image; hydro/SLF contained comments and a logger.

Remove all three files rather than shipping unused product promises or treating
old comments about unavailable APIs as current provider evidence. Keep the
existing shared App v3 flood/avalanche parser and all active platforms intact.
There is no config/registry/statistics migration and no interaction with a
separately installed radar integration. A new standalone river-gauge, radar or
bulletin product would need a separately verified source and product contract.

Repository import/reference searches, the complete supported-HA regression
suites and existing full-coverage gates verify the bounded removal. Do not add
placeholder tests, no-op imports, coverage exclusions or a lower threshold
merely to make a percentage increase. Exact candidate/CI evidence belongs to
the PR and its job summaries. Local suites pass 917 tests and 14 subtests on
both HA 2026.8.3 and 2026.10.2; CI retains HA 2026.8.3/2026.10.1.

## Explain every setup field in four languages

A separate config-flow follow-up adds field-level help to all ten actual field
occurrences across user/source, MeteoSwiss station, Open-Meteo coordinate and
Configure forms. DE/EN/FR/IT distinguish measured station weather, the independent
warning postcode, forecast/model-pollen/AQ/UV coordinates and the measured-pollen
station. Station entries keep using HA home coordinates for forecasts; Open-Meteo
entries keep their explicitly configured coordinates. No location is reassigned.

Replace the two hardcoded English source choices with a native translated
SelectSelector, retaining `meteoswiss`/`openmeteo` values and the existing default.
Remove the unused source label from Configure; source/location editing is still
not offered there. Keep polling defaults, custom intervals, options precedence,
validation/retry behaviour, saved entry data and entity/statistic identities.

Add canonical English `strings.json`, identical to translations/en.json. The
translation checker now rejects missing/extraneous field help and canonical
English drift, in addition to duplicate/unresolved/mismatched language keys
and manifest/version drift. All four catalogues contain 105 matching keys.
Twelve regressions failed against the earlier bundle and pass after the fix:
HA's actual translation loader serves setup/options help and source choices in
all four languages. Both HA 2026.8.3 and 2026.10.2 suites pass **929 tests and
14 subtests**, with **99.9031%** combined coverage and all **670 branches**.
The complete existing config-flow tests retain full line/branch coverage. A visual check of the new texts/selectors in the temporary HA
belongs to the next reviewed test package; no live walkthrough is claimed.

## Share entity metadata and distinguish version meanings

`entity.py` now provides small shared entity/coordinator bases: common
has_entity_name and default MeteoSwiss attribution, with source-specific
attribution retained by each family. The coordinator base adds no constructor,
update, availability or lifecycle hooks. HA's CoordinatorEntity remains in the
same delegation chain. Polling diagnostics use the non-coordinator base.

Only genuinely duplicated device dictionaries are centralized: weather plus
observations share their existing weather-device factory, while AQ plus modelled
pollen share their existing provider-device factory. Warning, measured-pollen,
calculated and shared-diagnostic groups keep their distinct device definitions.
No source/coordinator is merged, device is renamed, unique ID is changed or
entity is moved to another device. All nine family identity/metadata contracts
pass against the previous code and the refactor; existing real-Recorder,
reload/unload, availability and weather subscription tests remain in force.

The redacted diagnostic payload adds `integration_version` from the declared
component version. Existing config_entry.version/minor_version remain the config
format, not a release number. Loaded/unloaded-entry regressions demonstrate
this distinction, compare the component version with manifest.json, and retain
privacy checks. Version metadata now has a real diagnostic consumer rather than
a test-only import. It is not a commit/hash attestation: unpublished development
still declares 8.2.0 until a separately reviewed release package is prepared.
The actual HA download-route/usability review remains a separate Gold check.

Local HA 2026.8.3 and 2026.10.2 suites pass **940 tests and 14 subtests**,
**99.9677%** combined coverage and all **670 branches**. All modules now exceed
95%: const.py remains 98.51%, every other module is 100%, including entity.py
and version.py. CI enforces **above 95% for every module**, while keeping the
existing stricter flow/source gates and 99% aggregate floor. Isolated negative gate checks
reject a synthetic 95%/94.9% module despite a high aggregate. No module
or error-branch exclusions are added. This evidences the coverage rule, not the
complete Bronze/Silver assessment.

## Migrate installed polling choices and simplify Configure

New entries use **600 seconds** for observation polling without asking the user
for an interval. Remove that field, its help and its label from setup/Configure
in all four catalogues; keep canonical English synchronized (**101 keys each**).
Configure now explains its one purpose: selecting the measured-pollen station.
Source/location selections, source validation, independent refresh schedules,
minimum-interval guards and warning behaviour stay unchanged.

Schema **1.2** moves a legacy `update_interval` from data into options, keeping an
existing options value in preference to data. Missing intervals remain absent
and use the 600-second default. Copy both dictionaries through HA's update API;
retain unknown keys, pollen choice and all non-polling data. Reject unsupported
major schemas without writes; leave current/future minor schemas unchanged.
The migration is idempotent and needs no network or registry/statistics writes.
Stable **8.2.0** already reads the options value first, so migrated entries remain
readable when returning to it. Its older Configure UI can still change that
option; upgrading again retains the option value. No downgrade walkthrough on
live HA is claimed.

The new options flow merges its supported pollen field into existing options.
It cannot discard the hidden legacy interval or other stored options when the
user changes stations. Existing-entry polling is a deliberate compatibility
bridge, not a new polling field or an unqualified exemption from the current
[appropriate-polling rule](https://contributors.home-assistant.io/core/quality-scale/appropriate-polling/).
Future standardization of installed custom intervals needs a separate migration
and review; the default and source-specific schedules remain documented.

Fourteen new regressions fail against the preceding tree and pass after the
change. They cover both providers, absent/data/options/conflicting intervals,
unchanged registry/entry identity, repeated migration, unsupported/future
schemas and hidden-field rejection. The actual HA setup/options/reload/unload
paths additionally verify migrated 1200-second and new 600-second operation,
pollen changes, retained extra options, registry IDs and Recorder listeners.
Local HA **2026.8.3/2026.10.2** suites pass **956 tests and 14 subtests**,
**99.96787664632187%** combined coverage and **676/676 branches**. Migration and
config flow retain **100% lines/branches**; every module remains above 95% and
all stricter gates pass. CI still uses HA **2026.8.3/2026.10.1**. These tests
mock source transport and do not establish a new live installation/acceptance.
Published-release setup instructions remain explicitly scoped to 8.2.0 alongside
a clear unreleased-flow note, avoiding an instruction to find a removed field.

## Make catalogue diagnosis honest and remove a platform dependency

The optional station-count sensor previously stayed available whenever last-good
metadata existed, including after the 24-hour deadline and a failed refresh.
It now requires a successful current catalogue and its own completed update.
Availability and catalogue status check freshness when read, including between
polls. HA publishes state on its normal or explicit state update; no expiry
background task or extra request is added. No loaded snapshot means a None
native value instead of a healthy-looking zero. Stale station lists and public
exports are retained as last-good metadata; a successful refresh restores the
same entity/device/registry identity.

HA omits extra entity attributes while unavailable. The safe catalogue status
therefore includes retained `station_count` as well as current/stale/unavailable,
last success and sanitized error class. It remains accessible through the
redacted diagnostic without network access or a raw station/location payload.
Local cache counters remain available independently of provider connectivity.
The existing catalogue lock, 24-hour original cache deadline, bounded retries,
five-minute retry suppression and transition logging remain unchanged.

Seven new cold-load/expiry/failure/recovery cases reproduce the old defect,
including a complete HA config-entry/platform registration test. HTTP 404, 503
and invalid metadata retain the correct unavailable/last-good distinction.
The registered test verifies actual HA states, retained diagnostic count/status
without another request, recovery on the same identity and normal unload.
The preceding-tree run uses the previous warning-coordinator patch location;
only this test-fixture import path differs from the current run.

The [placement review](COORDINATOR_LAYOUT_REVIEW.md) inventories all seven actual
DataUpdateCoordinator definitions. Move the complete warning class from the
binary-sensor platform to coordinator.py; its class AST is identical. Setup
and typed runtime import the canonical module directly. The platform retains
an import of the same class for its entity annotation/old import path, with no
second class or wrapper. Logger namespace follows coordinator.py; warning
parsing, labels/timing, error/recovery logs, session close and startup/unload
behaviour remain covered by the existing regression suite.

Local HA **2026.8.3/2026.10.2** runs pass **963 tests and 14 subtests**,
**99.96791786974656%** combined coverage and **676/676 branches**. Catalogue,
entity, warning coordinator and all existing strict module gates remain at
100% lines/branches; every module exceeds 95%. Four catalogues still have
**101 keys**, manifest/module version remains 8.2.0, and CI still uses
**2026.8.3/2026.10.1**. No new dependency, lint/coverage suppression, altered
workflow, release or live installation. The five remaining source-specific
coordinator definitions still fail the literal module-placement rule; document
the source-client extraction prerequisite rather than claiming full compliance.

## Separate the measured-pollen source client from HA scheduling

The genuine MeteoSwissPollenCoordinator definition now lives in coordinator.py.
It composes MeteoSwissPollenClient from pollen_meteoswiss.py rather than inheriting
an implementation hidden in the source module. The client owns the same bounded
OGD CSV fetch, cp1252 decoding, transient retries, station/time validation, seven
species and existing payload/history format. The HA class owns its hourly
schedule and maps two payload-free source exceptions to the existing UpdateFailed
messages. No HA exception, coordinator or runtime type is imported by the client.
Cancellation and a missing-session setup error still propagate. Logger namespace
follows coordinator.py; once-per-outage/recovery and privacy tests remain active.

The source client borrows its session; it creates/closes no session and adds no
poller, task, cache, dependency or network destination. Actual station/option
choices, source schedules, four-hour age, ten-minute future skew, zero/missing
values, units and 24-row history remain unchanged. Setup and runtime typing use
the canonical class; HA fixtures now target that class and source parser tests
address client.parse_csv. Persisted configuration and entity/device/statistic
identities require no migration.

The provider reference-time parser moves once into weather_data.py as
parse_reference_timestamp. Observations use its previous private import alias;
measured pollen and hourly/archive precipitation use the canonical function.
The parser body, count conversion and CSV parser body are AST-equivalent to the
previous tree after documented identifier renames, preventing an import cycle
without introducing a competing UTC interpretation. Actual observation,
precipitation and pollen tests continue to exercise those consumers.

Four new direct-client tests pass no HA runtime/coordinator to the client: a
borrowed mocked aiohttp session supplies an oak-only zero/partial response, a transport
failure, invalid data and cancellation. Source exception messages contain no payload/text;
the client keeps the session open and the owner closes it. Existing HA source,
error/recovery/privacy, setup/options/reload/unload, Recorder and registry tests
remain green. These are internal source boundaries, not a separately published
library or an assertion that this integration imports without HA installed.

Local HA **2026.8.3/2026.10.2** runs pass **967 tests and 14 subtests**,
**99.968%** combined coverage and **676/676 branches**. Both strict coverage
checks pass: all modules exceed 95%, with the same source/flow 100% contracts.
Only the existing const.py line remains uncovered. DE/EN/FR/IT retain **101 keys**
and manifest/module version stays 8.2.0. CI remains **2026.8.3/2026.10.1**.
No release/tag or live HA change. The [placement review](COORDINATOR_LAYOUT_REVIEW.md)
now records **four** remaining source-module definitions; this closes the
measured-pollen finding without claiming complete common-modules or Silver.

## Remaining prerequisites and boundaries

- The version-module coverage gap is closed through its diagnostic consumer.
  Keep manifest/module consistency and all-module coverage checks; a percentage
  does not establish a complete integration-quality tier.
- Field help, translated source selection and the bounded polling/options
  migration are implemented. Final selector/UX and remaining provider/module
  contracts still need their own rule-specific review.
- Legacy intervals are retained through the explicit compatibility bridge; no
  existing 900/1200-second choice is silently replaced with 600 seconds.
- Shared entity metadata is now implemented and reviewed within this scope.
  Warning coordinator platform coupling and the catalogue diagnostic gap are
  corrected. Measured pollen now also has a source-client/canonical-coordinator
  boundary and the shared UTC parser prerequisite is complete. Four source-module
  coordinator definitions and Core-brand evidence remain open.
- The official [coverage rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/)
  applies per module, not only to the aggregate. The
  [UI setup rule](https://contributors.home-assistant.io/core/quality-scale/config-flow/)
  also requires understandable fields and proper data/options separation.

Stable 8.2.0 and its tags stay intact. No HA change, restart, release or repeated
first-install/restore test follows from this source-only cleanup. Bundle any
later accepted runtime changes into a separately reviewed test package.
