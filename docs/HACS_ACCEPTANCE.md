# HACS acceptance of the first beta

**Updated: 21 October 2026 · Plan and evidence V1.5**

Beta **8.2.0b1** is public. Its component files match the runtime already
accepted on HA 2026.10.2. The operator has confirmed the HACS 2.0.5 source switch,
download, restart and positive initial visual check. On 21 October, the operator
also completed a clean installation and backup restoration in a temporary HA
instance. That walkthrough found the missing initial pollen-station choice;
the correction is unreleased and still needs its focused HA UI check. The
accepted beta runtime does not need another full observation window.

[Release readiness](RELEASE_READINESS.md) separates remaining stable-release
work from later location/POI features.

The corrected setup is integrated through PR #37. Its **8.2.0b2** packaging is
prepared separately; publication, download and focused UI acceptance are still
distinct steps. Use the [candidate checklist](RELEASE_8.2.0b2.md), retaining the
completed first-beta install/restore evidence.

## 1. Inspect before changing anything

The following precheck does not remove/download software or restart HA.

1. Open **HACS** and find **MeteoSwiss**.
2. Open the existing entry's **three-dot menu → Repository**. Record its GitHub
   address, installed version and the HACS version. A missing entry is also a
   result; do not delete the HA integration.
3. If it already points to **martins-netizen/ha-meteoswiss**, select
   **Update information**. This refreshes metadata without downloading components.
4. Open **Download** or **Redownload**, expand **Need a different version?** and
   select **8.2.0b1** under **Release**. Check the announced version, then
   **Cancel** for this precheck. Older HACS versions may need beta visibility.
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
| Clean first installation | Temporary empty HA instance with HACS and no production device control | Add the repository as Integration; explicitly download 8.2.0b1; restart; configure MeteoSwiss once; check station, warning postcode and initial data. |
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
| Public prerelease and resolved tag | Confirmed: 8.2.0b1 → abbb6b7701134ac2573f35b425ab3f0697a80540. |
| HA 2026.10.2 runtime, 24 hours and visual acceptance | Complete; publication contains the same 33 component/translation/brand files. |
| HACS version and original source | Operator confirmed HACS 2.0.5 and LNKtwo/ha-meteoswiss. |
| 8.2.0b1 selectable and actually downloaded in HACS | Operator confirmed on 20 October 2026. |
| Active source and restart | Operator confirmation at 19:57 Europe/Zurich on 20 October: martins-netizen/ha-meteoswiss, downloaded 8.2.0b1, HA restarted. |
| Initial post-switch visual check | Positive operator report at 19:56 Europe/Zurich on 20 October. |
| Clean first HACS installation | Operator-confirmed on 21 October: temporary HA 2026.10.2 / HACS 2.0.5, downloaded 8.2.0b1, restart, new STAC entry, 600 seconds, KLO and warning postcode 8302; observations appeared immediately. |
| Isolated backup restoration | Operator-confirmed on 21 October: after changing the interval to 900 seconds and restoring the backup, the saved 600 seconds returned. This confirms the reported configuration recovery, not a separately collected file/registry comparison. |
| Measured-pollen comparison | After choosing a station in Configure, the operator reported the same measurements as on production. The exact station identifier was not separately supplied. |
| Initial pollen-station choice | Missing in 8.2.0b1. An unreleased correction adds explicit selection for both weather sources; focused HA UI acceptance of that correction remains open. |
| Pollen station identities and live files | On 21 October, 15 choices matched official metadata and hourly assets; all 15 URLs returned HTTP 200. Twelve feeds were current, three stale, including Luzern. Unsupported BLR is removed in the unreleased correction; dated evidence and offline regressions are in [POLLEN_STATIONS.md](POLLEN_STATIONS.md). |
| New independent post-switch live file/ID/statistics comparison | Not collected; earlier technical runtime acceptance remains valid within its original scope. |
| Default branch reliably hidden in version selection | Not guaranteed for 8.2.0b1; its hacs.json does not contain hide_default_branch. |
| HACS default listing or official HA quality tier | Not applied for or confirmed. |

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

The immutable beta tag remains unchanged. Future branch hiding must be checked
with the corresponding released manifest. The completed first-install and
restore rehearsals are not reopened by a documentation change. Test the new
pollen picker on the exact next candidate without deleting production entries.

## References

- [Add a custom repository](https://www.hacs.xyz/docs/faq/custom_repositories/)
- [Refresh information and select a version](https://www.hacs.xyz/docs/use/repositories/dashboard/)
- [HACS manifest and hide_default_branch](https://www.hacs.xyz/docs/publish/start/)
- [HACS version-specific manifest loading](https://github.com/hacs/integration/blob/2.0.5/custom_components/hacs/repositories/base.py)
- [Pinned frontend release selection](https://github.com/hacs/frontend/blob/20250128065759/src/components/dialogs/hacs-download-dialog.ts)
