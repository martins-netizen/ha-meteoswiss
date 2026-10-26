# Stable 8.3.1: short HACS update check

**Protocol version:** 1.0 · **Prepared:** 26 October 2026

The operator confirmed the 8.3.1b1 version/visual check. Stable 8.3.1 retains
that runtime with only two version changes. This protocol records a later
stable HACS download; it does not reopen the accepted beta UI or earlier
first-install/restore evidence.

Use only the announced published **8.3.1** through the existing maintained-fork
HACS repository. Until publication is confirmed, normal stable is **8.3.0**.

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
