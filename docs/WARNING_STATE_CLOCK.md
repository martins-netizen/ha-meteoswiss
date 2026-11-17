# Published warning validity and registered states

The warning coordinator still downloads the configured postcode's warnings at
its existing ten-minute interval. The three warning binary sensors also publish
local state changes when a warning already in that snapshot starts or ends.
This prevents a published upcoming warning from remaining upcoming until the
next download, or an ended warning from remaining active for that interval.

Each enabled entity owns at most one Home Assistant point-in-time callback for
the next relevant boundary. That callback updates its registered state and the
active/upcoming attributes, then selects the next boundary. It does not request
data or refresh the coordinator. Warning levels, types, translations, postcode,
unique IDs, entity IDs and device IDs retain their existing contracts.

The existing validity semantics remain inclusive: a warning is active at its
start and at its exact end instant. Its end transition therefore runs one
microsecond after the end. Overlapping warnings retain independent validity;
the critical sensor can turn off while another non-critical warning remains
active. All three sensors update their shared warning details at these
boundaries. Outlook records contribute no active/upcoming warning or callback.
Missing bounds keep their existing meaning: an absent start does not postpone
an active warning, and an absent end introduces no end callback. The largest
representable end time has no representable later boundary.

A source update replaces the pending callback. Failure, absent data, an empty
snapshot or a snapshot without future relevant boundaries leaves no callback.
Source failure still makes the entities unavailable; retained data is not a
successful refresh. Recovery schedules boundaries from the new snapshot.
Local validity changes also work when the entry's polling preference is disabled.
They cannot discover new warnings or correct a provider snapshot without a
later successful source refresh.

Entity removal and entry unload cancel the callback. A generation check also
rejects a callback already queued before cancellation or snapshot replacement,
so it cannot publish or rearm after removal. Reload retains registry identities
and gives the new entity instances their own callbacks.

## Native regression evidence

[`test_warning_state_clock.py`](../tests/test_warning_state_clock.py) retains
native integration setup, binary-sensor registration, state publication and
unload/reload, replacing only external source work. Its first regression fails
on the previous implementation: after advancing Home Assistant time to the
published start, the registered active sensors remain off and the upcoming
sensor remains on until a coordinator update.

The tests cover start and inclusive-end transitions, overlapping windows and
shared attributes, missing bounds, outlook/expired/empty/absent data, source
failure and recovery, disabled polling, replacement of pending work, individual
entity removal, unload/reload, stable IDs and canceled callbacks that were
already queued. Source-call counts remain unchanged during local boundaries.
These are isolated native Home Assistant tests, not production acceptance.

The focused warning suite passes all 69 cases on Python 3.14.10 with both Home
Assistant 2026.11.0 and 2026.11.2. It includes the 11 new lifecycle cases plus
existing warning semantics, translations and registered-state regressions.
`binary_sensor.py` has 111/111 covered lines and 34/34 covered branches in each
run, without exclusions. The integration-wide gate remains a separate full-suite
check.
