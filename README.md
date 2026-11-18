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
explain the changes from 8.2.0. Use a published release, not a branch.

**8.3.5b7 Gold engineering package:** the approved Gold source completion minimizes
native diagnostics downloads, publishes warning/forecast changes at local time
boundaries and uses INFO for optional-source outage/recovery transitions.
The complete 51-rule engineering assessment has passed source head and actual-
merge checks. This is a custom integration without an official Gold award or
independent security certification.

Check the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability before selecting **8.3.5b7**; these notes do not publish or
install it. Use the [short normal update and read-only check](docs/ACCEPTANCE_8.3.5b7.md),
[release notes](docs/RELEASE_8.3.5b7.md) and
[staged evidence](docs/RELEASE_EVIDENCE_8.3.5b7.md).
Published **8.3.5b6** remains the earlier bounded-accepted test package until
superseded in the catalogue. B7 retains its HGT ownership/recovery and
[precipitation resource limits](docs/PRECIPITATION_RESOURCE_BOUNDS.md).
Existing entries, IDs and statistics remain; accepted b3 cleanup and b5/b6
checks stay complete. Source validation, package checks, publication and
installed acceptance have separate evidence. **8.3.4 remains latest stable.**

**Published [8.3.5b4 test package](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b4):**
official measured HGT 12/20 history, initial backfill, continuing source
corrections and explicit ownership/removal. Published on **15 November 2026**;
release/tag/body and retention of all nineteen earlier releases are independently
confirmed. Keep the existing entry and update normally if choosing this test
release. Publication is complete; focused measured-HGT availability was later
operator-confirmed on b5. [Release notes](docs/RELEASE_8.3.5b4.md),
[publication evidence](docs/RELEASE_EVIDENCE_8.3.5b4.md) and
[the short read-only check](docs/ACCEPTANCE_8.3.5b4.md) explain the new entity and
station-specific statistics. Removing the final integration entry also removes
its owned OGD HGT products; normal sensor history and unrelated statistics remain.

**Earlier accepted cleanup, retained in later 8.3.5 betas:** [8.3.5b3](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b3)
packages the native **Remove obsolete HGT forecast statistics** repair. It
recommends complete removal of old forecast statistics after one clear
confirmation. Current forecasts, ordinary history and unrelated statistics are
retained; no unused replacement HGT archive remains after completed cleanup.
Published on **15 November 2026**; the operator confirmed the focused native
cleanup successful. See [publication and acceptance evidence](docs/RELEASE_EVIDENCE_8.3.5b3.md).
[Release notes](docs/RELEASE_8.3.5b3.md), [upgrade instructions](docs/UPGRADING_8.3.5.md)
and [the short focused check](docs/ACCEPTANCE_8.3.5b3.md) explain the deletion
boundary. **8.3.4 remains latest stable.** HA **2026.11.0 or newer** is required.

**Package-specific HA minimum:**

| Package | Required HA Core |
|---|---|
| 8.3.5b1 / b2 / b3 / b4 / b5 / b6 / b7 | 2026.11.0 or newer |
| Latest stable 8.3.4 | 2026.8.3 or newer |

The HA 2026.11.1 Marketplace page can show an installed beta together with the
minimum of the stable release it is following. The beta still requires
2026.11.0. See [the reproduced display mismatch](docs/MARKETPLACE_VERSION_DISPLAY.md).
Marketplace may also read the README from the installed immutable tag. B4's
tagged README retains its preparation wording; the release catalogue and
[current publication evidence](docs/RELEASE_EVIDENCE_8.3.5b4.md) confirm availability.
A documentation update on development does not change that tagged snapshot.

**Existing users, including b2:** update the existing entry normally; then use
**Settings → System → Repairs** if old HGT forecasts are found. Opening or
cancelling the repair deletes nothing. Confirming permanently removes the exact
listed old statistics and metadata. Earlier daily series, b2 archives and
attributable retired season series are covered, including disabled forecast
sensors. Read [ownership/conflict limits](docs/UPGRADING_8.3.5.md) before confirming.
No Mac script or entry recreation is needed. B2 itself retains its historical
archive-and-keep behaviour; the new cleanup is included in b3.

