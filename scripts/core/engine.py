#!/usr/bin/env python3
"""Synchronise KuCoin candles and replay production and research strategies.

TEL and TAO remain production/advisory assets. SUI is a frozen research-only
candidate with automatic one-variable experiments, excluded from live
portfolio rankings until manually promoted.
"""
from __future__ import annotations
import argparse, copy, csv, json, math, time, urllib.parse, urllib.request
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
    seconds=14400; now=int(time.time()); start=max(0,(since or now-seconds*1000)-seconds)
    params=urllib.parse.urlencode({'symbol':symbol,'type':candle_type,'startAt':start,'endAt':now})
    url='https://api.kucoin.com/api/v1/market/candles?'+params
    req=urllib.request.Request(url,headers={'User-Agent':'Crypto-Regime-Manager/7.1','Accept':'application/json'})
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

def atr(candles:list[Candle],period:int=14)->list[float]:
    out=[math.nan]*len(candles)
    if not candles: return out
    trs=[]
    for i,c in enumerate(candles):
        prev=candles[i-1].close if i else c.close
        trs.append(max(c.high-c.low,abs(c.high-prev),abs(c.low-prev)))
    if len(trs)<period: return out
    value=sum(trs[:period])/period; out[period-1]=value
    for i in range(period,len(trs)):
        value=(value*(period-1)+trs[i])/period; out[i]=value
    return out

def indicators(candles:list[Candle],cfg:dict[str,Any])->list[dict[str,Any]|None]:
    rcfg=cfg['regime']; closes=[c.close for c in candles]
    e50=ema(closes,int(rcfg['fast_ema'])); e200=ema(closes,int(rcfg['slow_ema']))
    rs=rsi(closes); rv=realised_vol(closes,int(rcfg['realised_volatility_window_candles']),int(rcfg['annualisation_periods'])); at=atr(candles,14)
    low=float(rcfg['low_volatility_threshold_pct']); high=float(rcfg['high_volatility_threshold_pct']); out=[]
    for i,c in enumerate(candles):
        if i<120 or math.isnan(rv[i]) or math.isnan(rs[i]): out.append(None); continue
        if rv[i]<low: regime='Low'
        elif rv[i]<high: regime='Medium'
        else:
            bullish=c.close>=e200[i] and e50[i]>=e200[i] and e50[i]>=e50[i-1]
            regime='High-Bull' if bullish else 'High-Bear'
        bearish=0
        j=i
        while j>=0 and candles[j].close<candles[j].open:
            bearish+=1; j-=1
        atr_ratio=(at[i]/at[i-6]) if i>=6 and not math.isnan(at[i]) and not math.isnan(at[i-6]) and at[i-6]>0 else math.nan
        out.append({'regime':regime,'rv':rv[i],'ema50':e50[i],'ema200':e200[i],'rsi14':rs[i],
                    'distance_ema200':(c.close/e200[i]-1)*100,'distance_ema50':(c.close/e50[i]-1)*100,
                    'ema200_slope_pct':(e200[i]/e200[i-1]-1)*100 if i>0 else math.nan,
                    'return24':(c.close/closes[i-6]-1)*100 if i>=6 else math.nan,
                    'ema50_slope_pct':(e50[i]/e50[i-1]-1)*100 if i>0 else math.nan,
                    'pullback20_pct':(1-c.close/max(closes[max(0,i-119):i+1]))*100,
                    'atr14':at[i],'atr_expansion_ratio':atr_ratio,'consecutive_bearish_candles':bearish})
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
        ('min_24h_return_pct','return24',lambda a,b:a<b,'24-hour return is below the required minimum'),
        ('min_pullback_from_20d_high_pct','pullback20_pct',lambda a,b:a<b,'Price has not pulled back far enough from its 20-day high'),
        ('min_ema50_slope_pct','ema50_slope_pct',lambda a,b:a<b,'EMA50 is falling faster than the allowed limit'),
        ('min_distance_from_ema200_pct','distance_ema200',lambda a,b:a<b,'Price is below the required EMA200 threshold'),
        ('min_distance_from_ema50_pct','distance_ema50',lambda a,b:a<b,'Price is below the required EMA50 threshold'),
        ('max_atr_expansion_ratio','atr_expansion_ratio',lambda a,b:a>b,'ATR is expanding above the allowed limit'),
        ('max_consecutive_bearish_candles','consecutive_bearish_candles',lambda a,b:a>b,'Too many consecutive bearish candles'),
        ('min_ema200_slope_pct','ema200_slope_pct',lambda a,b:a<b,'EMA200 is falling faster than the allowed limit')]
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
    production=[a for a in outputs if a.get('production_status','production')=='production']
    research=[a for a in outputs if a.get('production_status')!='production']
    ranked=sorted(production,key=lambda a:((a.get('intelligence') or {}).get('opportunity_score') or 0),reverse=True)
    eligible=[a for a in ranked if (a.get('latest') or {}).get('entry_allowed')]
    active_replay=sum(1 for a in production if a.get('open_position'))
    total_cap=sum(float(a.get('max_theoretical_capital',0) or 0) for a in production)
    best=eligible[0] if eligible else None
    return {
      'best_opportunity':({'id':best.get('id'),'symbol':best.get('symbol'),'score':best['intelligence']['opportunity_score'],
                           'recommended_bot':(best.get('latest') or {}).get('recommended_bot')} if best else None),
      'eligible_count':len(eligible),'monitored_assets':len(production),'research_assets':len(research),
      'active_replay_positions':active_replay,'combined_max_theoretical_capital':total_cap,
      'ranking':[{'rank':i+1,'id':a.get('id'),'symbol':a.get('symbol'),'score':(a.get('intelligence') or {}).get('opportunity_score'),
                  'action':(a.get('intelligence') or {}).get('action'),'entry_allowed':(a.get('latest') or {}).get('entry_allowed'),
                  'regime':(a.get('latest') or {}).get('regime'),'health':(a.get('health') or {}).get('status')} for i,a in enumerate(ranked)],
      'research':[{'id':a.get('id'),'symbol':a.get('symbol'),'promotion_status':(a.get('research') or {}).get('promotion_status')} for a in research],
      'operating_rule':'Production rankings include TEL and TAO only. Research assets never become live recommendations automatically.'
    }

