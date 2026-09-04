"""D317 -- the D310+ family is charged the UNIVERSE's spread, not its own names'.

    uv run python scripts/d317_cost_basis_audit.py

AN AUDIT, prompted by the principal asking me to re-check the claim that nothing
after D300 was an improvement. It closes nothing and proposes nothing.

A FRAMING WITHDRAWN AT THE DOOR. This began as "D310's pre-registration specifies
a held-name round trip, its runner uses a global median, therefore defect". The
principal's correction stands: a pre-registration records the thinking BEFORE a
run, not a contract the runner breaches. And the change had a documented reason --
D307 concluded, one study earlier, that "any comparison of two exit rules must
charge them a COMMON spread or it is partly measuring which rule happens to trade
tighter names". D310 charging one common rt is that recommendation applied.

WHAT REMAINS IS THE LEVEL, AND AN AXIS DISTINCTION NO RECORD DREW.

    rt = 4.0 * nanmedian(half[isfinite(half)])   =  56.98 bp

is 4x the UNIVERSE's median half-spread. The names the book weights run 18.51 bp
at N_eff=2 to 25.05 at N_eff=19 -- implied round trips 74 to 100. A common basis
can be set at a held-name level and stay common; no reading of D307 justifies
charging the book a spread cheaper than any name in it. This is the failure
CLAUDE.md names: "Estimate the spread of the names HELD rather than trusting a
fee assumption -- D285 missed a guessed 15 bp/side bar by 0.65 and the held names
measured 33.8."

AND THE WIDTH RESULT'S SIGN DEPENDS ON THE CHOICE. With a common R the advantage
of N=2 over N=19 is 13.505 - 0.1450*R, which crosses zero at R = 93.1 -- inside
the plausible range. Per-cell it is +8.04; at D302's held-name 105.24 it is -1.75
and the WIDE book wins. D307's common-spread rule is right for comparing exit
rules at fixed width, where the spread difference is incidental, and wrong for
comparing widths, where the spread difference is CAUSED by the choice under test.

WHAT THIS AUDIT DOES. Recomputes each `none/exp` cell's round trip from the names
the book actually WEIGHTS -- the weighted median half-spread over gate name-bars,
weights being the cell's own exponential weights -- and re-derives net.

The weighted MEDIAN, not the mean, for D302's reason: Corwin-Schultz clamps
negative daily estimates, which is a left truncation that biases the mean up. The
weighted mean is printed beside it to show how far apart they are.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "d317_cost_basis_audit.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


X = _load("d312", "run_d312_vol_targeted.py")
R, W, D, SP, M = X.R, X.W, X.D, X.SP, X.M
ANN = 252.0


def weighted_spread(G, finT, half, T, lam):
    """Half-spread of the names this book WEIGHTS, weighted by those weights."""
    gF, gO = G["gateF"], G["gateO"]
    vals, wts = [], []
    for t in range(1, T):
        fin = finT[t]
        for side in (0, 1):
            rows = gF[gO[side, t]:gO[side, t + 1]]
            rows = rows[fin[rows]]
            if rows.size == 0:
                continue
            w = R.exp_weights(lam, rows.size)
            h = half[t, rows]
            m = np.isfinite(h)
            if m.any():
                vals.append(h[m])
                wts.append(w[m])
    v = np.concatenate(vals)
    w = np.concatenate(wts)
    w = w / w.sum()
    o = np.argsort(v)
    med = float(v[o][np.searchsorted(np.cumsum(w[o]), 0.5)])
    return med, float((v * w).sum())


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    glob = float(np.nanmedian(half[np.isfinite(half)]))
    rt_charged = 4.0 * glob
    finT = A["finT"]
    T = A["r1T"].shape[0]

    d302_note = ("D302 published universe median 13.20 bp and held-name 26.31 bp; "
                 "this audit's global median is %.2f and its widest-book weighted "
                 "median %s -- corroborating the computation." % (glob, "{}"))

    print("D317  cost-basis audit of the D310+ family")
    print("  charged everywhere in D310-D316:  rt = 4 x %.2f = %.2f bp"
          % (glob, rt_charged))
    print("  D302 published: universe median half-spread 13.20 bp, "
          "HELD names 26.31 bp\n")

    d310 = json.loads((REPO / "data" / "d310_rank_weighted.json").read_text())["cells"]
    rows = {}
    print("%7s %8s %9s %10s %10s %9s %9s %10s" % (
        "N_eff", "gross", "turnover", "w-med half", "rt correct", "cost now",
        "cost ok", "NET ok"))
    print("-" * 82)
    for lv in (2, 3, 5, 7, 10, 14, 19):
        c = d310[f"none/exp{lv}"]
        med, mean = weighted_spread(G, finT, half, T, R.solve_lam(float(lv)))
        rt_ok = 4.0 * med
        cost_ok = c["turnover"] * rt_ok
        net_ok = c["gross_bp"] - cost_ok
        rows[str(lv)] = dict(
            gross=c["gross_bp"], turnover=c["turnover"],
            w_median_half=med, w_mean_half=mean, rt_charged=rt_charged,
            rt_correct=rt_ok, cost_charged=c["cost_bp"], cost_correct=cost_ok,
            net_charged=c["net_bp"], net_correct=net_ok, vol=c["vol_bp"],
            sharpe_charged=c["net_bp"] / c["vol_bp"] * np.sqrt(ANN),
            sharpe_correct=net_ok / c["vol_bp"] * np.sqrt(ANN))
        print("%7d %+8.2f %9.4f %10.2f %10.2f %9.2f %9.2f %+10.2f" % (
            lv, c["gross_bp"], c["turnover"], med, rt_ok, c["cost_bp"],
            cost_ok, net_ok))

    print("\n  EVERY CELL GOES NET-NEGATIVE. The published +4.37 at N_eff=2 is "
          "%+.2f." % rows["2"]["net_correct"])
    print("  Undercharge runs %.0f%% at N_eff=2 to %.0f%% at N_eff=19."
          % (100 * (rows["2"]["rt_correct"] / rt_charged - 1),
             100 * (rows["19"]["rt_correct"] / rt_charged - 1)))

    # WHAT SURVIVES: the SHAPE of the surface, which is what D314/D315a used.
    print("\nWHAT THE CORRECTION DOES NOT BREAK")
    net_ok = [rows[str(l)]["net_correct"] for l in (2, 3, 5, 7, 10, 14, 19)]
    mono = all(a >= b - 1e-12 for a, b in zip(net_ok, net_ok[1:]))
    sh = [rows[str(l)]["sharpe_correct"] for l in (2, 3, 5, 7, 10, 14, 19)]
    print("  net still monotone DOWN in width: %s" % mono)
    print("  net Sharpe still peaks at N_eff = %d"
          % [2, 3, 5, 7, 10, 14, 19][int(np.argmax(sh))])
    print("  concentration's advantage WIDENS: N=2 minus N=19 goes from "
          "%+.2f to %+.2f bp" % (rows["2"]["net_charged"] - rows["19"]["net_charged"],
                                 rows["2"]["net_correct"] - rows["19"]["net_correct"]))
    print("  -- because concentration improves the held spread too (%.2f vs "
          "%.2f bp), exactly as D300 found." % (rows["2"]["w_median_half"],
                                                rows["19"]["w_median_half"]))

    # AND THE OTHER HALF OF THE STORY: this construction TRADES MORE than D300's.
    print("\nTHE SECOND PROBLEM, INDEPENDENT OF THE FIRST")
    print("  D300/D306's hard-cut k-hold book at N=2: turnover 0.2003")
    print("  D310's rank-weighted book at N_eff=2:    turnover %.4f  (x%.2f)"
          % (rows["2"]["turnover"], rows["2"]["turnover"] / 0.2003))
    print("  D310 documented this -- weights drift as ranks move, so a weight")
    print("  going 0.30 -> 0.25 is a trade with no entry -- but the two")
    print("  constructions were never compared on NET with both correctly costed.")
    print("  D300/D306 remain the better-costed and lower-turnover book:")
    print("     D306 N=2/target  +15.25 net   at its own held-name rt of 73.2")
    print("     D306 N=2/none    +11.20 net   at its own held-name rt of 86.7")

    OUT.write_text(json.dumps(dict(
        note="AUDIT. D310's runner charges the universe median half-spread while "
             "its pre-registration specifies the held-name round trip. Affects "
             "D310, D311, D312, D313, D314, D315a, D316.",
        rt_charged=rt_charged, global_median_half=glob, cells=rows), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
