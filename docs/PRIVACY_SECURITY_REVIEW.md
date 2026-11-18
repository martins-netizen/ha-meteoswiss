# Privacy, architecture and security: bounded review

**Approved source review, 18 November 2026:** signed #129 merge
`8887597ebf8567b5969ee70b8f9dd6f261603aec` closes reproduced
diagnostics-export and local state-clock gaps, aligns two optional-source
transition logs with INFO, and supplies the project's engineering assessment
of all **51 rules through Gold**. The [current security boundaries](GOLD_SECURITY_BOUNDARIES.md)
separate that code/test evidence from provider retention, HA host controls,
repository governance and independent assurance. The [quality matrix](QUALITY_SCALE.md),
[completion review](GOLD_COMPLETION_REVIEW.md) and
[evidence contract](GOLD_EVIDENCE_CONTRACT.md) define the rule-by-rule result
and its completed source checks: ten trusted head checks and nine actual-merge
checks, with fresh native evidence on HA 2026.11.0/2026.11.2. B7 prepares this
source as a package with [separate evidence](RELEASE_EVIDENCE_8.3.5b7.md).
Neither this review nor package preparation claims b7 publication/installation,
an official HA tier, penetration test or security certification. The dated
owner-authenticated inventory below remains unchanged.

The [diagnostics correction](DIAGNOSTICS_PRIVACY_BOUNDARY.md) covers the real
HTTP envelope, including stored repair metadata for unloaded entries. Typed
configuration summaries omit unknown keys and values; redundant retired-station
IDs are removed from the persistent notice while the exact cleanup confirmation
list remains. The [warning](WARNING_STATE_CLOCK.md) and
[weather forecast](WEATHER_FORECAST_STATE_CLOCK.md) clocks publish changes from
existing snapshots without provider requests. The [logging correction](OUTAGE_LOG_LEVELS.md)
retains generic, deduplicated outage/recovery messages and Core's native required
source reporting. These changes add no API host, runtime dependency, account,
credential, telemetry, SQL operation, purge or cleanup permission.

**Published b6 boundary, 17 November 2026:** the test package combines the
measured-HGT pending-write ownership and bounded precipitation corrections.
There is no additional credential, endpoint, telemetry, persistent archive or
automatic purge. [Dated source/package evidence](RELEASE_EVIDENCE_8.3.5b6.md)
keeps automated checks, publication and installed acceptance separate. Prior
b3 cleanup, b5 availability and b6 normal-operation acceptance remain closed.
Those package-specific results do not establish independent privacy/security/
architecture certification or substitute for the completed source engineering review.

**Precipitation resource boundary included in 8.3.5b6:** a bounded metadata body could
previously amplify into many duplicate historical downloads. The source and
importer now validate/deduplicate a maximum four-file canonical station plan
before CSV I/O and share one 300-second source/parser-wait deadline. Invalid
station/period inputs, direct same-host noncanonical paths, present malformed
relevant assets and non-CSV headers are rejected at their applicable boundary.
Valid earlier partial files survive later failure; cancelled/expired parser
results cannot queue a new import. The budget does not forcibly stop a worker
thread or certify every historical hour. This is a reproduced resource/accuracy
finding, not evidence of a provider compromise or production incident. There
is no new host, coordinate, credential, telemetry, dependency or persistent
archive. [Exact contract and evidence limits](PRECIPITATION_RESOURCE_BOUNDS.md).

