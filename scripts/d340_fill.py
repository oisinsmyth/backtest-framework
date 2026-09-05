"""D340 -- the next-open fill: `ocT` / `mkt_oc`, two second implementations and
the synthetic gap fixture. Imported by run_d340_open_fill.py.

    uv run python scripts/d340_fill.py          # selftest

`ocT[t, i] = close[t]/open[t] - 1` (price only) is what a position entered at
bar t earns under `W.simulate(..., fill="open")`; `mkt_oc[t]` is the equal-weight
open-to-close market over live names with a real open (>= 20 names, mirroring
`market_reference`). Where a priced name has no usable open on a bar, `ocT` falls
back to `r1T` there (a fill at the prior close) and the cell is counted.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


W = _load("d306", "run_d306_width_exits.py")
D, M = W.D, W.M


# ------------------------------------------------------------------ arrays
def open_fill_arrays(A, panel, g):
    """(ocT, mkt_oc, fallback_mask, report). ocT is (T, n) contiguous, finite on
    every priced cell; mkt_oc is (T,)."""
    O = np.asarray(g["open"], float)
    C = np.asarray(g["close"], float)
    live = np.asarray(panel.live, bool)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    n, T = live.shape
    assert r1T.shape == (T, n), f"r1T {r1T.shape} vs panel {(T, n)}"
    pc = np.asarray(panel.closes, float)
    same = live & np.isfinite(pc) & np.isfinite(C)
    assert np.array_equal(pc[same], C[same]), "grid close != panel.closes on live cells"
    good = live & np.isfinite(O) & (O > 0) & np.isfinite(C) & (C > 0)
    oc = np.full((n, T), np.nan)
    oc[good] = C[good] / O[good] - 1.0
    mkt_oc = D.L.market_reference(oc, live)
    ocT = np.ascontiguousarray(oc.T)
    fb = finT & ~np.isfinite(ocT)
    ocT[fb] = r1T[fb]
    assert np.isfinite(ocT[finT]).all(), "ocT not finite on a priced cell after the fallback"
    assert np.isfinite(mkt_oc)[np.isfinite(mkt)].all(), "mkt_oc missing on a bar where mkt exists"
    rows = np.flatnonzero(fb.any(axis=0))
    names = [panel.symbols[i] for i in rows]
    report = dict(fallback_cells=int(fb.sum()), priced_cells=int(finT.sum()),
                  fallback_frac=float(fb.sum()) / float(finT.sum()),
                  fallback_names=names, n_fallback_names=len(names),
                  mkt_oc_bars=int(np.isfinite(mkt_oc).sum()), mkt_bars=int(np.isfinite(mkt).sum()),
                  cells_with_open=int(good.sum()))
    return ocT, mkt_oc, fb, report


def with_open_fill(A, panel, g):
    """A plain dict copy of A carrying the two extra keys; the cache is untouched."""
    ocT, mkt_oc, fb, report = open_fill_arrays(A, panel, g)
    return dict(A, ocT=ocT, mkt_oc=mkt_oc), fb, report


# ----------------------------------------------- second implementations
def pnl_recomputed_fill(trades, r1T, mkt, ocT, mkt_oc, accumulate="sum"):
    """Every trade's P&L from (row, e0, age, side): the entry bar on ocT/mkt_oc,
    every later bar on r1T/mkt. With (r1T, mkt) passed for (ocT, mkt_oc) it is
    the close-fill ledger."""
    out = np.empty(len(trades))
    for i, (row, e0, age, _p, side) in enumerate(trades):
        sgn = 1.0 if side == 0 else -1.0
        v = np.array(r1T[e0:e0 + age, row], float)
        m = np.array(mkt[e0:e0 + age], float)
        v[0] = ocT[e0, row]
        m[0] = mkt_oc[e0]
        if accumulate == "sum":
            out[i] = sgn * float((v - m).sum())
        else:
            out[i] = sgn * (math.expm1(float(np.log1p(v).sum())) - float(m.sum()))
    return out


def contributions_fill(res, r1T, ocT):
    """d322_four_group_report.contributions with the entry bar spliced to ocT.
    Weight 1/n_t for the trade's OWN leg, zero off the book's mask -- copied,
    not imported, so the D322 module is not edited."""
    n = {0: np.asarray(res["cnt0"], float), 1: np.asarray(res["cnt1"], float)}
    m = res["mask"].astype(float)
    w = {s: np.where(n[s] > 0, 1.0 / np.maximum(n[s], 1), 0.0) * m for s in (0, 1)}
    out = np.empty(len(res["trades"]))
    for i, (row, e0, age, _pnl, side) in enumerate(res["trades"]):
        sgn = 1.0 if side == 0 else -1.0
        sl = slice(e0, e0 + age)
        v = np.nan_to_num(r1T[sl, row], nan=0.0)
        o0 = float(ocT[e0, row])
        v[0] = o0 if np.isfinite(o0) else 0.0
        out[i] = sgn * float(np.dot(v, w[side][sl]))
    return out


# ------------------------------------------------------------ synthetic [G]
def synthetic_gap_case(W_=None, Y_=None):
    """T=3, n=2. Name 0 gaps +50% at the open of bar 1 and is flat open->close
    (r1T=+0.50, ocT=0.0); name 1 gaps -50% flat. The market gaps +1% and is flat
    (mkt[1]=+0.01, mkt_oc[1]=0.0). Long name 0, short name 1, entered at bar 1,
    k=1, no target. Returns what the two fills book."""
    W_ = W_ or W
    if Y_ is None:
        Y_ = _load("d323_syn", "run_d323_shortlist_at_operating_point.py")
    T, n, NB = 3, 2, W_.N_BASE
    r1T = np.zeros((T, n))
    r1T[1] = [0.50, -0.50]
    ocT = np.zeros((T, n))
    mkt = np.array([0.0, 0.01, 0.0])
    mkt_oc = np.zeros(T)
    vxT = np.full((T, n), 0.1)
    finT = np.ones((T, n), bool)
    rankT = np.full((2, T, n), NB, np.int32)      # NB = outside the gate
    rankT[0, 1, 0] = 0                             # long side, bar 1, name 0
    rankT[1, 1, 1] = 0                             # short side, bar 1, name 1
    A_syn = dict(r1T=r1T, mkt=mkt, vxT=vxT, finT=finT, rankT=rankT, ocT=ocT, mkt_oc=mkt_oc)
    gate = Y_.gate_from(rankT, finT)
    saved = W_.BASE_HOLD
    try:
        W_.BASE_HOLD = 1
        rc = W_.simulate(A_syn, gate, 1, False)
        ro = W_.simulate(A_syn, gate, 1, False, fill="open")
    finally:
        W_.BASE_HOLD = saved

    def by_side(res):
        assert len(res["trades"]) == 2, res["trades"]
        return {int(t[4]): float(t[3]) for t in res["trades"]}
    return dict(close=by_side(rc), open=by_side(ro),
                expect_close={0: 0.49, 1: 0.51}, expect_open={0: 0.0, 1: 0.0},
                entries_close=int(rc["ent"].sum()), entries_open=int(ro["ent"].sum()))


def check_gap_case(G):
    for s in (0, 1):
        assert abs(G["close"][s] - G["expect_close"][s]) < 1e-12, f"[G] close fill side {s}: {G['close'][s]}"
        assert G["open"][s] == 0.0, f"[G] open fill side {s}: {G['open'][s]!r}"
    assert G["entries_close"] == 2 and G["entries_open"] == 2, "[G] entries"


# ------------------------------------------------------------------ selftest
def selftest():
    import time
    t0 = time.time()
    print("D340  fill helper -- selftest")
    G = synthetic_gap_case()
    check_gap_case(G)
    print(f"    [G] synthetic gap: close fill books long {G['close'][0]:+.2f} / short {G['close'][1]:+.2f}; "
          f"open fill books {G['open'][0]:+.1f} / {G['open'][1]:+.1f}")

    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G_ = W.build_gate(A, verbose=False)
    r1T, mkt = np.asarray(A["r1T"]), np.asarray(A["mkt"])
    res = W.simulate(A, G_, 2, True)
    pnl = np.array([t[3] for t in res["trades"]])
    rec = pnl_recomputed_fill(res["trades"], r1T, mkt, r1T, mkt)
    worst = float(np.abs(rec - pnl).max())
    assert worst < 1e-12, f"[P] close-fill self-check {worst:.2e}"
    G22 = _load("d322_selftest", "d322_four_group_report.py")
    c0 = G22.contributions(res, r1T)
    c1 = contributions_fill(res, r1T, r1T)
    assert np.array_equal(c0, c1), "[2] contributions_fill(r1T, r1T) != d322.contributions"
    print(f"    [P] pnl_recomputed_fill with (r1T, mkt) reproduces the close-fill ledger to {worst:.1e} "
          f"on {len(pnl):,} trades; contributions_fill(res, r1T, r1T) == d322.contributions bitwise "
          f"({time.time() - t0:.0f}s)")

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    A2, fb, rep = with_open_fill(A, panel, g)
    print(f"    [F] fallback {rep['fallback_cells']:,} of {rep['priced_cells']:,} priced cells "
          f"({100 * rep['fallback_frac']:.3f}%), {rep['n_fallback_names']} names; mkt_oc on "
          f"{rep['mkt_oc_bars']:,} bars vs mkt on {rep['mkt_bars']:,}")
    r2 = W.simulate(A2, G_, 2, True)
    assert np.array_equal(np.nan_to_num(r2["book"], nan=-9e9), np.nan_to_num(res["book"], nan=-9e9))
    assert r2["trades"] == res["trades"], "[ID](c) the extra keys moved the close-fill ledger"
    ro = W.simulate(A2, G_, 2, True, fill="open")
    assert not np.array_equal(np.nan_to_num(ro["book"], nan=-9e9), np.nan_to_num(res["book"], nan=-9e9))
    reco = pnl_recomputed_fill(ro["trades"], r1T, mkt, A2["ocT"], A2["mkt_oc"])
    worst_o = float(np.abs(reco - np.array([t[3] for t in ro["trades"]])).max())
    assert worst_o < 1e-12, f"[P] open-fill {worst_o:.2e}"
    print(f"    [ID] close fill bit-identical with the extra keys; open fill differs; open-fill ledger "
          f"recomputed to {worst_o:.1e} on {len(ro['trades']):,} trades")
    print(f"\nOK  d340_fill selftest passes ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
