"""D288 axis E -- RANGE AND VOLATILITY, on the daily ragged panel.

    uv run python scripts/ragged_vol_scores.py --selftest

NOTHING HERE SCORES A CELL. It builds the five E candidates D288 pre-registered
at `fa098a2` and proves they are causal.

THIS IS NEW CODE, WHICH IS WHY THE SELF-TEST IS A TRUNCATION AUDIT. The other
four families were PORTS and could be checked by bit-identity against the
estimator they replaced. E has no predecessor on this panel, so there is nothing
to be identical to -- and the pre-registration says in terms that every defect in
this programme entered through a runner written for one study. The check that
replaces bit-identity is stronger than a bounds assertion:

    delete every bar after column T0, recompute, and require every finite cell
    at t < T0 to be BIT-IDENTICAL.

A causal score cannot notice that the future was removed. A score that peeks
forward changes, and the assertion names the family and the cell count. This is
the `top_n` look-ahead -- which cost D279 93% of its apparent edge -- caught by
construction rather than by someone thinking to look.

CORWIN-SCHULTZ IS THE REASON THAT AUDIT EXISTS. `d285_spread_estimate.
corwin_schultz` returns the pair (t, t+1) AT INDEX t:

    out[:, :-1] = s        # index t holds the estimate spanning bars t and t+1

That is correct for D285, which used it to price a cost after the fact. Used as
a SCORE it reads bar t+1 to rank at bar t, and it is exactly the shape of bug
that has already been shipped here once. E2 therefore trails over pairs ending
at index t-1, so the newest bar it touches is bar t itself.

UNLAGGED, matching every other family. `top_n` and `neutral_book` lag; lagging
here would double-lag and silently change the estimator.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import warnings
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


VOL_LEVEL_SCORES = ("atr_norm", "cs_spread", "rvol21", "vol_ratio", "range_over_atr")

ATR_BARS = 14
CS_BARS = 21
RVOL_BARS = 21
FAST_BARS = 5
SLOW_BARS = 63
MIN_FRAC = 0.8          # a window this sparse is still a window; below it is not


def _windows(x, w):
    """Trailing windows of `x`, aligned so row k ends AT k. NaN-padded head."""
    m = x.size
    out = np.full((m, w), np.nan)
    if m >= w:
        out[w - 1:] = np.lib.stride_tricks.sliding_window_view(x, w)
    return out


def _trail(x, w, fn):
    """Trailing `fn` over w own bars, NaN unless MIN_FRAC of the window is finite.

    NOT a global-grid window. Every caller passes a SYMBOL-LOCAL series taken at
    `at = np.flatnonzero(live[i])`, because 134 of 1,573 names carry internal
    holes and a union-grid window would average in days the name did not trade.
    """
    win = _windows(x, w)
    cnt = np.isfinite(win).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"), \
            warnings.catch_warnings():
        # an all-NaN window is the NORMAL state during warm-up and is handled by
        # the count test on the next line; numpy's "mean of empty slice" here is
        # noise, not information
        warnings.simplefilter("ignore", RuntimeWarning)
        val = fn(win)
    return np.where(cnt >= int(np.ceil(MIN_FRAC * w)), val, np.nan)


def vol_level_scores(g, live, cs_raw):
    """E1-E5. `cs_raw` is `d285_spread_estimate.corwin_schultz(high, low, live)`.

    Passed in rather than computed here so the mine holds ONE Corwin-Schultz
    implementation -- D285's, unchanged -- and this module only decides where it
    is allowed to read from.
    """
    O, H, L, C = g["open"], g["high"], g["low"], g["close"]
    n, T = C.shape
    out = {k: np.full((n, T), np.nan) for k in VOL_LEVEL_SCORES}

    for i in range(n):
        at = np.flatnonzero(live[i])
        # THE GUARD IS 2 BARS, NOT 65, AND THE TRUNCATION AUDIT IS WHY.
        #
        # This first read `if at.size < SLOW_BARS + 2: continue` -- skip the
        # symbol unless it has enough bars for the slowest window. That is a
        # SYMBOL-LEVEL test on a TOTAL bar count, so whether bar t got a score
        # depended on how many bars the name had in FUTURE. The audit caught it
        # as 851 cells whose finite mask moved when the future was deleted.
        #
        # It is small but it is not cosmetic: on a 35.7%-dead fixture the names
        # with few total bars are the ones that DELIST, so the guard silently
        # withheld scores from exactly the cohort this panel exists to include,
        # and the mine would never have ranked them. Survivorship arriving
        # through a warm-up check.
        #
        # Warm-up now belongs to `_trail`, which decides PER SCORE and PER BAR
        # from bars already seen. A name with 30 bars gets `atr_norm` and no
        # `vol_ratio`, which is the honest answer.
        if at.size < 2:
            continue
        o, h, l, c = O[i, at], H[i, at], L[i, at], C[i, at]
        prev = np.concatenate([[np.nan], c[:-1]])

        # TRUE RANGE, fractional so it is comparable across names. The gap terms
        # are what separate this from `range_frac`: a name that opens away from
        # yesterday's close was volatile even if its session range was tight.
        with np.errstate(invalid="ignore", divide="ignore"):
            tr = np.maximum.reduce([h - l, np.abs(h - prev), np.abs(l - prev)]) / prev
            r = np.log(c / prev)
        out["atr_norm"][i, at] = _trail(tr, ATR_BARS, lambda w: np.nanmean(w, axis=1))

        # E2. THE NEWEST PAIR THIS MAY READ IS THE ONE ENDING AT BAR t, WHICH
        # `corwin_schultz` STORES AT INDEX t-1. Shifting by one own bar is the
        # whole causality argument -- see the module docstring.
        raw = cs_raw[i, at]
        lagged = np.concatenate([[np.nan], raw[:-1]])
        out["cs_spread"][i, at] = _trail(lagged, CS_BARS,
                                         lambda w: np.nanmean(w, axis=1))

        sd = lambda w: np.nanstd(w, axis=1)                          # noqa: E731
        rv = _trail(r, RVOL_BARS, sd)
        out["rvol21"][i, at] = rv
        fast, slow = _trail(r, FAST_BARS, sd), _trail(r, SLOW_BARS, sd)
        with np.errstate(invalid="ignore", divide="ignore"):
            out["vol_ratio"][i, at] = np.where(slow > 0, fast / slow, np.nan)

            # E5 is TODAY'S range against the name's own norm, so it is the one
            # E term that is not a trailing level -- it is where the name sits
            # relative to its own recent behaviour.
            atr = out["atr_norm"][i, at]
            rf = np.where(c > 0, (h - l) / c, np.nan)
            out["range_over_atr"][i, at] = np.where(atr > 0, rf / atr, np.nan)

    for k in out:
        out[k][~live] = np.nan
        out[k] = np.where(np.isfinite(out[k]), out[k], np.nan)
    return out


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------
def truncation_audit(build, live, T0, names, label):
    """Delete the future and require the past to be bit-identical.

    `build(T0)` must return {name: (n,T0) array} computed from bars < T0 only.
    Reported per score with its cell count, because a family that silently
    produces nothing would otherwise pass an equality check trivially -- the
    same failure mode as a cross-check that verifies zero symbols.
    """
    full = build(None)
    cut = build(T0)
    bad = 0
    for k in names:
        a, b = full[k][:, :T0], cut[k]
        fa, fb = np.isfinite(a), np.isfinite(b)
        m = live[:, :T0]
        if not np.array_equal(fa & m, fb & m):
            n_diff = int(((fa ^ fb) & m).sum())
            print(f"      {label}/{k}: FINITE MASK MOVED on {n_diff:,} cells")
            bad += 1
            continue
        sel = fa & m
        if not np.array_equal(a[sel], b[sel]):
            d = np.abs(a[sel] - b[sel])
            print(f"      {label}/{k}: {int((d > 0).sum()):,} cells CHANGED, "
                  f"max |delta| {d.max():.3e}")
            bad += 1
        else:
            print(f"      {label}/{k}: causal, {int(sel.sum()):,} cells identical")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not a.selftest:
        print(__doc__)
        return 0

    B = _load("d256", "run_book_single_names.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    P1 = _load("d280p1", "d280_forecast_precheck.py")
    SP = _load("d285sp", "d285_spread_estimate.py")

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=0.0)
    g = P1.build_grids(panel, cleaned)
    live = panel.live
    print(f"loaded {panel.closes.shape[0]} names x {panel.closes.shape[1]} bars "
          f"in {time.time() - t0:.0f}s", flush=True)

    cs_raw = SP.corwin_schultz(g["high"], g["low"], live)

    def build(T0):
        if T0 is None:
            return vol_level_scores(g, live, cs_raw)
        gc = {k: v[:, :T0] for k, v in g.items()}
        lc = live[:, :T0]
        # RECOMPUTED, not sliced. Slicing `cs_raw` would carry the estimate that
        # spans T0-1 and T0 -- a bar the truncated world does not have -- and
        # would make the audit pass by feeding it the future it is testing for.
        return vol_level_scores(gc, lc, SP.corwin_schultz(gc["high"], gc["low"], lc))

    scores = build(None)
    print("\n  [1] coverage and bounds")
    for k in VOL_LEVEL_SCORES:
        v = scores[k]
        assert not np.isinf(v).any(), f"{k}: infinities"
        assert not np.isfinite(v[~live]).any(), f"{k}: finite off the live mask"
        fin = np.isfinite(v)
        assert fin.sum() > 0, f"{k}: produced nothing"
        print(f"      {k:16s} {int(fin.sum()):>9,} cells   "
              f"[{np.nanmin(v):+.4f}, {np.nanmax(v):+.4f}]")
    assert np.nanmin(scores["atr_norm"]) >= 0.0, "atr_norm went negative"
    assert np.nanmin(scores["cs_spread"]) >= 0.0, "cs_spread went negative"
    assert np.nanmin(scores["rvol21"]) >= 0.0, "rvol21 went negative"

    T0 = int(live.shape[1] * 0.7)
    print(f"\n  [2] truncation audit at column {T0} of {live.shape[1]}")
    bad = truncation_audit(build, live, T0, VOL_LEVEL_SCORES, "E")
    assert bad == 0, f"{bad} E score(s) READ THE FUTURE"

    print(f"\nOK  {len(VOL_LEVEL_SCORES)} E scores, all causal  "
          f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
