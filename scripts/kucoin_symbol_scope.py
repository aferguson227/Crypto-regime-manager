#!/usr/bin/env python3
"""Shared symbol scope for read-only KuCoin order/fill collectors.

KuCoin's current HF Spot order/fill APIs behave reliably when queried per symbol.
CRM derives a bounded symbol set from actual balances, live bots, live trades and
the research/deployment registry. No write permission is required.
"""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'

def load(name):
 try:
  x=json.loads((DOCS/name).read_text(encoding='utf-8-sig'));return x if isinstance(x,dict) else {}
 except:return {}

def asset(v):
 s=str(v or '').upper().replace('/','-')
 if s.endswith('-USDT'):return s[:-5]
 if s.endswith('USDT') and '-' not in s:return s[:-4]
 return s.split('-')[0] if s else ''

def symbols(limit=60):
 out=[]
 def add(a):
  a=asset(a)
  if not a or a in {'USDT','USD','USDC'}:return
  sym=f'{a}-USDT'
  if sym not in out:out.append(sym)

 # Current KuCoin balances first, so recently traded/live holdings are guaranteed scope.
 ku=load('kucoin_account.json')
 for row in ku.get('balances') or []:
  cur=row.get('currency') or row.get('coin') or row.get('asset')
  bal=row.get('balance',row.get('total',row.get('available',0)))
  try:nonzero=float(bal or 0)>0
  except:nonzero=True
  if nonzero:add(cur)

 # Live/reconciled trades and production bot profiles.
 for row in (load('live_portfolio_truth.json').get('deals') or []):add(row.get('asset') or row.get('pair'))
 for row in (load('live_bot_profiles.json').get('bots') or []):add(row.get('asset') or row.get('pair'))
 for row in (load('threecommas.json').get('deals') or []):add(row.get('asset') or row.get('pair') or row.get('symbol'))

 # Deployment/research candidates provide recent-order visibility for staged assets too.
 for row in (load('candidate_review.json').get('candidates') or []):add(row.get('asset') or row.get('pair'))
 for row in (load('coin_registry.json').get('coins') or []):add(row.get('asset') or row.get('pair'))
 for row in (load('recommended_bots.json').get('bots') or []):add(row.get('asset') or row.get('pair'))

 # TEL is the current production strategy and must never fall out of scope.
 add('TEL')
 return out[:max(1,int(limit))]

if __name__=='__main__':
 print('\n'.join(symbols()))
