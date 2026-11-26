# Trying 8.4.0b3 on an existing installation

After the beta appears in the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
open the installed MeteoSwiss repository in **Settings → Marketplace**.
Open the three-dot menu, choose **Install another version**, select
**8.4.0b3** and restart Home Assistant after installation.

To receive future beta updates through the normal update workflow, choose
**Include pre-releases** from the same menu and confirm. See the
[Marketplace documentation](https://www.home-assistant.io/integrations/marketplace/#keeping-installations-up-to-date).

1. **Search in the same form.** In MeteoSwiss **Configure**, choose Search.
   Enter `Morat` in the field that appears and submit the form. Look for
   **3280 Murten** in the results. Close the dialog before confirmation to
   keep your existing forecast location.
2. **Inspect the hourly gust forecast.** After a forecast refresh, open the
   24-hour peak gust sensor in **Developer tools → States**. Confirm that
   `hourly_forecast_unit` is `km/h` and that `hourly_forecast` contains 24
   intervals with `start`, `end` and `value`. Check `peak_start` and `peak_end`
   against the first interval with the highest value when all 24 values are
   available. If the sensor state is displayed in km/h, compare it with that
   value. A missing hour has a `null` value and leaves the peak state unknown.
3. **Check any dashboard that uses the gust series.** If a card shows when
   gusts reach a configured threshold, compare its time with the earliest
   known interval at or above that threshold. A missing interval may hide
   an earlier crossing. If your dashboard also shows global and diffuse
   solar radiation, check both series in W/m² after a refresh.

When reporting a result, include the installed integration and Home Assistant
Core versions and which checks you completed.
[Forecast sensor details](FORECAST_SENSORS.md#solar-radiation-and-peak-gusts)
