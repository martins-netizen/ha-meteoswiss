# Diagnostics privacy boundary

This development correction minimizes the downloadable diagnostics snapshot.
It changes no provider request, configured source, statistic ID, ownership
record, Recorder operation or cleanup confirmation.

## The complete native download

Home Assistant adds all same-domain repair issues around the integration's
diagnostics result. A persistent retired-HGT notice previously carried exact
station statistic IDs in unused translation placeholders. Those values could
appear in a download for another entry even though the integration callback
redacted its own location fields.

New notices omit those redundant placeholders. On component setup, before HA
registers its diagnostics platform, a metadata-only update clears placeholders
from that exact existing persistent notice through HA's public registry API.
Creation time, dismissed state and every other field are retained; other
notices are untouched. Core already owns registry loading, and this hook does
not reload the registry, load HGT ownership or inspect Recorder.

The repair confirmation still obtains and displays its exact selected IDs
independently before any write. The DE/EN/FR/IT catalogues and confirmation flow
remain unchanged. No deletion or new cleanup approval follows from a download.

## Configuration summary

Diagnostics export only fixed location-field redaction markers, a recognized
source enum and a finite numeric polling interval of at least 600 seconds.
Malformed allowed settings become `unknown` or `invalid`; unknown key names
and values are omitted. The historical `polen_station_code` key is treated as
location data. Arbitrary nested stored fields cannot become an unreviewed
export channel. Configuration and options in HA itself are not modified.

Runtime diagnostics retain source roles, availability, valid timestamps, data
shape, aggregate cache counts and exception class names. Raw provider bodies,
request URLs, exception messages, station identities and coordinates are not
added by this correction.

## Evidence and limits

Native HTTP tests inspect the outer `issues` envelope, loaded/unloaded/disabled
entries, stored pre-upgrade notices and normal manager re-synchronization.
They verify retained creation/dismissal metadata, unrelated issues and the
exact confirmation target list. Callback tests cover typed data/options,
unknown values, malformed inputs and loaded/unloaded runtime summaries.
Cancellation propagates without source, ownership or Recorder I/O.

A cold disabled-only domain normally has no diagnostics handler; once the
component loads, its setup hook runs before that handler is registered. These
are the supported HA 2026.11.0/2026.11.2 lifecycle boundaries tested here, not a
global filter for arbitrary registry mutations after startup.

This is a bounded implementation correction, not evidence that a user shared
sensitive diagnostics, an independent security certification or a reason to
repeat the accepted b3/b5/b6 operator checks.
