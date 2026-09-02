"""D280 part 3 -- extrapolate THE SCORE ITSELF, and measure it CROSS-SECTIONALLY.

    uv run python scripts/d280_score_extrapolation.py

NOTHING HERE SCORES A CELL. Measurement only, same standing as parts 1 and 2.

TWO CORRECTIONS TO PARTS 1 AND 2, BOTH OF THEM MINE
====================================================

1. THE FORECAST TARGET WAS WRONG. Parts 1 and 2 forecast the RAW close and the
   RAW range. The strategy never ranks on either -- it ranks on `hist_L`, which
   is ALREADY a smoothed quantity built from EMAs. Extrapolating a smooth series
   one step is a different and far better-posed problem than extrapolating a
   noisy one, and the derivatives should be taken from the series that actually
   feeds the score. That is what this file does.

2. THE METRIC WAS WRONG, AND THIS IS THE MORE SERIOUS OF THE TWO. G2 reported
   POOLED correlation over all names and all bars. **The strategy is purely
   CROSS-SECTIONAL**: at each bar it ranks the qualifying names against each
   other and holds the worst N. A score can rank well WITHIN each bar while
   showing almost nothing pooled, because pooling mixes the cross-section with
   the time series and with market-wide moves that no cross-sectional book is
   exposed to. The right statistic is the INFORMATION COEFFICIENT -- the
   cross-sectional rank correlation computed WITHIN each bar and averaged.

   G2's numbers are therefore withdrawn as a test of this construction, and so
   is the "combined IC ~0.018" bound derived from them.

WHAT IS MEASURED
----------------
  h(t)      = hist_L, the score D279 ranked on, LAGGED as R9 requires
  v, a, j   = first, second, third differences OF h ITSELF
  h_hat     = h(t) + v + a/2 + j/6         Taylor, weights FIXED not fitted

  IC        = Spearman rank correlation, WITHIN each bar, against the return of
              the NEXT bar; averaged over bars, with a t-statistic on the series
              of per-bar ICs.

  Reported twice: over ALL live names, and over the QUALIFYING SET ONLY -- the
  names S1_short would actually consider. The second is the one that matters,
  because that is the set the top-N ranking operates on, and a score can be
  informative across the whole universe while carrying nothing inside the
  already-filtered subset.

THE BAR, unchanged from part 1
-------------------------------
D279's corrected decomposition puts the ranking's contribution at +0.203 gross
Sharpe over turnover-matched random, and the book at -0.432 gross. **An
extrapolated score has to more than DOUBLE the ranking's contribution to reach
zero before costs.** So the question is not "is h_hat's IC positive" but "is it
materially larger than h's" -- a tie means nothing changes.

Reported alongside: what h(t)'s own IC is. If the extrapolation and the raw
score have the same IC, the derivatives add nothing and this line closes.
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
RP, U = B.RP, B.U

OUT = REPO / "data" / "d280_score_extrapolation.json"
SPLIT_DATE = "2018-01-01"
MIN_NAMES = 20          # a bar with fewer live names carries no cross-section


def d1(x, live):
    out = np.full_like(x, np.nan)
    ok = live[:, 1:] & live[:, :-1]
    out[:, 1:] = np.where(ok, x[:, 1:] - x[:, :-1], np.nan)
    return out


def rankdata(a):
    """Average ranks, ties shared. Small helper so scipy is not a dependency."""
    order = np.argsort(a, kind="stable")
    r = np.empty(a.size, dtype=float)
    r[order] = np.arange(1, a.size + 1, dtype=float)
    # share ties
    s = a[order]
    i = 0
    while i < s.size:
        j = i
        while j + 1 < s.size and s[j + 1] == s[i]:
            j += 1
        if j > i:
            r[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return r


def ic_series(score, fwd, mask):
    """Spearman IC within each bar. Returns per-bar ICs over bars that qualify."""
    out = []
    for t in range(score.shape[1]):
        m = mask[:, t] & np.isfinite(score[:, t]) & np.isfinite(fwd[:, t])
        if m.sum() < MIN_NAMES:
            continue
        a, b = score[m, t], fwd[m, t]
        if a.std() == 0 or b.std() == 0:
            continue
        ra, rb = rankdata(a), rankdata(b)
        out.append(float(np.corrcoef(ra, rb)[0, 1]))
    return np.array(out)


def report(name, ics, rows):
    if ics.size < 30:
        print(f"  {name:34s}  too few bars ({ics.size})")
        return
    mu, sd = ics.mean(), ics.std(ddof=1)
    t = mu / (sd / np.sqrt(ics.size))
    rows[name] = {"mean_ic": float(mu), "sd": float(sd), "t": float(t),
                  "bars": int(ics.size), "pct_positive": float((ics > 0).mean())}
    print(f"  {name:34s} {mu:+8.5f} {t:+8.2f} {ics.size:8,d} {(ics > 0).mean():8.1%}")


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    print(f"loaded + signals {time.time() - t0:.0f}s\n", flush=True)

    # NEXT bar's return -- what a position taken at t and held at t+1 earns.
    fwd = np.full_like(panel.total_log_returns, np.nan)
    ok = live[:, 1:] & live[:, :-1]
    fwd[:, :-1] = np.where(ok, np.expm1(panel.total_log_returns[:, 1:]), np.nan)

    dates = np.array(panel.dates)
    oos = live & (dates >= SPLIT_DATE)[None, :]

    # THE QUALIFYING SET -- exactly the names S1_short would consider at bar t,
    # which is where the top-N ranking actually operates.
    okm = ~(np.isnan(md) | np.isnan(hs)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & okm, warm)
    qual = oos & (s1 != 0.0)
    print(f"  out-of-sample live bars      {int(oos.sum()):,}")
    print(f"  of which S1 qualifies        {int(qual.sum()):,} "
          f"({qual.sum() / oos.sum():.1%})\n", flush=True)

    # h is the score, LAGGED, exactly as the corrected `top_n` uses it.
    h = C.lag1(hs)
    v = d1(h, live)
    a = d1(v, live)
    j = d1(a, live)
    cands = {
        "h  (D279's corrected score)": h,
        "h + v": h + v,
        "h + v + a/2": h + v + a / 2.0,
        "h + v + a/2 + j/6 (full)": h + v + a / 2.0 + j / 6.0,
        "v alone (pure momentum of h)": v,
        "a alone": a,
    }

    rows = {}
    for label, mask in (("ALL LIVE NAMES", oos), ("QUALIFYING SET ONLY", qual)):
        print(f"  IC vs NEXT-bar return -- {label}")
        print(f"  {'score':34s} {'mean IC':>8s} {'t':>8s} {'bars':>8s} {'IC>0':>8s}")
        for nm, s in cands.items():
            report(f"{label[:4]}|{nm}", ic_series(s, fwd, mask), rows)
        print(flush=True)

    print("  READING: a SHORT ranks ASCENDING, so a NEGATIVE IC is the tradeable")
    print("  direction -- low score, low forward return. What decides this line is")
    print("  whether any extrapolated variant has a MATERIALLY more negative IC on")
    print("  the QUALIFYING SET than `h` itself. A tie means the derivatives add")
    print("  nothing and D279's ranking is already the whole of it.\n")

    q = {k: v for k, v in rows.items() if k.startswith("QUAL")}
    base = q.get("QUAL|h  (D279's corrected score)")
    if base:
        print(f"  {'variant':34s} {'mean IC':>9s} {'vs h':>9s}")
        for k, val in q.items():
            print(f"  {k.split('|', 1)[1]:34s} {val['mean_ic']:+9.5f} "
                  f"{val['mean_ic'] - base['mean_ic']:+9.5f}")

    json.dump({"purpose": ("extrapolates the STRATEGY SCORE and measures it "
                           "cross-sectionally; scores no cell"),
               "corrections": ("part 1/2 forecast the raw close and used POOLED "
                               "correlation; both were the wrong target and the "
                               "wrong metric for a cross-sectional book"),
               "split_date": SPLIT_DATE, "min_names_per_bar": MIN_NAMES,
               "results": rows, "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
