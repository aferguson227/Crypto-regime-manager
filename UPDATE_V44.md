# Crypto Regime Manager V45.0.0 — Autonomous Diagnostics & Regime Intelligence

V44 makes the Operations Centre proactive instead of requiring routine manual checks.

## Autonomous operations
- Local Agent target cadence changes to 15 minutes while the PC is available.
- Quick diagnostics run automatically each agent cycle; deeper health checks run at most hourly.
- `CRM_CHECK.cmd` remains as the single manual diagnostic command when explicitly wanted.
- Refresh presentation uses **Current / Refresh due / Attention** rather than generic "stale" wording.
- Human-readable ages include units and expected cadence.

## Global market intelligence
- Adds a universal market regime derived from current KuCoin BTC trend, breadth, trend and volatility.
- Historical Kraken BTC/XBT evidence contributes only when it exists; missing evidence remains explicit.
- Asset-specific regimes remain authoritative for individual bot selection.

## Candidate economics and optimisation
- Recommended Bots show Q1 validated return on maximum capital, deal count and average hold time as historical evidence, not a profit forecast.
- "Suggested pilot" is renamed **Suggested initial allocation**.
- A candidate optimisation queue tracks regime-profile work automatically. Fresh multi-regime backtests are only marked runnable when comparable raw Kraken archives are configured locally.

## Coin memory and change briefing
- Adds a persistent Coin Registry so SUI, TAO and every researched candidate remain visible even when not currently recommended.
- Adds a Recommendation Timeline combining bot recommendations and coin lifecycle changes.
- Global-regime and meaningful coin-state changes become material Decision Inbox events and can appear in the opening briefing.

## Safety
V44 remains advisory/read-only. It does not start/stop/edit bots, place/cancel orders, transfer funds, withdraw assets or alter secrets.
