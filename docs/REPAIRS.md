# Correct an invalid saved forecast location

## 8.3.5 stable update

Stable 8.3.5 retains published b7's bounded HGT recovery, exact cleanup consent,
privacy and lifecycle behavior. Use the [catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases),
[package notes](RELEASE_8.3.5.md) and [stable guide](ACCEPTANCE_8.3.5.md).
Completed b3 cleanup and b5/b6/b7 reports stay closed. An already accepted b7
runtime needs no repeat migration, failure exercise or observation window.

**Published 8.3.5b4 measured-HGT repairs:** after a weather-station change, **Remove
unused official HGT statistics** lists the exact retired station products.
Recommended action: confirm removal if the old station is no longer wanted.
Opening/cancelling deletes nothing. Confirmation permanently deletes complete
listed external statistics and metadata; no archive is created. Active peer
entries protect shared series. Ownership or metadata conflicts produce a
non-fixable notice and block writes. Resolve the conflict or restore matching
Recorder/ownership backup; do not guess ownership from an ID prefix. The final
native removal of all MeteoSwiss entries also removes their owned OGD HGT
products. Complete station-change repairs before disabling every entry or
removing integration code, because a custom repair needs a loaded integration.
[Removal, failure and recovery details](HGT_OGD_PLAN.md#ownership-and-complete-removal).
These new repairs are separate from the accepted b3 obsolete-forecast repair.

**HGT cleanup in 8.3.5b3:** the package includes a native confirmation for
complete removal of obsolete forecast statistics. See the
[upgrade guide](UPGRADING_8.3.5.md) and [focused check](ACCEPTANCE_8.3.5b3.md).
Published b2 preserves archives; it does not contain this deletion repair.

On the development branch, if another entity is using the old statistic ID or
its deleted registry entry shows that it also used the ID of an existing
series, the repair leaves the data in place. The same check runs when you
confirm. If ownership is ambiguous, keep the series until you can identify its
origin. An unrelated deleted entity with no matching statistics requires no action.

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
  retains its recorded scope. The current matrix records the completed
  canonical-coordinator correction in approved #131 with its own evidence.

<a id="wind-statistics-preparation-blocked-unreleased"></a>

## Wind-statistics preparation blocked (8.3.5b1 test line)

An entry-specific warning means Recorder's arithmetic-to-circular transition
could not be verified safely. Direction readings continue, while new statistics
stay disabled for that sensor. Existing history/statistics are retained.

Check `wind_statistics_status` and `arithmetic_statistics_archive` on the wind
sensor, then follow [the migration guide](WIND_STATISTICS_MIGRATION.md). Resolve
Recorder readiness or conflicting metadata before reloading the existing entry.
Do not delete old statistics to remove the warning. The notice clears on a
successful retry and is removed on unload. A provider outage alone is not this
repair condition. The text is bundled and HA-loaded in DE/EN/FR/IT.

## Remove obsolete HGT forecast statistics (8.3.5b3)

Entry-owned inspection runs after registration, including disabled sensors and
attributable retired season identities. The fixable notice lists exact old
statistic IDs. **Recommended: permanently remove the old forecasts.** Opening
or cancelling the dialog performs no deletion. Explicit confirmation clears
complete series through native Recorder, verifies absence, recomputes Core
issues and refreshes the forecast's archive attribute. No replacement archive
or permanent preservation option is created by this repair.

When ownership, metadata, Recorder readiness or forecast customisation is
incompatible, a separate non-fixable diagnostic notice blocks deletion. Resolve
the conflict and reload the entry. Unrelated IDs are never inferred from names
or a broad prefix. See [upgrade paths and limits](UPGRADING_8.3.5.md).

The existing b2 archival conflict notice can coexist with this cleanup repair
when both compatible old source and destination metadata exist. A verified
explicit cleanup resolves that historical conflict without overwriting either
series. Wind migration conflicts remain a separate issue and deletion scope.

**In development.** Before archiving daily HGT forecasts, the integration checks
the current registry owner and retained records for both names. A known prior
owner of the source statistics or a claim on the destination pauses archival.
This also applies when another entity claimed and then released the archive
name before it had statistics. If a claim appears after a rename was queued,
the archive can already exist. Reload the entry after resolving the conflict
to check the stored series again.
