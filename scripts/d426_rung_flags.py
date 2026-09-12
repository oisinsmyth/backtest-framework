"""D426 -- rung 1 traded; a same-side rung 2 on the held name doubles down, restarts the clock and
brings the zone stops. Flags only; no outcome bar.

Per event k (name nm, touch day t_k, side s_k):
  r1        STACK1     no prior touch day on the name in the trailing 20 sessions (D422's s1)
  r2        STACK2-ANY exactly one prior touch day, either side (D422's s2any)
  prev_gap  for r2: sessions since that prior touch day; -1 otherwise
  prev_k    for r2: the index of the prior touch's event on the name (the rung-1 event it would
            double; -1 if the prior touch day carried no event of the same side -- then it was an
            opposite-side touch, and the add is NOT taken)
  add_A     r2, same-side prior event exists, prev_gap <= HOLD, and BOTH events in cell 2
  add_B     as add_A but only the rung-1 event need be in cell 2 (any same-side rung-2 touch adds)
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
HOLD, STACK_W = 5, 20


def load():
    _s = importlib.util.spec_from_file_location("d425l", REPO / "scripts" / "d425_zone_levels.py")
    ZL = importlib.util.module_from_spec(_s); sys.modules["d425l"] = ZL; _s.loader.exec_module(ZL)
    return ZL.load()            # I, P, B, fl, M, zones


def flags(I, fl):
    t, i, side, c2 = I["t"], I["i"], I["side"], I["c2"]
    N = len(t)
    order = np.lexsort((t, i))
    prev_gap = np.full(N, -1, np.int64); prev_k = np.full(N, -1, np.int64); opp_prior = np.zeros(N, bool)
    # D422's counter is distinct prior (DAY, SIDE) pairs -- a day touched on both sides counts as
    # two there, which its record calls "distinct touch days". Rung 2 here must be the rung D422
    # measured, so the same pairs are counted; the assertion below holds it to D422's flag.
    hist = {}                                     # name -> list of (day, side, first event index)
    for k in order:
        nm = int(i[k]); tk = int(t[k]); sk = int(side[k])
        h = hist.get(nm, [])
        prior = [(d, s, q) for d, s, q in h if tk - STACK_W <= d < tk]
        if len(prior) == 1:
            d, s, q = prior[0]; prev_gap[k] = tk - d
            if s == sk:
                prev_k[k] = q                     # the first same-side event of that day
            else:
                opp_prior[k] = True
        if not any(d == tk and s == sk for d, s, q in h):
            h.append((tk, sk, int(k))); hist[nm] = h
    r1, r2 = fl["s1"], fl["s2any"]
    assert np.all(prev_gap[r2] >= 1) and np.all(prev_gap[~r2] == -1), "[FLAG] prev_gap defined iff STACK2-ANY"
    assert np.all((prev_k >= 0) <= r2) and np.all(r1[prev_k[prev_k >= 0]] | ~r1[prev_k[prev_k >= 0]]), "[FLAG] prev_k only on rung 2"
    has = prev_k >= 0
    prior_c2 = np.zeros(N, bool); prior_c2[has] = c2[prev_k[has]]          # the CURRENT event's flag: was its prior in the cell
    prior_r1 = np.zeros(N, bool); prior_r1[has] = r1[prev_k[has]]          # ... and was it a rung-1 trade
    held = r2 & has & (prev_gap <= HOLD) & prior_c2
    add_A = held & prior_r1 & c2
    add_B = held & prior_r1
    return dict(r1=r1, r2=r2, prev_gap=prev_gap, prev_k=prev_k, opp_prior=opp_prior, add_A=add_A, add_B=add_B,
                held_prior_r2=held & ~prior_r1)


if __name__ == "__main__":
    I, P, B, fl, M, zones = load()
    F = flags(I, fl)
    c2 = I["c2"]; r1, r2, g, pk = F["r1"], F["r2"], F["prev_gap"], F["prev_k"]
    print(f"events {len(c2):,}   cell 2 {int(c2.sum()):,}   rung 1 & cell 2 {int((r1 & c2).sum()):,}   rung 2 & cell 2 {int((r2 & c2).sum()):,}")
    for lab, m in (("rung 2 pooled", r2), ("rung 2 & cell 2", r2 & c2)):
        gg = g[m]
        print(f"  {lab:16s} gap to prior touch p10/50/90 {np.quantile(gg,.1):.0f}/{np.median(gg):.0f}/{np.quantile(gg,.9):.0f}   gap <= 5: {100*(gg <= HOLD).mean():5.1f}%   "
              f"prior is same-side event: {100*(pk[m] >= 0).mean():5.1f}%   opposite-side: {100*F['opp_prior'][m].mean():5.1f}%")
    nA, nB = int(F["add_A"].sum()), int(F["add_B"].sum())
    r1c = int((r1 & c2).sum())
    print(f"  adds A (rung 2 in cell 2, rung 1 in cell 2, same side, gap <= 5): {nA:,}  = {100*nA/r1c:.1f}% of cell-2 rung-1 trades get doubled")
    print(f"  adds B (any same-side rung 2 on a held cell-2 rung 1):            {nB:,}  = {100*nB/r1c:.1f}%")
    print(f"  same-side rung 2 arriving on a held cell-2 trade that was itself rung 2 (not doubled; reported): {int(F['held_prior_r2'].sum()):,}")
    ga = g[F["add_A"]]
    print(f"  add gap A p10/50/90 {np.quantile(ga,.1):.0f}/{np.median(ga):.0f}/{np.quantile(ga,.9):.0f}   ->  rung 1's hold under the restart: 5 + gap, median {5 + np.median(ga):.0f} sessions")
