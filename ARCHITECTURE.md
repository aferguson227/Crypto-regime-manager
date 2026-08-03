# Crypto Regime Manager V6.1 architecture

## Core engine

- `scripts/core/engine.py` — KuCoin synchronisation, indicators, regimes, DCA replay, health scoring and opportunity ranking.
- `scripts/multi_coin_sync_backtest.py` — stable compatibility entry point used by GitHub Actions.

## Integrations

- `scripts/integrations/threecommas.py` — read-only RSA-authenticated 3Commas synchronisation.
- `scripts/threecommas_sync.py` — stable compatibility entry point used by GitHub Actions.

## Tools

- `scripts/tools/generate_3commas_rsa_keys.py` — local RSA key generation.
- `scripts/generate_3commas_rsa_keys.py` — compatibility entry point.

## Dashboard

- `docs/index.html` — portfolio dashboard.
- `docs/health.html` — strategy health.
- `docs/intelligence.html` — opportunity ranking.
- `docs/settings.html` — active strategy settings.

## Persistent local folders

Do not overwrite or delete these during upgrades:

- `data/` — continuously growing KuCoin candle history.
- `threecommas_private_setup/` — local RSA private material; never committed.
- `.git/` — Git repository metadata.


## V7 research assets
Assets may set `production_status: research`. Research assets use the same market-data and replay engine but are excluded from portfolio rankings and are assessed against explicit promotion gates.


## V9 Evidence layer
Qualified SUI hypotheses are replayed against the frozen TEL, TAO, and SUI baselines. Results are published in `evidence_library` and shown on `docs/evidence.html`.


## V11 Context & Trait Engine
- `context_traits` in `strategies.json` summarises asset traits by rule family and observed regime.
- `docs/traits.html` displays traits, context evidence, a research tree, and next experiments.
- Traits remain research-only and cannot alter production settings.
