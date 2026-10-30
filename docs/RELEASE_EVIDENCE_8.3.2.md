# Stable 8.3.2: publication and reported HA acceptance

**Evidence updated:** 30 October 2026

[Stable 8.3.2](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.2),
release ID **426633496**, was published on **28 October 2026 at 12:21:19 UTC**.
It is an immutable, published stable release, not a draft or prerelease, and
the latest-stable endpoint selects that same ID.

## Source and published text

The tag and release target are the approved regular PR #78 squash merge
**aea4c5eab0534a6e675a4f564bde7521df193c58**, tree
**34eb3ee9d660fa4dd322a947f4ea9f609b842e08**. Its sole parent is the accepted
published 8.3.2b1 source **5a39c3cdbf31f0807f52bcb4acb26190cc1e8423**.
All **38 non-version component files** match that beta; only manifest.json
and version.py change to **8.3.2**, within the 40-file component. HACS/CH,
minimum HA 2026.8.3, workflows, security guards and four **200-key** UI catalogues
are retained. The eleven previous tag SHAs remain unchanged.

The publisher receipt and independent GitHub reads agree on the release ID,
time, exact commit, flags and latest selection. The actual published body
reproduces exactly from the approved publisher and its immutable source notes,
including commit-pinned relative links. Body SHA-256:
**79be9796a6a1e25e5654cd986c1d91f428d63e23b142da00db46d09f2b5c2b97**.
Existing tags, published bodies and fixed-profile publishers remain historical
evidence. Do not republish or retag this release to update documentation.

## Checks on the actual merge

All seven actual-merge checks succeeded at that exact SHA with the expected
GitHub Actions/SonarCloud provenance: tests, HA 2026.8.3, HA 2026.10.1,
hassfest, Analyze Python, HACS validation and SonarCloud Code Analysis.

- [CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/40679096036):
  **1,983 tests plus 83 subtests** on each HA **2026.8.3 (48.86 s)** and
  **2026.10.1 (61.33 s)**. Config flow **406/406 statements, 146/146 branches**;
  whole integration **3,516/3,517 statements, 974/974 branches**, combined
  **99.977733%**. Existing strict gates and four exclusions pass unchanged.
- [CodeQL](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/40679096002)
  and [HACS](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/40679095983)
  completed successfully.
- Hosted logs confirm **Python 3.14.10 / pip 26.2.2 / certifi 2026.10.23** and
  **UV_OFFLINE=true**. Historical uv 0.11.31/0.12.23 remain explicitly unpatched,
  offline-only compatibility exceptions. These CI versions do not establish
  the Python or certificate store of an operator's HA installation.

The earlier exact PR head passed eight checks. Those results are separate from
the seven checks on the actual merge, not skipped or missing merge checks.

## Reported operator acceptance

The five focused **8.3.2b1** existing-entry steps were reported positive on
**HA Core 2026.10.4**, as recorded in the [beta protocol](ACCEPTANCE_8.3.2b1.md).
On **30 October 2026**, the operator additionally confirmed the actual HACS
download of **8.3.2**, an HA restart and working operation. This closes the
[short stable update check](ACCEPTANCE_8.3.2.md).

This is reported installed-version/restart/operation evidence. It is not a new
independent file/registry/statistic audit, separate clean installation, or a
newly reported Core/Python version. No repeat of the accepted dialog,
clean-install or restore steps, or new blanket 24-hour wait, is requested.
The unreported intermediate stable 8.3.1 download is not a prerequisite.

## Remaining development

The [quality matrix](QUALITY_SCALE.md) retains open Gold rules. The approved
next sequence is documentation reconciliation, a separate icon-translations
PR, then a separate exception-translations PR with DE/EN/FR/IT and native HA
checks. Later packages address diagnostic defaults, device metadata/classes,
stale grouping and rule-specific exemptions. Existing user choices, identities
and history remain compatibility boundaries. These are development scopes,
not features added to the immutable 8.3.2 release or an official HA quality tier.
