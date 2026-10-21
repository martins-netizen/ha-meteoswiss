# Set up MeteoSwiss

This guide is for readers without programming experience. You do not need a
MeteoSwiss account, API key or terminal commands. HACS must already be installed;
its official setup guide is linked below.

**Already using MeteoSwiss?** Follow [migration](MIGRATION.md) instead and retain
your existing HA integration entry.

## What this fork provides

The integration brings Swiss observations, forecasts, warnings, pollen and air
quality into your usual Home Assistant dashboards. A fork is a maintained
variant of the [original project](https://github.com/LNKtwo/ha-meteoswiss).
Reviewed fixes and four UI languages ship together.

| Benefit | What to expect |
|---|---|
| Follow local weather | Swiss station observations, official hourly rain statistics and a model forecast. The station does not measure at your house. |
| Follow natural hazards | Active/upcoming postcode warnings with severity and event text, including BAFU flood and SLF avalanche warnings when the feed supplies them. |
| Include pollen and air quality | Measurements from your selected pollen station, alongside modelled pollen and air quality. |
| Reduce manual maintenance | Bundled German, English, French and Italian UI text; no additional weather card is needed. |
| Understand missing data | A real zero, a missing individual value and a failed source are distinct. A failed warning source is not an all-clear. |

This fork combines documented corrections to warning mapping, data age and rain
statistics. Its changes, tests and known limits are public, with a dedicated
[issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues).
Some capabilities may already exist in your current version.

Experienced users can go directly to [settings and sources](USAGE.md),
[sensors](SENSORS.md), [warning codes](WARNING_CODES.md) or
[architecture](ARCHITECTURE.md). This is an independent community project;
the linked release status applies to all features described here.

### What “Precipitation (10 minutes)” means

It is the latest published **measured amount over one ten-minute interval**.
The measurement time marks that interval's end: 12:20 means the ten minutes
ending at 12:20, even if HA downloads the value later. It is not a continuously
updated amount through the present moment. The station files used here are
published every twenty minutes.

A separate official statistics archive covers completed hours. The fork no
longer creates its own current-hour sum. With the alternative Open-Meteo source,
precipitation is modelled and labelled **Precipitation (modelled interval)**;
its actual interval length is available as an attribute.

## 1. Check prerequisites

- Home Assistant **2026.8.3 or newer**, with working internet access.
- HACS already installed. Otherwise follow the
  [official HACS installation guide](https://www.hacs.xyz/docs/use/download/download/).
- Read [release status](../README.md#release-status). Install only the explicitly
  approved version; a development branch or successful CI run is not approval.
- Under **Settings → System → Backups**, create a full backup, download a copy
  and retain its recovery key securely.

A prerelease is a test version, not an automatically approved everyday release.

## 2. Download through HACS

1. Open **HACS** in the sidebar.
2. Open the top-right **three-dot menu → Custom repositories**.
3. Enter `https://github.com/martins-netizen/ha-meteoswiss`, choose
   **Integration** and select **Add**.
4. Open **MeteoSwiss (maintained fork)** and **Download**. Expand
   **Need a different version?**, select **8.2.0b1** under **Release**, and check
   the announced version before confirming. Older HACS versions may also need
   beta visibility. If the intended version is missing, stop; do not substitute
   a commit or development branch.
5. Restart Home Assistant and wait for the interface to return.

**Three-dot menu → Update information** refreshes repository metadata without
downloading components. The [HACS acceptance record](HACS_ACCEPTANCE.md)
distinguishes the completed operator-confirmed source switch from the still-open
clean first-install test.

Downloading supplies software. The next step configures its data locations.

## 3. Select a weather station and warning location

Open **Settings → Devices & services → Add integration → MeteoSwiss**.

For measured Swiss weather, choose **MeteoSwiss STAC API (Swiss Stations)**.
You do not need to work with its underlying API. Keep the initial update
interval at **600 seconds**.

Choose a weather station and enter the warning location's **four-digit
postcode**, for example **8302**. Do not enter the six-digit internal App code.
The integration checks the weather source before saving; a connection error
leaves the same form available to retry.

| Setting | Purpose |
|---|---|
| Weather station, for example Zürich / Kloten | Measured temperature, rain, wind and other station values. |
| Postcode | Weather/natural-hazard warning selection. |
| Home Assistant home location | Weather forecasts, modelled pollen and air quality. |
| Measured-pollen station | Pollen observations; select independently in integration options. |

The postcode does not automatically select the weather station. Check the HA
home location under **Settings → System → General** and change it only if it is
wrong; other integrations also use it.

**Alternative:** **Open-Meteo API (Free, Global)** supplies modelled current
conditions at entered coordinates. It is an explicitly different source, not an
automatic backup for Swiss station observations. Warnings still use the
four-digit postcode.

## 4. Check pollen station and initial values

Open the existing MeteoSwiss entry's **Configure** options and choose a
measured-pollen station. It is not derived from the weather station.
The current default is **Luzern (PLZ)**; PLZ is that station's identifier.

Open the integration's devices. Expect weather, observation sensors, three
warning sensors and pollen/air-quality entities. HA forecasts cover up to
24 hours and five days. Additional optional sources start in the background;
they need not all populate simultaneously.

| Display | Meaning |
|---|---|
| `0` | A real zero, for example no measured precipitation. |
| `unknown` | No usable individual value is available. |
| `unavailable` | The relevant source could not be refreshed successfully. |
| Warning sensor off | No matching alert in a successfully read warning feed. |

Foehn index or snow depth may stay unknown when the station does not supply
them. Missing UV alone does not establish an outage of other data.
An unavailable warning source is not an all-clear.

## 5. Use the data and get help

Use the entities in existing HA cards. A custom dashboard/card is not required.
DE/EN/FR/IT ship with the integration; do not copy translation files manually.
Some existing device/attribute names and provider choices retain English names
for compatibility.

Forecasts use **MeteoSwiss ICON Seamless via Open-Meteo**. They are model output,
not measurements at your house or a guaranteed selection of the most accurate
model in every situation. Modelled air quality does not replace a local sensor.

For problems, retain the integration instead of deleting/recreating it.
Record version, time and affected value; use [troubleshooting](USAGE.md#quick-troubleshooting)
or the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues).
Use [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential security reports.

Further references: [sensors](SENSORS.md), [technical settings](USAGE.md) and
[official HACS controls](https://www.hacs.xyz/docs/use/repositories/dashboard/).
