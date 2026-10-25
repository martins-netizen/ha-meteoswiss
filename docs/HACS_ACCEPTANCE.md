# HACS acceptance of the maintained fork

**Updated: 25 October 2026 · Plan and evidence V1.10**

## HACS catalogue admission

**martins-netizen/ha-meteoswiss is in the HACS default catalogue.** Frenck
[approved the submission](https://github.com/hacs/default/pull/12593#pullrequestreview-5639754168)
and merged [hacs/default PR #12593](https://github.com/hacs/default/pull/12593)
on **24 October 2026 at 20:04:26 UTC / 22:04:26 Europe/Zurich**. Merge commit:
**eb62dacb6c9806c5626543494263dbc34b0ae093**. The repository is present in the
[current integration list](https://github.com/hacs/default/blob/master/integration).

The [label-triggered Check run](https://github.com/hacs/default/actions/runs/40127024234)
passed all ten jobs, including the seven skipped before the **New default
repository** label was set. With JSON schema, Sorted and JQ from the original
run, all **13 distinct latest check results** succeeded on submission head
**eb64488d53f6b631f2b793b328b318c622457a5c**. The old skips are historical results.

New users search for **MeteoSwiss** in HACS and verify the repository owner.
The [custom-repository route](GETTING_STARTED.md#if-the-repository-is-not-listed)
remains a fallback, including for upstream source switches. Existing users keep
their configured entry and one software owner. Catalogue admission requires no
reinstallation by itself and does not prove which version a particular HA has
downloaded. See [quality evidence](QUALITY_SCALE.md) for the separate engineering
checklist; HACS admission does not assign a Home Assistant quality tier.

## Release and operator evidence

Stable [8.3.0](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.0)
was published on **24 October 2026 at 15:35:56 UTC / 17:35:56 Europe/Zurich**,
release ID **422817883**, source **3ca9a1c166920fbdda88d15238affafe520f4b68**.
It retains the accepted b4 runtime with version-only component changes. The
operator reported the focused b4 existing-entry check successful; screenshots
show its version and distinct station/forecast devices. On **25 October 2026**
the operator confirmed that the production update from **8.2 to stable 8.3**
worked successfully. This is reported update/operation evidence, without a new
independent file/registry comparison. Earlier first-install/restore
evidence remains valid; it is not a new clean 8.3 installation. See
[current readiness](RELEASE_READINESS.md).

For the earlier 8.2 series, Beta1's deployed runtime, the HACS 2.0.5 source switch,
temporary clean first installation and isolated backup restore are complete.
Beta2 added the explicit initial pollen choice; on 22 October the operator
completed new setup with other geographic locations and reported values.
This closes the focused practical setup/data check, with the evidence limits
below. Stable **8.2.0** was published on 22 October at **08:52:40 Europe/Zurich**.
The operator subsequently confirmed its HACS update after refreshing repository
information on 22 October. This is reported update evidence, not a new independent
component-file/registry/statistic comparison.

[Release readiness](RELEASE_READINESS.md) tracks the exact stable candidate.
The protocols below describe acceptance methods, not requests to repeat
completed tests. An independent newcomer review remains separate.

## 1. Inspect before changing anything

The following precheck does not remove/download software or restart HA.

1. Open **HACS** and find **MeteoSwiss**.
2. Open the existing entry's **three-dot menu → Repository**. Record its GitHub
   address, installed version and the HACS version. A missing entry is also a
   result; do not delete the HA integration.
3. If it already points to **martins-netizen/ha-meteoswiss**, select
   **Update information**. This refreshes metadata without downloading components.
4. Open **Download** or **Redownload**, expand **Need a different version?** and
    select the published stable **8.3.0** under **Release**. Check the version, then
    **Cancel** for this precheck. A stable release does not require beta visibility.
5. If the entry points to **LNKtwo/ha-meteoswiss**, retain it during this
   precheck. Confirm provenance, backup and recovery before following
   [migration](MIGRATION.md). Two repositories must not unknowingly manage the
   same installed directory.

HACS version, source address, installed version and offered target version are
sufficient precheck evidence. Screenshots need not include private account,
device or access details. A GitHub release alone does not prove local HACS visibility.

## 2. Two distinct practical checks

| Check | Suitable environment | Evidence required |
|---|---|---|
| Clean first installation | Temporary empty HA instance with HACS and no production device control | Find the maintained fork in HACS; explicitly download the intended published release; restart; configure MeteoSwiss once; check station, warning postcode and initial data. Use custom registration only as a fallback. |
| Source switch | Temporary instance with existing MeteoSwiss, or a separately planned production switch after precheck/recovery preparation | Replace the HACS software source while retaining the HA entry; compare target version/files and continued IDs, settings and statistics. |

No second permanent HA installation is required. An existing configured
production instance is not a clean first install. Successful version selection
alone is not a completed download.

### Clean first installation

Follow [getting started](GETTING_STARTED.md). Record HA/HACS versions, time,
release selection, successful return after restart and completed setup.
Check the weather station, four-digit warning postcode, HA forecast location
and independently selected measured-pollen station. Initial observations,
forecasts, warnings, pollen and air quality should be understandable. Distinguish
missing optional values from source outages.

### Source switch

Follow [migration](MIGRATION.md). The work depends on actual provenance.
An installer-deployed maintained fork already contains warning fixes absent
from older upstream versions; do not repeat migration tasks indiscriminately.

Confirm the saved software/configuration and restore route first. Treat actual
warning-consumer changes as described in migration. Do not actuate devices for
testing. After the switch, exactly one active HACS source manages `meteoswiss`;
retain the existing **Devices & services** entry.

Compare retained entity/statistic IDs, settings and actual data. Kloten's
official archive remains `meteoswiss:klo_precipitation_hourly`. Deliberately
retired entities are listed in migration; do not purge history. Recovery restores
software and its corresponding warning filters together.

## 3. Current evidence

| Evidence | State |
|---|---|
| Current stable release and resolved tag | Independently confirmed: 8.3.0 → 3ca9a1c166920fbdda88d15238affafe520f4b68, published 24 October at 15:35:56 UTC / 17:35:56 Europe/Zurich, release ID 422817883; latest-stable endpoint agrees. |
| Stable 8.3 production update | Operator-confirmed on 25 October: the update from 8.2 to stable 8.3 worked successfully. No new independent source-file/registry comparison or newly specified HA version is inferred. |
| Earlier stable release | 8.2.0 → 5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5, published 22 October at 08:52:40 Europe/Zurich; retained unchanged. |
| Stable 8.2.0 visible/downloaded in local HACS | Operator-confirmed on 22 October after Update information made the target available. No new independent file/ID/statistics comparison is inferred. |
| Public prerelease and resolved tag | Confirmed: 8.2.0b1 → abbb6b7701134ac2573f35b425ab3f0697a80540. |
| HA 2026.10.2 runtime, 24 hours and visual acceptance | Complete; publication contains the same 33 component/translation/brand files. |
| HACS version and original source | Operator confirmed HACS 2.0.5 and LNKtwo/ha-meteoswiss. |
| 8.2.0b1 selectable and actually downloaded in HACS | Operator confirmed on 20 October 2026. |
| Active source and restart | Operator confirmation at 19:57 Europe/Zurich on 20 October: martins-netizen/ha-meteoswiss, downloaded 8.2.0b1, HA restarted. |
| Initial post-switch visual check | Positive operator report at 19:56 Europe/Zurich on 20 October. |
| Clean first HACS installation | Operator-confirmed on 21 October: temporary HA 2026.10.2 / HACS 2.0.5, downloaded 8.2.0b1, restart, new STAC entry, 600 seconds, KLO and warning postcode 8302; observations appeared immediately. |
| Isolated backup restoration | Operator-confirmed on 21 October: after changing the interval to 900 seconds and restoring the backup, the saved 600 seconds returned. This confirms the reported configuration recovery, not a separately collected file/registry comparison. |
| Measured-pollen comparison | After choosing a station in Configure, the operator reported the same measurements as on production. The exact station identifier was not separately supplied. |
| Initial pollen-station choice | Added in published Beta2 for both source paths. On 22 October the operator completed setup with other geographic locations and reported values. Exact additional paths/stations were not separately supplied; automated tests cover both paths and persistence. |
| Pollen station identities and live files | On 21 October, 15 choices matched official metadata and hourly assets; all 15 URLs returned HTTP 200. Twelve feeds were current, three stale, including Luzern. Unsupported BLR is removed in Beta2; dated evidence and offline regressions are in [POLLEN_STATIONS.md](POLLEN_STATIONS.md). |
| Beta2 UI and retained options | Screenshot shows 8.2.0b2, 600 seconds and Zürich (PZH) in the temporary HA instance. This is not a new source-hash or all-entities comparison. |
| Beta2 public tag | Confirmed: 8.2.0b2 → 80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8, published 22 October 2026 at 07:12:40 Europe/Zurich. |
| New independent post-switch live file/ID/statistics comparison | Not collected; earlier technical runtime acceptance remains valid within its original scope. |
| Default branch hidden | Beta2/stable manifests set hide_default_branch=true. Its practical UI result was not separately reported; immutable Beta1 lacks that flag and is unchanged. |
| HACS default listing | Completed on 24 October through approved/merged PR #12593 and independently confirmed in the current integration list. See [admission evidence](#hacs-catalogue-admission). |
| Quality engineering evidence | The [rule matrix](QUALITY_SCALE.md) records code, tests, documentation and remaining work. Home Assistant assigns no official tiers to custom integrations; catalogue admission is a separate result. |

The written operator confirmation proves reported source, downloaded version
and restart; the preceding report confirms initial visual success. Submitted
images could not be independently read in that session and are not presented
as separately verified visual evidence. No new hashes, registry counts,
statistic identity comparisons are inferred. The later clean-install and restore
reports above are separate evidence from that original source-switch report.

The isolated restore selection included **Home Assistant → Settings and
history**. A custom integration is part of that HA configuration, not a separate
app in the restore list. **Get HACS 1.3.1** is the installer app and must not be
confused with the HACS integration version **2.0.5**. No production restore or
full comparison of all restored entities is claimed.

HACS 2.0.5 source inspection additionally established the UI route: an
uninstalled entry's bottom-right Download button opens the download dialog.
Adding a custom repository is not a download. Both are distinct from the HA
integration entry under **Devices & services**.

Both immutable beta tags remain unchanged. The completed first-install, restore
and Beta2 setup checks are not reopened by a documentation/version-only change.
A successful complete setup demonstrates the required picker path; it does not
independently prove every source/station change. Do not delete production entries
for these tests. The original 8.2 Beta2 Configure check concerned interval/pollen;
in 8.3, Configure edits weather station/base coordinates, measured pollen,
forecast and warning postcode together, with no polling field. See
[current settings](CALENDAR_AND_LOCATION_SETTINGS.md).

## References

- [Add a custom repository](https://www.hacs.xyz/docs/faq/custom_repositories/)
- [Refresh information and select a version](https://www.hacs.xyz/docs/use/repositories/dashboard/)
- [HACS manifest and hide_default_branch](https://www.hacs.xyz/docs/publish/start/)
- [HACS version-specific manifest loading](https://github.com/hacs/integration/blob/2.0.5/custom_components/hacs/repositories/base.py)
- [Pinned frontend release selection](https://github.com/hacs/frontend/blob/20250128065759/src/components/dialogs/hacs-download-dialog.ts)
