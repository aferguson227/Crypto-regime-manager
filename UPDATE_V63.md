# CRM V66.0.0 — Portfolio Capital & Live Execution Architecture

V63 moves CRM from single-bot conservative allocation toward a read-only multi-bot portfolio architecture while preserving the native execution hard lock.

- Portfolio Capital Manager 2.0 separates hard exchange commitments, theoretical full-ladder reserve, prudent active-DCA contingency and portfolio safety buffer.
- Candidate allocation uses the prudent multi-bot pool while retaining worst-case DCA headroom as a visible safeguard.
- Fast Live Truth is separated from research/backtesting and is designed for a frequent operational loop.
- Live Strategy Revalidation continuously asks whether an existing live strategy would still be selected today, but never mutates an active deal mid-trade.
- Research Integrity, Accounting Integrity and Execution Readiness are separated from System Health.
- Kraken evidence acquisition publishes explicit diagnostic stages.
- Deployment language is more specific and exact DCA recommendations remain gated by unseen validation.
- Native KuCoin execution remains HARD LOCKED.