def evaluate_research(asset:dict[str,Any],result:dict[str,Any],candles:list[Candle],equity_curve:list[tuple[int,float]])->dict[str,Any]:
    gates=asset.get('promotion_gates',{}); start_text=asset.get('forward_test_start')
    start_ts=int(datetime.fromisoformat(start_text.replace('Z','+00:00')).timestamp()) if start_text else candles[0].ts
    forward=[c for c in candles if c.ts>=start_ts]
    days=((forward[-1].ts-forward[0].ts)/86400+4/24) if forward else 0.0
    effective_longest=max(float(result.get('longest_trade_hours',0) or 0),float((result.get('open_position') or {}).get('hours_open',0) or 0))
    window_days=int(gates.get('evaluation_window_days',30)); window_sec=window_days*86400
    windows=[]
    if forward:
        cursor=forward[0].ts
        final=forward[-1].ts
        while cursor<=final:
            end=cursor+window_sec
            pts=[eq for ts,eq in equity_curve if cursor<=ts<end]
            if pts:
                windows.append({'start':iso(cursor),'end':iso(min(end,final)),'equity_change':pts[-1]-pts[0]})
            cursor=end
    profitable=sum(1 for w in windows if w['equity_change']>0)
    checks={
      'minimum_forward_days':days>=float(gates.get('minimum_forward_days',90)),
      'minimum_forward_candles':len(forward)>=int(gates.get('minimum_forward_candles',540)),
      'positive_net_pnl':float(result.get('net_pnl',0))>0 if gates.get('require_positive_net_pnl',True) else True,
      'maximum_drawdown':abs(min(0,float(result.get('maximum_drawdown_pct_of_capital',0))))<=float(gates.get('maximum_drawdown_pct',40)),
      'maximum_effective_trade_days':effective_longest/24<=float(gates.get('maximum_effective_trade_days',30)),
      'profitable_windows':profitable>=int(gates.get('minimum_profitable_windows',3))
    }
    enough=checks['minimum_forward_days'] and checks['minimum_forward_candles']
    passed=enough and all(checks.values())
    status='PASS — manual promotion review required' if passed else ('FAIL — review risk' if enough else 'COLLECTING FORWARD DATA')
    return {'mode':'research','label':asset.get('research_label','Research only'),'forward_test_start':start_text,
            'forward_days':days,'forward_candles':len(forward),'promotion_status':status,'all_gates_pass':passed,
            'checks':checks,'profitable_windows':profitable,'evaluation_windows':windows,
            'effective_longest_trade_hours':effective_longest,'gates':gates,'research_basis':asset.get('research_basis',{}),
            'note':'Passing gates does not enable live trading. Promotion must be reviewed and approved manually.'}

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
    sim_start_text=asset.get('forward_test_start'); sim_start_ts=int(datetime.fromisoformat(sim_start_text.replace('Z','+00:00')).timestamp()) if sim_start_text else candles[0].ts
    realised=0.; peak=0.; mdd=0.; maxcap=0.; pos=None; deals=[]; skipped=0; equity_curve=[]
    for i,c in enumerate(candles):
        decision=signals[i-1] if i>0 else None
        if c.ts>=sim_start_ts and pos is None and decision is not None:
            allowed,_=permission(decision,fcfg); setting=bots.get(decision['regime'],{})
            if allowed and setting.get('enabled',True):
                prices,sizes=ladder(c.open,setting,base)
                pos={'entry_i':i,'entry_ts':c.ts,'regime':decision['regime'],'setting':setting,'entry_signal':dict(decision),'qty':base/c.open,'cost':base,'fees':base*fee,'so':0,'prices':prices,'sizes':sizes}
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
                deals.append({'entry_time':iso(pos['entry_ts']),'exit_time':iso(c.ts),'regime':pos['regime'],'pnl':pnl,'hours':(i-pos['entry_i']+1)*4,'safety_orders':pos['so'],'capital':pos['cost'],'entry_signal':pos.get('entry_signal',{})})
                pos=None
        equity=realised
        if pos is not None:
            value=pos['qty']*c.close; equity+=value-pos['cost']-pos['fees']-value*fee
        peak=max(peak,equity); mdd=min(mdd,equity-peak); equity_curve.append((c.ts,equity))
    open_data=None; open_pnl=0.
    if pos is not None:
        last=candles[-1]; value=pos['qty']*last.close; open_pnl=value-pos['cost']-pos['fees']-value*fee
        avg=pos['cost']/pos['qty']; target=avg*(1+float(pos['setting']['take_profit_pct'])/100)
        open_data={'entry_time':iso(pos['entry_ts']),'regime':pos['regime'],'hours_open':(len(candles)-pos['entry_i'])*4,'safety_orders':pos['so'],'capital':pos['cost'],'average_entry':avg,'target':target,'last_close':last.close,'open_pnl':open_pnl,'required_rise_pct':(target/last.close-1)*100,'entry_signal':pos.get('entry_signal',{})}
    net=realised+open_pnl; latest=signals[-1]; allowed,reason=permission(latest,fcfg) if latest else (False,'Insufficient history')
    bot=bots.get(latest['regime'],{}) if latest else {}
    avg_hours=sum(d['hours'] for d in deals)/len(deals) if deals else 0
    longest_hours=max((d['hours'] for d in deals),default=0)
    health=health_monitor(candles,deals,equity_curve,open_data,maxcap,avg_hours,longest_hours,APP_CONFIG)
    result={'id':asset['id'],'display_name':asset['display_name'],'symbol':asset['symbol'],'production_status':asset.get('production_status','production'),'history_start':iso(candles[0].ts),'history_end':iso(candles[-1].ts),'candles':len(candles),
            'net_pnl':net,'realised_pnl':realised,'open_pnl':open_pnl,'return_on_max_capital_pct':net/maxcap*100 if maxcap else 0,'maximum_drawdown_dollars':mdd,'maximum_drawdown_pct_of_capital':mdd/maxcap*100 if maxcap else 0,'max_theoretical_capital':maxcap,'closed_deals':len(deals),'average_trade_hours':avg_hours,'longest_trade_hours':longest_hours,'skipped_entry_candles':skipped,'open_position':open_data,'health':health,
            'latest':{**(latest or {}),'entry_allowed':allowed,'entry_reason':reason,'recommended_bot':bot.get('name'),'bot_settings':bot,'last_close':candles[-1].close,'last_candle':iso(candles[-1].ts)},'recent_deals':deals[-10:],'all_deals':deals}
    result['intelligence']=trading_intelligence(result)
    if result['production_status']!='production':
        result['intelligence']={'opportunity_score':None,'action':'RESEARCH ONLY','confidence_label':'Not applicable','explanation':['Excluded from production ranking'],'cautions':['Forward validation is still in progress'],'note':'Research assets cannot generate live recommendations.'}
        result['research']=evaluate_research(asset,result,candles,equity_curve)
    return result


