"""D442 ADDENDUM 2 -- the SELECTION-HONEST rotation null on the two cells that passed.

    uv run python scripts/d442_rot_bestofn.py

THE DEFECT THIS REPAIRS, AND IT IS MINE. Addendum 1 compared a treatment whose risk fraction was
chosen as the ARGMAX OVER FOUR grid points against a null evaluated at ONE FIXED fraction. The
treatment therefore carried a best-of-4 advantage the null was never given. That is
FINDINGS.md section 59 in miniature -- a floor that prices one draw is blind to selection across
several -- and the margins it has to survive are thin: 23% on QQQ, 46% on DIA.

THE REPAIR. Every rotation offset is now scored the way the treatment was: V at all four risk
fractions, then the MAX. The null becomes the distribution of best-of-4, which is the same
statistic the treatment reports.

THE ASYMMETRY, STATED SO THE SCOPE IS CLEAR: a more lenient null can only turn a PASS into a
FAIL, never the reverse. D442's headline verdict on SPY was a FAIL and is untouched by this. Only
addendum 1's two passes are at risk, and they are the only cells run here.

PREDICTION, WRITTEN BEFORE THE RUN: the best-of-4 p95 rises enough to swallow QQQ (margin 23%)
and DIA survives (margin 46%). If both fall, O1's apparent wins were selection and the D442
verdict stands unqualified on all four symbols.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import d386_full_lifecycle as D386          # noqa: E402
import d440_lifecycle as D440               # noqa: E402
import d442_abstention as D442              # noqa: E402

OUT = REPO / "data" / "d442_rot_bestofn.json"
CELLS = [("QQQ", "static"), ("DIA", "static")]
N_PATHS, DAYS = 8_000, 600


def main() -> int:
    h = pd.read_csv(D440.HOLDS_CSV)
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    rows = []
    print("D442 ADDENDUM 2 -- selection-honest rotation null\n")
    print(f"  every offset scored at all {len(D386.RISK_FRACS)} risk fractions, then MAX --"
          f" the same statistic the treatment reports\n")

    for sym, rule in CELLS:
        g = h[h["symbol"] == sym].reset_index(drop=True)
        r = g["d_end"].to_numpy(dtype=float)
        m = D442.gate_mask(r, D442.THETA_PRIMARY)
        n = len(m)
        idx = np.arange(n)

        # the treatment, scored as best-of-4 -- unchanged from D442
        t_row = [D442.account(D442.apply_mask(g, m), plan, f, rule, N_PATHS, DAYS)["V"]
                 for f in D386.RISK_FRACS]
        treat = max(t_row)
        f_star = D386.RISK_FRACS[int(np.argmax(t_row))]

        # the null, scored the SAME way
        best = np.empty(n - 1)
        fixed = np.empty(n - 1)
        for j, off in enumerate(range(1, n)):
            mm = m[(idx - off) % n]
            gm = D442.apply_mask(g, mm)
            vs = [D442.account(gm, plan, f, rule, N_PATHS, DAYS)["V"]
                  for f in D386.RISK_FRACS]
            best[j] = max(vs)
            fixed[j] = vs[D386.RISK_FRACS.index(f_star)]

        p95_best = float(np.percentile(best, 95))
        p95_fixed = float(np.percentile(fixed, 95))
        clears = treat > p95_best
        print(f"  {sym} {rule}   treatment {treat:>7,.0f}  (argmax at {100 * f_star:.1f}%)")
        print(f"    null at the FIXED fraction   p50 {np.median(fixed):>7,.0f}"
              f"   p95 {p95_fixed:>7,.0f}   <- addendum 1 used this")
        print(f"    null as BEST-OF-{len(D386.RISK_FRACS)}        p50 {np.median(best):>7,.0f}"
              f"   p95 {p95_best:>7,.0f}   max {best.max():>8,.0f}")
        print(f"    the selection premium the null was denied: "
              f"{p95_best - p95_fixed:>+7,.0f}")
        print(f"    G2 -> {'PASS' if clears else 'FAIL'}"
              f"   ({'above' if clears else 'inside'} the selection-honest p95)\n")

        rows.append({"symbol": sym, "rule": rule, "treatment": treat, "f_star": f_star,
                     "p50_fixed": float(np.median(fixed)), "p95_fixed": p95_fixed,
                     "p50_best": float(np.median(best)), "p95_best": p95_best,
                     "max_best": float(best.max()),
                     "selection_premium": p95_best - p95_fixed,
                     "G2_selection_honest": "PASS" if clears else "FAIL",
                     "n_offsets": n - 1})

    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"wrote {OUT.relative_to(REPO)}")
    print(f"\nG2 passes under the selection-honest null: "
          f"{sum(1 for r in rows if r['G2_selection_honest'] == 'PASS')} of {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
