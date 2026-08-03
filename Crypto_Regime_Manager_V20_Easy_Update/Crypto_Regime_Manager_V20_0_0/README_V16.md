# Crypto Regime Manager V16.0.0

## Production milestone: Operational Intelligence

V16 consolidates portfolio ranking, entry permission, strategy health, candidate validation and research status into one explainable **Decision Cockpit**.

### Added
- `docs/cockpit.html`: mobile-first operating view.
- `operational_intelligence` in `docs/strategies.json`.
- Per-asset readiness, blockers, next manual action, data status and validation state.
- Portfolio-level alerts and explicit guardrails.
- V16 configuration principles in `config.json`.

### Preserved unchanged
- Candle indicators and regime classification.
- Production strategy and entry-filter logic.
- DCA ladders and exit behaviour.
- Historical simulations and deal accounting.
- Candidate fingerprints and immutable registry.
- Post-freeze evidence boundary and forward-validation gates.
- Research/production separation.
- Read-only 3Commas integration.

### Safety boundary
V16 does not authorise live execution and cannot alter bots, DCA settings, exits or candidate lifecycle stages.
