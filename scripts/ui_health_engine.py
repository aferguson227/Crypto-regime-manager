#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'ui_health.json'; ISSUES=DOCS/'visual_issues.json'
def main():
 pages=[]; problems=[]
 for p in sorted(DOCS.glob('*.html')):
  s=p.read_text(encoding='utf-8-sig'); row={'page':p.name,'design_css':'design-system.css' in s,'design_js':'design-system.js' in s,'viewport':'name="viewport"' in s,'home_path':('index.html' in s or p.name=='index.html' or 'design-system.js' in s),'mojibake':bool(re.search(r'â€”|â€“|Â£|ï¿½',s))}; pages.append(row)
  for key,label in [('design_css','shared design stylesheet'),('design_js','shared navigation/formatting script'),('viewport','responsive viewport'),('home_path','Dashboard return path')]:
   if not row[key]:problems.append({'severity':'warning','page':p.name,'issue':f'Missing {label}','safe_auto_fix':key in {'design_css','design_js'}})
  if row['mojibake']:problems.append({'severity':'critical','page':p.name,'issue':'Known mojibake sequence detected','safe_auto_fix':False})
 score=round(100*(1-len(problems)/max(1,len(pages)*5)),1); state='HEALTHY' if not problems else ('WARNING' if not any(x['severity']=='critical' for x in problems) else 'DEGRADED'); payload={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'overall':{'state':state,'score_pct':max(0,score),'pages_checked':len(pages),'issue_count':len(problems)},'policy':{'font':'Inter/system UI stack','layout':'shared responsive shell','locale':'en-GB','symbols':'explicit asset and quote codes'},'pages':pages,'issues':problems}; OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8'); ISSUES.write_text(json.dumps({'application_version':application_version(),'generated_at':payload['generated_at'],'issues':problems},indent=2),encoding='utf-8'); print(f'UI health: {state} - {max(0,score)}% ({len(pages)} pages)'); return 0 if state!='DEGRADED' else 1
if __name__=='__main__':raise SystemExit(main())
