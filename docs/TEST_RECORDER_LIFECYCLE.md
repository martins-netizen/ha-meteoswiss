# Native test Recorder lifecycle

**Evidence version:** 1.1 · **Updated:** 15 November 2026

The b2/b3 hosted suites intermittently reported an unclosed SQLite connection
from the HA fixture's later `gc.collect()`, commonly labelled with the first
Retry test. The historical logs do not contain its allocation frame; the label
alone is not an allocation diagnosis or a production-failure claim.

An isolated full run of unchanged published b3 with observational SQLite audit
and SQLAlchemy close events completed 2,900 tests + 83 subtests. It recorded
23 native connection creations and 21 explicit closes. After pool disposal in
the native wind migration test, DB-worker statistics-issue refreshes opened
two further connections. That run itself had only five upstream warnings:
the intermittent warning is not asserted to reproduce on every run. Audit
records retain identities as integers/strings, never owning the connections.

## Test-only correction and regression

The repository wraps the original native `recorder_mock` fixture. Before its
underlying fixture shuts down Recorder, it drains tracked HA background work,
waits for the native Recorder queue barrier, then drains resulting callbacks.
It leaves the original fixture's startup, shutdown and database disposal intact.
A surrounding thread-safe SQLAlchemy event guard requires one explicit pool
close for every opened connection after native teardown and removes its
listeners. No connection is forcibly closed by the guard; a mismatch fails.

The native regression leaves a short queued background database read to the
fixture. A teardown probe requires the real read to finish before `Engine.dispose`
and checks its result. With the earlier yield-only order the probe failed
(`observed [False]`, one teardown error); with draining it passes on both HA
versions. This proves the ordering defect and prevents a green test body from
hiding incomplete database work. The explicit close guard covers the existing
native history, HGT, wind, precipitation, lifecycle and handoff tests as well.

The affected native-test rerun plus the new regression passed 424 tests and
recorded 22 connections with 22 explicit closes. Complete suites on both HA
2026.11.0 and 2026.11.1 passed 2,901 tests + 83 subtests, five existing upstream
warnings, no SQLite ResourceWarning and the unchanged strict 99.98% coverage
gate. PR #114 was regularly merged at
`3f58d8ac9d60e792a2b01b9ced73e7bd39d0f192` on 15 November 2026.
All ten head and nine actual merge checks passed. Actual CI run
[43734809920](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43734809920)
confirmed the same 2,901 tests plus 83 subtests on both HA versions, only five
known upstream warnings and no SQLite ResourceWarning. Pinned Hassfest, audit,
CodeQL and HACS checks passed; the audit found zero active/unknown advisories
across 140 distinct locked package versions.

No `gc.collect()` timing workaround, warning suppression, direct close of user
data, fixture downgrade, lock override or weaker gate is introduced. All 48
component files, versions, published releases/tags and workflows remain unchanged.
The successful hosted checks are scoped to this test-only follow-up, not the
subsequent measured-HGT runtime feature. They are not
proof about every historical warning allocation. The already accepted b3 HA
update/cleanup stays closed; a test-only follow-up requires no production update.
