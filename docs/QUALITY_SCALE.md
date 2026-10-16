# Quality roadmap and evidence

This is a self-assessment against the current
[Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/).
It is not an official HA rating, HACS certification or release approval. HACS
installability/default listing is a separate assessment. The manifest deliberately
contains no `quality_scale` claim. Live acceptance and a tested fork release
remain separate gates after code review and CI.

## First-stage Bronze assessment

| Rule | Evidence / applicability |
|---|---|
| `action-setup` | Exempt: no integration-specific actions are registered. |
| `appropriate-polling` | Coordinators own bounded provider intervals; minimum observation interval 600 seconds. |
| `brands` | Existing `meteoswiss` assets in [HA brands](https://github.com/home-assistant/brands/tree/master/custom_integrations/meteoswiss); domain retained. |
| `common-modules` | Shared constants, time contract and entity descriptions are centralized. |
| `config-flow-test-coverage` | 100% lines and branches in `config_flow.py`, including options, errors/recovery and legacy/current duplicates; CI enforces it. |
| `config-flow` | Native user/options flow; no YAML setup. |
| `dependency-transparency` | README/usage describe public third-party services, networking, locations and the account-free setup. |
| `docs-actions`, `docs-triggers`, `docs-conditions` | Usage describes standard HA entity automation/forecast functions and the absence of custom actions/device automation extensions. |
| `docs-high-level-description` | README lists data families, scope and fork provenance. |
| `docs-installation-instructions` | README + usage document prerequisites, approved installation route and setup. Actual first HACS release remains pending. |
| `docs-removal-instructions` | Usage documents entry/component removal and effects on consumers/history. |
| `entity-event-setup` | CoordinatorEntity manages observations and forecast pollen; weather forecast subscription belongs to entity add/remove lifecycle. Tests verify pollen listeners are removed on unload. |
| `entity-unique-id` | Existing entry-based and shared diagnostic IDs retained; reload test checks registry mapping stability. |
| `has-entity-name` | Enabled on active entities, including the main weather entity with its device name. |
| `runtime-data` | Typed `MeteoSwissConfigEntry` and dataclass; shared diagnostic ownership flags alone remain domain-global. |
| `test-before-configure` | Both providers validate the observation coordinator before saving, within a 30-second total timeout. |
| `test-before-setup` | Required observation first refresh precedes platform setup; optional families refresh separately. |
| `unique-config-entry` | Source/location/postcode guards cover old entries without unique IDs and HA unique-ID checks. |

These are code/documentation findings to be confirmed in PR checks and the live
acceptance of the reviewed commit. They do not mark the existing installed
snapshot as having acquired these changes.

## Silver gaps and next implementation order

| Rule | Current assessment / next action |
|---|---|
| `action-exceptions` | Exempt: no integration-specific service actions. |
| `config-entry-unloading` | Native unload/reload; tests verify HA session ownership, replaced runtime state, stable entity IDs and removed observation/forecast listeners. |
| `docs-configuration-parameters`, `docs-installation-parameters` | Usage includes provider selection, intervals, coordinates, warning postcode and measured pollen station. |
| `entity-unavailable` | Observations/warnings and both pollen/AQ clients have failure/recovery tests, including registered pollen/AQ entity states. All-empty current pollen/AQ payloads fail; partial responses retain unknown fields. Measured pollen rejects age over four hours or future skew over ten minutes on refresh. Both weather forecast services return empty lists on forecast failure and recover, while valid observations remain available. Remaining optional per-entity paths still require review; full rule remains pending. |
| `integration-owner` | `@martins-netizen` in manifest. Repository Issues are currently disabled: enable a usable fork-specific support route before public release. |
| `log-when-unavailable` | Pollen/AQ, measured pollen and the ICON forecast client use coordinator transition logs. Forecast failures suppress raw coordinate URLs/HTTP exception chains even in debug logs; repeated failure and recovery are tested. Remaining providers still require review. Pending for the full integration. |
| `parallel-updates` | Explicit platform limits: sensor 1 for diagnostic polling, coordinator-driven weather/binary sensor 0; no device actions. |
| `reauthentication-flow` | Exempt: the public APIs require no credentials. |
| `test-coverage` | Pending. [Above 95% for every module](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/) is required; a passing flow or global average is insufficient. |

The starting snapshot had 68 passing tests and 54.78% combined line/branch
coverage (58.50% lines, 40.42% branches). Config flow was 33.79% combined.
CI now measures **all** integration modules, prints per-module coverage and
requires full config-flow, both pollen-client and ICON forecast-client line/branch coverage plus a
71% combined floor (raised from 67%, initially 60%). This
floor prevents regressions at this stage; it is not a substitute for Silver.
Unused camera/SLF/hydrology placeholders remain visible in the denominator.
They must be explicitly removed in a reviewed scope or covered; no exclusions
are introduced just to improve the metric. Current exact results are in the
PR and each CI job's summary.

Continue with the remaining optional-source failure/recovery, provider payload
parsing and freshness, forecast aggregation/timezones, then entity properties, diagnostics
and shared cache/station helpers. Raise the coverage gate as these changes land.
Gold/Platinum work follows this measured baseline, rather than adding labels.

## Reproduce

```sh
python -m pip install -r requirements_test.txt
pytest -q --cov=custom_components.meteoswiss --cov-branch --cov-report=term-missing --cov-report=json:coverage.json
python scripts/check_quality_coverage.py
python scripts/check_translations.py
```

Repeat in an isolated environment with `requirements_test_min.txt`. HACS
validator/default-list submission, signed-off live acceptance and the first
fork prerelease remain release tasks, not effects of this development PR.
