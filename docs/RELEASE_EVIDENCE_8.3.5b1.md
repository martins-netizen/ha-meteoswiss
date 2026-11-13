# 8.3.5b1 publication evidence

**Evidence version:** 1.0 · **Checked:** 13 November 2026

[8.3.5b1](https://github.com/martins-netizen/ha-meteoswiss/releases/tag/8.3.5b1)
is a published test prerelease. Stable **8.3.4 / ID 437853341** remains latest.

| Check | Observed result |
|---|---|
| Release | ID **444798178**, published **13 November 2026, 22:21:10 UTC** (23:21:10 CET); `draft=false`, `prerelease=true`, immutable |
| Tag and source | `8.3.5b1` resolves directly to approved regular merge **af1220249e672bd8a6742c73022a7c42aca2f20a**, tree **d96f2c05190eb24050a7d61e3cb13f86f808bb92** |
| Packaging checks | PR #108: ten exact-head and nine actual merge checks successful; both HA 2026.11.0/2026.11.1 jobs passed 2,715 tests plus 83 subtests and all strict gates |
| Component boundary | 42 non-version component files identical to reviewed source **b144a0b73d81358f27fd6ecd89a47120c8a0a1b9**; manifest.json/version.py checked separately as 8.3.5b1 |
| Approved English body | Exact byte match, SHA-256 **d2764b620bc7a2ebcf4907cdf937c2df0c38a3cc626b07c0d114c9e21c4c3919** |
| First invocation | V1.8 receipt: `published_and_verified`, `release_created=true`, `release_write_attempted=true`; verified at 22:21:21 UTC |
| Second invocation | Same release ID, URL, tag and publication time; `already_published_and_verified`, `release_created=false`, `release_write_attempted=false`; verified at 22:21:48 UTC |
| Independent readback | Exactly one matching release; tag, target commit, full body, flags and latest-stable endpoint agree with both receipts |
| Existing publications | All sixteen older tags unchanged; prior release IDs, bodies and publication flags retained |
| HA effects | Both receipts report no HA writes, restart or device/service calls; operator installation and acceptance remain pending |

The second invocation was harmless: it verified the existing matching release
without another write. No deletion, retagging or publication retry is needed.
The fixed publisher and historical release bodies remain unchanged.

The [focused acceptance protocol](ACCEPTANCE_8.3.5b1.md) is the next separate
operator step after installation approval. Existing arithmetic wind history
must first be exercised on an existing test/restored copy with a protected
backup. A software version rollback alone does not undo Recorder metadata.
No new operator history/registry read or HA acceptance is claimed here.
Full Gold, historical applicability and independent security/architecture
review remain open. Stable 8.3.5 promotion requires separate accepted-beta
evidence and its own reviewed version-only package.
