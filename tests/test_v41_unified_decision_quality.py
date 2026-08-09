from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs'
def test_v41_release_identity():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='52.0.0'
 assert json.loads((ROOT/'app/release.json').read_text(encoding='utf-8'))['release_name']=='KuCoin Historical Research & Universal Responsive UI'
def test_dashboard_is_unified():
 h=(DOCS/'index.html').read_text(encoding='utf-8')
 for text in ('Recommended action','Capital & portfolio','System synchronisation','DCA settings','Active issues','Interface quality'): assert text in h
 assert 'unified_dashboard.js' in h
def test_single_navigation_owner():
 w=(DOCS/'workspace.js').read_text(encoding='utf-8');d=(DOCS/'design-system.js').read_text(encoding='utf-8')
 assert 'workspace-nav' not in w
 assert 'crm-global-nav' in d
 assert 'workspace-nav,.v20-nav,.v20-tools' in d
def test_canonical_visible_versions_are_current():
 p=json.loads((ROOT/'config/page_policy.json').read_text(encoding='utf-8'))
 for row in p['canonical_pages']:
  h=(DOCS/row['path']).read_text(encoding='utf-8')
  visible=re.findall(r'>\s*V(\d+\.\d+\.\d+)(?=\s|<|·)',h)
  assert all(v=='52.0.0' for v in visible),(row['path'],visible)
def test_portfolio_does_not_format_usdt_as_usd_symbol():
 s=(DOCS/'portfolio.js').read_text(encoding='utf-8')
 assert "style:'currency'" not in s
 assert 'CRMFormat.quote' in s
def test_cloud_reliability_uses_current_workflows():
 s=(ROOT/'scripts/cloud_reliability_engine.py').read_text(encoding='utf-8')
 assert 'crm-data-refresh.yml' in s and 'crm-health-self-heal.yml' in s
 assert 'threecommas-update.yml' not in s and 'multi-coin-update.yml' not in s
def test_actions_only_current_workflows_can_be_active():
 s=(ROOT/'scripts/github_actions_intelligence_engine.py').read_text(encoding='utf-8')
 assert 'canonical_names' in s and 'if name not in canonical_names: continue' in s

def test_threecommas_preserves_quota_for_balance_request():
 s=(ROOT/'scripts/integrations/threecommas.py').read_text(encoding='utf-8')
 assert 'not_requested_quota_guard' in s
 assert 'Optional account-detail request skipped to preserve quota' in s
