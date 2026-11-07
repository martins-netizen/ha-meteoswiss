# 8.3.4b1: publication and reported short operation check

**Evidence version:** 1.0 · **Updated:** 7 November 2026

[8.3.4b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4b1),
release **437718127**, was published on **7 November 2026 at 17:12:54 UTC**.
It is an immutable test prerelease, draft=false and prerelease=true.
**8.3.3 / release 429354633 remains latest stable.**

## Approved source and immutable publication

The release tag targets regular packaging [PR #90](https://github.com/martins-netizen/ha-meteoswiss/pull/90)
squash merge **1e5c5d1a7fc1c18d520e99189ae4dd5894621706**, merged on
**7 November 2026 at 16:20:20 UTC**, tree
**de678c1b9ade03b1519ba091a787497d84e5bfd7**. Its sole parent is the reviewed
#88/#89 source **5a7eae00963d47294281da8812cb1ede35713b7f**. The actual merge
tree equals the reviewed package tree; the source branch was deleted.

All **39 non-version files** of the **41-file component** match that source.
Only manifest.json/version.py become **8.3.4b1**. HACS/CH, workflows, dependency
locks, icons and four **219-key** translation catalogues remain unchanged.
The beta delivers diagnostic defaults, virtual service metadata and accurate
Open-Meteo current-source labels/attribution. It adds no device cleanup pass.

Publisher V1.7 receipt and independent GitHub reads agree on release ID/time,
tag/source, flags, the fourteen unchanged older tag mappings and latest stable.
The complete published body equals the export from the immutable approved source,
with relative links pinned to that commit. Body SHA-256:
**be73949d1a650e29a2f3572ce16333bc6f75fe8fe81bfa35919d086653bed2d7**.
Fixed Publisher V1.7 SHA-256:
**dd95d2e28d7aa9ad792509a8a820bad94771d60c7dcd209058003fd27bdfc7e3**.
It performed no HA connection, installation, restart or device call.

The [original release notes](https://github.com/martins-netizen/ha-meteoswiss/blob/1e5c5d1a7fc1c18d520e99189ae4dd5894621706/docs/RELEASE_8.3.4b1.md)
and original focused protocol retain their preparation-time context at that
immutable commit. This later evidence record updates current status without
rewriting the published body, changing its tag or rerunning the publisher.

## Automated evidence

All seven checks succeeded on the actual package merge with the expected
GitHub Actions / SonarCloud provenance: tests, HA 2026.11.0, HA 2026.8.3,
hassfest, Analyze Python, HACS validation and SonarCloud Code Analysis.

- [Package CI 42390792356](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/42390792356)
- [CodeQL 42390792270](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/42390792270)
- [HACS validation 42390792359](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/42390792359)

Local complete packaging suites each passed **2,171 tests plus 83 subtests**
on HA **2026.11.0** and minimum **2026.8.3**. Component coverage is
**3,530/3,531 statements and 976/976 branches**, combined **99.977812%**;
the existing strict coverage and security gates passed unchanged. The twelve
fixed publisher profiles include 45 additional beta-publication cases; the
guarded package-PR helper passed ten offline cases. These are automated package
checks, distinct from the operator report below.

Current tests use the matching official pytest-homeassistant package for
HA 2026.11.0, a separate complete minimum-HA fixture and hash-checked test
dependency locks. CI success does not update or establish the live HA Python
or certificate store and does not independently validate every source value.

## Reported operator acceptance and its limits

After verified publication and the requested 8.3.4b1 check, the operator reported
**normal operation OK**, **HA Core 2026.11.0 / HA OS 18.4**, and that everything
works, on **7 November 2026**. This completes the agreed short operation check.
No further list of names/IDs, repeat download/restart or observation window
is required. Earlier settings, icon/error, first-install and restore checks
remain complete within their recorded scopes.

The reply directly follows the beta check request; it does not separately
restate the integration version or identify the checked instance as production
hardware or a test VM. It is not an independent file/registry/Recorder audit,
a manual proof of first-registration defaults, or a separate reported inspection
of an alternative-source entry. No blanket manual confirmation of all entities,
all translated failures or every provider is inferred. Native source/registry
tests remain the evidence for those automated paths.

Existing diagnostic choices remain authoritative: enabled helpers are not
expected to disable themselves during an update. No entry deletion, production
source switch, artificial outage, station change or device command is requested.
Historical orphan handling, remaining device classes and rule-specific Gold
review remain separate work. This evidence does not complete Gold, confer an
official HA quality tier or approve/publish stable 8.3.4.
