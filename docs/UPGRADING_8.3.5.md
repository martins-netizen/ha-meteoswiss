# 8.3.5 statistics migration: archive and keep history by default

**Release boundary:** **8.3.5b2** is the fixed test package described here.
Select it only once the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b2)
confirms publication; installation and [focused HGT acceptance](ACCEPTANCE_8.3.5b2.md)
remain separate. Published **8.3.5b1** still has the old HGT state-class Repair;
installing b1 again will not add this fix. Stable **8.3.4** remains latest.
The test line requires HA **2026.11.0 or newer**.

## Recommended default: automatically archive and keep

The normal update path requires no statistics-deletion decision. The
8.3.5b2 fix keeps existing entities, settings and ordinary history, moves
compatible old HGT forecast statistics to a separate archive, verifies that
their metadata row and attached data are retained, then asks Core to recompute
its repair issues. The resolved HGT state-class repair disappears through
that native recomputation. It is not manually dismissed or suppressed.

There is **no automatic deletion, fake measurement state class, replacement
archive sensor or new user setting to choose**. Existing wind archives keep
their current IDs and contents. Only genuine conflicts require diagnosis.

| Situation | Recommended action | Expected result |
|---|---|---|
| You currently have 8.3.5b1 and the HGT state-class repair | Keep the data and update to 8.3.5b2 once its publication is confirmed. Close the current deletion dialog without deleting. | This is an interim step, not acceptance of a permanently unresolved repair. |
| You update to the explicitly published 8.3.5b2 test package | Follow the normal existing-entry update below. No Delete action is part of it. | Old HGT statistics are archived; the live forecast keeps its original ID and no measurement state class. Native repair recomputation clears the resolved HGT notice. |
| HGT status is `ready` and an archive ID is present | Continue using the forecast normally. Select the archive only if you need its older statistics in a statistics chart. | Old forecast averages remain available as historical data; no new HGT measurement statistics are generated. |
| HGT status is `ready` and no archive exists | Continue normally. | There was no compatible old HGT series to move. This is not a before/after database audit. |
| HGT or wind preparation is `blocked` | Keep both existing series and IDs; open the entry-specific MeteoSwiss Repair for diagnosis. | No destination is overwritten or history deleted. Current forecasts/readings and ordinary history continue. |

## 1. Before and during an approved update

1. Keep a protected, usable before-update backup. A software downgrade alone
   does **not** reverse statistics metadata changes.
2. Exercise a historical migration on an existing test/restored copy before
   production. Creating/restoring a copy is a separate operator action. If no
   older statistics exist, record that the historical branch was not exercised.
3. Keep your existing integration entry, entity IDs, personal names, aliases,
   enabled/hidden choices and dashboards. Do not remove/recreate the entry.
4. Select the explicitly published fixed test version in the existing
   maintained-fork Marketplace entry, download it and restart HA once. Do not
   select a development branch or reinstall an already accepted version.
5. Check normal operation and the two statuses below. A successfully completed
   transition does not require a statistics purge or repeated restart.

## 2. HGT: what is preserved and what clears the repair

The affected sensor is **Heating degree days 12/20 today (forecast)**. Its
full-day prediction is neither a measured temperature nor an accumulating
measured total. Its current value and original entity ID continue unchanged.

Older versions produced arithmetic long-term statistics under that live ID.
Simply removing the inappropriate measurement state class leaves the old
metadata associated with a numeric sensor and causes Core's state-class Repair.
The 8.3.5b2 fix instead preserves that old metadata row under
`sensor.meteoswiss_hgt_forecast_archive_<registry_id>`, keeping its attached
long-term and short-term rows without recalculation. Core can then recognise
that the live forecast no longer owns a measurement-statistics series.

In **8.3.5b2**, open **Developer tools → States**, find the existing
HGT sensor and read its attributes; do not use Set state:

- `hgt_statistics_status: ready`: archival preparation and native repair refresh
  completed. A `forecast_statistics_archive` value identifies the retained series.
- `pending`: preparation is still running after startup; if it persists, collect
  a bounded diagnostic report.
- `blocked`: the archive, metadata or native repair refresh could not be verified.
  Follow the MeteoSwiss Repair; do not clear it by deleting historical data.

These new HGT attributes are not present in the published 8.3.5b1 package.
No new HGT measurement-statistics points are expected in either corrected
version. Ordinary state history still follows your existing Recorder retention.

## 3. Wind: existing archives and new circular statistics

The wind default already preserves old arithmetic statistics before starting
new circular statistics. The HGT follow-up does not rename an existing wind
archive again or change the wind algorithm.

Read `wind_statistics_status` and `arithmetic_statistics_archive` on the existing
wind-direction sensor under **Developer tools → States**:

- `ready`: new circular statistics are permitted. The live sensor keeps its ID.
- An archive value identifies old arithmetic averages; copy its **exact** ID.
- An empty archive needs no archive-chart action; it is not proof that older
  data never existed.
- `blocked`: current readings can continue, but incompatible new statistics
  are held back. Diagnose the real conflict without deletion or renaming.

Calm wind can legitimately have an unknown direction. Historical arithmetic
means are not recalculated or presented as corrected circular means.

## 4. Only if you use older statistics in a chart

Ordinary History charts keep the original sensor IDs. Long-term statistics
charts must use the archive for the older series; the live wind ID represents
the new circular series, while the HGT forecast produces no new measurement
statistics. No archive chart is required for normal current-value dashboards.

Copy the actual archive value from the relevant sensor attribute. In a
Statistics graph card's code editor, enter that statistic ID as the entity:

```yaml
type: statistics-graph
entities:
  - entity: sensor.COPY_THE_ACTUAL_ARCHIVE_ID
    name: Historical forecast or wind averages (archive)
stat_types:
  - mean
```

Replace the entire example ID; do not invent the registry suffix. Keep old wind
arithmetic averages separate from new circular averages and label old HGT data
as historical forecasts. Archive rows are not expected to acquire new points.

An archive deliberately has no live sensor. HA's advanced Statistics catalogue
can identify that fact; it is distinct from the persistent **live HGT sensor
has no state class** Repair cleared by the fix. Do not delete an archive to
silence catalogue diagnostics, and do not claim every catalogue entry is a new
runtime fault or that this change hides all validation results.

## 5. A genuine conflict or recovery

Open **Settings → System → Repairs** and the relevant MeteoSwiss notice. Keep
the existing entity and archive, record the installed version/status and whether
an archive is shown, and request diagnosis. Do not overwrite an occupied archive,
rename IDs, execute SQL or purge rows. Provider readings can continue while a
statistics transition is blocked.

Software rollback alone does not undo either metadata transition. Controlled
restoration or reverse migration requires separate approval and a verified
backup. No deletion, restoration or forced retry is automatic. The
[wind preservation contract](WIND_STATISTICS_MIGRATION.md) and
[focused acceptance protocol](ACCEPTANCE_8.3.5b2.md) retain their evidence limits.
