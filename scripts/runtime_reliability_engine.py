from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from scripts.release_identity import version as application_version
ROOT=Path(os.environ.get("CRM_PROJECT_PATH",Path(__file__).resolve().parents[1])); DOCS=ROOT/"docs"
FRESH_SECONDS=120; DEGRADED_SECONDS=600; RECOVERY_LIMIT=3

def _load(name):
 p=DOCS/name
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception:return {}
def _parse(ts):
 if not ts:return None
 try:return datetime.fromisoformat(str(ts).replace("Z","+00:00"))
 except Exception:return None
def age_seconds(ts,now=None):
 dt=_parse(ts)
 if not dt:return None
 now=now or datetime.now(timezone.utc)
 if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
 return max(0.0,(now-dt).total_seconds())
def classify(age):
 if age is None:return "OFFLINE"
 if age<=FRESH_SECONDS:return "HEALTHY"
 if age<=DEGRADED_SECONDS:return "DEGRADED"
 return "ACTION_REQUIRED"
def concise_fallback_message(base,fallback):
 base=(base or "").strip(); suffix="using published fallback"
 chunks=[c.strip() for c in base.replace(" · ","|").split("|") if c.strip()]
 out=[]; seen=False
 for c in chunks:
  if c.lower()==suffix:
   if seen:continue
   seen=True
  out.append(c)
 if fallback and not seen:out.append(suffix)
 return " · ".join(out)
def main():
 now=datetime.now(timezone.utc); live=_load("kucoin_live_service_status.json"); health=_load("crm_health_recovery.json"); paper=_load("paper_portfolio.json")
 hb=live.get("heartbeat_at") or live.get("generated_at"); age=age_seconds(hb,now); state=classify(age)
 unresolved=int(health.get("consecutive_unresolved_cycles") or health.get("recovery",{}).get("consecutive_unresolved_cycles") or 0)
 fallback=bool(live.get("using_last_good_snapshot") or live.get("using_published_fallback") or str(live.get("status","")).lower().startswith("fallback"))
 result={"schema_version":"1.0","application_version":application_version(),"generated_at":now.isoformat(),
 "authoritative_live_data":{"state":state,"heartbeat_at":hb,"age_seconds":age,"age_minutes":None if age is None else round(age/60,1),"fallback":fallback,"message":concise_fallback_message(live.get("message") or "KuCoin live-data service status unavailable.",fallback),"healthy":state=="HEALTHY","decision_critical_current":state=="HEALTHY"},
 "recovery_policy":{"attempt_limit":RECOVERY_LIMIT,"consecutive_unresolved_cycles":unresolved,"automatic_recovery_allowed":unresolved<RECOVERY_LIMIT,"escalated":unresolved>=RECOVERY_LIMIT,"rule":"After 3 unresolved cycles, stop repeating the same repair and surface one root cause."},
 "paper_runtime":{"state":"HEALTHY" if paper else "UNKNOWN","shared_runtime_contract":"Paper and live trading consume the same authoritative freshness state."}}
 (DOCS/'runtime_reliability.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(f"Runtime reliability: {state}; age={result['authoritative_live_data']['age_minutes']}m")
 return 0
if __name__=='__main__':raise SystemExit(main())
