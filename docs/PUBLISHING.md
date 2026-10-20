# First fork release: publication and remaining HACS acceptance

The first [GitHub prerelease 8.2.0b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.2.0b1)
was published on **20 October 2026 at 15:56:24 UTC (17:56:24 Europe/Zurich)**.
The published tag resolves to `abbb6b7701134ac2573f35b425ab3f0697a80540`;
release ID `418588999`, `prerelease=true`, `draft=false`, `immutable=true`.
The publication receipt and an independent release/tag read confirmed this.
Its 33 component, translation and brand files match the live-accepted runtime.

The runtime acceptance is complete. On 20 October 2026 the operator additionally
confirmed the HACS 2.0.5 source switch to this fork, downloaded version 8.2.0b1,
HA restart and a positive initial visual check. A clean first HACS installation
remains open; see the scoped [HACS acceptance record](HACS_ABNAHME_DE.md).
HACS listing and the HA Quality Scale remain separate assessments. This document
does not publish, retag or install anything.

The [current acceptance and stable-release checklist (German)](FREIGABESTAND_DE.md)
is the consolidated next-step record. Publishing this beta did not complete the
clean first-install test or publish a stable 8.2.0 release. The completed source
switch is not an open task to repeat.

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
and date. The live-accepted runtime is PR #31's merged commit
`0086b956d44b7144b242c5d5c1881d0b0650e524`, version `8.2.0b1`.
It was installed on HA 2026.10.2 on 19 October 2026 and completed its exact
24-hour observation period on 20 October 2026. The original protected
candidate commit passed all six post-merge checks. Manifest and module versions
both read `8.2.0b1`; DE/EN/FR/IT ship together.

The review found one isolated optional UV failure. It was reported as
unavailable and recovered on the next scheduled refresh; other checked data
remained available. The device-page visual check confirms forecast pollen
under Sensors. Registry checks confirm all twelve pollen categories, retained
identities, settings, consumers and hourly rain statistics. These are scoped
acceptance findings, not a guarantee of future provider availability.

Publication changes cover documentation and the guarded publication tool, not
integration runtime or workflow changes. Verify every file below
`custom_components/meteoswiss/` against the accepted commit before merging or
tagging. Use the resulting merged publication commit for the tag; do not tag
an unmerged PR or reinstall byte-identical runtime files.
[Release notes](RELEASE_8.2.0b1.md) record the scope and remaining limits.

The repository includes `scripts/veroeffentliche_meteoswiss_beta_v1.0.sh` for
the final publication when a connector cannot create releases. Pass `--publish`
and the exact approved merged publication commit. The tool rechecks that head,
all 33 accepted component blobs, unchanged workflows, versions and successful
post-merge checks; it creates only a GitHub prerelease, never changes HA, and
verifies an existing identical release without overwriting or retagging it.
Keep the resulting JSON/log receipt; a network failure after the write is an
uncertain outcome, not proof that publication failed. Re-running the same tool
first checks whether the expected release already exists.

- All CI compatibility jobs, Hassfest and CodeQL must pass for the candidate.
  Run the official **HACS validation** with no ignored checks; missing Issues,
  topics or other repository requirements must be fixed, not suppressed.
- Compare manifest and module versions and the complete DE/EN/FR/IT catalogues.
  Retain the integration domain, config entries, and IDs of retained entities
  and statistics. State the deliberately retired legacy season-HGT exception
  in the migration/release notes; do not promise that every old entity survives.
- The deployed runtime was originally installed with a reviewed installer.
  The operator has since confirmed the HACS 2.0.5 source switch, exact repository
  and downloaded 8.2.0b1 version, restart and initial visual success. This is
  operator-reported evidence; no new independent post-switch registry/statistic
  or file-hash comparison, executed rollback, or clean first install is claimed.
  The existing 24-hour runtime acceptance remains valid for the same code.
  Follow [START_DE.md](START_DE.md) for the still-open first-install rehearsal;
  [WECHSEL_DE.md](WECHSEL_DE.md) remains the source-switch guide for other users.
  A disposable instance is sufficient; a second permanent HA installation is not
  required. A default-store listing or nontechnical usability approval is not claimed.
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

