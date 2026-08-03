# Version 7.2 — Ranked Hypothesis Engine

V7.2 automatically diagnoses the unresolved SUI Candidate A trade, applies five one-variable experiments to the actual problem regime, ranks them, and rejects weak hypotheses. Results are post-hoc diagnostics only. No candidate can alter production or start a live SUI signal.

Hypotheses tested:
1. Close at or above EMA200.
2. EMA200 flat or rising.
3. ATR(14) not expanding versus 24 hours earlier.
4. No more than two consecutive bearish candles.
5. Close at or above EMA50.

The ranking weighs net improvement, duration reduction, drawdown, trade retention, and whether the unresolved problem trade changes.
