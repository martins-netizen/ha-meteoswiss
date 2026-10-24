# Release readiness: current candidate and completed 8.2.0

**Document version:** 2.4 · **Updated:** 24 October 2026
**Purpose:** One entry point for completed evidence, remaining publication steps
and work deliberately deferred to later versions.

## Current next-feature release position


**Published b3 and focused operator evidence:** **8.3.0b3** was published on
24 October 2026 at **13:19:44 UTC / 15:19:44 Europe/Zurich**, release ID
**422744751**, at the reviewed #65 merge
**9d75aa8673c417f24caaa1f83181b5ef811d56fc**. The operator confirms successful
station changes; screenshots show Säntis/Bowil today/tomorrow forecasts with
values. Earlier installation/restore evidence remains valid.

**Station-condition follow-up:** the Altdorf weather row's `unknown` condition
is explained: a selected POI must not supply another station's condition.
Development now adds a small optional ICON code/daylight request at the actual
measurement station, with catalogue coordinates/height, separate validity and
failure handling, and unchanged numeric measurements/IDs. See the
[station-condition guide](STATION_WEATHER_CONDITION.md). This is new source after
published b3, not a change to that immutable tag. README station-proximity advice
and Cache Statistics help are included; the compact forecast row's icon/text
layout is explained without adding a redundant entity.

The follow-up passes **1,559 tests plus 53 subtests** on each local
**HA 2026.8.3/2026.10.3**, with **99.97753%** combined coverage and unchanged
strict gates/four exclusions. The 132 b1/b2/b3 publisher cases still pass with a
frozen historical 38-file fixture inventory; their published helpers are
unchanged and must not be reused for the new 39-file component. Current CI
remains HA 2026.8.3/2026.10.1. Direct live probing was unconfirmed because this
preparation host could not resolve the API hostname; this does not diagnose the
operator's provider connection or replace candidate-specific HA acceptance.

Next: regular review/merge and exact post-merge checks for the follow-up, then
an explicitly announced follow-up test package with updated source/version and
publication guards. Check station-local model condition, retained measurements,
and an independent forecast point in the existing temporary HA before stable
8.3.0 promotion. No repeat clean install/restore or blanket 24-hour wait is
required. The separately reported UTM restart problem has no diagnosed cause;
do not attribute or dismiss it on the basis of these automated tests.

**Earlier b3 packaging record:** the following source boundary describes the
already published b3; it is retained as history, not an instruction to publish
or install b3 again.

**Prepared 8.3.0b3 package:** PR #63 was approved and regularly squash-merged
as **97338f68038eab80c75c2028c9deb5e24ad552e6**, preserving reviewed tree
**22a20a95027c9aa45b108033908062fc8c1422c5**. The new package changes only the
two component version fields relative to that source, and adds the guarded
V1.2 publisher plus [release notes](RELEASE_8.3.0b3.md) and
[acceptance checklist](ACCEPTANCE_8.3.0b3.md). B3 publication and its live HA checks
remain separate; existing beta/stable tags are preserved.

**Correction review after published b2:** the operator confirmed the
separate Säntis/Kloten device groups and otherwise reports the beta working on
HA **2026.10.3**. Three tomorrow values remained unknown for the 25 October
clock-change day, and the gear exposed only pollen. The
[calendar-day and unified-settings corrections](CALENDAR_AND_LOCATION_SETTINGS.md)
address both findings. They are a new source change requiring their own review,
new announced package and focused HA checks; b2 publication and the earlier
successful installation do not establish their acceptance. No stable promotion
or additional HACS catalogue inclusion is claimed.


The operator confirmed the HACS update to stable **8.2.0** on 22 October.
Completed source switch, clean install, restore and Beta2 setup are retained;
no repeat is required merely for the next feature packet. The old publication
sequence below remains historical evidence for 8.2.0.

The agreed next scope includes the architecture boundaries (PRs #54/#55),
forecast scalars (#53), official catalogue (#56), saved-location/height-aware
ICON routing (#57) and translated postcode/town/POI setup/reconfiguration.
PR #58's dialogs and the [overall review](RELEASE_REVIEW_2026-10-24.md)
corrections are integrated. PR #59 was approved and regularly squash-merged at
**4c8169206fdcb8688a438c16a93f867a633a344f**. Its independently verified tree
matches the approved 5686a7b source tree, and all eight PR/seven post-merge
checks passed. The agreed runtime scope is frozen at that source.

PR #60 was approved and regularly merged at
**a6b9df9f57dec3e93c8f698133cdb0e7e4c3e937**, tree
**187f3d3e8a847b934786d3b80f7df3a8cd14a3ab**, with eight PR and seven
post-merge checks successful. **8.3.0b1 was published on 24 October 2026 at
06:26 UTC / 08:26 Europe/Zurich**, prerelease ID **422558946**. The operator's
publisher JSON/log and independent GitHub reads confirm its exact tag/notes
and unchanged latest stable **8.2.0 / ID 420392277**. The original publisher,
[notes](RELEASE_8.3.0b1.md) and [baseline protocol](ACCEPTANCE_8.3.0b1.md)
remain unchanged; do not repeat that successful publication.

The operator reports a positive initial view with tomorrow's native daily
values unknown around the 25 October clock change, consistent with the known
fixed-offset/25-hour limitation. Säntis station/POI choices and selection were
also confirmed. The resulting screenshot exposed a new acceptance finding:
Säntis forecasts were displayed under the Kloten device/combined weather name.

PR #61 is approved and regularly merged as **781ba3a41fafc2e8dd5bc5f867f55c646c4a2412**,
with tree **1d956269953b0bea18fb70b042471f01ab584743** matching the approved
head. Eight PR and seven post-merge checks passed. The source/runtime scope is
frozen there for **8.3.0b2**: separate forecast device, eight scalars/HGT and
forecast-only weather entity, preserving IDs and documenting card/action targets.

**Prepared b2 package:** two component version fields, English
[notes](RELEASE_8.3.0b2.md), [focused protocol](ACCEPTANCE_8.3.0b2.md) and
[Publisher V1.1](../scripts/publish_meteoswiss_830_beta_v1.1.sh). Thirty-six other
component files, HACS metadata and workflows are identical to the #61 merge.
V1.1 derives from the successful b1 publisher and checks that b1's tag and
latest stable 8.2.0 remain unchanged. This is not a published b2 or completed
HA acceptance. Packaging PR review/merge, exact post-merge checks and approved
prerelease publication are next.

The display source's retained local evidence is 1,352 tests/53 subtests on
HA 2026.8.3/2026.10.2, including twelve display/registry cases and 99.97545%
combined coverage (3,197/3,198 lines; 876/876 branches). The b2 package passes **1,395 tests plus 53 subtests** in each environment,
including **88 shared publisher-profile cases**. Full regressions and both
historical/follow-up guard profiles run independently of root version, without
lowering any gate. Four complete 143-key catalogues and all prior runtime
exclusions remain. CI remains HA 2026.8.3 / 2026.10.1.

After that candidate is installed, verify the changed display/card target and
complete remaining point/pass/hut/language/new-entry checks. Keep the existing
entry and completed 8.2.0 clean-install/restore/update evidence. Do not restart a
blanket 24-hour period or equate publication with practical candidate acceptance.
Local 8.3.0b1 package evidence remains historical: 1,340 tests/53 subtests on
HA 2026.8.3/2026.10.2 and 99.97506% combined coverage. The display follow-up has
its own regression results and must preserve the existing strict gates.
CI still tests HA 2026.8.3 and 2026.10.1; no official quality tier is claimed.

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
