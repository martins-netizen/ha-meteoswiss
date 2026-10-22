# Coordinator placement review

**Review version:** 1.1 · **Date:** 22 October 2026
**Scope:** unreleased development after stable 8.2.0.

The [HA common-modules rule](https://contributors.home-assistant.io/core/quality-scale/common-modules/)
places DataUpdateCoordinator definitions in coordinator.py and the shared entity
base in entity.py. Distinct source behaviour still needs explicit boundaries.
This review records actual class definitions, not imports or type annotations.

| Coordinator | Current defining module | Finding |
|---|---|---|
| MeteoSwissDataUpdateCoordinator | coordinator.py | Canonical observation coordinator. |
| MeteoSwissAlertsCoordinator | coordinator.py | Moved from binary_sensor.py in this follow-up. |
| MeteoSwissForecastCoordinator | forecast_coordinator.py | Open: ICON forecast fetching/parsing/cache and coordinator lifecycle share a source module. |
| OpenMeteoDataUpdateCoordinator | openmeteo_coordinator.py | Open: alternative current-condition client and coordinator share a source module. |
| OpenMeteoPollenCoordinator | pollen_coordinator_openmeteo.py | Open: modelled pollen/AQ and the independently cached UV request share a source coordinator. |
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

## Remaining source boundaries

The four findings remain open against the literal HA module-placement rule.
Do not mark it complete merely because these modules have source-specific names.
Do not add lint suppressions, aliases or inheritance-only wrappers to conceal a
definition outside the canonical module. A useful next extraction separates a
source's transport/parser/cache contract from its thin HA coordinator lifecycle,
with the actual coordinator defined in coordinator.py.

Continue with a bounded source and compare its class/client contract before
and afterwards. The shared timestamp-parser prerequisite is complete; reuse
that implementation rather than introducing competing copies. Keep transport
and parsing in the source client, and define its genuine scheduling/HA lifecycle
in coordinator.py. The alternative current-condition client is a suitable next
bounded extraction; forecast, AQ/UV and Recorder statistics remain distinct.

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
