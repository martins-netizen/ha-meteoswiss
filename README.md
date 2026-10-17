# MeteoSwiss for Home Assistant — maintained fork

This is the maintained fork of [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss).
It combines reviewed corrections for continued use while upstream PRs remain
pending. It is not an official MeteoSwiss product. The upstream MIT licence
and attribution are retained.

**Prepared version: 8.2.0b1. No new release or HA deployment is performed by this PR.**
Minimum tested HA: **2026.8.3**; current test target: **2026.10.1**.

## Data and compatibility

- SwissMetNet observations and hourly precipitation statistics.
- MeteoSwiss ICON Seamless forecasts via Open-Meteo.
- Active/upcoming MeteoSwiss weather warnings with explicit feed availability.
- Measured pollen, pollen forecasts and air quality.
- Complete German, English, French and Italian UI catalogues.

The integration domain remains `meteoswiss`. Existing entity, config entry and
statistic IDs are preserved. Warning automations should use numeric `warn_type`
and `warn_level`, and must treat an unavailable source separately from no alert.

Warnings use the App v3 source and its [verified thirteen-family catalogue](docs/WARNING_CODES.md).
Before updating an existing installation, review warning filters: **0 is Wind,
4 is Slippery Roads**; wind/thunderstorm/rain uses `[0, 1, 2]`. Detailed messages
distinguish storm/heavy-rain/snowfall events. Thaw (6) is recognized if supplied.
Dashboard and automation migration is a separate deployment step.

## Installation and updates

An existing installation must first be checked for its source and installed
commit/version. Do not remove or recreate the integration/config entry.
After an approved tested prerelease is published, use the HACS custom repository
`https://github.com/martins-netizen/ha-meteoswiss`, category **Integration**, and
select that tested release. `main` is an upstream mirror and does not contain
all local corrections. Until a release is approved, retain the known working
installation rather than installing an unreviewed development snapshot.

The optional [shared warning template](examples/button-card-warnings.yaml) uses
labels supplied by the integration. It can replace duplicated dashboard warning
dictionaries after a separate dashboard check; it is not installed automatically.

See [setup, all parameters, removal and troubleshooting](docs/USAGE.md).

## Development and operation

- [Quality roadmap and measured gaps](docs/QUALITY_SCALE.md)
- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Maintenance, acceptance and releases](docs/MAINTENANCE.md)
- [Branch policy](DEVELOPMENT.md)
- [Changes](CHANGELOG.md)

```sh
python -m pip install -r requirements_test.txt
python scripts/check_translations.py
python -m pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
```

`development` is the protected integration branch; `main` tracks upstream.
Fork-specific support must be enabled before public release; repository Issues
are currently disabled. Existing development PRs remain the review record.
Provider outages must remain distinguishable from a valid empty/no-danger value.
