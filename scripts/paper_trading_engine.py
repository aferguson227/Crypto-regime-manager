#!/usr/bin/env python3
"""V67 persistent live paper-trading engine.

Every DCA-optimised candidate can accumulate genuine forward paper evidence against
current KuCoin prices even when no live capital is available. State persists outside
Git under CRM_Data. No exchange or provider write endpoint exists.
"""
from __future__ import annotations
import json,os,math
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'paper_portfolio.json'
FEE=0.001

def now(): return datetime.now(timezone.utc).isoformat()
def load(path,default=None):
 try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
 except:return {} if default is None else default
def data_root():
 raw=os.getenv('CRM_DATA_ROOT')
 return Path(raw) if raw else (Path(r'C:\Crypto\CRM_Data') if os.name=='nt' else Path.home()/'.crypto_regime_manager_data')
def state_path():
 p=data_root()/'state';p.mkdir(parents=True,exist_ok=True);return p/'paper_portfolio.json'
def price_map():
 d=load(D/'kucoin_live_prices.json');return {str(x.get('symbol') or '').split('-')[0].upper():x for x in d.get('prices') or [] if x.get('status')=='OK'}
def specs():
 d=load(D/'dca_deployment_specs.json')
 return {str(x.get('asset') or '').upper():x for x in d.get('specs') or [] if x.get('recommended_settings_available')}
def lifecycle():
 d=load(D/'deployment_lifecycle.json')
 return {str(x.get('asset') or '').upper():x for x in d.get('bots') or []}
def q(v):
 try:return float(v)
 except:return None
def so_trigger(entry,dev,step,index):
 # index 0 = first SO. Step scale expands incremental deviation.
 cumulative=sum(dev*(step**i) for i in range(index+1))
 return entry*(1-cumulative/100)
def add_fill(pos,quote,price,kind):
 qty=(quote*(1-FEE))/price
 pos['quantity']+=qty;pos['quote_in']+=quote;pos['fees_quote']+=quote*FEE
 pos['average_entry']=pos['quote_in']/pos['quantity'] if pos['quantity'] else price
 pos['fills'].append({'at':now(),'kind':kind,'price':price,'quote':round(quote,8),'quantity':qty})
def new_position(asset,st,price):
 bo=q(st.get('base_order_volume')) or 0
 p={'asset':asset,'state':'OPEN','opened_at':now(),'closed_at':None,'entry_price':price,'average_entry':price,
    'quantity':0.0,'quote_in':0.0,'fees_quote':0.0,'safety_orders_filled':0,'max_safety_orders':int(st.get('safety_orders') or 0),
    'fills':[],'realised_pnl_quote':0.0,'peak_capital_quote':0.0,'max_drawdown_quote':0.0,'last_price':price}
 add_fill(p,bo,price,'BASE');p['peak_capital_quote']=p['quote_in'];return p
def tick_position(pos,st,price):
 dev=q(st.get('so_deviation_pct')) or 0;step=q(st.get('step_scale')) or 1;vs=q(st.get('volume_scale')) or 1
 so=q(st.get('safety_order_volume')) or 0;maxso=int(st.get('safety_orders') or 0)
 while pos['safety_orders_filled']<maxso:
  idx=pos['safety_orders_filled'];trigger=so_trigger(pos['entry_price'],dev,step,idx)
  if price>trigger:break
  add_fill(pos,so*(vs**idx),price,f'SAFETY_{idx+1}');pos['safety_orders_filled']+=1
  pos['peak_capital_quote']=max(pos['peak_capital_quote'],pos['quote_in'])
 tp=q(st.get('take_profit_pct')) or 0
 mtm=pos['quantity']*price*(1-FEE)-pos['quote_in']
 pos['max_drawdown_quote']=min(pos.get('max_drawdown_quote',0.0),mtm);pos['last_price']=price
 if price>=pos['average_entry']*(1+tp/100):
  proceeds=pos['quantity']*price*(1-FEE);pnl=proceeds-pos['quote_in']
  pos.update(state='CLOSED',closed_at=now(),exit_price=price,realised_pnl_quote=pnl,open_pnl_quote=0.0)
  return True
 pos['open_pnl_quote']=mtm;pos['open_pnl_pct']=100*mtm/pos['quote_in'] if pos['quote_in'] else None
 return False
