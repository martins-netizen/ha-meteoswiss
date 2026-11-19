# Gold engineering evidence contract

This custom integration uses the Home Assistant
[quality-scale tiers](https://contributors.home-assistant.io/core/quality-scale/tiers/)
as an engineering checklist: 20 Bronze prerequisites, 10 Silver prerequisites
and 21 Gold rules. Custom integrations have no formal Home Assistant tier.
The manifest does not claim `quality_scale: gold`. Platinum's strict typing,
asynchronous dependency and injected-session requirements are separate.

The complete, reviewable rule inventory is
[quality_rules.json](quality_rules.json). It complements the narrative
[quality matrix](QUALITY_SCALE.md); an automated result cannot award a tier,
prove a human review happened or certify every installation.

**Current boundary, 19 November 2026:** approved signed #131 at
`115ddad474dcae15aa49fb5f368cbed600adf80d` completes the
[canonical correction](COORDINATOR_CANONICAL_COMPLETION.md) and calculated-HGT
midnight-state review. The older b7 human placement judgment missed the ninth
actual coordinator; automation did not establish that judgment. The corrected
source has explicit class-placement/alias evidence and native registered-state/
lifecycle regressions. Both actual supported Core jobs passed the full suite
and fresh 51-rule verification; the [dated record](RELEASE_EVIDENCE_8.3.5.md)
retains exact source/results. Stable packaging and publication have their own
gates. Earlier measured beta results and bounded operator acceptance retain
their own scope; see the [current matrix](QUALITY_SCALE.md).

## Explicit kinds of evidence

Each rule has its official identifier and tier, applicability, assessment,
bounded rationale, root-relative source and documentation references and,
where useful, function-level pytest selectors. Required fields and all 51
unique rule identifiers are validated. Documentation fragments must resolve.
Absolute paths, traversal, symlinks and duplicate references are refused.

| Field | Meaning |
|---|---|
| `applicability: applicable` | The requirement applies to this service. |
| `applicability: exempt` | A recorded service-specific exception, with the exact official rule URL. |
| `applicability: custom-route` | The HACS branding route is assessed; no Core branding submission is claimed. |
| `assessment: automated` | The named native behavior must actually pass in the current run. Source references explain its scope. |
| `assessment: reviewed` | Structural or documentation evidence requires human assessment. Any listed supporting tests must still pass. |
| `assessment: exempt` | The reason is recorded; automation checks its integrity, not its correctness. No fictional test pass is attached. |
| `assessment: pending` | A dependency remains unresolved. CI verification fails until reviewed evidence is present. |

Manual judgments include sensible polling, platform parallelism, useful
documentation, applicability and code organization. Tests support those
judgments where appropriate; they do not turn them into automated assertions.
The fixed seven-role service topology and conservative historical-ownership
boundary have their own [native evidence](FIXED_SERVICE_TOPOLOGY.md).

The metadata inventory independently specifies each exposed quantity's device
class, unit, state class, category and activation default. It checks native
registry/runtime entities for both providers and optional observed HGT. It does
not copy the integration's descriptions to build its expectations. Existing
circular wind readiness and Recorder history boundaries remain separately
tested. No class is invented where Home Assistant has no suitable quantity.

## One fresh native run

Both existing CI compatibility jobs run their complete suite exactly once.
The evidence checker adds JUnit output to that run and consumes the same
branch-coverage JSON used by the unchanged strict coverage gate. From the
repository root, after installing the documented native test environment:

```sh
quality_prefix="$(python scripts/check_quality_rules.py prepare)"
pytest -q --cov=custom_components.meteoswiss --cov-branch \
  --cov-report=term-missing --cov-report=json:coverage.json \
  --junitxml="$(python scripts/check_quality_rules.py junit-path)" \
  --junit-prefix="$quality_prefix"
python scripts/check_quality_coverage.py
python scripts/check_quality_rules.py verify
```

Stop if any command fails. `prepare` validates the index, creates a random run
nonce, snapshots the runtime/tests/policies/documentation and removes previous
JUnit/coverage output. It uses a fixed project-specific private directory under
the system temporary directory. Its directory is mode 0700 and its marker and
precreated JUnit file are mode 0600. Report names are fixed. No command accepts
an arbitrary input, output or source-root path. A subsequent `prepare` replaces
the previous run for that checkout, so simultaneous validation requires separate
checkouts.

`verify` refuses changed source, sessions older than one hour, reports predating
preparation, future timestamps, empty/malformed XML, foreign prefixes, duplicate
testcases, failed tests and absent or skipped required selectors. Every reported
matching parameter variant must pass; parameter-specific selectors are refused.
XML cannot prove that an unreported variant was not deselected. The unfiltered
CI command and strict runtime coverage establish the full-run boundary; the
checker verifies the per-rule matches within that run.

The XML parser follows the independently observed pinned pytest 9 CLI schema:
`testsuites` / `testsuite`, timezone-aware suite timestamp, prefix-qualified
classname, test name and child outcome elements. Successful pytest subtests
increase the suite counter without producing separate testcase rows. Counters
therefore must cover the emitted rows, but are not equated to them. A small real
pytest CLI regression checks that behavior independently of synthetic rejection
fixtures. The checker counts passing emitted variants, not subtests, as evidence.

Coverage must be freshly generated with branch coverage for the complete actual
component module inventory. Empty or fabricated inventories and inconsistent
statement totals fail. The existing coverage checker remains responsible for
all numerical thresholds and its stricter full line/branch requirements. This
new gate does not lower or replace them.

## Limits and review boundaries

The checker prints a bounded JSON result to standard output. Automated rows say
`automated_verified`; manual rows say `human_review_recorded`; exemptions say
`exemption_recorded`. `official_tier_awarded` is always false. CI retains its
read-only permissions, pinned actions, universal hash locks, dependency audit,
offline uv policy, Hassfest and existing required aggregate check.

Repository review approvals and whether SonarCloud is a required GitHub ruleset
check are administrative governance decisions. This source PR does not change
or pretend to enforce those settings. Provider response contracts use actual
published fixtures or independently verified native APIs; internally consistent
mocks are not proof of an external service's behavior. Production acceptance,
unattributable historical registry records and independent security assurance
remain distinct from this automated engineering evidence.
