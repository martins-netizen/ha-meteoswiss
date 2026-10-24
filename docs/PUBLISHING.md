# Publish the maintained fork

**Procedure version:** 1.3 · **Updated:** 24 October 2026

## Stable 8.3.0

The operator accepted published b4 and requested stable promotion. Component
code must match b4 **a8728e35837cc93ccc0ef0780e8f3dc2c0b65ce5**:37 non-version
files identical, with only manifest.json/version.py becoming 8.3.0. Read
[notes](RELEASE_8.3.0.md) and [readiness](RELEASE_READINESS.md).

1. Prepare only the version/docs/publisher package in a PR. Preserve HACS/CH,
   workflows, translations and all previous tags.
2. Pass exact-head checks and merge regularly. Verify the expected tree and
   successful merge checks: tests, HA 2026.8.3, HA 2026.10.1, hassfest,
   Analyze Python, HACS validation and SonarCloud Code Analysis.
3. Download **scripts/veroeffentliche_meteoswiss_stable_v1.3.sh** to the Mac.
   It uses existing `gh` authentication, requires Python3/gh, and needs no
   checkout. Supply the full approved merge SHA:

   ```bash
   bash veroeffentliche_meteoswiss_stable_v1.3.sh --check FULL_APPROVED_MERGE_SHA
   bash veroeffentliche_meteoswiss_stable_v1.3.sh --publish FULL_APPROVED_MERGE_SHA
   ```

   The first command is read-only and optional; publish repeats the checks.
   The only allowed write is creation of release 8.3.0 with draft=false,
   prerelease=false and make_latest=true. It verifies latest-stable selection
   afterwards. Notes use immutable commit URLs.
4. Retain the JSON/log under **Downloads/HA/05_Diagnose**. Independently verify
   tag/release/notes/latest and record ID/time in the operational master.
5. Follow the [HACS stable update check](ACCEPTANCE_8.3.0.md). Publication does
   not install in HA or establish HACS default-catalogue inclusion.

The helper requires the exact protected development head and expected check
apps. It compares all component paths/modes/blobs, version-only changes and
unchanged HACS/workflows. The previous stable release 8.2.0/ID 420392277 and
accepted b4/ID 422790421 must still exist with their expected flags. Seven
immutable tags are checked before and after publication. Latest must be8.2.0
immediately before creation and the exact new 8.3.0 afterwards. A matching
existing release is verified read-only; conflicting notes/tags stop. A timeout
after the write records an uncertain result: rerun to verify before doing
anything else, never delete or retag to force success.

The publisher makes no HA call, restart or device action. A branch name, source
version or green CI alone is not a published release.

## Historical publication routes

- Stable **8.2.0** used **veroeffentliche_meteoswiss_stable_v1.2.sh** and remains
  at 5a0bf684eb44fd54c4e91d7cbce9e90798b72fa5. Its33-file contract is historical.
- **8.3.0b1/b2/b3/b4** used beta publishersV1.0/V1.1/V1.2/V1.3. The first three
  retain38-file contracts; b4 has39. They create only their own prereleases
  and preserve the prior latest stable. Do not repurpose those files.
- Earlier8.2 beta helpers and all published tags remain unchanged. Successful
  HACS source-switch, clean-install and restore evidence is recorded in
  [HACS acceptance](HACS_ACCEPTANCE.md); it is not reopened by this promotion.

## HACS and quality boundaries

Use one software owner for `meteoswiss`; do not delete the configured HA entry
to switch versions. `hide_default_branch:true`, country CH and minimumHA 2026.8.3
remain. HACS validation is required, but passing it or creating a stable GitHub
release does not grant default-catalogue inclusion. A submission and an
official HA quality-tier assessment are distinct later processes. See
[quality](QUALITY_SCALE.md), [installation](GETTING_STARTED.md),
[migration/recovery](MIGRATION.md) and the [bounded review](RELEASE_REVIEW_2026-10-24.md).
