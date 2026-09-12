"""D471 -- the two things D469 left unmeasured: the spread where the moves are, and whether
path efficiency is a usable conditioner at all.

    uv run python scripts/d471_spread_and_path_efficiency.py --self-test
    uv run python scripts/d471_spread_and_path_efficiency.py --measure [--json]

**A MEASUREMENT, NOT A STUDY.** No signal, no entry rule, no edge, no Sharpe of any
construction. Nothing opened, closed or admitted (R15).

WHY
---
[D469](../docs/decisions/D469-RESULT-the-scalping-re-cost-the-spread-is-not-what-kills-it-a-fixed-commission-against-a-tenth-sized-tick-is.md)
put the MES breakeven accuracy at a 15-minute hold at **55.0%** by trading only the top
quintile of trailing volatility -- and flagged its own weakness in writing: *"the top
volatility quintile is exactly where fills are worst ... the conditioned rows are the most
optimistic cells in the table, not the safest."* D465's 97.6%-at-one-tick is **unconditional**.
So the first job here is to pay the spread that is actually quoted **in the bucket being
traded**, at **both** ends of the window, and recompute the bar.

The second job is the principal's question: **path efficiency.** For a window, efficiency is

    eff = |net displacement| / (total path length travelled)

in [0, 1]: 1 is a straight line, 0 is a round trip back to the start. It matters twice over.
**It separates a big move you can hold from a big move that shakes you out first**, which is
exactly the axis raw volatility cannot see -- high vol with low efficiency is chop.

**STAGE 0 COMES FIRST AND CAN KILL IT.** A conditioner is only usable if it **forecasts
itself**: the efficiency of the *next* window has to be predictable from the *previous* one.
That premise is measured here before anything is conditioned on it, and if the correlation is
~0 then path efficiency is a description of the past and not a signal, however good the story
is. Volatility passed this test in D469 at only rho = 0.232.

**RESOLUTION WARNING, and it is not a detail.** Path length is sampling-dependent -- for a
diffusion it diverges as the grid gets finer, so an efficiency NUMBER means nothing without
its grid. Everything here is on the same one-second grid, and only the RANKING across buckets
and the persistence correlation are claimed.

METHOD
------
**Non-overlapping** windows, unlike D469's overlapping pairs. Overlapping windows share
observations, so their statistics are correlated and an SE computed from them is a fiction.
Consecutive h-second blocks are independent, they give honest SEs, and they match the trading
model D469 priced (about 19 windows a day at 15 minutes).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
TICKS = REPO / "temp" / "d465_es_ticks_v2.npz"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "d471_spread_and_path_efficiency.json"

PX_SCALE = 1e-9
TICK_PTS = 0.25
INT64_SENTINEL = 9223372036854775807      # DBN's absent-quote marker (D465's 875-tick bug)
COMMISSION_RT_MES = 3.00                  # D466's declared cost line
TICK_USD_MES = 1.25
HORIZONS = (300, 900)
NQ = 5                                    # quintiles


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- primitives

def path_efficiency(px: np.ndarray) -> float:
    """|net move| / total path length, in [0, 1]. 1 = straight line, 0 = round trip."""
    if len(px) < 2:
        return float("nan")
    length = float(np.abs(np.diff(px)).sum())
    if length <= 0:
        return float("nan")
    return abs(float(px[-1] - px[0])) / length


def blocks_of(sec: np.ndarray, h: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Non-overlapping h-second blocks. Returns (block_id, start_idx, end_idx inclusive)."""
    bid = (sec - sec[0]) // h
    uniq, starts = np.unique(bid, return_index=True)
    ends = np.append(starts[1:], len(sec)) - 1
    return uniq, starts, ends


