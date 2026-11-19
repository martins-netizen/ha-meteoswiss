# 8.3.5 — Dated promotion and package evidence

**Evidence version:** 1.1 · **Updated:** 19 November 2026

This record separates published b7 and its bounded sight acceptance, the
completed pre-stable corrective source, and the prepared stable package.
Source #131 is approved, signed and fully checked. Stable package approval,
its actual-merge checks and authorized publication remain separate. Use the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for available versions; preparation is not a publication receipt.

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
explicit compatibility re-export in its old module. Approved #131 and the
separate actual source validation below close that implementation gap.

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

## Completed corrective source — 19 November 2026

[PR #131](https://github.com/martins-netizen/ha-meteoswiss/pull/131) was regularly
approved, squashed and signed on **19 November 2026 at 06:07:36 UTC / 07:07:36 CET**.
The former feature branch was removed. Its actual tree matches the reviewed
candidate exactly; public Git identities, message/body and all **57** changed
paths and blob hashes were independently checked before merge.

| Identity | Verified value |
|---|---|
| Approved corrective head | `63a1723a4149ff9ee8242fae1635f12623bd69b4` |
| Actual corrective merge / stable source | `115ddad474dcae15aa49fb5f368cbed600adf80d` |
| Exact corrective tree | `98fbd1b49500503c2994292957674f0ac00a1aa6` |
| Sole parent / preserved b7 | `9ea96fc5a5306342eef0aa73ae50cc95bb844fb4` |
| Fresh corrective source-evidence SHA-256 | `05ee7d7d0a3236c12c99014bf18d448bfa4aa8c0d7bcd8f607fc761408c4c196` |

All **ten** trusted exact-head and **nine** actual-merge checks passed. The
actual development push workflows completed on attempt one:
[CI 44469898473](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44469898473),
[HACS 44469898678](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44469898678)
and [CodeQL 44469898516](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44469898516).
SonarCloud passed too. No failed legacy commit status or unresolved review
thread remained, and the active strict squash ruleset retained no bypass actor.

Actual HA **2026.11.0** job **135376528998** passed **3,622 tests plus 83 subtests**
in **139.46 seconds**; actual HA **2026.11.2** job **135376529354** passed the same
count in **178.67 seconds**. Each retained the five known upstream deprecations.
Strict coverage passed with **4,834/4,835 statements**, **1,386/1,386 branches**
and **43 modules**. Both fresh evidence results bound the source fingerprint
above and all **51 rules**: 26 automated verifications, 16 documented reviews
and nine reasoned exemptions. Actual advisory job **135376529358** checked
**140** package/version pairs with **0 active, 0 unknown and 0 withdrawn**
findings. This is not a new owner-only alert/settings inventory.

The correction keeps component version **8.3.5b7**. It moves the single actual
measured-HGT coordinator to `coordinator.py`, leaving its former module as an
explicit compatibility re-export. It also publishes calculated forecast HGT's
new Swiss day through an entity-owned local callback, closing the registered-
state lag until the next hourly poll. Native regressions cover actual HA states,
23-/25-hour days, disabled polling, source failure/recovery and invalidated queued
callbacks after removal. A clean run against the unchanged b7 source reproduces
the old cached 15.0 value when the new day requires 11.0.

HGT formula, availability, identifiers, measured source/Recorder contracts and
explicit cleanup consent remain. No provider request or new source-age rule is
added. The separate suspected nonpersistent repair-placeholder leaks were
refuted by real Core serialization on both supported fixtures; no privacy/
repair-UI change was needed for that suspicion. The actual source review also
reconciled 51 current Markdown files; 131 source documents and 1,138 local links/
anchors were checked without a broken target. Historical evidence stayed intact.

## Prepared stable package boundary

Stable **8.3.5** is prepared on that actual approved corrective source. Only
`manifest.json` and `version.py` change component version; all **50** other
component files match source `115ddad474dcae15aa49fb5f368cbed600adf80d`.
Dependency inputs/locks, workflows, 20 protected policy files including the
exact rule index, and all **31** historical publication-profile paths remain.
The b1–b7 release/acceptance/evidence files stay immutable.

Fixed [Stable Publisher V1.9](../scripts/publish_meteoswiss_835_stable_v1.9.sh)
and its [refusal-path tests](../tests/test_release_835_stable_publisher.py) belong
to this package preparation. Its focused **139-case** suite passed on each
supported native fixture. The earlier unpublished V1.8 preparation remained
parked with the old source pin; it is not the operative publisher.

The complete stable package receives its own full native validation, exact-head
checks, normal approved signed package merge and actual-merge verification.
Those results belong to its final PR/run receipts; the **3,622** source tests
above are not projected onto the package. This record invents no package PR
number, future package merge SHA or publication receipt.

At the **19 November preparation check**, all **23** previous full release
records and **23** raw tag refs matched the preserved snapshots; stable
**8.3.4 / 437853341** was still latest and stable 8.3.5 was absent. Source and
package preparation do not alter those existing public records.

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

The assessment through Gold is a project engineering result on the corrected,
reviewed and verified #131 source; stable package/publication stages remain
separate. There is no official HA tier or independent certification. Provider
retention, HA deployment controls and broader assurance retain their
[separate boundaries](GOLD_SECURITY_BOUNDARIES.md).
