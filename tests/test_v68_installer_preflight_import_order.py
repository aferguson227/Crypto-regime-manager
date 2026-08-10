from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]

def test_installer_preflight_compiles_and_future_import_is_legal():
 p=ROOT/"scripts"/"installer_preflight.py"
 source=p.read_text(encoding="utf-8")
 ast.parse(source, filename=str(p))
 lines=source.splitlines()
 future=next(i for i,x in enumerate(lines) if x.strip()=="from __future__ import annotations")
 # Only shebang, module docstring, blank lines may precede a future import.
 prefix="\n".join(lines[:future])
 assert "import time" not in prefix
