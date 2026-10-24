# 8.3.0 — forecast locations and independent station conditions

**Release notes version:** 1.0 · **Prepared:** 24 October 2026

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product. Install a published release through HACS; a version in a branch is
not proof of publication.

## What changes from 8.2.0

- **Forecasts for a chosen place:** search the official catalogue by Swiss
  postcode, town or POI, inspect the category/height and confirm the intended
  point. Four-language dialogs preserve provider place names; full multilingual
  name aliases are not supplied. The selected point's altitude is used for ICON.
- **Four clear location roles:** HA home/base coordinates supply modelled air
  quality, modelled pollen and optional UV; measured pollen and weather use
  independently selected stations; the forecast may use a separate town/POI.
  Warnings keep their independent postcode. A mountain forecast does not move it.
- **Separate, named forecast display:** an explicit point has its own device
  and weather entity, eight today/tomorrow sensors and calculated HGT. Existing
  IDs and personal names remain. Existing forecast cards/actions may need
  [one explicit target change](FORECAST_DISPLAY.md#update-an-existing-card-or-forecast-action-once).
- **Complete calendar days:** daily values cover Swiss days, including 23-/25-hour
  summer/winter clock changes. Incomplete metrics remain unknown; real zero is
  retained. Maximum hourly rain probability includes its corresponding times.
- **One settings dialog:** Configure edits weather station/base coordinates,
  measured-pollen station, forecast location and warning postcode together,
  with atomic confirmation/cancellation. New observations use 600 seconds;
  existing individual intervals remain, without a polling field.
- **A condition at the measuring station:** the station weather row uses a small
  independent MeteoSwiss ICON Seamless current-code request through Open-Meteo
  at the station's official coordinates/height. This qualitative condition is
  modelled; temperature, humidity, wind and other observations remain measured.
  A missing condition affects no measured quantity and never borrows a POI value.
- **Reviewed internal boundaries:** source clients are separated from eight real
  canonical HA coordinators. Bounded HTTP handling, catalogue availability,
  independent UV failure/recovery, metadata, diagnostics and lifecycle coverage
  accompany the user-facing changes. Source selection and App v3 warnings stay.

## Install or update

New users follow [getting started](GETTING_STARTED.md). Existing users follow
[migration](MIGRATION.md), keep the existing HA entry and backup, and use exactly
one HACS repository for `meteoswiss`. Refresh repository information if needed,
then actually download the announced **8.3.0** and restart HA once. Refresh alone
does not install files. No API key, terminal command or additional weather card
is needed for the normal HACS installation.

Older upstream/manual users must review the documented retired rain/seasonal-HGT
entities and warning consumers: **Wind is 0; Slippery Roads is 4**. A software
update does not rewrite dashboards or automations. Users who already completed
those migrations should not repeat them merely because a new version is offered.

## Accepted runtime and validation

The operator reported successful overall operation after the requested b4 check and
requested stable publication. Screenshots show **8.3.0b4**, distinct measuring
station and forecast devices with weather symbols, measured values and known
today/tomorrow forecasts. The observed installation has seven devices and
45 entities; this is not a fixed count promised for every configuration.
The screenshots do not expose all condition attributes or independently prove
registry identity. Earlier operator-confirmed location switches, calendar-day
values, first-install/restore and source-switch evidence are retained.

Stable component code is identical to published b4 at
**a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5**: **37 non-version files** match;
only manifest.json/version.py become **8.3.0**. HACS/CH, workflows, all languages
and the seven prior tags remain unchanged. No new runtime feature is added in
the stable package and no additional blanket 24-hour wait is needed.

B4 passed **1,603 tests plus 53 subtests** on each local HA 2026.8.3 and
2026.10.3 / Python 3.14.8. Combined line/branch coverage is **99.97753%**,
3,474/3,475 statements and 976/976 branches, with all strict gates and four
existing exclusions retained. Stable packaging adds publisher/latest-release
regressions; [readiness](RELEASE_READINESS.md) records its exact results and
distinguishes local tests from CI's 2026.8.3/2026.10.1 matrix. CodeQL, SonarCloud,
hassfest and HACS checks must pass for the actual PR and merge commit.

The guarded **veroeffentliche_meteoswiss_stable_v1.3.sh** continues the successful
stable/b4 route. It verifies exact code, versions, checks, notes, accepted b4
publication, previous stable and seven preserved tags before creating only
**8.3.0**, `draft=false`, `prerelease=false`, `make_latest=true`. It verifies the
new latest stable afterwards. A matching repeat is read-only; conflicting tags,
notes or releases stop instead of being overwritten. Publication makes no HA
connection, installation, restart or device call. The [stable update check](ACCEPTANCE_8.3.0.md)
remains separate from GitHub publication.

## Known limits and later work

Provider gaps, optional-source failures and missing station quantities remain
possible; no guessed weather or automatic substitute pollen station fills them.
Keep official warning channels available. Forecasts are predictions; station
history continues across deliberate selection changes. Town/POI aliases in other
languages, separate hydrology/SLF products and complete Gold work remain later
scope. The App warning source remains in use.

The separately reported UTM restart issue has no diagnosed cause. Automated
unload/session tests and successful later operation do not establish that cause.
This release is not HACS default-catalogue inclusion or an officially awarded
Bronze/Silver/Gold tier. See [quality evidence](QUALITY_SCALE.md),
[review](RELEASE_REVIEW_2026-10-24.md) and [source details](STATION_WEATHER_CONDITION.md).

For problems use the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues),
or [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports. [Recovery](MIGRATION.md#if-something-fails) restores
matched software/settings/consumer changes; downgrading code alone does not
restore deliberately changed locations. No dashboard is automatically rewritten.
