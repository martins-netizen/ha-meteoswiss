# 8.3.0b1 — location and forecast test prerelease

**Prepared candidate:** 24 October 2026. Not yet published or accepted on the
operator's HA. The package is based on reviewed PR #59 at
4c8169206fdcb8688a438c16a93f867a633a344f; inside the integration only
manifest.json and version.py change their version. The other 36 component files,
HACS manifest and workflows are identical to that reviewed source.

This community fork builds on LNKtwo/ha-meteoswiss and retains its MIT licence
and attribution. It is an independent community project.

## What changes from stable 8.2.0

- **Choose a forecast postcode, town or POI.** Search the official catalogue,
  explicitly select the labelled point and confirm it. Its known catalogue
  height is used for the ICON request. Existing entries can change or reset
  only their forecast location through **Reconfigure**, keeping their entry
  and history. See [the point-selection guide](FORECAST_LOCATION_SETUP.md).
- **Use eight forecast sensors in ordinary cards.** Today's/tomorrow's maximum
  and minimum temperature, rainfall prediction and highest hourly rain
  probability reuse the existing ICON feed. Probability attributes identify
  every tied peak window. These predictions do not become measured statistics;
  see [forecast values and times](FORECAST_SENSORS.md).
- **Clearer setup.** Source labels/help and the selection flows ship in
  English, German, French and Italian. New observations use the developer-chosen
  600-second interval; existing individual intervals survive. Configure edits
  measured pollen; forecast Reconfigure is separate.
- **More explicit failure behaviour.** Fixed HTTPS destinations, rejected
  redirects and bounded compressed/decompressed downloads cover active sources.
  Current and forecast clients have clearer HA/source boundaries. Optional UV
  time validation and catalogue status preserve valid zero, unknown individual
  values and source outages as different states.
- **Correct time periods.** Daily weather fallback requires a complete,
  correctly aligned Swiss day. Fixed-offset native daily buckets that cover
  another period are withheld. Observation CSV processing runs in HA's executor.
  See [the overall review](RELEASE_REVIEW_2026-10-24.md) for reproduced failures,
  corrections and evidence limits.
- **HACS metadata.** country CH and hidden default branch ship in this package.
  A prerelease/custom repository does not establish default-store inclusion.

## What keeps its existing meaning

The model remains **MeteoSwiss ICON Seamless via Open-Meteo**. This is no switch
to processed OGD forecasts or a guarantee of greater weather accuracy. The
catalogue supplies point identity/coordinates/height, not a new forecast model.

A deliberate forecast selection affects ICON weather forecasts, the eight
forecast sensors and calculated HGT. Observation station, current modelled
conditions, AQ/pollen/UV base location, measured-pollen station and separately
confirmed warning postcode remain independent. Existing entries without an
explicit choice retain their original forecast coordinates. A mountain point
does not prove warning coverage for that mountain.

Warnings retain the MeteoSwiss App v3 interface and verified code catalogue.
Retained entry/entity/statistic IDs and personal options remain. The previously
retired local current-hour rain and seasonal forecast-HGT entities remain
retired; see [migration](MIGRATION.md). No dashboard, automation or physical
device is changed by downloading the integration.

## Known limits to check during this beta

- Provider place names remain unchanged. The four UI languages do not provide
  a multilingual name index. **3280** or **Murten** selects the verified town;
  Morat/Môrat is not yet an alias. Generic POIs are not relabelled as verified
  summit/pass/hut subtypes merely from their names.
- Native daily temperature/rain/HGT can be `unknown` around a clock change
  when the source's fixed-offset period differs from the Swiss calendar day.
  Hourly forecasts and complete hourly probability windows remain usable.
  Missing data is not silently zero or an estimate from a partial day.
- Observation/pollen publication can lag or omit individual parameters. Valid
  station identity does not guarantee a current measurement. UV's source time
  is checked on request; its result/status still share the existing AQ cache.
- Source polling, catalogue retry, forecast age and measurement age are
  different limits; see [sources and intervals](API_SOURCES.md). Independent
  second-by-second expiry of all legacy entities is not introduced.
- Formal HACS default-list inclusion and a complete HA Silver/Gold tier remain
  separate; the [current rule assessment](QUALITY_SCALE.md) lists the gaps.

## Test and recovery route

Use the **existing temporary HA**, with its current supported HA/HACS versions.
After this exact prerelease is published, refresh the maintained fork's HACS
information, explicitly download Release **8.3.0b1**, restart and retain the
configured integration entry. Do not substitute development or main.

Follow the [focused acceptance checklist](ACCEPTANCE_8.3.0b1.md) for setup,
existing-entry cancel/keep/change/reset, catalogue height, independent data
families, forecast sensors and missing-data behaviour. The prior clean install,
backup restore and stable update remain complete; no new blanket 24-hour wait
is imposed. Record the actual installed version and each result before stable
promotion. No HA acceptance is inferred from a successful GitHub release.

Retain a backup of the temporary instance before updating. Going back to 8.2.0
uses its original base-coordinate forecast behaviour; it ignores the new
explicit forecast choice. Reset that choice while the beta flow is available
or restore the earlier test backup if necessary. Keep the existing HA entry
and paired warning consumers; do not purge history as a rollback shortcut.

## Publication boundary

The candidate-specific publisher V1.0 checks the exact protected development
merge, all required successful checks with app/head provenance, source equality,
matching versions, unchanged CH/HACS/workflows and all three existing tags.
`--check` is read-only. `--publish` can create only this prerelease with
make_latest=false; it verifies the published tag/notes and unchanged stable
8.2.0. It cannot merge a PR, rewrite a release or contact HA. An uncertain write
is rechecked using the same exact commit; do not delete/recreate tags.

The earlier source review has automated HA/Recorder/flow/installation-layout
evidence. This candidate's exact CI and focused temporary-HA acceptance are
separate gates; neither a general first installation nor a quality-tier award
is repeated or inferred.
