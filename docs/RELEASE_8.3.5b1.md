# 8.3.5b1 — wind history and translated service groups test prerelease

**Notes version:** 1.0 · **Prepared:** 13 November 2026

**Preparation snapshot, 13 November 2026: not published or installed.** Stable
8.3.4 was latest at preparation; the live release catalogue records publication.
Packaging review/checks, publication and operator installation/acceptance are
separate gates. The fixed publisher exports the body below from an approved
packaging merge; a source PR approval alone does not publish this prerelease.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.4

- **Preserve old wind-direction averages before starting circular statistics.**
  Existing arithmetic statistics keep their metadata/rows under a separate
  archive ID. The retained wind sensor starts a new circular series only after
  verifying preservation. Its entity/device IDs, personal choices and ordinary
  state history stay in place. Conflicts block the transition with a translated
  repair; current readings continue. Calm/invalid directions are unknown.
  Historical arithmetic averages are not recalculated into circular averages.
  See [migration, chart impact and recovery](WIND_STATISTICS_MIGRATION.md).
- **Keep forecast-based HGT out of measured long-term statistics.** The HGT
  prediction and ordinary history remain available, as do earlier statistic
  rows. New forecast predictions no longer enter measurement aggregates. This
  can change a statistics chart's new points; no historical purge is requested.
  See [metadata and chart consequences](SENSOR_METADATA.md).
- **Translate default entity and service-group names in DE/EN/FR/IT.** Existing
  IDs, user names, icons, aliases, enabled/disabled choices and bindings remain.
  Personal names take precedence over defaults. Technical state/attribute
  contracts and provider-supplied locality aliases are separate from UI names.
  See [complete names](ENTITY_NAME_TRANSLATIONS.md),
  [service groups](SERVICE_GROUP_TRANSLATIONS.md) and
  [optional diagnostics](DIAGNOSTIC_TRANSLATIONS.md).
- **Retain shared diagnostic helpers across entry ownership changes.** A loaded
  peer takes over through its existing platform, retaining registry identities
  and settings without reloading weather sources. Ambiguous legacy ownership
  raises a repair rather than deleting or merging records. See
  [lifecycle and limits](SHARED_DIAGNOSTIC_LIFECYCLE.md).
- **Allow only bounded, user-confirmed removal of retired service shells.** HA's
  native device-page confirmation can remove an unambiguous empty shell for an
  entry that no longer exists. Current, disabled, shared, bound, linked or
  ambiguous groups stay protected. No automatic device/history cleanup runs.
  See [removal policy](DEVICE_REMOVAL.md).
- **Use a maintained Core security baseline.** This candidate requires
  **Home Assistant Core 2026.11.0 or newer**, because older Core versions pin
  dependencies affected by published vulnerabilities. Keep Core updated within
  the supported line; a minimum is not permanent security clearance. Test
  fixtures cover 2026.11.0/2026.11.1 with universal hash locks, explicit bootstrap
  floors and offline uv. The whole-lock advisory gate fails on active advisories
  and unknown results; its daily/manual workflow uses identical read-only steps.
  See [security rationale](../DEVELOPMENT.md#supported-home-assistant-versions)
  and [advisory scope](DEPENDENCY_ADVISORIES.md).

Provider selections, URLs, request schedules, credentials and data-sharing
behaviour are unchanged by this package. Providers still receive source IP and
the requested public station/postcode or coordinates. Diagnostic redaction does
not hide those requests from providers. The [bounded review](PRIVACY_SECURITY_REVIEW.md)
retains the limits of privacy, architecture and security evidence.

## Focused installation and acceptance

Only after verified publication and a separate installation decision, use the
existing Marketplace entry for **martins-netizen/ha-meteoswiss** and select
**8.3.5b1** with prereleases visible. Follow the
[focused acceptance plan](ACCEPTANCE_8.3.5b1.md). An existing test/restored copy
with historical wind data is the first migration target. Keep a protected
before-test backup and the existing entry; a metadata refresh alone installs
nothing. Do not delete entries or statistics to make a repair disappear.

The new circular series and the retained arithmetic archive serve different
purposes. Existing statistics charts may need the archive ID for older means;
the original sensor ID supplies new circular means. Ordinary history retains
its identity. A software rollback to stable **8.3.4** alone does not reverse
Recorder metadata. Use the [controlled recovery boundary](WIND_STATISTICS_MIGRATION.md#charts-diagnosis-and-recovery)
and retain both histories; never overwrite an occupied destination or use an
unreviewed SQL fix. Earlier accepted settings/icons/clean-install/restore scopes
remain closed; this is a new wind/history and naming acceptance scope.

## Source, checks and publication boundary

The reviewed source is regularly merged **PR #107** at
**b144a0b73d81358f27fd6ecd89a47120c8a0a1b9**, tree
**36220cb951ef7abad9e3de9cfa9fc27a8dae4360**. All ten PR-head and nine actual
merge checks passed, including SonarCloud after its two security findings were
corrected without accepting/suppressing issues. Both actual source-merge HA
jobs passed 2,660 tests plus 83 subtests with five existing upstream warnings.
The separate manual Dependency audit run **43389137603** passed on the same
source: 140 package/version pairs, no active advisories and no unknown results.
This is dated evidence; actual cron execution/notification delivery are separate.

Of **44 component files**, all **42 non-version files** match that reviewed
source exactly. Only manifest.json/version.py become **8.3.5b1**. Catalogues,
dependencies, universal hashes/platform markers, HA minimum, workflows and prior
security/coverage gates remain unchanged. Packaging has its own complete local
and hosted validation; source checks are not substituted for package checks.

Complete local packaging suites pass **2,715 tests plus 83 subtests** on each
HA **2026.11.0/2026.11.1**, Python **3.14.10**, with five existing upstream
warnings. All strict security/hash/graph/offline/translation/coverage gates
pass. Component coverage remains **3,884/3,885 statements, 1,086/1,086 branches**
(99.979883% combined). Fourteen fixed publication profiles retain every earlier
boundary; 55 new cases exercise the new profile and immutable CI/lock controls.
The exact packaging PR head and actual merge still require hosted acceptance.

Fixed **publish_meteoswiss_835_beta_v1.8.sh** permits only this prerelease from
the approved protected-development merge. It verifies the version-only
component boundary, expected checks/apps, unchanged workflows and all sixteen
existing tags. Its only remote write creates the prerelease with
`make_latest=false`; stable **8.3.4 / ID 437853341** must remain latest.
Matching retries verify; conflicts and uncertain writes stop. It accesses no HA
instance, installs nothing and performs no database or device operation. See
[publication gates](PUBLISHING.md#prepared-835b1-no-publication-performed).

Report ordinary bugs to the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
or use [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories).
This package does not complete the remaining Gold applicability/history work
or establish an official quality tier or independent security certification.
