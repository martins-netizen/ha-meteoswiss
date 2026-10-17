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

## Before the first fork prerelease

1. Finish review/merge of publication and usability changes.
2. Verify actual warning-consuming dashboards/automations alongside the source
   update, preserving intended behaviour and a paired rollback.
3. Complete live acceptance and ordinary-operation observation of the deployed
   candidate. Confirm retained entities, statistics and display settings.
4. Verify support/security settings and require the HACS check after its workflow
   exists on the maintained branch.
5. Publish an approved prerelease with matching versions, immutable release
   settings and release-only HACS selection; see [PUBLISHING.md](docs/PUBLISHING.md).

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
