# Measured HGT: bounded recovery after a transient failure

**Status: unreleased follow-up.** Published 8.3.5b4 retains the previous
six-hour failure cadence. The change described here requires a later reviewed
and published package; it does not alter any existing release or tag.

## What changes

An observed-HGT refresh can fail while Home Assistant starts or reloads, or
while a source or Recorder operation is temporarily unavailable. In b4 the
coordinator then waits for its normal six-hour poll. Existing statistics can
already be present while the latest-observed-day entity remains unavailable.
Their presence alone does not justify reporting a verified current value.

Transient failures now ask Home Assistant's native coordinator to retry after
60 seconds, then 120, 240, 480 and at most 900 seconds. The first delay exceeds
the shared manager's 30-second failure cooldown. Successful source/import
verification resets this sequence and restores the normal six-hour cadence.
There is one Core-owned timer, no separate retry task or new persistent state.
Disabling entry polling also disables this automatic retry, and entry unload
cancels the pending timer.

An ownership or metadata conflict retains the existing repair and normal
interval. The retry does not adopt foreign statistics, weaken source checks,
change source identities, bypass native commit/readback, delete data or create
an archive. It continues to report unavailable until verification succeeds.

## Evidence and limits

Native regressions inject one controlled import failure, then advance Core's
real polling timer. They cover both empty and already populated Recorder
history, entity recovery after one minute, unchanged existing rows, restored
six-hour polling, bounded repeated failures, success reset, conflict repairs,
disabled polling, unloading before the retry and multiple entries sharing one
verified station import.

These tests establish the retry behaviour. They do not identify the underlying
cause of a particular operator's first failure. A generic b4 error message or
existing rows must not be presented as proof of a Recorder timeout or complete
current availability.

## Existing users

Keep the entry, station, entity IDs and owned statistics. Once the follow-up
package is announced, update normally. No database edit, helper archive,
station change, entry recreation or repeated legacy-forecast cleanup is needed.
The accepted b3 forecast cleanup and published b4 feature remain separate.

For a focused check, read the measured entity's current state and source day,
and inspect its own statistic IDs under Developer tools → Statistics. During
an unsuccessful attempt the state remains unavailable; after verified recovery
the sensor reports `statistics_status: ready`. Missing source values remain
gaps, not invented zeroes. A single ready snapshot is not a guarantee about
every later refresh. See [the source contract](HGT_OGD_PLAN.md) and
[the b4 read-only acceptance scope](ACCEPTANCE_8.3.5b4.md).
