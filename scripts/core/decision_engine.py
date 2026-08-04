from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except Exception:
        return default

def _n(value: Any, default: float = 0.0) -> float:
    try: return float(value or 0)
    except Exception: return default

def _asset_score(asset: dict[str, Any]) -> tuple[float, dict[str, float], list[str], list[str]]:
    latest=asset.get('latest') or {}; health=asset.get('health') or {}; intel=asset.get('intelligence') or {}; open_pos=asset.get('open_position') or {}
    allowed=bool(latest.get('entry_allowed')); base=_n(intel.get('opportunity_score'))
    health_score=_n(health.get('score')); pnl=_n(health.get('recent_realised_pnl')); dd=abs(_n(health.get('recent_max_drawdown_pct_of_capital')))
    avg_hours=_n(health.get('recent_average_trade_hours') or health.get('recent_average_duration_hours')); avg_days=avg_hours/24
    open_days=_n(open_pos.get('hours_open'))/24; capital=_n(asset.get('max_theoretical_capital')); cap_eff=(pnl/capital*100) if capital else 0
    c={
      'entry_permission': 24 if allowed else -35,
      'opportunity': max(0,min(20,base*.20)),
      'health': max(-8,min(18,(health_score-50)*.36)),
      'recent_profit': max(-10,min(12,pnl/60)),
      'drawdown': max(-16,min(8,8-dd*.8)),
      'duration': max(-10,min(7,7-avg_days*1.3-open_days*.35)),
      'capital_efficiency': max(-6,min(8,cap_eff*1.5)),
    }
    score=max(0,min(100,round(45+sum(c.values()),1)))
    positives=[]; cautions=[]
    if allowed: positives.append('Current entry filters pass')
    else: cautions.append('Current entry is blocked')
    if health_score>=75: positives.append('Strategy health is strong')
    elif health_score<60: cautions.append('Strategy health requires review')
    if pnl>0: positives.append('Recent realised P&L is positive')
    else: cautions.append('Recent realised P&L is not positive')
    if dd>15: cautions.append('Recent drawdown is elevated')
    if open_pos: cautions.append(f'Open replay position has lasted {open_days:.1f} days')
    if cap_eff>0: positives.append('Recent capital efficiency is positive')
    return score,c,positives,cautions

def build(root: Path) -> dict[str, Any]:
    docs=root/'docs'; strategies=_read(docs/'strategies.json',{}); discovery=_read(docs/'coin_discovery.json',{}); validation=_read(docs/'candidate_validation.json',{}); queue=_read(docs/'research_queue.json',{})
    assets=strategies.get('assets') or []
    ranked=[]
    for a in assets:
        production=a.get('production_status','production')=='production'
        score,components,positives,cautions=_asset_score(a)
        ranked.append({'id':a.get('id'),'symbol':a.get('symbol'),'regime':(a.get('latest') or {}).get('regime'),'production':production,'entry_allowed':bool((a.get('latest') or {}).get('entry_allowed')),'recommended_bot':(a.get('latest') or {}).get('recommended_bot'),'decision_score':score,'components':components,'positives':positives,'cautions':cautions,'validation_state':'production_baseline' if production else (a.get('research') or {}).get('promotion_status','research')})
    production=sorted([x for x in ranked if x['production']],key=lambda x:x['decision_score'],reverse=True)
    eligible=[x for x in production if x['entry_allowed']]
    best=eligible[0] if eligible else None
    discovered=discovery.get('candidates') or discovery.get('researched_candidates') or []
    validation_candidates=validation.get('candidates') or []
    research_ready=[x for x in validation_candidates if str(x.get('status','')).upper() in {'PASS','READY','MANUAL REVIEW'}]
    payload={
      'version':'28.0.0','generated_at':datetime.now(timezone.utc).isoformat(),'mode':'unified_advisory_decision_engine',
      'best_setup':best,'production_ranking':production,'all_assets':ranked,
      'pipeline':{'production_assets':len(production),'eligible_production':len(eligible),'discovery_candidates':len(discovered),'validation_candidates':len(validation_candidates),'research_ready':len(research_ready),'queue_items':len(queue.get('items') or queue.get('queue') or [])},
      'synchronisation':{'strategy_snapshot':strategies.get('generated_at'),'discovery_snapshot':discovery.get('generated_at'),'validation_snapshot':validation.get('generated_at'),'all_modules_consumed':True},
      'policy':{'discovery_can_change_live_ranking':False,'validation_required_before_production':True,'manual_approval_required':True,'automatic_live_changes':False},
      'explanation':'The dashboard winner is recalculated from current production evidence after every refresh. Discovery and research affect priorities immediately, but cannot become a live recommendation until independent validation and manual approval.'
    }
    return payload

def write_decision_intelligence(root: Path) -> dict[str, Any]:
    payload=build(root); (root/'docs'/'decision_intelligence_v28.json').write_text(json.dumps(payload,indent=2),encoding='utf-8'); return payload
