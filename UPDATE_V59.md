# CRM V62.0.0 — KuCoin Trading Truth & Accounting Completion

V59 is the reliability clean-up before DCA Optimisation 2.0 and the next native-execution phase.

- KuCoin order verification now combines current HF orders, Classic Spot orders and untriggered stop orders so 3Commas-created TP/SO orders are not missed.
- A degraded order collector can no longer produce a false confirmed “missing TP” failure; the state becomes Unverified until KuCoin order visibility is healthy.
- “Orphan orders” is replaced by user-facing “leftover orders after a closed trade”.
- Open P/L remains unknown/updating when current trade P/L is unavailable; CRM no longer converts missing P/L to 0.
- Trading Briefing capital uses canonical capital intelligence first: exchange total, deployable capital and remaining active-deal DCA reserve.
- The fill ledger performs bounded historical weekly backfill (up to four windows per Local Agent cycle) through the legacy read-only KuCoin fills compatibility endpoint, persisting progress so realised cost basis can converge without blocking refreshes.
- Recommended/action badges use a universal content-sized responsive rule; “Keep active deal” and other badges cannot stretch across the card or hyphenate words.
- Empty redundant dashboard cards are automatically hidden rather than displayed as blank shells.
- Live execution remains read-only/HARD LOCKED. V59 does not create, change, cancel or submit KuCoin/3Commas orders.
