# Gold completion: reviewed source and separate stable promotion

**Review update, 19 November 2026:** approved signed
[PR #131](https://github.com/martins-netizen/ha-meteoswiss/pull/131) at
`115ddad474dcae15aa49fb5f368cbed600adf80d` is the stable promotion baseline.
Its exact tree is `98fbd1b49500503c2994292957674f0ac00a1aa6`, with sole parent
published b7 `9ea96fc5a5306342eef0aa73ae50cc95bb844fb4`. All ten trusted head
and nine actual-merge checks passed. Both actual supported Core jobs passed
**3,622 tests plus 83 subtests**, five known upstream warnings and strict
coverage gates. [Dated evidence](RELEASE_EVIDENCE_8.3.5.md) records source,
package and publication stages separately.

The overall pre-stable review found that the earlier common-modules judgment
had missed the ninth real HGT coordinator outside `coordinator.py`. No exception
applied. [The completed correction](COORDINATOR_CANONICAL_COMPLETION.md) places
the single actual class beside the other eight and keeps the former module as
an explicit re-export. Structural inventory, aliased-import refusal cases and
native logger/interval/ownership contracts cover that gap. The same source
fixes calculated forecast HGT's registered-state lag at Swiss midnight, with
native 23-/25-hour, disabled-polling, recovery and timer-removal evidence.
Formula, availability, IDs and source/Recorder boundaries remain.

B7's successful measured checks, publication and bounded positive sight report
remain valid in their own scope. They did not prove the missed placement
judgment and are not relabeled as later stable package acceptance.

## Delivery preparation — historical record

The original review on **17 November 2026** used published b6 at
`cc4f494694609af28fd27c46c475a8270d3858ab` as its baseline. Four disjoint
runtime candidates and an evidence/documentation change were validated
separately and together. At that preparation stage, their individual head
checks did not establish an integrated merge, package or installed acceptance.
The delivery route was reconciled on **18 November 2026**: the strict
up-to-date rule made the earlier parallel-head/exact-four-merge plan
unsuitable after its first squash merge. One regular completion PR preserved
that rule and all required checks. Original #125–#128 were closed unmerged as
replaced after #129's actual checks passed. Their successful candidate heads
remain historical evidence, not four unperformed merges or a second delivery
plan. Source completion itself created no component version or release.

## Necessary changes

| Change | Reproduced gap or missing evidence | Resulting contract |
|---|---|---|
| Diagnostic privacy | HA serializes persistent domain issues before invoking the callback; a redundant retired-station list escaped callback redaction. Unknown saved config fields also survived the old denylist. | Typed allowlist, minimal new notices and exact metadata-only startup cleanup before diagnostics registration. Native HTTP tests cover persisted, cross-entry, unloaded and disabled cases; exact deletion targets remain in the confirmation form. |
| Warning state clock | The registered state remained off after a warning became valid, until the next source update. Property-only checks missed it. | One entity-owned next-validity callback publishes registered state and attributes, cancels on removal and rejects queued old callbacks. Inclusive end semantics and outlook handling remain. |
| Forecast state clock | The named weather entity retained the previous model hour until its phase-shifted network poll. | One next UTC-hour/snapshot-expiry callback updates current state and forecast subscribers from the retained snapshot; source failure and unload cancel it. |
| Outage log levels | Two handwritten unavailable messages used WARNING rather than the current INFO contract. | One INFO message per optional UV/catalogue outage and recovery; retries, privacy and cached values remain. Core coordinator logging on the supported fixtures is delegated unchanged. |
| Complete evidence | The old matrix retained partial lifecycle/metadata judgments and had no current-run mapping to every rule. | Native fixed-role and full semantic metadata inventories, exact 51-rule index, fresh JUnit/coverage verification and reconciled current guides. |

The [privacy](DIAGNOSTICS_PRIVACY_BOUNDARY.md), [warning](WARNING_STATE_CLOCK.md),
[forecast](WEATHER_FORECAST_STATE_CLOCK.md) and [logging](OUTAGE_LOG_LEVELS.md)
guides retain precise behavior and limitations. The four runtime changes do
not overlap; the shared changelog and current matrix are consolidated here.

## Native evidence and interpretation

All **ten** trusted source-head and **nine** actual-merge checks passed. Three
actual development push workflows succeeded at attempt one. Both actual native
HA **2026.11.0** and **2026.11.2** jobs each passed **3,510 tests plus 83
subtests**, with five known upstream deprecations and no ResourceWarning,
SQLite, thread or finalizer warnings. Strict coverage passed at
**99.98382400517632%** combined: **4,801/4,802 statements** and
**1,380/1,380 branches**. [The dated #129 source record](RELEASE_EVIDENCE_8.3.5b7.md)
preserves these earlier metrics; [the dated record](RELEASE_EVIDENCE_8.3.5.md)
adds the completed b7 result and remaining stable gates. These #129 source
counts are not projected onto the separately recorded b7 or stable package results.

Both existing compatibility jobs consume fresh JUnit and coverage from their
single full run through the [evidence contract](GOLD_EVIDENCE_CONTRACT.md).
Required behavior references actually ran and passed. [The matrix](QUALITY_SCALE.md)
covers all **51 rules**: 20 Bronze, 10 Silver and 21 Gold. The index distinguishes
**26 automated verifications**, **16 documented review judgments** and **nine
reasoned exemptions**. Automation validates fresh evidence and references;
it does not award a tier or replace human judgment.

Device classes/categories/defaults are checked against an independently
specified 45-entity base inventory and optional measured HGT. Existing native
names/icons/errors cover DE/EN/FR/IT. [Eight fixed-role cases](FIXED_SERVICE_TOPOLOGY.md)
cover both providers, optional recovery, complete Configure/Reconfigure
transactions, native entry retirement and shared handoff.

A production historical-orphan inventory, station place-name aliases, manual
triggering of every failure or four fresh browser language rounds are not
additional Gold prerequisites. Existing operator reports retain their narrower
observed scope and are not repurposed as later package acceptance.

## What remains separate

B7's required checks, publication and bounded operator sight report remain
complete. Canonical coordinator placement and calculated-HGT midnight state
publication are completed in approved #131, retaining version 8.3.5b7 until
packaging. The prepared stable promotion changes only two component version
fields relative to that actual source, retaining its other 50 component files.
Fixed Publisher V1.9 verifies that source boundary and preserves all old
profiles, release records and tags. Package review, trusted head checks, normal
signed package merge, actual-merge verification and authorized publication
remain distinct stages. A matching runtime tree does not bypass these gates.

Stable publication follows its separately authorized workflow. Use the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability and [the stable guide](ACCEPTANCE_8.3.5.md) for an ordinary
package update. An already accepted b7 runtime needs no repeat installation,
migration, failure exercise or observation window solely for promotion.
Accepted b3 cleanup and b5/b6/b7 reports stay closed.

The project remains a **custom integration**, without an official Gold badge
or manifest tier. Platinum typing/dependency work and broad architecture
refactoring are separate from the applicable Gold checklist. Provider retention,
repository settings, HA host/network/backup controls and independent external
security assurance remain [explicit boundaries](GOLD_SECURITY_BOUNDARIES.md).
This review introduces no credential, endpoint, persistent archive, database
writer, automatic purge or expanded device-removal authority.
