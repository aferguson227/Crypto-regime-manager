#!/usr/bin/env python3
"""V32.3 read-only capital reconciliation and allocation engine."""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.capital_intelligence import AccountCapital, BotCapital, CapitalIntelligence
DOCS=ROOT/'docs'; OUTPUT=DOCS/'capital_intelligence.json'

def f(v):
    try:
        if v in (None,''): return None
        return float(v)
    except (TypeError,ValueError): return None

def i(v,default=0):
    try: return int(float(v))
    except (TypeError,ValueError): return default

def load(name):
    p=DOCS/name
    try:
        x=json.loads(p.read_text(encoding='utf-8-sig')); return x if isinstance(x,dict) else {}
    except Exception:return {}

def deal_capital(d):
    for k in ('capital_used_quote','capital_used','bought_volume'):
        x=f(d.get(k))
        if x is not None:return x
    return None

def deal_placed_reserve(d):
    for k in ('placed_order_reserve','reserved_quote_funds','reserved_funds','active_safety_order_capital'):
        x=f(d.get(k))
        if x is not None:return x
    return None

def geometric_remaining(safety,scale,start,count):
    if safety is None or count<=0:return 0.0 if count==0 else None
    scale=scale or 1.0
    return sum(safety*(scale**n) for n in range(start,start+count))

