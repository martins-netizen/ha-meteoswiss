# Release readiness: current candidate and completed 8.2.0

**Document version:** 1.8 · **Updated:** 24 October 2026
**Purpose:** One entry point for completed evidence, remaining publication steps
and work deliberately deferred to later versions.

## Current next-feature release position

The operator confirmed the HACS update to stable **8.2.0** on 22 October.
Completed source switch, clean install, restore and Beta2 setup are retained;
no repeat is required merely for the next feature packet. The old publication
sequence below remains historical evidence for 8.2.0.

The agreed next scope includes the architecture boundaries (PRs #54/#55),
forecast scalars (#53), official catalogue (#56), saved-location/height-aware
ICON routing (#57) and translated postcode/town/POI setup/reconfiguration.
PR #58's dialog package was approved and regularly merged at **5bed187**;
its tree and all seven post-merge checks are confirmed. The
[overall review](RELEASE_REVIEW_2026-10-24.md) adds four regression-backed
corrections plus reconciled source/install/quality documentation. Review and
merge that correction PR before freezing the exact **8.3.0b1** packet.

Then prepare matching versions, release notes and a candidate-specific guarded
publisher; the historical 8.2.0 helpers cannot publish 8.3.0b1. Pass exact PR and
post-merge checks, publish only the approved prerelease, and perform the
[focused postcode/town/POI and existing-entry checks](FORECAST_LOCATION_SETUP.md#focused-candidate-checks-in-the-existing-temporary-ha)
in the existing temporary HA. Check missing daily values/UV, source roles,
retained IDs and reset/cancel/keep. Do not reopen completed 8.2.0 installation,
restore or require a new blanket 24-hour wait.

A reviewed implementation is not candidate acceptance, stable publication,
HACS default-list inclusion or a complete Silver/Gold assessment.

## Completed evidence

| Evidence | Confirmed state |
|---|---|
| First public beta | `8.2.0b1`, published 20 October 2026 at 17:56:24 Europe/Zurich; immutable tag `abbb6b7701134ac2573f35b425ab3f0697a80540`. |
| Runtime acceptance | HA 2026.10.2, accepted runtime `0086b956d44b7144b242c5d5c1881d0b0650e524`; its technical 24-hour and visual acceptance are complete. Beta1's 33 component/translation/brand files match it. |
| HACS source switch | Operator-confirmed on 20 October: HACS 2.0.5, this fork, downloaded 8.2.0b1, restart and positive initial visual check. |
| Clean first installation | Operator-confirmed on 21 October in temporary HA 2026.10.2 / HACS 2.0.5: Beta1 STAC entry, 600 seconds, KLO, warning postcode 8302, immediate observations. |
| Isolated restore and pollen comparison | Operator confirmed restoration from 900 to saved 600 seconds, then chose a pollen station and reported matching production measurements. No independent restored-file/registry comparison is inferred. |
| Pollen catalogue | 15 official station identities and hourly assets verified on 21 October. Valid stations remain selectable during source gaps. Unsupported BLR was removed in Beta2. See [dated evidence](POLLEN_STATIONS.md). |
| Second public beta | `8.2.0b2`, published 22 October at 07:12:40 Europe/Zurich; immutable tag `80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8`. PR #37's setup changes and PR #38's packaging are integrated. |
| Beta2 tests | 836 passing tests and four subtests locally on each of HA 2026.8.3 and 2026.10.2; 99.05% combined coverage. Seven PR/six post-merge checks succeeded. CI's current-HA label remains 2026.10.1; local patch testing is separate evidence. |
| Stable candidate local tests | 859 tests and 14 subtests pass on each of HA 2026.8.3 and 2026.10.2; 99.0535% combined coverage, all 652 branches covered and existing module/flow gates retained. Four catalogues have 96 keys each. These local results do not replace candidate PR/post-merge checks. |
| First stable publication | **8.2.0** published 22 October at **08:52:40 Europe/Zurich**, immutable tag **5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5**, release ID 420392277, draft=false/prerelease=false. Receipt, independent tag and GitHub latest-stable endpoint agree. |
| Beta2 focused setup/data check | On 22 October the temporary UI showed b2 and existing 600 seconds/Zürich (PZH). The operator then completed new setup with other geographic locations and reported values. The practical new-entry test is complete; exact additional source paths/stations and every manual subcheck were not separately reported. |
| Warnings and source semantics | App v3 catalogue, bundled DE/EN/FR/IT, deployed warning consumers, retained identities and official rain statistics were checked during runtime acceptance. The isolated optional UV outage recovered at the next scheduled request. |

The [HACS acceptance record](HACS_ACCEPTANCE.md) distinguishes operator reports,
source/CI evidence and independent technical comparisons. Do not reopen the
completed source switch, clean install, restore or Beta2 walkthrough without a
concrete new failure. No new blanket 24-hour window is required for promotion
of identical component code.

## Completed stable publication and HACS update

**8.2.0 is published.** Publication is not a download or installation on HA.

| Order | Work | Completion criterion |
|---|---|---|
| 1 | Stable package review | Complete: only component versions differ from Beta2; HACS/workflows and both beta tags are unchanged. See [bounded review](RELEASE_REVIEW_2026-10-22.md). |
| 2 | Exact checks and merge | Complete: PR #39, seven successful PR checks, regular protected squash merge 5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5 and six successful post-merge checks. |
| 3 | Stable publication | Complete: guarded publisher V1.2 run 20261022-085229-238 reports published_and_verified; independent release/latest/tag reads confirm the exact approved commit. No HA write, restart or device call. |
| 4 | Local HACS visibility/update | Refresh information for this fork; confirm Release 8.2.0 is offered. The operator may then back up, download and restart the intended instance, retaining its HA entry. Operator-confirmed on 22 October after refreshing repository information; no new independent file/ID comparison or repeated clean install/restore is inferred. |

The component version/module both read 8.2.0. The other 31 component files
and HACS manifest match Beta2 exactly. No new functionality or dependency is
introduced. Existing production entries remain in place; a version-only change
does not require a repeated clean installation or restore.

The operator's completed walkthrough is not an independent nontechnical-user
study. Additional manual source combinations, a separate pollen-station-change
check, practical branch-hiding confirmation and a new read-only production
file/identity/statistics comparison are not claimed. They are supplementary
checks, not a demand to repeat the completed general setup test. Both setup
paths and pollen persistence/change behaviour have automated coverage.

## Security and quality follow-ups

The [22 October bounded review](RELEASE_REVIEW_2026-10-22.md) reassesses the
known source-destination/redirect/body-size gaps for this unchanged-runtime
promotion. It does not demonstrate a concrete exploit or claim zero
vulnerabilities. The separate [HTTP follow-up](HTTP_SOURCE_HARDENING.md) is now
in unreleased development and needs focused HA acceptance before release.
The [CodeQL follow-up](CODEQL_FORK_REVIEW.md) removes the foreign-fork skip on
development; the first actual external run still needs its own evidence.

The interval/field, seven-coordinator layout, unused-placeholder, UV/catalogue
and per-module coverage findings are now implemented in development. The
[current rule matrix](QUALITY_SCALE.md) records evidence and the separate
external Core-brand boundary. High aggregate coverage, HACS validation and
successful operation do not themselves establish a complete tier.
Independent beginner usability review remains separate. Neither it nor complete
Silver/Gold work is a reason to invent repeated acceptance windows for the
same release code.

## Later development

- **Location/POI selection and local forecasts:** the official OGD point
  catalogue is prioritised; selection and adopting processed forecasts are
  distinct decisions. [PR #35](https://github.com/martins-netizen/ha-meteoswiss/pull/35)
  is integrated through the planning/implementation PRs and remains separate
  from the immutable 8.2.0 package.
- **Warnings:** retain the MeteoSwiss App v3 source until further notice.
- **Silver, then Gold:** rule-by-rule evidence, without an official tier claim.
- **HACS default catalogue:** separate submission under its then-current rules;
  a custom-repository stable release is not catalogue approval.

## References

- [Stable release notes](RELEASE_8.2.0.md)
- [Publication procedure](PUBLISHING.md)
- [HACS acceptance](HACS_ACCEPTANCE.md)
- [Published Beta2 notes](RELEASE_8.2.0b2.md)
- [Quality matrix](QUALITY_SCALE.md)
