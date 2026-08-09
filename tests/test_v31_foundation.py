from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def test_version(): assert (ROOT/'VERSION').read_text(encoding="utf-8").strip()=='52.0.0'
def test_v31_assets():
 assert (ROOT/'docs/v31.css').exists() and (ROOT/'docs/v31.js').exists()
def test_html_v31_bundle():
 for p in (ROOT/'docs').glob('*.html'):
  t=p.read_text(encoding='utf-8'); assert 'v31.css' in t and 'v31.js' in t
def test_symbol_alias():
 from scripts.core.symbols import canonical_asset
 assert canonical_asset('XBTUSDT')=='BTC'
def test_reasoning():
 from scripts.core.recommendation_reasoning import build_dca_reasoning
 r=build_dca_reasoning({'take_profit_pct':1,'so_deviation_pct':1,'safety_orders':5},{'average_hours':24,'longest_hours':48,'max_capital':1000,'max_drawdown_dollars':-100},{'mark_to_market_pnl':10,'closed_deals':5})
 assert r['confidence']>0 and len(r['reasons'])==5
