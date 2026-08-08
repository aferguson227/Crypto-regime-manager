# Crypto Regime Manager V45.0.0 — Live Trade Intelligence & Expansion Readiness

V43 adds a read-only active-deal intelligence snapshot and an evidence-based gate for adding a second production coin. It never closes a deal, changes a bot, places an order or automatically promotes a research candidate.

## Active Trade Intelligence
- Active 3Commas deal P/L, hold time, DCA ladder progress, remaining safety orders and distance to TP when the API supplies the underlying values.
- Frozen Kraken/Q1 duration context is shown descriptively; V43 does not invent exit probabilities.
- Snapshot freshness is explicit: this is periodic monitoring, not a streaming market feed.

## Expansion Readiness
- A second asset is only presented for manual review when local capital, 3Commas trade state, TEL stress state, current breadth and independent Kraken/Q1 evidence all pass.
- One-new-asset-at-a-time policy.
- Historical max-capital is evidence only and is never copied mechanically into a live allocation.

## Engineering
- recommendation_history.json and research_pipeline.json are now canonical generated outputs, preventing future installer/build cleanliness false positives.
- Release Validation retains its canonical requirements-ci.txt dependency installation.


## Operations Centre refinement
- Startup Decision Briefing appears only for unacknowledged material event IDs.
- Decision Inbox remains visible after the modal is dismissed.
- Ready research candidates expose Add to Recommended Bots and Download Settings actions.
- Add to Recommended Bots is deliberately browser-local/read-only; it cannot create or edit a live bot.
- Recommendation History is surfaced directly on the Dashboard.
- Main Dashboard is now explicitly the Trading Operations Centre.

## Production-grade repository lifecycle
- Incoming installers clean runtime files using the incoming release policy before checking source cleanliness.
- Local Agent publishes recommendation history and research pipeline when materially changed, then restores remaining runtime noise.
- Repository Guardian fails builds when a generated docs JSON is not classified.
- Generated-output classification can distinguish runtime state from genuine source changes.
- Local credentials remain outside Git under the Windows user profile; published runtime snapshots remain in `docs/` only because GitHub Pages consumes them.
