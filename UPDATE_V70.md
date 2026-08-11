# CRM V70.0.0 — Resident Runtime & Live Trading Architecture

V70 replaces the collection of independently scheduled background processes with one hidden resident supervisor.

## Runtime ownership
- `CryptoRegimeManager-ResidentRuntime` becomes the single Windows scheduled owner.
- KuCoin Live Data Service and Research Worker run as hidden supervised child processes.
- The Local Agent becomes a low-priority publication job every 15 minutes rather than part of live trading truth.
- Legacy Local Agent and Research Worker scheduled tasks are disabled, not deleted, so rollback remains possible.

## Live-data targets
- resident heartbeat: 2 seconds
- browser/direct runtime target: 5–10 seconds
- KuCoin live heartbeat watchdog: 75 seconds maximum before automatic restart
- order truth target: 20 seconds
- balance target: 30 seconds
- paper-trading target: 30 seconds
- Git/publication: 15 minutes by default

## Installer safety
- resident maintenance mode pauses child writers before upgrades;
- runtime state remains outside Git;
- source release commits exclude `docs/*.json`;
- installer rebases immediately before push if remote read-only refresh commits advanced;
- rollback re-enables the previous scheduled architecture if V70 health verification fails.

## Safety boundary
CRM native live exchange writes remain locked. V70 is a reliability/runtime release, not a direct-execution unlock.


## Portfolio Truth & Decision Consistency

V70 now creates `portfolio_decision_consistency.json` from authoritative Runtime State.

- `Portfolio` is no longer allowed to equal free cash when a recognised live position also exists.
- Total portfolio truth uses the larger of exchange-reported equity and reconstructed cash + live-position market value.
- `Deployable now` is capped by genuinely free KuCoin cash after the remaining DCA reserve.
- If a live strategy has completed all configured safety orders, remaining DCA reserve becomes zero.
- A deployment candidate cannot continue to display a capital blocker when safe deployable cash is already greater than its required capital.
- The My Bots decision banner now models the future automated flow: `current live deal -> next ranked strategy -> final revalidation -> future execution`.
- Direct live execution remains locked.

## Paper Evidence Maturity

Paper strategies now use explicit forward-test maturity:

- Starting: 0 closed deals
- Early forward test: 1–4 closed deals
- Building evidence: 5–19 closed deals
- Meaningful forward evidence: 20+ closed deals

The dashboard reports elapsed forward-test time, current open-deal count and completed paper deals rather than simply saying `Building evidence`.

## Publication Quality

A delayed GitHub/website publication is no longer a live-trading fault when the local V70 resident runtime and KuCoin live heartbeat are current.

The dashboard presents this as `Website snapshot delayed` while live P/L, orders, paper bots and portfolio truth continue from local Runtime State.


## Release/Runtime Metadata Separation

V70 permanently separates software release identity from mutable runtime producer metadata.

Strict release identity:
- `VERSION`
- `app/release.json`
- `config.json` when it declares the app version
- `docs/version.json`
- optional strict release diagnostics metadata

Mutable runtime/publication JSON:
- may temporarily report the CRM version that last generated the snapshot;
- an older producer version is reported as `RUNTIME METADATA REFRESH REQUIRED`;
- it does not invalidate a successfully installed newer CRM release;
- a snapshot claiming a future CRM version remains a hard validation error.

This prevents stale runtime snapshots such as paper portfolio, KuCoin service status,
research status, health outputs or managed-bot state from blocking future software upgrades.
