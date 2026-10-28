# Calendar-day forecasts and one location-settings dialog

**Guide version:** 1.4 · **Updated:** 27 October 2026

**Availability:** included in the **8.3.0** runtime accepted as b4.
Use the [announced release](RELEASE_8.3.0.md); earlier beta notes describe their
historical scopes, not instructions to reinstall an older beta.

**From published 8.3.2b1 (retained for prepared stable 8.3.2):** the complete settings transaction also serves
the entry menu's Reconfigure route, with the same source checks, cancellation
and concurrency protection. See [current route guidance](FORECAST_LOCATION_SETUP.md#existing-entry).
The original 8.3.0 acceptance and numerical evidence below retain their scope.

## What the corrections address

On 24 October, the existing beta correctly separated Kloten observations from
Säntis predictions, but tomorrow's high, low and rain remained unknown. The
following Swiss day, 25 October, has 25 physical hours. Open-Meteo uses a fixed
UTC offset for daily buckets throughout a response, so that 24-hour bucket
cannot represent both Swiss midnights. The integration correctly rejected its
period but did not yet produce a complete Swiss-day replacement.

The same beta's gear opened only measured-pollen settings. Forecast changes
required Reconfigure, and the weather station could not be changed there. The
new flow makes all three locations available together in Configure.

## Change any or all three locations

After installing the announced correction, open **Settings → Devices & services
→ MeteoSwiss → the existing entry's Configure gear**.

| Setting in that dialog | Purpose |
|---|---|
| Weather measuring station | Measured current temperature, wind, rain and other observations. |
| Station for measured pollen | Measured pollen concentrations; independent of the weather station. |
| Forecast location | Keep the displayed point, search by postcode/town/POI, or reset to the original base coordinates. |
| Warning postcode | Independent four-digit Swiss warning area. A postcode in forecast search does not change it. |

For example, retain **Zürich/PZH pollen**, change observations from **Kloten to
Zürich/Fluntern**, and keep the **Säntis forecast**. You can also change all three
together. With **Keep**, submitting that form applies the displayed settings.
With **Search**, continue through search, explicit result selection and the
confirmation in the same flow. The last page lists the pending weather, pollen,
forecast and warning choices. **Cancelling any unfinished step saves none of
the pending changes.** A failed source check remains retryable.

The **HA home location is a general Home Assistant setting**, independent of
MeteoSwiss/SwissMetNet and pollen measuring stations. This integration uses it
as the default base for modelled air quality, modelled pollen, optional UV and
a forecast without a separately chosen point. For the alternative Open-Meteo
current-data entry, explicitly entered base coordinates take its place; that
dialog shows latitude/longitude instead of a measuring station. An explicitly
selected ICON forecast point remains independent.

Existing entity IDs, user names, unknown saved settings and individual legacy
polling intervals are retained. A loaded entry reloads once through its existing
listener; no HA Core restart is needed just to apply a location change.
Automatically generated entry/device labels follow the new station. Personal
names are preserved, so review any name that explicitly mentions the old place.
Old technical IDs may still contain the old station name.

**History after a deliberate station change:** the retained observation
entities continue their history with readings from the newly selected station.
Earlier readings are not rewritten. The external hourly precipitation archive
is separately keyed by station: an old Kloten archive remains Kloten, and the
new station uses its own archive. An existing chart explicitly targeting the
old station archive stays on that archive until you change its target.

The config entry ID is retained. If a present config-entry unique ID represents
the old observation/postcode combination, it is updated with a deliberate
observation/postcode change to keep duplicate detection correct. Entity unique
IDs are retained. Duplicate entries and concurrent edits are rejected without
partially applying the pending settings.

In the accepted **8.3.0/8.3.1** runtime, the older **three-dot menu → Reconfigure**
path remains forecast-only. Published 8.3.2b1 makes that route use the
same complete dialog; Configure already includes forecast selection.

## Complete Swiss calendar days

Aligned native daily aggregates remain preferred. For a daily bucket with
mismatched Swiss boundaries, the source now aggregates the same ICON response's
complete local calendar day:

- The two IANA `Europe/Zurich` midnights define 23, 24 or 25 physical hours.
- Temperature samples start at the first midnight and stop before the next.
  High, low and mean use all expected hourly samples, including both repeated
  autumn hours. These are hourly-sampled predictions, not finer-resolution
  measured extrema.
- Rain and probability describe the preceding hour: exclude the first
  midnight's bucket and include the next midnight's bucket.
- Completeness is checked separately for each field. A missing, invalid or
  gapped temperature/rain/probability field remains unknown independently;
  zero and negative temperatures remain valid. No missing aligned native field
  is silently replaced by a different basis.

One existing ICON request includes **25 past hours** alongside the **120-hour
rolling forecast**. The client validates at most 145 hours and returns only the
current/future 120 hours; elapsed hours are used internally for whole-day
coverage. There is no additional coordinator, source, cache or polling schedule.
Daily scalars, HGT and the forecast weather entity share the normalized daily
result. Scalar attributes `aggregation` (`provider_daily` or
`hourly_calendar_day`) and `day_hours` identify the basis.

See the provider's [time and timezone parameters](https://open-meteo.com/en/docs)
and [MeteoSwiss model documentation](https://open-meteo.com/en/docs/meteoswiss-api).
The selected model remains `meteoswiss_icon_seamless`.

## Focused HA checks after the new package is announced

1. Keep the existing test-system backup and entry. Confirm the new installed
   version; the old b2 package does not contain these changes.
2. Open the gear and check that weather station, measured-pollen station,
   forecast action and warning postcode appear together, with retained defaults.
3. Change all three, begin a forecast search, then cancel. Reopen settings:
   every previous choice must remain.
4. Confirm a deliberate test-station change while keeping pollen and forecast;
   verify new observations, correct station/device labels, existing IDs and
   independent Säntis predictions. Then restore the intended station through
   the same dialog. Review any station-specific archive card separately.
5. Exercise a confirmed combined change and forecast reset. Retained custom
   names and individual intervals must survive; no duplicate entry should appear.
6. For an available complete clock-change day, check high, low, rain and HGT
   with their aggregation attributes. Missing source hours must remain unknown,
   not zero. Do not recreate a historical date in the live system for this test;
   deterministic regressions cover both spring and autumn transitions.

The operator's successful **HA 2026.10.3 existing-beta test** is recorded
separately from automated compatibility tests and acceptance of these new
corrections. No stable release, HACS default-catalogue admission or official
Silver/Gold tier is established by this source change alone.

## Validation of this source change

Both local environments used Python **3.14.8**:

| Home Assistant | Regression result |
|---|---|
| Minimum **2026.8.3** | **1,440 passed + 53 subtests passed** |
| Current local **2026.10.3** | **1,440 passed + 53 subtests passed** |

Both reports retain **99.97671%** combined line/branch coverage: **3,355/3,356
lines and 938/938 branches**. All existing strict module gates pass, including
100% line/branch coverage for the flow, forecast client and scalar summary.
The existing four excluded lines and the previous thresholds are unchanged.
The one uncovered constant line is unchanged. Four complete **178-key**
translations match, English equals strings.json, and Ruff checks pass for the
changed Python files. The unchanged CI matrix still covers 2026.8.3/2026.10.1;
that is distinct from the local 2026.10.3 run and the operator’s beta test.

Regressions include same-form defaults, independent/combined location changes,
retry/cancel/no-partial-write behaviour, duplicate and concurrent edits, all four
languages, forecast reset and one real HA unload/reload preserving entities and
user names while changing station readings. Calendar fixtures cover 23/25-hour
spring/autumn days, a post-transition 24-hour day still misaligned with the
response offset, complete elapsed-today coverage, both repeated autumn hours,
midnight rain attribution, independent missing fields and genuine zero values.
The operator subsequently confirmed the b3 calendar-day values and shared
station changes, followed by positive b4 acceptance. Those reports are separate
from the original local test counts above; see [readiness](RELEASE_READINESS.md).

During original correction preparation, a fresh provider request could not be verified:
the API hostname failed to resolve for both the existing request and the
history-enabled request. This is not evidence that the operator’s provider is
down. This old preparation-host limitation is not a current diagnosis of the operator connection.
