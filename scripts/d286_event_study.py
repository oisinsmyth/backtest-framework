"""D286 follow-up -- the signal's raw response, with NO portfolio in the way.

    uv run python scripts/d286_event_study.py

NOTHING HERE SCORES A CELL, AND IT IS NOT A BOOK. Overlapping events are taken
deliberately, so this could not be traded with finite capital. It measures the
SIGNAL; every prior study measured the signal AND a portfolio construction
welded to it.

WHY THE CONSTRUCTION HAS BEEN CONTAMINATING EVERY NUMBER
=========================================================
A top-N book has a FIXED NUMBER OF SLOTS, so an exit does not merely end a
trade -- **it forces an entry.** Exit earlier and the slot refills sooner, from
a noisier part of the ranking, and that fresh position exits sooner in turn. The
construction manufactures its own churn, and no statistic computed on it can
separate "the signal is weak" from "the slots are thrashing".

D286 is the case in point. `cap` cut losers correctly -- +360 bp per touched
trade -- and made the book WORSE. `sig` held 3.3x longer and earned LESS per
trade. Both are statements about a slotted book, not about `hist_L`.

WHAT AN EVENT IS
================
A name ENTERS the bottom N (long side) or the top N (short side) of the
R9-lagged score, having not been there on the previous bar. That is a fresh
signal firing. **Every one is taken, whether or not anything else is open**, so
there are no slots to compete for and no exit is ever caused by another name.

WHAT IS REPORTED
================
The cumulative forward return from the event, bar by bar to `MAX_H`, for each
side and for the LONG-MINUS-SHORT spread -- the signal's response function. The
horizon at which the spread peaks is the answer D286 could not give: **how long
the edge actually lasts, free of slot churn.**

THE OVERLAP IS DISCLOSED, because D271 was wrong about exactly this. Counting
overlapping windows as independent trades turned 13,752 observations into 43,204
and a `t` of 2.31 into 5.30. Events here overlap by construction, so the count,
the mean events per bar and the implied overlap are all reported, and **the
t-statistics are computed ACROSS BARS -- one observation per bar, not per
event** -- which is the same correction D280 part 3 used for its ICs.
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
RP = B.RP

OUT = REPO / "data" / "d286_event_study.json"
N_LEVELS = (10, 25, 50)
MAX_H = 40


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    logr = panel.total_log_returns
    s = C.lag1(hs)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & live
    T = live.shape[1]
    print(f"loaded {time.time() - t0:.0f}s", flush=True)

    # forward CUMULATIVE simple return from bar t through t+k-1, within the
    # symbol's own live window -- the same quantity a position entered at the
    # close of t-1 and held k bars would earn.
    fwd = {}
    acc = np.zeros_like(logr)
    okk = live.copy()
    for k in range(1, MAX_H + 1):
        acc[:, :T - k + 1] += logr[:, k - 1:]
        okk[:, :T - k + 1] &= live[:, k - 1:]
        fwd[k] = np.where(okk, np.expm1(acc), np.nan)

    results = {}
    for N in N_LEVELS:
        inlo = np.zeros((live.shape[0], T), dtype=bool)
        inhi = np.zeros((live.shape[0], T), dtype=bool)
        for t in range(T):
            q = np.flatnonzero(ok[:, t])
            v = s[q, t]
            fin = np.isfinite(v)
            q, v = q[fin], v[fin]
            if q.size < 2 * N:
                continue
            o = np.argsort(v, kind="stable")
            inlo[q[o[:N]], t] = True
            inhi[q[o[-N:]], t] = True
        # a FRESH entry: in the extreme now, not on the previous bar
        ev_lo = inlo.copy()
        ev_hi = inhi.copy()
        ev_lo[:, 1:] &= ~inlo[:, :-1]
        ev_hi[:, 1:] &= ~inhi[:, :-1]

        n_lo, n_hi = int(ev_lo.sum()), int(ev_hi.sum())
        bars = int((inlo.any(axis=0)).sum())
        print(f"\n  N={N}: {n_lo:,} long events, {n_hi:,} short events over "
              f"{bars:,} bars", flush=True)
        print(f"        mean concurrent holds if never exited: "
              f"{n_lo / max(bars, 1):.1f}/bar entering, {N} slots in the book -- "
              f"the overlap the book cannot take")

        rows = {}
        print(f"\n  {'k':>4s} {'long bp':>9s} {'short bp':>9s} {'spread bp':>10s} "
              f"{'per bar':>8s} {'t (bars)':>9s}")
        for k in (1, 2, 3, 5, 8, 10, 13, 16, 20, 25, 30, 40):
            if k > MAX_H:
                continue
            f = fwd[k]
            # ONE OBSERVATION PER BAR, averaged across that bar's events, so the
            # t-statistic is not inflated by overlapping windows (D271).
            per_bar = []
            lo_v, hi_v = [], []
            for t in range(T):
                a = f[ev_lo[:, t], t]
                b = f[ev_hi[:, t], t]
                a = a[np.isfinite(a)]
                b = b[np.isfinite(b)]
                if a.size == 0 or b.size == 0:
                    continue
                per_bar.append(a.mean() - b.mean())
                lo_v.append(a.mean())
                hi_v.append(b.mean())
            if len(per_bar) < 100:
                continue
            arr = np.array(per_bar)
            tt = float(arr.mean() / (arr.std(ddof=1) / np.sqrt(arr.size)))
            rows[k] = {"long_bp": float(np.mean(lo_v) * 1e4),
                       "short_bp": float(np.mean(hi_v) * 1e4),
                       "spread_bp": float(arr.mean() * 1e4),
                       "spread_bp_per_bar": float(arr.mean() * 1e4 / k),
                       "t": tt, "bars": int(arr.size)}
            print(f"  {k:4d} {np.mean(lo_v) * 1e4:+9.1f} {np.mean(hi_v) * 1e4:+9.1f} "
                  f"{arr.mean() * 1e4:+10.1f} {arr.mean() * 1e4 / k:+8.2f} {tt:+9.2f}",
                  flush=True)

        best = max(rows, key=lambda k: rows[k]["spread_bp"]) if rows else None
        results[N] = {"n_long_events": n_lo, "n_short_events": n_hi,
                      "bars": bars, "horizons": rows, "peak_horizon": best}
        if best:
            print(f"\n    PEAK CUMULATIVE SPREAD at k={best}: "
                  f"{rows[best]['spread_bp']:+.1f} bp "
                  f"(t {rows[best]['t']:+.2f})")
            print(f"    D286's book held {6.24 if N == 10 else 7.07 if N == 25 else 7.77:.2f} "
                  f"bars on `disp` and {20.70 if N == 10 else 20.43 if N == 25 else 20.02:.2f} "
                  f"on `sig`.")

    print(f"\n  READING. This is the signal's GROSS response with no slots, no")
    print(f"  displacement, no re-entry block and no leg re-weighting. It is NOT")
    print(f"  tradeable -- events overlap, so a real book would need capital the")
    print(f"  slotted construction does not have. What it gives is the horizon the")
    print(f"  edge actually lives on, which every prior study measured through a")
    print(f"  portfolio that manufactures its own churn.")

    json.dump({"purpose": ("the signal's raw event response, unconstrained by "
                           "portfolio slots; scores no cell and is not a book"),
               "max_horizon": MAX_H, "results": {str(k): v for k, v in results.items()},
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
