# Official measured HGT: source and implementation boundary

**Status: source verified; importer not implemented or released by the HGT
cleanup follow-up.** Old forecast averages are not a source for measured HGT.
Do not attach measurement semantics to the existing forecast sensor to regain
long-term statistics.

## Official source

MeteoSwiss SwissMetNet OGD directly provides:

| Parameter | Meaning | Resolution |
|---|---|---|
| `xno000d0` | Official heating degree days 12/20 | Daily |
| `xno000m0` | Official heating degree days 12/20 | Monthly total |
| `xno000y0` | Official heating degree days 12/20 | Annual total |
| `xno012d0` | Different ATD12 measure | Daily; do not substitute |

The [official parameter catalogue](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_parameters.csv)
contains those fields. The [KLO recent daily file](https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_d_recent.csv)
contains `xno000d0`. The catalogue is CP1252 encoded; station data must be decoded
and schema-validated rather than assumed to have identical encoding.
The [official station documentation](https://opendatadocs.meteoswiss.ch/de/a-data-groundbased/a1-automatic-weather-stations)
recommends using supplied aggregates instead of reaggregating higher-resolution
values. NBCN homogenised monthly/annual `xhs000m0/y0` are a different series;
do not mix them silently with raw SMN daily observations.

## Required next implementation

- Separate measured station identity and forecast identity; no replacement or
  relabelling of existing forecast histories. Record source and daily semantics.
- Import available official historical daily HGT for the selected station,
  then upsert recent days, including corrected observations. Missing values are
  missing, never zero. Recheck at least the documented rolling five-day quality
  window and distinguish delayed publication from transport failure.
- Follow the [official download/time conventions](https://opendatadocs.meteoswiss.ch/general/download).
  Do not shift an OGD UTC observation day into a Swiss local-midnight day.
  Document the conversion from catalogue unit `°C` to the integration's HGT
  display convention `°C·d` and preserve one coherent Recorder unit contract.
- Use HA's verified-TLS shared session, bounded requests and native Recorder
  import/update APIs. No extra credentials, telemetry or direct database writes.
- Own refresh, retry, unload and station-change behaviour explicitly; no
  abandoned imported series or hidden permanent forecast archive. Surface
  missing station data and conflicts instead of fabricating observations.
- Require native tests on both supported HAs: backfill, idempotent corrections,
  missing days, year boundaries, source errors and lifecycle/ownership cleanup.
  Packaging and release approval remain separate from source verification.

The old forecast archive can be removed now. It is not needed to build or
maintain this measured series.
