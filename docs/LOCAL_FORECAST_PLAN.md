# Local forecast points: separate catalogue and forecast decisions

**Plan version:** 1.3 · **Updated:** 23 October 2026
**Status:** Catalogue-based location/POI implementation approved for the next feature release; dated catalogue audit retained, runtime implementation remains open.
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

That initial review did not obtain CSV payloads through the web reader. The
bounded direct download below now supplies independent catalogue evidence;
the earlier access limitation did not establish a provider outage.

## Catalogue snapshot verified on 21 October 2026

At **05:48:52 UTC**, a verified HTTPS GET returned the official point CSV:
**828864 bytes**, Latin1/semicolon, below the enforced 2 MiB download limit.
Its SHA-256 is
`bdf63842f244d4e5f232bc116f2dd71080fef34152a770258ffb90f03ed9dfeb`.
The independently downloaded STAC collection reports the same SHA-256
multihash and a catalogue modification time of **03:55:15 UTC** that day.
Checksum agreement identifies this snapshot; it is not a digital signature.

| Catalogue category | Rows | Unique type/ID pairs |
|---|---:|---:|
| 1 — station | 1118 | 1114 |
| 2 — postal code centre | 4071 | 4071 |
| 3 — Point of Interest | 631 | 631 |
| **Total** | **5820** | **5816** |

These are forecast-catalogue records, not a count of active observation
stations or proof of full App coverage. All rows have the fourteen expected
columns, documented types, nonempty required fields and finite coordinates/
heights. WGS84 latitude/longitude bounds pass. No height is missing in this
snapshot. Both WGS84 and LV95 are explicitly named in the columns; height is
declared as metres above sea level. An independent CRS transformation or
survey-height validation was not performed.

Four station keys occur twice: **(1,123) Seengen**, **(1,167) Gadmen**,
**(1,358) Kiental** and **(1,729) Zweisimmen**. Each pair is identical across
all fourteen columns. Collapse identical rows; reject conflicting identity
records rather than silently taking the first. **86 bare IDs occur in multiple
types**, independently confirming why identity must include type and ID.

### Proposed selection display, grounded in actual records

| Name | Category | Type / ID | Height | WGS84 latitude / longitude |
|---|---|---|---:|---|
| 8302 Kloten | Postal code centre | `2 / 830200` | 436 m | 47.451253 / 8.579761 |
| Säntis | Point of Interest | `3 / 711` | 2502 m | 47.249425 / 9.343242 |
| Gotthardpass | Point of Interest | `3 / 594` | 2107 m | 46.559306 / 8.561156 |
| Albert-Heim-Hütte SAC | Point of Interest | `3 / 454` | 2542 m | 46.608917 / 8.463553 |

All four intended examples exist; no neighbouring point was substituted.
The catalogue also contains **Säntis station (1,35), 2501 m** and
**Zürich/Kloten station (1,59), 426 m**. They are distinct from the POI and
postal-code examples. Do not confuse Kloten's catalogue centre with the
previous swisstopo search result, observation station or HA home coordinates.

The generic POI category supplies no per-record summit/pass/hut subtype.
Names suggest those familiar examples, but must not be promoted to verified
subtypes without another documented source. Altitude remains catalogue data,
not the forecast model's grid height or an automatic Open-Meteo elevation choice.

The parameter CSV was also downloaded: **8559 bytes**, **32 unique parameter
names**, and its SHA-256 matches STAC metadata. This does not establish actual
forecast field coverage or timestamp/aggregation semantics.

[Compact audit evidence](evidence/local_forecast_catalogue_2026-10-21.json)
records source URLs, UTC times, hashes, schema checks, duplicate findings and
the selected public rows. The audit used Python's standard-library CSV parser
with explicit Latin1 and semicolon settings, exact column/row-width checks,
finite numeric checks, grouping by the unchanged string type/ID pair and
full-row equality for duplicates. No integration parser or selection flow is
implemented. Forecast values, update cost, memory, CPU, accuracy and warning
coverage remain untested. The proposed display still needs usability review.

