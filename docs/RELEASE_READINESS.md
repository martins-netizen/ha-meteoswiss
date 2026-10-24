# Release readiness: 8.3.0 promotion from accepted b4

**Document version:** 2.6 · **Updated:** 24 October 2026

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

Stable publication, the actual release ID/time and the subsequent HACS update
are separate results. The [latest published stable endpoint](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
is authoritative. Until the stable publisher verifies 8.3.0 there, a source
version alone is not publication evidence.

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

## Remaining stable steps

1. Regular stable-package PR with all exact-head checks successful; merge without
   bypass, then verify the expected tree and all merge-commit checks.
2. Run **veroeffentliche_meteoswiss_stable_v1.3.sh --check FULL_MERGE_SHA**, or
   directly its approved **--publish FULL_MERGE_SHA** mode, which performs the
   same checks before its only remote write. It requires the exact protected
   development head, accepted b4 code/publication and previous stable 8.2.0.
3. Verify the published 8.3.0 tag, notes, release ID/time, latest-stable selection
   and all seven old tags. The helper never retags or overwrites a release.
4. Follow the [stable HACS update check](ACCEPTANCE_8.3.0.md), retaining the
   existing entry and intended locations. No new blanket 24-hour wait, repeated
   first-install or restore rehearsal is required for unchanged component code.

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
evidence, external Core branding limits and open/partial Gold rules. Official
tiers and HACS default-catalogue submission are separate from this release.
Further work includes sourced multilingual locality aliases, HA Repairs and
the remaining Gold items. Retain App v3 warnings; separate river/bulletin/radar
products are not introduced. A UTM restart problem was reported; its cause was
not diagnosed and these tests do not establish one.

## References

- [8.3.0 notes](RELEASE_8.3.0.md), [stable update](ACCEPTANCE_8.3.0.md)
- [B4 source/acceptance](RELEASE_8.3.0b4.md), [station condition](STATION_WEATHER_CONDITION.md)
- [Overall review](RELEASE_REVIEW_2026-10-24.md), [publishing](PUBLISHING.md)
- [Original stable notes](RELEASE_8.2.0.md), [HACS evidence](HACS_ACCEPTANCE.md)
