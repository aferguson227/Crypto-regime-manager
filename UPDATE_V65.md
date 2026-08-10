# CRM V67.0.0 — Live Portfolio Truth & Pipeline Consistency

- Open P/L is marked from the current public KuCoin level-1 price against the reconciled position quantity/cost basis and carries a pricing timestamp.
- The operational Local Agent cadence moves from 15 minutes to 5 minutes; heavyweight research remains isolated.
- Canonical KuCoin service is authoritative for system-health credential/data consistency.
- Degraded-but-usable KuCoin collectors no longer automatically become root system failures.
- Cross-exchange continuation terminal states close the permanent waiting loop. Missing independent Kraken continuation becomes a terminal confidence limitation, not an endless background task.
- Portfolio allocation falls back to the canonical multi-bot pool so candidates show numeric 0 rather than Unknown when no safe capital exists.
- Fast Live Truth uses the actual KuCoin order-state module.
- Native KuCoin live execution remains HARD LOCKED.
