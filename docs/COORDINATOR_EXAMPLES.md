# Coordinator examples for contributors

**Guide version:** 1.0 · **Updated:** 23 October 2026
**Scope:** development after PRs #54 and #55, unreleased after stable 8.2.0.
This guide explains existing behaviour; it does not implement location/POI
selection or change polling. Use the [architecture](ARCHITECTURE.md) for the
full contracts and [sensor guide](SENSORS.md) for end-user features.

## Choose the existing data family

All seven concrete coordinator classes are defined in
[coordinator.py](../custom_components/meteoswiss/coordinator.py). Setup creates
entry-owned instances in [typed runtime data](../custom_components/meteoswiss/runtime_data.py).
Seven class definitions do not mean that every entry creates seven different
classes: current-weather providers are alternatives, while hourly precipitation
and its archive use two instances of the same class.

| Class | Example and location role | Refresh schedule in entry setup | Source boundary / consumers |
|---|---|---|---|
| MeteoSwissDataUpdateCoordinator | Latest measured temperature and ten-minute rain at KLO, the observation station. | Configured current-weather interval; default/minimum 600 seconds. | Bounded station metadata/CSV logic remains in this class; weather and observation sensors share its result. |
| OpenMeteoDataUpdateCoordinator | Alternative modelled current conditions at the configured coordinates, not a KLO instrument reading. | Same configured current-weather interval; default/minimum 600 seconds. | OpenMeteoCurrentClient in openmeteo.py; alternative weather/sensor consumers. |
| MeteoSwissForecastCoordinator | ICON forecast and today/tomorrow summaries at forecast coordinates, independently of the observation station. | 3600 seconds. | IconForecastClient in forecast.py; weather.get_forecasts and eight scalar forecast sensors share the data. |
| MeteoSwissAlertsCoordinator | App v3 warnings for the separately configured warning postcode, for example 8302. | 600 seconds. | MeteoSwissAlertsAPI in alerts.py; warning entities use validated alerts/validity windows. |
| MeteoSwissPollenCoordinator | Actual measured pollen at the independently selected pollen station, for example PZH. | 3600 seconds. | MeteoSwissPollenClient in pollen_meteoswiss.py; measured-pollen sensors. |
| OpenMeteoPollenCoordinator | Modelled pollen/AQ and optional UV at forecast coordinates; not measured-pollen station data. | 1800 seconds. | OpenMeteoPollenClient in pollen_openmeteo.py; modelled pollen/AQ/UV entities. |
| MeteoSwissHourlyPrecipitationCoordinator | Official completed-hour precipitation and its archive for the observation station. | now assets hourly; historical/recent assets every seven days, with a thirteen-calendar-month lookback. | Source/parser in precipitation.py, Recorder projection in precipitation_recorder.py; external statistics, no replacement current-hour entity. |