**In 8.3.5b4: official measured HGT 12/20.** A separate observed-day
sensor and station-specific daily/monthly/annual statistics import the official
OGD products, backfill available observations and recheck corrections. Forecasts
keep their existing identity. This feature is **not in published b3**. B4 is
published; focused availability is accepted on b5. See [sources, charts and removal](docs/HGT_OGD_PLAN.md).
Removing the final MeteoSwiss integration entry also removes its owned OGD HGT
statistics; normal sensor history and unrelated series are retained.

**Available in the community catalogue.** On HA **2026.11 or newer**, open
**Settings → Marketplace** and search for **MeteoSwiss**. On older HA versions,
use HACS. Check that the repository is **martins-netizen/ha-meteoswiss**.
Existing HACS installations migrate automatically when HA upgrades to 2026.11;
do not reinstall HACS or recreate the MeteoSwiss entry.

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

The source completion follows **all 51 Home Assistant rules through Gold**:
20 Bronze prerequisites, 10 Silver prerequisites and 21 Gold rules. The
[current matrix](docs/QUALITY_SCALE.md), [exact evidence index](docs/quality_rules.json)
and [completion review](docs/GOLD_COMPLETION_REVIEW.md) link each applicable
contract to source, native tests or a recorded review; exemptions explain why.
Custom integrations have no official HA quality tier, so this is an engineering
assessment rather than a badge or manifest claim.

The completion corrects diagnostic-download privacy and time-only warning and
forecast state updates, aligns optional-source transition logs and verifies
the fixed seven service groups and complete entity metadata. Both existing
HA compatibility jobs check fresh JUnit/coverage from their single full run.
No new source requests, credentials, station discovery or deletion permission
is introduced. Existing names, IDs, personal choices and statistics remain.

