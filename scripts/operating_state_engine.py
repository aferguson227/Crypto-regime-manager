#!/usr/bin/env python3
"""Build the canonical V32.2 read-only operating-state snapshot.

The engine reconciles existing generated evidence. It never starts/stops bots,
changes settings, closes deals, submits orders or transfers funds.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from app.release import application_version
from app.models.operating_state import BotDecision, CapitalState, OperatingState, SourceState

DOCS = ROOT / 'docs'
OUTPUT = DOCS / 'operating_state.json'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(name: str) -> dict[str, Any]:
    path = DOCS / name
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def stamp(doc: dict[str, Any]) -> str | None:
    md = doc.get('metadata') if isinstance(doc.get('metadata'), dict) else {}
    return doc.get('generated_at') or doc.get('observed_at') or md.get('observed_at') or md.get('generated_at')


def source_state(name: str, doc: dict[str, Any], required: bool = True) -> SourceState:
    warnings: list[str] = []
    if not doc:
        warnings.append('Source is missing or invalid.')
        status = 'missing' if required else 'unavailable'
    else:
        status = str(doc.get('status') or doc.get('workflow_status') or (doc.get('metadata') or {}).get('source_status') or 'available')
    return SourceState(name, status, stamp(doc), str(doc.get('version')) if doc.get('version') else None, tuple(warnings))


def norm_name(value: Any) -> str:
    return ''.join(ch for ch in str(value or '').lower() if ch.isalnum())


def live_bots(three: dict[str, Any], asset: str) -> list[dict[str, Any]]:
    assets = three.get('assets') if isinstance(three.get('assets'), dict) else {}
    entry = assets.get(asset) if isinstance(assets.get(asset), dict) else {}
    return entry.get('bots') if isinstance(entry.get('bots'), list) else []


def live_deals(three: dict[str, Any], asset: str) -> list[dict[str, Any]]:
    assets = three.get('assets') if isinstance(three.get('assets'), dict) else {}
    entry = assets.get(asset) if isinstance(assets.get(asset), dict) else {}
    return entry.get('deals') if isinstance(entry.get('deals'), list) else []


def reconciliation_state(recon: dict[str, Any], asset: str, regime: str) -> str:
    rows = recon.get('reconciliations') if isinstance(recon.get('reconciliations'), list) else []
    row = next((x for x in rows if x.get('asset') == asset and x.get('regime') == regime), None)
    if not row:
        return 'NOT_COMPARED'
    comparisons = row.get('comparisons') if isinstance(row.get('comparisons'), list) else []
    states = {str(x.get('status')) for x in comparisons}
    if states == {'MATCH'}:
        return 'MATCH'
    if 'DIFFERENT' in states:
        return 'CHANGED'
    if any(s.startswith('MISSING_') for s in states):
        return 'INCOMPLETE'
    return 'MIXED'


def bot_live_state(three: dict[str, Any], asset: str, recommended: str | None) -> str:
    bots = live_bots(three, asset)
    if not bots:
        return 'NOT_FOUND'
    target = norm_name(recommended)
    matches = [b for b in bots if target and (target in norm_name(b.get('name')) or norm_name(b.get('name')) in target)]
    if not matches:
        # Fall back to regime words because production and live naming conventions differ.
        words = [x for x in ('low','medium','highbull','highbear') if x in target]
        matches = [b for b in bots if any(w in norm_name(b.get('name')) for w in words)]
    if not matches:
        return 'NO_MATCHING_BOT'
    deals=live_deals(three,asset)
    match_ids={b.get('bot_id') for b in matches if b.get('bot_id') is not None}
    match_names={norm_name(b.get('name')) for b in matches}
    has_deal=any((d.get('bot_id') in match_ids) or (norm_name(d.get('bot_name')) in match_names) for d in deals)
    if has_deal:
        return 'ACTIVE_DEAL'
    if any(bool(b.get('enabled')) for b in matches):
        return 'ENABLED_IDLE'
    return 'DISABLED'


def capital_state(three: dict[str, Any], kucoin: dict[str, Any] | None = None) -> CapitalState:
    enabled_reserve = 0.0
    known_reserve = False
    active = 0.0
    active_known = False
    warnings: list[str] = []
    for asset, entry in (three.get('assets') or {}).items() if isinstance(three.get('assets'), dict) else []:
        if not isinstance(entry, dict):
            continue
        for bot in entry.get('bots') or []:
            if bot.get('enabled') and bot.get('theoretical_max_dca_capital') is not None:
                enabled_reserve += float(bot['theoretical_max_dca_capital']); known_reserve = True
        for deal in entry.get('deals') or []:
            for key in ('bought_volume','actual_usd_profit','base_order_volume'):
                if deal.get(key) is not None and key == 'bought_volume':
                    active += float(deal[key]); active_known = True; break
    kucoin = kucoin or {}
    accounts = three.get('accounts') if isinstance(three.get('accounts'), list) else []
    total = free = None
    if str(kucoin.get('status') or '').lower()=='ok':
        total = kucoin.get('usdt_balance')
        free = kucoin.get('free_usdt')
    for account in accounts:
        if not isinstance(account, dict): continue
        total = total if total is not None else account.get('total_usd_value') or account.get('total_balance')
        free = free if free is not None else account.get('available_usdt') or account.get('free_usdt')
    if total is None or free is None:
        warnings.append('Exchange free USDT is unavailable. Configure KuCoin direct read-only account access; 3Commas Starter balance quota is not a dependable capital source.')
    if not active_known:
        warnings.append('Active-deal cost basis is unavailable; active capital cannot be fully reconciled.')
    if not known_reserve:
        warnings.append('Full enabled-bot DCA sizing is unavailable; theoretical reserve is incomplete.')
    available = None
    if free is not None and known_reserve:
        available = max(0.0, float(free) - enabled_reserve)
    completeness = 'complete' if total is not None and free is not None and active_known and known_reserve else 'partial'
    return CapitalState(
        exchange_total=float(total) if total is not None else None,
        free_available=float(free) if free is not None else None,
        active_deal_capital=active if active_known else None,
        enabled_bot_theoretical_reserve=round(enabled_reserve, 8) if known_reserve else None,
        available_after_reserve=round(available, 8) if available is not None else None,
        completeness=completeness,
        warnings=tuple(warnings),
    )


def evidence_state(strategies: dict[str, Any], walk: dict[str, Any]) -> dict[str, Any]:
    assets = strategies.get('assets') if isinstance(strategies.get('assets'), list) else []
    rows=[]
    for asset in assets:
        aid=str(asset.get('id') or '')
        research=asset.get('research') if isinstance(asset.get('research'),dict) else {}
        basis=research.get('basis') or asset.get('research_basis') or {}
        kraken=bool(basis) or aid == 'SUI'
        q1=bool(walk) and aid == 'SUI'
        kucoin=bool(asset.get('latest'))
        if kraken or q1:
            agree = 'UNKNOWN'
            promotion = str(research.get('promotion_status') or asset.get('promotion_status') or '')
            if 'PASS' in promotion.upper(): agree='AGREE'
            elif 'FAIL' in promotion.upper(): agree='DISAGREE'
            rows.append({'asset':aid,'kraken_historical': 'AVAILABLE' if kraken else 'UNKNOWN','q1_2026_validation':'AVAILABLE' if q1 else 'UNKNOWN','kucoin_current':'AVAILABLE' if kucoin else 'UNKNOWN','agreement':agree})
    return {'status':'PARTIAL' if rows else 'UNAVAILABLE','assets':rows,'note':'Agreement is only asserted when a published validation result explicitly supports it; missing evidence remains UNKNOWN.'}


def build() -> dict[str, Any]:
    generated = now_iso()
    strategies=load('strategies.json'); decisions=load('decision_intelligence_v28.json')
    three=load('threecommas.json'); kucoin=load('kucoin_account.json'); recon=load('configuration_reconciliation.json')
    walk=load('walk_forward_registry.json'); integrity=load('system_integrity.json'); capital_doc=load('capital_intelligence.json')
    assets={str(a.get('id')):a for a in strategies.get('assets',[]) if isinstance(a,dict)}
    ranked=decisions.get('production_ranking') if isinstance(decisions.get('production_ranking'),list) else []
    bot_rows=[]; deploy=[]
    for row in ranked:
        asset=str(row.get('id') or ''); regime=str(row.get('regime') or 'Unknown')
        recommendation=row.get('recommended_bot'); allowed=bool(row.get('entry_allowed'))
        live=bot_live_state(three,asset,recommendation)
        settings=reconciliation_state(recon,asset,regime)
        if live=='ACTIVE_DEAL': action='KEEP_ACTIVE_DEAL' if allowed else 'REVIEW_ACTIVE_DEAL'
        elif live=='ENABLED_IDLE': action='KEEP_ENABLED' if allowed else 'PAUSE_NEW_DEALS'
        elif allowed and live in {'DISABLED','NOT_FOUND','NO_MATCHING_BOT'}: action='DEPLOY_CANDIDATE'; deploy.append(str(recommendation or asset))
        else: action='WAIT' 
        bot_rows.append(BotDecision(asset,regime,str(assets.get(asset,{}).get('production_status') or 'production'),action,recommendation,allowed,float(row['decision_score']) if row.get('decision_score') is not None else None,live,settings,tuple(row.get('positives') or ()),tuple(row.get('cautions') or ())))
    regimes=[str(a.get('latest',{}).get('regime')) for a in assets.values() if isinstance(a.get('latest'),dict) and a.get('latest',{}).get('regime')]
    current='Mixed' if len(set(regimes))>1 else (regimes[0] if regimes else 'Unknown')
    best=next((b for b in bot_rows if b.entry_allowed and b.action in {'DEPLOY_CANDIDATE','KEEP_ACTIVE_DEAL','KEEP_ENABLED'}),None)
    next_priority=best.recommendation if best else None
    sources=(source_state('KuCoin strategy snapshot',strategies),source_state('Unified decision intelligence',decisions),source_state('3Commas live state',three),source_state('Capital intelligence',capital_doc,False),source_state('Configuration reconciliation',recon),source_state('Walk-forward registry',walk,False),source_state('System integrity',integrity))
    failures=[s for s in sources if s.status in {'missing','error','fail'}]
    snapshot_seed='|'.join([generated]+[f'{s.name}:{s.observed_at}:{s.status}' for s in sources])
    snapshot_id=hashlib.sha256(snapshot_seed.encode()).hexdigest()[:20]
    state=OperatingState('1.0',application_version(),snapshot_id,generated,'canonical_read_only_operating_state',True,'DEGRADED' if failures else 'READY',current,f"{len(regimes)} asset regimes observed: {', '.join(regimes) if regimes else 'none'}",tuple(bot_rows),tuple(deploy),next_priority,(CapitalState(currency=capital_doc.get('currency','USDT'),exchange_total=capital_doc.get('exchange_total'),free_available=capital_doc.get('free_available'),active_deal_capital=capital_doc.get('active_deal_capital'),placed_order_reserve=capital_doc.get('placed_order_reserve'),enabled_bot_theoretical_reserve=capital_doc.get('enabled_idle_capacity_reserve'),available_after_reserve=capital_doc.get('deployable_capital'),completeness=str(capital_doc.get('capital_status') or 'unknown').lower(),warnings=tuple(capital_doc.get('warnings') or ())) if capital_doc else capital_state(three,kucoin)),evidence_state(strategies,walk),sources,{'manual_approval_required':True,'automatic_live_changes':False,'automatic_settings_changes':False,'categories':['PRODUCTION_CONFIGURATION','LIVE_3COMMAS_CONFIGURATION','RESEARCH_CANDIDATE','FORWARD_VALIDATED_CONFIGURATION','DEPLOYMENT_RECOMMENDATION']})
    return state.to_dict()


def main() -> int:
    payload=build();OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f"Operating state written: {OUTPUT}");return 0

if __name__ == '__main__':
    raise SystemExit(main())
