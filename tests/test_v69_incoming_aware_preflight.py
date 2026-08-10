from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_incoming_equivalence_helper_exists():
 s=(ROOT/'scripts/installer_preflight.py').read_text(encoding='utf-8')
 assert 'def incoming_equivalent_change' in s
 assert "replace('\\r\\n','\\n')" in s
def test_live_service_runtime_prepare_is_in_v69_source():
 s=(ROOT/'RUN_KUCOIN_LIVE_SERVICE.ps1').read_text(encoding='utf-8')
 assert 'scripts.runtime_state_manager prepare' in s
 assert '$RuntimeApp' in s
