# Coordinator placement review

**Review version:** 1.4 · **Date:** 23 October 2026
**Scope:** unreleased development after stable 8.2.0.

The [HA common-modules rule](https://contributors.home-assistant.io/core/quality-scale/common-modules/)
places DataUpdateCoordinator definitions in coordinator.py and the shared entity
base in entity.py. Distinct source behaviour still needs explicit boundaries.
This review records actual class definitions, not imports or type annotations.

| Coordinator | Current defining module | Finding |
|---|---|---|
| MeteoSwissDataUpdateCoordinator | coordinator.py | Canonical observation coordinator. |
| MeteoSwissAlertsCoordinator | coordinator.py | Moved from binary_sensor.py in this follow-up. |
| MeteoSwissForecastCoordinator | coordinator.py | Extracted ICON source client owns HTTP/parsing; the canonical coordinator retains caching, scheduling and failure/recovery lifecycle. |
| OpenMeteoDataUpdateCoordinator | coordinator.py | Extracted current-condition client handles HTTP/parsing; HA coordinator retains cache, freshness, failure pause and lifecycle. |
| OpenMeteoPollenCoordinator | coordinator.py | Source-only pollen/AQ client includes the separate optional UV request; the real HA coordinator retains current-hour validation, the shared AQ/UV result cache and transition logs. |
| MeteoSwissPollenCoordinator | coordinator.py | Extracted measured-pollen client owns transport, parsing and freshness; HA coordinator owns scheduling and exception translation. |
| MeteoSwissHourlyPrecipitationCoordinator | precipitation.py | Open: official hourly/archive parsing, Recorder import and coordinator lifecycle share a source module. |

There are seven real coordinator classes. MeteoSwissSensor/MeteoSwissWeather
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

Six of seven actual coordinators are now canonical. Only the precipitation
source/importer boundary remains below; this is not full Silver/Gold completion.

## Remaining source boundaries

The precipitation finding remains open against the literal HA module-placement rule.
Do not mark it complete merely because these modules have source-specific names.
Do not add lint suppressions, aliases or inheritance-only wrappers to conceal a
definition outside the canonical module. A useful next extraction separates a
source's transport/parser/cache contract from its thin HA coordinator lifecycle,
with the actual coordinator defined in coordinator.py.

Continue with a bounded source and compare its class/client contract before
and afterwards. The shared timestamp-parser prerequisite is complete; reuse
that implementation rather than introducing competing copies. Keep transport
and parsing in the source client, and define its genuine scheduling/HA lifecycle
in coordinator.py. The next bounded work separates hourly/archive precipitation
source parsing, Recorder import and the actual HA coordinator. Forecast, AQ/UV
and Recorder statistics remain distinct.

Preserve per-host HTTP bounds, request/retry/cancellation budgets, freshness,
partial-value versus source-failure semantics, once-per-outage logs, cache keys
and original TTLs. Retain HA-owned sessions, optional-source startup and polling
listener cleanup. Measured pollen, forecasts, AQ/UV and Recorder imports keep
their separate data contracts and schedules. Validate each extraction through
existing source regressions and real HA registration/reload/unload tests before
combining it into a reviewed candidate.

This review neither changes the live installation nor grants a Bronze/Silver
tier. Stable 8.2.0 remains unchanged; a later accepted package needs its focused
HA acceptance. See the [quality follow-up](QUALITY_PROGRESS_2026-10-22.md) and
[next release plan](NEXT_RELEASE_PLAN.md).
