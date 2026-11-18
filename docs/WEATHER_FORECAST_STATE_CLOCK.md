# Forecast weather state follows the clock

The named forecast weather entity projects the configured point's existing
ICON snapshot. Its registered Home Assistant state now advances at each UTC
model-hour boundary, so its condition, temperature, humidity and wind follow
the current model hour even when no source refresh occurs. The same callback
updates active hourly and daily forecast subscribers; daily projections retain
their existing Swiss calendar-day rules, including midnight and DST.

Each added weather entity owns at most one pending callback. It schedules the
earlier of the next UTC hour and the snapshot's existing three-hour age limit.
A snapshot is valid at exactly three hours and expires immediately after that
boundary. Expiry writes the named entity as unavailable and pushes empty
forecasts to subscribers. Failed, empty, malformed or already expired data
cancels the clock. A later usable source update schedules it again. This
changes when Home Assistant sees the existing projections, not their source,
validation or availability rules.

The callback uses retained coordinator data. It does not fetch data, request a
coordinator refresh, add a poller, or change HTTP requests and source intervals.
It also works with entry polling disabled. Source updates replace the pending
callback. Unload cancels it, and an invalidated callback cannot write state,
notify subscribers or schedule another callback after removal. Reload creates
a new clock for the same existing entity identity.

An entry without an explicit catalogue selection retains its legacy combined
weather interface. That entity receives the same hour and age updates for its
forecast projections, while its numeric current-weather values and overall
availability still belong to the observation coordinator. With an explicit
forecast selection the observation weather entity advertises no forecast
interface and schedules no forecast clock. Observation, warning, measured
pollen and modelled air-quality update semantics are unchanged.

For compatibility, a legacy weather snapshot with no supplied `fetched_at`
still has no invented age limit. Its valid model-hour projections receive the
hour clock only. A supplied but malformed retrieval timestamp is rejected, as
before. Normal runtime snapshots supply a retrieval timestamp. Entity/device
IDs, native units, forecast windows and current-source attribution are
unchanged.

Native regression tests in `tests/test_weather_forecast_state_clock.py` check
registered state and actual subscriber callbacks across hour rollover, Swiss
midnight, strict age expiry, source failure/recovery, source/timer overlap,
disabled polling, unload/reload and canceled callbacks. They also assert that
clock transitions do not call the forecast source.
