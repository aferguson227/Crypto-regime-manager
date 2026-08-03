#!/usr/bin/env python3
"""Synchronise KuCoin candles and replay production and research strategies.

TEL and TAO remain production/advisory assets. SUI is a frozen research-only
candidate with automatic one-variable experiments, excluded from live
portfolio rankings until manually promoted.
"""
from __future__ import annotations
import argparse, copy, csv, hashlib, itertools, json, math, time, urllib.parse, urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
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
    if not path.exists(): return out
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

def sma(values:list[float],period:int)->list[float]:
    out=[math.nan]*len(values)
    if period<=0:return out
    run=0.0
    for i,v in enumerate(values):
        run+=v
        if i>=period: run-=values[i-period]
        if i>=period-1: out[i]=run/period
    return out

def indicators(candles:list[Candle],cfg:dict[str,Any])->list[dict[str,Any]|None]:
    rcfg=cfg['regime']; closes=[c.close for c in candles]
    e50=ema(closes,int(rcfg['fast_ema'])); e100=ema(closes,100); e150=ema(closes,150); e200=ema(closes,int(rcfg['slow_ema']))
    e12=ema(closes,12); e26=ema(closes,26)
    macd=[(e12[i]-e26[i]) if not math.isnan(e12[i]) and not math.isnan(e26[i]) else math.nan for i in range(len(closes))]
    macd_sig=ema([0.0 if math.isnan(x) else x for x in macd],9)
    macd_hist=[(macd[i]-macd_sig[i]) if not math.isnan(macd[i]) and not math.isnan(macd_sig[i]) else math.nan for i in range(len(closes))]
    rs=rsi(closes); rv=realised_vol(closes,int(rcfg['realised_volatility_window_candles']),int(rcfg['annualisation_periods'])); at=atr(candles,14)
    low=float(rcfg['low_volatility_threshold_pct']); high=float(rcfg['high_volatility_threshold_pct']); out=[]
    for i,c in enumerate(candles):
        if i<200 or math.isnan(rv[i]) or math.isnan(rs[i]): out.append(None); continue
        if rv[i]<low: regime='Low'
        elif rv[i]<high: regime='Medium'
        else:
            bullish=c.close>=e200[i] and e50[i]>=e200[i] and e50[i]>=e50[i-1]
            regime='High-Bull' if bullish else 'High-Bear'
        bearish=0; j=i
        while j>=0 and candles[j].close<candles[j].open:
            bearish+=1; j-=1
        atr_ratio=(at[i]/at[i-6]) if i>=6 and not math.isnan(at[i]) and not math.isnan(at[i-6]) and at[i-6]>0 else math.nan
        atr_window=[x for x in at[max(0,i-179):i+1] if not math.isnan(x)]
        atr_pct=(100*sum(1 for x in atr_window if x<=at[i])/len(atr_window)) if atr_window and not math.isnan(at[i]) else math.nan
        out.append({'regime':regime,'rv':rv[i],'ema50':e50[i],'ema100':e100[i],'ema200':e200[i],'rsi14':rs[i],
                    'distance_ema200':(c.close/e200[i]-1)*100,'distance_ema150':(c.close/e150[i]-1)*100,'distance_ema100':(c.close/e100[i]-1)*100,'distance_ema50':(c.close/e50[i]-1)*100,
                    'ema200_slope_pct':(e200[i]/e200[i-1]-1)*100 if i>0 else math.nan,
                    'ema200_24h_slope_pct':(e200[i]/e200[i-6]-1)*100 if i>=6 else math.nan,'ema100_24h_slope_pct':(e100[i]/e100[i-6]-1)*100 if i>=6 else math.nan,
                    'return24':(c.close/closes[i-6]-1)*100 if i>=6 else math.nan,
                    'ema50_slope_pct':(e50[i]/e50[i-1]-1)*100 if i>0 else math.nan,
                    'pullback20_pct':(1-c.close/max(closes[max(0,i-119):i+1]))*100,
                    'atr14':at[i],'atr_percentile':atr_pct,'atr_expansion_ratio':atr_ratio,'consecutive_bearish_candles':bearish,
                    'bullish_candle':1.0 if c.close>c.open else 0.0,
                    'rsi_recovery':1.0 if i>0 and not math.isnan(rs[i-1]) and rs[i]>rs[i-1] else 0.0,'rsi_two_candle_recovery':1.0 if i>1 and not math.isnan(rs[i-2]) and rs[i]>rs[i-1]>rs[i-2] else 0.0,
                    'macd_hist_improving':1.0 if i>0 and not math.isnan(macd_hist[i]) and not math.isnan(macd_hist[i-1]) and macd_hist[i]>macd_hist[i-1] else 0.0})
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
        ('min_ema200_slope_pct','ema200_slope_pct',lambda a,b:a<b,'EMA200 is falling faster than the allowed limit'),
        ('min_distance_from_ema100_pct','distance_ema100',lambda a,b:a<b,'Price is below the required EMA100 threshold'),('min_distance_from_ema150_pct','distance_ema150',lambda a,b:a<b,'Price is below the required EMA150 threshold'),
        ('min_ema200_24h_slope_pct','ema200_24h_slope_pct',lambda a,b:a<b,'EMA200 is not rising enough over 24 hours'),('min_ema100_24h_slope_pct','ema100_24h_slope_pct',lambda a,b:a<b,'EMA100 is not rising enough over 24 hours'),
        ('max_atr_percentile','atr_percentile',lambda a,b:a>b,'ATR percentile is above the allowed cap'),
        ('require_bullish_candle','bullish_candle',lambda a,b:a<b,'A bullish recovery candle is required'),
        ('require_rsi_recovery','rsi_recovery',lambda a,b:a<b,'RSI must be recovering'),('require_rsi_two_candle_recovery','rsi_two_candle_recovery',lambda a,b:a<b,'RSI must rise for two candles'),
        ('require_macd_hist_improving','macd_hist_improving',lambda a,b:a<b,'MACD histogram must be improving')]
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
        baseline_deals=max(1,a['closed_deals'])
        candidate_deals=int(b['closed_deals'])
        deal_count_ratio=candidate_deals/baseline_deals*100
        deal_count_change=candidate_deals-int(a['closed_deals'])
        retained_share=min(100.0,deal_count_ratio)
        candidate_open=b.get('open_position') or {}
        changed=bool(baseline_open and (not candidate_open or candidate_open.get('entry_time')!=baseline_open.get('entry_time')))
        # Ranking rewards solving the observed problem, while penalising over-restriction and worse drawdown.
        score=0.0
        score += max(-40,min(40,improvement/max(1,abs(a['net_pnl']))*40))
        score += max(-30,min(30,duration_reduction/max(24,a['effective_longest_trade_hours'])*30))
        score += 15 if changed else -10
        score += max(-15,min(15,dd_change*-2))
        if retained_share<min_deal_retention: score-=20
        elif retained_share>=60: score+=5
        diagnostic_pass=(improvement>float(ecfg.get('minimum_diagnostic_net_improvement',0)) and duration_reduction>0 and changed and dd_change>=-max_dd_worse and retained_share>=min_deal_retention)
        results.append({
          'candidate_id':h.get('id'),'candidate_name':h.get('name'),'hypothesis':h.get('hypothesis'),
          'amendment':{'regime':problem_regime,'field':h.get('field'),'value':h.get('value'),'human_rule':f"{problem_regime} {h.get('human_rule')}"},
          'metrics':b,'comparison':{'net_pnl_improvement':improvement,'effective_longest_trade_reduction_hours':duration_reduction,
          'maximum_drawdown_change_pct_points':dd_change,'blocked_or_replaced_current_problem_trade':changed,
          'baseline_closed_deals':int(a['closed_deals']),'candidate_closed_deals':candidate_deals,
          'closed_deal_count_change':deal_count_change,'closed_deal_count_ratio_pct':deal_count_ratio,
          'closed_deal_retained_share_pct':retained_share,'diagnostic_pass':diagnostic_pass},'rank_score':round(score,3)
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

    # Cluster rules that produce effectively identical outcomes. This stops
    # correlated filters from taking multiple top-ranking positions and from
    # being combined with one another as though they were independent evidence.
    def outcome_fingerprint(c:dict[str,Any])->tuple[Any,...]:
        m=c.get('metrics') or {}; x=c.get('comparison') or {}
        return (
          round(float(m.get('net_pnl',0) or 0),2),
          round(float(m.get('maximum_drawdown_pct_of_capital',0) or 0),2),
          round(float(m.get('effective_longest_trade_hours',0) or 0),1),
          int(m.get('closed_deals',0) or 0),
          bool(x.get('blocked_or_replaced_current_problem_trade')),
        )
    clusters:dict[tuple[Any,...],list[dict[str,Any]]]={}
    for c in qualified:
        clusters.setdefault(outcome_fingerprint(c),[]).append(c)
    representatives=[]; correlated_clusters=[]
    for members in clusters.values():
        members.sort(key=lambda c:float(c.get('rank_score',0)),reverse=True)
        representatives.append(members[0])
        if len(members)>1:
            correlated_clusters.append({
              'representative_id':members[0].get('candidate_id'),
              'candidate_ids':[m.get('candidate_id') for m in members],
              'reason':'These rules produced the same rounded P&L, drawdown, duration, deal count, and problem-trade outcome on the diagnostic sample.'
            })
    representatives.sort(key=lambda c:float(c.get('rank_score',0)),reverse=True)
    baseline_metrics=experiment.get('baseline_metrics') or compact_metrics(baseline)
    baseline_open=baseline_metrics.get('open_position') or {}
    suggestions=[]
    for c in representatives:
        suggestions.append({'type':'single_rule','priority':'High' if c.get('rank')==1 else 'Medium','candidate_id':c.get('candidate_id'),
          'title':c.get('candidate_name'),'reason':c.get('hypothesis'),'expected_evidence':{'net_improvement':(c.get('comparison') or {}).get('net_pnl_improvement'),
          'duration_reduction_hours':(c.get('comparison') or {}).get('effective_longest_trade_reduction_hours'),
          'drawdown_change_pp':(c.get('comparison') or {}).get('maximum_drawdown_change_pct_points')},
          'recommended_action':'Review for a new forward comparison; do not replace Candidate A.'})
    combinations=[]
    if ecfg.get('test_compatible_combinations') and len(representatives)>=2:
        problem_regime=experiment.get('problem_regime') or 'Low'
        maxn=int(ecfg.get('maximum_combination_candidates',6)); maxsize=int(ecfg.get('max_combination_size',2))
        combos=list(itertools.combinations(representatives[:4],min(2,maxsize)))[:maxn]
        a=baseline_metrics
        for idx,combo in enumerate(combos,1):
            candidate=copy.deepcopy(asset); candidate.pop('research_experiments',None); candidate.pop('strategy_evolution',None)
            rules=[]
            for item in combo:
                amend=item.get('amendment') or {}; candidate.setdefault('entry_filter',{}).setdefault(problem_regime,{})[amend.get('field')]=amend.get('value')
                rules.append(amend.get('human_rule'))
            cr=simulate(candles,signals,candidate,execution); b=compact_metrics(cr)
            improvement=b['net_pnl']-a['net_pnl']; duration=a['effective_longest_trade_hours']-b['effective_longest_trade_hours']; dd=b['maximum_drawdown_pct_of_capital']-a['maximum_drawdown_pct_of_capital']
            baseline_deals=max(1,int(a['closed_deals']))
            candidate_deals=int(b['closed_deals'])
            deal_count_ratio=candidate_deals/baseline_deals*100
            deal_count_change=candidate_deals-int(a['closed_deals'])
            retained_share=min(100.0,deal_count_ratio)
            op=b.get('open_position') or {}; changed=bool(baseline_open and (not op or op.get('entry_time')!=baseline_open.get('entry_time')))
            passed=improvement>float(ecfg.get('minimum_combination_net_improvement',0)) and duration>0 and changed and retained_share>=float(ecfg.get('minimum_deal_retention_pct',25))
            score=(improvement/max(1,abs(a['net_pnl']))*45)+(duration/max(24,a['effective_longest_trade_hours'])*30)+(-dd*2)+(10 if changed else -10)+(5 if retained_share>=60 else 0)
            combinations.append({'combination_id':f"SUI-G{idx}",'name':' + '.join(str(x.get('candidate_id')) for x in combo),'rules':rules,'metrics':b,
              'comparison':{'net_pnl_improvement':improvement,'duration_reduction_hours':duration,'drawdown_change_pp':dd,
              'baseline_closed_deals':int(a['closed_deals']),'candidate_closed_deals':candidate_deals,
              'closed_deal_count_change':deal_count_change,'closed_deal_count_ratio_pct':deal_count_ratio,
              'closed_deal_retained_share_pct':retained_share,'problem_trade_changed':changed,'diagnostic_pass':passed},'rank_score':round(score,3)})
        combinations.sort(key=lambda x:(x['comparison']['diagnostic_pass'],x['rank_score']),reverse=True)
        for i,c in enumerate(combinations,1): c['rank']=i
    best_single=representatives[0] if representatives else None; best_combo=combinations[0] if combinations and combinations[0]['comparison']['diagnostic_pass'] else None
    recommendation=None
    if best_combo and (not best_single or best_combo['rank_score']>float(best_single.get('rank_score',0))+5):
        recommendation={'kind':'combination','id':best_combo['combination_id'],'title':best_combo['name'],'status':'MANUAL REVIEW','reason':'A compatible two-rule combination produced the strongest post-hoc diagnostic score.'}
    elif best_single:
        recommendation={'kind':'single_rule','id':best_single.get('candidate_id'),'title':best_single.get('candidate_name'),'status':'MANUAL REVIEW','reason':'This one-variable hypothesis is the strongest interpretable improvement and should be tested before adding complexity.'}
    else:
        recommendation={'kind':'none','id':None,'title':'No strategy amendment recommended','status':'REJECT','reason':'No tested suggestion met the diagnostic safeguards.'}
    return {'version':'8.1','mode':'controlled_post_hoc_evolution','status':'SUGGESTIONS READY' if representatives else 'NO QUALIFIED SUGGESTIONS',
      'recommendation':recommendation,'single_rule_suggestions':suggestions,'combination_candidates':combinations,
      'correlated_hypothesis_clusters':correlated_clusters,
      'audit':{'baseline_id':experiment.get('baseline_id'),'problem_regime':experiment.get('problem_regime'),'individual_hypotheses_tested':len(candidates),'individual_hypotheses_passed':len(passing),'qualified_suggestions':len(representatives),'raw_qualified_hypotheses':len(qualified),'correlated_clusters':len(correlated_clusters),'combinations_tested':len(combinations)},
      'safeguards':ecfg.get('principles',[]),'manual_approval_required':True,'note':ecfg.get('suggestion_note')}

def build_cross_asset_evidence(cfg:dict[str,Any],outputs:list[dict[str,Any]],contexts:dict[str,dict[str,Any]])->dict[str,Any]|None:
    ecfg=cfg.get('cross_asset_evidence') or {}
    if not ecfg.get('enabled'):
        return None
    source_id=str(ecfg.get('source_asset','SUI'))
    source=next((x for x in outputs if x.get('id')==source_id),None)
    experiment=(source or {}).get('experiment') or {}
    evolution=(source or {}).get('evolution') or {}
    candidate_rows=experiment.get('candidates') or []
    if ecfg.get('test_only_qualified_suggestions',True):
        selected={str(x.get('candidate_id')) for x in (evolution.get('single_rule_suggestions') or [])}
        candidate_rows=[x for x in candidate_rows if str(x.get('candidate_id')) in selected]
    problem_regime=experiment.get('problem_regime') or 'Medium'
    baselines={x.get('id'):compact_metrics(x) for x in outputs}
    rules=[]
    for row in candidate_rows:
        amendment=row.get('amendment') or {}
        field=amendment.get('field'); value=amendment.get('value')
        if not field:
            continue
        asset_results=[]; improved=degraded=neutral=0
        for asset_id,ctx in contexts.items():
            baseline=baselines.get(asset_id)
            if not baseline:
                continue
            candidate=copy.deepcopy(ctx['asset'])
            candidate.pop('research_experiments',None); candidate.pop('strategy_evolution',None)
            candidate.setdefault('entry_filter',{}).setdefault(problem_regime,{})[field]=value
            replay=simulate(ctx['candles'],ctx['signals'],candidate,cfg['execution'])
            metrics=compact_metrics(replay)
            net_change=metrics['net_pnl']-baseline['net_pnl']
            duration_change=baseline['effective_longest_trade_hours']-metrics['effective_longest_trade_hours']
            dd_change=metrics['maximum_drawdown_pct_of_capital']-baseline['maximum_drawdown_pct_of_capital']
            base_deals=max(1,int(baseline['closed_deals'])); cand_deals=int(metrics['closed_deals'])
            retained=min(100.0,cand_deals/base_deals*100)
            duration_worsening=max(0.0,-duration_change)/max(24.0,baseline['effective_longest_trade_hours'])*100
            passes=(net_change>float(ecfg.get('minimum_net_improvement',0)) and
                    dd_change<=float(ecfg.get('maximum_drawdown_worsening_pp',5)) and
                    duration_worsening<=float(ecfg.get('maximum_duration_worsening_pct',10)) and
                    retained>=float(ecfg.get('minimum_deal_retention_pct',25)))
            materially_worse=(net_change < -max(1.0,abs(baseline['net_pnl'])*0.05) or
                              dd_change>float(ecfg.get('maximum_drawdown_worsening_pp',5)) or
                              duration_worsening>float(ecfg.get('maximum_duration_worsening_pct',10)))
            outcome='IMPROVED' if passes else ('DEGRADED' if materially_worse else 'NEUTRAL')
            if outcome=='IMPROVED': improved+=1
            elif outcome=='DEGRADED': degraded+=1
            else: neutral+=1
            asset_results.append({'asset_id':asset_id,'production_status':ctx['asset'].get('production_status','production'),
              'outcome':outcome,'baseline':baseline,'candidate':metrics,
              'comparison':{'net_pnl_change':net_change,'duration_reduction_hours':duration_change,
                'drawdown_change_pp':dd_change,'baseline_closed_deals':int(baseline['closed_deals']),
                'candidate_closed_deals':cand_deals,'closed_deal_retained_share_pct':retained}})
        tested=len(asset_results)
        if improved>=2 and degraded==0: verdict='PROMISING CROSS-ASSET RULE'
        elif improved==1 and degraded==0: verdict='ASSET-SPECIFIC PROMISE'
        elif degraded>=improved and degraded>0: verdict='DO NOT GENERALISE'
        else: verdict='MIXED EVIDENCE'
        confidence=round((improved*35 + neutral*10 - degraded*30)/max(1,tested),1)
        rules.append({'candidate_id':row.get('candidate_id'),'name':row.get('candidate_name'),'hypothesis':row.get('hypothesis'),
          'amendment':amendment,'problem_regime':problem_regime,'assets_tested':tested,'improved_assets':improved,
          'neutral_assets':neutral,'degraded_assets':degraded,'confidence_score':confidence,'verdict':verdict,
          'asset_results':asset_results})
    rules.sort(key=lambda x:(x['improved_assets'],-x['degraded_assets'],x['confidence_score']),reverse=True)
    recommendation=rules[0] if rules else None
    return {'version':'9.0','mode':'cross_asset_diagnostic_evidence','source_asset':source_id,
      'problem_regime':problem_regime,'rules':rules,
      'recommendation':({'candidate_id':recommendation['candidate_id'],'name':recommendation['name'],
        'verdict':recommendation['verdict'],'confidence_score':recommendation['confidence_score'],
        'next_action':'Review the asset-level evidence. Any live amendment still requires a new, asset-specific forward test.'} if recommendation else None),
      'audit':{'rules_tested':len(rules),'assets_available':len(contexts),'asset_ids':list(contexts)},
      'safeguards':ecfg.get('principles',[]),'note':ecfg.get('note')}


def build_asset_dna(cfg:dict[str,Any], outputs:list[dict[str,Any]], evidence:dict[str,Any]|None)->dict[str,Any]|None:
    dcfg=cfg.get('asset_dna') or {}
    if not dcfg.get('enabled') or not evidence:
        return None
    rules=evidence.get('rules') or []
    asset_ids=[str(x.get('id')) for x in outputs]
    profiles=[]
    vectors={}
    for asset_id in asset_ids:
        rule_effects=[]
        vector=[]
        for rule in rules:
            ar=next((x for x in (rule.get('asset_results') or []) if str(x.get('asset_id'))==asset_id),None)
            if not ar:
                continue
            b=ar.get('baseline') or {}; c=ar.get('candidate') or {}; x=ar.get('comparison') or {}
            base_net=float(b.get('net_pnl',0) or 0); net_change=float(x.get('net_pnl_change',0) or 0)
            base_duration=max(24.0,float(b.get('effective_longest_trade_hours',0) or 0)); duration_reduction=float(x.get('duration_reduction_hours',0) or 0)
            dd_change=float(x.get('drawdown_change_pp',0) or 0)
            base_deals=max(1,int(x.get('baseline_closed_deals',b.get('closed_deals',0)) or 1)); cand_deals=int(x.get('candidate_closed_deals',c.get('closed_deals',0)) or 0)
            deal_ratio=cand_deals/base_deals
            # Bounded, interpretable score from -10 to +10. Positive drawdown change means less-negative drawdown.
            profit_component=max(-5.0,min(5.0,net_change/max(100.0,abs(base_net))*5.0))
            duration_component=max(-2.0,min(2.0,duration_reduction/base_duration*2.0))
            drawdown_component=max(-2.0,min(2.0,dd_change/10.0*2.0))
            activity_component=max(-1.0,min(1.0,(deal_ratio-1.0)*2.0))
            score=round(profit_component+duration_component+drawdown_component+activity_component,2)
            vector.append(score)
            if score>=float(dcfg.get('strong_positive_score',4)): effect='STRONG POSITIVE'
            elif score>=float(dcfg.get('positive_score',1)): effect='POSITIVE'
            elif score<=float(dcfg.get('strong_negative_score',-4)): effect='HARMFUL'
            elif score<=float(dcfg.get('negative_score',-1)): effect='NEGATIVE'
            else: effect='NEUTRAL'
            rule_effects.append({
              'candidate_id':rule.get('candidate_id'),'name':rule.get('name'),'hypothesis':rule.get('hypothesis'),
              'effect':effect,'dna_score':score,'outcome':ar.get('outcome'),
              'comparison':{'net_pnl_change':net_change,'duration_reduction_hours':duration_reduction,
                'drawdown_change_pp':dd_change,'baseline_closed_deals':base_deals,
                'candidate_closed_deals':cand_deals,'deal_count_change':cand_deals-base_deals}
            })
        rule_effects.sort(key=lambda z:z['dna_score'],reverse=True)
        vectors[asset_id]=vector
        tested=len(rule_effects); pos=sum(1 for r in rule_effects if r['dna_score']>=1); neg=sum(1 for r in rule_effects if r['dna_score']<=-1)
        avg=round(sum(r['dna_score'] for r in rule_effects)/tested,2) if tested else 0.0
        confidence='HIGH' if tested>=6 else ('MEDIUM' if tested>=int(dcfg.get('minimum_rules_for_confidence',3)) else 'LOW')
        best=rule_effects[0] if rule_effects else None; worst=rule_effects[-1] if rule_effects else None
        profile_label='TREND-CONFIRMATION RESPONSIVE' if best and best['dna_score']>=4 else ('SELECTIVE BENEFIT' if pos else ('FILTER-SENSITIVE' if neg else 'INSUFFICIENT EVIDENCE'))
        profiles.append({'asset_id':asset_id,'production_status':next((x.get('production_status','production') for x in outputs if str(x.get('id'))==asset_id),'production'),
          'profile_label':profile_label,'confidence':confidence,'rules_tested':tested,'positive_rules':pos,'negative_rules':neg,
          'average_dna_score':avg,'best_rule':best,'worst_rule':worst,'rule_effects':rule_effects})
    # Simple similarity based on average absolute distance across common rule scores.
    similarities=[]
    for i,a in enumerate(asset_ids):
        for b in asset_ids[i+1:]:
            va,vb=vectors.get(a,[]),vectors.get(b,[])
            n=min(len(va),len(vb))
            if not n: continue
            mean_distance=sum(abs(va[j]-vb[j]) for j in range(n))/n
            similarity=max(0.0,100.0-mean_distance*10.0)
            similarities.append({'asset_a':a,'asset_b':b,'rules_compared':n,'similarity_score':round(similarity,1),
              'label':'SIMILAR RESPONSE' if similarity>=75 else ('PARTIAL SIMILARITY' if similarity>=45 else 'DISTINCT RESPONSE')})
    similarities.sort(key=lambda z:z['similarity_score'],reverse=True)
    return {'version':'10.0','mode':'asset_specific_research_dna','profiles':profiles,'similarities':similarities,
      'audit':{'assets_profiled':len(profiles),'distinct_rules':len(rules),'source':'Multi-Asset Evidence Library'},
      'safeguards':dcfg.get('principles',[]),'note':dcfg.get('note')}



def build_context_traits(cfg:dict[str,Any], outputs:list[dict[str,Any]], evidence:dict[str,Any]|None, dna:dict[str,Any]|None)->dict[str,Any]|None:
    tcfg=cfg.get('context_traits') or {}
    if not tcfg.get('enabled') or not dna:
        return None
    evidence_rules=(evidence or {}).get('rules') or []
    dna_profiles={str(p.get('asset_id')):p for p in (dna.get('profiles') or [])}
    profiles=[]
    for asset in outputs:
        aid=str(asset.get('id'))
        dp=dna_profiles.get(aid) or {}
        effects=dp.get('rule_effects') or []
        trend=[r for r in effects if any(k in str(r.get('name','')).upper() for k in ('EMA','TREND','STRUCTURAL'))]
        avg_trend=round(sum(float(r.get('dna_score',0) or 0) for r in trend)/len(trend),2) if trend else 0.0
        duration_days=round(sum(float((r.get('comparison') or {}).get('duration_reduction_hours',0) or 0) for r in effects)/max(1,len(effects))/24,1)
        dd_protection=round(sum(float((r.get('comparison') or {}).get('drawdown_change_pp',0) or 0) for r in effects)/max(1,len(effects)),1)
        activity_change=round(sum(float((r.get('comparison') or {}).get('deal_count_change',0) or 0) for r in effects)/max(1,len(effects)),1)
        tested=len(effects)
        confidence='HIGH' if tested>=8 else ('MEDIUM' if tested>=int(tcfg.get('minimum_rules_for_context_confidence',4)) else 'LOW')
        if avg_trend>=4: trend_label='STRONGLY TREND-CONFIRMATION RESPONSIVE'
        elif avg_trend>=1: trend_label='TREND-CONFIRMATION RESPONSIVE'
        elif avg_trend<=-1: trend_label='TREND FILTERS MAY BE COSTLY'
        else: trend_label='NO CLEAR TREND RESPONSE YET'
        traits=[
          {'name':'Trend-confirmation response','score':avg_trend,'label':trend_label,'basis':f'{len(trend)} trend-family rules'},
          {'name':'Duration rescue','score':duration_days,'unit':'days','label':'MATERIAL' if duration_days>=5 else ('MODEST' if duration_days>0 else 'NONE OBSERVED'),'basis':'Average longest-trade reduction'},
          {'name':'Drawdown protection','score':dd_protection,'unit':'pp','label':'MATERIAL' if dd_protection>=5 else ('MODEST' if dd_protection>0 else 'NONE OBSERVED'),'basis':'Average drawdown change'},
          {'name':'Activity sensitivity','score':activity_change,'unit':'deals','label':'HIGH' if abs(activity_change)>=20 else ('MODERATE' if abs(activity_change)>=5 else 'LOW'),'basis':'Average closed-deal change'}
        ]
        contexts=[]
        for rule in evidence_rules:
            ar=next((x for x in (rule.get('asset_results') or []) if str(x.get('asset_id'))==aid),None)
            if ar:
                contexts.append({'regime':rule.get('problem_regime'),'candidate_id':rule.get('candidate_id'),'rule':rule.get('name'),
                  'outcome':ar.get('outcome'),'net_pnl_change':(ar.get('comparison') or {}).get('net_pnl_change',0),
                  'duration_reduction_hours':(ar.get('comparison') or {}).get('duration_reduction_hours',0)})
        profiles.append({'asset_id':aid,'production_status':asset.get('production_status','production'),'confidence':confidence,
          'summary':trend_label,'rules_tested':tested,'traits':traits,'contexts':contexts})
    # Build a transparent research tree. Tested status is updated from actual evidence IDs.
    tested_ids={str(r.get('candidate_id')) for r in evidence_rules}
    id_map={'close_above_ema200':'SUI-B','close_above_ema50':'SUI-F'}
    tree=[]
    for family,children in (tcfg.get('research_tree') or {}).items():
        rows=[]
        for child in children:
            row=dict(child)
            cid=id_map.get(row.get('id'))
            if cid and cid in tested_ids: row['status']='tested'
            rows.append(row)
        tested_count=sum(1 for r in rows if r.get('status') in ('tested','diagnostic'))
        tree.append({'family':family,'tested_count':tested_count,'total_count':len(rows),'children':rows})
    # Suggestions prioritise untested siblings of the strongest observed family.
    suggestions=[]
    order=1
    for branch in tree:
        for child in branch['children']:
            if child.get('status')=='pending':
                suggestions.append({'priority':order,'family':branch['family'],'experiment_id':child.get('id'),'title':child.get('label'),
                  'reason':f"Extend the {branch['family'].lower()} branch with one new variable while preserving the frozen baseline.",
                  'approval':'MANUAL REVIEW REQUIRED'})
                order+=1
    return {'version':'11.0','mode':'contextual_asset_traits','profiles':profiles,'research_tree':tree,
      'next_experiments':suggestions[:6],'audit':{'assets_profiled':len(profiles),'evidence_rules':len(evidence_rules),'families':len(tree)},
      'safeguards':tcfg.get('principles',[]),'note':tcfg.get('note')}

def build_automatic_research_pipeline(cfg:dict[str,Any],outputs:list[dict[str,Any]],contexts:dict[str,Any])->dict[str,Any]|None:
    pcfg=cfg.get('automatic_research_pipeline') or {}
    if not pcfg.get('enabled'): return None
    source_id=str(pcfg.get('source_asset','SUI'))
    source=next((x for x in outputs if str(x.get('id'))==source_id),None)
    ctx=contexts.get(source_id)
    if not source or not ctx: return None
    baseline=compact_metrics(source); open_pos=baseline.get('open_position') or {}
    target_regime=str(open_pos.get('regime') or pcfg.get('default_regime','Medium'))
    experiments=pcfg.get('experiments') or []
    results=[]
    for item in experiments:
        asset=copy.deepcopy(ctx['asset']); asset.pop('research_experiments',None); asset.pop('strategy_evolution',None)
        asset['id']=item['id']; asset['display_name']=item['title']
        asset.setdefault('entry_filter',{}).setdefault(target_regime,{})[item['field']]=item['value']
        candidate=simulate(ctx['candles'],ctx['signals'],asset,cfg['execution']); m=compact_metrics(candidate)
        pnl_change=m['net_pnl']-baseline['net_pnl']; duration_change=baseline['effective_longest_trade_hours']-m['effective_longest_trade_hours']
        dd_change=m['maximum_drawdown_pct_of_capital']-baseline['maximum_drawdown_pct_of_capital']
        deal_change=m['closed_deals']-baseline['closed_deals']
        changed=bool(open_pos and (not m.get('open_position') or (m.get('open_position') or {}).get('entry_time')!=open_pos.get('entry_time')))
        pnl_norm=pnl_change/max(100.0,abs(baseline['net_pnl']))
        duration_norm=duration_change/max(24.0,baseline['effective_longest_trade_hours'])
        score=40*pnl_norm+25*duration_norm-2*dd_change+(10 if changed else 0)-max(0,-deal_change)*0.15
        status='PASS' if pnl_change>0 and duration_change>=0 and dd_change>=-float(pcfg.get('max_drawdown_worsening_pp',5)) else 'REJECT'
        results.append({'id':item['id'],'title':item['title'],'family':item['family'],'description':item['description'],
          'amendment':{'regime':target_regime,'field':item['field'],'value':item['value'],'human_rule':item['human_rule']},
          'status':status,'score':round(score,2),'metrics':m,'comparison':{'net_pnl_change':pnl_change,'duration_reduction_hours':duration_change,
          'drawdown_change_pp':dd_change,'deal_count_change':deal_change,'problem_trade_changed':changed}})
    results.sort(key=lambda r:(r['status']=='PASS',r['score']),reverse=True)
    for i,r in enumerate(results,1): r['rank']=i
    family_summary=[]
    for fam in sorted({r['family'] for r in results}):
        rows=[r for r in results if r['family']==fam]
        family_summary.append({'family':fam,'tested':len(rows),'passed':sum(1 for r in rows if r['status']=='PASS'),
          'best_score':max((r['score'] for r in rows),default=0),'best_experiment':max(rows,key=lambda r:r['score'])['title'] if rows else None})
    winner=results[0] if results else None
    return {'version':'12.0','mode':'automatic_diagnostic_research','source_asset':source_id,'target_regime':target_regime,
      'baseline_metrics':baseline,'experiments':results,'winner':winner,'family_summary':family_summary,
      'audit':{'experiments_run':len(results),'passed':sum(1 for r in results if r['status']=='PASS'),'rejected':sum(1 for r in results if r['status']=='REJECT')},
      'execution_policy':'Experiments run automatically on every workflow using the frozen diagnostic history.',
      'promotion_policy':'No experiment can alter a production strategy or begin a live forward test without explicit manual approval.',
      'note':pcfg.get('note')}



def build_autonomous_research_evolution(cfg:dict[str,Any],outputs:list[dict[str,Any]],contexts:dict[str,Any],pipeline:dict[str,Any]|None)->dict[str,Any]|None:
    acfg=cfg.get('autonomous_research_evolution') or {}
    if not acfg.get('enabled') or not pipeline: return None
    source_id=str(acfg.get('source_asset','SUI')); source=next((x for x in outputs if str(x.get('id'))==source_id),None); ctx=contexts.get(source_id)
    if not source or not ctx: return None
    baseline=compact_metrics(source); open_pos=baseline.get('open_position') or {}; target_regime=str(open_pos.get('regime') or pipeline.get('target_regime') or 'Medium')
    family_rows=pipeline.get('family_summary') or []; dominant=max(family_rows,key=lambda x:(x.get('passed',0),x.get('best_score',-999)),default=None)
    dominant_family=(dominant or {}).get('family')
    passed=int((dominant or {}).get('passed',0) or 0)
    queue=[]
    if dominant_family and passed>=int(acfg.get('minimum_family_passes',2)):
        queue=list((acfg.get('families') or {}).get(dominant_family,[]))
    if not queue:
        for fam,rows in (acfg.get('families') or {}).items():
            if rows: queue.append(rows[0])
    queue=queue[:int(acfg.get('max_experiments_per_cycle',8))]
    results=[]
    for item in queue:
        asset=copy.deepcopy(ctx['asset']); asset.pop('research_experiments',None); asset.pop('strategy_evolution',None)
        asset['id']=item['id']; asset['display_name']=item['title']; asset.setdefault('entry_filter',{}).setdefault(target_regime,{})[item['field']]=item['value']
        replay=simulate(ctx['candles'],ctx['signals'],asset,cfg['execution']); m=compact_metrics(replay)
        pnl=m['net_pnl']-baseline['net_pnl']; dur=baseline['effective_longest_trade_hours']-m['effective_longest_trade_hours']; dd=m['maximum_drawdown_pct_of_capital']-baseline['maximum_drawdown_pct_of_capital']; deals=m['closed_deals']-baseline['closed_deals']
        changed=bool(open_pos and (not m.get('open_position') or (m.get('open_position') or {}).get('entry_time')!=open_pos.get('entry_time')))
        score=40*pnl/max(100.0,abs(baseline['net_pnl']))+25*dur/max(24.0,baseline['effective_longest_trade_hours'])-2*dd+(10 if changed else 0)-max(0,-deals)*0.15
        status='PASS' if pnl>0 and dur>=0 and dd>=-5 else 'REJECT'
        results.append({'id':item['id'],'title':item['title'],'family':dominant_family or 'Exploration','status':status,'score':round(score,2),'metrics':m,'amendment':{'regime':target_regime,'field':item['field'],'value':item['value'],'human_rule':item['human_rule']},'comparison':{'net_pnl_change':pnl,'duration_reduction_hours':dur,'drawdown_change_pp':dd,'deal_count_change':deals,'problem_trade_changed':changed}})
    results.sort(key=lambda r:(r['status']=='PASS',r['score']),reverse=True)
    for i,r in enumerate(results,1): r['rank']=i
    winner=results[0] if results else None
    passed_results=[r for r in results if r['status']=='PASS' and r['score']>=float(acfg.get('minimum_score',10))]
    bridge=acfg.get('decision_bridge') or {}; research=(source.get('research') or {}); checks=research.get('checks') or {}
    forward_ready=bool(checks and all(checks.values()))
    confidence=min(95,round(25+10*len(passed_results)+5*passed,1)) if passed_results else 10
    advisory_status='FORWARD TEST CANDIDATE' if winner and winner['status']=='PASS' else 'NO DECISION CANDIDATE'
    if forward_ready and confidence>=float(bridge.get('minimum_confidence_pct',70)): advisory_status='MANUAL BOT REVIEW ELIGIBLE'
    decision={'status':advisory_status,'confidence_pct':confidence,'entry_rule_candidate':winner.get('amendment') if winner else None,'recommended_action':'Freeze the winning research rule and begin a new forward test; do not alter live bots yet.' if winner and winner['status']=='PASS' else 'Keep current bot decisions unchanged.','dca_settings':'UNCHANGED — DCA optimisation remains a separate validated research stage.','exit_policy':'UNCHANGED — no automatic close signal is authorised.','live_execution_authorised':False,'manual_approval_required':True}
    return {'version':'13.0','mode':'self_directed_research_evolution','source_asset':source_id,'target_regime':target_regime,'dominant_family':dominant_family,'family_evidence':dominant,'queue_generated_automatically':True,'experiments':results,'winner':winner,'decision_bridge':decision,'audit':{'experiments_run':len(results),'passed':sum(1 for r in results if r['status']=='PASS'),'rejected':sum(1 for r in results if r['status']=='REJECT')},'note':acfg.get('note')}


def _canonical_hash(value:Any)->str:
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()[:16]

def _load_registry(path:Path)->dict[str,Any]:
    if not path.exists():
        return {'schema_version':'1.0','candidates':[],'events':[]}
    try:
        value=load_json(path)
        if not isinstance(value,dict): raise ValueError('registry must be an object')
        value.setdefault('schema_version','1.0'); value.setdefault('candidates',[]); value.setdefault('events',[])
        return value
    except Exception as exc:
        return {'schema_version':'1.0','candidates':[],'events':[], 'load_warning':str(exc)}

def _next_candidate_id(registry:dict[str,Any],prefix:str)->str:
    used=[]
    for row in registry.get('candidates',[]):
        cid=str(row.get('candidate_id',''))
        if cid.startswith(prefix):
            try: used.append(int(cid[len(prefix):]))
            except ValueError: pass
    return f"{prefix}{max(used,default=0)+1}"

def build_candidate_intelligence(cfg:dict[str,Any],outputs:list[dict[str,Any]],contexts:dict[str,Any],autonomy:dict[str,Any]|None)->dict[str,Any]|None:
    ccfg=cfg.get('candidate_intelligence') or {}
    if not ccfg.get('enabled'): return None
    registry_path=ROOT/str(ccfg.get('registry_file','docs/candidate_registry.json'))
    registry=_load_registry(registry_path)
    now=datetime.now(timezone.utc)
    source_id=str(ccfg.get('source_asset','SUI'))
    winner=(autonomy or {}).get('winner') or {}
    bridge=(autonomy or {}).get('decision_bridge') or {}
    nomination=copy.deepcopy(ccfg.get('nominated_candidate') or {})
    use_autonomy=bool(bridge.get('status')=='FORWARD TEST CANDIDATE' and winner.get('status')=='PASS')
    if not use_autonomy and nomination:
        source_id=str(nomination.get('asset_id') or source_id)
        winner={'id':nomination.get('source_experiment_id'),'title':nomination.get('name'),'status':'PASS','amendment':nomination.get('amendment'),'score':nomination.get('diagnostic_score'),'metrics':{},'comparison':{}}
        bridge={'status':'FORWARD TEST CANDIDATE','confidence_pct':nomination.get('diagnostic_confidence_pct',0)}
    registered=None
    if ccfg.get('auto_register_forward_test_candidate') and bridge.get('status')=='FORWARD TEST CANDIDATE' and winner.get('status')=='PASS':
        amendment=copy.deepcopy(winner.get('amendment') or {})
        target_regime=(autonomy or {}).get('target_regime') if use_autonomy else nomination.get('regime')
        family=(autonomy or {}).get('dominant_family') if use_autonomy else nomination.get('family')
        signature={'asset_id':source_id,'regime':target_regime,'amendment':amendment,'source_version':(autonomy or {}).get('version') if use_autonomy else '13.0','source_experiment_id':winner.get('id')}
        fingerprint=_canonical_hash(signature)
        existing=next((x for x in registry['candidates'] if x.get('fingerprint')==fingerprint),None)
        if existing:
            registered=existing
        else:
            cid=_next_candidate_id(registry,str(ccfg.get('candidate_prefix','SUI-T')))
            ctx=contexts.get(source_id) or {}
            candles=ctx.get('candles') or []
            last_completed=candles[-1].ts if candles else int(now.timestamp()//14400*14400)
            forward_start=last_completed+14400
            metrics=copy.deepcopy(winner.get('metrics') or {})
            comparison=copy.deepcopy(winner.get('comparison') or {})
            registered={
              'candidate_id':cid,'fingerprint':fingerprint,'asset_id':source_id,'regime':target_regime,
              'name':nomination.get('name') if nomination and not use_autonomy else f"{source_id} {cid.split('-')[-1]} Trend Candidate",'family':family,
              'rule':amendment,'human_rule':amendment.get('human_rule'),'status':'FROZEN',
              'lifecycle_stage_index':2,'created_at':now.isoformat(),'frozen_at':now.isoformat(),
              'forward_test_start':iso(forward_start),'source_engine_version':'13.0','registered_by_engine_version':'14.0',
              'source_experiment_id':winner.get('id'),'diagnostic_score':winner.get('score'),
              'diagnostic_metrics':metrics,'diagnostic_comparison':comparison,'diagnostic_confidence_pct':bridge.get('confidence_pct'),
              'immutable':True,'production_effect':'NONE','live_execution_authorised':False,'dca_settings_status':'UNCHANGED',
              'notes':['Forward-test measurements begin only on candles at or after forward_test_start.','Any changed rule must be registered as a new candidate.']
            }
            registry['candidates'].append(registered)
            registry['events'].append({'time':now.isoformat(),'candidate_id':cid,'event':'REGISTERED_AND_FROZEN','from_stage':'DIAGNOSTIC WINNER','to_stage':'FROZEN','fingerprint':fingerprint})
    registry['updated_at']=now.isoformat(); registry['engine_version']='14.0'
    registry_path.parent.mkdir(parents=True,exist_ok=True); registry_path.write_text(json.dumps(registry,indent=2),encoding='utf-8')
    lifecycle=ccfg.get('lifecycle') or []
    rows=[]
    for c in registry.get('candidates',[]):
        idx=int(c.get('lifecycle_stage_index',0) or 0)
        rows.append({**c,'lifecycle':[{'stage':stage,'complete':i<=idx,'current':i==idx} for i,stage in enumerate(lifecycle)]})
    rows.sort(key=lambda x:x.get('created_at',''),reverse=True)
    graph={'family':(autonomy or {}).get('dominant_family'),'nodes':[]}
    for exp in (autonomy or {}).get('experiments') or []:
        graph['nodes'].append({'experiment_id':exp.get('id'),'title':exp.get('title'),'status':exp.get('status'),'score':exp.get('score'),'selected':bool(registered and exp.get('id')==registered.get('source_experiment_id'))})
    return {'version':'14.0','mode':'immutable_candidate_registry','registry_file':str(ccfg.get('registry_file')),'active_candidate':registered,'candidates':rows,'candidate_count':len(rows),'evidence_graph':graph,'lifecycle':lifecycle,'manual_approval_required':True,'live_execution_authorised':False,'principles':ccfg.get('principles',[]),'note':ccfg.get('note')}


def _candidate_asset(base_asset:dict[str,Any], candidate:dict[str,Any], forward_start:str)->dict[str,Any]:
    asset=copy.deepcopy(base_asset)
    asset.pop('research_experiments',None); asset.pop('strategy_evolution',None)
    asset['id']=str(candidate.get('candidate_id'))
    asset['display_name']=str(candidate.get('name') or candidate.get('candidate_id'))
    asset['production_status']='research'
    asset['research_label']='Frozen candidate forward validation'
    asset['forward_test_start']=forward_start
    amendment=candidate.get('rule') or {}
    regime=str(amendment.get('regime') or candidate.get('regime') or 'Medium')
    field=amendment.get('field')
    if field:
        asset.setdefault('entry_filter',{}).setdefault(regime,{})[field]=amendment.get('value')
    return asset

def _forward_gate_checks(row:dict[str,Any], gates:dict[str,Any])->dict[str,bool]:
    return {
      'minimum_days':float(row.get('forward_days',0))>=float(gates.get('minimum_forward_days',30)),
      'minimum_candles':int(row.get('forward_candles',0))>=int(gates.get('minimum_forward_candles',180)),
      'minimum_candidate_deals':int(row.get('candidate_metrics',{}).get('closed_deals',0))>=int(gates.get('minimum_candidate_deals',3)),
      'candidate_positive_pnl':float(row.get('candidate_metrics',{}).get('net_pnl',0))>0,
      'not_worse_than_baseline':float(row.get('comparison',{}).get('net_pnl_change',0))>=float(gates.get('minimum_pnl_advantage',0)),
      'drawdown_limit':abs(min(0,float(row.get('candidate_metrics',{}).get('maximum_drawdown_pct_of_capital',0))))<=float(gates.get('maximum_drawdown_pct',25)),
      'maximum_trade_days':float(row.get('candidate_metrics',{}).get('effective_longest_trade_hours',0))/24<=float(gates.get('maximum_effective_trade_days',30))
    }

def build_forward_validation(cfg:dict[str,Any], outputs:list[dict[str,Any]], contexts:dict[str,Any], candidate_intelligence:dict[str,Any]|None)->dict[str,Any]|None:
    fcfg=cfg.get('forward_validation_manager') or {}
    if not fcfg.get('enabled') or not candidate_intelligence: return None
    registry_path=ROOT/str((cfg.get('candidate_intelligence') or {}).get('registry_file','docs/candidate_registry.json'))
    registry=_load_registry(registry_path); now=datetime.now(timezone.utc); rows=[]
    for candidate in registry.get('candidates',[]):
        source_id=str(candidate.get('asset_id')); ctx=contexts.get(source_id)
        if not ctx: continue
        start_text=str(candidate.get('forward_test_start') or '')
        if not start_text: continue
        start_ts=int(datetime.fromisoformat(start_text.replace('Z','+00:00')).timestamp())
        # Independent validation uses only candles whose timestamp is at or after
        # the immutable candidate forward-test start. Historical diagnostic candles
        # are never counted toward candidate age, sample-size gates or windows.
        forward_candles=[c for c in ctx['candles'] if c.ts>=start_ts]
        pre_start_candles_ignored=sum(1 for c in ctx['candles'] if c.ts<start_ts)
        base_asset=copy.deepcopy(ctx['asset']); base_asset.pop('research_experiments',None); base_asset.pop('strategy_evolution',None)
        base_asset['id']=source_id+'-FORWARD-BASELINE'; base_asset['display_name']=source_id+' Forward Baseline'; base_asset['production_status']='research'; base_asset['forward_test_start']=start_text
        baseline=simulate(ctx['candles'],ctx['signals'],base_asset,cfg['execution'])
        cand_asset=_candidate_asset(ctx['asset'],candidate,start_text)
        cand=simulate(ctx['candles'],ctx['signals'],cand_asset,cfg['execution'])
        bm=compact_metrics(baseline); cm=compact_metrics(cand)
        days=((forward_candles[-1].ts-start_ts)/86400+4/24) if forward_candles else 0.0
        comparison={'net_pnl_change':cm['net_pnl']-bm['net_pnl'],'drawdown_change_pp':cm['maximum_drawdown_pct_of_capital']-bm['maximum_drawdown_pct_of_capital'],'duration_reduction_hours':bm['effective_longest_trade_hours']-cm['effective_longest_trade_hours'],'deal_count_change':cm['closed_deals']-bm['closed_deals']}
        candidate_windows=int(cm.get('profitable_windows',0) or 0)
        completed_windows=max(0,int(days//30))
        first_forward=iso(forward_candles[0].ts) if forward_candles else None
        last_forward=iso(forward_candles[-1].ts) if forward_candles else None
        integrity_ok=(not forward_candles) or forward_candles[0].ts>=start_ts
        row={'candidate_id':candidate.get('candidate_id'),'asset_id':source_id,'regime':candidate.get('regime'),'human_rule':candidate.get('human_rule'),'forward_test_start':start_text,'forward_days':days,'forward_candles':len(forward_candles),'first_forward_candle':first_forward,'last_forward_candle':last_forward,'pre_start_candles_ignored':pre_start_candles_ignored,'completed_30_day_windows':completed_windows,'profitable_30_day_windows':candidate_windows,'data_integrity_ok':integrity_ok,'data_integrity_warning':None if integrity_ok else 'First forward candle predates the immutable candidate forward-test start.','baseline_metrics':bm,'candidate_metrics':cm,'comparison':comparison,'latest_candidate':cand.get('latest'),'latest_baseline':baseline.get('latest')}
        checks=_forward_gate_checks(row,fcfg.get('promotion_gates') or {}); row['checks']=checks; row['all_gates_pass']=bool(checks and all(checks.values()))
        if not forward_candles: status='WAITING FOR FIRST POST-FREEZE CANDLE'
        elif row['all_gates_pass']: status='PASS — PAPER-TRADING REVIEW ELIGIBLE'
        else: status='COLLECTING FORWARD EVIDENCE'
        row['status']=status
        # Safe automatic lifecycle transition: Frozen -> Forward Test only.
        if forward_candles and candidate.get('status')=='FROZEN':
            candidate['status']='FORWARD TEST'; candidate['lifecycle_stage_index']=3
            registry['events'].append({'time':now.isoformat(),'candidate_id':candidate.get('candidate_id'),'event':'FORWARD_TEST_STARTED','from_stage':'FROZEN','to_stage':'FORWARD TEST','first_forward_candle':iso(forward_candles[0].ts)})
        candidate['forward_validation']={'updated_at':now.isoformat(),'status':status,'forward_days':days,'forward_candles':len(forward_candles),'first_forward_candle':first_forward,'last_forward_candle':last_forward,'completed_30_day_windows':completed_windows,'profitable_30_day_windows':candidate_windows,'data_integrity_ok':integrity_ok,'all_gates_pass':row['all_gates_pass'],'checks':checks}
        rows.append(row)
    registry['updated_at']=now.isoformat(); registry['engine_version']='15.3'; registry_path.write_text(json.dumps(registry,indent=2),encoding='utf-8')
    return {'version':'15.3','mode':'frozen_candidate_forward_validation','candidates':rows,'candidate_count':len(rows),'promotion_gates':fcfg.get('promotion_gates',{}),'live_execution_authorised':False,'manual_approval_required_for_paper_trading':True,'note':fcfg.get('note')}

def build_advisory_decisions(cfg:dict[str,Any], contexts:dict[str,Any], forward_validation:dict[str,Any]|None)->dict[str,Any]|None:
    dcfg=cfg.get('advisory_decision_preview') or {}
    if not dcfg.get('enabled') or not forward_validation: return None
    decisions=[]
    for row in forward_validation.get('candidates',[]):
        cid=row.get('candidate_id'); source_id=row.get('asset_id'); ctx=contexts.get(source_id)
        if not ctx or not ctx.get('signals'): continue
        latest=ctx['signals'][-1]
        candidate=next((c for c in _load_registry(ROOT/str((cfg.get('candidate_intelligence') or {}).get('registry_file','docs/candidate_registry.json'))).get('candidates',[]) if c.get('candidate_id')==cid),None)
        if not latest or not candidate: continue
        asset=_candidate_asset(ctx['asset'],candidate,candidate.get('forward_test_start'))
        current_regime=latest.get('regime')
        target_regime=candidate.get('regime')
        rule_applicable=current_regime==target_regime
        if rule_applicable:
            allowed,reason=permission(latest,asset.get('entry_filter',{}))
            rule_state='PASS' if allowed else 'BLOCK'
        else:
            allowed=None
            rule_state='NOT APPLICABLE'
            reason=f"Candidate applies only to {target_regime}; current regime is {current_regime}."
        eligible=bool(row.get('all_gates_pass'))
        action='RESEARCH WAIT'
        if eligible and rule_applicable:
            action='ADVISORY ENTRY ALLOWED' if allowed else 'ADVISORY ENTRY BLOCKED'
        elif eligible:
            action='WAIT FOR TARGET REGIME'
        decisions.append({'candidate_id':cid,'asset_id':source_id,'regime':current_regime,'target_regime':target_regime,'candidate_rule_applicable_now':rule_applicable,'candidate_rule_passes_now':allowed,'candidate_rule_state':rule_state,'reason':reason,'forward_validation_status':row.get('status'),'paper_trading_review_eligible':eligible,'action':action,'recommended_bot':(ctx['asset'].get('bots') or {}).get(current_regime,{}).get('name'),'dca_settings_status':'UNCHANGED','exit_policy':'UNCHANGED','live_execution_authorised':False})
    return {'version':'15.1','mode':'advisory_preview_only','decisions':decisions,'live_execution_authorised':False,'note':dcfg.get('note')}

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
    cfg=load_json(CONFIG); APP_CONFIG=cfg; outputs=[]; contexts={}
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
            contexts[asset['id']]={'asset':copy.deepcopy(asset),'candles':candles,'signals':asset_signals}
            result=simulate(candles,asset_signals,asset,cfg['execution'])
            if asset.get('production_status')!='production':
                result['experiment']=build_research_experiment(asset,candles,asset_signals,result,cfg['execution'])
                result['evolution']=build_strategy_evolution(asset,candles,asset_signals,result,cfg['execution'],result.get('experiment'))
        result['sync']={'new_candles':added,'error':error,'source':'KuCoin public spot candles API'}; result['strategy_config']={'regime':asset['regime'],'entry_filter':asset['entry_filter'],'bots':asset['bots']}
        write_deals(ROOT/asset['deal_log'],result.pop('all_deals')); outputs.append(result)
    evidence_library=build_cross_asset_evidence(cfg,outputs,contexts)
    asset_dna=build_asset_dna(cfg,outputs,evidence_library)
    context_traits=build_context_traits(cfg,outputs,evidence_library,asset_dna)
    automatic_research=build_automatic_research_pipeline(cfg,outputs,contexts)
    autonomous_evolution=build_autonomous_research_evolution(cfg,outputs,contexts,automatic_research)
    candidate_intelligence=build_candidate_intelligence(cfg,outputs,contexts,autonomous_evolution)
    forward_validation=build_forward_validation(cfg,outputs,contexts,candidate_intelligence)
    advisory_decisions=build_advisory_decisions(cfg,contexts,forward_validation)
    payload={'version':cfg.get('app',{}).get('version','5.3.0'),'app':cfg.get('app',{}),'generated_at':datetime.now(timezone.utc).isoformat(),'workflow_status':'ok' if not any((a.get('sync') or {}).get('error') for a in outputs) else 'warning','portfolio':portfolio_intelligence(outputs),'evidence_library':evidence_library,'asset_dna':asset_dna,'context_traits':context_traits,'automatic_research':automatic_research,'autonomous_evolution':autonomous_evolution,'candidate_intelligence':candidate_intelligence,'forward_validation':forward_validation,'advisory_decisions':advisory_decisions,'assets':outputs}
    out=ROOT/cfg['execution']['output_json']; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    update_health_history(ROOT/'docs/health_history.json',payload,int(cfg.get('health_monitor',{}).get('history_points',180)))
    print(json.dumps(payload,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
