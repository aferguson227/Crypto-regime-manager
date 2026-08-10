from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def text(p):return (ROOT/p).read_text(encoding='utf-8')
def test_preflight_distinguishes_runtime_from_source():
 s=text('scripts/installer_preflight.py')
 assert 'runtime_changes' in s and 'source_changes' in s
 assert 'restore_runtime_only' in s
def test_preflight_pauses_all_background_writers():
 s=text('scripts/installer_preflight.py')
 assert 'CryptoRegimeManager-LocalAgent' in s
 assert 'CryptoRegimeManager-ResearchWorker' in s
 assert 'kucoin_live_service.lock' in s
 assert 'taskkill.exe' in s
def test_preflight_never_discards_source_automatically():
 s=text('scripts/installer_preflight.py')
 assert 'genuine source/unclassified changes remain; no source file was discarded' in s
def test_troubleshooter_entrypoint_exists():
 assert (ROOT/'TROUBLESHOOT_INSTALL.cmd').exists()
