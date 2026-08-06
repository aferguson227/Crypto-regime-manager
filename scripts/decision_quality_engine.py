#!/usr/bin/env python3
"""Decision quality evidence and calibration summary for CRM V38."""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'decision_quality.json'
def load(n,d={}):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except Exception:return d
def main():
 now=datetime.now(timezone.utc).isoformat(); outcomes=load('outcome_intelligence.json'); hist=load('recommendation_history.json',{}); ws=load('professional_workspace.json'); points=hist.get('history') or hist.get('recommendations') or []
 completed=(outcomes.get('summary') or {}).get('completed') or outcomes.get('completed_count') or 0; accuracy=(outcomes.get('summary') or {}).get('accuracy_pct')
 readiness=(ws.get('decision_readiness') or {}).get('score_pct') or 0
 confidence=(ws.get('daily_decision') or {}).get('confidence_pct') or 0
 evidence_score=min(100,20+min(50,float(completed)*5)+min(30,len(points)*2))
 state='MEASURED' if completed and accuracy is not None else 'LIMITED_EVIDENCE'
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'state':state,'scores':{'evidence_coverage_pct':round(evidence_score,1),'decision_readiness_pct':readiness,'current_confidence_pct':confidence,'observed_accuracy_pct':accuracy},'sample':{'completed_outcomes':completed,'recommendation_history_points':len(points)},'guidance':['Do not increase autonomy until outcome evidence is sufficient.','Compare confidence with realised outcomes before changing recommendation logic.'],'guardrails':{'advisory_only':True,'manual_approval_required':True}}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(f'Decision quality written: {OUT}'); return 0
if __name__=='__main__':raise SystemExit(main())
