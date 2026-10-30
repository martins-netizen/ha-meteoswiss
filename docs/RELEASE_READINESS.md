# Release readiness: published and accepted stable 8.3.2

**Document version:** 2.13 · **Updated:** 30 October 2026

## Published and accepted stable 8.3.2

[Stable 8.3.2](RELEASE_8.3.2.md), ID **426633496**, was published **28 October
2026 at 12:21:19 UTC** from **aea4c5eab0534a6e675a4f564bde7521df193c58**.
It is latest stable, immutable and not a prerelease. The exact published
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
