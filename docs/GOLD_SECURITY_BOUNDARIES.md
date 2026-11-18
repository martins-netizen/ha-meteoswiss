# Gold engineering and security boundaries

**Prepared review, 17 November 2026.** The post-b6 work supplies the project's
engineering assessment of all 51 rules through Gold: 20 Bronze, ten Silver and
21 Gold. The [quality matrix](QUALITY_SCALE.md),
[completion review](GOLD_COMPLETION_REVIEW.md) and
[evidence contract](GOLD_EVIDENCE_CONTRACT.md) record applicability, source,
documentation and native regression evidence. Completion is gated on the
integrated source and its required checks. It is not an official Home Assistant
tier award, independent penetration test or security certification.

## Corrections after published b6

| Boundary | Prepared correction and evidence |
|---|---|
| Downloadable diagnostics | Typed configuration summaries omit unknown keys and values, including nested data; the declared legacy pollen-location key is redacted. Native HTTP tests include HA's outer same-domain issue envelope. Redundant station IDs are omitted from new retired-HGT notices and cleared from that exact persisted notice before diagnostics registration. Creation/dismissal metadata, other notices and the exact repair confirmation list remain. See [diagnostics privacy](DIAGNOSTICS_PRIVACY_BOUNDARY.md). |
| Warning validity | Registered warning states change at the validity boundaries already present in the retained snapshot. Each entity owns and cancels its local callback; queued obsolete callbacks cannot rearm after removal. These changes make no source request. See [warning clock](WARNING_STATE_CLOCK.md). |
| Forecast hour and age | Weather state and forecast subscribers follow the retained model hour and existing snapshot age limit. Native lifecycle tests cover expiry, recovery, overlap and unload without extra source calls. See [forecast clock](WEATHER_FORECAST_STATE_CLOCK.md). |
| Optional-source logging | Handwritten UV and station-catalogue outage/recovery transitions use generic, deduplicated INFO messages. Supported Core versions retain their native reporting for required coordinator failures. See [log levels](OUTAGE_LOG_LEVELS.md). |

The diagnostics startup update uses HA's public issue registry API. It does not
reload that registry, inspect Recorder or load HGT ownership. A cold disabled-only
domain has no diagnostics handler; component setup clears the known notice
before that handler is registered. This is a tested lifecycle boundary, not a
global filter for arbitrary issue-registry changes after startup.

## Retained runtime boundaries

The [source inventory](API_SOURCES.md) remains authoritative for destinations and
location purposes. The follow-ups add no API host, provider request, runtime
dependency, integration account, credential or maintainer telemetry. Shared HTTP
handling retains verified HTTPS, fixed hosts, disabled redirects, bounded
wire/decoded responses, timeouts and cancellation. Providers still receive the
selected public station, postcode or coordinates needed for each source and the
request's source IP.

No follow-up adds SQL, a purge, an archive or a wider cleanup permission.
[HGT ownership](HGT_OGD_PLAN.md#ownership-and-complete-removal), native Recorder
completion checks and listed-target consent retain their existing contracts.
Full HA backups must retain Recorder and ownership storage together. The
four-file/300-second [precipitation budget](PRECIPITATION_RESOURCE_BOUNDS.md)
does not certify every historical hour or forcibly stop an already running
parser thread.

The [fixed-service topology](FIXED_SERVICE_TOPOLOGY.md) and native metadata tests
supply evidence for the configured virtual groups and supported entities.
They do not invent a discoverable appliance inventory. Completing that rule
assessment requires neither a production orphan hunt nor destructive station
changes. Existing native four-language evidence does not imply a fresh manual
review in every language. Platinum-specific requirements are a separate scope.

## Evidence that remains separate

| Question | Authority and limit |
|---|---|
| Does this source meet the assessed rules? | The rule index and checks bind evidence to the integrated source. Automated results support behavior; documented applicability and human review still require judgment. A passing rule checker cannot award a tier or certify security. |
| What is installed and accepted? | Release/tag evidence establishes a package. An operator report establishes only its stated check. Accepted b3 cleanup, b5 availability and b6 normal operation remain closed; these prepared changes do not imply another installation, database audit or failure injection. |
| What do providers retain? | Provider policies and independent provider evidence govern server-side retention. This repository cannot audit their logs or enforce deletion. The [dated privacy review](PRIVACY_SECURITY_REVIEW.md#data-flow-and-provider-retention) retains the earlier provider statement without refreshing it. |
| Is an HA deployment protected? | HA account access, host/network exposure, debug-log sharing, backup security and restoration require deployment-specific evidence. Repository tests do not establish those controls. Ordinary state attributes and user cards retain their own sharing boundary. |
| Are repository controls current? | The [owner inventory](PRIVACY_SECURITY_REVIEW.md#owner-authenticated-alert-inventory) remains dated 11 November 2026. Code tests and dependency-feed results do not refresh owner-only alert/settings evidence, credential-management evidence or future governance decisions. Unknown API results remain unknown. |
| Has independent assurance been completed? | No independent offensive assessment, regulatory certification or universal privacy/architecture clearance is claimed. Sensitive future changes need their own review; suspected vulnerabilities should be [reported privately](../SECURITY.md). |

These operational and assurance boundaries are not missing runtime features to
be simulated through another migration, cleanup or manual language exercise.
The dated [privacy/security record](PRIVACY_SECURITY_REVIEW.md) preserves the
historical findings and release metrics separately from this prepared assessment.
