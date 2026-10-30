# 8.3.3b1: short version and icon check

**Protocol version:** 1.0 · **Prepared:** 30 October 2026

**Status:** not started. Run only after actual 8.3.3b1 publication is confirmed.
Stable 8.3.2 and earlier settings, first-install and restore acceptance remain
complete within their recorded scope.

1. **Install and confirm the announced package.** Prefer the existing test HA
   and configured entry. In the maintained-fork HACS entry, make prereleases
   visible, select **8.3.3b1** and actually Download/Redownload it. Refresh
   repository information first if needed. Restart HA once; report integration
   and HA Core versions. Keep the existing backup and entry.
2. **Inspect icons and personal choices.** Open the entity details or an HA
   entity list for available measured pollen, a forecast-summary sensor and a
   warning binary sensor. Their intended symbols should remain familiar;
   measured hazel/oak use a tree outline. Existing personal entity names/icons
   should remain. An explicitly configured dashboard icon can mask the default,
   so use entity details when checking native icon resolution. No temporary
   rename/icon edit or new dashboard is needed.
3. **Confirm normal operation.** Review existing weather/pollen/forecast values
   and the normal dashboards. Note any new integration error. A provider's
   pre-existing missing value or outage is separate from a display regression.
   If a source error occurs naturally, report whether its message is useful in
   the configured HA language; do not disable the network or manufacture errors.

Report **integration version, HA Core version, icons/retained personal choices
OK, normal operation OK**, or describe the affected entity. Screenshots are
optional and should omit personal details. Mark unavailable/not inspected
families explicitly; no artificial pollen/alert value is required.

Native HA tests already cover all 19 exception keys in DE/EN/FR/IT, the icon
catalogue, personal registry overrides after reload, safe errors and recovery.
This visual check does not claim an independent registry/statistic audit.
There is no new blanket 24-hour wait, restore or location-settings test.

If normal operation regresses, redownload stable **8.3.2** from the same HACS
repository and restart once. Keep the configured entry, settings and history.
See [scope and recovery](RELEASE_8.3.3b1.md).
