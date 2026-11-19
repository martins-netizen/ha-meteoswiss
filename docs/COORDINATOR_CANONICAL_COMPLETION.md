# Coordinator placement and HGT midnight correction before stable 8.3.5

**Review date:** 18 November 2026 · **Completion update:** 19 November 2026

**Stage:** approved correction regularly merged as signed
[PR #131](https://github.com/martins-netizen/ha-meteoswiss/pull/131), source
`115ddad474dcae15aa49fb5f368cbed600adf80d`, exact tree
`98fbd1b49500503c2994292957674f0ac00a1aa6`. Stable packaging is a separate
version-only promotion from this source; its own approval and publication
remain separate. [Dated evidence](RELEASE_EVIDENCE_8.3.5.md) records actual gates.

## Finding and prior evidence

The overall documentation/source review found **nine** actual
`DataUpdateCoordinator` definitions, not the eight recorded by the older layout
inventory. Published b7 defines the additional `MeteoSwissHgtCoordinator` in
`hgt_ogd_coordinator.py`. The current [common-modules rule](https://contributors.home-assistant.io/core/quality-scale/common-modules/)
requires coordinator definitions in `coordinator.py` and has no exception for a
specialized source family. The separate manager/Recorder boundary does not
justify treating a definition in another module as compliant.

The earlier 51-rule index and native b7 suite passed their implemented checks.
Those measured results, publication and bounded operator sight report remain
valid within that scope. The structural review was incomplete for this ninth
class; an automated reference check could not certify that human judgment.
The [dated evidence](RELEASE_EVIDENCE_8.3.5.md) records that limit explicitly.
An official HA tier or independent security certification was never awarded.

## Narrow correction

The correction places the **single actual** measured-HGT coordinator definition in
[coordinator.py](../custom_components/meteoswiss/coordinator.py), alongside the
other eight. It retains [hgt_ogd_coordinator.py](../custom_components/meteoswiss/hgt_ogd_coordinator.py)
as an explicit compatibility re-export of that same class, without a second
definition, wrapper or inheritance-only substitute. This also retains the
component path inventory and historical publisher fixtures.

The source reader, shared station ownership/locking and native Recorder
adapter stay in their existing HGT modules. Constructor, translated failures,
bounded retry, polling and unload semantics remain their existing contracts.
Retained entity/statistic IDs, provenance and cleanup consent do not change.
The correction introduces no source request, session, stored archive, purge,
credential or device operation. Native lifecycle/recovery regressions and a
complete class-definition inventory validate the actual corrected source.

## Calculated HGT midnight state correction

The same overall review reproduced a separate calendar-state defect in the
calculated forecast HGT sensor. After Swiss midnight, its Python projection
already selected the new daily mean, while Home Assistant's registered state
could still show yesterday's value until the next hourly source update. The
eight scalar forecast sensors already had their own clock; that did not update
the distinct calculated-HGT entity.

The corrective source gives calculated HGT one local next-midnight callback in
`Europe/Zurich`. It publishes both the value and `daily_mean_temperature` from
the retained daily snapshot, including 23-/25-hour Swiss days. A source update
replaces the pending callback; failure/empty data cancels it, successful
recovery schedules it again, and entity removal cancels it. Invalidated queued
callbacks must not write state or rearm. Entry polling can remain disabled.
No provider fetch, interval change or separate stored snapshot is introduced.

The existing coordinator-success availability, HGT 12/20 calculation,
identities, units, no-LTS policy and archive/cleanup boundaries remain. The
scalar sensors' three-hour age limit is not newly imposed on this HGT sensor.
This is a real change in registered-state timing, rather than a behavior-
identical version promotion. [The forecast guide](FORECAST_SENSORS.md#calculated-hgt-follows-the-swiss-day)
explains the user-visible contract. Native clock/lifecycle tests and a clean
old-source counterexample support the corrective review.

Two initially suspected repair-diagnostics leaks were separately refuted by
Core's omission of nonpersistent issue placeholders; see the
[privacy review](PRIVACY_SECURITY_REVIEW.md). They do not justify an extra
privacy or repair-UI change in this source PR.

## Delivery and acceptance

The correction received its own native review and trusted exact-head checks,
then normal approval and a signed squash merge as #131. The actual source
identity above is the stable promotion baseline; b7 did not already contain
these fixes. The [dated evidence](RELEASE_EVIDENCE_8.3.5.md) records the actual
source validation and separate package boundary. A prepared publisher or a
matching source tree does not itself establish stable publication.

Stable 8.3.5 changes only the two component version fields relative to that
source. Fixed Publisher V1.9 validates the direct parent, exact component
preservation, policies, package checks and publication readback. Old fixed
profiles and tags stay immutable. Package review, actual-merge checks and
authorized publication remain required in their own scope.

The b7 operator sight report remains closed. The corrective source has
its own native layout/clock/lifecycle tests; it does not invent another
production migration, failure injection or operator observation window. Stable selection and any ordinary package update
follow the published catalogue and [upgrade guide](ACCEPTANCE_8.3.5.md).
