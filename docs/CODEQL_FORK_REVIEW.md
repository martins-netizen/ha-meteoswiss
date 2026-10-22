# CodeQL for external pull requests

**Configuration review:** 22 October 2026.

The Python CodeQL job now runs for all pull requests targeting `development`,
including public-fork contributions. The old same-repository condition is
removed; a skipped job is not evidence of analysis.

## Permission and execution boundary

- Use `pull_request`, never privileged `pull_request_target`/`workflow_run`
  execution of contributor code. Checkout retains the default reviewed merge
  tree rather than substituting a head SHA from an untrusted event field.
- Workflow permissions default to none. Only the analysis job requests
  `contents: read` and `security-events: write`, the latter for result upload on
  trusted push runs. For public-fork PRs GitHub downgrades the token to read-only
  and withholds repository secrets. No secrets or custom token are referenced.
- GitHub explicitly allows code-scanning uploads on `pull_request` even with
  read-only scopes. Do not switch to a privileged trigger or supply a PAT to
  work around a failed upload.
- Retain full-SHA-pinned checkout/init/analyze actions, ephemeral GitHub-hosted
  runners, `persist-credentials: false`, the timeout and concurrency boundary.
  There is no dependency-install, contributor script, autobuild or privileged
  second upload workflow in this analysis job.
- Keep the repository's existing contributor-workflow approval policy. Review
  the submitted diff and workflow changes before approving an external run.
  This change does not weaken repository settings or branch rules.

Primary references: GitHub's
[unprivileged PR boundary](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target),
[code-scanning upload exception](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/resource-not-accessible)
and [PR scanning configuration](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options).

## Evidence and first external contribution

The workflow passes zizmor 1.31.1 offline analysis in auditor mode without
findings or suppressed findings. Online audits are not claimed. Own-repository
PR and post-merge CodeQL runs verify this exact revision once their checks
complete. They do not establish a completed foreign-fork execution.

For the first real external PR, inspect the run after ordinary maintainer
approval: verify the expected PR merge revision, successful Initialize CodeQL
and Analyze steps, and uploaded code-scanning results. A missing, skipped or
failed `Analyze Python` is not acceptance evidence. Investigate permissions or
upload failures within the unprivileged design; do not bypass required checks.
No synthetic external contributor/fork or outside message was created merely
to claim this evidence. No live HA test is needed for this CI-only change.
