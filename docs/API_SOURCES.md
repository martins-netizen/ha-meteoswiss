# API Sources & Attribution

This document describes all data sources used by the MeteoSwiss integration.

---

## 1. MeteoSwiss SwissMetNet (Current Weather)

| Property | Value |
|---|---|
| **Provider** | MeteoSwiss (Federal Office of Meteorology and Climatology) |
| **API** | `data.geo.admin.ch` STAC API |
| **Base URL** | `https://data.geo.admin.ch/api/stac/v1` |
| **Collection** | `ch.meteoschweiz.ogd-smn` |
| **Data** | 10-minute current weather measurements |
| **Stations** | 293+ SwissMetNet stations across Switzerland |
| **Format** | CSV (semicolon-separated) |
| **Update interval** | 10 minutes |
| **Rate limit** | None (Swiss open government data) |
| **Auth** | None required |
| **License** | Open use (attribution required) |
| **Attribution** | © MeteoSwiss |

### Access Pattern

```
1. GET /collections/ch.meteoschweiz.ogd-smn/items/{station_id}
2. Parse STAC Item → find asset "{collection}_{station}_t_now.csv"
3. Download CSV → parse latest row
```

---

## 2. MeteoSwiss App API (Weather Alerts)

| Property | Value |
|---|---|
| **Provider** | MeteoSwiss |
| **API** | MeteoSwiss App Web Service |
| **URL** | `https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail?plz={plz}00` |
| **Data** | Weather warnings per postal code |
| **Format** | JSON |
| **Update interval** | 10 minutes |
| **Rate limit** | Undocumented (use responsibly) |
| **Auth** | None required |
| **Attribution** | © MeteoSwiss |

### Warning types: legacy implementation labels, not an API specification

The following table describes the existing implementation. It is **not** a
verified complete provider-code specification. Investigation on 16 October 2026
found a conflict with the independent MeteoSwissApi reference client, which
uses `0` for wind and `4` for slippery roads. The current `4 = Wind` label below
must not be used as evidence for new safety-related automation filters.
Numeric corrections and additional labels require a separately reviewed change;
this validation/availability change preserves the raw provider `warn_type`.

| Code | Type |
|---|---|
| 1 | Thunderstorm |
| 2 | Rain |
| 3 | Snow |
| 4 | Wind |
| 5 | Ground Frost |
| 10 | Forest Fire |
| 11 | Flood |

