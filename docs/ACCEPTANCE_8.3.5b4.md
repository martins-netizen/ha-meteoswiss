# 8.3.5b4: focused measured-HGT acceptance

**Protocol version:** 1.0 · **Package date:** 15 November 2026

Publication, installation and successful first source/Recorder import are
separate evidence. Earlier b3 update/obsolete-forecast cleanup and b1/b2/wind
acceptance remain closed. Do not repeat deletion or create legacy test data.

## Update the existing entry normally

Once the announced [8.3.5b4 release](RELEASE_8.3.5b4.md) is published, update
through Marketplace and restart once as normally required for an integration
update. Keep the existing entry, station, IDs, names and dashboards. Retain a
usable protected full backup outside HA when a recovery point is required;
Recorder and the ownership storage belong together. There is no standalone
migration script, manual state-class setting or database edit.

## One focused read-only check

1. Confirm integration **8.3.5b4** and HA Core **2026.11.0 or newer**. An old
   Marketplace sidebar minimum can be the separately documented Core display
   mismatch; inspect the package/version rather than downgrading HA.
2. On the existing **weather-measurement station** device, find **Heating degree
   days 12/20 last observed day** (German: **Heizgradtage 12/20 letzter Messtag**).
   It is separate from today's forecast HGT on the forecast device. Initial
   backfill runs in the background; let that first attempt finish. No current
   value is fabricated while source/Recorder verification is incomplete.
3. Read the entity's attributes under **Developer tools → States**, without
   pressing Set state. Expected for successful current data:
   `value_type: observation`, `reference_time_zone: UTC`,
   `statistics_status: ready`, a completed `source_day` within the latest two
   UTC days, and a non-empty `statistic_ids` map. Point counts describe the
   available official products, not an independently audited continuous history.
4. Under **Developer tools → Statistics**, confirm the exact IDs listed by that
   sensor. KLO's example IDs end in `klo_hgt_12_20_daily`, `_monthly`, `_annual`.
   Use the [native graph example](HGT_OGD_PLAN.md#charts-gaps-and-corrections)
   to view observed daily amounts; monthly/annual bars use their own official
   products. Do not use an old forecast archive as input or a daily cumulative
   sum as one day's amount. Confirm normal weather/forecast operation too.

No station change, entry removal or destructive cleanup is required on
production for this check. Native tests already cover shared entries, station
changes, consent, corrections, cancellations, exact deletion and physical row
absence. Already cleaned b3 forecast statistics must not be recreated.

An Open-Meteo current-weather entry or HA without Recorder has no measured-HGT
entity; record that expected branch. A station without available official HGT,
source failure or stale publication is not a successful live import, and is not
a reason to manufacture a zero. Report its visible state without changing the
selected station merely to complete the check.

## Small private result and recovery

Report integration/Core version, observed-HGT available/delayed/unavailable,
status, source day, presence/counts of the listed products, graph plausibility
and normal operation OK/problem. Keep tokens, personal names, unrelated device
data and raw provider responses out of the report.

A successful first import confirms that bounded installed-source snapshot; it
does not manually prove every future correction or continuous publication.
The six-hour/weekly schedules and revision semantics have native regressions.
An optional later read-only comparison can confirm subsequent operation without
requiring a new broad acceptance window.

Keep ownership/metadata conflicts visible. Do not clear all statistics or edit
HA storage. Software rollback alone cannot undo Recorder data changes; restore
a matching full backup only through a separate controlled recovery action.
The [removal boundary](HGT_OGD_PLAN.md#ownership-and-complete-removal) explicitly
explains that final integration-entry deletion removes owned measured products.
