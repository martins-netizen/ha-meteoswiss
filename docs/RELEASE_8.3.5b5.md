# 8.3.5b5 — Measured HGT recovery test prerelease

**Notes version:** 1.1 · **Package date:** 16 November 2026 · **Updated:** 17 November 2026

Published as prerelease **447678651** from
`ba8a15aa282aa7b67d16c83cca6f99e38ee2bf4b` on 16 November 2026 at
22:08:42 UTC. Publication and the operator's focused observed-day availability
check are complete. See [the evidence and its limits](RELEASE_EVIDENCE_8.3.5b5.md).
The later [pending-import ownership correction](HGT_PENDING_IMPORT_OWNERSHIP.md)
is unreleased and is not included in this immutable package.

Publication and availability are determined by the release catalogue. Package
checks, publication, installation and live acceptance are separate evidence.
Stable 8.3.4 remains the normal stable choice.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## Recovery after a temporary HGT failure

8.3.5b5 packages the approved correction from
[PR #119](https://github.com/martins-netizen/ha-meteoswiss/pull/119).
After a temporary source or Recorder failure, the measured-HGT coordinator
retries through Home Assistant after **60 seconds**. Further failures increase
the delay to 120, 240, 480 and at most 900 seconds. A verified successful update
resets the delay and restores normal **six-hour** polling.

Published b4 can leave the latest-observed-day sensor unavailable until that
normal six-hour poll, even while its official statistics are already present.
The b5 correction shortens recovery; it does not establish the exact cause of
an earlier failure or manufacture a current value from existing rows.

Core owns one timer. Disabled entry polling and unload stop automatic retries.
Ownership or metadata conflicts retain their existing repair path and normal
interval. Source validation, native commit/readback and shared-station handling
remain unchanged. There is no new persistent retry state or replacement archive.
See [the recovery contract and limits](HGT_RETRY_RECOVERY.md).

## Existing users: update once, then read the measured sensor

Choose a published **8.3.5b5** test release in Marketplace and update the
existing integration normally. Keep its entry, station, names, entity IDs,
dashboards and owned statistics. Complete the normal integration-update restart
once; no additional restart is required just for the focused check.

On the weather-measurement station device, inspect **Heating degree days 12/20
last observed day** — German: **Heizgradtage 12/20 letzter Messtag**. This is
separate from forecast HGT. After source/Recorder verification succeeds it has
`statistics_status: ready`, a completed `source_day`, and a `statistic_ids` map
for the official daily, monthly and annual products. A zero can be a real
observation; unavailable or missing source data is not turned into zero.

Follow the [short b5 update and read-only check](ACCEPTANCE_8.3.5b5.md).
Do not press Set state, change state classes, recreate the entry, switch the
station, remove statistics or rerun obsolete cleanup to test recovery.
During an unsuccessful attempt the sensor remains unavailable; missing extra
attributes in that state are normal HA behaviour. Repeated source failures or
ownership conflicts are not a successful acceptance and remain visible.

The accepted **b3 obsolete-forecast cleanup stays complete**. Users upgrading
from earlier versions may still receive its existing explicit repair if old
forecast statistics are found. Read its deletion boundary and confirm only
when choosing permanent removal; b5 does not recreate those old forecasts.
See [the upgrade guide](UPGRADING_8.3.5.md) for all supported upgrade paths.

Official measured HGT remains separate station data in Recorder, with ongoing
source correction checks. Existing ownership/removal rules still apply:
removing the final integration entry permanently removes its owned OGD-HGT
statistics. A configured peer protects shared history; uncertain ownership
blocks deletion. Ordinary sensor history and unrelated series are retained.
Software rollback alone cannot undo database changes; a recovery point needs
a usable protected full HA backup containing Recorder and ownership storage.

## Reviewed source and package boundary

PR #119 was regularly squashed at
`6873c0390cb276dc6afa2c347d055e995d7bf956`, tree
`c3ad7191c52e8b62bb02c9dd2c3119949d1cd254`, direct parent
`a6a233513ac8e7c5937f9c41eee085e76108e801`. Public handle/noreply identity,
valid GitHub signature and source-branch deletion are confirmed. All ten
exact-head and nine actual merge checks passed. Actual
[CI 43872957431](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43872957431),
CodeQL 43872957350 and HACS 43872957758 ran on that merge. Both supported HA
jobs passed **3,101 tests plus 83 subtests**, five known upstream warnings,
and the strict coverage gates. The changed HGT module has full line/branch
coverage. The reviewed tree has 99.9831% combined coverage. Both universal
locks retain 138 selections; the complete audit checked 140 package/version
pairs with zero active/unknown/withdrawn findings. Hassfest reported no invalid
integration. SonarCloud passed.

The b5 package preserves all **50 non-version component files out of 52** from
that reviewed merge; only manifest.json and version.py advance to 8.3.5b5.
The two dependency locks, all workflows and existing validation gates remain
unchanged. The separate incomplete Dependabot #118 update is not included.
Package-specific head and actual merge checks remain required; the source
results above do not substitute for them.

Fixed **Publisher V1.12** targets this package only, with the full approved
package merge SHA. It checks the account, signed direct-parent merge, source
footprint, versions, policy, exact merge checks and release body. All twenty
older tag references and full release records, every older publisher, and
latest stable 8.3.4 are preserved. It creates a prerelease without marking it
latest and stops on changed or uncertain state. No HA installation is part of
publication. [Publication evidence and remaining steps](RELEASE_EVIDENCE_8.3.5b5.md).

**Home Assistant Core 2026.11.0 or newer is required.** Older Core releases pin
dependencies affected by published vulnerabilities; keep Core maintained.
The separately documented [Marketplace minimum-version display mismatch](MARKETPLACE_VERSION_DISPLAY.md)
does not change the package requirement. Check the selected package version.

No new account, runtime credential, coordinates, external endpoint, maintainer
telemetry or runtime dependency is introduced. Providers continue to receive
the existing public station identity and source IP. Full Gold and independent
privacy/security/architecture review remain open; this is a focused recovery
test package, not a general certification.
