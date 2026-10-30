# MeteoSwiss for Home Assistant — maintained fork

<img src="custom_components/meteoswiss/brand/icon.png" alt="Weather icon of the maintained fork" width="96" height="96">

**Swiss weather, forecasts and natural-hazard warnings in Home Assistant,
alongside pollen and air quality.** Use them in your own dashboards and
automations, with bundled translations and a documented path for existing users.

This fork continues [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and brings reviewed corrections together in one maintained version. The original
project provides the foundation; its MIT licence and attribution are retained.
This is an independent community project, not an official MeteoSwiss product.

**Start with the [latest published stable release](https://github.com/martins-netizen/ha-meteoswiss/releases/latest).**
This guide describes the **8.3 series**; [8.3.0 release notes](docs/RELEASE_8.3.0.md)
explain the changes from 8.2.0. Use a published HACS release, not a branch.

**Available in the HACS default catalogue.** Search for **MeteoSwiss** in HACS
and check that the repository is **martins-netizen/ha-meteoswiss**.

## Four places: what each one is used for

**HA home, pollen measurements, weather measurements and weather forecasts can
refer to four different places.** Each has a specific purpose:

| Place | What it is used for | Example |
|---|---|---|
| **1. HA home location** | The HA base coordinates are used for **modelled air quality, modelled pollen and optional UV via Open-Meteo**. They also define the **MeteoSwiss weather-forecast location** when you keep or explicitly return to the original base coordinates. | Your configured home position in **Kloten**. |
| **2. Pollen measurement station** | **Measured pollen concentrations** from the selected MeteoSwiss pollen station. Independent of weather measurements and weather forecasts. You might want to choose a station near your HA home location. | **Zürich (PZH)**. |
| **3. Weather measurement station** | **Measured current temperature, wind, rain and other observations**, shown on the station device and its original weather entity. You might want to choose a station near your HA home location. | **Zürich/Kloten**. |
| **4. Weather forecast location** | **ICON predictions:** hourly/daily forecasts, eight today/tomorrow sensors and calculated heating degree days. The separate forecast weather entity also shows the chosen point's **current model hour**, which is a prediction rather than a station measurement. | A selected town/postcode point or **Säntis** POI. |

The station weather row can also show a **modelled condition for the measuring station's own location**.
Its numeric values remain measurements; the condition is identified separately
as modelled. See [the source and failure behaviour](docs/STATION_WEATHER_CONDITION.md).

Find nearby SwissMetNet stations on the official
[MeteoSwiss measurement-network map](https://www.meteoswiss.admin.ch/services-and-publications/applications/measuring-networks.html),
then select the station by name in HA. The [setup guide](docs/GETTING_STARTED.md#3-select-pollen-weather-and-warning-locations)
also explains the map-link help included in stable 8.3.2.

For example: **HA home in Kloten, pollen measurements from Zürich, weather
measurements from Zürich/Kloten and weather forecasts for Säntis.** Changing
the forecast to Säntis changes its ICON predictions and calculated HGT. The
Kloten observations, selected pollen measurement station and modelled
AQ/pollen/UV at the base location retain their own places.

**Measured pollen and modelled pollen are different:** the pollen station
supplies measurements; modelled pollen uses the base coordinates. If you choose
an explicit forecast point, that point replaces the base location **only for
the ICON weather forecast role**.

**Warnings use a separate warning postcode**, for example **8302** for Kloten.
A postcode entered in the forecast search selects a forecast point; the warning
postcode selects the warning area. Enter them independently, even when both
are 8302. Choosing Säntis for the forecast does not move the warning postcode
or establish warnings for that mountain. A town/postcode forecast point is a
provider-assigned point, not the exact coordinates of your home.

The alternative **Open-Meteo current-weather source** uses modelled current
conditions at its entered coordinates in place of a weather measurement station.
These entered coordinates also become that entry's base location for
AQ/pollen/UV and its default weather forecast. An explicit forecast selection
still changes only the ICON forecast role.

The existing entry's **Configure (gear)** brings the **weather measuring
station, measured-pollen station and forecast location into one dialog**,
alongside the independent warning postcode. A postcode/town/POI search continues
inside that flow; cancelling preserves previous choices. The HA home location
remains a general HA setting. See the [unified settings and clock-change guide](docs/CALENDAR_AND_LOCATION_SETTINGS.md).

The [selection guide](docs/FORECAST_LOCATION_SETUP.md) and
[data/settings reference](docs/USAGE.md) explain the roles. The named
forecast device/card change is covered in [display and migration](docs/FORECAST_DISPLAY.md).

## Why choose this fork?

- **Less manual patching.** Reviewed fixes and German, English, French and Italian
  UI catalogues ship together. You do not need to copy translation files after
  each update.
- **Warnings with a checked meaning.** The current App v3 source and verified
  warning catalogue address the old wind-code mismatch and the demonstrated
  omission of drought in v1. Active and upcoming warnings retain their severity,
  validity and event text. See the [evidence and limits](docs/WARNING_CODES.md).
- **Understand missing data.** A real zero, a missing individual value and an
  unavailable source are distinct. A failed warning source is not an all-clear;
  an optional pollen or air-quality outage does not block station setup.
- **Build on your existing installation.** Existing setup and the IDs of retained
  entities and statistics are preserved. The [migration guide](docs/MIGRATION.md)
  explains the retired seasonal heating-degree entity, warning-filter changes,
  backup and recovery.
- **See how changes are checked.** Public review history, automated HA tests,
  CodeQL, SonarCloud and HACS validation accompany changes. The [overall review](docs/RELEASE_REVIEW_2026-10-24.md)
  records evidence and remaining work; the fork has its own support and private
  security-reporting routes.

On an older installation, check which fixes it already contains; not every
listed capability is new compared with every upstream version or local patch.
Forecasts and warning availability still depend on the external data providers.

Read the [plain-language overview](docs/GETTING_STARTED.md#what-this-fork-provides).

## Quality goals: Bronze, Silver and Gold

We follow the [Home Assistant Integration Quality Scale](https://contributors.home-assistant.io/core/quality-scale/)
as an engineering checklist, with rule-by-rule code, test and documentation
evidence. The following summarises the **8.3 series**, with the b4 runtime and
the bounded repair/map and 8.3.2b1 shared-settings follow-ups accepted by the operator. Home Assistant's [custom-integration guidance](https://contributors.home-assistant.io/marketplace/guides/integrations/#keep-up-with-home-assistant)
explains that custom integrations have no official quality tiers; Bronze,
Silver and Gold below identify the rules we use to guide improvements.

| Goal | What it means for you | Current evidence and remaining work |
|---|---|---|
| **Bronze: a sound foundation** | Setup in HA, stable entity identities, tested setup and clear instructions. | The checklist records setup/configuration tests, identity checks, installation guides and valid bundled brand images. |
| **Silver: reliable operation** | Clear unavailable states, recovery from source failures, clean unloading and a maintained support route. | All applicable Silver rules have recorded evidence, including more than 95% coverage per module. The checklist also records the underlying Bronze rules; focused b4 HA acceptance is operator-confirmed. |
| **Gold: a more complete user experience** | Easier configuration, useful diagnostics, translations and actionable help. | The shared location dialog and actionable repair notices have bounded evidence; the repair/map follow-up was accepted in 8.3.1b1. Remaining work includes icon/error translations, diagnostic defaults, metadata and stale-device handling, plus review of proposed exemptions. The five-step shared-Reconfigure check was reported positive on Core 2026.10.4. |

The [rule-by-rule assessment](docs/QUALITY_SCALE.md) links the scope, test evidence
and remaining work. [HACS catalogue admission](docs/HACS_ACCEPTANCE.md#hacs-catalogue-admission)
is complete and provides a separate distribution/review milestone. We keep the
quality checklist as a transparent engineering record, without an awarded-tier
badge or manifest claim.

**Accepted 8.3.1b1 follow-up:** [actionable repair notices](docs/REPAIRS.md) guide
users from an invalid saved forecast location to the existing settings. Official
station-map links help find nearby SwissMetNet stations. The operator confirmed
the requested version/visual check on 26 October. Published stable [8.3.1](docs/RELEASE_8.3.1.md) retains that runtime.
The published [8.3.2b1 follow-up](docs/RELEASE_8.3.2b1.md) adds the complete
Reconfigure route. The operator reported all five focused steps positive on
HA Core **2026.10.4**. Stable [8.3.2](docs/RELEASE_8.3.2.md) was published on
28 October; on 30 October the operator confirmed its HACS download, restart
and working operation. See [the bounded evidence](docs/RELEASE_EVIDENCE_8.3.2.md).

## Start here

| Your situation | Guide |
|---|---|
| First installation | [Step-by-step setup](docs/GETTING_STARTED.md) |
| Existing MeteoSwiss installation | [Switch or update safely](docs/MIGRATION.md) |
| Experienced HA user | [Data and settings](docs/USAGE.md), [warning codes](docs/WARNING_CODES.md), [architecture](docs/ARCHITECTURE.md) |
| Settings, missing data or troubleshooting | [English usage reference](docs/USAGE.md) |

## Release status

**[Stable 8.3.2](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.2)
is published and is the normal installation route.** Release ID **426633496**,
published **28 October 2026 at 12:21:19 UTC**, from
**aea4c5eab0534a6e675a4f564bde7521df193c58**. It retains the accepted 8.3.2b1
runtime, changing only two component version files. Both Configure and
Reconfigure offer the complete location-settings transaction.

The operator reported the five focused beta steps positive on **HA Core
2026.10.4**, then confirmed the actual **8.3.2 HACS download, HA restart and
working operation on 30 October**. The [release evidence](docs/RELEASE_EVIDENCE_8.3.2.md)
separates those reports from source, CI and publication checks. The
[short stable protocol](docs/ACCEPTANCE_8.3.2.md) is complete for that installation;
other users follow the normal update guide without repeating our earlier tests.

The [latest stable release page](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
is authoritative for normal installation. Select a published release in HACS;
refreshing repository information alone does not download files. Existing users
retain their configured entry. Earlier 8.3.1/beta releases and their immutable
notes remain history; an intermediate 8.3.1 download is not required.

Minimum supported HA is **2026.8.3**. Hosted CI also covers **2026.10.1**;
additional local regression tests cover **2026.10.3**. Operator reports on
2026.10.2/2026.10.3 and the five-step beta report on 2026.10.4 keep their own
scope; the stable update report supplies no new Core/Python version.
[HACS default-catalogue admission](docs/HACS_ACCEPTANCE.md#hacs-catalogue-admission),
earlier clean-install/restore checks and the 8.2-to-8.3 update are complete.
The [readiness record](docs/RELEASE_READINESS.md) retains their evidence.

## Data and compatibility

- SwissMetNet observations and hourly precipitation statistics.
- MeteoSwiss ICON Seamless forecasts via Open-Meteo.
- [Eight forecast sensors](docs/FORECAST_SENSORS.md)
  for today/tomorrow, including matching maximum-probability rain windows.
- Active/upcoming weather and natural-hazard warnings through the MeteoSwiss
  postcode feed, with explicit feed availability. This includes flood (BAFU)
  and avalanche (SLF) warnings when supplied for the selected postcode; it is
  not a separate river-gauge or full avalanche-bulletin integration.
- Measured pollen, pollen forecasts and air quality.
- Complete German, English, French and Italian UI catalogues.

The integration domain remains `meteoswiss`. Existing config entries and the
IDs of retained entities/statistics are preserved. The obsolete forecast-only
season-HGT entity is intentionally retired; review that exception in the
[migration guide](docs/MIGRATION.md). Warning automations should use numeric `warn_type`
and `warn_level`, and must treat an unavailable source separately from no alert.

Warnings use the App v3 source and its [verified thirteen-family catalogue](docs/WARNING_CODES.md).
Before updating an existing installation, review warning filters: **0 is Wind,
4 is Slippery Roads**; wind/thunderstorm/rain uses `[0, 1, 2]`. Detailed messages
distinguish storm/heavy-rain/snowfall events. Thaw (6) is recognized if supplied.
Dashboard and automation migration is a separate deployment step.

## Cache Statistics

The optional **Cache Statistics** diagnostic shows how often a local lookup
reuses data still within its cache lifetime. A higher hit rate can mean fewer
repeated downloads; it does not measure forecast accuracy or service health.
There is no target percentage to achieve. See [what the counters mean](docs/USAGE.md#cache-statistics-what-the-numbers-mean).

## Installation and updates

An existing installation must first be checked for its source and installed
commit/version. Do not remove or recreate the integration/config entry.
For installation or update:

1. Back up Home Assistant and keep the recovery key. Existing users first read
   the [migration and warning-consumer checks](docs/MIGRATION.md).
2. Open **HACS**, search for **MeteoSwiss** and choose the entry whose repository
   is **martins-netizen/ha-meteoswiss**. If this fork is already downloaded, open
   that entry. For a different installed source, follow the migration guide
   first. [Custom-repository steps](docs/GETTING_STARTED.md#if-the-repository-is-not-listed)
   are a fallback when the catalogue entry is not yet visible.
3. Open **Download/Redownload → Need a different version? → Release** and select
   the announced stable release. Refresh repository information if needed;
   then actually download it and restart HA. Do not keep two HACS repositories
   managing the same `meteoswiss` directory.
4. **New users only:** add **MeteoSwiss** in **Settings → Devices & services**.
   Choose the current-weather source and a measured-pollen station, then the
   observation station/base coordinates and the independent warning postcode.
   Choose whether to keep the base forecast location or search for a town/POI.
5. Existing users retain their HA entry. **Configure** edits the three MeteoSwiss
   location choices together; the HA home location remains in HA's own settings.

New observation entries refresh automatically every **600 seconds**; existing
individual intervals remain effective. No polling field is shown. The
[forecast selection guide](docs/FORECAST_LOCATION_SETUP.md) explains search,
confirmation and reset. With an explicit catalogue forecast, update an existing
forecast card/action target once as described in [display migration](docs/FORECAST_DISPLAY.md).
UI languages ship with the software; no API key or terminal command is required.
`development` is the maintained default branch; `main` tracks upstream.

The optional [shared warning template](examples/button-card-warnings.yaml) uses
labels supplied by the integration. It can replace duplicated dashboard warning
dictionaries after a separate dashboard check; it is not installed automatically.

See [setup, all parameters, removal and troubleshooting](docs/USAGE.md).

## Development and operation

- [Location/POI implementation plan and later quality work](docs/NEXT_RELEASE_PLAN.md)
- [Overall release review of 24 October 2026](docs/RELEASE_REVIEW_2026-10-24.md)
- [Historical review of 17 October 2026](docs/REVIEW_2026-10-17.md)
- [Quality roadmap and measured gaps](docs/QUALITY_SCALE.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Maintenance, acceptance and releases](docs/MAINTENANCE.md)
- [HACS publication checklist and release-note outline](docs/PUBLISHING.md)
- [Branch policy](DEVELOPMENT.md)
- [Changes](CHANGELOG.md)

Follow the [local compatibility checks](DEVELOPMENT.md#local-compatibility-checks)
in separate environments for both supported HA fixtures. The shared recipe
includes the Python/pip bootstrap check, constrained CA-bundle installation,
offline uv policy, translations and full line/branch coverage gates.

`development` is the protected integration branch; `main` tracks upstream.
Use this fork's [issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
for ordinary problems and
[private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential security reports. Bug reports should
include the installed fork version/commit, HA version, relevant states and
redacted logs. Do not upload full private backups or credentials.
Existing development PRs remain the review record.
Provider outages must remain distinguishable from a valid empty/no-danger value.

