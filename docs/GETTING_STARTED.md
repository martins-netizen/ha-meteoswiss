# Set up MeteoSwiss

## Location privacy before setup

This is a cloud-polling integration. Providers receive the station, postcode or
coordinates used by each request and can see the public source IP. Open-Meteo's
[API privacy notice](https://open-meteo.com/en/terms#privacy) says technical logs
may include coordinates and are deleted after 90 days. A weather-forecast point
does not move modelled pollen/AQ/UV's HA home/configured base coordinates.
Review the [source table](API_SOURCES.md) and [assessment](PRIVACY_SECURITY_REVIEW.md).

This guide describes the **8.3 series** for readers without programming experience.
You do not need an API key, MeteoSwiss account or terminal commands. Install
only a published release. **Already using MeteoSwiss?** Follow
[migration](MIGRATION.md) and keep your existing HA entry.

## What this fork provides

The integration brings Swiss weather, forecasts, natural-hazard warnings,
pollen and air quality into Home Assistant. It is an independent community
variant of the [original project](https://github.com/LNKtwo/ha-meteoswiss),
with reviewed corrections and German, English, French and Italian UI text.

| Benefit | What to expect |
|---|---|
| Current weather | Measured temperature, rain, wind and other values from a selected Swiss station. Its weather symbol is modelled for that station, not measured. |
| Forecasts for another place | A town/postcode or POI such as a mountain, with named forecast entities and today/tomorrow values. |
| Natural hazards | Active/upcoming postcode warnings, including flood and avalanche warnings when supplied by the shared feed. |
| Pollen and air quality | Measured pollen from an independently selected station, alongside modelled pollen and air quality. |
| Less manual maintenance | Bundled translations, retained settings/IDs and ordinary HA cards; no additional weather card is required. |

The fork retains the original MIT licence and attribution. It is not an official
MeteoSwiss product. Forecasts depend on providers and are not a guarantee of the
most accurate model in every situation. A failed warning feed is not an all-clear.

## 1. Check prerequisites

- For releases after 8.3.4, use Home Assistant **2026.11.0 or newer** with
  internet access. See the [security rationale](../DEVELOPMENT.md#supported-home-assistant-versions).
- **HA 2026.11 and newer** uses the built-in **Settings → Marketplace**.
- Published **8.3.4** declared a minimum of **HA 2026.8.3**. Its HACS steps
  below apply when using it on HA 2026.8.3 through 2026.10.x.
- Check the [latest stable release](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
  and [8.3.0 notes](RELEASE_8.3.0.md). A development branch is not a release.
- Create a full HA backup, download a copy and retain its recovery key securely.

<a id="2-download-through-hacs"></a>

## 2. Install a published release

The maintained fork is in the community catalogue following
[admission on 24 October 2026](HACS_ACCEPTANCE.md#hacs-catalogue-admission).
Verify **martins-netizen/ha-meteoswiss**, rather than the upstream project or
separate radar integration. Already configured from another source? Follow
[migration](MIGRATION.md) before replacing files.

### HA 2026.11 and newer: Marketplace

1. Open **Settings → Marketplace** and acknowledge the community-code notice
   if prompted. Search for **MeteoSwiss** and verify the repository above.
2. Select the announced published stable release, then choose **Install**.
   A development branch is not a release.
3. On a first installation, Marketplace opens setup and can load this integration
   without restarting HA. Continue with the location choices below. If setup
   does not open, use **Settings → Devices & services → Add integration**.
4. For an **existing installation**, keep the configured entry. Updates appear
   under **Settings → Updates** and still require an HA restart; follow the
   repair notice after installing. Do not create a second entry.

Upgrading HA to 2026.11 migrates existing HACS repositories automatically.
Do not reinstall HACS, re-add the repository or recreate the integration just
because the menu moved. Catalogue installs and updates do not require a GitHub
connection. See the [official Marketplace guide](https://www.home-assistant.io/integrations/marketplace/).

### Older HA: HACS

These steps apply to the published 8.3.4 release. Upgrade HA to 2026.11.0 or
later before moving to a newer MeteoSwiss release.

1. Open **HACS** in the sidebar, search for **MeteoSwiss** and verify the owner.
2. Open **Download/Redownload → Need a different version? → Release** and choose
   [8.3.4](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4).
3. If it is missing, refresh repository information and check the tagged release page.
   **Update information** refreshes metadata; it does not install files.
4. Actually download the selected release, restart HA and wait for it to return.
   New users then add **MeteoSwiss** under **Settings → Devices & services**;
   existing users keep their entry.

### If the repository is not listed

First refresh the catalogue/page and search again. Custom registration is a
fallback; it is normally unnecessary for this listed fork.

- **HA 2026.11+:** open **Settings → Marketplace → Add from link**. Connect
  GitHub if prompted (required for custom repositories), enter
  `https://github.com/martins-netizen/ha-meteoswiss` and choose **Add**.
  The type is detected automatically; choose **Integration** only if asked.
- **Older HA:** open **HACS → three-dot menu → Custom repositories**. Add the
  same URL with type **Integration**.

Return to the catalogue, open the fork and install the selected release as
above. If it is already listed, use that listing. Adding a URL alone does not
install files. An upstream source switch follows the
[source-switch procedure](MIGRATION.md#4-switch-hacs-software-ownership);
keep the configured HA entry and one software owner for `meteoswiss`.

## 3. Select pollen, weather and warning locations

Continue the setup opened by Marketplace, or open
**Settings → Devices & services → Add integration → MeteoSwiss** for a new entry.

For Swiss measurements, choose **MeteoSwiss STAC API (Swiss Stations)** and
explicitly select a **Station for measured pollen**. You might want a pollen
station near your HA home location. This station is independent of weather
measurements and the modelled pollen forecast. There is no preselected station.
New observation entries refresh automatically every **600 seconds**; there is
no interval field. Existing entries keep their stored individual interval.

Continue to the next dialog. Choose the **weather measurement station** and a
**four-digit Swiss warning postcode**, for example **8302**. You might want a
weather station near your home, too. The postcode selects warnings; it does
not choose the station. A failed source check leaves the form open to retry.

To locate a nearby station before choosing it, open the official
[MeteoSwiss measurement-network map](https://www.meteoswiss.admin.ch/services-and-publications/applications/measuring-networks.html)
and view SwissMetNet. Then return to HA and select the station by name. The map
does not change your HA settings. **From 8.3.1b1:** setup and Configure also
link to this map in the selected UI language. The operator accepted that test
release; stable 8.3.1 promotes the same help when announced. Stable 8.3.0 does
not show the link.

**Alternative:** Open-Meteo supplies modelled current weather at entered
coordinates instead of Swiss station observations. It is an explicit source
choice, not an automatic observation backup. Its coordinates also define that
entry's base location for modelled air quality, pollen and optional UV.

## 4. Choose the forecast location

Keep the original base location or choose **Search by postcode, town or POI**.
Enter a postcode or official catalogue name, select a result and check its name,
category and height before confirming. A postcode point is a forecast point,
not a post office or the exact position of your home. See
[selection and place-name limits](FORECAST_LOCATION_SETUP.md).

| Location | Purpose |
|---|---|
| HA home/base coordinates | Modelled air quality, modelled pollen and optional UV; also the default weather forecast if no separate point is selected. |
| Measured-pollen station | Pollen observations; independent of weather measurements and forecasts. |
| Weather measurement station | SwissMetNet observations and a separately labelled modelled weather condition at that station. |
| Forecast town/POI | ICON hourly/daily forecasts, eight today/tomorrow sensors and forecast HGT. |
| Separate warning postcode | Area for active/upcoming warnings; selecting a mountain forecast does not move it. |

For example, HA may be in Kloten, pollen measured in Zürich, weather measured
in Zürich/Kloten and forecasts selected for Säntis. Changing the forecast moves
only that role. The [README](../README.md#four-places-what-each-one-is-used-for)
explains these four places and the independent warning postcode.

## 5. Check pollen station and initial values

Open the existing entry's **Configure (gear)** to review or change the weather
station/base coordinates, measured-pollen station, forecast choice and warning
postcode in one dialog. A search continues inside it; cancelling saves none of
the pending choices. Confirmed changes reload the entry once, without an HA
Core restart. HA home coordinates remain in HA's general settings.

Open the integration's devices. Measurements and an explicitly selected
forecast place have separate names. Numeric forecast sensors cover today and
tomorrow; normal HA forecast cards provide hourly/daily predictions. Optional
sources start independently and may populate at different times.

| Display | Meaning |
|---|---|
| `0` | A real zero, for example no measured rain. |
| `unknown` | No usable individual value, including an unavailable optional station-condition code. |
| `unavailable` | The relevant source failed or its current data could not be validated. |
| Warning off | No matching alert in a successfully read feed. |

Stations do not all supply pressure, foehn index or snow depth. Missing values
do not automatically mean installation failure. The [pollen station list](POLLEN_STATIONS.md)
distinguishes real stations from temporary data availability; no substitute is
selected automatically. Older entries without a pollen choice retain Luzern
(station code PLZ) until you deliberately choose another station.

### What “Precipitation (10 minutes)” means

The latest published measured amount over one ten-minute interval. Its timestamp
marks the interval's end; it is not a continuously updated current-hour sum.
The source files publish every twenty minutes. The official archive covers
completed hours. The alternative Open-Meteo source is explicitly modelled and
exposes its interval length. See [sensors](SENSORS.md).

## 6. Use the data and get help

Use existing HA cards; translations ship with the integration. Some compatibility
attributes and provider names remain English. With a selected forecast point,
an older forecast card/action may need [one target change](FORECAST_DISPLAY.md).
The [forecast sensor guide](FORECAST_SENSORS.md) explains complete Swiss days
and the times of maximum hourly rain probability. [Cache Statistics](USAGE.md#cache-statistics-what-the-numbers-mean)
counts local cache lookups, not forecast accuracy or network requests.

For problems retain the entry and record version, time and affected value.
Use [troubleshooting](USAGE.md#quick-troubleshooting) or the
[fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues).
Use [private reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential vulnerabilities. Never post backups or credentials.

Further references: [settings](USAGE.md), [migration](MIGRATION.md),
[acceptance evidence](RELEASE_READINESS.md) and
[official Marketplace guide](https://www.home-assistant.io/integrations/marketplace/) (HA 2026.11+) and
[legacy HACS controls](https://www.hacs.xyz/docs/use/repositories/dashboard/).
