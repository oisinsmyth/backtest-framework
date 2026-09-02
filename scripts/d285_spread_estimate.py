"""D285 follow-up -- was the 15 bp/side bar in the right place? Measured, not argued.

    uv run python scripts/d285_spread_estimate.py

NOTHING HERE SCORES A CELL, AND D285'S VERDICT IS NOT REOPENED. `A_nofloor|book10`
broke even at 14.35 bp/side against a floor of 15 declared BEFORE the run and
failed. That stands, and the 0.65 bp gap is not to be argued away -- the whole
point of a pre-registered threshold is that a near miss cannot relitigate it.

WHAT IS OPEN IS A DIFFERENT QUESTION. **Was 15 bp/side the right bar?** I chose
it as a judgement -- "a book of low-priced just-fallen names will not trade at a
tighter spread than that in size" -- and a judgement is checkable. The answer
decides something real: whether this LINE is dead, or whether a future study on
it would be worth pre-registering.

**It is answered with an estimator, not an opinion.** The fixture is daily
OHLCV, so the effective spread of the names actually held can be estimated
directly.

CORWIN-SCHULTZ (2012), the high-low estimator
==============================================
Two adjacent days' high-low ranges carry both volatility and spread; the
volatility part scales with the interval and the spread part does not, so two
equations in two unknowns separate them.

    beta  = E[ (ln(H_t/L_t))^2 + (ln(H_t+1/L_t+1))^2 ]
    gamma = ( ln( max(H_t,H_t+1) / min(L_t,L_t+1) ) )^2
    alpha = (sqrt(2*beta) - sqrt(beta)) / (3 - 2*sqrt(2))
            - sqrt( gamma / (3 - 2*sqrt(2)) )
    S     = 2 * (exp(alpha) - 1) / (1 + exp(alpha))          proportional, ROUND TRIP

Negative daily estimates are set to zero, which is the authors' own convention:
the estimator is noisy day by day and unbiased only in the mean.

**S is a ROUND-TRIP proportional spread, so the comparable quantity is S/2** --
`breakeven_bps` is charged per side.

WHAT IS REPORTED
================
The holdings-weighted half-spread of the names `A_nofloor|book10` ACTUALLY HELD,
on the bars it held them -- not a universe average, because the book does not
trade a universe average. Reported beside the universe figure so the selection
effect is visible, and split by price bucket because D264 established that cost
in bp scales inversely with price.

WHAT WOULD MEAN WHAT, declared before the numbers are read:

  half-spread >> 14.35 bp   the bar was generous, the book was never tradeable,
                            and this line is closed on evidence rather than on
                            my judgement.
  half-spread ~ 14.35 bp    the bar was in about the right place and the study
                            failed on the right criterion.
  half-spread << 14.35 bp   MY THRESHOLD WAS WRONG. D285 still fails as
                            pre-registered -- that is not reopened -- but a
                            successor with a corrected bar would be worth
                            pre-registering, and this file is the reason why.

The estimator is itself an estimate, so its known biases are reported with it:
Corwin-Schultz is upward-biased when a day's range is inflated by overnight
moves and downward-biased for very illiquid names whose highs and lows sit
inside the quoted spread. Both are stated rather than corrected.
"""

from __future__ import annotations

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


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
FN = _load("d285", "run_factor_neutral.py")
RP = B.RP

OUT = REPO / "data" / "d285_spread_estimate.json"
BREAKEVEN = 14.351436126782723          # A_nofloor|book10, from the D285 summary
FLOOR = 15.0
SQ2 = 3.0 - 2.0 * np.sqrt(2.0)


