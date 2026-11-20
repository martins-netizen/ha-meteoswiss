# MeteoSwiss 8.3.6 package evidence

The [8.3.6 release notes](RELEASE_8.3.6.md) describe the changes since stable
8.3.5. This package promotes the integration tested in 8.3.6b1.

| Stage | Verified source and scope |
|---|---|
| Published beta | [8.3.6b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.6b1), release 452371818, signed package commit `ceec7a8b23a5669f20677ef67a87b31b2b523d5f` |
| Beta installation | The operator confirmed 8.3.6b1 running on Core 2026.11.2 and reported normal operation. The station display and the hourly and daily forecast displays were visible. |
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

## Stable package and publication

The approved head of [PR #150](https://github.com/martins-netizen/ha-meteoswiss/pull/150)
was `c1e000505359f5b81a90b24b0f01558581d95c28`. The signed squash merge and
tag `8.3.6` point to `85d74d7dbb892f71294a5ff8546633410b1c8fdb`. Both commits
have tree `910ed1b234e9287fa76e3542995601cd9596c0c0`.
All ten PR checks and all nine merge checks passed. The
[merge CI](https://github.com/martins-netizen/ha-meteoswiss/actions/runs/44779732102)
passed 3,888 tests and 83 subtests on each of Core 2026.11.0 and 2026.11.2.

GitHub published [8.3.6](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.6)
as the latest stable release on 20 November 2026 at 17:20:55 UTC (18:20:55 CET),
release ID `452980828`. The publisher removed the page title from the
[approved English notes](RELEASE_8.3.6.md) and expanded relative links to point
at the signed merge. The published body matched that output byte for byte
(2,762 UTF-8 bytes including the final newline, SHA-256
`b4dda56fb7318e853bd06ff97389519c18cdfbc963ba40106c73923d25b8ce7b`).
All 25 earlier release and tag records matched the pre-publication inventory.

After publication, the operator confirmed upgrading from 8.3.6b1 to stable
8.3.6. The station weather and forecast observations above were made on 8.3.6b1.
