#!/usr/bin/env python3
"""V45 explainable global market regime engine.
Uses current BTC/market evidence and recognises Kraken XBT as BTC everywhere.
"""
from __future__ import annotations
import json,hashlib,os,re
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.core.symbols import canonical_asset
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'global_market.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig'));return v if isinstance(v,dict) else {}
 except:return {}
def num(v):
 try:return float(v)
 except:return None
def clamp(v):return round(max(0,min(100,v)),1)
def historical_btc(registry):
 for x in registry.get('coins') or []:
  if isinstance(x,dict) and canonical_asset(str(x.get('symbol') or ''))=='BTC':return x
 return None
def main():
 market=load('market_intelligence.json');discovery=load('coin_discovery.json');registry=load('walk_forward_registry.json');hist=load('historical_data_status.json');candidates=discovery.get('researched_candidates') or []
 btc=next((x for x in candidates if isinstance(x,dict) and canonical_asset(str(x.get('base_currency') or x.get('symbol') or ''))=='BTC'),{})
 btc30=num(btc.get('trend_30d_pct'));btc24=num(btc.get('change_24h_pct'));breadth=num(market.get('breadth_score'));trend=num(market.get('trend_score'));vol=num(market.get('volatility_score'));btc_hist=historical_btc(registry)
 btc_kucoin=next((x for x in hist.get('inventory') or [] if str(x.get('symbol')).upper()=='BTC-USDT' and (x.get('bars') or 0)>0),None)
 contributions=[];score=50.0
 def add(label,value,weight,delta,source):
  nonlocal score
  score+=delta;contributions.append({'criterion':label,'value':value,'weight':weight,'score_contribution':round(delta,2),'source':source})
 if trend is not None:add('Market trend',trend,.35,(trend-50)*.35,'KuCoin/current CRM market intelligence')
 if breadth is not None:add('Market breadth',breadth,.25,(breadth-50)*.25,'Share of tracked candidates with positive medium-term trend')
 if btc30 is not None:add('BTC 30-day trend',btc30,1.0,max(-20,min(20,btc30)),'KuCoin BTC public market evidence')
 if btc24 is not None:add('BTC 24-hour move',btc24,1.2,max(-8,min(8,btc24))*1.2,'KuCoin BTC public market evidence')
 if vol is not None:add('Volatility penalty',vol,-.15,-max(0,vol-55)*.15,'Current market volatility score')
 score=clamp(score)
 if score>=75:regime='STRONG_BULL'
 elif score>=62:regime='BULL'
 elif score>=52:regime='ACCUMULATION'
 elif score>=43:regime='NEUTRAL'
 elif score>=32:regime='DISTRIBUTION'
 elif score>=20:regime='BEAR'
 else:regime='CAPITULATION'
 universe=(market.get('breadth_universe') or market.get('breadth_sample_size') or len([x for x in candidates if isinstance(x,dict) and x.get('trend_30d_pct') is not None]))
 positive=round((breadth/100)*universe) if breadth is not None and universe else None
 payload={'schema_version':'1.1','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'regime':regime,'score_pct':score,
  'explanation':f'{regime.replace("_"," ").title()} because the weighted current-market score is {score:.1f}%.',
  'criteria':contributions,'current_evidence':{'btc_30d_trend_pct':btc30,'btc_24h_change_pct':btc24,'breadth_pct':breadth,'breadth_positive_count':positive,'breadth_universe_count':universe,'market_trend_pct':trend,'volatility_pct':vol,'source':'KuCoin current/public CRM market evidence'},
  'breadth_explanation':(f'{positive} of {universe} tracked candidates have positive medium-term trend.' if positive is not None and universe else 'Breadth sample detail is unavailable.'),
  'historical_btc_evidence':{'status':'KRAKEN_VALIDATED' if btc_hist else ('KUCOIN_HISTORY_AVAILABLE' if btc_kucoin else 'BUILDING'),'registry_symbol':(btc_hist or {}).get('symbol'),'walk_forward_status':(btc_hist or {}).get('status'),'kucoin_bars':(btc_kucoin or {}).get('bars'),'kucoin_period_start':(btc_kucoin or {}).get('earliest'),'xbt_normalised_to_btc':True,'note':'CRM normalises XBT/XXBT to BTC. If Kraken validation is absent, KuCoin BTC-USDT history becomes the primary exchange-specific historical regime source while Kraken remains optional robustness evidence.'},
  'policy':{'universal_context':True,'asset_specific_regime_still_required':True,'automatic_bot_changes':False,'manual_approval_required':True}}
 payload['snapshot_id']=hashlib.sha256(json.dumps({'regime':regime,'score':score,'btc':btc30,'breadth':breadth},sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Global market written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
