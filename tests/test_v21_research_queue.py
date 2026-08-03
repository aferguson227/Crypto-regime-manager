from scripts.core.research_queue import build_research_queue

def test_queue_guardrails_and_multi_asset_ranking():
    cfg={"execution":{},"research_queue":{"enabled":True,"max_assets_per_cycle":2,"max_experiments_per_asset":1,"hypothesis_library":[{"id":"X","title":"Test","family":"Trend","field":"min_distance_from_ema200_pct","value":0,"human_rule":"test"}]}}
    outputs=[{"id":"A","health":{"score":20},"net_pnl":-10,"closed_deals":10,"longest_trade_hours":10,"maximum_drawdown_pct_of_capital":-2,"open_position":None},{"id":"B","health":{"score":90},"net_pnl":5,"closed_deals":10,"longest_trade_hours":10,"maximum_drawdown_pct_of_capital":-2,"open_position":None}]
    contexts={x["id"]:{"asset":{"id":x["id"],"entry_filter":{},"bots":{}},"candles":[],"signals":[]} for x in outputs}
    def sim(c,s,a,e): return {"net_pnl":1,"closed_deals":10,"longest_trade_hours":5,"maximum_drawdown_pct_of_capital":-1,"open_position":None}
    def compact(x): return {"net_pnl":x.get("net_pnl",0),"closed_deals":x.get("closed_deals",0),"effective_longest_trade_hours":x.get("longest_trade_hours",0),"maximum_drawdown_pct_of_capital":x.get("maximum_drawdown_pct_of_capital",0),"open_position":x.get("open_position")}
    q=build_research_queue(cfg,outputs,contexts,sim,compact)
    assert q["queue"][0]["asset_id"]=="A"
    assert q["guardrails"]["automatic_production_changes"] is False
