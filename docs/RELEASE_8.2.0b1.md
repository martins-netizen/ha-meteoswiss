# 8.2.0b1 — first maintained-fork prerelease

**Release-note source for the first maintained-fork beta.**
Availability is determined by an explicitly published prerelease on the
[fork Releases page](https://github.com/martins-netizen/ha-meteoswiss/releases).

This community fork builds on LNKtwo/ha-meteoswiss, retaining the MIT licence
and attribution. It is not an official MeteoSwiss product. Several earlier
contributions have also been accepted upstream in v8.1.2; compare the actual
installed version rather than assuming every capability is unique to this fork.

## What this beta contains

- Swiss station observations, official hourly rain statistics and native
  MeteoSwiss ICON Seamless forecasts through Open-Meteo.
- Source freshness, bounded retries, explicit missing-value/failure handling
  and setup/reload/unload cleanup.
- App v3 warnings with the verified thirteen-family catalogue and bundled
  German, English, French and Italian labels. Provider event text, severity
  and validity remain intact; a failed warning feed is not an all-clear.
- Measured pollen (including oak), forecast pollen, air quality and isolated
  optional UV availability. Pollen belongs under Sensors on device pages.
- Clear 10-minute precipitation naming and measurement-end timestamps.
- German first-install and migration guides, diagnostics and private
  vulnerability reporting.

## Before updating an existing installation

Keep the existing Home Assistant integration entry. Back up first and follow
[the migration guide](WECHSEL_DE.md), including its warning-consumer checks.

- Wind is type **0**; type **4** is Slippery Roads. Review active, upcoming and
  lead-time filters. Frost is family 5; retain the provider's concrete text.
- The forecast-only seasonal heating-degree entity and locally derived
  current-hour precipitation entity are intentionally retired. Update their
  consumers before installation.
- IDs and settings of retained entities and official hourly statistics remain.
  Recorder is not purged. Independent user-created helpers are not deleted.
- Existing local code/translation patches and HACS software-source ownership
  must be checked before replacing files. Do not keep two repositories managing
  the same `meteoswiss` directory.

## Verification and scope

The accepted runtime is
`0086b956d44b7144b242c5d5c1881d0b0650e524`.
Both manifest and module version are `8.2.0b1`. Minimum HA is **2026.8.3**;
CI additionally covers **2026.10.1**, and local tests plus deployed acceptance
cover **2026.10.2**. The accepted runtime's local suite passed **786 tests** on each of
HA 2026.8.3/2026.10.2, with **99.051% combined line/branch coverage**.
The accepted commit's [six post-merge checks](https://github.com/martins-netizen/ha-meteoswiss/commit/0086b956d44b7144b242c5d5c1881d0b0650e524/checks)
include HACS validation, Hassfest and CodeQL.

The deployed candidate completed its own 24-hour observation on 20 October
2026. Code, retained registry/statistic identities, personal settings and
warning consumers matched the expected installation. Official hourly rain
statistics progressed without missing expected complete hours. One isolated
optional UV request failed; UV correctly became unavailable and recovered
on the next scheduled refresh while other checked data remained available.
Forecast pollen's device-page grouping is visually confirmed.

A documentation-only publication commit may follow this runtime commit.
Before tagging, compare every component file byte for byte and complete the
publication PR's checks. Tag the approved merged publication commit, not an
unmerged PR or an unrelated branch.

## Acceptance update — 20 October 2026

After publication, the operator confirmed the HACS 2.0.5 source switch to
`martins-netizen/ha-meteoswiss`, downloaded version `8.2.0b1`, restart and a
positive initial visual check. The [current HACS record](HACS_ABNAHME_DE.md)
distinguishes that operator-reported evidence from an independent technical
post-switch comparison. A clean first installation remains open. This update
applies to the development documentation; it does not modify the immutable
published beta, its tag or its release-time evidence.

See the [stable-release checklist (German)](FREIGABESTAND_DE.md) for the
remaining work and the features intentionally deferred beyond this release.

## Known limits of the first beta

- The runtime was initially deployed with a reviewed installer. The operator
  subsequently confirmed the HACS source switch and initial visual success.
  A clean first HACS install and an executed recovery rehearsal remain open;
  no new independent post-switch file/registry/statistic comparison is claimed.
- HACS custom-repository availability, default-store inclusion and the HA
  Integration Quality Scale are separate. No default-store listing or official
  Silver/Gold/Platinum tier is claimed.
- Forecasts remain model data and depend on their stated providers. A real
  zero differs from a missing value or unavailable source; external services
  can be delayed, incomplete or temporarily unavailable.
- Shared postcode warnings can include SLF/BAFU hazards when supplied; separate
  avalanche-bulletin, river-gauge and radar placeholder modules are inactive.
- POI selection and direct OGD pollen/local forecasts are later work, not
  features introduced by this beta.

Use the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
for ordinary problems and
[private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports. Include versions, affected values and redacted logs;
do not upload backups or credentials.

