# MeteoSwiss 8.4.1

Forecasts, natural-hazard warnings, pollen and air quality can start when the
first current-weather refresh fails. Each service still depends on its own
data source. Current-weather entities show as unavailable until a normal
polling cycle receives fresh data. When station measurements are stale, the
setup log shows the age of the latest measurement in minutes.
[Startup fix #163](https://github.com/martins-netizen/ha-meteoswiss/pull/163)

## Update an existing installation

Use Home Assistant Core **2026.11.0** or newer. Once 8.4.1 appears in the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
open **Settings → Marketplace → MeteoSwiss** from **martins-netizen/ha-meteoswiss**.
Update your existing installation to **8.4.1** and complete the normal
restart. Keep your entry, station and options.

After the update, verify the installed version and check the forecast, warnings
and air quality after their first refresh. If current weather is unavailable,
check the setup log for the observation age and let the normal polling cycle
retry.

[Previous release notes](RELEASE_8.4.0.md)
