# Bounded release review — 22 October 2026

**Scope:** promotion of published **8.2.0b2** at
`80bf9195ecc3d42d9e4d1beb4ce8143e2c2df2c8` to the first stable **8.2.0**.
This is a source/documentation/acceptance reconciliation, not a penetration
test, an independent usability study or an official HA quality assessment.

## Candidate boundary

Keep all 31 non-version component/translation/brand files identical to Beta2.
Only `manifest.json` and `version.py` change their version to 8.2.0. Retain the
same HACS manifest, dependency list, workflows and provider choices. The
guarded stable publisher rejects changes outside those component boundaries.
The stable package is not published by opening or merging its PR.

## Evidence reconciled

Beta1 runtime acceptance, HACS source switch, temporary clean first installation
and isolated restore are complete within their documented scope. On 22 October
the operator also completed Beta2 setup with additional geographic locations
and reported values. The initial pollen-picker walkthrough is therefore
no longer an open general setup task. Exact additional locations/source paths
and a new independent file/registry/statistics comparison were not supplied.
No repeated production migration, deletion or blanket observation is required.

The public HA Core latest-release endpoint returned **2026.10.2** on 22 October;
the project already has test/practical evidence for that patch. The existing
CI labels and pinned requirements are retained, not silently described as a
different CI matrix. Candidate CI results must still be checked at its exact SHA.

## Local verification of stable packaging

Both HA 2026.8.3 and 2026.10.2 pass **859 tests and 14 subtests**. Combined
line/branch coverage is **99.0535%**, including all 652 measured branches;
existing full-coverage source/flow gates remain satisfied. DE/EN/FR/IT contain
96 matching keys each. Stable-publisher refusals, read-only preflight and
uncertain-write recovery are exercised with mocks, never live publication.
Exact candidate CI and the later post-merge checks are separate gates.

## Architecture and source contracts

The source adapters, coordinators, typed runtime data and HA entities remain
separated. Optional pollen/AQ/UV behaviour and entity/statistics contracts are
unchanged by stable packaging. No release-blocking architectural change was
identified in this bounded comparison. Existing Bronze/Silver gaps are retained
in the quality matrix rather than being treated as completed by promotion.

## Security findings retained with an explicit boundary

| Finding | Current evidence and release treatment |
|---|---|
| STAC asset destinations and HTTP response limits | Observation and hourly-archive clients receive asset URLs from the fixed official HTTPS STAC service. The selected `href` is not consistently restricted to an HTTPS destination, redirects use the session default, and some bodies are fully read before parsing. These are real hardening gaps. This review did not demonstrate attacker control over official TLS metadata or a concrete exploit, and it does not prove the absence of vulnerabilities. No new URL input or fetch surface is introduced by this package. Retain as priority scoped hardening after the unchanged-runtime release; reassess if a trust-boundary vulnerability is established. |
| External-fork CodeQL | `codeql.yml` deliberately skips foreign-fork PRs. Current release work is in this repository and is analysed; the skip does not establish safe analysis of external code. Before accepting an external contribution, provide an actually analysed, read-only and secret-free route. Do not execute untrusted code using privileged `pull_request_target`. This remains open and is not waived by this release. |
| Repository protection | The active development ruleset requires PRs, squash/linear history, resolved discussions and successful `tests`, `Analyze Python`, `HACS validation` checks bound to GitHub Actions 15368. Deletion/force pushes are blocked, with no bypass actors. Zero required external approvals are appropriate to the present single-maintainer workflow but do not constitute independent review. |
| Live alert/settings evidence | Existing reports and source checks are scoped evidence. This connector does not expose the code-scanning alert endpoint; this review cannot assert zero open alerts or independently reverify every security setting. Keep the established private reporting route. |

The reviewed risk boundary is unchanged public-provider fetching, not arbitrary
user-supplied destinations. Source hardening should cover scheme/host/port,
redirect targets, compressed/decompressed body limits, failure/retry semantics
and real current/archive payload sizes in a separately tested PR. It must not
silently remove official archive data or turn a source outage into zero.

## Documentation review

The primary README, setup and migration paths now distinguish published Beta2
from the prepared stable package. New setup explains the first pollen/source
dialog and the following weather/postcode dialog. Existing Configure options
change the interval and measured-pollen station; they do not edit PLZ or the
weather station. Existing users keep their entry. Four UI languages and the
original upstream attribution remain intact.

This is an editorial check for clear steps and consistent facts. An independent
nontechnical user walkthrough remains an explicitly separate improvement.

## Publication follow-up

Publication required review of the exact stable PR diff, successful checks,
a regular merge and approval of that exact merge commit. The publication tool has
a read-only `--check` mode and can create only the new stable 8.2.0 release;
it preserves both beta tags, rejects code/workflow/HACS drift, and performs no
HA action. Stable publication and actual HACS availability must be recorded
after they happen, never inferred from the manifest version.

**Confirmed afterwards:** the operator published stable 8.2.0 on 22 October
at 08:52:40 Europe/Zurich using the guarded V1.2 helper, run
20261022-085229-238. Its receipt and independent release/latest/tag reads
confirm immutable commit 5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5,
release ID 420392277 and prerelease=false. All seven PR/six post-merge checks
were successful. Local HACS visibility/download remains separate; no new
HA installation or security-hardening completion is inferred.
