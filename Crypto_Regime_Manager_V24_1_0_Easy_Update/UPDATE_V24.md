# Crypto Regime Manager V24.1.0

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

## V24.1 integration amendments

- Corrects Coin Discovery navigation styling on mobile.
- Runs the research-only discovery scanner after every scheduled replay update.
- Publishes and commits `coin_discovery.json` and `coin_universe.json` with the normal workflow.
- Adds explicit last-scan status, duration, source and error reporting.
- Replaces the misleading browser-side scan command with accurate automatic-schedule information.
- Changes dashboard refresh controls to show visible loading and completion feedback.
- Clarifies that browser refresh retrieves the newest published results; it does not directly trigger a private GitHub Actions job.
- Retains all safeguards: no automatic production coin additions, live bot changes or DCA changes.
