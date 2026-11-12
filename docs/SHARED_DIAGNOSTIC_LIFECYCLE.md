# Shared diagnostic lifecycle and retained identity

**Status: unreleased source follow-up.** Publication and operator acceptance are
separate. Published 8.3.4 does not acquire this behaviour merely because the
source has changed.

## What changes

The station-catalogue and cache-statistics helpers are shared across MeteoSwiss
entries. Previously, unloading their first entry left a loaded second entry
without the helpers; removing that first entry also removed their registry
records. Reversing startup order could replace both service-device IDs.

The follow-up keeps one explicit owner for exactly these two helpers. The first
successfully loaded eligible entry claims them. When it unloads, is disabled or
is removed, another loaded entry takes over through its existing sensor-platform
callback. The peer's weather coordinators are not reloaded or refreshed for the
transfer. An explicitly reloaded former owner does not take the helpers back
from an already loaded peer.

| Retained item | Behaviour |
|---|---|
| Entity identity | Keep the existing entity IDs, unique IDs and internal registry IDs. |
| Device identity | Keep the existing station-catalogue/cache service-device IDs and identifiers. |
| Personal choices | Retain entity/device names, icons, aliases, areas, labels, hidden state, options and explicit activation choices. |
| Disabled service groups | Keep user-disabled devices disabled. Recompute HA-derived config-entry disablement for the new owner. |
| Data contract | Keep diagnostic state/attribute formats, four-language names, catalogue/cache contents and polling intervals. Enabled helpers follow normal HA entity polling. |
| Other groups | Current weather, forecasts/HGT, warnings, measured pollen and modelled pollen/AQ remain attached to their own entry. |

The owning configuration entry is deliberately updated for the two shared
entities/devices. They can therefore appear under a different MeteoSwiss entry
after a transfer. Their IDs and personal names stay the same; no duplicate
helper pair is created. First registrations remain disabled by default.

## Setup, failures and shutdown

Helper objects are added only after their entry reaches HA's loaded state. An
in-progress sensor platform can temporarily retain existing registry ownership
when the previous entry is being removed. It starts no helper polling until
setup succeeds. If that setup fails or is cancelled, the previous still-existing
owner can retain the records; a successfully loaded peer can also reclaim them.
When the previous entry was deliberately removed and no peer loaded successfully,
the records remain with the failed successor for a later retry.

A failed native unload keeps the existing registration rather than announcing
a successful handoff. HA's restart requirement after a failed unload still
applies. Shutdown releases shared references/listeners and does not elect a new
owner while HA is stopping. The module does not close HA-owned HTTP sessions.

Before moving anything, both helpers are checked. The move uses synchronous
native entity/device registry operations, with no intervening await. Entity
ownership is changed before device-move events can remove old-owner entities.
A failed write attempts to restore the native snapshots. Exceptions are not
copied into logs or repair text.

## Ownership repair

The translated **Shared diagnostic ownership needs review** repair means that
the optional helpers could not be registered or moved safely. Ordinary weather
data is independent and can continue.

Examples include a conflicting retained group in the target entry, unexpected
attached entities/child devices, a legacy subentry binding or inconsistent
registry records. The integration does not merge, delete or rename those
records to make the transfer succeed. If rollback itself fails, it leaves the
helpers blocked and reports the issue; it does not claim that ownership has
been restored.

1. Check the MeteoSwiss entries and the station-catalogue/cache groups in the
   HA entity/device settings. Keep their existing names and IDs for comparison.
2. If the original owner still exists, reload that entry after its source/setup
   problem is resolved. Unambiguous original ownership can be used again.
3. If the issue remains, use redacted integration diagnostics and the repair
   name for a focused maintainer review. Historical conflicts need an explicit
   retention decision; editing HA's storage files is not the recovery method.

Resolve an existing ownership repair before intentionally removing an entry:
HA itself clears records that still belong to an entry the user removes. The
automatic ID-retention guarantee covers unambiguous supported bindings; it is
not permission to delete conflicting historical groups. This follow-up adds
no automatic orphan cleanup or device-removal approval hook.

## Native evidence and limits

[Lifecycle tests](../tests/test_diagnostic_lifecycle.py) cover both current
providers, owner/non-owner departure, startup order, entity and device activation
choices, personal settings, parallel/pending setup, cancellation, setup/unload
errors, collisions, failed writes/rollback, late cleanup, shutdown and native
repair translations. Provider transports are replaced; HA entry/platform and
registry operations are native.

A real disposable Recorder test retains old history rows and writes later
values under the same entity ID after owner removal. It does not inspect or
migrate an operator's database. No runtime SQL, purge or statistics conversion
is introduced. The [separate wind-statistics change](WIND_STATISTICS_MIGRATION.md)
keeps its own release/acceptance boundary.

The whole-integration suite and strict line/branch gates remain required on
both HA 2026.11.0 and 2026.11.1. The new lifecycle module also requires full
line/branch coverage. Dependency locks, CI permissions and version floors are
unchanged by this runtime follow-up.

Historical duplicate groups, generic dynamic/stale-device applicability,
remaining translations, strict typing/client packaging and independent review
remain separate. This is bounded engineering evidence, not completed Gold or
an official quality tier for this custom integration.

Primary guidance: [HA device registry](https://contributors.home-assistant.io/core/integrations/device-registry/),
[dynamic devices](https://contributors.home-assistant.io/core/quality-scale/dynamic-devices/)
and [stale devices](https://contributors.home-assistant.io/core/quality-scale/stale-devices/).
