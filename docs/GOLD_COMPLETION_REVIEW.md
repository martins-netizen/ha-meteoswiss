# Gold completion: prepared source review

**Baseline:** published 8.3.5b6 at
`cc4f494694609af28fd27c46c475a8270d3858ab`, reviewed 17 November 2026.
The runtime corrections below have disjoint source boundaries and were
validated separately and together. They are delivered with the evidence and
documentation in **one completion PR** against the current protected base.
This delivery route was reconciled on 18 November 2026: the strict GitHub
up-to-date rule makes the earlier parallel-head/exact-four-merge plan unsuitable
after its first squash merge. The successful heads of #125, #126, #127 and #128
remain candidate evidence; those PRs are superseded by this combined proposal,
without claiming that they were merged or closed. No protection is relaxed.
This completion adds no component version, package, tag, release or installed
acceptance.

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
guides retain their precise behavior and limitations. The four runtime changes
do not overlap; the shared changelog and current matrix are consolidated here.

## Native evidence and interpretation

Each runtime correction has its complete native suite on both supported HA
fixtures, **2026.11.0** and **2026.11.2**, including the existing strict coverage,
translation and installed-environment checks. The final combined source runs
the whole suite once per fixture with the [fresh evidence contract](GOLD_EVIDENCE_CONTRACT.md).
Required behavior references must actually run and pass. The index separates
automated evidence, documented human review and nine reasoned exemptions;
it cannot award a tier or certify a human judgment.

[The matrix](QUALITY_SCALE.md) covers all 20 Bronze, 10 Silver and 21 Gold
rules. Device classes/categories/defaults are checked against an independently
specified 45-entity base inventory and optional measured HGT. Existing native
names/icons/errors cover DE/EN/FR/IT. [Eight fixed-role cases](FIXED_SERVICE_TOPOLOGY.md)
cover both providers, optional recovery, complete Configure/Reconfigure
transactions, native entry retirement and shared handoff.

These are the actual rules. A production historical-orphan inventory, station
place-name aliases, a manual trigger of every failure or four fresh browser
language rounds are not additional requirements invented to defer closure.
Existing manual reports remain bounded and are not repurposed as new evidence.

## What remains separate

The combined completion PR must pass its own exact-head and actual-merge GitHub
checks. The earlier four candidate heads do not substitute for that combined
run, and no original candidate is to be merged as part of the superseded
parallel-head plan. The runtime and test bytes retain their complete native
validation; this delivery clarification is a documentation-only follow-up.
A matching code tree does not bypass normal approval. Closing the superseded
PRs is a separate explicit action after the replacement is ready.
Publication, installation and a focused operator report follow their own
authorized release workflow; a source PR does not claim that they occurred.
Published b3/b5/b6 acceptance is not reopened.

The project remains a **custom integration**, without an official Gold badge
or manifest tier. Platinum typing/dependency work and broad architecture
refactoring are separate from the applicable Gold checklist. Provider retention,
repository settings, HA host/network/backup controls and independent external
security assurance remain [explicit boundaries](GOLD_SECURITY_BOUNDARIES.md).
This review introduces no credential, endpoint, persistent archive, database
writer, automatic purge or expanded device-removal authority.
