# Crypto Regime Manager V18.0.0

## Intelligent Research Platform

V18 preserves every V17 strategy, DCA setting, candidate fingerprint and forward-validation boundary. It adds:

- **Unified Workspace** (`docs/workspace.html`) combining the action queue, production assets, research assets and validation progress.
- **Historical Data Manager** (`docs/data.html`, `scripts/data_manager.py`) for safe KuCoin 4-hour refreshes.
- A simplified five-screen primary navigation while retaining every legacy page for auditability.
- The same read-only execution guardrails: no automatic bot, DCA or exit changes.

## Refresh data

```bash
python scripts/data_manager.py status
python scripts/data_manager.py refresh --all
```

## Upgrade

Use the included Easy Update installer. It backs up and preserves local state, `.git`, `data`, and `threecommas`.
