# Release readiness

## Stable candidate 8.3.6

The [8.3.6b1 prerelease](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.6b1)
was published on 20 November 2026 at 07:07:12 UTC, release **452371818**, from
package merge `ceec7a8b23a5669f20677ef67a87b31b2b523d5f`. The operator
installed the beta on HA Core 2026.11.2 and confirmed the station weather,
daily minimum and maximum forecast temperatures, and the 24-hour forecast view.

Subsequent [PR #149](https://github.com/martins-netizen/ha-meteoswiss/pull/149)
changes only entity tests. Its signed merge is the packaging base for stable
8.3.6. The two component version fields change for this promotion. The package
has its own checks and publication approval. See the [candidate notes](RELEASE_8.3.6.md)
and the [latest stable release](https://github.com/martins-netizen/ha-meteoswiss/releases/latest).

## Published stable 8.3.5

**Stable [8.3.5](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5)
is published and independently verified**, release **450993306**, on
**19 November 2026 at 07:12:57 UTC / 08:12:57 CET**. Its tag resolves to signed
package merge `cc158cbdce07f015952275fba72e3c0160c63c80` from approved
[PR #132](https://github.com/martins-netizen/ha-meteoswiss/pull/132), exact tree
`d31322c0c2fd9029ad7c066803f7acdc68c7c4fa`. All ten trusted exact-head checks
and all nine actual-merge checks passed. Both actual Core fixtures passed
**3,761 tests plus 83 subtests**, strict coverage and fresh 51-rule verification,
with the five known upstream deprecations visible.

The package changes only two component version fields relative to approved
corrective source `115ddad474dcae15aa49fb5f368cbed600adf80d` from
[PR #131](https://github.com/martins-netizen/ha-meteoswiss/pull/131). Its other
50 component files and existing policies/locks remain unchanged. The canonical
ninth-coordinator placement and calculated-HGT Swiss-midnight registered-state
update are included; [the completion record](COORDINATOR_CANONICAL_COMPLETION.md)
retains their concrete corrective evidence.

Release and latest-stable records matched exactly, with `draft=false` and
`prerelease=false`. The English body matched the approved 10,715-byte export;
all 23 older complete release records and raw tag refs remained unchanged.
The [current evidence](RELEASE_EVIDENCE_8.3.5.md) records these completed stages.
No further package, merge, publisher run or publication approval is needed for
this release.

A normal Marketplace update of the existing entry and its ordinary restart
remain a separate user operation; installation of 8.3.5 is not yet confirmed.
Earlier b3/b5/b6/b7 operator reports stay closed. No repeated migration, failure
exercise or observation window is introduced. Future package availability
follows the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).

## Dated earlier release records

The following records retain their original dates, counts and then-open scope.
They are historical evidence, not current instructions to rerun completed
packages or a current list of remaining Gold work.

## 8.3.5b6 package boundary

B6 includes HGT pending-import ownership and bounded precipitation imports,
with the HA 2026.11.0 minimum and 2026.11.2 current fixture. Its
[dated evidence](RELEASE_EVIDENCE_8.3.5b6.md) separates source, package checks,
publication and installed acceptance. The [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
determines availability. Retain the existing entry and follow
[the short read-only check](ACCEPTANCE_8.3.5b6.md); accepted b3 cleanup/b5
availability remain closed. Full Gold and independent assurance remain separate.

**Document version:** 2.29 · **Updated:** 17 November 2026

<a id="prepared-835b1-reviewed-source-publication-and-operator-acceptance-separate"></a>


## Published 8.3.5b4: measured HGT, focused acceptance separate

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
restart HA. Its original [measured-HGT protocol](ACCEPTANCE_8.3.5b4.md) is
retained. For the retry correction choose published b5 and its
[focused recovery check](ACCEPTANCE_8.3.5b5.md); no prior b4 installation
or repeated cleanup is required. Accepted b1/b2/b3 scopes and PR #114 stay closed.

Publication is complete. Do not rerun a publisher as a new update action.
Choose the current published recovery test package through the release
catalogue. Keep the entry and station; completed cleanup stays complete.
Full Gold, independent review and any stable promotion remain separate.

## 8.3.5b3: published and focused cleanup accepted

[8.3.5b3](RELEASE_EVIDENCE_8.3.5b3.md), release **446112927**, was published on
**15 November 2026 at 14:19:50 UTC** from regular PR #113, merge
`b6c4502e5cdeb48121be628fdb7eda579df4f7c3`, exact tree
`bb8c9de9a3822d56eac6f49892852d3cede298df`. Ten head and nine actual merge
checks passed. Each native HA job passed 2,900 tests + 83 subtests and every
strict step; both hosted jobs had six warnings including the known SQLite one.
The immutable release/tag/English body and all eighteen older release records,
bodies and tags were independently confirmed. Stable **8.3.4** stays latest.
The 46 non-version component files out of 48 match accepted PR #112 source.

The operator confirmed the existing-entry update and focused native HGT cleanup
successful on 15 November: repair/listed old IDs gone, forecast ready with no
archive reference, cleanup-required false and normal operation retained. This
closes that agreed operator acceptance, without an independent whole-database
orphan-row audit. Do not repeat publication, installation or deletion; earlier
b1/b2 scopes also remain closed. See [upgrade guidance](UPGRADING_8.3.5.md).

PR #114's [test Recorder lifecycle](TEST_RECORDER_LIFECYCLE.md) is merged and
actually verified; that test-only change requires no production update.
Official measured HGT source PR #115 is now merged and actually verified too;
[published 8.3.5b4](RELEASE_EVIDENCE_8.3.5b4.md) packages it separately.
B3 acceptance remains closed. Focused b4 acceptance, remaining Gold,
independent review and any stable promotion remain separate.

## 8.3.5b2: fixed HGT archive test package

[8.3.5b2](RELEASE_8.3.5b2.md), release **445608354**, was published on
**14 November 2026 at 21:40:13 UTC** from packaging merge
`f8ea38babdfd44354059927888fb54fd662e5696`. It retains PR #110 runtime except
for its two version files. All 17 older tags/release bodies and stable 8.3.4
were independently confirmed. Publication is complete; its publisher is not a
new update action. The operator's visible HGT check is also closed: `ready`,
archive assignment and current forecast were shown, and disappearance of the
original live-HGT Core repair was explicitly confirmed. This is not a full
historical database or 46-file installation audit.

B2's archive-and-keep behaviour remains its immutable historical boundary.
The [b3 cleanup](UPGRADING_8.3.5.md) instead recommends explicit full removal of
obsolete forecasts. B3 publication and its focused native deletion acceptance
are now closed; earlier b1/wind and b2 visible acceptance also stay closed.


## Published 8.3.5b1: bounded acceptance recorded; HGT fixed in b2

The [test candidate](RELEASE_8.3.5b1.md) packages regularly merged source
`b144a0b73d81358f27fd6ecd89a47120c8a0a1b9`, including the reviewed HGT/wind
statistics and diagnostic/name/lifecycle work after stable 8.3.4. Its 42
non-version component files remain byte-identical; only manifest.json/version.py
change. HA 2026.11.0 is the minimum; fixtures remain 2026.11.0/2026.11.1.

Source PR #107 passed all ten head and nine actual merge checks. The separate
manual Dependency audit [run 43389137603](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43389137603)
also passed on that exact source: 140 package/version pairs, no active advisories
and no unknown results. This proves the manual hosted workflow. Later actual scheduled runs on b2 and
PR #112 source are recorded above; failure-notification delivery remains separate.

Packaging PR #108 was regularly merged as
`af1220249e672bd8a6742c73022a7c42aca2f20a`, exact tree
`d96f2c05190eb24050a7d61e3cb13f86f808bb92`. All ten head and nine actual merge
checks passed. After separate publication approval, release **444798178** was
published on **13 November 2026 at 22:21:10 UTC**, `prerelease=true`,
`draft=false`. Independent reads confirm the immutable tag, exact approved body,
all sixteen older tags and stable **8.3.4 / ID 437853341** as latest. A matching
second publisher invocation verified the same release without another write;
see [publication evidence](RELEASE_EVIDENCE_8.3.5b1.md).
B1 production installation and visual operation are operator-confirmed. A
read-only report matched all tagged component files and observed retained wind
arithmetic history plus new circular points. The HGT state-class Repair is
not accepted as a permanently unresolved normal outcome. The
[b2 archive fix](RELEASE_8.3.5b2.md) was published and its visible operator check
is closed. B3 adds the separate confirmed cleanup repair and needs its own
bounded acceptance before stable promotion.
The [focused protocol](ACCEPTANCE_8.3.5b1.md) keeps a historical wind migration
on a test/restored copy until its preservation boundary is accepted. A version
rollback alone does not reverse Recorder metadata. Earlier accepted scopes stay
closed; remaining Gold/lifecycle applicability and independent review stay open.

Complete local packaging validation passes **2,715 tests plus 83 subtests** on
each HA **2026.11.0/2026.11.1**, Python **3.14.10**, with five existing upstream
warnings and all strict gates. Integration coverage remains **99.979883%**
(3,884/3,885 statements and all 1,086 branches). Fourteen publication profiles
retain prior boundaries; 55 new cases cover the new profile and its locked CI
policy. Both actual hosted HA merge jobs passed the same test counts and gates.

<a id="prepared-stable-834"></a>

## Published stable 8.3.4; actual update protocol remains separate

[Stable 8.3.4](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4),
release **437853341**, was published on **7 November 2026 at 21:24:27 UTC**.
Its immutable tag points to regular packaging PR #93's merge
**f4479897023fa35d7c2fcb4c4859c4de8861fdda**, tree
**1657d5415c14653a81e2387f5e469a6c8deea4f8**. The publisher receipt and independent
GitHub reads agree on the release, tag, exact approved English body and latest
stable selection. All fifteen older tags, accepted beta body and previous stable
8.3.3 remain unchanged. See [publication evidence](RELEASE_EVIDENCE_8.3.4.md).

It makes the accepted beta's maintenance/quality improvements available through
the stable route: official-package HA 2026.11 validation, cleaner first-setup
diagnostic defaults and clearer source/service labels. Existing personal choices
are retained. See [benefits over 8.3.3](RELEASE_8.3.4.md#why-upgrade-from-833).
All 39 non-version component files match accepted beta
**1e5c5d1a7fc1c18d520e99189ae4dd5894621706**; only two version fields change.

Both actual package-merge jobs pass **2,225 tests plus 83 subtests** on HA
2026.11.0 / 2026.8.3, including the matching official current-HA test package.
Coverage is **99.977812%**, with all strict gates unchanged. All seven actual
merge checks succeed. Fixed Stable Publisher V1.7 and thirteen publication
profiles retain their accepted-source/body/version/check/tag/latest boundaries.

For an actual stable update, use only the [short protocol](ACCEPTANCE_8.3.4.md):
actual download, one restart, installed version and normal operation. Publication
does not assert a user's installation. Earlier beta, settings, icons, first
install and restore acceptance remain closed within their scopes; no extra
names/IDs, source switch or blanket wait is required. HGT PR #92, wind/history
migrations and remaining Gold work stay separate.

<a id="prepared-834b1-test-candidate"></a>

## Published 8.3.4b1; agreed short operation check complete

[8.3.4b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4b1),
release **437718127**, was published on **7 November 2026 at 17:12:54 UTC**
from regularly merged packaging PR #90,
**1e5c5d1a7fc1c18d520e99189ae4dd5894621706**, tree
**de678c1b9ade03b1519ba091a787497d84e5bfd7**. All seven actual package-merge
checks succeeded. The package preserves 39 non-version component files from
#88/#89 source `5a7eae00963d47294281da8812cb1ede35713b7f`; only the two
version fields change. Local packaging suites each passed **2,171 tests plus
83 subtests** on HA 2026.11.0 and 2026.8.3, with **99.977812%** coverage and
unchanged strict gates. Twelve publisher profiles and their refusal/retry
tests retain all prior publication boundaries.

Publisher receipt and independent verification agree on actual release/tag,
source, flags and exact exported body. All fourteen older tags remain unchanged;
**8.3.3 / ID 429354633 remained latest stable at that beta publication**.
The separate stable 8.3.4 publication is recorded above. Original published notes and
the immutable tag are retained. See the
[complete evidence](RELEASE_EVIDENCE_8.3.4b1.md).

The operator subsequently reported normal operation OK, **HA Core 2026.11.0 /
HA OS 18.4**, and that everything works. This completes the agreed
[short check](ACCEPTANCE_8.3.4b1.md). The reply follows the beta check request;
it does not separately restate the integration version, identify the instance
as production hardware or a VM, independently audit registry/Recorder data,
or separately report an alternative-source inspection. No further names/IDs,
download/restart or blanket wait are requested. Earlier accepted checks remain
closed. Historical orphans, device classes and full Gold remain separate.
This beta record is provenance for the separately published stable 8.3.4.

<a id="prepared-stable-833"></a>

## Published and accepted stable 8.3.3

[Stable 8.3.3](RELEASE_8.3.3.md), release **429354633**, was published on
**30 October 2026 at 18:21:55 UTC** from
**3d4fad2330c89f134eba208e8b2db55705177e7d**, tree
**b53df969640e8b15df690de59a95639f3735e05c**. It was latest until 8.3.4 and remains immutable,
draft=false and prerelease=false. Publisher receipt/log and independent
release/tag/notes/source/latest verification agree. All thirteen older tags
remain unchanged; the published body matches the approved export, SHA-256
**62d7b02e39bec84162e0cc5b3770600c4c87109b83be473f803fd59c5f877de0**.

The operator subsequently confirmed **8.3.3 installed and normal operation OK**
on **30 October**, completing the [short actual stable update](ACCEPTANCE_8.3.3.md).
This report does not restate Core/OS/Python or provide an independent registry
audit. Beta icons/personal choices on Core 2026.10.4 / HA OS 18.4, earlier shared
settings, clean-install and restore checks remain complete within their scopes.

All **39 non-version component files** of the 41-file package match accepted
published beta **d9fbc3fd49220b0ecc019d2babe0c173c46986f5 / ID 429321251**;
only manifest.json/version.py become 8.3.3. Four 219-key catalogues,
English/source parity, icons.json, HACS/CH, workflows and security guards match.
No runtime addition follows the accepted beta.

All seven actual merge checks pass: CI **41105597207**, CodeQL **41105597266**,
HACS **41105597240**, with SonarCloud Code Analysis. Actual HA 2026.8.3/2026.10.1
jobs pass **2,096 tests plus 83 subtests** each (43.83 s / 71.36 s).
Fixed Stable Publisher V1.6 retains the version-only/accepted-publication/check
boundaries and adds the eleventh publication test profile. The
[complete evidence](RELEASE_EVIDENCE_8.3.3.md) separates source, environment,
publication and the bounded operator report. No further HA acceptance or
blanket observation wait is pending for this release. Full Gold remains open.

<a id="prepared-833b1-test-candidate"></a>

## Published and accepted 8.3.3b1: native icons and translated errors

[8.3.3b1](RELEASE_8.3.3b1.md), ID **429321251**, was published on **30 October
2026 at 17:42:37 UTC** from **d9fbc3fd49220b0ecc019d2babe0c173c46986f5**.
It is an immutable prerelease. Publisher receipt/log and independent actual
release/tag/notes/latest checks agree; all twelve earlier tags remained
unchanged and stable 8.3.2 stayed latest. The published body matches the
approved immutable-source export, SHA-256
**4124b1dbe4250345bc2019763f0e4db43cfb165aa84f25f1cb3ced32e9903ca1**.

The operator subsequently reported **icons/personal choices OK and normal
operation OK** on **HA Core 2026.10.4 / HA OS 18.4**. This closes the
[short focused check](ACCEPTANCE_8.3.3b1.md) within that reported scope.
No independent registry/statistic inventory or manual triggering of every
translated failure is inferred. The reply did not restate the integration
version; it directly follows the requested 8.3.3b1 check.

Reviewed #80/#81 source is **c7c64d64e0efa582873d2e8e492531deb2aa6112**,
tree **43fc687bc766bbaf4fafd845b5a95449aea85713**. The beta retains all 39
non-version files; only manifest.json/version.py become 8.3.3b1. The actual
packaging merge has all seven checks successful: CI **41075487719**, CodeQL
**41075487573**, HACS **41075487638**. Both hosted HA 2026.8.3/2026.10.1 jobs
pass **2,045 tests plus 83 subtests** (52.19 s / 52.84 s respectively).

Hosted checks use **Python 3.14.10 / pip 26.2.2 / certifi 2026.10.23 /
UV_OFFLINE=true**. Historical HA uv pins remain explicit unpatched offline
compatibility exceptions. Flow coverage remains **406/406 statements and
146/146 branches**; whole component **3,516/3,517 statements and 974/974
branches**, with all strict gates and four exclusions unchanged. Local
Python 3.12 checks do not claim native HA validation. CI does not patch a
live HA Python image. Remaining Gold work is separate.

## Published and accepted stable 8.3.2

[Stable 8.3.2](RELEASE_8.3.2.md), ID **426633496**, was published **28 October
2026 at 12:21:19 UTC** from **aea4c5eab0534a6e675a4f564bde7521df193c58**.
It was latest until 8.3.3 on 30 October, and remains immutable and not a
prerelease. The exact published
source/notes and all eleven prior tags were independently checked. Actual
merge checks pass **1,983 tests plus 83 subtests** on each hosted HA fixture;
see [the complete release evidence](RELEASE_EVIDENCE_8.3.2.md).
On **30 October** the operator confirmed its HACS download, HA restart and
working operation, closing the [short stable update](ACCEPTANCE_8.3.2.md).
Accepted source
is published beta **5a39c3cdbf31f0807f52bcb4acb26190cc1e8423**, tree
**8add2f80ac62d78ac3817ff4b5898c74ad80da0f**. Of 40 component files,
**38 non-version files match**; only manifest.json/version.py become **8.3.2**.
HACS/CH, workflows, security guards and four 200-key catalogues are unchanged.
No runtime addition follows the accepted beta.

Stable Publisher V1.5 retains the version-only/check/provenance boundaries,
previous stable 8.3.1 and accepted beta 8.3.2b1 publication guards, all eleven
old tags, latest selection and read-only retry semantics. It adds a ninth
fixed publication regression profile: **431 publication cases**, including
51 added cases. Both complete local suites pass **1,983 tests plus 83 subtests**
on **HA 2026.8.3 (57.17 s)** and **HA 2026.10.3 (52.80 s)**. These existing
local interpreters remain **Python 3.14.8**; they provide regression evidence,
not proof of the current security baseline. Coverage is unchanged at
**3,516/3,517 statements and 974/974 branches**, combined **99.977733%**;
all existing strict gates and the four exclusions remain. Exact-head hosted
checks and the later actual merge checks are separate publication gates.

Publication and the [short actual stable download](ACCEPTANCE_8.3.2.md) are
separate results; both are now recorded as complete within their scope.
The five accepted beta steps below and earlier clean-install/restore checks
remain closed. Full Gold and future features stay separate.

<a id="prepared-832b1-test-candidate"></a>

## Published and accepted 8.3.2b1: complete shared settings

**8.3.2b1 / ID 425962004** was published **27 October 2026 at 20:40:42 UTC**
from **5a39c3cdbf31f0807f52bcb4acb26190cc1e8423**. The receipt/log and
independent release/tag/notes/versions/latest checks agree, including unchanged
latest stable 8.3.1 and ten old tags. All seven actual merge checks passed,
with **1,932 tests plus 73 subtests** on each hosted HA 2026.8.3/2026.10.1
using Python 3.14.10, pip 26.2.2, certifi 2026.10.23 and offline uv.

The operator reported **all five focused steps positive on HA Core 2026.10.4**.
This closes installation/version, both settings routes, cancellation, combined
saving and restoration of intended choices for the configured source. No
separate clean installation, independent registry/statistic audit, manual test
of every provider or independently inspected UTM environment is inferred.
The following preserves the original source/package evidence.

[8.3.2b1](RELEASE_8.3.2b1.md) retained the reviewed shared-settings source.
Reviewed runtime is merged PR #76 at
**d6ae2a0b1ae9c195c9647f6b416d347891f91a74**, tree
**489d818a27e58c45428085ab3d917b25ac694dbf**. It includes #75's secured local
recipe and the shared native settings transaction, retained search/reset on
source retry, concurrent-edit protection and complete four-language confirmation.
All eight updated-head checks and seven actual merge checks passed.

Both actual source-merge HA jobs passed **1,883 tests plus 73 subtests** on
**Python 3.14.10 / pip 26.2.2 / certifi 2026.10.23**, with UV_OFFLINE enabled.
Config flow has **406/406 statements and 146/146 branches**; whole integration
has **3,516/3,517 statements and 974/974 branches**, with all existing strict
gates/four exclusions retained. The historical uv pins remain explicitly
unpatched offline-only compatibility exceptions. CI is separate from operator
acceptance and does not patch a live HA image.

Packaging retains **38 non-version files** within the 40-file component, only
manifest.json/version.py become **8.3.2b1**. HACS/CH, minimum HA, workflows,
security guards and the ten older tags remain. The four **200-key** catalogues
retain English/source parity. V1.5 adds an eighth fixed publication profile:
**380 publication cases** pass, including 49 added cases for this package.
Both complete local suites pass **1,932 tests plus 73 subtests** on
**HA 2026.8.3 (88.63 s)** and **HA 2026.10.3 (81.64 s)**. These existing local
environments still use **Python 3.14.8**; they are regression evidence, not
evidence of the newer security baseline. Coverage remains **3,516/3,517
statements and 974/974 branches**, combined **99.977733%**, with the existing
strict gates. Hosted exact-head and actual merge checks remain separate gates
before publication; their later successful result is recorded above. The
[focused existing-entry protocol](ACCEPTANCE_8.3.2b1.md) records the accepted
operator report; previous clean-install/restore acceptance stays closed.

<a id="prepared-stable-831"></a>

## Published stable 8.3.1

Stable **8.3.1 / ID 424249153** was published on **26 October 2026 at
12:54:24 UTC** from **fa298ca72bf62da727797f9bfcacf95c83ffeaf1**, retaining
the accepted b1 runtime. Actual stable HACS download is separately unconfirmed.
The following retains its historical package evidence.
The [stable 8.3.1 package](RELEASE_8.3.1.md) promotes the accepted b1 runtime. Source is published beta
**c7b20c78d4273a33ba8c6f06c1834fc2f22c8665**, tree
**d6e3853205f387372b1a2e49d6fb9f33c6b513b0**. Of 40 component files,
**38 non-version files match**; only manifest.json/version.py become **8.3.1**.
HACS/CH, workflows and all four 180-key catalogues are unchanged.

Stable Publisher V1.4 derives from the successful V1.3 route. It checks exact
protected development/source/version boundaries, seven checks and their apps,
previous stable 8.3.0 and accepted beta 8.3.1b1 publications, nine preserved tags,
release notes and latest selection before/after the single permitted write.
A matching retry is read-only; conflicts stop. Complete package tests retain
all earlier profiles and add the new stable profile: **1,780 tests plus
73 subtests** pass on each local **HA 2026.8.3 and 2026.10.3 / Python 3.14.8**,
including **331 publication-profile cases**. Combined coverage remains
**99.977698%**: **3,503/3,504 statements** and **980/980 branches**. Both strict
gates pass; thresholds, strict modules and four exclusions are unchanged.
DE/EN/FR/IT each have **180 keys** with English/source parity. Actual PR/head
and regular merge checks remain separate evidence before publication.

After publication, the [short stable update](ACCEPTANCE_8.3.1.md) records the
version actually downloaded through HACS and continued intended places/values.
The accepted beta UI check and previous first-install/restore checks stay closed.
No new blanket 24-hour observation window is added.

<a id="prepared-831b1-test-candidate"></a>

## Published and accepted 8.3.1b1

Beta **8.3.1b1 / ID 423899845** was published on **26 October 2026 at
05:54:44 UTC** from **c7b20c78d4273a33ba8c6f06c1834fc2f22c8665**, after
approved PR #71. Receipt/log and independent release/tag/notes/version/latest
checks confirm the result, including unchanged stable **8.3.0 / ID 422817883**.
All eight PR checks and seven merge checks passed. The operator subsequently
confirmed the requested installed-version and visual check. This is focused
reported acceptance; no separately supplied HA-core version, registry/statistic
audit or deliberate damaged-selection test is inferred.

The source retains PR #70 repair/map runtime at
**22004177b96adb4452fdbd116174915de4dc18cf** with only beta version changes.
Its local suites passed **1,729 tests plus 63 subtests** on each HA 2026.8.3
and 2026.10.3 / Python 3.14.8, including **280 publication-profile cases**.
Coverage was **99.977698%**: **3,503/3,504 statements**, **980/980 branches**,
all strict gates and the four previous exclusions retained. All four 180-key
catalogues have English/source parity. The [focused protocol](ACCEPTANCE_8.3.1b1.md)
remains available as a method, not a request to repeat completed checks.

<a id="current-release-position"></a>

## Historical 8.3.0 release position (24–25 October)

The operator accepted **8.3.0b4** with a positive overall result and requested stable 8.3.
Additional screenshots show the installed b4 version, seven devices/45 entities,
a working station weather symbol and measurements, and a separate named forecast
with known today/tomorrow values. The count is installation-specific. Screenshots
do not prove every attribute, registry identity or an unperformed source-outage
test. Public summaries contain no private screenshots or raw diagnostics.

The stable package retains b4 runtime **a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5**.
Of 39 component files, **37 are byte-identical**; manifest.json/version.py change
only from b4 to **8.3.0**. HACS metadata, seven earlier tags, workflows and four
178-key UI catalogues are retained. This is a version-only promotion; no new
feature is included after the accepted runtime.

Stable **8.3.0 was published on 24 October 2026 at 15:35:56 UTC**, release ID
**422817883**, from **3ca9a1c166920fbdda88d15238affafe520f4b68**. The
[latest published stable endpoint](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
agreed at that verification; the later 8.3.1 publication is recorded above.
[HACS catalogue admission](HACS_ACCEPTANCE.md#hacs-catalogue-admission)
was completed later that day. On **25 October** the operator confirmed that the
production update from **8.2 to stable 8.3** worked successfully. Publication,
catalogue admission and reported local update are now separately recorded.

## Completed evidence

| Area | Evidence and boundary |
|---|---|
| Original stable 8.2.0 | Published 22 October at 06:52:40 UTC /08:52:40 Europe/Zurich; release ID 420392277, tag 5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5. Operator-confirmed HACS update. |
| HACS/source switch, first install and restore | Operator-confirmed on 20–22 October in HACS 2.0.5/HA 2026.10.2 within the [recorded scope](HACS_ACCEPTANCE.md). No new independent beginner-usability study is claimed. |
| B1/B2 | Published as 422558946/422656379; initial selection worked and display ambiguity was corrected with a separate named forecast device. Earlier beta notes remain historical. |
| B3 | Published 24 October 13:19:44 UTC /15:19:44 Europe/Zurich, ID 422744751, tag 9d75aa8673c417f24caaa1f83181b5ef811d56fc. Operator confirmed shared station changes and known calendar-day values on 2026.10.3. |
| B4 | Published 24 October 14:47:49 UTC /16:47:49 Europe/Zurich, ID 422790421, tag a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5. Receipt/log, independent release/tag/notes/manifest/checks and retained latest 8.2.0 verified. Operator accepted the focused HA check; screenshots supplement that report. |
| B4 automation | 1,603 tests +53 subtests on each local HA 2026.8.3/2026.10.3, Python 3.14.8. Combined 99.97753%:3474/3475 statements,976/976 branches. Strict gates/four existing exclusions retained; 176 publisher-profile cases. |
| Stable package automation | 1,653 tests +63 subtests on each local HA 2026.8.3/2026.10.3. Includes 226 publisher cases across five profiles: 220 shared boundary cases and six stable-specific cases; stable/latest selection, preserved publications/tags and no-write retries are covered. Coverage and strict gates unchanged. |
| Hosted checks | CI matrix remains 2026.8.3/2026.10.1; tests, SonarCloud, HACS, hassfest and CodeQL must pass on the exact stable PR/head and merge. Additional local 2026.10.3 evidence is distinct. |
| Documentation | Current setup/migration/roles/settings guides describe 8.3; provider labels, selected-place limits, card-target changes, cache counters and quality-tier limits remain explicit. |
| Stable publication | PR #68 regularly merged as 3ca9a1c166920fbdda88d15238affafe520f4b68. Release 8.3.0 / ID 422817883 published 24 October at 15:35:56 UTC, latest stable, no draft/prerelease; tag and seven prior tags verified. |
| HACS catalogue | [hacs/default #12593](https://github.com/hacs/default/pull/12593) approved by Frenck and merged 24 October at 20:04:26 UTC. Current integration list contains the fork; all 13 distinct latest checks passed. See [evidence](HACS_ACCEPTANCE.md#hacs-catalogue-admission). |
| Stable production update | Operator confirmed on 25 October that the update from 8.2 to stable 8.3 worked successfully. This is reported operational evidence, not a new independent byte/registry audit. |

## Completed publication and operator update

The stable-package PR, exact-head/merge checks, guarded publication and
release/tag/latest verification are complete. The [publication procedure](PUBLISHING.md#stable-830)
retains their version-specific method as history, not a new instruction to
merge, publish or retag 8.3.0 again. HACS catalogue admission is also complete.

The [stable HACS update check](ACCEPTANCE_8.3.0.md) is closed by the operator's
successful production-update report. Its protocol remains available for other
installations; it does not reopen this completed update. No new blanket 24-hour
wait, repeated first-install or restore rehearsal is required for unchanged
component code. Catalogue admission alone requires no reinstallation.

Do not repeat merges or publication once their exact result is confirmed.
Operational outcomes belong in the operator's master; this source document
does not manufacture a future release time or HA installation result.

## Security and quality follow-ups

The shared [HTTP hardening](HTTP_SOURCE_HARDENING.md), eight canonical coordinator
roles and source-client separation are in the b4 source, not future architecture
work to repeat. The [CodeQL route](CODEQL_FORK_REVIEW.md) is implemented; the first
actual foreign-fork run still needs evidence. No penetration-test or
zero-vulnerability claim is made. Private-reporting activation is
operator-confirmed, not a fresh administration-settings audit.

The [rule matrix](QUALITY_SCALE.md) records applicable technical Bronze/Silver
evidence, the custom branding route and open/partial Gold work. Custom integrations
have no official HA quality tiers; the rules guide our engineering assessment.
The completed HACS catalogue admission is a separate distribution result.
The bounded [HA Repairs follow-up](REPAIRS.md) is published and operator-accepted
in 8.3.1b1; stable promotion remains a separate publication. Further work includes sourced multilingual
locality aliases and the remaining Gold items. Retain App v3 warnings; separate river/bulletin/radar
products are not introduced. A UTM restart problem was reported; its cause was
not diagnosed and these tests do not establish one.

## References

- [8.3.0 notes](RELEASE_8.3.0.md), [stable update](ACCEPTANCE_8.3.0.md)
- [B4 source/acceptance](RELEASE_8.3.0b4.md), [station condition](STATION_WEATHER_CONDITION.md)
- [Overall review](RELEASE_REVIEW_2026-10-24.md), [publishing](PUBLISHING.md)
- [Original stable notes](RELEASE_8.2.0.md), [HACS evidence](HACS_ACCEPTANCE.md)
