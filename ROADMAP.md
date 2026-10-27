# Maintained-fork roadmap

This describes current fork work. Historical upstream release claims remain in
the changelog as history; they are not current certifications. Check the
[release status](README.md#release-status) before installing.

## Published 8.3.1 and prepared shared-settings follow-up

Stable [8.3.1](docs/RELEASE_8.3.1.md), ID **424249153**, was published on
**26 October 2026 at 12:54:24 UTC** from
**fa298ca72bf62da727797f9bfcacf95c83ffeaf1**. It retains the accepted 8.3.1b1
repair/map runtime and is the normal installation route. Actual HACS downloads
are recorded separately from GitHub publication.

The next bounded package is [8.3.2b1](docs/RELEASE_8.3.2b1.md), **prepared,
not published**. Approved PR #76 is regularly integrated, after including #75
and passing the required checks. Configure and Reconfigure share the complete
weather/pollen/forecast/warning-postcode transaction, source retry and
concurrent-edit protection. Only the two component version files change for
this package. Its [focused existing-entry HA check](docs/ACCEPTANCE_8.3.2b1.md)
remains pending; earlier acceptance is not extended to an uninstalled build.

Published 8.3.1 includes language-matched official SwissMetNet map help and
entry-specific repair notices for invalid saved forecast selections. The
8.3.1b1 version/visual acceptance and earlier 8.3.0 acceptance remain closed.

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
| Remaining Gold engineering work | Complete focused HA acceptance of the prepared shared-Reconfigure follow-up; review device metadata, icon/error translations, diagnostic defaults, stale-device handling and proposed exemptions; preserve existing user choices and history. |
| External contributor CodeQL | The unprivileged route is implemented; retain evidence from the first actual external-fork run. A skipped analysis is not completed analysis. |
| Processed local-forecast data | Assess provider payloads, resource limits and compatibility separately from the already released catalogue-based ICON selection. |
| New sources/entities | Scope and test separately; no new device actions/sources in a documentation or release change. |

Radar in a separate integration is not a feature delivered by this repository.
