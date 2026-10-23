# Saved forecast location and ICON routing

**Guide version:** 1.1 · **Updated:** 23 October 2026
**Status:** Second POI development package, unreleased after 8.2.0. The translated
search, confirmation and reconfiguration package now supplies the
[HA user path](FORECAST_LOCATION_SETUP.md); practical candidate acceptance remains. Users
should not edit HA storage manually to try this internal contract.

## What a selected location means

A confirmed catalogue point supplies the location of the **weather forecast**.
For example, a Säntis selection requests ICON forecasts for that point and its
catalogue altitude. It does not turn Kloten observations into mountain weather.

| Data family | Location after an explicit forecast selection |
|---|---|
| ICON hourly/daily forecasts, eight forecast scalars and calculated HGT | Selected catalogue point; known catalogue height sent explicitly |
| MeteoSwiss observations and precipitation archive | Existing observation station |
| Alternative modelled current weather | Existing configured base coordinates |
| Modelled air quality/pollen and optional UV | Existing base coordinates, independently of the forecast POI |
| Measured pollen | Existing measured-pollen station |
| App v3 warnings | Separately confirmed existing warning postcode |

Global HA coordinates, existing entity/unique IDs, device groups and statistics
are retained. Weather and forecast-derived entities expose a local
forecast_location attribute with the selected name, category and catalogue
height, or an invalid-selection status. Existing names are not automatically
rewritten. An explicit POI forecast never supplies the current-condition
fallback on the existing weather entity. Current-condition inputs and the
existing measured-rain fallback still work. The legacy same-location forecast
fallback remains unchanged when no selection has been saved.

## Offline, versioned selection contract

forecast_location_config.py serializes the immutable selection from the
[catalogue source](FORECAST_LOCATION_CATALOGUE.md) into the entry-data key
forecast_location. Its schema is version 1 and its named CRS is EPSG:4326:

- Fixed provider and source URL; point type and opaque ID together.
- Original name, WGS84 latitude/longitude and optional altitude_masl.
- Station abbreviation only for station points; four ASCII postcode digits
  only for postcode points. A point ID is never converted into a warning code.
- Raw catalogue SHA-256 and original aware retrieval timestamp, normalized to UTC.

The decoder validates the exact key set, version, role constraints, text limits,
finite numeric coordinates/heights, WGS84 bounds, hash and timestamp. Boolean
coordinates, unknown versions, injected URLs, missing keys and malformed fields
are rejected privately. The hash identifies the downloaded bytes; it does not
cryptographically authenticate a provider record.

Ordinary setup and reload read this saved selection **without fetching the
catalogue**. A temporary catalogue outage cannot move an already selected point.
An entry with no forecast_location key follows the existing base-coordinate
logic, including independent legacy-coordinate fallbacks. Polling-setting
migration does not create or infer a forecast selection from the station or PLZ.

A present but invalid selection disables only the forecast request. It cannot
silently fall back to HA coordinates or another point. Current observations,
warnings and pollen retain their own availability. Diagnostics distinguish
legacy, catalogue and invalid status. Recovery requires a valid explicit
selection and reload; the reconfiguration dialog provides that user path.
The storage package itself writes no selections into existing entries; the
new dialog writes only after explicit confirmation. Old 8.2.0 does
not understand this additive key: downgrading would restore that version's
legacy forecast-location behaviour, so it is not a same-location rollback for
an entry deliberately moved to a POI.

## Height and request/cache identity

The [Open-Meteo API documentation](https://open-meteo.com/en/docs) describes
elevation as the target height for statistical downscaling and explicitly
supports mountain peaks. Apply the finite catalogue altitude in metres,
including real zero and negative heights. If the catalogue height is missing,
omit elevation and retain the provider's automatic DEM selection. Never send
elevation=nan: that would disable downscaling rather than request automatic
height. Keep the existing cell_selection default and explicit
models=meteoswiss_icon_seamless. This is not adoption of processed OGD/App
local-forecast products or an accuracy guarantee.

Legacy/automatic-height requests retain the existing v3 coordinate cache key.
An explicit-height request uses a v4 key containing the coordinates **and the
normalized requested height**. Different heights and automatic-height requests
cannot share a cached response. Equivalent int/float heights can share the same
request; names, IDs and catalogue hashes do not change the forecast payload and
are not cache dimensions. Cache TTL, failure/circuit handling, optional startup,
polling and borrowed-session ownership remain unchanged.

## Privacy, validation and remaining work

Local HA entity metadata identifies the selection. Downloaded diagnostics
redact the entire saved object in both data and options, including unexpected
nested fields. Only fixed status and elevation-mode labels are exported. Logs
and formatted source/storage errors include no selected names, coordinates,
point IDs, altitude, hashes or payloads. Existing source destination, TLS,
redirect, response-size and retry protections remain in force.

Regression tests cover JSON round trips for all point roles, missing/zero/
negative height, invalid selections, exact request parameters, elevation cache
isolation, both current-weather providers, real HA setup/reload/unload,
forecast-service output, local metadata, private diagnostics and recovery after
a corrected selection. A [dated public-point client probe](evidence/selected_forecast_location_2026-10-23.json)
at 18:42:00 UTC on 23 October 2026 returned 120 hourly rows and daily aggregates
for Kloten postal code, Säntis, Gotthardpass and Albert-Heim-Hütte SAC using their
catalogue heights. This is source/request compatibility evidence, not a
forecast-accuracy comparison. The HA tests use controlled source responses; they are
not the operator's temporary-HA acceptance. The dialogs are now regression-tested; practical postcode/summit/pass/hut
selection checks remain for the next reviewed candidate. No operator installation or release is performed by this package.
