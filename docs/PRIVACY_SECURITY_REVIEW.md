# Privacy, architecture and security: bounded review

**Review:** 11 November 2026 · **Base:** `7a5481ad5a8f8c47a9e10cf582c8b10750ad4009`.
This source/configuration review is not an independent penetration test,
regulatory certification or assurance that every deployment is secure.

| Area | Verified strengths | Remaining boundary |
|---|---|---|
| Privacy | No integration account/credential, analytics SDK or separate maintainer telemetry in the reviewed runtime. Location fields and saved forecast selections are redacted from diagnostics; raw payloads, cache keys and expected private error URLs are omitted. | Providers still receive station/postcode/coordinates and the public source IP. Retention is outside this integration's control. Ordinary state attributes, HA-wide debug logs and user-supplied cards need separate sharing review. |
| Architecture | Typed entry-owned runtime, borrowed HA session, source/coordinator separation, bounded parsing and independent optional-source failures; native lifecycle tests. | Strict typing and a separately distributed client-library boundary are not fully established. Large coordinator/sensor/config-flow modules and shared diagnostic ownership retain maintenance costs and documented limits. Coverage is evidence, not architecture certification. |
| Security | Fixed-host HTTPS/TLS, no redirects, wire/decompression limits, bounded timeouts/retries and cancellation tests. Hash-locked minimum/current fixtures, explicit Python/pip/certifi/uv floors, offline uv, pinned actions, least-privilege workflows and actual-merge verification. Exact PyPI vulnerability metadata checks returned no active advisories for either 138-pin test lock. | Current private alert state and some repository settings were inaccessible through the review connection. There is no complete security clearance or independent offensive assessment. Required approving reviews are zero; SonarCloud is checked in the project workflow but is not a ruleset-required check. |

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

## Follow-up priorities

1. Verify current Dependabot/CodeQL/secret-scanning alert counts and enabled
   secret scanning/push protection with the owner's authenticated read access.
   An inaccessible API is unknown, not an empty alert list.
2. Review making SonarCloud required, dependency-update automation and a
   whole-lock vulnerability gate. Fixed floors do not detect every future advisory.
3. Continue wind-statistics, translation and device-lifecycle work; obtain
   independent review of data migrations and sensitive changes.
4. Verify HA account/network/backup controls separately. This repository review
   does not prove MFA, firewall rules, external exposure or restoration on a host.
