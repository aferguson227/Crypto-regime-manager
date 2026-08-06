# Manual outcome annotations

Create `manual_outcomes.json` only when an outcome cannot be reconciled from read-only 3Commas data. Keep recommendation IDs unchanged. Supported statuses are `PENDING`, `ACTIVE`, `COMPLETED`, `IGNORED`, `EXPIRED`, `CANCELLED`, and `SUPERSEDED`.

Example:

```json
{"outcomes":[{"recommendation_id":"...","status":"COMPLETED","acted_on_at":"2026-08-06T08:00:00Z","closed_at":"2026-08-07T10:00:00Z","entry_price":1.0,"exit_price":1.05,"realised_profit_pct":5.0,"maximum_adverse_excursion_pct":-2.0,"maximum_favourable_excursion_pct":6.0,"notes":"Manually reconciled."}]}
```
