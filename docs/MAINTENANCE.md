# Maintenance and release procedure

1. Keep `main` aligned with `LNKtwo/main`; review upstream changes before
   integrating them into `development`. Keep individual upstream PR branches
   focused. If an upstream fix is accepted, rebuild/rebase the integration
   branch without duplicate patches, preserving the known deployed baseline.
2. Changes go through a branch and PR to protected `development`. Keep required
   checks `tests`, CodeQL's `Analyze Python` and `HACS validation`; do not bypass
   protection. External PRs follow the [unprivileged CodeQL review procedure](CODEQL_FORK_REVIEW.md);
   a skipped analysis is not a successful security scan.
3. Run `python scripts/check_translations.py` and the complete tests with both
   `requirements_test_min.txt` (HA 2026.8.3) and `requirements_test.txt`
   (HA 2026.10.1). Add regression tests for real failures. Measure line/branch coverage and run
   `scripts/check_quality_coverage.py`; review the per-module report and
   `docs/QUALITY_SCALE.md` before making any quality-level claim. Review Hassfest and
   CodeQL results; do not suppress a failed check to obtain a release.
4. Before release, verify the installed source/commit and create a restorable
   backup including the integration and affected dashboard configuration.
   Run a live read-only check of observations, forecasts, active/upcoming alerts,
   pollen and precipitation statistics. Test an unavailable warning feed with
   mocks; do not simulate danger by actuating devices. Verify that existing IDs
   and history persist and that active/upcoming warning consumers use the
   verified catalogue and preserve the provider's concrete event text.
5. Update manifest.json, version.py and CHANGELOG.md together when preparing a
   release. Stable `8.2.0` was published on 22 October 2026; later development
   changes remain unreleased until separately packaged and accepted. Tag only
   the approved tested commit on `development`, not the upstream mirror `main`;
   preserve existing immutable stable/beta tags. HACS must point at
   `martins-netizen/ha-meteoswiss` and the selected tested release; never infer
   the installation's source or change it without checking the live state.
6. Review HA breaking changes before upgrades. Review dependencies, GitHub
   Actions and security alerts regularly. Existing GitHub monitoring continues;
   an unanswered upstream PR does not prevent maintenance of the fork. No
   automatic merging or device deployment is introduced.
7. If a deployment fails, restore the previous integration backup and restart
   HA. Do not delete/recreate config entries, entity registries or statistics.

CI and release records are the reproducible evidence for a version. Record
manual acceptance with the actual installed commit/version and HA version.
Do not record tokens, account data or full private diagnostic payloads.

Follow [the publication checklist](PUBLISHING.md) for repository metadata,
the official HACS validation, local brand assets and explicit release selection.
A passing HACS check does not complete live acceptance or
award a Home Assistant Quality Scale tier.

## Local tool input boundaries

`python scripts/check_quality_coverage.py` takes no arguments. It reads only
`coverage.json` beside this repository's root README, independently of the
current working directory, and rejects a symbolic-link report. Generate that
file with the documented pytest coverage command before each gate run; a
different report pathname is no longer a supported argument. The per-module,
strict source/flow, branch-coverage and aggregate requirements are unchanged.

The candidate-specific [8.3.0b1 publisher](PUBLISHING.md#next-candidate-830b1)
adds read-only preflight and one prerelease-only creation path; its tests exercise
source equality, check provenance, old tags, stable preservation and uncertain
writes. It performs no HA deployment. Keep it separate from the historical
8.2.0 tools below.

All three historical versioned release helpers use Bash `[[ ... ]]` conditions, including
their help and argument guards. Their embedded Python publication code, fixed
release targets, commit/check validation and immutable-tag protections remain
unchanged. These are historical package-specific recipes, not publishers for
the next development release. This maintenance correction neither creates a
release nor changes already published scripts/tags or a Home Assistant instance.

The local tool regressions run without HA or GitHub access:

```sh
python -m unittest discover -s tests -p test_development_tools.py -v
```

They cover fixed-root report selection, rejected path arguments/symlinks,
retained coverage failures and all three shell entry points. Existing mocked
publisher tests continue to verify publication/refusal/retry behaviour.
Removing source patterns is not a claim that SonarQube Cloud has reanalysed
the commit or computed a quality gate; verify its actual result separately.

See [SonarQube Cloud source/test classification](SONAR_ANALYSIS.md) for the
automatic-analysis configuration, Python version and coverage evidence limits.
