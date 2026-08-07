import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_v25_cloud_foundation():
    cfg=json.loads((ROOT/'config.json').read_text(encoding="utf-8"))
    assert cfg['version']=='41.1.0'
    assert cfg['historical_data_manager']['automatic_refresh'] is True
    assert cfg['historical_data_manager']['laptop_required'] is False
    assert cfg['autonomous_infrastructure']['scheduler']=='GitHub Actions'
    assert cfg['autonomous_infrastructure']['automatic_3commas_changes'] is False
    assert (ROOT/'scripts/cloud_update.py').exists()
    assert (ROOT/'docs/cloud_status.json').exists()
    assert (ROOT/'docs/cloud.html').exists()
    workflow=(ROOT/'.github/workflows/crm-data-refresh.yml').read_text(encoding="utf-8")
    assert 'schedule:' in workflow and 'scripts/cloud_update.py' in workflow
