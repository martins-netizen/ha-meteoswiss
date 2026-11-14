# 8.3.5b1: focused wind-history and default-name acceptance

**Protocol version:** 1.2 · **Updated:** 14 November 2026

**Bounded b1 operator evidence recorded; HGT follow-up acceptance remains open.** [8.3.5b1 is published and verified](RELEASE_EVIDENCE_8.3.5b1.md)
as test prerelease **444798178** from approved merge
`af1220249e672bd8a6742c73022a7c42aca2f20a`. Packaging and publication are complete;
the operator reported successful visual inspection and production installation
on 13 November. A read-only b1 report on 14 November matched all 44 expected
component files and observed both the retained arithmetic wind archive and new
circular points. Its only flagged follow-up was the HGT legacy state-class
notice. These observations have no pre-update DB baseline and do not prove
every historical row was retained. A later HGT archival package needs its own
installation approval and focused native readback. The
publisher made no HA calls, restart or device commands. No new operator DB or
registry read is claimed. Earlier accepted settings, icons, clean-install and
generic restore checks remain closed within their scopes.

## HGT follow-up: the separate b2 scope

The fixed [8.3.5b2 package](RELEASE_8.3.5b2.md) uses its own
[short HGT acceptance protocol](ACCEPTANCE_8.3.5b2.md). The b1 evidence above
remains accepted; do not repeat its generic installation/visual checks.


Use the [archive-and-keep default](UPGRADING_8.3.5.md). After a later explicitly
published fixed test package, verify HGT status `ready`, the retained historical
archive where applicable, continuing forecast/raw history and that the resolved
live-sensor state-class Repair has cleared. A real archive conflict must remain
visible and must not overwrite a destination. Earlier generic visual/install
checks stay accepted; do not reinstall b1 or purge statistics for this purpose.
Existing wind archive IDs and circular behaviour must remain unchanged. Native
all-field/PK/long-/short-term preservation tests are separate from this future
operator readback; a software rollback alone does not undo metadata changes.

## Before installation

Use HA **2026.11.0 or newer**, preferably the existing test/restored copy that
already contains the earlier wind history. For an instance with arithmetic
wind statistics, exercise that migration on the copy before production use.
Keep a protected, usable before-test backup. Creating a new copy or restoring a
backup is a separate operator action, not an automatic part of this protocol.
If no historical series exists, report that branch as **not exercised**.

Record only the technical versions, retained wind entity ID, prior statistics
range and whether the existing charts contain that history. Keep the report
private; omit home coordinates, postcode, personal names and unrelated device
data. A selected historical chart range and sample values provide bounded
operator evidence, not proof of every database row. Native SQLite tests retain
their separate row/metadata-preservation evidence.

## Four focused checks

1. **Install the verified published version.** After the installation decision,
   select 8.3.5b1 in the existing maintained-fork Marketplace entry, download it
   and restart HA once. Retain the existing entry/settings. Report actual
   integration/Core versions. Refreshing the catalogue is not an installation.
2. **Check wind/HGT and retained history.** On the test copy with earlier wind
   statistics, inspect `wind_statistics_status` and
   `arithmetic_statistics_archive`. A successful transition is `ready`; an old
   arithmetic series is retained under its distinct archive ID, while new
   circular points belong to the unchanged wind sensor ID. Inspect the same
   earlier chart range/samples under the archive and retained ordinary history.
   Report a `blocked` repair explicitly, without deleting statistics or an
   occupied archive. HGT current predictions/raw history and earlier statistics
   remain; no new HGT measurement-statistics points are expected. Use existing
   history and automation-generated statistics; do not invent a new soak window
   or treat missing provider values as a new regression.
3. **Inspect default names and personal choices.** On the existing German UI,
   check the service-group and optional diagnostic names that are actually
   present. Personal names take precedence, so unchanged personal labels are
   expected. Retain IDs, aliases, icons, enabled/disabled and hidden choices.
   Mark absent alternative-source/helper branches as not inspected. No source
   switch, new entry, diagnostic toggle or device deletion is required.
4. **Confirm ordinary operation.** Check current weather, forecast, pollen and
   warning availability against the usual dashboards and review new errors or
   Repairs. Distinguish an existing provider outage from a package regression.
   Do not trigger outages, disable peer entries or deliberately remove devices;
   native automated tests cover those failure/ownership boundaries.

## Result and recovery

Report **integration/Core versions; ordinary operation OK/problem; names and
retained choices OK/problem; wind status/archive and earlier chart/history
observed/not exercised/blocked; HGT current/history OK/problem**. Record the
actual scope rather than a blanket "everything secure" statement. Screenshots
are optional and should omit private details.

On a copy, stop a failed migration/repair test and preserve its before/after
evidence. Redownloading stable **8.3.4** alone does not reverse the Recorder
metadata change. The [controlled reverse sequence](WIND_STATISTICS_MIGRATION.md#charts-diagnosis-and-recovery)
retains both algorithms under separate unoccupied IDs; an approved restoration
is another recovery path and can discard newer changes. Neither is automatic
or authorised by this plan. Never delete the arithmetic archive, overwrite an
occupied ID or apply direct SQL to clear a repair.

The integration contacts public providers as documented in
[API_SOURCES.md](API_SOURCES.md); this check adds no new provider, credential or
telemetry. It is a bounded operator acceptance, separate from a historical
orphan inventory, a manual four-language audit, independent penetration testing
and the remaining Gold matrix. B1 installation is operator-reported; no new
follow-up installation or restoration is claimed.
