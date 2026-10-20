# MeteoSwiss for Home Assistant — maintained fork

<img src="custom_components/meteoswiss/brand/icon.png" alt="Weather icon of the maintained fork" width="96" height="96">

**Swiss weather, forecasts and natural-hazard warnings in Home Assistant,
alongside pollen and air quality.** Use them in your own dashboards and
automations, with bundled translations and a documented path for existing users.

This fork continues [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and brings reviewed corrections together in one maintained version. The original
project provides the foundation; its MIT licence and attribution are retained.
This is an independent community project, not an official MeteoSwiss product.

**First maintained-fork beta: `8.2.0b1`.** The deployed runtime has completed
its live acceptance. See [release availability and beta limits](#release-status)
before installing.

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
  entities and statistics are preserved. The [migration guide](docs/WECHSEL_DE.md)
  explains the retired seasonal heating-degree entity, warning-filter changes,
  backup and recovery.
- **See how changes are checked.** Public review history, automated HA tests,
  CodeQL and HACS validation accompany changes. The [quality review](docs/REVIEW_2026-10-17.md)
  records evidence and remaining work; the fork has its own support and private
  security-reporting routes.

On an older installation, check which fixes it already contains; not every
listed capability is new compared with every upstream version or local patch.
Forecasts and warning availability still depend on the external data providers.

Deutsch: [Was bringt mir dieser Fork im Alltag?](docs/START_DE.md#was-bringt-mir-dieser-fork)

## Start here / Hier beginnen

| Your situation / Deine Situation | Guide / Anleitung |
|---|---|
| First installation / Neu einrichten | [Schritt für Schritt auf Deutsch](docs/START_DE.md) |
| Existing MeteoSwiss installation / Bestehende Installation | [Sicher wechseln oder aktualisieren](docs/WECHSEL_DE.md) |
| Experienced HA user / HA bereits vertraut | [Data and settings](docs/USAGE.md), [warning codes](docs/WARNING_CODES.md), [architecture](docs/ARCHITECTURE.md) |
| Settings, missing data or troubleshooting | [English usage reference](docs/USAGE.md) |

## Release status

**8.2.0b1 is the first maintained-fork beta, with completed deployed
24-hour acceptance.** It is intended for explicit prerelease testing.
Download it only when the [published GitHub prerelease](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.2.0b1)
is available. If that page is not available, publication has not completed;
do not substitute a tag or development-branch download.

Minimum supported/tested HA: **2026.8.3**; CI also covers **2026.10.1**.
The candidate additionally passed local tests and deployed acceptance on
**2026.10.2**. See the [beta notes and known limits](docs/RELEASE_8.2.0b1.md).
The operator confirmed the HACS 2.0.5 source switch, downloaded version
`8.2.0b1`, restart and a positive initial visual check on 20 October 2026.
A clean first HACS installation remains open. The [HACS acceptance record](docs/HACS_ABNAHME_DE.md)
distinguishes this operator-confirmed result from independent technical evidence.
A default-store listing and an official HA quality tier are not claimed.
The [current acceptance and stable-release checklist (German)](docs/FREIGABESTAND_DE.md)
separates completed beta work from the remaining release gates and later features.

## Data and compatibility

- SwissMetNet observations and hourly precipitation statistics.
- MeteoSwiss ICON Seamless forecasts via Open-Meteo.
- Active/upcoming weather and natural-hazard warnings through the MeteoSwiss
  postcode feed, with explicit feed availability. This includes flood (BAFU)
  and avalanche (SLF) warnings when supplied for the selected postcode; it is
  not a separate river-gauge or full avalanche-bulletin integration.
- Measured pollen, pollen forecasts and air quality.
- Complete German, English, French and Italian UI catalogues.

The integration domain remains `meteoswiss`. Existing config entries and the
IDs of retained entities/statistics are preserved. The obsolete forecast-only
season-HGT entity is intentionally retired; review that exception in the
[migration guide](docs/WECHSEL_DE.md). Warning automations should use numeric `warn_type`
and `warn_level`, and must treat an unavailable source separately from no alert.

Warnings use the App v3 source and its [verified thirteen-family catalogue](docs/WARNING_CODES.md).
Before updating an existing installation, review warning filters: **0 is Wind,
4 is Slippery Roads**; wind/thunderstorm/rain uses `[0, 1, 2]`. Detailed messages
distinguish storm/heavy-rain/snowfall events. Thaw (6) is recognized if supplied.
Dashboard and automation migration is a separate deployment step.

## Installation and updates

An existing installation must first be checked for its source and installed
commit/version. Do not remove or recreate the integration/config entry.
Once a tested release is approved:

1. Back up Home Assistant and keep the recovery key. Existing users first follow
   the [migration and warning-consumer checks](docs/WECHSEL_DE.md).
2. In **HACS → menu → Custom repositories**, add
   `https://github.com/martins-netizen/ha-meteoswiss` as **Integration**.
3. Open Download/Redownload, expand **Need a different version?**, and explicitly
   select **8.2.0b1** in **Release**. Check the announced version before confirming
   the download, then restart Home Assistant. Older HACS versions may additionally
   require enabling beta visibility. Do not substitute a branch or commit.
   Do not keep two HACS repositories managing the same `meteoswiss` directory.
4. **New users only:** add **MeteoSwiss** under **Settings → Devices & services**.
   Choose **MeteoSwiss STAC API (Swiss Stations)** for measured station weather;
   enter the weather station and the four-digit warning postcode.
5. Check the HA home location for forecasts/AQ and independently select the
   measured pollen station in the integration's **Configure** options.

Existing users keep their existing HA entry; they do not add it a second time.
`development` is the maintained default branch and `main` is an upstream mirror.
Neither branch name is a release approval. API keys or terminal commands are
not needed for the normal released installation.

The optional [shared warning template](examples/button-card-warnings.yaml) uses
labels supplied by the integration. It can replace duplicated dashboard warning
dictionaries after a separate dashboard check; it is not installed automatically.

See [setup, all parameters, removal and troubleshooting](docs/USAGE.md).

## Development and operation

- [Next-release plan: location/POIs, Silver and Gold (German)](docs/NEXT_RELEASE_PLAN_DE.md)
- [Quality review of 17 October 2026](docs/REVIEW_2026-10-17.md)
- [Quality roadmap and measured gaps](docs/QUALITY_SCALE.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Maintenance, acceptance and releases](docs/MAINTENANCE.md)
- [HACS publication checklist and release-note outline](docs/PUBLISHING.md)
- [Branch policy](DEVELOPMENT.md)
- [Changes](CHANGELOG.md)

```sh
python -m pip install -r requirements_test.txt
python scripts/check_translations.py
python -m pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
```

`development` is the protected integration branch; `main` tracks upstream.
Use this fork's [issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
for ordinary problems and
[private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential security reports. Bug reports should
include the installed fork version/commit, HA version, relevant states and
redacted logs. Do not upload full private backups or credentials.
Existing development PRs remain the review record.
Provider outages must remain distinguishable from a valid empty/no-danger value.

