# MeteoSwiss 8.4.0b1

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution.

This first 8.4 beta adds new ways to find a forecast location and three
forecast sensors for dashboards and automations.

- **Find a place in another Swiss language.** Searching for *Genf* or
  *Ginevra* finds **1201 Genève**. Searching for *Morat* finds **3280 Murten**.
  Home Assistant displays and saves the MeteoSwiss catalogue name and point
  you select. Search aliases cover 184 postal forecast points.
- **Plan with solar radiation and wind gusts.** On the forecast device, two
  sensors show mean global and diffuse solar radiation for the current hour
  in W/m². Each includes 24 hourly values. A third sensor shows the strongest
  forecast gust in that window and the earliest hour in which it occurs.
  It reports a peak only when all 24 gust values are available. Hourly
  forecast gusts are also available through `weather.get_forecasts`.

All three sensors use the existing ICON Seamless request for your chosen
forecast location. The minimum Home Assistant Core version is **2026.11.0**.
[Instructions for trying the beta on an existing installation](https://github.com/martins-netizen/ha-meteoswiss/blob/8.4.0b1/docs/ACCEPTANCE_8.4.0b1.md)
