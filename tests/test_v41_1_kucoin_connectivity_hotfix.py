from scripts.integrations import kucoin_account as k

def test_private_headers_include_content_type():
    h=k.sign_headers('GET','/api/v1/accounts','','','key','secret','pass','3')
    assert h['Content-Type']=='application/json'
    assert h['KC-API-KEY-VERSION']=='3'

def test_fallback_versions():
    assert k.candidate_versions('3')==['3','2']
    assert k.candidate_versions('2')==['2','3']

def test_official_base_fallback_only():
    bases=k.candidate_bases('https://api.kucoin.eu')
    assert bases[0]=='https://api.kucoin.eu'
    assert set(bases)<={'https://api.kucoin.com','https://api.kucoin.eu'}

def test_safe_error_classification():
    category,code,msg=k.classify_error(401,{'code':'400004','msg':'Passphrase Error'},'')
    assert category=='INVALID_PASSPHRASE'
    assert code=='400004'

def test_read_only_allowlist():
    assert k.ALLOWED=={('GET','/api/v1/accounts')}
