# Coordinator placement review

**Review version:** 1.7 · **Updated:** 25 October 2026
**Scope:** the released 8.3 runtime. The completed extraction sections below
retain the sequence and evidence of the original reviews; they are not new
architecture work to repeat. See [current release status](RELEASE_READINESS.md).

The [HA common-modules rule](https://contributors.home-assistant.io/core/quality-scale/common-modules/)
places DataUpdateCoordinator definitions in coordinator.py and the shared entity
base in entity.py. Distinct source behaviour still needs explicit boundaries.
This review records actual class definitions, not imports or type annotations.

| Coordinator | Current defining module | Finding |
|---|---|---|
| MeteoSwissDataUpdateCoordinator | coordinator.py | Canonical observation coordinator. |
| MeteoSwissAlertsCoordinator | coordinator.py | Moved from binary_sensor.py in this follow-up. |
| MeteoSwissForecastCoordinator | coordinator.py | Extracted ICON source client owns HTTP/parsing; the canonical coordinator retains caching, scheduling and failure/recovery lifecycle. |
| MeteoSwissStationConditionCoordinator | coordinator.py | Optional station-local current model code; station_condition.py owns bounded HTTP/parsing and validity. The canonical coordinator owns catalogue resolution, caching and scheduling. |
| OpenMeteoDataUpdateCoordinator | coordinator.py | Extracted current-condition client handles HTTP/parsing; HA coordinator retains cache, freshness, failure pause and lifecycle. |
| OpenMeteoPollenCoordinator | coordinator.py | Source-only pollen/AQ client includes the separate optional UV request; the real HA coordinator retains current-hour validation, the shared AQ/UV result cache and transition logs. |
| MeteoSwissPollenCoordinator | coordinator.py | Extracted measured-pollen client owns transport, parsing and freshness; HA coordinator owns scheduling and exception translation. |
| MeteoSwissHourlyPrecipitationCoordinator | coordinator.py | Source-only hourly/archive client and amount parser in precipitation.py; explicit Recorder projection/import in precipitation_recorder.py; genuine HA coordinator composes both. |

There are eight real coordinator classes. MeteoSwissSensor/MeteoSwissWeather
are coordinator-backed entities, not additional coordinator definitions. The
shared station-catalogue loader is a locked metadata service, not a
DataUpdateCoordinator. Shared entity bases already live in entity.py.

## Completed platform dependency removal

Move the complete warning coordinator definition to coordinator.py; setup and
typed runtime data now import it directly. binary_sensor.py keeps an import of
the same class for its entity annotation and compatibility with the prior
import path. There is no duplicate definition or wrapper class. The moved class
has identical AST, signature, update interval, warning-label handling, exceptions,
last-success timestamp and close behaviour. Its logger now belongs to the
coordinator module. Actual warning failure/recovery/privacy, registered entity,
reload/unload and Recorder tests remain required; import placement alone is not
proof of runtime correctness.

## Completed measured-pollen client separation

MeteoSwissPollenClient in pollen_meteoswiss.py has no HA coordinator/runtime or
UpdateFailed dependency. It borrows the supplied aiohttp session, fetches the
same bounded hourly CSV, decodes cp1252 and returns the same seven species,
source/time metadata, partial/zero values and 24-row history. It retains the
four-hour maximum age and ten-minute future skew. Its payload-free transport
and invalid-data exception messages expose no raw response, station identifier or URL.
Cancellation and the missing-session setup error still propagate.

The actual MeteoSwissPollenCoordinator definition now lives in coordinator.py.
It composes the client and translates its two source failures to the existing
UpdateFailed messages, with the same 3600-second default and optional HA startup.
It is not a wrapper/subclass of a coordinator hidden in the source module.
Setup, runtime typing and fixtures use the canonical class. Its logger follows
the coordinator module; per-outage/recovery and privacy contracts remain tested.

The shared provider timestamp parser is now parse_reference_timestamp in
weather_data.py, used by observation, measured-pollen and precipitation readers.
The observation module keeps its previous private import alias, not a second
parser implementation. Parsed UTC values and naive-versus-offset behaviour are
unchanged. AST comparison confirms the CSV/time parser bodies and count parser,
after documented identifier renames. The source module no longer imports the
HA coordinator, so canonical composition introduces no circular dependency.

The four new direct-client tests supply only a borrowed mocked aiohttp session;
they pass no HomeAssistant instance/coordinator to the client. Existing provider fixtures,
Recorder and registered entity/reload tests continue to exercise the HA side.
This is an internal source boundary, not a separately published Python package
or a claim that the integration package can be imported without HA installed.

## Completed alternative current-weather client separation

OpenMeteoCurrentClient in openmeteo.py owns the unchanged bounded request,
transient retry policy, WMO descriptions and current/optional-hourly parsers.
It accepts coordinates and a borrowed aiohttp session, with no HomeAssistant,
DataUpdateCoordinator, UpdateFailed, cache, polling task or session ownership.
Source failures become an empty-message OpenMeteoCurrentError with the raw
exception chain suppressed when formatted. Cancellation still propagates.
This remains an internal integration boundary, not a standalone Python package.

The genuine OpenMeteoDataUpdateCoordinator is defined in coordinator.py and
composes that client. It retains the 600-second minimum, coordinate-specific
openmeteo:v2 cache key and original ten-minute TTL. It validates one-hour age
and ten-minute future skew on both fetched data and cache hits before accepting
values, resets failures only on success, and keeps the five-failure/five-minute
circuit pause. Session closure remains HA-owned. Logger namespace follows the
canonical coordinator module; failure/recovery messages and privacy are retained.

The old openmeteo_coordinator.py source/coordinator mixture is removed. Setup,
config-flow validation, weather typing, runtime typing and test mocks use the
canonical class, rather than a re-export or inheritance-only wrapper. Source
parser tests use the composed client. Direct client tests pass only a mocked
borrowed session and cover zero/partial values, source errors, cancellation and
missing session. Existing cache/freshness/HA registration and recovery tests
continue to apply. Request and parser bodies are AST-identical; ICON forecasts,
AQ/UV, measured pollen and Recorder statistics retain their independent sources.

## Completed ICON forecast client separation

IconForecastClient in forecast.py owns the same bounded Open-Meteo request,
explicit meteoswiss_icon_seamless model, three-attempt transient retry and
rolling-hourly/native-daily parser. It borrows its session and takes no HA
coordinator/runtime, cache or scheduler. Rolling coverage, finite/partial/zero
values, UTC timestamps, Zurich date labels and daily fixed-offset/DST handling
are retained. Missing coordinates and provider/data failures become an empty
IconForecastError with raw traceback context suppressed. Cancellation and the
existing missing-session RuntimeError remain unhandled setup/cancellation cases.

The genuine MeteoSwissForecastCoordinator definition now lives in coordinator.py
and composes the client. HA retains the same constructor/default interval,
forecast:v3:icon-seamless coordinate key, original 30-minute TTL, five-failure/
five-minute pause, source marker and borrowed-session close contract. Cache
hits do not renew the TTL. Existing consumer freshness/forecast-service rules,
optional source startup and once-per-outage/recovery logs remain required.
The old forecast_coordinator.py module is removed; imports and HA mocks target
the actual defining module, not an alias or wrapper. Logger namespace follows
its owning module without exposing coordinates, payloads or raw error chains.

Direct source tests pass only a borrowed mocked session and exercise explicit
model parameters, zero/partial values, private failures, cancellation and setup
errors. Existing request, DST, daily aggregates, cache expiry, circuit recovery,
registered forecast services and reload/unload tests remain in place. Request
and parser ASTs are retained apart from the documented client method name and
HA-to-source exception type adaptation. At that extraction step five of seven
classes were canonical. The modelled-pollen extraction below raises this to six.

## Completed modelled pollen/AQ and optional UV client separation

OpenMeteoPollenClient in pollen_openmeteo.py owns the original two bounded
requests and current-hour parser. It takes coordinates and a borrowed session,
with no HA object, coordinator, cache, timer or session ownership. AQ/pollen
retains four transient attempts, the five-day hourly request, UTC seconds,
Swiss labels and zero/partial-value handling. An invalid AQ feed still fails
before requesting UV; optional UV cannot rescue it. UV retains its separate
HTTP request and independent success flag: a failed request is unavailable,
while a valid response missing a numeric value remains available/unknown.
Cancellation from either request propagates. Missing session remains RuntimeError.
Source transport/data failures expose an empty OpenMeteoPollenError with the
raw formatted exception chain suppressed; the coordinator maps it to the same
fixed HA failure message.

The genuine OpenMeteoPollenCoordinator now lives in coordinator.py. It keeps
the constructor/default/minimum interval, entry-owned lifecycle, coordinate key
pollen:<latitude>,<longitude>, original 1800-second TTL, current-hour validation
and invalid-cache removal. UV availability transitions remain logged once by HA.
UV data/status are cached atomically with the AQ result; there was no separate
UV cache or independent UV expiry to preserve. Cache hits do not renew TTL.
Neither a new UV cache nor a new polling schedule is introduced.

The old mixed module is removed. Setup, runtime typing and HA mocks reference
the actual canonical class. Its logger follows the coordinator module. Parser,
source helpers and optional UV request retain identical AST; the main request
only adapts the parser name and private missing-session class label. Coordinator
initialisation is identical after client composition, as are transition logs
and cache/update flow after source-call/error/import-name adaptations. Ten new
cases include direct borrowed-session requests without an HA runtime, private
failures, both cancellation points, missing session, invalid AQ, optional UV
failure and a cache hit that cannot postpone expiry.

At that step six of seven coordinators were canonical. The precipitation
source/importer extraction below closes the final inventory finding.

## Completed hourly/archive precipitation boundaries

precipitation.py now defines MeteoSwissHourlyPrecipitationClient, the unchanged
asset/calendar helpers and a pure parser returning UTC interval start plus
amount in mm. It imports neither HA nor Recorder. The original station metadata
and CSV requests retain four transient attempts, the fixed OGD host, cp1252 and
separate current/archive byte limits. Source methods suppress raw transport/
data exception chains behind an empty PrecipitationSourceError; cancellation
propagates. The session is borrowed, with no new cache, scheduler or close call.

precipitation_recorder.py defines MeteoSwissPrecipitationImporter, an explicit
HA/Recorder adapter. It runs pure CSV parsing through HA's executor, merges
valid files in the configured period order and retains later valid corrections
without duplicates. Lookback remains thirteen calendar months for the archive.
It projects source amounts to the same Recorder mean/min/max entries and retains
statistic ID, arithmetic mean type, has_sum=false, unit class, mm and name.
A valid subset remains queueable when another file fails. Missing assets,
all-invalid data and queue failure do not report success or manufacture zeros.
The returned import/partial/failure metadata is unchanged.

The genuine MeteoSwissHourlyPrecipitationCoordinator now lives in coordinator.py
and composes source plus importer. All four HA failure messages remain distinct,
with private formatted chains. Hourly and weekly schedules, optional Recorder
dependency, startup, keepalive polling and unload cancellation remain unchanged.
There is no old-module alias or inheritance-only wrapper. Both source and Recorder
adapter have strict 100% line/branch gates, alongside the canonical coordinator.

AST comparisons retain asset/calendar helpers, all CSV validation, source
requests/retry after the period-attribute adaptation, Recorder metadata/result,
all six earlier coordinators, setup functions and runtime fields. Source parser
output changes only at its boundary: amount replaces Recorder mean/min/max;
the adapter supplies the same old projection. Existing real-Recorder regressions
confirm repeated upserts and correction without duplicate hours. Seventeen new
cases cover direct borrowed-session requests, both transport cancellation points,
private errors/retry budgets, four HA failure categories, partial parser failure
and executor cancellation before queuing.

All seven original coordinator definitions became canonical at this milestone.
The station-condition follow-up adds the eighth class. Canonical placement
does not establish every Bronze/Silver/Gold requirement.

## Remaining architecture and release limits

Keep independent data-family timing, freshness, per-host HTTP bounds, original
cache TTLs and HA-owned sessions. No suppression, coverage exclusion or lowered
threshold replaces an architecture boundary. Later changes must retain source
and registered entity/Recorder lifecycle evidence.

The agreed next feature release still includes official-catalogue location/POI
selection. Its stored location, altitude, migration and translated UI contracts
remain separate work before packaging and focused HA acceptance. This inventory
does not change the running HA or grant an official quality tier. See the
[quality evidence](QUALITY_PROGRESS_2026-10-22.md) and
[next release plan](NEXT_RELEASE_PLAN.md).
