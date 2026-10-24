# Focused acceptance of 8.3.0b2

**Protocol version:** 1.0 · **Prepared:** 24 October 2026.
Run only after the exact approved b2 prerelease is published. These are
prepared steps, not a claim of completed operator acceptance.

## Update the existing temporary UTM HA

1. Check that you are in the temporary instance. Retain its current backup and
   make a new backup before this update. Keep the configured MeteoSwiss entry,
   source settings, interval and important IDs. Do not repeat a clean install
   or isolated restore that already passed.
2. In the already-added **martins-netizen/ha-meteoswiss** HACS entry, refresh
   information and choose Download/Redownload → another version → Release →
   **8.3.0b2**. Enable beta visibility if needed. If that exact release is absent,
   stop at selection; do not download a branch or add the repository again.
3. Download and restart HA once. Confirm the downloaded and loaded b2 version.
   Keep the current Säntis choice if it is still saved; no initial reset is needed.

## Check the display correction

| Check | Expected result | Record |
|---|---|---|
| Current-condition device | Kloten keeps its current readings and original entity IDs. With an explicit forecast-point choice, its weather row does not contain that point's forecast extremes. | Device name/current temperature and old IDs. |
| Forecast device | A separate named group identifies Säntis and the forecast role. Its eight scalar sensors and HGT retain their previous IDs/options. | Name, selected category/height in attributes, group membership. |
| Forecast weather entity | A new weather entity belongs to that forecast group. Its current-hour model values and forecast concern the same selected point. Pressure may be absent; no station fallback is expected. | Name, current model temperature, hourly/daily forecast. |
| Test card/action | Select that new forecast weather entity in one forecast card or weather.get_forecasts action. Keep current-condition cards on Kloten. | Correct place visible and forecast returned. |
| Own names | Existing user names/device areas/options survive. A manually chosen name can override automatic location wording; adjust it deliberately if needed. | Retained user settings. |
| Cancel/keep/change/reset | Cancel a search, explicitly keep the saved point, then select a different point and finally confirm return to original base coordinates. Cancel/keep do not change it; change/reset update the forecast group without duplicate devices/IDs. Other source locations remain. | Labels, IDs, unchanged source roles. |
| Missing data | Daily unknown around the 25 October clock change remains distinct from a source outage. Hourly forecasts and complete probability windows can still work. | Affected field/date if unexpected. |

Do not expect station and model temperatures to match. No physical device
needs to be operated. A fresh forecast source failure and recovery have
automated coverage; do not deliberately interrupt the household network.

## Finish only the remaining feature checks

Säntis station/POI choices and initial display were already observed in b1;
repeat their selection only as needed for the corrected display. Complete
the outstanding **Gotthardpass / Albert-Heim-Hütte**, another UI language,
Murten/3280 alias boundary and temporary additional-entry checks from the
[original protocol](ACCEPTANCE_8.3.0b1.md), using the new forecast entity.
Keep the existing entry. Remove only a clearly identified extra test entry
after recording its result. Confirm both forecast and warning postcodes retain
their independent purposes.

Report HA/HACS versions, loaded b2, table results and remaining feature results.
If one field is unexpected, include its time/source status, not private
coordinates/tokens/full backups. After this focused acceptance, reconcile the
record and make a separate stable-release decision. No automatic production
install, HACS submission or new blanket waiting period is part of this check.
See [release notes and recovery](RELEASE_8.3.0b2.md).
