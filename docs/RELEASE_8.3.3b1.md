# 8.3.3b1 — native icons and translated update errors test prerelease

**Notes version:** 1.1 · **Status updated:** 30 October 2026

**Published and accepted:** release **429321251**, published **30 October 2026
at 17:42:37 UTC**, from **d9fbc3fd49220b0ecc019d2babe0c173c46986f5**.
The immutable release/tag/notes and twelve earlier tags were independently
verified. The operator subsequently reported icons/personal choices and normal
operation OK on **HA Core 2026.10.4 / HA OS 18.4**; see the
[completed short check](ACCEPTANCE_8.3.3b1.md). The published body below is
retained verbatim. Stable 8.3.2 remains latest; [8.3.3](RELEASE_8.3.3.md) is
prepared, not yet published.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.2

- **Native entity icons.** All 24 previous custom symbols now use HA's
  icons.json mechanism: measured/modelled pollen, today/tomorrow forecast
  summaries, calculated HGT and the three warning binary sensors. The intended
  symbols stay the same, including the tree outlines for measured hazel/oak.
  Personal names and icons continue to take precedence. Other sensors keep
  their existing domain/device-class defaults.
- **Source errors in four languages.** The 21 source-update failure sites use
  19 stable message keys in English, German, French and Italian. HA can resolve
  these through its native exception-translation mechanism. Messages distinguish
  observations, warnings, measured/modelled pollen, air quality, forecasts,
  the separate station condition and precipitation errors without inserting
  private locations, URLs or raw provider exceptions.

Default icons are resolved by the frontend and may no longer appear as an
`icon` attribute in every backend state. Use the entity's value/state in
automations; see [icon resolution](ICON_TRANSLATIONS.md). Existing default
symbols are intentionally familiar, so this is not a dashboard redesign.
Dashboards with an explicit icon continue to use that configured override.

Source selection, independent locations, polling, measurement values,
availability/recovery and existing entity/statistic identities are retained.
There is no settings migration or registry rewrite. This package adds no new
forecast, warning or pollen source. See [translated errors](EXCEPTION_TRANSLATIONS.md)
and the [remaining Gold assessment](QUALITY_SCALE.md).

## Install only the announced test release

After actual publication is confirmed, use the existing maintained-fork HACS
entry to Download/Redownload **8.3.3b1**. Make prereleases visible and refresh
repository information if needed. Refreshing information alone does not
download files. Restart HA once, confirm the installed version and follow the
[three-step visual check](ACCEPTANCE_8.3.3b1.md), preferably on the existing
test HA. Keep the configured entry and existing backup.

The earlier settings, first-install and restore checks remain complete within
their reported scope. This package needs no deliberately broken source/network,
new entry, forced device action or blanket new 24-hour observation period.
Native tests already load every new error key in all four languages; a manual
provider failure is not required to prove translation coverage.

## Reviewed source and packaging boundary

Reviewed [PR #80](https://github.com/martins-netizen/ha-meteoswiss/pull/80) and
[PR #81](https://github.com/martins-netizen/ha-meteoswiss/pull/81) are regularly
merged. Combined source **c7c64d64e0efa582873d2e8e492531deb2aa6112**, tree
**43fc687bc766bbaf4fafd845b5a95449aea85713**, passes all eight combined PR
checks and seven actual merge checks. Each hosted HA 2026.8.3/2026.10.1 job
passes **1,996 tests plus 83 subtests**. This is source evidence; candidate
packaging has its own required checks.

The **41-file** component retains **39 non-version files** exactly from that
reviewed source; only manifest.json/version.py become **8.3.3b1**. The four
catalogues have **219 keys each**, with strings.json matching English. HACS/CH,
workflows and security guards are retained. Flow coverage is **406/406 statements
and 146/146 branches**; whole-component coverage is **3,516/3,517 statements
and 974/974 branches**, with the existing gates/four exclusions.

Hosted validation uses Python **3.14.10**, pip **26.2.2**, certifi **2026.10.23**
and offline uv. Historical HA-pinned uv versions remain explicitly unpatched
offline compatibility exceptions. These development checks do not update an
installed HA Core image. [Readiness](RELEASE_READINESS.md#prepared-833b1-test-candidate)
keeps source, packaging, publication and manual acceptance separate.

## Publication, recovery and support

Fixed **publish_meteoswiss_833_beta_v1.6.sh** checks the exact approved protected
development merge, the reviewed version-only component boundary, all successful
checks with expected apps, all twelve earlier tags and latest stable
**8.3.2 / ID 426633496**. Its only remote write creates **8.3.3b1** with
prerelease=true and make_latest=false. Matching retries verify; conflicting
tags/notes stop. It makes no HA connection or restart. See
[publication](PUBLISHING.md#833b1-test-candidate-prepared).

If normal operation regresses, redownload stable **8.3.2** from the same HACS
repository and restart once. Retain the existing entry, settings and history;
software rollback does not undo a personal icon you deliberately edited.
See [recovery](MIGRATION.md#if-something-fails).

Report issues to the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues),
or use [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports. This bounded package does not complete Gold or
confer an official HA quality tier.
