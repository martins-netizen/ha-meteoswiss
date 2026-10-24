# 8.3.0b4 — station-local weather condition test prerelease

**Document version:** 1.0 · **Updated:** 24 October 2026

**Status:** test-release track. Install only when this exact release is
announced; source version and package preparation do not establish publication.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and preserves the original MIT licence and attribution. It is not an official
MeteoSwiss product. Stable **8.2.0** remains the normal installation route.

## What this test package changes

- **A condition for the measuring station:** the original station weather row
  gains its own modelled condition, such as Cloudy, from MeteoSwiss ICON Seamless
  via Open-Meteo at the station's official catalogue coordinates and height.
  Temperature, humidity, pressure, wind and precipitation remain measurements.
  The selected town/POI forecast keeps its own place and condition.
- **Small, independently failing request:** only current code/daylight are
  requested, not another full forecast. Refresh normally occurs every ten
  minutes or at the current model interval's end. Cached data never outlive that
  interval. A failed or missing model condition affects no measured quantity;
  no POI condition or invented sunny/rainy value fills the gap.
- **Clear origin:** attribution credits both sources. Local `condition_*`
  attributes identify the modelled value, station role, time and availability.
  Existing setup/Configure field help explains this in German, English, French
  and Italian. Open-Meteo current-weather entries need no extra condition request.
- **More useful guidance:** README suggests choosing pollen and weather
  measuring stations near the HA home location. Cache Statistics documentation
  explains local lookups, hits and misses, with no target percentage or claim
  that these count network requests or forecast accuracy. HA's compact weather
  row can show a condition as an icon, with its text in detail/activity views.

See the [station condition guide](STATION_WEATHER_CONDITION.md) for source,
validity, load and failure boundaries, and the [cache explanation](USAGE.md#cache-statistics-what-the-numbers-mean).
The b3 calendar-day and shared-location settings corrections are retained.

## Install the announced version in the existing test HA

1. Keep the existing maintained-fork HACS entry, HA entry and backup.
2. Refresh repository information if needed, then choose Download/Redownload
   and explicitly select Release **8.3.0b4**. Refreshing information alone does
   not install files. Restart Home Assistant once after the download.
3. Confirm the installed version and follow the [focused b4 checklist](ACCEPTANCE_8.3.0b4.md).

No new integration entry, location setting or entity identity is introduced.
After deliberate test changes, restore the intended station and forecast choices.
Redownloading an older software version does not restore changed user settings.

## Reviewed source and publication boundary

PR #66 was approved and regularly squash-merged as
**95890788c12bfc675d41f81052c2143522434924**, preserving reviewed tree
**bf14f7f9adad561eb6e43a1b5854c29d792d767a**. This test package retains all
**37 non-version component files** from that source and changes only
manifest.json/version.py to b4. HACS/workflow files and earlier immutable tags
remain unchanged. The component contains **39 files**, including the new client.

The guarded **publish_meteoswiss_830_beta_v1.3.sh** follows the successful b3
publication route. It accepts only the exact approved protected development
head, verifies the source/version-only boundary, seven required checks, notes,
six earlier tags and unchanged latest stable **8.2.0 / ID 420392277**, and creates
only this prerelease with `make_latest=false`. It does not overwrite existing
tags/notes, install in HA or restart it. The older helpers keep their historical
38-file contracts and must not publish this new source.

## Validation and remaining acceptance

The functional source passes **1,559 tests plus 53 subtests** on each local
**HA 2026.8.3 and 2026.10.3 / Python 3.14.8**. Combined line/branch coverage is
**99.97753%** (3,474/3,475 statements, 976/976 branches), with every strict gate
and the four existing exclusions retained. Meaningful HA tests cover optional
source failure/recovery, interval-end refresh, true station metadata, independent
snowy POI forecasts, retained IDs/names after station changes, pending request
cancellation on unload and HA-owned session lifetime.

The package additionally tests all four publisher profiles, including their
real shell/gh-fixture/report path without live GitHub writes. The complete package
passes **1,603 tests plus 53 subtests** on each local HA version, including
**176 publisher-profile cases**. Coverage and strict gates are unchanged. Four complete
178-key UI catalogues retain English/strings.json parity. CI remains
HA 2026.8.3/2026.10.1, distinct from the additional local HA 2026.10.3 run.

Fresh provider probing from preparation was unconfirmed due to DNS resolution
failure. This does not diagnose the operator's connection or establish live
acceptance. The operator's successful b3 station switches and known today/
tomorrow values remain valid and need no repeat clean-install/restore or blanket
24-hour waiting period. This new condition source needs only its own focused
check. The separately reported UTM restart problem has no diagnosed cause.

This is a **test prerelease**, not stable 8.3.0, HACS default-catalogue inclusion
or an officially awarded HA quality tier.

## Recovery

Retain the backup and previously used announced beta/stable version. Review
[migration and recovery](MIGRATION.md) for deliberately changed settings and
consumer targets. No production dashboard or automation is rewritten by this
package or the publisher.
