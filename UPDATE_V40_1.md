# V40.1.0 — Synchronisation & Workflow Efficiency

V40.1 reduces unnecessary automation noise and makes synchronisation visible.

- Health & Self-Heal commits only material state changes; volatile timestamps alone do not publish.
- Existing hourly Data Refresh also collects GitHub Actions telemetry, avoiding a separate telemetry publication cycle.
- Pages verifies the live `version.json` after deployment.
- Engineering Command Centre shows GitHub main, live website, Actions, 3Commas and application-refresh synchronisation.
- GitHub Actions intelligence treats superseded failures as historical rather than active incidents.
- Engineering Package 2.2 includes synchronisation and material-change policies.
- Build System 4.1 validates material-change and synchronisation managers.

Trading remains read-only and all live trading changes remain manual.
