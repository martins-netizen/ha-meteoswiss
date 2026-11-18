# 8.3.5b7 — Gold privacy, state boundaries and quality evidence

**Notes version:** 1.0 · **Package scope:** 18 November 2026

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss product.

This test package prepares the approved source completion from
[PR #129](https://github.com/martins-netizen/ha-meteoswiss/pull/129).
Check [the release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability before selecting **8.3.5b7**. Preparing these notes does not
publish or install it. **8.3.4 remains latest stable**; the
[latest-stable page](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
remains the normal stable choice. Published b6 and earlier releases retain
their immutable contents and recorded acceptance.

## What changes

- **Smaller diagnostics downloads:** typed saved-configuration summaries omit
  unknown fields and redact location fields. Native tests include Home
  Assistant's outer repair-issue envelope. New retired-HGT notices omit
  redundant station statistic IDs; startup clears those placeholders from that
  exact existing notice before diagnostics registration. Creation/dismissal
  metadata, other notices and the exact cleanup confirmation targets remain.
- **Warnings follow their validity times:** an entity-owned local callback
  publishes changes when a retained warning becomes active or expires, even
  between provider polls. Inclusive end semantics and upcoming-warning handling
  remain. Removal cancels the callback and invalidates already queued work.
- **Forecasts follow the model hour and age limit:** the forecast weather state
  and its subscribers update at the next UTC hour or retained-snapshot expiry.
  They use the existing snapshot; no extra provider request or faster polling
  is introduced. Source failure and unload cancel the local callback.
- **Quieter optional-source transitions:** handwritten UV and station-catalogue
  outage/recovery messages use generic INFO text once per transition. Required
  coordinator failures retain the supported Core versions' native reporting.
- **Complete evidence through Gold:** the current assessment covers all
  **51 rules**: 20 Bronze, 10 Silver and 21 Gold. It distinguishes 26 automated
  verifications, 16 documented review judgments and nine reasoned exemptions,
  with fresh native JUnit/coverage and complete service/metadata inventories.

The [diagnostics boundary](DIAGNOSTICS_PRIVACY_BOUNDARY.md),
[warning clock](WARNING_STATE_CLOCK.md), [forecast clock](WEATHER_FORECAST_STATE_CLOCK.md),
[log levels](OUTAGE_LOG_LEVELS.md) and [Gold review](GOLD_COMPLETION_REVIEW.md)
record the exact behavior and limits. This is a project engineering assessment,
without an official Home Assistant tier, badge or independent security certification.
Provider retention, deployment controls and external assurance remain
[separate boundaries](GOLD_SECURITY_BOUNDARIES.md).

## Update the existing entry

Minimum Home Assistant remains **2026.11.0**; the current compatibility fixture
is **2026.11.2**. An installation already on 2026.11.2 needs no Core update for
this package. When b7 is published, update the existing entry normally and
complete its ordinary restart once. Keep station, settings, names, dashboards,
entity/statistic IDs and existing measured histories. Follow the
[short normal-update check](ACCEPTANCE_8.3.5b7.md).

B7 retains the measured-HGT recovery/ownership safeguards and bounded hourly
precipitation imports from b6. Completed b3 cleanup, b5 observed-day availability
and b6 normal-operation acceptance stay closed. No intermediate beta, station
change, entry removal, failure injection or repeated language exercise is
required. New upgrading users can still receive the existing explicit repair
for attributable obsolete HGT forecasts; the
[upgrade guide](UPGRADING_8.3.5.md) explains its separate consent boundary.

This package adds no host, credential, runtime dependency, provider request,
archive, automatic purge or wider deletion authority. Diagnostics sanitization
changes issue metadata only; it does not inspect Recorder or delete statistics.
The existing final-entry owned-HGT removal boundary remains. A usable protected
full backup, including Recorder and ownership storage, is the recovery point;
code rollback alone cannot restore deleted data.

## Source and packaging evidence

The approved source is signed #129 merge
`8887597ebf8567b5969ee70b8f9dd6f261603aec`, tree
`1c624b207a9f0444e8a4625373a27a588e3f3535`, with sole parent
`cc4f494694609af28fd27c46c475a8270d3858ab`.
All ten trusted source-head checks and nine actual-merge checks passed.
Both source compatibility jobs passed **3,510 tests plus 83 subtests**;
these are source results, not results for a future package merge.

Packaging changes only `manifest.json` and `version.py` within the component;
all **50 non-version files out of 52 component files** must match that source.
Dependency inputs/locks, the 51-rule index and workflow policy remain unchanged.
New fixed Publisher V1.14 checks the separately approved signed direct-parent
package merge and its actual checks, preserves all **22** earlier complete
release records/tags including b6 and latest stable 8.3.4, and refuses overwrite
or retagging. [Dated evidence](RELEASE_EVIDENCE_8.3.5b7.md) separates source,
package, publication and installed acceptance. A successful source review does
not silently complete the later steps.
