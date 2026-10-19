# Sensor reference

This describes the current maintained code, not every feature in older upstream
releases. Keys are internal description keys, not fixed entity IDs. HA derives
entity IDs on first addition; retained entities keep their existing identity.
For setup use [START_DE.md](START_DE.md); existing users use [WECHSEL_DE.md](WECHSEL_DE.md).

## Weather entity

Current temperature, humidity, pressure and wind follow the selected observation
source: measured SwissMetNet station or explicitly selected Open-Meteo modelled
current weather. The weather symbol can use a valid location forecast when no
direct station condition exists.

Hourly/daily forecasts use **MeteoSwiss ICON Seamless via Open-Meteo**, refreshed
hourly, projected to up to 24 hours/five Swiss calendar days. For station entries
the forecast point is HA's home location; for Open-Meteo entries it is the explicit
location. The warning postcode does not move the forecast. Native units are °C,
hPa, km/h and mm; HA converts weather attributes to the user's selected units.
Forecast failure returns an empty forecast while valid observations remain usable.

## Observation sensors

The integration polls at the configured interval (default/minimum ten minutes).
MeteoSwiss publishes the per-station ten-minute files every **20 minutes**;
polling more often does not make new measurements appear sooner. Values depend
on what the selected station actually measures.

| Key | Meaning | Native unit | Station parameter |
|---|---|---|---|
| `temperature` | Air temperature | °C | `tre200s0` |
| `humidity` | Relative humidity | % | `ure200s0` |
| `wind_speed` | Ten-minute mean wind | km/h | `fu3010z0` |
| `wind_direction` | Wind direction | ° | `dkl010z0` |
| `wind_gust` | Maximum one-second gust | km/h | `fu3010z1` |
| `pressure` | QFF sea-level pressure | hPa | `pp0qffs0` |
| `precipitation` | Latest available measured ten-minute amount | mm | `rre150z0` |
| `dew_point` | Measured dew point, with Magnus fallback | °C | `tde200s0` or calculation |
| `sunshine_duration` | Ten-minute sunshine total | min | `sre000z0` |
| `global_radiation` | Ten-minute mean global radiation | W/m² | `gre000z0` |
| `snow_depth` | Snow depth, if measured | cm | `htoauts0` |
| `foehn_index` | Foehn index, if measured | Code | `wcc006s0` |

Numeric observation descriptions have state class `measurement`. Attributes
include `measurement_time`, `source_status` and `pending_rows`. Missing fields
stay unknown; a stale/failed whole source is unavailable. The station rain name
is **Precipitation (10 minutes)**, with `measurement_interval_seconds=600` and
`measurement_time` marking the interval's end. For example, end time 12:20
means the ten minutes ending at 12:20, even when downloaded at 12:35. It is
neither the rainfall since 12:00 nor a total for the previous whole hour.

For Open-Meteo current weather the name is **Precipitation (modelled interval)**.
Its amount covers `measurement_interval_seconds` (normally 900 seconds), not
an hourly total or a precipitation rate. An absent provider duration remains
unknown. It is not labelled as a measured ten-minute value. Names are bundled
in DE/EN/FR/IT; the `precipitation` unique key and existing entity IDs are stable.
Station-only parameters stay unknown when absent; archived hourly statistics
are not supplied for the alternative source.
Soil-temperature sensor descriptions are not part of the current platform.

### Completed hourly precipitation statistics

With Recorder loaded, the station importer writes external statistics under
`meteoswiss:<station>_precipitation_hourly`, for example
`meteoswiss:klo_precipitation_hourly`. These completed-hour totals are a separate
series, not the ten-minute sensor's history.
The importer shifts interval ends to UTC interval starts, applies corrections
without duplicate hours and does not invent zeros for gaps. The archive looks
back 13 calendar months at initial import and normally weekly; the current-hourly
file is checked hourly. Existing mean/min/max metadata is retained; this is not
a cumulative `total_increasing` counter.

### Removed derived running-hour sensor

`precipitation_current_hour` is retired before the first maintained beta release.
It was a local sum of already published intervals since the current hour began,
not an official completed-hour value or a rolling last-60-minutes amount. Data
publication delays caused repeated unknown states and missing intermediate
intervals could leave an unmarked partial sum. It is no longer calculated or
created. On setup/reload, only the retired entity belonging to that entry is
removed from the entity registry; no Recorder purge is performed. Existing
raw measurements, other entries, independently created Utility Meter helpers
and official archive statistics are not deleted. Review old dashboard and
automation references before updating; see [migration](WECHSEL_DE.md).

## Pollen, air quality and UV

Modelled and measured pollen are user-facing environmental sensors. Both appear
under **Sensors** on their respective Home Assistant device pages, alongside the
other environmental values. After updating the integration, setup/reload also
corrects previously registered pollen entities from **Diagnostic** to **Sensors**;
their entity/unique IDs, history and personal settings are retained. Technical
cache and station-catalogue helpers remain under **Diagnostic**. This grouping
does not change whether a value is modelled or measured.

### Modelled pollen

