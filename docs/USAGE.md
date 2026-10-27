# Setup, settings and data availability

For a first installation without programming knowledge, use
[the step-by-step guide](GETTING_STARTED.md). Existing users follow the
[separate migration guide](MIGRATION.md), including the warning filters and
the retired legacy season-HGT entity. This page is the detailed reference.

## Quick troubleshooting

| What you see | What to check first |
|---|---|
| One value is `unknown` | Does that station/provider supply it? Check measurement time; do not replace a missing value with zero. |
| A family is `unavailable` | Check the relevant source/Internet connection and a later refresh; weather, warnings and pollen fail independently. |
| Weather observations work but warnings do not | Check the four-digit Swiss warning postcode and warning-source status. |
| Forecast or AQ describes a different location | Forecast: check any explicit catalogue selection, otherwise the original HA/configured base location. AQ/pollen keep the base location. See the [display follow-up](FORECAST_DISPLAY.md) for a named forecast device and card targets after 8.3.0b1. |
| Measured pollen is from another station | Choose the pollen station independently in Configure; it is not selected from the weather station. |
| A warning card uses an old label or misses Wind/Drought | Review the actual dashboard/automation dictionaries and filters using the migration guide. |
| The integration is missing after a new HACS download | Restart HA, then reload the browser. Existing users must not create a second entry. |
| HACS search does not show this fork | Let HACS refresh its catalogue, reload the page and verify the repository name. Use the [documented fallback](GETTING_STARTED.md#if-the-repository-is-not-listed) if needed. |
| HACS shows no newer version | Open the maintained fork, refresh its repository information and check the published release. Refreshing metadata does not download files; an actual download and restart are separate. |
| A repair notice names an invalid saved forecast location | From 8.3.1b1, use its settings link to correct or explicitly reset that entry's forecast choice. See [the repair guide](REPAIRS.md). Temporary provider outages do not trigger this notice. |

Do not delete/re-add the integration to troubleshoot. Report installed version,
source repository, affected entity, exact time/timezone and relevant redacted logs.
Use private vulnerability reporting for security details, not a public issue.

## Before installing

This fork targets HA 2026.8.3 or newer. It reads public HTTPS APIs without an
account, API key or local device. Network access to MeteoSwiss/data.geo.admin.ch
and Open-Meteo is required. HA's TLS verification remains enabled. Observation,
forecast, warning and pollen services can fail independently.

Use the approved release and the installation/update procedure in the README.
Search for **MeteoSwiss** in HACS and verify **martins-netizen/ha-meteoswiss**;
the maintained fork is in the default catalogue. Existing upstream installations
follow the migration guide before switching software ownership. Custom-repository
registration is a [fallback](GETTING_STARTED.md#if-the-repository-is-not-listed).
A prepared development PR is not a tested HACS release. Existing installations
must retain their config entry, domain, entity unique IDs and statistic IDs.

## Refresh interval and shared location settings

In **8.3.0**, new observation entries use **600 seconds automatically**; no
polling field is shown. Existing stored individual intervals remain effective.
**Configure** edits weather station/base coordinates, measured-pollen station,
forecast selection and warning postcode together. A search continues within
that flow and final confirmation applies all pending choices together.
Cancelling an unfinished step saves none. See [unified settings](CALENDAR_AND_LOCATION_SETTINGS.md).

**From published 8.3.2b1 (retained for prepared stable 8.3.2):** the entry's **three-dot menu → Reconfigure** opens
the same complete location settings as Configure. Both routes validate the
selected source and forecast, reject duplicate/concurrent changes, and retain
the existing entry and entities. The previous stable forecast-only shortcut
remains the behaviour of 8.3.1 until this follow-up is released and installed.

Schema 1.2 retains a legacy interval in options, with its previous precedence
over data. Unknown options, IDs and the 600-second default remain. Diagnostics
show configuration-format/coordinator-interval metadata; do not edit HA storage.
Older 8.2.0 can read that stored interval, but downgrading software does not undo
deliberately changed settings.

## Add a new entry

1. In **Settings → Devices & services → Add integration**, choose **MeteoSwiss**.
2. Choose **MeteoSwiss STAC API** for measured Swiss station weather, or
   **Open-Meteo API** for modelled weather at explicit coordinates. Explicitly
   select a **Station for measured pollen**, independently of the weather location.
   New observations refresh automatically every 600 seconds.
3. For MeteoSwiss, select a weather station and enter the postcode for warnings.
   The postcode does not automatically select or filter the station.
   For Open-Meteo, enter latitude, longitude and the warning postcode.
4. The integration checks the observation source before saving. A connection
   error leaves the form open for a retry. Optional forecast/pollen/warning
   outages do not block otherwise valid observations.
5. Keep the original forecast base or search/select/confirm a catalogue point.
   An explicitly selected point is checked before final saving; a failed check
   remains retryable. It does not change warnings, measurements or modelled AQ/pollen/UV.

MeteoSwiss entries are unique by station and postcode. Open-Meteo entries are
unique by coordinates and postcode. Legacy entries without unique IDs are also
checked. Separate warning postcodes intentionally allow separate entries.

## Parameters

| Parameter | Meaning | Default / constraint |
|---|---|---|
| Data source | Swiss station measurements or Open-Meteo location data | Open-Meteo in a new setup |
| Weather station | SwissMetNet observation station | Required for MeteoSwiss |
| Postal code | MeteoSwiss weather-warning area, independent of observation station | Required by the setup form |
| Latitude / longitude | Open-Meteo weather and forecast location | 47.05 / 8.31; finite values in −90…90 / −180…180 |
| Update interval | Observation refresh, not a displayed form field | New entries 600 seconds; stored legacy values retained. |
| Pollen station | Measured MeteoSwiss pollen station, independently of weather station and forecast location | Explicit setup choice; older 8.2.0b1 and existing entries without a saved choice fall back to Luzern (PLZ). |

Change weather station/base coordinates, measured pollen, forecast point and
warning postcode with **Configure**; the HA home setting remains separate.
Saving confirmed changes reloads the entry once. The current-weather provider
type is not changed by that dialog. See [four location roles](../README.md#four-places-what-each-one-is-used-for).

Use the official
[MeteoSwiss measurement-network map](https://www.meteoswiss.admin.ch/services-and-publications/applications/measuring-networks.html)
to locate SwissMetNet stations, then choose the station by name in HA. This is
an external reference, not a station selector for HA. **From 8.3.1b1:**
the weather-station field in setup and Configure includes the map link in
DE/EN/FR/IT. It does not send your HA coordinates or selection to the map.

## Reading values and using automations

The integration provides sensors, weather entities and weather-warning binary
sensors. There are no integration-specific service actions, device triggers or
device conditions. Use standard HA state/numeric-state triggers and conditions;
use HA's `weather.get_forecasts` action for hourly/daily forecasts. Warning
examples are in `examples/button-card-warnings.yaml` and the architecture guide.
Automations must check availability and measurement time when freshness matters.

An unavailable source is not a value of zero or an all-clear. Some parameters
are not measured at a station and legitimately stay unknown. Foehn index and
snow can be reported sparsely; their existing limited fallback is retained.

### Alternative Open-Meteo current weather

Choose this source explicitly for **modelled** current weather at coordinates;
it is not a measured Swiss station or an automatic fallback from your station.
The independent weather forecast still uses MeteoSwiss ICON Seamless.

Invalid individual measurements stay unknown while valid fields remain usable.
An all-empty or invalid/stale current response makes the source's entities
unavailable; a later valid refresh restores them automatically. Observation
freshness uses the provider timestamp, not the time of the download.

For this source, precipitation in mm covers the provider's backward-looking
interval. Check the precipitation sensor's `measurement_interval_seconds`
attribute (normally 900 for 15 minutes); it is **not** an hourly total or mm/h.
If the provider omits that duration, it remains unknown. The station-specific
archived hourly totals are not calculated for this source.

### Weather forecast availability

A failed download, malformed response or empty/unusable hourly forecast makes
the hourly and daily `weather.get_forecasts` results empty. Valid station
observations remain available. A later valid refresh restores the forecast
automatically; retained old coordinator data is not served as a successful
forecast during an outage. The client logs an availability transition once,
rather than repeating raw errors with the location URL.

The requested rolling forecast must have ordered, valid times extending beyond
now, start no more than one hour ahead and contain a valid temperature in an
unexpired hour. This checks the returned horizon, not the model's issuance time.
Individual missing/invalid values stay missing; valid zero and negative
temperature values remain valid. Missing daily fields
can use hourly fallback only for a complete, correctly aligned Swiss day. The
existing 30-minute cache and three-hour age guard in weather forecasts remain.

### Current weather attributes and ongoing forecast subscriptions

The weather entity supplies current temperature, pressure and wind using HA's
native properties, so HA can apply your selected display units. Existing entity
IDs and public attribute/service names remain unchanged. A missing current
field remains absent; a failed observation source makes the entity unavailable
until recovery.

Forecast updates are also pushed to existing hourly/daily subscribers, including
HA's weather WebSocket API. Failure pushes an empty forecast and a valid refresh
restores it without requiring a new subscription. Actual dashboard rendering
still belongs to the separate live acceptance.

Hourly forecasts omit completed intervals and show up to 24 hours from the
current hour. Daily forecasts show at most five Swiss calendar days, retaining
provider full-day highs/lows even when the hourly window begins in the afternoon.
Missing native daily fields are reconstructed only
from every expected Swiss calendar hour. Rain and probability include the
next midnight's preceding-hour bucket. Partial/gapped/invalid series leave the
affected daily field unknown; valid zero stays zero. Native provider buckets are used only when both boundaries align with the
Swiss day; otherwise the source derives the day from
complete 23-/24-/25-hour Swiss calendar coverage in the same ICON response.
It includes 25 past hours for today, while retaining the 120-hour rolling
forecast and existing refresh schedule. Each metric has its own completeness
check; a missing hour still leaves that metric unknown. This applies to scalar
daily values, daily HGT and the weather entity together. Full-day scalar
attributes identify `provider_daily` or `hourly_calendar_day` and `day_hours`.
These are model predictions, not local measurement totals.

### Pollen, air quality and UV

A valid concentration of `0` means zero; a missing individual field stays
`unknown`. If a pollen/AQ response contains no valid value for the current hour,
or the measured-pollen source fails validation/download, the affected source's
sensors become `unavailable`. They recover after a valid refresh. Missing
forecast pollen has `level_name: No data`, while a real zero retains `None`.
These existing English attributes are compatibility values, not UI translations.

UV is optional and fetched separately. A transport/JSON/response-shape failure
makes only UV `unavailable`. Validation also rejects missing, future
or at-least-one-hour-old UV timestamps and requests Unix seconds to avoid local
time ambiguity. A current valid response without a usable UV number leaves it
`unknown`. A valid zero remains zero. Repeated UV failures produce one private
warning, followed by one recovery log when the source responds correctly again.
Valid pollen/AQ remains available. Source status is retained with the existing
30-minute current-hour cache; no additional polling loop is introduced. MeteoSwiss measured pollen uses the selected
pollen station and its own measurement time (`last_update`), independently of
weather observations. The provider timestamp is UTC and marks the end of the
measured hour. On each refresh, data older than four hours or more than ten
minutes in the future makes measured-pollen sensors unavailable. Exact limits
are accepted; a later valid response recovers automatically. This conservative
policy accommodates hourly data and provider caching, and is not a guarantee
of publication latency. No independent expiry timer runs between polls: check
`last_update` in automations that need a tighter age limit. A rejected response
does not overwrite the last valid measurement/history or affect weather,
modelled pollen or air-quality availability.

### Partial publication and graph gaps

A Kloten source-file check on 15 October 2026 found a latest row with rain `0`
but temperature, humidity, pressure and wind still blank. Previous rows held
measurements. Always selecting that partial last row produced simultaneous
unknown states in HA. This identifies one reproducible cause, not every past gap.
MeteoSwiss documents missing measurements as empty CSV fields:
[CSV/time/missing values](https://opendatadocs.meteoswiss.ch/general/download).

The parser selects the latest row that actually reports instantaneous weather
when this file supplies those parameters. It skips trailing rows that only
contain accumulation/sparse fields, preserving the chosen observation's true UTC
time. Rain-only stations use their measured fields instead. This does not merge
older individual values into a newer row: a missing gust in an otherwise valid
new row remains unknown. Hourly precipitation imports remain a separate path.

Observation sensors expose these machine-readable attributes:

| Attribute | Meaning |
|---|---|
| `measurement_time` | Selected observation's actual UTC time; never refresh time |
| `source_status` | `current` for the selected latest row, `partial_update` when trailing incomplete rows were skipped |
| `pending_rows` | Number of skipped trailing rows; no claim about why they are incomplete |

`current` describes row selection, not a guarantee that every parameter exists.
Station rain is named **Precipitation (10 minutes)** and exposes
`measurement_interval_seconds=600`. It is the amount measured in the interval
ending at `measurement_time`, not a live estimate up to the present instant.
The used per-station files are published every 20 minutes, so a successful
refresh may legitimately find no new observation. See [the provider contract](API_SOURCES.md#swissmetnet-and-hourly-rain).
For hour totals use the separate official completed-hour statistics. The local
running-hour sensor is retired; no missing interval is converted to a dry hour.
The one-hour observation age limit remains in force. All-empty, invalid-time,
future-time and stale sources fail updates and make coordinator entities
unavailable. A valid zero remains zero. No synthetic historical measurements
or retrospective gap-filling are written to Recorder.

To investigate an additional gap, record its exact time and time zone, entity
ID, entity state (`unknown` versus `unavailable`), the attributes above, and
redacted integration diagnostics/logs. Compare simultaneous observation sensors
and HA restarts/Recorder operation with the original source timestamps. A
screenshot alone cannot determine the cause of every earlier interruption.

### Hourly precipitation archive and heating degree days

Official hourly imports keep the existing statistic ID and unit. Only valid,
non-negative totals for the selected station and completed whole-hour UTC
intervals are queued. Repeated imports update existing hours, including provider
corrections, without creating duplicate hours. If one archive file fails, valid
files can still be imported; missing data is not filled with zero. No valid
records means a failed importer update, preserving the previously stored data.

Daily HGT 12/20 remains a forecast-based calculation: at a daily mean of 12 °C
or lower, HGT is 20 minus that mean; above 12 °C it is zero. Missing/non-finite
temperatures remain missing. Existing season helper functions are tested, but
this change does not introduce a measured seasonal HGT archive or new sensors.
The entity reads an existing valid daily mean immediately on initial addition,
and uses the current Europe/Zurich calendar day on each state write. Missing,
boolean or non-finite means stay unknown. Availability follows the independent
forecast coordinator; a failed forecast does not make old HGT data current.

### Warning state labels

The three warning entities use explicit translated states rather than the
binary safety class's generic safe/unsafe labels: active warning, critical
warning, or announced warning; their negative states refer only to that
specific warning category. They do not assert general safety. DE/EN/FR/IT are
bundled. Automation states remain `on`/`off`; `unknown` and `unavailable` retain
their separate HA meanings. User-customized names and existing IDs are retained.

### Warning source, validation and privacy

Only a successful empty warning feed means no alerts. Malformed published
warnings fail the entire refresh, retaining last-good coordinator data while
registered binary sensors become unavailable. A later valid feed recovers
without changing entity IDs. Active, upcoming, outlook and expired warnings
remain separate. Provider codes and severity must be whole, finite non-boolean
numbers; severity is 1–5. Missing validity bounds stay missing, while timestamp
zero means the Unix epoch. Invalid/reversed bounds or malformed text/outlook
values cannot silently disappear as an all-clear. Unknown whole numeric types
remain visible with their original number.

The warning request has a total 30-second budget including bounded transport
retries. Expected warning and pollen transport errors do not expose raw HTTP
exception chains in HA debug logs. Setup/platform messages omit station names,
and warning request/parser logs omit postcodes, URLs and raw payload errors.
HA owns the borrowed HTTP session and logs availability loss/recovery once.
The station observation client also suppresses raw source/CSV details and HTTP
exception chains; failure/recovery and malformed-source paths have regressions.

Warnings use the App **v3** postcode endpoint. The signed Android app 3.6.0
establishes the [thirteen-family catalogue](WARNING_CODES.md), including Thaw
(prepared when the provider sends code 6) and Drought (code 12, observed in v3).
Wind/storm, rain/heavy rain, snow/snowfall and thunderstorms are covered;
severity and detailed event wording remain in the level and provider description.
Type 5 is the general Frost category; a ground-frost event keeps its detailed
description. There is no silent v1 fallback on failure.

Before installing this correction, inspect existing dashboard/awning filters:
**0 means Wind and 4 means Slippery Roads**. A wind/thunderstorm/rain filter
uses `[0, 1, 2]`, including corresponding upcoming/lead-time checks. Review
hardcoded type-5 labels too. Integration updates do not rewrite those consumers;
follow the migration checks in the source investigation.

## Diagnostics and the station catalogue

HA's integration diagnostics download includes source status, validated UTC
timestamps, cache counts/hit rates and catalogue status. It works even for an
unloaded entry. Known location settings are redacted; raw provider data, raw
error messages, arbitrary data keys and cache keys/values are omitted. The
download does not trigger a catalogue request.

Setup and the optional stations diagnostic share the same 24-hour station
catalogue. `current` means valid cached metadata, `stale` means retained last-good
metadata after expiry/failure, and `unavailable` means no valid catalogue has
been loaded. These are catalogue states, not weather measurement freshness.
Setup still validates the selected station's actual observation source.

the optional stations diagnostic is available only
with a current, successfully loaded catalogue. An expired/failed catalogue makes
it unavailable even when last-good station metadata remains in memory. A first
failed load does not report a healthy zero-station value. A subsequent successful
refresh restores the existing entity; no new entity or automatic enabling is
needed. Freshness is checked when the entity is read; HA publishes the changed
state on its next scheduled or requested state update, without a new timer.

HA omits extra entity attributes while an entity is unavailable. Use the
integration diagnostic's `station_catalogue` section for `data_status`, retained
`station_count`, last-success time and sanitized error type. Its count describes
the retained snapshot, not fresh weather readings. Downloading diagnostics does
not request station metadata. The local cache-statistics sensor remains usable
during a provider outage because it describes local counters, not connectivity.

Automatic retries wait five minutes after a failure; retrying setup explicitly
can try immediately. A repeated cache hit does not renew the download time.

The station helper keeps its existing entity identity and registry setting;
this change does not enable a helper you disabled. Public station GeoJSON is
retained. The generated picture-elements configuration is absent (`None`)
unless a caller explicitly supplies an image and entity ID; no placeholder
third-party image is used. Cache hit-rate totals include all three caches.

## Cache Statistics: what the numbers mean

**Cache Statistics** is an optional local diagnostic, not another weather
measurement. A cache temporarily keeps data already obtained, so several
consumers can reuse it instead of downloading it again. The entity's main
value, such as **90.0% hit rate**, is the overall fraction of successful local
cache lookups across `current_weather`, `forecast` and `stations`.

| Counter | Meaning | How to interpret a higher value |
|---|---|---|
| `overall_hit_rate` / `hit_rate` | Hits divided by hits plus misses, as a percentage. The overall value weights the three caches by lookup count. | More lookups found unexpired cached data. For example, 900 hits out of 1,000 lookups gives 90%. Reuse can reduce repeated downloads and waiting. |
| `hits` | Lookups which found an entry within its cache lifetime. | More reuse; this is a cumulative count, not a quality score. |
| `misses` | Lookups which found no entry or an expired entry. | Expected on startup, at expiry, or when requesting another location. A miss does not by itself mean an API error. |
| `total_requests` | Local cache lookups: `hits + misses`. | More cache activity. **This is not a count of HTTP/API requests.** |
| `entries` | Entries currently retained after expired entries are removed. | More distinct cached results, not better data or faster weather updates. |
| `evictions` | Expired entries removed during lookup or cleanup. | Normal cache turnover, not an error count. |

A high hit rate is useful when it avoids duplicate work **within the allowed
lifetime**. It does not prove that the provider data are fresh or accurate, that
the service is reachable, or that a warning source is healthy. Source timestamps
and availability have their own checks. A low rate can be normal when a source
is polled less often than its cache expires; do not increase lifetimes simply
to chase 100%. There is no universal good/bad threshold.

These are shared, in-memory counters for the integration's three caches, not
per-station request bills. A new HA process starts new caches/counters; reloading
an entry does not necessarily reset them. Reading the statistics does not
download weather data, though it removes expired local entries. The diagnostic
can be disabled without disabling caching. It does not cover every source's
private cache or every network request in the integration.

## Remove an entry

In **Settings → Devices & services → MeteoSwiss**, open the relevant entry's menu
and choose **Delete**. Remove or adjust automations and dashboards referring to
its entities. To uninstall the custom component afterwards, remove it in HACS
and restart HA. Existing Recorder retention/purging remains governed by HA;
uninstalling is not an instruction to delete historical statistics or backups.
Do not use removal/re-addition as an update or troubleshooting procedure.

## Diagnostic version fields

The diagnostic payload's `integration_version` is the component's declared
release version. `config_entry.version` and `minor_version` describe the saved
configuration format; they are not the installed release. Include the release
version when reporting a problem, and retain the private/redacted reporting
process. A version value alone does not prove the exact installed commit.
