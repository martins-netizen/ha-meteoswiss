# 8.3.5b2 — HGT archive default test prerelease

**Notes version:** 1.0 · **Prepared:** 14 November 2026

**Preparation snapshot:** this file describes the fixed test package, not a
claim that publication or operator installation has already happened. The
release catalogue records actual publication. Stable 8.3.4 remains latest.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## Recommended migration: update, archive and keep

8.3.5b2 fixes the HGT legacy state-class Repair left by 8.3.5b1. The default
automatically archives compatible old HGT forecast statistics, verifies the
same metadata primary key and all other fields, and asks Core to recompute
its actual statistics Repairs. The resolved live-HGT Repair clears. Historical
data is retained; deleting statistics is not part of the update.

The forecast retains its entity/unique/device IDs, value, unit, settings and
ordinary history. It remains a forecast without a measurement state class.
The archive has no replacement live entity. Existing wind archives keep their
IDs, and the live wind sensor continues its circular statistics. Historical
arithmetic means are not converted or recalculated.

1. Keep a protected, usable before-update backup and your existing integration
   entry. A software downgrade alone does not reverse Recorder metadata.
2. Once this prerelease is published, select **8.3.5b2** in the existing
   maintained-fork Marketplace entry, download it and restart HA once.
3. On the original HGT sensor, check `hgt_statistics_status: ready` and
   `forecast_statistics_archive` where old data existed. Confirm that the
   old live-HGT state-class Repair has disappeared and the forecast/history
   still work. No Delete action, entry recreation or extra settings choice is
   needed. See the [short focused protocol](ACCEPTANCE_8.3.5b2.md).

An occupied destination, incompatible metadata or an unverified native refresh
produces a translated MeteoSwiss Repair instead of overwriting data or reporting
completion. Keep the data and request diagnosis. An archive may be identified
as having no live entity in the advanced Statistics catalogue; that is separate
from the resolved live-HGT state-class Repair. See
[archive status, charts and recovery](UPGRADING_8.3.5.md).

## Source and validation boundary

The runtime is regularly merged **PR #110**, commit
**71c4c6269ea0c06cc5d2c43db9b0a24d8e6e9c08**, tree
**49f0f0e071074409daaaee235937a9f49eb1c84b**. All ten exact-head and nine actual
merge checks succeeded. Both actual merge HA jobs passed **2,753 tests plus
83 subtests**, with five existing upstream warnings and all strict gates.
Native Recorder tests verify every historical long-/short-term field, metadata
and row identity, retained registry choices, reload/retry and genuine Repair
recomputation. Both new modules have 100% line and branch coverage.

Of **46 component files**, all **44 non-version files** are identical to that
accepted source. Only manifest.json/version.py become **8.3.5b2**. Dependencies,
universal locks/platform markers, HA minimum, workflows and security/coverage
gates remain unchanged. Complete packaging validation is required on HA
**2026.11.0 and 2026.11.1**; source checks do not substitute for package checks.
The V1.9 publisher retains all earlier publication profiles and checks all
seventeen previous immutable tags, stable selection and actual merge checks.

The package requires **Home Assistant Core 2026.11.0 or newer**, because older
Core versions pin dependencies affected by published vulnerabilities. Keep Core
maintained; a minimum version is not permanent security clearance. Existing
providers, credentials, request schedules and data-sharing behaviour remain
unchanged. The [privacy/security assessment](PRIVACY_SECURITY_REVIEW.md) retains
its evidence limits; remaining Gold rules and independent review stay open.

## Publication and operator acceptance

The publication authorisation covers this fixed test package after successful
packaging checks. The controlled flow uses a regular packaging PR, ten trusted
exact-head checks, a regular merge and all nine actual merge checks before its
sole release write. Fixed **publish_meteoswiss_835_beta_v1.9.sh** creates only
8.3.5b2 with `draft=false`, `prerelease=true` and `make_latest=false`.
Stable **8.3.4 / ID 437853341**, all older tags and their published bodies remain.
Matching retries verify an existing matching release without another write.
Conflicting or uncertain results stop for a readback, never a retag or overwrite.

Publishing this package does not install it or authorise HA restoration/device
commands. The existing b1 production/visual and bounded wind readback remain
accepted. The new HGT archival transition needs the
[focused b2 readback](ACCEPTANCE_8.3.5b2.md) before any stable promotion.
