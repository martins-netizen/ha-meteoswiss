# Maintained-fork roadmap

This describes current fork work. Historical upstream release claims remain in
the changelog as history; they are not current certifications. Check the
[release status](README.md#release-status) before installing.

## Implemented and tested in the maintained candidate

- HA-owned HTTP sessions, bounded transient retries, cancellation and independent
  required/optional source startup.
- Station observations with measurement times, trailing-partial-row handling
  and explicit failure/recovery.
- Location-based ICON Seamless forecasts, native weather units and continuing
  HA forecast subscriptions.
- Completed hourly precipitation statistics and a 13-month archive import,
  retaining statistic identity and corrections.
- App v3 warnings, verified thirteen-family mapping, active/upcoming separation
  and German/English/French/Italian labels.
- Measured pollen, modelled pollen/AQ and separately optional current UV.
- Forecast-based daily HGT 12/20; no fictitious measured seasonal total.
- Shared station metadata, redacted diagnostics and checked cache expiry.
- PR review, minimum/current HA tests, CodeQL and Hassfest. The packaging PR
  adds local icons, HACS validation and plain-language user guides.

Code and CI success do not mark a candidate as installed or accepted on a real
HA system. Source providers and optional individual values can be unavailable.

## Release progress

The first immutable beta 8.2.0b1 was published on 20 October 2026 after
completed HA 2026.10.2 runtime acceptance. The operator also confirmed the
HACS 2.0.5 source switch, download, restart and initial visual success.
Those are completed steps, not work to repeat.

Before a first stable version, complete the clean first-install and isolated
recovery rehearsal, assess remaining findings and check the exact stable
package/version. See [release readiness](docs/RELEASE_READINESS.md) and
[publication](docs/PUBLISHING.md). A second permanent operator HA instance is
not required; do not erase production configuration to test first installation.

There is no current HA Silver, Gold or Platinum claim. Coverage gates and
remaining per-module limits are in [QUALITY_SCALE.md](docs/QUALITY_SCALE.md).

## Separate future scopes

| Scope | Decision still needed |
|---|---|
| Inactive camera/SLF/hydrology research | Remove/move out of the runtime package or implement real contracts/tests; no exclusions merely to inflate coverage. |
| API size and asset-URL boundaries | Provider-aware size/scheme/host/redirect checks, after verifying actual delivery paths. Catalogue validation is not a universal network limit. |
| External contributor CodeQL | Review the same-repository PR guard before accepting external forks; skipped analysis is not completed analysis. |
| Shared parsing boundaries | Consider extracting the reused timestamp parser from the station coordinator; avoid reorganisation without a purpose. |
| Further HA Quality Scale rules | Complete rule-specific and every-module evidence before asserting a tier. |
| New sources/entities | Scope and test separately; no new device actions/sources in a documentation or release change. |

Radar in a separate integration is not a feature delivered by this repository.
