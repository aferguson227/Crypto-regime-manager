# CRM V67.0.0 — Trader Portfolio Command Centre

V60 finishes the reliability/UI clean-up before DCA Optimisation 2.0 and the next native-execution phase.

## Portfolio-first dashboard
The opening view is now a trader-focused portfolio command centre. It distinguishes:
- Portfolio value
- KuCoin cash
- Reserved for active DCA
- Safe to allocate now
- Open P/L
- Realised P/L
- Trading P/L
- Live position
- Next opportunity

The former duplicate Portfolio Now panel is removed.

## Capital semantics
CRM no longer uses one ambiguous “available” number. `capital_intelligence.json` now exposes `kucoin_cash_available`, `active_dca_reserve` and `safe_to_allocate_now` separately.

If a candidate is next in the portfolio queue but no safe capital is currently available, the dashboard explains that it is waiting for capital rather than showing a contradictory zero suggested allocation.

## Realised P/L backfill
Historical cost-basis backfill now publishes weekly-window progress, an estimated number of remaining background cycles and approximate background time remaining. Open P/L remains visible while realised history is incomplete, and the Trading P/L card explicitly identifies partial status.

## Trade Protection & DCA Health
The former “Trading safety checks” presentation becomes Trade Protection & DCA Health. It verifies:
- live position recognition;
- take-profit order visibility;
- current DCA order state;
- remaining DCA capital reserve.

CRM no longer assumes every configured safety order must always be resting on KuCoin; provider-controlled DCA orders may be staged at trigger time.

## Recovery state
A failed background account refresh no longer makes the trading view appear unusable when a sufficiently fresh KuCoin balance snapshot is still available. The dashboard distinguishes “Trading data current · background recovery” from a genuine decision-data failure.

## Permanent UI control contract
Status badges/pills use a single intrinsic-width component contract. They cannot flex-grow across a card, hyphenate words, or inherit full-width styling. This specifically prevents “Keep active deal” and similar states from becoming stretched bars.

## Empty secondary panels
Secondary dashboard cards with no meaningful rendered content are hidden automatically rather than appearing as blank shells.

## Safety
V60 remains read-only for native KuCoin execution. It cannot place or cancel exchange orders and cannot automatically modify/start/stop 3Commas bots.
