# 8.3.5: normal update and retained acceptance

**Protocol version:** 1.0 · **Updated:** 18 November 2026

Choose stable **8.3.5** only when it is listed in the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).
Preparation and repository refresh do not download or install it. Minimum Core
is **2026.11.0**; an installation on **2026.11.2** already meets that minimum.

## Already using the accepted b7 runtime

The positive focused b7 sight report remains complete. Coordinator placement
and calculated-HGT Swiss-midnight state publication receive their own source/
native validation before stable packaging. The clock corrects yesterday's
registered value lingering until a provider refresh; the later stable version
bump must match that separately approved corrective source. No repeat
migration, failure exercise or operator observation window is required. If choosing the stable label when
published, use the existing entry's ordinary Marketplace update and complete
its normal update restart once. No additional acceptance checklist is imposed.

## Upgrading from stable 8.3.4 or an earlier version

1. Read the [release notes](RELEASE_8.3.5.md) and
   [upgrade/cleanup guide](UPGRADING_8.3.5.md). Keep a usable protected recovery
   backup when needed, including Recorder and ownership storage together.
2. Update the existing entry through **Settings → Marketplace** to explicitly
   published **8.3.5** and complete the ordinary update restart once. Keep the
   station, options, dashboards and retained entity/statistic IDs. Intermediate
   betas, station switches and entry recreation are unnecessary.
3. Check the installed version and normal weather/station displays after their
   ordinary refresh. Missing optional source data must retain its explicit
   status; do not force an outage, warning or fake state to manufacture a test.
4. If **Remove obsolete HGT forecast statistics** appears under **Settings →
   System → Repairs**, review its exact IDs. The recommended permanent removal
   deletes those obsolete predictions only after confirmation. Opening or
   cancelling deletes nothing. Follow the upgrade guide's backup/ownership
   boundaries. Already completed cleanup stays complete.
5. With a MeteoSwiss measurement station and Recorder, measured HGT imports in
   the background. Its last-observed-day sensor may be unavailable until source
   and Recorder verification succeeds; native bounded retry handles transient
   failures. The [HGT guide](HGT_OGD_PLAN.md) explains source periods, chart IDs
   and removal. Do not substitute old forecasts for measured history.

A short report of the selected version and observed normal operation is enough
for this focused check. Keep raw diagnostics and personal configuration private.
No initially disabled diagnostic helper needs enabling, no physical device
operation is required, and earlier b3/b5/b6/b7 acceptance stays closed. This is
not an independent installed-file/database audit or security certification.
