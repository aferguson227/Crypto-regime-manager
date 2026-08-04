# Crypto Regime Manager V29.0.0 — Strategy Factory

V29 turns coin discovery into a complete research pipeline while retaining manual production safeguards.

## Included
- Mobile discovery spacing fix: the DCA proposal tile and warning panel no longer overlap.
- Consistent navigation: Dashboard, Cockpit, Research, Discovery, Backtest Lab, Validation, Queue, Data, More.
- New **Kraken Backtest Lab** with private browser-side CSV inspection and 4-hour conversion.
- Universal Python importer for Kraken, KuCoin, Binance, Coinbase, TradingView and generic OHLCV CSV files.
- Timeframe detection and safe conversion from 15m, 30m, 1h, 2h and 4h to canonical 4h candles.
- Generalised fee-aware DCA replay and bounded parameter optimisation for any normalised coin.
- Strategy lifecycle: Discovered → Backtesting → Optimising → Forward Validation → Paper Trading → Production → Monitoring → Retired.
- Cloud workflow consumes import and backtest registries before rebuilding unified decision intelligence.
- Discovery and backtests can prioritise research, but cannot alter 3Commas or promote a strategy automatically.

## Using Kraken files
1. For immediate private inspection, open **Backtest Lab** and select a CSV. Processing happens in the browser.
2. Download the normalised 4h CSV if required.
3. For cloud backtesting, place CSV files in `data/imports`, commit and run the autonomous refresh workflow.
4. Review `docs/backtest_lab.json`; promising candidates still require independent forward validation and manual approval.
