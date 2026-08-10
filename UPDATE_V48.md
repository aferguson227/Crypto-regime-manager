# Crypto Regime Manager V61.0.0 — Persistent Recommendation Workflow & Live Trade Truth

- Local Agent no longer uses interactive rebase for generated JSON; remote changes trigger a regenerate-on-latest-main retry.
- V47 historical research outputs are now included in Local Agent material publication, fixing 0-bars/queued dashboard snapshots that were being restored after each run.
- Staged recommendations use stable asset identity and migrate earlier browser-saved recommendations. They appear near Live Portfolio with Remove and Review removal states.
- Background research remains automatic; a static GitHub Pages button cannot securely trigger code on the local PC, so Add to Recommended marks user interest rather than pretending to start a process that already runs automatically.
- Active trade hold time is recalculated from the actual opening timestamp in the browser.
- Trade Intelligence can reconstruct average entry from cost/quantity, obtain a current public KuCoin price, derive TP from the live bot TP percentage, and calculate distance-to-TP/open P&L when sufficient evidence exists.
- Realised P/L is never fabricated without complete closed-fill cost basis.
- Refresh is renamed Refresh view to distinguish reloading published state from the independent Local Agent and cloud collectors.
- Universal mobile-safe typography and sentence/title formatting are applied across status/value cards.
