"""D428 -- the combined book's pool, as masks. No outcome bar is read here.

POOL   STACK2-ANY & cell 2 & entry price < CUT (D427's fixed cheap-tercile cut) & prior touch 3-20 sessions back
PRIO   the prior touch was the opposite side, 3-10 back (D427's L3) -- refill priority inside the pool
LONG   demand zones only -- a reported arm, not the primary
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
CUT = 38.51           # D427: the base population's lower price tercile, fixed there
HOLD = 5


def load():
    _s = importlib.util.spec_from_file_location("d427l", REPO / "scripts" / "d427_layers.py")
    LY = importlib.util.module_from_spec(_s); sys.modules["d427l"] = LY; _s.loader.exec_module(LY)
    I, P, B, fl, M, F, L = LY.load()
    X = LY.layers(I, fl, F)
    assert abs(X["cut"] - CUT) < 0.01, f"[STAGE0] D427's cut moved: {X['cut']:.2f}"
    return I, P, B, fl, M, F, L, X


def pool(I, X):
    E, side = I["E"], I["side"]
    pl = X["L1"] & (E < CUT)                   # L1 is already R2 & gap 3-20
    return dict(pool=pl, prio=pl & X["L3"], long=pl & (side > 0))


if __name__ == "__main__":
    I, P, B, fl, M, F, L, X = load()
    Q = pool(I, X)
    T = int(I["T"][0]); t = I["t"]; yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    m = Q["pool"]; n = int(m.sum()); per_day = n / T
    days = np.bincount(t[m], minlength=T)
    print(f"pool {n:,} events   {per_day:.3f}/day   mean occupancy at a 5-day hold {HOLD*per_day:.2f} positions   "
          f"days with an event {int((days>0).sum()):,} of {T:,}   p95 events on an event day {np.quantile(days[days>0],.95):.0f}   max {days.max()}")
    print(f"  long {int(Q['long'].sum()):,} ({100*Q['long'].sum()/n:.1f}%)   priority events {int(Q['prio'].sum()):,} ({100*Q['prio'].sum()/n:.1f}%)   names {len(set(I['i'][m].tolist())):,}")
    print(f"  2018+ {int((m & (yr>=2018)).sum()):,}   2021-2026 {int((m & (yr>=2021)).sum()):,}")
    for N in (2, 3, 4, 5, 7, 10):
        print(f"  N={N:2d}: occupancy/N = {HOLD*per_day/N:.2f}")
