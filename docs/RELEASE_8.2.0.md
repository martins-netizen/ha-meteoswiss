# 8.2.0 — first stable maintained-fork release

**Prepared candidate; not yet published.** Install this version only after
the [Releases page](https://github.com/martins-netizen/ha-meteoswiss/releases)
contains an explicitly published **8.2.0** release, with no prerelease flag.
A version in a branch or PR is not an available HACS download.

This community fork builds on LNKtwo/ha-meteoswiss and retains its MIT licence
and attribution. It is not an official MeteoSwiss product.

## What it provides

- Swiss station observations, official hourly rain statistics and native
  MeteoSwiss ICON Seamless forecasts through Open-Meteo.
- Active/upcoming postcode warnings through the MeteoSwiss App v3 feed, with
  the verified thirteen-family catalogue and the provider's event text.
  BAFU flood and SLF avalanche warnings are included when supplied by that
  shared feed; separate river gauges and avalanche bulletins are not provided.
- Measured pollen from an explicitly chosen station, alongside modelled
  pollen, air quality and independently available optional UV values.
- Bundled German, English, French and Italian interface text, including the
  distinction between weather, warning, forecast and measured-pollen locations.
- Reviewed handling of missing values, valid zeros, stale measurements and
  source failure/recovery, while retaining existing settings and supported IDs.

## Changes from the tested second beta

Only the manifest/module version changes from **8.2.0b2** to **8.2.0** within
the integration. The other 31 component/translation/brand files, HACS manifest
and workflows match the published beta at
`80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8`.
Release documentation and the guarded stable publication helper are updated
separately. No POI feature, new forecast model or architectural rewrite is added.

Beta2 added the required initial pollen-station choice, fifteen choices checked
against official metadata, and postcode help without internal App-code details.
Existing entries keep their saved pollen choice; an older entry without one
retains the documented Luzern fallback until explicitly changed in Configure.

## Installation and migration

New users follow [getting started](GETTING_STARTED.md). Once 8.2.0 is actually
published, explicitly select **8.2.0** under HACS Download/Redownload → Release,
download, restart HA and add MeteoSwiss. Select a measured-pollen station in the
first dialog, followed by the chosen weather source's location settings.

Existing users follow [migration](MIGRATION.md), retain their configured HA
entry and confirm their HACS software owner. Back up first; do not delete the
integration or recreate it to update from a beta.

When moving from old upstream/manual installations, review affected consumers:

- **Wind is 0; Slippery Roads is 4.** Wind/thunderstorm/rain filters use
  `[0, 1, 2]` where that is the intended meaning. Check active and upcoming
  warning filters, labels and lead times; do not replace every 4 indiscriminately.
- The unreliable locally calculated current-hour rain entity and the old
  forecast-only seasonal heating-degree entity are deliberately retired.
  The measured **Precipitation (10 minutes)** entity and official hourly rain
  archive remain. User-created helpers are not automatically removed.
- Retained entity/statistic IDs, personal precision and existing settings
  remain. Pair actual warning-consumer changes with their recovery route.
  Do not actuate devices merely to test an update.

Users already on the maintained betas should not repeat migrations that their
actual installation has already completed.

## Acceptance and supported environment

Minimum supported HA is **2026.8.3**. Automated checks cover that minimum and
the pinned current-HA test environment; HA **2026.10.2** also has local test
and operator-confirmed practical evidence. The
[readiness record](RELEASE_READINESS.md) distinguishes the exact sources:

- Beta1's deployed runtime completed its technical 24-hour/visual acceptance.
- The HACS 2.0.5 source switch, clean temporary first installation and isolated
  backup restore were operator-confirmed on 20–21 October 2026.
- On 22 October the temporary HA interface showed Beta2 and the existing
  600-second/Zürich pollen settings. The operator then completed new setup
  with other geographic locations and reported values.
- Both weather-source setup paths and pollen-choice persistence/retry have
  automated regression coverage. The operator did not identify the additional
  locations, source paths or pollen station separately. This is not a claim
  of a separate manual test of every combination or an independent beginner review.

Stable publication follows successful checks, regular merge and approval
of the exact stable packaging commit. No new blanket 24-hour window is
required for this version-only component change.

## Known limits and follow-ups

Real pollen stations can temporarily stop publishing current data; stale zero
values do not become current observations. [Dated station evidence](POLLEN_STATIONS.md)
is not a permanent live-status list. There is no automatic substitute station.

Forecasts are model output, not a guarantee of the most accurate model at every
point. Data and warnings may be delayed or incomplete; keep the official
warning channels available. An unavailable warning feed is not an all-clear.

Shared HTTP destination/redirect/response-size hardening and a safe CodeQL
route for external-fork contributions remain separate work, with the current
boundaries described in the [release review](RELEASE_REVIEW_2026-10-22.md).
No penetration-test result, zero-vulnerability claim, completed Silver/Gold
assessment or HACS default-catalogue approval is implied.

Location/POI selection and processed local forecasts remain later development.
The App v3 warning source stays in use. Report ordinary problems through the
[fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
and confidential vulnerabilities through
[private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories).
