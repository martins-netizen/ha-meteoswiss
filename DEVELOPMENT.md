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

The supported HA versions keep their upstream dependency pins, including
**uv 0.11.31 for HA 2026.8.3** and **uv 0.12.23 for HA 2026.10.1**. These uv
versions are **not security-patched** and are restricted to offline test use.
The compatibility job sets [`UV_OFFLINE=true`](https://docs.astral.sh/uv/reference/environment/#uv_offline)
for all steps, including HA subprocesses. uv cannot fetch packages in this mode;
the separate pip installation step supplies the test dependencies. The check
accepts older uv only for those exact HA/uv pairs, and rejects missing offline
mode even with newer uv. Review this exception when changing the HA matrix.
Do not use these legacy fixture environments for online uv operations.
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
python -m pip install --disable-pip-version-check --constraint requirements_ci_security.txt -r requirements_test.txt
python scripts/check_ci_security.py installed --ha-version 2026.10.1
python -m compileall -q custom_components/meteoswiss tests
python scripts/check_translations.py
python -m pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
```

For the minimum-HA job, substitute `requirements_test_min.txt` and `2026.8.3`.
These checks do not update the separately pinned validator containers, an
installed Home Assistant instance, or existing local environments. Those
runtimes and certificate stores need their own security review.

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
