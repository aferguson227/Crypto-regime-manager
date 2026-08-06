from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any

@dataclass(frozen=True)
class ConfidenceComponent:
    name: str
    score: float | None
    weight: float
    status: str
    explanation: str

@dataclass(frozen=True)
class RecommendationRecord:
    recommendation_id: str
    asset: str
    bot_name: str
    action: str
    overall_confidence: float
    risk_level: str
    confidence_components: tuple[ConfidenceComponent, ...]
    score_breakdown: dict[str, float]
    supporting_evidence: tuple[str, ...]
    risks: tuple[str, ...]
    blockers: tuple[str, ...]
    expected_behaviour: dict[str, Any]
    production_comparison: dict[str, Any]
    capital_impact: dict[str, Any]
    evidence_agreement: dict[str, Any]
    explanation: str

@dataclass(frozen=True)
class RecommendationIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    mode: str
    read_only: bool
    manual_approval_required: bool
    overall_action: str
    market_regime: str
    recommendations: tuple[RecommendationRecord, ...]
    history_file: str
    warnings: tuple[str, ...]
    source_snapshots: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
