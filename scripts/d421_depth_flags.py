"""D421 -- the three depth flags, as a MODULE so the pre-registration's stage 0 and the runner
compute the same thing. Flags only; no outcome is read here.

  DEEP-1  re-entry       the zone was alive during the name's previous trade (a_k <= last_exit),
                          per-name sequential walk with every event entered and a five-bar hold.
                          D420's classification. Parameter-free.
  DEEP-2  breach above   a HIGHER zone on the same name was touched within the last 60 sessions
                          and its FAR edge traded through on or before this touch day.
                          Demand: some prior j with t_j in [t_k-60, t_k), same side, hi_j > hi_k,
                          and min LO over [t_j, t_k] < lo_j. Supply is the mirror.
                          The 60 is the zone life, not a new parameter.
  DEEP-3  stack depth    number of distinct prior zones on the name touched in the trailing 20
                          sessions: 0, 1, 2+  (stack 1, 2, 3+). The 20 is a declared parameter.
"""
import importlib.util
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
HOLD, LIFE, STACK_W = 5, 60, 20


def load():
    """D419's cached inputs, plus the arming day and the zone edges from D413's runner -- one call
    to the zone builder, and the event table asserted to align with the cache before anything is
    attached. D419's cache carries the entry price and the OHLC windows, not the zone's edges."""
    _s = importlib.util.spec_from_file_location("d420", REPO / "scripts" / "run_d420_episode.py")
    G = importlib.util.module_from_spec(_s)
    sys.modules["d420"] = G
    _s.loader.exec_module(G)
    B, M, Z4, D = G.B, G.M, G.Z4, G.D
    I = dict(B.build_inputs())
    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    assert np.array_equal(A["tt"][g], I["t"]) and np.array_equal(Z["i"][g], I["i"]) \
        and np.array_equal(Z["side"][g], I["side"]), "[ALIGN] D413's event table does not match D419's cache"
    I["a"], I["lo"], I["hi"] = Z["a"][g], Z["lo"][g], Z["hi"][g]
    assert np.all(I["a"] <= I["t"]) and np.all(I["lo"] < I["hi"]), "[ALIGN] zone table malformed"
    return I, P, G


def flags(I, P):
    t, i, side, a = I["t"], I["i"], I["side"], I["a"]
    N = len(t)
    HI, LO = P["HI"], P["LO"]
    # zone edges in the panel's basis: D413's Z carries lo/hi; recover from the arming/creation
    # bar's own OHLC. The cache stores E and ATR but not lo/hi, so rebuild them from D413's runner.
    lo_z, hi_z = I["lo"], I["hi"]
    order = np.lexsort((t, i))
    d1 = np.zeros(N, bool); d2 = np.zeros(N, bool); d3 = np.zeros(N, np.int32)
    last_exit = {}; hist = {}                     # name -> list of (t_j, side_j, lo_j, hi_j)
    for k in order:
        nm = int(i[k]); tk = int(t[k]); sk = int(side[k])
        # DEEP-1
        le = last_exit.get(nm, -10**9)
        d1[k] = a[k] <= le
        last_exit[nm] = tk + HOLD if a[k] > le else last_exit[nm]
        h = hist.get(nm, [])
        # DEEP-3: prior touches inside the trailing window
        d3[k] = sum(1 for (tj, sj, lj, hj) in h if tk - STACK_W <= tj < tk)
        # DEEP-2: a higher same-side zone, touched inside the life, breached on or before today
        hit = False
        for (tj, sj, lj, hj) in h:
            if sj != sk or not (tk - LIFE <= tj < tk):
                continue
            if sk > 0:
                if hj > hi_z[k] and np.nanmin(LO[tj:tk + 1, nm]) < lj:
                    hit = True; break
            else:
                if lj < lo_z[k] and np.nanmax(HI[tj:tk + 1, nm]) > hj:
                    hit = True; break
        d2[k] = hit
        h.append((tk, sk, float(lo_z[k]), float(hi_z[k]))); hist[nm] = h
    return d1, d2, d3


if __name__ == "__main__":
    I, P, G = load()
    d1, d2, d3 = flags(I, P)
    c2 = I["c2"]
    print(f"events {len(d1):,}   cell 2 {int(c2.sum()):,}")
    for lab, m in (("DEEP-1 re-entry", d1), ("DEEP-2 breach above", d2)):
        print(f"  {lab:22s} share pooled {100*m.mean():5.1f}%   cell 2 {100*m[c2].mean():5.1f}%")
    for b, lab in ((0, "stack 1"), (1, "stack 2"), (2, "stack 3+")):
        m = (d3 == b) if b < 2 else (d3 >= 2)
        print(f"  DEEP-3 {lab:15s} share pooled {100*m.mean():5.1f}%   cell 2 {100*m[c2].mean():5.1f}%")
    print(f"  overlap: DEEP-2 within DEEP-1 {100*(d2[d1]).mean():.1f}%   DEEP-1 within DEEP-2 {100*(d1[d2]).mean():.1f}%")
