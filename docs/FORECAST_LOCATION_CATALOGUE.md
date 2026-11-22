# Official forecast-location catalogue foundation

**Guide version:** 1.5 · **Updated:** 22 November 2026
**Status:** included in the 8.3 runtime accepted as b4. Source clients,
saved identities/height routing and the four-language setup/Configure flow
are integrated. See [selection](FORECAST_LOCATION_SETUP.md) and
[current release evidence](RELEASE_READINESS.md). Do not edit HA storage manually.

## What this package supplies

The official MeteoSwiss catalogue identifies forecast points by **type and ID
together**. A station, postal code and mountain POI can share a bare number or
name. A forecast catalogue station does not prove an active observation sensor.
Keep the current observation station, warning postcode and pollen station
independent of the explicitly selected forecast location.

| Type | Meaning | Public example |
|---|---|---|
| 1 | Station | Zürich / Kloten, KLO, ID 59, catalogue height 426 m |
| 2 | Postal code | 8302 Kloten, ID 830200, catalogue height 436 m |
| 3 | Point of Interest | Säntis, ID 711, catalogue height 2502 m |

“8302 Kloten (postal code)” means the catalogue point assigned to that postal
code, not a post office or the operator's house coordinates. The source's
generic POI type supplies no individual summit/pass/hut subtype. Heights are
catalogue metadata, not proof of model grid elevation or forecast downscaling.

The pure forecast_locations.py module supplies immutable ForecastPoint,
ForecastCatalogue, ForecastLocation and ForecastSearchResult records.
A deliberate catalogue selection includes the point, fixed provider/source URL,
raw-byte SHA-256 and UTC retrieval time. The hash is a content version, not a
digital signature or provider issuance time. The [saved-location package](SAVED_FORECAST_LOCATION.md) now defines its offline
versioned entry representation, ICON altitude handling and matching cache keys.

## Parsing and atomic acceptance

The source is the fixed public
[MeteoSwiss point CSV](https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_point.csv).
Use its documented **Latin1/semicolon** format and fourteen named columns.
Reordered columns are accepted; missing/duplicate/extra headers or uneven rows
are rejected. Validate types, required identity/name, station/postal-code roles,
four ASCII postcode digits, finite coordinates/heights and WGS84 bounds.
Missing altitude remains unknown; real zero/negative altitude is retained.
Validate the named LV95 values without claiming an independent CRS transformation.

Collapse duplicate type/ID pairs only when all fourteen original field values
match. A conflict in even an unused language label rejects the whole snapshot.
Unknown point types, malformed CSV, control characters, non-finite coordinates
or an all-empty catalogue also fail atomically. Invalid fields and payloads do
not appear in formatted exception chains. Opaque IDs retain leading zeroes;
neither the postcode nor an App ID is inferred from a point ID.

## Explicit local search

Search runs over the downloaded catalogue and sends no search term to a server.
Names match across case, accents, punctuation and German ae/oe/ue spellings.
Public station abbreviations and postcode/name combinations are supported too.
A numeric query must be a four-digit postcode; it does not match an internal
catalogue ID. Exact names precede prefixes and other token matches, with a
deterministic type/ID tie-break. Ambiguity remains visible.

Queries are limited to 128 characters. Empty or one-character queries yield no
results. Return up to twenty candidates by default, with a caller-specified
integer limit from one to fifty. The full match count and truncated flag allow
the future dialog to ask for a narrower search. Never auto-select the first
candidate, a same-named point of another type or a neighbouring place.

For example, in a contributor probe using one shared client and borrowed session:

```python
from .forecast_location_client import MeteoSwissForecastCatalogueClient
from .forecast_locations import ForecastPointType, search_forecast_locations


async def catalogue_example(session):
    client = MeteoSwissForecastCatalogueClient(session)
    catalogue = await client.async_get_catalogue()
    candidates = search_forecast_locations(catalogue, "Saentis")
    # Explicit public example: choose the known POI, never candidates.points[0].
    selected = catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711")
    return candidates, selected
```

This example does not update HA. Future flows should reuse the client across
searches and offload catalogue-wide search from the event loop. They must also
handle a removed identity explicitly rather than substitute another point.

### Multilingual postal search names

Searching for `Morat` finds **3280 Murten**. `Merlach` finds **3280 Meyriez**,
which has a different forecast ID despite sharing the same four-digit postcode.
The displayed and saved name comes from the live MeteoSwiss catalogue. Local
aliases apply only to postal points whose ID and full catalogue name both match
the checked table. Stations and mountain POIs retain their catalogue names.

The 22 November 2026 table covers 184 postal forecast points in 94 settlements
with 120 distinct additional spellings. These include German, French, Italian
and Romansh endonyms and exonyms as recorded by swisstopo. For example,
`Genf`, `Ginevra` and `Genevra` all match Genève. Coverage follows the source
name groups and the verification below. Some settlements have a source name in
only one language. An exonym can have customary or informal status.

The offline generator accepts a postal point only when all three sources agree:

