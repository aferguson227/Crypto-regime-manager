from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_release_identity():
 assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='54.0.0'
def test_account_balance_endpoint_is_explicitly_read_only():
 source=(ROOT/'scripts/integrations/threecommas.py').read_text(encoding='utf-8')
 assert 'account_table_data' in source and 'ACCOUNTS_READ' in source
 assert 'sell_all_to_usd' not in source and 'sell_all_to_btc' not in source
def test_account_intelligence_output_exists_and_is_advisory():
 data=json.loads((ROOT/'docs/account_intelligence.json').read_text(encoding='utf-8'))
 assert data['application_version']=='54.0.0' and data['read_only'] is True
 assert data['status'] in {'HEALTHY','PARTIAL','UNAVAILABLE'}
def test_threecommas_workflow_rebuilds_downstream_state():
 text=(ROOT/'.github/workflows/crm-data-refresh.yml').read_text(encoding='utf-8')
 for module in ('account_intelligence_engine','capital_intelligence_engine','command_state_engine'):
  assert module in text
