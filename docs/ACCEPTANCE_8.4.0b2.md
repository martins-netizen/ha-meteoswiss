# Trying 8.4.0b2 on an existing installation

After the beta appears in the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
open the installed MeteoSwiss repository in **Settings → Marketplace**.
Open the three-dot menu, choose **Install another version**, select
**8.4.0b2** and restart Home Assistant after installation.

If the beta is missing from the list, open the repository's Marketplace
device under **Settings → Devices & services → Marketplace**, enable its
**Pre-release** entity and turn on the switch. See the
[Marketplace documentation](https://www.home-assistant.io/integrations/marketplace/#keeping-installations-up-to-date).

1. **Search in the same form.** In MeteoSwiss **Configure**, choose Search.
   Enter `Morat` in the field that appears, then submit the form. Check for
   **3280 Murten** in the results. Close the dialog before confirmation to
   keep your existing forecast location.
2. **Review the weather dashboard on your tablet.** After a forecast refresh,
   check the 24-hour global and diffuse solar radiation series (W/m²) and
   verify that the forecast peak gust and its time are readable. If the card
   is absent, open the forecast device to check the underlying sensors. Zero
   radiation at night is valid. The peak gust is unavailable when one or more
   of the 24 hourly gust values are missing.

When reporting a result, include the installed integration and Home Assistant
Core versions and which checks you completed.
[Forecast sensor details](FORECAST_SENSORS.md#solar-radiation-and-peak-gusts)
