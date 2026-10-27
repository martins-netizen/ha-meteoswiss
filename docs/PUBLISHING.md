# Publish the maintained fork

**Procedure version:** 1.7 · **Updated:** 27 October 2026

<a id="832b1-test-candidate-prepared"></a>

## 8.3.2b1 shared-settings test candidate (prepared)

[8.3.2b1](RELEASE_8.3.2b1.md) is **not published or installed**. The package
retains reviewed PR #76 at **d6ae2a0b1ae9c195c9647f6b416d347891f91a74**,
tree **489d818a27e58c45428085ab3d917b25ac694dbf**. Of 40 component files,
38 non-version files match; only manifest.json/version.py become 8.3.2b1.
HACS/CH, workflows and security guards are retained, with 200 translation keys
per language. Stable **8.3.1 / ID 424249153** remains latest.

1. Review and regularly merge the packaging PR. Confirm the actual tree and
   successful merge checks: tests, HA 2026.8.3, HA 2026.10.1, hassfest,
   Analyze Python, HACS validation and SonarCloud Code Analysis. Inspect every
   additional check too; no bypass or source additions after review.
2. Download **scripts/publish_meteoswiss_832_beta_v1.5.sh** from that approved
   packaging merge to the Mac. Use existing `gh` authentication and the full
   approved merge SHA:

   ```bash
   bash publish_meteoswiss_832_beta_v1.5.sh --check FULL_APPROVED_PACKAGING_MERGE_SHA
   bash publish_meteoswiss_832_beta_v1.5.sh --publish FULL_APPROVED_PACKAGING_MERGE_SHA
   ```

   Check is read-only and optional; publish repeats all gates. The only remote
   write creates **8.3.2b1**, draft=false, prerelease=true, make_latest=false.
3. Retain the JSON/log under Downloads/HA/05_Diagnose. Independently verify the
   actual release/tag/notes/latest and record ID/time. Only then announce the
   [focused UTM/existing-entry check](ACCEPTANCE_8.3.2b1.md).

The V1.5 helper derives from the successful fixed V1.4 beta profile. It requires
the exact protected development head, the reviewed source/version-only boundary,
expected check apps, unchanged HACS/workflows and all **ten** earlier tags.
Latest must be published stable 8.3.1 immediately before creation and afterwards.
Matching retries only verify; conflicting tags/notes stop, and an uncertain
write remains unconfirmed. No HA connection, installation or restart is made.
Earlier fixed publishers and immutable releases are unchanged.

<a id="stable-831-prepared"></a>

## Stable 8.3.1 (completed)

[Stable 8.3.1](RELEASE_8.3.1.md), ID **424249153**, was published on
**26 October 2026 at 12:54:24 UTC** from
**fa298ca72bf62da727797f9bfcacf95c83ffeaf1** and is latest stable. Its receipt
and independent GitHub reads confirm publication, version-only source, tags and
checks. Actual stable HACS installation remains separate. The fixed procedure
below is historical evidence; do not repeat it for 8.3.2b1. The operator
confirmed the focused version/visual check of published 8.3.1b1 on 26 October.
Keep the existing beta tag/release/notes unchanged. This package retains its
**38 non-version component files**, with only manifest.json/version.py changing
to **8.3.1**. HACS/CH, workflows and all four 180-key catalogues match.

1. Review and regularly merge the version/docs/publisher package. Verify its
   exact tree and all seven merge checks: tests, HA 2026.8.3, HA 2026.10.1,
   hassfest, Analyze Python, HACS validation and SonarCloud Code Analysis.
2. Use **scripts/veroeffentliche_meteoswiss_stable_v1.4.sh**, derived from the
   successful stable V1.3 route, with the full approved packaging merge SHA:

   ```bash
   bash veroeffentliche_meteoswiss_stable_v1.4.sh --check FULL_APPROVED_PACKAGING_MERGE_SHA
   bash veroeffentliche_meteoswiss_stable_v1.4.sh --publish FULL_APPROVED_PACKAGING_MERGE_SHA
   ```

   Check is read-only and optional; publish repeats all gates. The only remote
   write creates **8.3.1**, draft=false, prerelease=false, make_latest=true.
3. Retain the JSON/log under Downloads/HA/05_Diagnose. Independently verify the
   actual release/tag/notes/latest and record the result. Only then announce the
   [short stable update check](ACCEPTANCE_8.3.1.md).

The fixed-profile helper requires the exact protected development head, the
40-file footprint/version-only comparison against accepted beta
**c7b20c78d4273a33ba8c6f06c1834fc2f22c8665**, expected check apps, unchanged
HACS/workflows and all nine earlier tags. It verifies previous stable
**8.3.0 / ID 422817883** and accepted beta **8.3.1b1 / ID 423899845** by their
actual published flags. Latest must be 8.3.0 immediately before creation and
the exact new 8.3.1 afterwards. Matching retries verify without another write;
conflicting tags/notes stop, and uncertain writes are recorded as unconfirmed.
No HA connection, installation, restart or device action is performed.

<a id="831b1-test-candidate-prepared"></a>

## 8.3.1b1 test prerelease (completed)

[8.3.1b1](RELEASE_8.3.1b1.md), ID **423899845**, was published on
**26 October 2026 at 05:54:44 UTC** from
**c7b20c78d4273a33ba8c6f06c1834fc2f22c8665** after approved PR #71 and its
seven merge checks. The receipt/log and independent release/tag/notes/version/
latest checks agree; latest stable remained 8.3.0. The operator subsequently
confirmed the [focused version/visual check](ACCEPTANCE_8.3.1b1.md).

Beta Publisher V1.4 retains its fixed source/40-file/8-tag contract and creates
only that prerelease with make_latest=false. It is historical publication
evidence, not an instruction to republish b1 or use its source SHA for the new
stable package. Earlier helpers, immutable tags and published notes are unchanged.

## Stable 8.3.0

**Publication completed:** [8.3.0](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.0)
was published on **24 October 2026 at 15:35:56 UTC**, release ID **422817883**,
from **3ca9a1c166920fbdda88d15238affafe520f4b68**. It was latest stable until the 8.3.1 publication on 26 October.
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
