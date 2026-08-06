# V32.8.0 — Adaptive Intelligence

V32.8.0 introduces a capped, advisory learning layer over the governed static recommendation model. It compares static and adaptive scores, measures confidence calibration, ranks strategies using observed outcomes and capital efficiency, and proposes the next capital allocation in portfolio context.

Adaptive weighting remains dormant until a strategy has at least eight completed and judged outcomes. When active, historical influence is capped at 25% and cannot change production settings, bots, deals, orders or balances. Manual approval remains mandatory.

The included Build System 1.1 maintenance update restores `docs/diagnostics.json` after acceptance runs so routine diagnostics timestamps no longer appear as source changes.
