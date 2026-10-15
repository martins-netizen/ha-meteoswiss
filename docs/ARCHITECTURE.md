# Maintained fork: architecture and data contracts

## Purpose and boundaries

Maintain the existing integration for reliable local use while upstream PRs
remain pending. Preserve `meteoswiss`, config entries, unique IDs, entity IDs,
and Recorder statistic IDs. Upstream source, licence and attribution remain
recognisable. There is no new integration domain and no automatic migration of
users' dashboards. `main` follows upstream; `development` integrates reviewed
local changes. A release is an explicitly tested snapshot of `development`.

## Responsibilities

- API clients download and validate payloads. A transport or decoding failure
  must escape to the coordinator; it must not become an empty successful result.
- Coordinators own refresh intervals, success/failure status and data caching.
  Optional forecasts, alerts, pollen and precipitation imports cannot delay the
  required observation setup. Optional initial refresh tasks belong to the entry.
- Entities expose values and availability; display translations never determine
  automation logic. The native HA update lifecycle handles unload and reload.
- Home Assistant owns the shared TLS-verified HTTP session. Each request has a
  30-second timeout. An entry must not close a session used by other entries.
- Retries are bounded and limited to transient transport errors, HTTP 408/429
  and server failures. Permanent HTTP errors, invalid JSON/schema and cancellation
  are not retried. A numeric Retry-After above the local delay limit defers the
  operation to a later refresh instead of retrying prematurely.

## Sources and time

| Data | Source and location | Time semantics |
|---|---|---|
| Observations | Selected SwissMetNet station, or configured Open-Meteo location | `last_update` is measurement time, aware UTC. Missing timestamps, age over one hour or more than ten minutes in the future fail the update. |
| Weather forecast | MeteoSwiss ICON Seamless via Open-Meteo at HA location (explicit coordinates for Open-Meteo entries) | Unix seconds from provider become aware UTC ISO strings. `local_date` is the Europe/Zurich date; `fetched_at` is retrieval time, not model issuance time. |
| Warnings | MeteoSwiss App API for configured postal code | UTC validity windows; active, upcoming and outlook remain separate. |
| Measured pollen | Selected MeteoSwiss pollen station | Provider measurement timestamp, independent of weather station. |
| Pollen/AQ forecast | Open-Meteo for forecast location | Select the actual current hour, never midnight or the next non-null future value. Missing data stays missing. |
| Hourly precipitation | Official station CSV, external Recorder statistics | Interval-end times are shifted to interval starts in UTC; IDs remain unchanged. |

Forecast rows contain `datetime`, `local_date`, `fetched_at`, `source`,
`weather_code`, `is_day`, `condition`, measurements and optional native daily
aggregates. Producer and consumer use `weather_data.py` for time/condition
normalisation. The two hours repeated at autumn DST remain distinct. Daily
labels respect Open-Meteo's returned fixed UTC offset; native daily aggregates
are provider buckets and are not claimed to be recalculated 23/25-hour local
measurement days. Missing aggregates can fall back to available hourly values;
for today these may cover only the remaining hours.

Failed or more than three-hour-old forecasts are not used as current conditions.
Numeric temperature or zero rain does not establish a clear/partly cloudy sky.
The positive station-rain fallback is a precipitation-interval estimate, not a
separate cloud observation. Daily HGT 12/20 remains explicitly a forecast.

## Warnings and safety-dependent consumers

Only a valid, successfully decoded response without warnings means no warnings.
HTTP errors, exhausted retries and malformed non-empty warning lists mark the
coordinator unavailable. Existing data is retained by HA and accompanied by
`data_status: unavailable` and the unchanged `last_successful_update`; its
absence must never silently mean no danger. Unknown numeric warning types stay
visible, retaining their code. Existing English text attributes are retained
for compatibility; numeric types/levels are the automation contract.

An automation protecting an awning must check source availability and freshness
as well as the absence of relevant alerts. An unavailable warning sensor is not
permission to open. The exact reaction (block opening, notify, or close) belongs
to the house's automation policy and must be tested on the actual installation.
This PR does not modify device actions or deployed automations.

## Localisation

`translations/{en,de,fr,it}.json` supplies all UI labels. English is the fallback.
No Core-only placeholders or strings.json build step is required. Warning type,
level and feed-status labels live under native `selector` keys. The catalogue
is loaded once in an executor and exposed as `warning_labels` on warning
entities. A reusable dashboard template selects the viewing user's language;
it does not copy the dictionary into each dashboard. Provider free text is
preserved as received, without claiming it is translated.

See `examples/button-card-warnings.yaml`. Existing local dashboard translations
stay in place until a separately verified adoption of the common template.
Do not rename established entities during this change.

## Verification and remaining limits

Tests cover warning failure/recovery, invalid payloads, bounded retries,
cancellation, HA-owned sessions, stale observations, current-hour AQ data,
forecast contracts, DST and translation coverage. CI runs minimum and current
HA test environments plus Hassfest and CodeQL. Passing CI is not a live-house
acceptance test. The `quality_scale: platinum` claim inherited from upstream is
removed; no HA quality certification is asserted.

Inactive camera/SLF/hydrology placeholders remain outside the runtime platform
list. Removing them or adding new providers is a separate scoped change.