def breakeven_accuracy(cost_ticks: np.ndarray | float,
                       mean_abs_move_ticks: np.ndarray | float):
    """p to net zero on a +/-|M| outcome paying cost: p = (1 + cost/E|M|)/2."""
    return (1.0 + np.asarray(cost_ticks) / np.asarray(mean_abs_move_ticks)) / 2.0


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:58} {detail}")
        if not cond:
            fails.append(label)

    # --- path efficiency, on paths whose answer is known by hand
    chk("eff of a straight line = 1",
        abs(path_efficiency(np.array([1., 2., 3., 4.])) - 1.0) < 1e-12)
    chk("eff of an exact round trip = 0",
        abs(path_efficiency(np.array([1., 5., 1.])) - 0.0) < 1e-12)
    # 0 -> 3 -> 1 is a NET of 1 over a PATH of 3+2 = 5, so 0.2. I first wrote 1/3 here and
    # the check failed -- the arithmetic was wrong, not the function.
    chk("eff of out-and-two-thirds-back = 0.2",
        abs(path_efficiency(np.array([0., 3., 1.])) - 0.2) < 1e-12)
    chk("eff is sign-blind (a straight fall is also 1)",
        abs(path_efficiency(np.array([4., 3., 2., 1.])) - 1.0) < 1e-12)
    for p in (np.array([0., 1., -2., 5., 3.]), np.array([0., -1., -1., 2.])):
        e = path_efficiency(p)
        chk(f"eff in [0,1] for {list(p.astype(int))}", 0.0 <= e <= 1.0 + 1e-12, f"{e:.4f}")
    # RESOLUTION: the same underlying move sampled finer has a LONGER path, so lower
    # efficiency. This is why only rankings on one fixed grid are claimed.
    coarse = path_efficiency(np.array([0., 10.]))
    fine = path_efficiency(np.array([0., 3., 1., 6., 4., 10.]))
    chk("eff FALLS under finer sampling (resolution-dependent)", fine < coarse,
        f"coarse {coarse:.3f} vs fine {fine:.3f}")

    # --- the block machinery, against a hand-built case
    sec = np.array([0, 1, 2, 10, 11, 20, 21, 22], dtype=np.int64)
    uniq, st, en = blocks_of(sec, 10)
    chk("blocks: 3 blocks of width 10", len(uniq) == 3, f"{len(uniq)}")
    chk("blocks: starts", list(st) == [0, 3, 5], f"{list(st)}")
    chk("blocks: ends are INCLUSIVE and tile with no gap",
        list(en) == [2, 4, 7], f"{list(en)}")
    px = np.array([5., 7., 6., 1., 9., 2., 2., 2.])
    chk("reduceat block max matches a loop",
        list(np.maximum.reduceat(px, st)) == [7., 9., 2.])
    chk("reduceat block min matches a loop",
        list(np.minimum.reduceat(px, st)) == [5., 1., 2.])
    # path length by cumulative sum must equal the direct sum, per block
    cum = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(px)))])
    for k in range(len(st)):
        direct = float(np.abs(np.diff(px[st[k]:en[k] + 1])).sum())
        viacum = float(cum[en[k]] - cum[st[k]])
        chk(f"path length by cumsum == direct, block {k}", abs(direct - viacum) < 1e-12,
            f"{direct:.2f}")

    # --- adverse excursion from ENTRY (a fixed stop keys on this, not on a running peak)
    up = np.array([100., 101., 102., 103.])
    chk("a monotone rise has ZERO adverse excursion for a long",
        abs(float(up[0] - up.min())) < 1e-12)
    dip = np.array([100., 97., 99., 104.])
    chk("a long that dips 3 before paying 4 has adverse 3",
        abs(float(dip[0] - dip.min()) - 3.0) < 1e-12)
    chk("the SHORT side of the same path has adverse 4",
        abs(float(dip.max() - dip[0]) - 4.0) < 1e-12)

    # --- the sentinel filter, which is the bug that made D465 read 875-tick spreads
    bid = np.array([100, INT64_SENTINEL, 102, 0], dtype=np.int64)
    ask = np.array([101, 103, INT64_SENTINEL, 5], dtype=np.int64)
    ok = ((bid != INT64_SENTINEL) & (ask != INT64_SENTINEL) & (bid > 0) & (ask > 0)
          & (ask >= bid))
    chk("sentinel filter admits only the clean quote", list(ok) == [True, False, False, False],
        f"{list(ok)}")

    # --- the cost identity, and that a wider spread RAISES the bar
    lo = float(breakeven_accuracy(3.41, 22.83))
    hi = float(breakeven_accuracy(4.41, 22.83))
    chk("a wider spread raises breakeven accuracy", hi > lo,
        f"{lo:.3%} -> {hi:.3%} for one extra tick of cost")
    chk("a bigger move lowers it", breakeven_accuracy(3.41, 34.4) < lo,
        f"{float(breakeven_accuracy(3.41, 34.4)):.3%} at 34.4 ticks")
    chk("zero cost needs exactly 50%", abs(float(breakeven_accuracy(0.0, 10.0)) - .5) < 1e-15)

    # --- THE RANDOM-WALK BENCHMARK FOR EFFICIENCY, which is what makes the measured
    # numbers interpretable. For a driftless walk of n steps, E|net| = sigma*sqrt(2n/pi)
    # and E[path] = n*sigma*sqrt(2/pi), so efficiency -> 1/sqrt(n) EXACTLY. Without this
    # line "efficiency is 0.033" is an uninterpretable small number.
    rng = np.random.default_rng(4711)
    for n in (100, 900):
        effs = [path_efficiency(np.concatenate([[0.0], np.cumsum(rng.standard_normal(n))]))
                for _ in range(4000)]
        got, want = float(np.mean(effs)), 1.0 / np.sqrt(n)
        chk(f"simulated walk efficiency ~ 1/sqrt(n) at n={n}",
            abs(got - want) / want < 0.06, f"{got:.4f} vs 1/sqrt(n) {want:.4f}")

    # --- the coarsening, on a hand-built series
    s = np.array([0, 1, 2, 5, 6, 10, 11, 14], dtype=np.int64)
    p_ = np.array([1., 2., 3., 4., 5., 6., 7., 8.])
    ss = np.zeros(8, dtype=np.int64)
    sc, pc, _ = coarsen(s, p_, ss, 5)
    chk("coarsen takes the LAST point in each bucket", list(pc) == [3., 5., 8.],
        f"{list(pc)} at secs {list(sc)}")
    chk("coarsen keeps the matching seconds", list(sc) == [2, 6, 14], f"{list(sc)}")

    # --- window runs: non-overlapping, inside one session, spanning ~h
    sec_c = np.arange(0, 100, 10, dtype=np.int64)          # 10 points, 10 s apart
    px_c = np.arange(10.0)
    sess_c = np.zeros(10, dtype=np.int64)
    st, en, pv = sweep_windows(sec_c, px_c, sess_c, m=3, h=30)
    chk("runs are non-overlapping and m apart",
        len(st) > 0 and all(en[:-1] <= st[1:]), f"starts {list(st)} ends {list(en)}")
    chk("every run has a valid predecessor at start-m",
        len(st) > 0 and all(pv == st - 3), f"prev {list(pv)}")
    chk("first run is dropped (it has no predecessor)", 0 not in list(st), f"{list(st)}")
    # a session boundary must break a run
    sess_b = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], dtype=np.int64)
    st_b, en_b, _ = sweep_windows(sec_c, px_c, sess_b, m=3, h=30)
    chk("a run may not straddle a session boundary",
        all(sess_b[a] == sess_b[b] for a, b in zip(st_b, en_b)),
        f"{[(int(a), int(b)) for a, b in zip(st_b, en_b)]}")
    # a time gap larger than the tolerance must break a run
    sec_gap = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 500], dtype=np.int64)
    st_g, en_g, _ = sweep_windows(sec_gap, px_c, sess_c, m=3, h=30)
    chk("a run whose span is far from h is rejected",
        all(abs((sec_gap[b] - sec_gap[a]) - 30) <= 0.15 * 30
            for a, b in zip(st_g, en_g)),
        f"spans {[int(sec_gap[b]-sec_gap[a]) for a, b in zip(st_g, en_g)]}")

    # --- the variance ratio, on series whose answer is known
    rg = np.random.default_rng(471471)
    walk = np.cumsum(rg.standard_normal(200_000))
    r1 = np.diff(walk)
    for kk in (5, 20):
        rk = r1[:(len(r1) // kk) * kk].reshape(-1, kk).sum(axis=1)
        vr = float(np.var(rk, ddof=1) / (kk * np.var(r1, ddof=1)))
        chk(f"variance ratio of a random walk ~ 1 at k={kk}", abs(vr - 1.0) < 0.05,
            f"{vr:.4f}")
    def vr_of(series, kk=20):
        r = np.diff(series)
        rk_ = r[:(len(r) // kk) * kk].reshape(-1, kk).sum(axis=1)
        return float(np.var(rk_, ddof=1) / (kk * np.var(r, ddof=1)))

    # VR IS BLIND TO DETERMINISTIC DRIFT, and I first asserted the opposite. A constant
    # drift adds no VARIANCE, so it cannot move a variance ratio: VR reads AUTOCORRELATION,
    # not trend. The failed check is kept, inverted, because the property matters -- a
    # market could drift steadily and still read exactly 1.00 here.
    eps = rg.standard_normal(200_000)
    chk("variance ratio is UNMOVED by a deterministic drift",
        abs(vr_of(np.cumsum(eps) + np.arange(200_000) * 0.02) - vr_of(np.cumsum(eps)))
        < 1e-9, f"{vr_of(np.cumsum(eps) + np.arange(200_000)*0.02):.4f}")
    # positive return autocorrelation (momentum) must read ABOVE 1
    mom = np.cumsum(eps[1:] + 0.25 * eps[:-1])
    chk("variance ratio of positively autocorrelated returns is > 1", vr_of(mom) > 1.05,
        f"{vr_of(mom):.3f}")
    # bid-ask bounce -- a random level shift each step -- must read BELOW 1
    bounce = np.cumsum(rg.standard_normal(200_000)) + rg.choice([-0.5, 0.5], 200_000)
    chk("variance ratio detects bid-ask bounce as < 1", vr_of(bounce) < 0.95,
        f"{vr_of(bounce):.3f}")

    # --- the clock abstraction must not know which clock it is
    px_k = np.array([10., 11., 12., 13., 14., 15.])
    sec_k = np.array([0, 1, 2, 3, 4, 5], dtype=np.int64)
    ses_k = np.zeros(6, dtype=np.int64)
    sz_k = np.ones(6, dtype=np.int64)
    # VOLUME BEFORE THE TRADE, so the clock starts at 0 like a wall clock does. Using
    # cumsum(sz) put the first boundary a partial bucket early and made the volume clock
    # inequivalent to a trade-count clock on unit sizes -- found by this check disagreeing
    # with the time clock below on data where they MUST agree.
    cum_k = np.cumsum(sz_k) - sz_k                # 0,1,2,3,4,5
    pv, _, _ = clock_sample(cum_k, px_k, sec_k, ses_k, 2)
    pt, _, _ = clock_sample(sec_k, px_k, sec_k, ses_k, 2)
    chk("volume clock on unit-size trades == every 2nd trade",
        list(pv) == [11., 13., 15.], f"{list(pv)}")
    chk("time clock of 2 s on 1 s trades gives the same points",
        list(pt) == [11., 13., 15.], f"{list(pt)}")
    chk("THE TWO CLOCKS AGREE where they must (unit sizes, one trade a second)",
        list(pv) == list(pt), f"{list(pv)} vs {list(pt)}")
    # and a LUMPY size distribution must REGROUP the trades
    sz_l = np.array([1, 1, 8, 1, 1, 1], dtype=np.int64)
    pl, _, _ = clock_sample(np.cumsum(sz_l) - sz_l, px_k, sec_k, ses_k, 2)
    chk("a lumpy trade regroups the volume buckets", list(pl) != list(pv),
        f"{list(pl)} against {list(pv)}")

    # clock_cell must compute the SAME numbers as the hand primitives on one window
    rg2 = np.random.default_rng(99)
    p_ = np.cumsum(rg2.standard_normal(4000)) + 100.0
    s_ = np.arange(4000, dtype=np.int64)
    ss_ = np.zeros(4000, dtype=np.int64)
    cell = clock_cell(p_, s_, ss_, m=10)
    chk("clock_cell returns a cell on a synthetic series", cell is not None)
    if cell:
        # a driftless walk must read VR ~ 1 and a corrected ratio ~ 1
        chk("clock_cell VR ~ 1 on a random walk", abs(cell["variance_ratio"] - 1) < 0.12,
            f"{cell['variance_ratio']:.3f}")
        chk("clock_cell corrected ratio ~ 1 on a random walk",
            abs(cell["efficiency_over_corrected_benchmark"] - 1) < 0.12,
            f"{cell['efficiency_over_corrected_benchmark']:.3f}")
        chk("clock_cell kurtosis ~ 3 on a Gaussian window return",
            abs(cell["kurtosis_of_window_return"] - 3.0) < 0.8,
            f"{cell['kurtosis_of_window_return']:.2f}")
        # and the identity gate inside it did not raise, which is itself the check
        chk("clock_cell identity holds (it raises otherwise)", True,
            f"ratio {cell['efficiency_over_corrected_benchmark']:.6f} "
            f"= sqrt(VR)*nonGauss")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


# ---------------------------------------------------------------- grid sweep

def load_grid():
    """The one-second RTH grid, with a session id. Shared by --measure and --grid-sweep."""
    import pandas as pd
    z = np.load(TICKS)
    if "iid" not in z:
        raise GateError("[INPUT] cache carries no instrument_id; re-run d465 --extract")
    ts = z["ts"]
    px = z["px"].astype(np.float64) * PX_SCALE
    bid, ask = z["bid"], z["ask"]
    good = ((px > 0) & (bid != INT64_SENTINEL) & (ask != INT64_SENTINEL)
            & (bid > 0) & (ask > 0) & (ask >= bid))
    ts, px, iid = ts[good], px[good], z["iid"][good].astype(np.int64)
    sec = (ts // 1_000_000_000).astype(np.int64)
    uniq, first = np.unique(sec, return_index=True)
    last = np.append(first[1:], len(px)) - 1
    et = pd.DatetimeIndex(pd.to_datetime(uniq, unit="s", utc=True)) \
        .tz_convert("America/New_York")
    etm = et.hour.values * 60 + et.minute.values
    rth = (etm >= 9 * 60 + 30) & (etm < 16 * 60)
    # session id: the ET calendar date, as an integer
    sess = (et.year.values * 10000 + et.month.values * 100 + et.day.values)
    return uniq[rth], px[last][rth], iid[last][rth], sess[rth]


def load_trades_rth():
    """TRADE-level RTH data. A volume clock must place boundaries inside a second, so it
    cannot be built from the one-second grid."""
    import pandas as pd
    z = np.load(TICKS)
    if "iid" not in z:
        raise GateError("[INPUT] cache carries no instrument_id; re-run d465 --extract")
    px = z["px"].astype(np.float64) * PX_SCALE
    bid, ask = z["bid"], z["ask"]
    good = ((px > 0) & (bid != INT64_SENTINEL) & (ask != INT64_SENTINEL)
            & (bid > 0) & (ask > 0) & (ask >= bid) & (z["sz"] > 0))
    sec = (z["ts"][good] // 1_000_000_000).astype(np.int64)
    px, sz = px[good], z["sz"][good].astype(np.int64)
    et = pd.DatetimeIndex(pd.to_datetime(sec, unit="s", utc=True)) \
        .tz_convert("America/New_York")
    etm = et.hour.values * 60 + et.minute.values
    rth = (etm >= 9 * 60 + 30) & (etm < 16 * 60)
    sess = et.year.values * 10000 + et.month.values * 100 + et.day.values
    return sec[rth], px[rth], sz[rth], sess[rth]


def clock_sample(key: np.ndarray, px: np.ndarray, sec: np.ndarray, sess: np.ndarray,
                 step):
    """Last observation in each `step`-sized bucket of a monotone clock `key`.

    `key` is wall-clock seconds for a time clock and cumulative contracts for a volume
    clock -- the rest of the pipeline cannot tell which, which is the point.
    """
    b = key // step
    _, f = np.unique(b, return_index=True)
    l = np.append(f[1:], len(px)) - 1
    return px[l], sec[l], sess[l]


def coarsen(sec: np.ndarray, px: np.ndarray, sess: np.ndarray, delta: int):
    """Last observation in each delta-second bucket. Returns (sec, px, sess) coarsened."""
    b = sec // delta
    _, f = np.unique(b, return_index=True)
    l = np.append(f[1:], len(sec)) - 1
    return sec[l], px[l], sess[l]


def sweep_windows(sec_c, px_c, sess_c, m: int, h: int):
    """Non-overlapping runs of m steps (m+1 points) inside ONE session, spanning ~h seconds.

    Returns (start_idx, end_idx) for runs that pass, plus the preceding run's start.
    """
    n = len(sec_c)
    starts = np.arange(0, n - m - 1, m, dtype=np.int64)
    ends = starts + m
    ok = ((sess_c[starts] == sess_c[ends])
          & (np.abs((sec_c[ends] - sec_c[starts]) - h) <= 0.15 * h))
    # the immediately preceding run must also be valid and in the same session
    prev = starts - m
    okp = np.zeros(len(starts), dtype=bool)
    okp[1:] = ok[:-1] & (sess_c[np.maximum(prev[1:], 0)] == sess_c[starts[1:]])
    keep = ok & okp
    return starts[keep], ends[keep], prev[keep]


def do_grid_sweep(as_json: bool) -> int:
    """Does path efficiency say anything different on a COARSER grid?

    D471 measured on one-second sampling only and said so. The reason to expect a coarse
    grid to differ is concrete: at one-second sampling BID-ASK BOUNCE inflates the path
    length, which is exactly why RTH came in BELOW the random-walk value (ratio 0.87-0.93).
    Coarsen and that noise averages out, so any genuine trend structure should emerge.

    Two readings per cell, and they are independent instruments that must agree:
      * efficiency / (1/sqrt(m))  -- 1.00 means indistinguishable from a driftless walk
      * the VARIANCE RATIO Var(r_k)/(k*Var(r_1)) -- the standard test for the same thing,
        1.00 random walk, >1 trending, <1 mean-reverting.
    """
    sec, px, iid, sess = load_grid()
    P(f"RTH one-second grid: {len(sec):,} seconds over "
      f"{len(np.unique(sess)):,} sessions\n")

    GRIDS = (1, 5, 15, 60, 300)
    WINDOWS = (900, 3600)
    out = {"grids_seconds": list(GRIDS), "windows_seconds": list(WINDOWS), "cells": []}

    for h in WINDOWS:
        P(f"=== window {h//60} min, RTH only ===")
        P(f"  {'grid':>6}{'steps m':>9}{'windows':>10}{'eff':>8}{'1/sqrt m':>11}"
          f"{'naive':>8}{'C':>7}{'mean-of-r':>10}{'r-o-m':>8}{'sqrt VR':>9}{'VR':>8}"
          f"{'persist':>11}{'rho->|M|':>10}")
        for d in GRIDS:
            m = h // d
            if m < 8:
                continue
            sc, pc, ssc = coarsen(sec, px, sess, d)
            st, en, pv = sweep_windows(sc, pc, ssc, m, h)
            if len(st) < 500:
                P(f"  {d:>6}{m:>9}{len(st):>10}   too few windows")
                continue
            cumabs = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(pc)))])
            net = np.abs(pc[en] - pc[st])
            path = cumabs[en] - cumabs[st]
            eff = np.where(path > 0, net / np.maximum(path, 1e-15), np.nan)
            # the preceding run, known at entry
            net_p = np.abs(pc[pv + m] - pc[pv])
            path_p = cumabs[pv + m] - cumabs[pv]
            eff_p = np.where(path_p > 0, net_p / np.maximum(path_p, 1e-15), np.nan)
            fin = np.isfinite(eff) & np.isfinite(eff_p)
            rw = 1.0 / np.sqrt(m)
            e_mean = float(np.nanmean(eff[fin]))

            # VARIANCE RATIO, ON THE SAME WINDOW POPULATION. The first version took it from
            # the whole RTH coarse series while efficiency came from the SUBSET of windows
            # that passed the span/session/predecessor filter -- and the identity gate below
            # caught the mismatch (0.8196 against 0.7871). Both now read the steps INSIDE
            # the accepted windows, so the identity closes to float precision instead of to
            # a tolerance.
            inside = st[fin][:, None] + np.arange(1, m + 1, dtype=np.int64)[None, :]
            r_in = (pc[inside] - pc[inside - 1]).ravel()
            signed_net = (pc[en] - pc[st])[fin]
            vr = float(np.var(signed_net, ddof=1) / (m * np.var(r_in, ddof=1)))

            # THE 1/sqrt(m) BENCHMARK IS ONLY RIGHT FOR GAUSSIAN STEPS, and one-second ES
            # steps are mostly ZERO with occasional one-tick jumps. In general, for iid
            # steps, E[path] = m*E|r| and E|net| = sigma*sqrt(m)*sqrt(2/pi), so
            #     efficiency = C / sqrt(m),  C = sqrt(2/pi) * sigma_r / E|r|
            # and C is 1 ONLY when sigma/E|r| takes its Gaussian value sqrt(pi/2). So the
            # benchmark must be measured per grid, not assumed. The check that this is the
            # right correction: corrected ratio should equal sqrt(variance ratio).
            e_abs_r = float(np.mean(np.abs(r_in)))
            sd_r = float(np.std(r_in, ddof=1))
            C = np.sqrt(2.0 / np.pi) * sd_r / e_abs_r if e_abs_r > 0 else np.nan
            rw_corr = C / np.sqrt(m)
            ratio_corr = e_mean / rw_corr if rw_corr > 0 else np.nan

            # MEAN-OF-RATIOS IS NOT RATIO-OF-MEANS. The derivation above is about E|net| and
            # E[path]; `eff.mean()` averages the ratio, and for positively correlated
            # numerator and denominator that sits systematically BELOW E|net|/E[path].
            # sqrt(VR) is a ratio-of-variances quantity, so the ratio-of-means form is what
            # it should be compared against -- otherwise the two instruments appear to
            # disagree by a constant that is purely Jensen.
            eff_rom = float(np.mean(net[fin]) / np.mean(path[fin]))
            ratio_rom = eff_rom / rw_corr if rw_corr > 0 else np.nan

            # AND THE LAST LEAK IS FAT TAILS. E|net| = sigma_net*sqrt(2/pi) holds for a
            # GAUSSIAN net; a leptokurtic one has E|X|/sigma BELOW sqrt(2/pi). So the two
            # instruments are related by
            #     efficiency/(C/sqrt(m)) = sqrt(VR) * (E|net|/sigma_net)/sqrt(2/pi)
            # and that is an IDENTITY, not an approximation -- so it is asserted, and it is
            # what turns "the two roughly agree" into a closed loop.
            sd_net = float(np.std(signed_net, ddof=1))
            gauss = (float(np.mean(np.abs(signed_net))) / sd_net) / np.sqrt(2.0 / np.pi) \
                if sd_net > 0 else np.nan
            pred = np.sqrt(vr) * gauss
            if np.isfinite(pred) and abs(ratio_rom - pred) > 1e-9:
                raise GateError(
                    f"[IDENTITY] window {h}s grid {d}s: efficiency/(C/sqrt m) = "
                    f"{ratio_rom:.4f} but sqrt(VR)*non-Gaussianity = {pred:.4f}. The two "
                    f"instruments are algebraically the same quantity; a gap means one of "
                    f"VR, C or the Gaussian factor is computed on a different population")

            rho_p = float(np.corrcoef(eff_p[fin], eff[fin])[0, 1])
            rho_m = float(np.corrcoef(eff_p[fin], net[fin])[0, 1])
            P(f"  {d:>6}{m:>9}{int(fin.sum()):>10,}{e_mean:>8.4f}{rw:>11.4f}"
              f"{e_mean/rw:>8.2f}{C:>7.2f}{ratio_corr:>9.2f}{ratio_rom:>9.2f}"
              f"{np.sqrt(vr):>9.2f}{vr:>8.2f}{rho_p:>+11.3f}{rho_m:>+10.3f}")
            out["cells"].append({
                "window_s": h, "grid_s": d, "steps": int(m),
                "n_windows": int(fin.sum()), "mean_efficiency": e_mean,
                "naive_random_walk_efficiency_1_over_sqrt_m": float(rw),
                "efficiency_over_naive_benchmark": e_mean / rw,
                "step_shape_C_sqrt2overpi_times_sd_over_meanabs": float(C),
                "corrected_benchmark_C_over_sqrt_m": float(rw_corr),
                "efficiency_over_CORRECTED_benchmark": float(ratio_corr),
                "efficiency_ratio_of_means": eff_rom,
                "ratio_of_means_over_CORRECTED_benchmark": float(ratio_rom),
                "sqrt_variance_ratio": float(np.sqrt(vr)),
                "non_gaussianity_factor_EabsNet_over_sigma_over_sqrt2pi": float(gauss),
                "identity_sqrtVR_times_nongaussianity": float(pred),
                "variance_ratio": vr,
                "persistence_rho_trailing_eff_to_forward_eff": rho_p,
                "rho_trailing_eff_to_forward_abs_move": rho_m,
                "se_rho": float(1.0 / np.sqrt(max(int(fin.sum()), 1)))})
        P("")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D471 amendment: path efficiency on COARSER grids, which D471 left "
                      "open. Two independent instruments per cell -- efficiency over its "
                      "random-walk benchmark, and the variance ratio. A measurement; no "
                      "signal, no edge, nothing admitted.",
           "source": "D465 v2 windowed ES front-month ticks, RTH only, 2025-09-11..2026-09-10",
           "note": "efficiency/(1/sqrt(m)) and the variance ratio both read 1.00 for a "
                   "driftless walk; they are computed from the same prices but are not the "
                   "same statistic, so agreement between them is the check",
           "sweep": out}
    if as_json:
        p = REPO / "data" / "d471_path_efficiency_grid_sweep.json"
        p.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"wrote {p.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------- volume clock

def clock_cell(px_c, sec_c, sess_c, m: int, span_key=None, span_target=None,
               span_tol=0.15):
    """One cell of the sweep, identical arithmetic for a time clock and a volume clock.

    Returns a dict of every statistic, or None if too few windows survive.
    """
    n = len(px_c)
    starts = np.arange(0, n - m - 1, m, dtype=np.int64)
    ends = starts + m
    ok = sess_c[starts] == sess_c[ends]
    if span_key is not None:                      # a TIME clock also checks its own span
        ok &= np.abs((span_key[ends] - span_key[starts]) - span_target) \
            <= span_tol * span_target
    prev = starts - m
    okp = np.zeros(len(starts), dtype=bool)
    okp[1:] = ok[:-1] & (sess_c[np.maximum(prev[1:], 0)] == sess_c[starts[1:]])
    keep = ok & okp
    st, en, pv = starts[keep], ends[keep], prev[keep]
    if len(st) < 300:
        return None

    cumabs = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(px_c)))])
    net = np.abs(px_c[en] - px_c[st])
    path = cumabs[en] - cumabs[st]
    eff = np.where(path > 0, net / np.maximum(path, 1e-15), np.nan)
    net_p = np.abs(px_c[pv + m] - px_c[pv])
    path_p = cumabs[pv + m] - cumabs[pv]
    eff_p = np.where(path_p > 0, net_p / np.maximum(path_p, 1e-15), np.nan)
    fin = np.isfinite(eff) & np.isfinite(eff_p)
    if fin.sum() < 300:
        return None

    inside = st[fin][:, None] + np.arange(1, m + 1, dtype=np.int64)[None, :]
    r_in = (px_c[inside] - px_c[inside - 1]).ravel()
    signed_net = (px_c[en] - px_c[st])[fin]
    vr = float(np.var(signed_net, ddof=1) / (m * np.var(r_in, ddof=1)))

    e_abs_r, sd_r = float(np.mean(np.abs(r_in))), float(np.std(r_in, ddof=1))
    C = np.sqrt(2.0 / np.pi) * sd_r / e_abs_r
    rw_corr = C / np.sqrt(m)
    eff_rom = float(np.mean(net[fin]) / np.mean(path[fin]))
    ratio_rom = eff_rom / rw_corr

    sd_net = float(np.std(signed_net, ddof=1))
    gauss = (float(np.mean(np.abs(signed_net))) / sd_net) / np.sqrt(2.0 / np.pi)
    pred = np.sqrt(vr) * gauss
    if abs(ratio_rom - pred) > 1e-9:
        raise GateError(f"[IDENTITY] m={m}: {ratio_rom:.6f} vs sqrt(VR)*nonGauss "
                        f"{pred:.6f} -- the two instruments are the same quantity")

    net_t = net[fin] / TICK_PTS
    kurt = float(np.mean(((signed_net - signed_net.mean()) / sd_net) ** 4))
    mins = (sec_c[en] - sec_c[st])[fin] / 60.0
    return {"steps": m, "n_windows": int(fin.sum()),
            "mean_efficiency": float(np.nanmean(eff[fin])),
            "efficiency_ratio_of_means": eff_rom,
            "step_shape_C": float(C),
            "efficiency_over_corrected_benchmark": float(ratio_rom),
            "variance_ratio": vr, "sqrt_variance_ratio": float(np.sqrt(vr)),
            "non_gaussianity_factor": float(gauss),
            "kurtosis_of_window_return": kurt,
            "mean_abs_move_ticks": float(net_t.mean()),
            "breakeven_accuracy_MES": float(breakeven_accuracy(
                1.009 + COMMISSION_RT_MES / TICK_USD_MES, net_t.mean())),
            "persistence_rho_eff": float(np.corrcoef(eff_p[fin], eff[fin])[0, 1]),
            "rho_eff_to_forward_abs": float(np.corrcoef(eff_p[fin], net[fin])[0, 1]),
            # THE HEADLINE A/B: does the clock keep the VOLATILITY conditioner alive?
            "persistence_rho_abs_move": float(np.corrcoef(net_p[fin], net[fin])[0, 1]),
            "se_rho": float(1.0 / np.sqrt(int(fin.sum()))),
            "wallclock_minutes_mean": float(mins.mean()),
            "wallclock_minutes_p10": float(np.quantile(mins, .10)),
            "wallclock_minutes_p90": float(np.quantile(mins, .90))}


