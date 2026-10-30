# 8.3.3 — native icons and translated update errors

**Notes version:** 1.1 · **Status updated:** 30 October 2026

**Published and accepted:** release **429354633**, published **30 October 2026
at 18:21:55 UTC**, from **3d4fad2330c89f134eba208e8b2db55705177e7d**,
latest stable and immutable. The operator subsequently confirmed **8.3.3
installed and normal operation OK**, closing the [short update](ACCEPTANCE_8.3.3.md).
See [source/publication/check evidence](RELEASE_EVIDENCE_8.3.3.md).
The originally published body below is retained verbatim; its publication and
short stable update are now complete.

This community fork builds on [LNKtwo/ha-meteoswiss](https://github.com/LNKtwo/ha-meteoswiss)
and retains its MIT licence and attribution. It is not an official MeteoSwiss
product.

## What changes from stable 8.3.2

- **Native entity icons.** The 24 previous custom symbols now use HA's
  icons.json mechanism for measured/modelled pollen, today/tomorrow forecast
  summaries, calculated HGT and the three warning binary sensors. The symbols
  stay the same, including tree outlines for measured hazel/oak. Personal names
  and icons retain precedence; other entities retain their domain/device-class
  defaults. See [icon resolution](ICON_TRANSLATIONS.md).
- **Source errors in four languages.** All 21 source-update failure sites use
  19 stable exception keys in German, English, French and Italian. Messages
  distinguish the affected source without private locations, URLs or raw
  provider exceptions. Retry, availability and recovery boundaries remain.
  See [translated errors](EXCEPTION_TRANSLATIONS.md).

Default icons are resolved by the frontend and may no longer appear as an
`icon` attribute in every backend state. Automations should use entity values
and states. Explicit dashboard icons continue to take precedence.

This update retains sources, independent locations, polling, measurement
values, entity/statistic identities, personal names and configured icons.
It performs no settings migration or registry rewrite and adds no provider,
dashboard redesign or device action.

## Accepted beta and version-only promotion

**8.3.3b1 / ID 429321251** was published on **30 October 2026 at 17:42:37 UTC**
from **d9fbc3fd49220b0ecc019d2babe0c173c46986f5**, tree
**80802d36d46fd21ee2d5b04c981ce657b6bbf87f**. Publisher receipt/log and
independent release/tag/notes/latest checks agree; all twelve earlier tags
were unchanged. The operator subsequently reported **icons/personal choices OK
and normal operation OK** on **HA Core 2026.10.4 / HA OS 18.4**. The
[acceptance record](ACCEPTANCE_8.3.3b1.md) preserves the scope and limits of
that report separately from automated evidence.

Stable packaging keeps **39 non-version files** of that 41-file component
identical. Only manifest.json/version.py become **8.3.3**. HACS/CH, minimum
HA, workflows, security guards, icons.json and the four **219-key** catalogues
are retained. English/source catalogue parity remains. No runtime addition
follows the accepted beta, and all thirteen earlier tags are preserved.

The beta's exact merge passed seven checks and **2,045 tests plus 83 subtests**
on each hosted HA 2026.8.3/2026.10.1 with **Python 3.14.10 / pip 26.2.2 /
certifi 2026.10.23 / UV_OFFLINE=true**. Historical HA uv pins remain explicit
unpatched offline compatibility exceptions. Stable packaging adds the eleventh
fixed publication test profile; its own exact-head and actual-merge checks
remain separate gates. See [readiness](RELEASE_READINESS.md).

## Short stable update

After publication is confirmed, actually Download/Redownload **8.3.3** through
the existing maintained-fork HACS entry, then restart HA once. Refresh repository
information first if needed; refreshing alone does not download files.
Keep the configured entry and existing backup, then confirm the installed
version and continued normal operation using the
[short stable protocol](ACCEPTANCE_8.3.3.md).

The accepted beta icon check and earlier settings, clean-install and restore
checks stay closed. No deliberate source failure or new blanket 24-hour wait
is needed. Published stable **8.3.2** remains the recovery version; redownload
it from the same repository and restart once if this update regresses.
Software rollback retains entries/history and does not undo deliberately
changed location choices.

## Publication and remaining quality work

**publish_meteoswiss_833_stable_v1.6.sh** continues the fixed Stable V1.5
profile. It requires the approved protected development merge, version-only
accepted-beta boundary, successful checks and their expected apps, previous
stable **8.3.2 / ID 426633496**, accepted beta **8.3.3b1 / ID 429321251** and
all thirteen older tags. Its only remote write creates stable **8.3.3** with
draft=false, prerelease=false and make_latest=true. Latest must be the previous
stable before creation and the exact new release afterwards. Matching retries
only verify; conflicts stop. No HA connection, restart or device call occurs.
See [publishing](PUBLISHING.md#stable-833-prepared).

Native icons and translated update failures now have published-beta evidence;
the [quality matrix](QUALITY_SCALE.md) retains diagnostic defaults, device
metadata/classes, stale grouping and rule-specific exemptions as separate
remaining work. This release does not complete Gold or confer an official HA tier.

Use the [fork issue tracker](https://github.com/martins-netizen/ha-meteoswiss/issues)
for problems, or [private vulnerability reporting](https://github.com/martins-netizen/ha-meteoswiss/security/advisories)
for confidential reports.
