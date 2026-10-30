# Maintained-fork roadmap

This describes current fork work. Historical upstream release claims remain in
the changelog as history; they are not current certifications. Check the
[release status](README.md#release-status) before installing.

## Stable 8.3.2 published and accepted

[Stable 8.3.2](docs/RELEASE_8.3.2.md), ID **426633496**, was published on
**28 October 2026 at 12:21:19 UTC** from
**aea4c5eab0534a6e675a4f564bde7521df193c58** and is latest stable.
The [publication and acceptance record](docs/RELEASE_EVIDENCE_8.3.2.md) confirms
the exact source, immutable notes, seven successful merge checks and preserved
old tags. On **30 October** the operator confirmed the HACS download, HA
restart and working operation. This closes the short stable update.

Both Configure and Reconfigure share complete weather/pollen/forecast/warning
settings, source retry and concurrent-edit protection. The five-step beta
acceptance on Core 2026.10.4 and earlier repair/map, first-install and restore
evidence stay closed within their recorded scopes.

## Accepted 8.3.3b1, prepared stable 8.3.3 and remaining Gold work

The combined #80/#81 runtime was published as
[8.3.3b1](docs/RELEASE_8.3.3b1.md), ID **429321251**, on **30 October 2026 at
17:42:37 UTC**, from **d9fbc3fd49220b0ecc019d2babe0c173c46986f5**. The actual
release/tag/notes and twelve earlier tags were independently checked. Seven
actual merge checks pass with **2,045 tests plus 83 subtests** on each hosted
HA fixture. The operator reported icons/personal choices and normal operation
OK on **HA Core 2026.10.4 / HA OS 18.4**; the
[short beta check](docs/ACCEPTANCE_8.3.3b1.md) is complete within its scope.

1. Review and regularly merge the [stable 8.3.3 package](docs/RELEASE_8.3.3.md).
   It retains all 39 non-version component files of the accepted beta. Verify
   exact-head and actual merge checks, then publish separately.
2. After confirmed publication, complete only the
   [short actual stable download](docs/ACCEPTANCE_8.3.3.md). Earlier icon,
   settings, clean-install and restore checks remain closed.
3. Review diagnostic defaults for new entities, device metadata/classes,
   stale grouping and rule-specific exemptions in separate later scopes.

Stable 8.3.2 remains latest until the separate promotion. Preserve personal
registry choices, identities and history. The [Gold matrix](docs/QUALITY_SCALE.md)
retains the remaining requirements; the two delivered features do not complete Gold.

## Implemented and released in 8.3.0

- HA-owned HTTP sessions, bounded transient retries, cancellation and independent
  required/optional source startup.
- Station observations with measurement times, trailing-partial-row handling
  and explicit failure/recovery.
- Catalogue-backed postcode/town/POI selection, height-aware ICON Seamless
  forecasts, native weather units and continuing HA forecast subscriptions.
- Separately named observation/forecast devices, eight today/tomorrow sensors,
  complete Swiss calendar-day handling and a shared location-settings dialog.
- Completed hourly precipitation statistics and a 13-month archive import,
  retaining statistic identity and corrections.
- App v3 warnings, verified thirteen-family mapping, active/upcoming separation
  and German/English/French/Italian labels.
- Measured pollen, modelled pollen/AQ and separately optional current UV.
- Forecast-based daily HGT 12/20; no fictitious measured seasonal total.
- Shared station metadata, redacted diagnostics and checked cache expiry.
- Bounded HTTP/asset validation, shared parsing and separated source/coordinator
  responsibilities, with inactive standalone camera/SLF/hydrology placeholders removed.
- PR review, minimum/current HA tests, CodeQL, SonarCloud, Hassfest, HACS
  validation, bundled icons and plain-language user guides.

Code and CI success do not mark a candidate as installed or accepted on a real
HA system. Source providers and optional individual values can be unavailable.

## Release progress

Stable **8.3.0** was published on **24 October 2026**, retaining the runtime
accepted in b4 with version-only component changes. Later that day, Frenck
approved and merged [HACS catalogue admission #12593](https://github.com/hacs/default/pull/12593).
New users find this fork through normal HACS search. The
[admission record](docs/HACS_ACCEPTANCE.md#hacs-catalogue-admission) links the
review, successful checks and current catalogue entry.

The operator's earlier source-switch, clean-install and isolated restore checks
are complete within their recorded scope; do not repeat them for catalogue
admission. On 25 October the operator confirmed that the production update
from 8.2 to stable 8.3 worked successfully. See
[release readiness](docs/RELEASE_READINESS.md) and [publication](docs/PUBLISHING.md).

We use the HA Quality Scale to guide documented engineering work. The
[rule matrix](docs/QUALITY_SCALE.md) records applicable Bronze/Silver evidence,
test coverage and remaining Gold work. Official HA tiers are not assigned to
custom integrations.

## Separate future scopes

| Scope | Decision still needed |
|---|---|
| Locality names in other languages | Obtain authoritative aliases; preserve provider identities and avoid invented translations or duplicate places. |
| Remaining Gold engineering work | Review device metadata, diagnostic defaults, stale-device handling and proposed exemptions; icon/error translations are published in accepted 8.3.3b1 and prepared for stable 8.3.3; preserve existing user choices and history. Shared-Reconfigure focused acceptance is completed within its reported scope. |
| External contributor CodeQL | The unprivileged route is implemented; retain evidence from the first actual external-fork run. A skipped analysis is not completed analysis. |
| Processed local-forecast data | Assess provider payloads, resource limits and compatibility separately from the already released catalogue-based ICON selection. |
| New sources/entities | Scope and test separately; no new device actions/sources in a documentation or release change. |

Radar in a separate integration is not a feature delivered by this repository.
