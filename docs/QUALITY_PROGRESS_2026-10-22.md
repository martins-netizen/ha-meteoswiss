# Bronze/Silver follow-up — 22 October 2026

**Record version:** 1.0. **Scope:** unreleased development after stable 8.2.0.
The [dated original audit](QUALITY_AUDIT_2026-10-17.md) remains historical.
This document records individual improvements, not an official HA quality tier.

## Remove unused product placeholders

Review found no imports/callers of `camera.py`, `hydro.py`, `slf.py` or
`MeteoSwissRadarCamera` outside those files. Active platform forwarding lists
only sensor, weather and binary_sensor; `Platform.CAMERA` was already removed
in earlier history. No service, config flow or test registers these placeholders.
The camera never returned an image; hydro/SLF contained comments and a logger.

Remove all three files rather than shipping unused product promises or treating
old comments about unavailable APIs as current provider evidence. Keep the
existing shared App v3 flood/avalanche parser and all active platforms intact.
There is no config/registry/statistics migration and no interaction with a
separately installed radar integration. A new standalone river-gauge, radar or
bulletin product would need a separately verified source and product contract.

Repository import/reference searches, the complete supported-HA regression
suites and existing full-coverage gates verify the bounded removal. Do not add
placeholder tests, no-op imports, coverage exclusions or a lower threshold
merely to make a percentage increase. Exact candidate/CI evidence belongs to
the PR and its job summaries. Local suites pass 917 tests and 14 subtests on
both HA 2026.8.3 and 2026.10.2; CI retains HA 2026.8.3/2026.10.1.

## Remaining prerequisites and boundaries

- `version.py` remains release-tool metadata with a per-module coverage gap.
  Manifest/version consistency is checked by tooling; that does not make its
  runtime line coverage complete. Keep the rule open until a meaningful
  version/diagnostic contract or a separately reviewed consolidation exists.
- Field descriptions, source-choice translations, appropriate selectors and
  data/options placement still need the next bounded config-flow work.
- Polling-interval removal needs a deliberate legacy-value migration decision;
  never silently replace an existing 900/1200-second choice with 600 seconds.
- A shared entity base/module-layout review, Core-brand evidence and the
  complete catalogue diagnostic availability contract remain separate findings.
- The official [coverage rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/)
  applies per module, not only to the aggregate. The
  [UI setup rule](https://contributors.home-assistant.io/core/quality-scale/config-flow/)
  also requires understandable fields and proper data/options separation.

Stable 8.2.0 and its tags stay intact. No HA change, restart, release or repeated
first-install/restore test follows from this source-only cleanup. Bundle any
later accepted runtime changes into a separately reviewed test package.
