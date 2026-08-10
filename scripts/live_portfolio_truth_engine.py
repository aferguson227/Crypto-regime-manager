#!/usr/bin/env python3
"""V51 canonical live portfolio truth built from exchange reconciliation."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'live_portfolio_truth.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 tc=load('threecommas.json');trade=load('trade_intelligence.json');recon=load('execution_reconciliation.json');acct=load('independent_trade_accounting.json');cap=load('capital_intelligence.json');prices=load('kucoin_live_prices.json')
 rby={(str(x.get('asset')).upper(),x.get('bot_id')):x for x in recon.get('deals') or []};tby={(str(x.get('asset')).upper(),x.get('bot_id')):x for x in trade.get('trades') or []};pby={str(x.get('symbol') or '').split('-')[0].upper():x for x in prices.get('prices') or []};aby={str(x.get('asset') or '').upper():x for x in cap.get('asset_allocations') or []}
 deals=[]
 for a,b in (tc.get('assets') or {}).items():
  for d in b.get('deals') or []:
   key=(str(a).upper(),d.get('bot_id'));r=rby.get(key) or {};t=tby.get(key) or {}
   effective=r.get('crm_position_truth') or 'OPEN';provider_stale=r.get('reconciliation_state')=='PROVIDER_STALE_OPEN'
   asset=str(a).upper();pa=pby.get(asset) or {};aa=aby.get(asset) or {};qty=aa.get('quantity');cost=aa.get('quote_cost');px=pa.get('price')
   live_pnl=(float(qty)*float(px)-float(cost)) if qty not in (None,0) and cost is not None and px is not None and pa.get('status')=='OK' else None
   live_pct=(100*live_pnl/float(cost)) if live_pnl is not None and float(cost)!=0 else None
   deals.append({'asset':asset,'bot_id':d.get('bot_id'),'bot_name':d.get('bot_name'),'provider_status':d.get('status'),
    'effective_position_state':effective,'provider_stale':provider_stale,'opened_at':d.get('created_at'),
    'open_pnl_quote':live_pnl if live_pnl is not None else t.get('profit_quote'),'open_pnl_source':'KUCOIN_LIVE_MARK_TO_MARKET' if live_pnl is not None else 'PROVIDER_FALLBACK',
    'open_pnl_price':px,'open_pnl_priced_at':prices.get('generated_at'),'profit_pct':live_pct if live_pct is not None else t.get('profit_pct'),
    'capital_used_quote':cost if cost is not None else d.get('capital_used_quote'),'distance_to_take_profit_pct':t.get('distance_to_take_profit_pct'),
    'action':'Reconcile stale 3Commas deal; KuCoin position is already closed.' if provider_stale else t.get('crm_recommendation') or 'Monitor'})
 effective_open=[x for x in deals if x['effective_position_state']=='OPEN']
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'authority':'KuCoin closure evidence + CRM ledger; 3Commas is execution-provider telemetry.',
  'effective_open_deal_count':len(effective_open),'provider_reported_deal_count':len(deals),'stale_provider_deal_count':sum(x['provider_stale'] for x in deals),
  'open_pnl_quote':(sum(float(x.get('open_pnl_quote')) for x in effective_open if x.get('open_pnl_quote') is not None) if effective_open and any(x.get('open_pnl_quote') is not None for x in effective_open) else (0.0 if not effective_open else None)),
  'open_pnl_status':('LIVE' if effective_open and all(x.get('open_pnl_source')=='KUCOIN_LIVE_MARK_TO_MARKET' for x in effective_open) else ('FALLBACK' if effective_open and any(x.get('open_pnl_quote') is not None for x in effective_open) else ('NO_OPEN_TRADES' if not effective_open else 'UPDATING'))),
  'open_pnl_priced_at':prices.get('generated_at'),'open_pnl_price_source':prices.get('source'),
  'realised_profit_quote':acct.get('realised_profit_quote'),'realised_profit_status':acct.get('realised_profit_status'),'deployable_capital':cap.get('deployable_capital'),
  'deals':deals,'read_only':True}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Live portfolio truth written: {OUT}; effective_open={len(effective_open)} stale={p["stale_provider_deal_count"]}');return 0
if __name__=='__main__':raise SystemExit(main())
