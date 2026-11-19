# 8.3.5 — Dated promotion and package evidence

**Evidence version:** 1.0 · **Recorded:** 18 November 2026

This record separates published b7 source and bounded sight acceptance, the
prepared coordinator-placement/HGT-clock source corrections, and future stable packaging/
publication. The correction must complete normal source gates before a stable
publisher can be pinned to its actual approved merge. Use the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for available versions. No stable 8.3.5 publication is claimed here.

## Published and accepted source

[PR #130](https://github.com/martins-netizen/ha-meteoswiss/pull/130) was regularly
squashed and signed on **18 November 2026 at 18:01:51 UTC / 19:01:51 CET**.
The package subsequently became published **8.3.5b7**, release **450428545**,
on **18 November 2026 at 19:02:40 UTC / 20:02:40 CET**.

| Identity | Verified value |
|---|---|
| Approved b7 head | `7674fc94dcba77d1ae44ec93950b0f0913670b27` |
| Actual b7 merge and tag | `9ea96fc5a5306342eef0aa73ae50cc95bb844fb4` |
| Actual b7 tree | `d758a57c9a1bf6f88968ba454c641d0f973bdc16` |
| Sole parent / approved Gold source | `8887597ebf8567b5969ee70b8f9dd6f261603aec` |
| Full b7 source-evidence snapshot SHA-256 | `86b76e782d3009472fdc690e034f4f5c36412f49050fe90ad306fa54764e2de9` |
| Published English body SHA-256, 6,330 bytes | `411798d81ccf78d1c5014579b69b1d84db734617b3880b736f85da7c757708f6` |

All **ten** b7 head and **nine** actual-merge checks passed. The actual push
workflows completed on attempt one:
[CI 44365186056](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44365186056),
[HACS 44365186203](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44365186203)
and [CodeQL 44365186028](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44365186028).
Both actual HA jobs, **2026.11.0** and **2026.11.2**, each passed **3,609 tests
plus 83 subtests**, in **183.28** and **190.53** seconds respectively. Five known
upstream deprecations were visible; no resource/SQLite/thread/finalizer warning
was observed. Strict coverage covered **4,801/4,802 statements** and
**1,380/1,380 branches** across **43 modules**, **99.98382400517632%** combined.
Fresh evidence recorded all **51 rules**: 26 automated verifications, 16
review judgments and nine reasoned exemptions. The fingerprint binds runtime,
tests, policies and documentation, not only component code.

The later overall review found that the `common-modules` structural judgment
had missed the ninth actual coordinator definition outside `coordinator.py`.
The rule has no specialized-family exception. Those old native/index results
remain measured historical facts; they are not proof that the incomplete human
placement judgment was correct. The [canonical correction](COORDINATOR_CANONICAL_COMPLETION.md)
places the single actual HGT class beside the other eight and retains only an
explicit compatibility re-export in its old module. Its complete native/
structural checks and normal approved source merge are required separately.

Both universal locks verified **138** selections; the complete actual advisory
audit checked **140** package/version pairs with zero active, unknown or
withdrawn findings. These feed results do not refresh the separate dated
owner-authenticated settings inventory or external assurance.

Publication readback confirmed the exact b7 tag, English title/body,
`draft=false` and `prerelease=true`. All 22 previous full release records and
tags remained unchanged; stable **8.3.4 / 437853341** stayed latest. The frozen
[b7 preparation record](RELEASE_EVIDENCE_8.3.5b7.md) retains what was known when
its immutable package was prepared; the completed facts above are a later record.

After the normal b7 update/sight-check prompt, a positive focused operator sight
report was received. That bounded acceptance is complete. The reply did not
repeat the version number, and no independent installed-file inventory,
complete database audit, physical test or fresh four-language browser review
is inferred. Earlier b3 cleanup and b5/b6 reports remain closed too.

## Corrective source and future package boundary

The narrow source correction retains the b7 component version. It moves the
single actual measured-HGT coordinator definition into `coordinator.py`, leaves
its former path as a compatibility re-export, and reconciles current guides.
It also fixes calculated forecast HGT's registered-state lag across Swiss
midnight by publishing retained daily data through an entity-owned local clock.
This state-timing change has its own native regressions; existing HGT formula
and availability are retained, with no new provider request or source-age rule.
Existing component paths, native APIs, IDs, source/Recorder contracts and all
historical publisher profiles remain. Complete native checks, exact-head
checks, a normal approved source merge and actual-merge verification are still
required for that correction. No new operator migration or observation is
invented for these source corrections. The separately suspected nonpersistent
repair-placeholder leaks were refuted by actual Core serialization on both
supported fixtures; no privacy/repair-UI change is part of this correction.

Only after that actual source merge can stable **8.3.5** packaging be frozen.
At the later packaging step, `manifest.json` and `version.py` change version;
all **50** other component files must match the newly approved corrective
source, not blindly match old b7. Dependency inputs/locks, workflow gates and
the then-approved exact rule index remain protected. All **31** historical
publication-profile paths and b1–b7 evidence stay immutable.

Stable Publisher **V1.8** and its new refusal-path fixtures are planned for that
later package. They are not publication-ready or part of the present source
correction merely because a work-in-progress file exists. They must be pinned
to the verified actual corrective merge and validated again before delivery.

This record does not invent a future corrective/stable PR number, approved
source SHA, package count, successful run or publication receipt. Exact final
source/package results belong in their own PR/run receipts after validation;
old b7 counts are not projected onto them.

## Stable publication transition

The fixed publisher must retain all **23** older full release records and tag
references, including b7 **450428545** and stable 8.3.4 **437853341**. Before a new
publication, latest stable must still be that reviewed 8.3.4. Only the exact
approved 8.3.5 stable release may replace it afterward, with `draft=false`,
`prerelease=false`, `make_latest=true` and the exact English
[release notes](RELEASE_8.3.5.md). A matching already published release is a
read-only verification case; no old body or tag is overwritten. An uncertain
write must be read back before another publication attempt.

## Existing acceptance and remaining scope

The accepted b7 sight scope is not reopened by the source
correction or later stable packaging; no new migration or operator observation
window is required for these source changes; native regressions cover the new
HGT clock. A user who chooses
the stable label can update normally when it is published, completing its
ordinary update restart once. New upgrading users follow the
[stable update guide](ACCEPTANCE_8.3.5.md) and explicit repair consent where
attributable obsolete forecasts are found. Earlier acceptance is not reopened.

The assessment through Gold is a project engineering result, with the newly
identified canonical placement and HGT-clock corrections explicitly gated before closure;
there is no official HA tier or independent certification. Provider
retention, HA deployment controls and broader assurance retain their
[separate boundaries](GOLD_SECURITY_BOUNDARIES.md).
