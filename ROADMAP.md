# Maintained-fork roadmap

## Current engineering work

The pre-stable correction is merged as signed
[PR #131](https://github.com/martins-netizen/ha-meteoswiss/pull/131), source
`115ddad474dcae15aa49fb5f368cbed600adf80d`. It puts the single actual HGT
coordinator beside the other eight in `coordinator.py`, preserving its old
import path as an explicit re-export. The same source publishes calculated HGT
at Swiss midnight from the retained daily snapshot; its formula, availability
and identities remain. [The completion record](docs/COORDINATOR_CANONICAL_COMPLETION.md)
retains the original missed structural judgment and the native clock/lifecycle
evidence rather than treating b7's old passing index as proof of that judgment.

The next step is **stable 8.3.5 packaging** on this actual approved source.
Only two component version fields change; the remaining 50 component files,
locks, workflows, policies and exact quality index stay protected. New fixed
publisher **V1.9** verifies the direct source-to-package boundary and preserves
all older release records/tags. Package approval, actual-merge checks and
authorized publication remain separate; no future package merge is invented.

The [dated record](docs/RELEASE_EVIDENCE_8.3.5.md),
[cumulative release notes](docs/RELEASE_8.3.5.md) and
[stable guide](docs/ACCEPTANCE_8.3.5.md) describe these stages. B7 publication and
its positive bounded sight report remain complete. Earlier b3/b5/b6/b7 reports
stay closed; promotion does not require another migration, failure exercise or
operator observation window. Choose the stable label only when published and
complete the ordinary existing-entry update/restart once.

The [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
remains authoritative. Minimum Core is **2026.11.0**, current compatibility
**2026.11.2**. The [matrix](docs/QUALITY_SCALE.md) and
[fresh-evidence contract](docs/GOLD_EVIDENCE_CONTRACT.md) describe project
engineering evidence, without an official HA tier or independent certification.

## Retained release capabilities

- SwissMetNet observations, independent catalogue-selected ICON forecasts,
  warnings, measured pollen and modelled pollen/air quality/optional UV.
- Official measured HGT daily/monthly/annual products, historical backfill,
  continuing corrections, bounded retries and explicit station-history ownership.
- Native confirmed cleanup for obsolete HGT forecasts without a replacement
  HGT archive. Wind arithmetic archives remain intentional older history while
  the retained sensor produces circular statistics.
- Guarded hourly precipitation imports, source-specific budgets and explicit
  failures; no fabricated gap filling or silent source success.
- Native four-language names/icons/errors, retained personal registry choices,
  seven fixed virtual service roles and shared diagnostic ownership/handoff.
- Minimized native diagnostic exports and local warning/forecast state clocks,
  independent source schedules and deduplicated optional-source transition logs.
- Marketplace/HACS catalogue distribution, normal existing-entry updates,
  reproducible test locks, complete advisory auditing and fresh quality evidence.

The [architecture](docs/ARCHITECTURE.md), [source table](docs/API_SOURCES.md) and
[usage guide](docs/USAGE.md) retain exact behavior and limits. Earlier release
notes and dated metrics remain historical records rather than reopened tasks.

## Separate future scopes

| Scope | Boundary |
|---|---|
| Platinum typing/dependency architecture | Separate justified work; not a missing Gold rule or part of this promotion. |
| Locality names in other languages | Obtain authoritative aliases; preserve provider identity and personal names. |
| Provider retention and deployment assurance | Provider policies, host/network/backup controls and independent assessment need their own evidence. The owner-authenticated inventory remains dated 11 November 2026. |
| External contributor CodeQL | Retain evidence from the first actual external-fork route; skipped analysis is not success. |
| New sources/entities or processed forecast data | Scope and validate separately; no new device actions/source role in a release-only change. |

Radar is maintained in a separate integration and is not delivered by this repository.
