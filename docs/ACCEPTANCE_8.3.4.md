# Stable 8.3.4: short actual update check

**Protocol version:** 1.1 · **Updated:** 7 November 2026

**Stable 8.3.4 is published and independently verified as latest stable.**
See [publication evidence](RELEASE_EVIDENCE_8.3.4.md). Earlier 8.3.4b1 has the
operator's positive normal-operation report on **Core 2026.11.0 / HA OS 18.4**;
see the [bounded beta evidence](RELEASE_EVIDENCE_8.3.4b1.md). Stable retains all
39 non-version component files and changes only the two version fields.
This protocol covers an actual stable update; publication does not assert an
individual user's installation.

1. Keep the existing configured entry
   and backup. In the maintained-fork Marketplace entry (HACS on older HA),
   refresh information if needed, then actually Download/Redownload **8.3.4**.
2. Restart HA once. Confirm the installed integration version is **8.3.4** and
   the usual values/dashboards continue to work.
3. Report the installed integration version and normal-operation result. Report
   Core/OS versions only if changed. Record the reply within its actual scope;
   it is not an independent registry/statistic inventory.

Do not repeat completed settings, first-install, restore or beta checks. No
additional name/ID list, diagnostic toggle, source/station change, deliberate
outage, device action or new blanket observation wait is required.
Existing enabled diagnostic helpers stay enabled; do not recreate entries to
demonstrate a first-registration default. HGT behaviour remains the accepted
beta behaviour; the separate HGT follow-up is not part of this stable package.

If normal operation regresses, redownload stable **8.3.3** through the same
repository and restart once, retaining entries, personal choices and history.
