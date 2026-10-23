# Bronze/Silver follow-up — 22 October 2026

**Record version:** 1.13. **Updated:** 23 October 2026. **Scope:** unreleased development after stable 8.2.0.
The [dated original audit](QUALITY_AUDIT_2026-10-17.md) remains historical.
This document records individual improvements, not an official HA quality tier.

## Saved forecast location, altitude routing and independent current weather

The second POI package adds an offline versioned encoder/decoder and explicit
legacy/catalogue/invalid target resolution. Setup routes only ICON forecasts
and derived scalars/HGT to a confirmed point; current weather, AQ/pollen/UV,
observations, warning postcode and measured pollen retain their existing roles.
Known catalogue altitude, including zero/negative values, is sent to Open-Meteo
as its downscaling target. Missing height keeps automatic DEM. Explicit-height
cache keys include normalized height; the legacy key and original TTL remain.

An invalid saved selection disables forecast requests without moving them to
home coordinates. A selected POI cannot become the existing weather entity's
current-condition forecast fallback. Local weather/scalar/HGT attributes
identify the point; diagnostics redact the entire saved object in both data
and options and export only fixed status/elevation-mode labels. Normal startup
and reload never require catalogue access or write a selection into old entries.

Seventy-four additional cases exercise JSON/roles/provenance, malformed private
inputs, altitude requests/cache isolation, real HA setup for both current-weather
providers, forecast services, local attributes, ID-preserving reload/unload,
private unloaded diagnostics and repair from invalid to valid selection.
Both local HA **2026.8.3 and 2026.10.2** pass **1,219 tests and 53 subtests**;
combined line/branch coverage is **99.97375%**, **2,990/2,991 lines** and all
**818/818 branches**. Every strict source/flow gate passes; the new storage
module is also explicitly held at 100%. Thresholds and the existing exclusion policy are unchanged. CI still targets HA 2026.8.3/2026.10.1.

A real read-only probe through the actual encoder/resolver/ICON client on
**23 October 2026 at 18:42:00 UTC** returned 120 hours and daily aggregates for
Kloten postal code, Säntis, Gotthardpass and Albert-Heim-Hütte SAC with explicit
catalogue heights 436/2502/2107/2542 m. The caller retained its session. See
[public-point evidence](evidence/selected_forecast_location_2026-10-23.json) and
[the saved-location contract](SAVED_FORECAST_LOCATION.md). This demonstrates
request/source compatibility, not point-forecast accuracy or operator-HA
acceptance. Translated search/confirmation/reconfiguration and the focused
temporary-HA checks remain open before a candidate. No installation or release.

## Official forecast-location catalogue, identity and search foundation (preceding package)

The first approved POI implementation package adds immutable type/opaque-ID
points, explicit selected-point provenance, atomic Latin1 catalogue validation
and bounded deterministic local search in forecast_locations.py. The source-only
forecast_location_client.py borrows its session, uses existing HTTPS/redirect/
wire-and-decoded body limits, a total download/retry deadline, off-loop parsing,
instance coalescing, original monotonic TTL and an explicit failure/retry boundary.
Invalid refreshes retain last-good hash/time without returning stale success.
No HA setup, persistent config, forecast coordinates, entity IDs or polling change.

Ninety-five new cases cover the public fixture, role/composite/leading-zero
identity, provenance/immutability, schema/CSV/controls, duplicate conflicts,
coordinates/missing heights, candidate ambiguity/ranking/limits, case/accents/
German transliteration, cache expiry, simultaneous loads, failure pause/recovery,
retained metadata, private errors, cancellation, deadline and real shared HTTP
redirect/size/permanent-error/Retry-After behaviour.

Both actual local HA **2026.8.3 and 2026.10.2** pass **1,145 tests and 53 subtests**;
combined line/branch coverage is **99.97243%**, all **768/768 branches**. Every
module exceeds 95%; both new modules have 100% line/branch coverage and are
additionally required at 100% by the existing strict gate. Both environment
gates pass without lower thresholds, new exclusions or dependency/CI changes.
CI remains HA 2026.8.3/2026.10.1, separately from local 2026.10.2.

