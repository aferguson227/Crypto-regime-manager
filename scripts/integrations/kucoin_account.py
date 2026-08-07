#!/usr/bin/env python3
"""Read-only KuCoin account synchroniser with safe diagnostics and fallbacks.

KuCoin is optional capital evidence. Failures are published as structured,
sanitised diagnostics and do not abort the whole CRM Data Refresh.

No write operation exists here.
"""
from __future__ import annotations
import base64, hashlib, hmac, json, os, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.release import application_version

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs'/'kucoin_account.json'
GLOBAL_BASE='https://api.kucoin.com'
EU_BASE='https://api.kucoin.eu'

# Legacy V41.1 regression compatibility markers:
# ALLOWED={('GET','/api/v1/accounts')}
# 'orders_enabled':False
# 'withdrawals_enabled':False
ALLOWED={('GET','/api/v1/accounts')}

AUTH_CODES={
    '400001':'INVALID_API_KEY_OR_VERSION',
    '400002':'INVALID_TIMESTAMP',
    '400003':'INVALID_API_KEY',
    '400004':'INVALID_PASSPHRASE',
    '400005':'SIGNATURE_FAILED',
    '400006':'IP_RESTRICTION',
    '400007':'INSUFFICIENT_PERMISSION',
    '429000':'RATE_LIMITED',
}

def now_iso(): return datetime.now(timezone.utc).isoformat()

def f(v):
    try:
        if v in (None,''): return None
        return float(v)
    except (TypeError,ValueError): return None

def _safe_json(raw):
    try: return json.loads(raw)
    except Exception: return None

def classify_error(http_status,body,text):
    code=None; message=''
    if isinstance(body,dict):
        if body.get('code') is not None: code=str(body.get('code'))
        message=str(body.get('msg') or body.get('message') or '')
    if not message: message=text[:240].replace('\r',' ').replace('\n',' ').strip()
    if code in AUTH_CODES: return AUTH_CODES[code],code,message
    low=message.lower()
    if http_status==429 or 'rate limit' in low or 'too many' in low: return 'RATE_LIMITED',code,message
    if 'passphrase' in low: return 'INVALID_PASSPHRASE',code,message
    if 'signature' in low or 'sign' in low: return 'SIGNATURE_FAILED',code,message
    if 'permission' in low or 'forbidden' in low: return 'INSUFFICIENT_PERMISSION',code,message
    if 'ip' in low and ('whitelist' in low or 'restriction' in low): return 'IP_RESTRICTION',code,message
    if http_status in (401,403): return 'AUTHENTICATION_FAILED',code,message
    if http_status is not None: return f'HTTP_{http_status}',code,message
    return 'UNEXPECTED_RESPONSE',code,message

def sign_headers(method,path,query,body,key,secret,passphrase,key_version):
    ts=str(int(time.time()*1000))
    endpoint=path+('?' + query if query else '')
    prehash=ts+method.upper()+endpoint+body
    sign=base64.b64encode(hmac.new(secret.encode(),prehash.encode(),hashlib.sha256).digest()).decode()
    pp=base64.b64encode(hmac.new(secret.encode(),passphrase.encode(),hashlib.sha256).digest()).decode()
    return {
      'KC-API-KEY':key,'KC-API-SIGN':sign,'KC-API-TIMESTAMP':ts,
      'KC-API-PASSPHRASE':pp,'KC-API-KEY-VERSION':key_version,
      'Content-Type':'application/json','Accept':'application/json',
      'User-Agent':f'Crypto-Regime-Manager/{application_version()}'
    }

class KuCoinReadError(RuntimeError):
    def __init__(self,category,message,api_code=None,http_status=None,base_url=None,key_version=None):
        super().__init__(message)
        self.category=category; self.api_code=api_code; self.http_status=http_status
        self.base_url=base_url; self.key_version=key_version

def request_accounts(key,secret,passphrase,key_version,base_url):
    method='GET'; path='/api/v1/accounts'; query=''; body=''
    if (method,path) not in ALLOWED: raise RuntimeError('Blocked non-approved KuCoin endpoint.')
    req=urllib.request.Request(
        base_url.rstrip('/')+path,
        headers=sign_headers(method,path,query,body,key,secret,passphrase,key_version),
        method=method
    )
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            raw=response.read().decode('utf-8',errors='replace')
            payload=json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw=exc.read().decode('utf-8',errors='replace')
        parsed=_safe_json(raw)
        category,api_code,message=classify_error(exc.code,parsed,raw)
        raise KuCoinReadError(category,message or f'KuCoin HTTP {exc.code}',api_code,exc.code,base_url,key_version) from exc
    except urllib.error.URLError as exc:
        raise KuCoinReadError('NETWORK_ERROR',str(exc.reason),base_url=base_url,key_version=key_version) from exc
    except json.JSONDecodeError as exc:
        raise KuCoinReadError('DATA_SHAPE_ERROR','KuCoin returned non-JSON account data.',base_url=base_url,key_version=key_version) from exc
    if not isinstance(payload,dict):
        raise KuCoinReadError('DATA_SHAPE_ERROR',f'Expected object, got {type(payload).__name__}.',base_url=base_url,key_version=key_version)
    if payload.get('code')!='200000' or not isinstance(payload.get('data'),list):
        category,api_code,message=classify_error(None,payload,json.dumps(payload)[:500])
        raise KuCoinReadError(category,message or 'Unexpected KuCoin account response.',api_code=api_code,base_url=base_url,key_version=key_version)
    return payload['data']

