#!/usr/bin/env python3
"""CRM V39 engineering command centre, ROI backlog and release predictor."""
from __future__ import annotations
import json,statistics
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'engineering_health.json';READY=DOCS/'release_readiness.json'
def load(n,d={}):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except Exception:return d
def clamp(v):return max(0,min(100,round(float(v),1)))
def main():
 now=datetime.now(timezone.utc).isoformat();op=load('operational_health.json');ui=load('ui_health.json');heal=load('self_healing_status.json');gh=load('github_actions_health.json');dq=load('decision_quality.json');diag=load('diagnostics_runtime.json') or load('diagnostics.json');life=load('issue_lifecycle.json');repo=load('repository_health.json');perf=load('performance_history.json',{'snapshots':[]})
 evidence=(dq.get('scores') or {}).get('evidence_coverage_pct')
 scores={'application':clamp(((diag.get('overall') or {}).get('score')) or 0),'operations':clamp((op.get('overall') or {}).get('score_pct') or 0),'interface':clamp((ui.get('overall') or {}).get('score_pct') or (100 if (ui.get('overall') or {}).get('state')=='HEALTHY' else 70)),'actions':100 if gh.get('state')=='HEALTHY' else (70 if gh.get('state')=='WARNING' else 35),'self_healing':100 if heal.get('state') in {'HEALTHY','REPAIRED'} else 70,'repository':100 if repo.get('state') in {None,'HEALTHY'} else 75}
 backlog=[]
 for x in life.get('issues') or []:
  sev=x.get('severity','warning'); benefit=5 if sev in {'critical','high'} else (4 if sev in {'warning','medium'} else 2); frequency=min(5,max(1,int(x.get('historical_occurrences',1)))); confidence=5 if x.get('fingerprint')!='UNKNOWN' else 3; effort=1 if x.get('automatic') else 2; risk=1 if x.get('automatic') else 2; roi=round((benefit*frequency*confidence)/(effort+risk),1)
  backlog.append({**x,'user_benefit':benefit,'frequency':frequency,'confidence':confidence,'estimated_effort':effort,'regression_risk':risk,'roi_score':roi})
 backlog.sort(key=lambda x:x['roi_score'],reverse=True)
 blockers=[x for x in backlog if x.get('severity') in {'critical','high'}];overall=clamp(sum(scores.values())/len(scores));readiness=clamp(overall-15*len(blockers))
 build_times=[float(x.get('build_duration_seconds')) for x in perf.get('snapshots',[]) if isinstance(x.get('build_duration_seconds'),(int,float))]
 predicted_build=round(statistics.median(build_times),1) if build_times else None
 deploy=gh.get('successful_duration_median_seconds');success_rate=gh.get('success_rate_pct');regression='VERY_LOW' if not blockers and overall>=95 else ('LOW' if overall>=85 else 'MODERATE')
 ready=readiness>=85 and not blockers
 decision_display={'state':'LEARNING','label':'Insufficient evidence','evidence_coverage_pct':evidence} if evidence is None or float(evidence)<30 else {'state':dq.get('state'),'label':dq.get('state'),'evidence_coverage_pct':evidence}
 payload={'schema_version':'2.0','application_version':application_version(),'generated_at':now,'overall':{'state':'HEALTHY' if overall>=90 else ('WARNING' if overall>=70 else 'DEGRADED'),'score_pct':overall},'scores':scores,'action_queue':backlog[:12],'highest_value_improvements':backlog[:5],'recently_closed':life.get('recently_closed',[])[:10],'technical_debt':{'state':'LOW' if len(backlog)<4 else ('MODERATE' if len(backlog)<10 else 'HIGH'),'known_items':len(backlog)},'decision_quality_display':decision_display,'release_predictor':{'readiness_pct':readiness,'ready':ready,'recommendation':'READY' if ready else 'HOLD','regression_risk':regression,'expected_build_seconds':predicted_build,'expected_deployment_seconds':deploy,'actions_success_rate_pct':success_rate,'blockers':[x.get('title') for x in blockers]},'guardrails':{'no_trading_changes':True,'no_secret_changes':True,'no_force_push':True,'no_unreviewed_source_rewrites':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');READY.write_text(json.dumps({'schema_version':'2.0','application_version':application_version(),'generated_at':now,**payload['release_predictor'],'scores':scores},indent=2),encoding='utf-8');print(f'Engineering health written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
