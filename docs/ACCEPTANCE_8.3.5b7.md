# 8.3.5b7: normal update and read-only check

**Protocol version:** 1.0 · **Updated:** 18 November 2026

Use this once after choosing the published **8.3.5b7** test package. Confirm
availability in [the release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).
Keep the existing entry, station and options. Minimum Core is 2026.11.0;
2026.11.2 already meets it. A preparation record or repository refresh does
not establish that b7 was installed.

1. Use **Settings → Marketplace** to download/update **8.3.5b7** and complete
   the normal update restart once. Verify the installed version is **8.3.5b7**. Keep your
   normal protected recovery backup; no new migration, station switch or entry
   recreation is part of this check.
2. Check the existing weather/forecast and ordinary station displays after
   normal refresh. Existing measured HGT and precipitation statistics should
   retain their usual values or their explicit source/status indication where
   configured. Previously accepted HGT cleanup and availability stay complete;
   there is no second historical-data audit.
3. If a normal UTC-hour transition or an upcoming warning boundary is observed
   during ordinary use, check that the displayed forecast/warning follows it.
   Warning feeds and future warnings may naturally be absent. Do not create a
   fake warning, force an outage, press **Set state**, or change polling to
   manufacture this observation. Precise boundary/cancellation cases have
   native regression evidence.
4. Optionally download diagnostics once and inspect the JSON locally. Saved
   location fields should be redacted and unknown saved settings omitted;
   runtime summaries retain roles/status, valid timestamps and aggregate counts.
   The retired-HGT issue must not export its old redundant station-ID list.
   Do not infer that ordinary state attributes/cards are globally anonymized.
   Keep the downloaded file private; do not post raw diagnostics, coordinates,
   entry IDs, personal titles or logs publicly. The complete envelope and
   persisted-notice cases are primarily covered by native tests.
5. Report the installed version, whether normal operation looks correct, and
   only the category of any new repair or error. If an optional UV/catalogue
   outage/recovery happens naturally, its generic INFO transition may be
   reported; creating an outage or enabling debug logging is unnecessary.

No initially disabled diagnostic entity needs enabling. No repeated cleanup,
entry removal, statistics deletion, four-language browser round or manual
exercise of every failure is required. Existing explicit obsolete-forecast
repairs for new upgrading users retain their
[separate confirmation boundary](UPGRADING_8.3.5.md).

This confirms only the installed package and observed normal behavior. Source
checks establish the precise timing/privacy regressions; this short report is
not a complete database audit, provider-retention review or security
certification. [Notes](RELEASE_8.3.5b7.md) and
[dated evidence](RELEASE_EVIDENCE_8.3.5b7.md) keep those scopes separate.