[PR #129](https://github.com/martins-netizen/ha-meteoswiss/pull/129) completed
source head and actual-merge checks at `8887597ebf8567b5969ee70b8f9dd6f261603aec`.
The earlier #125–#128 candidates were closed unmerged as replaced.
[B7 preparation](docs/RELEASE_EVIDENCE_8.3.5b7.md) packages this approved source;
its package checks, publication and installed acceptance remain separate, as
explained in the [delivery review](docs/GOLD_COMPLETION_REVIEW.md#what-remains-separate).
Use the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability; published b6 and its accepted bounded operator check do not
include these later source changes. [Security boundaries](docs/GOLD_SECURITY_BOUNDARIES.md)
keep provider retention, HA host controls and independent assurance explicit.
The dated owner-authenticated security inventory remains scoped to
**11 November 2026**, not a fresh alert clearance.

[HACS catalogue admission](docs/HACS_ACCEPTANCE.md#hacs-catalogue-admission)
and accepted previous releases remain recorded distribution milestones.
[Four-language names](docs/ENTITY_NAME_TRANSLATIONS.md), [icons](docs/ICON_TRANSLATIONS.md),
[errors](docs/EXCEPTION_TRANSLATIONS.md), [shared diagnostic ownership](docs/SHARED_DIAGNOSTIC_LIFECYCLE.md)
and [conservative native device removal](docs/DEVICE_REMOVAL.md) retain their
tested contracts. The [dependency advisory gate](docs/DEPENDENCY_ADVISORIES.md)
still rejects active or unknown findings for either complete universal lock.

## Start here

| Your situation | Guide |
|---|---|
| First installation | [Step-by-step setup](docs/GETTING_STARTED.md) |
| Existing MeteoSwiss installation | [Switch or update safely](docs/MIGRATION.md) |
| Experienced HA user | [Data and settings](docs/USAGE.md), [warning codes](docs/WARNING_CODES.md), [architecture](docs/ARCHITECTURE.md) |
| Settings, missing data or troubleshooting | [English usage reference](docs/USAGE.md) |

## Release status

**[Stable 8.3.4 is published](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4)
and is the normal installation and update target.** Publication on
**7 November 2026 at 21:24:27 UTC** was independently verified, including the
release tag, approved English notes and selection as latest stable. See the
[publication evidence](docs/RELEASE_EVIDENCE_8.3.4.md).

Compared with 8.3.3, this maintenance and quality release provides:

- **Verified HA 2026.11 support**, using the matching official HA test package
  and reproducible dependency locks.
- **A cleaner first setup**, with optional diagnostic helpers initially disabled.
  Existing enabled helpers, personal settings, names, icons and IDs are retained.
- **Clearer data-source information**, including modelled Open-Meteo current
  conditions and explicit virtual data-service groups.

Read [what the update means for existing users](docs/RELEASE_8.3.4.md#why-upgrade-from-833).
Use **Settings → Marketplace** on HA 2026.11+, or HACS on older HA. Keep the
existing configured entry, actually Download/Redownload **8.3.4** and restart HA
once, following the [short stable update](docs/ACCEPTANCE_8.3.4.md). Refreshing
repository information alone does not download files. The
[latest stable page](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
is authoritative.

**Earlier beta 8.3.4b1 is provenance, not the current installation target.**
Its normal operation was operator-confirmed on **HA Core 2026.11.0 / HA OS 18.4**.
Stable 8.3.4 retains all 39 non-version component files from that accepted beta;
only two version fields change. Historical beta references and their
[bounded evidence](docs/RELEASE_EVIDENCE_8.3.4b1.md) remain accurate. The HGT
statistics follow-up stays outside this stable release.

Earlier stable **8.3.3** remains an immutable previous release and recovery
option. Its actual installation and normal operation were operator-confirmed
on 30 October; see [that release's evidence](docs/RELEASE_EVIDENCE_8.3.3.md).
Earlier beta, shared-settings, clean-install and restore checks remain complete
within their recorded scopes. An intermediate beta or older stable download
is not required.

**8.3.5 support baseline.** The test line requires **HA 2026.11.0 or
newer**. This Core baseline brings fixes for known vulnerabilities in
dependencies shipped with older Core releases. CI tests **2026.11.0** and
**2026.11.2** with their matching official test packages.
[Core security rationale](DEVELOPMENT.md#supported-home-assistant-versions)

Published stable **8.3.4** declared **HA 2026.8.3** as its minimum. Its
package-merge jobs passed **2,225 tests plus 83 subtests** on HA 2026.8.3 and
2026.11.0. For installations on older HA, follow the
[8.3.4 setup guide](https://github.com/martins-netizen/ha-meteoswiss/blob/8.3.4/docs/GETTING_STARTED.md).

Native icons and translated errors are retained from stable 8.3.3. The
[51-rule Gold source assessment](docs/QUALITY_SCALE.md) is complete at approved
#129. B7 package validation, publication and its focused installed check retain
separate evidence; no official tier or independent certification is claimed.

**8.3.5 test-line wind-statistics change.** Wind direction uses HA's circular angle
statistics after a verified migration. Existing arithmetic statistics are kept
under a separate archive ID; new circular statistics use the original sensor.
Review [chart impact, repair notices and rollback](docs/WIND_STATISTICS_MIGRATION.md)
before updating. Calm wind has no direction and is reported as unknown.

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
2. On **HA 2026.11+**, open **Settings → Marketplace**, acknowledge the community-code
   notice if prompted, and search for **MeteoSwiss**. Verify
   **martins-netizen/ha-meteoswiss**. For 8.3.4 on older HA, open **HACS**.
   For a different installed source, follow migration first. The
   [custom-repository fallback](docs/GETTING_STARTED.md#if-the-repository-is-not-listed)
   explains **Add from link** and the older HACS menu.
3. Select a published stable release that supports your HA version. For an **update**,
   use **Settings → Updates** on HA 2026.11+, then restart through the resulting
   repair notice. For 8.3.4 on older HA, use **Download/Redownload → Need a
   different version? → Release** in HACS, then download and restart.
   Refreshing metadata alone does not install files. Keep one software owner
   for `meteoswiss`.
4. **New users only:** Marketplace opens setup after the first installation;
   no restart is normally needed for an integration not previously loaded.
   Alternatively use **Settings → Devices & services → Add integration → MeteoSwiss**.
   On older HA, restart after the HACS download before adding the integration.
   Choose weather source, measured-pollen station, observation station/base
   coordinates, warning postcode and the independent forecast town/POI.
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

