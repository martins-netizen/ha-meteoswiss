# Correct an invalid saved forecast location

**Availability:** included in published, operator-accepted
[8.3.1b1](RELEASE_8.3.1b1.md). The [stable 8.3.1 package](RELEASE_8.3.1.md)
promotes the same behaviour and is published. Stable 8.3.0 does not
include this notice; use an announced release from the intended release track.

## What the notice means

A MeteoSwiss notice under **Settings → System → Repairs** says that the saved
forecast location for the named entry cannot be read. The integration cannot
safely use that selection, so it keeps those forecasts unavailable until you
correct the setting. It does not silently substitute another forecast place.

The notice concerns the saved location data. A temporary Internet outage,
unavailable provider, old catalogue snapshot or missing individual forecast
value does not trigger it. Weather measurements, measured pollen, modelled
air quality/pollen/UV and the warning postcode keep their own settings.

## Correct it using the existing entry

1. Follow **Open MeteoSwiss settings** in the repair notice. It opens the
   MeteoSwiss integration page in your HA. Find the entry named in the notice.
2. Choose that entry's **Configure (gear)**. Keep the existing weather, pollen
   and warning choices unless you deliberately want to change them.
3. Under the forecast choice, either search for and select the intended place,
   or explicitly return to the original base coordinates.
4. Review the confirmation and save. The notice disappears when a valid
   selection, or the explicit base-coordinate reset, is saved.

The existing **Reconfigure** forecast shortcut can also correct the selection.
The [selection guide](FORECAST_LOCATION_SETUP.md) explains point search and
confirmation; [shared settings](CALENDAR_AND_LOCATION_SETTINGS.md) explains the
independent location roles.

Cancelling leaves the previous settings and notice intact. If a newly selected
point cannot be validated, the form remains open and the existing setting is
retained. A base-coordinate reset is an explicit choice, not an automatic fallback.
Keep the existing integration entry, entities and history.

## When the notice is cleared

The issue is specific to one configuration entry. A confirmed correction clears
that entry's notice; other entries retain their own notices. Ordinary reloads
preserve an unresolved issue and an ignored notice's state. Disabling the entry
hides its notice; reenabling checks the saved configuration again. Removing the
entry removes its notice, including after an unsuccessful source startup.

Home Assistant checks the saved selection again on startup. The repair notice
does not fetch a catalogue, change a location, call a device, or reset the entry.
The original tests verified its settings link on HA **2026.8.3**, the minimum
supported at the time. See the [current support policy](../DEVELOPMENT.md#supported-home-assistant-versions).

## Evidence

- [Repair lifecycle tests](../tests/test_forecast_repairs.py): native entry and
  settings flows, cancellation/confirmation, multiple entries, ignored notices,
  source outages, disable/reenable/removal and HA-loaded DE/EN/FR/IT text.
- [Registered weather/entity tests](../tests/test_forecast_location_routing.py):
  both current-weather sources, retained IDs and independent failure/recovery.
- [Engineering checklist](QUALITY_SCALE.md): the accepted b1 repair follow-up
  and remaining Gold work are recorded separately.

## Wind-statistics preparation blocked (unreleased)

An entry-specific warning means Recorder's arithmetic-to-circular transition
could not be verified safely. Direction readings continue, while new statistics
stay disabled for that sensor. Existing history/statistics are retained.

Check `wind_statistics_status` and `arithmetic_statistics_archive` on the wind
sensor, then follow [the migration guide](WIND_STATISTICS_MIGRATION.md). Resolve
Recorder readiness or conflicting metadata before reloading the existing entry.
Do not delete old statistics to remove the warning. The notice clears on a
successful retry and is removed on unload. A provider outage alone is not this
repair condition. The text is bundled and HA-loaded in DE/EN/FR/IT.
