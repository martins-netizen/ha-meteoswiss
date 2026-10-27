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
dependency installation requires **3.14.10 or newer within 3.14** and records
the selected Python and pip versions without local account or file paths.
An older cached interpreter stops the job instead of running the tests.

[Python 3.14.10](https://www.python.org/downloads/release/python-31410/)
blocks the compromised eMudhra intermediate CA keys in the `ssl` module and
includes additional security fixes. Future security advisories may require
raising this floor again. The latest-patch lookup is intentional; see the
[setup-python documentation](https://github.com/actions/setup-python/blob/5fda3b95a4ea91299a34e894583c3862153e4b97/docs/advanced-usage.md#check-latest-version).

The supported HA test versions and their dependency requirements remain
separate from this interpreter baseline. The workflow installs dependencies
with pip; the minimum-HA fixture still includes the uv version required by
that HA. This change does not update uv, the separately pinned validator
containers or an installed Home Assistant instance. Those runtimes and their
certificate stores need their own security review.

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
