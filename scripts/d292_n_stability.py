"""D292 -- does the third-order improvement survive where the primary's edge does not?

    uv run python scripts/d292_n_stability.py [--lo 15] [--hi 40]

POST-HOC AND DISCLOSED. Not pre-registered as a cell; it varies the ONE
parameter D291 and D292 both inherited and never questioned. Stage 1, spends
nothing, reads no holdout.

THE FINDING THAT PROMPTED IT. `hist_L` alone at k=5 has close t of -0.88 at
N=10, +0.53 at 19, +2.00 at 23, +2.86 at 25, +2.02 at 30 and +1.01 at 50. Its
edge lives in a window of N in [23,30]. D290's grid was {3,5,10,25,50}: it
contained the spike and neither neighbour, so a spike looked like a peak. Every
D291 and D292 number is conditioned on N=25.

THE CRITERION, FIXED HERE BEFORE THE NUMBERS EXIST.

  INHERITED   the improvement tracks the primary's own N profile. Measured as
              corr( primary_t(N), improvement_t(N) ) over the sweep. High
              positive correlation means the combination is riding the same
              spike and adds nothing of its own.
  ROBUST      the improvement is positive across most of the range INCLUDING
              where the primary is weak (N <= 21, primary t < +1). A real
              combination should be LESS knife-edge than its primary, not more.

Both readings are reported for every cell whatever the numbers say. The
improvement is measured two ways because they are different questions:

  vs PRIMARY at N    does the filtered book beat the unfiltered one it came from?
  vs PRIMARY at N'   ... at the same book size, so the comparison is selection
                     and not concentration.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
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


D = _load("d292", "run_d292_third_order.py")
ET = _load("d290et", "d290_entry_test.py")
R, M = D.R, D.M
OUT = REPO / "data" / "d292_n_stability.json"


def own(s):
    m = (s[1] > 0) & (s[3] > 0)
    if int(m.sum()) < M.MIN_BARS:
        return None
    d = s[0][m] / s[1][m] - s[2][m] / s[3][m]
    sd = d.std(ddof=1)
    if sd == 0:
        return None
    return float(d.mean() * 1e4), float(d.mean() / (sd / np.sqrt(d.size)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo", type=int, default=15)
    ap.add_argument("--hi", type=int, default=40)
    a = ap.parse_args()

    res = json.loads((REPO / "data" / "d292_third_order.json").read_text())
    cells = [(r["B1"], r["B2"], r["op"], r["f"])
             for r in res["rows"] if r["screen"] or r["promote"]]
    k = res["k"]

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    fwd = {"close": M.forward_returns(panel, live)[k]}
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fwd["open"] = ET.open_entry(on, idr, live, (k,))[k]

    order_a, cnt_a, _ = R.ranked(z[D.PRIMARY], base)
    Rp = {b: R.ranked(z[b], base) for b in D.PARTNERS}
    Ns = list(range(a.lo, a.hi + 1))

    print(f"D292 N-STABILITY   A = {D.PRIMARY}   k = {k}   N in "
          f"[{a.lo}, {a.hi}]   entry = open unless stated\n")

    out = []
    for (b1, b2, opn, f) in cells:
        rowsN = []
        for N in Ns:
            plan = R.LegPlan(order_a, cnt_a, N, T)
            if plan.cols.size == 0:
                continue
            p = {b: (R.pct_at(Rp[b][2], Rp[b][1], plan.lo, plan.cols),
                     R.pct_at(Rp[b][2], Rp[b][1], plan.hi, plan.cols))
                 for b in (b1, b2)}
            klo, khi = D.OPS[opn](p[b1][0], p[b1][1], p[b2][0], p[b2][1], f, N)
            if not klo.any() or not khi.any():
                continue
            npr = max(1, int(round(float(klo.sum(axis=0).mean()))))
            plan2 = R.LegPlan(order_a, cnt_a, npr, T)
            o1 = np.ones(plan.lo.shape, bool)
            o1h = np.ones(plan.hi.shape, bool)
            o2 = np.ones(plan2.lo.shape, bool)
            o2h = np.ones(plan2.hi.shape, bool)
            rec = {"N": N, "npr": npr}
            for e in ("close", "open"):
                fk = fwd[e]
                prim = R.spread_sums(fk, plan, o1, o1h, T)
                primN = R.spread_sums(fk, plan2, o2, o2h, T)
                both = R.spread_sums(fk, plan, klo, khi, T)
                sp, sb = own(prim), own(both)
                if sp is None or sb is None:
                    continue
                rec[f"{e}_primary_t"] = sp[1]
                rec[f"{e}_primary_bp"] = sp[0]
                rec[f"{e}_both_t"] = sb[1]
                rec[f"{e}_both_bp"] = sb[0]
                for tag, ctrl in (("vsN", prim), ("vsNp", primN)):
                    st = R.paired_t(both[0], both[1], ctrl[0], ctrl[1],
                                    both[2], both[3], ctrl[2], ctrl[3])
                    rec[f"{e}_imp_{tag}_t"] = None if st is None else st[1]
            rowsN.append(rec)

        pt = np.array([r.get("open_primary_t", np.nan) for r in rowsN], float)
        bt = np.array([r.get("open_both_t", np.nan) for r in rowsN], float)
        im = np.array([r.get("open_imp_vsN_t", np.nan) for r in rowsN], float)
        imp = np.array([r.get("open_imp_vsNp_t", np.nan) for r in rowsN], float)
        ok = np.isfinite(pt) & np.isfinite(im)
        corr = float(np.corrcoef(pt[ok], im[ok])[0, 1]) if ok.sum() > 3 else None
        weak = ok & (pt < 1.0)
        print(f"{'=' * 90}")
        print(f"  {b1} + {b2}   {opn}  f={f:.2f}")
        print(f"{'=' * 90}")
        print(f"    {'N':>3s} {'held':>4s} | {'prim t':>7s} {'both t':>7s} | "
              f"{'imp vs N':>9s} {'imp vs N-prime':>14s} | {'prim bp':>8s} "
              f"{'both bp':>8s}")
        for r in rowsN:
            if r["N"] % 2 and r["N"] not in (25, 15, 40):
                continue
            star = "  <- D292 cell" if r["N"] == 25 else ""
            print(f"    {r['N']:3d} {r['npr']:4d} | "
                  f"{D.fmt(r.get('open_primary_t'), 7)} "
                  f"{D.fmt(r.get('open_both_t'), 7)} | "
                  f"{D.fmt(r.get('open_imp_vsN_t'), 9)} "
                  f"{D.fmt(r.get('open_imp_vsNp_t'), 14)} | "
                  f"{D.fmt(r.get('open_primary_bp'), 8, 1)} "
                  f"{D.fmt(r.get('open_both_bp'), 8, 1)}{star}")
        print(f"\n    corr(primary t, improvement t) over N = "
              f"{(f'{corr:+.2f}' if corr is not None else '--')}"
              f"    -> {'INHERITED' if (corr or 0) > 0.5 else 'independent of the primary'}")
        print(f"    improvement vs N   : positive on {int((im[ok] > 0).sum())}/"
              f"{int(ok.sum())} of N | where primary is WEAK (t<1): "
              f"{int((im[weak] > 0).sum())}/{int(weak.sum())}")
        print(f"    both-book own t    : p50 {np.nanmedian(bt):+.2f}  "
              f"max {np.nanmax(bt):+.2f}  |  primary own t: p50 "
              f"{np.nanmedian(pt):+.2f}  max {np.nanmax(pt):+.2f}")
        print(f"    improvement vs N'  : positive on "
              f"{int((imp[np.isfinite(imp)] > 0).sum())}/"
              f"{int(np.isfinite(imp).sum())} of N\n")
        out.append(dict(B1=b1, B2=b2, op=opn, f=f, corr_open=corr, rows=rowsN))

    json.dump({"purpose": "D292 post-hoc: whether the third-order improvement "
                          "survives across N, where hist_L's own edge is a "
                          "spike at N in [23,30].",
               "primary": D.PRIMARY, "k": k, "N_range": [a.lo, a.hi],
               "cells": out}, open(OUT, "w"), indent=1)
    print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
