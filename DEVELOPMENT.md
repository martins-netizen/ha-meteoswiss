# Development branch

This repository is a fork of
[`LNKtwo/ha-meteoswiss`](https://github.com/LNKtwo/ha-meteoswiss).

## Documentation and communication language

Use **English** for GitHub project documentation, pull request titles and
descriptions, and maintainer-written project discussions. Canonical guide
filenames and current links use English names. Historical link redirects may
retain their old filenames, but their explanatory text is English.

Operator-specific documentation and conversation in ChatGPT remain **German**.
Do not copy private operating notes, hosts, account details or backups into this
public repository. UI translation catalogues remain DE/EN/FR/IT. Quoted provider
messages, exact UI evidence, place names and established identifiers retain
their original spelling.

Before merging a documentation PR, check language consistency, relative links
and anchors, factual status against its evidence, and required GitHub checks.
For changes to supported versions or setup steps, update the README, user
guides and changelog together. Keep historical release evidence scoped to its
published version.

## Supported Home Assistant versions

New releases require **HA 2026.11.0 or newer**. Published stable 8.3.4
declared HA 2026.8.3 as its minimum. For HA 2026.8.3 through 2026.10.x, use
the [8.3.4 release instructions](https://github.com/martins-netizen/ha-meteoswiss/blob/8.3.4/docs/GETTING_STARTED.md)
and upgrade HA before moving to a newer MeteoSwiss release.

Older Home Assistant Core releases pinned dependencies affected by published
security advisories. Core 2026.10.4 still used Pillow 12.3.0, which is affected
by several image-decoding vulnerabilities. Core 2026.11.0 provides a newer
dependency set with fixes for these known issues.
[Core 2026.8.3 pins](https://github.com/home-assistant/core/blob/2026.8.3/homeassistant/package_constraints.txt)
· [Core 2026.10.4 pins](https://github.com/home-assistant/core/blob/2026.10.4/homeassistant/package_constraints.txt)
· [Core 2026.11.0 pins](https://github.com/home-assistant/core/blob/2026.11.0/homeassistant/package_constraints.txt)

| Dependency | Core 2026.8.3 | Core 2026.11.0 and 2026.11.1 | Example security advisory |
|---|---:|---:|---|
| Pillow | 12.3.0 | 13.0.0 | [GHSA-5x8w-8jj5-q52h](https://github.com/advisories/GHSA-5x8w-8jj5-q52h) |
| PyJWT | 2.13.0 | 2.15.1 | [GHSA-ffc3-869f-jxw9](https://github.com/advisories/GHSA-ffc3-869f-jxw9) |
| aiohttp | 3.14.3 | 3.14.5 | [GHSA-9xw5-w5jj-pvcg](https://github.com/advisories/GHSA-9xw5-w5jj-pvcg) |
| cryptography | 48.0.1 | 50.0.2 | [GHSA-g6cj-pr64-35w5](https://github.com/advisories/GHSA-g6cj-pr64-35w5) |
| uv | 0.11.31 | 0.13.6 | [GHSA-hq85-5cpj-mr62](https://github.com/advisories/GHSA-hq85-5cpj-mr62) |

## CI Python security baseline

The compatibility jobs request the latest stable Python **3.14** patch release
with `actions/setup-python`'s `check-latest: true`. A check before the first
dependency installation requires **3.14.10 or newer within 3.14** and
**pip 26.2.2 or newer**. It records the selected versions without local account
or file paths. An older cached interpreter or installer stops the job.

[Python 3.14.10](https://www.python.org/downloads/release/python-31410/)
blocks the compromised eMudhra intermediate CA keys in the `ssl` module and
includes additional security fixes. Future security advisories may require
raising this floor again. The latest-patch lookup is intentional; see the
[setup-python documentation](https://github.com/actions/setup-python/blob/5fda3b95a4ea91299a34e894583c3862153e4b97/docs/advanced-usage.md#check-latest-version).

Dependency installation uses pip with `requirements_ci_security.txt`, which
requires **certifi 2026.10.19 or newer**. A second check after installation
rejects outdated pip or certifi, verifies the selected HA version and reports
the uv policy before tests run. Prerelease package versions fail this check.
These floors follow the [Python security announcement](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576).

The minimum fixture uses **HA 2026.11.0** and the current fixture uses
**HA 2026.11.1**. Both use the corresponding official **pytest-homeassistant**
release and **uv 0.13.6**. The installed check requires **uv 0.13.4 or newer**
in both jobs. The compatibility job sets
[`UV_OFFLINE=true`](https://docs.astral.sh/uv/reference/environment/#uv_offline)
for all steps, including HA subprocesses. A separate hash-checked pip step
supplies the test dependencies.
Regression tests probe the installed uv binary against a loopback-only index:
offline mode must make no requests, while a local positive control proves the
detector works. No public package index is used by this probe.

## Local compatibility checks

Run these commands from the repository root in an activated, isolated virtual
environment using the supported patched Python and pip described above. Create
a separate environment for each HA fixture. If the bootstrap check fails,
update or recreate that environment using its supported Python/package manager;
do not bypass the check or modify Home Assistant's managed runtime.

This is the shared local recipe for the README, quality evidence and maintenance
guide. It follows the compatibility job's security, translation and coverage
checks:

```sh
export UV_OFFLINE=true
python scripts/check_ci_security.py bootstrap
python -m pip install --disable-pip-version-check --require-hashes --constraint requirements_ci_security.txt -r requirements_test.txt
python -m pip check
python scripts/check_ci_security.py installed --ha-version 2026.11.1
python -m compileall -q custom_components/meteoswiss tests
python scripts/check_translations.py
python -m pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
```

For the minimum-HA job, substitute `requirements_test_min.txt` and `2026.11.0`.
Install each requirements file in its own fresh environment. The official
test package version must match HA. The plugin registers itself.
[`home-assistant/core` test package](https://github.com/home-assistant/core/tree/2026.11.0/packages/pytest-homeassistant)
`tests/ha_helpers.py` supplies configuration-entry, clock and Recorder helpers.
`pytest.ini` disables the separate respx plugin so
HA can install its httpx alias first, and sets function-scoped asyncio fixtures.
Writable HA test configuration uses a temporary directory in both fixtures.
The station reload regression checks that exact entity IDs and the personal
name in HA's entity registry survive a station change. It also checks the
friendly name, which includes the device name in both supported fixtures.
These checks do not update the separately pinned validator containers, an
installed Home Assistant instance, or existing local environments. Those
runtimes and certificate stores need their own security review.

## Test dependency lockfiles

`requirements_test.in` and `requirements_test_min.in` declare the current and
minimum fixture inputs. Their corresponding `.txt` files are generated universal
lockfiles: direct and transitive test dependencies have exact versions and
SHA-256 hashes, with platform markers where required. CI and the local recipe
install these lockfiles using pip's `--require-hashes` and verify the installed
graph with `pip check`. The separate certifi security constraint still applies.
The bootstrap pip version remains controlled by the pre-installation security
check; it is not supplied by either fixture lockfile.

Regenerate deliberately in an isolated maintenance environment with a patched
uv (at least 0.13.4; generated and verified with 0.13.6), outside the frozen
minimum fixture. These commands need network access; CI tests retain
`UV_OFFLINE=true` throughout:

```sh
UV_OFFLINE=false uv pip compile --universal --python-version 3.14.10 --generate-hashes --output-file requirements_test.txt requirements_test.in
UV_OFFLINE=false uv pip compile --universal --python-version 3.14.10 --generate-hashes --output-file requirements_test_min.txt requirements_test_min.in
```

An existing lockfile retains its resolved versions by default. For an intended
dependency update, add `--upgrade-package NAME` and review every resulting
change. Commit changed inputs and regenerated lockfiles together, then install
both into fresh environments and run the complete compatibility/coverage
recipe. Keep generated hashes and upstream pins. When changing the minimum,
update the advertised requirement, CI matrix and matching HA/test-package pins
together. Keep private index URLs, credentials and machine-specific paths out
of the generated files.

## Complete test-lock vulnerability gate

The separate `Test dependency advisories` job queries known vulnerability
metadata for every package/version selected by both universal locks, including
foreign-platform markers. The existing required `tests` aggregate requires its
success alongside both HA fixtures, Hassfest and universal-lock verification.
Every active advisory and every unknown result fails the job; no package or
advisory ignore switch exists. Fixed version floors remain necessary and do not
replace this check.

The isolated network job installs only the existing hash-pinned compiler/parser
subset after the same bootstrap security check. It uses no integration data or
GitHub/API secret and does not install an HA fixture. The HA compatibility
jobs remain offline for uv. A separate daily/manual `Dependency audit` workflow
uses identical steps, `contents: read`, pinned actions and no persisted checkout
credentials. Actual GitHub scheduling/notification behaviour needs its own
acceptance after merge.

From a supported hash-installed maintenance environment:

```sh
python -m scripts.check_dependency_advisories --output dependency-advisories.json
```

The JSON records selected versions, both lock inventories, active/withdrawn IDs,
unknown error codes and query start time. Only public package/version names are
sent to PyPI. The [full contract](docs/DEPENDENCY_ADVISORIES.md) records transport
bounds, proxy handling, response validation and limitations. A service outage
must recover before rerunning; a vulnerability needs a reviewed compatible
input/lock update and both full suites. Do not override HA pins or weaken the
aggregate/security gates. This check neither merges updates nor deploys HA.

## Scheduled dependency proposals

`.github/dependabot.yml` schedules weekly GitHub Actions and Python dependency
checks against the default `development` branch. The Python ecosystem is `pip`
at `/`, matching the existing `.in`/`.txt` fixture files. There is no `uv.lock`
project in this repository. Security alerts and security updates remain enabled
independently of the version-update schedule.

Python version proposals use `lockfile-only`, including transitive dependencies.
They must fit the reviewed input constraints; they do not automatically raise
the minimum HA version or independently update the matching HA/test-package
pins. Exact direct tool pins also need an intentional input change. Security
fixes that require a newer HA dependency set need a coordinated fixture and
baseline PR rather than an override of HA's pins. There are no ignored packages
or excluded fixture files in the Dependabot configuration.

Dependabot's pip-compile updater does not use this repository's universal uv
command. A separate read-only CI job therefore recompiles copies of both locks
with their hash-pinned uv compiler and compares package selections, versions,
extras, platform markers and hashes. It rejects a Linux-only lock even when
the Linux compatibility tests pass. The existing `tests` merge gate requires
this job as well as both HA fixtures and Hassfest. Network resolution is confined
to this maintenance job; the HA test jobs keep `UV_OFFLINE=true` throughout.

If an automated proposal fails the universal-lock check, inspect its intended
update and regenerate both locks with the commands above before requesting
review. Keep the resolved input versions, hashes and markers together. Do not
merge a proposal by disabling this check, changing the advertised minimum to
match an accidental update, or suppressing its security alert.

Review the actual managed update job and its proposal separately from graph
submissions or empty update checks. Before merging, bring the proposal branch
up to date with `development` and wait for all required checks on that exact
head. The strict branch policy requires this base alignment even when an older
head has green checks. Keep the required checks active and use the regular
approved squash-merge process. There is no automatic merge or HA installation.

### Verified managed proposals — 12 November 2026

Version updates are enabled for this fork. The first managed GitHub Actions
and pip jobs both reached the PR-creation endpoint successfully (HTTP 204),
created their proposals and completed the reviewed merge path:

| Ecosystem | Proposal | Merged update |
|---|---|---|
| GitHub Actions | [#100](https://github.com/martins-netizen/ha-meteoswiss/pull/100) | SHA-pinned setup-python 7.0.0 → 7.1.0 and CodeQL Action 4.37.9 → 4.39.3. |
| pip / requirements | [#101](https://github.com/martins-netizen/ha-meteoswiss/pull/101) | bleak 3.0.2 → 3.1.0 and regex 2026.11.7 → 2026.11.9 in both universal test locks. |

The initial Python proposal reduced each lock from 138 to 123 selections and
changed platform markers/extras. The universal-lock guard and its regression
test correctly rejected it. Both locks were regenerated with the native
universal uv compiler before merge: all 138 selections and their platform
conditions were restored, with only the two reviewed package versions and
their hashes changed. This correction is a reviewed maintenance step; future
pip-compile proposals still need the same universal-lock verification.

Both actual merge commits passed the eight regular checks, including HA
2026.11.0 and 2026.11.1 with 2,357 tests and 83 subtests each, the security and
coverage gates, and both universal locks with 138 selections. See the merge CI
for [#100](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43218969192)
and [#101](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43226584044).
The pip dependency-graph update after #101 also completed successfully; it is
separate from the required merge checks. This acceptance covers the configured
pip/requirements path; other package managers and lockfile formats require
their own acceptance. Published releases and HA installations are separate.

## Branch policy

The `development` branch is an integration branch for changes that have been
tested locally while the corresponding upstream pull requests are pending.

The following rules apply:

- `main` stays aligned with upstream `LNKtwo/main`.
- `fix/*` and `feat/*` branches stay focused on individual upstream pull requests.
- `development` combines the locally validated changes for continued testing
  and development.
- Own prereleases may be tagged from approved, tested `development` commits;
  they remain clearly identified as fork releases, not upstream releases.
- Changes should remain small and reviewable so they can be proposed upstream
  independently.
- This branch is not presented as an official MeteoSwiss integration release.

See `docs/ARCHITECTURE.md` and `docs/MAINTENANCE.md` for data contracts,
localisation, compatibility checks and release acceptance.

If upstream accepts a change, compare the accepted implementation and reconcile
it through a reviewed PR into `development`. Remove superseded local patches
in that PR without discarding fork-specific corrections. Do not rewrite or
force-push the protected integration branch to refresh its upstream history.
