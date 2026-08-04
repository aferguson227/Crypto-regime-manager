#!/usr/bin/env python3
from pathlib import Path
from core.backtest_lab import run_lab
import json
if __name__=='__main__':print(json.dumps(run_lab(Path(__file__).resolve().parents[1]),indent=2))
