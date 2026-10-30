# Stable 8.3.3: publication and reported HA acceptance

**Evidence updated:** 30 October 2026

[Stable 8.3.3](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.3),
release **429354633**, was published on **30 October 2026 at 18:21:55 UTC**.
It is latest stable, immutable, draft=false and prerelease=false.

## Source and published text

The tag/release target is the approved normal PR #83 squash merge
**3d4fad2330c89f134eba208e8b2db55705177e7d**, merged at **18:17:03 UTC**,
tree **b53df969640e8b15df690de59a95639f3735e05c**, exactly matching the approved
PR tree. Its sole parent is accepted published beta
**d9fbc3fd49220b0ecc019d2babe0c173c46986f5 / release 429321251**.

All **39 non-version files** of the 41-file component match that beta; only
manifest.json/version.py become 8.3.3. HACS/CH, minimum HA, workflows, security
guards, icons.json, four **219-key** catalogues and English/source parity remain.
All thirteen older tag mappings were independently re-read and unchanged.

Publisher receipt/log and independent GitHub reads agree on release ID/time,
tag/source, flags and latest selection. The complete published body equals
the approved export with relative links pinned to that immutable commit.
Body SHA-256:
**62d7b02e39bec84162e0cc5b3770600c4c87109b83be473f803fd59c5f877de0**.
The fixed Stable Publisher V1.6 SHA-256 is
**51d59fb08324a24afec94c9e98e5c8a4f307a3819c2a882b170ac819c1691e21**.
It performed no HA write, restart or device call. Existing tags and published
bodies remain immutable; later documentation edits do not retag this release.

## Checks on the actual merge

All seven checks succeeded on that exact merge with expected GitHub Actions /
SonarCloud provenance: tests, HA 2026.8.3, HA 2026.10.1, hassfest, Analyze Python,
HACS validation and SonarCloud Code Analysis. No extra commit statuses were
outstanding and no skipped check was counted as a pass.

- [CI 41105597207](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/41105597207):
  **2,096 tests plus 83 subtests** on HA **2026.8.3 (43.83 s)** and
  **2026.10.1 (71.36 s)**. Flow **406/406 statements, 146/146 branches**;
  component **3,516/3,517 statements, 974/974 branches**. Existing strict
  coverage gates and four exclusions pass unchanged.
- [CodeQL 41105597266](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/41105597266)
  and [HACS 41105597240](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/41105597240)
  succeeded. SonarCloud Code Analysis also succeeded.
- Hosted logs confirm **Python 3.14.10 / pip 26.2.2 / certifi 2026.10.23 /
  UV_OFFLINE=true**. Historical HA uv 0.11.31/0.12.23 are explicit unpatched
  offline-only compatibility exceptions, not claims of patched uv.

All eight earlier exact-PR-head checks also passed. These are separate from
the seven checks on the actual merge. CI versions do not patch or establish
the Python/certificate store of the operator's HA installation.

## Reported operator acceptance

After confirmed beta publication, the operator reported **icons/personal
choices OK and normal operation OK** on **HA Core 2026.10.4 / HA OS 18.4**;
see the [beta check](ACCEPTANCE_8.3.3b1.md). Native tests load all 19 exception
keys in DE/EN/FR/IT. No deliberate source failure or manual exercise of every
translated error is inferred from that visual/operation report.

After stable publication, the operator explicitly confirmed **8.3.3 installed
and normal operation OK** on **30 October 2026**. This closes the
[short actual stable update](ACCEPTANCE_8.3.3.md). The report does not restate
Core/OS/Python, separately establish the restart, or independently audit files,
registry, statistics or every provider. It is not inferred from publication.

The earlier shared-settings, clean-install and restore checks remain complete
within their scopes. No further release-specific HA test or new blanket wait
is pending. Remaining Gold rules and future features are separate work; this
does not confer an official HA quality tier on a custom integration.
