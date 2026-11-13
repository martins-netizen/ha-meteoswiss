# Privacy, architecture and security: bounded review

**Review:** 11 November 2026 · **Base:** `11ef5eaf7cb93d28f1039216b05670750ad6de6a`.
This source/configuration review is not an independent penetration test,
regulatory certification or assurance that every deployment is secure.

| Area | Verified strengths | Remaining boundary |
|---|---|---|
| Privacy | No integration account/credential, analytics SDK or separate maintainer telemetry in the reviewed runtime. Location fields and saved forecast selections are redacted from diagnostics; raw payloads, cache keys and expected private error URLs are omitted. | Providers still receive station/postcode/coordinates and the public source IP. Retention is outside this integration's control. Ordinary state attributes, HA-wide debug logs and user-supplied cards need separate sharing review. |
| Architecture | Typed entry-owned runtime, borrowed HA session, source/coordinator separation, bounded parsing and independent optional-source failures; native lifecycle tests. | Strict typing and a separately distributed client-library boundary are not fully established. Large coordinator/sensor/config-flow modules retain maintenance costs. The unreleased typed shared-diagnostic lifecycle bounds ownership/handoff; ambiguous legacy groups still need review. Coverage is evidence, not architecture certification. |
| Security | Fixed-host HTTPS/TLS, no redirects, wire/decompression limits, bounded timeouts/retries and cancellation tests. Hash-locked minimum/current fixtures, explicit Python/pip/certifi/uv floors, offline uv, pinned actions, least-privilege workflows and actual-merge verification. Exact PyPI vulnerability metadata checks returned no active advisories for either 138-pin test lock. | The owner-authenticated 11 November inventory below closes the previously inaccessible alert/settings check. This is a point-in-time inventory, not complete security clearance or an independent offensive assessment. Required approving reviews are zero; SonarCloud is checked in the project workflow but is not a ruleset-required check. |

The engineering foundation is strong. An unqualified "top-level in every
respect" statement would exceed this evidence. The [quality matrix](QUALITY_SCALE.md)
retains open Gold work; custom integrations have no official quality tier.

## Data flow and provider retention

The [source/request table](API_SOURCES.md) is the data-flow inventory. A selected
weather-forecast point does not move the modelled pollen/AQ/UV location:
MeteoSwiss-source entries retain HA home coordinates for those families;
alternative-source entries use their configured base coordinates. Warning
postcode and measured-pollen station are independent. HTTPS protects transport,
but the receiving provider can see query parameters.

Open-Meteo's [API privacy notice](https://open-meteo.com/en/terms#privacy) states
that technical logs can include IP addresses and geographical coordinates and
are deleted after 90 days. This is the provider's statement, not an independent
retention audit or a guarantee by this fork. Other providers have their own
policies. No precision reduction or source selection is silently applied.

## Repository evidence and limits

On the review date, active `Protect development` rules require PR/squash merges,
linear history, resolved conversations, an up-to-date branch, `Analyze Python`,
`tests` and `HACS validation`. The aggregate `tests` gate requires both HA jobs
and Hassfest. No bypass actors were listed; approving-review count is zero.
Upstream `main` is separately protected against deletion/non-fast-forward.

A SHA-256-verified Gitleaks **8.30.1** binary scanned a fresh mirror with
`--all`: **402 scanned commits**, **423 reachable commits**, **132 refs**.
Three generic-key matches were inspected and verified as public translation
keys, not credentials. No credential finding was confirmed in that scan.
A separate bounded text/commit-metadata check found no supplied private-profile
email, local-user marker or `/Users/` path. Unknown secret formats, unreachable
objects, external forks, release binaries, issue attachments, CI artifacts and
HA installations are outside that result. It is not a perpetual absence guarantee.

This follow-up adds Git exclusions for common local credentials/private keys.
Ignore rules do not protect already tracked files and do not replace scanning.
Review the actual diff/artifact before publication; report a suspected secret
or vulnerability [privately](../SECURITY.md).

A point-in-time query of PyPI's published vulnerability metadata checked all
**138 pins in each test lock**, **140 distinct package/version pairs** across
the two: **zero active advisories and zero unknown responses**, without an
ignore list. Withdrawn advisories are excluded. This checks known published
advisories, not malicious packages, unknown vulnerabilities, OS/container/action
dependencies or an operator's installed environment. It does not substitute for
the owner-only GitHub alert inventory or a recurring gate.

## Owner-authenticated alert inventory

The owner supplied a filtered, read-only GitHub report at **11 November 2026,
07:05:03 UTC**. All query groups succeeded; reported counts match their arrays.
This updates the earlier review connection's unknown alert state.

