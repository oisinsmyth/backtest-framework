"""D515 diagnostic: is crude's (and gold's) edge SLOWER, or is it simply in hours the arm never trades?

edge_sigma at H=1 restricted to the day-session segments the arm trades, against the overnight segments it does not.
A decomposition of D515's own cells; nothing new is read.

    uv run python -u working/d515_where_in_the_clock_scratch.py
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D515 = _load("d515c", "run_d515_horizon_ladder.py")
D506B = _load("d506b", "d506_macd_breadth.py")
edge_sigma = D515.edge_sigma

meta = json.loads(D506B.META.read_text(encoding="utf-8")); specs = meta["specs"]; d_all = pd.read_csv(D506B.FIX)
print("WHERE IN THE CLOCK IS THE EDGE? edge_sigma at H=1, by segment group\n")
print(f"  {'root':5s} {'window':>8s} | {'DAY segs':>9s} {'n':>7s} | {'NIGHT segs':>10s} {'n':>7s} | {'all':>8s}  reading")
rows = []
for r in D515.ROOTS:
    w = specs[r]["day_window"]; first, last = D506B.seg_index(w[0]), D506B.seg_index(w[1])
    sig, og, ns, nseg = D515.flat_series(d_all, r, w)
    f = D515.forward(og, 1)
    day = np.zeros(nseg, bool); day[first:last + 1] = True
    night = ~day
    def e(mask):
        s = sig[:, mask].ravel(); ff = f[:, mask].ravel()
        m = np.isfinite(s) & np.isfinite(ff) & (s != 0)
        return edge_sigma(s, ff), int(m.sum())
    ed, nd = e(day); en, nn = e(night); ea, na = e(np.ones(nseg, bool))
    tag = "edge is in the NIGHT" if en > ed + 0.004 else ("edge is in the DAY" if ed > en + 0.004 else "even")
    rows.append(dict(root=r, day_edge=ed, day_n=nd, night_edge=en, night_n=nn, all_edge=ea, reading=tag))
    print(f"  {r:5s} {str(w):>8s} | {ed:+9.4f} {nd:7,} | {en:+10.4f} {nn:7,} | {ea:+8.4f}  {tag}")
D = pd.DataFrame(rows)
print("\nREAD:")
for r in ("CL", "GC"):
    x = D[D.root == r].iloc[0]
    print(f"  {r}: the arm trades only the day segments, where edge_sigma is {x.day_edge:+.4f}; the overnight segments it never trades read {x.night_edge:+.4f}")
print(f"\n  roots whose edge is larger at night: {list(D[D.night_edge > D.day_edge + 0.004].root)}")
print(f"  roots whose edge is larger in the day: {list(D[D.day_edge > D.night_edge + 0.004].root)}")
D.to_csv(REPO / "working" / "d515_where_in_the_clock.csv", index=False, float_format="%.5f")
print("\nwrote working/d515_where_in_the_clock.csv")
