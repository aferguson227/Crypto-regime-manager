import json
from pathlib import Path
from scripts.core.engine import portfolio_intelligence
ROOT=Path(__file__).resolve().parents[1]

def _asset(symbol, allowed, score, health, pnl, dd, capital, open_hours=0):
    a={'id':symbol.lower(),'symbol':symbol,'production_status':'production','latest':{'entry_allowed':allowed,'regime':'Low','recommended_bot':symbol+' Bot'},'intelligence':{'opportunity_score':score,'action':'CAUTIOUS'},'health':{'score':health,'status':'Watch','recent_realised_pnl':pnl,'recent_max_drawdown_pct_of_capital':dd,'recent_average_duration_hours':24},'max_theoretical_capital':capital}
    if open_hours:a['open_position']={'hours_open':open_hours}
    return a

def test_v26_release_and_safeguards():
    cfg=json.loads((ROOT/'config.json').read_text(encoding="utf-8"))
    assert cfg['version']=='39.1.0'
    assert cfg['portfolio_intelligence_v26']['automatic_live_changes'] is False
    assert cfg['portfolio_intelligence_v26']['manual_approval_required'] is True
    assert (ROOT/'docs/v26.js').exists()
    cloud=(ROOT/'docs/cloud.html').read_text(encoding="utf-8")
    assert 'Displayed in your device timezone' in cloud
    assert 'Technical diagnostics' in cloud

def test_v26_risk_adjusted_ranking_penalises_blocked_and_long_open_positions():
    good=_asset('GOOD-USDT',True,70,80,500,-8,2000)
    open_asset=_asset('OPEN-USDT',True,80,80,500,-8,2000,240)
    blocked=_asset('BLOCK-USDT',False,95,95,900,-4,2000)
    out=portfolio_intelligence([good,open_asset,blocked])
    assert out['ranking'][0]['symbol']=='GOOD-USDT'
    assert next(x for x in out['ranking'] if x['symbol']=='BLOCK-USDT')['classification']=='rejected'
    assert out['manual_approval_required'] is True and out['automatic_live_changes'] is False
