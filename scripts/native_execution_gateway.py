#!/usr/bin/env python3
"""V52 native KuCoin execution gateway — deliberately locked.

This module establishes the future direct-execution contract (clientOid,
validation, kill switch, endpoint selection and idempotency lookup) but V52 cannot
submit or cancel a live order. That lock is intentional and regression-tested.
"""
from __future__ import annotations
import hashlib,json,os,re,uuid
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];POL=ROOT/'config'/'v52_execution_assurance_policy.json'
CLIENT_RE=re.compile(r'^[A-Za-z0-9_-]{8,64}$')
@dataclass(frozen=True)
class IntendedOrder:
 symbol:str;side:str;order_type:str;size:str|None=None;funds:str|None=None;price:str|None=None;time_in_force:str='GTC';role:str='ORDER'
def policy():
 return json.loads(POL.read_text(encoding='utf-8-sig'))
def deterministic_client_oid(asset:str,deal_token:str,role:str,ordinal:int=0)->str:
 seed=f'{asset.upper()}|{deal_token}|{role}|{ordinal}'
 digest=hashlib.sha256(seed.encode()).hexdigest()[:24]
 return f"crm52-{asset.lower()}-{digest}"[:64]
def validate(order:IntendedOrder):
 if not order.symbol.endswith('-USDT'):raise ValueError('V52 native preparation supports USDT Spot pairs only.')
 if order.side not in {'buy','sell'}:raise ValueError('side must be buy or sell')
 if order.order_type not in {'limit','market'}:raise ValueError('order type must be limit or market')
 if order.order_type=='limit' and (not order.price or not order.size):raise ValueError('limit orders require price and size')
 if order.order_type=='market' and not(order.size or order.funds):raise ValueError('market order requires size or funds')
 return True
def build_payload(order:IntendedOrder,client_oid:str):
 validate(order)
 if not CLIENT_RE.match(client_oid):raise ValueError('invalid clientOid')
 p={'clientOid':client_oid,'symbol':order.symbol,'type':order.order_type,'side':order.side,'remark':'crm-shadow'}
 if order.size:p['size']=str(order.size)
 if order.funds:p['funds']=str(order.funds)
 if order.price:p['price']=str(order.price)
 if order.order_type=='limit':p['timeInForce']=order.time_in_force
 return p
def live_writes_locked()->bool:
 p=policy().get('native_execution') or {}
 return not bool(p.get('manual_live_orders')) or not bool(p.get('automatic_live_orders'))
def submit_live_order(*args,**kwargs):
 raise RuntimeError('V52 LIVE ORDER LOCK: native KuCoin submission is intentionally disabled until a later guarded-execution release.')
def cancel_live_order(*args,**kwargs):
 raise RuntimeError('V52 LIVE ORDER LOCK: native KuCoin cancellation is intentionally disabled until a later guarded-execution release.')
if __name__=='__main__':
 print('V52 native execution gateway: LOCKED_SHADOW; live submission/cancellation unavailable.')
