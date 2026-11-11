# Wind direction: preserve arithmetic history, start circular statistics

**Status:** Unreleased follow-up; published stable 8.3.4 is unchanged.

For equal durations, 350° and 10° have a circular mean of north (0°), not
the old arithmetic 180°. HA [stops a series when its mean algorithm changes](https://www.home-assistant.io/docs/configuration/long-term-statistics/#when-the-unit-or-the-state-class-changes).
Historical arithmetic means cannot be reconstructed as correct circular means.

## Contract

- Keep unique/entity/device IDs, valid numeric degrees, personal names/icons/aliases,
  enabled/disabled choices and the ordinary state-history identity.
- Before enabling `WIND_DIRECTION`/`MEASUREMENT_ANGLE` statistics, inspect Recorder
  metadata. An empty target or an already circular series can continue.
- Rename a compatible arithmetic series with HA's supported metadata API to
  `sensor.meteoswiss_wind_arithmetic_<registry_id>`. Its metadata row ID and
  attached statistic rows stay the same. No SQL, deletion, recalculation,
  in-place algorithm conversion or backfill is performed.
- Read back and verify the archive before enabling the angle state class.
  New circular statistics use the retained sensor ID and a new metadata row.
- An occupied archive, unexpected metadata, failed Recorder startup or timeout
  blocks the transition. Current readings and raw history continue without a
  state class; incompatible new statistics are not produced.

Calm wind (speed zero) has no direction and is published as unknown. Invalid,
non-finite or out-of-range directions also stay unknown; valid 0°/360° still
mean north when wind is not calm. This follows HA's wind-direction contract.
Other observation and weather-entity values are unchanged.

A blocked transition creates an entry-specific warning under **Settings →
System → Repairs**, translated in DE/EN/FR/IT. It links to this guide, clears
after a successful retry and is removed on unload. It does not expose a database
path or raw exception. Resolve the Recorder/metadata problem before reloading;
do not delete historical statistics to silence the warning.

Preparation runs after HA startup in an entry-owned background task, cancelled
on unload. Waiting does not cancel Recorder's shared readiness future. Reload
recognizes an archived/already circular series and a previous interruption after
renaming. With Recorder disabled there is no local series to migrate.

## Charts, diagnosis and recovery

`wind_statistics_status` is `pending`, `ready` or `blocked`.
`arithmetic_statistics_archive` identifies the retained archive when present.
Existing current-value automations keep their sensor ID. Statistics charts for
that ID start a new circular series; select the archive ID for older arithmetic
averages. Those old values remain arithmetic, not corrected directions.

The archive has no live sensor, so HA's Statistics tools can flag that expected
condition. Do not delete the archive to hide it if its history is needed.
Ordinary retention still governs raw states and short-term rows; no extra
lifetime guarantee is made.

Retain a verified backup before deploying a release with this migration.
Software rollback alone does not undo the database change. The tested reverse
sequence first archives any new circular series under a distinct free ID, then
restores the old arithmetic ID. That is separate controlled recovery; there is
no automatic rollback or overwrite of an occupied destination.

Native HA/SQLite tests cover the blocked direct change, old metadata/rows,
real 350°/10° circular compilation, registry choices, conflicts, readback failure,
cancellation, startup/reload and a reverse sequence retaining both algorithms.
They do not constitute a migration or manual acceptance of an operator's DB.
