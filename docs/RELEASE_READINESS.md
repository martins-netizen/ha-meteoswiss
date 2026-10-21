# Release readiness: beta and first stable version

**Document version:** 1.1 · **Updated:** 21 October 2026
**Purpose:** One entry point for completed evidence, remaining release steps
and work deliberately deferred to later versions.

## Completed evidence

| Evidence | Confirmed state |
|---|---|
| First public beta | `8.2.0b1`, published on 20 October 2026 at 17:56:24 Europe/Zurich; immutable tag at `abbb6b7701134ac2573f35b425ab3f0697a80540`. This is a community fork, not an official MeteoSwiss product. |
| Runtime acceptance | HA 2026.10.2, accepted runtime `0086b956d44b7144b242c5d5c1881d0b0650e524`; its own 24-hour observation and visual acceptance are complete. The 33 published component/translation/brand files match that runtime. |
| Candidate tests | 786 passing tests on each of HA 2026.8.3 and 2026.10.2, 99.051% combined line/branch coverage; successful candidate checks include HACS, Hassfest and CodeQL. This does not complete a Silver assessment. |
| HACS source switch | On 20 October 2026 the operator confirmed HACS 2.0.5, `martins-netizen/ha-meteoswiss`, downloaded `8.2.0b1`, restart and a positive initial visual check. |
| Warnings, languages and migration | App v3 and its verified catalogue, bundled DE/EN/FR/IT, actual warning consumers, retained identities and rain statistics were checked during runtime acceptance. |
| Optional UV outage | An isolated outage on 19 October recovered at the next scheduled request. Other checked data families remained available. |

[HACS acceptance](HACS_ACCEPTANCE.md) records the evidence boundaries.
The operator's latest confirmation is not a newly collected post-switch file,
registry or statistics comparison, or an executed rollback. The source switch
itself is nevertheless complete and should not be repeated without a concrete reason.

## Remaining work before the first stable version

**8.2.0** is the proposed first stable fork version. It has not been published
or automatically approved.

| Order | Work | Completion criterion |
|---|---|---|
| 1 | **Exercise a clean HACS first installation** | In a temporary isolated HA instance: add the custom repository, explicitly select/download the beta, restart, complete setup once, check initial data and understandable errors. Follow the getting-started guide step by step. |
| 2 | **Exercise recovery in the isolated test** | Restore the saved software/configuration through the documented route, including paired warning-filter changes. Do not test on production devices. Simulated tool tests or a written procedure are not an executed recovery rehearsal. |
| 3 | **Resolve findings and finalise scope** | Assess first-install, guide and quality-review findings. Fix and test release-blocking errors; publish justified remaining limitations. Completing every Silver/Gold criterion is not a prerequisite. |
| 4 | **Prepare the stable version** | Manifest/module versions agree on 8.2.0; release/migration notes are current. Include `hide_default_branch: true` in the next reviewed HACS manifest and check release selection. Do not move the immutable beta tag. |
| 5 | **Check and approve the exact candidate** | Successful PR and supported-HA checks, reviewed diff against accepted runtime, regular merge, and a publication decision for that exact commit. |
| 6 | **Publish stable and check HACS availability** | Create a separate stable tag/release, verify version/package contents and confirm that HACS offers the intended stable version. Only then is stable publication complete. |

The operator does **not** need to supply a second permanent HA environment or
delete the production integration. The temporary first-install test remains
open until actually performed.

A new independent **read-only** post-switch comparison of installed files,
identities and statistics progression is useful supplementary evidence. It has
not been collected. It requires no repeat source switch, deletion, restart or
new 24-hour window.

Documentation changes require no HA update. A version/package-only change does
not automatically invalidate completed runtime acceptance. Functional runtime
changes need an explicitly defined test/observation scope. Do not insert new
features into an accepted candidate.

## Security and quality follow-ups

The [17 October review](REVIEW_2026-10-17.md) identified shared
destination/redirect/response-size boundaries and a safe CodeQL route for
external-fork contributions. Completion is not claimed here. Reassess source
hardening risk before stable approval; that review did not demonstrate a
concretely exploitable vulnerability. Before accepting external-fork code,
actually provide safe analysis of it.

Other Bronze/Silver gaps include interval/field design, common module layout,
the external Core-brand evidence and inactive placeholders/per-module coverage.
They remain visible in the [quality matrix](QUALITY_SCALE.md). High aggregate
coverage, HACS validation and successful operation do not close them collectively.
An independent usability test with a new nontechnical user also remains open;
our own first-install walkthrough would not constitute that independent review.

## Later development

- **Location/POI selection and direct local forecasts:** prioritise the official
  OGD point catalogue. Catalogue selection and forecast source are separate
  decisions; the detailed proposal is in
  [PR #35](https://github.com/martins-netizen/ha-meteoswiss/pull/35).
- **Warnings:** retain the MeteoSwiss App v3 API until further notice. Replacing
  it with MeteoGate/MeteoAlarm is outside the current scope.
- **Silver, then Gold:** complete evidence rule by rule; do not claim an official
  HA tier or HACS certification.
- **HACS default catalogue:** a separate later submission, with then-current
  requirements and appropriate `country` metadata in the released manifest.
  Custom-repository availability and a stable GitHub release are independent.

## Evidence

- [Publication procedure](PUBLISHING.md)
- [HACS acceptance and evidence limits](HACS_ACCEPTANCE.md)
- [Beta scope and limitations](RELEASE_8.2.0b1.md)
- [Quality matrix](QUALITY_SCALE.md)