def build()->dict[str,Any]:
    three=load('threecommas.json'); kucoin=load('kucoin_account.json'); state=load('operating_state.json')
    generated=datetime.now(timezone.utc).isoformat(); warnings=[]
    account_rows=[]
    capital_source='3Commas read-only account snapshot'
    if str(kucoin.get('status') or '').lower()=='ok' and kucoin.get('free_usdt') is not None:
        capital_source='KuCoin direct read-only account API'
        account_rows.append(AccountCapital(None,'KuCoin direct account','KuCoin',str(kucoin.get('currency') or 'USDT'),f(kucoin.get('usdt_balance')),f(kucoin.get('free_usdt')),kucoin.get('generated_at')))
    else:
        for a in three.get('accounts') or []:
            if not isinstance(a,dict):continue
            account_rows.append(AccountCapital(i(a.get('account_id'),None),str(a.get('name') or '3Commas account'),a.get('exchange_name'),str(a.get('currency') or 'USDT'),f(a.get('total_usd_value')),f(a.get('free_usdt')),three.get('generated_at')))
    totals=[a.total_equity for a in account_rows if a.total_equity is not None]
    frees=[a.free_available for a in account_rows if a.free_available is not None]
    exchange_total=sum(totals) if totals else None; free=sum(frees) if frees else None
    if not account_rows:
        warnings.append('No read-only exchange account records are available. Configure KuCoin read-only account access to remove the 3Commas balance dependency.')
    elif capital_source.startswith('3Commas') and any((a.get('balance_records') or 0)==0 for a in (three.get('accounts') or []) if isinstance(a,dict)):
        warnings.append('3Commas account balance data is incomplete. Configure KuCoin direct read-only account access for dependable deployable-capital calculation.')
    bot_rows=[]; all_active=[]; all_placed=[]; all_remaining=[]; all_idle=[]
    assets=three.get('assets') if isinstance(three.get('assets'),dict) else {}
    for asset,entry in assets.items():
        if not isinstance(entry,dict):continue
        deals=entry.get('deals') or []
        for bot in entry.get('bots') or []:
            if not isinstance(bot,dict):continue
            bid=bot.get('bot_id'); name=str(bot.get('name') or 'Unnamed bot')
            matches=[d for d in deals if (bid is not None and d.get('bot_id')==bid) or str(d.get('bot_name') or '')==name]
            active_values=[deal_capital(d) for d in matches]; active_known=[x for x in active_values if x is not None]
            placed_values=[deal_placed_reserve(d) for d in matches]; placed_known=[x for x in placed_values if x is not None]
            active=sum(active_known) if len(active_known)==len(matches) and matches else (0.0 if not matches else None)
            placed=sum(placed_known) if len(placed_known)==len(matches) and matches else (0.0 if not matches else None)
            per=f(bot.get('theoretical_max_dca_capital')); maxdeals=i(bot.get('max_active_deals'),1) or 1
            safety=f(bot.get('safety_order_volume')); scale=f(bot.get('volume_scale')) or 1.0; maxso=i(bot.get('max_safety_orders'),0)
            remaining_parts=[]; complete=True
            for d in matches:
                completed=i(d.get('completed_safety_orders'),0)
                rem=geometric_remaining(safety,scale,completed,max(0,maxso-completed))
                if rem is None: complete=False
                else: remaining_parts.append(rem)
            remaining=sum(remaining_parts) if complete else None
            unused=max(0,maxdeals-len(matches)); idle=per*unused if per is not None and bot.get('enabled') else (0.0 if not bot.get('enabled') else None)
            req=per if bot.get('enabled') and unused>0 else None
            bw=[]
            if per is None: bw.append('Complete base/safety-order sizing is unavailable.')
            if matches and active is None: bw.append('Active deal cost basis is incomplete.')
            if matches and remaining is None: bw.append('Remaining safety-order reserve cannot be calculated.')
            completeness='complete' if not bw else 'partial'
            row=BotCapital(str(asset),i(bid,None),name,bool(bot.get('enabled')),len(matches),maxdeals,per,active,placed,remaining,idle,req,completeness,tuple(bw)); bot_rows.append(row)
            if active is not None:all_active.append(active)
            if placed is not None:all_placed.append(placed)
            if remaining is not None:all_remaining.append(remaining)
            if idle is not None:all_idle.append(idle)
    active_total=sum(all_active) if bot_rows and len(all_active)==len(bot_rows) else None
    placed_total=sum(all_placed) if bot_rows and len(all_placed)==len(bot_rows) else None
    remaining_total=sum(all_remaining) if bot_rows and len(all_remaining)==len(bot_rows) else None
    idle_total=sum(all_idle) if bot_rows and len(all_idle)==len(bot_rows) else None
    deployable=max(0.0,free-(idle_total or 0.0)) if free is not None and idle_total is not None else None
    required=(remaining_total or 0)+(idle_total or 0) if remaining_total is not None and idle_total is not None else None
    coverage=(free/required) if free is not None and required and required>0 else (1.0 if required==0 and free is not None else None)
    priority=state.get('next_capital_priority')
    priority_row=next((b for b in bot_rows if priority and priority.lower() in b.bot_name.lower()),None)
    next_required=priority_row.next_deal_required_capital if priority_row else None
    can_fund=(deployable>=next_required) if deployable is not None and next_required is not None else None
    if free is None:warnings.append('Free USDT is unknown; deployable capital cannot be asserted.')
    if any(b.completeness!='complete' for b in bot_rows):warnings.append('One or more bot capital records are partial.')
    status='COMPLETE' if not warnings else ('PARTIAL' if bot_rows else 'UNAVAILABLE')
    seed=json.dumps({'generated':generated,'three':three.get('generated_at'),'state':state.get('snapshot_id')},sort_keys=True)
    payload=CapitalIntelligence('1.0',application_version(),generated,hashlib.sha256(seed.encode()).hexdigest()[:20],'USDT',tuple(account_rows),tuple(bot_rows),exchange_total,free,active_total,placed_total,remaining_total,idle_total,deployable,coverage,status,priority,next_required,can_fund,{
      'free_available':f'Read-only free USDT from {capital_source}.',
      'active_deal_capital':'Sum of known cost basis for active deals.',
      'placed_order_reserve':'Shown separately; not subtracted from free USDT because exchange free balance normally already excludes open-order funds.',
      'remaining_active_deal_dca_reserve':'Unplaced remaining safety-order ladder requirement for active deals.',
      'enabled_idle_capacity_reserve':'Maximum full-ladder capital for unused enabled-bot deal slots.',
      'deployable_capital':'free_available minus enabled_idle_capacity_reserve; never inferred when source data is incomplete.'
    },tuple(warnings)).to_dict()
    allocations=[]
    for asset,entry in assets.items():
        qty=sum(float(d.get('allocated_asset_quantity') or 0) for d in (entry.get('deals') or []) if isinstance(d,dict))
        quote=sum(float(d.get('capital_used_quote') or 0) for d in (entry.get('deals') or []) if isinstance(d,dict))
        if qty or quote:
            allocations.append({'asset':asset,'quantity':qty or None,'quote_currency':next((d.get('quote_currency') for d in entry.get('deals') or [] if isinstance(d,dict) and d.get('quote_currency')), 'USDT'),'quote_cost':quote or None})
    payload['asset_allocations']=allocations
    payload['capital_source']=capital_source
    payload['kucoin_direct_status']=kucoin.get('status') or 'not_configured'
    return payload

def main():
    p=build();OUTPUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Capital intelligence written: {OUTPUT}');return 0
if __name__=='__main__':raise SystemExit(main())
