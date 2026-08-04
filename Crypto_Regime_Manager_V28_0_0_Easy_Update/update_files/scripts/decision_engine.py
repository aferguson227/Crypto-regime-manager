#!/usr/bin/env python3
from pathlib import Path
from core.decision_engine import write_decision_intelligence
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=write_decision_intelligence(ROOT)
    print(f"V28 decision intelligence updated: {p.get('best_setup',{}).get('symbol') if p.get('best_setup') else 'no eligible setup'}")
