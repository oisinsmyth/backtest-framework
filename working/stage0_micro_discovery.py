"""STAGE 0, step 1: which micro/mini contracts EXIST in the archive at all? Metadata only, no bars.

The taker-affordability screen found the three cheapest markets we hold -- NG (2.1% cost/move), HG
(3.1%) and SI (3.4%) -- are locked out by C-d at full size (sigma $1,081 / $704 / $1,249 against a
$500 bar). The micro contract is the instrument that breaks that tie, and our verified spec file has
only seven: MES MNQ MYM M2K M6E MCL MGC.

DO NOT GUESS THE ROOT CODES. This enumerates every outright root in one archive file's symbol
mapping table and reports them, so the candidate list is read off the exchange's own symbology
rather than from memory. Existence first; liquidity and specs are step 2.

    python working/stage0_micro_discovery.py            # SYSTEM python (databento)
"""
from __future__ import annotations
import re
import sys
from collections import Counter
from pathlib import Path
import pandas as pd
import databento as db

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_breadth_hourly as B  # noqa: E402

OUTRIGHT_ANY = re.compile(r"^([A-Z0-9]{1,5}?)([FGHJKMNQUVXZ])(\d{1,2})$")
# the full-size roots whose cheap-but-too-big rows motivated this, plus the ones we already trade
PARENTS = {"NG", "HG", "SI", "GC", "CL", "ES", "NQ", "YM", "RTY", "ZN", "ZF", "ZB", "6E"}
KNOWN_MICROS = {"MES", "MNQ", "MYM", "M2K", "M6E", "MCL", "MGC"}

files = B.ohlcv_files()
f = files[-1]
for cand in files:                                   # prefer the most recent, most liquid slice
    if cand.name[10:14] >= "2026":
        f = cand
print(f"reading symbology from {f.name}\n")

store = db.DBNStore.from_file(f)
roots = Counter()
per_root_syms = {}
for sym in store.metadata.mappings:
    m = OUTRIGHT_ANY.match(str(sym))
    if not m:
        continue
    r = m.group(1)
    roots[r] += 1
    per_root_syms.setdefault(r, []).append(str(sym))

print(f"{len(roots):,} outright root codes in this file's symbology, {sum(roots.values()):,} symbols\n")

print("== the roots we already score")
for r in sorted(PARENTS | KNOWN_MICROS):
    print(f"   {r:<5} {roots.get(r, 0):>4} contract months" + ("" if r in roots else "   <-- ABSENT"))

print("\n== every root code that could be a micro or mini of one of those (prefix M, or a Q/M variant)")
cands = []
for r in sorted(roots):
    if r in PARENTS or r in KNOWN_MICROS:
        continue
    hit = ((r.startswith("M") and (r[1:] in PARENTS or len(r) <= 3)) or
           (r.startswith("Q") and len(r) <= 3) or
           (r.endswith("L") and r[:-1] in PARENTS) or
           r in {"SIL", "MHG", "MNG", "QG", "QI", "QC", "QO", "QM", "MBT", "MET"})
    if hit:
        cands.append(r)
        print(f"   {r:<5} {roots[r]:>4} contract months   e.g. {sorted(per_root_syms[r])[:4]}")

print(f"\n== the specific codes CME lists for micro gas, copper and silver")
for code, what in (("MNG", "Micro Henry Hub Natural Gas"), ("MHG", "Micro Copper"), ("SIL", "Micro Silver"),
                   ("QG", "E-mini Natural Gas"), ("QI", "E-mini Silver"), ("QC", "E-mini Copper"),
                   ("QO", "E-mini Gold"), ("QM", "E-mini Crude")):
    n = roots.get(code, 0)
    print(f"   {code:<5} {what:<30} {n:>4} contract months" + ("" if n else "   <-- NOT IN THE ARCHIVE"))

out = sorted(set(cands) | {c for c in ("MNG", "MHG", "SIL", "QG", "QI", "QC", "QO", "QM") if c in roots})
(REPO / "working" / "stage0_micro_candidates.txt").write_text("\n".join(out))
print(f"\nwrote {len(out)} candidate root codes to working/stage0_micro_candidates.txt")
