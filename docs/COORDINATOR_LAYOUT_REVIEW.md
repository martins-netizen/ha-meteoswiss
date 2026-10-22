# Coordinator placement review

**Review version:** 1.0 · **Date:** 22 October 2026
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
| MeteoSwissPollenCoordinator | pollen_meteoswiss.py | Open: measured-pollen parsing/freshness and coordinator lifecycle share a source module. |
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

## Remaining source boundaries

The five findings remain open against the literal HA module-placement rule.
Do not mark it complete merely because these modules have source-specific names.
Do not add lint suppressions, aliases or inheritance-only wrappers to conceal a
definition outside the canonical module. A useful next extraction separates a
source's transport/parser/cache contract from its thin HA coordinator lifecycle,
with the actual coordinator defined in coordinator.py.

Start with a bounded source and compare its class/client contract before and
afterwards. The shared MeteoSwiss reference-time parser currently lives in the
observation coordinator and is imported by measured pollen and precipitation.
Move that genuine shared parser to weather_data.py as a prerequisite where
needed, so a canonical coordinator importing its source client does not create
a cycle. Reuse it without changing UTC parsing or introducing competing copies.

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
