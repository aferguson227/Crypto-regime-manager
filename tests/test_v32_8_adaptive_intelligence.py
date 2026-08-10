import json
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_v328_release_and_output():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='59.0.0'
 rel=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert rel['release_name']=='KuCoin Historical Research & Universal Responsive UI'
 assert (ROOT/'docs/adaptive_intelligence.json').exists()
 assert (ROOT/'docs/adaptive.html').exists()

def test_v328_adaptive_safeguards():
 p=json.loads((ROOT/'docs/adaptive_intelligence.json').read_text(encoding='utf-8'))
 assert p['read_only'] is True
 assert p['manual_approval_required'] is True
 assert p['minimum_evidence_required']>=8
 assert p['adaptive_influence_cap_pct']<=25
 for s in p['strategies']:
  if s['evidence_count']<p['minimum_evidence_required']:
   assert s['adaptation_status']=='INSUFFICIENT_EVIDENCE'
   assert s['effective_score']==s['static_score']

def test_v328_routes_and_cloud_pipeline():
 routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
 assert any(r['path']=='adaptive.html' for r in routes)
 cloud=(ROOT/'scripts/cloud_update.py').read_text(encoding='utf-8')
 assert 'adaptive_intelligence_engine' in cloud

def test_v328_build_restores_generated_diagnostics():
 text=(ROOT/'build.ps1').read_text(encoding='utf-8')
 assert 'scripts.generated_output_manager' in text
 assert 'diagnostics_runtime.json' in (ROOT/'.gitignore').read_text(encoding='utf-8')
 assert 'Build System 2.1' in text
