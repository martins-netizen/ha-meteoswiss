# Entity icon translations

**Scope:** implemented in #80 and included in prepared [8.3.3b1](RELEASE_8.3.3b1.md), not yet published. Stable 8.3.2 retains its previous icon implementation.

All 24 existing custom entity icons move from Python descriptions to
`custom_components/meteoswiss/icons.json`, using the entities' existing
translation keys. This follows the [HA icon-translations rule](https://contributors.home-assistant.io/core/quality-scale/icon-translations/).

The mapping retains the previous symbols for measured/modelled pollen,
today/tomorrow forecast summaries, calculated HGT and the three warning
binary sensors. It adds no invented state/range icons. Weather conditions,
other observation sensors, AQ and diagnostics continue to use HA's domain
and device-class defaults where no custom icon was previously set.

Entity IDs, translation keys, names, measurements and polling are unchanged.
No registry migration is performed. A personal icon set in entity settings
continues to take precedence; clearing that override returns to the translated
default. Default icons are resolved by the frontend rather than repeated in
every backend state attribute. Automations should use the numeric/state value,
not assume a default `icon` attribute is always present.

Validation checks the mapping against the earlier custom icons, links every
key to an active description and all four catalogues, and exercises a personal
name/icon through a native HA entry reload. Hassfest validates icons.json.
The existing minimum/current HA jobs and quality gates still apply. No new
release or manual HA installation is performed by this change; a later
candidate needs a short visual check before stable publication.
