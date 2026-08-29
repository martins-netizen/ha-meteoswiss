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
- Changes should remain small and reviewable so they can be proposed upstream
  independently.
- This branch is not presented as an official MeteoSwiss integration release.

If upstream accepts a change, the integration branch should be rebuilt or
rebased on the updated upstream history rather than carrying duplicate patches.
