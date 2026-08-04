#!/usr/bin/env python3
from pathlib import Path
from core.data_import import run_import_queue
import json
if __name__=='__main__': print(json.dumps(run_import_queue(Path(__file__).resolve().parents[1]),indent=2))
