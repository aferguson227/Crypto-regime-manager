from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json
from typing import Any

@dataclass(frozen=True)
class SourceState:
    name: str
    status: str
    observed_at: str | None
    version: str | None
    warnings: tuple[str, ...] = ()

@dataclass(frozen=True)
class BotDecision:
    asset: str
    regime: str
    production_status: str
    action: str
    recommendation: str | None
    entry_allowed: bool
    decision_score: float | None
    live_bot_state: str
    settings_state: str
    reasons: tuple[str, ...] = ()
    cautions: tuple[str, ...] = ()

@dataclass(frozen=True)
class CapitalState:
    currency: str = 'USDT'
    exchange_total: float | None = None
    free_available: float | None = None
    active_deal_capital: float | None = None
    placed_order_reserve: float | None = None
    enabled_bot_theoretical_reserve: float | None = None
    available_after_reserve: float | None = None
    completeness: str = 'unknown'
    warnings: tuple[str, ...] = ()

@dataclass(frozen=True)
class OperatingState:
    schema_version: str
    application_version: str
    snapshot_id: str
    generated_at: str
    mode: str
    read_only: bool
    overall_status: str
    current_market_regime: str
    market_regime_summary: str
    bot_decisions: tuple[BotDecision, ...]
    deploy_today: tuple[str, ...]
    next_capital_priority: str | None
    capital: CapitalState
    evidence_agreement: dict[str, Any]
    source_states: tuple[SourceState, ...]
    governance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