def compact_metrics(result:dict[str,Any])->dict[str,Any]:
    research=result.get('research') or {}
    return {
      'net_pnl':float(result.get('net_pnl',0) or 0),
      'realised_pnl':float(result.get('realised_pnl',0) or 0),
      'open_pnl':float(result.get('open_pnl',0) or 0),
      'return_on_max_capital_pct':float(result.get('return_on_max_capital_pct',0) or 0),
      'maximum_drawdown_pct_of_capital':float(result.get('maximum_drawdown_pct_of_capital',0) or 0),
      'closed_deals':int(result.get('closed_deals',0) or 0),
      'average_trade_hours':float(result.get('average_trade_hours',0) or 0),
      'longest_completed_trade_hours':float(result.get('longest_trade_hours',0) or 0),
      'effective_longest_trade_hours':float(research.get('effective_longest_trade_hours',max(float(result.get('longest_trade_hours',0) or 0),float((result.get('open_position') or {}).get('hours_open',0) or 0)))),
      'profitable_windows':int(research.get('profitable_windows',0) or 0),
      'open_position':result.get('open_position')
    }

def build_research_experiment(asset:dict[str,Any],candles:list[Candle],signals:list[dict[str,Any]|None],baseline:dict[str,Any],execution:dict[str,Any])->dict[str,Any]|None:
    ecfg=asset.get('research_experiments') or {}
    hypotheses=ecfg.get('hypotheses') or []
    if not ecfg.get('enabled') or not ecfg.get('auto_generate') or not hypotheses:
        return None
    baseline_research=baseline.get('research') or {}; checks=baseline_research.get('checks') or {}
    failed=[]
    if checks and not checks.get('positive_net_pnl',True): failed.append('positive_net_pnl')
    if checks and not checks.get('maximum_effective_trade_days',True): failed.append('maximum_effective_trade_days')
    if checks and not checks.get('profitable_windows',True): failed.append('profitable_windows')
    if not failed:
        return {'status':'NO EXPERIMENT REQUIRED','baseline_id':ecfg.get('baseline_id','SUI-A'),'reason':'Candidate A currently passes the monitored risk gates.','failed_gates':[],'candidates':[]}
    a=compact_metrics(baseline); baseline_open=a.get('open_position') or {}
    problem_regime=baseline_open.get('regime') or 'Low'
    problem_entry=(baseline_open.get('entry_signal') or {}) if baseline_open else {}
    results=[]
    min_deal_retention=float(ecfg.get('minimum_deal_retention_pct',25.0)); max_dd_worse=float(ecfg.get('maximum_drawdown_worsening_pp',5.0))
    for h in hypotheses:
        candidate=copy.deepcopy(asset); candidate['id']=h.get('id'); candidate['display_name']=h.get('name')
        candidate.setdefault('entry_filter',{}).setdefault(problem_regime,{})[h['field']]=h['value']
        candidate.pop('research_experiments',None)
        cr=simulate(candles,signals,candidate,execution); b=compact_metrics(cr)
        improvement=b['net_pnl']-a['net_pnl']; duration_reduction=a['effective_longest_trade_hours']-b['effective_longest_trade_hours']
        dd_change=b['maximum_drawdown_pct_of_capital']-a['maximum_drawdown_pct_of_capital']
        baseline_deals=max(1,a['closed_deals']); retention=b['closed_deals']/baseline_deals*100
        candidate_open=b.get('open_position') or {}
        changed=bool(baseline_open and (not candidate_open or candidate_open.get('entry_time')!=baseline_open.get('entry_time')))
        # Ranking rewards solving the observed problem, while penalising over-restriction and worse drawdown.
        score=0.0
        score += max(-40,min(40,improvement/max(1,abs(a['net_pnl']))*40))
        score += max(-30,min(30,duration_reduction/max(24,a['effective_longest_trade_hours'])*30))
        score += 15 if changed else -10
        score += max(-15,min(15,dd_change*-2))
        if retention<min_deal_retention: score-=20
        elif retention>=60: score+=5
        diagnostic_pass=(improvement>float(ecfg.get('minimum_diagnostic_net_improvement',0)) and duration_reduction>0 and changed and dd_change>=-max_dd_worse and retention>=min_deal_retention)
        results.append({
          'candidate_id':h.get('id'),'candidate_name':h.get('name'),'hypothesis':h.get('hypothesis'),
          'amendment':{'regime':problem_regime,'field':h.get('field'),'value':h.get('value'),'human_rule':f"{problem_regime} {h.get('human_rule')}"},
          'metrics':b,'comparison':{'net_pnl_improvement':improvement,'effective_longest_trade_reduction_hours':duration_reduction,
          'maximum_drawdown_change_pct_points':dd_change,'blocked_or_replaced_current_problem_trade':changed,
          'closed_deal_retention_pct':retention,'diagnostic_pass':diagnostic_pass},'rank_score':round(score,3)
        })
    results.sort(key=lambda x:(x['comparison']['diagnostic_pass'],x['rank_score']),reverse=True)
    for i,r in enumerate(results,1): r['rank']=i
    winner=results[0] if results else None
    status='STRONGEST CANDIDATE — MANUAL REVIEW' if winner and winner['comparison']['diagnostic_pass'] else 'ALL DIAGNOSTICS REJECTED'
    diagnosis=[]
    if baseline_open:
        diagnosis.append(f"Candidate A has an unresolved {problem_regime} trade lasting {float(baseline_open.get('hours_open',0))/24:.1f} days.")
        if problem_entry:
            diagnosis.append(f"At entry: price vs EMA50 {float(problem_entry.get('distance_ema50',0)):.2f}%, price vs EMA200 {float(problem_entry.get('distance_ema200',0)):.2f}%, EMA200 slope {float(problem_entry.get('ema200_slope_pct',0)):.4f}%, ATR ratio {float(problem_entry.get('atr_expansion_ratio',0) or 0):.3f}, bearish candles {int(problem_entry.get('consecutive_bearish_candles',0) or 0)}.")
    diagnosis.append(f"Five one-variable hypotheses were applied to the actual problem regime ({problem_regime}) and ranked using profit, duration, drawdown, trade retention, and whether the problem trade changed.")
    return {'status':status,'evaluation_mode':'post_hoc_ranked_diagnostic','baseline_id':ecfg.get('baseline_id','SUI-A'),
      'failed_gates':failed,'problem_regime':problem_regime,'generated_automatically':True,'diagnosis':diagnosis,
      'baseline_metrics':a,'candidates':results,'winner':winner,'manual_approval_required':True,
      'manual_approval_note':ecfg.get('manual_approval_note'),
      'caveat':'All ranked diagnostics reuse data already observed by Candidate A. Even the winner is hypothesis evidence only and must begin a new forward comparison after manual approval.'}


