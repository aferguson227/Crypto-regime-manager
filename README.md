# Crypto Regime Manager V6.1

V6.1 reorganises the project into a modular core without changing the live TEL or TAO strategy rules.

- Shared strategy and replay engine: `scripts/core/engine.py`
- Read-only 3Commas integration: `scripts/integrations/threecommas.py`
- Local security tools: `scripts/tools/`
- Dashboard pages: `docs/`

The package intentionally excludes `data/`. Keep your existing candle-history folder unchanged during the upgrade.

See `UPDATE_V6_1.md` for installation steps and `ARCHITECTURE.md` for the project layout.
