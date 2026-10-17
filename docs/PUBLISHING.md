# First fork release: preparation and acceptance

This is a release checklist, not a release announcement. Version `8.2.0b1`
is prepared; no tag, GitHub release, HACS promotion or HA deployment is created
by these files. The first release remains a **prerelease** until live acceptance
is recorded. HACS listing and the HA Quality Scale are separate assessments.

## Repository settings to complete before publication

| Setting | Required result |
|---|---|
| Default branch | `development`, the protected maintained branch. Retain `main` as the upstream mirror. Verify that existing development protection still applies. |
| Issues | Enabled, so the manifest's fork-specific issue tracker is usable. The bundled issue forms collect versions, relevant states and redacted evidence. |
| Description | `Maintained MeteoSwiss integration for Home Assistant: observations, ICON forecasts, warnings, pollen and air quality.` |
| Topics | `home-assistant`, `home-assistant-integration`, `hacs`, `meteoswiss`, `switzerland`, `weather`, `pollen`, `air-quality`, `open-meteo` |
| Actions and permissions | Keep the existing restricted action policy, full-SHA requirement and read-only default token. The HACS workflow uses the official image by digest, with no additional action allowlist entry or repository write permission. |

The default branch must contain the maintained README and HACS manifest when
the repository is promoted. Do not direct users to the upstream mirror. These
settings must be verified from GitHub; documentation does not change them.

## Candidate and deployment evidence

Record the **exact merged candidate commit**, supported HA version, CI links
and date. The currently prepared warning migration is based on PR #19,
`a566eb3305b968fbc4bfb73ff0ca43a55145a809`; that identifies a code candidate,
not a claim that it is installed or released.

- All CI compatibility jobs, Hassfest and CodeQL must pass for the candidate.
  Run the official **HACS validation** with no ignored checks; missing Issues,
  topics or other repository requirements must be fixed, not suppressed.
- Compare manifest and module versions and the complete DE/EN/FR/IT catalogues.
  Retain the integration domain, config entries, and IDs of retained entities
  and statistics. State the deliberately retired legacy season-HGT exception
  in the migration/release notes; do not promise that every old entity survives.
- Rehearse a first installation and a same-domain HACS source switch in a
  separate HA test installation. Follow [START_DE.md](START_DE.md) and
  [WECHSEL_DE.md](WECHSEL_DE.md), checking actual HACS UI wording, a single
  preserved HA entry, registry/statistic identity and the paired rollback.
  Source review and reading the HACS manual are not this end-to-end rehearsal.
  Have a new user follow the steps and record confusing points before claiming
  that nontechnical usability has been demonstrated.
- Before updating an existing installation, migrate the actual warning
  consumers as described in [WARNING_CODES.md](WARNING_CODES.md). Wind is 0,
  thunderstorm 1, rain 2 and slippery roads 4. Category 5 is Frost; preserve
  the concrete provider message. Include Thaw 6 and Drought 12 where intended.
- Back up the installed component and affected consumers and verify a working
  restore route. Test source failures with mocks, without actuating devices.
- After installation, verify observations, native forecasts, both warning lists,
  precipitation precision/statistics and pollen/AQ. A legitimate missing optional
  value must remain distinguishable from a failed whole source. Confirm the
  intended dashboards and automations against the new catalogue.
- Record a completed observation period for the **actual deployed code and
  consumers**. A successful earlier version or a read-only precheck is not a
  completed deployment acceptance of a later version.

Documentation, issue forms and brand-only changes can be reviewed separately.
If a publication commit adds only those assets, compare all previously accepted
runtime files byte for byte and run its PR checks; do not infer acceptance from
the version number alone or reinstall an identical runtime needlessly.

## Release promotion

1. Complete the repository settings above and confirm the intended default
   branch. Keep the existing protected-PR workflow; no admin bypass or force push.
2. With the first approved GitHub prerelease ready, set
   `"hide_default_branch": true` in `hacs.json` through a reviewed promotion PR.
   This prevents branch downloads from being offered in HACS. Do not set it
   early while there is no selectable release.
3. Confirm that `manifest.json`, `version.py`, the changelog and release tag
   describe the same candidate. Consolidate the unreleased notes only when
   that release is actually approved; keep upstream historical attribution.
   Replace the README's prepared/no-release notice with the actual approved
   version, prerelease limitations and release link. Keep the two user guides
   aligned with the rehearsed installation/migration route.
4. Create a GitHub **prerelease** from the exact approved commit and tag
   `8.2.0b1`. A tag by itself is insufficient for the release-based HACS route.
   Review the notes before publishing. Do not enable automatic merging or
   automatic HA installation.
5. Add the custom repository in HACS as **Integration**, enable prerelease/beta
   versions where required and explicitly select the tested prerelease. Verify
   the displayed repository/version and installed runtime file hashes.
   Do not remove/recreate the existing integration or its history.
6. Check the published release with HACS again. Store the public CI/release
   evidence, then consider a separate default-store submission after the fork
   has a usable support route and a confirmed release.

## Prepared release-note outline

`8.2.0b1 — first maintained-fork prerelease`:

- Continued maintenance of LNKtwo/ha-meteoswiss; MIT licence and attribution retained.
- Station observations, hourly rain statistics and native ICON Seamless forecasts.
- Source freshness, bounded retries and explicit failure/recovery behaviour.
- App v3 warning source, verified thirteen-family catalogue and complete
  German/English/French/Italian labels, including prepared Thaw handling.
- Measured/forecast pollen, air quality and isolated optional UV availability.
- Required minimum HA 2026.8.3; CI also covers HA 2026.10.1.
- Migration warning: review numeric warning filters and dashboard labels before
  updating; existing config entries and retained entity/statistic IDs remain.
  The obsolete forecast-only season-HGT entity is deliberately removed.
- Not an official MeteoSwiss product. Data and alerts can be delayed or incomplete;
  this integration does not replace the providers' official warning channels.

Replace this outline with the final approved changes and actual acceptance
evidence when publishing. Do not promise standalone SLF, BAFU or radar modules:
the corresponding placeholders are not active integrations in this fork.

## Local icon and validator maintenance

`custom_components/meteoswiss/brand/icon.png` and `icon@2x.png` are the fork's
original weather drawing, covered by this repository's MIT licence. They use
neither the Home Assistant logo nor an official MeteoSwiss logo. Rebuild them
with `python scripts/build_brand_assets.py` in an environment with Pillow;
Pillow is a development-only requirement, not an integration dependency.

The HACS workflow pins `ghcr.io/hacs/action` by immutable image digest. Its
source revision is recorded in the workflow. Review and update the digest
periodically alongside other tooling; changing a source action SHA alone would
not pin its mutable container tag. The validator reads the exact public PR/push
commit with a read-only token, has no ignored checks and posts no comments.

References checked 17 October 2026:

- [HACS general requirements and releases](https://www.hacs.xyz/docs/publish/start/)
- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/)
- [Official HACS validator](https://www.hacs.xyz/docs/publish/action/)
- [HA custom integration images](https://contributors.home-assistant.io/core/integrations/brands/)
