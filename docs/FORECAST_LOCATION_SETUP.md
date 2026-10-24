# Choose or change a weather forecast location

**Guide version:** 1.5 · **Updated:** 24 October 2026
**Availability:** included in the **8.3.0** runtime accepted as b4.
Use the [announced release](RELEASE_8.3.0.md); earlier beta notes describe their
historical scopes, not instructions to reinstall an older beta.

## What you are choosing

The forecast location is the place for **ICON weather forecasts**, the eight
today/tomorrow forecast sensors and calculated heating degree days. You might
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
eight scalars, HGT and forecast weather entity. Station entities/IDs and personal
names remain; existing cards/actions for a selected point use the new forecast
weather entity. The measuring station has its own [modelled condition](STATION_WEATHER_CONDITION.md),
with unchanged measured numeric values. The initial b1 ambiguity is corrected.

## New setup

1. Choose the current-weather source and measured-pollen station as before.
2. Choose the observation station or current-weather base coordinates and the
   separate four-digit warning postcode. The source is checked first.
3. At **Weather forecast location**, either keep the original base location or
   choose **Search by postcode, town or POI**.
4. Enter a four-digit postcode or a catalogue place name, for example **8302**,
   **Säntis**, **Gotthardpass** or **Albert-Heim-Hütte**.
5. Select the intended result. Check its category, catalogue height above sea
   level and coordinates. A postal-code point is an assigned forecast point,
   not a post office or the exact position of your home. A station and a
   same-named POI are different points. No result is preselected.
6. Read **Confirm the forecast location**, including the unchanged warning
   postcode, then submit. The selected point's ICON response is checked before
   saving. **Search for another location** returns without saving.

One configured entry has one forecast location. The existing guards against
duplicate current-source/warning entries still apply.

## Existing entry

Open **Settings → Devices & services → MeteoSwiss → Configure (gear)**.
Change the weather station, measured-pollen station and forecast point in the
same form, alongside the independent warning postcode. Search/select/confirm
continues inside this flow. Nothing is saved until final confirmation;
cancelling an unfinished step discards all pending changes. See
[unified settings](CALENDAR_AND_LOCATION_SETTINGS.md).

The entry and retained entity/statistic IDs, personal names and legacy intervals
remain. A loaded entry reloads once after a confirmed change without a Core
restart. Keeping the current forecast leaves that role unchanged; other settings
are still applied if deliberately changed and confirmed. The older
**three-dot menu → Reconfigure** remains a forecast-only shortcut.

To undo a forecast move choose **Return to the original base coordinates** and
confirm. An invalid saved point needs a replacement or explicit reset; keeping
it cannot conceal an invalid selection. Do not delete/recreate the entry.

## No match, too many matches or a failed source

Search runs locally over the bounded official catalogue. Search text is not
sent to a geocoder. Refine queries producing more than twenty matches. Accents,
case, punctuation and German ae/oe/ue spellings are supported. A failed catalogue
load leaves a retryable search and preserves the existing saved location.
A failed ICON check leaves the confirmation open for retry or another search.
Cancelling any unfinished change preserves the entry. Normal HA startup needs
no catalogue download; a previously confirmed valid selection remains usable.

## Languages and place names

Dialogs, help, actions and point categories ship in **English, German, French
and Italian**. The official catalogue supplies just one point_name per record;
its four language columns describe **categories**, not translated place names.
The integration keeps those provider names. It does not translate or invent
summit/pass/hut subtypes from a generic POI category.

For example, the audited catalogue contains **Murten, postcode 3280** as point
**2/328000**, but no separate Morat spelling. Murten and Morat refer to the same
place; [Swiss Post uses both names](https://site.post.ch/de/ueber-uns/post-eroeffnet-modernisierte-filiale-in-murten).
Enter **3280** or **Murten** for now. Accent normalization alone cannot turn
Morat (or Môrat) into Murten. A future sourced multilingual alias index must map
names to the same confirmed catalogue identity, preserve ambiguity and avoid
assuming that every locality sharing a postcode is the same forecast point.
Complete multilingual locality/POI names are **not** claimed by these dialogs.

## Verification after a location change

For focused tests of a future changed selection flow, exercise the postcode, summit, pass
and hut examples above, including Säntis station versus POI. Confirm the chosen
name/height in local forecast attributes and actual forecast values. On an
existing entry, cancel once, keep once, then confirm a change and reset it;
check that other source settings, IDs and values remain. Review one non-English
UI and the documented Murten/Morat limitation. These are targeted feature checks,
not a repeat of completed 8.2.0 clean-install/restore acceptance or a new blanket
24-hour waiting period. See [the saved-location contract](SAVED_FORECAST_LOCATION.md)
for storage, privacy, height/cache rules and downgrade behaviour.
