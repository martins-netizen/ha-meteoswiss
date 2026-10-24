# 8.3.0b2 — forecast display test prerelease

**Prepared candidate:** 24 October 2026. This file does not establish publication
or practical HA acceptance. Use only the explicitly announced GitHub prerelease.

This community fork builds on LNKtwo/ha-meteoswiss and retains its MIT licence
and attribution. It is not an official MeteoSwiss product.

## Why this follow-up

Testing 8.3.0b1 confirmed the Säntis station/POI choices, but its device and
combined weather row still labelled the resulting predictions as Kloten.
This package contains the reviewed display separation from PR #61, source
**781ba3a41fafc2e8dd5bc5f867f55c646c4a2412**, plus the b2 version fields.
Its 36 other component files, HACS metadata and workflows match that source.
It keeps the earlier location/POI, forecast-sensor and architecture work.

## Distinct places and source roles

- **Current-condition device:** retains the station/base-source values and
  original weather entity. SwissMetNet readings are observations; the optional
  Open-Meteo current source remains modelled current conditions.
- **Named forecast device:** for example **MeteoSwiss Säntis (Forecast)**,
  translated in English/German/French/Italian. It groups the eight existing
  forecast scalars and daily HGT with a new forecast-only weather entity.
- **Forecast weather entity:** its current model hour and hourly/daily
  predictions all use ICON for the selected point. It never combines Kloten
  measurements with Säntis predictions. Missing model fields remain missing.

The forecast group reuses the existing HGT device identity. Existing entity,
unique and statistic IDs, personal names/options and areas are retained.
An old technical ID may still contain Kloten. User-chosen names are respected
and can override automatic labels. Changing a selected place updates this
entry's forecast context, not separate historical series per place.

## One change for forecast cards and actions

After an explicit catalogue choice, the original current-condition weather
entity **does not advertise forecast features**. In a forecast card or
`weather.get_forecasts` action, select the new weather entity from the named
forecast device. Keep the original station entity for current readings.
The [display and migration guide](FORECAST_DISPLAY.md) shows the exact steps.

Without a catalogue selection, the original combined weather interface remains
available for compatibility. The new forecast entity is available there too,
labelled as the base location. No dashboard or automation is rewritten.

## What keeps its meaning

ICON Seamless remains supplied through Open-Meteo; this is no model change or
accuracy guarantee. All projections reuse the existing forecast coordinator
and snapshot: no extra forecast request, cache or poller. Forecast selection
affects ICON weather/scalars/HGT, not observation, warning postcode, measured
pollen station or modelled AQ/pollen/UV base location. App v3 warnings retain
their independent verified-code/postcode feed.

The clock-change limit is unchanged: fixed-offset native daily buckets that
do not span the exact Swiss calendar day are withheld. Around **25 October
2026**, temperature/rain/HGT daily values can be `unknown` while hourly
forecasts remain usable. Complete hourly probability windows keep their
correct UTC-offset timestamps. No fabricated zero or partial-day estimate.

Provider place names are not a multilingual alias index: **Murten/3280** works;
Morat/Môrat is not yet an alias. See [location selection](FORECAST_LOCATION_SETUP.md).

## Install and check only in the existing temporary HA

Keep its existing entry and backup. After actual publication, refresh the
already-added fork in HACS and explicitly download **8.3.0b2**, then restart
HA once. Confirm the loaded version and the named forecast group before
changing a test card. The [focused b2 protocol](ACCEPTANCE_8.3.0b2.md) covers
the changed display, retained IDs, point changes/reset and remaining b1 checks.
Completed clean-install/restore evidence is retained; no blanket new 24-hour
wait is introduced. A source outage alone is not a demonstrated regression.

This is a **test prerelease**, not stable promotion or HACS default-list
admission. Stable **8.2.0** remains Latest; 8.3.0b1 and earlier tags are retained.
Minimum HA stays **2026.8.3**, CI **2026.8.3 / 2026.10.1**, with local testing
also on **2026.10.2**. No official Silver/Gold tier is claimed.

## Recovery

Record the prior HACS version and chosen locations before testing. Return the
forecast to the original base coordinates explicitly if that is the desired
context. To recover the exact former test installation, restore its retained
backup. Downloading the preceding 8.3.0b1 alone retains saved point data, but
restores its ambiguous combined display and lacks the new forecast weather
entity. Cards/actions changed to that new entity must target the old entity
again or be restored from backup. Do not delete the integration or purge history.
Stable 8.2.0 uses its earlier base-location routing, not the saved catalogue POI.
