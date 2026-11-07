# 8.3.4b1 — diagnostic defaults and provider metadata test prerelease

**Notes version:** 1.0 · **Prepared:** 7 November 2026

**Prepared candidate, not published or installed.** Stable 8.3.3 remains latest.
Packaging PR/head/merge checks, publication and actual HA acceptance are separate
steps. The publication helper exports the body below from the approved merge.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.3

- **Optional diagnostics start disabled only on first registration.** The shared
  station-catalogue and cache-statistics helpers are troubleshooting tools.
  Existing enabled, user-disabled and integration-disabled entries retain their
  choice, personal names/icons and IDs. Ordinary environmental entities remain
  enabled. Required station metadata and provider polling do not depend on
  these optional helpers. See [diagnostic defaults](DIAGNOSTIC_DEFAULTS.md).
- **Seven virtual groups are identified as data services.** Group identifiers,
  device IDs and personal names are retained. These groups do not represent
  physical hardware with invented serial or firmware information.
- **The alternative current-weather source has accurate provenance.** Its group
  uses Open-Meteo / Weather Forecast API labels and its weather/current-value
  attribution describes modelled current conditions. MeteoSwiss observations,
  ICON forecasts, measured pollen, modelled pollen/AQ and warnings keep their
  independent sources. See [provider metadata](PROVIDER_METADATA.md).
- **Pollen-station changes are verified without deleting groups.** Native
  Configure/Reconfigure round trips for both current providers reuse all seven
  groups and every entity binding. Personal names, icons, aliases, precision,
  hidden/disabled choices and IDs survive. No cleanup pass is added. This does
  not inventory possible historical orphans from earlier versions.

Source selection, values, units, schedules, source failure/recovery and retained
Recorder/statistic identities do not change. Existing personal names take
precedence over default group names. The test tooling now covers HA 2026.11.0
with the matching official pytest-homeassistant package and a separate complete
minimum-HA 2026.8.3 fixture; test dependency installs are hash-checked. These
development checks do not update an installed HA Core/Python image.

## Focused installation and acceptance

Only after actual publication is confirmed, select **8.3.4b1** in the existing
maintained-fork Marketplace entry (HACS on older HA), making prereleases visible
and refreshing repository information if necessary. Download/Redownload the
selected version; a metadata refresh alone does not install it. Prefer the
existing test HA and entry. Keep the existing backup and restart HA once after
the download. Follow the [focused version/registry check](ACCEPTANCE_8.3.4b1.md).

Existing diagnostic helpers are not expected to switch off during an update.
Do not recreate an entry or delete devices to demonstrate a new-registration
default. Do not change a production source solely to inspect Open-Meteo labels;
the native tests cover that path if no alternative-source entry is available.
Earlier settings, icons/errors, first-install and restore acceptance stay closed.

## Source and publication boundary

Regularly merged [PR #88](https://github.com/martins-netizen/ha-meteoswiss/pull/88)
and [PR #89](https://github.com/martins-netizen/ha-meteoswiss/pull/89) culminate in
reviewed source **5a7eae00963d47294281da8812cb1ede35713b7f**, tree
**dded226f403b4425f02034d40c7f849572b1a401**. All seven actual source-merge
checks passed. Source local suites each passed **2,126 tests plus 83 subtests**
on HA 2026.11.0 and 2026.8.3; packaging has its own complete-suite validation.
Source coverage is **3,530/3,531 statements, 976/976 branches**, combined
**99.977812%**, with all strict coverage/security gates retained.

Of **41 component files**, **39 non-version files match that source exactly**;
only manifest.json/version.py become **8.3.4b1**. Four 219-key catalogues,
English/source parity, icons, HACS/CH, workflow files and dependency locks remain.
The fixed **publish_meteoswiss_834_beta_v1.7.sh** checks the exact approved
protected development packaging merge, version-only component boundary, check
provenance and all **fourteen** existing tags. Its sole remote write creates
this prerelease with make_latest=false. Stable **8.3.3 / ID 429354633** must
remain latest. Matching retries verify; conflicting tags/notes stop. It makes
no HA connection, installation or restart. See [publication](PUBLISHING.md#834b1-test-candidate-prepared).

If operation regresses, redownload stable **8.3.3** from the same repository and
restart once, keeping the existing entry, settings and history. Software rollback
does not undo personal edits. See [recovery](MIGRATION.md#if-something-fails).
Report issues to the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
or use [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories).
Remaining device classes, translations and historical orphan questions stay
separate; this bounded test package does not complete Gold or confer an official
HA quality tier.
