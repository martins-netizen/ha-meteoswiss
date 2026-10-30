# Stable 8.3.3: short HACS update check

**Protocol version:** 1.1 · **Updated:** 30 October 2026

**Completed within the reported scope.** Following independently verified
stable publication (release **429354633**, source
**3d4fad2330c89f134eba208e8b2db55705177e7d**), the operator confirmed
**8.3.3 installed and normal operation OK** on **30 October 2026**. This closes
the requested short stable update; no independent file/registry audit or new
Core/OS/Python version is inferred. See [release evidence](RELEASE_EVIDENCE_8.3.3.md).
The steps below retain the completed method, not another test request.

Published **8.3.3b1 / ID 429321251** has the operator's positive icon/personal
choice and normal-operation report on **HA Core 2026.10.4 / HA OS 18.4**;
see the [completed beta check](ACCEPTANCE_8.3.3b1.md). Stable packaging retains
its 39 non-version component files and changes only two version files.

1. After confirmed publication, keep the configured entry, intended settings
   and existing backup. In the maintained-fork HACS entry refresh repository
   information if needed, then actually Download/Redownload **8.3.3**.
2. Restart HA once. Confirm the installed integration version is **8.3.3**
   and intended values/dashboards continue to work.
3. Report the installed version and update result. Record the report within
   that scope; no independent file/registry comparison is inferred.

Do not repeat the accepted beta icon check, five earlier settings steps,
first installation or restore. No forced outage or new blanket 24-hour wait
is required. If normal operation regresses, redownload stable **8.3.2** from
the same HACS repository and restart once. Preserve entries, choices and history.
