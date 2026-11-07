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

Both HA fixtures keep their upstream dependency pins. The current fixture uses
**HA 2026.11.0** with the matching official **pytest-homeassistant 2026.11.0**
and **uv 0.13.6**, which meets the uv security floor. The minimum fixture keeps
**HA 2026.8.3**, **pytest-homeassistant-custom-component 0.13.357** and
**uv 0.11.31**. That older uv is **not security-patched** and is restricted to
offline test use.
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
python -m pip install --disable-pip-version-check --require-hashes --constraint requirements_ci_security.txt -r requirements_test.txt
python -m pip check
python scripts/check_ci_security.py installed --ha-version 2026.11.0
python -m compileall -q custom_components/meteoswiss tests
python scripts/check_translations.py
python -m pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
```

For the minimum-HA job, substitute `requirements_test_min.txt` and `2026.8.3`.
Install each requirements file in its own fresh environment: the official and
legacy test plugins supply overlapping fixtures and must not be installed
together. The official package is published from
[`home-assistant/core`](https://github.com/home-assistant/core/tree/2026.11.0/packages/pytest-homeassistant);
its version must match HA. `tests/ha_helpers.py` selects the corresponding
configuration-entry, clock and Recorder helpers without replacing HA APIs.
Only the minimum fixture explicitly loads the legacy plugin; the official
plugin registers itself. `pytest.ini` disables the separate respx plugin so
HA can install its httpx alias first, and sets function-scoped asyncio fixtures.
Writable HA test configuration uses a temporary directory in both fixtures.
The station reload regression checks the personal name in HA's entity registry
as well as the displayed friendly name: HA 2026.11 prefixes the entity name
with its device name, while the minimum fixture retains the older display.
Both fixtures still require the exact entity IDs and personal name to survive
the station change.
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
recipe. Do not hand-edit hashes, remove upstream HA pins or automatically
advance the frozen minimum HA/test-plugin pair. Keep private index URLs,
credentials and machine-specific paths out of the generated files.

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
