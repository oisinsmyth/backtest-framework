"""Axis H -- HARVESTED from this repo's own prior instruments, on the daily panel.

    uv run python scripts/ragged_structure_scores.py --selftest

NOTHING HERE SCORES A CELL.

WHY THIS AXIS EXISTS. A scan of the 267 decision records and `src/` found several
instruments built for earlier studies that have NEVER been run cross-sectionally
on the daily single-name panel. They cost nothing to reuse and they are
mechanically distinct from anything in D288's 31.

    structure.fair_value_gaps    -> H1, H2   unfilled three-bar imbalances
    structure.market_structure   -> H3, H4, H5   BOS/CHoCH state machine
    D195, the volatility-estimator gate -> H6, H7   OHLC-efficient estimators
    D280 / D286's overnight finding     -> H8   did the gap reverse intraday

TWO THINGS WERE DELIBERATELY NOT HARVESTED, and the reasons are recorded so the
omissions are visible rather than accidental:

  * THE WEDGE BREAKOUT IS CLOSED -- D249 and D254, three distinct claims across
    two universes (`FINDINGS.md` section 8). Not proposed.
  * THE VOLUME REGIME GATE IS CLOSED -- D226, "the spike moved between asset
    classes; a fitted parameter". Not proposed.

AND ONE WAS DROPPED ON COST AND ON PARAMETER DISCIPLINE.
`terrain_swing.SwingSupplyDemandSensor` was the original H5. It emits a
`PriceDensity` rebuilt per bar, which is the same shape as
`VolumeProfileSensor` -- measured at 0.17 ms x 4,137,239 bars, i.e. ~12 minutes
of pure-Python single-threaded work. Its `k` is also constrained to
`SWING_K = (2, 3)` because D173 fixed that set and calls a third value "an
unregistered search". It is replaced by `choch_dist`, which falls out of the
`market_structure` pass already being made, costs nothing extra, and introduces
no new parameter.

K = 3 THROUGHOUT, taken from `run_uptrend_onset.K` -- the same pivot half-width
`signals_ragged` already uses. Choosing a different one here would be an
unregistered parameter search dressed as a new feature.

CAUSALITY. `market_structure` is documented as a single causal forward pass in
which a pivot at `t-k` influences the state at `t` and never at `t-1`.
`fair_value_gaps` computes `filled_at` by scanning forward, but `alive_at(j)`
only ever asks whether a gap was already dead BY j, which is knowable at j. Both
claims are checked rather than trusted, by the truncation audit from
`ragged_vol_scores` -- delete every bar after T0, recompute, require bit-identity
before T0.

UNLAGGED, matching every other family.
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

from backtest_framework.research.structure import (  # noqa: E402
    fair_value_gaps, market_structure)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


V = _load("ragged_vol_scores", "ragged_vol_scores.py")

STRUCTURE_SCORES = ("fvg_dist", "fvg_signed", "struct_trend", "retrace_leg",
                    "choch_dist", "park_vol_21", "gk_minus_cc", "gap_reversal")

K = 3                   # run_uptrend_onset.K, the half-width signals_ragged uses
ATR_BARS = 14
VOL_BARS = 21
FRESH_BARS = 252        # a level older than a year is not a level, see below
_LOG2 = np.log(2.0)


def _atr_price(o, h, l, c):
    """Trailing mean true range IN PRICE UNITS -- H1 and H5 are distances, so they
    normalise by a price-unit scale rather than a fractional one."""
    prev = np.concatenate([[np.nan], c[:-1]])
    with np.errstate(invalid="ignore"):
        tr = np.maximum.reduce([h - l, np.abs(h - prev), np.abs(l - prev)])
    return V._trail(tr, ATR_BARS, lambda w: np.nanmean(w, axis=1))


def _gap_features(bars, close, atr):
    """H1, H2. Nearest LIVE fair-value gap, and whether price sits inside one.

    Swept in bar order with a running list rather than rescanning every gap at
    every bar: a gap enters at `formed_at` and leaves at `filled_at`, so the
    total work is the sum of gap lifetimes rather than bars x gaps.
    """
    m = len(bars)
    dist = np.full(m, np.nan)
    signed = np.full(m, np.nan)
    gaps = fair_value_gaps(bars)
    by_start = {}
    for gp in gaps:
        by_start.setdefault(gp.formed_at, []).append(gp)

    alive = []
    for j in range(m):
        alive.extend(by_start.get(j, ()))
        # a gap is dead the bar it is filled; `alive_at` is the module's own test
        # STALE LEVELS ARE NOT LEVELS. `alive_at` alone kept gaps that formed
        # years earlier, when the name traded at a fraction of today's price --
        # genuinely 829 ATRs away and genuinely irrelevant. Those extremes were
        # not denominator noise, so guarding the denominator did not remove
        # them; at the tail the score was really measuring HOW FAR THE STOCK HAS
        # TRAVELLED, i.e. a momentum proxy wearing a structure label.
        alive = [gp for gp in alive
                 if gp.alive_at(j) and (j - gp.formed_at) <= FRESH_BARS]
        if not alive or not np.isfinite(close[j]) or not np.isfinite(atr[j]) \
                or atr[j] <= 0:
            continue
        px = close[j]
        best = min(alive, key=lambda gp: abs(px - gp.midpoint))
        # LOG-PRICE DISTANCE, NOT ATR MULTIPLES. Measured, after two wrong
        # guesses: the extremes are not penny stocks, they are FROZEN prices.
        # AVNS printed an identical $24.99 close on four consecutive days while
        # this score doubled each day -- 1080, 1512, 1890, 3780 -- because true
        # range collapses in a takeover or halt, ATR decays toward zero, and any
        # real level is then an unbounded number of "ATRs" away. An ATR floor set
        # as a fraction of price cannot fix that; the denominator is the problem.
        # log(close/level) is scale-free, bounded by the actual price move, and
        # directly comparable across names, which is what a cross-sectional rank
        # needs.
        if best.midpoint > 0 and px > 0:
            dist[j] = float(np.log(px / best.midpoint))
        inside = [gp for gp in alive if gp.lo <= px <= gp.hi]
        signed[j] = 0.0 if not inside else float(
            max(inside, key=lambda gp: gp.width).direction)
    return dist, signed


def _structure_features(bars, close, atr):
    """H3, H4, H5 from one `market_structure` pass."""
    m = len(bars)
    trend = np.full(m, np.nan)
    retr = np.full(m, np.nan)
    choch = np.full(m, np.nan)
    states = market_structure(bars, K)
    for j, st in enumerate(states):
        trend[j] = float(st.trend.value)
        lo, hi = st.last_low, st.last_high
        # RETRACEMENT ON CONFIRMED PIVOTS ONLY. Computed here from `last_low`
        # and `last_high` rather than through `structure.retracement`, which
        # needs a `Leg`; the quantity is the same and the inputs are the state
        # machine's own confirmed levels, so it inherits their causality.
        # THE LEG MUST BE A LEG. `hi > lo` alone let a two-tick swing through and
        # the ratio blew up: the first run measured retrace_leg over
        # [-2295, +1207]. A rank book selects the TAIL, so a score whose tail is
        # denominator noise selects on denominator noise -- the same defect as
        # D288's k=1 microstructure cluster. Half an ATR is the smallest move
        # worth calling a swing.
        li, hj = st.last_low_index, st.last_high_index
        fresh = (li is not None and hj is not None
                 and (j - li) <= FRESH_BARS and (j - hj) <= FRESH_BARS)
        if lo is not None and hi is not None and fresh and np.isfinite(close[j]) \
                and np.isfinite(atr[j]) and atr[j] > 0 and (hi - lo) > 0.5 * atr[j]:
            retr[j] = (close[j] - lo) / (hi - lo)
        # AND THE ATR MUST BE A REAL ATR. `atr > 0` admitted stub sessions whose
        # true range rounds to a tick, producing distances of 9,079 ATRs.
        if st.level_alive and st.choch_level is not None \
                and st.choch_index is not None \
                and (j - st.choch_index) <= FRESH_BARS \
                and np.isfinite(close[j]) \
                and close[j] > 0 and st.choch_level > 0:
            # log-price for the same reason as `fvg_dist`: VSA's -2865 came from
            # a frozen tape, not from a distant level.
            choch[j] = float(np.log(close[j] / st.choch_level))
    return trend, retr, choch


def structure_scores(g, cleaned, panel, live):
    """H1-H8."""
    O, H, L, C = g["open"], g["high"], g["low"], g["close"]
    n, T = C.shape
    out = {k: np.full((n, T), np.nan) for k in STRUCTURE_SCORES}

    for i, sym in enumerate(panel.symbols):
        at = np.flatnonzero(live[i])
        if at.size < 2:
            continue
        bars = cleaned[sym]
        if at.size != len(bars):
            raise AssertionError(
                f"{sym}: {at.size} live bars against {len(bars)} cleaned bars")
        o, h, l, c = O[i, at], H[i, at], L[i, at], C[i, at]
        atr = _atr_price(o, h, l, c)

        d, s = _gap_features(bars, c, atr)
        out["fvg_dist"][i, at], out["fvg_signed"][i, at] = d, s
        tr, rt, ch = _structure_features(bars, c, atr)
        out["struct_trend"][i, at] = tr
        out["retrace_leg"][i, at] = rt
        out["choch_dist"][i, at] = ch

        # H6/H7 -- D195 established that estimator choice is a measurable
        # question. Axis E uses only close-to-close, the LEAST efficient of the
        # three, so these are the same quantity estimated better.
        prev = np.concatenate([[np.nan], c[:-1]])
        with np.errstate(invalid="ignore", divide="ignore"):
            hl = np.log(np.where((h > 0) & (l > 0), h / l, np.nan))
            co = np.log(np.where((c > 0) & (o > 0), c / o, np.nan))
            rr = np.log(c / prev)
        park = V._trail(hl ** 2, VOL_BARS, lambda w: np.nanmean(w, axis=1))
        park = np.sqrt(np.maximum(park / (4.0 * _LOG2), 0.0))
        gk_v = V._trail(0.5 * hl ** 2 - (2.0 * _LOG2 - 1.0) * co ** 2, VOL_BARS,
                        lambda w: np.nanmean(w, axis=1))
        gk = np.sqrt(np.maximum(gk_v, 0.0))
        cc = V._trail(rr, VOL_BARS, lambda w: np.nanstd(w, axis=1))
        out["park_vol_21"][i, at] = park
        # GK is INTRADAY-ONLY, close-to-close carries the overnight. Their
        # difference is therefore an overnight-contribution probe, which is the
        # window D280 part 4 measured as carrying the whole hist_L effect.
        out["gk_minus_cc"][i, at] = gk - cc

        # H8 -- did the overnight move REVERSE during the session. Only defined
        # on consecutive own bars with a non-trivial gap; a "gap" spanning an
        # internal hole is a multi-session move, not one night.
        adjacent = np.zeros(at.size, dtype=bool)
        adjacent[1:] = np.diff(at) == 1
        with np.errstate(invalid="ignore", divide="ignore"):
            gap = np.where(adjacent & (prev > 0), o / prev - 1.0, np.nan)
            intr = np.where(o > 0, c / o - 1.0, np.nan)
            # A 1 bp "gap" is not a gap. The first run allowed |gap| > 1e-4 and
            # gap_reversal ranged over [-14338, +1880] -- entirely denominator.
            # 50 bp is the smallest overnight move worth dividing by.
            out["gap_reversal"][i, at] = np.where(
                np.abs(gap) > 5e-3, -intr / gap, np.nan)

    for k in out:
        out[k][~live] = np.nan
        out[k] = np.where(np.isfinite(out[k]), out[k], np.nan)
    return out


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

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=0.0)
    g = P1.build_grids(panel, cleaned)
    live = panel.live
    print(f"loaded {live.shape[0]} names x {live.shape[1]} bars in "
          f"{time.time() - t0:.0f}s", flush=True)

    def build(T0):
        if T0 is None:
            return structure_scores(g, cleaned, panel, live)
        # TRUNCATION MUST CUT THE BAR LISTS TOO, not only the grids -- the
        # structure machine and the gap scan read `cleaned`, so slicing the grid
        # alone would hand them the future the audit is testing for.
        keep = {}
        for i, sym in enumerate(panel.symbols):
            n_ok = int(live[i, :T0].sum())
            keep[sym] = cleaned[sym][:n_ok]

        class _P:
            symbols = panel.symbols
        return structure_scores({k: v[:, :T0] for k, v in g.items()}, keep,
                                _P(), live[:, :T0])

    t = time.time()
    scores = build(None)
    print(f"  built in {time.time() - t:.0f}s")

    print("\n  [1] coverage and bounds")
    for k in STRUCTURE_SCORES:
        v = scores[k]
        assert not np.isinf(v).any(), f"{k}: infinities"
        assert not np.isfinite(v[~live]).any(), f"{k}: finite off the live mask"
        assert np.isfinite(v).sum() > 0, f"{k}: produced nothing"
        print(f"      {k:16s} {int(np.isfinite(v).sum()):>9,} cells   "
              f"[{np.nanmin(v):+.4f}, {np.nanmax(v):+.4f}]")
    u = np.unique(scores["struct_trend"][np.isfinite(scores["struct_trend"])])
    assert set(u.tolist()) <= {-1.0, 0.0, 1.0}, f"struct_trend not categorical: {u}"
    assert np.nanmin(scores["park_vol_21"]) >= 0.0, "Parkinson vol went negative"
    # BOUNDS THAT CANNOT SILENTLY REGRESS. Every one of these fired on run 1,
    # where the tails were pure division noise rather than signal.
    for k, lim in (("retrace_leg", 30.0), ("choch_dist", 10.0),
                   ("gap_reversal", 200.0), ("fvg_dist", 10.0)):
        lo_, hi_ = float(np.nanmin(scores[k])), float(np.nanmax(scores[k]))
        assert max(abs(lo_), abs(hi_)) <= lim, (
            f"{k} reached [{lo_:.1f}, {hi_:.1f}], outside +/-{lim:.0f} -- the "
            f"denominator guard has regressed and the tail is division noise")
    print(f"      struct_trend takes exactly {sorted(u.tolist())}")

    T0 = int(live.shape[1] * 0.7)
    print(f"\n  [2] truncation audit at column {T0} of {live.shape[1]}")
    bad = V.truncation_audit(build, live, T0, STRUCTURE_SCORES, "H")
    assert bad == 0, f"{bad} H score(s) READ THE FUTURE"

    print(f"\nOK  {len(STRUCTURE_SCORES)} H scores, all causal  "
          f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
