# Maintained fork: architecture and data contracts

## Purpose and boundaries

Maintain the existing integration for reliable local use while upstream PRs
remain pending. Preserve `meteoswiss`, config entries, unique IDs, entity IDs,
and Recorder statistic IDs. Upstream source, licence and attribution remain
recognisable. There is no new integration domain and no automatic migration of
users' dashboards. `main` follows upstream; `development` integrates reviewed
local changes. A release is an explicitly tested snapshot of `development`.

## Responsibilities

- API clients download and validate payloads. A transport or decoding failure
  must escape to the coordinator; it must not become an empty successful result.
- Coordinators own refresh intervals, success/failure status and data caching.
  Optional forecasts, alerts, pollen and precipitation imports cannot delay the
  required observation setup. The diagnostic stations map is loaded lazily.
  Optional initial refresh tasks belong to the entry. Recorder is an optional
  ordered dependency: history imports are created only when it is loaded.
- Entities expose values and availability; display translations never determine
  automation logic. The native HA update lifecycle handles unload and reload.
- Home Assistant owns the shared TLS-verified HTTP session. Each request has a
  30-second timeout. An entry must not close a session used by other entries.
- Retries are bounded and limited to transient transport errors, HTTP 408/429
  and server failures. Permanent HTTP errors, invalid JSON/schema and cancellation
  are not retried. A numeric Retry-After above the local delay limit defers the
  operation to a later refresh instead of retrying prematurely.

Entry-specific coordinators and the borrowed session live in typed
`entry.runtime_data` (`MeteoSwissRuntimeData`). Domain-global flags only coordinate
the single shared diagnostic devices. Weather forecast listeners are registered
when the entity is added and removed with that entity. Configuration validates
the chosen observation provider with the same coordinator contract, without
listeners/polling, using HA's shared session and a 30-second total timeout.

## Sources and time

| Data | Source and location | Time semantics |
|---|---|---|
| Observations | Selected SwissMetNet station, or configured Open-Meteo location | `last_update` is measurement time, aware UTC. Missing timestamps, age over one hour or more than ten minutes in the future fail the update. |
| Weather forecast | MeteoSwiss ICON Seamless via Open-Meteo at HA location (explicit coordinates for Open-Meteo entries) | Unix seconds from provider become aware UTC ISO strings. `local_date` is the Europe/Zurich date; `fetched_at` is retrieval time, not model issuance time. |
| Warnings | MeteoSwiss App API for configured postal code | UTC validity windows; active, upcoming and outlook remain separate. |
| Measured pollen | Selected MeteoSwiss pollen station | UTC hourly interval-end measurement time; accepted age up to four hours and future skew up to ten minutes, independently of weather observations. Checked on refresh. |
| Pollen/AQ forecast | Open-Meteo for forecast location | Request Unix seconds and select the actual current hour, never midnight or the next non-null future value. Missing data stays missing; cached prior-hour values cannot extend this window. |
| Hourly precipitation | Official station CSV, external Recorder statistics | Interval-end times are shifted to interval starts in UTC; IDs remain unchanged. |

Trailing partial station rows (for example rain=0 while instantaneous weather
is still blank) do not replace the latest measured observation row. The original
measurement time and one-hour age limit remain authoritative. Missing individual
parameters in a measured row stay missing. Sensors expose `measurement_time`,
`source_status` and `pending_rows`; see `docs/USAGE.md`. No historic records are
fabricated to fill observation gaps.

Station CSVs use the provider's Windows-1252 encoding and must identify the
selected station on every row. Non-finite individual measurements stay missing;
an all-invalid measured row fails the update. Sparse snow/foehn fallback keeps
its existing limited scope and skips invalid older values. The running-hour
rain total deduplicates by interval timestamp (latest valid value wins), ignores
non-finite/negative amounts and is missing if no valid current-hour interval
exists. A measured zero remains zero; equal amounts in distinct intervals still
add up. Its station observation timestamp is not an aggregate completeness claim.

The separate hourly precipitation importer validates station, finite
non-negative totals and completed whole-hour UTC interval ends before shifting
them to Recorder interval starts. Existing statistic IDs, units and mean
metadata remain unchanged. Historical/recent/now ordering retains later valid
corrections for overlapping hours. Transient metadata/download errors receive
the bounded transport retries; malformed data is not retried. Valid subsets of
an archive can still be queued if another file fails, with `partial_import`
and `failed_downloads` in coordinator results. All-invalid or all-failed data
fails without queuing empty statistics. A real in-memory Recorder test confirms
repeat-import upserts and correction of an existing hour without duplicate rows.

HGT 12/20 retains its existing threshold and reference temperature. Missing,
boolean and non-finite temperatures do not become zero heating demand or
contaminate totals. Tests cover daily boundaries and the existing season helper
functions; no new seasonal history collection or HA entities are introduced.

Both pollen clients require at least one finite non-negative current tracked
concentration (integer counts for measured pollen). Zero is valid. A partial
response keeps missing fields unknown; no valid current concentration fails
the update. Measured pollen also validates station identity and measurement
timestamp syntax and freshness. Its existing provider timestamp/history format
is retained. The hourly source has its own four-hour maximum age and ten-minute
future tolerance, with inclusive boundaries. The age is recalculated from the
measurement time on every refresh, never from fetch time. Repeated cached data
cannot renew the measurement's freshness. There is no separate expiry timer
between polls: the displayed timestamp remains authoritative for automations.

