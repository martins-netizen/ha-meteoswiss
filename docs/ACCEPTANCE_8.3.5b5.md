# 8.3.5b5: update and focused HGT recovery check

**Protocol version:** 1.0 · **Package date:** 16 November 2026

**Recorded outcome, 17 November 2026:** after updating to b5 the operator
confirmed the observed-day HGT entry available. The focused availability
acceptance is closed. This protocol remains a guide for other installations;
its other fields are not inferred from that report. Do not repeat the accepted
update or b3 cleanup. [Publication and evidence limits](RELEASE_EVIDENCE_8.3.5b5.md).

The check is for the existing measured-HGT sensor after an ordinary update.
Publication availability follows the release catalogue. It does not require
repeating the accepted b3 cleanup or destructive station/removal tests.

## Update the existing integration

1. If selecting this test correction, choose published **8.3.5b5** in
   **Settings → Marketplace → MeteoSwiss**. Keep the existing entry and station.
   Verify Core **2026.11.0 or newer**. A recovery point needs a usable protected
   full HA backup with Recorder and the ownership storage together.
2. Complete the ordinary integration-update restart once. Do not reinstall
   HACS, remove the entry, change sensor IDs or rerun a migration script.
3. Let the background HGT update run. If its first attempt fails temporarily,
   b5 schedules another attempt after one minute instead of waiting six hours.
   Give the initial source/import attempt and retry time to finish. This is
   not a guarantee that an ongoing provider or Recorder outage ends in a minute.

## Read the measured sensor

On the existing weather-measurement station device choose **Heating degree
days 12/20 last observed day** (German: **Heizgradtage 12/20 letzter Messtag**).
Do not use today's HGT forecast on the forecast device as the acceptance target.

| Target | Successful state/attribute | Meaning |
|---|---|---|
| Last observed day sensor | Numeric value and `statistics_status: ready` | Current source/import verification succeeded. |
| Source date | `source_day` is a completed UTC day within the latest two UTC days | The value is a recent published observation. |
| Product IDs | Non-empty `statistic_ids` | Exact daily/monthly/annual external Recorder IDs. |
| Existing native Statistics graph | Plausible observed values using its listed IDs | Existing owned history is still available. |
| Normal weather and forecasts | Usual data available | The focused update did not disrupt normal operation. |

Read attributes under **Settings → Tools → States** without pressing
**Set state**. Use **Tools → Statistics** and the IDs provided by this sensor;
do not guess an entity suffix. For KLO the external IDs are
`meteoswiss:klo_hgt_12_20_daily`, `_monthly` and `_annual`.
See [the native graph examples](HGT_OGD_PLAN.md#charts-gaps-and-corrections).
The ordinary live sensor does not need a manually assigned state class.

If it remains **unavailable**, that is an incomplete recovery. Missing extra
attributes in that state are normal HA behaviour. Wait for the bounded retry
sequence; persistent failures can reach 15-minute intervals. Preserve any
ownership/metadata repair and report the visible state. Do not force a value,
delete statistics, change the station or repeatedly restart HA to hide it.
The precise cause of the original b4 failure is not established by this fix.

An Open-Meteo current-weather entry or HA without Recorder has no measured-HGT
entity; record that expected branch instead of inventing a passing result.

## Small private result

Report **integration/Core version**, observed-HGT available/unavailable,
`statistics_status`, `source_day`, presence of the listed products, and normal
weather/forecast operation OK/problem. Do not send tokens, full logs, personal
names or unrelated device information. No new diagnostic script is necessary
for this focused UI check.

A successful snapshot confirms this installed update and its current source
verification, not every future publication or every historical database row.
Native regressions already exercise timed recovery, existing history, shared
entries, bounded reset, conflicts, disabled polling and unload cancellation.

Users who completed the b3 obsolete-forecast repair are done with that cleanup.
Earlier-version users who receive it should follow the existing explicit
[upgrade repair](UPGRADING_8.3.5.md); b5 adds no new cleanup or replacement archive.
