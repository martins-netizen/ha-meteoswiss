# 8.3.1 — forecast repair notices and SwissMetNet station map

**Notes version:** 1.0 · **Prepared:** 26 October 2026

**Status:** stable promotion prepared, not yet published. The latest published
stable release remains 8.3.0 until the actual GitHub release confirms otherwise.
Published 8.3.1b1 has passed the operator's focused version/visual check.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from 8.3.0

- **Find a nearby SwissMetNet station:** weather-station help in setup and
  Configure links to the official MeteoSwiss measurement-network map in German,
  English, French and Italian. Locate the station on the map, then select its
  name in HA. The link contains no configured coordinates or station selection.
- **Resolve an unreadable saved forecast location:** an entry-specific HA Repairs
  notice links to the existing MeteoSwiss settings. Choose and confirm a valid
  point or explicitly return to the original base coordinates. Cancelling or
  failed validation keeps the saved setting and notice; no alternative place is
  selected automatically. Ordinary reloads preserve ignored notices, and entry
  disablement/removal cleans up only that entry's notice.
- **Keep temporary outages separate:** a provider or network outage does not
  create a saved-location repair. Observations, forecast data, measured pollen,
  modelled AQ/pollen/UV and the independent warning postcode retain their
  existing settings and source behaviour.

See [repair guidance](REPAIRS.md), [station selection](GETTING_STARTED.md#3-select-pollen-weather-and-warning-locations)
and the [source/settings reference](USAGE.md).

## Accepted source and version-only promotion

Test release **8.3.1b1 / ID 423899845** was published on **26 October 2026 at
05:54:44 UTC** from **c7b20c78d4273a33ba8c6f06c1834fc2f22c8665**. The
operator subsequently confirmed the requested installed-version and visual
check. This is reported focused acceptance, not a new independent HA-core,
registry, statistic or source-outage audit.

Stable packaging retains **38 non-version component files** from that accepted
source. Only manifest.json/version.py become **8.3.1**; there are **40 component
files**. HACS metadata, minimum HA, workflows, all four 180-key UI catalogues and
the nine existing tags remain unchanged. No new runtime behaviour is added
after the accepted beta, and the published beta/tag/notes are not rewritten.

The source passed **1,729 tests plus 63 subtests** on each local HA 2026.8.3
and 2026.10.3 / Python 3.14.8. Packaging adds a seventh fixed publication
profile; exact package results are recorded in [readiness](RELEASE_READINESS.md).
Coverage gates, strict modules and the four existing exclusions are retained.
Hosted CI covers HA 2026.8.3/2026.10.1 separately from the additional local
2026.10.3 run. Actual PR/head and regular merge checks must pass before publication.

## Update through the existing HACS entry

After stable **8.3.1** is announced, use Download/Redownload in the existing
maintained-fork HACS repository, select that version and restart HA once.
Refresh repository information first if needed; refreshing alone does not
download component files. Keep the configured HA entry and existing backup.

The [short stable update check](ACCEPTANCE_8.3.1.md) confirms the version actually
downloaded and continued intended places/values. The accepted beta UI check,
earlier first-install/restore and existing location checks need no repeat.
No new integration entry, storage-format migration, additional polling,
dashboard change or blanket 24-hour observation window is introduced.

Stable 8.3.0 remains the published recovery version until this promotion is
confirmed. Deliberately changed location settings are separate from software
rollback; see [migration/recovery](MIGRATION.md#if-something-fails).

## Publication and remaining work

**veroeffentliche_meteoswiss_stable_v1.4.sh** derives from the successful stable
V1.3 route. It requires the exact approved protected development merge, checks
the source/version-only boundary, seven merge checks and their provenance,
published 8.3.0 and accepted 8.3.1b1 IDs/flags, and all nine earlier tags. Only
stable **8.3.1** can be created, with draft=false, prerelease=false and
make_latest=true. Latest must be 8.3.0 immediately before creation and the exact
new release afterwards. Matching retries are read-only; conflicts stop.
Publication makes no HA connection, restart or device call. See [publishing](PUBLISHING.md#stable-831-prepared).

The [quality matrix](QUALITY_SCALE.md) records the bounded repair evidence and
remaining Gold work. Reconfiguration-route review, icon/error translations,
metadata/defaults, stale-device handling and authoritative multilingual place
aliases remain separate follow-ups. The App v3 warning source stays in use.

Use the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
for problems, or [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports.
