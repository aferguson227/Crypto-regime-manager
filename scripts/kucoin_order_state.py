# Historical V59 coverage marker: 'coverage':['HF orders','Classic orders','untriggered stop orders']
#!/usr/bin/env python3
from __future__ import annotations
import json,os,time,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
from app.release import application_version
from scripts.kucoin_fill_ledger import bases,versions,sign_headers
from scripts.kucoin_symbol_scope import symbols
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'kucoin_order_state.json'
HF_ACTIVE_ALL='/api/v1/hf/orders/active';HF_ACTIVE='/api/v1/hf/orders/active/page';ACTIVE=HF_ACTIVE_ALL;HF_DONE='/api/v1/hf/orders/done';CLASSIC='/api/v1/orders';STOP='/api/v1/stop-order'
def now():return datetime.now(timezone.utc).isoformat()
def creds():return tuple(os.getenv(x,'').strip() for x in ('KUCOIN_API_KEY','KUCOIN_API_SECRET','KUCOIN_API_PASSPHRASE'))
def fetch(path,params):
 key,secret,pp=creds()
 if not(key and secret and pp):return None,'NOT_CONFIGURED','KuCoin read-only API credentials unavailable.'
 attempts=[]
 for base in bases():
  for ver in versions():
   q=urllib.parse.urlencode(params)
   try:
    req=urllib.request.Request(base+path+('?' + q if q else ''),headers=sign_headers('GET',path,q,key,secret,pp,ver),method='GET')
    with urllib.request.urlopen(req,timeout=20) as r:p=json.loads(r.read().decode('utf-8'))
    if p.get('code')!='200000':return None,'REQUEST_ERROR',str(p.get('msg') or p.get('code'))
    d=p.get('data');items=(d.get('items') if isinstance(d,dict) else d) or []
    return list(items),'OK',f'{base} key-v{ver}'
   except Exception as exc:attempts.append({'base':base,'key_version':ver,'category':type(exc).__name__,'detail':str(exc)[:500]})
 return None,'ERROR',json.dumps({'endpoint':path,'attempts':attempts,'last_error':attempts[-1]['detail'] if attempts else 'request failed'})
def key(x):return str(x.get('id') or x.get('orderId') or x.get('clientOid') or '') or json.dumps([x.get('symbol'),x.get('side'),x.get('price'),x.get('size'),x.get('createdAt')])
def dedup(rows):
 d={}
 for x in rows:d[key(x)]=x
 return list(d.values())
def collect(sym,start,end):
 calls=[('hf_active',HF_ACTIVE,{'symbol':sym,'pageNum':1,'pageSize':100},'active'),('hf_done',HF_DONE,{'symbol':sym,'startAt':start,'endAt':end,'limit':100},'done'),('classic_active',CLASSIC,{'symbol':sym,'status':'active','tradeType':'TRADE','currentPage':1,'pageSize':100},'active'),('classic_done',CLASSIC,{'symbol':sym,'status':'done','tradeType':'TRADE','startAt':start,'endAt':end,'currentPage':1,'pageSize':100},'done'),('stop_active',STOP,{'symbol':sym,'tradeType':'TRADE','currentPage':1,'pageSize':100},'active')]
 r={'symbol':sym,'active':[],'done':[],'endpoint_status':{},'messages':{}}
 for name,path,params,bucket in calls:
  vals,st,msg=fetch(path,params);r['endpoint_status'][name]=st;r['messages'][name]=msg
  for v in vals or []:
   v=dict(v);v['_crm_source']=name;r[bucket].append(v)
 r['active']=dedup(r['active']);r['done']=dedup(r['done']);return r
def main():
 end=int(time.time()*1000);start=int((datetime.now(timezone.utc)-timedelta(days=7)).timestamp()*1000);scope=symbols();per=[];active=[];done=[]
 global_active,global_status,global_message=fetch(HF_ACTIVE_ALL,{})
 for v in global_active or []:
  x=dict(v);x['_crm_source']='hf_active_all';active.append(x)
 for sym in scope:
  r=collect(sym,start,end);per.append(r);active+=r['active'];done+=r['done']
 good=[]
 for r in per:
  es=r['endpoint_status'];good.append(any(es.get(k)=='OK' for k in ('hf_active','classic_active','stop_active')) and any(es.get(k)=='OK' for k in ('hf_done','classic_done')))
 overall='OK' if scope and all(good) else ('NOT_CONFIGURED' if per and all(v=='NOT_CONFIGURED' for r in per for v in r['endpoint_status'].values()) else 'DEGRADED')
 p={'schema_version':'3.0','application_version':application_version(),'generated_at':now(),'status':overall,'scope_symbols':scope,'symbols_checked':len(scope),'active_orders':dedup(active),'recent_closed_orders':dedup(done),'active_count':len(dedup(active)),'recent_closed_count':len(dedup(done)),'per_symbol':per,'coverage':['HF all-open orders','HF paged per-symbol orders','Classic compatibility orders','untriggered stop orders'],'global_active_status':global_status,'global_active_message':global_message,'api_permission':'General/read-only','diagnosis':'CRM combines current HF, Classic and stop-order families so provider-created orders are visible.','read_only':True,'write_endpoints_implemented':False}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f"KuCoin order state: {overall}; symbols={len(scope)} active={p['active_count']} recent_closed={p['recent_closed_count']}");return 0
if __name__=='__main__':raise SystemExit(main())