1. The point has MeteoSwiss type 2. Its ID equals the register's four-digit
   postcode followed by its two-digit additional number. Exactly one active
   ZIP area has that key and contains the MeteoSwiss LV95 coordinates.
2. The ZIP area's locality foreign key identifies an active official locality
   with the exact catalogue name. Its polygon contains exactly one swissNAMES3D
   settlement centre (`TLM_SIEDLUNGSNAME_ZENTRUM`, `Ort`) with that primary name.
3. Additional names must share that centre's `NAMENGRUPPE_UUID` and be marked as
   endonyms or exonyms in one of the four national languages. Unmatched and
   ambiguous records are skipped. This procedure never selects a nearby centre.

| OGD input used on 22 November 2026 | SHA-256 of the downloaded file |
|---|---|
| [MeteoSwiss forecast points](https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/ogd-local-forecasting_meta_point.csv) | `3dd6b9fbdc0b24df507153ef75fc09eef9f230d6d0c20de9a91418c27fe7e069` |
| [swissNAMES3D, 29 April 2026, LV95 CSV](https://data.geo.admin.ch/ch.swisstopo.swissnames3d/swissnames3d_2026/swissnames3d_2026_2056.csv.zip) | `e488e19f10a392e75aec35f7dc0a915dde1fe859b16e86eb36756854424f96dd` |
| [Official index of localities, 1 November 2026, LV95 FileGDB](https://data.geo.admin.ch/ch.swisstopo-vd.ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz_2056.gdb.zip) | `a593bcc2b21a439f70d74e5eae136ae502fb1a47a73daf2a4f4d125f6e0bb77e` |

To update, download the three files, record their dates and hashes, and review
the resulting diff. The contributor script uses GDAL's Python bindings with
OpenFileGDB and GEOS. Home Assistant uses the checked-in table offline.

```sh
python3 scripts/generate_forecast_location_aliases.py \
  ogd-local-forecasting_meta_point.csv swissnames3d_2026_2056.csv.zip \
  ortschaftenverzeichnis_plz_2056.gdb.zip > postal_aliases.py
diff -u custom_components/meteoswiss/forecast_location_aliases.py postal_aliases.py
```

**Data attribution.** Source: MeteoSwiss. Settlement names and boundaries:
Federal Office of Topography swisstopo. The derived data retain the providers'
attribution requirements. See the [MeteoSwiss OGD terms](https://opendatadocs.meteoswiss.ch/#terms-of-use)
and [swisstopo OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices).

## Fetch, cache and failure boundary

forecast_location_client.py borrows its caller's verified session. It owns no
HA object, poller or session closure. The shared HTTP helper enforces the fixed
HTTPS destination, refuses redirects and bounds both wire and decoded bodies
to **2 MiB**. Download/retry has a **30-second total deadline**, at most three
transient attempts and the existing Retry-After policy. Malformed payloads are
not retried. CSV parsing runs off the event loop; cancellation propagates from
download or parsing without committing a snapshot or imposing a failure pause.

A client-instance lock coalesces simultaneous loads. Its successful snapshot
has an original **24-hour monotonic TTL**; reads do not extend expiry. Failed
refreshes impose a **300-second retry pause** and raise a private unavailable
error. They preserve the previous immutable snapshot without returning it as
fresh success. The explicit last_good_snapshot property retains original
hash/retrieval time and may be stale. It is a future recovery aid, not a reason
to replace an already confirmed location or make old forecasts appear current.
This source client supplies no global factory or disk cache. Confirmed
selection persistence is owned by the separate saved-location contract.

## Evidence and remaining acceptance

A real read-only source-client probe on **23 October 2026, 17:35:21 UTC** fetched
the 828864-byte catalogue, parsed **5816 distinct points** and four identical
duplicate rows: 1114 stations, 4071 postal codes and 631 POIs. Source bytes have
the same SHA-256 as the independently audited 21 October snapshot. Searches
distinguished Kloten postal code/station and Säntis station/POI, and found
Gotthardpass and Albert-Heim-Hütte SAC. A second call reused the same snapshot;
the caller retained session ownership. See the
[dated source/client evidence](evidence/forecast_location_catalogue_2026-10-23.json).
Source: MeteoSwiss.

The eight-row public fixture stores the exact decoded source fields as UTF-8
for GitHub review; transport tests re-encode it as Latin1. It includes one real
identical station duplicate. Focused tests cover identities, provenance,
schema/roles/coordinates, duplicate conflicts, missing heights, search ambiguity,
limits/ranking, original TTL, coalescing, failure pause/recovery, retained old
metadata, privacy, cancellation, total timeout and the actual shared HTTP path.

This establishes catalogue mechanics. The saved-location package adds compatible
offline routing and height semantics; the [translated HA setup/reconfiguration](FORECAST_LOCATION_SETUP.md) now consumes
this foundation; focused temporary-HA acceptance remains required. ICON Seamless and App v3
warnings retain their source roles. No HA installation, release or quality-tier/HACS-list
acceptance follows from this foundation.
