#!/usr/bin/env python3
from __future__ import annotations
import json,re
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'ui_health.json'; ISSUES=DOCS/'visual_issues.json'; POLICY=ROOT/'config/page_policy.json'
VISIBLE_VERSION=re.compile(r'>\s*V(\d+\.\d+\.\d+)(?=\s|<|·)');LEGACY_NAV=('workspace-nav','v20-nav','v20-tools')
def main():
 policy=json.loads(POLICY.read_text(encoding='utf-8-sig')); canonical={x['path'] for x in policy.get('canonical_pages',[])}; drill=set(policy.get('drilldown_pages',[])); legacy=set(policy.get('legacy_pages',[])); pages=[];problems=[];current=application_version()
 for p in sorted(DOCS.glob('*.html')):
  s=p.read_text(encoding='utf-8-sig');visible=VISIBLE_VERSION.findall(s);stale=sorted({v for v in visible if v!=current});legacy_nav=[c for c in LEGACY_NAV if c in s];raw_nav_count=len(re.findall(r'<nav\b',s,re.I));role='canonical' if p.name in canonical else 'drilldown' if p.name in drill else 'legacy' if p.name in legacy else 'unclassified';row={'page':p.name,'role':role,'design_css':'design-system.css' in s,'design_js':'design-system.js' in s,'viewport':'name="viewport"' in s,'home_path':('index.html' in s or p.name=='index.html' or 'design-system.js' in s),'mojibake':bool(re.search(r'â€”|â€“|Â£|ï¿½',s)),'stale_visible_versions':stale,'legacy_nav_classes':legacy_nav,'raw_nav_count':raw_nav_count};pages.append(row)
  for key,label in [('design_css','shared design stylesheet'),('design_js','shared navigation/formatting script'),('viewport','responsive viewport'),('home_path','Dashboard return path')]:
   if not row[key]:problems.append({'severity':'warning','page':p.name,'issue':f'Missing {label}','safe_auto_fix':key in {'design_css','design_js'}})
  if row['mojibake']:problems.append({'severity':'critical','page':p.name,'issue':'Known mojibake sequence detected','safe_auto_fix':False})
  if stale:problems.append({'severity':'critical' if role=='canonical' else 'warning','page':p.name,'issue':f'Visible stale version label(s): {", ".join(stale)}; expected {current}','safe_auto_fix':True})
  if legacy_nav and role in {'canonical','drilldown'}:problems.append({'severity':'warning','page':p.name,'issue':f'Legacy navigation markup remains: {", ".join(legacy_nav)}','safe_auto_fix':True})
  if raw_nav_count>1:problems.append({'severity':'warning','page':p.name,'issue':f'Multiple static navigation blocks detected ({raw_nav_count})','safe_auto_fix':True})
 score=round(100*(1-len(problems)/max(1,len(pages)*7)),1);state='HEALTHY' if not problems else ('DEGRADED' if any(x['severity']=='critical' for x in problems) else 'WARNING');payload={'schema_version':'2.0','application_version':current,'generated_at':datetime.now(timezone.utc).isoformat(),'overall':{'state':state,'score_pct':max(0,score),'pages_checked':len(pages),'issue_count':len(problems),'canonical_pages':len(canonical),'legacy_pages':len(legacy)},'policy':{'font':'Inter/system UI stack','layout':'single canonical navigation + unified dashboard','locale':'en-GB','symbols':'explicit asset and quote codes','visible_version':current},'pages':pages,'issues':problems};OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8');ISSUES.write_text(json.dumps({'application_version':current,'generated_at':payload['generated_at'],'issues':problems},indent=2),encoding='utf-8');print(f'UI health: {state} - {max(0,score)}% ({len(pages)} pages, {len(problems)} issue(s))');return 0 if state!='DEGRADED' else 1
if __name__=='__main__':raise SystemExit(main())