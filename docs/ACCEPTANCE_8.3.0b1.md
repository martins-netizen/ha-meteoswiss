# Focused acceptance of 8.3.0b1

**Protocol version:** 1.0 · **Prepared:** 24 October 2026.
Run only after the approved exact prerelease is published. This checklist is
prepared work, not a claim of an executed HA test.

## Prepare the existing temporary instance

1. Confirm you are in the **temporary UTM HA**, not production. Keep its HA and
   HACS versions for this check. Note the current MeteoSwiss entry, weather and
   measured-pollen station, warning postcode, personal interval and important
   weather/entity/statistic IDs. A few screenshots or notes are sufficient.
2. Create and retain a backup of that test instance. The earlier successful
   clean install and isolated restore remain completed evidence; they do not
   need to be repeated.
3. After publication, open the **already added martins-netizen/ha-meteoswiss**
   HACS repository, refresh information and open Download/Redownload. Under
   **Need a different version? → Release**, explicitly select **8.3.0b1**.
   Enable beta visibility there if required by your HACS version. If the exact
   release is missing, stop at selection; do not download a branch or add the
   repository again.
4. Download, restart HA once and confirm the downloaded/loaded 8.3.0b1 version.
   Keep the configured entry. Publication and download alone do not prove that
   the new code is loaded.

## Checks and expected results

Use **Settings → Devices & services → MeteoSwiss**. For the existing entry,
**Configure** edits measured pollen; **three-dot menu → Reconfigure** edits the
forecast location. In German the latter is **Neu konfigurieren**.

| Check | Expected result | Result to record |
|---|---|---|
| Existing entry after update | Retained entities/settings load; observations and warning/pollen roles are unchanged. Optional missing values are distinguishable from outage. No second integration entry appears. | Version, unchanged settings/IDs and initial values. |
| Cancel and keep | Open Reconfigure, start a search then cancel. Reopen and explicitly keep the current location. Neither operation changes the forecast point or other settings. | Both operations unchanged. |
| Kloten postcode | Search **8302**, deliberately select the Kloten postal-code point, inspect category/height/coordinates and confirm with the unchanged warning postcode. Nothing is preselected. | Selected label/height and actual hourly forecast. |
| Summit and ambiguity | Search **Säntis**. Distinguish the station from the generic POI. Select the intended POI and confirm. Current weather remains at its original source; forecast metadata identifies the POI and catalogue height. | Which point/category was chosen; forecast and current values. |
| Pass and hut | Repeat with **Gotthardpass** and **Albert-Heim-Hütte**. Each confirmed selection changes the forecast point only. | Name/category/height and forecast present or a specific error. |
| Forecast sensors | Eight today/tomorrow values exist on the weather device. Inspect one highest-probability sensor's peak_start/peak_end/peak_periods attributes. Zero has no invented peak time; predictions have no measured-total state class. | Visible entities and an example period/value. |
| Missing data and clock change | Distinguish unknown individual values from unavailable sources. Around the 25 October change, native daily temperature/rain/HGT may be unknown while hourly forecasts remain usable. Do not force a network outage or expect fabricated zeros. | Value/status and affected date/time if unexpected. |
| Language and place-name limit | Review the flow once in another available HA language. Actions/help/categories translate. **3280** or **Murten** resolves the town; Morat/Môrat does not yet resolve as an alias. | UI language and understandable labels. |
| Explicit reset | Reconfigure → return to original base coordinates → confirm. Check the prior source roles, personal options and retained IDs again. No Core restart is needed for a confirmed reconfiguration. | Original forecast behaviour and unchanged other settings. |

An ICON connection failure must leave the confirmation available for retry or
another search. A failed catalogue search must keep the previous saved point.
No physical device needs to be operated to verify these behaviours.

## New-entry path without discarding the existing test entry

Add **one extra temporary MeteoSwiss entry** with a different observation
station/warning-postcode combination from the existing entry. The normal
duplicate guard intentionally rejects an identical source combination.

Check that setup requires a measured-pollen choice, explains each location role,
has no polling-interval field, and then offers keep/search/select/confirm for
the forecast point. Choose **8302 Kloten** as forecast target and finish. Check
initial observations/forecast and the independently saved pollen station.
After recording the result, remove only this clearly identified extra test
entry if it is no longer needed. Preserve the original entry and its history.
Both current-weather paths and all four flow languages also have automated
coverage; an exhaustive manual repetition of every combination is not required.

## Report and next decision

Report: **HA version, HACS version, loaded 8.3.0b1, each table result, new-entry
result and any affected timestamp/source status**. Avoid sharing private
coordinates, tokens, full backups or unrelated log content. A source outage is
not automatically a software regression; provide the affected family and time.

If the changed paths pass, reconcile the exact candidate/acceptance record and
prepare the separate stable release decision. A specific new failure is fixed
and retested before promotion. No automatic merge, production installation,
HACS default-list submission or arbitrary new 24-hour wait is part of this
checklist. See [release notes and recovery](RELEASE_8.3.0b1.md).
