# Setup, settings and data availability

## Before installing

This fork targets HA 2026.8.3 or newer. It reads public HTTPS APIs without an
account, API key or local device. Network access to MeteoSwiss/data.geo.admin.ch
and Open-Meteo is required. HA's TLS verification remains enabled. Observation,
forecast, warning and pollen services can fail independently.

Use the approved release and the installation/update procedure in the README.
A prepared development PR is not a tested HACS release. Existing installations
must retain their config entry, domain, entity unique IDs and statistic IDs.

## Add a new entry

1. In **Settings → Devices & services → Add integration**, choose **MeteoSwiss**.
2. Choose **MeteoSwiss STAC API** for measured Swiss station weather, or
   **Open-Meteo API** for weather at explicit coordinates. Select an update
   interval of at least 600 seconds (default 600).
3. For MeteoSwiss, select a weather station and enter the postcode for warnings.
   The postcode does not automatically select or filter the station.
   For Open-Meteo, enter latitude, longitude and the warning postcode.
4. The integration checks the observation source before saving. A connection
   error leaves the form open for a retry. Optional forecast/pollen/warning
   outages do not block otherwise valid observations.

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
| Update interval | Observation polling interval in seconds | 600; minimum 600 |
| Pollen station | Measured MeteoSwiss pollen station, independently of weather station | PLZ; choose from the supported list |

Change the update interval and measured pollen station using the entry's
**Configure** button. Saving options reloads the entry without recreating it.
Changing source/location is not offered by this options form. For MeteoSwiss
entries, weather and pollen forecasts use the HA installation location; station
coordinates describe observations. For Open-Meteo they use the explicit location.

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
running-hour and archived hourly totals are not calculated for this source.

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
temperature values remain valid. A response with absent daily aggregates can
use the existing hourly fallback, which may cover only part of today. The
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
If native daily aggregates are missing, extrema/probability can use available
hours; these may cover only part of today. A fallback rain sum stays unknown
when a represented hourly value is missing or an internal time gap exists.
Valid zero rain stays zero. Provider native daily totals are used when present;
the integration does not recalculate them as local measurement totals.

### Pollen, air quality and UV

A valid concentration of `0` means zero; a missing individual field stays
`unknown`. If a pollen/AQ response contains no valid value for the current hour,
or the measured-pollen source fails validation/download, the affected source's
sensors become `unavailable`. They recover after a valid refresh. Missing
forecast pollen has `level_name: No data`, while a real zero retains `None`.
These existing English attributes are compatibility values, not UI translations.

UV is optional and fetched separately. Its failure leaves UV unknown while
valid pollen/AQ remains available. MeteoSwiss measured pollen uses the selected
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
The running-hour precipitation sensor aggregates published intervals separately;
its `measurement_time` describes the station observation, not the aggregate end.
If no valid rain interval has been published in the current UTC hour, this
total stays unknown, including before the first interval arrives after the hour
changes. A valid zero is displayed as zero. Invalid/negative rain amounts are
skipped and a repeated interval timestamp is counted once; equal amounts at
different timestamps remain separate intervals. This sum does not assert that
every interval in the hour was received.
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

### Warning validation, privacy and remaining numeric-code verification

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
The station observation client's broader legacy logging still needs review.

The existing warning-name mapping is **not** approved as a complete API code
specification. See [the source investigation](API_SOURCES.md#warning-types-legacy-implementation-labels-not-an-api-specification),
particularly the `0`/`4` wind-versus-slippery-roads discrepancy. Verify numeric
meanings and existing dashboard/awning filters before a deployment or release;
do not change a safety filter solely because a translated label changed.

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
Automatic retries wait five minutes after a failure; retrying setup explicitly
can try immediately. A repeated cache hit does not renew the download time.

The station helper keeps its existing entity identity and registry setting;
this change does not enable a helper you disabled. Public station GeoJSON is
retained. The generated picture-elements configuration is absent (`None`)
unless a caller explicitly supplies an image and entity ID; no placeholder
third-party image is used. Cache hit-rate totals include all three caches.

## Remove an entry

In **Settings → Devices & services → MeteoSwiss**, open the relevant entry's menu
and choose **Delete**. Remove or adjust automations and dashboards referring to
its entities. To uninstall the custom component afterwards, remove it in HACS
and restart HA. Existing Recorder retention/purging remains governed by HA;
uninstalling is not an instruction to delete historical statistics or backups.
Do not use removal/re-addition as an update or troubleshooting procedure.
