#!/usr/bin/env python3
"""V51 read-only KuCoin Spot order-state collector."""
from __future__ import annotations
import json,os,time,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
from app.release import application_version
from scripts.kucoin_fill_ledger import bases,versions,sign_headers
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'kucoin_order_state.json'
ACTIVE='/api/v1/hf/orders/active';DONE='/api/v1/hf/orders/done'
def now():return datetime.now(timezone.utc).isoformat()
def creds():
 return tuple(os.getenv(x,'').strip() for x in ('KUCOIN_API_KEY','KUCOIN_API_SECRET','KUCOIN_API_PASSPHRASE'))
def fetch(path,params):
 key,secret,pp=creds()
 if not(key and secret and pp):return None,'NOT_CONFIGURED','KuCoin read-only API credentials unavailable.'
 last=None;attempts=[]
 for base in bases():
  for ver in versions():
   try:
    query=urllib.parse.urlencode(params)
    req=urllib.request.Request(base+path+('?' + query if query else ''),headers=sign_headers('GET',path,query,key,secret,pp,ver),method='GET')
    with urllib.request.urlopen(req,timeout=20) as r:p=json.loads(r.read().decode('utf-8'))
    if p.get('code')!='200000':raise RuntimeError(str(p.get('msg') or p.get('code')))
    data=p.get('data')
    items=data.get('items') if isinstance(data,dict) else data
    return list(items or []),'OK',f'{base} key-v{ver}'
   except Exception as exc:
    last=exc;attempts.append({'base':base,'key_version':ver,'category':type(exc).__name__,'detail':str(exc)[:500]})
 return None,'ERROR',json.dumps({'endpoint':path,'attempts':attempts,'last_error':str(last or 'request failed')})
def main():
 end=int(time.time()*1000);start=int((datetime.now(timezone.utc)-timedelta(days=7)).timestamp()*1000)
 active,sa,ma=fetch(ACTIVE,{})
 done,sd,md=fetch(DONE,{'startAt':start,'endAt':end,'limit':100})
 overall='OK' if sa=='OK' and sd=='OK' else ('NOT_CONFIGURED' if sa=='NOT_CONFIGURED' and sd=='NOT_CONFIGURED' else 'DEGRADED')
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'status':overall,
  'active_orders':active or [],'recent_closed_orders':done or [],'active_count':len(active or []),'recent_closed_count':len(done or []),
  'active_endpoint':ACTIVE,'closed_endpoint':DONE,'api_permission':'General/read-only',
  'messages':{'active':ma,'closed':md},'read_only':True,'write_endpoints_implemented':False}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'KuCoin order state: {overall}; active={p["active_count"]}; recent_closed={p["recent_closed_count"]}');return 0
if __name__=='__main__':raise SystemExit(main())