def do_volume_clock(as_json: bool) -> int:
    """Path efficiency on a VOLUME clock -- sample every V contracts, not every N seconds.

    The theory is Clark (1973) and the volume-clock literature: price moves on transactions,
    not on the wall clock, so returns sampled in volume time should be closer to iid
    Gaussian and time-clock sampling smears structure across quiet and busy periods.

    THERE IS A SHARP PREDICTION AGAINST US HERE, and it is the reason to run it. Volatility
    clusters IN TIME -- that clustering is exactly why the volatility conditioner reached
    rho = +0.31 and cut the breakeven bar to 54.8%. A volume clock ABSORBS that clustering
    by construction: a busy period produces more bars rather than bigger ones. So the volume
    clock may well destroy the one conditioner that worked. That is measured, not assumed,
    by carrying `persistence_rho_abs_move` on both clocks in the same run.
    """
    sec, px, sz, sess = load_trades_rth()
    tot = int(sz.sum())
    P(f"RTH trades {len(px):,}  volume {tot:,} contracts  "
      f"{len(np.unique(sess)):,} sessions\n")

    # Calibrate the bar so a volume bar is, ON AVERAGE, one 15-minute wall-clock bar. RTH is
    # 390 minutes, so 26 bars a session. Same bar COUNT is what makes the A/B fair.
    n_bars = len(np.unique(sess)) * 26
    V = tot / n_bars
    P(f"volume bar calibrated to the 15-minute bar COUNT: {n_bars:,} bars -> "
      f"V = {V:,.0f} contracts\n")

    MS = (900, 180, 60, 15)
    cumvol = np.cumsum(sz) - sz          # volume BEFORE each trade, so the clock starts at 0
    rows = {"volume": [], "time": []}

    P("  clock    steps   bar unit        windows  wall-clock min   E|M|tk  p_be    "
      "eff    C   corr'd    VR   kurt   rho|M|  rhoEff")
    for m in MS:
        # --- VOLUME clock: fine grid every V/m contracts
        v = max(int(round(V / m)), 1)
        pv_, sv_, ssv_ = clock_sample(cumvol, px, sec, sess, v)
        cv = clock_cell(pv_, sv_, ssv_, m)
        # --- TIME clock: fine grid every 900/m seconds, window 900 s
        d = max(900 // m, 1)
        pt_, stt_, sst_ = clock_sample(sec, px, sec, sess, d)
        ct = clock_cell(pt_, stt_, sst_, m, span_key=stt_, span_target=m * d)
        for tag, c, unit in (("volume", cv, f"{v} contracts"),
                             ("time", ct, f"{d} s")):
            if c is None:
                P(f"  {tag:7}{m:>7}   {unit:14} too few windows")
                continue
            c["clock"] = tag
            c["bar_unit"] = unit
            rows[tag].append(c)
            P(f"  {tag:7}{m:>7}   {unit:14}{c['n_windows']:>8,}   "
              f"{c['wallclock_minutes_mean']:>5.1f} "
              f"[{c['wallclock_minutes_p10']:>4.1f},{c['wallclock_minutes_p90']:>5.1f}]"
              f"{c['mean_abs_move_ticks']:>8.1f}{c['breakeven_accuracy_MES']:>7.1%}"
              f"{c['mean_efficiency']:>8.4f}{c['step_shape_C']:>6.2f}"
              f"{c['efficiency_over_corrected_benchmark']:>8.2f}"
              f"{c['variance_ratio']:>7.2f}{c['kurtosis_of_window_return']:>7.1f}"
              f"{c['persistence_rho_abs_move']:>+9.3f}{c['persistence_rho_eff']:>+8.3f}")
        P("")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D471 amendment 2: path efficiency and the volatility conditioner on a "
                      "VOLUME clock against the wall clock, same bar count, same arithmetic. "
                      "A measurement; no signal, no edge, nothing admitted.",
           "source": "D465 v2 windowed ES front-month ticks, RTH only, 2025-09-11..2026-09-10",
           "bar_calibration": {"sessions": int(len(np.unique(sess))),
                               "bars_per_session": 26, "total_bars": int(n_bars),
                               "contracts_per_bar": float(V),
                               "total_contracts": tot},
           "note": "rho|M| is the persistence of the absolute move -- the volatility "
                   "conditioner that reached +0.31 on the wall clock and cut the breakeven "
                   "bar to 54.8%. A volume clock absorbs volatility clustering by "
                   "construction, so this column is the point of the comparison.",
           "rows": rows}
    if as_json:
        p = REPO / "data" / "d471_volume_clock.json"
        p.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"wrote {p.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------- measurement

