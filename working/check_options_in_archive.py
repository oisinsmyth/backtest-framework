"""Do we hold OPTIONS ON FUTURES in the archive, and for which roots?

The ohlcv-1m pull was scope ALL_SYMBOLS ("each contract month, each calendar spread and each option
on a future"). If that is literally true we already own the data for a dealer-gamma study, which the
lead-scan excluded for a SCHEDULING reason and never on merit. If it is not, that avenue needs a
purchase and is a different proposition.

Census of one recent file's symbology: how many symbols are option-like, on which underlying roots,
and does the `statistics` schema carry open interest for them (which is what a gamma-exposure
estimate needs, strike by strike).

    python working/check_options_in_archive.py        # SYSTEM python (databento)
"""
from __future__ import annotations
import re
import sys
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_breadth_hourly as B  # noqa: E402

# CME option symbology: an underlying code, a month letter, a year digit, then C/P and a strike.
OPT = re.compile(r"^([A-Z0-9]{1,4})([FGHJKMNQUVXZ])(\d{1,2})\s*([CP])(\d+(?:\.\d+)?)$")
FUT = re.compile(r"^([A-Z0-9]{1,5}?)([FGHJKMNQUVXZ])(\d{1,2})$")

files = B.ohlcv_files()
f = [x for x in files if x.name[10:14] >= "2026"][-1]
print(f"symbology census on {f.name}\n")
store = db.DBNStore.from_file(f)

kinds = Counter()
opt_roots = Counter()
samples = {}
for sym in store.metadata.mappings:
    s = str(sym)
    if OPT.match(s):
        kinds["option"] += 1
        r = OPT.match(s).group(1)
        opt_roots[r] += 1
        samples.setdefault(r, s)
    elif FUT.match(s):
        kinds["future outright"] += 1
    elif "-" in s:
        kinds["spread (has a dash)"] += 1
    else:
        kinds["other"] += 1
        samples.setdefault("_other_" + s[:2], s)

print(f"{sum(kinds.values()):,} symbols in this file's symbology")
for k, v in kinds.most_common():
    print(f"   {k:<24} {v:>8,}")

print(f"\noption-like symbols by underlying root ({len(opt_roots)} roots):")
for r, n in opt_roots.most_common(20):
    print(f"   {r:<6} {n:>7,}   e.g. {samples[r]}")
if not opt_roots:
    print("   NONE. The ohlcv-1m pull does not carry options on futures in this file's symbology,")
    print("   so a dealer-gamma study would need a separate purchase.")
print("\na few 'other' shapes, to show what the regexes are not catching:")
for k, v in list(samples.items())[:6]:
    if k.startswith("_other_"):
        print(f"   {v}")
