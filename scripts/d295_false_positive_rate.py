"""D295 -- re-scored on the STAGE-APPROPRIATE bar, with the false-positive count.

    uv run python scripts/d295_false_positive_rate.py

The pre-registration's four conditions included a best-of-19 family-wise floor
and a cost-coverage gate. Both are PROMOTION instruments and this stage promotes
nothing: the mined fixture is not spent, no holdout is read, and the question is
which cells to carry rather than which to certify. Applying them here is the
error the principal corrected on D291 and which this study repeated.

Re-scored on "beats its own rate- and persistence-matched null", with the
question that actually matters at a screen: HOW MANY OF THESE ARE NOISE?

  - the naive count at p < 0.05, and how many are expected by luck
  - the count tested against the NULL'S OWN correlated structure, because 19
    cells sharing one base book are nowhere near 19 independent tests
  - Benjamini-Hochberg, which bounds the proportion of the shortlist that is
    false -- the right instrument when the cost of a false positive is one more
    candidate carried forward

Cost is REPORTED and does not gate. It is a stage-3 question and this is stage 2.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d295_false_positive_rate.json"


def main() -> int:
    res = json.loads((REPO / "data" / "d295_exits.json").read_text())
    rows = {r["cell"]: r for r in res["rows"] if r["cell"] != "B0"}

    dist = {}
    for f in sorted((REPO / "temp").glob("d295_null_*.json")):
        for key, dd in json.loads(f.read_text()).items():
            dist.setdefault(key, []).extend(dd.values())
    dist = {k: np.array(v) for k, v in dist.items() if k in rows}
    ndraw = min(len(v) for v in dist.values())
    print(f"{len(dist)} cells, {ndraw} matched null draws each\n")

    def emp_p(arr, v):
        return float((arr >= v).sum() + 1) / (arr.size + 1)

    for k, r in rows.items():
        r["p"] = emp_p(dist[k], r["d_bp"])

    order = sorted(rows.values(), key=lambda r: r["p"])
    print("RE-SCORED ON ITS OWN NULL ALONE  (cost reported, NOT gating)\n")
    print(f"  {'cell':10s} {'D bp/bar':>9s} {'D t':>6s} {'p':>7s} | "
          f"{'turn':>6s} {'cost/bar':>9s} | {'run w/l':>8s} | screen")
    for r in order:
        print(f"  {r['cell']:10s} {r['d_bp']:+9.2f} {r['d_t']:+6.2f} "
              f"{r['p']:7.4f} | {r['turnover']:6.1%} "
              f"{r['cost_bar_robust']:9.2f} | "
              f"{(f'{r[chr(114)+chr(117)+chr(110)+chr(95)+chr(114)+chr(97)+chr(116)+chr(105)+chr(111)]:8.2f}' if r['run_ratio'] else '      --')} | "
              f"{'YES' if r['p'] < 0.05 else 'no'}")

    m = len(order)
    nsig = sum(1 for r in order if r["p"] < 0.05)
    print(f"\n  cells at p < 0.05        : {nsig} of {m}")
    print(f"  expected by luck (0.05m) : {0.05 * m:.2f}")

    # the count, against the null's OWN correlated structure -- 19 cells sharing
    # one base book are nowhere near 19 independent tests
    keys = list(dist)
    cnt_null = []
    for d in range(ndraw):
        c = 0
        for k in keys:
            other = np.delete(dist[k], d)
            if emp_p(other, dist[k][d]) < 0.05:
                c += 1
        cnt_null.append(c)
    cnt_null = np.array(cnt_null)
    print(f"\n  THE COUNT, against the null's own correlation structure:")
    print(f"    observed                 : {nsig}")
    print(f"    null p50 / p95 / max     : {np.percentile(cnt_null, 50):.0f} / "
          f"{np.percentile(cnt_null, 95):.0f} / {cnt_null.max()}")
    print(f"    naive binomial sd        : {np.sqrt(m * 0.05 * 0.95):.2f}")
    print(f"    ACTUAL null sd           : {cnt_null.std(ddof=1):.2f}  "
          f"({cnt_null.std(ddof=1) / np.sqrt(m * 0.05 * 0.95):.1f}x the binomial)")
    print(f"    P(null count >= observed): {(cnt_null >= nsig).mean():.1%}")

    # Benjamini-Hochberg: what fraction of the shortlist is false?
    ps = np.sort(np.array([r["p"] for r in order]))
    print(f"\n  BENJAMINI-HOCHBERG -- the shortlist question")
    print(f"    finest p expressible with {ndraw} draws: {1 / (ndraw + 1):.4f}")
    bh = {}
    for q in (0.05, 0.10, 0.20, 0.50):
        thr = np.arange(1, m + 1) / m * q
        below = np.flatnonzero(ps <= thr)
        bh[q] = int(below.max() + 1) if below.size else 0
        print(f"    q = {q:4.2f} -> keep {bh[q]:2d} cells")
    if nsig:
        print(f"\n    naive shortlist of {nsig} carries ~{0.05 * m:.2f} expected "
              f"false -> {0.05 * m / nsig:.0%} of it is noise")

    json.dump({"purpose": "D295 re-scored on its own null alone, with the "
                          "false-positive arithmetic. The pre-registered floor "
                          "and cost gate are promotion instruments and this "
                          "stage promotes nothing.",
               "draws": int(ndraw), "n_cells": m, "n_sig": nsig,
               "expected_by_luck": 0.05 * m,
               "count_null_p50": float(np.percentile(cnt_null, 50)),
               "count_null_p95": float(np.percentile(cnt_null, 95)),
               "count_null_max": int(cnt_null.max()),
               "p_count": float((cnt_null >= nsig).mean()),
               "bh": {str(k): v for k, v in bh.items()},
               "rows": [{k: r[k] for k in
                         ("cell", "rule", "param", "d_bp", "d_t", "p",
                          "turnover", "cost_bar_robust", "run_ratio",
                          "run_win", "run_lose", "trade_median", "win_rate")}
                        for r in order]}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
