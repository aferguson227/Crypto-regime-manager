#!/usr/bin/env python3
"""V32.4 transparent, read-only deployment intelligence engine."""
from __future__ import annotations
import hashlib, json, sys, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.deployment_intelligence import DeploymentAction, DeploymentIntelligence, SettingsSnapshot
DOCS=ROOT/'docs'; OUTPUT=DOCS/'deployment_intelligence.json'
EXACT_FIELDS=('base_order_volume','safety_order_volume','take_profit_pct','so_deviation_pct','safety_orders','volume_scale','step_scale','max_active_deals','max_active_safety_orders','start_condition','order_type','trailing_enabled','cooldown_seconds')

def load(path: Path)->dict[str,Any]:
    try:
        v=json.loads(path.read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
    except Exception:return {}

def num(v):
    try:return float(v) if v not in (None,'') else None
    except (TypeError,ValueError):return None

def normal(v):return ''.join(c for c in str(v or '').lower() if c.isalnum())
def name_tokens(v):
    stop={'bot','dca','strategy','the'}
    return {x for x in re.findall(r'[a-z0-9]+',str(v or '').lower()) if x not in stop}
def best_live_bot(bots,name,asset):
    wanted=name_tokens(name)|{str(asset).lower()}
    scored=[]
    for bot in bots:
        tokens=name_tokens(bot.get('name'))
        score=len(wanted & tokens)
        if str(asset).lower() in tokens: score+=3
        scored.append((score,bot))
    return max(scored,key=lambda x:x[0])[1] if scored and max(x[0] for x in scored)>=3 else None

def config_settings(cfg,asset,regime):
    a=next((x for x in cfg.get('assets',[]) if x.get('id')==asset),{})
    b=(a.get('bots') or {}).get(regime) or {}
    vals={
      'bot_name':b.get('name'),'base_order_volume':num((cfg.get('execution') or {}).get('base_order')),
      'safety_order_volume':num(b.get('safety_order_volume')),'take_profit_pct':num(b.get('take_profit_pct')),
      'so_deviation_pct':num(b.get('so_deviation_pct')),'safety_orders':b.get('safety_orders'),
      'volume_scale':num(b.get('volume_scale')),'step_scale':num(b.get('step_scale')),
      'max_active_deals':b.get('max_active_deals',1),'max_active_safety_orders':b.get('max_active_safety_orders'),
      'start_condition':b.get('start_condition'),'order_type':b.get('order_type'),
      'trailing_enabled':b.get('trailing_enabled'),'cooldown_seconds':b.get('cooldown_seconds')}
    missing=tuple(k for k in EXACT_FIELDS if vals.get(k) is None)
    return SettingsSnapshot('PRODUCTION_CONFIGURATION',vals,not missing,missing)

def live_settings(three,asset,name):
    entry=((three.get('assets') or {}).get(asset) or {})
    bots=entry.get('bots') or []; target=normal(name)
    bot=next((b for b in bots if target and (target in normal(b.get('name')) or normal(b.get('name')) in target)),None) or best_live_bot(bots,name,asset)
    if not bot:return SettingsSnapshot('LIVE_3COMMAS_CONFIGURATION',{},False,EXACT_FIELDS)
    aliases={'base_order_volume':['base_order_volume'],'safety_order_volume':['safety_order_volume'],'take_profit_pct':['take_profit_pct','take_profit'],
      'so_deviation_pct':['so_deviation_pct','safety_order_deviation_pct','safety_order_step_percentage','price_deviation_to_open_safety_orders'],'safety_orders':['max_safety_orders','safety_orders'],
      'volume_scale':['volume_scale','martingale_volume_coefficient'],'step_scale':['step_scale','martingale_step_coefficient'],
      'max_active_deals':['max_active_deals'],'max_active_safety_orders':['max_active_safety_orders','active_safety_orders_count'],
      'start_condition':['start_condition','strategy_list'],'order_type':['order_type','start_order_type'],'trailing_enabled':['trailing_enabled','trailing'],
      'cooldown_seconds':['cooldown_seconds','cooldown']}
    vals={'bot_name':bot.get('name'),'enabled':bot.get('enabled'),'bot_id':bot.get('bot_id')}
    for field,keys in aliases.items(): vals[field]=next((bot.get(k) for k in keys if bot.get(k) is not None),None)
    missing=tuple(k for k in EXACT_FIELDS if vals.get(k) is None)
    return SettingsSnapshot('LIVE_3COMMAS_CONFIGURATION',vals,not missing,missing)

def compare(a,b):
    rows=[]
    for k in EXACT_FIELDS:
        av=a.values.get(k); bv=b.values.get(k)
        if av is None or bv is None: status='NOT_COMPARABLE'
        elif isinstance(av,(int,float)) and isinstance(bv,(int,float)): status='MATCH' if abs(float(av)-float(bv))<1e-9 else 'DIFFERENT'
        else: status='MATCH' if str(av).lower()==str(bv).lower() else 'DIFFERENT'
        rows.append({'field':k,'production_value':av,'live_value':bv,'status':status})
    comparable=[r for r in rows if r['status']!='NOT_COMPARABLE']
    changed=any(r['status']=='DIFFERENT' for r in comparable) if comparable else None
    return changed,tuple(rows)

def recommended_settings(production,live):
    values={'bot_name':production.values.get('bot_name') or live.values.get('bot_name')}
    evidence={}
    for field in EXACT_FIELDS:
        pv=production.values.get(field); lv=live.values.get(field)
        if pv is not None:
            values[field]=pv; evidence[field]='GOVERNED'
        elif lv is not None:
            values[field]=lv; evidence[field]='KEEP_LIVE'
        else:
            values[field]=None; evidence[field]='UNAVAILABLE'
    missing=tuple(k for k in EXACT_FIELDS if values.get(k) is None)
    values['_evidence']=evidence
    return SettingsSnapshot('CANONICAL_LIVE_GOVERNED_RECOMMENDATION',values,not missing,missing)

def evidence_for(state,asset):
    rows=((state.get('evidence_agreement') or {}).get('assets') or [])
    row=next((x for x in rows if x.get('asset')==asset),None)
    return row or {'asset':asset,'kraken_historical':'UNKNOWN','q1_2026_validation':'UNKNOWN','kucoin_current':'AVAILABLE','agreement':'UNKNOWN'}

def confidence(row,evidence,capital,settings_complete):
    score=max(0,min(100,float(row.get('decision_score') or 0)))
    if not row.get('entry_allowed'): score-=35
    if evidence.get('agreement')=='AGREE': score+=8
    elif evidence.get('agreement')=='DISAGREE': score-=20
    elif evidence.get('agreement')=='UNKNOWN': score-=8
    if capital.get('capital_status')!='COMPLETE': score-=10
    if not settings_complete: score-=8
    return round(max(0,min(100,score)),1)

def build()->dict[str,Any]:
    cfg=load(ROOT/'config.json'); state=load(DOCS/'operating_state.json'); capital=load(DOCS/'capital_intelligence.json'); three=load(DOCS/'threecommas.json')
    decisions=load(DOCS/'decision_intelligence_v28.json'); generated=datetime.now(timezone.utc).isoformat()
    actions=[]; deploy=[]; keep=[]; review=[]; warnings=[]
    ranked=decisions.get('production_ranking') or []
    state_rows={r.get('asset'):r for r in state.get('bot_decisions') or []}
    for row in ranked:
        asset=str(row.get('id') or ''); regime=str(row.get('regime') or 'Unknown'); name=str(row.get('recommended_bot') or asset)
        osrow=state_rows.get(asset,{})
        prod=config_settings(cfg,asset,regime); live=live_settings(three,asset,name); recommended=recommended_settings(prod,live); changed,diffs=compare(recommended,live)
        ev=evidence_for(state,asset); cap_required=None; cap_available=capital.get('deployable_capital'); can_fund=None
        caprow=next((b for b in capital.get('bots') or [] if asset==b.get('asset') and len(name_tokens(name)&name_tokens(b.get('bot_name')))>=2),None)
        if caprow: cap_required=caprow.get('next_deal_required_capital')
        if cap_available is not None and cap_required is not None: can_fund=float(cap_available)>=float(cap_required)
        blocks=[]
        if not row.get('entry_allowed'): blocks.append('Current entry permission is blocked.')
        if str(osrow.get('production_status')).lower() not in {'production','forward_validated','forward-validated'}: blocks.append('Strategy is not approved production or forward-validated configuration.')
        live_state=str(osrow.get('live_bot_state') or 'UNKNOWN')
        if live_state=='ACTIVE_DEAL':
            action='KEEP_ACTIVE_DEAL'; keep.append(name)
        elif live_state=='ENABLED_IDLE':
            # An enabled bot with no deal is not automatically a keep-running decision.
            # Preserve entry only when current entry permission is positive; otherwise recommend pausing new deals.
            action='KEEP_ENABLED' if bool(row.get('entry_allowed')) else 'PAUSE_NEW_DEALS'
            (keep if action=='KEEP_ENABLED' else review).append(name)
        else:
            if capital.get('capital_status')!='COMPLETE' or can_fund is not True: blocks.append('Complete deployable-capital confirmation is unavailable.')
            if not recommended.complete: blocks.append('Exact DCA settings are incomplete; deployment is blocked.')
            if ev.get('agreement')=='DISAGREE': blocks.append('Kraken, Q1 validation and current KuCoin evidence disagree.')
            action='DEPLOY_TODAY' if not blocks else 'WAIT'
            (deploy if action=='DEPLOY_TODAY' else review).append(name)
        conf=confidence(row,ev,capital,recommended.complete)
        eligible=action in {'KEEP_ACTIVE_DEAL','KEEP_ENABLED','DEPLOY_TODAY'} and bool(row.get('entry_allowed'))
        actions.append(DeploymentAction(asset,name,action,conf,eligible,tuple(blocks),tuple(row.get('positives') or ()),tuple(row.get('cautions') or ()),regime,str(osrow.get('live_bot_state') or 'UNKNOWN'),str(osrow.get('settings_state') or 'NOT_COMPARED'),cap_required,cap_available,can_fund,prod,recommended,changed,tuple(diffs),ev))
    overall='DEPLOY' if deploy else ('MAINTAIN' if keep else 'WAIT')
    if capital.get('capital_status')!='COMPLETE': warnings.append('Capital reconciliation is incomplete; no new deployment may be asserted.')
    if any(not a.recommended_settings.complete for a in actions): warnings.append('One or more exact DCA setting sets are incomplete; missing fields are shown explicitly.')
    source={'operating_state_snapshot':state.get('snapshot_id'),'capital_snapshot':capital.get('snapshot_id'),'decision_generated_at':decisions.get('generated_at'),'threecommas_generated_at':three.get('generated_at')}
    seed=json.dumps({'generated':generated,'source':source},sort_keys=True)
    payload=DeploymentIntelligence('1.0',application_version(),generated,hashlib.sha256(seed.encode()).hexdigest()[:20],'read_only_advisory_deployment_intelligence',True,True,str(state.get('current_market_regime') or 'Unknown'),round(sum(a.confidence for a in actions)/len(actions),1) if actions else 0,overall,tuple(deploy),tuple(keep),tuple(review),state.get('next_capital_priority'),str(capital.get('capital_status') or 'UNAVAILABLE'),{
      'exchange_total':capital.get('exchange_total'),'free_available':capital.get('free_available'),'active_deal_capital':capital.get('active_deal_capital'),'reserved_capital':capital.get('remaining_active_deal_dca_reserve'),'deployable_capital':capital.get('deployable_capital'),'next_capital_required':capital.get('next_capital_required'),'can_fund_next_priority':capital.get('can_fund_next_priority')},tuple(actions),state.get('evidence_agreement') or {},source,tuple(warnings)).to_dict()
    return payload

def main()->int:
    p=build(); OUTPUT.write_text(json.dumps(p,indent=2),encoding='utf-8'); print(f'Deployment intelligence written: {OUTPUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