def corwin_schultz(H, L, live):
    """Per-bar proportional ROUND-TRIP spread. NaN where the pair is unusable."""
    ok = live[:, :-1] & live[:, 1:] & np.isfinite(H[:, :-1]) & np.isfinite(H[:, 1:]) \
        & (L[:, :-1] > 0) & (L[:, 1:] > 0)
    h1, l1 = H[:, :-1], L[:, :-1]
    h2, l2 = H[:, 1:], L[:, 1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        b = np.log(h1 / l1) ** 2 + np.log(h2 / l2) ** 2
        g = np.log(np.maximum(h1, h2) / np.minimum(l1, l2)) ** 2
        a = (np.sqrt(2.0 * b) - np.sqrt(b)) / SQ2 - np.sqrt(g / SQ2)
        s = 2.0 * (np.expm1(a)) / (1.0 + np.exp(a))
    s = np.where(ok & np.isfinite(s), s, np.nan)
    # the authors' own convention: a negative daily estimate is set to zero
    s = np.where(np.isfinite(s), np.maximum(s, 0.0), np.nan)
    out = np.full(H.shape, np.nan)
    out[:, :-1] = s
    return out


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FN.FEE)
    g = P1.build_grids(panel, cleaned)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    print(f"loaded {time.time() - t0:.0f}s", flush=True)

    half = corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4    # bp PER SIDE
    fin = np.isfinite(half)
    print(f"  Corwin-Schultz computed on {int(fin.sum()):,} name-bars\n", flush=True)

    # the book D285 actually ran, rebuilt with the same seed and the same call
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & live
    base = np.where(ok, 1.0, 0.0)
    base[:, 0] = 0.0
    pos = FN.neutral_book(base, hs, 10)
    held = (RP.enforce_live(pos, panel, 0) != 0.0) & fin

    uni = half[fin & (base != 0.0)]
    bk = half[held]
    px = g["close"][held]
    rows = {}

    def show(label, v):
        if v.size < 100:
            print(f"  {label:30s} too few observations")
            return
        rows[label] = {"n": int(v.size), "mean": float(v.mean()),
                       "median": float(np.median(v)),
                       "p25": float(np.percentile(v, 25)),
                       "p75": float(np.percentile(v, 75))}
        print(f"  {label:30s} {v.mean():8.2f} {np.median(v):8.2f} "
              f"{np.percentile(v, 25):8.2f} {np.percentile(v, 75):8.2f} {v.size:11,d}")

    print(f"  ESTIMATED HALF-SPREAD, bp PER SIDE. Compare against the book's")
    print(f"  breakeven of {BREAKEVEN:.2f} and the pre-registered floor of {FLOOR:.0f}.\n")
    print(f"  {'':30s} {'mean':>8s} {'median':>8s} {'p25':>8s} {'p75':>8s} {'obs':>11s}")
    show("qualifying universe", uni)
    show("HELD by A_nofloor|book10", bk)
    for lo, hi in ((0, 2), (2, 5), (5, 10), (10, 25), (25, 1e9)):
        m = held & (g["close"] >= lo) & (g["close"] < hi)
        show(f"  held, ${lo:g}-{hi:g}" if hi < 1e9 else f"  held, ${lo:g}+", half[m])

    w = float(np.mean(bk)) if bk.size else float("nan")
    print(f"\n  VERDICT ON THE BAR, not on the study:")
    print(f"    book breakeven                 {BREAKEVEN:8.2f} bp/side")
    print(f"    estimated half-spread, held    {w:8.2f} bp/side")
    print(f"    pre-registered floor           {FLOOR:8.2f} bp/side")
    if w > BREAKEVEN:
        print(f"\n    The estimate EXCEEDS the breakeven by {w - BREAKEVEN:.2f} bp/side.")
        print(f"    The book was never tradeable and the 15 bp floor was GENEROUS.")
        print(f"    This line closes on evidence rather than on my judgement.")
    else:
        print(f"\n    The estimate is BELOW the breakeven by {BREAKEVEN - w:.2f} bp/side.")
        print(f"    D285 STILL FAILS AS PRE-REGISTERED -- that is not reopened -- but")
        print(f"    the 15 bp floor was too strict, and a successor with a corrected")
        print(f"    bar would be worth pre-registering.")
    print(f"\n  Estimator caveats, stated rather than corrected: Corwin-Schultz is")
    print(f"  UPWARD-biased when a day's range is inflated by overnight moves, and")
    print(f"  DOWNWARD-biased for very illiquid names whose high and low sit inside")
    print(f"  the quoted spread. The second bias runs AGAINST the book.")

    json.dump({"purpose": ("estimates the effective spread of the names D285's "
                           "book actually held; scores no cell and does not "
                           "reopen D285's verdict"),
               "estimator": "Corwin-Schultz (2012) high-low, half-spread in bp",
               "book_breakeven_bps": BREAKEVEN, "preregistered_floor_bps": FLOOR,
               "held_mean_half_spread_bps": w, "rows": rows,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
