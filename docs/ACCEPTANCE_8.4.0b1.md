# Trying 8.4.0b1 on an existing installation

Once the beta appears in the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
open the installed **martins-netizen/ha-meteoswiss** integration in **Settings
→ Marketplace**. Select **8.4.0b1**, update and complete the normal restart.
Check the installed integration version and your Home Assistant Core version
(minimum **2026.11.0**).

1. **Try the place search.** Open the existing integration’s **Configure**
   dialog and search for a forecast location. Enter *Morat* and look for
   **3280 Murten**. A search by postcode *3280* also offers Greng and
   Meyriez as separate points. Close the dialog before confirming to keep
   your current forecast location.
2. **Check your forecast device.** After the normal refresh, open the two
   solar radiation sensors for the current hour. Each uses W/m² and provides
   an `hourly_forecast` attribute with 24 hourly intervals. A value of zero
   at night is valid. An unavailable sample appears as `null` in the series.
3. **Check the gust forecast.** The peak gust sensor shows the maximum of
   24 valid hourly gusts. Its `peak_start` and `peak_end` attributes identify
   the first hour that reaches that value. Incomplete coverage leaves the
   peak unknown. The window begins at the start of the current clock hour.

When reporting the result, include the installed integration and Core
versions and the search or forecast display you checked.
[Forecast sensor details](FORECAST_SENSORS.md#solar-radiation-and-peak-gusts)
