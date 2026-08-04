from pathlib import Path
import json, tempfile
from scripts.core.decision_engine import write_decision_intelligence

def test_v28_unified_ranking_and_policy():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); (root/'docs').mkdir()
        strategies={'generated_at':'now','assets':[{'id':'tel','symbol':'TEL-USDT','production_status':'production','latest':{'entry_allowed':True,'recommended_bot':'TEL Bot','regime':'Low'},'health':{'score':70,'recent_realised_pnl':300,'recent_max_drawdown_pct_of_capital':-10,'recent_average_trade_hours':24},'intelligence':{'opportunity_score':70},'max_theoretical_capital':2000,'open_position':None}]}
        (root/'docs'/'strategies.json').write_text(json.dumps(strategies));(root/'docs'/'coin_discovery.json').write_text(json.dumps({'candidates':[1,2]}));(root/'docs'/'candidate_validation.json').write_text(json.dumps({'candidates':[]}))
        out=write_decision_intelligence(root)
        assert out['best_setup']['symbol']=='TEL-USDT'
        assert out['pipeline']['discovery_candidates']==2
        assert out['policy']['discovery_can_change_live_ranking'] is False
