#!/usr/bin/env python3
"""Synchronise KuCoin TEL/USDT and TAO/USDT candles and replay both frozen strategies."""
from __future__ import annotations
import argparse, csv, json, math, time, urllib.parse, urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config.json"

@dataclass
class Candle:
    ts:int; open:float; high:float; low:float; close:float; volume:float=0.0; trades:int=0

def iso(ts:int)->str:
    return datetime.fromtimestamp(ts,tz=timezone.utc).isoformat().replace('+00:00','Z')

def load_json(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding='utf-8'))

def load_history(path:Path)->list[Candle]:
    out=[]
    with path.open(newline='',encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            dt=datetime.fromisoformat(r['time'].replace('Z','+00:00'))
            out.append(Candle(int(dt.timestamp()),float(r['open']),float(r['high']),float(r['low']),float(r['close']),float(r.get('volume',0) or 0),int(float(r.get('trades',0) or 0))))
    return sorted({c.ts:c for c in out}.values(),key=lambda c:c.ts)

def save_history(path:Path,candles:list[Candle])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['time','open','high','low','close','volume','trades'])
        for c in candles:w.writerow([iso(c.ts),c.open,c.high,c.low,c.close,c.volume,c.trades])

def fetch_kucoin(symbol:str,candle_type:str,since:int|None)->list[Candle]:
    if candle_type!='4hour': raise ValueError('Only 4hour is supported')
    seconds=14400; now=int(time.time()); start=max(0,(since or now-seconds*500)-seconds)
    params=urllib.parse.urlencode({'symbol':symbol,'type':candle_type,'startAt':start,'endAt':now})
    url='https://api.kucoin.com/api/v1/market/candles?'+params
    req=urllib.request.Request(url,headers={'User-Agent':'Crypto-Regime-Manager/6.1','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as response: payload=json.loads(response.read().decode('utf-8'))
    if payload.get('code')!='200000' or not isinstance(payload.get('data'),list): raise RuntimeError(f'Unexpected KuCoin response: {payload}')
    rows=[]
    for r in payload['data']:
        ts=int(r[0])
        if ts+seconds>now: continue
        rows.append(Candle(ts,float(r[1]),float(r[3]),float(r[4]),float(r[2]),float(r[5]),0))
    return sorted(rows,key=lambda c:c.ts)

def ema(values:list[float],period:int)->list[float]:
    alpha=2/(period+1); out=[values[0]]
    for v in values[1:]: out.append(alpha*v+(1-alpha)*out[-1])
    return out

def rsi(values:list[float],period:int=14)->list[float]:
    out=[math.nan]*len(values)
    if len(values)<=period:return out
    gains=[];losses=[]
    for a,b in zip(values,values[1:]):
        d=b-a; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains[:period])/period; al=sum(losses[:period])/period
    out[period]=100 if al==0 else 100-100/(1+ag/al)
    for i in range(period+1,len(values)):
        ag=(ag*(period-1)+gains[i-1])/period; al=(al*(period-1)+losses[i-1])/period
        out[i]=100 if al==0 else 100-100/(1+ag/al)
    return out

def realised_vol(values:list[float],window:int,annual:int)->list[float]:
    ret=[math.nan]+[math.log(b/a) for a,b in zip(values,values[1:])]; out=[math.nan]*len(values)
    for i in range(window,len(values)):
        sample=ret[i-window+1:i+1]; mean=sum(sample)/window
        var=sum((x-mean)**2 for x in sample)/(window-1)
        out[i]=math.sqrt(var)*math.sqrt(annual)*100
    return out

def indicators(candles:list[Candle],cfg:dict[str,Any])->list[dict[str,Any]|None]:
    rcfg=cfg['regime']; closes=[c.close for c in candles]
    e50=ema(closes,int(rcfg['fast_ema'])); e200=ema(closes,int(rcfg['slow_ema']))
    rs=rsi(closes); rv=realised_vol(closes,int(rcfg['realised_volatility_window_candles']),int(rcfg['annualisation_periods']))
    low=float(rcfg['low_volatility_threshold_pct']); high=float(rcfg['high_volatility_threshold_pct']); out=[]
    for i,c in enumerate(candles):
        if i<120 or math.isnan(rv[i]) or math.isnan(rs[i]): out.append(None); continue
        if rv[i]<low: regime='Low'
        elif rv[i]<high: regime='Medium'
        else:
            bullish=c.close>=e200[i] and e50[i]>=e200[i] and e50[i]>=e50[i-1]
            regime='High-Bull' if bullish else 'High-Bear'
        out.append({'regime':regime,'rv':rv[i],'ema50':e50[i],'ema200':e200[i],'rsi14':rs[i],
                    'distance_ema200':(c.close/e200[i]-1)*100,'distance_ema50':(c.close/e50[i]-1)*100,
                    'return24':(c.close/closes[i-6]-1)*100 if i>=6 else math.nan})
    return out

def permission(signal:dict[str,Any],fcfg:dict[str,Any])->tuple[bool,str]:
    reg=signal['regime']; global_cfg=fcfg.get('global',{}); local=fcfg.get(reg,{})
    if local.get('blocked',False): return False,f'{reg} entries are blocked'
    max_e200=global_cfg.get('max_distance_above_ema200_pct')
    if max_e200 is not None and signal['distance_ema200']>float(max_e200): return False,'Price is too far above EMA200'
    checks=[
        ('max_rsi14','rsi14',lambda a,b:a>b,'RSI is above the allowed maximum'),
        ('max_distance_from_ema50_pct','distance_ema50',lambda a,b:a>b,'Price is too far above EMA50'),
        ('max_24h_return_pct','return24',lambda a,b:a>b,'24-hour return is above the allowed maximum'),
        ('min_24h_return_pct','return24',lambda a,b:a<b,'24-hour return is below the required minimum')]
    for key,metric,bad,msg in checks:
        if key in local and bad(signal[metric],float(local[key])): return False,msg
    return True,'All entry rules pass'

def ladder(entry:float,setting:dict[str,Any],base:float)->tuple[list[float],list[float]]:
    prices=[];sizes=[];cum=0.0
    for k in range(int(setting.get('safety_orders',0))):
        cum+=float(setting['so_deviation_pct'])/100*float(setting['step_scale'])**k
        prices.append(entry*(1-cum)); sizes.append(base*float(setting['volume_scale'])**(k+1))
    return prices,sizes

def health_monitor(candles:list[Candle],deals:list[dict[str,Any]],equity_curve:list[tuple[int,float]],open_data:dict[str,Any]|None,maxcap:float,overall_avg_hours:float,overall_longest_hours:float,cfg:dict[str,Any])->dict[str,Any]:
    hcfg=cfg.get('health_monitor',{})
    recent_days=int(hcfg.get('recent_window_days',90)); cutoff=candles[-1].ts-recent_days*86400
    recent_deals=[]
    for d in deals:
        try: exit_ts=int(datetime.fromisoformat(d['exit_time'].replace('Z','+00:00')).timestamp())
        except Exception: continue
        if exit_ts>=cutoff: recent_deals.append(d)
    recent_pnl=sum(float(d['pnl']) for d in recent_deals)
    recent_avg=sum(float(d['hours']) for d in recent_deals)/len(recent_deals) if recent_deals else 0.0
    recent_longest=max((float(d['hours']) for d in recent_deals),default=0.0)
    recent_points=[(ts,eq) for ts,eq in equity_curve if ts>=cutoff]
    if not recent_points: recent_points=equity_curve[-1:]
    peak=recent_points[0][1] if recent_points else 0.0; recent_mdd=0.0
    for _,eq in recent_points:
        peak=max(peak,eq); recent_mdd=min(recent_mdd,eq-peak)
    recent_mdd_pct=recent_mdd/maxcap*100 if maxcap else 0.0
    open_loss_pct=(float(open_data['open_pnl'])/maxcap*100) if open_data and maxcap else 0.0
    open_hours=float(open_data['hours_open']) if open_data else 0.0
    age_hours=max(0.0,(datetime.now(timezone.utc).timestamp()-candles[-1].ts)/3600)
    score=100; flags=[]; positives=[]
    warn_f=float(hcfg.get('freshness_warning_hours',12)); crit_f=float(hcfg.get('freshness_critical_hours',24))
    if age_hours>crit_f: score-=40; flags.append(f'Market data is {age_hours:.0f} hours old')
    elif age_hours>warn_f: score-=20; flags.append(f'Market data is {age_hours:.0f} hours old')
    else: positives.append('Market data is current')
    if recent_pnl<0: score-=20; flags.append(f'Recent {recent_days}-day realised P&L is negative')
    elif recent_deals: positives.append(f'Recent {recent_days}-day realised P&L is positive')
    else: flags.append(f'No completed deals in the last {recent_days} days')
    dd_warn=-abs(float(hcfg.get('drawdown_warning_pct',10))); dd_crit=-abs(float(hcfg.get('drawdown_critical_pct',20)))
    if recent_mdd_pct<=dd_crit: score-=20; flags.append(f'Recent drawdown reached {recent_mdd_pct:.1f}% of capital')
    elif recent_mdd_pct<=dd_warn: score-=10; flags.append(f'Recent drawdown reached {recent_mdd_pct:.1f}% of capital')
    else: positives.append('Recent drawdown is within the monitoring limit')
    if overall_avg_hours>0 and recent_avg>0:
        ratio=recent_avg/overall_avg_hours
        if ratio>=float(hcfg.get('duration_critical_multiple',2.0)): score-=18; flags.append('Recent average trade duration is over twice the historical average')
        elif ratio>=float(hcfg.get('duration_warning_multiple',1.5)): score-=9; flags.append('Recent average trade duration is elevated')
        else: positives.append('Recent trade duration is consistent with history')
    if open_data:
        loss_warn=-abs(float(hcfg.get('open_loss_warning_pct',10))); loss_crit=-abs(float(hcfg.get('open_loss_critical_pct',20)))
        if open_loss_pct<=loss_crit: score-=20; flags.append(f'Open replay position is {open_loss_pct:.1f}% of capital underwater')
        elif open_loss_pct<=loss_warn: score-=10; flags.append(f'Open replay position is {open_loss_pct:.1f}% of capital underwater')
        duration_ref=max(overall_avg_hours*2,336.0)
        if open_hours>duration_ref*2: score-=16; flags.append(f'Open replay position has lasted {open_hours/24:.1f} days')
        elif open_hours>duration_ref: score-=8; flags.append(f'Open replay position duration is elevated ({open_hours/24:.1f} days)')
    else: positives.append('No unresolved replay position')
    score=max(0,min(100,int(round(score))))
    if score>=85: status='Excellent'
    elif score>=70: status='Healthy'
    elif score>=50: status='Watch'
    else: status='Review'
    return {
      'score':score,'status':status,'flags':flags,'positives':positives,
      'recent_window_days':recent_days,'recent_closed_deals':len(recent_deals),
      'recent_realised_pnl':recent_pnl,'recent_average_trade_hours':recent_avg,
      'recent_longest_trade_hours':recent_longest,'recent_max_drawdown_dollars':recent_mdd,
      'recent_max_drawdown_pct_of_capital':recent_mdd_pct,'open_loss_pct_of_capital':open_loss_pct,
      'open_hours':open_hours,'data_age_hours':age_hours,
      'historical_average_trade_hours':overall_avg_hours,'historical_longest_trade_hours':overall_longest_hours,
      'note':hcfg.get('note','Health score is a monitoring indicator, not a forecast.')
    }

def trading_intelligence(asset_result:dict[str,Any])->dict[str,Any]:
    """Create a transparent opportunity score. This is a ranking aid, not a probability."""
    latest=asset_result.get('latest') or {}; health=asset_result.get('health') or {}
    allowed=bool(latest.get('entry_allowed')); regime=latest.get('regime','Unknown')
    health_score=float(health.get('score',0) or 0); recent_pnl=float(health.get('recent_realised_pnl',0) or 0)
    recent_dd=float(health.get('recent_max_drawdown_pct_of_capital',0) or 0)
    rsi_v=float(latest.get('rsi14',50) or 50); dist50=float(latest.get('distance_ema50',0) or 0)
    ret24=float(latest.get('return24',0) or 0); open_pos=asset_result.get('open_position')
    score=round(0.55*health_score)
    reasons=[]; cautions=[]
    if allowed:
        score+=25; reasons.append('All configured entry filters pass')
    else:
        score-=20; cautions.append(latest.get('entry_reason') or 'Entry filters do not pass')
    regime_bonus={'High-Bull':12,'Medium':8,'Low':6,'High-Bear':0}.get(regime,0)
    score+=regime_bonus
    if regime=='High-Bear': cautions.append('High-Bear conditions carry elevated long-DCA risk')
    else: reasons.append(f'{regime} regime has an active strategy configuration')
    if recent_pnl>0: score+=7; reasons.append('Recent 90-day realised P&L is positive')
    elif recent_pnl<0: score-=10; cautions.append('Recent 90-day realised P&L is negative')
    if recent_dd<=-20: score-=12; cautions.append('Recent drawdown is above the critical health threshold')
    elif recent_dd<=-10: score-=6; cautions.append('Recent drawdown is elevated')
    else: score+=3; reasons.append('Recent drawdown is within the monitoring limit')
    if open_pos:
        score-=8; cautions.append('Replay already has an unresolved position')
    else: score+=3; reasons.append('No unresolved replay position')
    # Setup quality, deliberately modest so it cannot override blocked entries.
    if 35<=rsi_v<=60: score+=3; reasons.append('RSI is within a balanced entry zone')
    elif rsi_v>70: score-=4; cautions.append('RSI is elevated')
    if abs(dist50)<=10: score+=2
    if abs(ret24)>=12: score-=3; cautions.append('The last 24-hour move is unusually large')
    score=max(0,min(100,int(round(score))))
    if not allowed: action='WAIT'
    elif score>=80: action='STRONG CANDIDATE'
    elif score>=65: action='CANDIDATE'
    else: action='CAUTIOUS'
    confidence='High' if score>=80 else ('Moderate' if score>=65 else 'Low')
    return {
      'opportunity_score':score,'action':action,'confidence_label':confidence,
      'explanation':reasons[:6],'cautions':cautions[:6],
      'score_components':{'strategy_health_weight':round(0.55*health_score,1),'entry_permission':25 if allowed else -20,
                          'regime_bonus':regime_bonus,'recent_pnl_positive':recent_pnl>0,'recent_drawdown_pct':recent_dd},
      'note':'Opportunity score is a transparent ranking aid, not a probability of profit or financial advice.'
    }

def portfolio_intelligence(outputs:list[dict[str,Any]])->dict[str,Any]:
    ranked=sorted(outputs,key=lambda a:(a.get('intelligence') or {}).get('opportunity_score',0),reverse=True)
    eligible=[a for a in ranked if (a.get('latest') or {}).get('entry_allowed')]
    active_replay=sum(1 for a in outputs if a.get('open_position'))
    total_cap=sum(float(a.get('max_theoretical_capital',0) or 0) for a in outputs)
    best=eligible[0] if eligible else None
    return {
      'best_opportunity':({'id':best.get('id'),'symbol':best.get('symbol'),'score':best['intelligence']['opportunity_score'],
                           'recommended_bot':(best.get('latest') or {}).get('recommended_bot')} if best else None),
      'eligible_count':len(eligible),'monitored_assets':len(outputs),'active_replay_positions':active_replay,
      'combined_max_theoretical_capital':total_cap,
      'ranking':[{'rank':i+1,'id':a.get('id'),'symbol':a.get('symbol'),'score':(a.get('intelligence') or {}).get('opportunity_score'),
                  'action':(a.get('intelligence') or {}).get('action'),'entry_allowed':(a.get('latest') or {}).get('entry_allowed'),
                  'regime':(a.get('latest') or {}).get('regime'),'health':(a.get('health') or {}).get('status')} for i,a in enumerate(ranked)],
      'operating_rule':'Treat scores as a ranking aid. Never start a new deal when entry_allowed is false, and do not alter an existing open deal.'
    }

def update_health_history(path:Path,payload:dict[str,Any],limit:int=180)->None:
    try: history=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'points':[]}
    except Exception: history={'points':[]}
    points=list(history.get('points',[])); stamp=payload.get('generated_at')
    for asset in payload.get('assets',[]):
        row={'generated_at':stamp,'id':asset.get('id'),'last_candle':(asset.get('latest') or {}).get('last_candle'),'score':(asset.get('health') or {}).get('score'),'status':(asset.get('health') or {}).get('status'),'recent_pnl':(asset.get('health') or {}).get('recent_realised_pnl'),'recent_drawdown_pct':(asset.get('health') or {}).get('recent_max_drawdown_pct_of_capital')}
        if not any(x.get('id')==row['id'] and x.get('last_candle')==row['last_candle'] for x in points): points.append(row)
    history={'version':payload.get('version'),'generated_at':stamp,'points':points[-limit:]}
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(history,indent=2),encoding='utf-8')

