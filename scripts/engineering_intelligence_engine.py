#!/usr/bin/env python3
"""CRM V38 engineering health, backlog prioritisation and release advisor."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'engineering_health.json'; READY=DOCS/'release_readiness.json'
def load(n,d={}):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except Exception:return d
def clamp(v):return max(0,min(100,round(float(v),1)))
def main():
 now=datetime.now(timezone.utc).isoformat(); op=load('operational_health.json'); ui=load('ui_health.json'); heal=load('self_healing_status.json'); gh=load('github_actions_health.json'); dq=load('decision_quality.json'); diag=load('diagnostics_runtime.json') or load('diagnostics.json')
 scores={'application':clamp(((diag.get('overall') or {}).get('score')) or 0),'operations':clamp((op.get('overall') or {}).get('score_pct') or 0),'interface':clamp((ui.get('overall') or {}).get('score_pct') or (100 if (ui.get('overall') or {}).get('state')=='HEALTHY' else 70)),'actions':100 if gh.get('state')=='HEALTHY' else (70 if gh.get('state')=='WARNING' else 35),'decision_quality':clamp((dq.get('scores') or {}).get('evidence_coverage_pct') or 0),'self_healing':100 if heal.get('state') in {'HEALTHY','REPAIRED'} else 70}
 backlog=[]
 for src,items in [('operations',op.get('issues') or []),('actions',gh.get('issues') or []),('self_healing',heal.get('issues') or [])]:
  for x in items:
   sev=str(x.get('severity') or x.get('risk') or 'warning').lower(); benefit=5 if sev in {'critical','high'} else 4; effort=1 if x.get('automatic') else 2; confidence=5 if x.get('fingerprint') else 3; priority=round((benefit*confidence)/effort,1)
   backlog.append({'source':src,'fingerprint':x.get('fingerprint'),'title':x.get('title') or x.get('detail'),'severity':sev,'priority_score':priority,'expected_user_benefit':benefit,'estimated_effort':effort,'confidence':confidence,'automatic':bool(x.get('automatic'))})
 backlog=sorted(backlog,key=lambda x:x['priority_score'],reverse=True)
 overall=clamp(sum(scores.values())/len(scores)); blockers=[x for x in backlog if x['severity'] in {'critical','high'}]; readiness=clamp(overall-(15*len(blockers))); ready=readiness>=85 and not blockers
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'overall':{'state':'HEALTHY' if overall>=90 else ('WARNING' if overall>=70 else 'DEGRADED'),'score_pct':overall},'scores':scores,'backlog':backlog[:25],'highest_value_improvements':backlog[:5],'technical_debt':{'state':'LOW' if len(backlog)<4 else ('MODERATE' if len(backlog)<10 else 'HIGH'),'known_items':len(backlog)},'release_advisor':{'readiness_pct':readiness,'ready':ready,'recommendation':'READY' if ready else 'HOLD','blockers':[x['title'] for x in blockers]},'guardrails':{'no_trading_changes':True,'no_secret_changes':True,'no_force_push':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); READY.write_text(json.dumps({'schema_version':'1.0','application_version':application_version(),'generated_at':now,**payload['release_advisor'],'scores':scores},indent=2),encoding='utf-8'); print(f'Engineering health written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
