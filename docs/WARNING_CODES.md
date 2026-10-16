# Warning-code proposal — verification pending

**Draft only. This catalogue is not approved for merge, release or HA deployment.**
Review date: 16 October 2026. Automated tests establish consistency between the
proposed parser labels and translations; they do **not** prove the provider's
numeric semantics. Raw `warnings[].warnType` identifiers are never renumbered.

## What the sources establish

- The official [Naturgefahrenportal](https://www.naturgefahren.ch/) presents
  twelve current named hazard families. Its current frontend uses identifiers
  such as `wind`, `slippery-roads`, `heat-wave`, `avalanches`, `earthquake` and
  `drought`. This establishes those names, not a complete App API numeric table.
- The independent [MeteoSwissApi WarnType implementation at 33ade33](https://github.com/thomasgalliker/MeteoSwissApi/blob/33ade33ec2de8b51a9867e6412d31288b06c0a67/MeteoSwissApi/Models/WarnType.cs)
  supplies the candidate numerical mapping below. It is an independently
  authored client, not an official MeteoSwiss specification.
- A provider response previously observed on 11 October 2026 identifies ground
  frost as type `5`; the captured fields and source endpoint are in
  `tests/test_alert_types.py`.
- Direct reads of the existing public `v1/plzDetail` endpoint on 16 October 2026
  returned type `10` with provider text/links identifying forest fire, including
  for `plz=830200`. These responses do not prove the other numbers.
- No complete official numeric App API specification was found during this
  investigation. The new portal's named identifiers are a different interface;
  they cannot be silently substituted for the configured postcode App service.

## Proposed catalogue and evidence

| Code | Proposed English label | German | Numeric evidence |
|---|---|---|---|
| 0 | Wind | Wind | Independent client; provider confirmation pending |
| 1 | Thunderstorm | Gewitter | Independent client; provider confirmation pending |
| 2 | Rain | Regen | Independent client; provider confirmation pending |
| 3 | Snow | Schnee | Independent client; provider confirmation pending |
| 4 | Slippery Roads | Strassenglätte | Independent client; provider confirmation pending |
| 5 | Ground Frost | Bodenfrost | Earlier observed provider warning + independent client |
| 7 | Heat | Hitze | Independent client; provider confirmation pending |
| 8 | Avalanches | Lawinen | Independent client; provider confirmation pending |
| 9 | Earthquakes | Erdbeben | Independent client; provider confirmation pending |
| 10 | Forest Fire | Waldbrand | Provider response on 16 October + independent client |
| 11 | Flood | Hochwasser | Independent client; provider confirmation pending |
| 12 | Drought | Trockenheit | Independent client; provider confirmation pending |

Code `6` remains `Unknown (6)`. The independent client calls it mass movements,
but its status and meaning in the current postcode endpoint are unconfirmed.
Other unknown whole numeric identifiers also remain visible with their original
number. Recognition of a label does not claim the endpoint supplies every
hazard family, particularly for drought or non-weather agencies.

## Before approval

Obtain the provider's complete authoritative enumeration for
`https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz=830200`, explicitly covering
`warnings[].warnType`, `warningsOverview[].warnType`, code zero, reserved/retired
codes and any differences from v2/v3. Prefer a stable official documentation or
metadata URL; otherwise retain the provider's written answer as evidence.

Then compare the response with every proposed label and all four translations,
and test source-derived examples. A passing unit test alone cannot close this
verification gate.

Inspect the actual HA dashboards, markisen/awning protection, templates and
automations before installation. The existing implementation labels `4` as
wind; any live filter such as `[1, 2, 4]` must be checked against authoritative
code meanings. Do not blanket-replace numeric literals or alter warning
thresholds based on the proposed translated names. Existing entities/statistics
and the installed observation snapshot are not changed by this draft.