This conservative integration policy allows hourly aggregation, the documented
[20-minute pollen publication cycle](https://opendatadocs.meteoswiss.ch/changelog/1.2.0)
and [up to two-hour asset caching](https://opendatadocs.meteoswiss.ch/general/download).
It is not a provider SLA. MeteoSwiss reference times are UTC and hourly times
mark interval ends; neither local timezone nor DST changes their age. A stale
or implausibly future response fails locally without a transport retry. Normal
coordinator unavailability/recovery then applies only to measured pollen.

Forecast pollen, AQ/UV and measured-pollen sensors use CoordinatorEntity for
subscription, unavailability and removal. Values are read directly from current
coordinator data, including initial addition; a source failure retains prior
data internally while exposing unavailable states. A valid later response
recovers automatically. UV is a separate optional request: a failure makes UV
unknown without discarding valid pollen/AQ. UV alone cannot rescue an invalid
primary feed. Coordinator transition logs replace repeated client error logs;
optional UV logs contain only the exception class, never a coordinate URL.

Forecast rows contain `datetime`, `local_date`, `fetched_at`, `source`,
`weather_code`, `is_day`, `condition`, measurements and optional native daily
aggregates. Producer and consumer use `weather_data.py` for time/condition
normalisation. The two hours repeated at autumn DST remain distinct. Daily
labels respect Open-Meteo's returned fixed UTC offset; native daily aggregates
are provider buckets and are not claimed to be recalculated 23/25-hour local
measurement days. Missing aggregates can fall back to available hourly values;
for today these may cover only the remaining hours.

The ICON forecast client separates transport retries from response validation.
It requires structured hourly/daily objects, list-valued series and nonempty,
strictly ordered timestamps. The rolling horizon must extend beyond now and
start no more than one hour ahead, with at least one finite temperature in an
unexpired hour. This is a payload-consistency guard for the requested rolling
forecast, not a model-issuance-time guarantee. Missing daily data can still
fall back to hourly aggregates. Invalid individual numbers stay missing;
valid zero values and negative temperatures are retained. Humidity and
probability are bounded to 0–100, bearings to 0–360, and negative precipitation,
snowfall or wind speeds are missing. Unknown codes cannot manufacture clear sky.

Only validated forecasts enter the versioned 30-minute cache. Transient
transport failures retry at most three times; malformed data is not retried.
Five failed refreshes retain the existing five-minute circuit-breaker pause.
The weather entity continues exposing valid observations during a forecast
failure, while its hourly/daily forecast services return empty lists. A valid
refresh restores forecasts automatically. Coordinator transition logs replace
duplicate client errors; the client logs neither the coordinate URL nor raw
HTTP exception chains, including at debug level. Tests exercise the registered
weather entity through both HA forecast services and verify unload cleanup.

Failed or more than three-hour-old forecasts are not used as current conditions.
Numeric temperature or zero rain does not establish a clear/partly cloudy sky.
The positive station-rain fallback is a precipitation-interval estimate, not a
separate cloud observation. Daily HGT 12/20 remains explicitly a forecast.

## Warnings and safety-dependent consumers

Only a valid, successfully decoded response without warnings means no warnings.
HTTP errors, exhausted retries and malformed non-empty warning lists mark the
coordinator unavailable. Existing data is retained by HA and accompanied by
`data_status: unavailable` and the unchanged `last_successful_update`; its
absence must never silently mean no danger. Unknown numeric warning types stay
visible, retaining their code. Existing English text attributes are retained
for compatibility; numeric types/levels are the automation contract.

An automation protecting an awning must check source availability and freshness
as well as the absence of relevant alerts. An unavailable warning sensor is not
permission to open. The exact reaction (block opening, notify, or close) belongs
to the house's automation policy and must be tested on the actual installation.
This PR does not modify device actions or deployed automations.

## Localisation

`translations/{en,de,fr,it}.json` supplies all UI labels. English is the fallback.
No Core-only placeholders or strings.json build step is required. Warning type,
level and feed-status labels live under native `selector` keys. The catalogue
is loaded once in an executor and exposed as `warning_labels` on warning
entities. A reusable dashboard template selects the viewing user's language;
it does not copy the dictionary into each dashboard. Provider free text is
preserved as received, without claiming it is translated.

See `examples/button-card-warnings.yaml`. Existing local dashboard translations
stay in place until a separately verified adoption of the common template.
Do not rename established entities during this change.

## Verification and remaining limits

Tests cover warning failure/recovery, invalid payloads, bounded retries,
cancellation, HA-owned sessions, stale observations, current-hour AQ data,
registered pollen/AQ entity states and unload, forecast service failure/recovery,
contracts, DST and translation coverage. Both pollen clients and the ICON
forecast client, hourly precipitation importer and HGT utilities have full
line/branch coverage, enforced in CI alongside config flow. The station client
must retain at least 95% line and branch coverage, and the whole-integration
floor is 80%; Silver remains pending.
CI runs minimum and current
HA test environments plus Hassfest and CodeQL. Passing CI is not a live-house
acceptance test. The `quality_scale: platinum` claim inherited from upstream is
removed; no HA quality certification is asserted.

Inactive camera/SLF/hydrology placeholders remain outside the runtime platform
list. Removing them or adding new providers is a separate scoped change.
