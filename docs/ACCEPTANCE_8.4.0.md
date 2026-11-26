# Updating an existing installation to MeteoSwiss 8.4.0

Use Home Assistant Core **2026.11.0** or newer. You can update the existing
installation from 8.3.6 or 8.4.0b3 once stable 8.4.0 appears in the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).

1. In **Settings → Marketplace**, open **MeteoSwiss** from
   **martins-netizen/ha-meteoswiss**. Select stable **8.4.0** and complete
   the normal restart. Keep the existing entry, station and options.
2. Verify that the installed version is **8.4.0** and check your usual
   weather and forecast views after the next refresh.
3. If you use the new forecast sensors, check the global and diffuse
   radiation series in W/m² and the gust series in km/h on the forecast
   device. [Forecast sensor details](FORECAST_SENSORS.md#solar-radiation-and-peak-gusts)

The stable package carries forward the runtime from 8.4.0b3.
The [release notes](RELEASE_8.4.0.md) describe the changes since stable 8.3.6.
