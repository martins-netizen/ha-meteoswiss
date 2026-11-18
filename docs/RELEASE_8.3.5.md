# MeteoSwiss 8.3.5

**Notes version:** 1.0 · **Planned stable scope:** 18 November 2026

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss product.

This release marks an important milestone for the project. It adds official measured heating degree days, improves diagnostic privacy and completes our engineering assessment against all 51 Home Assistant quality rules through Gold. Seven beta releases and extensive testing in Home Assistant have helped shape this release.

The changes below are the planned cumulative scope from **stable 8.3.4**.
Before stable packaging, a corrective source change places the ninth HGT
coordinator definition in the canonical module and fixes calculated forecast
HGT's registered-state rollover at Swiss midnight. Its other data contracts
and the completed bounded operator sight report remain. The stable package
must be based on that correction's separately approved actual source merge;
this draft is not an installable stable package or a publication claim. Use the [release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases)
for availability; these notes do not publish or install a package. The
preceding stable package is **8.3.4**; current stable selection follows the
catalogue. Older releases and their original notes remain immutable.

## What improves for existing users

- **Official measured heating degree days:** SwissMetNet OGD supplies HGT 12/20
  daily, monthly and annual products. A separate last-observed-day sensor appears
  on the measurement-station device. Initial available history is backfilled,
  new observations continue to arrive and source corrections are rechecked.
  Forecast HGT remains a distinct prediction. HGT is a climatic index derived
  from station temperatures, not a measurement of a building's energy use.
- **A clear route out of obsolete forecast statistics:** the recommended native
  repair removes attributable old HGT forecast statistics after one explicit
  confirmation. Current forecasts and ordinary retained history continue. A
  completed cleanup leaves no unused replacement HGT archive.
- **Correct wind-direction averages:** HA's circular angle statistics handle
  north-crossing directions correctly. Older arithmetic means are preserved
  under a separate archive ID; the retained sensor starts its circular series.
  Those older averages cannot be converted into correct circular observations.
- **More private diagnostics:** typed saved-configuration summaries omit unknown
  settings and redact location fields. Native tests include HA's outer repair-
  issue envelope. Redundant station IDs are removed from the exact retired-HGT
  notice; its cleanup form still lists the exact confirmation targets.
- **Weather displays follow time changes:** local callbacks publish warning
  validity and forecast model-hour/snapshot-expiry changes between provider
  polls. They use retained data and make no additional request themselves.
  Calculated HGT also publishes the new Swiss day's value and daily mean at
  midnight, fixing yesterday's registered value remaining until the next poll.
  Removal, failure and already queued callbacks retain cancellation safeguards.
- **Clearer names and dependable lifecycle behavior:** default entity and service
  labels resolve in DE/EN/FR/IT while personal registry choices and retained IDs
  survive reloads. Shared diagnostics hand over ownership without reloading a
  peer weather entry. Manual device removal permits only an unambiguous retired
  empty shell. Provider locality aliases remain a separate naming boundary.
- **Bounded recovery and imports:** temporary measured-HGT source/Recorder
  failures retry after 60 seconds with bounded backoff to 15 minutes, returning
  to six-hour polling after verification. Pending-import ownership survives
  cancellation races. Hourly precipitation imports validate/deduplicate at most
  four canonical CSVs within one 300-second awaited-work budget, retaining valid
  partial files and real zero. The lookback is not a retention purge.
- **Engineering evidence through Gold:** after the separately reviewed
  canonical coordinator correction, the planned stable assessment covers
  20 Bronze, 10 Silver and 21 Gold rules: 26 automated verifications, 16
  documented review judgments and nine reasoned exemptions. Fresh native
  JUnit/coverage checks, service-lifecycle and complete entity-metadata
  inventories retain every existing security and strict coverage gate.

The [quality matrix](QUALITY_SCALE.md),
[canonical correction](COORDINATOR_CANONICAL_COMPLETION.md),
[security boundaries](GOLD_SECURITY_BOUNDARIES.md) and [source contracts](API_SOURCES.md)
provide precise evidence. The completed b7 checklist report did not detect the
ninth coordinator-placement gap; this stable work corrects that implementation
boundary before claiming closure. This is the
project's engineering assessment, without an official Home Assistant tier or
independent privacy/security certification. Optional UV/catalogue outage and
recovery messages use generic INFO text once per transition; supported Core
versions keep their native reporting for required coordinator failures.

