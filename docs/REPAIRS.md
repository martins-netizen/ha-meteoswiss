# Correct an invalid saved forecast location

**Status:** unreleased development after 8.3.0. This notice is not part of the
published 8.3.0 package. Install only a separately announced release.

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
Its existing settings link works with the supported HA minimum **2026.8.3**;
this feature does not require a newer repair-flow API.

## Evidence

- [Repair lifecycle tests](../tests/test_forecast_repairs.py): native entry and
  settings flows, cancellation/confirmation, multiple entries, ignored notices,
  source outages, disable/reenable/removal and HA-loaded DE/EN/FR/IT text.
- [Registered weather/entity tests](../tests/test_forecast_location_routing.py):
  both current-weather sources, retained IDs and independent failure/recovery.
- [Engineering checklist](QUALITY_SCALE.md): the unreleased repair follow-up is
  distinguished from the already accepted 8.3 runtime.
