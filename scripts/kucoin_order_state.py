#!/usr/bin/env python3
"""V57 read-only KuCoin Spot order-state collector.

Uses current symbol-aware HF Spot endpoints. The previous account-wide request
could return "Symbol can't be empty"; V57 queries a bounded relevant-symbol scope.
"""
from __future__ import annotations
import json,os,time,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
from app.release import application_version
from scripts.kucoin_fill_ledger import bases,versions,sign_headers
from scripts.kucoin_symbol_scope import symbols

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'kucoin_order_state.json'
ACTIVE='/api/v1/hf/orders/active/page';DONE='/api/v1/hf/orders/done'

def now():return datetime.now(timezone.utc).isoformat()
def creds():return tuple(os.getenv(x,'').strip() for x in ('KUCOIN_API_KEY','KUCOIN_API_SECRET','KUCOIN_API_PASSPHRASE'))

def fetch(path,params):
 key,secret,pp=creds()
 if not(key and secret and pp):return None,'NOT_CONFIGURED','KuCoin read-only API credentials unavailable.'
 attempts=[]
 for base in bases():
  for ver in versions():
   query=urllib.parse.urlencode(params)
   try:
    req=urllib.request.Request(base+path+('?' + query if query else ''),headers=sign_headers('GET',path,query,key,secret,pp,ver),method='GET')
    with urllib.request.urlopen(req,timeout=20) as r:p=json.loads(r.read().decode('utf-8'))
    if p.get('code')!='200000':
     # Application-level request errors are not evidence of an authentication/region failure.
     msg=str(p.get('msg') or p.get('code'))
     return None,'REQUEST_ERROR',json.dumps({'base':base,'key_version':ver,'endpoint':path,'detail':msg})
    data=p.get('data')
    items=data.get('items') if isinstance(data,dict) else data
    return list(items or []),'OK',f'{base} key-v{ver}'
   except Exception as exc:
    attempts.append({'base':base,'key_version':ver,'category':type(exc).__name__,'detail':str(exc)[:500]})
 return None,'ERROR',json.dumps({'endpoint':path,'attempts':attempts,'last_error':attempts[-1]['detail'] if attempts else 'request failed'})

def collect_symbol(sym,start,end):
 active,sa,ma=fetch(ACTIVE,{'symbol':sym,'pageNum':1,'pageSize':100})
 done,sd,md=fetch(DONE,{'symbol':sym,'startAt':start,'endAt':end,'limit':100})
 return {'symbol':sym,'active':active or [],'done':done or [],'active_status':sa,'done_status':sd,'messages':{'active':ma,'closed':md}}

def main():
 end=int(time.time()*1000);start=int((datetime.now(timezone.utc)-timedelta(days=7)).timestamp()*1000)
 scope=symbols();per=[];active=[];done=[]
 for sym in scope:
  row=collect_symbol(sym,start,end);per.append(row);active.extend(row['active']);done.extend(row['done'])
 statuses=[x[k] for x in per for k in ('active_status','done_status')]
 if not scope:overall='NO_SYMBOL_SCOPE'
 elif statuses and all(x=='OK' for x in statuses):overall='OK'
 elif statuses and all(x=='NOT_CONFIGURED' for x in statuses):overall='NOT_CONFIGURED'
 else:overall='DEGRADED'
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':now(),'status':overall,
  'scope_symbols':scope,'symbols_checked':len(scope),'active_orders':active,'recent_closed_orders':done,
  'active_count':len(active),'recent_closed_count':len(done),'per_symbol':per,
  'active_endpoint':ACTIVE,'closed_endpoint':DONE,'api_permission':'General/read-only',
  'diagnosis':('Symbol-aware collection healthy.' if overall=='OK' else 'One or more symbol-specific KuCoin order requests need attention.'),
  'read_only':True,'write_endpoints_implemented':False}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f'KuCoin order state: {overall}; symbols={len(scope)} active={len(active)} recent_closed={len(done)}')
 return 0

if __name__=='__main__':raise SystemExit(main())
