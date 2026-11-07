# Maintained-fork roadmap

This describes current fork work. Historical upstream release claims remain in
the changelog as history; they are not current certifications. Check the
[release status](README.md#release-status) before installing.

## Prepared stable 8.3.4: clearer setup and verified HA 2026.11 support

[Stable 8.3.4](docs/RELEASE_8.3.4.md) is a maintenance/quality package from
accepted published beta **8.3.4b1 / ID 437718127**, source
**1e5c5d1a7fc1c18d520e99189ae4dd5894621706**. Its benefits over 8.3.3 are the
official-package HA 2026.11 compatibility baseline, a cleaner initial sensor
list and explicit source/service provenance. Existing choices and weather
behaviour are retained; 39 component files match and only two version files
change. All fifteen older tags and the beta's published body are protected.

The HGT statistics change in [PR #92](https://github.com/martins-netizen/ha-meteoswiss/pull/92)
is reserved for a later version with separate acceptance. Full Gold is not a
prerequisite for this version-only stable promotion. Packaging review, successful
actual merge checks, publication and the [short stable update](docs/ACCEPTANCE_8.3.4.md)
are pending; this preparation does not assert a published or installed release.

## Stable 8.3.3 published and accepted

[Stable 8.3.3](docs/RELEASE_8.3.3.md), ID **429354633**, was published on
**30 October 2026 at 18:21:55 UTC** from
**3d4fad2330c89f134eba208e8b2db55705177e7d** and is latest stable.
The [release evidence](docs/RELEASE_EVIDENCE_8.3.3.md) confirms the exact
source/immutable notes, all seven actual merge checks and thirteen retained
old tags. On **30 October**, the operator confirmed **8.3.3 installed and normal
operation OK**. The [short stable update](docs/ACCEPTANCE_8.3.3.md) is complete.

It retains all 39 non-version component files of accepted beta 8.3.3b1:
native icons, personal overrides and 19 translated source-error categories.
Only two version files change. The beta icon check on **Core 2026.10.4 /
HA OS 18.4** remains separate evidence from the later stable version/operation
report. Shared settings, first-install and restore acceptance stay closed.

## Published 8.3.4b1 test package; short operation check complete

[8.3.4b1](docs/RELEASE_8.3.4b1.md) packages the regularly merged diagnostic-default
and provider-metadata changes from #88/#89. Its 39 non-version component files
match reviewed merge `5a7eae00963d47294281da8812cb1ede35713b7f`; only two version
files change. Packaging PR #90 was regularly merged at
`1e5c5d1a7fc1c18d520e99189ae4dd5894621706`, with all seven actual merge
checks successful. The fixed V1.7 publisher created release **437718127** on
**7 November 2026 at 17:12:54 UTC**, retaining all fourteen older tags and
latest stable 8.3.3. The operator subsequently confirmed normal operation
on **HA Core 2026.11.0 / HA OS 18.4**, completing the agreed
[short check](docs/ACCEPTANCE_8.3.4b1.md). See the
[bounded evidence](docs/RELEASE_EVIDENCE_8.3.4b1.md); no further HA check
or stable promotion follows from this documentation update.

## Remaining Gold and provider-evidence work

The [diagnostic-defaults and service-metadata change](docs/DIAGNOSTIC_DEFAULTS.md), released in 8.3.4b1,
adds first-registration diagnostic defaults and explicit virtual service groups,
with registry-preservation tests. Stable 8.3.3 does not include this change.

The [provider-metadata follow-up](docs/PROVIDER_METADATA.md), released in 8.3.4b1, corrects
Open-Meteo current-weather labels and attribution while keeping group identity
and personal choices. Native pollen-station round trips reuse all seven groups;
no cleanup is needed for those tested changes. Historical orphaned groups have
not been independently inventoried and are not deleted by this change.

Review remaining device classes, historical stale grouping and rule-specific
exemptions in separate bounded scopes. Obtain
authoritative multilingual locality aliases before adding provider name
translations. Preserve personal registry choices, identities, history,
four-language catalogues and existing quality/security gates.

The [Gold matrix](docs/QUALITY_SCALE.md) retains these requirements. Native
icons and translated update failures are released and accepted; they do not
complete the full checklist. No new feature, HA test or release is approved by
this status reconciliation.

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
| Remaining Gold engineering work | Diagnostic defaults, service metadata and alternative-provider labels are implemented in unreleased development. Native pollen-station changes reuse the existing groups; historical orphan review, device classes and proposed exemptions remain separate. Icon/error translations are delivered in published and operator-accepted stable 8.3.3; preserve existing user choices and history. Shared-Reconfigure focused acceptance is completed within its reported scope. |
| External contributor CodeQL | The unprivileged route is implemented; retain evidence from the first actual external-fork run. A skipped analysis is not completed analysis. |
| Processed local-forecast data | Assess provider payloads, resource limits and compatibility separately from the already released catalogue-based ICON selection. |
| New sources/entities | Scope and test separately; no new device actions/sources in a documentation or release change. |

Radar in a separate integration is not a feature delivered by this repository.
