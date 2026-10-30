# 8.3.2b1 — shared location settings test prerelease

**Notes version:** 1.0 · **Prepared:** 27 October 2026

**Publication and acceptance addendum — 27 October 2026:** **8.3.2b1**, ID
**425962004**, was published at **20:40:42 UTC** from
**5a39c3cdbf31f0807f52bcb4acb26190cc1e8423**. The operator subsequently
reported all five focused steps positive on **HA Core 2026.10.4**. The original
package scope below and published release body remain unchanged. Stable
[8.3.2](RELEASE_8.3.2.md) was published on 28 October and its actual
HACS download/restart/operation was confirmed on 30 October. See
[stable evidence](RELEASE_EVIDENCE_8.3.2.md); the beta body below is historical.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.1

- **The same settings through either route.** Open the entry's **Configure
  gear** or **three-dot menu → Reconfigure** to change weather measurements,
  measured pollen and the weather forecast in one dialog, alongside the
  independent warning postcode. Previously, the Reconfigure shortcut changed
  only the forecast; Configure already offered the complete set of places.
- **Keep choices when retrying.** After a failed observation-source check, a
  chosen forecast search or return to base remains selected for the retry.
  It no longer silently changes back to Keep.
- **Save the complete choice together.** Both routes share source validation,
  staged confirmation and duplicate/concurrent-edit protection. Cancelling an
  unfinished dialog or a failed validation saves no partial change. If another
  dialog has already saved, reopen the older dialog to review current settings.
- **Consistent help in four languages.** Complete Reconfigure fields and the
  combined location confirmation are bundled in German, English, French and
  Italian. Initial setup retains its own forecast confirmation.

For MeteoSwiss observations, choose a weather measuring station. An existing
Open-Meteo current-data entry instead shows its base coordinates. The pollen
measurement station, explicit forecast point and warning postcode remain
independent. Changing a station or forecast does not change the global HA home
location. See [the four location roles](../README.md#four-places-what-each-one-is-used-for)
and [shared settings](CALENDAR_AND_LOCATION_SETTINGS.md).

Existing config entries, entity/statistic identities, custom names, unrelated
settings and legacy intervals are retained. A confirmed change to a loaded
entry reloads it once through its existing listener. A deliberate weather-station
change continues the retained observation history with the new readings;
station-keyed external precipitation archives keep their own identities.
The forecast source, App v3 warnings, source polling, dashboards and stored
configuration format are unchanged.

## Install only the announced test package

Use the existing test HA and configured entry. Once publication is announced,
refresh this fork's HACS information if needed, make prereleases visible, and
actually Download/Redownload **8.3.2b1**. Restart HA once, confirm the installed
version and follow the [focused five-step check](ACCEPTANCE_8.3.2b1.md).
Refreshing information alone does not download files.

Keep the existing backup and intended settings. Do not delete/recreate the
entry. Earlier first-install, restore and stable-operation checks remain
complete within their recorded scope. This dialog follow-up needs no blanket
new 24-hour waiting period or deliberately broken network/source.

## Reviewed source and evidence

Approved [PR #76](https://github.com/martins-netizen/ha-meteoswiss/pull/76) was
regularly merged as **d6ae2a0b1ae9c195c9647f6b416d347891f91a74**, tree
**489d818a27e58c45428085ab3d917b25ac694dbf**, after incorporating reviewed
documentation PR #75 and passing eight updated-head checks. All seven actual
post-merge checks and CI/CodeQL/HACS workflows passed. Both hosted HA fixtures
passed **1,883 tests plus 73 subtests** on Python **3.14.10**; config flow has
**406/406 statements and 146/146 branches**, and the whole integration has
**3,516/3,517 statements and 974/974 branches** with existing strict gates.
The four UI catalogues have **200 keys each**, with English/source parity.

The candidate changes only manifest.json/version.py within the **40-file**
component: **38 non-version files match** that reviewed source. HACS/CH,
workflows, security guards and all ten earlier tags are retained. Package tests
add an eighth fixed publication profile; [readiness](RELEASE_READINESS.md#prepared-832b1-test-candidate)
records its own results without extending earlier live acceptance.

Development CI now checks patched Python/pip and constrains certifi; historical
HA uv pins are explicitly unpatched, offline-only compatibility exceptions.
The [secured local recipe](../DEVELOPMENT.md#local-compatibility-checks) explains
these boundaries. These development protections do not update the Python or
CA packages in an installed HA Core image.

## Publication, recovery and support

The fixed **publish_meteoswiss_832_beta_v1.5.sh** checks the exact approved
protected development merge, the version-only source boundary, check provenance,
unchanged earlier tags and latest stable **8.3.1 / ID 424249153**. Its only
remote write can create **8.3.2b1**, prerelease=true and make_latest=false.
Matching retries verify without posting again; conflicting tags or notes stop.
It makes no HA connection or restart. See [the publication procedure](PUBLISHING.md#832b1-test-candidate-prepared).

If rollback is needed, redownload published stable **8.3.1** through the same
HACS repository and restart once. Software rollback does not undo deliberate
location changes: restore intended choices separately. Retain the configured
entry and history; see [recovery](MIGRATION.md#if-something-fails).

Report issues to the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues),
or use [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports. Remaining Gold checklist items and proposed exemptions
retain their [documented scope](QUALITY_SCALE.md); this package does not complete
Gold or confer an official HA tier.
