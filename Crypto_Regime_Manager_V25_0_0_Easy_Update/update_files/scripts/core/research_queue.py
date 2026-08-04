"""Automatic, advisory-only multi-asset research queue.

The queue identifies the weakest configured asset/regime, evaluates one-variable
entry-filter hypotheses against the unchanged baseline, and publishes ranked
research tasks. It never modifies production configuration or live bots.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Callable

MetricFn = Callable[[dict[str, Any]], dict[str, Any]]
SimulateFn = Callable[[list[Any], list[dict[str, Any] | None], dict[str, Any], dict[str, Any]], dict[str, Any]]


def _weakness(asset: dict[str, Any]) -> tuple[float, list[str]]:
    health = asset.get("health") or {}
    score = 100.0 - float(health.get("score", 0) or 0)
    reasons: list[str] = []
    if float(asset.get("net_pnl", 0) or 0) < 0:
        score += 25
        reasons.append("negative total mark-to-market P&L")
    if float((health.get("recent_realised_pnl", 0) or 0)) < 0:
        score += 15
        reasons.append("negative recent realised P&L")
    open_pos = asset.get("open_position") or {}
    hours = float(open_pos.get("hours_open", 0) or 0)
    if hours > 30 * 24:
        score += min(30, hours / 24 / 4)
        reasons.append(f"open replay position has lasted {hours/24:.1f} days")
    drawdown = abs(min(0.0, float(asset.get("maximum_drawdown_pct_of_capital", 0) or 0)))
    if drawdown > 20:
        score += min(20, drawdown / 2)
        reasons.append(f"historical drawdown is {drawdown:.1f}% of capital")
    if not reasons:
        reasons.append("lowest relative health among configured assets")
    return round(score, 2), reasons


def _candidate_metrics(result: dict[str, Any], compact_metrics: MetricFn) -> dict[str, Any]:
    return compact_metrics(result)


def build_research_queue(
    cfg: dict[str, Any],
    outputs: list[dict[str, Any]],
    contexts: dict[str, Any],
    simulate: SimulateFn,
    compact_metrics: MetricFn,
) -> dict[str, Any] | None:
    qcfg = cfg.get("research_queue") or {}
    if not qcfg.get("enabled", False):
        return None

    eligible = [a for a in outputs if str(a.get("id")) in contexts]
    if not eligible:
        return {
            "version": "21.0",
            "status": "WAITING FOR DATA",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "queue": [],
            "guardrails": {"advisory_only": True, "production_changes": False},
        }

    ranked_assets = []
    for asset in eligible:
        weakness, reasons = _weakness(asset)
        ranked_assets.append({"asset": asset, "weakness": weakness, "reasons": reasons})
    ranked_assets.sort(key=lambda row: row["weakness"], reverse=True)

    max_assets = int(qcfg.get("max_assets_per_cycle", 3))
    max_experiments = int(qcfg.get("max_experiments_per_asset", 8))
    min_improvement = float(qcfg.get("minimum_net_pnl_improvement", 0.0))
    max_dd_worse = float(qcfg.get("maximum_drawdown_worsening_pp", 5.0))
    min_retention = float(qcfg.get("minimum_deal_retention_pct", 25.0))
    library = qcfg.get("hypothesis_library") or []
    queue: list[dict[str, Any]] = []

    for asset_rank, row in enumerate(ranked_assets[:max_assets], start=1):
        current = row["asset"]
        aid = str(current.get("id"))
        ctx = contexts[aid]
        baseline = compact_metrics(current)
        open_pos = baseline.get("open_position") or {}
        target_regime = str(open_pos.get("regime") or (current.get("latest") or {}).get("regime") or "Medium")
        candidates = []

        for item in library[:max_experiments]:
            candidate_asset = copy.deepcopy(ctx["asset"])
            candidate_asset.pop("research_experiments", None)
            candidate_asset.pop("strategy_evolution", None)
            candidate_asset["id"] = f"{aid}-{item.get('id')}"
            candidate_asset["display_name"] = f"{aid} · {item.get('title')}"
            candidate_asset.setdefault("entry_filter", {}).setdefault(target_regime, {})[item["field"]] = item["value"]
            simulated = simulate(ctx["candles"], ctx["signals"], candidate_asset, cfg["execution"])
            metrics = _candidate_metrics(simulated, compact_metrics)

            pnl_change = metrics["net_pnl"] - baseline["net_pnl"]
            duration_reduction = baseline["effective_longest_trade_hours"] - metrics["effective_longest_trade_hours"]
            dd_change = metrics["maximum_drawdown_pct_of_capital"] - baseline["maximum_drawdown_pct_of_capital"]
            deal_retention = 100.0 * metrics["closed_deals"] / max(1, baseline["closed_deals"])
            open_changed = bool(open_pos and (
                not metrics.get("open_position") or
                (metrics.get("open_position") or {}).get("entry_time") != open_pos.get("entry_time")
            ))
            rank_score = (
                45 * pnl_change / max(100.0, abs(baseline["net_pnl"]))
                + 25 * duration_reduction / max(24.0, baseline["effective_longest_trade_hours"])
                - 2.0 * dd_change
                + (10 if open_changed else 0)
                - max(0.0, min_retention - deal_retention) * 0.15
            )
            passed = (
                pnl_change > min_improvement
                and dd_change >= -max_dd_worse
                and deal_retention >= min_retention
            )
            candidates.append({
                "experiment_id": f"{aid}-{item.get('id')}",
                "title": item.get("title"),
                "family": item.get("family"),
                "field": item.get("field"),
                "value": item.get("value"),
                "human_rule": item.get("human_rule"),
                "status": "PASS" if passed else "REJECT",
                "rank_score": round(rank_score, 2),
                "comparison": {
                    "net_pnl_change": round(pnl_change, 2),
                    "duration_reduction_hours": round(duration_reduction, 1),
                    "drawdown_change_pp": round(dd_change, 2),
                    "deal_retention_pct": round(deal_retention, 1),
                    "problem_trade_changed": open_changed,
                },
                "candidate_metrics": metrics,
            })

        candidates.sort(key=lambda item: (item["status"] == "PASS", item["rank_score"]), reverse=True)
        winner = next((c for c in candidates if c["status"] == "PASS"), None)
        queue.append({
            "priority": asset_rank,
            "asset_id": aid,
            "production_status": current.get("production_status", "production"),
            "weakness_score": row["weakness"],
            "weakness_reasons": row["reasons"],
            "target_regime": target_regime,
            "baseline": baseline,
            "recommended_experiment": winner,
            "status": "CANDIDATE READY FOR MANUAL REVIEW" if winner else "NO ROBUST IMPROVEMENT FOUND",
            "experiments": candidates,
            "next_action": (
                "Review and freeze the winning candidate before any forward test."
                if winner else
                "Keep the production baseline unchanged and expand the hypothesis library later."
            ),
        })

    return {
        "version": "21.0",
        "mode": "automatic_multi_asset_research_queue",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "READY" if queue else "WAITING FOR DATA",
        "queue": queue,
        "summary": {
            "assets_reviewed": len(queue),
            "assets_with_candidate": sum(1 for row in queue if row.get("recommended_experiment")),
            "experiments_run": sum(len(row.get("experiments") or []) for row in queue),
        },
        "guardrails": {
            "advisory_only": True,
            "automatic_production_changes": False,
            "automatic_bot_changes": False,
            "automatic_dca_changes": False,
            "manual_freeze_required": True,
            "forward_validation_required": True,
        },
        "note": "The queue proposes evidence-based one-variable experiments. It cannot alter live bots or production configuration.",
    }
