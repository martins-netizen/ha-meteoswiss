# SonarQube Cloud analysis

**Document version:** 1.0 · **Date:** 22 October 2026.

This repository uses SonarQube Cloud automatic analysis. Its configuration is
`.sonarcloud.properties` at the repository root, rather than the
`sonar-project.properties` file used for CI-based scanning. The setting follows
the same source/test separation as the SmartGuard project.

Keep `sonar.sources=.` so integration code, local Python/shell tooling and
workflow files remain in the source scope. Classify `tests` through
`sonar.tests=tests` and remove `tests/**` only from the production-source scope.
Those files still belong to test analysis; they are not excluded from testing
or removed from the repository. Do not replace this with a blanket exclusion
of scripts or runtime files. Python 3.14 matches both supported HA test jobs.

This addresses the warning that test-like files were detected without an
explicit `sonar.tests` definition. The configuration must be present on the
default branch for automatic analysis. Check the next actual analysis to
confirm that the classification warning disappears; a green PR quality gate
alone is not proof that the default-branch warning has cleared.

Automatic analysis does not import the pytest coverage report. The enforced
line/branch coverage evidence remains in the existing CI test jobs and their
summaries. A future switch to CI-based Sonar scanning would need a separately
reviewed workflow and disabling automatic analysis to avoid duplicate scans.
This configuration adds no token, workflow, permission or release change.

References:

- [Automatic analysis configuration](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/automatic-analysis#additional-analysis-configuration)
- [Source and test scope](https://docs.sonarsource.com/sonarqube-cloud/managing-your-projects/project-analysis/setting-analysis-scope/setting-initial-scope)
