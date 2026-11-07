# 8.3.4b1: focused version, registry and source-label check

**Protocol version:** 1.1 · **Updated:** 7 November 2026

**The agreed short operation check is complete.** After verified publication,
the operator reported normal operation OK, **HA Core 2026.11.0 / HA OS 18.4**,
and that everything works. This answers the immediately preceding 8.3.4b1
check request; the reply does not separately restate the integration version
or identify the instance as production hardware or a test VM. No additional
list of names/IDs, repeat download/restart or observation window is required.

This is a bounded operator report, not an independent registry/Recorder audit,
a separate alternative-source inspection or manual proof of first-registration
defaults. Those automated paths retain their own evidence. See
[publication and acceptance evidence](RELEASE_EVIDENCE_8.3.4b1.md).
Stable 8.3.3 and earlier accepted settings, icon/error, first-install and restore
checks retain their scope.

## Original focused checklist (reference, not a repeat request)

The checklist below records the original requested scope. It is not a new
installation, registry inventory or provider-switch request. Publication was
verified before the reported operation check.

1. **Install and report the actual versions.** Prefer the existing test HA and
   entry. In Marketplace (HACS on older HA), make prereleases visible, select
   **8.3.4b1** and Download/Redownload it. Keep the existing backup and entry.
   Restart HA once and report the installed integration and HA Core versions.
2. **Inspect existing names and choices.** Normal weather/forecast/pollen entities
   should keep their IDs and personal names/icons. Existing diagnostic helpers
   retain their previous enabled/disabled choices; they must not be expected to
   disable themselves during this update. Device groups should be data services.
   If an Open-Meteo current-source entry already exists, inspect the default
   provider/model and modelled-data attribution. A personal group name can mask
   its default name. Mark the alternative source as not inspected if absent;
   do not change a production source or create/delete entries for this check.
3. **Confirm ordinary operation.** Review current values and the usual dashboards
   for new errors. Distinguish an already missing provider value from a new
   regression. No deliberate outage, pollen-station change, diagnostic toggle,
   actuator command or new observation window is needed.

Report **integration version, HA Core version, retained names/IDs/choices OK,
normal operation OK**, plus whether an existing alternative-source entry was
inspected. Screenshots are optional and should omit personal details.

Native tests already cover first-registration defaults, both sources, manual
opt-in, setup/reload preservation and Configure/Reconfigure pollen-station round
trips without entity/device deletion. This focused visual check is not an
independent Recorder/registry inventory or a historical orphan audit. If normal
operation regresses, redownload **8.3.3**, restart once and keep the entry/history;
see [scope and recovery](RELEASE_8.3.4b1.md).
