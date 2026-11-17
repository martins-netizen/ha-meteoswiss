# 8.3.5b6 — HGT ownership and bounded precipitation imports

**Notes version:** 1.0 · **Package scope:** 17 November 2026

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss product.

This test prerelease combines the HGT ownership correction from
[PR #121](https://github.com/martins-netizen/ha-meteoswiss/pull/121) and the
precipitation source/import correction from
[PR #123](https://github.com/martins-netizen/ha-meteoswiss/pull/123).
Use [the release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability and [latest stable](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
for the normal stable choice. Published b5 remains an immutable earlier test
package.

## What changes

- **HGT ownership:** station retirement waits for pending native Recorder writes
  before treating empty metadata as absence. Cancellation cannot prematurely
  discard the provenance needed for later confirmed removal. Uncertainty keeps
  ownership and its existing blocked notice. This prevents a narrowly reproduced
  race; it does not reclaim already-unowned history or prove a production incident.
- **Hourly precipitation:** canonical station/period destinations, deduplication
  and at most four CSVs are validated before downloading the plan. One
  300-second budget covers awaited source/parser work. Invalid relevant assets
  or CSV schemas retain their failure status; valid preceding files and real
  zero remain usable. A cancelled/expired parser cannot queue a late import.
- **Compatibility:** minimum Core remains **2026.11.0**; current CI uses
  **2026.11.2**. Existing entries, entity/statistic IDs, units, polling and the
  b5 bounded HGT retry schedule remain. No new archive or cleanup is introduced.

The precipitation deadline does not forcibly stop a running thread, cap total
memory or add a Recorder commit/readback/rollback guarantee. Queue acceptance
retains its existing meaning. Partial status is period-level, not proof that
every historical hour exists; the thirteen-month lookback does not purge old
Recorder rows. See [the full resource contract](PRECIPITATION_RESOURCE_BOUNDS.md).

## Update the existing entry

When b6 is available, update normally, completing the update's ordinary restart
once. Keep the configured station, entry, names, dashboards and statistics.
An installation on Core 2026.11.2 already meets the minimum. Follow
[the short read-only check](ACCEPTANCE_8.3.5b6.md): measured HGT, existing
hourly precipitation statistics and normal weather/forecast operation.
No intermediate beta, station switch, entry deletion, manual Set state or
repeated obsolete-forecast cleanup is required.

Completed b3 cleanup and b5 measured-HGT availability acceptance stay closed.
Users upgrading from older versions can still receive the existing explicit
repair for attributable obsolete forecasts; read [the upgrade guide](UPGRADING_8.3.5.md)
before confirming permanent deletion. Removing the final integration entry has
the existing owned-HGT deletion boundary. Code rollback alone cannot undo
database changes; a usable protected full backup is the recovery point.

## Source and packaging evidence

The package source is the actual approved #123 merge
`8e6dc429e54f2973ac120601fc5134f882c535d9`, tree
`fc8c1f98e80ecffcac35fd02ee3c62a0f2cc9888`, direct parent
`1439b83c8dedde1a89f62fcc4c0fd689f1b6baa6`.
Packaging changes only `manifest.json` and `version.py` within the component;
all **50 non-version component files** are retained from this source, not from
b5. Dependency locks, workflow policy and old publishers remain unchanged.
Fixed Publisher V1.13 checks the approved signed direct-parent package merge,
trusted actual checks, preservation of all 21 older releases/tags and latest
stable 8.3.4. It cannot overwrite or retag an existing release.

[Dated evidence](RELEASE_EVIDENCE_8.3.5b6.md) distinguishes source checks,
package checks, publication and installed acceptance. None independently
establishes full Gold or external privacy/security/architecture assurance.
