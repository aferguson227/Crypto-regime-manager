# Crypto Regime Manager V24.0.0

## Coin Discovery and advisory DCA research

V24 moves Coin Discovery from an eligibility-only foundation to a bounded research pipeline.

### Added

- Automatic KuCoin USDT universe screening using public exchange data.
- Liquidity, spread, volatility-fit, drawdown and trend scoring.
- Bounded 4-hour candle research for the strongest eligible assets.
- Ranked discovery candidates with clear evidence metrics.
- Advisory DCA proposals covering TP, safety-order deviation, safety-order count, volume scale and step scale.
- A mobile-friendly Discovery page with persistent Dashboard return navigation.
- Foundations for a later hypothesis generator when the current research library is exhausted.

### Permanent safeguards

- No automatic production additions.
- No automatic 3Commas changes.
- No automatic DCA changes.
- Full fee-aware replay required.
- Independent walk-forward validation required.
- Manual approval required.

### Run discovery

```text
python scripts/coin_discovery.py
```

The initial scan deliberately performs deep research on only the highest-liquidity eligible assets to protect API reliability. The limit can be adjusted in `config.json`.
