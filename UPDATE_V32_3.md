# V32.3.0 — Capital Intelligence Engine

V32.3.0 adds canonical, read-only capital reconciliation. It reads 3Commas account, bot and active-deal data and distinguishes exchange equity, free USDT, active-deal capital, placed-order reserve, remaining active-deal DCA requirement, enabled idle-bot reserve and deployable capital. Unknown values remain unknown; no balance or reserve is invented.

The integration remains GET-only and cannot start or stop bots, change settings, close deals, submit orders or transfer funds.
