# 8.3.6b1 source and package record

| Item | Reviewed value |
|---|---|
| Published stable baseline | [8.3.5](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5), release 450993306, tag commit `cc158cbdce07f015952275fba72e3c0160c63c80` |
| Last source PR | [#147](https://github.com/martins-netizen/ha-meteoswiss/pull/147), approved head `8e9ffb1199ffa777739d3010c55027045945ed82` |
| Signed source merge | `f9abaa12018fb89fd6c31633eadf6a975019d596`, 19 November 2026 at 23:16:50 UTC |
| Source Git tree | `e958573cbae9bd8b5685a627645f9ff1477c73f8` |
| Sole parent of source merge | [#146](https://github.com/martins-netizen/ha-meteoswiss/pull/146), `80572dad002fa3e246c77f58bfbbe739f8860680` |

The [stable-to-source comparison](https://github.com/martins-netizen/ha-meteoswiss/compare/8.3.5...f9abaa12018fb89fd6c31633eadf6a975019d596)
covers 15 commits and 62 changed files. The changes include integration-wide
strict type checking, ownership checks around statistics cleanup and archive
renames, whole precipitation probabilities at the HA forecast interface, and
off-event-loop CSV parsing for station and measured-pollen data.

The package changes two component files, `manifest.json` and `version.py`,
from 8.3.5 to 8.3.6b1. All 50 other component files match the reviewed source.
The [beta notes](RELEASE_8.3.6b1.md) are the English release body used by the
publisher. The [publishing guide](PUBLISHING.md#836b1-prerelease) explains
how to verify the eventual package merge. The prerelease preserves the 24
existing releases and tags, with 8.3.5 remaining the latest stable version.

All nine checks passed on the #147 source merge, including Sonar. Each of the
HA 2026.11.0 and 2026.11.2 jobs passed 3,805 tests plus 83 subtests, reported
five warnings and verified 51 quality rules. Strict mypy passed for 44 source
files. The advisory check covered 145 package/version pairs and reported zero
active, unknown or withdrawn findings. [CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44636281799)
· [HACS validation](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44636281785)
· [CodeQL](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44636281775)

The package PR and the subsequent package merge each receive their own
checks. Publication can be confirmed in the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).
The [existing-entry check](ACCEPTANCE_8.3.6b1.md) records only what the operator
observes after installation.
