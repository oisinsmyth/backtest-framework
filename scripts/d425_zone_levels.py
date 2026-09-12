"""D425 -- exit levels read off the ZONES THE DETECTOR ALREADY FINDS, per event.

The zone table is D413's: every ARMED departure zone on every name (touched or not), with its
creation bar u, arming bar a, band [lo, hi], side, and first-touch day tt (-1 if never touched
within LIFE). D423 could only see touched zones (the event table); this reads the whole table.

For event k (name nm, touch day t_k, side s_k, entry E_k):

  ZTP     the nearest LIVE opposite-side zone beyond the entry, in the trade's direction: a zone on
          the name with side != s_k, armed by t_k (a_j <= t_k), not yet touched (tt_j == -1 or
          tt_j > t_k), inside its life (t_k <= a_j + LIFE), whose band lies beyond E_k
          (long: lo_j > E_k, short: hi_j < E_k). Target = its NEAR edge. NaN when none.
          "Take profit at the next supply zone."

  ZTRAIL  a stop that follows NEW same-side zones as they arm during the hold: for hold bar b
          (day t_k + 1 + b), the far edge of every same-side zone on the name armed on or before
          that day and after t_k, ratcheted in the trade's favour (long: max lo_j; short: min hi_j).
          Evaluated on the CLOSE (a close beyond it exits). NaN until the first such zone arms.
          "Trail the stop under the last demand zone."  Shape (N, HOLD); reads bars after the
          entry BY CONSTRUCTION -- it is the exit rule, not a flag.

  FAR     the entry zone's own far edge (D423), the initial stop the trail ratchets from.
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
HOLD, LIFE = 5, 60


def load():
    _s = importlib.util.spec_from_file_location("d423l", REPO / "scripts" / "d423_exit_levels.py")
    LV = importlib.util.module_from_spec(_s); sys.modules["d423l"] = LV; _s.loader.exec_module(LV)
    I, P, B, fl, M = LV.load()
    G = sys.modules["d420"]                              # registered by d421_depth_flags.load()
    Z4, M13 = G.Z4, G.M
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M13.THETA, M13.LIFE, M13.H, delta=M13.DELTA)
    Z, g = A["Z"], A["good"]
    assert np.array_equal(A["tt"][g], I["t"]) and np.array_equal(Z["i"][g], I["i"]), "[ALIGN] zone table vs event table"
    zones = dict(i=Z["i"], side=Z["side"], a=Z["a"], lo=Z["lo"], hi=Z["hi"], tt=np.where(A["has"], A["tt"], -1))
    return I, P, B, fl, M, zones


def levels(I, zones):
    t, i, side, E = I["t"], I["i"], I["side"], I["E"]
    N = len(t)
    ztp = np.full(N, np.nan); trail = np.full((N, HOLD), np.nan)
    n_live = np.zeros(N, np.int32); n_new = np.zeros(N, np.int32)
    zi, zs, za, zlo, zhi, ztt = zones["i"], zones["side"], zones["a"], zones["lo"], zones["hi"], zones["tt"]
    zo = np.argsort(zi, kind="stable")
    zb = np.searchsorted(zi[zo], np.arange(zi.max() + 2))
    eo = np.argsort(i, kind="stable")
    eb = np.searchsorted(i[eo], np.arange(i.max() + 2))
    for nm in range(i.max() + 1):
        ks = eo[eb[nm]:eb[nm + 1]]
        if ks.size == 0:
            continue
        js = zo[zb[nm]:zb[nm + 1]] if nm < len(zb) - 1 else np.array([], int)
        if js.size == 0:
            continue
        s_j, a_j, lo_j, hi_j, tt_j = zs[js], za[js], zlo[js], zhi[js], ztt[js]
        for k in ks:
            tk = int(t[k]); sk = int(side[k]); e = float(E[k])
            live = (s_j != sk) & (a_j <= tk) & ((tt_j < 0) | (tt_j > tk)) & (tk <= a_j + LIFE)
            if sk > 0:
                cand = live & (lo_j > e); n_live[k] = cand.sum()
                if cand.any(): ztp[k] = lo_j[cand].min()
            else:
                cand = live & (hi_j < e); n_live[k] = cand.sum()
                if cand.any(): ztp[k] = hi_j[cand].max()
            new = (s_j == sk) & (a_j > tk) & (a_j <= tk + HOLD)
            n_new[k] = new.sum()
            if new.any():
                far = lo_j[new] if sk > 0 else hi_j[new]; when = a_j[new] - tk - 1        # bar index at which it arms
                for b in range(HOLD):
                    m = when <= b
                    if m.any():
                        trail[k, b] = far[m].max() if sk > 0 else far[m].min()
    far0 = np.where(side > 0, I["lo"], I["hi"]).astype(float)
    return dict(ztp=ztp, trail=trail, far=far0, n_live=n_live, n_new=n_new)


if __name__ == "__main__":
    I, P, B, fl, M, zones = load()
    L = levels(I, zones)
    c2 = I["c2"]; A = fl["s2any"]; m = A & c2
    print(f"zones armed {len(zones['i']):,}  touched {(zones['tt'] >= 0).sum():,}   events {len(I['t']):,}   ANY & cell 2 {int(m.sum()):,}")
    d = I["side"] * (L["ztp"] - I["E"]) / I["ATR"]
    for lab, mm in (("pooled", np.ones_like(m)), ("ANY", A), ("ANY & cell 2", m)):
        f = mm & np.isfinite(L["ztp"]); q = np.quantile(d[f], [.1, .25, .5, .75, .9])
        print(f"  ZTP {lab:13s} coverage {100*f.sum()/mm.sum():5.1f}%   distance ATR p10/25/50/75/90 {q[0]:5.2f} {q[1]:5.2f} {q[2]:5.2f} {q[3]:5.2f} {q[4]:5.2f}   "
              f"within 1 ATR {100*(d[f] <= 1).mean():5.1f}%  within 2 {100*(d[f] <= 2).mean():5.1f}%   live opp zones per event p50 {np.median(L['n_live'][mm]):.0f}")
    print("  (ZTRAIL engagement reads the hold and is reported by the runner, not here)")
