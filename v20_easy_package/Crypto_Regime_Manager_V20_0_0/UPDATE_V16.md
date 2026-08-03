# V16.0.0 — Decision Cockpit

This milestone accelerates development by combining several presentation and operational-intelligence improvements into one release while leaving all trading and forward-validation behaviour unchanged.

## Acceptance criteria
- Existing V15.3 simulations produce the same deal outputs when run on the same candle data.
- Forward validation uses only candles at or after each immutable candidate start.
- Research assets remain excluded from production opportunity ranking.
- The cockpit explains each asset's decision, blockers and next manual action.
- No automatic live execution, bot modification, DCA change or exit-policy change is possible.
