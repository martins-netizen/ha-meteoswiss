# 8.3.2b1: focused shared-settings check

**Protocol version:** 1.0 · **Prepared:** 27 October 2026

**Status:** pending publication, installation and operator acceptance. This is a
short check of the existing entry in the existing test HA, not another clean
installation or restore rehearsal. The normal stable release remains **8.3.1**.

1. **Install the announced version.** After publication is confirmed, use the
   maintained-fork HACS entry → Download/Redownload → **8.3.2b1**. Refresh its
   information first if necessary and make prereleases visible. Restart HA once
   and confirm the installed integration and HA Core versions. Keep the existing
   backup and note the intended weather station/base coordinates, measured-pollen
   station, forecast point and warning postcode. Do not create a new entry.
2. **Compare both entry points.** Open MeteoSwiss → Configure (gear), review and
   cancel. Then use the existing entry's three-dot menu → Reconfigure. Both
   should show the same weather, pollen, forecast-action and warning-postcode
   fields and defaults. A MeteoSwiss entry has a weather-station field; an
   existing Open-Meteo current-data entry has latitude/longitude instead. Only
   test the source already configured; no second entry is needed. Weather-station
   help retains the official station-map link.
3. **Cancel pending changes.** In Reconfigure, select a different weather station
   and/or pollen station, choose a forecast search and continue through explicit
   result selection to the combined confirmation. Review the pending places,
   then cancel before saving. Reopen Configure and verify the original choices
   remain. If a provider temporarily prevents validation, retry later and report
   that source condition separately; do not force an outage.
4. **Confirm a combined change.** Through Reconfigure, deliberately select the
   weather/pollen/forecast places you want to test and keep the warning postcode.
   Confirm the selected forecast and pending places. Open Configure to verify
   all saved choices together. Review corresponding station/forecast values,
   place labels and existing cards. Custom names and retained technical IDs may
   still contain a previous station name; the documented label/history rules
   apply. An explicit forecast move keeps weather measurements and modelled
   AQ/pollen/UV at their own locations. Applying settings needs no Core restart.
5. **Restore the intended choices through Configure.** Confirm them there and
   verify them through Reconfigure. Check that expected values recover and a
   valid entry has no unexpected saved-location repair. This exercises saving
   through both routes while finishing with the intended configuration.

Report **HA Core version, integration version, same fields/defaults via both
routes, cancellation retained the original choices, combined saving worked,
and intended settings/values restored**. Mark an inapplicable source route as
not tested. Screenshots are optional and should exclude personal details.

Automated native-HA tests already cover source/forecast retry, simultaneous
dialogs, duplicate rejection, retained entry/entity IDs, the single loaded-entry
reload and all four UI languages. Do not corrupt storage, create duplicate
entries, disable network/security controls or repeat a restore to manufacture
these cases. Visual acceptance does not by itself prove a separate registry or
statistic audit. No new blanket 24-hour observation window is required.

If a regression blocks normal operation, cancel unsaved forms and redownload
stable **8.3.1**, then restart once. Restore deliberately changed location
choices separately; preserve the config entry and history. See
[candidate scope and recovery](RELEASE_8.3.2b1.md).
