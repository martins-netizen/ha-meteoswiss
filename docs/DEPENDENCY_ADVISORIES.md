# Complete test-lock vulnerability checks

**Status:** unreleased CI/security follow-up after PR #106. Component files,
test dependency selections, hashes, platform support and HA versions are unchanged.

The `Test dependency advisories` CI job checks both universal test lockfiles.
The existing required `tests` aggregate also requires this job to succeed.
A separate `Dependency audit` workflow schedules the same read-only steps daily
at 05:17 UTC and supports manual dispatch. GitHub controls actual scheduling and
workflow notifications; this does not create an automatic update or merge.

## Inventory and result

The checker reuses the strict hash-lock parser. It includes every selection,
including Windows/macOS markers, and deduplicates only identical package/version
pairs. The reviewed locks each contain 138 selections and together contain 140
distinct pairs. This is a full-lock check, rather than a scan of only packages
installed on the Linux runner. Inputs are bounded and symlink locks are rejected.

For each pair, it requests PyPI's [release-specific JSON metadata](https://docs.pypi.org/api/json/#get-a-release)
and verifies the returned package and version. PyPI supplies known advisories in
`vulnerabilities`; a valid upstream `withdrawn` timestamp records a retraction.
The checker blocks on every active advisory, regardless of severity or whether
a patched version is available. A missing/invalid inventory, identity mismatch,
invalid withdrawal, future withdrawal or failed request is an unknown result
and also fails the job. Only valid, already effective withdrawals are excluded.
There are no package exclusions, ignore lists or alternate-index switches.

## Transport and supply-chain boundaries

Requests use only `https://pypi.org/pypi/<project>/<version>/json`, with verified
origin TLS, no redirects, a two-MiB response limit and a ten-second socket timeout.
Eight workers perform at most two attempts per pair. Only transient transport
errors and selected transient HTTP statuses can retry, with one second of delay;
an excessive/invalid Retry-After stops that pair. The job has a 15-minute bound.
Standard configured proxies remain supported; proxy settings, raw exception
strings and response bodies never enter reports. No API credential or cookie is
added. The report contains package/version identities, lock owners, advisory IDs,
fixed error codes, aggregate counts and the query start time.

The isolated job checks the existing Python/pip bootstrap floor and installs
only the existing SHA-256-pinned compiler/parser subset. It does not execute uv
or install either HA fixture. Both HA compatibility jobs retain their
`UV_OFFLINE=true` policy and full regression/coverage checks. Workflows keep
`contents: read`, pinned actions and checkout credential persistence disabled.

## Reproduce and handle a failure

Use the patched, hash-installed maintenance environment from
[DEVELOPMENT.md](../DEVELOPMENT.md#local-compatibility-checks):

```sh
python -m scripts.check_dependency_advisories --output dependency-advisories.json
```

The command returns nonzero for an active advisory, unknown result, invalid lock,
outdated bootstrap or failed report write. Inspect its safe package/version/ID
diagnostic and the JSON report. For a service outage, confirm recovery and rerun;
do not change failure into success. For a real vulnerability, coordinate the
matching HA/test-package inputs and regenerate both universal locks with their
platform markers and hashes, then run the complete compatibility suites. Do not
override HA's dependency pins, lower a security floor, suppress an advisory or
dismiss an alert to make CI pass. [Dependency maintenance](../DEVELOPMENT.md#test-dependency-lockfiles)
and [confidential reporting](../SECURITY.md) retain their existing procedures.

## Evidence and limits

Regression tests cover all-platform inventory, deduplication, unsafe inputs, exact
release identity, active/withdrawn/invalid advisories, malformed/ambiguous JSON,
TLS/redirect/body limits, bounded retries, unknown-result failure, redacted CLI
errors and the aggregate gate for failed/skipped/cancelled advisory jobs.
The initial live check found 140/140 known results and no active advisories;
its timestamped report is a point-in-time observation. A separate request of a
known vulnerable old release checks the positive path without installing it.
Actual new PR checks and scheduled-run acceptance remain separate.

PyPI coverage and publication delay limit what this feed can establish. A clean
result does not prove absence of unknown vulnerabilities, malicious packages,
OS/container/action issues or exposure in an installed HA environment. The
dated owner-authenticated GitHub inventory is separate. Full Gold, independent
security review and operator acceptance are not established by this CI change.
