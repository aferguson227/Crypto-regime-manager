from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any

@dataclass(frozen=True)
class MarketIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    mode: str
    read_only: bool
    manual_approval_required: bool
    regime: str
    regime_confidence_pct: float
    trend_score: float
    volatility_score: float
    breadth_score: float
    correlation_score: float
    risk_appetite: str
    recommended_exposure: str
    tracked_assets: tuple[dict[str, Any], ...]
    strategy_context: tuple[dict[str, Any], ...]
    stress_tests: tuple[dict[str, Any], ...]
    confidence_attribution: dict[str, float]
    source_files: dict[str, str]
    warnings: tuple[str, ...]
    def to_dict(self)->dict[str,Any]:
        return json.loads(json.dumps(asdict(self)))
