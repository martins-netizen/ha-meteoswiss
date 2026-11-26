# MeteoSwiss 8.4.0b3

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution.

- **Find the hour when forecast gusts reach your threshold.** The 24-hour
  peak gust sensor now includes an hourly series with timestamps and gust
  speeds in km/h. Dashboards and automations can read the series and apply
  their own thresholds. Missing hourly values appear as `null`.
  [PR #157](https://github.com/martins-netizen/ha-meteoswiss/pull/157)
- **Search for your forecast location in fewer steps.** The postcode or
  place-name field appears in the same form when you choose Search in initial
  setup, Configure or Reconfigure. Submit to see matching points and confirm
  a selection. If the search finds no match, edit the query in place.
  [PR #155](https://github.com/martins-netizen/ha-meteoswiss/pull/155)
- The hourly global and diffuse solar radiation and multilingual postal
  search names from [8.4.0b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.4.0b1)
  are included. The minimum Home Assistant Core version is **2026.11.0**.
  Compatibility tests cover 2026.11.0 and 2026.11.3.

[Try the beta on an existing installation](https://github.com/martins-netizen/ha-meteoswiss/blob/8.4.0b3/docs/ACCEPTANCE_8.4.0b3.md)
