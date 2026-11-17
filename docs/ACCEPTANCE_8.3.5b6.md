# 8.3.5b6: normal update and read-only check

**Protocol version:** 1.0 · **Updated:** 17 November 2026

Use this once after choosing the published **8.3.5b6** test package. Confirm
availability in [the release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).
Keep the existing configured entry and station. Core 2026.11.0 or newer is
required; an existing 2026.11.2 installation needs no Core update for this check.

1. In **Settings → Marketplace**, open this integration and download/update
   **8.3.5b6**. Complete the normal update restart once. Refreshing repository
   information alone does not install the package. Verify its installed version.
2. For a configured official MeteoSwiss measurement station with Recorder,
   after the integration's normal refresh, open **Heizgradtage
   12/20 letzter Messtag** / **Heating degree days 12/20 last observed day**.
   Read the value and, in Developer Tools → States, its `statistics_status:
   ready`, completed `source_day`, and `statistic_ids` map for official daily,
   monthly and annual HGT. Zero is valid when supplied by the source. This is
   distinct from today's HGT forecast. For Open-Meteo current-weather entries,
   or without Recorder, this measured-HGT check is **not applicable**; absence
   of that feature is expected and is not a package failure.
3. Where official hourly precipitation imports and Recorder are active, inspect
   their existing statistics in a chart already using them or in **Developer
   Tools → Statistics**. No new chart or dashboard is required. Real **0 mm**
   is valid; rainfall need not occur.
   Retained history/current completed values or an explicit partial/source
   failure status must not be confused with manufactured zero or a new hourly
   entity. This importer uses external Recorder statistics. Where this family
   is not configured or Recorder is absent, this check is **not applicable**.
4. Check the existing weather, forecast and ordinary station sensors. Report
   only a new repair or warning category if one appears; do not post raw logs,
   coordinates, entry IDs, tokens or personal device names publicly.

Do not press **Set state**, add a state class, switch stations, remove the
entry, force a timeout or delete statistics to test this package. Those
boundaries have native regressions. Previously accepted b3 cleanup and b5
availability stay complete. New upgrading users may see the existing explicit
obsolete-forecast repair; its [confirmation boundary](UPGRADING_8.3.5.md) is
separate from this read-only check.

An unavailable measured-HGT value is not acceptance. A temporary failure retries
after one minute with bounded backoff up to 15 minutes; verified success restores
the six-hour cadence. Persistent failure/conflict remains visible and needs its
specific diagnosis. Do not infer ready from old chart rows alone.

This check confirms installed-package operation within the observed scope. It
does not reproduce a pending-write race, audit every historical row, prove every
hour present or establish full Gold/independent assurance. [Notes](RELEASE_8.3.5b6.md)
and [evidence](RELEASE_EVIDENCE_8.3.5b6.md) retain those limits.
