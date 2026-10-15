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
new row remains unknown. Hourly precipitation imports are separate and unchanged.

Observation sensors expose these machine-readable attributes:

| Attribute | Meaning |
|---|---|
| `measurement_time` | Selected observation's actual UTC time; never refresh time |
| `source_status` | `current` for the selected latest row, `partial_update` when trailing incomplete rows were skipped |
| `pending_rows` | Number of skipped trailing rows; no claim about why they are incomplete |

`current` describes row selection, not a guarantee that every parameter exists.
The running-hour precipitation sensor aggregates published intervals separately;
its `measurement_time` describes the station observation, not the aggregate end.
The one-hour observation age limit remains in force. All-empty, invalid-time,
future-time and stale sources fail updates and make coordinator entities
unavailable. A valid zero remains zero. No synthetic historical measurements
or retrospective gap-filling are written to Recorder.

To investigate an additional gap, record its exact time and time zone, entity
ID, entity state (`unknown` versus `unavailable`), the attributes above, and
redacted integration diagnostics/logs. Compare simultaneous observation sensors
and HA restarts/Recorder operation with the original source timestamps. A
screenshot alone cannot determine the cause of every earlier interruption.

## Remove an entry

In **Settings → Devices & services → MeteoSwiss**, open the relevant entry's menu
and choose **Delete**. Remove or adjust automations and dashboards referring to
its entities. To uninstall the custom component afterwards, remove it in HACS
and restart HA. Existing Recorder retention/purging remains governed by HA;
uninstalling is not an instruction to delete historical statistics or backups.
Do not use removal/re-addition as an update or troubleshooting procedure.
