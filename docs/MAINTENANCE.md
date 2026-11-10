# Maintenance and release procedure

1. Keep `main` aligned with `LNKtwo/main`; review upstream changes before
   integrating them into `development`. Keep individual upstream PR branches
   focused. If an upstream fix is accepted, rebuild/rebase the integration
   branch without duplicate patches, preserving the known deployed baseline.
2. Changes go through a branch and PR to protected `development`. Keep required
   checks `tests`, CodeQL's `Analyze Python` and `HACS validation`; do not bypass
   protection. External PRs follow the [unprivileged CodeQL review procedure](CODEQL_FORK_REVIEW.md);
   a skipped analysis is not a successful security scan.
3. Follow the [local compatibility checks](../DEVELOPMENT.md#local-compatibility-checks)
   in separate environments for `requirements_test_min.txt` (HA 2026.11.0)
   and `requirements_test.txt` (HA 2026.11.1). Use the matching official test
   package in both environments.
   Apply the Python/pip bootstrap,
   hash-checked generated lockfiles, `pip check`, certifi constraint,
   installed-version check and offline uv policy before
   running the complete translations/tests/coverage sequence. Add regression
   tests for real failures. Retain `scripts/check_quality_coverage.py` and review
   the per-module report and
   `docs/QUALITY_SCALE.md` before making any quality-level claim. Review Hassfest and
   CodeQL results; do not suppress a failed check to obtain a release.
   For dependency maintenance, update the `.in` inputs and regenerate their
   universal SHA-256 lockfiles together using the
   [documented maintenance environment](../DEVELOPMENT.md#test-dependency-lockfiles).
   Keep the tested minimum aligned with `hacs.json` and review transitive
   dependency updates explicitly.
4. Before release, verify the installed source/commit and create a restorable
   backup including the integration and affected dashboard configuration.
   Run a live read-only check of observations, forecasts, active/upcoming alerts,
   pollen and precipitation statistics. Test an unavailable warning feed with
   mocks; do not simulate danger by actuating devices. Verify that existing IDs
   and history persist and that active/upcoming warning consumers use the
   verified catalogue and preserve the provider's concrete event text.
5. Update manifest.json, version.py and CHANGELOG.md together when preparing a
   release. Align the minimum HA requirement, installation guidance and
   release notes. Use the [release status](../README.md#release-status) and
   [release evidence](RELEASE_READINESS.md) to distinguish published and
   planned changes. Tag the approved tested commit on `development` and
   preserve existing immutable stable/beta tags. Marketplace (HACS for 8.3.4
   on older HA) must point at
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
[HACS catalogue admission](HACS_ACCEPTANCE.md#hacs-catalogue-admission) is complete.
Keep **Settings → Marketplace** first in user guides for HA 2026.11+, with
HACS guidance for 8.3.4 on older HA and custom registration as a fallback. Preserve
historical HACS evidence and technical `hacs.json`/validation names; UI wording
does not establish a new live acceptance result. HACS checks and admission remain separate
from live acceptance and the [Quality Scale engineering checklist](QUALITY_SCALE.md).

## Local tool input boundaries

`python scripts/check_quality_coverage.py` takes no arguments. It reads only
`coverage.json` beside this repository's root README, independently of the
current working directory, and rejects a symbolic-link report. Generate that
file with the documented pytest coverage command before each gate run; a
different report pathname is no longer a supported argument. The per-module,
strict source/flow, branch-coverage and aggregate requirements are unchanged.

The historical [8.3 publishers](PUBLISHING.md#stable-830) retain version-specific
preflight and publication paths. Their tests exercise source equality, check
provenance, old tags, stable selection/preservation and uncertain writes. They
perform no HA deployment. Keep these fixed-version tools as historical recipes;
do not reuse them for a future release. Regression profiles run independently
of the current root version.

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
