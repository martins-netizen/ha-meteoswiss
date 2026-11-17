# Optional-source outage and recovery logging

**Review:** 17 November 2026 · **Source baseline:** 8.3.5b6.

The optional UV response and shared weather-station catalogue log one generic
message when their source becomes unavailable, and one on recovery. Both
handwritten transition messages now use **INFO**, following the current
[Silver logging rule](https://contributors.home-assistant.io/core/quality-scale/log-when-unavailable/).
Repeated failed polls, failure-cache hits and healthy-cache hits do not repeat
those transitions. Raw locations, response bodies and exception URLs remain
absent from the messages.

Only those two message severities change. Required coordinator failures keep
Home Assistant's native `UpdateFailed` reporting on the supported 2026.11.0
and 2026.11.2 fixtures. Those versions do not provide the newer
`UpdateFailedUnreachable` example shown in the current developer guide; the
integration does not override Core logging or invent an unsupported API.
Retries, cache retention, source freshness, entity availability, polling,
configuration, statistics and identifiers retain their existing behavior.

Native tests exercise UV failure/recovery while AQ and pollen remain usable,
and catalogue expiry, bounded retries, stale-data retention and recovery. They
check transition counts and actual log-record levels, including private-error
markers and healthy-cache reuse. Existing provider and availability tests remain
part of both complete HA compatibility runs. No operator failure injection or
repeated b6 installation is required for this logging correction.
