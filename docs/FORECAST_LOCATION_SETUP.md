# Choose or change a weather forecast location

**Guide version:** 1.11 · **Updated:** 26 November 2026

Location selection has been available since [8.3.0](RELEASE_8.3.0.md).
[8.4.0](RELEASE_8.4.0.md) includes a shorter search flow and search names in
other Swiss languages for selected postal forecast points.

## What you are choosing

The forecast location is the place for **ICON weather forecasts**, the
forecast sensors and calculated heating degree days. You might
want observations at Zürich/Kloten while checking a forecast for Säntis.

The observation station, current-weather base coordinates, modelled air
quality/pollen/UV, measured-pollen station and warning postcode remain separate.
A mountain forecast does not establish warning coverage for that mountain.
Existing names/IDs are retained; local forecast_location attributes identify
the chosen forecast point. After moving the forecast, the weather entity's
current symbol no longer borrows that different-location forecast; current
measurements remain available.

## Separate measurement and forecast display

The [display guide](FORECAST_DISPLAY.md) describes the named forecast device,
its sensors and forecast weather entity. Station entities/IDs and personal
names remain; existing cards/actions for a selected point use the new forecast
weather entity. The measuring station has its own [modelled condition](STATION_WEATHER_CONDITION.md),
with unchanged measured numeric values. The initial b1 ambiguity is corrected.

## New setup

1. Choose the current-weather source and measured-pollen station as before.
2. Choose the observation station or current-weather base coordinates and the
   separate four-digit warning postcode. The source is checked first.
3. At **Weather forecast location**, either keep the original base location or
   choose **Search by postcode, town or POI**. Enter a four-digit postcode or a
   place name in the field that appears and submit the form to see the results.
   Try **8302**, **Morat**, **Säntis**, **Gotthardpass** or **Albert-Heim-Hütte**.
4. Select the intended result. Check its category, catalogue height above sea
   level and coordinates. A postal-code point is an assigned forecast point,
   not a post office or the exact position of your home. A station and a
   same-named POI are different points. No result is preselected.
5. Read **Confirm the forecast location**, including the unchanged warning
   postcode, then submit. The selected point's ICON response is checked before
   saving. **Search for another location** returns without saving.

One configured entry has one forecast location. The existing guards against
duplicate current-source/warning entries still apply.

## Existing entry

Open **Settings → Devices & services → MeteoSwiss → Configure (gear)**.
Change the weather station, measured-pollen station and forecast point in the
same form, alongside the independent warning postcode. For a new forecast point,
choose **Search by postcode, town or POI**, enter the search term in the same
form, then select and confirm the intended result. Cancelling an unfinished
step discards all pending changes. See
[unified settings](CALENDAR_AND_LOCATION_SETTINGS.md).

The entry and retained entity/statistic IDs, personal names and legacy intervals
remain. A loaded entry reloads once after a confirmed change without a Core
restart. Keeping the current forecast leaves that role unchanged; other settings
are still applied if deliberately changed and confirmed.

**Three-dot menu → Reconfigure** opens the same
complete settings dialog. You can change weather observations, measured pollen,
forecast point and warning postcode together through either route. A failed
source check retains the chosen search/reset for the retry. If another dialog
saves settings first, the older dialog aborts without overwriting them; reopen
it to review the current values. This shared route first shipped in
[8.3.2](RELEASE_8.3.2.md).

To undo a forecast move choose **Return to the original base coordinates** and
confirm. An invalid saved point needs a replacement or explicit reset; keeping
it cannot conceal an invalid selection. Do not delete/recreate the entry.

## No match, too many matches or a failed source

Search runs locally over the bounded official catalogue. Search text is not
sent to a geocoder. Refine queries producing more than twenty matches. Accents,
case, punctuation and German ae/oe/ue spellings are supported. If the catalogue
fails to load or the search gives no match, retry in the same form.
A failed ICON check leaves the confirmation open for retry or another search.
Cancelling any unfinished change preserves the entry. Normal HA startup needs
no catalogue download; a previously confirmed valid selection remains usable.

## Languages and place names

Dialogs, help, actions and point categories ship in **English, German, French
and Italian**. The official catalogue supplies just one point_name per record;
its four language columns describe **categories**, not translated place names.
The integration keeps those provider names. It does not translate or invent
summit/pass/hut subtypes from a generic POI category.

Searching for **Morat**, **Môrat** or **3280 Morat** finds **Murten** (point **2/328000**).
Searching for **Genève**, **Geneve** or **Genf** finds **1201 Genève**.
Searching for **3280** also shows **Greng** and **Meyriez**, which have their own
forecast points. The selected point keeps its MeteoSwiss name in Home Assistant.
Verified postal aliases from swisstopo are available in all interface languages.
Stations and POIs keep their catalogue names. See the
[alias coverage and sources](FORECAST_LOCATION_CATALOGUE.md#multilingual-postal-search-names).

## Verification after a location change

For focused tests of a future changed selection flow, exercise the postcode, summit, pass
and hut examples above, including Säntis station versus POI. Confirm the chosen
name/height in local forecast attributes and actual forecast values. On an
existing entry, cancel once, keep once, then confirm a change and reset it;
check that other source settings, IDs and values remain. Review one non-English
UI and confirm both Murten and Morat find the same forecast point. These are targeted feature checks,
not a repeat of completed 8.2.0 clean-install/restore acceptance or a new blanket
24-hour waiting period. See [the saved-location contract](SAVED_FORECAST_LOCATION.md)
for storage, privacy, height/cache rules and downgrade behaviour.
