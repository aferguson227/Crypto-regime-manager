from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any

@dataclass(frozen=True)
class PortfolioPosition:
    asset: str
    bot_name: str
    action: str
    enabled: bool
    active_deals: int
    allocated_capital: float | None
    reserve_capital: float | None
    deployable_priority: int | None
    efficiency_score: float | None
    overlap_group: str
    warnings: tuple[str, ...] = ()

@dataclass(frozen=True)
class PortfolioIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    status: str
    currency: str
    portfolio_health_score: float | None
    diversification_score: float | None
    capital_efficiency_score: float | None
    total_equity: float | None
    allocated_capital: float | None
    reserved_capital: float | None
    deployable_capital: float | None
    allocation_pct: float | None
    reserve_pct: float | None
    available_pct: float | None
    next_capital_priority: str | None
    positions: tuple[PortfolioPosition, ...]
    overlap_analysis: dict[str, Any]
    warnings: tuple[str, ...]
    read_only: bool = True
    manual_approval_required: bool = True
    def to_dict(self)->dict[str,Any]: return json.loads(json.dumps(asdict(self)))
