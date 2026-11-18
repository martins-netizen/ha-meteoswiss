# Gold completion: approved source and b7 package boundary

**Approved source:** [PR #129](https://github.com/martins-netizen/ha-meteoswiss/pull/129),
signed merge `8887597ebf8567b5969ee70b8f9dd6f261603aec`, 18 November 2026.
Its sole parent is published b6 at
`cc4f494694609af28fd27c46c475a8270d3858ab`. The disjoint runtime corrections
below and their evidence/documentation passed both source-head and actual-merge
checks together. **8.3.5b7 prepares this approved source as a test package**;
its package validation, publication and installed acceptance are separate.

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
**1,380/1,380 branches**. [The dated b7 source record](RELEASE_EVIDENCE_8.3.5b7.md)
provides the exact commits, runs and remaining package gates. These source
counts are not projected onto a future b7 package merge.

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

Source integration and its required head/merge checks are complete. B7 changes
only two component version fields; all 50 non-version component files must
match the approved source. Package preparation adds its own fixed publisher,
independent refusal-path fixtures and current documentation. It retains the
rule index, dependency locks and every existing workflow/check gate. A matching
runtime tree does not bypass normal package approval or its own exact-head and
actual-merge checks.

Publication and a normal existing-entry update follow their authorized release
workflow. Use the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability and [the short b7 protocol](ACCEPTANCE_8.3.5b7.md) after
publication. Neither source completion nor these notes claim b7 is published,
installed or accepted. Accepted b3 cleanup, b5 availability and b6 bounded
normal operation stay closed; no repeated migration or destructive test is
required.

The project remains a **custom integration**, without an official Gold badge
or manifest tier. Platinum typing/dependency work and broad architecture
refactoring are separate from the applicable Gold checklist. Provider retention,
repository settings, HA host/network/backup controls and independent external
security assurance remain [explicit boundaries](GOLD_SECURITY_BOUNDARIES.md).
This review introduces no credential, endpoint, persistent archive, database
writer, automatic purge or expanded device-removal authority.
