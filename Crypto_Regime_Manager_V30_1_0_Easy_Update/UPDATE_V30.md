# V30.1 Backtest Lab and ZIP Archive Update

- Restores the Backtest Lab dark theme, application font, readable text and card styling.
- Adds a page-specific CSS fallback so stale global styling cannot make the page unreadable.
- Corrects mobile spacing, navigation wrapping, lifecycle badges and floating controls.
- Accepts CSV and ZIP selections in the Backtest Lab with clear large-archive guidance.
- Adds safe local ZIP extraction for Kraken datasets, including nested CSV folders.
- Allows the training and Q1 validation inputs to be folders, individual CSV files or ZIP archives.
- Rejects unsafe ZIP paths and keeps archive processing local.
- Preserves UTC-aligned 4-hour normalisation, fee-aware research and manual promotion gates.
