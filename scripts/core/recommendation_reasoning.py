from __future__ import annotations
from typing import Any
def build_dca_reasoning(settings:dict[str,Any],training:dict[str,Any],validation:dict[str,Any])->dict[str,Any]:
    tp=float(settings.get("take_profit_pct",0)); dev=float(settings.get("so_deviation_pct",0)); sos=int(settings.get("safety_orders",0));
    avg=float(training.get("average_hours",0))/24; longest=float(training.get("longest_hours",0))/24; capital=float(training.get("max_capital",0)); dd=abs(float(training.get("max_drawdown_dollars",0)));
    dd_pct=(dd/capital*100) if capital else 0; q1=float(validation.get("mark_to_market_pnl",0)); closed=int(validation.get("closed_deals",0));
    reasons=[f"Take profit {tp:.2f}% is the best fee-aware training candidate.",f"Safety-order spacing starts at {dev:.2f}% across {sos} orders.",f"Training average holding time was {avg:.1f} days; longest was {longest:.1f} days.",f"Training drawdown used {dd_pct:.1f}% of peak model capital.",f"Frozen Q1 validation produced {closed} closed deals and ${q1:,.2f} mark-to-market P&L."]
    confidence=max(0,min(100,40+min(closed,20)*2+(15 if q1>0 else -20)-(10 if dd_pct>30 else 0)))
    return {"confidence":confidence,"summary":"Frozen settings selected on pre-2026 data and checked once on Q1 2026.","reasons":reasons}