## L0: verify the catalogue at four public examples

Retain **8302 Kloten, Säntis, Gotthardpass and Albert-Heim-Hütte SAC** for
comparison. Do not infer OGD IDs from App IDs. First establish whether each
example exists in the current official catalogue. A missing example is a result;
do not silently substitute a neighbouring point.

The first bounded download is recorded above. On future rechecks, record UTC retrieval time, source URL, byte count,
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

**L0 catalogue audit is complete; L0 as a whole remains open.** Complete when the four records or their absence are documented,
identity/coordinate contracts are settled and the result-selection prototype is
understandable. A working App catalogue endpoint is not another prerequisite.

## L1: optional future processed-forecast evaluation

This is not a prerequisite for the approved catalogue-plus-ICON location
feature. Evaluate it only for a separately agreed forecast-source change.

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

**The initial source decision is settled:** use official catalogue coordinates
with the existing MeteoSwiss ICON Seamless forecast via Open-Meteo. Use small
regular PRs for catalogue/typed data, translated selection and compatible
forecast-location plumbing. Include
DE/EN/FR/IT and meaningful failure, duplicate, missing-height, time, cache,
migration and unload tests. Check HA forecast consumers and existing
automations separately. Do not explore the catalogue by changing production
or deleting existing HA entries.

## Implementation sequence confirmed on 23 October 2026

PR #54 integrates the modelled-pollen/AQ/UV source boundary. The separate
precipitation source/Recorder boundary is prepared in PR #55. This planning
branch is reconciled with development after #54; it does not duplicate #55.
The operator explicitly retains location/POI selection in the next feature
release. Complete these bounded packages before freezing features:

| Package | Deliverable | Evidence required before completion |
|---|---|---|
| Catalogue and location contract | Source-only bounded client/parser; typed identity/provenance and deterministic search over the official point catalogue. | Latin1/semicolon schema, identical/conflicting duplicates, distinct type/ID pairs, accents, ambiguous/empty results, invalid coordinates/heights, size limit, cancellation and private errors. |
| Forecast-location plumbing | Explicit saved catalogue choice, independent of measurement/warning roles; reuse the existing ICON coordinator/client. | Decide catalogue altitude versus provider grid/downscaling semantics from primary documentation; make request and cache identity agree. Preserve existing HA-home location semantics and IDs until a deliberate change. Test failure/recovery, migration and reload. |
| HA selection and user guide | Search by four-digit postcode or town/POI name, then confirm a labelled result; matching new-setup and reconfiguration paths, DE/EN/FR/IT help. | Explain forecast purpose before entry. Distinguish station/postal centre/POI and catalogue height. Keep warning postcode separate. Check Kloten, summit, pass and hut in the existing temporary HA. |

Keep L0's remaining selection/altitude contract work inside the first two
packages; the 21 October catalogue audit alone is not complete feature
acceptance. No live catalogue re-download is claimed by this plan update.
Persist confirmed coordinates/provenance so a temporary catalogue failure
does not move a selected location or make valid forecasts unavailable.
Never label a generic POI as a verified summit/pass/hut subtype solely from
its name. The practical walkthrough must make the different location roles
understandable without explaining internal provider IDs to the user.

## Scope boundaries

Stable 8.2.0 was published on 22 October and its HACS update was confirmed by
the operator; the particular instance was not explicitly identified. Clean
first installation and isolated restore were confirmed on 21 October, and
Beta2 setup with other locations on 22 October. Do not reopen those completed
checks. The new location feature needs its own focused acceptance in the
existing temporary HA; no additional permanent environment is required.

Full Silver/Gold evidence and HACS default-list submission remain separate
from this feature plan. Neither is awarded by passing our tests. No release,
installation, catalogue feature or HACS inclusion is claimed by this PR.

See the [development plan](NEXT_RELEASE_PLAN.md) and
[earlier POI evidence](POI_FEASIBILITY.md).
