#!/usr/bin/env python3
"""V70 Portfolio Truth & Decision Consistency Guard.

Builds a single advisory truth layer from current runtime files so:
- cash cannot be mislabeled as total portfolio value;
- deployable capital and deployment blockers cannot contradict each other;
- the next-capital candidate is expressed as an automation preview;
- paper evidence maturity is explicit;
- stale website publication is not treated as a live-trading blocker when the
  resident runtime and KuCoin live truth are current.

This module is READ ONLY with respect to exchange/provider execution.
"""
from __future__ import annotations
import json,math,os,time
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
from scripts.runtime_state_manager import state_dir

ROOT=Path(__file__).resolve().parents[1]
STATE=state_dir()
OUT=STATE/"portfolio_decision_consistency.json"
DOC_OUT=ROOT/"docs"/"portfolio_decision_consistency.json"

def now():return datetime.now(timezone.utc).isoformat()

def load(name):
    for p in (STATE/name, ROOT/"docs"/name):
        try:
            d=json.loads(p.read_text(encoding="utf-8-sig"))
            if isinstance(d,dict):return d
        except Exception:pass
    return {}

def q(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except:return None

def first_number(obj,keys):
    if not isinstance(obj,dict):return None
    for key in keys:
        if key in obj:
            v=q(obj.get(key))
            if v is not None:return v
    for child in obj.values():
        if isinstance(child,dict):
            v=first_number(child,keys)
            if v is not None:return v
    return None

def asset(v):
    return str(v or "").upper().replace("/USDT","").replace("-USDT","").replace("USDT","").strip()

def ts(v):
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).timestamp()
    except:return None

def age_seconds(d):
    t=ts(d.get("heartbeat_at") or d.get("generated_at") or d.get("updated_at"))
    return None if t is None else max(0,time.time()-t)

def rows_from(d):
    for k in ("bots","positions","rows","items","strategies"):
        v=d.get(k)
        if isinstance(v,list):return v
    return []

def position_value(row):
    return first_number(row,[
        "position_value_quote","position_value_usdt","position_value",
        "current_value_quote","current_value_usdt","market_value_quote",
        "market_value_usdt","market_value","position_size_quote","capital_in_deal",
        "quote_value","value_quote"
    ])

def live_rows(managed,live_truth):
    rows=[]
    for r in rows_from(managed):
        if str(r.get("state") or r.get("status") or "").upper()=="LIVE":
            rows.append(r)
    if rows:return rows
    for r in rows_from(live_truth):
        if (q(r.get("quantity")) or q(r.get("base_quantity")) or 0)>0:
            rows.append(r)
    return rows

def paper_rows(paper,managed):
    p={asset(x.get("asset") or x.get("symbol")):x for x in rows_from(paper)}
    rows=[]
    for r in rows_from(managed):
        a=asset(r.get("asset") or r.get("symbol"))
        if str(r.get("state") or "").upper()=="PAPER" or a in p:
            x=dict(p.get(a) or {})
            x.update({k:v for k,v in r.items() if k not in x or x.get(k) is None})
            x["_asset"]=a;rows.append(x)
    if rows:return rows
    for a,x in p.items():
        y=dict(x);y["_asset"]=a;rows.append(y)
    return rows

def evidence(row):
    closed=int(q(row.get("closed_deals")) or q(row.get("deals_completed")) or 0)
    open_deal=bool(row.get("position")) or bool(row.get("open_position")) or bool(q(row.get("open_pnl_quote")))
    opened=(row.get("position") or {}).get("opened_at") if isinstance(row.get("position"),dict) else None
    opened=opened or row.get("opened_at") or row.get("first_seen_at") or row.get("created_at")
    t=ts(opened)
    hours=(max(0,time.time()-t)/3600) if t else None
    if closed==0:stage="STARTING"
    elif closed<5:stage="EARLY_FORWARD_TEST"
    elif closed<20:stage="BUILDING_EVIDENCE"
    else:stage="MEANINGFUL_FORWARD_EVIDENCE"
    if hours is None:duration="Forward test active"
    elif hours<48:duration=f"{hours:.1f}h forward test"
    else:duration=f"{hours/24:.1f}d forward test"
    return {
        "stage":stage,"closed_deals":closed,"open_deal":open_deal,
        "duration_hours":round(hours,2) if hours is not None else None,
        "summary":f"{duration} · {1 if open_deal else 0} open deal · {closed} closed deal(s)"
    }

