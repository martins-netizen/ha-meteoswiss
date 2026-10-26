# 8.3.1b1 focused Home Assistant check

**Protocol version:** 1.1 · **Updated:** 26 October 2026

**Reported result — 26 October 2026:** after publication of 8.3.1b1, the operator
confirmed the requested version and visual check. This closes the focused
practical acceptance within the requested scope. No new independent HA-core,
registry, statistic or deliberate damaged-selection audit is inferred. The
steps below remain the protocol, not a request to repeat completed checks.
The [stable update check](ACCEPTANCE_8.3.1.md) records a later actual stable download.

Use the existing test HA and entry. Install only after the exact **8.3.1b1**
release is announced. The normal stable release remains **8.3.0**. Retain the
existing backup; this check does not require another first installation or
restore rehearsal.

1. **Install and confirm.** In the existing maintained-fork HACS repository,
   select Download/Redownload → **8.3.1b1** once available, then restart HA once.
   Check that this version is installed. Refreshing repository information
   alone does not download files.
2. **Find the settings link.** Open MeteoSwiss → Configure. At the weather
   measurement station, open **Official SwissMetNet station map** (translated
   into your HA/flow language). The official measurement-network page should
   open. Return to HA and cancel without changing your settings. If your entry
   uses Open-Meteo current weather, it has no weather-station field; mark this
   route not applicable.
3. **Check setup help without adding an entry.** Start Add integration →
   MeteoSwiss, choose MeteoSwiss STAC API and a measured-pollen station, then
   continue to the weather-station form. Check its map link and cancel the
   unfinished flow. Do not save another integration entry.
4. **Check normal operation.** Your intended weather/pollen/forecast places,
   measurements and forecasts should remain. With a valid saved forecast
   selection, no new forecast-configuration repair should appear. Optional
   missing provider values are not by themselves a failed installation.
5. **Only if already present:** follow an actual invalid-location notice under
   Settings → System → Repairs and the [repair guide](REPAIRS.md). Confirm a
   valid point or explicit base reset; the notice should clear. If no notice
   exists, record **not applicable**. Do not edit HA storage or damage a saved
   selection to manufacture one.

Record the installed HA/integration versions, whether each applicable link
opened, and whether intended places/values remain correct. Report an actual
unexpected repair separately from a temporary source outage. Tests already
cover the damaged-selection lifecycle, all four translations, URL placeholders
and failure/recovery; no forced outage or new 24-hour waiting period is needed.

Cancel test forms and close external map tabs when finished. If you deliberately
saved other location choices, restore the intended ones. This checklist does
not publish a stable release or replace previous acceptance evidence.
