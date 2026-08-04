from __future__ import annotations
import csv,json,math,itertools
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

def load(path:Path):
 with path.open(encoding='utf-8-sig') as f:return [{**r,'time':datetime.fromisoformat(r['time'].replace('Z','+00:00')),'open':float(r['open']),'high':float(r['high']),'low':float(r['low']),'close':float(r['close'])} for r in csv.DictReader(f)]
def capital(bo,so,n,vs):return bo+sum(so*(vs**i) for i in range(n))
def replay(rows,tp,dev,n,vs,step,fee=.001,bo=100,so=100):
 pnl=0.;deals=0;dur=[];maxcap=capital(bo,so,n,vs);open_trade=None;equity=[]
 for i,c in enumerate(rows):
  if open_trade is None:open_trade={'i':i,'cost':bo,'qty':bo/c['close'],'next':c['close']*(1-dev),'so':0}
  t=open_trade
  while t['so']<n and c['low']<=t['next']:
   amount=so*(vs**t['so']); price=t['next'];t['cost']+=amount;t['qty']+=amount/price;t['so']+=1;t['next']*=1-dev*(step**t['so'])
  avg=t['cost']/t['qty']; target=avg*(1+tp+fee*2)
  if c['high']>=target:
   pnl+=t['qty']*target-t['cost']-t['cost']*fee-t['qty']*target*fee;deals+=1;dur.append((i-t['i'])*4);open_trade=None
  mark=pnl+(t['qty']*c['close']-t['cost'] if t else 0);equity.append(mark)
 peak=-1e99;mdd=0
 for x in equity:peak=max(peak,x);mdd=min(mdd,x-peak)
 return {'net_pnl':round(pnl,2),'closed_deals':deals,'average_hours':round(sum(dur)/len(dur),1) if dur else 0,'longest_hours':max(dur) if dur else 0,'max_drawdown_dollars':round(mdd,2),'max_capital':round(maxcap,2),'open_position':bool(open_trade)}
def optimise(path:Path):
 rows=load(path);results=[]
 for tp,dev,n,vs,step in itertools.product((.008,.01,.012,.015,.02),(.008,.012,.02,.03,.04),(4,5,6,7),(1.3,1.4,1.5,1.6),(1.0,1.1,1.2)):
  r=replay(rows,tp,dev,n,vs,step);r['settings']={'take_profit_pct':tp*100,'so_deviation_pct':dev*100,'safety_orders':n,'volume_scale':vs,'step_scale':step};r['score']=r['net_pnl']-abs(r['max_drawdown_dollars'])*.35-r['longest_hours']*.02-(500 if r['open_position'] else 0);results.append(r)
 return sorted(results,key=lambda x:x['score'],reverse=True)[:20]
def run_lab(root:Path):
 out=[]
 for p in sorted((root/'data'/'normalized').glob('*_4H.csv')):
  try: out.append({'dataset':p.name,'status':'BACKTESTED','candidates':optimise(p)})
  except Exception as e:out.append({'dataset':p.name,'status':'ERROR','error':str(e)})
 payload={'version':'29.0.0','generated_at':datetime.now(timezone.utc).isoformat(),'datasets':out,'policy':{'fee_aware':True,'forward_validation_required':True,'manual_approval_required':True,'live_changes':False}}
 (root/'docs'/'backtest_lab.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');return payload
