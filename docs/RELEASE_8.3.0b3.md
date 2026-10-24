# 8.3.0b3 — calendar days and location settings test prerelease

**Document version:** 1.0 · **Updated:** 24 October 2026

**Status:** prepared test package. The approved packaging merge, explicit
prerelease publication and focused HA acceptance remain separate steps.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and preserves the original MIT licence and attribution. It is not an official
MeteoSwiss product. Stable **8.2.0** remains the normal installation route.

## What this test package fixes

- **All three locations in one Configure dialog:** change the MeteoSwiss
  weather measuring station, measured-pollen station and forecast location
  together through the existing entry's gear. The separate warning postcode
  is there too. A postcode/town/POI search continues inside the same flow;
  cancelling an unfinished flow preserves every old choice.
- **Calendar-day values through clock changes:** retain aligned native daily
  aggregates, otherwise use complete hourly coverage of the actual 23/24/25-hour
  Swiss day. Both repeated autumn hours and the final midnight rain bucket count.
  Missing individual coverage remains unknown. Daily scalars, HGT and the
  forecast weather entity use the same validated result.
- **Clear place roles:** the HA home position is a general HA setting,
  independent of the measuring stations. It supplies default model coordinates;
  an alternative current-data entry can have explicit base coordinates. Choosing
  a forecast POI does not move measured weather, measured pollen or warning area.

The existing single ICON query includes the elapsed part of today and retains
the 120-hour rolling forecast. No extra coordinator, source or polling schedule
is introduced. [The correction guide](CALENDAR_AND_LOCATION_SETTINGS.md) explains
aggregation attributes, independent roles, history and evidence limits.

## Existing entries and history

Keep the existing integration entry, selected forecast point, entity IDs,
personal names and individual legacy intervals. A loaded entry reloads once
after a confirmed setting change. The forecast-only **Reconfigure** shortcut
remains available.

A deliberate station change continues retained observation-entity histories
with readings from the new station. Earlier readings are not rewritten.
External hourly precipitation archives remain station-specific; charts that
explicitly target the old station's archive keep that target until changed.
The config-entry unique ID follows a deliberate observation/postcode identity
change for duplicate detection; the entry ID and entity unique IDs are retained.

## Install only after the publication is announced

1. Keep the test-system backup and note the intended weather, pollen, forecast
   and warning choices. Use the existing maintained-fork HACS entry.
2. Refresh its information if necessary. Open Download/Redownload, explicitly
   select Release **8.3.0b3**, confirm the download and restart HA once.
   Refreshing information alone does not install the new files. If the release
   is absent, stop and wait for publication; do not select a branch.
3. Confirm the installed version and follow the [focused checklist](ACCEPTANCE_8.3.0b3.md).
   Do not delete/recreate the integration.

## Reviewed source and publication boundary

The functional source is the approved PR #63 merge
**97338f68038eab80c75c2028c9deb5e24ad552e6**, tree
**22a20a95027c9aa45b108033908062fc8c1422c5**. This package retains all 36
non-version component files and changes only manifest.json/version.py to b3.
HACS and workflow configuration remain unchanged. The English notes and all
four UI languages ship with the package.

Use **publish_meteoswiss_830_beta_v1.2.sh** with the full approved packaging
merge commit: first `--check`, then `--publish`. It checks the exact protected
development head, component blobs, version-only differences, required checks,
notes, prior immutable tags and unchanged latest stable 8.2.0. Its only remote
write creates this prerelease; repeat verification does not retag or overwrite
notes. No HA connection, installation or restart is performed by the publisher.
The previous b1/b2 publishers remain historical and unchanged.

## Validation and remaining acceptance

The functional correction passed 1,440 tests plus 53 subtests on both local HA
2026.8.3 and 2026.10.3, with all strict source/flow coverage gates retained.
Packaging additionally exercises the existing publisher regressions for b1,
b2 and b3, including the real shell/gh-fixture/report path without GitHub writes.
The complete package passed **1,484 tests plus 53 subtests** on both local
**HA 2026.8.3 and 2026.10.3 / Python 3.14.8**. Its 132 publisher-profile cases
cover all three revisions. Coverage is **99.97671%** combined (3,355/3,356 lines,
938/938 branches), with all strict gates and four existing exclusions retained.
Four complete 178-key translations match strings.json/English. Current CI
(2026.8.3/2026.10.1) and local HA targets remain explicitly distinguished.

Fresh provider access from the preparation environment was blocked by DNS for
both old and history-enabled requests. That does not establish a provider outage
at the operator's HA. Actual fresh values and frontend behaviour belong to the
new package's focused acceptance. The successful existing-beta HA 2026.10.3
test is retained, not presented as acceptance of this package.

This is a **test prerelease**. It does not establish a stable 8.3.0 release,
official HACS default-catalogue inclusion or an HA Silver/Gold tier. Completed
8.2.0 clean-install/restore checks remain valid; no blanket new 24-hour period
is added for this focused correction.

## Recovery

Retain the backup and the previously used announced beta/stable version.
During testing, restore intended locations through the common dialog after any
deliberate changes. A software redownload alone does not restore previous user
settings. For a complete reversal of deliberate configuration changes, use the
retained backup and the [migration/recovery instructions](MIGRATION.md).
