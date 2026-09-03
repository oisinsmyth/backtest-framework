"""D292 -- the rotate-B null ACROSS N. Is the profile content, or is it shape?

    uv run python scripts/d292_null_across_n.py [--draws 200] [--workers 6]

POST-HOC AND DISCLOSED, and the criterion below is fixed before the numbers
exist. Stage 1: spends nothing, reads no holdout, promotes nothing.

WHAT IT TESTS. `d292_n_stability.py` showed the combined book's own open-entry t
sits above +1.3 at every N in [15,40] while the primary it filters is a spike,
and that the improvement is LARGEST where the primary is WEAKEST (corr -0.74).
That is a shape across a parameter. Nothing has tested whether a partner with no
content would draw the same shape -- D292's nulls exist only at N=25.

THREE NULLS, because they answer different things:

  rot B1     B1 content-free, B2 real
  rot B2     B2 content-free, B1 real
  ROT BOTH   both content-free -- hist_L filtered by two partners of the right
             SHAPE and no CONTENT. This is the one the question actually asks,
             and D292 never ran it at any N.

THE STATISTIC IS THE PROFILE, NOT A CELL. Adjacent N share nearly all their
names, so 26 values of N are perhaps 3-5 independent observations and counting
"26 of 26 positive" would be counting the same fact repeatedly. Instead:

    per draw:   the MEDIAN improvement t across N in [15,40]
    observed:   the same median, from the real partners

so one number summarises the whole profile and the null draws it the same way.

THE CRITERION, FIXED HERE.

  PASS   the observed median-across-N improvement exceeds the 95th percentile of
         the ROT BOTH null, AND exceeds it for the weaker of the two single
         rotations. Beating only the single rotations would show one partner
         carries content, not that the pair does.
  FAIL   anything else. In particular, if ROT BOTH reproduces the profile, the
         shape is the operator's and not the partners'.

Reported whatever the answer: the per-N null bands, so the profile can be seen
against what chance draws rather than against zero.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
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
R, M, FN = D.R, D.M, D.FN
OUT = REPO / "data" / "d292_null_across_n.json"
SEED = 20260903
NULLS = ("rot_B1", "rot_B2", "rot_both")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--lo", type=int, default=15)
    ap.add_argument("--hi", type=int, default=40)
    a = ap.parse_args()
    t0 = time.time()

    res = json.loads((REPO / "data" / "d292_third_order.json").read_text())
    cells = [(r["B1"], r["B2"], r["op"], r["f"])
             for r in res["rows"] if r["screen"] or r["promote"]]
    k = res["k"]

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fk = ET.open_entry(on, idr, live, (k,))[k]          # OPEN ENTRY, as 1e requires

    order_a, cnt_a, _ = R.ranked(z[D.PRIMARY], base)
    Ns = list(range(a.lo, a.hi + 1))
    plans = {N: R.LegPlan(order_a, cnt_a, N, T) for N in Ns}
    prim = {}
    for N in Ns:
        pl = plans[N]
        prim[N] = R.spread_sums(fk, pl, np.ones(pl.lo.shape, bool),
                                np.ones(pl.hi.shape, bool), T)
    Rp = {b: R.ranked(z[b], base) for b in D.PARTNERS}
    pct_real = {(b, N): (R.pct_at(Rp[b][2], Rp[b][1], plans[N].lo, plans[N].cols),
                         R.pct_at(Rp[b][2], Rp[b][1], plans[N].hi, plans[N].cols))
                for b in D.PARTNERS for N in Ns}
    rp = R.rotate_plan(live)
    print(f"loaded | {len(cells)} cells x {len(Ns)} N x {len(NULLS)} nulls x "
          f"{a.draws} draws   ({time.time() - t0:.0f}s)", flush=True)

    def improvement(p1, p2, opn, f, N):
        pl = plans[N]
        klo, khi = D.OPS[opn](p1[0], p1[1], p2[0], p2[1], f, N)
        if not klo.any() or not khi.any():
            return None
        both = R.spread_sums(fk, pl, klo, khi, T)
        c = prim[N]
        st = R.paired_t(both[0], both[1], c[0], c[1], both[2], both[3], c[2], c[3])
        return None if st is None else st[1]

    obs = {}
    for ci, (b1, b2, opn, f) in enumerate(cells):
        obs[ci] = [improvement(pct_real[(b1, N)], pct_real[(b2, N)], opn, f, N)
                   for N in Ns]

    def one_draw(key, draw):
        rot = {}
        for bi, b in enumerate(D.PARTNERS):
            rng = np.random.default_rng(SEED + 131 * bi + 7919 * draw)
            off = rng.integers(1, T, size=live.shape[0])
            cnt_r, pos_r = R.ranked_pos(R.rotate(z[b], rp, off), base)
            for N in Ns:
                pl = plans[N]
                rot[(b, N)] = (R.pct_at(pos_r, cnt_r, pl.lo, pl.cols),
                               R.pct_at(pos_r, cnt_r, pl.hi, pl.cols))
        out = {}
        for ci, (b1, b2, opn, f) in enumerate(cells):
            for nm in NULLS:
                vals = []
                for N in Ns:
                    p1 = rot[(b1, N)] if nm in ("rot_B1", "rot_both") else pct_real[(b1, N)]
                    p2 = rot[(b2, N)] if nm in ("rot_B2", "rot_both") else pct_real[(b2, N)]
                    vals.append(improvement(p1, p2, opn, f, N))
                v = [x for x in vals if x is not None]
                out[(ci, nm)] = float(np.median(v)) if v else None
        return out

    print(f"  {a.draws} draws, {a.workers} threads", flush=True)
    nres = FN.parallel_map(one_draw, [(d, d) for d in range(a.draws)],
                           workers=a.workers)
    dist = {(ci, nm): [] for ci in range(len(cells)) for nm in NULLS}
    for d, out in nres.items():
        for kk, v in out.items():
            if v is not None:
                dist[kk].append(v)

    print(f"\n  MEDIAN IMPROVEMENT t ACROSS N in [{a.lo}, {a.hi}], open entry\n")
    rows = []
    for ci, (b1, b2, opn, f) in enumerate(cells):
        o = [x for x in obs[ci] if x is not None]
        omed = float(np.median(o))
        print(f"  {b1} + {b2}   {opn}  f={f:.2f}")
        print(f"    observed median across N : {omed:+.3f}")
        verdict = {}
        for nm in NULLS:
            arr = np.array(dist[(ci, nm)])
            p95 = float(np.percentile(arr, 95))
            p = float((arr >= omed).sum() + 1) / (arr.size + 1)
            verdict[nm] = omed > p95
            print(f"    {nm:9s} null: p50 {np.percentile(arr, 50):+.3f}  "
                  f"p95 {p95:+.3f}  max {arr.max():+.3f}  | p = {p:.4f}  "
                  f"{'BEATS' if omed > p95 else 'no'}")
        weaker_single = verdict["rot_B1"] and verdict["rot_B2"]
        pas = verdict["rot_both"] and weaker_single
        print(f"    -> {'PASS' if pas else 'FAIL'}"
              f"   (rot_both {'beaten' if verdict['rot_both'] else 'NOT beaten'};"
              f" both singles {'beaten' if weaker_single else 'not both beaten'})\n")
        rows.append(dict(B1=b1, B2=b2, op=opn, f=f, obs_median=omed,
                         per_N=obs[ci],
                         nulls={nm: dict(p50=float(np.percentile(dist[(ci, nm)], 50)),
                                         p95=float(np.percentile(dist[(ci, nm)], 95)),
                                         max=float(max(dist[(ci, nm)])),
                                         p=float((np.array(dist[(ci, nm)]) >= omed).sum() + 1)
                                         / (len(dist[(ci, nm)]) + 1),
                                         beaten=bool(verdict[nm]))
                                for nm in NULLS},
                         **{"pass": pas}))

    npass = sum(1 for r in rows if r["pass"])
    print(f"  {npass} of {len(rows)} cells PASS the pre-committed criterion")
    json.dump({"purpose": "D292 post-hoc: the rotate-B null across N. Is the "
                          "broad positive profile the partners' content or the "
                          "operator's shape?",
               "criterion": "observed median-across-N improvement must exceed "
                            "the p95 of the ROT BOTH null and of both single "
                            "rotations",
               "N_range": [a.lo, a.hi], "draws": a.draws, "k": k,
               "entry": "open", "rows": rows}, open(OUT, "w"), indent=1)
    print(f"  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
