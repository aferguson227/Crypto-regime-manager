import unittest
from scripts.core.engine import build_operational_intelligence

class V16OperationalIntelligenceTests(unittest.TestCase):
    def test_research_never_becomes_live_entry(self):
        outputs=[{
            'id':'SUI','symbol':'SUI-USDT','production_status':'research','history_end':'2026-08-03T04:00:00Z',
            'latest':{'regime':'Medium','entry_allowed':True,'recommended_bot':'SUI Research Bot'},
            'health':{'score':90,'status':'Excellent'},'intelligence':{'opportunity_score':95},'sync':{'new_candles':1,'error':None}
        }]
        result=build_operational_intelligence({},outputs,{'candidates':[]},{'decisions':[]})
        row=result['assets'][0]
        self.assertFalse(row['entry_allowed'])
        self.assertEqual(row['production_status'],'RESEARCH')
        self.assertFalse(result['guardrails']['live_execution_authorised'])

    def test_sync_error_vetoes_review_ready(self):
        outputs=[{
            'id':'TEL','symbol':'TEL-USDT','production_status':'production','history_end':'2026-08-03T04:00:00Z',
            'latest':{'regime':'Low','entry_allowed':True,'recommended_bot':'TEL Bot'},
            'health':{'score':90,'status':'Excellent'},'intelligence':{'opportunity_score':90},
            'sync':{'new_candles':0,'error':'network failure'}
        }]
        result=build_operational_intelligence({},outputs,None,None)
        self.assertEqual(result['assets'][0]['readiness'],'DATA BLOCKED')
        self.assertEqual(result['summary']['review_ready'],0)
        self.assertEqual(result['summary']['critical_alerts'],1)

    def test_healthy_production_setup_is_manual_review_only(self):
        outputs=[{
            'id':'TEL','symbol':'TEL-USDT','production_status':'production','history_end':'2026-08-03T04:00:00Z',
            'latest':{'regime':'Low','entry_allowed':True,'recommended_bot':'TEL Bot'},
            'health':{'score':90,'status':'Excellent'},'intelligence':{'opportunity_score':82},
            'sync':{'new_candles':1,'error':None}
        }]
        result=build_operational_intelligence({},outputs,None,None)
        self.assertEqual(result['assets'][0]['readiness'],'REVIEW SETUP')
        self.assertEqual(result['summary']['review_ready'],1)
        self.assertFalse(result['guardrails']['automatic_bot_changes'])

if __name__=='__main__': unittest.main()
