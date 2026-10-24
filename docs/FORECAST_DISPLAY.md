# Keep current conditions and a selected forecast location distinct

**Guide version:** 1.1 · **Updated:** 24 October 2026.
**Availability:** the prepared **8.3.0b2** candidate, based on reviewed PR #61.
This correction is not included in immutable 8.3.0b1 or stable 8.2.0. Follow the
[b2 notes](RELEASE_8.3.0b2.md) and [focused protocol](ACCEPTANCE_8.3.0b2.md);
wait for an announced release rather than downloading a branch.

## What changes on screen

Choosing Säntis for a forecast does not move the Zürich/Kloten observation
station. In 8.3.0b1 the station device still grouped the forecast values under
its Kloten heading. Its combined weather row could show Kloten's temperature
alongside Säntis's daily extremes. That presentation was ambiguous.

The follow-up gives predictions their own named device and weather entity:

| Group | Values shown | Location |
|---|---|---|
| MeteoSwiss Zürich/Kloten | Existing current-condition weather entity and station sensors | The selected observation station. For the alternative current source these remain modelled current conditions at its configured base coordinates. |
| MeteoSwiss Säntis (Forecast) | New forecast weather entity, eight today/tomorrow sensors and calculated HGT | The explicitly selected forecast point and its catalogue height. |
| Existing warning, measured-pollen and AQ/pollen groups | Their existing values | Their independently configured postcode, pollen station or base location. |

The forecast group's name is translated in EN/DE/FR/IT; in German it is
**MeteoSwiss Säntis (Prognose)**. Its weather entity's temperature, condition,
humidity and wind are **ICON model values for that point**, including the
current model hour. They are not measurements from Säntis. The `value_type`
attribute is `forecast`; selected name, category and height remain in
`forecast_location`. A field absent from ICON, such as current pressure, stays
absent. Neither missing model hours nor a failed forecast borrow Kloten values.

## Update an existing card or forecast action once

After installing the announced follow-up and restarting HA:

1. Open **Settings → Devices & services → MeteoSwiss**. Find the device named
   after your forecast point. With an unchanged base location it is named
   **MeteoSwiss Forecast (base location)** instead.
2. Open its **weather entity** and check the location and forecast. Use this
   entity in cards that should show the selected place's weather predictions.
3. For an existing weather card, edit the card and choose that forecast weather
   entity. For a `weather.get_forecasts` action, change its entity target to the
   same entity. Exact IDs depend on the HA language and personal renaming;
   select the entity from its device rather than copying a guessed ID.
4. Keep the original station weather entity for current conditions. After an
   explicit catalogue selection it does **not** advertise hourly/daily forecasts.
   Consequently, a forecast card/action targeting that old entity must be
   switched as above. An entry with no catalogue selection retains its legacy
   combined weather interface for compatibility; the new forecast entity is
   also available and makes the source role explicit.

No dashboard or automation is rewritten automatically. Station measurements,
warning postcode, air quality and pollen settings do not move with the forecast.

## Existing names, IDs and history

**Development after b3:** the observation weather row can also have a
[station-local modelled condition](STATION_WEATHER_CONDITION.md). Its numeric
values remain measured; its condition is not borrowed from this forecast group.
HA may show the forecast condition only as an icon in the compact device-page
row, with its text in the weather detail/activity view. That layout does not
mean the condition is missing from the weather entity.

The eight existing forecast sensors and HGT keep their unique/entity IDs and
personal options. They move to the forecast group, which reuses HGT's existing
device identity instead of creating a different device for every chosen place.
Personal entity names, device names and areas are retained. A user-chosen name
can override the automatic location label; check it if the displayed label is
still misleading after the update.

Old technical entity IDs may therefore still contain `kloten`; changing those
automatically would break existing references. Default display names identify
the forecast group. Selecting a different place or explicitly returning to the
base location updates that group, without deleting history or creating a set of
entities per place. History follows the configured entry; it is not an archive
of separate per-location series. Forecast scalars still have no measured-total
state class, and HGT's existing calculation/statistics contract is unchanged.

The new forecast weather entity has a separate stable unique ID ending in
`_forecast_weather`. It and all forecast projections reuse the existing ICON
coordinator and snapshot. No second forecast request, new cache or poller is
added. Forecast subscribers receive refresh/failure/recovery and are removed on
unload. Invalid saved selections remain explicitly unavailable.

## Focused follow-up check

Keep the existing temporary HA entry and its backup. After the follow-up is
reviewed, published and installed, check these changed display paths:

- Select **Säntis** deliberately. Station and POI remain distinct choices. The
  forecast group identifies Säntis; its current model hour and daily/hourly
  predictions refer to that point. Kloten current conditions stay on Kloten.
- Check that all eight scalar sensors and HGT belong to the forecast group,
  with retained IDs and personal names/options. Open a probability window.
- Point one test weather card/action at the new forecast weather entity. Do not
  infer that its current model-hour temperature is a station measurement.
- Change the selected point, then explicitly reset to the base location.
  Check the updated label, retained IDs and unchanged other source settings.
- Keep `unknown` daily values around the 25 October clock change separate from
  source `unavailable`; the [known calendar-day limitation](FORECAST_SENSORS.md)
  is unchanged by this display correction.

The earlier [8.3.0b1 protocol](ACCEPTANCE_8.3.0b1.md) is preserved as the published
baseline. Continue its remaining pass/hut, language and new-entry checks using
the follow-up's forecast device. Completed installation/restore evidence is not
reopened; no new blanket 24-hour wait is required.
