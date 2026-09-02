"""D285 follow-up -- is the edge SEPARABLE from the spread, or are they the same thing?

    uv run python scripts/d285_edge_vs_spread.py

NOTHING HERE SCORES A CELL AND D285 IS NOT REOPENED. Its stop clause forbids
bolting a filter on after the fact, and this does not propose one. It answers a
prior question: **could ANY selectivity filter work on this book, or is the edge
the spread?**

WHY THE QUESTION IS NOT ALREADY ANSWERED, AND WHY IT NEARLY IS. D285
pre-registered a filter -- universe B, entry close >= $5 -- and it made things
WORSE: breakeven fell 14.35 -> 12.63 bp/side and the book's advantage over its
volatility-matched control collapsed from +0.493 to -0.036 gross Sharpe. That is
prediction F4, declared against the construction, and it held at all three N.

**But price is a PROXY for spread, and a bad one.** A direct test asks whether
the edge survives inside the names that are actually cheap to trade. If it does,
a successor with a spread-based screen would be worth pre-registering. If the
edge rises monotonically with the spread, the two are one quantity and the whole
line is closed -- not by my judgement, and not by one filter's failure.

THE TEST
========
Every trade the book took, tagged with the estimated half-spread of its name at
ENTRY (Corwin-Schultz, as in `d285_spread_estimate.py`), then bucketed by spread
quintile of the qualifying universe. For each bucket:

    move per trade          what the trade made, bp
    2 x est. half-spread    what crossing costs, round trip, bp
    move - cost             THE ONLY COLUMN THAT MATTERS

**A bucket with a positive final column is a subset worth pre-registering. If
none is positive, no filter on this axis can rescue the book**, and the
inference is about the strategy rather than about the threshold I happened to
pick.

Trades are tagged with a 21-BAR TRAILING mean of the estimate -- the only form a
screen could use at entry. See the comment above the bucketing for the two
rejected alternatives and why the forward-looking one produced a spectacular and
false q1.

THE ESTIMATOR IS THE WEAK LINK AND THE CONCLUSION IS CONDITIONAL ON IT.
Corwin-Schultz is upward-biased when a day's range carries overnight movement,
which is exactly this population. Its tightest quintile reads 25.21 bp/side on a
$32.67 median stock -- about 8 cents -- and that is far too wide for anything
genuinely liquid. **So the shortfall reported for q1 is an upper bound on the
true one, and this file cannot by itself close the line.** Settling it needs
quote data the fixture does not carry.
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
P1 = _load("d280p1", "d280_forecast_precheck.py")
FN = _load("d285", "run_factor_neutral.py")
SP = _load("d285sp", "d285_spread_estimate.py")
RP = B.RP

OUT = REPO / "data" / "d285_edge_vs_spread.json"
N = 10


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FN.FEE)
    g = P1.build_grids(panel, cleaned)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4   # bp per side
    # THE TRAILING ESTIMATE IS THE ONLY IMPLEMENTABLE ONE. A screen applied at
    # entry may use bars STRICTLY BEFORE the entry bar. The window mean -- the
    # average over a trade's own holding period -- is forward-looking and cannot
    # be screened on, which is exactly the class of error that destroyed D279's
    # first result. Both are computed; only the trailing one may gate a book.
    LOOKBACK = 21
    trail = np.full_like(half, np.nan)
    for k in range(1, LOOKBACK + 1):
        src = np.where(np.isfinite(half), half, 0.0)
        cnt = np.isfinite(half).astype(float)
        if k == 1:
            acc = np.zeros_like(half); num = np.zeros_like(half)
        acc[:, k:] += src[:, :-k]
        num[:, k:] += cnt[:, :-k]
    trail = np.where(num > 0, acc / np.maximum(num, 1.0), np.nan)
    print(f"loaded {time.time() - t0:.0f}s", flush=True)

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & live
    base = np.where(ok, 1.0, 0.0)
    base[:, 0] = 0.0
    pos = RP.enforce_live(FN.neutral_book(base, hs, N), panel, 0)
    simple = np.expm1(panel.total_log_returns)

    # walk episodes exactly as `FN.episode_moves` does -- split on entry, exit
    # and sign change -- but keep the entry bar so each trade can be tagged.
    moves, entry_spread, win_spread, trail_spread, price, run = [], [], [], [], [], []
    n, T = pos.shape
    for i in range(n):
        row = pos[i]
        t = 0
        while t < T:
            if row[t] == 0.0:
                t += 1
                continue
            sgn, t0_ = row[t], t
            acc = 0.0
            while t < T and row[t] == sgn:
                r = simple[i, t]
                if np.isfinite(r):
                    acc += sgn * r
                t += 1
            w = half[i, t0_:t]
            w = w[np.isfinite(w)]
            if not np.isfinite(trail[i, t0_]) or w.size == 0:
                continue
            moves.append(acc * 1e4)
            entry_spread.append(float(half[i, t0_]) if np.isfinite(half[i, t0_]) else 0.0)
            win_spread.append(float(w.mean()))
            trail_spread.append(float(trail[i, t0_]))
            price.append(float(g["close"][i, t0_]))
            run.append(t - t0_)

    m = np.array(moves)
    es = np.array(entry_spread)
    ws = np.array(win_spread)
    ts = np.array(trail_spread)
    px = np.array(price)
    print(f"  {m.size:,} trades tagged with an entry-bar spread estimate\n", flush=True)

    # BUCKET AND COST ON THE TRAILING ESTIMATE, AND ON NOTHING ELSE.
    #
    # Two rejected alternatives, both recorded because each was tried:
    #   ENTRY BAR ALONE is implementable but 41% of estimates clip to zero, so
    #   three quintile cuts land on the same value and q1/q2/q3 collapse.
    #   THE WINDOW MEAN is stable and is the better cost proxy -- a trade pays
    #   the spread at both ends of a ~6-bar hold -- but it averages over the
    #   trade's OWN HOLDING PERIOD and is therefore FORWARD-LOOKING. Bucketing
    #   on it selects trades using information the screen would not have, which
    #   is the class of error that destroyed D279's first result. It produced a
    #   spectacular q1 (+240 bp net) and that number is an artefact.
    #
    # The trailing mean is stable AND available at entry, so it is the only one
    # a real screen could use. It is used for the buckets and for the cost.
    zero_share = float((es == 0.0).mean())
    print(f"  entry-bar estimates clipped to zero: {zero_share:.1%}; bucketing and "
          f"costing on a\n  {LOOKBACK}-bar TRAILING mean, the only estimate "
          f"available at entry.\n")
    qs = np.percentile(ts, [20, 40, 60, 80])
    buckets = np.digitize(ts, qs)
    rows = {}
    print(f"  {'spread quintile':18s} {'est. half-sp':>13s} {'move/trade':>11s} "
          f"{'2x spread':>10s} {'MOVE - COST':>12s} {'med px':>8s} {'trades':>8s}")
    for b in range(5):
        s = buckets == b
        if s.sum() < 100:
            continue
        mv, cost = float(m[s].mean()), 2.0 * float(ts[s].mean())
        rows[f"q{b + 1}"] = {"n": int(s.sum()), "half_spread_bp": float(ts[s].mean()),
                             "window_mean_half_spread_bp": float(ws[s].mean()),
                             "move_bp": mv, "round_trip_cost_bp": cost,
                             "net_bp": mv - cost, "median_price": float(np.median(px[s])),
                             "median_move_bp": float(np.median(m[s]))}
        print(f"  q{b + 1} {'(tightest)' if b == 0 else '(widest)' if b == 4 else '':13s} "
              f"{ts[s].mean():13.2f} {mv:11.2f} {cost:10.2f} {mv - cost:+12.2f} "
              f"{np.median(px[s]):8.2f} {int(s.sum()):8,d}")

    pos_b = [k for k, v in rows.items() if v["net_bp"] > 0]
    print(f"\n  buckets where the move covers the estimated spread: {pos_b or 'NONE'}")
    if not pos_b:
        print(f"\n  NO SUBSET ON THIS AXIS IS TRADEABLE. The edge does not sit inside the")
        print(f"  names that are cheap to trade, so no spread or liquidity screen can")
        print(f"  rescue the book -- the inference is about the strategy, not about the")
        print(f"  15 bp threshold I picked, and not about universe B's one failure.")
    else:
        print(f"\n  A tradeable subset EXISTS on this axis. D285 still fails as")
        print(f"  pre-registered -- that is not reopened -- but a successor screening on")
        print(f"  ESTIMATED SPREAD rather than price would be worth pre-registering, and")
        print(f"  would need its own out-of-sample test and its own multiplicity.")

    corr = float(np.corrcoef(ts, m)[0, 1])
    print(f"\n  corr(entry half-spread, trade move) = {corr:+.4f}   "
          f"positive means the edge IS the spread")
    json.dump({"purpose": ("does the D285 book's edge survive inside cheap-to-trade "
                           "names? scores no cell, reopens no verdict"),
               "n_trades": int(m.size), "corr_spread_move": corr,
               "buckets": rows, "tradeable_buckets": pos_b,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
