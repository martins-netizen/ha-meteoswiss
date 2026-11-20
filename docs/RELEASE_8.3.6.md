# MeteoSwiss 8.3.6

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution.

8.3.6 carries forward the integration tested in **8.3.6b1**. For users of
stable 8.3.5, the main changes concern older weather statistics, the chance
of rain shown in forecasts, and the processing of station and pollen data.

## Changes since 8.3.5

- **Wind and heating-degree-day (HGT) history.** Before archiving a series, the
  integration checks which entity owns the source ID and whether another entity
  has claimed the archive name. It verifies ownership and metadata again when
  Recorder finishes the rename. The repair for obsolete HGT forecast statistics
  also rechecks ownership before removing a series you confirmed. A conflicting
  owner blocks cleanup. [Wind history](WIND_STATISTICS_MIGRATION.md) ·
  [HGT cleanup](UPGRADING_8.3.5.md)
- **Measured HGT.** Concurrent station registrations respect the existing
  500-station ownership limit. When capacity is reached, a rejected
  registration queues no statistics import. The integration also handles older
  repair notices with missing metadata.
- **Rain forecasts.** Hourly and daily forecasts return the chance of
  precipitation in whole percentage points. Halfway values round to the
  nearest even integer, so 12.5% gives 12% and 13.5% gives 14%. Missing values
  stay unknown and a genuine zero stays zero. The provider data retains its
  original precision.
- **Stations and measured pollen.** Worker threads decode and parse downloaded
  CSV files, leaving Home Assistant's event loop available while large files
  are processed. Measured-pollen history keeps the most recent 24 parsed rows.
- **Development checks.** CI runs strict mypy across the integration. Tests for
  optional weather data wait for the initial background refresh before reading
  a value after setup or reload. [PR #149](https://github.com/martins-netizen/ha-meteoswiss/pull/149)

## Updating

The minimum Home Assistant Core version is **2026.11.0**. Once Marketplace
lists stable 8.3.6, update the existing entry and complete its normal restart.
An installation on 8.3.5 can move directly to 8.3.6. If you already use the
published beta, the stable package carries the same runtime behaviour. The
beta operator confirmed station weather, daily forecast extremes and the
24-hour forecast display on HA Core 2026.11.2. [Existing-entry update guide](ACCEPTANCE_8.3.6.md)
