# Maintained fork: architecture and data contracts

## Purpose and boundaries

Maintain an independent community fork with reviewed fixes, its own releases
and [HACS catalogue admission](HACS_ACCEPTANCE.md#hacs-catalogue-admission).
The contracts below describe the released 8.3 runtime. Preserve `meteoswiss`, config entries, unique IDs, entity IDs,
and Recorder statistic IDs for retained entities. The legacy forecast-only
season-HGT entity is explicitly retired rather than presented as a measured
accumulated total; see the migration guide. Upstream source, licence and attribution remain
recognisable. There is no new integration domain and no automatic migration of
users' dashboards. `main` follows upstream; `development` integrates reviewed
local changes. A release is an explicitly tested snapshot of `development`.

## Responsibilities

See the [coordinator examples](COORDINATOR_EXAMPLES.md) for the eight concrete
classes, entry-owned instances, polling and practical consumer/failure examples.

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

## Scalar forecast projections

The eight forecast sensors reuse the existing ICON coordinator; they add no
HTTP request, cache or independent poller. Pure calculations in
`forecast_summary.py` select native whole-day temperature/rain fields or complete
preceding-hour probability intervals. Target dates use Europe/Zurich; UTC hour
boundaries retain repeated DST intervals. Missing fields yield unknown, while
failed/stale snapshots yield unavailable. Entity-owned point timers update hour,
midnight and three-hour retrieval-age boundaries and are cancelled on unload.
Forecast sensors have no measurement/total state class and retain numeric states
with bounded peak-window attributes. See [the forecast guide](FORECAST_SENSORS.md).

## Distinct forecast display

The [display contract](FORECAST_DISPLAY.md) separates the existing observation
weather/device from a location-labelled forecast group. DeviceInfo translation
keys render the selected catalogue name or an explicit base/invalid-location
label in all four UI languages. The group reuses the existing calculated/HGT
device identifier; eight scalar registry records move to it without changing
unique/entity IDs. HGT remains on that same device. HA retains user names,
areas and entity options; no registry purge or location-specific device is added.

A new stable `_forecast_weather` unique ID projects only the existing ICON
snapshot, including its current model hour. It does not borrow any observation
coordinator fields and adds no polling/request/cache. Shared native forecast
projection/subscriber methods live in MeteoSwissForecastWeatherBase. Missing
fields/current hours remain absent/unknown, failed/stale data unavailable.
The original weather entity keeps its ID and current source. Once a catalogue
point is selected (or invalid), it advertises no forecast features; without a
selection its legacy combined interface remains for compatibility. Forecast
cards/actions for a selected point therefore need the new entity target.
Source requests, coordinates, warnings, AQ/pollen/UV and Recorder contracts are
unchanged. Tests cover a real HA registry with old IDs, translated names,
independent source failures and reset/reload, not just constructed metadata.

## Sources and time

### Station-local weather condition

`station_condition.py` owns the small ICON current-code/daylight HTTP request,
mapping and interval validation. The eighth canonical class,
`MeteoSwissStationConditionCoordinator` in `coordinator.py`, resolves station
catalogue coordinates/height, caches by that point, schedules ten-minute/end-of-
interval refreshes and owns source failure/recovery. The role is optional in
typed runtime data; setup registers its weather listener before a background
initial refresh, and entry unload cancels pending work and listeners.

The existing station weather entity keeps numeric observations and its IDs.
Only the qualitative condition can come from this model role, with explicit
provenance attributes and provider attribution. Observation availability remains
independent. A condition outage does not borrow POI forecasts or invoke the
old rain heuristic. Open-Meteo current entries retain their existing source and
have no extra condition coordinator. See the [user/source contract](STATION_WEATHER_CONDITION.md).

| Data | Source and location | Time semantics |
|---|---|---|
| Observations | Selected SwissMetNet station, or configured Open-Meteo location | `last_update` is measurement time, aware UTC. Missing timestamps, age over one hour or more than ten minutes in the future fail the update. |
| Weather forecast | MeteoSwiss ICON Seamless via Open-Meteo at an explicitly saved catalogue point, otherwise legacy HA/configured base coordinates | Unix seconds from provider become aware UTC ISO strings. `local_date` is the Europe/Zurich date; `fetched_at` is retrieval time, not model issuance time. |
| Warnings | MeteoSwiss App API for configured postal code | UTC validity windows; active, upcoming and outlook remain separate. |
| Measured pollen | Selected MeteoSwiss pollen station | UTC hourly interval-end measurement time; accepted age up to four hours and future skew up to ten minutes, independently of weather observations. Checked on refresh. |
| Pollen/AQ forecast | Open-Meteo for the existing base location, independent of a selected weather-forecast POI | Request Unix seconds and select the actual current hour, never midnight or the next non-null future value. Missing data stays missing; cached prior-hour values cannot extend this window. |
| Hourly precipitation | Official station CSV, external Recorder statistics | Interval-end times are shifted to interval starts in UTC; IDs remain unchanged. |

Trailing partial station rows (for example rain=0 while instantaneous weather
is still blank) do not replace the latest measured observation row. The original
measurement time and one-hour age limit remain authoritative. Missing individual
parameters in a measured row stay missing. Sensors expose `measurement_time`,
`source_status` and `pending_rows`; see `docs/USAGE.md`. No historic records are
fabricated to fill observation gaps.

Station CSVs use the provider's Windows-1252 encoding and must identify the
selected station on every row. Their decode, row selection and numeric parsing
run in HA's executor after the bounded download, rather than blocking its event
loop. The observation adapter remains in the legacy coordinator class; the
canonical placement does not claim every source is fully extracted. Non-finite individual measurements stay missing;
an all-invalid measured row fails the update. Sparse snow/foehn fallback keeps
its existing limited scope and skips invalid older values. The retained rain
sensor exposes one latest measured ten-minute amount, its end time and a
600-second interval. Open-Meteo instead retains its provider-defined model
interval and has a separate translation key; the unique key remains stable.
There is no locally derived current-hour sum: an incomplete set of published
intervals must not masquerade as a complete hourly amount. A setup/reload
migration removes only the exact retired unique ID for the current entry,
without touching other entries, helpers or purging Recorder statistics.

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
recovers automatically. UV is a separate optional request: a failed response
makes only UV unavailable. A current, structurally valid response with a missing
number makes UV unknown. Its Unix timestamp must be no later than now and less
than one hour old. UV alone cannot rescue an invalid primary feed. Private
coordinator transition logs replace repeated raw source errors and never include
a coordinate URL. UV data/status remain atomic in the existing AQ cache.

Forecast rows contain `datetime`, `local_date`, `fetched_at`, `source`,
`weather_code`, `is_day`, `condition`, measurements and optional native daily
aggregates. Producer and consumer use `weather_data.py` for time/condition
normalisation and finite-number validation. The two hours repeated at autumn DST remain distinct. Daily
labels respect Open-Meteo's returned fixed UTC offset. Its native daily bucket
is used only when its actual start and end match both Swiss midnights. Otherwise
the 8.3 source derives that mismatched day from complete
Swiss hourly coverage in the same response. Temperature samples cover local
midnight inclusive to the next midnight exclusive; precipitation/probability
buckets end after the first midnight and include the next one. UTC instants
keep both repeated autumn hours. Native aligned aggregates remain preferred;
no fallback fills a missing aligned native field. Scalars, HGT and weather share
the normalized result and its aggregation provenance. The one request adds
25 past hours, validates at most 145 rows and projects only the current/future
120 hours; no new coordinator, cache or polling schedule is introduced.

IconForecastClient in forecast.py separates transport retries from response
validation; the genuine MeteoSwissForecastCoordinator in coordinator.py composes
it. The old forecast_coordinator.py module is removed. The client borrows the
HA-owned session and has no coordinator/cache/scheduler dependency. HA retains
the same interval, versioned coordinate cache/TTL and five-failure/five-minute
pause. Missing-session setup errors and cancellation still propagate; other
source failures have an empty-message IconForecastError with raw context
suppressed, translated to the existing UpdateFailed message by the coordinator.
It requires structured hourly/daily objects, list-valued series and nonempty,
strictly ordered timestamps. The rolling horizon must extend beyond now and
start no more than one hour ahead, with at least one finite temperature in an
unexpired hour. This is a payload-consistency guard for the requested rolling
forecast, not a model-issuance-time guarantee. Missing daily data can still
fall back to hourly aggregates. Invalid individual numbers stay missing;
valid zero values and negative temperatures are retained. Humidity and
probability are bounded to 0–100, bearings to 0–360, and negative precipitation,
snowfall or wind speeds are missing. Unknown codes cannot manufacture clear sky.

A saved catalogue selection is decoded offline and affects ICON forecasts only.
The [saved-location contract](SAVED_FORECAST_LOCATION.md) defines exact schema,
height/downscaling, privacy and invalid-selection recovery. Known altitude is
sent explicitly and included in a height-aware cache key; missing altitude and
legacy entries retain automatic DEM and the old coordinate key. Current/AQ/
pollen base coordinates and the warning postcode remain separate. A selected
forecast cannot supply the existing weather entity's current-condition fallback.

Only validated forecasts enter the versioned 30-minute cache. Transient
transport failures retry at most three times; malformed data is not retried.
Five failed refreshes retain the existing five-minute circuit-breaker pause.
The weather entity continues exposing valid observations during a forecast
failure. Supported hourly/daily forecast projections return empty lists. A valid
refresh restores forecasts automatically. Coordinator transition logs replace
duplicate client errors; the client logs neither the coordinate URL nor raw
HTTP exception chains, including at debug level. Tests exercise the registered
weather entity through both HA forecast services and verify unload cleanup.

Failed or more than three-hour-old forecasts are not used as current conditions.
Numeric temperature or zero rain does not establish a clear/partly cloudy sky.
The positive station-rain fallback is a precipitation-interval estimate, not a
separate cloud observation. Daily HGT 12/20 remains explicitly a forecast.

## Native weather entity and forecast subscribers

Current temperature, pressure and wind use HA's `native_temperature`,
`native_pressure` and `native_wind_speed` properties. HA converts them, and
native forecast fields, into the user's configured units. Public state/service
keys remain `temperature`, `pressure`, `wind_speed` and forecast `templow`.
Humidity and wind bearing retain valid zero; failed observations supply no old
current attributes while HA retains the accepted coordinator data for recovery.
Entity/config-entry IDs and device identifiers are unchanged.

A forecast-coordinator callback updates the weather condition and schedules
`async_update_listeners` for hourly/daily subscribers with an entry-owned task.
Existing HA WebSocket subscribers receive updated forecasts, an empty list on
forecast failure, and new values on recovery without resubscribing. Unload
removes both observation and forecast coordinator listeners. A forecast failure
does not mark valid station measurements unavailable.

The hourly projection selects usable temperatures in the current hour plus
23 hours; completed intervals and past days are not returned as upcoming data.
Daily buckets follow Europe/Zurich dates, recomputed from aware UTC timestamps,
with at most five current/future calendar days. The first 12:00-14:00 local
entry represents the day's condition/wind, or the first available hour if that
window is absent. Native provider maxima/minima and precipitation/probability
aggregates take priority, including valid zeros. Fallback extrema require
all instantaneous temperatures in [local midnight, next midnight). Rain and
probability require every preceding-hour bucket in (midnight, next midnight],
including the next day's 00:00 row and excluding the previous day's last bucket.
Missing, invalid or gapped hours leave only the affected aggregate unknown.
Physical UTC-hour sets handle 23/25-hour days and repeated local times. The
source withholds fixed-offset native buckets that cover a different period;
it does not silently relabel or rescale them.

Failed/malformed or older-than-three-hour fetched forecasts are suppressed;
metadata more than ten minutes in the future is rejected. Legacy rows without
retrieval metadata retain compatibility, with their actual interval/day still
filtered. Weather projection logs no raw payload or coordinates. Numbers and
boolean/time guards live in `weather_data.py` and are reused by both weather
clients, avoiding divergent copies of the validation rules.

## Alternative Open-Meteo current conditions

This explicitly selected source uses Open-Meteo's modelled current conditions;
it is not a SwissMetNet station measurement and is never an automatic fallback
for a failed selected station. Its default model selection is independent from
the weather entity's explicit MeteoSwiss ICON Seamless forecast coordinator.
The current request fixes Celsius, km/h, mm and Unix seconds.

Current values are validated individually for finite numbers and sensible
ranges. Valid zero and negative temperatures are retained. A current response
with no usable measurement, an invalid timestamp, age over one hour or a future
skew over ten minutes fails without replacing the accepted data or weather code.
Only validated data enters the versioned ten-minute cache; a cache hit resets
failure counters without extending the original TTL. Five failed updates keep
the five-minute circuit pause. Only transient transports retry (at most four
attempts); malformed payloads do not retry. HA logs unavailable/recovered
transitions; client logging suppresses private request URLs and raw HTTP causes.
Cancellation propagates and the borrowed HA session remains open on close.

OpenMeteoCurrentClient in openmeteo.py owns the request and parsers without an
HA coordinator or cache. The genuine OpenMeteoDataUpdateCoordinator in
coordinator.py composes it and owns the acceptance state described above:
cache lookup/TTL, freshness for both cached and newly fetched data, failure
counts, circuit pause and weather-code commit. Client source exceptions carry
no payload/coordinates in their message; the coordinator maps them to the same
HA UpdateFailed message as before. Setup/config-flow/weather/runtime imports
use the canonical class; the old mixed module is removed. No compatibility
wrapper, duplicate implementation, session owner or additional poller is added.

Current precipitation is the amount over the provider's backward-looking
`current.interval` in seconds, not an hourly total or rate. The precipitation
sensor exposes it as `measurement_interval_seconds`; an absent interval stays
unknown rather than assuming one hour. The separate station hourly statistics
are not supplied by this alternative source.

The legacy optional hourly preview is isolated from current observations:
invalid containers/timestamps discard the preview only, partial numbers stay
missing, and it selects usable temperatures within the current UTC hour plus
23 hours. A missing current hour never causes a midnight fallback. The HA
forecast services continue to use their independent ICON forecast coordinator.

## Shared station catalogue, cache and diagnostics

Setup and the optional station diagnostic use one named-column parser and
shared catalogue loader. The old map-only parser read WIGOS/type columns as
name/height and could commit an empty result. The shared parser uses official
column names, Windows-1252 (or explicit UTF-8 BOM), quoted semicolon CSV and a
2 MiB validated-payload limit. Unknown/invalid rows are skipped; a conflicting
duplicate identifier or an all-invalid catalogue fails atomically. Stations
without coordinates remain selectable metadata but have null GeoJSON geometry;
finite coordinates including zero are valid. Existing station/config/entity IDs
are retained.

The shared catalogue cache is valid for 24 hours on the monotonic clock; cache
hits preserve the original successful-download time and deadline. One loader
lock shares in-flight downloads between setup/diagnostic consumers. Only valid
snapshots are committed. An expired catalogue remains as last-good metadata
with `stale` status after download failure; no successful catalogue means
`unavailable`, not a successful zero-station result. Automatic retry waits five
minutes, while an explicit setup retry may try immediately. Only transient
transports retry, at most three attempts within a total 30-second budget.
Cancellation propagates. HA sessions are borrowed; the standalone fallback
owns and closes its session. The selected observation coordinator still checks
actual weather independently; stale metadata is never a substitute measurement.

The generic cache expires at the exact TTL deadline, rejects invalid/negative
lifetimes and permits zero only for immediate expiry. Cache reads do not extend
TTL. Empty/false values are valid; `None` is not negative-cached. Cleanup on
set/statistics prevents unrequested expired entries being reported as current.
Canonical key creation isolates types, argument boundaries and keyword order,
with long keys hashed. Existing weather/forecast cache key namespaces and their
600/1800-second lifetimes stay unchanged. The cache diagnostic's overall hit
rate now includes the station cache as well.

Integration diagnostics also work when an entry has no runtime data. They use
fixed coordinator roles, data type/count, safe UTC timestamps and exception
class names. They omit raw data/keys, free coordinator names, raw errors, cache
keys/values and known location fields (redacted recursively in configuration).
The current coordinators already use static names; role-based export is a
further guard for legacy/future sources, not evidence of a live data leak.
Downloading diagnostics performs no catalogue network request. `available` in
the coordinator summary means an instance exists; `last_update_success` carries
the separate fetch result.

The station diagnostic exposes catalogue status and last successful download,
with unavailable state until a valid catalogue exists. Last-good metadata can
stay available with an explicit `stale` label. Its GeoJSON remains available;
the picture-elements helper now requires an explicit map image and actual
entity ID instead of inventing an external image URL/entity. Its Swiss fixed
bounds are north-up. Existing registry disabled/enabled flags are unchanged.

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

## Shared entity metadata

`entity.py` owns common naming/default attribution and the two repeated weather/
AQ device definitions. Coordinator entities use the typed shared coordinator
base; polling diagnostics use its plain-entity counterpart. The bases add no
lifecycle/update/availability overrides or constructor behaviour. Sources,
distinct device groups, IDs and source-specific attribution stay with their
existing owners. Nine family contracts pass on both the previous tree and the
refactor, alongside the existing registered lifecycle/Recorder tests.

Diagnostics expose the declared component release as `integration_version`,
separately from the config entry's schema version/minor version. This additive,
non-private value does not identify a commit or prove a deployment. The version
module is now exercised by a real consumer. Every integration module must exceed
95% coverage; existing stricter per-module/flow and aggregate gates remain.
See the [dated review and remaining boundaries](QUALITY_PROGRESS_2026-10-22.md).

## Setup text and source choices

Canonical English `strings.json` matches translations/en.json. All DE/EN/FR/IT
form fields carry their own purpose text; the translation checker enforces
label/help parity. Native source selection uses translated labels while keeping
the saved source keys. This introduces no data migration, interval change or
new Configure field. Field-help/source-choice delivery is exercised through
HA's real translation loader. See the [quality follow-up](QUALITY_PROGRESS_2026-10-22.md).

## Polling and options migration

New entries use a developer-selected observation refresh of 600 seconds; no
polling field is exposed by setup or Configure. MeteoSwiss station data is
published in ten-minute intervals. Existing source-specific forecast, warning,
pollen and external-statistics schedules remain independent and unchanged.

Config schema **1.2** moves `update_interval` from `entry.data` to `entry.options`
when present. An already saved options value wins, preserving the previous
runtime precedence and exact stored choice. No interval is synthesized when
neither field exists: runtime falls back to 600 seconds. Existing coordinator
minimum-interval guards remain intact. This is a compatibility bridge for
installed choices, not a new user-editable polling feature or a blanket quality
rule exemption. A future removal of that bridge needs its own migration/review.

Only the polling setting moves. Measured-pollen choice remains in options;
weather source, station, coordinates and warning postcode remain in data.
Unknown fields, entry identity/title, entity/device registrations and statistics
are not rewritten. Future major schemas are rejected without mutation; current
and newer minor schemas are left intact. Stable 8.2.0 already reads interval
options before data, so it can still read migrated entries. Its older Configure
form can still edit that value; a later upgrade keeps the options value.

The unreleased shared-settings follow-up stages all three location choices and
the warning postcode through both Configure and native Reconfigure. A shared
location-flow mixin reuses catalogue search/selection and ICON validation for
setup and existing-entry settings. One settings-transaction mixin owns source
validation, pending data/options, duplicate checks, confirmation and concurrent
edit rejection; each HA route retains its native completion result. Setup keeps
its separate forecast confirmation. There is no second geocoder or duplicate
search implementation.
Data/options are updated together only after confirmation. Source failure,
cancel, a duplicate observation identity or a concurrent edit cannot partially
apply the pending choices. Existing unknown data/options and legacy intervals
are retained. HA’s registered listener owns one reload. A station/coordinate or
warning-postcode change refreshes a present config-entry unique ID for duplicate
guards, while keeping the entry_id, entity IDs and user names. External hourly
precipitation archive IDs stay station-specific: an old station’s archive is
never relabelled as the new station. Retained observation entities’ histories
continue across a deliberate source-station change; the UI explains this.

## Shared HTTP boundary

`http.py` owns destination validation and bounded reads for every active client;
source adapters retain parsing and their existing retry decorators. It disables
automatic redirects/decompression and separately bounds wire and inflated bytes.
The [HTTP contract](HTTP_SOURCE_HARDENING.md) records per-class budgets,
encoding support, real archive samples and focused HA acceptance still required.
No source, coordinator lifecycle, entity identity or HA-owned session changes.

## Catalogue diagnostic availability and coordinator placement

The station metadata service keeps its existing 24-hour monotonic deadline,
five-minute retry suppression, single-flight lock and last-good snapshot. The
optional station-count entity now reports available only after its own update
and while the loader reports `current`. The property checks expiry on read;
there is no extra expiry task or network call. HA writes frontend state on its
regular/explicit state update. No valid snapshot means a `None` native value,
not a healthy-looking zero. Stale metadata remains retained, not reclassified as
fresh or deleted. Recovery uses the same entity ID/device/registry preference.

The safe catalogue status adds a retained `station_count`. This remains
accessible in the redacted integration diagnostic even when HA hides the extra
attributes of an unavailable entity; neither getter nor diagnostic download
starts a metadata fetch. Public station exports remain part of the optional
entity's retained attributes and do not enter the redacted diagnostic payload.
Cache statistics observe local counters and are not a provider-health signal.

The warning coordinator definition moves from binary_sensor.py to coordinator.py.
Setup and typed runtime data import the canonical class directly; the platform
still imports that same class, preserving its old import path without a second
implementation. Its complete class AST is unchanged. Logging now uses the
coordinator module namespace; warning parsing, labels, timing, once-per-outage
logging, session ownership and cleanup remain covered by source/lifecycle tests.
The [placement review](COORDINATOR_LAYOUT_REVIEW.md) records the original seven-
coordinator placement milestone after the source/Recorder extractions. The
station-condition follow-up adds the eighth canonical class. No
blanket common-modules/Silver completion follows from this move.

## Measured pollen client boundary

pollen_meteoswiss.py now contains MeteoSwissPollenClient, its pure CSV parser and
two payload-free source exceptions, with no HA coordinator/runtime dependency.
The client borrows its caller's session and keeps the same fixed OGD host,
bounded CSV read, cp1252 decoding, transient retry budget and station path.
It returns the existing current/history/source/time payload or signals a
transport/invalid-data failure. It creates no session, background task, new cache
or polling schedule. Cancellation and a missing-session setup error propagate.

MeteoSwissPollenCoordinator lives in coordinator.py and composes the client.
It keeps the old constructor inputs, hourly default and name, translating the
two source exceptions into the same HA UpdateFailed messages without exposing
raw error chains. The logger namespace now follows the coordinator module.
Entity, device and statistics identity are independent of this internal class
location; persisted configuration needs no migration. Source-facing fixtures
now address client.parse_csv; HA lifecycle fixtures use the canonical class.

parse_reference_timestamp in weather_data.py supplies the one shared provider
UTC parser for observations, measured pollen and hourly/archive statistics.
The previous observation-module private name remains an import alias only.
The parser bodies and count conversion are AST-equivalent after identifier
renames; four-hour age, ten-minute future skew, seven species, zero/None
semantics, units and 24-row history stay unchanged. Direct-client tests verify
borrowed-session ownership, message-free source errors and cancellation without passing
an HA runtime/coordinator to the client. This is not a separately packaged library.
The [placement review](COORDINATOR_LAYOUT_REVIEW.md) records the subsequent
source extractions; the original seven coordinator definitions became canonical at that milestone. Full
common-modules/Silver evidence remains open.

## Modelled pollen/AQ and UV source boundary

pollen_openmeteo.py defines OpenMeteoPollenClient, pure current-hour/value
helpers and an empty source error. coordinator.py defines the actual
OpenMeteoPollenCoordinator, composing that client. The source owns both bounded
requests, parsing and the existing four-attempt AQ transport retry; it owns no
HA runtime, session, cache or polling task. A valid AQ response precedes the
optional UV request. UV failure leaves valid AQ/pollen usable; valid-but-missing
UV remains unknown. Cancellation and missing-session setup errors propagate.

HA retains the shared coordinate-specific pollen cache and original 1800-second
TTL, validates cached data against the current UTC hour and valid current
values, and logs each UV outage/recovery once. UV value/status travel atomically
with AQ: the old code did not have a separate UV cache. Cache hits cannot renew
the TTL. Setup/runtime imports and registered lifecycle mocks use the canonical
class. Existing entity IDs, grouping, options, source parameters and startup/
unload/reload contracts remain unchanged. The precipitation boundary below
completed the original seven-class coordinator placement inventory.

## Hourly/archive precipitation source and Recorder boundary

precipitation.py contains the borrowed-session source client, station/asset
selection and pure completed-hour amount parser, with no HA or Recorder imports.
The original HTTPS host, redirect/body bounds, cp1252, four transient attempts,
calendar lookback and interval-end-to-start conversion remain. Source values
contain start/amount; no Recorder metadata leaks into that contract.

precipitation_recorder.py owns the HA executor call, ordered file/period merging,
Recorder mean/min/max projection and queue operation. It retains the existing
statistic IDs/metadata, later valid corrections, partial-import counts and all
failure categories. Parsing stays off the event loop. Source/parse cancellation
never queues data; invalid or absent data never becomes a zero statistic.
MeteoSwissHourlyPrecipitationCoordinator in coordinator.py composes both layers
and translates the same four failure messages. Entry-owned hourly/weekly polling,
optional Recorder startup, keepalive listener and unload behaviour are retained.
The original seven coordinators became canonical at that milestone; the station-
condition follow-up adds the eighth. This is an
inventory result, not a complete quality-tier or live acceptance claim.

## Verification and remaining limits

The [official forecast-location catalogue foundation](FORECAST_LOCATION_CATALOGUE.md)
adds a source-only client, immutable composite identities/provenance and pure
local candidate search. Strict snapshots, borrowed-session HTTP limits,
off-loop parsing, coalescing, original cache expiry and explicit stale fallback
are tested. Setup and the unified Configure flow use this source through the
shared location-flow mixin. Saved selections preserve provenance and height;
translated dialogs and named forecast entities are implemented. See
[selection](FORECAST_LOCATION_SETUP.md) and [saved roles](SAVED_FORECAST_LOCATION.md).

Tests cover warning failure/recovery, invalid payloads, bounded retries,
cancellation, HA-owned sessions, stale observations, current-hour AQ data,
registered pollen/AQ entity states and unload, forecast service failure/recovery,
contracts, DST and translation coverage. Both pollen clients and the ICON
forecast client, alternative Open-Meteo current client, hourly precipitation importer and HGT utilities have full
line/branch coverage, enforced in CI alongside config flow. The weather entity
and shared weather-data contract also require full line/branch coverage. Cache,
diagnostics and the shared station catalogue now have the same CI requirement. The station client
must retain 100% line and branch coverage, and the whole-integration
floor is 99.0%. The [rule matrix](QUALITY_SCALE.md) records the applicable
Bronze/Silver engineering evidence and remaining Gold work. The current gate in
`scripts/check_quality_coverage.py` is authoritative for the complete enforced
module list; the global percentage does not certify every inactive module.
CI runs minimum and current
HA test environments plus Hassfest and CodeQL. Passing CI is not a live-house
acceptance test. The `quality_scale: platinum` claim inherited from upstream is
removed; no HA quality certification is asserted.

The 8.3 runtime removes the unused camera/SLF/hydrology
placeholders after checking imports, platform registration and repository
references. No active platform, entity or provider is removed. Flood/avalanche
warnings remain part of the existing App v3 feed; a separate radar integration
is unaffected. Adding standalone radar/river/bulletin products would require
new source contracts, not reinstating unimplemented modules. See the
[dated quality follow-up](QUALITY_PROGRESS_2026-10-22.md).
