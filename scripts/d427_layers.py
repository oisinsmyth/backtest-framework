"""D427 -- the five layers on rung 2, as masks. No outcome bar is read here.

Base   R2 = STACK2-ANY & cell 2 (D422's rung, 9,411)
  L1 GAP     the prior touch is 3-20 sessions back (drop gap 1-2: the market running through the first zone)
  L2 LONG    demand zones only (side > 0)
  L3 OPP     the prior touch was the OPPOSITE side, 3-10 sessions back -- a PRIORITY in the book, a
             reported sub-cell per trade (a priority changes nothing in the path-invariant lens)
  L4 ZTP     the exit: limit at the next live opposite-side zone (D425), else t+5
  L5 CHEAP   entry price below the base population's lower tercile, a FIXED cut computed here
Cumulative order: L1, L1+L2, L1+L2 (+L3 priority), +L4, +L5.
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]


def load():
    _s = importlib.util.spec_from_file_location("d426f", REPO / "scripts" / "d426_rung_flags.py")
    RF = importlib.util.module_from_spec(_s); sys.modules["d426f"] = RF; _s.loader.exec_module(RF)
    I, P, B, fl, M, zones = RF.load()
    F = RF.flags(I, fl)
    _z = importlib.util.spec_from_file_location("d425l", REPO / "scripts" / "d425_zone_levels.py")
    ZL = sys.modules.get("d425l") or importlib.util.module_from_spec(_z)
    if "d425l" not in sys.modules:
        sys.modules["d425l"] = ZL; _z.loader.exec_module(ZL)
    L = ZL.levels(I, zones)
    return I, P, B, fl, M, F, L


def layers(I, fl, F):
    c2, side, E = I["c2"], I["side"], I["E"]
    R2 = fl["s2any"] & c2
    g = F["prev_gap"]
    L1 = R2 & (g >= 3)
    L2 = R2 & (side > 0)
    L3 = R2 & F["opp_prior"] & (g >= 3) & (g <= 10)
    cut = float(np.quantile(E[R2], 1 / 3))
    L5 = R2 & (E < cut)
    cum = {"base": R2, "L1": L1, "L1+L2": L1 & (side > 0), "L1+L2+L3prio": L1 & (side > 0),
           "L1+L2+L3prio+L4": L1 & (side > 0), "L1..L5": L1 & (side > 0) & (E < cut)}
    return dict(R2=R2, L1=L1, L2=L2, L3=L3, L5=L5, cut=cut, cum=cum)


if __name__ == "__main__":
    I, P, B, fl, M, F, L = load()
    X = layers(I, fl, F)
    yr = np.array([int(str(x)[:4]) for x in I["dates"][I["t"]]])
    print(f"base R2 {int(X['R2'].sum()):,}   price cut for L5: ${X['cut']:.2f}")
    for k in ("L1", "L2", "L3", "L5"):
        m = X[k]; print(f"  {k:6s} alone   n {int(m.sum()):6,}  = {100*m.sum()/X['R2'].sum():5.1f}% of base   2018+ {int((m & (yr>=2018)).sum()):6,}   2021+ {int((m & (yr>=2021)).sum()):6,}   ZTP coverage {100*np.isfinite(L['ztp'][m]).mean():.1f}%")
    for k, m in X["cum"].items():
        print(f"  {k:18s}  n {int(m.sum()):6,}   2018+ {int((m & (yr>=2018)).sum()):6,}   2021+ {int((m & (yr>=2021)).sum()):6,}   L3 inside {int((m & X['L3']).sum()):5,}   names {len(set(I['i'][m].tolist())):5,}   events/day {m.sum()/int(I['T'][0]):.2f}")
