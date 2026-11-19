# HGT ownership while Recorder writes are pending

**Package scope:** introduced in b6 and retained by published b7. Stable 8.3.5
uses approved corrective source #131 without changing the ownership contracts
below. Availability follows the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
with source/package checks and installed acceptance recorded separately in the
[stable evidence](RELEASE_EVIDENCE_8.3.5.md). The original review on 17 November 2026
used development `1d34e525d2938f6e265265a1efc80571ba9c1eca`.
This correction is not in the immutable published 8.3.5b5 package.

**Merged source:** [PR #121](https://github.com/martins-netizen/ha-meteoswiss/pull/121)
was regularly squashed at `b936505d348c199717c00b3211def7fa6b3013c1` on
17 November 2026. All ten head and nine actual-merge checks passed. The actual
[merge CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44166982779)
passed 3,180 tests plus 83 subtests on each of HA 2026.11.0/2026.11.1, with
strict coverage and full coverage of all four HGT modules. The byte-identical
tree also passed the complete local 2026.11.2 fixture. The source/merge gate is
complete; packaging and publication remain separate. Do not rerun the PR helper
or repeat the already accepted b3/b5 operator checks.

## Problem and trigger

Official measured HGT was introduced in 8.3.5b4. Its importer records the station
as owned before queuing native Recorder writes. That ordering protects
interrupted imports, but a later passive cleanup check could remove that
ownership too early.

The narrow trigger is a station change or final entry removal during its first
import, while Recorder has accepted writes but has not committed the first
metadata row. Cancelling the caller cannot retract those queued writes. The
old cleanup check could see an empty database, discard the station's ownership
record, then leave later-committed statistics outside the cleanup inventory.
An empty read is therefore not proof that nothing remains to be written.

A controlled regression reproduces this with the real HA Recorder and the
actual HGT coordinator cancellation/finally path. It blocks the first native
`ImportStatisticsTask`, changes the configured station, cancels the refresh,
then releases the writer. This is a demonstrated lifecycle defect, not evidence
that it occurred in an operator's production database. It does not explain the
earlier b4 unavailable-sensor report.

## Correction

Issue synchronization locks retired stations in stable order and rechecks that
the station set is unchanged. Before inspecting retired metadata, a native
`SynchronizeTask` waits behind already queued Recorder writes, including after
cancellation of their original caller. The wait retains the existing 30-second
bound. Only a synchronized empty result can release an unused ownership record.
The importer uses the same completion helper instead of a second implementation.
On coordinator cancellation, the passive issue scan is skipped and durable
ownership is retained, allowing unload to finish promptly even with a blocked
writer. The next normal refresh or explicit entry-removal hook performs the
synchronized inventory. No new background cleanup task is started.

If data committed, the station remains owned and its exact products remain in
the existing cleanup repair. A station change still requires the listed-target
confirmation before deleting those products. Final native integration-entry
removal still performs its already documented owned-data cleanup. A timeout,
changed target, storage failure or unverified result retains ownership and
surfaces the existing blocked-cleanup notice. Cancellation propagates; it does
not count as proof of completion or authorization to delete.

This changes no statistic/entity ID, storage schema, source validation, polling
cadence, retry policy or consent text. It introduces no new archive, account,
credential, destination, telemetry or dependency. Ordinary history and unrelated
statistics retain their existing contracts.

## Upgrade and recovery boundary

No new user action is needed for the correction itself after the ordinary
update to a published package containing it. Follow the
[stable guide](ACCEPTANCE_8.3.5.md), retaining completed b7 acceptance,
and keep the existing entry and station. Do not switch stations,
remove entries, delete data or repeat the accepted b3 cleanup as a test.
Follow the existing [ownership/removal guide](HGT_OGD_PLAN.md#ownership-and-complete-removal)
for an actual intended station change or removal.

The correction prevents premature loss of provenance; it does not adopt
pre-existing statistics whose ownership record is already missing. IDs alone
cannot safely prove ownership. Such a conflict requires a specific review or
a matching protected full backup, rather than prefix-based bulk deletion.
Published b5 availability acceptance remains closed; source regressions do not
establish a new release or whole-database absence audit.

Native regressions cover pending-write cancellation, station serialization,
target changes, failed completion barriers and the final-removal boundary.
The exact local validation result is recorded with the reviewed PR candidate;
the completed hosted/merge result is recorded above. The b6 package retains
its own reviewed source, checks and publication evidence.