def build_strategy_evolution(asset:dict[str,Any],candles:list[Candle],signals:list[dict[str,Any]|None],baseline:dict[str,Any],execution:dict[str,Any],experiment:dict[str,Any]|None)->dict[str,Any]|None:
    ecfg=asset.get('strategy_evolution') or {}
    if not ecfg.get('enabled') or not experiment:
        return None
    candidates=experiment.get('candidates') or []
    passing=[c for c in candidates if (c.get('comparison') or {}).get('diagnostic_pass')]
    passing.sort(key=lambda c:float(c.get('rank_score',0)),reverse=True)
    min_score=float(ecfg.get('minimum_single_rule_rank_score',20.0))
    qualified=[c for c in passing if float(c.get('rank_score',0))>=min_score]
    baseline_metrics=experiment.get('baseline_metrics') or compact_metrics(baseline)
    baseline_open=baseline_metrics.get('open_position') or {}
    suggestions=[]
    for c in qualified:
        suggestions.append({'type':'single_rule','priority':'High' if c.get('rank')==1 else 'Medium','candidate_id':c.get('candidate_id'),
          'title':c.get('candidate_name'),'reason':c.get('hypothesis'),'expected_evidence':{'net_improvement':(c.get('comparison') or {}).get('net_pnl_improvement'),
          'duration_reduction_hours':(c.get('comparison') or {}).get('effective_longest_trade_reduction_hours'),
          'drawdown_change_pp':(c.get('comparison') or {}).get('maximum_drawdown_change_pct_points')},
          'recommended_action':'Review for a new forward comparison; do not replace Candidate A.'})
    combinations=[]
    if ecfg.get('test_compatible_combinations') and len(qualified)>=2:
        problem_regime=experiment.get('problem_regime') or 'Low'
        maxn=int(ecfg.get('maximum_combination_candidates',6)); maxsize=int(ecfg.get('max_combination_size',2))
        combos=list(itertools.combinations(qualified[:4],min(2,maxsize)))[:maxn]
        a=baseline_metrics
        for idx,combo in enumerate(combos,1):
            candidate=copy.deepcopy(asset); candidate.pop('research_experiments',None); candidate.pop('strategy_evolution',None)
            rules=[]
            for item in combo:
                amend=item.get('amendment') or {}; candidate.setdefault('entry_filter',{}).setdefault(problem_regime,{})[amend.get('field')]=amend.get('value')
                rules.append(amend.get('human_rule'))
            cr=simulate(candles,signals,candidate,execution); b=compact_metrics(cr)
            improvement=b['net_pnl']-a['net_pnl']; duration=a['effective_longest_trade_hours']-b['effective_longest_trade_hours']; dd=b['maximum_drawdown_pct_of_capital']-a['maximum_drawdown_pct_of_capital']
            retention=b['closed_deals']/max(1,a['closed_deals'])*100
            op=b.get('open_position') or {}; changed=bool(baseline_open and (not op or op.get('entry_time')!=baseline_open.get('entry_time')))
            passed=improvement>float(ecfg.get('minimum_combination_net_improvement',0)) and duration>0 and changed and retention>=float(ecfg.get('minimum_deal_retention_pct',25))
            score=(improvement/max(1,abs(a['net_pnl']))*45)+(duration/max(24,a['effective_longest_trade_hours'])*30)+(-dd*2)+(10 if changed else -10)+(5 if retention>=60 else 0)
            combinations.append({'combination_id':f"SUI-G{idx}",'name':' + '.join(str(x.get('candidate_id')) for x in combo),'rules':rules,'metrics':b,
              'comparison':{'net_pnl_improvement':improvement,'duration_reduction_hours':duration,'drawdown_change_pp':dd,'trade_retention_pct':retention,'problem_trade_changed':changed,'diagnostic_pass':passed},'rank_score':round(score,3)})
        combinations.sort(key=lambda x:(x['comparison']['diagnostic_pass'],x['rank_score']),reverse=True)
        for i,c in enumerate(combinations,1): c['rank']=i
    best_single=qualified[0] if qualified else None; best_combo=combinations[0] if combinations and combinations[0]['comparison']['diagnostic_pass'] else None
    recommendation=None
    if best_combo and (not best_single or best_combo['rank_score']>float(best_single.get('rank_score',0))+5):
        recommendation={'kind':'combination','id':best_combo['combination_id'],'title':best_combo['name'],'status':'MANUAL REVIEW','reason':'A compatible two-rule combination produced the strongest post-hoc diagnostic score.'}
    elif best_single:
        recommendation={'kind':'single_rule','id':best_single.get('candidate_id'),'title':best_single.get('candidate_name'),'status':'MANUAL REVIEW','reason':'This one-variable hypothesis is the strongest interpretable improvement and should be tested before adding complexity.'}
    else:
        recommendation={'kind':'none','id':None,'title':'No strategy amendment recommended','status':'REJECT','reason':'No tested suggestion met the diagnostic safeguards.'}
    return {'version':'8.0','mode':'controlled_post_hoc_evolution','status':'SUGGESTIONS READY' if qualified else 'NO QUALIFIED SUGGESTIONS',
      'recommendation':recommendation,'single_rule_suggestions':suggestions,'combination_candidates':combinations,
      'audit':{'baseline_id':experiment.get('baseline_id'),'problem_regime':experiment.get('problem_regime'),'individual_hypotheses_tested':len(candidates),'individual_hypotheses_passed':len(passing),'qualified_suggestions':len(qualified),'combinations_tested':len(combinations)},
      'safeguards':ecfg.get('principles',[]),'manual_approval_required':True,'note':ecfg.get('suggestion_note')}