A real borrowed-session client probe at **17:35:21 UTC on 23 October 2026**
fetched/parsed 828864 bytes, **5816 unique points / 631 POIs**, four identical
duplicate rows and the same content hash as the earlier audit. It checked
public search examples, snapshot cache reuse and caller session ownership.
The [catalogue contract](FORECAST_LOCATION_CATALOGUE.md) links exact source
evidence and distinguishes this foundation from the remaining persisted
selection, height/request/cache semantics, translated HA dialogs and practical
acceptance. No operator HA installation, release, HACS inclusion or complete
quality-tier claim follows. country: CH is already integrated through PR #35.

## Separate hourly/archive precipitation, Recorder and HA coordination

precipitation.py now defines a borrowed-session source client and a pure
completed-hour parser returning start/amount without HA or Recorder imports.
precipitation_recorder.py owns executor parsing, ordered corrections and the
same Recorder projection/metadata/queue result. The real HA coordinator moves
to coordinator.py and composes both. All four availability messages, optional
Recorder startup, hourly/weekly polling and entry-owned cleanup remain.

Source requests retain fixed host/body limits, cp1252, four transient attempts
and empty private errors; cancellation propagates. CSV validation, thirteen-month
calendar lookback, station checks, zero/invalid values and UTC interval conversion
are retained. Source amounts become the same Recorder mean/min/max rows only
in the adapter. Partial file failures preserve valid hours; all-invalid data
never becomes zero or a successful empty import. Real-Recorder tests retain
repeat-import upserts and a corrected hour without duplicate statistics.

Seventeen new cases cover direct source requests without an HA object, both
transport cancellation points, private errors/retry counts, each HA failure
category, partial parser failure and executor cancellation before queueing.
Both actual local HA environments, **2026.8.3 and 2026.10.2**, pass **1,050 tests
and 53 subtests**; combined line/branch coverage is **99.97036%**, all **716/716
branches**. Every module exceeds 95%; source, Recorder adapter and coordinator
have 100% line/branch coverage. Both strict gates pass, with the new adapter
additionally gated at 100%; no exclusions or lower thresholds were introduced.

AST checks retain asset/calendar helpers, all CSV validation, source request/
retry after a private period-attribute adaptation, Recorder metadata/result,
all six previous coordinators, setup functions and runtime fields. The only
parser-boundary projection change moves mean/min/max creation to the adapter.
All seven actual coordinator definitions are now canonical, closing this
bounded inventory. Official location/POI selection remains in the agreed next
release scope before packaging. CI remains HA 2026.8.3/2026.10.1, separately
from actual local 2026.10.2. No manifest/dependency, source/model, identity,
HA installation, release or complete Bronze/Silver/Gold claim changes.

## Separate modelled pollen/AQ and optional UV from HA coordination

OpenMeteoPollenClient in pollen_openmeteo.py borrows its session, owns the
existing bounded AQ/pollen and optional UV requests, and preserves parser,
transient retry and UTC-current-hour data contracts. The actual coordinator
moves to coordinator.py, composing the client and keeping cache, polling and
HA error/logging lifecycle. An empty source error suppresses raw formatted
transport/data chains. Cancellation from AQ or UV and missing-session setup
errors propagate. Optional UV failure cannot invalidate good AQ; valid missing
UV remains unknown. No separate UV cache existed: UV value/status stay in the
same AQ result, with the original coordinate key and 1800-second TTL. Hits do
not extend it. No new poller, client-owned session or source model is added.

Ten new cases cover the direct client without an HA object and the cache TTL
boundary. Existing real entity registration, unknown/unavailable/recovery,
private logging, session ownership, retry, DST, reload/unload and Recorder
regressions pass. Actual local HA **2026.8.3 and 2026.10.2** each pass **1,033
tests and 53 subtests**, **99.96985%** combined line/branch coverage and
**716/716 branches**. Both existing strict gates pass; source client and canonical
coordinator retain full line/branch coverage. Parser, three source helpers and
UV request AST are unchanged. The AQ request only adapts the parser method and
private missing-session class label. Coordinator initialisation, cache/update
flow and UV transition logs retain their AST after documented composition/
source-error/import-name adaptations. All five previously canonical coordinator
classes remain AST-identical.

