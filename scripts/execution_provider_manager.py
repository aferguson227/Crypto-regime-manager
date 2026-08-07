#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1]; DOCS=ROOT/'docs'; OUT=DOCS/'execution_provider_status.json'
def load(name):
    try:return json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
    except Exception:return {}
def main():
    k=load('kucoin_account.json'); t=load('threecommas.json')
    payload={
      'application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
      'providers':{
        'kucoin_direct_read_only':{'state':str(k.get('status') or 'not_configured').upper(),'role':'capital source','write_enabled':False},
        'threecommas_read_only':{'state':str(t.get('status') or 'UNKNOWN').upper(),'role':'bot/deal state','write_enabled':False},
        'hummingbot':{'state':'PLANNED_PAPER_FIRST','role':'future execution','write_enabled':False},
        'kucoin_direct_execution':{'state':'DISABLED','role':'future execution','write_enabled':False},
      },
      'live_write_enabled':False,'manual_approval_required':True
    }
    OUT.write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(f'Execution provider status written: {OUT}')
    return 0
if __name__=='__main__': raise SystemExit(main())
