# Updating an existing installation to stable 8.3.6

You can update directly to [stable 8.3.6](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.6)
from 8.3.5 or 8.3.6b1. The minimum Home Assistant
Core version is 2026.11.0.

1. In **Settings → Marketplace**, open **MeteoSwiss** from
   **martins-netizen/ha-meteoswiss**. Select stable **8.3.6** and complete the
   normal restart. Keep the same integration entry, station and options.
2. Verify the installed version reads **8.3.6** and open your usual weather
   and forecast views after their normal refresh.

The operator already confirmed the station weather, daily minimum and maximum
temperatures, and the 24-hour forecast display on the released beta. A stable
update from 8.3.6b1 changes the integration version and requires no repeated
beta checks. The [release notes](RELEASE_8.3.6.md) describe what changes for
users upgrading from 8.3.5. If an older installation shows an existing HGT
repair, the [upgrade guide](UPGRADING_8.3.5.md) explains its separate
confirmation step.
