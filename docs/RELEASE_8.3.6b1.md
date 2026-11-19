# MeteoSwiss 8.3.6b1

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution.

This first 8.3.6 beta brings together the changes since stable **8.3.5**.
It strengthens the checks that protect existing Recorder statistics and lets
Home Assistant keep processing other work while the integration reads large
station and pollen CSV files. Check the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for beta availability. [8.3.5 is the stable release](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5).

## What changes for existing installations

- **Older wind and heating-degree-day (HGT) forecast statistics.** Before
  archiving a series, the integration checks who owns the source ID and
  whether another entity has claimed the archive name. It checks ownership
  and the metadata again after Recorder processes the rename. A conflict
  blocks completion. A retry can recognise an already completed rename. The
  existing repair for obsolete HGT forecasts also rechecks ownership before
  clearing the statistics you explicitly confirmed. See the
  [wind history guide](WIND_STATISTICS_MIGRATION.md) and
  [HGT cleanup guide](UPGRADING_8.3.5.md).
- **Measured HGT.** Stations registered at the same time now share one check
  of the 500-station ownership limit. When the limit is reached, a rejected
  station queues no Recorder import. Older repair notices with incomplete
  metadata can be handled during upgrade.
- **Forecasts.** Home Assistant's hourly and daily forecasts now return
  precipitation probability in whole percentage points. For example, 12.5%
  rounds to 12% and 13.5% rounds to 14%. A real zero stays 0%, a missing or
  invalid value stays unknown, and the original provider values keep their
  precision.
- **Station and measured-pollen data.** A worker thread decodes and parses
  the downloaded CSV, so larger files spend less time blocking Home
  Assistant's event loop. The station catalogue and coordinator updates are
  still published on the event loop. The measured-pollen history keeps the
  most recent 24 parsed rows with the existing timestamps and readings.

For developers, CI now runs strict mypy on the full integration and on the
shared HTTP retry contract. This includes provider clients, options flows,
coordinators, entities and Recorder operations. The
[development guide](../DEVELOPMENT.md) documents the same check for a checkout.

## Trying the beta

Minimum Home Assistant Core is **2026.11.0**. The two compatibility fixtures
are **2026.11.0** and **2026.11.2**. If you choose the published beta, update
the integration through Marketplace, restart once and keep the existing entry
and settings. The [short update check](ACCEPTANCE_8.3.6b1.md) covers installed
version, forecast and normal station or pollen operation.

The package uses the signed merge of
[PR #147](https://github.com/martins-netizen/ha-meteoswiss/pull/147) at
`f9abaa12018fb89fd6c31633eadf6a975019d596`. The
[package record](RELEASE_EVIDENCE_8.3.6b1.md) identifies the reviewed source.
