# 8.2.0b2 — pollen setup test prerelease

**Prepared test candidate; publication is a separate step.** A branch, PR or
tag alone is not an available HACS release. Check the
[fork Releases page](https://github.com/martins-netizen/ha-meteoswiss/releases)
for an explicitly published **8.2.0b2** prerelease before downloading it.

This community fork builds on LNKtwo/ha-meteoswiss and retains its MIT licence
and attribution. It is not an official MeteoSwiss product.

## Changes from 8.2.0b1

- Choose a measured-pollen station explicitly in the first setup dialog for
  either weather source. No station is silently preselected for a new entry.
  DE/EN/FR/IT explain the independent weather, warning and pollen locations.
- Retain the choice across weather-source retries and allow later changes in
  Configure without recreating the entry. Existing saved settings remain.
- Use 15 station identifiers/names verified against official metadata and
  current-hourly assets. Remove unsupported BLR from the choices. This does not
  remove a real station merely because its current measurements are stale.
- Keep postcode guidance about the four-digit Swiss postal code, without
  internal App-code details.
- Set `hide_default_branch: true` in this candidate's HACS manifest so that
  development-branch downloads are not offered for this released manifest.
  The immutable 8.2.0b1 manifest and tag are unchanged.

The [dated station evidence](POLLEN_STATIONS.md) includes real current Zürich
and stale Luzern data. A valid station may temporarily publish no new values;
old zero concentrations must not appear as current measurements. There is no
automatic substitute station.

## Focused acceptance in the temporary HA instance

The operator already completed a clean 8.2.0b1 HACS installation and an isolated
backup restore on HA 2026.10.2 / HACS 2.0.5. Those results and the earlier
runtime observation are retained; they do not claim this new UI was tested.

1. Back up the temporary instance. After this prerelease is actually published,
   explicitly select **8.2.0b2** under HACS Download/Redownload → Release and
   restart HA. Confirm the downloaded version, not a branch/commit offer.
2. Keep an existing entry initially. Check its interval and saved pollen station
   in Configure; confirm that its retained entities still update. The code does
   not automatically move an old station choice to a different station.
3. In the **temporary instance only**, remove that test entry after noting its
   settings, then add MeteoSwiss again. Confirm the first dialog requires a
   pollen-station choice, the labels/help are understandable, and the warning
   postcode guidance contains no internal App-suffix instruction.
4. For the measured-weather path, choose the desired pollen station, then the
   weather station and four-digit warning postcode. Check initial data and the
   saved pollen station in Configure. Current pollen data depend on the source;
   use the dated evidence as explanation, not as a permanent live-status list.
5. Change the pollen station in Configure and check the saved choice and source
   values. The modelled pollen forecast location must not change with it.
6. In a second temporary test entry, check the **Open-Meteo** setup path with an
   explicit pollen station and a distinct coordinate/postcode combination.
   Clean up that extra test entry afterwards.
7. Reopen HACS version selection and confirm the intended prerelease is offered
   and the default branch is hidden with the corresponding candidate manifest.

Do not delete/recreate the production integration, actuate devices, or restore
the production system for this check. No new blanket 24-hour observation period
is imposed for this focused setup correction. Report the chosen station,
downloaded version and the result of each check; an independent nontechnical
usability review remains separate.

## Publication and limits

Use the guarded **V1.1** publication helper with the exact approved merged
packaging commit. It checks that 31 component files still match the CI-tested
onboarding source `a90ed05cd9d23ce1bee341bcc5a662678a7e9bcc`, and that only the
version changes in the other two component files. It also checks branch hiding,
unchanged workflows, the old immutable beta tag, versions and all post-merge
checks. Publication creates only the new prerelease; it does not install HA.

The new onboarding code has automated regression coverage. Its focused HA UI
acceptance is still pending. Existing [beta limits](RELEASE_8.2.0b1.md),
[migration requirements](MIGRATION.md), provider availability, and
[security/quality follow-ups](RELEASE_READINESS.md) remain applicable. This is
not stable 8.2.0, a HACS default-catalogue approval or an official HA quality tier.
