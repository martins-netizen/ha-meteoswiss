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

## Development and operation

- [Architecture and data contracts](docs/ARCHITECTURE.md)
- [Maintenance, acceptance and releases](docs/MAINTENANCE.md)
- [Branch policy](DEVELOPMENT.md)
- [Changes](CHANGELOG.md)

```sh
python -m pip install -r requirements_test.txt
python scripts/check_translations.py
python -m pytest -q
```

`development` is the protected integration branch; `main` tracks upstream.
Report fork-specific problems in [this repository](https://github.com/martins-netizen/ha-meteoswiss/issues).
Provider outages must remain distinguishable from a valid empty/no-danger value.
