# Trying 8.3.6b1 on an existing installation

Choose this check after **8.3.6b1** appears in the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).
The minimum Home Assistant Core version is 2026.11.0.

1. In **Settings → Marketplace**, open the installed MeteoSwiss integration
   from **martins-netizen/ha-meteoswiss**. Select **8.3.6b1** from its
   available versions, update and complete the normal restart. Verify that
   Marketplace shows **8.3.6b1** as the installed version.
2. Open your usual station and forecast displays after their normal refresh.
   Where available, hourly and daily rain probabilities should appear as whole
   percentages. If you use measured pollen, check whether the selected
   station's latest reading or usual availability indication appears.
3. If you already chart wind or measured HGT history, open an existing chart
   and check that the expected series is available. If a new repair appears,
   note its title. Opening or confirming a cleanup, removing an entry or
   changing Recorder data is unnecessary for this check.

To report the result, give the installed integration and Core versions and
which displays worked or showed a new issue. Include the repair title if relevant.
The [beta notes](RELEASE_8.3.6b1.md) describe changes since stable 8.3.5.