def simulate(candles:list[Candle],signals:list[dict[str,Any]|None],asset:dict[str,Any],execution:dict[str,Any])->dict[str,Any]:
    base=float(execution['base_order']); fee=float(execution['fee_rate']); bots=asset['bots']; fcfg=asset['entry_filter']
    realised=0.; peak=0.; mdd=0.; maxcap=0.; pos=None; deals=[]; skipped=0; equity_curve=[]
    for i,c in enumerate(candles):
        decision=signals[i-1] if i>0 else None
        if pos is None and decision is not None:
            allowed,_=permission(decision,fcfg); setting=bots.get(decision['regime'],{})
            if allowed and setting.get('enabled',True):
                prices,sizes=ladder(c.open,setting,base)
                pos={'entry_i':i,'entry_ts':c.ts,'regime':decision['regime'],'setting':setting,'qty':base/c.open,'cost':base,'fees':base*fee,'so':0,'prices':prices,'sizes':sizes}
                maxcap=max(maxcap,base+sum(sizes))
            else: skipped+=1
        filled=False
        if pos is not None:
            while pos['so']<len(pos['prices']) and c.low<=pos['prices'][pos['so']]:
                px=pos['prices'][pos['so']]; size=pos['sizes'][pos['so']]
                pos['qty']+=size/px; pos['cost']+=size; pos['fees']+=size*fee; pos['so']+=1; filled=True
            avg=pos['cost']/pos['qty']; target=avg*(1+float(pos['setting']['take_profit_pct'])/100)
            if not filled and c.high>=target:
                proceeds=pos['qty']*target; pnl=proceeds-pos['cost']-pos['fees']-proceeds*fee; realised+=pnl
                deals.append({'entry_time':iso(pos['entry_ts']),'exit_time':iso(c.ts),'regime':pos['regime'],'pnl':pnl,'hours':(i-pos['entry_i']+1)*4,'safety_orders':pos['so'],'capital':pos['cost']})
                pos=None
        equity=realised
        if pos is not None:
            value=pos['qty']*c.close; equity+=value-pos['cost']-pos['fees']-value*fee
        peak=max(peak,equity); mdd=min(mdd,equity-peak); equity_curve.append((c.ts,equity))
    open_data=None; open_pnl=0.
    if pos is not None:
        last=candles[-1]; value=pos['qty']*last.close; open_pnl=value-pos['cost']-pos['fees']-value*fee
        avg=pos['cost']/pos['qty']; target=avg*(1+float(pos['setting']['take_profit_pct'])/100)
        open_data={'entry_time':iso(pos['entry_ts']),'regime':pos['regime'],'hours_open':(len(candles)-pos['entry_i'])*4,'safety_orders':pos['so'],'capital':pos['cost'],'average_entry':avg,'target':target,'last_close':last.close,'open_pnl':open_pnl,'required_rise_pct':(target/last.close-1)*100}
    net=realised+open_pnl; latest=signals[-1]; allowed,reason=permission(latest,fcfg) if latest else (False,'Insufficient history')
    bot=bots.get(latest['regime'],{}) if latest else {}
    avg_hours=sum(d['hours'] for d in deals)/len(deals) if deals else 0
    longest_hours=max((d['hours'] for d in deals),default=0)
    health=health_monitor(candles,deals,equity_curve,open_data,maxcap,avg_hours,longest_hours,APP_CONFIG)
    result={'id':asset['id'],'display_name':asset['display_name'],'symbol':asset['symbol'],'history_start':iso(candles[0].ts),'history_end':iso(candles[-1].ts),'candles':len(candles),
            'net_pnl':net,'realised_pnl':realised,'open_pnl':open_pnl,'return_on_max_capital_pct':net/maxcap*100 if maxcap else 0,'maximum_drawdown_dollars':mdd,'maximum_drawdown_pct_of_capital':mdd/maxcap*100 if maxcap else 0,'max_theoretical_capital':maxcap,'closed_deals':len(deals),'average_trade_hours':avg_hours,'longest_trade_hours':longest_hours,'skipped_entry_candles':skipped,'open_position':open_data,'health':health,
            'latest':{**(latest or {}),'entry_allowed':allowed,'entry_reason':reason,'recommended_bot':bot.get('name'),'bot_settings':bot,'last_close':candles[-1].close,'last_candle':iso(candles[-1].ts)},'recent_deals':deals[-10:],'all_deals':deals}
    result['intelligence']=trading_intelligence(result)
    return result

