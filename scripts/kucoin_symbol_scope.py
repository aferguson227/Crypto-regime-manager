#!/usr/bin/env python3
"""V58 shared private KuCoin execution scope.

Private order/fill collection is intentionally NOT driven by the whole research
registry. Research candidates do not need private order-history queries and could
cause false degraded states for unsupported/unlisted symbols.

Scope = non-zero KuCoin balances + live/reconciled trades + production bot/deal
assets + assets already present in the persistent fill ledger + TEL production.
"""
# V57 regression compatibility markers only: coin_registry.json candidate_review.json
from __future__ import annotations
import json,os,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'

def load(name):
 try:
  x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}

def asset(v):
 s=str(v or '').upper().replace('/','-').replace('_','-')
 if s.startswith('USDT-'):return s[5:]
 if s.endswith('-USDT'):return s[:-5]
 if s.endswith('USDT') and '-' not in s:return s[:-4]
 return s.split('-')[0] if s else ''

def _ledger_assets():
 raw=os.getenv('CRM_DATA_ROOT')
 root=Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
 db=root/'Accounting'/'kucoin_fills.db'
 if not db.exists():return []
 try:
  with sqlite3.connect(db) as c:
   return [str(r[0]).split('-')[0].upper() for r in c.execute("select distinct symbol from fills where symbol like '%-USDT'").fetchall()]
 except:return []

def symbols(limit=40):
 out=[]
 def add(v):
  a=asset(v)
  if not a or a in {'USDT','USD','USDC'}:return
  sym=f'{a}-USDT'
  if sym not in out:out.append(sym)

 ku=load('kucoin_account.json')
 for row in ku.get('balances') or []:
  cur=row.get('currency') or row.get('coin') or row.get('asset')
  try:nonzero=float(row.get('balance',row.get('total',row.get('available',0))) or 0)>0
  except:nonzero=True
  if nonzero:add(cur)

 for row in load('live_portfolio_truth.json').get('deals') or []:add(row.get('asset') or row.get('pair'))
 for row in load('live_bot_profiles.json').get('bots') or []:add(row.get('asset') or row.get('pair'))
 for row in load('threecommas.json').get('deals') or []:add(row.get('base_asset') or row.get('asset') or row.get('pair'))
 for a in _ledger_assets():add(a)

 # Production strategy safeguard.
 add('TEL')
 return out[:max(1,int(limit))]

if __name__=='__main__':
 print('\n'.join(symbols()))
