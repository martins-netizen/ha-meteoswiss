# Bronze/Silver follow-up — 22 October 2026

**Record version:** 1.3. **Scope:** unreleased development after stable 8.2.0.
The [dated original audit](QUALITY_AUDIT_2026-10-17.md) remains historical.
This document records individual improvements, not an official HA quality tier.

## Remove unused product placeholders

Review found no imports/callers of `camera.py`, `hydro.py`, `slf.py` or
`MeteoSwissRadarCamera` outside those files. Active platform forwarding lists
only sensor, weather and binary_sensor; `Platform.CAMERA` was already removed
in earlier history. No service, config flow or test registers these placeholders.
The camera never returned an image; hydro/SLF contained comments and a logger.

Remove all three files rather than shipping unused product promises or treating
old comments about unavailable APIs as current provider evidence. Keep the
existing shared App v3 flood/avalanche parser and all active platforms intact.
There is no config/registry/statistics migration and no interaction with a
separately installed radar integration. A new standalone river-gauge, radar or
bulletin product would need a separately verified source and product contract.

Repository import/reference searches, the complete supported-HA regression
suites and existing full-coverage gates verify the bounded removal. Do not add
placeholder tests, no-op imports, coverage exclusions or a lower threshold
merely to make a percentage increase. Exact candidate/CI evidence belongs to
the PR and its job summaries. Local suites pass 917 tests and 14 subtests on
both HA 2026.8.3 and 2026.10.2; CI retains HA 2026.8.3/2026.10.1.

## Explain every setup field in four languages

A separate config-flow follow-up adds field-level help to all ten actual field
occurrences across user/source, MeteoSwiss station, Open-Meteo coordinate and
Configure forms. DE/EN/FR/IT distinguish measured station weather, the independent
warning postcode, forecast/model-pollen/AQ/UV coordinates and the measured-pollen
station. Station entries keep using HA home coordinates for forecasts; Open-Meteo
entries keep their explicitly configured coordinates. No location is reassigned.

Replace the two hardcoded English source choices with a native translated
SelectSelector, retaining `meteoswiss`/`openmeteo` values and the existing default.
Remove the unused source label from Configure; source/location editing is still
not offered there. Keep polling defaults, custom intervals, options precedence,
validation/retry behaviour, saved entry data and entity/statistic identities.

Add canonical English `strings.json`, identical to translations/en.json. The
translation checker now rejects missing/extraneous field help and canonical
English drift, in addition to duplicate/unresolved/mismatched language keys
and manifest/version drift. All four catalogues contain 105 matching keys.
Twelve regressions failed against the earlier bundle and pass after the fix:
HA's actual translation loader serves setup/options help and source choices in
all four languages. Both HA 2026.8.3 and 2026.10.2 suites pass **929 tests and
14 subtests**, with **99.9031%** combined coverage and all **670 branches**.
The complete existing config-flow tests retain full line/branch coverage. A visual check of the new texts/selectors in the temporary HA
belongs to the next reviewed test package; no live walkthrough is claimed.

## Share entity metadata and distinguish version meanings

`entity.py` now provides small shared entity/coordinator bases: common
has_entity_name and default MeteoSwiss attribution, with source-specific
attribution retained by each family. The coordinator base adds no constructor,
update, availability or lifecycle hooks. HA's CoordinatorEntity remains in the
same delegation chain. Polling diagnostics use the non-coordinator base.

Only genuinely duplicated device dictionaries are centralized: weather plus
observations share their existing weather-device factory, while AQ plus modelled
pollen share their existing provider-device factory. Warning, measured-pollen,
calculated and shared-diagnostic groups keep their distinct device definitions.
No source/coordinator is merged, device is renamed, unique ID is changed or
entity is moved to another device. All nine family identity/metadata contracts
pass against the previous code and the refactor; existing real-Recorder,
reload/unload, availability and weather subscription tests remain in force.

The redacted diagnostic payload adds `integration_version` from the declared
component version. Existing config_entry.version/minor_version remain the config
format, not a release number. Loaded/unloaded-entry regressions demonstrate
this distinction, compare the component version with manifest.json, and retain
privacy checks. Version metadata now has a real diagnostic consumer rather than
a test-only import. It is not a commit/hash attestation: unpublished development
still declares 8.2.0 until a separately reviewed release package is prepared.
The actual HA download-route/usability review remains a separate Gold check.

