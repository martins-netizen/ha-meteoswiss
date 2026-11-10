# 8.3.4 — clearer data sources and verified HA 2026.11 support

**Notes version:** 1.0 · **Prepared:** 7 November 2026

**Prepared stable package, not published or installed.** It promotes the
published and operator-accepted 8.3.4b1 runtime with two component version
changes. Packaging review/checks, regular merge, publication and the short
actual stable update remain separate steps. Latest stable is still 8.3.3.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## Why upgrade from 8.3.3?

**8.3.4 is a maintenance and quality release for a clearer setup and a
well-tested upgrade to Home Assistant 2026.11.** Its practical benefits are:

- **Confidence on HA 2026.11.** The current compatibility suite uses HA
  **2026.11.0 and its matching official pytest-homeassistant package**, alongside
  a separate complete minimum-HA **2026.8.3** fixture. Hash-checked dependency
  locks make these checks reproducible. Normal operation of the released beta
  was also operator-confirmed on **Core 2026.11.0 / HA OS 18.4**. These are
  integration compatibility checks; they do not update HA Core or its Python.
- **A cleaner first setup.** Two technical troubleshooting helpers, the station
  catalogue and cache statistics, start disabled when first registered. Ordinary
  weather, forecast, warning and pollen sensors remain readily available.
  Enable either helper when needed. Existing enabled/disabled choices, names,
  icons and IDs are retained, so an enabled helper stays enabled after updating.
  See [diagnostic defaults](DIAGNOSTIC_DEFAULTS.md).
- **Know which source a value represents.** With Open-Meteo selected for current
  weather, its group and attribution now identify the **Open-Meteo Weather
  Forecast API and modelled current conditions**. The seven virtual groups are
  identified as data services. This makes the observation, forecast, pollen/AQ,
  warning and diagnostic groups easier to understand without inventing physical
  hardware metadata. See [provider labels](PROVIDER_METADATA.md).

For an existing installation already working well on 8.3.3, the main gain is
the verified HA 2026.11 baseline and clearer source/service information.
The cleaner default sensor list applies to new registrations. Your existing
configuration, personal names, IDs and diagnostic choices continue to apply.
Weather values, forecast models, polling and statistic identities are retained.

Native setup/reload and Configure/Reconfigure tests protect personal registry
choices and reuse all seven groups during pollen-station changes. These tests
provide regression assurance; they are not a claim that a user's database was
independently audited.

## Accepted beta, with version-only component changes

Published **8.3.4b1 / ID 437718127** dates from **7 November 2026 at 17:12:54 UTC**,
tag/source **1e5c5d1a7fc1c18d520e99189ae4dd5894621706**. The operator subsequently
reported normal operation on **Core 2026.11.0 / HA OS 18.4** and that everything
works. See [the bounded beta evidence](RELEASE_EVIDENCE_8.3.4b1.md).

Stable packaging retains **39 non-version component files** byte-for-byte;
only manifest.json/version.py become **8.3.4**. All **fifteen older tags**,
the beta's exact published body, four 219-key catalogues, HACS/CH, dependency
locks and workflow files are retained. The HGT statistic-behaviour change in
[PR #92](https://github.com/martins-netizen/ha-meteoswiss/pull/92) is reserved for
a later version with separate acceptance. This release keeps the accepted HGT
behaviour and does not delete registry or Recorder data.

## Update after publication

Once publication has been independently confirmed, update the existing entry
to **8.3.4** through **Settings → Marketplace** on HA 2026.11+, or HACS on older
HA. Refresh repository information if needed, then actually Download/Redownload
the release and restart HA once. Keep your existing entry and backup.
Confirm the installed version and continued normal operation using the
[short stable protocol](ACCEPTANCE_8.3.4.md).

Earlier accepted setup/settings, icon/error, first-install, restore and beta
checks stay complete within their reported scopes. No new source switch,
station change, deliberate outage, device command, name/ID list or blanket
observation wait is requested. If this update regresses, redownload stable
**8.3.3** from the same repository and restart once, retaining the entry/history.

## Publication and remaining quality work

Fixed **Stable Publisher V1.7** requires the exact approved protected packaging
merge, successful checks with expected provenance, the accepted beta source/body,
version-only component changes and all fifteen prior tags. Its sole remote write
creates published stable **8.3.4** with make_latest=true. Matching retries verify;
conflicting tags or bodies stop. It makes no HA connection or restart.
See [publication](PUBLISHING.md#stable-834-prepared) and
[readiness](RELEASE_READINESS.md#prepared-stable-834).

Device-class/statistics migrations, historical orphan review, remaining
translations and rule-specific exemptions stay separate. This release does
not complete Gold or confer an official HA quality tier on a custom integration.
