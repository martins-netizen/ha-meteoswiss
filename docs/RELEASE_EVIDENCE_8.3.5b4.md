# 8.3.5b4: publication evidence and focused acceptance

**Evidence version:** 1.1 · **Updated:** 15 November 2026

**Status: published and independently verified; focused HA acceptance pending.**

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
restart HA. The [focused measured-HGT acceptance](ACCEPTANCE_8.3.5b4.md) remains
pending; accepted b1/b2/b3 scopes and PR #114 stay closed.

## Source, identity and package integrity

Source PR #115 is regularly merged at
`29d9bc73b2ad0dedc91c73cf167f46223330d22a`; its ten head and nine actual merge
checks were successful. Both source jobs passed 3,034 tests plus 83 subtests.
The b4 packaging merge has the exact prepared tree, single reviewed parent,
public handle/noreply author, GitHub committer and valid GitHub signature.
GitHub removed its source branch. All 50 non-version component files are
unchanged; only manifest.json/version.py advance from b3 to b4. Workflows,
dependency locks, Core 2026.11.0 minimum and every existing gate are retained.

The fixed V1.11 publisher bytes in the signed merge match the independently
tested profile. The bound Mac publication wrapper passed 49 local guard/resume
scenarios. The real returned publication receipt reports `published_and_verified`,
no repeated merge, all nineteen old release records/tag refs retained, and no
HA access, installation, restart or device call. Fresh authenticated GitHub
readback independently confirms release ID 446375287, its exact target commit,
published prerelease flags, public author and English body. Body SHA-256:
`66ea1274b447897bc41b28205a7bfc431ed69d97bdb29835236d80d77bd051b3`.
Stable 8.3.4 remains latest; b4 does not request stable promotion.

## Remaining installed-source evidence

The new official HGT importer is in b4, not in b3. No b4 installation or runtime
success is inferred from publication. Update the existing entry normally and
use the [short read-only protocol](ACCEPTANCE_8.3.5b4.md). First source backfill
and Recorder verification must finish before reporting the observed-day sensor
ready. A successful first snapshot does not manually prove all future source
corrections. Do not recreate old forecast data, switch stations, remove entries
or repeat the accepted b3 deletion merely to test this package.

The immutable tagged README retains its preparation wording. This current
evidence and the release catalogue record publication; later development
documentation does not change that installed-tag snapshot. The separately
documented Marketplace minimum-version display mismatch is also not an HA-Core
fix. Full Gold and independent security/privacy/architecture review remain open.