Local HA 2026.8.3 and 2026.10.2 suites pass **940 tests and 14 subtests**,
**99.9677%** combined coverage and all **670 branches**. All modules now exceed
95%: const.py remains 98.51%, every other module is 100%, including entity.py
and version.py. CI enforces **above 95% for every module**, while keeping the
existing stricter flow/source gates and 99% aggregate floor. Isolated negative gate checks
reject a synthetic 95%/94.9% module despite a high aggregate. No module
or error-branch exclusions are added. This evidences the coverage rule, not the
complete Bronze/Silver assessment.

## Migrate installed polling choices and simplify Configure

New entries use **600 seconds** for observation polling without asking the user
for an interval. Remove that field, its help and its label from setup/Configure
in all four catalogues; keep canonical English synchronized (**101 keys each**).
Configure now explains its one purpose: selecting the measured-pollen station.
Source/location selections, source validation, independent refresh schedules,
minimum-interval guards and warning behaviour stay unchanged.

Schema **1.2** moves a legacy `update_interval` from data into options, keeping an
existing options value in preference to data. Missing intervals remain absent
and use the 600-second default. Copy both dictionaries through HA's update API;
retain unknown keys, pollen choice and all non-polling data. Reject unsupported
major schemas without writes; leave current/future minor schemas unchanged.
The migration is idempotent and needs no network or registry/statistics writes.
Stable **8.2.0** already reads the options value first, so migrated entries remain
readable when returning to it. Its older Configure UI can still change that
option; upgrading again retains the option value. No downgrade walkthrough on
live HA is claimed.

The new options flow merges its supported pollen field into existing options.
It cannot discard the hidden legacy interval or other stored options when the
user changes stations. Existing-entry polling is a deliberate compatibility
bridge, not a new polling field or an unqualified exemption from the current
[appropriate-polling rule](https://contributors.home-assistant.io/core/quality-scale/appropriate-polling/).
Future standardization of installed custom intervals needs a separate migration
and review; the default and source-specific schedules remain documented.

Fourteen new regressions fail against the preceding tree and pass after the
change. They cover both providers, absent/data/options/conflicting intervals,
unchanged registry/entry identity, repeated migration, unsupported/future
schemas and hidden-field rejection. The actual HA setup/options/reload/unload
paths additionally verify migrated 1200-second and new 600-second operation,
pollen changes, retained extra options, registry IDs and Recorder listeners.
Local HA **2026.8.3/2026.10.2** suites pass **956 tests and 14 subtests**,
**99.96787664632187%** combined coverage and **676/676 branches**. Migration and
config flow retain **100% lines/branches**; every module remains above 95% and
all stricter gates pass. CI still uses HA **2026.8.3/2026.10.1**. These tests
mock source transport and do not establish a new live installation/acceptance.
Published-release setup instructions remain explicitly scoped to 8.2.0 alongside
a clear unreleased-flow note, avoiding an instruction to find a removed field.

## Remaining prerequisites and boundaries

- The version-module coverage gap is closed through its diagnostic consumer.
  Keep manifest/module consistency and all-module coverage checks; a percentage
  does not establish a complete integration-quality tier.
- Field help, translated source selection and the bounded polling/options
  migration are implemented. Final selector/UX and remaining provider/module
  contracts still need their own rule-specific review.
- Legacy intervals are retained through the explicit compatibility bridge; no
  existing 900/1200-second choice is silently replaced with 600 seconds.
- Shared entity metadata is now implemented and reviewed within this scope.
  Remaining source-specific coordinator placement, Core-brand evidence and the
  complete catalogue diagnostic availability contract remain separate findings.
- The official [coverage rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/)
  applies per module, not only to the aggregate. The
  [UI setup rule](https://contributors.home-assistant.io/core/quality-scale/config-flow/)
  also requires understandable fields and proper data/options separation.

Stable 8.2.0 and its tags stay intact. No HA change, restart, release or repeated
first-install/restore test follows from this source-only cleanup. Bundle any
later accepted runtime changes into a separately reviewed test package.
