# 8.3.5b3: focused native HGT cleanup acceptance

**Protocol version:** 1.0 · **Package date:** 15 November 2026

This tests the new native confirmed deletion repair. Earlier b1 operation/wind
and b2 visible archive/Repair acceptance remain closed; do not repeat them as
new prerequisites. Publication is separate from installation and deletion.

## Normal existing-entry update

Keep an existing usable protected backup outside HA if a recovery point is
required. Once the explicit [8.3.5b3 release](RELEASE_8.3.5b3.md) is published,
update the existing maintained-fork installation through Marketplace normally,
including the one restart required to load an integration update. Keep entry,
entity IDs, names, settings and dashboards. No standalone script, fake state
class, registry edit or direct database operation is part of the normal upgrade.

## One clear recommended action

1. Open **Settings → System → Repairs**. The entry-specific **Remove obsolete
   HGT forecast statistics** repair lists the exact old forecast series.
   Review them and confirm **Permanently remove old HGT forecasts**. This
   deliberately deletes the complete selected statistics and metadata; ordinary
   history and current forecasts are retained. Cancelling keeps the data and
   leaves cleanup outstanding.
2. After successful completion, confirm that the cleanup repair is gone. On
   the original forecast under **Developer tools → States**, read
   `hgt_statistics_status: ready`, `forecast_statistics_archive: null` and
   `hgt_legacy_cleanup_required: false`. Do not use Set state. The current HGT
   value remains a forecast with no measurement state class.
3. In **Developer tools → Statistics**, confirm that the exact old IDs listed
   in the repair are absent. Check normal forecast operation. Existing wind
   archives/current wind and precipitation series are retained; no new broad
   inventory or unrelated deletion is requested.

If there is no cleanup repair because no attributable old statistics exist or
they were already removed, record that branch. Do not create unwanted legacy
data just to test deletion. A disabled forecast sensor can still have an
entry-specific repair; a completely disabled integration is inspected when next
enabled. Already unattributable historical orphan rows need separate inventory;
the integration cannot identify their former owner from a display name.

## Small private result

Record installed integration/Core versions, whether old data existed, whether
the native confirmation was exercised, repair gone/present, old exact IDs
absent/present, forecast ready/no archive and normal operation OK/problem.
Avoid unrelated personal names, locations, tokens or device data.

`ready` before confirmation can describe b2's safe archival boundary; it does
not mean that an archive was deleted. Absence of a notice alone is not a full
historical database audit. Native tests separately prove complete long-/short-
term cascading and preservation of unrelated control rows.

## Failed verification or recovery

A conflict or unverified operation stays visible. Do not treat a timeout or
missing answer as proof that no write happened. Close and reopen the repair to
read the actual state before another deliberate confirmation; never run a
blanket purge or SQL. A suitable backup is the recovery route for deliberately
deleted values, through a separate controlled restoration. Software downgrade
alone cannot restore rows. See [the upgrade guide](UPGRADING_8.3.5.md).

This protocol does not certify full Gold, independent security/privacy or the
separately planned measured OGD HGT importer. The known SQLite test-cleanup
diagnostic remains separate.