**CI update included in b6:** the paired current HA/official test fixture advanced
to **2026.11.2**, with the **2026.11.0** minimum and all existing security,
integrity, advisory and coverage gates retained. Only those two current package
versions/hashes change; all other 136 current selections and the minimum lock
are unchanged. No integration runtime, destination, credential, telemetry or
published package changes. This maintenance does not refresh the dated owner
alert/settings inventory, provider-retention evidence or independent assurance.
[Fixture contract](../DEVELOPMENT.md#current-fixture-update).

**HGT ownership finding addressed in b6, 17 November 2026:** a source review of development
`1d34e525d2938f6e265265a1efc80571ba9c1eca` found a narrowly reproduced HGT
ownership race: queued initial imports could commit after station retirement
had incorrectly discarded provenance. The correction included in b6 serializes
retired checks with station refreshes and waits for native queued writes before
using empty metadata as absence. It retains ownership on uncertainty and adds
native Recorder regressions. No additional credentials, destinations, telemetry,
source data or persistent archive is introduced. See [the exact trigger and limits](HGT_PENDING_IMPORT_OWNERSHIP.md).
This evidence strengthens one lifecycle boundary; it is not independent
security/privacy certification or proof of a production incident.

**Reviewed source:** PR #115 introduced official measured HGT and is preserved
in the published [b4 package](RELEASE_EVIDENCE_8.3.5b4.md). The later approved
#119 merge `6873c0390cb276dc6afa2c347d055e995d7bf956` adds bounded native recovery;
all ten head and nine actual merge checks passed, both HA suites have 3,101
passing tests plus 83 subtests, and the complete audit still covers 140 package
versions. B5 packages that reviewed source. Publication is independently
verified and the operator reported the observed-day entry available on b5;
that bounded availability acceptance is closed. These engineering/operator
checks are not a complete historical-data audit or independent certification.

**8.3.5b5 measured-HGT recovery:** bounded retries change failure cadence,
not credentials, destinations, source validation, native statistics ownership
or cleanup consent. Core owns the timer; unload and disabled polling prevent
retries. Existing localised error categories keep provider exception text out
of normal errors. This does not establish the cause of an earlier failure or
complete independent security assurance. See [scope](HGT_RETRY_RECOVERY.md).

**Published b4 measured-HGT review, 15 November 2026:** official station CSVs add
no new coordinates, credentials, account or maintainer telemetry. Providers
receive the public station identity and source IP. Exact canonical HTTPS assets,
ETag revalidation, bounded compressed/decoded reads, off-loop CSV parsing,
completed UTC periods and a conservative 1,000 degree-days per day ceiling
protect the new boundary. Each file is limited to 16 MiB and 100,000 rows.
A shared manager serializes each station's native Recorder import and deletion;
all three products and metadata snapshots are checked before writes, and every
result is read back after native completion. Owner storage contains station
codes only, never observations or a second archive. Unknown/lost ownership or
changed units/source/mean semantics block mutation. Full HA backups must keep
Recorder and ownership storage together. Retired station deletion requires the
listed-target repair confirmation; confirmed final integration removal deletes
its owned public OGD projections. Failed final cleanup leaves a non-fixable
notice instead of a generic confirmation that could falsely imply deletion.
See [retention and recovery limits](HGT_OGD_PLAN.md#ownership-and-complete-removal).
This is source/native-test evidence, not independent security certification.

**HGT cleanup in the 8.3.5b3 test package:** an entry-owned post-startup
inventory discovers attributable obsolete forecast statistics across old and b2
upgrade paths, including disabled sensors and native season-entity tombstones.
The native repair recommends complete deletion and requires explicit confirmation;
opening a flow never authorises a write. Ownership/metadata conflicts block the
operation. A native Recorder completion barrier and absence readback precede
Core repair recomputation and an entry-scoped forecast-attribute refresh. No
replacement archive, SQL or device call is introduced. Existing archives are
transitional until confirmed removal, not the normal final state. See
[the upgrade contract](UPGRADING_8.3.5.md) and [native tests](../tests/test_hgt_cleanup.py).
This changes the b3 policy beyond b2; historical b2 evidence below remains
scoped to its published archive-and-keep runtime. It is not full Gold certification.


## Dated review and release record

The following table and repository inventory retain the **11 November 2026**
review scope and base `11ef5eaf7cb93d28f1039216b05670750ad6de6a`.
Publication/readback notes were updated on 15 November and later release
boundaries are labelled individually. Historical gaps describe those snapshots;
the current rule assessment is linked above. No fresh owner-only inventory or
credential-management evidence is inferred from subsequent code tests.

This source/configuration review is not an independent penetration test,
regulatory certification or assurance that every deployment is secure.

| Area | Verified strengths | Remaining boundary |
|---|---|---|
| Privacy | No integration account/credential, analytics SDK or separate maintainer telemetry in the reviewed runtime. Location fields and saved forecast selections are redacted from diagnostics; raw payloads, cache keys and expected private error URLs are omitted. | Providers still receive station/postcode/coordinates and the public source IP. Retention is outside this integration's control. Ordinary state attributes, HA-wide debug logs and user-supplied cards need separate sharing review. |
| Architecture | Typed entry-owned runtime, borrowed HA session, source/coordinator separation, bounded parsing and independent optional-source failures; native lifecycle tests. | Strict typing and a separately distributed client-library boundary are not fully established. Large coordinator/sensor/config-flow modules retain maintenance costs. The published b1 typed shared-diagnostic lifecycle bounds ownership/handoff; ambiguous legacy groups still need review. Coverage is evidence, not architecture certification. |
| Security | Fixed-host HTTPS/TLS, no redirects, wire/decompression limits, bounded timeouts/retries and cancellation tests. Hash-locked minimum/current fixtures, explicit Python/pip/certifi/uv floors, offline uv, pinned actions, least-privilege workflows and actual-merge verification. Exact PyPI vulnerability metadata checks returned no active advisories for either 138-pin test lock. | The owner-authenticated 11 November inventory below closes the previously inaccessible alert/settings check. This is a point-in-time inventory, not complete security clearance or an independent offensive assessment. Required approving reviews are zero; SonarCloud is checked in the project workflow but is not a ruleset-required check. |

An unqualified "top-level in every respect" statement would exceed this dated
evidence. The [quality matrix](QUALITY_SCALE.md) records the current engineering
assessment; custom integrations have no official quality tier.


## 8.3.5b3: published and focused cleanup accepted

[8.3.5b3](RELEASE_EVIDENCE_8.3.5b3.md), release **446112927**, was published on
**15 November 2026 at 14:19:50 UTC** from regular PR #113, merge
`b6c4502e5cdeb48121be628fdb7eda579df4f7c3`, exact tree
`bb8c9de9a3822d56eac6f49892852d3cede298df`. Ten head and nine actual merge
checks passed. Each native HA job passed 2,900 tests + 83 subtests and every
strict step; both hosted jobs had six warnings including the known SQLite one.
The immutable release/tag/English body and all eighteen older release records,
bodies and tags were independently confirmed. Stable **8.3.4** stays latest.
The 46 non-version component files out of 48 match accepted PR #112 source.

The operator confirmed the existing-entry update and focused native HGT cleanup
successful on 15 November: repair/listed old IDs gone, forecast ready with no
archive reference, cleanup-required false and normal operation retained. This
closes that agreed operator acceptance, without an independent whole-database
orphan-row audit. Do not repeat publication, installation or deletion; earlier
b1/b2 scopes also remain closed. See [upgrade guidance](UPGRADING_8.3.5.md).

PR #114 [test Recorder lifecycle](TEST_RECORDER_LIFECYCLE.md) is merged and
verified: ten head and nine actual merge checks passed; both HA jobs passed
2,901 tests plus 83 subtests without SQLite ResourceWarning. It changed no
component, version, workflow or lock. It requires no production update.

Measured OGD HGT is absent from published b3. Its later b4/b5/b6 source,
publication and acceptance boundaries are recorded above and in the
[measured-HGT contract](HGT_OGD_PLAN.md). The b3 snapshot did not establish
Gold engineering completion, independent review or later stable promotion.

## 8.3.5b2: fixed HGT archive test package

[8.3.5b2](RELEASE_8.3.5b2.md), release **445608354**, was published on
**14 November 2026 at 21:40:13 UTC** from packaging merge
`f8ea38babdfd44354059927888fb54fd662e5696`. It retains PR #110 runtime except
for its two version files. All 17 older tags/release bodies and stable 8.3.4
were independently confirmed. Publication is complete; its publisher is not a
new update action. The operator's visible HGT check is also closed: `ready`,
archive assignment and current forecast were shown, and disappearance of the
original live-HGT Core repair was explicitly confirmed. This is not a full
historical database or 46-file installation audit.

B2's archive-and-keep behaviour remains its immutable historical boundary.
The [b3 cleanup](UPGRADING_8.3.5.md) instead recommends explicit full removal of
obsolete forecasts. B3 publication and its focused native deletion acceptance
are now closed; earlier b1/wind and b2 visible acceptance also stay closed.


## Data flow and provider retention

The [source/request table](API_SOURCES.md) is the data-flow inventory. A selected
weather-forecast point does not move the modelled pollen/AQ/UV location:
MeteoSwiss-source entries retain HA home coordinates for those families;
alternative-source entries use their configured base coordinates. Warning
postcode and measured-pollen station are independent. HTTPS protects transport,
but the receiving provider can see query parameters.

At the 11 November review, Open-Meteo's
[API privacy notice](https://open-meteo.com/en/terms#privacy) stated that technical
logs can include IP addresses and geographical coordinates and are deleted
after 90 days. This records the provider's statement at that review, without a
new retention audit or a guarantee by this fork. Other providers have their own
policies. No precision reduction or source selection is silently applied.

## Repository evidence and limits

On the review date, active `Protect development` rules require PR/squash merges,
linear history, resolved conversations, an up-to-date branch, `Analyze Python`,
`tests` and `HACS validation`. The aggregate `tests` gate requires both HA jobs
and Hassfest. No bypass actors were listed; approving-review count is zero.
Upstream `main` is separately protected against deletion/non-fast-forward.

A SHA-256-verified Gitleaks **8.30.1** binary scanned a fresh mirror with
`--all`: **402 scanned commits**, **423 reachable commits**, **132 refs**.
Three generic-key matches were inspected and verified as public translation
keys, not credentials. No credential finding was confirmed in that scan.
A separate bounded text/commit-metadata check found no supplied private-profile
email, local-user marker or `/Users/` path. Unknown secret formats, unreachable
objects, external forks, release binaries, issue attachments, CI artifacts and
HA installations are outside that result. It is not a perpetual absence guarantee.

That review added Git exclusions for common local credentials/private keys.
Ignore rules do not protect already tracked files and do not replace scanning.
Review the actual diff/artifact before publication; report a suspected secret
or vulnerability [privately](../SECURITY.md).

A point-in-time query of PyPI's published vulnerability metadata checked all
**138 pins in each test lock**, **140 distinct package/version pairs** across
the two: **zero active advisories and zero unknown responses**, without an
ignore list. Withdrawn advisories are excluded. This checks known published
advisories, not malicious packages, unknown vulnerabilities, OS/container/action
dependencies or an operator's installed environment. It does not substitute for
the owner-only GitHub alert inventory or a recurring gate.

## Owner-authenticated alert inventory

The owner supplied a filtered, read-only GitHub report at **11 November 2026,
07:05:03 UTC**. All query groups succeeded; reported counts match their arrays.
This updates the earlier review connection's unknown alert state.

| Check | Reported result |
|---|---|
| Dependabot open | 0 |
| Dependabot closed | 67; all `fixed`, with `fixed_at` set and no dismissal reason |
| Code-scanning open | 0 |
| Secret-scanning open | 0 |
| Secret scanning / push protection | Enabled |
| Automatic security updates | Enabled, not paused |
| Additional non-provider patterns / validity checks | Disabled |

The 67 fixes were recorded on 10 November between 22:19:39 and 22:19:46 UTC.
No alert was manually dismissed by this review. No secret values or raw error
payloads were included in the supplied report. Optional scanning features were
not enabled by this read-only assessment. A clean inventory at that date does not
prove the absence of unknown vulnerabilities, unrecognised secret formats or
exposure in every external artifact; the other scope limits above remain.

## Continuing operational and governance checks

1. Review making SonarCloud required and retain the accepted dependency-update
   workflow. The published b1 [whole-lock gate](DEPENDENCY_ADVISORIES.md) now has
   bounded source/live evidence. PR #107's initial advisory/HA jobs passed, but
   its initial SonarCloud security gate failed. All corrected-head/actual-merge
   checks now pass; manual audit run 43389137603 also passed on the reviewed
   merge. Actual cron execution and failure-notification delivery remain separate.
   Fixed floors and this feed do not detect every future vulnerability.
2. Review future migrations and sensitive changes on their own evidence.
   The prepared rule index covers the existing translation and fixed-service
   lifecycle contracts; it does not require a production orphan inventory or
   a fresh four-language visual exercise. Closed release/operator checks above
   remain closed. Independent assurance remains a separate undertaking.
3. Retain dated owner-authenticated inventories as the repository changes.
   Future inaccessible APIs remain unknown, not empty alert lists.
4. Verify HA account/network/backup controls separately. This repository review
   does not prove MFA, firewall rules, external exposure or restoration on a host.

## 8.3.5 test-line shared-diagnostic lifecycle scope

The [lifecycle follow-up](SHARED_DIAGNOSTIC_LIFECYCLE.md) explicitly retains the two
shared helper identities across entry departure and startup order, with native
registry operations and no peer-coordinator reload. It adds no provider endpoint,
credential, telemetry or permissions. Ambiguous ownership and failed transfers
raise a local translated repair; exception messages are not exported. Tests cover
retained user choices, cancellation/shutdown, rollback and disposable Recorder
history. Historical conflicts, operator acceptance and independent review remain
separate. The dated security inventory above is not refreshed by these tests.

## 8.3.5 test-line manual device-removal scope

The [bounded approval policy](DEVICE_REMOVAL.md) classifies native registry
records locally. It adds no provider requests, telemetry, location export,
credentials or integration permissions. Only HA's user-confirmed removal of an
unambiguous empty retired service shell is allowed; active/shared/disabled
groups, entity bindings and device relationships stay protected. No automatic
cleanup or Recorder deletion is introduced. The source-history review is not a
production inventory; native UI/Recorder tests do not establish independent
security clearance, operator acceptance or completed Gold.

## 8.3.5 test-line service-group naming scope

The [native naming follow-up](SERVICE_GROUP_TRANSLATIONS.md) changes only local
default labels. Station/postcode placeholders preserve text already present in
the previous names; providers, requests, credentials and permissions do not
change. Native tests verify that integration diagnostics still redact saved
locations and do not export device translation placeholders. Personal registry
choices and historical rows remain intact. This does not refresh the dated
security inventory or establish operator acceptance, independent review or Gold.

## Complete entity-name evidence

The [name-inventory follow-up](ENTITY_NAME_TRANSLATIONS.md) adds tests and
documentation only. It checks every exposed name and retained registry choice
through HA's native DE/EN/FR/IT rendering, including both weather entities'
device-name inheritance. Component files, translations, requests, dependencies,
CI permissions, diagnostics and migrations remain unchanged. This adds no
personal-data flow or renewed security inventory. The Gold naming rule's
automated evidence is now explicit; release/operator UI acceptance and the
overall architecture/security boundaries above still apply.

## Complete test-lock advisory gate

The [CI follow-up](DEPENDENCY_ADVISORIES.md) checks all selections from both
universal locks against release-specific PyPI vulnerability metadata. Active
advisories and unknown results fail the existing required aggregate gate;
the same isolated read-only steps are scheduled daily. Only public package
names/versions and the CI runner's network address reach PyPI, possibly through
its configured proxy. No HA location, state, credential or user configuration
is read. Origin TLS stays verified; responses, retries and job time are bounded.
No raw provider/exception/proxy details enter reports. Integration sources,
dependencies, HA offline policy and workflow permissions stay unchanged.

This supplies the missing source implementation of a recurring whole-lock check.
All ten corrected-head and nine actual-merge checks passed for PR #107,
including SonarCloud without accepted issues. Manual workflow
[run 43389137603](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/43389137603)
also passed on the same reviewed merge: 140 package/version pairs, no active
advisories and no unknown results. Actual cron execution and delivery of a
failure notification have not been observed.
TLS certificate/hostname validation is explicit; the checker emits JSON without
accepting a report path or writing files. A live known-result inventory
is dated evidence and does not refresh the owner-only GitHub alert/settings
inventory or establish an independent security clearance or completed Gold.

<a id="prepared-835b1-acceptance-boundary"></a>

## Published 8.3.5b1 acceptance boundary

The [test candidate](RELEASE_8.3.5b1.md) packages the reviewed source with only
two component-version changes; all 42 non-version files remain identical.
[Publication is verified](RELEASE_EVIDENCE_8.3.5b1.md), including a matching
second invocation with no write attempt. The operator reported successful b1
production installation and visual inspection on 13 November. A bounded
read-only report on 14 November matched all 44 tagged files and observed old
arithmetic wind data plus new circular points; its isolated HGT legacy Repair
was a b1 issue later addressed by the published b3 follow-up. This has no pre-update
DB baseline and does not prove every historical row was retained. Its
[focused acceptance plan](ACCEPTANCE_8.3.5b1.md) separates actual wind-history
preservation, translated defaults and ordinary operation from automatic/native
test evidence. That b1 snapshot left historical stale-device inventory, rule
applicability and independent security/architecture review open. The prepared
rule assessment now supplies applicability and native lifecycle evidence;
it does not infer a production inventory or independent assurance. No operator DB read,
device command, installation, cleanup or new security guarantee follows from
publication. A software rollback alone does not reverse Recorder metadata.

## Published b2 HGT archive boundary

The published b2 runtime preserves compatible old
forecast statistics under a distinct archive ID before native Core repair
recomputation. The shared archive boundary verifies the same metadata PK and
all metadata fields; native tests compare every long-/short-term row field.
Existing live IDs, registry choices, wind archive IDs and raw-history identities
remain unchanged. No fake archive entity, direct SQL, deletion, re-import,
measurement-class workaround or issue suppression is introduced. Genuine
conflicts remain visible, unrelated valid Core repairs survive recomputation,
and startup/timeout/unload/retry boundaries are covered. This local/native
evidence is not a new operator migration, an independent security/architecture
assessment or completion of the remaining Gold rules.
