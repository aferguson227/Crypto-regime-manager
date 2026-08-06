from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any

@dataclass(frozen=True)
class CommandPriority:
    rank: int
    category: str
    asset: str | None
    bot_name: str | None
    action: str
    confidence_pct: float | None
    urgency: str
    rationale: tuple[str, ...]
    blockers: tuple[str, ...]
    capital_required: float | None
    can_fund: bool | None

@dataclass(frozen=True)
class CommandState:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    mode: str
    read_only: bool
    manual_approval_required: bool
    overall_status: str
    market: dict[str, Any]
    portfolio: dict[str, Any]
    capital: dict[str, Any]
    recommendations: tuple[dict[str, Any], ...]
    priority_queue: tuple[CommandPriority, ...]
    risks: tuple[str, ...]
    evidence: dict[str, Any]
    cloud: dict[str, Any]
    health: dict[str, Any]
    source_snapshots: dict[str, Any]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
