# CRM V65.0.0 — Evidence Resolution & Accounting Baseline

V64 is a consolidation release focused on permanently resolving repeated pipeline states.

- Accounting Baseline closes the exhausted 730-day cost-basis investigation without estimating the unknown older transaction.
- Matched and future KuCoin realised P/L continues independently from the baseline.
- Cross-Exchange Continuation Resolver 2.0 forces Kraken-open cases into explicit terminal or diagnostic states using cached KuCoin 4h history.
- Research Integrity detects contradictory continuation states.
- Canonical KuCoin Service publishes one authoritative read-only data contract across CRM processes.
- Portfolio Capital Manager 2.0 now runs in the fast Local Agent before portfolio allocation.
- 3Commas is explicitly secondary monitoring; KuCoin remains authoritative.
- Terminal resolution state persists in CRM_Data across upgrades.
- Native KuCoin live-order submission remains HARD LOCKED.
