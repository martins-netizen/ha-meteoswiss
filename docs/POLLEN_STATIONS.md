# Verified measured-pollen stations

**Evidence date:** 21 October 2026. **Source:** MeteoSwiss.

The setup/Configure list was checked against the actual
[OGD station metadata](https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/ogd-pollen_meta_stations.csv)
and the
[STAC collection items](https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen/items?limit=100).
Both identify **15 supported stations with current-hourly file assets**.
Every one of those 15 hourly URLs returned HTTP 200 during the check.
Station names and identifiers below come from the metadata, not from weather
stations or a manually inferred location mapping.

| Code | Official station name |
|---|---|
| PBE | Bern |
| PBS | Basel |
| PBU | Buchs, SG |
| PCF | La Chaux-de-Fonds |
| PDS | Davos / Wolfgang |
| PGE | Genève |
| PLO | Locarno / Monti |
| PLS | Lausanne |
| PLU | Lugano |
| PLZ | Luzern |
| PMU | Münsterlingen |
| PNE | Neuchâtel |
| PPY | Payerne |
| PSN | Sion |
| PZH | Zürich |

Some narrative provider pages say 16 stations while the technical guide says
15. The integration uses the actual station metadata and matching hourly
assets. The old **Coldrerio / Mezzana (BLR)** choice was not in that metadata;
its STAC item had no assets and its constructed hourly URL returned HTTP 403.
It is therefore removed from the supported choices. This does not establish
whether a physical monitoring site exists there. Other empty items, PME and
PVI, and the PJU item without an h_now asset do not establish current-hourly support.

## A real station can have stale data

Availability is separate from station identity. At the check time, 12 of the
15 files had measurements accepted by the integration's existing four-hour
freshness policy. Three files were reachable but stale:

| Station | Latest source measurement, UTC | Europe/Zurich local time | Result at check time |
|---|---|---|---|
| Zürich (PZH), for comparison | 21 October 2026 19:00 | 21 October 21:00 CEST | Current; seven valid zero concentrations. |
| Luzern (PLZ) | 19 October 2026 16:00 | 19 October 18:00 CEST | Stale; unavailable. |
| Buchs, SG (PBU) | 19 October 2026 12:00 | 19 October 14:00 CEST | Stale; unavailable. |
| Neuchâtel (PNE) | 11 October 2026 01:00 | 11 October 03:00 CEST | Stale; unavailable. |

These are dated observations, not permanent station-status labels. The files
do not explain the publication gaps. A real zero remains valid when fresh;
old zero values must not imply a current all-clear. The code does not silently
substitute another station. Temporarily stale real stations remain selectable
and recover on a later valid scheduled refresh. Existing saved settings are
not automatically rewritten, including an old unsupported BLR selection; such
a user must choose a supported station in Configure.

No additional live pollen check is required to complete otherwise valid weather
setup: a temporary optional-source outage must not prevent creating the entry.
Measured-pollen station selection does not change the modelled forecast location.

## Reproducible regression evidence

[The frozen evidence fixture](../tests/fixtures/pollen_stations_2026-10-21.json)
records retrieval time, source URLs, SHA-256 hashes, official names/identifiers,
hourly-asset membership and the unmodified Zürich/Luzern CSV sample contents.
Tests compare the selectable list with that external snapshot and check that
the real current Zürich / stale Luzern examples follow the existing parser's
freshness policy. CI does not rely on live network requests.

For a later catalogue review, re-fetch metadata and all STAC pages, compare
identifiers and hourly assets, and record the new evidence date. Do not remove
a station merely because its most recent measurements are temporarily missing.

See [the provider's pollen documentation](https://opendatadocs.meteoswiss.ch/a-data-groundbased/a7-pollen-stations)
and [setup/settings](USAGE.md).