def write_deals(path:Path,deals:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=['entry_time','exit_time','regime','pnl','hours','safety_orders','capital','entry_distance_ema200_pct','entry_ema200_slope_pct']
    rows=[]
    for deal in deals:
        sig=deal.get('entry_signal') or {}
        rows.append({**{k:deal.get(k) for k in fields[:7]},
                     'entry_distance_ema200_pct':sig.get('distance_ema200'),
                     'entry_ema200_slope_pct':sig.get('ema200_slope_pct')})
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

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
        if not candles:
            result={'id':asset['id'],'display_name':asset['display_name'],'symbol':asset['symbol'],'production_status':asset.get('production_status','production'),
                    'history_start':None,'history_end':None,'candles':0,'net_pnl':0,'realised_pnl':0,'open_pnl':0,'return_on_max_capital_pct':0,
                    'maximum_drawdown_dollars':0,'maximum_drawdown_pct_of_capital':0,'max_theoretical_capital':0,'closed_deals':0,
                    'average_trade_hours':0,'longest_trade_hours':0,'skipped_entry_candles':0,'open_position':None,
                    'health':{'score':0,'status':'Review','flags':['No candle data available'],'positives':[]},
                    'latest':{'entry_allowed':False,'entry_reason':'No candle data available','recommended_bot':None},
                    'intelligence':{'opportunity_score':None,'action':'RESEARCH ONLY' if asset.get('production_status')!='production' else 'WAIT'},
                    'recent_deals':[],'all_deals':[]}
            if asset.get('production_status')!='production':
                result['research']={'mode':'research','label':asset.get('research_label'),'forward_test_start':asset.get('forward_test_start'),
                                    'promotion_status':'WAITING FOR FIRST KUCOIN SYNC','all_gates_pass':False,'checks':{},'gates':asset.get('promotion_gates',{})}
        else:
            asset_signals=indicators(candles,asset)
            result=simulate(candles,asset_signals,asset,cfg['execution'])
            if asset.get('production_status')!='production':
                result['experiment']=build_research_experiment(asset,candles,asset_signals,result,cfg['execution'])
                result['evolution']=build_strategy_evolution(asset,candles,asset_signals,result,cfg['execution'],result.get('experiment'))
        result['sync']={'new_candles':added,'error':error,'source':'KuCoin public spot candles API'}; result['strategy_config']={'regime':asset['regime'],'entry_filter':asset['entry_filter'],'bots':asset['bots']}
        write_deals(ROOT/asset['deal_log'],result.pop('all_deals')); outputs.append(result)
    payload={'version':cfg.get('app',{}).get('version','5.3.0'),'app':cfg.get('app',{}),'generated_at':datetime.now(timezone.utc).isoformat(),'workflow_status':'ok' if not any((a.get('sync') or {}).get('error') for a in outputs) else 'warning','portfolio':portfolio_intelligence(outputs),'assets':outputs}
    out=ROOT/cfg['execution']['output_json']; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    update_health_history(ROOT/'docs/health_history.json',payload,int(cfg.get('health_monitor',{}).get('history_points',180)))
    print(json.dumps(payload,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
