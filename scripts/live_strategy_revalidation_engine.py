#!/usr/bin/env python3
"""V63 rolling live-bot strategy revalidation; advisory only."""
import json
from datetime import datetime,timezone
from pathlib import Path
from app.release import application_version
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs';OUT=D/'live_strategy_revalidation.json'
def load(n):
 try:return json.loads((D/n).read_text(encoding='utf-8-sig'))
 except:return {}
def main():
 live=load('live_portfolio_truth.json');opt=load('dca_optimisation_v2.json');wf=load('kucoin_walk_forward.json')
 oby={str(x.get('asset') or '').upper():x for x in opt.get('assets') or []};wby={str(x.get('asset') or '').upper():x for x in wf.get('assets') or []};rows=[]
 for d in live.get('deals') or []:
  if d.get('effective_position_state')!='OPEN':continue
  a=str(d.get('asset') or '').upper();o=oby.get(a) or {};w=wby.get(a) or {}
  rows.append({'asset':a,'bot_name':d.get('bot_name'),'deal_open':True,'current_regime':w.get('current_regime_family'),
   'latest_optimisation_status':o.get('optimisation_status'),'latest_validated_settings':o.get('winning_strategy_settings'),
   'latest_unseen_validation':o.get('unseen_validation_metrics'),
   'recommendation':'KEEP_CURRENT_DEAL_FROZEN' if d.get('effective_position_state')=='OPEN' else 'REVIEW_NEXT_SETTINGS',
   'next_deal_policy':'After this deal closes, compare production settings with the latest unseen-validated settings before the next deployment.',
   'automatic_mid_trade_setting_change':False})
 p={'schema_version':'1.0','application_version':application_version(),'generated_at':datetime.now(timezone.utc).isoformat(),'live_bots':rows,'principle':'Would CRM deploy this strategy today? Revalidate continuously, but never mutate an active deal mid-trade.','read_only':True}
 OUT.write_text(json.dumps(p,indent=2),encoding='utf-8');print(f'Live strategy revalidation: {len(rows)} open bot(s)');return 0
if __name__=='__main__':raise SystemExit(main())
