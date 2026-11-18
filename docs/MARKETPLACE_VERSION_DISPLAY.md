# Marketplace minimum-version display for an installed beta

**Checked: 15 November 2026, Home Assistant Core 2026.11.1.**
The operator's Marketplace page displays installed **8.3.5b3** alongside
**Requires Home Assistant 2026.8.3**. That minimum belongs to published stable
8.3.4; the installed beta requires **2026.11.0**.

The published [b3 manifest](https://github.com/martins-netizen/ha-meteoswiss/blob/8.3.5b3/hacs.json)
and [current development manifest](https://github.com/martins-netizen/ha-meteoswiss/blob/development/hacs.json)
both declare 2026.11.0. The immutable [8.3.4 manifest](https://github.com/martins-netizen/ha-meteoswiss/blob/8.3.4/hacs.json)
declares 2026.8.3; it was the latest stable in that reproduced case. Current
8.3.5 packages require **2026.11.0**. Follow the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases) for
actual stable selection, and [current evidence](RELEASE_EVIDENCE_8.3.5.md) for
the promotion stage. Do not rewrite an old tag or publish solely to change a display.

## Reproduced cause and evidence limit

An offline reproduction uses the unchanged Marketplace classes from the
installed official HA 2026.11.1 package, with provider responses mocked and
zero network or production writes. With installed version 8.3.5b3, latest stable
8.3.4, beta visibility enabled and no explicit selected tag:

- `version_to_install()` returns 8.3.4.
- `async_get_repository_manifest()` requests that version's `hacs.json`.
- `get_documentation()` instead requests the installed version's README.
- `repository_summary()` exports the repository manifest's minimum beside the
  independently stored installed version.

An explicit selected tag of 8.3.5b3 makes the same manifest method read b3 and
return 2026.11.0. The installed beta field is unchanged in both cases. This
reproduces mixed-version information without a stale GitHub file. It does not
claim the operator's live `selected_tag` or cache has been read; those were not
queried. Refreshing information can reproduce the mismatch if the selected
reference remains the stable one.

## Correct interpretation and next boundary

For an installed **8.3.5 beta, use HA 2026.11.0 or newer**. This repository's
minimum, CI matrix and beta source manifests already agree. Keep the existing
installation; no redownload, downgrade, storage-file edit or HA code patch is
needed to restate that requirement.

A lasting Marketplace correction should distinguish the installed package's
minimum from the selected/available package's minimum. Reusing only the installed
minimum for installation checks could incorrectly allow an incompatible future
update. That backend/UI correction belongs to Home Assistant Marketplace and
needs separate native regressions for stable, beta and selected-version paths.
This integration PR documents and proves the boundary; it does not patch the
production Core or claim that its live page has already changed.
