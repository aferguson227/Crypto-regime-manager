#!/usr/bin/env python3
"""Consolidate engineering findings into a persistent issue lifecycle."""
from __future__ import annotations
import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';OUT=DOCS/'issue_lifecycle.json'
def load(n,d):
 try:return json.loads((DOCS/n).read_text(encoding='utf-8-sig'))
 except Exception:return d
def main():
 now=datetime.now(timezone.utc).isoformat(); previous=load('issue_lifecycle.json',{'issues':[]}); old={x['key']:x for x in previous.get('issues',[]) if x.get('key')}
 rows=[]
 for source,name in [('operational','operational_health.json'),('actions','github_actions_health.json'),('self_healing','self_healing_status.json'),('ui','ui_health.json'),('repository','repository_health.json')]:
  d=load(name,{})
  candidates=(d.get('issues') or [])
  if source=='ui': candidates+=d.get('findings') or []
  for x in candidates:
   fp=str(x.get('fingerprint') or x.get('code') or x.get('title') or 'UNKNOWN')
   title=str(x.get('title') or x.get('detail') or fp)
   key=hashlib.sha1((source+'|'+fp+'|'+title).encode()).hexdigest()[:16]
   rows.append((key,source,fp,title,x))
 grouped={}
 for key,source,fp,title,x in rows:
  g=grouped.setdefault(key,{'key':key,'source':source,'fingerprint':fp,'title':title,'severity':str(x.get('severity') or x.get('risk') or 'warning').lower(),'occurrences':0,'automatic':bool(x.get('automatic')),'recommended_action':x.get('safe_action') or x.get('action') or x.get('repair')})
  g['occurrences']+=1
 issues=[]
 for key,g in grouped.items():
  prior=old.get(key,{})
  g['first_detected_at']=prior.get('first_detected_at',now);g['last_detected_at']=now;g['lifecycle']='DETECTED' if not prior else 'OPEN';g['historical_occurrences']=int(prior.get('historical_occurrences',0))+g['occurrences'];issues.append(g)
 closed=[]
 for key,p in old.items():
  if key not in grouped:
   q=dict(p);q['lifecycle']='CLOSED';q['closed_at']=now;closed.append(q)
 issues.sort(key=lambda x:({'critical':0,'high':1,'warning':2,'medium':2,'info':3}.get(x['severity'],4),-x['historical_occurrences']))
 payload={'schema_version':'1.0','application_version':application_version(),'generated_at':now,'summary':{'open':len(issues),'closed_this_scan':len(closed),'automatic_available':sum(1 for x in issues if x['automatic'])},'issues':issues,'recently_closed':closed[:25]}
 OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');print(f'Issue lifecycle written: {OUT}');return 0
if __name__=='__main__':raise SystemExit(main())
