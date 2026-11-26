# MeteoSwiss 8.4.0

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution.

8.4.0 carries forward the integration tested in
[8.4.0b3](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.4.0b3).
The main changes since stable 8.3.6 concern forecast-location search, solar
radiation and wind gusts.

- **Find Swiss places by names in other national languages.** Search for
  *Genf* or *Ginevra* to find **1201 Genève**, or *Morat* to find **3280 Murten**.
  Results use the MeteoSwiss catalogue name and postcode.
  [PR #152](https://github.com/martins-netizen/ha-meteoswiss/pull/152)
- **Choose a forecast location in fewer steps.** When you choose Search in
  setup, Configure or Reconfigure, enter the postcode or name in that form.
  The result list lets you select and confirm the location. If there is no
  match, edit the query in the same form.
  [PR #155](https://github.com/martins-netizen/ha-meteoswiss/pull/155)
- **Use solar radiation and wind gust forecasts in dashboards and automations.**
  The forecast device provides 24 hourly values for global and diffuse solar
  radiation in W/m². The peak gust sensor offers the hourly gust series in
  km/h and identifies the earliest strongest gust when all 24 hours are
  available. Missing hourly values appear as `null`. These data come from
  the existing ICON Seamless forecast request.
  [PR #157](https://github.com/martins-netizen/ha-meteoswiss/pull/157)

The minimum Home Assistant Core version is **2026.11.0**. Once Marketplace
lists stable 8.4.0, update the existing installation and complete the normal
restart.
[Existing-installation update guide](ACCEPTANCE_8.4.0.md) ·
[Forecast sensor details](FORECAST_SENSORS.md#solar-radiation-and-peak-gusts)
