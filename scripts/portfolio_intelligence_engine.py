#!/usr/bin/env python3
"""V32.7 portfolio-wide read-only capital, overlap and priority analysis."""
from __future__ import annotations
import hashlib,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.release import application_version
from app.models.portfolio_intelligence import PortfolioIntelligence,PortfolioPosition
DOCS=ROOT/'docs';OUTPUT=DOCS/'portfolio_intelligence.json'

def load(name:str)->dict[str,Any]:
 try:
  x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except Exception:return {}
def num(v):
 try:
  f=float(v);return f if math.isfinite(f) else None
 except (TypeError,ValueError):return None
def build()->dict[str,Any]:
 cap=load('capital_intelligence.json'); rec=load('recommendation_intelligence.json'); three=load('threecommas.json')
 generated=datetime.now(timezone.utc).isoformat();warnings=[]
 recs={str(r.get('asset')):r for r in rec.get('recommendations',[]) if isinstance(r,dict)}
 positions=[];groups={}
 for b in cap.get('bots',[]) if isinstance(cap.get('bots'),list) else []:
  asset=str(b.get('asset') or 'UNKNOWN');r=recs.get(asset,{})
  allocated=num(b.get('active_deal_capital'));reserve=num(b.get('remaining_dca_reserve'))
  if reserve is None:reserve=num(b.get('idle_capacity_reserve'))
  action=str(r.get('action') or 'WAIT');confidence=num(r.get('overall_confidence'))
  efficiency=None
  if confidence is not None and allocated is not None: efficiency=round(confidence/(1+allocated/1000),2)
  group='BTC-linked altcoin' if asset not in {'BTC','ETH','USDT'} else asset
  groups.setdefault(group,[]).append(asset)
  bw=tuple(b.get('warnings') or ())
  positions.append(PortfolioPosition(asset,str(b.get('bot_name') or asset),action,bool(b.get('enabled')),int(b.get('active_deals') or 0),allocated,reserve,None,efficiency,group,bw))
 ranked=sorted(range(len(positions)),key=lambda i:((recs.get(positions[i].asset,{}) or {}).get('overall_confidence') or -1),reverse=True)
 out=[]
 for rank,i in enumerate(ranked,1):
  p=positions[i];out.append(PortfolioPosition(p.asset,p.bot_name,p.action,p.enabled,p.active_deals,p.allocated_capital,p.reserve_capital,rank,p.efficiency_score,p.overlap_group,p.warnings))
 positions=out
 total=num(cap.get('exchange_total'));allocated=num(cap.get('active_deal_capital'));reserved=num(cap.get('remaining_active_deal_dca_reserve'))
 idle=num(cap.get('enabled_idle_capacity_reserve')); reserved=(reserved+idle) if reserved is not None and idle is not None else (reserved if idle is None else idle)
 deployable=num(cap.get('deployable_capital'))
 def pct(v):return round(100*v/total,1) if v is not None and total and total>0 else None
 allocation_pct,reserve_pct,available_pct=pct(allocated),pct(reserved),pct(deployable)
 unique=len({p.asset for p in positions});div=round(min(100,unique*25),1) if positions else None
 efficiencies=[p.efficiency_score for p in positions if p.efficiency_score is not None];eff=round(sum(efficiencies)/len(efficiencies),1) if efficiencies else None
 completeness=100 if cap.get('capital_status')=='COMPLETE' else 60 if cap.get('capital_status')=='PARTIAL' else 20
 health=round(sum(x for x in (div,eff,completeness) if x is not None)/len([x for x in (div,eff,completeness) if x is not None]),1) if any(x is not None for x in (div,eff,completeness)) else None
 if total is None:warnings.append('Total exchange equity remains unknown; portfolio percentages cannot be asserted.')
 if deployable is None:warnings.append('Deployable capital remains unknown; next allocation is advisory only.')
 overlap={k:{'assets':sorted(set(v)),'count':len(set(v)),'concentration_warning':len(set(v))>2} for k,v in groups.items()}
 nextp=cap.get('next_capital_priority') or next((p.bot_name for p in positions if p.action in {'DEPLOY_TODAY','KEEP_RUNNING'}),None)
 seed=json.dumps({'generated':generated,'capital':cap.get('snapshot_id'),'recommendation':rec.get('snapshot_id')},sort_keys=True)
 payload=PortfolioIntelligence('1.0',application_version(),generated,hashlib.sha256(seed.encode()).hexdigest()[:20],'COMPLETE' if not warnings else 'PARTIAL',str(cap.get('currency') or 'USDT'),health,div,eff,total,allocated,reserved,deployable,allocation_pct,reserve_pct,available_pct,nextp,tuple(positions),overlap,tuple(warnings)).to_dict()
 return payload
def main():
 p=build();OUTPUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Portfolio intelligence written: {OUTPUT}');return 0
if __name__=='__main__':raise SystemExit(main())
