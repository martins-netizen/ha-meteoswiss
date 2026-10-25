# 8.3.0 stable update check

**Protocol version:** 1.0 · **Updated:** 24 October 2026

**Reported result — 25 October 2026:** the operator confirmed that the production
update from 8.2 to stable 8.3 worked successfully. This closes the reported update
check; no new independent file/registry audit is inferred. The protocol below
remains available for other installations without reopening the completed check.

The runtime was accepted as b4. Stable changes only its two version files;
do not repeat completed clean-install, restore or location-dialog rehearsals.

1. After actual publication, open the existing maintained-fork HACS repository.
   Refresh information if needed; explicitly download **Release 8.3.0**.
2. Restart HA once after the download and confirm the installed version.
3. Confirm the existing station, independent forecast point, measured-pollen
   station and warning postcode remain intended. Existing entities/forecast
   card targets and normal source availability should remain as accepted in b4.
4. Report any actual new problem with version, time and redacted details.

The publisher does not perform these HA actions. A GitHub release is not proof
of a HACS installation. No new blanket 24-hour observation window or artificial
provider outage is required. Retain the backup and
[migration/recovery guide](MIGRATION.md). Keep the separate
[b4 source acceptance](ACCEPTANCE_8.3.0b4.md) as the runtime evidence.
