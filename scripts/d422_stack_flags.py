"""D422 -- the second-zone conditions, with D421's two wrinkles resolved. Flags only; no outcome.

WRINKLE 2, FIXED: prior touches are counted as DISTINCT TOUCH DAYS, not events. Two zones armed
and touched on the same day are one touch day -- for the event itself (they never counted each
other) and now for every later event too (D421 counted a same-day pair as two).

WRINKLE 1, OPENED INTO THREE ARMS. For event k (touch day t_k, side s_k), over the trailing 20
sessions [t_k - 20, t_k):
  prior_same   distinct prior days with a SAME-side touch on the name
  prior_opp    distinct prior days with an OPPOSITE-side touch on the name

  STACK2-SAME   prior_same == 1 and prior_opp == 0     PRIMARY -- "the second demand zone in a decline"
  STACK2-ANY    prior_same + prior_opp == 1            D421's rung, side-blind, distinct-day -- the baseline
  STACK1        prior_same + prior_opp == 0            the initial touch
  STACK3P       prior_same + prior_opp >= 2            the trend

  FLIP          the "supply becomes demand" claim, as the claim actually reads: this zone's midpoint
                lies inside the band of a prior OPPOSITE-side zone on the name, touched within the
                last 60 sessions, whose far edge was traded through before today -- a level that
                was one thing, was broken, and is now being approached from the other side.
                Independent of the stack count; also reported intersected with STACK2-ANY.
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
HOLD, LIFE, STACK_W = 5, 60, 20


def load():
    _s = importlib.util.spec_from_file_location("d421f", REPO / "scripts" / "d421_depth_flags.py")
    F = importlib.util.module_from_spec(_s)
    sys.modules["d421f"] = F
    _s.loader.exec_module(F)
    return F.load()


def flags(I, P):
    t, i, side, lo_z, hi_z = I["t"], I["i"], I["side"], I["lo"], I["hi"]
    N = len(t)
    HI, LO = P["HI"], P["LO"]
    order = np.lexsort((t, i))
    same = np.zeros(N, np.int32); opp = np.zeros(N, np.int32); flip = np.zeros(N, bool)
    hist = {}                                       # name -> list of (t_j, s_j, lo_j, hi_j)
    for k in order:
        nm = int(i[k]); tk = int(t[k]); sk = int(side[k]); mid = 0.5 * (lo_z[k] + hi_z[k])
        h = hist.get(nm, [])
        days_same, days_opp = set(), set()
        hit = False
        for (tj, sj, lj, hj) in h:
            if tj >= tk:
                continue                            # same-day siblings never count
            if tk - STACK_W <= tj:
                (days_same if sj == sk else days_opp).add(tj)
            if not hit and sj != sk and tk - LIFE <= tj and lj <= mid <= hj:
                # the opposite-side zone's FAR edge traded through before today?
                if sj > 0:                          # it was demand: breached if price went BELOW it
                    hit = np.nanmin(LO[tj:tk + 1, nm]) < lj
                else:                               # it was supply: breached if price went ABOVE it
                    hit = np.nanmax(HI[tj:tk + 1, nm]) > hj
        same[k] = len(days_same); opp[k] = len(days_opp); flip[k] = hit
        h.append((tk, sk, float(lo_z[k]), float(hi_z[k]))); hist[nm] = h
    tot = same + opp
    return dict(same=same, opp=opp, flip=flip,
                s2same=(same == 1) & (opp == 0), s2any=(tot == 1), s1=(tot == 0), s3p=(tot >= 2))


if __name__ == "__main__":
    I, P, G = load()
    fl = flags(I, P)
    c2 = I["c2"]; dates = I["dates"]
    yr = np.array([int(str(x)[:4]) for x in dates[I["t"]]]); h2 = yr >= 2018
    print(f"events {len(I['t']):,}   cell 2 {int(c2.sum()):,}   second half {int(h2.sum()):,}")
    for lab in ("s1", "s2same", "s2any", "s3p", "flip"):
        m = fl[lab]
        print(f"  {lab:7s} pooled {100*m.mean():5.1f}%  n {int(m.sum()):7,}   cell 2 {100*m[c2].mean():5.1f}%  n {int(m[c2].sum()):6,}   "
              f"cell 2 & 2018+ n {int((m & c2 & h2).sum()):6,}")
    both = fl["flip"] & fl["s2any"]
    print(f"  flip & s2any  pooled n {int(both.sum()):,}   cell 2 n {int((both & c2).sum()):,}")
    print(f"  share of s2any that is same-side: {100*fl['s2same'][fl['s2any']].mean():.1f}%")
