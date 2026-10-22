# Bounded HTTP source reads

**Status:** unreleased development change after stable 8.2.0.
**Review date:** 22 October 2026. This is scoped hardening, not a penetration test.

## Contract

All active source clients use `http.py`. Each call supplies its own fixed host:
OGD observations, metadata, measured pollen and archives use `data.geo.admin.ch`;
weather/UV use `api.open-meteo.com`; AQ/model pollen use
`air-quality-api.open-meteo.com`; App v3 warnings retain
`app-prod-ws.meteoswiss-app.ch`. A metadata asset cannot select another host.
Only HTTPS with the exact host and default/explicit port 443 is accepted.
Credentials, fragments, alternate ports, IP destinations, host suffixes,
backslashes and control characters are rejected before a request.

Automatic redirects are disabled. Every 3xx, including same-host redirects,
is a source failure; no Location target is fetched. None of the sampled OGD
URLs below redirected. A future provider move requires an explicit destination
review rather than silently broadening this boundary.

| Body class | Wire-byte limit | Decoded-byte limit |
|---|---:|---:|
| JSON, including STAC metadata | 2 MiB | 2 MiB |
| Station catalogue | 2 MiB | 2 MiB |
| Current/recent weather CSV and measured pollen | 16 MiB | 16 MiB |
| Hourly historical decade CSV | 64 MiB | 64 MiB |

Limits are enforced while streaming, independently of Content-Length. The
client disables automatic decompression and advertises gzip/deflate only.
Identity, gzip and standard zlib-wrapped deflate are accepted; other/stacked
encodings, corrupt/truncated streams and trailing compressed data are refused.
Decompression requests at most the remaining decoded budget plus one byte,
so an inflated body is never fully expanded merely to check its length.
These are bounded input budgets, not a claim that the whole HA process uses
only that memory: parsing/decoded strings can require additional memory.

The existing HA-owned session, TLS verification, 30-second request timeout,
outer source budgets, retry counts, Retry-After handling and cancellation remain.
Policy/size/encoding failures are ValueErrors and do not trigger transport
retries. The helper logs nothing and its errors contain no requested URL or
payload. Source adapters retain their redacted errors and failure/recovery
semantics. Rejected warnings cannot become an all-clear; rejected precipitation
cannot enter Recorder as zero. Optional UV remains independent of valid AQ.
Entity IDs, statistic IDs, source models, warning codes, locations, CSV cp1252
and the official archive importer are preserved.

## Dated provider samples and limits of evidence

Read-only OGD samples on 22 October used the published KLO station item at
`https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/items/klo`.
All sampled assets used the exact OGD host and returned without a redirect.

| Official asset | Actual bytes |
|---|---:|
| STAC station item JSON | 6,193 |
| `ogd-smn_klo_t_now.csv` | 6,134 |
| `ogd-smn_klo_t_recent.csv` | 5,882,319 |
| `ogd-smn_klo_h_now.csv` | 1,336 |
| `ogd-smn_klo_h_recent.csv` | 1,038,352 |
| `ogd-smn_klo_h_historical_1980-1989.csv` | 7,836,982 |
| `ogd-smn_klo_h_historical_1990-1999.csv` | 8,716,101 |
| `ogd-smn_klo_h_historical_2000-2009.csv` | 9,701,115 |
| `ogd-smn_klo_h_historical_2010-2019.csv` | 12,566,240 |
| `ogd-smn_klo_h_historical_2020-2029.csv` | 7,682,391 |

These current samples justify headroom for real archives; they do not prove a
provider-wide maximum, future response sizes, all stations or the live behaviour
of every other service. No additional location-bearing App/AQ/forecast probe
is claimed. Offline tests exercise those clients through the shared transport.
A future oversized response must remain unavailable until its legitimate
size/schema has been checked; do not remove limits or manufacture data.

## Verification and next acceptance

Local regression suites pass 917 tests and 14 subtests on HA 2026.8.3 and
2026.10.2. Existing HA 2026.8.3/2026.10.1 CI pins remain unchanged. The new
transport and all already-gated active modules require full line/branch coverage.
Tests include malicious metadata, destination isolation, each redirect status,
missing/dishonest lengths, exact limits, chunked reads, split compressed streams,
compression expansion, corrupt/truncated content, cancellation, session ownership,
archive budgets/encoding, warning failure and measured-pollen failure.

Before the next runtime release, test a reviewed package in the existing
temporary HA: current observations, ICON forecast, active/upcoming warnings,
measured pollen, AQ/UV and official hourly/archive statistics. Confirm retained
IDs/settings and recovery after a real ordinary refresh. This is a focused
transport acceptance, not a requirement to repeat clean installation, restore
or a blanket 24-hour test. Stable 8.2.0 and the running HA are not changed by
this development PR. POI selection, CodeQL fork analysis and Silver/Gold
assessment are separate work.
