# Sources, locations and update contracts

This describes requests made by the current maintained integration. Provider
publication, the integration's polling interval and its cache lifetime are
different things. Public access does not imply unlimited requests, guaranteed
availability or permission for every use. Check the providers' current terms.

## Where each family comes from

| Family | Provider and endpoint | Location | Normal integration refresh |
|---|---|---|---|
| Station observations | MeteoSwiss SwissMetNet via `data.geo.admin.ch/api/stac/v1` | Selected weather station | Configured interval, minimum/default 600 seconds |
| Alternative current conditions | Open-Meteo `api.open-meteo.com/v1/forecast` | Explicit coordinates | Configured interval, minimum/default 600 seconds |
| Weather forecasts | MeteoSwiss ICON Seamless through the same Open-Meteo forecast endpoint | HA home location for station entries; explicit coordinates otherwise | 1 hour |
| Weather/hazard warnings | MeteoSwiss App `app-prod-ws.meteoswiss-app.ch/v3/plzDetail` | Warning postcode with the internal `00` suffix added by the client | 10 minutes |
| Measured pollen | MeteoSwiss `data.geo.admin.ch/ch.meteoschweiz.ogd-pollen` | Independently selected pollen station | 1 hour |
| Pollen/AQ model values | Open-Meteo `air-quality-api.open-meteo.com/v1/air-quality` | Same point as weather forecasts | 30 minutes |
| Optional current UV | Separate Open-Meteo forecast request, `current=uv_index` | Same point as pollen/AQ | As part of that family's 30-minute refresh |
| Official hourly rain statistics | SwissMetNet station hourly assets | Selected weather station | Now file hourly; recent/historical archive initially and normally weekly |
| Station catalogue | `data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv` | Public station metadata | Shared 24-hour cache with guarded retry |

Weather, warning and pollen locations are not interchangeable. The postcode
does not choose the weather station or move the forecast point. Public weather
queries send the corresponding station, postcode or coordinates to their
providers; no provider account/API key is required for the endpoints above.
Current free-service conditions are at [Open-Meteo terms](https://open-meteo.com/en/terms).

## SwissMetNet and hourly rain

The client requests collection `ch.meteoschweiz.ogd-smn`, selects the station's
`ogd-smn_<station>_t_now.csv` asset (or its supported recent fallback) and
validates the selected station, real measurement time and usable values.
It skips trailing partial publication rows without making an old value current.
CSV uses semicolons, a dot decimal divider and Windows-1252; the catalogue also
accepts an explicit UTF-8 BOM. The number of stations is read from the current
catalogue, not hardcoded as a promise of network coverage.

The independent hourly importer uses `rre150h0` in `_h_now`, `_h_recent` and
matching historical assets. It retains 13 calendar months on archive import.
Completed-hour UTC interval ends become interval starts for Recorder; missing
hours are not invented, and later valid provider corrections update the same
statistic ID. The live running-hour sum is a separate partial accumulation.

For provider time/encoding/missing-value rules, see
[MeteoSwiss download documentation](https://opendatadocs.meteoswiss.ch/general/download).
Its recommended conditional requests/jitter are follow-up transport improvements,
not existing features implied by this page. MeteoSwiss supplies the measurements;
geo.admin.ch/swisstopo supplies their delivery infrastructure.

## Forecast and alternative current weather

The weather forecast explicitly requests `models=meteoswiss_icon_seamless`,
120 rolling hourly rows and daily extrema/mean/rain aggregates. Provider model
selection within Seamless is not a local benchmark deciding which of all
weather models is most accurate. The integration records retrieval time, not
a verified model-issuance time. It exposes up to 24 hours/five local days through
HA. See [Open-Meteo's MeteoSwiss model documentation](https://open-meteo.com/en/docs/meteoswiss-api).

The alternative current-weather provider requests temperature, humidity,
pressure, wind, precipitation, code/daylight and optional UV with explicit
Celsius, km/h, mm and Unix seconds. These are modelled conditions, not station
measurements or an automatic fallback from a station outage. Precipitation
retains the provider's backwards-looking `current.interval` duration.

Default forecast cache lifetime is 30 minutes; current-weather cache lifetime
is ten minutes. These are cache limits, not promises about model issuance or
provider publication. See [the general API contract](https://open-meteo.com/en/docs).

## Warning source

Warnings use the App v3 postcode response. This is an observed app interface,
not a formally guaranteed open-data schema. The signed-app catalogue,
captured drought comparison, all thirteen numeric families and migration
limits are documented in [WARNING_CODES.md](WARNING_CODES.md).

No warning means a successful valid empty feed. HTTP/parser failure instead
marks that source unavailable; there is no silent v1 fallback. Unknown future
integer types retain their code. Active/upcoming/outlook windows stay separate.
Provider event text and severity are retained; raw family numbers are the
automation contract. An integration update does not rewrite users' consumers.

## Pollen, AQ and UV

Measured pollen uses `ogd-pollen_<station>_h_now.csv` and exposes six tracked
types: birch, alder, hazel, beech, ash and grass. Other possible provider columns
do not imply more sensor entities. The station defaults to Luzern (PLZ) and
can be changed independently of the weather station.

The AQ request supplies modelled birch/alder/grass/mugwort/ragweed pollen and
PM2.5, PM10, NO₂, O₃. It selects the actual current hour using Unix seconds;
availability depends on provider/parameter/geography, not a claimed uniform
global resolution. UV is a separate optional current value, not daily maximum.

See [Open-Meteo AQ documentation](https://open-meteo.com/en/docs/air-quality-api)
and [MeteoSwiss pollen](https://opendatadocs.meteoswiss.ch/a-data-groundbased/a7-pollen-stations).
Those references describe providers; the supported sensor list is [SENSORS.md](SENSORS.md).
Open-Meteo/Copernicus CAMS model values are not local air-quality measurements.

## Networking, retries and privacy

HA owns the shared TLS-verified session. Each request uses a 30-second timeout;
this is not a universal 30-second deadline for every multi-request update.
Warnings, station-catalogue loading and setup-form validation also have outer
budgets. Retry counts vary by client (three/four attempts) and only transient
errors retry. Retry-After is honoured within the local delay cap; a longer pause
ends that retry sequence. It is not a persistent cross-refresh cooldown.

Current/forecast clients have their documented circuit pauses; not every family
has the same breaker. Polling, caches, multiple entries, archive downloads and
retries determine total traffic: there is no fixed requests/hour guarantee.
Station asset destinations are supplied by STAC metadata; universal asset
host/scheme/redirect and response-size boundaries remain a hardening scope.

Expected errors omit raw coordinate/postcode URLs and CSV values from logs;
diagnostics redact configured locations and omit raw payloads/cache keys.
Provider text in the optional dashboard template is HTML-escaped. Review any
user-supplied card separately. Normal state attributes still contain the
selected public station/source details and should be reviewed before sharing.

Retain source attribution when presenting data: **MeteoSwiss**, **Open-Meteo**,
and **Copernicus CAMS** where applicable. The fork's MIT software licence does
not replace the providers' data/service terms. This is not an official
MeteoSwiss product or a replacement for official warning channels.
