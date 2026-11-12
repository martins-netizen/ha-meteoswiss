# Native names for the remaining service groups

**Status:** unreleased development follow-up after the bounded device-removal
policy in PR #104. Published stable 8.3.4 is unchanged. This updates display
metadata, not sources, observations, forecast calculations or registry identities.

The two diagnostic groups and forecast groups already use native HA device
translations. This follow-up supplies the remaining current-weather,
modelled air-quality/pollen, warning and measured-pollen names in DE/EN/FR/IT.
All English defaults remain exactly the same.

| Group | Native device key | Variable text retained |
|---|---|---|
| MeteoSwiss current weather | `current_meteoswiss` | `station`: the existing selected station label; `MeteoSwiss {station}` in every language. |
| Open-Meteo current weather | `current_openmeteo` | None; provider identity remains Open-Meteo. |
| Modelled air quality/pollen | `modelled_air_quality` | None; the existing shared Open-Meteo group. |
| Warnings | `warnings` | `postal_code`: the saved warning postcode, including leading zeros. |
| Measured pollen | `measured_pollen` | `station`: the existing pollen-station label. |

## Fixed wording

The brand prefixes remain `MeteoSwiss` or `Open-Meteo` as shown in the English
defaults below. The variable station/postcode text is never translated or used
to generate a new identifier.

| Language | Open-Meteo current label | Air-quality/pollen label | Warning wording | Measured-pollen wording |
|---|---|---|---|---|
| English | Current Weather | Air Quality & Pollen | Alerts | Pollen (Measured) |
| German | Aktuelles Wetter | Luftqualität und Pollen | Wetterwarnungen | Pollen (gemessen) |
| French | Météo actuelle | Qualité de l’air et pollen | Alertes météo | Pollen (mesuré) |
| Italian | Meteo attuale | Qualità dell’aria e pollini | Allerte meteo | Pollini (misurati) |

English defaults remain `Open-Meteo Current Weather`,
`Open-Meteo Air Quality & Pollen`, `MeteoSwiss Alerts - {postal_code}` and
`MeteoSwiss Pollen (Measured) - {station}`. This work does not invent multilingual
locality aliases, change provider branding or translate compatibility values.

## Names and existing choices

HA renders the default device name through its native translation mechanism
during setup/reload using its configured language. A system-language round trip
uses the existing entry; this change adds no language listener, polling or
automatic peer reload. A browser's independently selected language is not a
separately implemented naming path.

Existing entity/device row IDs, unique IDs, entity IDs and bindings stay the
same. Personal device and entity names, aliases, icons, areas, labels, visibility,
activation choices and display precision remain authoritative. Only default
device labels change with language. HA controls initial entity-ID language on
first registration; existing dashboards do not need an ID migration.

Manufacturer/model strings, attributions, units, device/state classes, raw
states and technical attributes retain their contracts. A disabled group stays
disabled. The ownership handoff and manual removal policies from
[shared diagnostics](SHARED_DIAGNOSTIC_LIFECYCLE.md) and
[device removal](DEVICE_REMOVAL.md) keep their identities and protection checks.

## Privacy and evidence

Station/postcode text already belonged to the old device names; placeholders
add no new provider request, credential, telemetry or permission. They remain
local HA display metadata. Integration diagnostics retain the existing location
redaction and do not export device translation placeholders.

[Native tests](../tests/test_service_device_translations.py) cover both
providers, all four languages, Unicode station labels and leading-zero
postcodes, diagnostics redaction, pre-existing English groups, personal names,
all three entity activation choices, hidden entries, aliases/areas/labels and
precision. A full language round trip retains all seven group IDs and every
entity binding. Device disablement/source failure remains independent. A real
temporary Recorder database retains old rows and appends new values under the
same entity ID after changing the default group language.

The four catalogues retain English/source and placeholder parity. Existing
strict coverage/security/lock gates still apply. Release and operator UI
acceptance remain separate; technical compatibility strings, authoritative place
aliases, historical inventory and full Gold require their own assessment.
