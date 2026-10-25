# Publish the maintained fork

**Procedure version:** 1.5 · **Updated:** 25 October 2026

## 8.3.1b1 test candidate (prepared)

The [8.3.1b1 package](RELEASE_8.3.1b1.md) is prepared, **not published**.
Its runtime is the approved/merged PR #70 source
**22004177b96adb4452fdbd116174915de4dc18cf**. Do not run a publisher against
that runtime commit: the version-only packaging PR must first be reviewed,
regularly merged and pass all checks at its own exact merge SHA.

The new **scripts/publish_meteoswiss_831_beta_v1.4.sh** derives from Beta
Publisher V1.3. It accepts only that exact approved protected development head,
checks the 40-file component footprint against PR #70 with only two version
changes, preserves HACS/workflows and eight earlier tags, and requires the
seven expected merge checks. Latest stable must remain **8.3.0 / ID 422817883**.

After packaging approval and verified merge checks, use the full packaging
merge SHA with the existing Mac `gh` authentication:

```bash
bash publish_meteoswiss_831_beta_v1.4.sh --check FULL_APPROVED_PACKAGING_MERGE_SHA
bash publish_meteoswiss_831_beta_v1.4.sh --publish FULL_APPROVED_PACKAGING_MERGE_SHA
```

The optional first command is read-only; publish repeats the checks. The only
remote write creates **8.3.1b1**, draft=false, prerelease=true, make_latest=false.
The latest-stable check runs again immediately before creation and afterwards.
A matching retry verifies without posting again. Conflicting tag/notes stop;
an uncertain result must be checked before retrying, never deleted or retagged.
Retain the JSON/log under Downloads/HA/05_Diagnose, independently verify the
release/tag/notes/latest, and then announce the [focused check](ACCEPTANCE_8.3.1b1.md).

This helper makes no HA connection or restart. It does not alter the stable
8.3.0 release, install the candidate, or establish its UI acceptance. Earlier
fixed-profile helpers retain their historical contracts and must not be reused
for this new package.

## Stable 8.3.0

**Publication completed:** [8.3.0](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.0)
was published on **24 October 2026 at 15:35:56 UTC**, release ID **422817883**,
from **3ca9a1c166920fbdda88d15238affafe520f4b68**. It is the latest stable release.
[HACS catalogue admission](HACS_ACCEPTANCE.md#hacs-catalogue-admission) was completed
later that day. On 25 October the operator also confirmed the successful
production update from 8.2 to stable 8.3; see [the evidence](HACS_ACCEPTANCE.md).

The following is the completed, version-specific publication procedure. Keep
it as a recovery/audit reference; do not repeat it or reuse its fixed-version
publisher for a future release. Existing tags and release notes remain unchanged.

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
remain. HACS validation is required for future changes. The separate
[catalogue submission](HACS_ACCEPTANCE.md#hacs-catalogue-admission) has now been
approved and merged; no repeat submission is needed. The Home Assistant Quality
Scale guides our documented engineering work; official tiers are not assigned
to custom integrations. See
[quality](QUALITY_SCALE.md), [installation](GETTING_STARTED.md),
[migration/recovery](MIGRATION.md) and the [bounded review](RELEASE_REVIEW_2026-10-24.md).
