#!/usr/bin/env python3
"""V32.9 read-only market context, regime evidence and portfolio stress tests."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.market_intelligence import MarketIntelligence
DOCS=ROOT/'docs'; OUTPUT=DOCS/'market_intelligence.json'

def load(name:str)->dict[str,Any]:
 try:
  x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except Exception:return {}
def num(v):
 try:
  f=float(v);return f if math.isfinite(f) else None
 except (TypeError,ValueError):return None
def clamp(v):return round(max(0,min(100,v)),1)
def build()->dict[str,Any]:
 strategies=load('strategies.json'); discovery=load('coin_discovery.json'); adaptive=load('adaptive_intelligence.json'); portfolio=load('portfolio_intelligence.json')
 generated=datetime.now(timezone.utc).isoformat(); warnings=[]; assets=[]
 rows=((strategies.get('portfolio') or {}).get('ranking') or [])
 for r in rows:
  if not isinstance(r,dict):continue
  trend=55 if str(r.get('action')).upper() in {'CAUTIOUS','BUY','DEPLOY'} else 40
  if bool(r.get('entry_allowed')):trend+=15
  regime=str(r.get('regime') or 'Unknown'); vol=35 if regime.lower()=='low' else 65
  assets.append({'asset':str(r.get('id') or 'UNKNOWN'),'symbol':r.get('symbol'),'regime':regime,'entry_allowed':bool(r.get('entry_allowed')),'trend_score':clamp(trend),'volatility_score':clamp(vol),'opportunity_score':num(r.get('score'))})
 candidates=discovery.get('researched_candidates') or []
 breadth_vals=[num(x.get('trend_30d_pct')) for x in candidates if isinstance(x,dict) and num(x.get('trend_30d_pct')) is not None]
 positive=sum(1 for x in breadth_vals if x>0); breadth=clamp(100*positive/len(breadth_vals)) if breadth_vals else 50
 trend_vals=[a['trend_score'] for a in assets]; trend=round(statistics.mean(trend_vals),1) if trend_vals else 50
 vol_vals=[a['volatility_score'] for a in assets]; volatility=round(statistics.mean(vol_vals),1) if vol_vals else 50
 unique=len({a['regime'] for a in assets}); correlation=clamp(75-unique*10) if assets else 50
 composite=clamp(trend*.45+breadth*.30+(100-volatility)*.15+(100-correlation)*.10)
 if composite>=70:regime='BULL_ACCUMULATION';risk='RISK_ON';exposure='HIGH'
 elif composite>=55:regime='ACCUMULATION';risk='BALANCED';exposure='MODERATE'
 elif composite>=40:regime='MEAN_REVERTING';risk='CAUTIOUS';exposure='LOW_TO_MODERATE'
 else:regime='DEFENSIVE';risk='RISK_OFF';exposure='LOW'
 contexts=[]
 for s in adaptive.get('strategies') or []:
  if not isinstance(s,dict):continue
  reasons=[]; blockers=[]
  asset=str(s.get('asset') or 'UNKNOWN'); a=next((x for x in assets if x['asset']==asset),{})
  if a.get('entry_allowed'):reasons.append('Current operating data allows entry.')
  else:blockers.append('Current operating data does not allow entry.')
  if regime in {'BULL_ACCUMULATION','ACCUMULATION'}:reasons.append(f'Market context is {regime.replace("_"," ").title()}.')
  if str(s.get('action'))=='WAIT':blockers.append('Governed recommendation remains WAIT.')
  contexts.append({'asset':asset,'bot_name':s.get('bot_name'),'action':s.get('action'),'effective_score':s.get('effective_score'),'market_regime':regime,'why_now':reasons,'why_not':blockers,'market_support_score':clamp(composite if a.get('entry_allowed') else composite*.65)})
 total=num(portfolio.get('exchange_total'));allocated=num(portfolio.get('allocated_capital'));reserved=num(portfolio.get('reserved_capital'))
 def stress(name,shock,reserve_mult):
  exposed=allocated if allocated is not None else None
  loss=round(exposed*abs(shock)/100,2) if exposed is not None else None
  stressed_reserve=round(reserved*reserve_mult,2) if reserved is not None else None
  return {'scenario':name,'market_shock_pct':shock,'estimated_capital_impact':loss,'stressed_reserve_requirement':stressed_reserve,'status':'ESTIMATED' if loss is not None else 'UNKNOWN','automatic_action':False}
 stress_tests=[stress('BTC decline',-10,1.25),stress('Volatility expansion',-6,1.5),stress('Rapid recovery',8,.9)]
 attribution={'trend':45.0,'market_breadth':30.0,'volatility':15.0,'cross_asset_diversification':10.0}
 if not assets:warnings.append('No current tracked-asset regime records were available; neutral defaults were used.')
 if total is None:warnings.append('Exchange equity is unknown; stress-test capital impacts may be incomplete.')
 source={'strategies':'strategies.json','coin_discovery':'coin_discovery.json','adaptive_intelligence':'adaptive_intelligence.json','portfolio_intelligence':'portfolio_intelligence.json'}
 seed=json.dumps({'regime':regime,'composite':composite,'assets':assets,'sources':source},sort_keys=True)
 payload=MarketIntelligence('1.0',application_version(),generated,hashlib.sha256(seed.encode()).hexdigest()[:20],'read_only_market_context',True,True,regime,composite,trend,volatility,breadth,correlation,risk,exposure,tuple(assets),tuple(contexts),tuple(stress_tests),attribution,source,tuple(warnings)).to_dict()
 payload['breadth_evidence']={'positive_assets':positive,'assets_with_30d_trend':len(breadth_vals),'source':'coin_discovery.researched_candidates.trend_30d_pct','status':'MEASURED' if breadth_vals else 'NEUTRAL_FALLBACK'}
 return payload
def main()->int:
 p=build();OUTPUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Market intelligence written: {OUTPUT}');return 0
if __name__=='__main__':raise SystemExit(main())
