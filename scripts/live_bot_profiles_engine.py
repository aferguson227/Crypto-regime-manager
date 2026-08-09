#!/usr/bin/env python3
"""V51 per-live-bot settings/regime profiles for compact Dashboard accordions."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'live_bot_profiles.json'
def load(n):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 tc=load('threecommas.json');wf=load('kucoin_walk_forward.json');rb=load('regime_backtest_intelligence.json');gm=load('global_market.json')
 wfby={str(x.get('asset') or '').upper():x for x in wf.get('assets') or []};rbby={str(x.get('asset') or '').upper():x for x in rb.get('datasets') or []};rows=[]
 for asset,bucket in (tc.get('assets') or {}).items():
  enabled=[b for b in bucket.get('bots') or [] if b.get('enabled')]
  if not enabled and not (bucket.get('deals') or []):continue
  a=str(asset).upper();kw=wfby.get(a) or {};rr=rbby.get(a) or {};reg=str(kw.get('current_regime_family') or gm.get('regime') or 'UNKNOWN').upper()
  profiles_out={}
  source_profiles=kw.get('regime_profiles') or rr.get('regime_profiles') or {}
  for name,p in source_profiles.items():
   frozen=(p.get('frozen_training_winner') or {}) if isinstance(p,dict) else {}
   settings=frozen.get('settings') or p.get('settings') or {}
   metrics=p.get('validation_metrics') or p.get('metrics') or {}
   profiles_out[name]={'entry_trigger':frozen.get('entry_trigger') or p.get('entry_trigger'),'settings':settings,'metrics':metrics,'validated':bool(p.get('validation_pass')) if 'validation_pass' in p else str(p.get('status'))=='EXPLORATORY_PASS'}
  for b in enabled or (bucket.get('bots') or [])[:1]:
   live={'take_profit_pct':b.get('take_profit_pct'),
    'so_deviation_pct':b.get('so_deviation_pct') if b.get('so_deviation_pct') is not None else b.get('safety_order_deviation_pct'),
    'safety_orders':b.get('max_safety_orders'),'volume_scale':b.get('volume_scale'),'step_scale':b.get('step_scale'),
    'base_order_volume':b.get('base_order_volume'),'safety_order_volume':b.get('safety_order_volume'),
    'max_active_safety_orders':b.get('max_active_safety_orders'),'max_active_deals':b.get('max_active_deals'),
    'start_condition':b.get('start_condition'),'order_type':b.get('order_type') if b.get('order_type') is not None else b.get('start_order_type'),
    'trailing_enabled':b.get('trailing_enabled'),'cooldown_seconds':b.get('cooldown_seconds')}
   current=profiles_out.get(reg) or {}
   rows.append({'asset':a,'bot_id':b.get('bot_id'),'bot_name':b.get('name'),'enabled':b.get('enabled'),'current_regime':reg,'live_settings':live,
    'recommended_current_regime':current,'regime_profiles':profiles_out,'recommendation':'Use the validated current-regime profile only after manual review; an unvalidated regime means do not start a new deal automatically.'})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'bots':rows,'per_bot_settings':True,'automatic_changes':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Live bot profiles written: {OUT}; bots={len(rows)}');return 0
if __name__=='__main__':raise SystemExit(main())
