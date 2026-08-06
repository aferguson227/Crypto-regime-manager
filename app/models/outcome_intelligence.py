from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any

@dataclass(frozen=True)
class OutcomeRecord:
    recommendation_id: str
    recommendation_snapshot_id: str | None
    recommendation_recorded_at: str | None
    asset: str
    bot_name: str
    recommended_action: str
    recommendation_confidence: float | None
    market_regime: str | None
    status: str
    reconciliation_source: str
    acted_on_at: str | None
    closed_at: str | None
    entry_price: float | None
    exit_price: float | None
    realised_profit_value: float | None
    realised_profit_pct: float | None
    maximum_adverse_excursion_pct: float | None
    maximum_favourable_excursion_pct: float | None
    hold_hours: float | None
    correct: bool | None
    notes: str | None
    evidence: dict[str, Any]

@dataclass(frozen=True)
class OutcomeIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    mode: str
    read_only: bool
    manual_approval_required: bool
    records: tuple[OutcomeRecord, ...]
    analytics: dict[str, Any]
    confidence_calibration: tuple[dict[str, Any], ...]
    source_files: dict[str, Any]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
