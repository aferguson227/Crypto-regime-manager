# CRM V69.0.0 — Persistent My Bots, Paper Ledger & Runtime Watchdog

## Persistent My Bots
- My Bots membership is now stored in `C:\Crypto\CRM_Data\Runtime\State\managed_bot_registry.json`.
- Browser localStorage is retained only as an immediate/fallback cache.
- Add/remove actions persist through the resident local runtime API.
- First-run migration seeds validated paper strategies so upgrades no longer unexpectedly empty My Bots.
- Live bots remain included automatically.

## Paper trading ledger
- Paper history is migrated from the legacy pre-V69 state location into Runtime State without deleting old history.
- Up to 100 closed paper deals per bot remain persisted.
- The dashboard now shows total/open/realised paper P/L, closed deals, win rate, observation days, profit/day, max drawdown and SO use.
- Recent closed paper trades are visible from the bot details panel.

## Direct local runtime truth
- The resident KuCoin service exposes a localhost-only API on `127.0.0.1:8765`.
- Dashboard browsers on the CRM machine poll this runtime API every 10 seconds.
- Live service heartbeat, paper portfolio, managed portfolio and registry state can therefore update independently of GitHub/publication cadence.
- If the local API is unavailable, the dashboard falls back to the published snapshot.

## Runtime watchdog
- Health/recovery and Windows schedule health prefer the authoritative external Runtime State heartbeat over older published files.
- The resident service captures a startup heartbeat immediately and continues its 20-second cycle.
- Publication lag no longer makes a healthy resident service look an hour old.

## Safety
- The localhost API can only modify My Bots membership.
- It exposes no exchange order, cancellation, credential or allocation write endpoint.
- Native KuCoin execution remains HARD LOCKED.
