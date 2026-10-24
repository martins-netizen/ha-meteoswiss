# 8.3.0b3 focused Home Assistant acceptance

**Protocol version:** 1.0 · **Updated:** 24 October 2026

**Prerequisite:** the reviewed b3 package is explicitly published and downloaded
through the existing maintained-fork HACS entry. An open PR or a source version
is not an installation target. Use the existing temporary HA; retain its backup.

## Record the starting point

Confirm **8.3.0b3** after the one post-download Core restart. Record the actual
HA version, weather station, pollen station, forecast point and warning postcode.
The previously reported successful beta test on HA 2026.10.3 is a baseline,
not a result to repeat or a substitute for these new checks.

| Check | Action and expected result | Record |
|---|---|---|
| One dialog | Open the existing entry's Configure gear. Weather station, measured-pollen station and forecast action appear together, alongside warning postcode. Current choices remain selected. | Screenshot and retained defaults. |
| Cancel all pending changes | Change weather and pollen stations, choose forecast Search, select a test point, then cancel before final submission. Reopen Configure: every original choice remains. | Choices retained. |
| Weather station alone | Confirm a different valid measuring station while keeping pollen and forecast. Existing observation IDs/personal names remain, new measurements/labels identify the new station, and forecast stays at the chosen POI. | Before/after station, values and IDs. |
| Combined change | Choose all three locations together. Search/select/confirm remains inside the same flow; the final page lists pending choices and saves them together. Warning postcode is independent. | Confirmed choices and separate devices. |
| Forecast reset | Explicitly reset the forecast to the original base coordinates and confirm. Observation and measured-pollen choices stay as selected. Restore the intended forecast afterwards. | Independent choices retained. |
| Calendar-day values | When complete source data are available, inspect high, low and rain for today/tomorrow, plus today's HGT. Scalar aggregation/day_hours identify the basis. A complete clock-change day uses 23 or 25 physical hours; missing coverage remains unknown. | Values, date and relevant attributes. |
| Forecast display | The named forecast weather entity's current model hour and hourly/daily forecasts concern that same forecast point. Current station measurements remain separate. | Selected point, forecast card/action target. |
| Histories and archives | Deliberate station changes continue retained observation histories; earlier readings are retained. Explicit station-specific precipitation archive cards remain on their old station until retargeted. | Any consumer needing a deliberate change. |
| Language | Read the common dialog and its search/confirmation in the configured UI language; station/provider names are retained. | Any unclear label or untranslated field. |

Restore the intended weather, pollen, forecast and warning choices after
deliberate test changes. The HA home position remains a **general HA setting**;
do not move it to test a weather measuring station or a forecast POI.

Do not create a fake historical date, force an outage or invent zero values.
Deterministic regressions cover both clock changes and missing/invalid hours.
No additional test entry, full clean installation, restore rehearsal or blanket
24-hour waiting period is required for this focused patch. Investigate a
concrete new failure if one appears.

## Completion boundary

Record actual outcomes in the operational master. Publication is complete only
after its GitHub checks; these UI/source checks are complete only after the
operator's actual observations. Stable 8.3.0 promotion is a separate decision.
