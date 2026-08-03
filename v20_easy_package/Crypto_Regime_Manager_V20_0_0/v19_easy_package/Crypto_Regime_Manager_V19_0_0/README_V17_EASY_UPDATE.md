# Crypto Regime Manager V17.0.1 — Easy Update

This maintenance release fixes the displayed version and provides a low-effort, state-preserving installer.

## Fixes included

- The dashboard reads the release number from `docs/version.json`, so an older generated `strategies.json` cannot make it display V16.
- Cockpit displays V17.0.1.
- `VERSION`, `config.json`, release metadata and bundled dashboard output agree on 17.0.1.
- Existing trading logic, DCA settings, entry/exit rules and forward-validation behaviour are unchanged.

## Installation

1. Extract the ZIP.
2. Double-click `INSTALL_V17_EASY.bat`.
3. Select your existing Crypto Regime Manager project folder.
4. Wait for the success message.
5. Open GitHub Desktop, review the changes, commit and push.

The installer preserves `.git`, `data`, `threecommas`, candidate registry, health history, generated strategy results, deal history and 3Commas snapshots. It also creates a timestamped backup of the preserved state files.
