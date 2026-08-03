# V7 update checklist

1. Fetch/Pull in GitHub Desktop.
2. Keep `.git`, `threecommas_private_setup`, and existing `data/TELUSDT_4H.csv` and `data/TAOUSDT_4H.csv`.
3. Copy `.github`, `docs`, `scripts`, `config.json`, READMEs and VERSION into the repository and replace existing code files.
4. Copy only the new `data/SUIUSDT_4H.csv` into the existing data folder.
5. Commit: `Add SUI research mode V7` and push.
6. Run `Update Crypto Regime Manager` once. The first run downloads KuCoin SUI-USDT history.
7. Confirm `data/SUIUSDT_4H.csv` is populated and `docs/strategies.json` contains SUI.
8. Open `research.html` and verify SUI says Research Only.
