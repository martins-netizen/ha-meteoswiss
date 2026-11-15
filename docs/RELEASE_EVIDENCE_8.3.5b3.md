# 8.3.5b3: publication and focused cleanup acceptance

**Evidence version:** 1.0 · **Updated:** 15 November 2026

[Release 446112927](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b3)
was published on **15 November at 14:19:50 UTC**, immutable,
`draft=false`, `prerelease=true`. Regular packaging
[PR #113](https://github.com/martins-netizen/ha-meteoswiss/pull/113) was merged
at 14:16:36 UTC as `b6c4502e5cdeb48121be628fdb7eda579df4f7c3`, tree
`bb8c9de9a3822d56eac6f49892852d3cede298df`, parent
`9d7be4f935e751314bb950c70869bf09b143a6b1`. The reviewed head was
`093c524083482c21b0b8ef800521d59e691c4c08`.

Independent API reads confirmed the exact prepared tree, public handle/noreply
author, GitHub committer, valid merge signature and deleted package branch.
All ten trusted head checks and all nine actual merge checks succeeded.
[Actual CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43723462913)
passed 2,900 tests + 83 subtests on each HA 2026.11.0/2026.11.1 and every
strict step. Pinned Hassfest passed; the advisory audit checked 140 versions
with zero active advisories and zero unknown results. Both hosted suites had
six warnings, including the separately tracked SQLite test-cleanup warning.

All 46 non-version component files out of 48 match accepted PR #112 source;
only manifest.json/version.py become b3. Workflows, universal locks and
security/coverage gates are unchanged. The exact approved English release
body, all eighteen previous release records/bodies/tags and latest stable
8.3.4 / ID 437853341 were independently confirmed. Original operator receipts
were retained. Publication and its publisher are complete, not a new action.

## Operator acceptance

On 15 November the operator explicitly confirmed the immediately preceding
focused sequence successful: existing-entry update to b3, native confirmed
removal of the listed obsolete HGT forecasts, repair and listed old statistic
IDs gone, and the running forecast showing `ready`, no archive reference and
cleanup-required false. Normal forecast operation/ordinary history were
retained. This closes the agreed [focused acceptance](ACCEPTANCE_8.3.5b3.md);
do not repeat installation, deletion or earlier b1/b2 acceptance.

This is operator/visible acceptance, not a newly ingested all-row Recorder or
all-file installation audit. Native cascading/ownership tests retain their
separate evidence; already unattributable historical orphan rows cannot be
ruled out for all HA from this report. Publication itself performed no HA write.
Immutable release notes/body remain unchanged. The [test-only lifecycle
follow-up](TEST_RECORDER_LIFECYCLE.md), official measured OGD HGT import,
independent review, remaining Gold rules and any stable promotion are separate.
