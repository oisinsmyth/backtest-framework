"""D442 ADDENDUM -- the enumerated rotation null on QQQ and DIA.

    uv run python scripts/d442_rot_extra.py

D442 enumerated ROT on the primary symbol only, exactly as its pre-registration said it would,
which left QQQ-static +192 and DIA-static +151 measured but UNCONTROLLED. Its §8 named closing
that as the cheapest open item the study created. This is that, and nothing else.

NOTHING NEW IS DECIDED HERE. Same gate, same theta, same seed, same paths, same days, same G2
test -- V must sit ABOVE the enumerated ROT p95. The only thing that changes is which symbol the
enumeration runs on. No threshold is swept and no arm is added.

THE PREDICTION, WRITTEN BEFORE THE RUN: both land INSIDE their p95 and G2 fails on both, because
the mechanism D442 found on SPY -- a real floor-touch reduction paid for with P&L -- is
symbol-independent. The honest caveat is that DIA carries the best ratio in the study
(touch -74.8% against P&L -32.1%), so if any cell clears it is that one.
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

OUT = REPO / "data" / "d442_rot_extra.json"

CELLS = [
    # symbol, rule, frac -- the V-maximising size D442 reported for the O1 arm
    ("QQQ", "static", 0.004),
    ("QQQ", "voltgt", 0.011),
    ("DIA", "static", 0.004),
    ("DIA", "voltgt", 0.011),
]
N_PATHS, DAYS = 8_000, 600


def main() -> int:
    h = pd.read_csv(D440.HOLDS_CSV)
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    rows = []

    print("D442 ADDENDUM -- enumerated rotations on QQQ and DIA\n")
    print(f"  theta {D442.THETA_PRIMARY}, seed {D442.SEED}, {N_PATHS:,} paths, {DAYS} days\n")

    for sym, rule, frac in CELLS:
        g = h[h["symbol"] == sym].reset_index(drop=True)
        r = g["d_end"].to_numpy(dtype=float)
        m = D442.gate_mask(r, D442.THETA_PRIMARY)

        base = D442.account(g, plan, frac, rule, N_PATHS, DAYS)["V"]
        treat = D442.account(D442.apply_mask(g, m), plan, frac, rule, N_PATHS, DAYS)["V"]
        rot = D442.rot_account(g, m, plan, frac, rule, N_PATHS, DAYS, every=1)

        blk = np.asarray([D442.account(D442.apply_mask(g, mm), plan, frac, rule,
                                       N_PATHS, DAYS)["V"]
                          for mm in D442.blkrand_masks(m, 200, D442.SEED)], dtype=float)

        up = treat > base
        clears = treat > rot["p95"]
        g2 = "PASS" if (up and clears) else "FAIL"
        pctile = float((np.asarray([rot["p05"], rot["p50"], rot["p95"]]) < treat).sum())

        print(f"  {sym} {rule} @ {100 * frac:.1f}%   BASE {base:>7,.0f}   O1 {treat:>7,.0f}"
              f"   dV {treat - base:>+7,.0f}")
        print(f"    ROT {rot['n_offsets']:,} offsets ENUMERATED:"
              f"  p05 {rot['p05']:>7,.0f}   p50 {rot['p50']:>7,.0f}"
              f"   p95 {rot['p95']:>7,.0f}   max {rot['max']:>8,.0f}")
        print(f"    BLKRAND 200 draws:               "
              f"  p05 {np.percentile(blk, 5):>7,.0f}   p50 {np.median(blk):>7,.0f}"
              f"   p95 {np.percentile(blk, 95):>7,.0f}")
        print(f"    G2 -> {g2}   ({'above' if clears else 'inside'} the enumerated p95)\n")

        rows.append({"symbol": sym, "rule": rule, "frac": frac, "V_base": base,
                     "V_treat": treat, "dV": treat - base, "G2": g2,
                     "rot_p05": rot["p05"], "rot_p50": rot["p50"], "rot_p95": rot["p95"],
                     "rot_max": rot["max"], "rot_offsets": rot["n_offsets"],
                     "rot_enumerated": rot["enumerated"],
                     "blk_p50": float(np.median(blk)),
                     "blk_p95": float(np.percentile(blk, 95)),
                     "above_rot_p95": bool(clears), "rank_markers": pctile})

    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"wrote {OUT.relative_to(REPO)}  ({len(rows)} cells)")
    n_pass = sum(1 for r in rows if r["G2"] == "PASS")
    print(f"\nG2 passes: {n_pass} of {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
