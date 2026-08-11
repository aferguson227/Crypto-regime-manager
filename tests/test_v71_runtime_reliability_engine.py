from scripts.runtime_reliability_engine import classify,concise_fallback_message
def test_states():
 assert classify(None)=='OFFLINE'; assert classify(30)=='HEALTHY'; assert classify(300)=='DEGRADED'; assert classify(3600)=='ACTION_REQUIRED'
def test_stale_not_healthy(): assert classify(23*3600)!='HEALTHY'
def test_fallback_dedup():
 s='Resident local service · using published fallback · using published fallback · using published fallback'; o=concise_fallback_message(s,True); assert o.count('using published fallback')==1
def test_fallback_append_once(): assert concise_fallback_message('Resident local service',True).count('using published fallback')==1
