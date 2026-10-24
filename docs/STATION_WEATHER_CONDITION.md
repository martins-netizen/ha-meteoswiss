# A weather condition for the observation station

**Guide version:** 1.2 · **Updated:** 24 October 2026.
**Availability:** included in the **8.3.0** runtime accepted as b4.
Use the [announced release](RELEASE_8.3.0.md); earlier beta notes describe their
historical scopes, not instructions to reinstall an older beta.

## What you see and where it comes from

The station weather entity can show a condition such as **Cloudy**, alongside
its measured temperature, humidity, pressure and wind. The condition is
**modelled for the selected weather station's location**, using MeteoSwiss
ICON Seamless through Open-Meteo. It is not a measured SwissMetNet weather code.
Open-Meteo derives the symbol from the model fields; the
[provider documentation](https://open-meteo.com/en/docs/meteoswiss-api)
describes this distinction and the current model-hour data.

For example, with **Altdorf measurements** and a **Säntis forecast**:

| Item | Location and source |
|---|---|
| Station temperature, humidity, pressure, wind and precipitation | Altdorf's SwissMetNet measurements, unchanged. |
| Station weather condition/symbol | Modelled for Altdorf, at the catalogue coordinates and height. |
| Forecast weather entity, today/tomorrow sensors and HGT | The explicitly chosen Säntis point, unchanged. |
| Warnings, measured pollen and modelled AQ/pollen/UV | Their own previously configured locations, unchanged. |

The station's existing weather entity and IDs are retained. Its attribution
credits SwissMetNet and the model delivery through Open-Meteo. Local attributes
`condition_value_type: modelled`, `condition_location: weather_station`,
`condition_source` and `condition_timestamp` make the condition's origin
explicit; `condition_available` describes only this additional field. No new
entity or location setting is required.

In HA's compact device-page weather row, the condition may be shown only as
an icon while temperature and daily extremes occupy the right-hand side.
The condition text is available in the weather detail/activity view. A missing
word in that compact row is different from an actual `unknown` weather state.

## Why it was unknown before

Stable 8.2.0 could borrow the current ICON interval's condition for its combined
weather row. With explicit town/POI forecasts introduced in 8.3.0b1, that reuse
was blocked: Säntis snowfall must not become Altdorf's current weather condition.
The SwissMetNet observation payload supplies measured quantities, without this
qualitative code, so the station row could correctly have measured attributes
while its condition was `unknown`. This follow-up supplies the missing
station-local model condition without borrowing another location's forecast.

## Requests, validity and failures

- A separate optional coordinator uses the shared authoritative station
  catalogue to obtain the selected station's coordinates and available height.
  It does not substitute HA home coordinates, the warning postcode or a POI.
- The small request asks only for `current=weather_code,is_day`, explicitly
  with `models=meteoswiss_icon_seamless`. It downloads no extra daily/hourly
  forecast arrays. Existing forecast requests and source selection are unchanged.
- Refresh is normally every ten minutes, earlier when the current model
  interval ends. The coordinate/height-specific cache lasts at most ten minutes
  and never beyond that interval. Hits do not extend its original lifetime.
  Polling frequency is not a claim that the provider issues a new model run
  every ten minutes. Retries and deliberate reloads can make extra requests.
- Valid codes, daylight, provider interval and timestamps are checked. Expired,
  missing or invalid conditions remain `unknown`, without invented sunshine,
  a last-good value masquerading as current, or rain inferred from another source.
- A condition or station-metadata failure does not prevent valid station
  measurements from loading. Only the condition becomes unknown. A failure of
  the observation source itself retains its existing unavailable semantics.
- Station changes through Configure reload the entry once and choose the new
  station's metadata. Measured pollen and forecast choices retain their own roles.
  Model requests/tasks/listeners are entry-owned and cancelled on unload; HA's
  borrowed HTTP session is never closed by this source.

The alternative Open-Meteo current-weather source already supplies its own
modelled condition and does not gain this additional request. Missing catalogue
coordinates do not trigger an arbitrary geographic fallback. Logs and downloaded
diagnostics omit location URLs, cache keys and raw provider payloads.

## Focused verification after installation

Keep the existing entry and select different measurement and forecast places.
Confirm a station-local condition plus unchanged measured values, and a
separately named forecast point. Change the weather station while keeping the
forecast point: the condition request follows the station and the entity IDs
remain. Check a night symbol if naturally available. Do not force an outage,
change HA's clock or repeat a clean install/restore to test this correction.
An actual provider failure should leave measured values usable and affect only
the condition. Automated lifecycle/error/interval regressions complement this
focused operator check; they do not establish a successful user installation.

The operator accepted b4 and requested stable promotion on 24 October. The
[readiness record](RELEASE_READINESS.md) distinguishes the visible screenshots,
operator report and automated coverage. Do not repeat the completed check just
for the stable version-only promotion.
