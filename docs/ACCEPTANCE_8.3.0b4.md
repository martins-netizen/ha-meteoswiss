# 8.3.0b4 focused Home Assistant acceptance

**Protocol version:** 1.0 · **Updated:** 24 October 2026

Use the existing temporary HA, entry and maintained-fork HACS repository.
Install only after publication of **8.3.0b4** is confirmed; record the version
after the one post-download HA restart. Retain the existing backup.

| Check | Action and expected result | Record |
|---|---|---|
| Station condition | Open the weather measuring station. A valid available model code now gives a condition/symbol, while the numeric values still match its measured sensors. | Station, condition and temperature/humidity. |
| Independent forecast | Keep a different explicit town/POI forecast. Its device/weather entity and scalars still concern that point. A station's condition must not copy the POI merely to become known. Matching codes can naturally occur. | Measurement and forecast places. |
| Provenance | Open the station weather entity's attributes. `condition_value_type` is `modelled`, `condition_location` is `weather_station`, and source/time/availability are present for a usable condition. | Attributes or focused screenshot. |
| Station change | Through existing Configure, change only the weather station while keeping pollen and forecast choices. The condition follows the station, numeric measurements/labels identify it, and existing entity IDs/personal names remain. | Before/after station and retained names. |
| Restore intended choices | Restore the desired station and any deliberately changed settings. The HA home location remains a general HA setting. | Intended places restored. |
| Natural failure/night | If naturally observed, only a failed condition becomes unknown while measurements remain usable; a clear night must not show sunshine. Do not force an outage or wait for one just to finish this check. | Any actual new failure or night-symbol finding. |

On the compact HA device page, the forecast condition may be represented only
by an icon beside temperature/extrema; the detail/activity view supplies its
text. That is different from an actual `unknown` condition.

The existing automated HA regressions already exercise source outages,
expiry/cache boundaries, reload/unload, pending-request cancellation and session
ownership. Do not change the clock, recreate the integration or perform another
restore rehearsal. No blanket 24-hour observation period is added. Retain the
successful b3 calendar-day/combined-settings and prior installation evidence.

Record actual outcomes in the operational master. Candidate acceptance does not
publish stable 8.3.0; stable promotion remains a separate reviewed decision.