## Release selection and subsequent promotion

1. Preserve the protected maintained default branch `development`; `main`
   remains the upstream mirror. The immutable `8.2.0b1` tag must not move.
2. First inspect the installed HACS version, current software owner and available
   release without downloading, removing software or changing the HA config entry.
   Refresh repository metadata if needed. In current HACS, open Download/Redownload,
   expand **Need a different version?**, and select **8.2.0b1** under **Release**.
   Older HACS versions may additionally require beta visibility. Check the
   announced download version; do not accept a branch or commit fallback.
3. Complete the still-open clean first-install rehearsal described in
   [HACS_ABNAHME_DE.md](HACS_ABNAHME_DE.md). The operator-confirmed source switch
   is complete; do not repeat it. A temporary isolated instance is sufficient;
   do not require a second permanent HA installation or use the production system
   as an empty first-install test. Rehearse the documented recovery route there
   and keep the runtime's completed 24-hour acceptance. A new independent read-only
   post-switch file/identity check is useful supplementary evidence, not a reason
   to redo the source switch.
4. Include `"hide_default_branch": true` in the next reviewed release's
   `hacs.json`. HACS can read that manifest from the selected ref, so changing
   only `development` does not change the immutable `8.2.0b1` manifest or prove
   branch downloads are hidden when that beta is selected. Keep this limitation
   visible; do not retag an existing release or create a runtime update merely
   to avoid explicitly selecting this beta.
5. Before a later default-store submission, add the appropriate `country`
   metadata to its released manifest, recheck the then-current inclusion rules,
   and retain successful HACS/Hassfest checks and a usable support route.
   Neither this prerelease nor its rehearsal is a default-store approval.

The beta-selection route was checked against the source of HACS 2.0.5 and its
pinned frontend 20250128065759 on 20 October 2026. The operator subsequently
confirmed that version selection, download, source switch and restart succeeded.
Source inspection alone is not a practical test; the clean first-install path
still needs its own run.

## Published beta scope

`8.2.0b1 — first maintained-fork prerelease`:

- Continued maintenance of LNKtwo/ha-meteoswiss; MIT licence and attribution retained.
- Station observations, hourly rain statistics and native ICON Seamless forecasts.
- Source freshness, bounded retries and explicit failure/recovery behaviour.
- App v3 warning source, verified thirteen-family catalogue and complete
  German/English/French/Italian labels, including prepared Thaw handling.
- Measured/forecast pollen, air quality and isolated optional UV availability.
- Required minimum HA 2026.8.3; CI also covers HA 2026.10.1. Local tests and
  deployed 24-hour acceptance additionally cover HA 2026.10.2.
- Migration warning: review numeric warning filters and dashboard labels before
  updating; existing config entries and retained entity/statistic IDs remain.
  The obsolete forecast-only season-HGT and derived current-hour rain entities
  are deliberately removed. The measured 10-minute rain entity and official
  hourly rain statistics remain; independent user helpers are not deleted.
- Not an official MeteoSwiss product. Data and alerts can be delayed or incomplete;
  this integration does not replace the providers' official warning channels.

The [published beta notes](RELEASE_8.2.0b1.md) and immutable GitHub release record
contain the approved changes and acceptance evidence. This recap does not alter
that release. Standalone SLF, BAFU or radar modules are not promised: the
corresponding placeholders are not active integrations in this fork.

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

Publication requirements rechecked 20 October 2026:

- [HACS general requirements and releases](https://www.hacs.xyz/docs/publish/start/)
- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/)
- [Official HACS validator](https://www.hacs.xyz/docs/publish/action/)
- [HA custom integration images](https://contributors.home-assistant.io/core/integrations/brands/)

