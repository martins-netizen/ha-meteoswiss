# MeteoSwiss 8.4.0b2

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution.

- **Search for your forecast location in fewer steps.** The postcode or
  place-name field appears in the same form when you choose Search in initial
  setup, Configure or Reconfigure. Submit to see the matches, choose a point
  and confirm it. If the search finds no match, edit the query in place.
  [PR #155](https://github.com/martins-netizen/ha-meteoswiss/pull/155)
- **Check solar radiation and wind gusts for your forecast location.** This
  beta includes the hourly global and diffuse solar radiation, 24-hour peak
  gust and multilingual postal search names introduced in
  [8.4.0b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.4.0b1).
- The minimum Home Assistant Core version is **2026.11.0**. Compatibility
  tests cover both 2026.11.0 and 2026.11.3.

[Try the beta on an existing installation](https://github.com/martins-netizen/ha-meteoswiss/blob/8.4.0b2/docs/ACCEPTANCE_8.4.0b2.md)
