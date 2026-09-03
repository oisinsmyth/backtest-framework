"""Q1's Jaccard conflates two things. Split them.

D297's premise measured 0.721 on a FIXED holding path: it decomposed each held
position-bar of one book and asked whether an idio-referenced rule would fire on
that same position. D303's two rules produce DIFFERENT books -- once one exits a
position the other keeps, the holdings diverge and the exit sets are drawn from
different position populations.

So a low Jaccard could mean either:
  (a) the rules disagree about positions they BOTH hold  -- a reference effect
  (b) the books do not hold the same positions at all    -- a path effect

This measures (b) directly, and then recomputes agreement restricted to the
positions both books actually held, which is the quantity comparable to 0.721.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework")
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location(
    "d303", REPO / "scripts" / "run_d303_reference.py")
D = importlib.util.module_from_spec(spec)
sys.modules["d303"] = D
spec.loader.exec_module(D)

A = D.load_cache(mmap=False)
xm = {"flat": 0.9627, "sqrt": 0.9687}

for band in ("flat", "sqrt"):
    raw = D.simulate(A, "raw", band, 1.0)
    exc = D.simulate(A, "excess", band, xm[band])

    def keys(res):
        return {(x[0], x[1], x[5]) for x in res["trades"]}

    def fired(res):
        return {(x[0], x[1], x[5]) for x in res["trades"] if x[6]}

    kr, ke = keys(raw), keys(exc)
    shared = kr & ke
    fr, fe = fired(raw), fired(exc)

    naive = len(fr & fe) / max(len(fr | fe), 1)
    # restricted to positions BOTH books held -- comparable to D297's 0.721
    fr_s, fe_s = fr & shared, fe & shared
    restricted = len(fr_s & fe_s) / max(len(fr_s | fe_s), 1)

    print(f"band = {band}")
    print(f"  positions held by raw          {len(kr):,}")
    print(f"  positions held by excess       {len(ke):,}")
    print(f"  positions held by BOTH         {len(shared):,}  "
          f"({100 * len(shared) / max(len(kr | ke), 1):.1f}% of the union)")
    print(f"  jaccard over all triggers      {naive:.3f}   (what the runner "
          f"reports)")
    print(f"  jaccard on SHARED positions    {restricted:.3f}   (comparable to "
          f"D297's 0.721)")
    print(f"  of shared positions, raw fired {len(fr_s):,}, excess fired "
          f"{len(fe_s):,}, both {len(fr_s & fe_s):,}")
    print()
