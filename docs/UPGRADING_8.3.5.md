# 8.3.5 upgrade: remove obsolete HGT forecast statistics

**Availability:** the native cleanup described here is an unreleased follow-up
to published **8.3.5b2**. B2 itself retains its archive-and-keep behaviour;
its immutable [release notes](RELEASE_8.3.5b2.md) and
[accepted test scope](ACCEPTANCE_8.3.5b2.md) remain historical evidence.
Use a released package containing this follow-up, on HA **2026.11.0 or newer**.
Stable **8.3.4** remains the latest stable release until explicitly superseded.

## Recommended default: remove obsolete forecast statistics

The old HGT series contains averages of earlier changing **forecasts**. It is
not a measured heating-degree-day record. It is no longer updated and is not
needed for current forecasts or the separately planned official OGD history.
The recommendation is to delete it completely rather than keep an unused
archive. No statistics are deleted merely by installing an update or opening
a repair; the destructive action has one explicit confirmation.

| Upgrade starting point | What the native repair handles |
|---|---|
| Earlier release with HGT statistics under the original daily entity ID | The exact registered forecast identity and its compatible old series. The existing safe metadata transition may first move it to a temporary archive; the repair discovers either location. |
| 8.3.5b2 with an existing `forecast_statistics_archive` | The archive derived from that entity's registry ID, without clearing unrelated series. |
| Retired forecast-only `season_hgt` entity | Its old statistics when the active registry or native deleted-entry tombstone still proves ownership. |
| Disabled HGT sensor or disabled forecast feature within a loaded entry | Entry-owned inspection still discovers registered/tombstoned series; it does not require a live forecast sensor. |
| Fresh installation or already completed cleanup | No old metadata, no cleanup notice, no new archive. |
| Disabled integration entry | Inspection runs when the entry is next enabled; disabled entries do not execute migrations in the background. |
| Missing ownership, reused entity ID, foreign metadata or customisation re-enabling forecast statistics | No guessed deletion. A visible conflict requires diagnosis. Historical records whose registry ownership was already erased cannot be silently identified from a display name. |

## One normal upgrade, one native confirmation

1. Keep an existing usable protected backup outside HA if a recovery point is
   required. Do not remove/recreate the integration, entities or dashboards.
2. Update the existing Marketplace/HACS installation to an explicitly released
   package containing this follow-up, using the ordinary installation procedure.
3. Open **Settings → System → Repairs → Remove obsolete HGT forecast statistics**.
   Review the exact statistic IDs shown. They are forecasts, not OGD observations.
4. Confirm **Permanently remove old HGT forecasts**. This is irreversible within
   the live database and is the recommended action for normal users.
5. The native Recorder operation removes **all** hourly and short-term rows and
   their metadata for those IDs. It has no date-window cutoff. Readback verifies
   absence, Core recomputes its statistics repairs, and the live forecast drops
   its cached archive reference without a full HA restart.

Closing the dialog does not delete anything and does not complete the migration.
An unverified operation remains an error; a lost answer is never reported as
success or blindly resubmitted. Reopen the repair to inspect the actual state.
Other entries' issues remain independent.

## After successful cleanup

- The current HGT forecast keeps its entity/unique/device IDs, value, unit and
  personal settings. It has no measurement state class and produces no new
  measured HGT statistics. Ordinary state history follows Recorder retention.
- No obsolete HGT archive metadata or linked statistics remain in the live
  Recorder database. No replacement archive is created or later reimported.
- Wind arithmetic archives, current circular wind statistics, precipitation,
  OGD observations and all unrelated series are outside this HGT deletion.
- Existing protected backups are not deleted. Logical Recorder deletion does
  not promise secure physical erasure from database pages, backups or copies.
- Official measured HGT history is a separate feature with its own provenance;
  see [the OGD source plan](HGT_OGD_PLAN.md). Deleting old forecasts does not
  generate measured history or make b2 an OGD HGT importer.

## Evidence and recovery boundary

[Upgrade cleanup tests](../tests/test_hgt_cleanup.py) cover original and archived
series, retired season tombstones, disabled sensors, consent, conflicts,
idempotence and real Recorder foreign-key cascading of old hourly and short-term
rows with unrelated control series retained. The inspection and deletion use
native HA APIs, not SQL or direct database-file modification in production.
A previous software version alone cannot restore deleted rows; restoration
requires a suitable backup and is a separate deliberate operation.
