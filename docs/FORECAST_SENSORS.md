# Forecast sensors: today and tomorrow

**Guide version:** 1.7 · **Updated:** 24 October 2026
**Availability:** included in the **8.3.0** runtime accepted as b4.
Use the [announced release](RELEASE_8.3.0.md); earlier beta notes describe their
historical scopes, not instructions to reinstall an older beta.

## What you get

Eight numeric sensors make the existing location forecast available to ordinary
HA cards and automations. They belong to
the named forecast device alongside HGT and a separate forecast weather entity,
retaining IDs and personal names. Names ship in
English, German, French and Italian. No extra integration, API key or second
forecast request is needed.

| Sensor | Today | Tomorrow | Unit |
|---|---|---|---|
| Maximum temperature | Whole-day forecast maximum | Whole-day forecast maximum | °C |
| Minimum temperature | Whole-day forecast minimum | Whole-day forecast minimum | °C |
| Precipitation | Whole-day forecast amount | Whole-day forecast amount | mm |
| Highest hourly precipitation probability | Current and upcoming hours | All hours tomorrow | % |

These are **predictions**, not measured daily records. Today's temperature
extremes may already have occurred. Today's rainfall prediction includes the
elapsed part of the day; it is not the amount still expected or already measured.
Native aligned daily fields supply those three full-day values. They are never
reconstructed from only the remaining rolling hours.

**Complete Swiss calendar days:** Open-Meteo’s native daily buckets use one
fixed UTC offset per response. If such a bucket does not match the Swiss
midnight-to-midnight period, the source derives the affected day from complete
hourly coverage of the **23, 24 or 25 physical hours** of that Swiss day. The
same request includes the elapsed part of today. Daily scalar values, HGT and
the weather entity share the validated result. Missing/invalid/gapped fields
remain unknown independently, and zero remains zero. Attributes `aggregation`
(`provider_daily` or `hourly_calendar_day`) and `day_hours` distinguish the basis.
These are hourly-sampled model aggregates; no finer-resolution extrema are
claimed. For the original b1/b2 limitation and its correction see
[calendar-day behaviour](CALENDAR_AND_LOCATION_SETTINGS.md).

The source remains **MeteoSwiss ICON Seamless via Open-Meteo**, at the existing
forecast location. An explicitly saved catalogue point routes these sensors and calculated HGT; local forecast_location attributes identify
its name, category and height. The translated setup/Configure dialog selects it; see [the selection guide](FORECAST_LOCATION_SETUP.md)
and [saved-location contract](SAVED_FORECAST_LOCATION.md). Warning postcode,
forecast location and observation station
have distinct purposes; see [getting started](GETTING_STARTED.md).

## What does an 80% probability mean?

The sensor contains the highest **single hourly probability** in its period.
It is not the probability of rain at any time during the entire day, an average,
or a probability obtained by combining hourly values. Today considers the
current and later hours, so an elapsed morning peak drops out in the afternoon.

The matching time appears in attributes. State `80` with
`peak_start: 2026-10-23T14:00:00+02:00` and
`peak_end: 2026-10-23T15:00:00+02:00` means **80% between 14:00 and 15:00**.
It does not promise rain starts at 14:00. Adjacent equally high hours form one
window. Separate equally high windows are all retained in `peak_periods`;
`peak_start`/`peak_end` describe the first one. A complete series with 0% returns
numeric zero and no peak time. Missing or invalid hours produce `unknown`.

[Open-Meteo's hourly convention](https://open-meteo.com/en/docs) assigns
precipitation probability to the **preceding hour**: a row stamped 15:00 describes
14:00–15:00. Tomorrow's 00:00 row closes today's last hour. The calculation uses
physical UTC hours and Swiss calendar boundaries, including 23-/25-hour days.
Local times carry UTC offsets to distinguish repeated hours.

## Attributes and availability

Find entities under **Settings → Devices & services → MeteoSwiss**. Inspect
attributes in **Developer tools → States**. Entity IDs depend on your HA
language and personal renaming; the internal keys below are stable.

| Attribute | Meaning |
|---|---|
| `value_type` | Always `forecast`, distinguishing predictions from observations. |
| `forecast_date` | Target date in Europe/Zurich. |
| `forecast_period` | `full_day`, or `remaining_hours` for today's probability. |
| `source` | MeteoSwiss ICON Seamless via Open-Meteo. |
| `fetched_at` | Snapshot retrieval time in UTC, not model issuance time. |
| `expected_hours`, `valid_hours` | Probability interval coverage for the stated period. |
| `coverage_complete` | Whether every expected probability interval is valid. |
| `peak_start`, `peak_end` | First maximum-probability window, or null. |
| `peak_periods` | All maximum-probability windows as `{start, end}` pairs. |

An available source with a missing field produces `unknown`. A failed source,
missing retrieval timestamp, snapshot older than three hours, or retrieval time
more than ten minutes in the future produces `unavailable`. Old peak times are
not carried into an unavailable state. HA may omit unavailable attributes;
templates should handle their absence.

The existing coordinator refreshes hourly. Local timers update remaining-hour
selection, midnight rollover and the age boundary without network requests.
Unloading the entry removes those listeners.

## Cards, automations and history

Use an ordinary entity card or numeric-state condition with the numeric sensor.
A template can show probability plus `peak_start`/`peak_end`; use `peak_periods`
to display every tied window. Check `has_value(entity_id)` before formatting
numbers, and handle an empty peak list.

Keys are `forecast_<metric>_<day>`, where `<day>` is `today`/`tomorrow` and
`<metric>` is `maximum_temperature`, `minimum_temperature`, `precipitation` or
`probability`. Unique IDs include the config-entry ID. Reloads retain entity
IDs; no retained observation, weather or statistic ID is changed.

These sensors have **no measurement/total state class**. Their target date moves
at midnight and predictions change during the day; they must not become measured
daily totals or long-term rainfall statistics. Normal Recorder history can show
how a prediction changed. For measured rainfall use the
[official hourly statistics](SENSORS.md#completed-hourly-precipitation-statistics).
In the prepared b2 display correction, forecast cards/actions for an explicit
catalogue selection use the new forecast weather entity. The original weather
entity retains current conditions and its ID. Without a catalogue selection,
its legacy forecast interface remains available; see [migration](FORECAST_DISPLAY.md).
