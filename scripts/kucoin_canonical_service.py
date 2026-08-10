#!/usr/bin/env python3
"""V64 canonical KuCoin data/credential service status.

Read-only diagnostic contract. It does not expose secrets; it records whether the
same credential names and canonical data products are visible to this process.
"""
from __future__ import annotations
import json,os
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'kucoin_canonical_service.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def present(*names): return any(bool(os.getenv(n)) for n in names)
def main():
 account=load('kucoin_account.json');orders=load('kucoin_order_state.json');fills=load('kucoin_fill_ledger.json')
 creds={'api_key':present('KUCOIN_API_KEY','KUCOIN_KEY'),'api_secret':present('KUCOIN_API_SECRET','KUCOIN_SECRET'),'api_passphrase':present('KUCOIN_API_PASSPHRASE','KUCOIN_PASSPHRASE')}
 products={'account':str(account.get('status') or '').upper()=='OK','orders':str(orders.get('status') or '').upper() in {'OK','DEGRADED'},'fills':str(fills.get('status') or '').upper() in {'OK','DEGRADED'}}
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),
    'credential_contract':'canonical environment aliases; secrets never written','credential_visibility':creds,'data_products':products,
    'status':'READY' if all(products.values()) else 'DEGRADED',
    'principle':'KuCoin is authoritative. Local Agent, accounting, research diagnostics and future execution consume the same canonical data products instead of independently redefining account truth.',
    'read_only':True,'secrets_persisted':False}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print('Canonical KuCoin service:',p['status']);return 0
if __name__=='__main__':raise SystemExit(main())