Setup, typed runtime and HA mocks reference the genuine class. Six of seven
coordinators are now canonical, leaving precipitation parsing/Recorder/coordinator
separation. The operator's next release scope also includes official-catalogue
location/POI selection; neither remaining task is silently deferred. Manifests,
dependencies, languages, released 8.2.0 and the CI matrix are unchanged. CI remains
HA 2026.8.3/2026.10.1. No HA installation, release or completed Silver/Gold claim.

## Scalar forecast sensors for today and tomorrow

The unreleased F1 candidate adds eight numeric sensors to the existing weather
device: native full-day maximum/minimum temperature and precipitation, plus
the highest hourly precipitation probability and all tied peak windows. Pure
calculations live in forecast_summary.py; entities use the existing forecast
coordinator and add no HTTP request. Today's probability uses current/upcoming
hour intervals; native temperature/rain fields retain whole-day meaning.

Missing native fields and incomplete hourly coverage stay unknown. Failed or
stale snapshots are unavailable, with no retained peak times. Local timers
handle hour/midnight/three-hour age boundaries and are cancelled on unload.
UTC interval ends map to preceding hours across Swiss DST boundaries. Normal
numeric states, stable entry-scoped unique IDs, shared device metadata and no
measurement/total state class keep predictions separate from observations and
long-term measured statistics. DE/EN/FR/IT names and the English
[forecast guide](FORECAST_SENSORS.md) explain the user-facing contract.

Forty new cases cover native zero/negative values, missing/invalid fields,
partial probabilities, elapsed/tied peaks, midnight interval assignment,
23-/25-hour days, exact freshness boundaries, real HA registration, failure/
recovery, local-only timer changes, reload identity and unload cleanup. Both
actual local HA environments, **2026.8.3 and 2026.10.2**, pass **1,023 tests and
53 subtests**. Combined line/branch coverage is **99.96978%**, with **716/716 branches**.
Every module exceeds 95%; sensor.py and forecast_summary.py have 100% line/branch
coverage. Both strict gates pass, with forecast_summary.py newly required at 100%. Source model, request,
weather service, observations, warnings, polling/options, manifests, dependencies
and CI matrix remain unchanged. CI still uses HA 2026.8.3/2026.10.1.

A read-only source control at public Zurich city-centre coordinates on
**23 October 2026 at 15:30 UTC** returned 120 rows and all eight values, including
complete current-day/tomorrow probability windows. This demonstrates current
source field availability; it is not acceptance of an installed HA build or a
forecast-accuracy guarantee. No operator HA installation or release was performed.

## Separate the ICON forecast source from HA coordination

Move the actual MeteoSwissForecastCoordinator to coordinator.py, composing
IconForecastClient in forecast.py, and remove the mixed forecast_coordinator.py.
Setup, weather/runtime imports and HA mocks use the canonical class. Preserve
the explicit ICON Seamless request, 120 rolling hours, three transient attempts,
UTC timestamps, Zurich labels, native daily offsets/DST, partial/zero values and
forecast validation. Source failures use an empty domain error with formatted
raw context suppressed; cancellation and missing-session setup errors propagate.

HA retains the default hourly schedule, coordinate-specific v3 cache key,
original 30-minute TTL, five-failure/five-minute pause, fixed availability message
and HA-owned session closure. Weather/forecast-service freshness, optional
startup and once-per-outage/recovery behaviour remain covered by existing HA
regressions. Direct client tests pass only a borrowed mocked session. The
strict coverage checker follows the renamed source without weakening thresholds.
Five of seven actual coordinators are canonical; modelled pollen/AQ/UV and
hourly/archive precipitation remain distinct placement findings. No manifest,
workflow, dependency, location/ID, model selection or released 8.2.0 change.

