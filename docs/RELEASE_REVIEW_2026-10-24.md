# Overall release review — 24 October 2026

## Status addendum 1.2 — 25 October 2026

Stable **8.3.0** was published on 24 October at **15:35:56 UTC**, release ID
**422817883**, from **3ca9a1c166920fbdda88d15238affafe520f4b68**. Later that day,
Frenck approved and merged [hacs/default #12593](https://github.com/hacs/default/pull/12593)
at **20:04:26 UTC**. The fork is in the current integration list, and all 13
distinct latest check results passed. [HACS acceptance](HACS_ACCEPTANCE.md#hacs-catalogue-admission)
retains the admission evidence and the separate earlier operator checks.

The earlier addendum and source audit below describe their dated scope; their
then-open publication/admission steps are now complete. The operator's subsequent
stable HACS update is a separate result. The [quality matrix](QUALITY_SCALE.md)
uses the HA rules as an engineering checklist; official tiers are not assigned
to custom integrations. Existing code/test evidence and open Gold work remain
visible. The user guides now put normal HACS search first, as requested in the
admission review, with custom registration as a fallback.

## Review addendum 1.1: stable 8.3.0 promotion

The original review below is a dated source audit; its then-open runtime,
dialog and acceptance findings were corrected in the subsequent PRs recorded
in [readiness](RELEASE_READINESS.md). The operator accepted published b4 and
requested stable promotion on 24 October. Screenshots confirm the version and
separate measurement/forecast devices with symbols and values. They do not
independently expose every provenance attribute or registry ID.

The stable package retains all 37 non-version component files from accepted
b4 at a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5. Only manifest/module versions
become 8.3.0; HACS/CH, workflows, all previous tags and old publishers remain.
Current setup, migration, location, source and quality guides are aligned.
Publisher V1.3 adds stable/latest selection with prior stable/beta publication
checks, read-only retries and refusal of changed source/checks/tags/notes.
Full local suite: 1,653 tests +63 subtests on each HA 2026.8.3 and
2026.10.3; coverage remains 99.97753% with unchanged strict gates/exclusions.
Exact PR and post-merge checks are still required. Publication and a subsequent
stable HACS update remain separate results; see [stable notes](RELEASE_8.3.0.md).
No official HA tier, HACS catalogue approval or diagnosed UTM restart cause is
inferred. The [quality matrix](QUALITY_SCALE.md) retains open Gold/Core-brand
boundaries. No new feature or blanket observation window is added.

## Original source review 1.0 — historical findings


**Review version:** 1.0. **Baseline:** approved PR #58, regularly squash-merged
as **5bed187e8a680b8d194f9f3ee171fe89671c3fae**. Its tree is
fc441608bebc5d8f20519f897150ea47b0dc601c, identical to the approved PR tree.
All eight PR checks and seven post-merge checks passed. The changes below belong
to the associated correction PR and remain unreleased.

**Conclusion:** the agreed architecture/location feature is implemented, but
the review found four concrete runtime corrections and contradictory current
instructions. These are corrected and regression-tested before candidate
packaging. No release, HA installation or HACS default submission follows from
this review alone. The immutable stable 8.2.0 package is unchanged.

## Method and scope

Reviewed source/HA boundaries, data/time contracts, configuration persistence,
location routing, cache identity, source failure/privacy, Recorder semantics,
setup/update/removal instructions, translated dialogs and current HACS rules.
Ran the complete regression suite in both local HA environments and tested the
component without repository-root runtime files. New regressions were first
run against the preceding implementation to demonstrate the failures.

This is a code, test and documentation review, with bounded public-source probes.
It is not an independent penetration test, a manual HACS/browser walkthrough,
a forecast-accuracy study or an official HA quality-tier assessment. No access
to a user's HA, credentials, device controls or private backups was needed.

## Findings fixed before the next candidate

| Finding | Severity and concrete failure | Correction and regression evidence |
|---|---|---|
| R1: partial-day weather fallback | Medium. Two remaining dry hours could publish daily rain/probability 0 and temperature extrema as though they described a whole day. Internal continuity did not prove midnight coverage. | Every valid instantaneous hour is required for fallback extrema. Rain/probability require the preceding-hour end buckets, including next midnight. Invalid/missing/gapped hours invalidate only their aggregate. Native full-day zero still wins. Tests cover ordinary days, missing midnight and 23-/25-hour days. |
| R2: provider daily periods at DST | Medium. Open-Meteo labels daily aggregates using one fixed offset for a response. Keeping the correct date label alone could still present a 24-hour bucket as a different Swiss calendar period. | Accept all five native daily fields only when provider start/end equal both Swiss midnights. Otherwise preserve the hourly feed and leave native daily fields missing. Nine spring/autumn cases cover before/after the transition, both offsets and ordinary days; the repeated-hour test retains both distinct physical hours and daylight. |
| R3: unverified UV timestamp | Medium. A numeric UV result without a time, with an old time or with a future time was accepted as current. | Request Unix seconds and require a timestamp no later than now and less than one hour old. Rejection makes only UV unavailable. Current zero remains zero; a current valid response with a missing number remains unknown. Direct source and registered HA outage/cache/recovery/privacy tests cover it. |
| R4: station CSV event-loop work | Medium. Up to the existing bounded CSV budget could be decoded, materialised and scanned on HA's event loop. | Run decode/selection/numeric parsing in HA's executor after the bounded download. A thread-identity regression proves the real reader is not called on the loop thread. Existing incomplete-row, station identity, sparse fallback, freshness, cancellation and private-failure contracts remain. |
| D1: contradictory release/setup/source documentation | Medium for installation decisions. Some current pages still described merged dialogs as planned, completed stable HACS acceptance as unreported, six measured pollen species, or AQ as following a selected forecast POI. Publisher examples omitted their scripts/ directory. | Reconcile README, setup/source/architecture, quality/readiness/publication plans and coordinator examples. Keep 8.2.0 setup separate from unreleased fields. Record seven measured pollen types including oak, independent AQ base location, completed acceptance and the alias limit. Historical release recipes remain version-specific. |

A bounded public Kloten-point request on **23 October 2026 at 22:17:22 UTC**
returned fixed offset 7200 and daily timestamps 86,400 seconds apart across the
25 October clock change. This supports R2's period mismatch; the controlled
nine-case fixture is the repeatable regression. A separate current-UV request
returned Unix time, interval 900 and valid numeric zero. These probes establish
response shape/time semantics, not forecast accuracy or future availability.
The [provider definitions](https://open-meteo.com/en/docs) identify precipitation
and its probability as preceding-hour fields and document the fixed daily
offset. No provider/model is changed.

### Deliberate missing values around clock changes

Scalar daily temperature/rain and daily HGT require an accepted native daily
aggregate. They can therefore be unknown when the source period mismatches the
Swiss day; they are not silently estimated from remaining hours. The weather
service can use a complete correctly aligned hourly fallback when available.
Hourly forecasts and complete probability windows remain usable. These limits
are now explicit in FORECAST_SENSORS.md and USAGE.md.

## Architecture and lifecycle

All seven actual coordinators are defined in coordinator.py, and common entity
bases are in entity.py. ICON/current/modelled AQ/measured pollen/precipitation
have real source boundaries; the precipitation Recorder adapter owns statistic
projection and queuing. The station observation adapter still resides in its
legacy coordinator; R4 bounds its loop impact without claiming a complete
source-class extraction. A later extraction can remain a focused internal PR.

ConfigEntry.runtime_data owns per-entry instances and the borrowed verified-TLS
session. Optional initial refreshes do not delay required observations. HA owns
session closure; unload removes source listeners, Recorder keep-alive listeners
and entity timers. Real loaded HA, Recorder and WebSocket regressions exercise
setup/reload/unload, failure/recovery and retained IDs. Queue acceptance is not
mistaken for synchronous Recorder persistence; upsert/correction tests inspect
the database too.

Forecast point identity is type plus opaque ID, never just name/postcode. New
setup and Reconfigure require an explicit result and confirmation; no first
result is preselected. Selected height is requested and included in the cache
key. Missing height leaves automatic DEM enabled. Offline saved selection needs
no startup catalogue download; invalid selection disables forecasts alone and
has explicit reset/replacement. Confirmed changes merge into latest entry data
and trigger one loaded-entry reload. Cancel/keep do not change the location.

Observations, modelled current weather, AQ/pollen/UV base coordinates, measured
pollen and warning postcode retain their independent meanings. A POI forecast
cannot become the home current-condition fallback. No automatic source switch,
new network poller, renamed retained identity or history purge is introduced.

## Security and repository protections

Reviewed HTTP boundaries enforce the source-specific HTTPS host, normal port,
no URL credentials/control characters, no redirects and wire/decompressed limits.
Archive budgets retain official historical precipitation support. Shared TLS
verification is kept. Bounded transient retries respect supported Retry-After
forms within their sequence; permanent input/schema errors do not become
repeated retries. Cancellation propagates. There is no new claim of a persistent
provider-wide cooldown or unlimited free API access.

Saved point objects are wholly redacted from diagnostics in data and options.
Exports contain safe state/time/count metadata, not arbitrary payload or cache
keys. Formatted error-chain/log tests cover coordinates, names, IDs and request
URLs. Provider warning text is escaped in the bundled optional card example.
Local HA entity attributes intentionally retain selected public source metadata;
review them before sharing screenshots.

Fresh ruleset reads confirm active protected development: PRs, squash/linear
history, resolved discussions and GitHub-Actions-bound tests, Analyze Python and
HACS validation; deletion/force pushes blocked, no bypass actors. Required
external approvals are zero, consistent with one maintainer, and do not establish
an independent human review. The upstream mirror has deletion/force-push
protection. Workflows use pinned action SHAs/tool images, minimal job permissions
and no persisted checkout credentials. External CodeQL uses pull_request, not
privileged pull_request_target. A first real foreign-fork run remains separate
evidence; an own-branch success does not prove that path.

SECURITY.md now states the private reporting route and supported-version policy.
Prior operator confirmations of Secret Protection, push protection and Dependabot
security updates remain scoped reports. This connector does not expose all
administrative security/alert settings: this review does not independently
reconfirm them or claim zero open alerts/vulnerabilities. No security settings
or protections were weakened to run a check.

## Installation and documentation

README has separate first-install and existing-entry paths, a short current
release status and links to the feature guide. Published 8.2.0 retains its
original interval/setup instructions; development describes automatic defaults,
pollen-only Configure and separate forecast Reconfigure. Existing users keep
the HA entry, IDs and statistic history. Download, configure, restart, source
switch, update-information and restore are distinct operations.

Completed source switch, temporary clean first installation, isolated restore,
Beta2 geographic setup and stable HACS update remain recorded within their
reported evidence limits. They are not reopened. The 8.2.0 publication helpers
are historical, hardcoded release recipes; none is a publisher for 8.3.0b1.
A future candidate needs its own matching version packet and guarded publisher.

The four UI catalogues have 140 matching keys and strings.json equals English.
Official catalogue place names are not claimed to be multilingual: Murten and
Morat share a town/postcode, but only Murten/3280 currently resolves to the
verified point 2/328000. A sourced multilingual alias index remains a separate
follow-up, preserving ambiguity and composite identity. This is not solved by
translating dialogs/categories or by merging every point with the same postcode.

The editorial review targets beginners and experienced users but is not an
independent nontechnical-user study. Historical dated audits remain evidence
of their original snapshot; the current quality matrix replaces stale gaps.

## HACS assessment checked on 24 October 2026

| Requirement/evidence | Current result |
|---|---|
| Repository and packaging | Public active martins-netizen repository, maintained development default, usable description/topics/Issues and MIT attribution. Exactly one custom_components integration. All 38 runtime/brand/translation files are inside that component. |
| Component manifest | Domain, name, documentation, issue tracker, codeowner, version, config flow, service/cloud-polling metadata and empty extra requirements present. Version remains 8.2.0 until candidate packaging; no tag is rewritten. |
| HACS manifest | Name, minimum HA 2026.8.3, hide_default_branch and country CH in development. Country CH is absent from immutable 8.2.0, so a new released HACS manifest is required before default submission. |
| Brands | Local valid RGBA PNGs: icon.png 256×256 and icon@2x.png 512×512. Current HACS rules accept the local brand route; external Core brand evidence is a separate quality-tier issue. |
| Official validations | PR #58 and its exact merge passed HACS with no ignores and Hassfest. The correction PR must independently pass its own exact checks. Source validation does not approve a future package. |
| Existing HACS use | Published releases and prior practical source-switch/clean-install/update evidence exist; no new manual HACS test is claimed here. |
| Default list/Core collision | Fresh hacs/default integration list has 3,982 entries and no maintained fork. Core dev's meteoswiss manifest path returned 404, while a weather-manifest control succeeded. This is a dated eligibility check, not a promise about future Core changes. |
| Remaining submission gate | Review corrections, exact candidate packaging/CI, focused acceptance and reviewed stable full GitHub release. Then a separate owner/major-contributor editable alphabetical PR from a fresh hacs/default master branch, with current checks and truthful template. HACS review decides inclusion. |

The current primary references are [integration packaging](https://www.hacs.xyz/docs/publish/integration/),
[general metadata](https://www.hacs.xyz/docs/publish/start/) and
[default-list submission](https://www.hacs.xyz/docs/publish/include/).
These checks establish an implementable HACS path; they do not award a HACS
certification, default listing or official HA tier. Full Bronze/Silver evidence
and the still-open Gold rules are enumerated in QUALITY_SCALE.md.

## Verification record

- **Full suites:** 1,295 tests and 53 subtests pass on each local HA 2026.8.3 and
  2026.10.2 environment. CI still tests 2026.8.3 and 2026.10.1.
- **Coverage:** 99.97506% combined; 3,138/3,139 statements, all 870 branches.
  Every module exceeds 95%, all existing strict gates are 100%, with no new
  exclusion or lowered threshold.
- **Component-only simulation:** copied the 38 component files into an isolated
  HA-style directory without repository-root runtime assets/scripts/docs. Both
  environments import that staged component and pass 235 focused tests covering
  source setup, migration, selection, reconfiguration, Recorder, weather/scalars,
  UV and lifecycle. Test harness files are separate supporting files. This is
  an automated install-layout check, not an actual HACS download or UTM session.
- **Static/document checks:** compile, four-catalogue/version validation,
  production/changed-test Ruff checks, relative Markdown targets/anchors,
  Python example compilation, YAML decoding and shell syntax. Versioned
  publisher refusal/check/retry behaviour remains covered by existing tests;
  no live publishing command is executed.

The sole uncovered const.py line is unchanged from baseline. Coverage measures
executed code paths, not proof of every weather/provider assumption. Exact
hosted checks/reviews must be inspected on the final correction head and again
after any approved merge. Candidate acceptance is still a real next step.

## Remaining work in order

1. Review/merge the correction PR; verify its exact merged tree and post-merge
   checks. Do not silently install development because the source version matches.
2. Freeze the agreed scope and prepare the exact 8.3.0b1 versions/notes and
   candidate-specific publisher. Review its protected merge and checks.
3. Publish the approved prerelease, then perform the focused point/height,
   source-role, cancel/keep/change/reset, language and missing-data checks in
   the existing temporary HA. No repeated clean-install/restore or arbitrary
   new 24-hour wait is required. Investigate a concrete new failure if found.
4. Approve the evidenced stable release separately. Submit to HACS defaults only
   after the reviewed released metadata and then-current rules are verified.

Nonblocking follow-ups include sourced multilingual names, HTTP conditional
requests/jitter and the documented Gold items (translated exceptions/icons,
Repair issues, diagnostic defaults and stale-device handling). Warning timing
is republished with the ten-minute source refresh, and legacy HGT/weather
subscriptions with their coordinator refresh; they have no independent
second-by-second validity clock. Measured pollen age is checked on refresh,
not by a separate timer. Automations needing tighter boundaries must inspect
validity/measurement times. These are explicit scheduling limits, not new live
regression findings or reasons to infer a safe all-clear during an outage.
