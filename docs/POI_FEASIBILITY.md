# POI feasibility: first bounded source probe

**Document version:** 1.5 · **Probe:** 17 October 2026 · **Updated:** 24 October 2026
**Result:** Public name search and coordinate-based forecasts were exercised.
Current App-catalogue access and complete POI-warning coverage were not proved.
No POI feature was implemented or approved by this probe.

On 23 October the operator approved catalogue-based location/POI selection
for the next feature release, keeping the existing ICON source. That later
decision is recorded in the local-forecast plan; it does not expand what the
historical probe below demonstrated. Catalogue, saved routing and translated
selection/reconfiguration are now integrated through PRs #56–#58. The final
review and focused candidate acceptance remain; see the
[selection guide](FORECAST_LOCATION_SETUP.md).

## Current planning boundary

Keep the original evidence below as history. The official OGD local-forecast
point catalogue is now the preferred investigation path, specified in the
[local-forecast plan](LOCAL_FORECAST_PLAN.md).
That route does not depend on successful App-POI access. Keep App v3 warnings
and a separately confirmed warning postcode. A forecast point alone proves no
point-specific warning coverage; adopting processed OGD forecasts needs its
own data/resource/source decision.

**New catalogue evidence, 21 October:** a direct bounded OGD download and
STAC checksum comparison now establish **5820 rows / 5816 unique type/ID pairs**,
including **631 POIs**. Kloten postal code 8302, Säntis POI, Gotthardpass and
Albert-Heim-Hütte SAC are present with provider-declared WGS84/LV95 coordinates
and heights. Four duplicated station keys have fully identical rows; 86 bare
IDs occur in multiple types. See the
[current catalogue audit](LOCAL_FORECAST_PLAN.md#catalogue-snapshot-verified-on-21-october-2026)
and [compact evidence](evidence/local_forecast_catalogue_2026-10-21.json).
This improves catalogue/altitude provenance; it does not turn the historical
App probe, forecast-source evaluation or warning-coverage questions into passes.

The [development plan](NEXT_RELEASE_PLAN.md) uses three mountain examples plus
a postcode control. This probe used documented public swisstopo search and the
existing Open-Meteo/MeteoSwiss ICON source, without accessing protected App services.

## 1. Static App-catalogue evidence

The previously signature-verified MeteoSwiss Android 3.6.0 package contains
assets/localdata.sqlite, embedded catalogue version 181. Its poi table has
623 entries: 335 summits, 205 mountain huts and 83 passes, with POI IDs, names,
Swiss grid coordinates, altitude, warnregion, activity flags and DE/FR/IT/EN
categories. This snapshot does not prove current live coverage.

| Example | App POI ID | App x / y | App height | App warnregion |
|---|---:|---|---:|---:|
| Säntis summit | 711 | 744170 / 234918 | 2502 m | 168 |
| Gotthardpass | 594 | 686073 / 157063 | 2107 m | 302 |
| Albert-Heim-Hütte SAC | 454 | 678517 / 162475 | 2542 m | 149 |

Bare region numbers prove neither current spatial meaning nor flood, avalanche,
drought or other hazard coverage. POI IDs are not postcodes; the existing
postcode suffix `00` does not apply. The grid's CRS needs evidence before use;
the network probe instead used WGS84 coordinates supplied by public search.

Package traceability:

- APK SHA-256: `a76f4a1bc8fbd41509e0fc43cf0a08c9f0ce27e802def596d4c15939bae6082a`
- Signing certificate SHA-256: `07dbd58510fa5a8d7f02aafa88960dac64508a26a3b29fabf5d5a26e95490b60`
- SQLite SHA-256: `812f4eed10ee97a7deb6d237cef88582ae706e570b9d63d7bbfab668db586ed3`

Only these findings are documented. No APK, complete database or decompiled code
is shipped. Inspection of all three DEX files did not establish a complete
POI request contract; the package contained no .so libraries. This is not a
completeness claim for all App implementation components.

The earlier single request to app-prod-static.meteoswiss-app.ch/v1/db.sqlite
returned 403. No retries with altered identities/credentials were made.

## 2. Public name/postcode search

[GeoAdmin Search](https://docs.geo.admin.ch/access-data/search.html) documents
SearchServer with type=locations, origins=gazetteer or zipcode, sr=4326 and a
bounded result count. On 17 October, four terms and one expanded Säntis search
were requested: five GETs, no authentication or mass catalogue download.

| Selected result | WGS84 latitude / longitude | Selection finding |
|---|---|---|
| Säntis, alpine summit, AI | 47.249424 / 9.343241 | First five results were other same-name places; summit appeared in the expanded 34-result response. |
| Gotthardpass, pass, TI | 46.559311 / 8.561156 | Two differently named results shared coordinates. |
| Albert-Heim-Hütte SAC, building, UR | 46.608932 / 8.463569 | Two nearby building results; name alone was insufficient. |
| 8302 Kloten, postcode | 47.458755 / 8.582091 | Unambiguous control; coordinates for a postal code are not automatically HA's home location. |

Do not auto-select the first result. Show category, canton/municipality and
verified altitude where available, then let users choose. Bound/debounce
requests and cache results. Treat HTML label markup as text. The internal search
result id is not a stable location identity. Use a stable feature identity only
when actually documented; otherwise retain confirmed coordinates/provenance.
Search results alone do not establish summit altitude.

Source: © Data: swisstopo. [FSDI terms](https://www.geo.admin.ch/en/general-terms-of-use-fsdi)
allow registration-free use subject to fair use, dataset terms and attribution.
Before feature publication, settle search load, attribution and data scope.

## 3. Existing forecast at the selected coordinates

Four GETs with exactly models=meteoswiss_icon_seamless, three forecast hours and
four variables returned HTTP 200 at approximately **17:19 Europe/Zurich on
17 October 2026**. Every example had three consecutive hours and finite
temperature, precipitation, wind-speed and weather-code values.

This is bounded reachability/contract evidence, not an accuracy comparison or
full five-day/HA acceptance. See the
[MeteoSwiss ICON documentation](https://open-meteo.com/en/docs/meteoswiss-api).
No switch to App point forecasts was made.

| Location | Embedded App height | Forecast default height |
|---|---:|---:|
| Säntis | 2502 m | 2399 m |
| Gotthardpass | 2107 m | 2108 m |
| Albert-Heim-Hütte SAC | 2542 m | 2518 m |
| Kloten control | Not copied | 442 m |

Forecast-response coordinates describe the model grid and must not overwrite
the chosen location. Default grid altitude may differ from summit altitude.
Open-Meteo [documents elevation](https://open-meteo.com/en/docs#api-documentation).
A fifth Säntis request with elevation=2502 returned HTTP 200, three hours and
2502 m. This proves technical input support, not independent catalogue-height
verification or better forecast accuracy.

Define altitude source, units, validation and cache identity before implementation.
Altitude must not be merely a decorative label.

[Compact evidence](evidence/poi_probe_2026-10-17.json) records time, public URLs,
selected results, returned grid, finite-value counts and capture hashes.
It contains no private HA coordinates/accounts/App credentials. Values and
search ranking change, so repeat contract checks rather than expecting identical
weather values. Weather source: MeteoSwiss via Open-Meteo.

## 4. Decision and remaining evidence

The original P1 candidate was documented public location search feeding
confirmed coordinates to the existing ICON source. The App database was
supplementary evidence, not a mandatory shipped catalogue. The newer OGD
catalogue investigation is a separate proposal, not a completed replacement.

Original P0 was incomplete: actual App-POI requests and the examples' warning
coverage were not proved. Neither search results nor successful forecasts
establish natural-hazard coverage. Never silently use a neighbouring postcode
or old bare region ID; explicitly confirm a separate warning location and keep
unsupported coverage distinct from an all-clear.

Before a feature PR:

1. Settle location/altitude sources and permitted use; handle ambiguity,
   duplicates, Unicode, empty/broken responses and outages.
2. Prove example/hazard coverage or explicitly support a separately confirmed
   warning postcode.
3. Define typed location data and UI flow with separate forecast, observation
   and warning roles, preserving existing entries.
4. Retain confirmed coordinates and altitude/provenance. Search failure must
   not unnecessarily disable existing forecasts; do not search at every refresh.
5. Provide DE/EN/FR/IT, meaningful failure/migration/lifecycle tests, required CI
   and a scoped HA visual check. Implement only after R0/S1 prerequisites.

Silver work remains independent of open POI questions.