## Home Assistant baseline

**Home Assistant Core 2026.11.0 or newer is required.** Older Core releases pin
libraries affected by published vulnerabilities. This maintained baseline is
therefore part of the support policy, rather than a claim that raising the
minimum permanently clears every security risk. Keep Core updated. Current
compatibility is checked on **2026.11.2**, alongside the 2026.11.0 minimum.
See the [Core security rationale](../DEVELOPMENT.md#supported-home-assistant-versions).

## Upgrade the existing entry

Update directly from a supported earlier release to published **8.3.5** through
**Settings → Marketplace**. Keep the existing configured entry, station and
options; intermediate betas and entry recreation are unnecessary. Complete the
ordinary update restart once. Review the [upgrade guide](UPGRADING_8.3.5.md)
and the [focused normal-update guide](ACCEPTANCE_8.3.5.md).

If already running the accepted **8.3.5b7** runtime, the planned coordinator
placement and calculated-HGT midnight corrections receive their own source/
native checks before promotion. The new callback changes state-publication
timing; it does not require a migration or repeat the earlier bounded sight
acceptance. No repeated failure test or operator observation window is imposed. If choosing the stable
label when published, use the normal package update and its ordinary restart.

### Obsolete HGT forecasts: the recommended cleanup

For users whose old forecasts are still attributable, open **Settings → System
→ Repairs → Remove obsolete HGT forecast statistics**. Review the exact IDs and
confirm **Permanently remove old HGT forecasts**. Opening or cancelling deletes
nothing. Confirmation permanently removes all selected long-/short-term rows
and metadata without a date-window cutoff; readback verifies absence and Core
recomputes the corresponding statistics repairs. No replacement HGT archive is
kept. This is the recommended default for those obsolete predictions.

The repair covers earlier direct upgrades, b2 archives, attributable retired
season-HGT identities and disabled forecast sensors. It does not guess ownership
of already orphaned histories or erase unrelated data. The forecast-only season
entity is intentionally retired. Wind arithmetic archives, official measured
HGT and other statistics are outside this deletion. Retained wind archives have
a separate historical purpose; [chart guidance](WIND_STATISTICS_MIGRATION.md)
explains their arithmetic meaning and the expected absence of a live entity.

Keep a usable protected full backup, including Recorder and ownership storage,
when a recovery point is needed. Software downgrade alone cannot restore deleted
rows. Existing backups/copies are not erased, and logical Recorder deletion is
not secure physical erasure. Completed b3 cleanup is not repeated.

### Official measured HGT: use and removal

Measured history requires an enabled MeteoSwiss measurement-station entry and
Recorder; an Open-Meteo current entry does not invent station observations.
Missing/delayed source values remain unavailable, while supplied zero is valid.
Use each daily/monthly/annual product's own statistic ID with native Statistics
graph **change**; do not add the products together or derive observations from
forecast archives. The [HGT guide](HGT_OGD_PLAN.md) explains UTC periods, gaps,
corrections, chart semantics and retry limits.

Station changes retain owned history and can offer an explicit retired-station
repair. Configured peers, including disabled peers, protect shared products.
Deleting the final integration entry removes its owned measured-HGT products,
including retired stations; remove entries before uninstalling files if that
lifecycle cleanup is intended. Ordinary sensor history and unrelated statistics
remain. Read the [complete removal boundary](HGT_OGD_PLAN.md#ownership-and-complete-removal)
before removing an entry. No arbitrary series is adopted from its name alone.

## Privacy, resources and promotion evidence

Cumulatively from 8.3.4, measured-HGT backfill and polling add source traffic to
the existing official host. Providers still receive the selected station,
postcode or coordinates and the request's source IP. Diagnostic redaction is
not global anonymization of ordinary state attributes, cards, logs or provider
records. The source table and dated provider/owner reviews retain their scope.

The planned source corrections and stable packaging add no host,
request, runtime dependency, source account, telemetry or deletion authority
beyond b7. The placement and midnight-state corrections receive normal review;
subsequent stable packaging must retain that approved source apart from the
two version fields and preserve existing quality/security gates. [Dated evidence](RELEASE_EVIDENCE_8.3.5.md)
records the completed b7 checks, publication and bounded sight report separately
from stable packaging and authorized publication. The earlier releases and
their notes remain preserved; stable availability follows the catalogue.
