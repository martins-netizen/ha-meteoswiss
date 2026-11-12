# Translated diagnostic names without changing identity

**Status:** Unreleased follow-up after wind-statistics PR #97. Published stable
8.3.4 is unchanged. The two optional helpers remain disabled on first creation.

The station-catalogue and cache-statistics helpers previously hard-coded English
entity and service-device names. They now use HA's native `translation_key`
mechanism, with bundled names in all four supported languages.

| Language | Station-catalogue entity | Cache entity |
|---|---|---|
| English | Weather Stations | Cache Statistics |
| German | Wetterstationen | Cache-Statistik |
| French | Stations météo | Statistiques du cache |
| Italian | Stazioni meteo | Statistiche della cache |

Their two device names use the same translated labels with the existing
`MeteoSwiss` brand prefix. The English entity/device defaults stay unchanged.
HA controls name rendering and the initial entity-ID language. This change does
not rename existing registered IDs or require a dashboard migration.

## Preserved contracts

- Unique IDs remain `meteoswiss_stations_map` and `meteoswiss_cache_stats`.
  Device identifiers remain `(meteoswiss, stations_map)` and
  `(meteoswiss, cache_stats)`. They are shared virtual services, not new stations.
- Existing entity/device registry row IDs, entity IDs and bindings stay the
  same. Personal entity/device names, icons, aliases, area assignments and
  enabled/user-disabled/integration-disabled choices are retained on reload.
- Ordinary current-weather, warnings, forecast, measured/modelled pollen and
  AQ entities are unchanged. No location/provider names are invented or renamed.
- Diagnostic state strings such as `<count> stations`, `Running` and
  `<rate>% hit rate`, numeric attributes and technical attribute keys retain
  their existing format. They are not converted to new enums or numeric states.
  Existing consumers must not start depending on a translated display name.
- There is no registry deletion, statistics operation, additional request,
  polling interval, source change, version bump or automatic enablement.

## Native HA evidence and limits

`tests/test_diagnostic_translations.py` registers real HA entities/devices for
both observation providers in DE/EN/FR/IT. It verifies HA-loaded entity/device
translations, disabled first registration with no diagnostic polling, retained
legacy IDs and personal choices, reload, and a full language-change round trip.
The existing diagnostic-default/provider/entity contracts remain active.

The test matrix covers entities with and without personal names and all three
enabled/disabled states. Personal device names remain authoritative when HA
constructs the friendly name; their prefix is not overwritten by translation.
Same entity IDs keep the ordinary history/statistic lookup identity; this
naming change neither reads nor modifies an operator's Recorder database.

This is bounded source/registry evidence, not a reported operator UI acceptance
or a completed Gold checklist. Technical compatibility strings and authoritative
multilingual place aliases retain separate reviews. The later
[service-group follow-up](SERVICE_GROUP_TRANSLATIONS.md) covers the remaining
fixed group labels; shared ownership has its separate lifecycle scope below.
See [the Gold matrix](QUALITY_SCALE.md) and [diagnostic defaults](DIAGNOSTIC_DEFAULTS.md).

The later [complete entity-name review](ENTITY_NAME_TRANSLATIONS.md) verifies
all exposed families through HA in the four languages. It distinguishes the
Gold entity-name rule from unchanged technical state/attribute contracts and
the separate task of obtaining authoritative place aliases.

The separate unreleased [lifecycle follow-up](SHARED_DIAGNOSTIC_LIFECYCLE.md)
now bounds shared ownership and handoff while retaining both entity/device
identities and personal choices. Its failure/repair, concurrency and Recorder
tests do not turn the earlier naming tests into a complete historical orphan
inventory or a claim of operator acceptance.