The official [natural-hazards portal](https://www.naturgefahren.ch/) lists twelve
current hazard families, including slippery roads, heat, avalanches, earthquakes
and drought. Its current frontend uses semantic identifiers such as `wind` and
`slippery-roads`, not a published complete App API numeric table. Code `6` is
labelled mass movements in the independent reference client, but is not one of
the twelve current portal families; it remains unconfirmed here. Do not infer
that this integration fetches every portal layer merely from a label list.

Reference for the discrepancy (independent client, not an official specification):
[MeteoSwissApi WarnType at 33ade33](https://github.com/thomasgalliker/MeteoSwissApi/blob/33ade33ec2de8b51a9867e6412d31288b06c0a67/MeteoSwissApi/Models/WarnType.cs).

### Warning Levels

| Level | Meaning |
|---|---|
| 1 | No or minor danger |
| 2 | Moderate danger |
| 3 | Significant danger |
| 4 | High danger |
| 5 | Very high danger |

---

## 3. MeteoSwiss ogd-pollen (Measured Pollen)

| Property | Value |
|---|---|
| **Provider** | MeteoSwiss |
| **API** | `data.geo.admin.ch` direct file access |
| **Base URL** | `https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/` |
| **Data** | Hourly measured pollen concentrations |
| **Stations** | 16 pollen stations across Switzerland |
| **Format** | CSV (semicolon-separated) |
| **Update interval** | 1 hour |
| **Rate limit** | None (open data) |
| **Auth** | None required |
| **Attribution** | © MeteoSwiss |

### Pollen Types Measured

Birch (Betula), Alder (Alnus), Hazel (Corylus), Beech (Fagus), Ash (Fraxinus), Oak (Quercus), Grasses (Poaceae), Mugwort (Artemisia), Ragweed (Ambrosia), Plantain (Plantago), Nettle (Urtica), Sorrel (Rumex)

### Access Pattern

```
GET https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/{station}/ogd-pollen_{station}_h_now.csv
```

---

## 4. Open-Meteo Forecast API

| Property | Value |
|---|---|
| **Provider** | Open-Meteo |
| **URL** | `https://api.open-meteo.com/v1/forecast` |
| **Data** | Weather forecast (hourly + daily) |
| **Coverage** | Global |
| **Format** | JSON |
| **Update interval** | 1 hour |
| **Rate limit** | 10,000 requests/day (free tier) |
| **Auth** | None required (API key for higher limits) |
| **License** | MIT License (CC-BY 4.0 for data) |
| **Attribution** | Open-Meteo (https://open-meteo.com/) |

### Parameters Used

- `temperature_2m`, `relative_humidity_2m`
- `precipitation`, `precipitation_probability`
- `windspeed_10m`, `winddirection_10m`
- `weather_code` (WMO code)
- `snowfall`, `freezing_level_height`

---

### Alternative current-weather source

An entry explicitly configured as Open-Meteo also reads `current` values at its
configured coordinates: temperature, humidity, sea-level pressure, wind speed
and direction, precipitation, WMO code, day/night and optional UV. These are
modelled current conditions, not SwissMetNet measurements. Units are explicitly
Celsius, km/h and mm; times are Unix seconds. Its default model selection does
not change the separate `meteoswiss_icon_seamless` forecast request.

Current precipitation covers the backward-looking `current.interval` duration,
which is retained on the precipitation sensor as `measurement_interval_seconds`.
It must not be interpreted as an hourly sum or rate. The optional legacy hourly
preview is bounded to 24 hours and does not drive HA weather forecast services.
See [the provider's current-response contract](https://open-meteo.com/en/docs).

## 5. Open-Meteo Air Quality API

| Property | Value |
|---|---|
| **Provider** | Open-Meteo |
| **URL** | `https://air-quality-api.open-meteo.com/v1/air-quality` |
| **Data** | Pollen forecast + air quality |
| **Coverage** | Global (CAMS 11km model) |
| **Format** | JSON |
| **Update interval** | 30 minutes |
| **Rate limit** | 10,000 requests/day (free tier) |
| **Auth** | None required |
| **Attribution** | Open-Meteo / Copernicus CAMS |

### Parameters Used

- **Pollen:** `alder_pollen`, `birch_pollen`, `grass_pollen`, `mugwort_pollen`, `ragweed_pollen`
- **Air Quality:** `pm2_5`, `pm10`, `nitrogen_dioxide`, `ozone`

---

## 6. Stations Metadata

| Property | Value |
|---|---|
| **URL** | `https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv` |
| **Data** | Station list (ID, name, canton, coordinates, altitude) |
| **Format** | CSV (semicolon-separated, ISO-8859-1 encoding) |
| **Update interval** | Static (rarely changes) |
| **Caching** | 24 hours |

---

## Rate Limiting & Best Practices

- All coordinators use **shared aiohttp session** (single TCP connection pool)
- **TTL caching** reduces API calls:
  - Current weather: 10 minutes (600s)
  - Forecast: 30 minutes (1800s)
  - Stations metadata: 24 hours (86400s)
  - Pollen: 30 minutes (1800s)
- **Circuit breaker** opens after 5 consecutive failures (5-minute pause)
- **Exponential backoff** retry (4 attempts, 1-10s delays)
- Total outbound calls: ~15-20 requests/hour (normal operation)

---

## Attribution Requirements

When displaying data from this integration, include:

- **MeteoSwiss** — © MeteoSwiss (current weather, alerts, measured pollen)
- **Open-Meteo** — Data by Open-Meteo.com (forecast, air quality, pollen forecast)
- **geo.admin.ch** — Source: Federal Office of Topography swisstopo (station data delivery)
