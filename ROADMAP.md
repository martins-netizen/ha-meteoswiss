# Maintained-fork roadmap

## Published stable 8.3.6

[Stable 8.3.6](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.6)
was published on 20 November 2026. It carries forward the 8.3.6b1 runtime and
includes the startup and reload test corrections from
[PR #149](https://github.com/martins-netizen/ha-meteoswiss/pull/149).
See the [publication record](docs/RELEASE_EVIDENCE_8.3.6.md) for the package
checks and confirmed upgrade. Open engineering topics are listed under
[Separate future scopes](#separate-future-scopes).

## Published stable 8.3.5

The pre-stable correction is merged as signed
[PR #131](https://github.com/martins-netizen/ha-meteoswiss/pull/131), source
`115ddad474dcae15aa49fb5f368cbed600adf80d`. It puts the single actual HGT
coordinator beside the other eight in `coordinator.py`, preserving its old
import path as an explicit re-export. The same source publishes calculated HGT
at Swiss midnight from the retained daily snapshot; its formula, availability
and identities remain. [The completion record](docs/COORDINATOR_CANONICAL_COMPLETION.md)
retains the original missed structural judgment and the native clock/lifecycle
evidence rather than treating b7's old passing index as proof of that judgment.

**Stable [8.3.5](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5)
was published on 19 November 2026 at 07:12:57 UTC / 08:12:57 CET**, release
**450993306**. Package [PR #132](https://github.com/martins-netizen/ha-meteoswiss/pull/132)
was regularly approved, signed and merged as
`cc158cbdce07f015952275fba72e3c0160c63c80`; all ten head and nine actual-merge
checks passed. The tag, exact approved release text, stable/latest status and
preservation of all 23 earlier complete release records and tag refs were
independently verified. The [dated record](docs/RELEASE_EVIDENCE_8.3.5.md)
contains the exact package identities, native checks and publication results.

**The 8.3.5 packaging and publication work is complete.** Its two component
version fields changed relative to approved #131 source; the other 50 component
files, locks, workflows, policies and exact quality index remained unchanged.

The [cumulative release notes](docs/RELEASE_8.3.5.md) and
[stable guide](docs/ACCEPTANCE_8.3.5.md) cover normal existing-entry updates.
B7 publication and its positive bounded sight report remain complete. Earlier
b3/b5/b6/b7 reports stay closed; no repeated migration, failure exercise or
operator observation window is required. Users who choose published 8.3.5 can
update the existing entry and complete its ordinary update restart once.
Installation of stable 8.3.5 has not been confirmed by the publication report.

The [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
remains authoritative. Minimum Core is **2026.11.0**, current compatibility
**2026.11.3**. The [matrix](docs/QUALITY_SCALE.md) and
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
| Platinum typing/dependency architecture | Strict mypy now checks the full integration. The broader architecture and any tier assessment require their own evidence. |
| Extend multilingual locality search | Use authoritative sources for additional aliases. [8.4.0b1](docs/RELEASE_8.4.0b1.md) already supports aliases for 184 postal forecast points. |
| Provider retention and deployment assurance | Provider policies, host/network/backup controls and independent assessment need their own evidence. The owner-authenticated inventory remains dated 11 November 2026. |
| External contributor CodeQL | Retain evidence from the first actual external-fork route; skipped analysis is not success. |
| New sources/entities or processed forecast data | Scope and validate separately; no new device actions/source role in a release-only change. |

Radar is maintained in a separate integration and is not delivered by this repository.
