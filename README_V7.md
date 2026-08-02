# Crypto Regime Manager V7 — SUI Research Mode

V7 preserves TEL and TAO as production/advisory assets and adds SUI as a frozen research candidate.

## SUI forward-test rules
- Data source: KuCoin public SUI-USDT 4-hour candles.
- Forward test begins 2026-04-01.
- Earlier fetched candles are indicator warm-up only.
- SUI is excluded from portfolio rankings, best-opportunity selection, production capital totals and 3Commas instructions.
- Passing promotion gates requires a later manual review; the app never auto-promotes SUI.

## Updating an existing V6.1 repository
Keep `.git`, `threecommas_private_setup`, and the existing `data` folder. Copy the V7 code folders/files over the project, then copy only `data/SUIUSDT_4H.csv` into the existing data folder. Do not replace TEL or TAO candle files.