def write_deals(path:Path,deals:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True); fields=['entry_time','exit_time','regime','pnl','hours','safety_orders','capital']
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(deals)

def main()->int:
    global APP_CONFIG
    parser=argparse.ArgumentParser(); parser.add_argument('--no-sync',action='store_true'); args=parser.parse_args()
    cfg=load_json(CONFIG); APP_CONFIG=cfg; outputs=[]
    for asset in cfg['assets']:
        path=ROOT/asset['history_file']; candles=load_history(path); added=0; error=None
        if not args.no_sync:
            try:
                fresh=fetch_kucoin(asset['symbol'],cfg['execution']['candle_type'],candles[-1].ts if candles else None)
                old=len(candles); candles=sorted({c.ts:c for c in candles+fresh}.values(),key=lambda c:c.ts); added=len(candles)-old; save_history(path,candles)
            except Exception as exc:error=str(exc)
        result=simulate(candles,indicators(candles,asset),asset,cfg['execution']); result['sync']={'new_candles':added,'error':error,'source':'KuCoin public spot candles API'}; result['strategy_config']={'regime':asset['regime'],'entry_filter':asset['entry_filter'],'bots':asset['bots']}
        write_deals(ROOT/asset['deal_log'],result.pop('all_deals')); outputs.append(result)
    payload={'version':cfg.get('app',{}).get('version','5.3.0'),'app':cfg.get('app',{}),'generated_at':datetime.now(timezone.utc).isoformat(),'workflow_status':'ok' if not any((a.get('sync') or {}).get('error') for a in outputs) else 'warning','portfolio':portfolio_intelligence(outputs),'assets':outputs}
    out=ROOT/cfg['execution']['output_json']; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    update_health_history(ROOT/'docs/health_history.json',payload,int(cfg.get('health_monitor',{}).get('history_points',180)))
    print(json.dumps(payload,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
