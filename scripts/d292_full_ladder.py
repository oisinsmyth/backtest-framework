"""D292 -- the FULL ladder: every book's own number, not just the differences.

    uv run python scripts/d292_full_ladder.py

The result record reported t1, t2 and t_min -- all DIFFERENCES against parents.
It almost never reported what each book actually earns on its own, which is the
first thing anyone wants and the thing that makes the differences readable.

Four rungs, each at close entry and open entry:

    hist_L alone       N=25, k=5, no filter at all          (D290's tier-1 cell)
    parent B1          hist_L filtered by B1 only
    parent B2          hist_L filtered by B2 only
    third order        hist_L filtered by both

Each rung is reported as its OWN spread return and its OWN t -- the same
statistic D290 ranked candidates on -- so the four are directly comparable, and
the paired differences on top of them can be read as what they are.

Parents are rebuilt at the third-order cell's own per-bar count, exactly as the
runner does, so the four rungs differ ONLY in what selects the names.
"""

from __future__ import annotations

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
OUT = REPO / "data" / "d292_full_ladder.json"


def own(sums):
    """A book's OWN spread bp and t -- not a difference against anything."""
    m = (sums[1] > 0) & (sums[3] > 0)
    if int(m.sum()) < M.MIN_BARS:
        return None
    d = sums[0][m] / sums[1][m] - sums[2][m] / sums[3][m]
    sd = d.std(ddof=1)
    if sd == 0:
        return None
    return dict(bp=float(d.mean() * 1e4),
                t=float(d.mean() / (sd / np.sqrt(d.size))),
                bars=int(d.size), held=float(sums[1][sums[1] > 0].mean()))


def main() -> int:
    res = json.loads((REPO / "data" / "d292_third_order.json").read_text())
    rows_in = [r for r in res["rows"] if r["screen"] or r["promote"]]

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    N, k = res["N"], res["k"]
    fwd = {"close": M.forward_returns(panel, live)[k]}
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fwd["open"] = ET.open_entry(on, idr, live, (k,))[k]

    order_a, cnt_a, _ = R.ranked(z[D.PRIMARY], base)
    plan = R.LegPlan(order_a, cnt_a, N, T)
    pcts = {}
    for b in D.PARTNERS:
        _, cb, pb = R.ranked(z[b], base)
        pcts[b] = (R.pct_at(pb, cb, plan.lo, plan.cols),
                   R.pct_at(pb, cb, plan.hi, plan.cols))

    ones_lo = np.ones(plan.lo.shape, dtype=bool)
    ones_hi = np.ones(plan.hi.shape, dtype=bool)
    solo = {e: own(R.spread_sums(fwd[e], plan, ones_lo, ones_hi, T))
            for e in ("close", "open")}
    print(f"D292 FULL LADDER   A = {D.PRIMARY}   N = {N}   k = {k}\n")
    print(f"  RUNG 0 -- {D.PRIMARY} ALONE, no filter, all {N} names:")
    for e in ("close", "open"):
        s = solo[e]
        print(f"    {e + ' entry':12s}  {s['bp']:+8.2f} bp   t {s['t']:+5.2f}   "
              f"{s['bars']:,} bars")

    out = []
    for r in rows_in:
        b1, b2, opn, f = r["B1"], r["B2"], r["op"], r["f"]
        p1, p2 = pcts[b1], pcts[b2]
        klo, khi = D.OPS[opn](p1[0], p1[1], p2[0], p2[1], f, N)
        m1lo, m1hi = D.parent_masks(p1[0], p1[1], klo, khi)
        m2lo, m2hi = D.parent_masks(p2[0], p2[1], klo, khi)
        rec = dict(B1=b1, B2=b2, op=opn, f=f, void=r["void"],
                   promote=r["promote"], t_min_close=r["t_min"])
        print(f"\n{'=' * 76}")
        print(f"  {b1} + {b2}   {opn}  f={f:.2f}"
              + ("   [VOID by the turnover audit]" if r["void"] else ""))
        print(f"{'=' * 76}")
        print(f"    {'rung':22s} {'entry':6s} | {'held':>5s} {'bp':>9s} "
              f"{'own t':>7s} | {'vs parent':>10s}")
        for e in ("close", "open"):
            fk = fwd[e]
            # THE RUNG THE PRE-REGISTRATION LEFT OUT. Its control was the
            # parents, on the ground that D291 had already answered "does the
            # stack beat hist_L alone". But D291 tested SINGLE filters; the
            # MEAN-RANK operator did not exist there, so nothing has ever
            # compared it to the primary. N' is hist_L's own top names at the
            # third order's count, so the two differ only in what selects them.
            npr = max(1, int(round(float(klo.sum(axis=0).mean()))))
            p2plan = R.LegPlan(order_a, cnt_a, npr, T)
            o2lo = np.ones(p2plan.lo.shape, dtype=bool)
            o2hi = np.ones(p2plan.hi.shape, dtype=bool)
            books = {
                f"{D.PRIMARY} alone": R.spread_sums(fk, plan, ones_lo, ones_hi, T),
                f"{D.PRIMARY} at N'={npr}": R.spread_sums(fk, p2plan, o2lo, o2hi, T),
                f"+ {b1}": R.spread_sums(fk, plan, m1lo, m1hi, T),
                f"+ {b2}": R.spread_sums(fk, plan, m2lo, m2hi, T),
                f"+ both": R.spread_sums(fk, plan, klo, khi, T)}
            third = books["+ both"]
            for nm, bk in books.items():
                s = own(bk)
                if s is None:
                    continue
                diff = ""
                if nm.endswith(f"N'={npr}"):
                    st = R.paired_t(third[0], third[1], bk[0], bk[1],
                                    third[2], third[3], bk[2], bk[3])
                    if st:
                        diff = f"t {st[1]:+.2f}"
                        rec[f"{e}_t_vs_primary"] = st[1]
                        rec[f"{e}_bp_vs_primary"] = st[0]
                if nm.startswith("+ ") and nm != "+ both":
                    st = R.paired_t(third[0], third[1], bk[0], bk[1],
                                    third[2], third[3], bk[2], bk[3])
                    if st:
                        diff = f"t {st[1]:+.2f}"
                        rec[f"{e}_t_vs_{'B1' if nm.endswith(b1) else 'B2'}"] = st[1]
                print(f"    {nm:22s} {e:6s} | {s['held']:5.1f} {s['bp']:+9.2f} "
                      f"{s['t']:+7.2f} | {diff:>10s}")
                rec[f"{e}_{nm.replace('+ ', '').replace(' ', '_')}"] = s
            print()
        out.append(rec)

    json.dump({"purpose": "D292: each rung's OWN spread return and t, close and "
                          "open entry, so the paired differences can be read "
                          "against the levels they were computed from.",
               "solo": solo, "N": N, "k": k, "rows": out},
              open(OUT, "w"), indent=1)
    print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
