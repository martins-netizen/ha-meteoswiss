# 8.3.5b6 — Dated source and package evidence

**Evidence version:** 1.0 · **Recorded:** 17 November 2026

This record describes the evidence available during b6 preparation. Publication
and current availability are determined by [the release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
not by a preparation record embedded in an immutable tag. Source, package,
publication and installed acceptance are separate steps.

## Source

Approved PR #121 merged at `b936505d348c199717c00b3211def7fa6b3013c1`.
All ten head and nine actual-merge checks passed; native pending-write/lifecycle
regressions cover HGT ownership. Approved CI PR #122 merged at
`1439b83c8dedde1a89f62fcc4c0fd689f1b6baa6`; all ten observed actual checks passed.
Its native HA 2026.11.0/2026.11.2 jobs passed 3,180 tests plus 83 subtests each.

PR #123 was regularly squashed at **21:30:57 UTC / 22:30:57 CET** on
17 November 2026 at `8e6dc429e54f2973ac120601fc5134f882c535d9`.
Its tree `fc8c1f98e80ecffcac35fd02ee3c62a0f2cc9888` matches the reviewed
head `2a2e96ffb4af34594d440a14caa754ccc147d1c8`; its sole parent is the
#122 merge above. Public handle/noreply identity, valid GitHub signature and
source-branch deletion are verified. All ten trusted head checks passed.
All nine required actual-merge checks passed. Actual
[CI 44180613701](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44180613701),
HACS 44180613702 and CodeQL 44180613797 completed successfully at attempt one.
The two actual native jobs each passed **3,291 tests plus 83 subtests**, with
the five existing upstream deprecations and no SQLite/thread/finalizer warning.
The actual merge retains **99.98346560846561%** strict coverage, with all four
HGT modules and the three changed runtime modules fully covered. Its lock job
verified 138 universal selections per fixture; the advisory audit checked 140
package/version pairs with zero active, unknown or withdrawn findings. Hassfest
reported no invalid integration.

The source candidate passed **3,291 tests plus 83 subtests** per local fixture
on Python 3.14.10, HA 2026.11.0/2026.11.2. Five known upstream deprecations
remain; no SQLite, thread or finalizer warning was observed. Strict coverage
passes at **99.98346560846561%**, with all three changed runtime modules and
all four HGT modules fully covered. Focused source/setup/resource contracts
pass 250 tests per fixture. These are source results, not package results.

## Package and publication boundary

B6 packaging changes two version fields within 52 component files; all other
50 must match the actual source above. It retains dependency inputs/locks,
workflow policy and all historical publishers and test profiles. New Publisher
V1.13 and **88 passing independent native fixture tests** cover its b6 policy
and refusal paths; all 27 historical publisher/profile/fixture paths remain
byte-identical. These focused results do not replace the package's complete
compatibility and actual-merge gates.
It requires a separately approved signed direct-parent package merge and its
own successful actual checks before publication.

The fixed publisher preserves all **21** previous full release records and
tags, including b5 release **447678651** at
`ba8a15aa282aa7b67d16c83cca6f99e38ee2bf4b`, and latest stable **8.3.4** /
**437853341**. It does not overwrite an existing tag/release. Old b5 notes,
publication evidence and focused availability acceptance remain historical facts.

## Installed acceptance and remaining assurance

No installed b6 operation is inferred from this preparation. Use
[the short read-only protocol](ACCEPTANCE_8.3.5b6.md) after publication and a
normal update. Accepted b3 cleanup and b5 availability are not reopened.
Full Gold and independent privacy/security/architecture assurance remain
unestablished; [the bounded assessment](PRIVACY_SECURITY_REVIEW.md) stays authoritative.
