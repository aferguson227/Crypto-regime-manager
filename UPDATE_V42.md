# Crypto Regime Manager V43.0.0 — Autonomous Research & Decision Integrity

## Purpose

V42 turns the stable V41.2 local-agent architecture into a stricter decision platform.

### Decision integrity
- Portfolio actions are now per-bot, not copied from one asset-level recommendation.
- Only bots with active deals can be labelled `KEEP_ACTIVE_DEAL`.
- Enabled idle bots are explicitly `KEEP_ENABLED` or `PAUSE_NEW_DEALS`.
- Command State understands the new lifecycle actions and prioritises them consistently.

### Canonical DCA recommendation
- Missing governed fields inherit the current live value when CRM has no evidence to change it.
- Live SO deviation remains mapped through the canonical 3Commas aliases.
- Recommended settings expose evidence provenance and avoid unnecessary `Unknown` values.

### Research promotion
- New `research_pipeline.json` reconciles current KuCoin discovery with frozen Kraken/Q1 evidence.
- Candidates are classified as `READY_FOR_MANUAL_REVIEW`, `NEEDS_HISTORICAL_VALIDATION`, or `RESEARCH_REJECT`.
- No candidate is promoted automatically and no live trading action is enabled.

### Interface
- Long regime labels such as ACCUMULATION are protected against awkward mid-word wrapping.
- The unified Dashboard shows how many current candidates are ready for manual research review.

### Safety
CRM remains advisory and read-only. V42 cannot start/stop/edit bots, place/cancel orders, transfer funds, withdraw assets, or alter secrets.
