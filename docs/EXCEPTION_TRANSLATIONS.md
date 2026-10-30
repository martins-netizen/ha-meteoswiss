# Translated update failures

**Scope:** implemented in #81 and published in [8.3.3b1](RELEASE_8.3.3b1.md)
on 30 October 2026. The operator reported normal operation OK on **Core
2026.10.4 / HA OS 18.4**. This does not claim manual triggering of every
translated failure. Stable [8.3.3](RELEASE_8.3.3.md) is prepared, not published;
latest stable 8.3.2 retains its earlier messages.

All 21 user-facing `UpdateFailed` sites use 19 stable keys in the integration's
`exceptions` catalogue, with English, German, French and Italian messages.
HA receives the translation domain/key without a simultaneous inline English
message. The [exception-translations rule](https://contributors.home-assistant.io/core/quality-scale/exception-translations/)
describes this native mechanism.

The messages identify observations, warnings, measured/modelled pollen, AQ,
the selected forecast, the station's separate model condition and hourly
precipitation. They describe unusable or missing data without exposing parser
variables. Separate failure categories remain separate translation keys.

Messages include no station/postcode, coordinates, download URL or raw provider
exception. Existing `from None` boundaries, retry/circuit timing, availability,
cache and recovery behaviour remain. Programmer errors and private source
validation exceptions are not relabelled as successful updates.

Tests verify native HA loading of all four exception catalogues, complete
coverage of actual raised keys, and absence of inline messages/placeholders.
Existing source, privacy and recovery tests now assert stable error categories
instead of language-specific English text. This change was reviewed separately
from the icon-translations PR; published 8.3.3b1 bundles both. Its
[focused visual/operation report](ACCEPTANCE_8.3.3b1.md) and automated error
coverage remain distinct evidence. Stable promotion retains this runtime.
