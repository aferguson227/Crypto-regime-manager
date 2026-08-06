#!/usr/bin/env python3
"""Operational Intelligence for CRM V39.0.0.
Read-only aggregation of system, data, deployment and trading health.
"""
from __future__ import annotations
import json, statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.release import application_version

ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'
OUT=DOCS/'operational_health.json'; ISSUES=DOCS/'issues.json'; HISTORY=DOCS/'performance_history.json'

def read(name:str, default:Any=None):
    try:return json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
    except Exception:return {} if default is None else default

def dt(value):
    try:return datetime.fromisoformat(str(value).replace('Z','+00:00')).astimezone(timezone.utc)
    except Exception:return None

def age_hours(value):
    x=dt(value)
    return None if not x else round((datetime.now(timezone.utc)-x).total_seconds()/3600,2)

def issue(severity, system, title, detail, action, metric=None):
    return {'severity':severity,'system':system,'title':title,'detail':detail,'recommended_action':action,'metric':metric,'first_detected_at':datetime.now(timezone.utc).isoformat(),'last_detected_at':datetime.now(timezone.utc).isoformat()}

def clamp(v): return max(0,min(100,round(float(v),1)))

def main()->int:
    now=datetime.now(timezone.utc).isoformat(); tc=read('threecommas.json'); cloud=read('cloud_reliability.json'); diag=read('diagnostics_runtime.json') or read('diagnostics.json'); ws=read('professional_workspace.json'); cap=read('capital_intelligence.json'); cmd=read('command_state.json')
    active=[]
    endpoints=[]
    for name,row in (tc.get('endpoint_diagnostics') or {}).items():
        observed=row.get('observed_at'); latency=row.get('latency_ms')
        endpoints.append({'name':name,'status':row.get('status','unknown'),'category':row.get('category','unknown'),'http_status':row.get('http_status'),'records':row.get('records'),'observed_at':observed,'age_hours':age_hours(observed),'latency_ms':latency,'message':row.get('message')})
        if row.get('status')!='pass': active.append(issue('warning' if row.get('category') in {'rate_limited','permission_denied'} else 'critical','3Commas',f'{name} endpoint {row.get("category","failed").replace("_"," ")}',row.get('message') or 'Endpoint failed.','Review 3Commas permissions, quota and the next scheduled retry.',{'http_status':row.get('http_status'),'records':row.get('records')}))
    tc_age=age_hours(tc.get('last_success_at') or tc.get('generated_at'))
    if tc_age is None or tc_age>2: active.append(issue('critical' if tc_age is None or tc_age>6 else 'warning','3Commas','3Commas data is stale',f'Last successful sync was {tc_age if tc_age is not None else "unknown"} hours ago.','Run the 3Commas workflow and inspect endpoint diagnostics.',{'age_hours':tc_age}))
    app_pipe=(cloud.get('pipelines') or {}).get('application') or {}; app_age=app_pipe.get('last_success_age_hours')
    if app_age is None or app_age>6: active.append(issue('critical' if app_age is None or app_age>12 else 'warning','Application','Application refresh is stale',f'Last successful application refresh age: {app_age}.','Run the autonomous refresh workflow and inspect its failed step.',{'age_hours':app_age}))
    dscore=((diag.get('overall') or {}).get('score')) or 0
    system_score=clamp(dscore)
    data_score=100
    if tc.get('status')=='partial': data_score-=20
    if tc_age is None:data_score-=40
    elif tc_age>2:data_score-=min(45,(tc_age-2)*8)
    if app_age is None:data_score-=30
    elif app_age>6:data_score-=min(35,(app_age-6)*5)
    decision=((ws.get('decision_readiness') or {}).get('score_pct')) or 0
    trading_score=70
    deals=[]
    for asset,payload in (tc.get('assets') or {}).items():
        for d in payload.get('deals') or []:
            created=dt(d.get('created_at')); duration=None if not created else round((datetime.now(timezone.utc)-created).total_seconds()/3600,1)
            rec={'asset':asset,'bot_name':d.get('bot_name'),'status':d.get('status'),'profit_pct':d.get('profit_pct'),'duration_hours':duration,'completed_safety_orders':d.get('completed_safety_orders'),'max_safety_orders':d.get('max_safety_orders'),'capital_used':d.get('capital_used'),'quote_currency':'USDT'}; deals.append(rec)
            if duration and duration>168: active.append(issue('warning','Trading',f'Long-running deal: {d.get("bot_name")}',f'Deal has been open for {duration} hours.','Review the deal and market regime manually; CRM remains read-only.',{'duration_hours':duration,'profit_pct':d.get('profit_pct')})); trading_score-=10
            if isinstance(d.get('profit_pct'),(int,float)) and d['profit_pct']<-10: active.append(issue('critical','Trading',f'Deep unrealised loss: {d.get("bot_name")}',f'Current profit is {d["profit_pct"]:.2f}%.','Review safety-order use and risk limits manually.',{'profit_pct':d['profit_pct']})); trading_score-=20
    deployment_score=100
    for p in (cloud.get('pipelines') or {}).values():
        if p.get('state')=='failure':deployment_score-=35
        elif p.get('state')=='warning':deployment_score-=15
    if active and not any(i['severity']=='critical' for i in active): overall='WARNING'
    elif any(i['severity']=='critical' for i in active): overall='CRITICAL'
    else: overall='HEALTHY'
    scores={'system':system_score,'data':clamp(data_score),'trading':clamp(trading_score),'deployment':clamp(deployment_score),'decision_readiness':clamp(decision)}
    overall_score=clamp(sum(scores.values())/len(scores))
    payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'overall':{'state':overall,'score_pct':overall_score,'active_issue_count':len(active),'critical_count':sum(i['severity']=='critical' for i in active),'warning_count':sum(i['severity']=='warning' for i in active)},'scores':scores,'threecommas':{'status':tc.get('status','unknown'),'last_attempt_at':tc.get('last_attempt_at'),'last_success_at':tc.get('last_success_at'),'last_success_age_hours':tc_age,'endpoints':endpoints,'accounts':len(tc.get('accounts') or []),'bots':sum(len(x.get('bots') or []) for x in (tc.get('assets') or {}).values()),'deals':len(deals)},'application':{'cloud_state':app_pipe.get('state','unknown'),'last_success_at':app_pipe.get('last_success_at'),'last_success_age_hours':app_age,'diagnostics_score_pct':system_score},'trading':{'active_deals':deals,'deal_count':len(deals)},'decision':{'primary_action':(ws.get('daily_decision') or {}).get('action'),'bot_name':(ws.get('daily_decision') or {}).get('bot_name'),'readiness_score_pct':decision,'ready_for_manual_action':(ws.get('decision_readiness') or {}).get('ready_for_manual_action',False)},'issues':active,'safeguards':{'read_only':True,'manual_approval_required':True}}
    OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); ISSUES.write_text(json.dumps({'application_version':application_version(),'generated_at':now,'issues':active},indent=2),encoding='utf-8')
    hist=read('performance_history.json',{'schema_version':'1.0','points':[]}); points=hist.get('points') or []; points.append({'generated_at':now,'overall_score_pct':overall_score,**scores,'threecommas_age_hours':tc_age,'application_age_hours':app_age,'active_issues':len(active)}); hist={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'retention_points':720,'points':points[-720:]}; HISTORY.write_text(json.dumps(hist,indent=2),encoding='utf-8')
    print(f'Operational health written: {OUT}'); return 0
if __name__=='__main__': raise SystemExit(main())
