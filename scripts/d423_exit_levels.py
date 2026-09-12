"""D423 -- the exit LEVELS the structure implies, per event, computed from nothing after the entry.

For event k (name nm, touch day t_k, side s_k, zone [lo_k, hi_k], entry E_k = the touch-day close):

  SWING   the extreme of the path between the PRIOR touch day t_j and today, in the trade's
          direction: long  max HI[t_j .. t_k-1],  short  min LO[t_j .. t_k-1].
          "Where the first bounce ended" -- the structural target a second-zone trade is drawn
          to. t_j is the most recent distinct prior touch day on the name within STACK_W sessions
          (unique when STACK2-ANY holds). NaN when there is no prior touch, or when the swing is
          not beyond the entry in the trade's direction (a target behind the entry is not one).

  OPP     the nearest TESTED opposite-side level in the trade's direction: over prior events on
          the name with s_j != s_k and t_k - LIFE <= t_j < t_k, long: the smallest lo_j above E_k;
          short: the largest hi_j below E_k. NaN when none. Only zones that were touched are in
          the event table, so this is a level that already reacted once, not a live untouched zone.

  FAR     the zone's far edge -- long lo_k, short hi_k -- D418's ST-edge level, used here as a
          stop ON THE CLOSE (a close beyond it), not intrabar.

The walker and the book read these as prices; the flags read no outcome bar.
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
HOLD, LIFE, STACK_W = 5, 60, 20


def load():
    _s = importlib.util.spec_from_file_location("d422r", REPO / "scripts" / "run_d422_second_zone.py")
    M = importlib.util.module_from_spec(_s)
    sys.modules["d422r"] = M
    _s.loader.exec_module(M)
    I, P, B, fl = M.load_all()
    return I, P, B, fl, M


def levels(I, P):
    t, i, side, lo_z, hi_z, E = I["t"], I["i"], I["side"], I["lo"], I["hi"], I["E"]
    N = len(t)
    HI, LO = P["HI"], P["LO"]
    order = np.lexsort((t, i))
    tj_of = np.full(N, -1, np.int64)
    swing = np.full(N, np.nan); opp = np.full(N, np.nan)
    hist = {}                                       # name -> list of (t_j, s_j, lo_j, hi_j)
    for k in order:
        nm = int(i[k]); tk = int(t[k]); sk = int(side[k]); e = float(E[k])
        h = hist.get(nm, [])
        tj = -1; best = np.nan
        for (tjj, sj, lj, hj) in h:
            if tjj >= tk:
                continue                            # same-day siblings never count
            if tk - STACK_W <= tjj and tjj > tj:
                tj = tjj
            if sj != sk and tk - LIFE <= tjj:
                if sk > 0 and lj > e and (not np.isfinite(best) or lj < best):
                    best = lj
                if sk < 0 and hj < e and (not np.isfinite(best) or hj > best):
                    best = hj
        if tj >= 0:
            if sk > 0:
                x = np.nanmax(HI[tj:tk, nm]); swing[k] = x if x > e else np.nan
            else:
                x = np.nanmin(LO[tj:tk, nm]); swing[k] = x if x < e else np.nan
        tj_of[k] = tj; opp[k] = best
        h.append((tk, sk, float(lo_z[k]), float(hi_z[k]))); hist[nm] = h
    far = np.where(side > 0, lo_z, hi_z).astype(float)
    return dict(tj=tj_of, swing=swing, opp=opp, far=far)


def dist_atr(level, I):
    """Signed distance from the entry to a level, in ATR, favourable positive."""
    return I["side"] * (level - I["E"]) / I["ATR"]


if __name__ == "__main__":
    I, P, B, fl, M = load()
    L = levels(I, P)
    c2 = I["c2"]; A = fl["s2any"]; m = A & c2
    yr = np.array([int(str(x)[:4]) for x in I["dates"][I["t"]]])
    print(f"events {len(I['t']):,}   STACK2-ANY {int(A.sum()):,}   ANY & cell 2 {int(m.sum()):,}   & 2018+ {int((m & (yr >= 2018)).sum()):,}")
    for nm_, lv, sign in (("SWING", L["swing"], +1), ("OPP", L["opp"], +1), ("FAR", L["far"], -1)):
        d = sign * dist_atr(lv, I)
        for lab, mm in (("pooled", np.ones_like(m)), ("ANY", A), ("ANY & cell 2", m)):
            f = mm & np.isfinite(lv)
            q = np.nanquantile(d[f], [.1, .25, .5, .75, .9]) if f.any() else [np.nan] * 5
            print(f"  {nm_:5s} {lab:13s} coverage {100*f.sum()/mm.sum():5.1f}%   distance ATR p10/25/50/75/90  "
                  f"{q[0]:5.2f} {q[1]:5.2f} {q[2]:5.2f} {q[3]:5.2f} {q[4]:5.2f}   share within 1 ATR {100*(d[f] <= 1).mean():5.1f}%   within 2 {100*(d[f] <= 2).mean():5.1f}%")
    both = m & np.isfinite(L["swing"]) & np.isfinite(L["opp"])
    print(f"  ANY & cell 2 with both SWING and OPP: {100*both.sum()/m.sum():.1f}%;  OPP nearer than SWING on {100*(L['opp'][both]*I['side'][both] < L['swing'][both]*I['side'][both]).mean():.1f}% of those")
    print(f"  prior touch t_j is the SAME side on {100*(I['side'][m] == I['side'][L['tj'][m]]).mean():.1f}% of ANY & cell 2 (t_j >= 0 on {100*(L['tj'][m] >= 0).mean():.1f}%)")
