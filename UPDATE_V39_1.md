# V39.1.0 — Workflow Reliability & Clean Operations

V39.1 consolidates five accumulated GitHub Actions workflows into four clearly separated responsibilities: Data Refresh, Pages Deploy, Health & Self-Heal, and Release Validation. It reduces runner demand, prevents workflow overlap, distinguishes GitHub-hosted runner delays from CRM concurrency faults, fixes false Pages-timeout diagnosis, and makes generated-output cleanup deterministic.

The hourly data workflow refreshes 3Commas every run and performs the heavier market refresh every four hours in the same runner. Account balance queries are quota-aware and may reuse a recent read-only balance snapshot while still refreshing bots and deals.

All trading safeguards remain unchanged: CRM is advisory and read-only and cannot modify live bots, deals, orders, secrets, or capital.
