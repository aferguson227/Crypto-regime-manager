#!/usr/bin/env python3
"""V64 persistent terminal-resolution cache."""
from __future__ import annotations
import json,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs'
def root():
 raw=os.getenv('CRM_DATA_ROOT')
 p=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 q=p/'state';q.mkdir(parents=True,exist_ok=True);return q
def load(p):
 try:return json.loads(Path(p).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 old=load(root()/'terminal_resolutions.json');items=old.get('items') or {}
 cont=load(D/'cross_exchange_continuation.json')
 for x in cont.get('assets') or []:
  if x.get('terminal'):
   items['continuation:'+str(x.get('asset'))]={'kind':'continuation','asset':x.get('asset'),'status':x.get('continuation_status'),'resolved_at':cont.get('generated_at'),'evidence':x}
 fills=load(D/'kucoin_fill_ledger.json')
 if fills.get('realised_profit_status')=='HISTORICAL_COST_BASIS_UNAVAILABLE':
  items['accounting:baseline']={'kind':'accounting_baseline','status':'ESTABLISHED','resolved_at':fills.get('generated_at'),'limitation':fills.get('accounting_limitation')}
 p={'schema_version':'1.0','application_version':application_version(),'updated_at':datetime.now(timezone.utc).isoformat(),'items':items,
    'principle':'Terminal evidence and accounting-baseline decisions survive upgrades and are not restarted merely because CRM is reinstalled.'}
 (root()/'terminal_resolutions.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
 (D/'resolution_state_status.json').write_text(json.dumps({'schema_version':'1.0','application_version':application_version(),'generated_at':p['updated_at'],'persistent_path':str(root()/'terminal_resolutions.json'),'terminal_items':len(items)},indent=2),encoding='utf-8')
 print('Persistent resolution cache:',len(items));return 0
if __name__=='__main__':raise SystemExit(main())
