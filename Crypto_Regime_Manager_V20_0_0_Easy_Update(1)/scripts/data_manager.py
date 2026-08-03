#!/usr/bin/env python3
"""Safe KuCoin historical-data manager for V20.

This utility never changes strategies. It refreshes completed 4-hour candles,
keeps existing history, and optionally reruns the normal engine so every
research/health view is recalculated from the same source data.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.core.engine import load_history, save_history, fetch_kucoin

def config(): return json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
def assets(): return config()['assets']
def status():
    rows=[]
    for a in assets():
        path=ROOT/a['history_file']; candles=load_history(path)
        rows.append({'id':a['id'],'symbol':a['symbol'],'file':str(path.relative_to(ROOT)),'candles':len(candles),'first':datetime.fromtimestamp(candles[0].ts,tz=timezone.utc).isoformat() if candles else None,'last':datetime.fromtimestamp(candles[-1].ts,tz=timezone.utc).isoformat() if candles else None})
    print(json.dumps({'version':'20.0.0','source':'KuCoin','timeframe':'4hour','assets':rows},indent=2))
def refresh(ids,rerun=True):
    selected=[a for a in assets() if a['id'] in ids]
    if not selected: raise SystemExit('No matching assets.')
    for a in selected:
        path=ROOT/a['history_file']; old=load_history(path); since=old[-1].ts if old else None
        fresh=fetch_kucoin(a['symbol'],'4hour',since)
        merged=sorted({c.ts:c for c in old+fresh}.values(),key=lambda c:c.ts)
        save_history(path,merged)
        print(f"{a['id']}: {len(old)} -> {len(merged)} candles (+{len(merged)-len(old)})")
    if rerun:
        subprocess.run([sys.executable,str(ROOT/'scripts/multi_coin_sync_backtest.py'),'--skip-fetch'],cwd=ROOT,check=True)
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('status')
    r=sub.add_parser('refresh'); r.add_argument('--all',action='store_true'); r.add_argument('--asset',action='append',choices=[a['id'] for a in assets()]); r.add_argument('--no-rerun',action='store_true')
    ns=ap.parse_args()
    if ns.cmd=='status': status()
    else:
        ids=[a['id'] for a in assets()] if ns.all else (ns.asset or [])
        refresh(ids,not ns.no_rerun)
if __name__=='__main__': main()
