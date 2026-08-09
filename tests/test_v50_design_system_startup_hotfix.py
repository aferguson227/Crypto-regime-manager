from pathlib import Path
import shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]
def test_node_checks_both_dashboard_javascript_files_when_available():
    node=shutil.which('node')
    if not node:return
    for rel in ['docs/design-system.js','docs/unified_dashboard.js']:
        r=subprocess.run([node,'--check',rel],cwd=ROOT,text=True,capture_output=True)
        assert r.returncode==0,r.stderr