def publication_health(resident,live_service):
    pub=load("publication_status.json")
    if not pub:pub=load("local_agent_status.json")
    age=age_seconds(pub)
    resident_age=age_seconds(resident);live_age=age_seconds(live_service)
    runtime_live=(resident.get("status") in ("LIVE","RECOVERING") and
                  resident_age is not None and resident_age<20 and
                  live_age is not None and live_age<90)
    delayed=age is not None and age>1800
    return {
        "age_seconds":round(age,1) if age is not None else None,
        "delayed":delayed,
        "trading_blocker":bool(delayed and not runtime_live),
        "status":"WEBSITE_SNAPSHOT_DELAYED" if delayed else "CURRENT",
        "plain_english":("Website snapshot is delayed, but local live trading truth is current."
                         if delayed and runtime_live else
                         "Publication is current." if not delayed else
                         "Publication and local runtime freshness both need attention.")
    }

def main():
    account=load("kucoin_account.json")
    capital=load("capital_intelligence.json")
    live_truth=load("live_portfolio_truth.json")
    managed=load("managed_bot_portfolio.json")
    paper=load("paper_portfolio.json")
    lifecycle=load("deployment_lifecycle.json")
    resident=load("crm_resident_status.json")
    live_service=load("kucoin_live_service_status.json")

    cash=first_number(capital,["free_usdt","kucoin_cash","cash_quote","cash_usdt","available_usdt","available_cash"])
    if cash is None:
        cash=first_number(account,["free_usdt","available_usdt","cash_usdt","available_quote"])
    reported=first_number(capital,["portfolio_value","portfolio_value_usdt","total_equity","exchange_equity","equity_quote"])
    if reported is None:
        reported=first_number(account,["portfolio_value","portfolio_value_usdt","total_equity","equity_usdt"])

    lives=live_rows(managed,live_truth)
    live_value=sum(v for v in (position_value(r) for r in lives) if v is not None)
    # If reported portfolio is only cash, cash+live_value wins. If exchange equity
    # already includes positions, reported remains authoritative when larger.
    reconstructed=(cash or 0)+live_value if cash is not None else None
    portfolio=max(x for x in (reported,reconstructed) if x is not None) if any(x is not None for x in (reported,reconstructed)) else None

    reserve=first_number(capital,["reserved_for_active_dca","dca_reserve","active_dca_reserve","remaining_dca_requirement"])
    if reserve is None:reserve=0.0
    # When all configured safety orders are filled, remaining DCA reserve is zero.
    all_full=True if lives else False
    for r in lives:
        filled=q(r.get("safety_orders_filled") or r.get("so_filled") or r.get("completed_safety_orders"))
        maximum=q(r.get("max_safety_orders") or r.get("safety_orders") or r.get("max_so"))
        if filled is None or maximum is None or filled<maximum:all_full=False
    if all_full:reserve=0.0

    deployable=first_number(capital,["deployable_capital","safe_allocation_now","safe_to_allocate","available_for_new_bot"])
    if deployable is None and cash is not None:deployable=max(0,cash-reserve)
    if cash is not None and deployable is not None:deployable=max(0,min(deployable,cash-reserve))

    papers=paper_rows(paper,managed)
    lifecycle_by={asset(x.get("asset") or x.get("symbol")):x for x in rows_from(lifecycle)}
    def rank(r):
        return q(r.get("portfolio_rank")) or q(r.get("rank")) or 999999
    papers.sort(key=rank)
    next_bot=papers[0] if papers else None
    next_asset=next_bot.get("_asset") if next_bot else None
    lc=lifecycle_by.get(next_asset,{}) if next_asset else {}
    required=first_number(next_bot or {},["capital_required","required_capital","max_funds","capital"])
    if required is None:required=first_number(lc,["capital_required","required_capital","max_funds"])
    ev=evidence(next_bot or {}) if next_bot else None
    capital_gate=(required is not None and deployable is not None and deployable>=required)
    live_open=bool(lives)

    if next_asset:
        if live_open:
            automation_state="QUEUED_AFTER_LIVE_DEAL"
            action=f"If the current live deal closed now, {next_asset}/USDT is ranked #1 for the next capital decision."
        elif not capital_gate:
            automation_state="WAITING_FOR_CAPITAL"
            action=f"{next_asset}/USDT is ranked #1, but safe capital is not yet sufficient."
        elif ev and ev["closed_deals"]==0:
            automation_state="SHADOW_READY_EVIDENCE_BUILDING"
            action=f"{next_asset}/USDT is ranked #1 and capital is sufficient, but forward paper evidence is still starting."
        else:
            automation_state="READY_FOR_FINAL_REVALIDATION"
            action=f"{next_asset}/USDT is ranked #1 and should receive the next final deployment revalidation."
    else:
        automation_state="NO_CANDIDATE";action="No managed paper strategy is currently ranked for next capital."

    # Contradiction gate: capital cannot be called a blocker if it is demonstrably sufficient.
    stale_capital_blocker=False
    blockers=lc.get("blockers") or []
    if capital_gate:
        stale_capital_blocker=any("capital" in str(x).lower() for x in blockers)

    live_age=age_seconds(live_service)
    truth_current=live_age is not None and live_age<90
    consistency_ok=(portfolio is not None and cash is not None and
                    (reported is None or portfolio+1e-9>=reported) and
                    not stale_capital_blocker)

    result={
        "schema_version":"1.0","application_version":application_version(),
        "generated_at":now(),"read_only":True,
        "portfolio":{
            "reported_value_quote":reported,
            "reconstructed_value_quote":reconstructed,
            "authoritative_value_quote":round(portfolio,4) if portfolio is not None else None,
            "cash_quote":round(cash,4) if cash is not None else None,
            "live_position_value_quote":round(live_value,4),
            "dca_reserve_quote":round(reserve,4),
            "deployable_quote":round(deployable,4) if deployable is not None else None,
            "live_positions":len(lives),
            "truth_current":truth_current,
            "note":"Portfolio includes recognised cash plus live-position market value; deployable capital is capped by free cash."
        },
        "next_capital":{
            "asset":next_asset,"capital_required_quote":required,
            "capital_gate_pass":capital_gate,"automation_state":automation_state,
            "plain_english":action,
            "paper_evidence":ev,
            "stale_capital_blocker_detected":stale_capital_blocker,
            "auto_execution_permitted":False
        },
        "publication":publication_health(resident,live_service),
        "consistency":{
            "status":"PASS" if consistency_ok else "ATTENTION",
            "portfolio_cash_mislabelling_corrected":bool(portfolio is not None and cash is not None and portfolio>cash+0.01),
            "deployment_blocker_consistent":not stale_capital_blocker,
            "live_truth_current":truth_current
        }
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    tmp=OUT.with_suffix(".tmp");tmp.write_text(json.dumps(result,indent=2),encoding="utf-8");os.replace(tmp,OUT)
    try:
        DOC_OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    except Exception:pass
    print(f"Portfolio decision consistency: {result['consistency']['status']}; portfolio={portfolio}; cash={cash}; live={live_value}; next={next_asset}; state={automation_state}")
    return 0

if __name__=="__main__":raise SystemExit(main())