Both actual local HA environments, **2026.8.3 and 2026.10.2**, pass **983 tests
and 53 subtests**. Combined line/branch coverage is **99.96811%**, with all
**676/676 branches** and every module above 95%; both existing strict gates
pass. The ICON source and canonical coordinator each retain 100% line/branch
coverage. Six new direct-client cases cover explicit model parameters, partial/
zero values, private transport/data errors, cancellation and setup failures.
AST comparisons retain helpers, request, retry and parser bodies, with the
private missing-coordinate exception and method names adapted to the source
boundary; constructor/update lifecycle AST is retained after composing the
client. Existing coordinator classes remain AST-identical. Compilation, standard Ruff E4/E7/E9/F/I checks on changed Python
files, four 101-key catalogues/version 8.2.0, 35 local documentation links/anchors
and diff checks pass. The broader local Ruff profile adds no findings over the
base; its 21 pre-existing test-style findings remain outside this extraction.
CI deliberately remains on HA 2026.8.3/2026.10.1. This is an unreleased proposal;
its exact PR head and GitHub check results remain separate evidence.

## Separate the alternative current-weather client from HA coordination

Move the genuine OpenMeteoDataUpdateCoordinator to coordinator.py and compose
OpenMeteoCurrentClient from the source-only openmeteo.py module. Remove the
mixed openmeteo_coordinator.py module and update setup/config-flow/weather/
runtime imports and test mocks to the actual defining module. Request, WMO
mapping and current/optional-hourly parser bodies retain identical AST. Shared
number/time functions remain in weather_data.py.

The client has no HA coordinator/cache/scheduler dependency and borrows its
session. It maps the existing transport/decoding/data/setup failures to an
empty-message source exception; cancellation propagates. HA retains exactly
the existing cache key and ten-minute TTL, one-hour/ten-minute freshness bounds,
five-failure/five-minute circuit pause, failure counter reset, weather-code
commit and unavailable/recovered messages. Freshness applies equally to new
and cached observations. Source exception text and formatted chains disclose
no coordinates or response. Logger namespace follows the canonical module.

Direct client tests pass no HA object and cover zero/partial values, borrowed
session ownership, transport/malformed-data errors, cancellation and missing
session. Existing retry/HTTP limits, DST, optional preview, stale-cache/circuit,
config-flow, actual entity registration, reload/unload and Recorder tests remain
required. The coverage gate follows the source rename and retains full line/
branch coverage for both source client and coordinator; no exclusion or lower
threshold is introduced. Four of seven genuine coordinators are now canonical;
three source-placement findings remain. See the
[placement review](COORDINATOR_LAYOUT_REVIEW.md) and
[architecture](ARCHITECTURE.md#alternative-open-meteo-current-conditions).
No HA deployment, release, source selection, config migration, entity/statistic
identity or independent ICON forecast change is part of this extraction.

Both local suites pass **977 tests and 53 subtests** on actual HA 2026.8.3 and
2026.10.2, with **99.96803%** combined line/branch coverage and **676/676 branches**.
The five new direct-client cases pass; source client and canonical coordinator
both retain 100% line/branch coverage, every module exceeds 95%, and all strict
gates pass. Source request/parser bodies and the HA cache/circuit update body
are AST-identical after the documented client call/error-type adaptation.
Ruff, compilation, bundled translations/version, 41 local documentation links/
anchors and diff checks pass. CI remains on HA 2026.8.3/2026.10.1.


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
  corrected. Measured pollen, alternative current conditions and ICON forecasts
  now have separate source clients and canonical coordinators, with the shared
  UTC parser retained. Modelled pollen/AQ/UV and precipitation are also separated;
  all seven real coordinators are canonical. Broader rule-specific review and
  Core-brand evidence remain separate from this closed placement inventory.
- The official [coverage rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/)
  applies per module, not only to the aggregate. The
  [UI setup rule](https://contributors.home-assistant.io/core/quality-scale/config-flow/)
  also requires understandable fields and proper data/options separation.

Stable 8.2.0 and its tags stay intact. No HA change, restart, release or repeated
first-install/restore test follows from this source-only cleanup. Bundle any
later accepted runtime changes into a separately reviewed test package.
