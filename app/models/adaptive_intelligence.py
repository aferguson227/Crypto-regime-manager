from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any

@dataclass(frozen=True)
class AdaptiveStrategy:
    asset: str
    bot_name: str
    action: str
    static_score: float
    adaptive_score: float
    effective_score: float
    evidence_count: int
    adaptation_status: str
    confidence_calibration_pct: float | None
    observed_accuracy_pct: float | None
    average_return_pct: float | None
    capital_efficiency_score: float | None
    risk_adjusted_score: float | None
    rank: int | None
    weight_adjustments: dict[str, float]
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

@dataclass(frozen=True)
class AdaptiveIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    mode: str
    read_only: bool
    manual_approval_required: bool
    minimum_evidence_required: int
    adaptive_influence_cap_pct: float
    adaptation_enabled: bool
    next_capital_priority: str | None
    strategies: tuple[AdaptiveStrategy, ...]
    confidence_calibration: tuple[dict[str, Any], ...]
    portfolio_optimisation: dict[str, Any]
    source_files: dict[str, str]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