def main():
 old=load(state_path(),{'bots':{}});bots=old.get('bots') or {};pm=price_map();sp=specs();lc=lifecycle();changed=0
 eligible={a for a,s in sp.items() if str((lc.get(a) or {}).get('lifecycle_state') or '') not in {'ACTIVE'}}
 for asset in sorted(eligible):
  pr=pm.get(asset) or {};price=q(pr.get('price'))
  if not price:continue
  st=(sp[asset].get('recommended_dca_settings') or {})
  b=bots.setdefault(asset,{'asset':asset,'mode':'PAPER','created_at':now(),'closed_deals':0,'realised_pnl_quote':0.0,'history':[]})
  pos=b.get('position')
  if not pos or pos.get('state')=='CLOSED':
   pos=new_position(asset,st,price);b['position']=pos;changed+=1
  closed=tick_position(pos,st,price)
  if closed:
   b['closed_deals']=int(b.get('closed_deals') or 0)+1;b['realised_pnl_quote']=q(b.get('realised_pnl_quote')) or 0
   b['realised_pnl_quote']+=q(pos.get('realised_pnl_quote')) or 0
   b.setdefault('history',[]).append({k:pos.get(k) for k in ['opened_at','closed_at','entry_price','exit_price','quote_in','realised_pnl_quote','safety_orders_filled','max_drawdown_quote']})
   b['history']=b['history'][-100:];changed+=1
  b['last_price']=price;b['updated_at']=now();b['settings']=st
 # Do not delete old paper history when candidate leaves current eligibility.
 state={'schema_version':'1.0','updated_at':now(),'bots':bots,'fee_rate':FEE}
 state_path().write_text(json.dumps(state,indent=2),encoding='utf-8')
 rows=[]
 for a,b in sorted(bots.items()):
  pos=b.get('position') or {};rows.append({'asset':a,'mode':'PAPER','state':pos.get('state'),'opened_at':pos.get('opened_at'),
   'position_quote':pos.get('quote_in'),'average_entry':pos.get('average_entry'),'current_price':b.get('last_price'),
   'safety_orders_filled':pos.get('safety_orders_filled'),'max_safety_orders':pos.get('max_safety_orders'),
   'open_pnl_quote':pos.get('open_pnl_quote'),'open_pnl_pct':pos.get('open_pnl_pct'),'closed_deals':b.get('closed_deals'),
   'realised_pnl_quote':b.get('realised_pnl_quote'),'max_drawdown_quote':pos.get('max_drawdown_quote'),
   'settings':b.get('settings'),'updated_at':b.get('updated_at')})
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now(),'bots':rows,
  'summary':{'paper_bots':len(rows),'open':sum(x.get('state')=='OPEN' for x in rows),'closed_deals':sum(int(x.get('closed_deals') or 0) for x in rows),
             'realised_pnl_quote':round(sum(q(x.get('realised_pnl_quote')) or 0 for x in rows),2),
             'open_pnl_quote':round(sum(q(x.get('open_pnl_quote')) or 0 for x in rows if x.get('state')=='OPEN'),2)},
  'persistent_state':str(state_path()),'read_only_exchange':True,'automatic_live_deployment':False,
  'principle':'Paper bots use current KuCoin prices and the exact unseen-validated DCA setup. Results are forward evidence, not historical backtest results.'}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
 print(f"Paper portfolio: bots={len(rows)} open={payload['summary']['open']} paper_P/L={payload['summary']['open_pnl_quote']}")
 return 0
if __name__=='__main__':raise SystemExit(main())
