# Maintained-fork roadmap

## Current engineering work

The **8.3.5b5** test package includes the approved #119 HGT retry correction.
Publication is verified and the operator confirmed measured HGT available on
b5. Existing entries, IDs and owned statistics remain; completed b3 cleanup
stays closed. The next bounded correction preserves HGT ownership when a station
changes/removes during a queued initial import. It adds native Recorder race
regressions and remains unreleased; see [the failure and cleanup boundary](docs/HGT_PENDING_IMPORT_OWNERSHIP.md).
Full Gold and independent privacy/security/architecture assurance remain separate.

This describes current fork work. Historical upstream release claims remain in
the changelog as history; they are not current certifications. Check the
[release status](README.md#release-status) before installing.

## Published 8.3.5b4: measured HGT, availability accepted on b5

[8.3.5b4](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b4),
release **446375287**, was published on **15 November 2026 at 21:20:21 UTC**
(22:20:21 CET) from regular packaging [PR #116](https://github.com/martins-netizen/ha-meteoswiss/pull/116),
merge `a6a233513ac8e7c5937f9c41eee085e76108e801`, tree
`010be578bb121fcad058c1bc8c1fcfccb6761ebf`, parent
`29d9bc73b2ad0dedc91c73cf167f46223330d22a`.

Ten exact-head checks and all nine actual merge checks passed. The actual
[CI 43761426012](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43761426012),
CodeQL 43761426015 and HACS 43761426023 push runs succeeded on that merge.
Both HA 2026.11.0/2026.11.1 jobs passed **3,092 tests plus 83 subtests**, five
known upstream warnings and no SQLite ResourceWarning. Strict line/branch gates
passed at **99.9831%** combined coverage; all four HGT OGD modules retain full
line/branch coverage. Pinned Hassfest reported zero invalid integrations; both
universal locks verified 138 selections and the audit of 140 package/version
pairs found zero active/unknown advisories. SonarCloud passed.

The release/tag and exact approved English body were independently read back.
All nineteen older complete release records, bodies and tag references are
unchanged. **8.3.4 remains latest stable.** The 50 non-version component files
out of 52 match reviewed PR #115 source. This publication does not install or
restart HA. Its original [measured-HGT protocol](docs/ACCEPTANCE_8.3.5b4.md) is
retained. For the retry correction choose published b5 and its
[focused recovery check](docs/ACCEPTANCE_8.3.5b5.md); no prior b4 installation
or repeated cleanup is required. Accepted b1/b2/b3 scopes and PR #114 stay closed.

Publication is complete. Do not rerun a publisher as a new update action.
Choose the current published recovery test package through the release
catalogue. Keep the entry and station; completed cleanup stays complete.
Full Gold, independent review and any stable promotion remain separate.

## Earlier 8.3.5b3: focused HGT cleanup accepted

[8.3.5b3](docs/RELEASE_EVIDENCE_8.3.5b3.md) was published from regular PR #113
at `b6c4502e5cdeb48121be628fdb7eda579df4f7c3` on 15 November. Ten head and
nine actual merge checks passed, all eighteen prior releases/tags are unchanged,
and stable 8.3.4 stays latest. The operator confirmed the existing-entry update
and focused native HGT cleanup successful; do not reopen those completed steps.
The [upgrade guide](docs/UPGRADING_8.3.5.md) retains consent/ownership boundaries.

The [test Recorder lifecycle](docs/TEST_RECORDER_LIFECYCLE.md) follow-up was
regularly merged as PR #114 at `3f58d8ac9d60e792a2b01b9ced73e7bd39d0f192`.
Ten head and nine actual merge checks passed; both actual HA jobs passed
2,901 tests plus 83 subtests without SQLite ResourceWarning. That test-only
change requires no production update.

Official measured-HGT source PR #115 and packaging PR #116 are complete.
The published b4 package and remaining focused check are recorded above.
Earlier b1/b2/b3 acceptance and PR #114 stay closed.

## Published stable 8.3.4: clearer setup and verified HA 2026.11 support

[Stable 8.3.4](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4),
release **437853341**, was published on **7 November 2026 at 21:24:27 UTC** from
regular packaging PR #93 at **f4479897023fa35d7c2fcb4c4859c4de8861fdda**.
Release/tag/English notes and selection as latest stable are independently
confirmed; all fifteen older tags remain unchanged. See the
[publication evidence](docs/RELEASE_EVIDENCE_8.3.4.md).

This maintenance and quality release retains the accepted 8.3.4b1 runtime:
39 non-version component files match; only two version fields change. Its
benefits over 8.3.3 are the official-package HA 2026.11 compatibility baseline,
a cleaner initial sensor list and explicit source/service provenance.
Existing personal choices and weather behaviour are retained.

The HGT statistics change in [PR #92](https://github.com/martins-netizen/ha-meteoswiss/pull/92)
is reserved for a later version. Full Gold is separate. Packaging merge,
successful actual checks and publication are complete; the
[short actual stable update](docs/ACCEPTANCE_8.3.4.md) is a distinct user action.
Earlier beta and installation acceptance remain closed within their scopes.

## Stable 8.3.3 published and accepted

[Stable 8.3.3](docs/RELEASE_8.3.3.md), ID **429354633**, was published on
**30 October 2026 at 18:21:55 UTC** from
**3d4fad2330c89f134eba208e8b2db55705177e7d**. It was latest until stable
8.3.4 on 7 November and remains an immutable previous release.
The [release evidence](docs/RELEASE_EVIDENCE_8.3.3.md) confirms the exact
source/immutable notes, all seven actual merge checks and thirteen retained
old tags. On **30 October**, the operator confirmed **8.3.3 installed and normal
operation OK**. The [short stable update](docs/ACCEPTANCE_8.3.3.md) is complete.

It retains all 39 non-version component files of accepted beta 8.3.3b1:
native icons, personal overrides and 19 translated source-error categories.
Only two version files change. The beta icon check on **Core 2026.10.4 /
HA OS 18.4** remains separate evidence from the later stable version/operation
report. Shared settings, first-install and restore acceptance stay closed.

## Published 8.3.4b1 test package; short operation check complete

[8.3.4b1](docs/RELEASE_8.3.4b1.md) packages the regularly merged diagnostic-default
and provider-metadata changes from #88/#89. Its 39 non-version component files
match reviewed merge `5a7eae00963d47294281da8812cb1ede35713b7f`; only two version
files change. Packaging PR #90 was regularly merged at
`1e5c5d1a7fc1c18d520e99189ae4dd5894621706`, with all seven actual merge
checks successful. The fixed V1.7 publisher created release **437718127** on
**7 November 2026 at 17:12:54 UTC**, retaining all fourteen older tags and
then-latest stable 8.3.3. The operator subsequently confirmed normal operation
on **HA Core 2026.11.0 / HA OS 18.4**, completing the agreed
[short check](docs/ACCEPTANCE_8.3.4b1.md). See the
[bounded evidence](docs/RELEASE_EVIDENCE_8.3.4b1.md). This completed beta check
is retained as provenance; the separate stable publication is recorded above.

## 8.3.5b2: automatic HGT archive default

The accepted [PR #110](https://github.com/martins-netizen/ha-meteoswiss/pull/110)
runtime is packaged in [8.3.5b2](docs/RELEASE_8.3.5b2.md), retaining all 44
non-version component files. The [recommended update](docs/UPGRADING_8.3.5.md)
archives compatible old HGT statistics and clears the resolved native Repair.
Regular package PR/checks/publication precede the
[focused operator acceptance](docs/ACCEPTANCE_8.3.5b2.md). Earlier b1 scopes
stay accepted; stable 8.3.4 and remaining Gold/independent review stay separate.

## Remaining Gold and provider-evidence work

The [complete test-lock advisory gate](docs/DEPENDENCY_ADVISORIES.md), shipped in
test prerelease 8.3.5b1,
adds the recurring vulnerability check identified by the security review.
Every selected package/version across both universal locks is checked; active
advisories and unknown results block the required `tests` aggregate. Daily/manual
checks use identical read-only steps. PR #107's exact head and actual merge
checks passed; manual audit run 43389137603 also passed on the reviewed source.
An actual cron execution, independent review and full Gold remain separate.

The published [8.3.5b1 test version](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b1)
packages the merged follow-ups below, retaining all 42 non-version component
files. [Publication evidence](docs/RELEASE_EVIDENCE_8.3.5b1.md) records the approved
regular merge, successful packaging checks and verified prerelease. Stable
8.3.4 remains latest. Operator installation, normal operation and a bounded
read-only wind/HGT check are recorded in the
[focused acceptance plan](docs/ACCEPTANCE_8.3.5b1.md). The HGT state-class Repair
remains an open migration issue in b1. The published
[b2 archive default](docs/RELEASE_8.3.5b2.md) preserves that old series and
uses native Core repair recomputation; it needs a later fixed test package and
operator acceptance before stable promotion. Packaging itself introduced no
additional runtime capability.

The [diagnostic-defaults and service-metadata change](docs/DIAGNOSTIC_DEFAULTS.md), delivered in stable 8.3.4 after first shipping in 8.3.4b1,
adds first-registration diagnostic defaults and explicit virtual service groups,
with registry-preservation tests. Earlier stable 8.3.3 did not include this change.

The [provider-metadata follow-up](docs/PROVIDER_METADATA.md), delivered in stable 8.3.4 after first shipping in 8.3.4b1, corrects
Open-Meteo current-weather labels and attribution while keeping group identity
and personal choices. Native pollen-station round trips reuse all seven groups;
no cleanup is needed for those tested changes. Historical orphaned groups have
not been independently inventoried and are not deleted by this change.

The [Foehn/HGT metadata review](docs/SENSOR_METADATA.md), shipped in 8.3.5b1, retains their
numeric contracts without inventing device classes. It corrects the HGT
forecast's measurement state class, keeping old statistics and ordinary history
while stopping new forecast measurement statistics. Native Recorder tests cover
the boundary and registry preservation.

The [applicability review](docs/GOLD_APPLICABILITY.md) records two reasoned
discovery exemptions for this public weather service. Its seven virtual groups
do not fit the official single-device exception; dynamic-device and historical
stale-device assessments remain partial, with their evidence limits explicit.

The published b1 [wind-statistics follow-up](docs/WIND_STATISTICS_MIGRATION.md)
preserves existing arithmetic rows under an archive ID before enabling circular
statistics on the retained sensor. Release/operator acceptance remain open.
The published b1 [diagnostic-name follow-up](docs/DIAGNOSTIC_TRANSLATIONS.md)
translates both optional helper entities and their shared service groups while
preserving IDs and personal registry choices. Technical state/attribute strings
retain their compatibility contracts. The published b1
[service-group naming follow-up](docs/SERVICE_GROUP_TRANSLATIONS.md) covers the
remaining fixed group labels through native DE/EN/FR/IT device keys, retaining
English defaults, provider/station text, IDs and personal choices. It adds
native language-round-trip, diagnostics-redaction and Recorder evidence;
technical strings, authoritative place aliases and operator acceptance remain separate.
The [complete entity-name review](docs/ENTITY_NAME_TRANSLATIONS.md) now checks all
45 registered entities per provider through native DE/EN/FR/IT naming, including
personal choices and weather-device inheritance. It supplies automated evidence
for every exposed name and distinguishes four retained inactive catalogue keys.
Technical compatibility strings and place aliases are separate scopes rather
than missing entity-name keys; release/operator naming acceptance remains open.
Review historical stale grouping in a bounded scope. Obtain
authoritative multilingual locality aliases before adding provider name
translations. Preserve personal registry choices, identities, history,
four-language catalogues and existing quality/security gates.

The published b1 [shared-diagnostic lifecycle fix](docs/SHARED_DIAGNOSTIC_LIFECYCLE.md)
adds explicit ownership and native registry-preserving handoff for the two
helpers. It covers ordinary entry departure, changed startup order and bounded
failure/concurrency cases without reloading peer weather sources. Conflicting
legacy records stop the transfer with a repair; historical cleanup and overall
dynamic/stale-device applicability remain separate. Release/operator acceptance
is not inferred from this source work.

The published b1 [manual device-removal policy](docs/DEVICE_REMOVAL.md) permits
only an unambiguous empty service shell for a non-existing entry ID. Current,
disabled, shared, bound or linked groups stay protected. Native device-page
and Recorder tests bound the behaviour; source-history review establishes
identifier forms, not production orphans. No automatic historical cleanup or
full stale-device/Gold completion is claimed.

The [Gold matrix](docs/QUALITY_SCALE.md) retains these requirements. Native
icons and translated update failures are released and accepted; they do not
complete the full checklist. No new feature, HA test or release is approved by
this status reconciliation.

## Implemented and released in 8.3.0

- HA-owned HTTP sessions, bounded transient retries, cancellation and independent
  required/optional source startup.
- Station observations with measurement times, trailing-partial-row handling
  and explicit failure/recovery.
- Catalogue-backed postcode/town/POI selection, height-aware ICON Seamless
  forecasts, native weather units and continuing HA forecast subscriptions.
- Separately named observation/forecast devices, eight today/tomorrow sensors,
  complete Swiss calendar-day handling and a shared location-settings dialog.
- Completed hourly precipitation statistics and a 13-month archive import,
  retaining statistic identity and corrections.
- App v3 warnings, verified thirteen-family mapping, active/upcoming separation
  and German/English/French/Italian labels.
- Measured pollen, modelled pollen/AQ and separately optional current UV.
- Forecast-based daily HGT 12/20; no fictitious measured seasonal total.
- Shared station metadata, redacted diagnostics and checked cache expiry.
- Bounded HTTP/asset validation, shared parsing and separated source/coordinator
  responsibilities, with inactive standalone camera/SLF/hydrology placeholders removed.
- PR review, minimum/current HA tests, CodeQL, SonarCloud, Hassfest, HACS
  validation, bundled icons and plain-language user guides.

Code and CI success do not mark a candidate as installed or accepted on a real
HA system. Source providers and optional individual values can be unavailable.

## Release progress

Stable **8.3.0** was published on **24 October 2026**, retaining the runtime
accepted in b4 with version-only component changes. Later that day, Frenck
approved and merged [HACS catalogue admission #12593](https://github.com/hacs/default/pull/12593).
New users find this fork through normal HACS search. The
[admission record](docs/HACS_ACCEPTANCE.md#hacs-catalogue-admission) links the
review, successful checks and current catalogue entry.

The operator's earlier source-switch, clean-install and isolated restore checks
are complete within their recorded scope; do not repeat them for catalogue
admission. On 25 October the operator confirmed that the production update
from 8.2 to stable 8.3 worked successfully. See
[release readiness](docs/RELEASE_READINESS.md) and [publication](docs/PUBLISHING.md).

We use the HA Quality Scale to guide documented engineering work. The
[rule matrix](docs/QUALITY_SCALE.md) records applicable Bronze/Silver evidence,
test coverage and remaining Gold work. Official HA tiers are not assigned to
custom integrations.

## Separate future scopes

| Scope | Decision still needed |
|---|---|
| Locality names in other languages | Obtain authoritative aliases; preserve provider identities and avoid invented translations or duplicate places. |
| Remaining Gold engineering work | Diagnostic defaults, service metadata and alternative-provider labels are delivered in published stable 8.3.4. Native pollen-station changes reuse the existing groups; historical orphan review, entity translations and the fixed-group lifecycle assessment remain separate. The published b1 wind migration has bounded native/operator evidence; historical inventory and remaining rule-specific evidence stay separate. Discovery exemptions have documented applicability reasons. Icon/error translations are delivered in published and operator-accepted stable 8.3.3; preserve existing user choices and history. Shared-Reconfigure focused acceptance is completed within its reported scope. |
| External contributor CodeQL | The unprivileged route is implemented; retain evidence from the first actual external-fork run. A skipped analysis is not completed analysis. |
| Processed local-forecast data | Assess provider payloads, resource limits and compatibility separately from the already released catalogue-based ICON selection. |
| New sources/entities | Scope and test separately; no new device actions/sources in a documentation or release change. |

Radar in a separate integration is not a feature delivered by this repository.
