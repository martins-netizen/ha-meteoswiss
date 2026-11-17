# Bounded hourly precipitation imports

**Scope:** unreleased source hardening, reviewed 17 November 2026. This is
separate from the accepted HGT cleanup and ownership corrections. No operator
cleanup, station change or repeated installation is required to test this work.

## Why per-response limits were insufficient

STAC metadata was limited to 2 MiB, and each CSV already had fixed-host HTTPS,
redirect rejection, byte limits, a 30-second timeout and bounded retries.
However, metadata could still select many repeated archive URLs. A malformed
or compromised provider item could turn one small response into thousands of
sequential downloads. This is a reproduced resource-boundary finding, not a
claim of observed exploitation or a production incident.

The source now validates a three-letter station and supported period inputs
before I/O. Rejected optional precipitation configuration disables only that
family during entry setup, with one sanitized warning; the primary observation
refresh still performs its own required validation. This does not turn an
invalid primary source into a healthy one or start any rejected CSV request. An asset must bind its exact filename to its canonical HTTPS path
in that station's OGD directory. Credentials, queries, fragments, other paths,
stations and arbitrary same-host resources are not accepted. Direct CSV calls
enforce this boundary too; importer validation is not the only guard.

Historical filenames must identify aligned ten-year ranges relevant to the
lookback and may not start in a future UTC year. The current decade's end can
still be in the future: `2020-2029` is valid in 2026. Out-of-window/future assets
and unrelated filenames are ignored. A present, relevant canonical asset with
malformed record or missing/invalid href fails metadata validation, rather than being
silently omitted from an apparently successful import. Truly absent assets do
not prove how much history that station has published.

## Whole-plan and time bounds

The client and Recorder adapter both validate the complete plan before any CSV
download. URLs are deduplicated and at most **four unique CSV files** are
allowed. The production thirteen-calendar-month archive can intersect two
historical decades; `recent` and an optional combined `now` add at most one
file each. Ordinary hourly `now` polling remains a separate coordinator.
An oversized plan fails before downloading any CSV, without silently taking
the first four files. An unbounded full-station-history import is not supported;
a no-lookback internal call is still subject to the same four-file cap.
The thirteen-month window bounds archive import input; it does not delete older
recorded rows. This change introduces no new retention purge.

One monotonic **300-second deadline** covers metadata/retry/download waits and
awaited off-loop parsing. A new request or parser wait does not receive a fresh
five minutes. Existing per-attempt wire/decoded limits remain **64 MiB** for a
historical CSV and **16 MiB** for `now`/`recent`, with at most four transient
attempts per selected file. The metadata limit remains 2 MiB. There is no new
user setting, alternate host, transport bypass or persistent retry loop.

These are input and awaited-work limits, not a process-RSS ceiling or a promise
to stop a Python worker thread at an exact instant. A parser already running in
the executor can finish after timeout/cancellation; its late result is ignored
and cannot queue statistics. Final projection/queue acceptance of previously
completed valid files can occur after the source deadline. This is not a
Recorder transaction/commit deadline, nor rollback of previously queued writes.

## Failure, partial data and real zero

Clearly malformed non-CSV/HTML/JSON bodies or missing required CSV headers count
as file failures. A correctly headed CSV with no valid in-window rows can be
legitimately empty. Existing malformed-row filtering remains conservative.

Valid earlier files, including a real **0 mm**, survive a later download,
parsing failure or deadline expiry. Remaining files are not started after the
deadline. Results identify failed/unprocessed downloads and partial periods.
No valid completed values means a failed update with no empty Recorder write.
External cancellation propagates and queues no new result from that import.

`partial_import` and `imported_periods` describe known failures and whether each
requested period produced values. They do **not** certify that every expected
file, hour or historical observation exists. In particular, absent provider
assets, gaps, blank/malformed rows and a valid but empty in-window file cannot
be converted into invented missing-hour counts. `partial_import: false` is not an
independent completeness certificate.

The stable `meteoswiss:<station>_precipitation_hourly` ID, millimetres,
mean/min/max projection and declared historical → recent → now correction
order within one combined import remain. Independent hourly/archive pollers
retain their own schedules; this is not a global cross-poller ordering promise.
The provider's completed-hour end is still shifted back one hour for Recorder's
UTC start. Native queue acceptance remains distinct from database commit; the
existing repeat-import/correction tests retain that contract. No SQL writer,
purge, entity migration, new archive or additional observation storage is added.

## Evidence and remaining boundaries

A bounded public HTTPS read of the KLO STAC item on 17 November returned 6,193
bytes and seven canonical hourly assets: five decades from 1980-1989 through
2020-2029, `recent` and `now`. This verifies the sampled naming/path convention,
not every station's history, a provider-wide maximum or future availability.
The [official download guide](https://opendatadocs.meteoswiss.ch/general/download)
remains authoritative for source products. No private location, credential or
cookie is needed for this station-resource check.

Regressions cover large/repeated metadata, exact destination binding, invalid
inputs before I/O, whole-plan rejection, date boundaries, source/header errors,
deadline exhaustion, real zero, cancellation and late real-executor completion.
Native Recorder semantic tests retain interval, metadata and correction checks.
The exact local results belong to the reviewed PR candidate; hosted checks,
approved merge and any later package publication remain separate. This bounded
hardening is not an independent security or full Gold certification.
