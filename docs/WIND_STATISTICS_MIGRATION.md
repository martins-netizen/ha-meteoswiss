# Wind direction: preserve arithmetic history, start circular statistics

**8.3.5 stable scope:** this migration was introduced in the test line and is
retained unchanged from the published b7 runtime. Use the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability and the [stable update guide](ACCEPTANCE_8.3.5.md). Earlier
accepted operator checks stay closed; no repeated migration is required.

The [current upgrade guide](UPGRADING_8.3.5.md) recommends explicitly confirmed
removal of obsolete **HGT forecasts**. Wind is a different boundary: its older
arithmetic averages are intentional retained history under an archive ID. The
integration does not delete or reinterpret that archive to silence a notice.
Native rename/readback checks protect the old rows before circular statistics
start at the retained wind sensor ID. This is not b2's historical HGT
archive-and-keep policy.

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

**In development.** When the migration needs an archive, it checks the sensor's
registry identity and the archive name after reading Recorder. A previous
registry owner of an existing source series or a recorded claim on the
destination blocks the move. If an entity claims the archive after Recorder
has queued the rename, the rename can finish. The migration reports a conflict
and a later retry verifies the stored archive before enabling circular statistics.

An existing compatible circular series can continue when a deleted entity
claims only the arithmetic archive ID and the current sensor still owns
its series. Recorder keeps both series. MeteoSwiss leaves
`arithmetic_statistics_archive` empty while the archived series has an
ambiguous owner. The ownership checks still apply to new migrations and
conflicts at the current sensor ID.

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
`arithmetic_statistics_archive` identifies the retained archive when its ownership is verified.
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
