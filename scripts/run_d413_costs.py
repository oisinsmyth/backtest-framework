"""D413 COSTS -- the number that decides whether any of the rest matters.

    uv run python scripts/run_d413_costs.py --run

EXPLORATORY. Clears nothing and changes no verdict. But CLAUDE.md's reporting standard is not
optional and D413's record twice said this had not been done:

  "Estimate the spread of the names HELD (Corwin-Schultz off the OHLC) rather than trusting a fee
   assumption -- D285 missed a guessed 15 bp/side bar by 0.65 and the held names measured 33.8."

D413's diagnostics found the edge is MONOTONE DECREASING IN PRICE -- +33.6 bp in the cheapest
quintile against +6.1 bp in the dearest. Cost in bp scales INVERSELY with price. That is the D284
shape exactly, and it means the gross edge is largest precisely where it is most expensive to take.
So the cost estimate is not a formality here; it is the question.

The estimator is D285's own `corwin_schultz`, imported rather than reimplemented.

COMMISSION is IBKR's published US equity tiered rate, $0.0035/share. The $0.35 minimum and the 1%
-of-trade-value cap are NOT modelled, because order size is not modelled -- so the commission here
is a FLOOR on the true commission for small orders, and that is stated rather than smoothed over.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413", REPO / "scripts" / "run_d413_distance_armed_zones.py")
M = importlib.util.module_from_spec(_s)
sys.modules["d413"] = M
_s.loader.exec_module(M)
Z4, D = M.Z4, M.D

_c = importlib.util.spec_from_file_location("d285cs", REPO / "scripts" / "d285_spread_estimate.py")
CS = importlib.util.module_from_spec(_c)
sys.modules["d285cs"] = CS
_c.loader.exec_module(CS)

OUT = REPO / "data" / "d413_costs.json"
IBKR_PER_SHARE = 0.0035


def run():
    t0 = time.time()
    print("D413 COSTS -- Corwin-Schultz on the names actually held\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g, tt = A["Z"], A["good"], A["tt"]

    # D285's estimator wants (n_symbols, T). The panel here is (T, n_symbols).
    s_nT = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T)
    spread = s_nT.T                                   # proportional ROUND-TRIP spread, per bar

    r = A["r"][g]
    ii = Z["i"][g]
    te = tt[g]                                        # entry bar: the touch
    tx = np.minimum(te + M.H, P["CL"].shape[0] - 1)   # exit bar
    px_in = P["CL"][te, ii]
    px_out = P["CL"][tx, ii]

    s_in, s_out = spread[te, ii], spread[tx, ii]
    ok = np.isfinite(s_in) & np.isfinite(s_out) & np.isfinite(px_in) & (px_in > 0)
    print(f"  events {r.size:,}   with a usable spread estimate at BOTH bars {int(ok.sum()):,} "
          f"({100*ok.mean():.1f}%)")

    r, ii, px_in, px_out = r[ok], ii[ok], px_in[ok], px_out[ok]
    s_in, s_out = s_in[ok], s_out[ok]

    # Crossing costs HALF the quoted spread each way; a round trip crosses twice.
    spread_cost = 0.5 * s_in + 0.5 * s_out
    comm = IBKR_PER_SHARE / px_in + IBKR_PER_SHARE / px_out
    total = spread_cost + comm
    net = r - total

    def bp(x):
        return 1e4 * float(np.mean(x))

    print(f"\n  --- per trade, in bp ---")
    print(f"  GROSS                     {bp(r):+8.2f}")
    print(f"  spread (Corwin-Schultz)   {-bp(spread_cost):+8.2f}   "
          f"(one-way median {1e4*np.median(0.5*s_in):.1f} bp)")
    print(f"  commission (IBKR floor)   {-bp(comm):+8.2f}")
    print(f"  NET                       {bp(net):+8.2f}   "
          f"+-{1e4*net.std(ddof=1)/np.sqrt(net.size):.2f}")
    print(f"  breakeven round-trip cost {bp(r):.2f} bp; actual {bp(total):.2f} bp  ->  "
          f"coverage {bp(r)/bp(total):.2f}x")

    # Corwin-Schultz floors each negative daily estimate at zero (the authors' convention), which
    # truncates the noise on one side only and biases the MEAN upward. The median is the more
    # honest central estimate of the typical cost, so both are reported and neither is chosen.
    med_total = float(np.median(total))
    med_gross = float(np.median(r))
    print(f"  MEDIAN round-trip cost    {1e4*med_total:8.2f} bp  vs a median gross of "
          f"{1e4*med_gross:+.2f}  ->  coverage on medians {med_gross/med_total:.2f}x")
    print(f"  (the zero-floor in Corwin-Schultz biases the MEAN cost upward; the truth is "
          f"between these two, and both are short)")

    res = dict(n=int(r.size), gross_bp=bp(r), spread_bp=bp(spread_cost), comm_bp=bp(comm),
               total_bp=bp(total), net_bp=bp(net),
               net_se_bp=float(1e4 * net.std(ddof=1) / np.sqrt(net.size)),
               coverage=float(bp(r) / bp(total)),
               spread_oneway_median_bp=float(1e4 * np.median(0.5 * s_in)))

    print(f"\n  --- by PRICE quintile: the D284 tension, measured ---")
    q = np.quantile(px_in, np.linspace(0, 1, 6))
    q[-1] += 1e-9
    b = np.clip(np.searchsorted(q, px_in, side="right") - 1, 0, 4)
    rows = []
    for j in range(5):
        m = b == j
        rows.append(dict(n=int(m.sum()), price=float(np.median(px_in[m])),
                         gross=bp(r[m]), cost=bp(total[m]), net=bp(net[m]),
                         net_se=float(1e4 * net[m].std(ddof=1) / np.sqrt(m.sum()))))
        w = rows[-1]
        print(f"  ${w['price']:6.1f}   n {w['n']:7,}   gross {w['gross']:+7.2f}   "
              f"cost {w['cost']:6.2f}   NET {w['net']:+7.2f} +-{w['net_se']:.2f} bp")
    res["by_price"] = rows

    print(f"\n  --- the same, on the two filters the diagnostics pointed at ---")
    age = (A["idx"] + 1)[g][ok].astype(float)
    for tag, m in (("age >= 3 bars (drops the losing youngest tercile)", age >= 3),
                   ("age >= 3 AND price >= $20", (age >= 3) & (px_in >= 20)),
                   ("price >= $20 only", px_in >= 20)):
        if m.sum() < 1000:
            continue
        se = float(1e4 * net[m].std(ddof=1) / np.sqrt(m.sum()))
        print(f"  {tag:52s}  n {int(m.sum()):7,}  gross {bp(r[m]):+7.2f}  "
              f"NET {bp(net[m]):+7.2f} +-{se:.2f} bp  ({bp(net[m])/se:+.1f} SE)")
        res[f"filter_{tag[:20]}"] = dict(n=int(m.sum()), gross=bp(r[m]), net=bp(net[m]), se=se)

    OUT.write_text(json.dumps(dict(exploratory=True, **res), indent=1, default=float),
                   encoding="utf-8")
    print(f"\n  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