| Description key | Pollen | Display thresholds, grains/m³ |
|---|---|---|
| `birch_pollen` | Birch | 10 / 50 / 200 |
| `alder_pollen` | Alder | 10 / 50 / 200 |
| `grass_pollen` | Grass | 5 / 20 / 50 |
| `mugwort_pollen` | Mugwort | 10 / 50 / 200 |
| `ragweed_pollen` | Ragweed | 5 / 20 / 50 |

Keys differ from some translation keys, such as `pollen_ambrosia`. These are
Open-Meteo AQ model values, not local measurements. The client selects the
actual current hour and refreshes every 30 minutes. Thresholds are the existing
display categories, not personalised medical advice. English compatibility
`level_name` values distinguish a valid zero (`None`) from missing data (`No data`).

### Air quality and optional UV

| Key | Meaning | Native unit |
|---|---|---|
| `pm25` | PM2.5 | µg/m³ |
| `pm10` | PM10 | µg/m³ |
| `nitrogen_dioxide` | NO₂ | µg/m³ |
| `ozone` | O₃ | µg/m³ |
| `uv_index` | Optional current modelled UV | Existing `UV Index` label |

AQ follows the same 30-minute coordinator. UV is requested separately; failure
makes only UV unavailable while valid AQ/pollen stays usable. A successful
response with a missing UV value remains unknown. It is not the daily
maximum UV. An empty/failed primary feed makes that family unavailable, while
valid individual zeros remain zero.

### Measured MeteoSwiss pollen

The separately selected pollen station refreshes hourly. Seven keys are supplied:
`ms_pollen_birch`, `ms_pollen_alder`, `ms_pollen_hazel`, `ms_pollen_beech`,
`ms_pollen_ash`, `ms_pollen_grass`, `ms_pollen_oak`. Their columns are `kabetuh0`, `kaalnuh0`,
`kacoryh0`, `kafaguh0`, `kafraxh0`, `khpoach0`, `kaquerh0`.

The public PZH hourly file and OGD parameter inventory were checked on
17 October 2026: oak is a supported measured series. Ambrosia and mugwort are
not present in that hourly schema; their existing Open-Meteo entities remain
modelled. Older/partial CSVs without oak retain valid existing values and leave
only the missing oak value unknown. Existing six unique IDs stay unchanged;
oak adds one measured entity per integration entry, with DE/EN/FR/IT names.

Values are measured concentrations, with the compatibility `unit` attribute
`No/m³`. Attributes include `station`, `source`, `history_24h`, `last_update`.
History contains up to 24 source rows, not a guarantee of 24 consecutive hours.
These descriptions do not declare a new long-term-statistics state class or
silently migrate units. Missing individual counts stay unknown; a source older
than four hours is rejected on refresh.

## Daily heating degree days

`heating_degree_days` is a **forecast-based HGT 12/20 estimate for today**.
At a forecast daily mean of at most 12 °C, the result is **20 minus that mean**;
above 12 °C it is zero. A mean of 10 °C gives 10 °C·d, not 2 °C·d. Missing or
invalid temperatures stay unknown. Attributes identify the forecast/calculation;
native unit is °C·d and state class is `measurement`.

There is no measured seasonal accumulation entity. The obsolete forecast-only
`season_hgt` registry entity is removed if present. This does not instruct users
to purge historical data; consumers of that old entity need migration review.
Season helpers in `calc.py` are not a persisted HA seasonal counter.

## Warning sensors

| Description key | On means |
|---|---|
| `any_alert` | At least one active, non-outlook warning |
| `critical_alert` | An active warning at level 3 or higher |
| `upcoming_alert` | A published, non-outlook warning with a future start |

All three expose active `alerts`, separate `upcoming_alerts`, counts,
`next_alert_start`, `last_successful_update`, `data_status`, and the four-language
`warning_labels` catalogue. A failed source is not off or an all-clear. Original
numeric types/levels and provider text remain intact.

The postcode feed carries weather and natural-hazard warnings. Avalanche (8)
and flood (11) warnings are processed by these same sensors when supplied for
the selected postcode. They do not require the inactive standalone SLF/BAFU
modules. A custom dashboard or automation can still exclude these families
with its own filters. See [scope and official source](WARNING_CODES.md#natural-hazard-scope).

Use the [verified catalogue](WARNING_CODES.md#numeric-warning-families):
**0 is Wind; 4 is Slippery Roads.** Severity is a separate number from 1 to 5.
The critical sensor's threshold is not a universal threshold for an awning.
Own automations need availability, severity, timing and relevant-family rules.
Warning sensors refresh every ten minutes; validity transitions are evaluated
on state writes, without a separate second-by-second timer.

## Shared diagnostics and inactive modules

`meteoswiss_stations_map` is the shared catalogue helper's unique ID, not a fixed
entity ID: station count, GeoJSON and catalogue status. It is not another weather
station and can stay disabled. `meteoswiss_cache_stats` is the shared cache
helper's unique ID. Existing entity names can differ. Integration diagnostics
download a redacted technical summary.

Camera/radar, standalone SLF and standalone BAFU modules are inactive placeholders;
they do not create additional entities. This does not exclude avalanche or
flood warnings supplied through the postcode feed. Standalone river-gauge
measurements and full avalanche-bulletin products are not provided by those
placeholders.
