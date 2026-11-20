# MeteoSwiss 8.3.6 package evidence

The [8.3.6 release notes](RELEASE_8.3.6.md) describe the changes since stable
8.3.5. This package promotes the integration tested in 8.3.6b1.

| Stage | Verified source and scope |
|---|---|
| Published beta | [8.3.6b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.6b1), release 452371818, signed package commit `ceec7a8b23a5669f20677ef67a87b31b2b523d5f` |
| Existing installation | The operator confirmed 8.3.6b1 running on Core 2026.11.2 and reported normal operation. The station display and the hourly and daily forecast displays were visible. |
| Stable package base | [PR #149](https://github.com/martins-netizen/ha-meteoswiss/pull/149), signed merge `ea278684dfccb6770e32cad1cdf51e7e08fb7614`, tree `6430dd70c4b8c98655640021ecac980a7f127a46` |

Between the beta tag and #149, only seven test files changed. The tests wait
for optional background fetches before checking results. All nine checks triggered by
the merge passed. The [merge CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44694358568)
ran 3,854 tests and 83 subtests on each of Core 2026.11.0 and 2026.11.2.

Of the 52 files under `custom_components/meteoswiss`, 50 match the beta
byte for byte. In `manifest.json` and `version.py`, the version changes from
`8.3.6b1` to `8.3.6`. The existing beta sight check therefore covers the
same integration behavior. No new migration or operator observation period
is part of this promotion.

The [publishing guide](PUBLISHING.md) covers the separate package approval
and publication steps. Stable availability can be checked in the
[release catalogue](https://github.com/martins-netizen/ha-meteoswiss/releases).
