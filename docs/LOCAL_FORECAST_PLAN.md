# Local forecast points: separate catalogue and forecast decisions

**Plan version:** 1.1 · **Updated:** 21 October 2026
**Status:** Documented source review and bounded work plan.
No runtime change, new source adapter or HA installation.

## Decision and purpose

Prioritise the official MeteoSwiss catalogue as the basis for name/postcode/
mountain-POI selection. Users need an unambiguous name, supported point type and
verified altitude. Selection explicitly means **weather forecast location**.

Keep the existing App v3 warning API until further notice. The confirmed
warning postcode, observation station and measured-pollen station remain
separate. Selecting a forecast point changes neither global HA coordinates
nor those other roles.

Two decisions are independent:

1. **Use the catalogue:** a confirmed point may initially supply coordinates
   to the existing ICON Seamless source.
2. **Change forecast source:** consider processed MeteoSwiss local forecasts
   only after separate feasibility and compatibility evidence. Catalogue
   selection must not silently change models.

## Evidence reviewed on 20 October 2026

| Finding | Evidence and boundary |
|---|---|
| Approximately 6000 points: type 1 stations, 2 postcodes, 3 mountain POIs. Identity is the pair point_type_id + point_id. | [Product documentation](https://opendatadocs.meteoswiss.ch/e-forecast-data/e4-local-forecast-data). |
| Catalogue supplies names, identity, altitude and coordinates. Forecast files are updated hourly and contain all points for each parameter; hourly files can reach 33 MB per parameter. | Product documentation and metadata links in the [STAC collection](https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-local-forecasting). |
| Processed forecasts combine INCA, ICON-CH1-EPS, ICON-CH2-EPS and ECMWF; the collection describes the same forecast basis as App/website. | STAC description, not proof of identical App displays at every instant. |
| An official example demonstrates location selection and forecasts; its format check treats height as optional. | [Example project](https://github.com/MeteoSwiss/opendata-localforecast-demos) and [pinned script](https://github.com/MeteoSwiss/opendata-localforecast-demos/blob/a75a153dcec3af619b5c7277c8da6c39fc767626/scripts/check_data_format.py). |
| A targeted local-forecast API beta is planned for the end of 2026. | [Provider roadmap](https://opendatadocs.meteoswiss.ch/general/roadmap), not an availability guarantee or already usable endpoint. |

The product description states nine calendar days including today; STAC states
+0 to +192 hours. Check actual per-point/per-parameter ranges rather than
promising 216 complete hours. OGD updates hourly; the App can update more often.

Official metadata:
[point catalogue](https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_point.csv)
and [parameter catalogue](https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_parameters.csv).

**Evidence limit:** documentation, STAC collection metadata and the provider's
format-check script were read. The available web reader could not read CSV
payloads because of their content type; an additional STAC item request was
not accessible through that reader. Neither proves a provider outage.
No independent current point count, forecast values, downloaded-file size/hash,
runtime or memory measurement was obtained. Reading the vendor script is not
running and passing its live test.

## L0: verify the catalogue at four public examples

Retain **8302 Kloten, Säntis, Gotthardpass and Albert-Heim-Hütte SAC** for
comparison. Do not infer OGD IDs from App IDs. First establish whether each
example exists in the current official catalogue. A missing example is a result;
do not silently substitute a neighbouring point.

After a bounded download, record UTC retrieval time, source URL, byte count,
SHA-256, expected columns, valid counts by type, duplicate identity pairs and
the four selected records. Retain catalogue/provider modification times only
when actually supplied. Establish coordinates/CRS, altitude reference and units
from metadata; do not guess LV03/LV95/WGS84 from a numeric value.

The search prototype shows name, postcode if present, type and verified altitude.
Ambiguous matches require selection. A generic POI type does not itself identify
an individual record as summit/pass/hut; show that subtype only with evidence.
Missing altitude remains unknown. A grid-model height must not masquerade as
summit height. Check Unicode/accents, empty results, duplicates, unknown types
and removed points.

**L0 complete when:** the four records or their absence are documented,
identity/coordinate contracts are settled and the result-selection prototype is
understandable. A working App catalogue endpoint is not another prerequisite.

## L1: measure processed forecast cost and semantics

Download catalogue metadata first, then only the parameters needed for a bounded
comparison. Filter the chosen point while parsing instead of retaining the full
all-location table in HA memory. Measure actual bytes per update, duration,
peak memory, CPU and estimated daily traffic. Multiple configured locations
should share parameter downloads where feasible.

The first comparison covers temperature, wind/gusts, precipitation, weather
symbol and daily temperature extrema. Classify every currently exposed HA
forecast field as directly supplied, correctly derivable or unavailable.
Do not silently fill missing fields from another forecast source; a mixed
source product needs a separate visible design.

Time resolution and aggregation belong to the contract. Distinguish interval
end, instantaneous value and local calendar day; check UTC/Europe/Zurich and
DST. Do not label three-hour precipitation probability as one-hour probability.
Map symbols to HA conditions through verified semantics; do not copy proprietary
MeteoSwiss graphics.

A contemporaneous four-location comparison can explain differences from
Open-Meteo or the official display. It cannot alone prove higher accuracy.
Without observations and a suitable longer comparison, do not claim “always
the most accurate forecast”.

**L1 complete when:** data, field coverage, time semantics and resource cost are
evidenced. Then justify direct OGD, catalogue plus existing forecasts, or waiting
for a suitable point-query API. Bandwidth and Pi 5 resources matter.

## L2: location contract and implementation

Store provider, type, opaque point ID, display name, coordinates/CRS, optional
altitude/provenance and catalogue version. Keep type and ID together.
A search term is not persistent identity.

Changing forecast location changes no observation station or warning postcode.
Existing entries initially retain HA-home forecasts and their configured warning
postcode. New selection is explicit. Unchanged measurement sources retain
entity/unique/statistic IDs; never combine different station histories.

Catalogue and forecasts have separate lifecycles. Do not search on each weather
refresh. Search failure must not invalidate a confirmed location unnecessarily.
A valid saved selection and last-good catalogue can persist with visible age,
without making old forecast data appear fresh. Removed IDs need an actionable
message and reselection, not a silent replacement.

A future adapter uses HA-owned sessions, TLS, fixed HTTPS destinations, redirect
validation, timeouts, cancellation, bounded retries and actually enforced size
limits. Validate the documented Latin1/semicolon CSV contract; execute no data.
Logs/diagnostics exclude private searches, coordinate URLs and full payloads.
Provide correct source attribution.

**Implement only after the source decision:** use small regular PRs for
catalogue/typed data, translated selection and any forecast adapter. Include
DE/EN/FR/IT and meaningful failure, duplicate, missing-height, time, cache,
migration and unload tests. Check HA forecast consumers and existing
automations separately. Do not explore the catalogue by changing production
or deleting existing HA entries.

## Scope boundaries

Silver/Gold work remains independent. This plan does not change beta 8.2.0b1,
its runtime acceptance or the confirmed HACS switch. The clean first-install
test remains separately open; the operator need not provide another permanent
HA environment.

See the [development plan](NEXT_RELEASE_PLAN.md) and
[earlier POI evidence](POI_FEASIBILITY.md).
