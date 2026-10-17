# App v3 warning source and verified catalogue

The warning client uses
`https://app-prod-ws.meteoswiss-app.ch/v3/plzDetail?plz={postcode}00`.
The catalogue below was verified on **17 October 2026** against the signed
MeteoSwiss Android app **3.6.0**, build **3060003**, package
`ch.admin.meteoswiss`. API v3 and the app version are separate version numbers.

## Numeric warning families

| `warnType` | English | German |
|---:|---|---|
| 0 | Wind | Wind |
| 1 | Thunderstorm | Gewitter |
| 2 | Rain | Regen |
| 3 | Snow | Schnee |
| 4 | Slippery Roads | Strassenglätte |
| 5 | Frost | Frost |
| 6 | Thaw | Tauwetter |
| 7 | Heat | Hitze |
| 8 | Avalanches | Lawinen |
| 9 | Earthquakes | Erdbeben |
| 10 | Forest Fire | Waldbrand |
| 11 | Flood | Hochwasser |
| 12 | Drought | Trockenheit |

All thirteen labels ship in German, English, French and Italian. These are
warning families, not a list of currently active events. **Starkregen** belongs
to Rain, **Sturm** to Wind, and **Schneefall** to Snow; this catalogue does not
assign separate numbers to those event descriptions. Preserve `warn_level`,
validity and the provider's full `description` rather than deriving severity
from a family name or translating away event-specific detail.

The app calls type 5 **Frost**. A captured type-5 event described ground frost;
that description remains intact, but does not establish a separate numeric
ground-frost family. Type 6 has the resource label **Thaw**. Its icon slot is a
placeholder and the examined weather-group list skips 6. Current issuance was
not observed; the client recognizes it if actually supplied, without inventing
a warning or claiming that the provider currently issues it. Future unknown
integer types remain visible as `Unknown (number)` with their original code.

## Provenance of the numeric mapping

The APK was obtained from a public mirror, verified statically and never run.
Its publisher certificate matches MeteoSwiss's own
[Android asset links](https://www.meteoschweiz.admin.ch/.well-known/assetlinks.json).
Google Android SDK Build Tools 35.0.0 `apksigner` verified APK signature schemes
v2 and v3, plus its source stamp. The analysed bytes are fixed by these hashes:

- APK SHA-256: `a76f4a1bc8fbd41509e0fc43cf0a08c9f0ce27e802def596d4c15939bae6082a`.
- Signer SHA-256: `07dbd58510fa5a8d7f02aafa88960dac64508a26a3b29fabf5d5a26e95490b60`.
- Public mirror route: `https://d.apkpure.com/b/APK/ch.admin.meteoswiss?version=latest`.
  That route may return a different version later; the hash identifies this one.
- [Official app listing](https://play.google.com/store/apps/details?id=ch.admin.meteoswiss).

The `gefahren_typen` and `gefahren_typen_titles` resource arrays have 13
positions. The label helper `Lwn2.o` uses its first integer directly as the
array index (`const` resource at byte offset 8; `aget` at 44). In the local
forecast path `Lzm4.o`, that argument comes from `WarningEntry.component1()`,
which reads `warnType`, and reaches the helper unchanged at offset 320.
A separate home-screen path also reads raw `warnType` for icon indexing.
This establishes a code-to-label relationship, rather than assuming that menu
order proves the API numbers. No APK or decompiled third-party source is
redistributed in this repository. German wording is the integration's
translation of the English base resources, not a claim to reproduce an
unexamined German language split verbatim.

## Captured v3 response and drought cross-check

At **2026-10-17 06:20:09 UTC**, public reads for postcode 8302 showed:

- `v1/plzDetail?plz=830200`: only type 10, level 2, region 2600.
- `v3/plzDetail?plz=830200`: type 12, level 4, region 42, plus the same
  field-for-field type-10 object. Both ongoing warnings omit `validTo`.
- [The app drought feed](https://app-prod-static.meteoswiss-app.ch/v1/warnings/v5/drought_de.json)
  contains `DROUGHT_42` with the same type, level, start and text as v3.
  Its geometry identifies that region as **östliches Mittelland**.
- [The app overview](https://app-prod-static.meteoswiss-app.ch/v1/warnings/v5/all_overviews.json)
  contains a separate drought layer and type-12 summary.

The original full v3 response SHA-256 is
`ae7fb419817d3a92b8f395d4cda397f38b65c6af238a272e1955ea157795405e`.
`tests/fixtures/warnings_v3_830200.json` retains its unmodified warning fields
and capture provenance, omitting unrelated forecasts. Tests use this capture
offline. The separate drought product's `capTime` was 05:19:14 UTC, which is
not the download time or a new validity boundary.

Region numbers are scoped to their hazard family: `DROUGHT_42` is not an
unqualified universal region 42. The client relies on the provider's postcode
selection and does not join these numbers to an old local region table.

There is **no silent v1 fallback**: doing so would hide the demonstrated drought
warning. Transport or malformed-data failures leave sensors unavailable;
last-good data must not be presented as current or mistaken for an all-clear.
Existing timeout, retries, lifecycle and identity contracts still apply.

## Migration and limits

The legacy integration labelled **4 as Wind**. The verified catalogue instead
has **0 = Wind** and **4 = Slippery Roads**. Before installing this change,
read the actual dashboard, awning and automation consumers. A filter intended
for wind, thunderstorms and rain must select **[0, 1, 2]**; an old **[1, 2, 4]**
selects slippery roads instead of wind. Review active and upcoming checks,
including lead-time checks. Change only filters whose intent is confirmed;
never replace every occurrence of `4`. Also review hardcoded labels for type 5.

Entity IDs, unique IDs, statistics and warning `alert_id` construction are
unchanged. Installing the integration does not edit dashboards or automations.
Consumer migration, backup, rollback and live verification are separate
deployment steps. After installation, compare provider and HA active/upcoming
types, levels, descriptions and validity; verify failure and recovery handling.

The evidence establishes the catalogue in app 3.6.0 and the captured v3
response. It does not establish every historical v1 version, current issuance
of every family, a formal API stability guarantee, or a certified warning
system. Later app/API changes need a fresh source comparison.
