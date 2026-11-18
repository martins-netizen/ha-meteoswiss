# 8.3.5b7 — Dated source and package evidence

**Evidence version:** 1.0 · **Recorded:** 18 November 2026

This record separates approved source, package validation, publication and
installed acceptance. Availability follows
[the release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
not preparation wording embedded in an immutable package. No b7 publication
or installation is claimed here.

## Approved source

[PR #129](https://github.com/martins-netizen/ha-meteoswiss/pull/129) was regularly
squashed and signed on **18 November 2026 at 15:14:08 UTC / 16:14:08 CET**:

| Identity | Verified value |
|---|---|
| Approved source head | `6eec5c38cfd51659a12ba583c90b2badce25eb4a` |
| Actual merge | `8887597ebf8567b5969ee70b8f9dd6f261603aec` |
| Actual tree | `1c624b207a9f0444e8a4625373a27a588e3f3535` |
| Sole parent / published b6 tag | `cc4f494694609af28fd27c46c475a8270d3858ab` |
| Fresh source-evidence snapshot SHA-256 | `75a353b92a09cd27f12d16fe48aac31b9228d28ff432abdf44a786232d5c8d17` |

The source-evidence fingerprint is the complete `check_quality_rules.py`
snapshot of runtime, tests, policies and documentation, not a runtime-only hash.

All **ten** trusted head checks and **nine** required actual-merge checks passed.
The actual development push workflows completed successfully at attempt one:
[CI 44333261771](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44333261771),
[HACS 44333261549](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44333261549)
and [CodeQL 44333261605](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44333261605).
The source merge retains the approved runtime/test tree; original candidates
#125–#128 were closed unmerged as replaced. Their separate head checks are
historical evidence, not substitutes for #129's completed merge checks.

Both actual source HA jobs, **2026.11.0** and **2026.11.2**, each passed
**3,510 tests plus 83 subtests**, in 184.59 and 100.89 seconds respectively.
Five known upstream deprecations remain; there were no ResourceWarning,
SQLite, thread or finalizer warnings. Strict coverage passed with
**4,801/4,802 statements**, **1,380/1,380 branches** and
**99.98382400517632%** combined coverage. The sole allowed missing statement is
the unused SSL-connector helper line in `const.py`; strict module gates remain.
Fresh evidence covers all **51 rules**: 26 automated verifications,
16 documented review judgments and nine reasoned exemptions. Native service
lifecycle and semantic metadata inventories are complete within their declared
scope. The [index](quality_rules.json), [matrix](QUALITY_SCALE.md) and
[evidence contract](GOLD_EVIDENCE_CONTRACT.md) retain exact mappings.

Both universal locks verified **138 selections**. The source advisory audit
checked **140 package/version pairs** with zero active, unknown or withdrawn
findings. These feed results do not refresh the dated owner-authenticated
security/settings inventory or certify external services.

## Prepared package and required checks

B7 packaging changes only two component version fields. The other **50 of 52**
component files must remain byte-identical to source #129 above; dependency
inputs/locks, workflow/check policy and `docs/quality_rules.json` remain
unchanged. All **29** historical publisher/profile/release-fixture paths and
historical release evidence remain immutable. New Publisher V1.14 and its independent refusal-path fixtures belong to this
package preparation. Their focused result and the package's complete native
counts must be recorded after final validation; source counts above are not
package results.

A package PR still needs its own approved exact head, successful required
checks, regular signed squash with the approved source as sole direct parent,
and successful trusted actual-merge workflows. This record does not invent a
package PR number, future merge SHA, successful run or publication receipt.
The immutable notes are [RELEASE_8.3.5b7.md](RELEASE_8.3.5b7.md).

## Publication preservation boundary

Fixed Publisher V1.14 must preserve all **22** earlier complete release records,
bodies and tag references, including published b6 release **449276745** at
`cc4f494694609af28fd27c46c475a8270d3858ab`, and latest stable **8.3.4** /
**437853341**. It must not overwrite or retag an existing release. B6 was
published on **17 November 2026 at 22:28:34 UTC / 23:28:34 CET** and has a
positive bounded normal-operation report. None of that publishes or accepts b7.
A later publication receipt must read back b7's exact tag, merge, prerelease
status and approved English body and confirm the older records remain intact.

## Installed acceptance and assurance limits

After publication and one normal existing-entry update, use the
[short read-only check](ACCEPTANCE_8.3.5b7.md). No installed b7 acceptance is
claimed in this preparation. Accepted b3 cleanup, b5 observed-day availability
and b6 bounded normal operation stay closed.

The completed source assessment is the project's engineering result through
Gold, not an official Home Assistant award or external privacy/security/
architecture certification. Provider retention, HA host/backup controls and
independent assurance remain [explicit boundaries](GOLD_SECURITY_BOUNDARIES.md).
