# Foehn and HGT metadata: numeric codes, predictions and statistics

**Review version:** 1.1 · **Reviewed:** 10 November 2026
**Status:** Unreleased source follow-up after published stable 8.3.4.

## Device classes must fit the quantity

Home Assistant's [device-class rule](https://contributors.home-assistant.io/core/quality-scale/entity-device-class/)
asks for a class wherever one fits. It does not require inventing a class for
every numeric value. Both supported HA fixtures, **2026.11.0** and **2026.11.1**,
were inspected against their sensor class/unit definitions.

| Entity | Existing contract | Device-class decision |
|---|---|---|
| Foehn index | Numeric provider code, unit `Code` | Keep no device class. It is not an air-quality index, temperature or wind speed. A text `enum` would require different states and removal of the existing unit/state class. |
| Today's HGT 12/20 | Forecast-derived degree days, unit `°C·d` | Keep no device class. Degree days combine temperature difference and time; neither `temperature`, `temperature_delta` nor `duration` accepts this unit. |

MeteoSwiss's [published Foehn-code definition](https://opendata.swiss/en/dataset/messwerte-fohnindex-10-min-wert)
distinguishes 0 (no Foehn), 1 (mixed Foehn air) and 2 (Foehn). These are category
codes, not a continuous wind-strength scale. This review preserves the numeric
contract and its existing identities. It does not convert this sensor to text,
rename entities, change units or claim an observation at stations without data.

## Correct the HGT forecast's state class

The actual error is the HGT sensor's old `state_class=measurement`.
Its daily mean comes from the location forecast and can include hours still in
the future. [HA's sensor guidance](https://contributors.home-assistant.io/core/entities/sensor/#state-classes)
reserves measurement statistics for present-time measurements, not predictions.
The eight other forecast-summary sensors already omit a state class.

The follow-up therefore sets **HGT `state_class=None`**, retaining its numeric
value, HGT 12/20 formula, `°C·d` spelling, forecast attribution, selected location,
unique/entity/device IDs and personal registry choices. There is no new sensor,
extra request, configuration change or entry/device deletion.

### What this means for history and existing charts

- Current HGT values and automations using the numeric state continue normally.
- Ordinary state history continues under the configured Recorder retention.
- New HGT predictions no longer produce five-minute/hourly measurement statistics.
- Existing statistic metadata, IDs and hourly rows are retained without rewriting
  them as measured heating demand. They remain historical forecast summaries.
- A chart that uses HGT long-term statistics stops gaining new points after this
  change. Use current values/ordinary history for the forecast. A measured HGT
  archive is a separate feature requiring actual observations and validation.

Home Assistant can flag an existing series whose entity no longer has a state
class in its Statistics tools. See [the statistics guide](https://www.home-assistant.io/docs/configuration/long-term-statistics/#when-the-unit-or-the-state-class-changes).
Do not delete old data to hide that indication. This follow-up performs no
statistics purge, metadata conversion, backfill or lifetime-history guarantee.
Normal Recorder retention still applies to raw state history.

## Native regression evidence

Two new tests use actual HA entity setup/reload and the SQLite Recorder on both
supported HA fixtures. Both fail against the previous measurement declaration.
With the correction they verify:

- Forecast values and raw history are recorded while measured temperature, used
  as a control, still receives compiled statistics; HGT receives none.
- Seeded earlier HGT hourly rows and statistic metadata remain unchanged across
  entry reload and a new statistics compilation window.
- Entity-registry identity, device binding, personal name, icon and aliases stay
  unchanged; the existing HGT entity still publishes its updated prediction.

The older HGT boundary, missing-data, Swiss-date rollover, forecast routing,
identity and official precipitation archive tests remain active. These are local
automated tests, not an inventory of a user's database or a manual HA acceptance.

## Remaining wind-direction work

Both supported HAs provide `WIND_DIRECTION` and `MEASUREMENT_ANGLE`. The legacy
wind-direction sensor still uses no device class and arithmetic `measurement`.
A circular mean correctly handles the 360°/0° boundary, but HA deliberately
[stops a series when its mean type changes](https://www.home-assistant.io/docs/configuration/long-term-statistics/#when-the-unit-or-the-state-class-changes).
Silently reinterpreting older arithmetic means as circular means would be wrong.

Wind direction therefore remains a separate migration task with an explicit
policy for preserving the old series. This HGT follow-up does not alter wind
metadata or statistics. The overall `entity-device-class` assessment stays
partial; this review does not complete Gold or confer an official quality tier.
