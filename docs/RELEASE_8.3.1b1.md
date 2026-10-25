# 8.3.1b1 — repair notices and station-map help test prerelease

**Notes version:** 1.0 · **Prepared:** 25 October 2026

**Status:** prepared candidate, not a published release. Install only after
publication of this exact version is announced. Stable **8.3.0** remains the
normal installation route.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.0

- **A useful configuration notice:** when a saved forecast location cannot be
  read, HA Repairs identifies the affected entry and links to its existing
  MeteoSwiss settings. Choose and confirm a valid forecast point or explicitly
  return to the original base coordinates. Cancellation and failed validation
  retain the previous settings and notice; no replacement location is invented.
  Ordinary reloads retain ignored notices, and disabling/removing an entry
  cleans up its own notice. See [repair guidance](REPAIRS.md).
- **Find a nearby weather station:** the weather-station help in setup and
  Configure links to the official MeteoSwiss measurement-network map in German,
  English, French or Italian. Locate a SwissMetNet station there, then select
  its name in HA. The static link contains no configured coordinates or station
  selection. See [the setup guide](GETTING_STARTED.md#3-select-pollen-weather-and-warning-locations).
- **Keep failures distinct:** a temporary provider or network outage does not
  create a saved-configuration repair. Forecast availability still follows its
  own source. Weather measurements, measured pollen, modelled AQ/pollen/UV and
  the warning postcode retain their independent settings and source behaviour.

The normal settings dialog, observation intervals, entity/statistic identities,
forecast source and App v3 warnings are retained. No integration entry, schema
migration, dashboard change or additional provider polling is introduced.

## Install only the announced test package

1. Use the existing temporary/test HA, configured entry and maintained-fork HACS
   repository. Retain the existing backup and intended location choices.
2. Once this release is announced, refresh repository information if needed.
   Make prereleases visible for this repository if HACS hides them. Choose
   Download/Redownload and explicitly select **8.3.1b1**; refreshing information
   alone does not install the package.
3. Restart HA once after downloading. Check the installed version and complete
   the [short UI checklist](ACCEPTANCE_8.3.1b1.md).

Do not delete the existing integration or create a new entry for this update.
Publication does not install software in HA. The earlier first-install,
restore, location and stable-update checks remain complete; no repeated restore
or blanket 24-hour wait is required.

## Reviewed source and publication

[PR #70](https://github.com/martins-netizen/ha-meteoswiss/pull/70) was approved
and regularly merged as **22004177b96adb4452fdbd116174915de4dc18cf**, tree
**6bb5eb45e10cd3390b32e5901ccbe288a6591a63**. All eight PR checks and seven
post-merge checks succeeded. This package retains its **38 non-version
component files**; only manifest.json/version.py become **8.3.1b1**. The
component has **40 files**. HACS metadata, workflows and all eight existing
release tags are retained.

The new **publish_meteoswiss_831_beta_v1.4.sh** derives from the proven b4
publisher. It accepts only the exact approved protected development head,
verifies the source/version-only boundary and seven merge checks, and creates
only this prerelease with **make_latest=false**. Latest stable must remain
**8.3.0 / ID 422817883**, including immediately before creation and afterwards.
Matching retries verify the existing release without posting again; conflicting
tags/notes stop. It makes no HA connection or restart. Earlier fixed-profile
publishers and immutable releases remain unchanged. See [publication](PUBLISHING.md#831b1-test-candidate-prepared).

## Evidence and remaining UI acceptance

The source's native HA tests exercise correction/confirmation, cancellation,
failed validation, multiple entries, ignored notices, provider outages,
disable/reenable/removal, retained entity IDs and DE/EN/FR/IT text. Native setup
and options tests verify URL-placeholder interpolation and language fallback;
all four official map pages were checked successfully during PR #70.

The package adds fixed-profile publication/refusal/retry tests, including
preservation of stable 8.3.0 and rejection of unreviewed repair-code changes.
Exact full-suite and coverage results are recorded in [readiness](RELEASE_READINESS.md#prepared-831b1-test-candidate).
CI covers HA 2026.8.3/2026.10.1; additional local tests use HA 2026.10.3.
Four complete **180-key** UI catalogues retain English/source parity.

Real HA UI acceptance of these new links/notices remains pending. Do not
deliberately corrupt saved settings, force an outage or recreate an entry to
produce a notice. Automated native-HA regressions cover the damaged-selection
cases; a valid existing entry should have no new repair notice.

## Recovery and support

Retain the existing backup and published stable **8.3.0**. If needed, redownload
8.3.0 through the same HACS repository and restart once. The package introduces
no new configuration format. Software rollback does not undo a location choice
you deliberately changed; restore intended settings separately.

Report problems to the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues),
or use [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports. No new official HA quality tier is claimed.
