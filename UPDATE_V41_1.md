# V45.0.0 — Data Completeness & Execution Independence

- Direct read-only KuCoin account provider for free USDT and capital state.
- 3Commas remains the live bot/deal provider; Starter-plan balance quota is no longer a capital dependency once KuCoin read-only access is configured.
- Dashboard DCA comparison is Live vs Recommended only.
- Missing recommendations keep the live setting with an explicit insufficient-evidence explanation.
- Market breadth uses the canonical breadth_score and evidence coverage.
- Synchronisation and cloud watchdog states are cause-specific and self-correcting.
- Execution-provider abstraction includes Hummingbot and KuCoin-direct future providers, both disabled.
- No live write action is enabled in V41.1.
