from __future__ import annotations
import json, os
from pathlib import Path
from scripts.release_identity import version as application_version
ROOT=Path(os.environ.get("CRM_PROJECT_PATH",Path(__file__).resolve().parents[1])); DOCS=ROOT/'docs'
def main():
 p=DOCS/'runtime_reliability.json'
 if not p.exists():return 0
 d=json.loads(p.read_text(encoding='utf-8')); live=d['authoritative_live_data']; age=live.get('age_minutes')
 if age is None: age_text='No fresh heartbeat available'
 elif age<1: age_text='Just now'
 elif age<60: age_text=f'{int(round(age))}m ago'
 else: age_text=f'{int(age//60)}h {int(age%60)}m ago'
 card={"schema_version":"1.0","application_version":application_version(),"title":"KuCoin live data service","status":live['state'],"last_update":age_text,"detail":live['message'],"fallback":live['fallback'],"action_required":live['state'] in ('ACTION_REQUIRED','OFFLINE'),"recovery_escalated":d['recovery_policy']['escalated']}
 (DOCS/'runtime_reliability_card.json').write_text(json.dumps(card,indent=2),encoding='utf-8'); print(json.dumps(card)); return 0
if __name__=='__main__':raise SystemExit(main())
