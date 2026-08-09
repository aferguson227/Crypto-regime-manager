import json
from pathlib import Path
from scripts.capital_intelligence_engine import build
from scripts.integrations.threecommas import ALLOWED_PATHS, sanitise_account
ROOT=Path(__file__).parents[1]

def test_v323_release_and_capital_route():
    assert (ROOT/'VERSION').read_text(encoding='utf-8').strip()=='56.0.0'
    routes=json.loads((ROOT/'config/routes.json').read_text(encoding='utf-8'))['routes']
    assert any(r['path']=='capital.html' and r['primary'] for r in routes)
    assert (ROOT/'docs/capital.js').exists()

def test_capital_engine_is_read_only_and_does_not_invent_free_cash():
    state=build()
    assert state['application_version']=='56.0.0'
    assert state['read_only'] is True
    assert state['capital_status'] in {'COMPLETE','PARTIAL','UNAVAILABLE'}
    if state['free_available'] is None:
        assert state['deployable_capital'] is None
        assert state['warnings']

def test_accounts_endpoint_is_read_only_allowlisted():
    assert '/public/api/ver1/accounts' in ALLOWED_PATHS
    assert all('update' not in p and 'enable' not in p and 'disable' not in p for p in ALLOWED_PATHS)
    row=sanitise_account({'id':7,'name':'KuCoin','exchange_name':'KuCoin','total_usd_value':'1000','available_usdt':'250'})
    assert row['account_id']==7 and row['total_usd_value']==1000.0 and row['free_usdt']==250.0

def test_capital_methodology_avoids_double_subtracting_open_orders():
    state=build()
    text=state['methodology']['placed_order_reserve'].lower()
    assert 'not subtracted' in text
