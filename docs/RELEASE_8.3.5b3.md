# 8.3.5b3 — Native HGT cleanup test prerelease

**Notes version:** 1.0 · **Package date:** 15 November 2026

The release catalogue determines publication and availability. These package
notes do not claim installation, production deletion or operator acceptance.
Stable 8.3.4 remains the regular stable release.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## Recommended HGT migration: remove obsolete forecasts

8.3.5b3 adds a native Home Assistant repair for complete removal of obsolete
HGT forecast statistics. Earlier versions recorded changing forecasts as
measurement statistics; b2 preserved those values in an archive. Those old
averages are not measured heating degree days and receive no new values.

The repair recommends deletion and lists the exact statistic IDs. **Opening
or cancelling the repair does not delete anything. Explicit confirmation
permanently removes the selected hourly and short-term series and their
metadata from Recorder, without creating a replacement archive.** The result
is verified before completion and the live forecast's cached archive reference
is cleared. Keep an existing protected, usable backup outside HA if recovery is
required; software downgrade alone cannot restore deleted statistics.

The same normal upgrade handles attributable earlier daily forecast series,
b2 archives and retired season identities, including disabled forecast sensors
within a loaded integration entry. It needs no Mac script or entry recreation.
Fresh installations and already cleaned entries need no deletion step. Missing
ownership, conflicting metadata or a reused entity ID never authorises guessed
deletion; see [upgrade paths and limits](UPGRADING_8.3.5.md).

1. Once **8.3.5b3** is published, update the existing maintained-fork Marketplace
   installation normally. Keep the existing entry, IDs and personal settings.
2. Open **Settings → System → Repairs → Remove obsolete HGT forecast statistics**.
   Review the listed old forecast series and confirm the recommended removal.
3. Confirm that the cleanup notice disappears, the forecast still works, and
   `forecast_statistics_archive` is empty with `hgt_legacy_cleanup_required: false`.
   The [focused protocol](ACCEPTANCE_8.3.5b3.md) separates fresh/previously cleaned
   entries from a deletion that was actually exercised.

Current HGT forecasts, ordinary state history and entity/unique/device IDs are
retained. Wind arithmetic archives, live circular wind statistics, precipitation
and unrelated series are outside this deletion. Existing backups are retained.
Logical Recorder deletion does not promise physical erasure from database pages
or copies. An archive's former `ready` status alone is not proof of cleanup.

## Official measured HGT is separate

Official SwissMetNet OGD directly provides HGT 12/20 as `xno000d0/m0/y0`, including
KLO. The [source plan](HGT_OGD_PLAN.md) defines a separate measured series with
historical backfill and ongoing corrections. **This package does not yet
implement that importer or resume measured HGT long-term statistics.** Current
forecast values continue; removed forecast averages are not needed as OGD input.

## Reviewed source and package boundary

The runtime is accepted [PR #112](https://github.com/martins-netizen/ha-meteoswiss/pull/112),
regularly merged at **9d7be4f935e751314bb950c70869bf09b143a6b1**, tree
**e5dc7499c52d3b379847cf29358b67048a87c320**. All ten head checks and nine required
actual merge checks passed, including the unchanged pinned Hassfest image.
Both actual HA jobs passed **2,845 tests plus 83 subtests** with every strict
step. The minimum-version run had six warnings: five known dependency warnings
and the separately tracked SQLite test-fixture ResourceWarning; the current
version had five. Its allocation remains unproved; no filter or gate was relaxed.
A real scheduled audit on that exact source also passed, checking 140 package
versions with zero active advisories and zero unknown results.

All **46 non-version component files** out of **48** remain identical to the
accepted source. Only manifest.json/version.py become **8.3.5b3**. Workflows,
universal locks, security/coverage gates, supported platforms and minimum HA
version remain unchanged. Full packaging validation on **HA 2026.11.0 and
2026.11.1** is required separately; source results do not replace package checks.

The fixed V1.10 publisher creates only this prerelease after successful exact
head and actual merge checks. It retains all eighteen older immutable tags and
the existing stable selection. The controlled workflow also compares all
eighteen earlier release records and bodies. Matching reruns verify existing
state; conflicts or uncertain write results require readback, never overwrite.

**Home Assistant Core 2026.11.0 or newer is required.** Older Core versions pin
dependencies affected by published vulnerabilities. Keep Core maintained; a
minimum version is not permanent security clearance. Provider requests,
credentials and data-sharing behaviour remain those of the accepted runtime.
The [bounded privacy/security review](PRIVACY_SECURITY_REVIEW.md) and remaining
Gold rules keep their evidence limits.

Publication creates a GitHub prerelease with `draft=false`, `prerelease=true`
and `make_latest=false`. It does not access HA, install the update or confirm
production migration. Earlier b1/b2 accepted scopes remain closed; the new
native deletion repair needs the [focused b3 acceptance](ACCEPTANCE_8.3.5b3.md)
before any later stable promotion.
