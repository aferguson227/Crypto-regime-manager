# Crypto Regime Manager V32.1.1

## Diagnostics and Acceptance Engine

V32.1.1 adds an observational diagnostics engine without changing trading logic or enabling any 3Commas write capability.

### Included

- `RUN_DIAGNOSTICS.cmd` one-click local acceptance run.
- Machine-readable `docs/diagnostics.json`.
- Dashboard `docs/diagnostics.html`.
- Redacted `CRM_Diagnostics_*.zip` export for support and review.
- Release, route, HTML asset, UTF-8, JSON, freshness, source, secret and read-only checks.
- Full test-suite and publication-validator execution in local mode.
- Optional automatic screenshots of primary routes using Microsoft Edge headless mode.

### Privacy

The export excludes `.env`, PEM and key files and refuses to include files containing secret-like material.
