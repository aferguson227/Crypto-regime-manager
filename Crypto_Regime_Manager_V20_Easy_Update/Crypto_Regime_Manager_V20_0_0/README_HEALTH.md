# Version 5.3 — Strategy Health Monitor

Version 5.3 adds a rules-based health score for TEL and TAO. It uses the latest 90 days of replay performance, recent drawdown, recent trade duration, unresolved replay-position stress and candle freshness.

## Status bands

- 85–100: Excellent
- 70–84: Healthy
- 50–69: Watch
- 0–49: Review

The score is a monitoring indicator, not a forecast or probability of profit. It never changes bot settings or closes an existing deal.

## Updated files

- `scripts/multi_coin_sync_backtest.py`
- `docs/index.html`
- `docs/settings.html`
- `.github/workflows/multi-coin-update.yml`
- `config.json`
- `VERSION`

## New files

- `docs/health.html`
- `docs/health_history.json`
- `README_HEALTH.md`

After pushing the release, run **Update Crypto Regime Manager** once. The workflow will regenerate `strategies.json`, append the first health-history records and publish the health page.