| Check | Reported result |
|---|---|
| Dependabot open | 0 |
| Dependabot closed | 67; all `fixed`, with `fixed_at` set and no dismissal reason |
| Code-scanning open | 0 |
| Secret-scanning open | 0 |
| Secret scanning / push protection | Enabled |
| Automatic security updates | Enabled, not paused |
| Additional non-provider patterns / validity checks | Disabled |

The 67 fixes were recorded on 10 November between 22:19:39 and 22:19:46 UTC.
No alert was manually dismissed by this review. No secret values or raw error
payloads were included in the supplied report. Optional scanning features were
not enabled by this read-only assessment. A clean current inventory does not
prove the absence of unknown vulnerabilities, unrecognised secret formats or
exposure in every external artifact; the other scope limits above remain.

## Follow-up priorities

1. Review making SonarCloud required and retain the accepted dependency-update
   workflow. The unreleased [whole-lock gate](DEPENDENCY_ADVISORIES.md) now has
   bounded source/live evidence; new hosted/scheduled acceptance remains separate.
   Fixed floors and this feed do not detect every future vulnerability.
2. Continue bounded translation and device-lifecycle work; obtain independent
   review of migrations and sensitive changes. Wind PR #97 is merged; release
   and operator database acceptance remain separate.
3. Retain dated owner-authenticated inventories as the repository changes.
   Future inaccessible APIs remain unknown, not empty alert lists.
4. Verify HA account/network/backup controls separately. This repository review
   does not prove MFA, firewall rules, external exposure or restoration on a host.

## Unreleased shared-diagnostic lifecycle scope

The [lifecycle follow-up](SHARED_DIAGNOSTIC_LIFECYCLE.md) explicitly retains the two
shared helper identities across entry departure and startup order, with native
registry operations and no peer-coordinator reload. It adds no provider endpoint,
credential, telemetry or permissions. Ambiguous ownership and failed transfers
raise a local translated repair; exception messages are not exported. Tests cover
retained user choices, cancellation/shutdown, rollback and disposable Recorder
history. Historical conflicts, operator acceptance and independent review remain
separate. The dated security inventory above is not refreshed by these tests.

## Unreleased manual device-removal scope

The [bounded approval policy](DEVICE_REMOVAL.md) classifies native registry
records locally. It adds no provider requests, telemetry, location export,
credentials or integration permissions. Only HA's user-confirmed removal of an
unambiguous empty retired service shell is allowed; active/shared/disabled
groups, entity bindings and device relationships stay protected. No automatic
cleanup or Recorder deletion is introduced. The source-history review is not a
production inventory; native UI/Recorder tests do not establish independent
security clearance, operator acceptance or completed Gold.

## Unreleased service-group naming scope

The [native naming follow-up](SERVICE_GROUP_TRANSLATIONS.md) changes only local
default labels. Station/postcode placeholders preserve text already present in
the previous names; providers, requests, credentials and permissions do not
change. Native tests verify that integration diagnostics still redact saved
locations and do not export device translation placeholders. Personal registry
choices and historical rows remain intact. This does not refresh the dated
security inventory or establish operator acceptance, independent review or Gold.

## Complete entity-name evidence

The [name-inventory follow-up](ENTITY_NAME_TRANSLATIONS.md) adds tests and
documentation only. It checks every exposed name and retained registry choice
through HA's native DE/EN/FR/IT rendering, including both weather entities'
device-name inheritance. Component files, translations, requests, dependencies,
CI permissions, diagnostics and migrations remain unchanged. This adds no
personal-data flow or renewed security inventory. The Gold naming rule's
automated evidence is now explicit; release/operator UI acceptance and the
overall architecture/security boundaries above still apply.

## Complete test-lock advisory gate

The [CI follow-up](DEPENDENCY_ADVISORIES.md) checks all selections from both
universal locks against release-specific PyPI vulnerability metadata. Active
advisories and unknown results fail the existing required aggregate gate;
the same isolated read-only steps are scheduled daily. Only public package
names/versions and the CI runner's network address reach PyPI, possibly through
its configured proxy. No HA location, state, credential or user configuration
is read. Origin TLS stays verified; responses, retries and job time are bounded.
No raw provider/exception/proxy details enter reports. Integration sources,
dependencies, HA offline policy and workflow permissions stay unchanged.

This closes the missing source implementation of a recurring whole-lock check,
not its as-yet unrun hosted/scheduled acceptance. A live known-result inventory
is dated evidence and does not refresh the owner-only GitHub alert/settings
inventory or establish an independent security clearance or completed Gold.
