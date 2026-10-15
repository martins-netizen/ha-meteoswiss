# Maintenance and release procedure

1. Keep `main` aligned with `LNKtwo/main`; review upstream changes before
   integrating them into `development`. Keep individual upstream PR branches
   focused. If an upstream fix is accepted, rebuild/rebase the integration
   branch without duplicate patches, preserving the known deployed baseline.
2. Changes go through a branch and PR to protected `development`. Keep required
   check `tests` and CodeQL's `Analyze Python`; do not bypass protection.
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
   and history persist and that both dashboards render Bodenfrost correctly.
5. Update manifest.json, version.py and CHANGELOG.md together. `8.2.0b1` is the
   prepared prerelease version; this branch does not publish or deploy it.
   Tag the approved tested commit on `development`, not the upstream mirror
   `main`. The first release should be a GitHub prerelease. HACS must point at
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
