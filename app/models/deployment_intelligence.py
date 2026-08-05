from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from typing import Any

@dataclass(frozen=True)
class SettingsSnapshot:
    source: str
    values: dict[str, Any]
    complete: bool
    missing_fields: tuple[str, ...] = ()

@dataclass(frozen=True)
class DeploymentAction:
    asset: str
    bot_name: str
    action: str
    confidence: float
    eligible: bool
    blocking_reasons: tuple[str, ...]
    supporting_reasons: tuple[str, ...]
    cautions: tuple[str, ...]
    current_regime: str
    live_state: str
    settings_state: str
    capital_required: float | None
    capital_available: float | None
    can_fund: bool | None
    production_settings: SettingsSnapshot
    recommended_settings: SettingsSnapshot
    settings_changed: bool | None
    settings_differences: tuple[dict[str, Any], ...]
    evidence: dict[str, Any]

@dataclass(frozen=True)
class DeploymentIntelligence:
    schema_version: str
    application_version: str
    generated_at: str
    snapshot_id: str
    mode: str
    read_only: bool
    manual_approval_required: bool
    current_market_regime: str
    current_regime_confidence: float
    overall_action: str
    deploy_today: tuple[str, ...]
    keep_running: tuple[str, ...]
    review_or_pause: tuple[str, ...]
    next_capital_priority: str | None
    capital_status: str
    capital_summary: dict[str, Any]
    actions: tuple[DeploymentAction, ...]
    evidence_agreement: dict[str, Any]
    source_snapshots: dict[str, Any]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))
