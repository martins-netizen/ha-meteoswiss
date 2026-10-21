# Switch to this maintained fork

Use this guide when MeteoSwiss is already configured. The fork replaces its
software while retaining the existing HA configuration:
**do not delete MeteoSwiss under Devices & services or add it again afterwards.**

Check [release status](../README.md#release-status) first. A branch or open PR
is not a released version; this guide is not permission to install an unapproved
candidate.

## When switching is useful

Choose this fork to receive reviewed fixes and bundled translations from one
maintained source instead of local file patches. See the
[plain-language overview](GETTING_STARTED.md#what-this-fork-provides).

For experienced users:

- [Verified warnings](WARNING_CODES.md): Wind is 0, Slippery Roads 4; App v3 also
  supplies the demonstrated drought warning missing from v1 for the example
  postcode. Avalanche 8 and Flood 11 are handled when supplied.
- Failures, stale data and valid zeros remain distinct.
  [Tests and review](REVIEW_2026-10-17.md) document evidence and remaining work.
- Retained configuration/entity/statistic IDs survive. The deliberate exceptions
  and necessary consumer changes are described below.
- DE/EN/FR/IT ship together; local translation patches are unnecessary.

Compare with the actual installed version. Existing fixes are not a new benefit,
and switching does not promise more accurate forecasts from the same stated model.

## 1. Identify your current installation

| Existing source | Route |
|---|---|
| This maintained fork, already in HACS | Download only the approved update after reading its notes; do not add a second repository. |
| LNKtwo/ha-meteoswiss through HACS | Use the software-source switch below. |
| Manual files, local patches or uncertain provenance | Establish source and changes before overwriting. |

In **HACS → three-dot menu → Repository**, record the source and version.
Matching version strings do not prove identical manually patched code.
If provenance is unclear, stop and ask in the
[fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues).

## 2. Back up and inspect current consumers

Create a full backup under **Settings → System → Backups**, download it and
retain its recovery key. Include integration/configuration, dashboards and
automations; retain the previous software for recovery. An external database
needs its own matching backup. An untested backup is not a demonstrated restore.

Record important entity IDs and existing statistic charts.

### Precipitation changes

**Precipitation (10 minutes)** is the latest published measured ten-minute
amount. Its measurement time is the interval end, not an accumulation since the
current hour began. A 12:20 observation covers the ten minutes ending at 12:20.
Used station files are published every twenty minutes; polling faster does not
create newer measurements.

For Open-Meteo, **Precipitation (modelled interval)** retains the provider interval
in `measurement_interval_seconds`.

The extra locally calculated **current-hour precipitation** entity is retired.
It was not an official hourly total: before the first published interval it was
unknown, and missing intervals could yield an incomplete subtotal.
Before updating, inspect its cards, templates and automations. Remove those
references or use official completed-hour statistics where appropriate.
Setup/reload removes only this integration's exact retired entity;
it does not purge history or statistics.

**The official precipitation archive remains.** Its statistic ID is
`meteoswiss:<station>_precipitation_hourly`, for example
`meteoswiss:klo_precipitation_hourly`. The provider timestamp marks the
**end** of an hour, whereas HA stores the corresponding **start**, in UTC.
For example, a provider reference of 12:00 UTC covers 11:00–12:00 UTC and is
stored with a start of 11:00 UTC. Do not confuse a provider reference with an
HA chart's interval-start timestamp. User-created utility-meter helpers are not
deleted by the fork; inspect consumers before removing them yourself.

Retained entity/statistic IDs should remain unchanged. Two other scope limits:

- The old forecast-only **seasonal heating-degree-days** entity is deliberately
  retired. It was not a reliable accumulated measurement counter. Update its
  consumers; daily forecast HGT 12/20 remains, without a new measured seasonal total.
- Soil-temperature sensors and separate radar/SLF/BAFU modules are inactive.
  This concerns separate measurements/bulletins, not avalanche/flood warnings
  supplied by the shared MeteoSwiss warning feed. Do not plan unsupported modules
  from historical upstream announcements.

## 3. Review warning consumers

Updating software does **not** automatically update your dashboards/automations.

| Intended warning | Verified code |
|---|---:|
| Wind / storm | **0** |
| Thunderstorm | **1** |
| Rain / heavy rain | **2** |
| Snow / snowfall | **3** |
| Slippery roads | **4** |
| Frost, preserving the concrete event text | **5** |
| Thaw, if supplied | **6** |
| Drought | **12** |

The [full catalogue](WARNING_CODES.md#numeric-warning-families) has thirteen
families. Code 4 must no longer mean Wind. Wind/thunderstorm/rain filters use
**`[0, 1, 2]`**, replacing the old **`[1, 2, 4]`** where that specific
meaning was intended. Do not replace every 4 indiscriminately.

For awnings, blinds or other device consumers:

1. Record which affected automations are enabled, then pause them for migration.
2. Check active **and upcoming** alerts, lead-time checks and labels. A fixed
   “ground frost” label does not describe every event in the Frost family.
3. Apply affected consumer changes with the software update, verify them and
   re-enable only automations that were previously enabled.

If numeric filters are unclear, have them reviewed first. Outage handling depends
on your installation; **unavailable is not permission to open an awning**.
Do not actuate devices merely to test migration.

## 4. Switch HACS software ownership

When moving from `LNKtwo/ha-meteoswiss`:

1. Remove its old software entry through the **HACS three-dot menu**. This removes
   managed component files; it is not deletion of the configured integration
   under **Devices & services**.
2. Under **HACS → three-dot menu → Custom repositories**, add
   `https://github.com/martins-netizen/ha-meteoswiss` as **Integration**.
3. Open **MeteoSwiss (maintained fork)** and **Download/Redownload**.
   Under **Need a different version? → Release**, explicitly select **8.2.0b1**.
   Verify the announced version before download. Older HACS versions may need
   beta visibility. If the target is missing or HACS rejects the switch, stop;
   do not delete HA configuration or edit hidden storage files.
4. Check the paired warning changes, then restart HA **once**. No extra restart
   is intended between removing and replacing software.

The [HACS acceptance precheck](HACS_ACCEPTANCE.md) distinguishes version
selection from actual replacement. Confirm backup, recovery and target before
removing the old software entry.

Both repositories manage the same `meteoswiss` directory. Keep exactly one
active software owner. Switching HACS source intentionally retains measurement
history but replaces component files; resolve local code/translation patches first.

## 5. Check the result

- The **existing** entry loads with its previous station and postcode.
- Retained IDs, charts and official hourly rain statistics continue.
- Observations, forecasts and active/upcoming warnings are plausible; a
  successfully empty feed is distinguishable from source failure.
- Measured-pollen station, intentionally disabled helpers and personal display
  precision remain. Weather and pollen stations are independent.
- Consumer mapping is correct; re-enable only previously enabled automations.

Missing individual values are not automatically installation failures.
See [initial values](GETTING_STARTED.md#4-check-pollen-station-and-initial-values).
A visual check is not ordinary-operation observation, and acceptance of older
runtime code does not automatically accept a later changed runtime.

## If something fails

Keep affected device automations paused. Use the verified backup/recovery route
to restore **software and paired warning changes together**. Restart and verify
that previous version. Do not mix code and warning filters from different generations.

Do not delete entries, entities or statistics as a troubleshooting shortcut.
Provide version, previous source, time and relevant redacted logs; do not post
full backups or credentials.

Bundled UI languages update with the software. Do not overwrite them with old
translation files. Personal dashboard labels remain separately maintained.
