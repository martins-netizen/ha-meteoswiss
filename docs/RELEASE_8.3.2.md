# 8.3.2 — complete shared location settings

**Notes version:** 1.1 · **Status updated:** 30 October 2026

**Published:** 28 October 2026 at **12:21:19 UTC**, release **426633496**,
from **aea4c5eab0534a6e675a4f564bde7521df193c58**, immutable and latest until
stable [8.3.3](RELEASE_8.3.3.md) was published on 30 October.
On **30 October** the operator confirmed its HACS download, HA restart and
working operation. See [the current evidence](RELEASE_EVIDENCE_8.3.2.md).
The published release body below is retained verbatim as historical text;
the publication and short stable update it describes are now completed.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.1

- **One complete dialog through either route.** Configure (gear) and the entry
  menu's Reconfigure both offer weather measurements, measured pollen, forecast
  selection and the independent warning postcode. For MeteoSwiss weather,
  choose a measuring station; an Open-Meteo current-data entry instead shows
  its base coordinates. Previously, Reconfigure changed only the forecast.
- **Retain retry choices.** A failed observation-source check keeps the chosen
  forecast search/reset for the retry, instead of silently reverting to Keep.
- **Save all pending settings together.** Both routes share source checks,
  confirmation and duplicate/concurrent-edit protection. Cancellation or failed
  validation saves no partial change. If another dialog saves first, reopen the
  older dialog to review the current values.
- **Complete four-language help.** German, English, French and Italian include
  the full reconfiguration form and combined confirmation. Initial setup keeps
  its separate forecast confirmation.

The [four location roles](../README.md#four-places-what-each-one-is-used-for)
remain distinct. An explicit forecast move does not move observations,
measured pollen, modelled AQ/pollen/UV or the warning postcode. The global HA
home location is independent. See [shared settings](CALENDAR_AND_LOCATION_SETTINGS.md).

Existing config entries, entity/statistic identities, custom names, unrelated
settings and legacy intervals are retained. A loaded entry reloads once after
confirmation. Deliberately changing the weather station continues retained
observation history with the new station's readings; external station-keyed
precipitation archives retain their own identities. No configuration-format
migration, new source, polling, dashboard change or device action is introduced.

## Accepted beta and version-only promotion

**8.3.2b1 / ID 425962004** was published on **27 October 2026 at 20:40:42 UTC**
from **5a39c3cdbf31f0807f52bcb4acb26190cc1e8423**, tree
**8add2f80ac62d78ac3817ff4b5898c74ad80da0f**. The publisher receipt/log and
independent release/tag/notes/latest checks agree. The operator subsequently
reported all five [focused steps](ACCEPTANCE_8.3.2b1.md) positive on
**HA Core 2026.10.4**, including version, both routes, cancellation, combined
saving and restoration of intended choices. This is reported acceptance, not
an independent registry/statistic audit or a separate clean installation.

Stable packaging keeps **38 non-version files** from that accepted beta.
Only manifest.json/version.py become **8.3.2**, within the 40-file component.
HACS/CH, minimum HA, workflows, security guards and the four **200-key** UI
catalogues match. The eleven previous tags and published release bodies remain
unchanged. There is no runtime addition after the accepted beta.

The beta's exact merge passed all seven checks and **1,932 tests plus 73
subtests** on each hosted HA 2026.8.3/2026.10.1, with Python **3.14.10**.
Stable packaging adds a ninth fixed publication profile; its own results are
recorded in [readiness](RELEASE_READINESS.md). Coverage gates and the four
existing exclusions are retained. Additional local HA 2026.10.3 tests and the
operator's Core 2026.10.4 report are separate from the hosted matrix.

## Short stable update

After **8.3.2** is published and announced, actually Download/Redownload that
stable version through the existing maintained-fork HACS entry and restart HA
once. Refresh repository information first if necessary; refreshing alone
does not download files. Keep the configured entry and existing backup.

Follow the [short version/update check](ACCEPTANCE_8.3.2.md). The accepted beta
dialog tests and earlier first-install/restore checks stay closed. No repeat
of the five dialog steps or blanket new 24-hour wait is required.
Software rollback does not undo deliberately changed location choices;
restore those separately and retain entries/history. Published stable
**8.3.1** remains the recovery version until this promotion is confirmed.

## Publication and remaining quality work

**veroeffentliche_meteoswiss_stable_v1.5.sh** derives from the successful
stable V1.4 profile. It requires the exact approved protected development
merge, the accepted-beta/version-only boundary, successful check provenance,
previous stable **8.3.1 / ID 424249153**, accepted beta **8.3.2b1 / ID 425962004**
and all eleven prior tags. Its only remote write creates stable **8.3.2**,
draft=false, prerelease=false, make_latest=true. Latest must be the previous
stable immediately before creation and this exact release afterwards.
Matching retries only verify; conflicting tags/notes stop. The publisher makes
no HA connection, restart or device call. See [publishing](PUBLISHING.md#stable-832-prepared).

Shared Reconfigure now has both automated and reported focused HA evidence.
The [quality matrix](QUALITY_SCALE.md) retains remaining icon/error translations,
metadata/defaults, stale-device handling and proposed exemptions. This promotion
does not complete the full Gold checklist or confer an official HA tier.

Use the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
for problems, or [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports.
