from pathlib import Path
import json
from scripts.core.research_analytics import write_research_analytics

def test_v311_workflows_and_analytics(tmp_path: Path):
    docs=tmp_path/'docs'; docs.mkdir()
    (docs/'walk_forward_registry.json').write_text(json.dumps({'coins':[{'symbol':'BTC','status':'PASS','next_stage':'FORWARD VALIDATION','frozen_settings':{'take_profit_pct':1,'so_deviation_pct':1},'training_metrics':{'net_pnl':100,'closed_deals':10,'average_hours':12},'q1_2026_metrics':{'mark_to_market_pnl':20,'closed_deals':5,'max_drawdown_dollars':-10,'max_capital':100}}]}))
    (docs/'coin_discovery.json').write_text(json.dumps({'researched_candidates':[{'base_currency':'BTC','trend_30d_pct':20,'annualised_realised_vol_pct':30}]}))
    result=write_research_analytics(tmp_path)
    assert result['version']=='31.1.0'
    assert result['coins'][0]['regime']['label']=='TRENDING'
    assert (docs/'research_report.json').exists()