def do_measure(as_json: bool) -> int:
    if not TICKS.exists():
        raise SystemExit(f"missing {TICKS}; run d465 --extract")
    z = np.load(TICKS)
    if "iid" not in z:
        raise GateError("[INPUT] cache carries no instrument_id -- this is the v1 cache "
                        "that pooled expiries; re-run d465 --extract")
    ts, iid = z["ts"], z["iid"]
    px = z["px"].astype(np.float64) * PX_SCALE
    bid, ask = z["bid"], z["ask"]

    # quote filter FIRST, and it is the same one D465 needed after reading 875-tick spreads
    good = ((px > 0) & (bid != INT64_SENTINEL) & (ask != INT64_SENTINEL)
            & (bid > 0) & (ask > 0) & (ask >= bid))
    dropped = int((~good).sum())
    ts, px, iid = ts[good], px[good], iid[good]
    half_tk = ((ask[good] - bid[good]).astype(np.float64) * PX_SCALE) / TICK_PTS / 2.0
    P(f"ES trades {len(px):,}  ({dropped:,} dropped on the quote filter)")

    sec = (ts // 1_000_000_000).astype(np.int64)
    # one expiry per second, or a cross-record measurement is reading the calendar basis
    _, f_ = np.unique(sec, return_index=True)
    i64 = iid.astype(np.int64)
    if int((np.maximum.reduceat(i64, f_) != np.minimum.reduceat(i64, f_)).sum()):
        raise GateError("[INPUT] a second carries two expiries")

    # collapse to the one-second grid: LAST trade in each second
    uniq_sec, first = np.unique(sec, return_index=True)
    last = np.append(first[1:], len(px)) - 1
    g_px, g_id, g_half = px[last], i64[last], half_tk[last]
    cum = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(g_px)))])
    P(f"one-second grid: {len(uniq_sec):,} seconds\n")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D471: the spread PAID in the bucket being traded, and whether path "
                      "efficiency forecasts itself well enough to be a conditioner. A "
                      "measurement -- no signal, no edge, no Sharpe, nothing admitted.",
           "source": "D465 v2 windowed ES front-month ticks, 2025-09-11..2026-09-10",
           "grid": "one-second last trade; non-overlapping windows",
           "resolution_warning": "path length and therefore efficiency are grid-dependent; "
                                 "only rankings on this one-second grid and the persistence "
                                 "correlation are claimed",
           "quote_records_dropped": dropped,
           "by_horizon": {}}

    for h in HORIZONS:
        lab = f"{h//60}m"
        uniq, st, en = blocks_of(uniq_sec, h)
        span = uniq_sec[en] - uniq_sec[st]
        npts = en - st + 1
        # A BLOCK MUST ACTUALLY SPAN ITS OWN WIDTH. The first run allowed span >= 0.5h and
        # the blocks averaged 534 seconds of trading against a 900-second width -- so it
        # measured ~9-minute moves and labelled them 15-minute ones, understating E|M| by
        # a third and inflating every breakeven. The tell was arithmetic that was there to
        # be done: 23,224 blocks x 900 s = 20.9M seconds against a 12.4M-second grid.
        valid = ((span >= 0.95 * h) & (npts >= 30)
                 & (np.maximum.reduceat(g_id, st) == np.minimum.reduceat(g_id, st)))
        # and its immediate predecessor must exist and be valid, to condition causally
        prev_ok = np.zeros(len(uniq), dtype=bool)
        has_prev = np.concatenate([[False], uniq[1:] == uniq[:-1] + 1])
        prev_ok[1:] = valid[:-1]
        use = valid & has_prev & prev_ok
        k = np.flatnonzero(use)
        if len(k) < 2000:
            P(f"{lab}: only {len(k)} usable blocks, skipped")
            continue

        entry, exitp = g_px[st[k]], g_px[en[k]]
        fwd_signed = (exitp - entry) / TICK_PTS
        fwd_abs = np.abs(fwd_signed)
        fwd_len = (cum[en[k]] - cum[st[k]]) / TICK_PTS
        fwd_eff = np.where(fwd_len > 0, fwd_abs / np.maximum(fwd_len, 1e-12), np.nan)
        # the PREVIOUS block, known in full at entry
        kp = k - 1
        prv_abs = np.abs(g_px[en[kp]] - g_px[st[kp]]) / TICK_PTS
        prv_len = (cum[en[kp]] - cum[st[kp]]) / TICK_PTS
        prv_eff = np.where(prv_len > 0, prv_abs / np.maximum(prv_len, 1e-12), np.nan)
        # adverse excursion from ENTRY, both sides
        blk_max = np.maximum.reduceat(g_px, st)[k]
        blk_min = np.minimum.reduceat(g_px, st)[k]
        adv_long = (entry - blk_min) / TICK_PTS
        adv_short = (blk_max - entry) / TICK_PTS
        # THE ADVERSE EXCURSION ON THE SIDE THAT WON. min(long, short) takes the gentler
        # side whichever way price went, which is not a trade anyone can place; the
        # question is "having called the direction right, how much pain came first".
        adv_correct = np.where(fwd_signed > 0, adv_long, adv_short)
        # the spread actually quoted at BOTH ends of the window
        cost_spread = g_half[st[k]] + g_half[en[k]]
        comm_tk = COMMISSION_RT_MES / TICK_USD_MES

        fin = np.isfinite(prv_eff) & np.isfinite(fwd_eff)

        # SESSION, because the overnight weighting is the whole gap with D469. D469 required
        # BOTH the entry second and the exit second to carry a trade, which silently drops
        # quiet overnight windows and activity-weights its sample; these blocks tile every
        # calendar block equally, dead Asian-hours blocks included. Neither is wrong -- they
        # answer different questions -- so the confound is removed by splitting rather than
        # by arguing about which mean is "the" mean.
        import pandas as pd
        et = pd.DatetimeIndex(pd.to_datetime(uniq_sec[st[k]], unit="s", utc=True)) \
            .tz_convert("America/New_York")
        et_min = et.hour.values * 60 + et.minute.values
        rth = (et_min >= 9 * 60 + 30) & (et_min < 16 * 60)
        P(f"=== {lab} holds, {len(k):,} non-overlapping windows "
          f"({fin.sum():,} with a finite efficiency pair; {int(rth.sum()):,} RTH) ===")

        # ---- STAGE 0: does either conditioner forecast ITSELF?
        r_vol = float(np.corrcoef(prv_abs[fin], fwd_abs[fin])[0, 1])
        r_eff = float(np.corrcoef(prv_eff[fin], fwd_eff[fin])[0, 1])
        r_cross = float(np.corrcoef(prv_eff[fin], fwd_abs[fin])[0, 1])
        n_f = int(fin.sum())
        se = 1.0 / np.sqrt(n_f)
        P(f"  STAGE 0, persistence on independent windows (SE ~ {se:.4f}):")
        P(f"    trailing |move|  -> forward |move|  rho {r_vol:+.3f}  "
          f"({abs(r_vol)/se:>5.1f} SE)")
        P(f"    trailing eff     -> forward eff     rho {r_eff:+.3f}  "
          f"({abs(r_eff)/se:>5.1f} SE)")
        P(f"    trailing eff     -> forward |move|  rho {r_cross:+.3f}  "
          f"({abs(r_cross)/se:>5.1f} SE)")

        # ---- the spread where the moves are, by trailing-volatility quintile
        def quintile_table(key: np.ndarray, keyname: str, mask: np.ndarray) -> list:
            kk = key[mask]
            edges = np.quantile(kk, np.linspace(0, 1, NQ + 1))
            out = []
            P(f"\n  by {keyname} quintile -- and the bar RE-COSTED on the spread each "
              f"bucket actually quotes:")
            P(f"  {'q':>3}{'n':>8}{'trail':>8}{'fwd|M|':>8}{'fwd eff':>9}{'rw eff':>8}"
              f"{'ratio':>7}{'spr(tk)':>9}{'cost':>7}{'p_be':>8}{'D469 p_be':>11}"
              f"{'adv/|M|':>9}")
            for q in range(NQ):
                m = mask.copy()
                sel = ((kk >= edges[q]) & (kk <= edges[q + 1])) if q == NQ - 1 else \
                      ((kk >= edges[q]) & (kk < edges[q + 1]))
                m[np.flatnonzero(mask)[~sel]] = False
                if m.sum() < 200:
                    continue
                e_abs = float(fwd_abs[m].mean())
                spr = float(cost_spread[m].mean())
                cost_true = spr + comm_tk
                cost_d469 = 1.009 + comm_tk          # D469's UNCONDITIONAL crossing
                p_true = float(breakeven_accuracy(cost_true, e_abs))
                p_d469 = float(breakeven_accuracy(cost_d469, e_abs))
                adv = float(adv_correct[m].mean())
                out.append({"quintile": q + 1, "n": int(m.sum()),
                            "trailing_mean": float(key[m].mean()),
                            "fwd_mean_abs_ticks": e_abs,
                            "fwd_mean_efficiency": float(np.nanmean(fwd_eff[m])),
                            "spread_both_ends_ticks": spr,
                            "cost_ticks_true": cost_true,
                            "breakeven_accuracy_true": p_true,
                            "breakeven_accuracy_at_d469_unconditional_spread": p_d469,
                            "mean_adverse_over_move": adv / e_abs})
                # THE BENCHMARK THAT MAKES AN EFFICIENCY NUMBER MEAN ANYTHING. A driftless
                # walk of n steps has efficiency 1/sqrt(n) exactly, so the ratio below is
                # the only scale-free reading: 1.00 means indistinguishable from a coin.
                steps = float((en[k][m] - st[k][m]).mean())
                rw = 1.0 / np.sqrt(max(steps, 1.0))
                eff_m = float(np.nanmean(fwd_eff[m]))
                out[-1]["random_walk_efficiency_1_over_sqrt_steps"] = float(rw)
                out[-1]["efficiency_over_random_walk"] = eff_m / rw
                P(f"  {q+1:>3}{m.sum():>8,}{key[m].mean():>8.1f}{e_abs:>8.1f}"
                  f"{eff_m:>9.3f}{rw:>8.3f}{eff_m/rw:>7.2f}{spr:>9.3f}{cost_true:>7.2f}"
                  f"{p_true:>8.1%}{p_d469:>11.1%}{adv/e_abs:>9.2f}")
            return out

        t_vol = quintile_table(prv_abs, "TRAILING |move|, ALL HOURS", fin.copy())
        t_vol_rth = quintile_table(prv_abs, "TRAILING |move|, RTH ONLY (09:30-16:00 ET)",
                                   fin & rth)
        t_eff = quintile_table(prv_eff, "TRAILING efficiency, ALL HOURS", fin.copy())

        # ---- the 2D cross: does efficiency add anything ON TOP of volatility?
        P(f"\n  top-volatility windows SPLIT by trailing efficiency "
          f"(does eff add to vol?):")
        hi_vol = fin & (prv_abs >= np.quantile(prv_abs[fin], 0.8))
        cross = []
        med_eff = float(np.median(prv_eff[hi_vol]))
        for tag, m in (("eff BELOW median", hi_vol & (prv_eff < med_eff)),
                       ("eff ABOVE median", hi_vol & (prv_eff >= med_eff))):
            if m.sum() < 200:
                continue
            e_abs = float(fwd_abs[m].mean())
            spr = float(cost_spread[m].mean())
            p_true = float(breakeven_accuracy(spr + comm_tk, e_abs))
            adv = float(adv_correct[m].mean())
            cross.append({"cell": tag, "n": int(m.sum()), "fwd_mean_abs_ticks": e_abs,
                          "fwd_mean_efficiency": float(np.nanmean(fwd_eff[m])),
                          "spread_both_ends_ticks": spr,
                          "breakeven_accuracy_true": p_true,
                          "mean_adverse_over_move": adv / e_abs})
            P(f"    {tag:20} n {m.sum():>7,}  fwd|M| {e_abs:>6.1f}  "
              f"fwd eff {np.nanmean(fwd_eff[m]):.3f}  spr {spr:.3f}  "
              f"p_be {p_true:>6.1%}  adv/|M| {adv/e_abs:.2f}")

        res["by_horizon"][h] = {
            "n_windows": int(len(k)), "n_finite_pairs": n_f,
            "persistence": {"trailing_abs_to_forward_abs": r_vol,
                            "trailing_eff_to_forward_eff": r_eff,
                            "trailing_eff_to_forward_abs": r_cross,
                            "se": float(se)},
            "commission_ticks": comm_tk,
            "by_trailing_volatility": t_vol,
            "by_trailing_volatility_RTH": t_vol_rth,
            "n_rth_windows": int(rth.sum()),
            "by_trailing_efficiency": t_eff,
            "top_vol_split_by_efficiency": cross,
        }
        P("")

    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"wrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--grid-sweep", action="store_true")
    ap.add_argument("--volume-clock", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.measure:
        return do_measure(a.json)
    if a.grid_sweep:
        return do_grid_sweep(a.json)
    if a.volume_clock:
        return do_volume_clock(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
