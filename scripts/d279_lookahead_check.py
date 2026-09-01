"""D279 DEFECT CHECK -- does the top-N ranking use the bar it is about to earn?

    uv run python scripts/d279_lookahead_check.py

THE SUSPICION, stated as code rather than prose.

`hold_book` is R9-compliant and lags by one bar:

    p[:, 1:] = mask[:, :-1]           # position at t comes from signal at t-1

`pooled_returns` then earns bar t's return on the position held at bar t. So the
BASE book is aligned correctly and D256's result is not in question.

But `run_concentrated_short.top_n` ranks with:

    s = score[q, t]                   # <-- score AT BAR t
    out[pick, t] = base[pick, t]      # <-- earns bar t's return

`base[:, t]` is properly lagged, so WHICH NAMES QUALIFY is honest. But WHICH N OF
THE QUALIFIERS ARE HELD is decided using `hist_L` computed from the close of bar
t -- the bar the position is about to be paid for. `hist_L` is a function of
recent returns including that bar's. **Ranking on it and then booking that same
bar's return is look-ahead**, and it lands on exactly the quantity hurdle C
tests: the selection of N from the qualifying set.

THIS SCRIPT DOES NOT ARGUE. It scores `top25` and `top50` three ways --
unlagged (what D279 ran), lagged by one bar (what R9 requires), and the
qualifying-set-only base -- and prints them side by side. If the lagged number
collapses toward the base, D279's headline is an artefact of my runner and must
be withdrawn, not amended.

No nulls, no hurdles, no new cells. This is a correctness test of a reported
number.
"""

from __future__ import annotations

import importlib.util
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
PPY, RF, BORROW, FEE = C.PPY, C.RF, C.BORROW, C.FEE


def lag1(a):
    """Shift a score grid one bar forward, exactly as `hold_book` shifts a mask.
    Column 0 becomes NaN so it ranks last rather than ranking on nothing."""
    out = np.full_like(a, np.nan)
    out[:, 1:] = a[:, :-1]
    return out


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    print(f"loaded {time.time() - t0:.0f}s\n", flush=True)

    sc = lambda p: RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)

    # HOW MUCH OF hist_L AT BAR t IS BAR t ITSELF? If the score barely moves when
    # lagged, the look-ahead would be harmless. Measured, not assumed.
    live = panel.live & np.isfinite(hs) & np.isfinite(lag1(hs))
    a, b = hs[live], lag1(hs)[live]
    print(f"  corr(hist_L at t, hist_L at t-1) over {live.sum():,} live bars: "
          f"{np.corrcoef(a, b)[0, 1]:+.4f}")
    r = np.expm1(panel.total_log_returns)
    m2 = live & np.isfinite(r)
    print(f"  corr(hist_L at t,   return at t) : {np.corrcoef(hs[m2], r[m2])[0, 1]:+.4f}"
          "   <-- if this is materially negative, ranking on it is peeking")
    print(f"  corr(hist_L at t-1, return at t) : "
          f"{np.corrcoef(lag1(hs)[m2], r[m2])[0, 1]:+.4f}"
          "   <-- the honest, tradeable version\n", flush=True)

    base = sc(s1)
    print(f"  {'cell':28s} {'expo':>7s} {'CAGR':>8s} {'Sharpe':>8s}")
    print(f"  {'S1_short|all (base)':28s} {base['exposure_gross']:6.2%} "
          f"{base['cagr']:+7.2%} {base['excess_sharpe']:+8.3f}")
    for N in (25, 50):
        for label, s in (("UNLAGGED - what D279 ran", hs),
                         ("LAGGED 1 bar - R9", lag1(hs))):
            p = C.top_n(s1, s, N)
            v = sc(p)
            print(f"  {f'top{N}  {label}':28s} {v['exposure_gross']:6.2%} "
                  f"{v['cagr']:+7.2%} {v['excess_sharpe']:+8.3f}", flush=True)
    print(f"\n  {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
