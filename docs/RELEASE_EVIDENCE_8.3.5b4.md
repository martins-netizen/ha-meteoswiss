# 8.3.5b4: preparation and publication evidence

**Evidence version:** 1.0 · **Updated:** 15 November 2026

**Status: package preparation; not published, installed or operator-accepted.**
Stable 8.3.4 remains latest. Existing b3 acceptance remains complete.

## Reviewed source is actually merged and checked

[PR #115](https://github.com/martins-netizen/ha-meteoswiss/pull/115) was regularly
merged at `29d9bc73b2ad0dedc91c73cf167f46223330d22a`, tree
`92a5f77ab72d8476abde64b2c4b3185cd7a01684`, parent
`3f58d8ac9d60e792a2b01b9ced73e7bd39d0f192`. Public handle/noreply identity,
GitHub committer, valid signature and source-branch deletion are confirmed.
Ten exact-head checks and all nine actual merge checks passed. Actual
[CI 43753628495](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43753628495),
CodeQL 43753628485 and HACS 43753628480 are successful push runs on that merge.
Both HA 2026.11.0/2026.11.1 jobs passed 3,034 tests plus 83 subtests, five known
upstream warnings and no SQLite ResourceWarning. Strict coverage is 99.9831%;
all four new HGT modules have full line/branch coverage. Pinned Hassfest passed
with zero invalid integrations. Both universal locks verify 138 package
selections; 140 distinct package/version pairs have zero active/unknown
advisories. SonarCloud is successful.

## Prepared package boundary

All 50 non-version component files out of 52 match that exact source. Only two
component version fields become 8.3.5b4. Release notes, the short read-only
acceptance guide and active documentation are reconciled. Publisher V1.11 has
its own fixed source/version/52-file/19-old-tag profile and publication regressions;
all sixteen older publisher profiles remain separate and unchanged in scope.
Workflows, locks, HA minimum, runtime dependencies and existing gates stay fixed.

Complete local package suites on HA 2026.11.0 and 2026.11.1 each pass **3,092
tests plus 83 subtests**, with five known upstream warnings and no SQLite
ResourceWarning. Strict per-module/branch gates pass with 99.9831% combined
coverage and full line/branch coverage of the four HGT modules. Both installed
dependency/offline baselines, compilation and all four 251-key catalogues pass.
The package still needs ten exact-head GitHub checks, explicit packaging
approval, a regular guarded merge and actual merge verification. Publication requires the concrete approved merge, confirmed
prerelease/tag/body, all nineteen earlier release records/bodies/tags and latest
stable selection. A successful local simulation is not a real GitHub release.

## Published and installed state

No publication/installation claim is made here. Once performed, record the exact
packaging merge/tree/parent, trusted checks, release ID, tag/body/readback and
publication time. Then record the separate [focused measured-HGT result](ACCEPTANCE_8.3.5b4.md).
Do not reopen b3 forecast deletion, b1/b2 acceptance or PR #114 test-only checks.
