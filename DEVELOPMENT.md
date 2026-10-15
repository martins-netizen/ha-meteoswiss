# Development branch

This repository is a fork of
[`LNKtwo/ha-meteoswiss`](https://github.com/LNKtwo/ha-meteoswiss).

The `development` branch is an integration branch for changes that have been
tested locally while the corresponding upstream pull requests are pending.

Branch policy:

- `main` stays aligned with upstream `LNKtwo/main`.
- `fix/*` and `feat/*` branches stay focused on individual upstream pull requests.
- `development` combines the locally validated changes for continued testing
  and development.
- Own prereleases may be tagged from approved, tested `development` commits;
  they remain clearly identified as fork releases, not upstream releases.
- Changes should remain small and reviewable so they can be proposed upstream
  independently.
- This branch is not presented as an official MeteoSwiss integration release.

See `docs/ARCHITECTURE.md` and `docs/MAINTENANCE.md` for data contracts,
localisation, compatibility checks and release acceptance.

If upstream accepts a change, the integration branch should be rebuilt or
rebased on the updated upstream history rather than carrying duplicate patches.
