# Stable 8.3.4: publication evidence

**Evidence version:** 1.0 · **Updated:** 7 November 2026

## Published version and normal installation target

[Stable 8.3.4](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.4)
was published on **7 November 2026 at 21:24:27 UTC**, release ID **437853341**.
The immutable tag points to regularly squashed packaging PR #93 at
**f4479897023fa35d7c2fcb4c4859c4de8861fdda**, tree
**1657d5415c14653a81e2387f5e469a6c8deea4f8**. GitHub's
[latest stable endpoint](https://github.com/martins-netizen/ha-meteoswiss/releases/latest)
selects that exact release. It is published, draft=false and prerelease=false.

The publisher receipt and independent GitHub reads agree on release ID, tag,
source, exact approved English body and latest selection. The body SHA-256 is
**b2e3b150db393a76d3f29be0051022c2e1c6078d295460abb4d740501171736c**.
All fifteen previous tag targets remain unchanged. Accepted beta release
**437718127** and its exact published body are retained, as is previous stable
**8.3.3 / ID 429354633** and its body.

The [frozen release-scope page](RELEASE_8.3.4.md) records the packaging snapshot;
this evidence document records the subsequent actual publication. Published
release bodies, tags and earlier publisher scripts remain immutable.

## Benefits and accepted runtime

Compared with 8.3.3, stable 8.3.4 brings verified HA 2026.11 compatibility with
the matching official test package and reproducible dependency locks, cleaner
first-registration diagnostic defaults, and clearer current-source attribution
and virtual data-service metadata. Existing personal choices remain in place.
See [practical benefits and existing-user scope](RELEASE_8.3.4.md#why-upgrade-from-833).

All **39 non-version component files** match accepted published beta
**1e5c5d1a7fc1c18d520e99189ae4dd5894621706 / ID 437718127**; only
manifest.json/version.py become **8.3.4**. References to 8.3.4b1 record that
historical source and its [bounded acceptance](RELEASE_EVIDENCE_8.3.4b1.md).
They do not make the beta the current installation target.

All seven actual packaging-merge checks pass. Both [hosted compatibility jobs](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/42413833720)
pass **2,225 tests plus 83 subtests** on HA 2026.11.0 and minimum HA 2026.8.3.
Combined integration coverage is **99.977812%** (3,530/3,531 statements,
976/976 branches), with unchanged strict dependency, security, translation,
compilation and coverage gates. The current fixture uses official
**pytest-homeassistant 2026.11.0**. Five existing upstream fixture warnings remain
visible; the minimum fixture has no warnings. Fixed Stable Publisher V1.7 and
630 publication cases over thirteen profiles retain their reviewed boundaries.

## Actual stable update and evidence limits

For an actual update, use the [short stable protocol](ACCEPTANCE_8.3.4.md):
download **8.3.4**, restart HA once and confirm installed version and normal
operation. Core/OS versions are only needed if changed. Keep the existing entry
and backup; earlier settings, icons, clean-install, restore and beta acceptance
stay complete within their recorded scopes.

Publication does not assert a user's installation or independently audit
personal registry/Recorder data. The beta operation report remains bounded to
its original scope on **Core 2026.11.0 / HA OS 18.4**. Native regression tests
provide separate automated evidence.

HGT statistics PR #92, wind/history migrations, historical orphan review and
remaining Gold rules are separate. This stable release retains the accepted
HGT behaviour and does not delete registry or Recorder data.
