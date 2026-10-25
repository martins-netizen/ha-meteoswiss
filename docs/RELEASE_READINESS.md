# Release readiness: 8.3.0 promotion from accepted b4

**Document version:** 2.9 · **Updated:** 25 October 2026

## Prepared 8.3.1b1 test candidate

The [repair and station-map package](RELEASE_8.3.1b1.md) is prepared, **not
published**. Its reviewed runtime is PR #70 at
**22004177b96adb4452fdbd116174915de4dc18cf**, tree
**6bb5eb45e10cd3390b32e5901ccbe288a6591a63**. All eight PR checks and seven
post-merge checks passed. Packaging retains **38 non-version component files**;
only the two version files become **8.3.1b1**. HACS/CH, workflows, all four
180-key catalogues and eight earlier release tags are unchanged.

Publisher V1.4 has a fixed 40-file/source contract, exact-merge/check provenance,
read-only preflight, immutable-tag and retry guards. It preserves latest stable
**8.3.0 / ID 422817883**, including a final pre-write check. The shared
publication tests retain all five earlier profiles and add the new one. Local
full suites pass **1,729 tests plus 63 subtests** on each **HA 2026.8.3 and
2026.10.3 / Python 3.14.8**, including **280 publication-profile cases**.
Combined coverage remains **99.977698%**: **3,503/3,504 statements** and
**980/980 branches**. Both coverage gates pass; strict modules, thresholds and
the four existing exclusions are unchanged. DE/EN/FR/IT each have **180 keys**
with English/source parity. Hosted packaging checks must pass on the exact PR
head and later regular merge; they are separate from these local results.

After packaging review and a regular merge, verify that merge's checks before
announcing publication. The [focused UI check](ACCEPTANCE_8.3.1b1.md) is pending;
it needs no damaged production entry, forced outage, repeated restore or new
blanket observation period. The operator-confirmed stable 8.3 update below
remains complete. A prepared package is not a HA installation or UI acceptance.

## Current release position

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
agrees. [HACS catalogue admission](HACS_ACCEPTANCE.md#hacs-catalogue-admission)
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
The bounded [HA Repairs follow-up](REPAIRS.md) is unreleased development and
needs separate focused acceptance. Further work includes sourced multilingual
locality aliases and the remaining Gold items. Retain App v3 warnings; separate river/bulletin/radar
products are not introduced. A UTM restart problem was reported; its cause was
not diagnosed and these tests do not establish one.

## References

- [8.3.0 notes](RELEASE_8.3.0.md), [stable update](ACCEPTANCE_8.3.0.md)
- [B4 source/acceptance](RELEASE_8.3.0b4.md), [station condition](STATION_WEATHER_CONDITION.md)
- [Overall review](RELEASE_REVIEW_2026-10-24.md), [publishing](PUBLISHING.md)
- [Original stable notes](RELEASE_8.2.0.md), [HACS evidence](HACS_ACCEPTANCE.md)