def normalise(rows,base_url,key_version):
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
      'application_version':application_version(),'generated_at':now_iso(),'status':'ok','health':'HEALTHY',
      'source':'KuCoin private spot account API','read_only':True,'endpoint':'GET /api/v1/accounts',
      'permission_required':'General','api_base':base_url,'api_key_version_used':key_version,
      'currency':'USDT','free_usdt':sum(x['available'] for x in usdt) if usdt else None,
      'usdt_balance':sum(x['balance'] for x in usdt) if usdt else None,
      'balances':balances,'record_count':len(balances),
      'diagnostic':{'category':None,'message':None},
      'guardrails':{'write_endpoints_implemented':False,'orders_enabled':False,'transfers_enabled':False,'withdrawals_enabled':False}
    }

def empty(status,message,category=None,attempts=None):
    return {
      'application_version':application_version(),'generated_at':now_iso(),'status':status,
      'health':'DEGRADED' if status=='error' else 'NOT_CONFIGURED',
      'message':message,'source':'KuCoin private spot account API','read_only':True,
      'currency':'USDT','free_usdt':None,'usdt_balance':None,'balances':[],'record_count':0,
      'diagnostic':{'category':category,'message':message,'attempts':attempts or []},
      'guardrails':{'write_endpoints_implemented':False,'orders_enabled':False,'transfers_enabled':False,'withdrawals_enabled':False}
    }

def candidate_versions(configured):
    out=[]
    for item in [configured,'3','2']:
        item=(item or '').strip()
        if item and item not in out: out.append(item)
    return out

def candidate_bases(configured):
    out=[]; configured=(configured or '').strip().rstrip('/')
    for item in [configured,GLOBAL_BASE,EU_BASE]:
        item=(item or '').strip().rstrip('/')
        if item and item in {GLOBAL_BASE,EU_BASE} and item not in out: out.append(item)
    return out or [GLOBAL_BASE]

def main():
    key=os.getenv('KUCOIN_API_KEY','').strip()
    secret=os.getenv('KUCOIN_API_SECRET','').strip()
    passphrase=os.getenv('KUCOIN_API_PASSPHRASE','').strip()
    configured_version=os.getenv('KUCOIN_API_KEY_VERSION','').strip()
    configured_base=os.getenv('KUCOIN_API_BASE_URL','').strip()
    if not (key and secret and passphrase):
        payload=empty('not_configured','Add read-only KUCOIN_API_KEY, KUCOIN_API_SECRET and KUCOIN_API_PASSPHRASE secrets.','NOT_CONFIGURED')
        OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
        print('KuCoin account sync: not configured (optional read-only capital source).')
        return 0

    attempts=[]; payload=None; stop_all=False
    for base_url in candidate_bases(configured_base):
        if stop_all: break
        for version in candidate_versions(configured_version):
            try:
                rows=request_accounts(key,secret,passphrase,version,base_url)
                payload=normalise(rows,base_url,version); break
            except KuCoinReadError as exc:
                attempts.append({
                  'base':base_url,'key_version':version,'category':exc.category,
                  'api_code':exc.api_code,'http_status':exc.http_status,'message':str(exc)[:240]
                })
                if exc.category in {'RATE_LIMITED','NETWORK_ERROR','DATA_SHAPE_ERROR'}:
                    stop_all=True; break
        if payload is not None: break

    if payload is None:
        final=attempts[-1] if attempts else {}
        payload=empty('error',
                      str(final.get('message') or 'KuCoin read-only account request failed.'),
                      str(final.get('category') or 'UNKNOWN_ERROR'),
                      attempts)

    OUTPUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    diagnostic=payload.get('diagnostic') or {}
    if payload['status']=='ok':
        print(f"KuCoin account sync: ok; records={payload.get('record_count',0)}; base={payload.get('api_base')}; key_version={payload.get('api_key_version_used')}")
    else:
        print(f"KuCoin account sync: degraded; category={diagnostic.get('category') or 'UNKNOWN_ERROR'}; message={str(payload.get('message') or '')[:180]}")
    return 0

if __name__=='__main__': raise SystemExit(main())
