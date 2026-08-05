from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from typing import Any

@dataclass(frozen=True)
class AccountCapital:
    account_id: int | None
    name: str
    exchange: str | None
    currency: str
    total_equity: float | None
    free_available: float | None
    observed_at: str | None = None

@dataclass(frozen=True)
class BotCapital:
    asset: str
    bot_id: int | None
    bot_name: str
    enabled: bool
    active_deals: int
    max_active_deals: int | None
    per_deal_max_capital: float | None
    active_deal_capital: float | None
    placed_order_reserve: float | None
    remaining_dca_reserve: float | None
    idle_capacity_reserve: float | None
    next_deal_required_capital: float | None
    completeness: str
    warnings: tuple[str, ...] = ()

@dataclass(frozen=True)
class CapitalIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    currency: str
    accounts: tuple[AccountCapital, ...]
    bots: tuple[BotCapital, ...]
    exchange_total: float | None
    free_available: float | None
    active_deal_capital: float | None
    placed_order_reserve: float | None
    remaining_active_deal_dca_reserve: float | None
    enabled_idle_capacity_reserve: float | None
    deployable_capital: float | None
    reserve_coverage_ratio: float | None
    capital_status: str
    next_capital_priority: str | None
    next_capital_required: float | None
    can_fund_next_priority: bool | None
    methodology: dict[str, Any]
    warnings: tuple[str, ...]
    read_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
