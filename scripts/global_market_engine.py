#!/usr/bin/env python3
"""V44 global market regime engine.
Uses current KuCoin breadth/BTC context plus available historical BTC evidence.
Missing historical BTC evidence stays explicit; it is never fabricated.
"""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'global_market.json'
def load(n):
 try:
  v=json.loads((DOCS/n).read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else {}
 except:return {}
def num(v):
 try:return float(v)
 except:return None
def clamp(v):return round(max(0,min(100,v)),1)
def main():
 market=load('market_intelligence.json'); discovery=load('coin_discovery.json'); registry=load('walk_forward_registry.json')
 candidates=discovery.get('researched_candidates') or []
 btc=next((x for x in candidates if isinstance(x,dict) and str(x.get('base_currency') or '').upper()=='BTC'),{})
 btc30=num(btc.get('trend_30d_pct')); btc24=num(btc.get('change_24h_pct')); breadth=num(market.get('breadth_score')); trend=num(market.get('trend_score')); vol=num(market.get('volatility_score'))
 btc_hist=next((x for x in registry.get('coins') or [] if isinstance(x,dict) and str(x.get('symbol') or '').upper() in {'BTC','XBT'}),None)
 score=50.0
 if trend is not None:score+=(trend-50)*.35
 if breadth is not None:score+=(breadth-50)*.25
 if btc30 is not None:score+=max(-20,min(20,btc30))*1.0
 if btc24 is not None:score+=max(-8,min(8,btc24))*1.2
 if vol is not None:score-=(max(0,vol-55))*.15
 score=clamp(score)
 if score>=75:regime='STRONG_BULL'
 elif score>=62:regime='BULL'
 elif score>=52:regime='ACCUMULATION'
 elif score>=43:regime='NEUTRAL'
 elif score>=32:regime='DISTRIBUTION'
 elif score>=20:regime='BEAR'
 else:regime='CAPITULATION'
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'regime':regime,'score_pct':score,
  'current_evidence':{'btc_30d_trend_pct':btc30,'btc_24h_change_pct':btc24,'breadth_pct':breadth,'market_trend_pct':trend,'volatility_pct':vol,'source':'KuCoin current/public CRM market evidence'},
  'historical_btc_evidence':{'status':'AVAILABLE' if btc_hist else 'MISSING','registry_symbol':(btc_hist or {}).get('symbol'),'walk_forward_status':(btc_hist or {}).get('status'),'note':'Historical BTC/XBT Kraken evidence contributes only when present in the walk-forward registry.'},
  'policy':{'universal_context':True,'asset_specific_regime_still_required':True,'automatic_bot_changes':False,'manual_approval_required':True}}
 payload['snapshot_id']=hashlib.sha256(json.dumps({'regime':regime,'score':score,'btc':btc30,'breadth':breadth},sort_keys=True).encode()).hexdigest()[:24]
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Global market written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
