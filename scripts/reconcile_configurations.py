#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from app.models.source_metadata import build_metadata
from app.models.operating_categories import OperatingCategory
FIELDS={
 'take_profit_pct':'take_profit_pct','so_deviation_pct':'safety_order_deviation_pct',
 'safety_orders':'max_safety_orders','volume_scale':'volume_scale','step_scale':'step_scale'
}
def equal(a,b):
    if isinstance(a,(int,float)) and isinstance(b,(int,float)): return abs(float(a)-float(b))<1e-9
    return a==b

def main():
    cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    live_path=ROOT/'docs'/'threecommas.json'
    live=json.loads(live_path.read_text(encoding='utf-8')) if live_path.exists() else {'assets':{},'status':'missing'}
    rows=[]
    for asset in cfg.get('assets',[]):
      symbol=asset['id']
      live_bots=live.get('assets',{}).get(symbol,{}).get('bots',[])
      by_name={b.get('name'):b for b in live_bots}
      for regime,prod in asset.get('bots',{}).items():
        if prod.get('enabled') is False: continue
        lb=by_name.get(prod.get('name'))
        comparisons=[]
        for pk,lk in FIELDS.items():
          pv=prod.get(pk); lv=lb.get(lk) if lb else None
          status='MATCH' if lb and equal(pv,lv) else ('MISSING_FROM_3COMMAS' if not lb or lv is None else 'DIFFERENT')
          comparisons.append({'field':pk,'production_value':pv,'live_value':lv,'status':status})
        rows.append({'asset':symbol,'regime':regime,'bot_name':prod.get('name'),
          'production_category':OperatingCategory.PRODUCTION_CONFIGURATION,
          'live_category':OperatingCategory.LIVE_3COMMAS_CONFIGURATION,
          'live_bot_found':bool(lb),'comparisons':comparisons})
    out={'metadata':build_metadata('config.json + docs/threecommas.json',status='fresh' if live.get('status')=='ok' else 'incomplete',warnings=[] if live.get('status')=='ok' else ['Live 3Commas data unavailable or incomplete']),
      'read_only':True,'deployment_recommendations_enabled':True,'reconciliations':rows}
    path=ROOT/'docs'/'configuration_reconciliation.json'; path.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(path)
if __name__=='__main__': main()
