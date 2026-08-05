from __future__ import annotations
import re
from pathlib import Path
ALIASES={"XBT":"BTC","XXBT":"BTC","XETH":"ETH"}
QUOTES=("USDT","USDC","USD","EUR","GBP","BTC","ETH")
def canonical_asset(value:str)->str:
    s=re.sub(r"[^A-Z0-9]","",str(value).upper())
    for q in QUOTES:
        if s.endswith(q) and len(s)>len(q): s=s[:-len(q)]; break
    return ALIASES.get(s,s)
def symbol_key(name:str)->str:
    return canonical_asset(Path(name).stem)
