# MeteoSwiss 8.4.2b1

This beta addresses the archive conflict reproduced for issue #162. An
existing circular wind direction series can continue when a deleted
registry entry claims only the arithmetic archive ID and the current
sensor's ownership is clear. Recorder preserves both histories. MeteoSwiss
can leave `arithmetic_statistics_archive` empty while the archive's owner
is unclear. An ownership conflict at the current sensor ID still blocks
preparation. [Issue #162](https://github.com/martins-netizen/ha-meteoswiss/issues/162) · [PR #165](https://github.com/martins-netizen/ha-meteoswiss/pull/165)

## Download and install the beta in Marketplace

Use Home Assistant Core **2026.11.0** or newer. Keep a verified backup of
Home Assistant and its Recorder history.

1. Once **8.4.2b1** appears in the release catalogue, open **Settings →
   Devices & services → Marketplace** and select the device for
   **martins-netizen/ha-meteoswiss**. Enable the **Pre-release** entity
   if it is disabled, then switch it on.
   [Release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases) ·
   [Marketplace update documentation](https://www.home-assistant.io/integrations/marketplace/#keeping-installations-up-to-date)
2. In **Settings → Marketplace**, open your existing **MeteoSwiss**
   repository from **martins-netizen/ha-meteoswiss**. Open the three-dot
   menu, choose **Install another version**, and select **8.4.2b1**.
   Marketplace downloads and installs that version on the existing entry.
   Keep your configured station and options.
   [Marketplace version selection](https://www.home-assistant.io/integrations/marketplace/#installing-another-version)
3. When installation finishes, use Home Assistant's restart reminder to
   restart Home Assistant. Confirm that Marketplace shows **8.4.2b1** as
   installed.

## Check the wind direction statistics

1. In **Developer tools → States**, open your existing wind direction
   sensor. After startup, check `wind_statistics_status` and `state_class`.
   For the archive-only conflict, expect `ready` and `measurement_angle`.
   Check whether the repair for the missing state class has cleared.
2. After fresh wind readings and a Recorder interval, check that the same
   sensor's circular statistics have advanced. If you know the arithmetic
   archive ID, look it up in **Developer tools → Statistics** and check its
   older history. Keep both series in Recorder while testing.
3. Report the Home Assistant Core version, installed MeteoSwiss version,
   `wind_statistics_status`, and whether the repair cleared and both
   histories are visible. If the state is still `blocked`, preserve the
   history and report the remaining repair.
