import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_release_identity():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='38.0.0'
 release=json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))
 assert release['release_name']=='Autonomous Engineering Platform'
def test_shared_design_and_navigation():
 for p in (ROOT/'docs').glob('*.html'):
  text=p.read_text(encoding='utf-8')
  assert 'design-system.css' in text, p.name
  assert 'design-system.js' in text, p.name
def test_dashboard_is_visual_and_decision_first():
 html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
 for phrase in ['Today’s Trading Briefing','Decision readiness','Which bot?','How much?','Which settings?','What changed?']:
  assert phrase in html
 assert 'visual-meter' in html
def test_formatting_semantics_are_explicit():
 engine=(ROOT/'scripts/professional_workspace_engine.py').read_text(encoding='utf-8')
 for phrase in ['currency_policy','unknown_policy','negative_sign','display_rule']:
  assert phrase in engine
 js=(ROOT/'docs/design-system.js').read_text(encoding='utf-8')
 for phrase in ['en-GB','Europe/London','quote(v','asset(v']:
  assert phrase in js
def test_ui_validator_exists():
 assert (ROOT/'scripts/ui_consistency.py').exists()
