import json
from pathlib import Path
from scripts.integrations import threecommas
from scripts.core.symbols import canonical_asset
ROOT=Path(__file__).parents[1]

def test_canonical_release_and_read_only_mode():
    rel=json.loads((ROOT/'app/release.json').read_text(encoding="utf-8"))
    assert rel['version']=='33.0.2'
    assert rel['threecommas_mode']=='read_only'
    assert rel['deployment_recommendations_enabled'] is True

def test_threecommas_endpoint_allowlist_and_no_mutation_api():
    assert all('/public/api/ver1/' in p for p in threecommas.ALLOWED_PATHS)
    source=(ROOT/'scripts/integrations/threecommas.py').read_text(encoding="utf-8")
    assert 'signed_post' not in source and 'signed_delete' not in source

def test_xbt_is_btc():
    assert canonical_asset('XBT')=='BTC'

def test_v32_outputs_exist_and_are_read_only():
    integrity=json.loads((ROOT/'docs/system_integrity.json').read_text(encoding="utf-8"))
    reconciliation=json.loads((ROOT/'docs/configuration_reconciliation.json').read_text(encoding="utf-8"))
    assert integrity['checks']['read_only_3commas'] is True
    assert reconciliation['read_only'] is True
