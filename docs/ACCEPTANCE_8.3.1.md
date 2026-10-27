# Stable 8.3.1: short HACS update check

**Protocol version:** 1.1 · **Updated:** 27 October 2026

The operator confirmed the 8.3.1b1 version/visual check. Stable 8.3.1 retains
that runtime with only two version changes. This protocol records a later
stable HACS download; it does not reopen the accepted beta UI or earlier
first-install/restore evidence.

Use only the announced published **8.3.1** through the existing maintained-fork
HACS repository. Publication is confirmed: release **424249153**,
**26 October 2026 at 12:54:24 UTC**, source
**fa298ca72bf62da727797f9bfcacf95c83ffeaf1**. Actual installation remains
a separate operator result; no confirmation is inferred here.

1. Retain the existing backup and configured HA entry. In HACS, refresh
   repository information if needed, then actually Download/Redownload
   **8.3.1**. Do not delete/recreate the entry or register a second software owner.
2. Restart HA once after downloading. Check that the installed integration
   version is **8.3.1** and intended places/values remain.
3. Report the version/update result. An operator report is distinct from an
   independent source-file or registry comparison; record only what was checked.

An installation already on accepted b1 does not need the map/settings test again.
No forced source failure, damaged saved location, restore rehearsal or new
24-hour wait is required. If deliberately changed settings need restoration,
restore them explicitly; a software download does not undo those choices.
