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


## V12 Automatic Research Pipeline
Pending one-variable experiments are executed automatically during the main workflow and published to `docs/pipeline.html`. Production changes remain manual.

## V33 unified command state

`docs/command_state.json` is the canonical presentation snapshot for the Trading Command Centre. It references rather than replaces the governed Market, Operating State, Capital, Portfolio, Recommendation, Adaptive, Outcome and Cloud Reliability outputs. All decisions remain read-only and require manual approval.


## V40 Unified Core Managers
Operational plumbing is centralised behind canonical managers for generated outputs, workflows, releases, diagnostics and UI validation. This reduces duplicated logic and regression risk.

## V40.1 Synchronisation & Workflow Efficiency
Health publication now uses semantic material-change detection, Pages verifies the deployed version, and Synchronisation Intelligence compares repository, live-site, Actions and data health without changing remote state.

## V41 canonical presentation layer
V41 defines `docs/index.html` as the canonical decision workspace and `docs/design-system.js` as the single navigation owner. `config/page_policy.json` classifies canonical, drill-down and legacy pages. UI health validates visible release labels, duplicate/legacy navigation, shared design assets and quote/base-asset presentation. Runtime health engines only treat the four current GitHub workflows as active operational sources.
