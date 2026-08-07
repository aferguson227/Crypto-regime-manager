#!/usr/bin/env python3
"""Read-only KuCoin spot-account synchroniser.

Only GET /api/v1/accounts is implemented. Use a dedicated API key with General
(read-only) permission. No order, transfer or withdrawal operation exists here.
"""
from __future__ import annotations
import base64, hashlib, hmac, json, os, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.release import application_version

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs'/'kucoin_account.json'
DEFAULT_BASE='https://api.kucoin.com'
ALLOWED={('GET','/api/v1/accounts')}

def now_iso(): return datetime.now(timezone.utc).isoformat()

def f(v):
    try:
        if v in (None,''): return None
        return float(v)
    except (TypeError,ValueError): return None

def sign_headers(method:str,path:str,query:str,body:str,key:str,secret:str,passphrase:str,key_version:str)->dict[str,str]:
    ts=str(int(time.time()*1000))
    endpoint=path+('?' + query if query else '')
    prehash=ts+method.upper()+endpoint+body
    sign=base64.b64encode(hmac.new(secret.encode(),prehash.encode(),hashlib.sha256).digest()).decode()
    pp=base64.b64encode(hmac.new(secret.encode(),passphrase.encode(),hashlib.sha256).digest()).decode()
    return {
      'KC-API-KEY':key,'KC-API-SIGN':sign,'KC-API-TIMESTAMP':ts,
      'KC-API-PASSPHRASE':pp,'KC-API-KEY-VERSION':key_version,
      'Accept':'application/json','User-Agent':f'Crypto-Regime-Manager/{application_version()}'
    }

def request_accounts(key:str,secret:str,passphrase:str,key_version:str='2',base_url:str=DEFAULT_BASE):
    method='GET'; path='/api/v1/accounts'; query=''; body=''
    if (method,path) not in ALLOWED: raise RuntimeError('Blocked non-approved KuCoin endpoint.')
    req=urllib.request.Request(base_url.rstrip('/')+path,headers=sign_headers(method,path,query,body,key,secret,passphrase,key_version),method=method)
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            payload=json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        detail=exc.read().decode('utf-8',errors='replace')[:500]
        raise RuntimeError(f'KuCoin HTTP {exc.code}: {detail}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'KuCoin connection failed: {exc.reason}') from exc
    if payload.get('code')!='200000' or not isinstance(payload.get('data'),list):
        raise RuntimeError(f'Unexpected KuCoin account response: {payload}')
    return payload['data']

def normalise(rows:list[dict[str,Any]])->dict[str,Any]:
    balances=[]
    for r in rows:
        if not isinstance(r,dict): continue
        balances.append({
          'currency':str(r.get('currency') or '').upper(),
          'account_type':r.get('type'),
          'balance':f(r.get('balance')) or 0.0,
          'available':f(r.get('available')) or 0.0,
          'holds':f(r.get('holds')) or 0.0,
        })
    usdt=[x for x in balances if x['currency']=='USDT']
    return {
      'application_version':application_version(),'generated_at':now_iso(),'status':'ok',
      'source':'KuCoin private spot account API','read_only':True,'endpoint':'GET /api/v1/accounts',
      'permission_required':'General','currency':'USDT',
      'free_usdt':sum(x['available'] for x in usdt) if usdt else None,
      'usdt_balance':sum(x['balance'] for x in usdt) if usdt else None,
      'balances':balances,'record_count':len(balances),
      'guardrails':{'write_endpoints_implemented':False,'orders_enabled':False,'transfers_enabled':False,'withdrawals_enabled':False}
    }

def empty(status:str,message:str):
    return {'application_version':application_version(),'generated_at':now_iso(),'status':status,'message':message,'source':'KuCoin private spot account API','read_only':True,'currency':'USDT','free_usdt':None,'usdt_balance':None,'balances':[],'record_count':0,'guardrails':{'write_endpoints_implemented':False}}

def main()->int:
    key=os.getenv('KUCOIN_API_KEY','').strip()
    secret=os.getenv('KUCOIN_API_SECRET','').strip()
    passphrase=os.getenv('KUCOIN_API_PASSPHRASE','').strip()
    key_version=os.getenv('KUCOIN_API_KEY_VERSION','2').strip() or '2'
    base=os.getenv('KUCOIN_API_BASE_URL',DEFAULT_BASE).strip() or DEFAULT_BASE
    if not (key and secret and passphrase):
        payload=empty('not_configured','Add read-only KUCOIN_API_KEY, KUCOIN_API_SECRET and KUCOIN_API_PASSPHRASE secrets to enable direct capital intelligence.')
        OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
        print('KuCoin account sync: not configured (optional read-only capital source).')
        return 0
    try:
        payload=normalise(request_accounts(key,secret,passphrase,key_version,base)); rc=0
    except Exception as exc:
        payload=empty('error',str(exc)); rc=1
    OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(f"KuCoin account sync: {payload['status']}; records={payload.get('record_count',0)}")
    return rc

if __name__=='__main__': raise SystemExit(main())
