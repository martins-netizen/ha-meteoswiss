# 8.3.5b2: focused HGT archive acceptance

**Protocol version:** 1.0 · **Prepared:** 14 November 2026

The new scope is the automatic HGT archive and removal of its resolved Core
Repair. B1 installation/visual operation and the bounded wind/archive readback
are already accepted; do not repeat those older scopes as new prerequisites.
This protocol records no b2 installation or production migration yet.

## Normal update and recommended default

Keep a protected, usable before-update backup and the existing entry. For an
existing historical migration, use the agreed test/restored-copy boundary;
creating/restoring a copy is a separate operator action. Once the fixed
[8.3.5b2 package](RELEASE_8.3.5b2.md) is actually published and installation is
authorised, select it in the existing maintained-fork Marketplace entry,
download it and restart HA once. Retain names, settings, entity IDs and charts.
Do not recreate the entry, add a fake measurement class or click Delete in the
old statistics dialog. The default archives compatible old data automatically.

## Three focused checks

1. On the original HGT forecast, read `hgt_statistics_status` and
   `forecast_statistics_archive` in Developer tools → States. Expect `ready`;
   an archive ID is present if compatible old HGT statistics existed. Read only;
   do not use Set state. The forecast remains without a state class.
2. Confirm that the original live-HGT "entity no longer has a state class"
   Repair is gone. Compare older HGT samples/ranges under the exact archive ID
   and confirm the live forecast/ordinary history continue. Existing wind
   archive IDs and circular statistics must remain unchanged. An archive's
   no-live-entity entry in the advanced Statistics catalogue is a separate fact.
3. Report installed integration/Core versions, HGT status/archive, Repair
   gone/present and forecast/history OK/problem. Keep the report private and
   omit unrelated names, locations, credentials and device data.

The existing 14 November b1 readback is a before-fix baseline, with 90-day
hourly and 48-hour short-term windows. Compare overlapping timestamps/values;
natural retention and time passing make total counts alone insufficient to
prove loss or preservation. Native tests separately compare every row field.
If there was no earlier HGT series, record that historical migration was not
exercised rather than inventing data or a new soak window.

## Conflict or recovery

`pending` means preparation has not completed. `blocked` plus a MeteoSwiss
Repair means verification failed; retain both series and collect a bounded
diagnostic report. Do not delete, overwrite, manually rename IDs or execute SQL
to hide the conflict. Software rollback alone does not reverse metadata.
Controlled reverse migration/restoration requires a separately approved usable
backup. See [the full upgrade guide](UPGRADING_8.3.5.md).

These checks do not request a fresh four-language audit, forced provider outage,
peer/device deletion, full-history inventory or independent security review.
Remaining Gold work and external assurance keep their own scope.
