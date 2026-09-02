"""D288 Phase 0.5 -- the five PRICE scores ported to the DAILY RAGGED panel.

    uv run python scripts/ragged_price_scores.py --selftest

NOTHING HERE SCORES A CELL. No book is built, no rule is proposed, no position
series is formed. This file moves five committed estimators onto a panel they
could not previously run on, and proves the move changed no number.

WHY THE PORT IS NEEDED
----------------------
`run_magnitude_calibration.build_scores` produces nine price scores and is
FIFTEEN-MINUTE ONLY, in two separate ways:

    out[k][i] = np.asarray(series)          # length len(cleaned[sym]) == T
    U.rolling_fit(T, li, ...)               # symbol-local pivots vs a global T

Both are correct on a rectangular panel and silently wrong on a ragged one,
where every name starts on its own date and 134 of 1,573 carry internal holes.

Four of the nine already have a daily path through
`run_book_single_names.signals_ragged` -- the Impulse log-band level and
histogram (`A.log_parts`) and the two swing-line slopes (`U.rolling_fit`). The
FIVE ported here had none:

    macd_line        macd = ema(12) - ema(26)          macd.zero_line_score
    macd_hist        macd - signal                     macd.signal_line_score
    trailing_return  close(t)/close(t-37) - 1          macd.trailing_return_score
    rsi              Wilder RSI, window 14             structure.rsi
    impulse_nodz     mi - smma(close, 34)              macd.impulse_no_deadzone_score

EVERY ONE OF THESE PRIMITIVES IS ALREADY PANEL-AGNOSTIC. They take a bar
sequence and return a tuple aligned 1:1 with it, NaN before their own seed. So
the port is purely the scatter idiom from `signals_ragged`, and nothing else:

    at = np.flatnonzero(live[i])            # this symbol's own bars
    grid[i, at] = series_of_length_len(at)

THE ONE THING A RAGGED PORT MUST NOT DO. Index a symbol's bar list by a global
`t`, or assume a shared warm-up. Every score here warms on ITS OWN CLOCK counted
in ITS OWN BARS -- `warm[i, at[need:]] = True`, exactly as `signals_ragged` does
it. Before that the cell is NaN in the score grid and False in the warm mask; it
is NEVER zero, because zero is a value this arithmetic can legitimately produce
and a zero fill would be indistinguishable from a real reading.

WARM-UP IS PER SCORE, NOT PER FAMILY. `signals_ragged` takes one `max` because
its consumers form a single book from all of its parts. These five are
independent candidates, and collapsing them to a shared 992-bar gate would throw
away 978 warm bars of RSI per name for no reason. `WARM_UP_BARS` below is
derived from the committed primitives, never chosen.

AND THE IMPULSE WARM-UP IS THE FINDING TO CARRY OUT OF PHASE 0.5.
`impulse_nodz` needs 992 bars -- the Wilder leg's alpha = 1/34 takes 926 bars to
decay a seed to 1e-12 of price, on top of the 66-bar zlema seed. That is roughly
FOUR YEARS of daily data before the first actionable cell. Whether the score is
minable on this panel at all is a fact about the panel, so `--selftest` counts
the names that clear it rather than leaving D288 to assume they do.

LAGGING IS THE CONSUMER'S JOB. Scores are returned UNLAGGED, at the bar they are
computed on, matching `signals_ragged` and `build_scores`. `top_n` and
`neutral_book` call `lag1` themselves. DO NOT LAG HERE -- a second lag would be
invisible and would make every downstream result conservative-looking and wrong.

EQUIVALENCE IS TESTED, NOT ASSERTED. `price_scores` takes `live` explicitly and
defaults it to all-True, so the rectangular 15-minute panel and the ragged daily
panel go through the SAME code path with no branch between them. `--selftest`
runs this function and the ORIGINAL `build_scores` on the rectangular panel and
requires `np.array_equal(..., equal_nan=True)` on all five -- bit-identical, not
within a tolerance. A port that only passes because it special-cases the test is
not a port.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.research import structure as ST  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


RP = _load("ragged_panel", "ragged_panel.py")

PRICE_SCORES = ("macd_line", "macd_hist", "trailing_return", "rsi", "impulse_nodz")


def warm_up_bars() -> dict[str, int]:
    """Own-bar index from which each score may be acted on. DERIVED, not chosen.

    Each entry is that score's own seed plus its own IIR burn-in, taken from the
    committed primitives so an edit to a window length cannot leave this file
    stale:

      macd_line        (slow-1) seed + burn_in(slow)                  = 385
      macd_hist        + the signal SMA seed, i.e. `M.warm_up_bars()` = 393
      trailing_return  the lookback itself; an FIR window, no burn-in =  37
      rsi              the Wilder window; first defined index is `w`   =  14
      impulse_nodz     2(L-1) zlema seed + max burn-in of its two legs = 992

    `impulse_nodz` is 8 bars SHORTER than `M.impulse_warm_up_bars()` (1,000)
    because it never reads the 9-bar SMA signal line -- it is `mi - smma(close)`,
    and the dead zone and the signal are both absent from it. Reported both ways
    in the self-test so the 1,000-bar family figure is not quietly restated as
    something it is not."""
    macd_seed = M.DEFAULT_SLOW - 1
    macd_burn = M.burn_in_bars(M.DEFAULT_SLOW)
    L = M.IMPULSE_LENGTH
    imp = 2 * (L - 1) + max(
        M.burn_in_for_alpha(1.0 / L), M.burn_in_for_alpha(2.0 / (L + 1.0)))
    return {
        "macd_line": macd_seed + macd_burn,
        "macd_hist": M.warm_up_bars(),
        "trailing_return": M.MATCHED_MOMENTUM_LOOKBACK,
        "rsi": ST.RSI_WINDOW,
        "impulse_nodz": imp,
    }


WARM_UP_BARS = warm_up_bars()


def price_scores(panel, cleaned, live=None):
    """The five price scores on a ragged OR a rectangular panel. UNLAGGED.

    Returns `(scores, warm)`, both dicts keyed by `PRICE_SCORES`:

      scores[k]  (n, T) float, NaN everywhere the estimator has no value --
                 off the symbol's live bars, and before that symbol's own seed.
                 NEVER zero-filled: `impulse_nodz` and `macd_line` both reach
                 exactly 0.0 legitimately, so a zero fill would be a fabricated
                 reading indistinguishable from a real one.
      warm[k]    (n, T) bool, True from that symbol's own `WARM_UP_BARS[k]`-th
                 LIVE bar onward. Counted in the symbol's own bars, never in
                 grid columns -- a name with an internal hole spans more columns
                 than it has bars, and gating on columns would let it act early.

    `live` is taken explicitly and defaults to `panel.live`, falling back to
    all-True for a rectangular panel that has no such attribute. That default is
    the whole reason both panels can share this code path, which is what makes
    the equivalence test meaningful.

    THE SCORES ARE NOT LAGGED. The value at column `t` is computed from bars up
    to and including `t`. Consumers (`top_n`, `neutral_book`) apply `lag1`
    themselves; applying it here as well would silently double-lag every study
    built on this function."""
    n, T = panel.closes.shape
    if live is None:
        live = getattr(panel, "live", np.ones((n, T), dtype=bool))

    scores = {k: np.full((n, T), np.nan) for k in PRICE_SCORES}
    warm = {k: np.zeros((n, T), dtype=bool) for k in PRICE_SCORES}

    for i, sym in enumerate(panel.symbols):
        bars = cleaned[sym]
        # SCATTER TO ACTUAL BAR INDICES, NOT A CONTIGUOUS SLICE -- `signals_ragged`'s
        # rule. `index_of`'s span exceeds the bar count for a holed name, and a
        # slice would misalign every value after the hole by the hole's width.
        at = np.flatnonzero(live[i])
        if at.size != len(bars):
            raise AssertionError(
                f"{sym}: {at.size} live bars against {len(bars)} cleaned bars -- "
                "the panel and the bar list disagree")
        if at.size == 0:
            continue

        mac = M.macd_series(bars)
        scores["macd_line"][i, at] = np.asarray(M.zero_line_score(mac), dtype=float)
        scores["macd_hist"][i, at] = np.asarray(M.signal_line_score(mac), dtype=float)
        scores["trailing_return"][i, at] = np.asarray(
            M.trailing_return_score(bars, M.MATCHED_MOMENTUM_LOOKBACK), dtype=float)
        scores["rsi"][i, at] = np.asarray(ST.rsi(bars), dtype=float)
        imp = M.impulse_macd_series(bars)
        scores["impulse_nodz"][i, at] = np.asarray(
            M.impulse_no_deadzone_score(imp), dtype=float)

        # each score warms on ITS OWN clock, counted in this symbol's own bars
        for k, need in WARM_UP_BARS.items():
            if at.size > need:
                warm[k][i, at[need:]] = True
    return scores, warm


# --------------------------------------------------------------------------
# the self-test -- equivalence against the 15-minute original, then the daily run
# --------------------------------------------------------------------------


def selftest() -> int:
    print("RAGGED PRICE-SCORE PORTS -- equivalence against the 15-minute original\n")
    C = _load("d267", "run_magnitude_calibration.py")
    # D267's OWN handle on the loader, so the panel `build_scores` is measured on
    # is provably the panel it would have used -- not a second, separately loaded
    # copy that happens to look the same.
    R = C.R

    raw_panel, raw_cleaned = R.load_full()
    panel, cleaned = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])

    want = C.build_scores(panel, cleaned)          # the ORIGINAL, unmodified
    got, gwarm = price_scores(panel, cleaned)      # no `live` -> the all-True default

    bad = 0
    for k in PRICE_SCORES:
        a, b = want[k], got[k]
        same = np.array_equal(a, b, equal_nan=True)
        d = a - b
        worst = float(np.nanmax(np.abs(d))) if np.isfinite(d).any() else 0.0
        print(f"  {k:16s} identical: {str(same):5s}   finite cells {int(np.isfinite(a).sum()):9,d}"
              f"   max abs diff {worst:.3e}")
        bad += 0 if same else 1
    if bad:
        raise AssertionError(f"{bad} price score(s) differ from build_scores")
    print("\n  [1] all five price scores are BIT-IDENTICAL to "
          "run_magnitude_calibration.build_scores")

    # A warm mask that is never False, or never True, would pass [1] and prove
    # nothing. Pin that it actually gates, and that it gates each score by its own
    # constant rather than by one shared maximum.
    T = panel.closes.shape[1]
    for k in PRICE_SCORES:
        need = WARM_UP_BARS[k]
        exp = np.zeros(T, dtype=bool)
        exp[need:] = True
        if not np.array_equal(gwarm[k][0], exp):
            raise AssertionError(f"{k}: warm mask is not its own {need}-bar gate")
    if len({WARM_UP_BARS[k] for k in PRICE_SCORES}) != len(PRICE_SCORES):
        raise AssertionError("the five warm-ups collapsed to fewer than five values")
    print("  [2] warm masks gate per score, not per family: "
          + ", ".join(f"{k}={WARM_UP_BARS[k]}" for k in PRICE_SCORES))

    # ---------------------------------------------------------------- daily
    print("\nTHE DAILY RAGGED PANEL\n")
    B = _load("d256", "run_book_single_names.py")
    t0 = time.time()
    dpanel, dcleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    t_load = time.time() - t0
    n, T = dpanel.closes.shape
    own = dpanel.live.sum(axis=1)
    print(f"  panel: {n:,} symbols x {T:,} union bars, loaded in {t_load:.1f}s")

    t0 = time.time()
    dsc, dwarm = price_scores(dpanel, dcleaned)
    t_score = time.time() - t0
    print(f"  scored in {t_score:.1f}s\n")

    print(f"  {'score':16s} {'finite cells':>14s} {'warm cells':>14s} "
          f"{'names w/ any warm':>18s}  {'need':>5s}")
    for k in PRICE_SCORES:
        g = dsc[k]
        if np.isinf(g).any():
            raise AssertionError(f"{k}: infinite value on the daily panel")
        if (np.isfinite(g) & ~dpanel.live).any():
            raise AssertionError(f"{k}: finite value off the live mask")
        names = int((own > WARM_UP_BARS[k]).sum())
        print(f"  {k:16s} {int(np.isfinite(g).sum()):14,d} {int(dwarm[k].sum()):14,d} "
              f"{names:14,d}/{n:<4,d} {WARM_UP_BARS[k]:5,d}")
    print("\n  no score contains an infinity, and none is finite off the live mask")

    # PER-SYMBOL WARM-UP, SHOWN RATHER THAN CLAIMED. If the warm-up were global
    # these first-finite columns would coincide; they must not.
    print("\n  first finite COLUMN per named symbol (a global warm-up would tie these):")
    picks = [s for s in ("AA", "ZUMZ", "AAOI", "ENRNQ", "AAMRQ") if s in dpanel.symbols]
    picks = (picks + [s for s in dpanel.symbols if s not in picks])[:4]
    for sym in picks:
        i = dpanel.symbols.index(sym)
        t0i = int(np.flatnonzero(dpanel.live[i])[0])
        cells = []
        for k in ("rsi", "macd_line", "impulse_nodz"):
            f = np.flatnonzero(np.isfinite(dsc[k][i]))
            w = np.flatnonzero(dwarm[k][i])
            cells.append(f"{k}: fin {int(f[0]) if f.size else '--':>6} "
                         f"warm {int(w[0]) if w.size else '--':>6}")
        print(f"    {sym:8s} live from column {t0i:5,d} ({dpanel.dates[t0i]}), "
              f"{int(own[i]):5,d} bars | " + " | ".join(cells))
    firsts = {int(np.flatnonzero(np.isfinite(dsc['rsi'][dpanel.symbols.index(s)]))[0])
              for s in picks}
    if len(firsts) < 2:
        raise AssertionError("every sampled symbol warms on the same column -- "
                             "that is a global warm-up, which is the bug being ported away from")
    print("  [3] first-finite columns differ across symbols: the warm-up is per symbol")

    imp_names = int((own > WARM_UP_BARS["impulse_nodz"]).sum())
    print(f"\n  THE IMPULSE WARM-UP FINDING: impulse_nodz needs "
          f"{WARM_UP_BARS['impulse_nodz']:,} own bars "
          f"(M.impulse_warm_up_bars() = {M.impulse_warm_up_bars():,} for the family,\n"
          f"  8 more because nodz never reads the 9-bar signal SMA). "
          f"{imp_names:,} of {n:,} names ({100.0 * imp_names / n:.1f}%) clear it.")

    print("\n  ALL SELF-TESTS PASSED. No cell scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    ap.print_help()
    raise SystemExit(2)
