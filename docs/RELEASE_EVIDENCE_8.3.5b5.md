# 8.3.5b5: source, package and publication evidence

**Evidence version:** 1.1 · **Updated:** 17 November 2026

## Completed publication and focused availability

Published [8.3.5b5](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b5),
release **447678651**, at **22:08:42 UTC on 16 November 2026** from approved
regular package merge `ba8a15aa282aa7b67d16c83cca6f99e38ee2bf4b`, tree
`cd82dfa02bf1638125283b6ad44c54dc3cce5028`, direct parent
`6873c0390cb276dc6afa2c347d055e995d7bf956`.
All ten expected package-head and nine actual-merge checks passed. The immutable
release/tag/English body, all twenty earlier releases/tags and latest stable
**8.3.4 / 437853341** were independently verified. The fifty non-version
component files match the reviewed #119 source.

After updating the existing installation to b5, the operator reported the
last-observed-day HGT entry available. This closes that focused availability
acceptance. It does not independently verify every historical row, all
attributes in the protocol below or which recovery attempt succeeded. The
earlier b4 unavailable-state cause remains unproven. Completed b3 cleanup stays
closed; no repeat installation, cleanup or diagnostic export is requested.

The [pending-import ownership correction](HGT_PENDING_IMPORT_OWNERSHIP.md) is a
later, separate unreleased change. It does not alter this immutable release.
The preparation requirements below explain the completed publication process;
they are not outstanding steps or instructions to publish b5 again.

## Confirmed source

[PR #119](https://github.com/martins-netizen/ha-meteoswiss/pull/119) is regularly
merged at `6873c0390cb276dc6afa2c347d055e995d7bf956`, tree
`c3ad7191c52e8b62bb02c9dd2c3119949d1cd254`, direct parent
`a6a233513ac8e7c5937f9c41eee085e76108e801`. Its valid GitHub signature,
handle/noreply author, GitHub committer and source-branch deletion are verified.
Ten trusted head checks and nine actual merge checks passed. Actual merge
[CI 43872957431](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43872957431),
CodeQL 43872957350 and HACS 43872957758 are successful. Both supported HA suites
passed 3,101 tests plus 83 subtests, five known warnings, the strict coverage
gates and full coverage of the changed HGT coordinator. Combined source-tree
coverage is 99.9831%. Locks retain 138 selections each; the whole audit has
140 package/version pairs, zero active/unknown/withdrawn findings. Hassfest
reports zero invalid integrations; SonarCloud passed.

The approved publication documentation from #117 is included: fourteen of its
twenty documents are byte-identical and six retain all original content with
additional recovery guidance. #117 is closed as superseded, not a second merge.
The separately failing #118 dependency-lock update is not part of this source.

## Historical preparation: package and publication boundary

The b5 candidate changes only the two version fields among the 52 component
files and adds package documentation, Publisher V1.12 and its regressions.
All 50 non-version component files, old publishers/frozen notes, workflows,
locks and gates retain their reviewed source bytes.

Before publication, the b5 package needs complete local checks, all ten trusted
checks on its exact PR head, an explicitly approved regular package merge and
all actual merge checks. The source evidence above is already complete; these
package checks and publication are separate and are not claimed complete by
this prepared evidence page. The exact package PR/merge and publication
results must be recorded after they exist.

Use fixed `scripts/publish_meteoswiss_835_beta_v1.12.sh` with the full approved
package merge SHA: `--check SHA` performs read-only validation, while
`--publish SHA` is the separately controlled release step. It requires the
existing `martins-netizen` account, signed direct parent #119, exact non-version
source, two version fields, HACS policy, workflows/locks/gates and all actual
checks. Only the b5 prerelease can be created; no older release/tag is edited.
Its relative English release links are frozen to that approved commit.

The publisher verifies all twenty earlier tag references and complete older
release records/IDs before and after publication, plus latest stable
**8.3.4 / 437853341**. Interrupted or uncertain results retain a local receipt
and do not authorise blind retries, retagging or overwriting existing notes.
A matching existing publication can be read back without creating a duplicate.

Publication/availability follows the release catalogue. Publication alone does
not establish installation or current HGT availability. The original
[focused b5 UI protocol](ACCEPTANCE_8.3.5b5.md) describes the observed-day sensor,
its own source date/product IDs and normal weather/forecast operation. The
operator's actual availability report is recorded separately above; do not
infer the unreported protocol fields from it or reopen the agreed check.

Already accepted b3 cleanup stays closed. No new deletion, station change,
entry removal, broad log export or diagnostic script is required for this
check. Full Gold and independent privacy/security/architecture review remain
separate. The original production trigger remains unknown.