These are attempted-refresh schedules, not a guarantee that the provider has
published a new value. Cache hits do not extend their original expiry. Source
measurement time, retrieval time, cache lifetime and polling interval are
different concepts. Current setup obtains forecast coordinates from HA home
for station entries, or the configured coordinates for Open-Meteo entries;
catalogue-based POI selection is still planned. See
[source/time contracts](ARCHITECTURE.md#sources-and-time) and
[polling/options migration](ARCHITECTURE.md#polling-and-options-migration-unreleased-after-820).

## Example: consume one existing forecast, without another request

A consumer receives the entry instead of creating another client, cache or
poller. This minimal read illustrates ownership, not the full entity lifecycle:

```python
from .runtime_data import MeteoSwissConfigEntry


def forecast_snapshot(entry: MeteoSwissConfigEntry):
    coordinator = entry.runtime_data.forecast_coordinator
    if coordinator is None or not coordinator.last_update_success:
        return None
    return coordinator.data
```

An actual entity must also enforce its applicable freshness/missing-field
contract and register/clean up listeners through HA. See
[weather.py](../custom_components/meteoswiss/weather.py),
[forecast sensor entities](../custom_components/meteoswiss/sensor.py) and
their [real registration/rollover tests](../tests/test_forecast_summary_entities.py).
The eight forecast sensors derive values from the same snapshot. They do not
request ICON once per sensor or turn a missing probability into zero.

## Example: exercise a source without a Home Assistant coordinator

Inside an async test or a bounded developer probe, borrow the caller's existing
verified session. The test harness supplies a mocked session/response; it needs
no HA object to construct the source client:

```python
from aiohttp import ClientSession

from .forecast import IconForecastClient


async def read_icon_source(session: ClientSession):
    client = IconForecastClient(47.451253, 8.579761, session)
    return await client.async_get_data()
```

The example coordinates are the public catalogue record for Kloten postal code 8302,
not private HA-home coordinates. This does not select that point in an existing
entry. The caller owns the session; the client must not close it. Normal HA
entities reuse their coordinator instead of invoking this probe. Source errors
remain payload-free and cancellation propagates. The complete mocked examples
are [ICON client tests](../tests/test_forecast_client.py),
[alternative-current tests](../tests/test_openmeteo_client.py),
[measured-pollen tests](../tests/test_measured_client.py) and
[modelled-pollen/AQ/UV tests](../tests/test_pollen_openmeteo_client.py).

## Example: distinguish missing data from an outage

| Scenario | Expected result and example evidence |
|---|---|
| KLO publishes a trailing incomplete row. | Keep the latest valid observation and its real measurement time; do not mark old data as newly measured. An expired observation eventually fails freshness. See [observation-gap tests](../tests/test_observation_gaps.py). |
| Warning request fails, then recovers. | Warning availability fails and subsequently recovers; the outage is not an empty all-clear. A successfully validated empty feed is different. See [warning/lifecycle tests](../tests/test_reliability.py). |
| Measured pollen contains a valid zero but another species is absent. | Zero remains zero; the missing species remains unknown while a valid source stays available. A source-wide failure is unavailable. See [measured-pollen tests](../tests/test_measured_client.py). |
| AQ is valid but the optional UV request fails. | AQ/pollen stay usable; UV is unavailable. A valid UV response without a number instead yields unknown. UV value/status use the same AQ cache result and original 1800-second TTL. See [UV/TTL tests](../tests/test_pollen_openmeteo_client.py) and [entity semantics](../tests/test_uv_availability.py). |

## Example: import and correct a completed rain hour

An official CSV row ending at 07:00 UTC with 0.4 mm becomes a statistic
starting at 06:00 UTC, with mean/min/max all 0.4. A later valid correction to
0.7 mm updates that same station/hour. The identifier stays
meteoswiss:klo_precipitation_hourly; another station must not share its history.
The source parser returns start/amount; only the Recorder adapter projects it
into HA statistics metadata and queues the import. Queue acceptance is not a
synchronous database-commit confirmation.

If one archive file fails, keep valid files and report a partial import. If
all data is invalid, fail the update and queue nothing. Recorder is optional;
setup creates the two import instances only when it is loaded. Because external
statistics have no entity listener, setup retains entry-owned listeners to keep
these coordinators polling and removes them on unload. Do not add another
background loop. See [setup ownership](../custom_components/meteoswiss/__init__.py),
[source/adapter boundary tests](../tests/test_precipitation_boundaries.py),
[real Recorder semantics](../tests/test_precipitation_semantics.py) and
[source/import regressions](../tests/test_precipitation_sources.py).

## Extending one family

Keep transport/parsing in the relevant source client and HA scheduling,
cache/availability and listener ownership in the real coordinator. Reuse
the HA-owned session, fixed HTTPS destinations and enforced response limits.
Test the affected source contract plus meaningful HA failure/recovery and
reload/unload behaviour. Do not return fabricated zeros or suppress
cancellation, expose coordinate URLs in errors, create duplicate pollers, or
change retained entity/statistic identities to simplify a refactor.

Canonical placement closes one specific layout finding. The station
observation coordinator still contains source-processing logic; seven canonical
definitions alone are not a complete Silver/Gold or architectural-purity claim.
