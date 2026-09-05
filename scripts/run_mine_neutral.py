"""D288 Phase 2 -- the 31-candidate two-leg event screen.

    uv run python scripts/run_mine_neutral.py --selftest
    uv run python scripts/run_mine_neutral.py

PRE-REGISTERED AT `fa098a2`, WHICH WAS COMMITTED BEFORE THIS FILE EXISTED (R8).
The candidate list, the gates, the shape predictions and the stop condition are
all fixed there. This runner may not add a candidate, and if it did the ledger in
that record would be wrong -- so `CANDIDATES` is asserted against the
pre-registered count of 31 at import.

THE INSTRUMENT IS D286'S, NOT A NEW ONE. Every fresh entry into the bottom N or
top N is an event, TAKEN WHETHER OR NOT ANYTHING ELSE IS OPEN -- no slots to
compete for, no exit caused by another name. That is the point: eight
constructions have closed here and D286 established the failure is in the signal,
so measuring through a portfolio would put the construction back in the way.

THE t IS COMPUTED ACROSS BARS, ONE OBSERVATION PER BAR. Events overlap by
construction. D271 counted overlapping windows as independent trades and turned a
`t` of 2.31 into 5.30.

BOTH LEGS ARE REPORTED SEPARATELY, ALWAYS. D286's headline is why: `hist_L`'s
spread was +56.3 bp with BOTH LEGS POSITIVE at every horizon and every N, which
means it sorts "rises less" from "rises more" rather than winners from losers. A
spread alone hides which of those you have, and only one of them is a short.

WHAT THIS RUNNER DOES NOT DO. It does not apply the best-of-31 floor (gate A) or
the mechanism re-derivation (gate B). Those read this output; keeping them in
separate files stops a floor from being quietly recomputed once the numbers are
visible.
"""

from __future__ import annotations

import argparse
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
SP = _load("d285sp", "d285_spread_estimate.py")
FN = _load("fast_null", "fast_null.py")
RF = _load("ragged_features", "ragged_features.py")
PS = _load("ragged_price_scores", "ragged_price_scores.py")
PR = _load("ragged_profile", "ragged_profile.py")
VS = _load("ragged_vol_scores", "ragged_vol_scores.py")
SS = _load("ragged_session_scores", "ragged_session_scores.py")
RP = B.RP

OUT = REPO / "data" / "d288_mine.json"
# temp/ is git-ignored and this is rebuildable, so it is the right shelf
# for 1.6 GB of derived arrays -- see temp/README.md.
CACHE = REPO / "temp" / "d288_scores.npz"
N_LEVELS = (10, 25, 50)
HORIZONS = (1, 2, 3, 5, 8, 10, 13, 16, 20, 25, 30, 40)
MAX_H = max(HORIZONS)
MIN_BARS = 100                  # D286's threshold for reporting a horizon at all
N_PREREGISTERED = 31            # `docs/decisions/D288-the-mine-with-a-mechanism-gate.md`

# The axis each candidate belongs to. Gate B checks a SHAPE PREDICTION PER AXIS,
# so this mapping is part of the pre-registration and not a display convenience.
AXES = {
    "A": ("hist_L", "md", "macd_hist", "macd_line", "trailing_return"),
    "B": RF.INTRABAR_SCORES,
    "C": RF.VOL_SCORES,
    "D": PR.PROFILE_SCORES,
    "E": VS.VOL_LEVEL_SCORES,
    "F": SS.SESSION_SCORES,
}
CANDIDATES = tuple(c for ax in "ABCDEF" for c in AXES[ax])
AXIS_OF = {c: ax for ax, cs in AXES.items() for c in cs}
assert len(CANDIDATES) == N_PREREGISTERED, (
    f"{len(CANDIDATES)} candidates but D288 pre-registered {N_PREREGISTERED}; "
    "the ledger and the best-of-N floor in that record are both wrong if this "
    "runner changes the count")
assert len(set(CANDIDATES)) == N_PREREGISTERED, "duplicate candidate name"


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------
def _cache_key(fixture):
    """Fixture identity plus every module that computes a candidate.

    A cache keyed on the fixture alone would serve stale scores the moment an
    estimator changed, which is worse than no cache -- the numbers would look
    fine and belong to code that no longer exists.
    """
    st = Path(fixture).stat()
    parts = [f"{Path(fixture).name}:{st.st_size}:{int(st.st_mtime)}"]
    for f in ("run_book_single_names.py", "ragged_features.py",
              "ragged_price_scores.py", "ragged_profile.py",
              "ragged_vol_scores.py", "ragged_session_scores.py",
              "d285_spread_estimate.py",
              "ragged_panel.py"):  # D334
        parts.append(f"{f}:{int((REPO / 'scripts' / f).stat().st_mtime)}")
    parts.append("|".join(CANDIDATES))
    return "\n".join(parts)


def build_scores(panel, cleaned, g, live, workers=None, use_cache=True):
    """Every candidate on one panel, UNLAGGED. `screen` lags, once, itself.

    THREADED ACROSS FAMILIES, AND CACHED ACROSS RUNS. The screen, gate 0 and
    gate A each need all 31, and rebuilding them three times is three times the
    only genuinely expensive step: `VolumeProfileSensor.density` is pure Python
    over the lookback window and D's cadence is one rebuild PER BAR. The four
    numpy families cost under a second each and overlap with it for free.
    """
    key = _cache_key(B.FIXTURE)
    if use_cache and CACHE.exists():
        z = np.load(CACHE, allow_pickle=False)
        if str(z["key"]) == key:
            print(f"  scores from cache {CACHE.relative_to(REPO)} "
                  f"({CACHE.stat().st_size / 1e9:.2f} GB)", flush=True)
            return ({c: z[c] for c in CANDIDATES}, z["warm"],
                    [k for k in z.files if k not in set(CANDIDATES) | {"key", "warm"}])
        print(f"  cache MISS -- fixture or an estimator module changed", flush=True)

    vol, vpx = RF.volume_grids(panel, cleaned, live=live)
    out, timings = {}, {}

    def fam(name, fn):
        t = time.time()
        r = fn()
        timings[name] = time.time() - t
        return r

    jobs = {
        # A1-A2 also carry `warm`, which is the shared base for all 31.
        "A12": lambda: B.signals_ragged(panel, cleaned, 0),
        "A345": lambda: PS.price_scores(panel, cleaned, live=live),
        "B": lambda: RF.intrabar_scores(g, live),
        "C": lambda: RF.volume_scores(vol, vpx, panel.total_log_returns, live),
        # REBUILD_EVERY_DAILY = 1 is left at its default and that choice binds:
        # 51,895 of PG's 54,004 cells move between cadence 1 and cadence 26.
        # It is also the whole cost of this function.
        "D": lambda: PR.build_profile_scores(panel, cleaned, vol, 0, live=live),
        "E": lambda: VS.vol_level_scores(
            g, live, SP.corwin_schultz(g["high"], g["low"], live)),
        "F": lambda: SS.session_scores(g, live),
    }
    print(f"  building {len(jobs)} score families on threads", flush=True)
    t0 = time.time()
    res = FN.parallel_map(lambda k, f: fam(k, f), list(jobs.items()),
                          workers=workers or len(jobs))
    print(f"  families: " + "  ".join(f"{k} {timings[k]:.0f}s"
                                      for k in sorted(timings, key=timings.get))
          + f"   wall {time.time() - t0:.0f}s", flush=True)

    md, hs, g_lo, g_hi, i_lo, atr, warm = res["A12"]
    sc = {"hist_L": hs, "md": md}

    # A3-A5 ARE MASKED BY THEIR OWN WARM-UP, NOT BY D256'S. `price_scores`
    # returns a per-score `warm` counted in the SYMBOL'S OWN BARS because the
    # five have different seeds -- `impulse_nodz` needs 992 own bars and 34.7% of
    # its finite values on this panel are seed transient, `macd_line` loses
    # 13.8%, and `rsi`/`trailing_return` lose nothing. Ranking on a seed
    # transient is ranking on the estimator's start-up, not on the market.
    price, pwarm = res["A345"]
    for k in ("macd_hist", "macd_line", "trailing_return"):
        sc[k] = np.where(pwarm[k], price[k], np.nan)

    sc.update(res["B"])
    sc.update(res["C"])
    prof, census = res["D"]
    sc.update(prof)
    print(f"  volume profile census: {census}", flush=True)
    sc.update(res["E"])
    sc.update(res["F"])

    missing = [c for c in CANDIDATES if c not in sc]
    assert not missing, f"candidates not built: {missing}"
    extra = [k for k in sc if k not in set(CANDIDATES)]
    out = {c: sc[c] for c in CANDIDATES}

    if use_cache:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        t = time.time()
        np.savez(CACHE, key=np.array(key), warm=warm, **out)
        print(f"  cached {CACHE.stat().st_size / 1e9:.2f} GB to "
              f"{CACHE.relative_to(REPO)} in {time.time() - t:.0f}s "
              f"(temp/ is git-ignored and rebuildable)", flush=True)
    return out, warm, extra


def forward_returns(panel, live):
    """Cumulative SIMPLE return from bar t through t+k-1, on the name's own bars.

    Stored float32, accumulated float64. The reported quantity is a mean over
    thousands of bars printed to 0.1 bp; float32 carries ~1e-9 absolute on a 1e-2
    return, four orders inside that. The alternative was 632 MB of float64 shared
    across 31 worker threads.
    """
    logr = panel.total_log_returns
    T = live.shape[1]
    fwd, acc, okk = {}, np.zeros_like(logr), live.copy()
    for k in range(1, MAX_H + 1):
        acc[:, :T - k + 1] += logr[:, k - 1:]
        okk[:, :T - k + 1] &= live[:, k - 1:]
        if k in HORIZONS:
            fwd[k] = np.where(okk, np.expm1(acc), np.nan).astype(np.float32)
    return fwd


def legs(score, base, N):
    """Fresh entries into the bottom N (long) and top N (short) of the LAGGED score.

    THE LAG IS HERE AND NOWHERE ELSE. Every score module returns unlagged and says
    so; `C.lag1` is D279's, the function that exists because the first version of
    `top_n` ranked on bar t's score to earn bar t's return and 93% of that study's
    apparent edge was the bug.

    ONE COLUMN SORT FOR THE WHOLE PANEL, not a Python loop over 4,187 bars.
    `np.argsort(..., axis=0)` sorts every bar inside one C call and puts NaN
    last, so the bottom N are rows 0..N-1 and the top N are rows cnt-N..cnt-1
    where `cnt` is that bar's finite count. Measured against the loop it
    replaces by `legs_loop` in the self-test, which is also the lag audit's
    second implementation -- gate A calls this a few thousand times and the loop
    version made the floor a multi-hour run.
    """
    order, cnt = rank_columns(score, base)
    return legs_from_order(order, cnt, N, base.shape)


def rank_columns(score, base):
    """Sort each bar's qualifying names ONCE. THE LAG IS HERE AND NOWHERE ELSE.

    Split out from `legs` because the sort does not depend on N and the study
    reads three N off the same ranking -- hoisting identical arithmetic out of a
    loop, which is the only kind of optimisation CLAUDE.md allows (it changes no
    float, it just stops recomputing one). Gate A does this 31 times per draw
    instead of 93.
    """
    v = np.where(base, C.lag1(score), np.nan)
    return np.argsort(v, axis=0, kind="stable"), np.isfinite(v).sum(axis=0)


def legs_from_order(order, cnt, N, shape):
    n, T = shape
    valid = cnt >= 2 * N

    inlo = np.zeros((n, T), dtype=bool)
    inhi = np.zeros((n, T), dtype=bool)
    cols = np.flatnonzero(valid)
    if cols.size:
        lo_rows = order[:N, cols]
        # the last N FINITE entries of each column, which is not the last N rows
        hi_idx = cnt[cols][None, :] - np.arange(N, 0, -1)[:, None]
        hi_rows = np.take_along_axis(order[:, cols], hi_idx, axis=0)
        bc = np.broadcast_to(cols, lo_rows.shape)
        inlo[lo_rows, bc] = True
        inhi[hi_rows, bc] = True

    ev_lo, ev_hi = inlo.copy(), inhi.copy()
    ev_lo[:, 1:] &= ~inlo[:, :-1]
    ev_hi[:, 1:] &= ~inhi[:, :-1]
    return ev_lo, ev_hi, inlo


def legs_loop(score, base, N):
    """The obvious per-bar implementation. KEPT, and used only by the self-test.

    `legs` is a vectorised rewrite of this, and a rewrite that is merely
    plausible is how D286 shipped a move 10x too small. This is the thing it has
    to equal.
    """
    s = C.lag1(score)
    n, T = base.shape
    inlo = np.zeros((n, T), dtype=bool)
    inhi = np.zeros((n, T), dtype=bool)
    for t in range(T):
        q = np.flatnonzero(base[:, t])
        if q.size == 0:
            continue
        v = s[q, t]
        fin = np.isfinite(v)
        q, v = q[fin], v[fin]
        if q.size < 2 * N:
            continue
        o = np.argsort(v, kind="stable")
        inlo[q[o[:N]], t] = True
        inhi[q[o[-N:]], t] = True
    ev_lo, ev_hi = inlo.copy(), inhi.copy()
    ev_lo[:, 1:] &= ~inlo[:, :-1]
    ev_hi[:, 1:] &= ~inhi[:, :-1]
    return ev_lo, ev_hi, inlo


def bar_sums(f, rows, cols, T):
    """Per-bar sum and count of `f` over the given event cells.

    SPARSE ON PURPOSE. Events are at most N per bar, so this touches ~105k cells
    where a masked full-array sum touches 6.6M. Gate A recomputes this statistic
    a few thousand times under rotation, and the dense version made that a
    multi-hour run rather than a several-minute one.

    Gate A imports THIS function rather than reimplementing it, so the floor and
    the observed value are the same arithmetic in the same order -- a floor
    computed by slightly different code is not a floor for that number.
    """
    v = f[rows, cols]
    fin = np.isfinite(v)
    c, vv = cols[fin], v[fin].astype(np.float64)
    return (np.bincount(c, weights=vv, minlength=T),
            np.bincount(c, minlength=T))


def screen(name, score, base, fwd):
    """One candidate, all N, all horizons. Pure and read-only -- runs on a thread."""
    res = {}
    T = base.shape[1]
    order, cnt = rank_columns(score, base)          # once, not once per N
    for N in N_LEVELS:
        ev_lo, ev_hi, inlo = legs_from_order(order, cnt, N, base.shape)
        lr, lc = np.nonzero(ev_lo)
        hr, hc = np.nonzero(ev_hi)
        rows = {}
        for k in HORIZONS:
            f = fwd[k]
            slo, clo = bar_sums(f, lr, lc, T)
            shi, chi = bar_sums(f, hr, hc, T)
            m = (clo > 0) & (chi > 0)
            if int(m.sum()) < MIN_BARS:
                continue
            lo = slo[m] / clo[m]
            hi = shi[m] / chi[m]
            d = lo - hi
            tt = float(d.mean() / (d.std(ddof=1) / np.sqrt(d.size)))
            rows[k] = {"long_bp": float(lo.mean() * 1e4),
                       "short_bp": float(hi.mean() * 1e4),
                       "spread_bp": float(d.mean() * 1e4),
                       "spread_bp_per_bar": float(d.mean() * 1e4 / k),
                       "t": tt, "bars": int(d.size)}
        best = max(rows, key=lambda k: rows[k]["spread_bp"]) if rows else None
        res[N] = {"horizons": rows, "peak_horizon": best,
                  "n_long_events": int(ev_lo.sum()),
                  "n_short_events": int(ev_hi.sum()),
                  "ranking_bars": int(inlo.any(axis=0).sum())}
    return res


# --------------------------------------------------------------------------
# the three runner assertions CLAUDE.md requires, plus coverage
# --------------------------------------------------------------------------
def assertions(scores, base, fwd, panel, live):
    print("\n  RUNNER ASSERTIONS", flush=True)

    # 1. LAG AUDIT, IN A SECOND IMPLEMENTATION. `legs` must rank bar t on the
    #    score at t-1. Rebuilt here by hand from the UNLAGGED array, so a bug in
    #    `C.lag1` cannot hide behind itself.
    s = scores["hist_L"]

    # 0. THE VECTORISED RANKING MUST EQUAL THE LOOP IT REPLACED, exactly, on
    #    every cell -- not approximately and not on a sample. `legs` sorts whole
    #    columns in one C call for speed; `legs_loop` is the obvious version.
    #    Checked on the score with the most TIED values, not on `hist_L`:
    #    `on_persist` takes multiples of 1/21, so tie-breaking decides much of
    #    its book, and a rewrite that disagreed about ties would pass on a
    #    continuous score and fail here.
    for probe in ("hist_L", "on_persist"):
        for N in (10, 50):
            a = legs(scores[probe], base, N)
            b = legs_loop(scores[probe], base, N)
            for x, y, w in zip(a, b, ("ev_lo", "ev_hi", "inlo")):
                assert np.array_equal(x, y), (
                    f"legs != legs_loop on {probe} N={N} ({w}): "
                    f"{int((x ^ y).sum()):,} cells differ")
    print(f"    [0] vectorised ranking == the per-bar loop, on hist_L and "
          f"on_persist at N=10 and 50")

    ev_lo, _, inlo = legs(s, base, 25)
    checked = 0
    for t in range(200, live.shape[1], 401):
        q = np.flatnonzero(base[:, t])
        v = s[q, t - 1]                       # BY HAND: bar t ranks on t-1
        fin = np.isfinite(v)
        q, v = q[fin], v[fin]
        if q.size < 50:
            continue
        want = set(q[np.argsort(v, kind="stable")[:25]].tolist())
        got = set(np.flatnonzero(inlo[:, t]).tolist())
        assert want == got, f"LAG AUDIT FAILED at t={t}: {len(want ^ got)} names differ"
        checked += 1
    assert checked >= 5, f"lag audit only covered {checked} bars"
    print(f"    [1] lag audit: bottom-25 rebuilt from the unlagged score on "
          f"{checked} bars, identical")

    # 1b. and it must FAIL on an unlagged book, or it is not testing anything.
    raised = False
    try:
        bad = np.roll(s, -1, axis=1)          # shifted the wrong way: peeks ahead
        _, _, ibad = legs(bad, base, 25)
        for t in range(200, live.shape[1], 401):
            q = np.flatnonzero(base[:, t])
            v = s[q, t - 1]
            fin = np.isfinite(v)
            q, v = q[fin], v[fin]
            if q.size < 50:
                continue
            want = set(q[np.argsort(v, kind="stable")[:25]].tolist())
            assert want == set(np.flatnonzero(ibad[:, t]).tolist())
    except AssertionError:
        raised = True
    assert raised, "the lag audit PASSED a look-ahead book -- it proves nothing"
    print(f"    [1b] and it raises on a deliberately forward-shifted score")

    # 2. SIGN AUDIT, IN MONEY. The long leg must hold the LOW score and the short
    #    leg the HIGH one. D280 shipped a sign inversion through five parts on
    #    reasoning alone; this settles it on the arrays that earn the return.
    lag = C.lag1(s)
    _, ev_hi, _ = legs(s, base, 25)
    lo_v = lag[ev_lo]
    hi_v = ev_hi & np.isfinite(lag)
    lo_m, hi_m = np.nanmean(lo_v), np.nanmean(lag[hi_v])
    assert lo_m < hi_m, f"SIGN INVERTED: long leg mean {lo_m} >= short leg {hi_m}"
    print(f"    [2] sign audit in money: long-leg mean score {lo_m:+.5f} < "
          f"short-leg {hi_m:+.5f}")

    # 3. RIGHT QUANTITY. fwd[1] is the one-bar simple return and nothing else.
    r1 = np.expm1(panel.total_log_returns)
    m = np.isfinite(fwd[1]) & live
    d = np.abs(fwd[1][m].astype(np.float64) - r1[m])
    assert d.max() < 1e-6, f"fwd[1] is not the one-bar return: max |delta| {d.max():.3e}"
    print(f"    [3] right quantity: fwd[1] == expm1(log return) on "
          f"{int(m.sum()):,} cells, max |delta| {d.max():.2e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true",
                    help="assertions and coverage only; no screen")
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    print(f"loaded {live.shape[0]} names x {live.shape[1]} bars "
          f"in {time.time() - t0:.0f}s", flush=True)

    scores, warm, extra = build_scores(panel, cleaned, g, live)
    # SCORES BUILT AND NOT SCREENED ARE DISCLOSED. The families produce a few
    # terms D288 did not pre-register (`rsi`, `impulse_nodz`, and the profile
    # census keys). They are NOT screened and NOT in the ledger -- naming them
    # here is what stops a later "we also looked at" from being invisible.
    if extra:
        print(f"  built but NOT screened, by pre-registration: {sorted(extra)}")
    # ONE SHARED BASE FOR ALL 31. A candidate with narrower coverage would
    # otherwise be scored on an easier subset of the panel, and the comparison
    # between candidates is the whole study.
    base = warm & live
    fwd = forward_returns(panel, live)
    print(f"built {len(scores)} candidates + {len(fwd)} horizons "
          f"in {time.time() - t0:.0f}s", flush=True)

    # WARM CELLS, NOT FINITE CELLS. `impulse_nodz` needs 992 own bars and 34.7%
    # of its finite values on this panel are seed transient; two candidates
    # compared on finite cells are compared on different samples.
    print(f"\n  COVERAGE (shared base: {int(base.sum()):,} warm live cells)")
    cover = {}
    for c in CANDIDATES:
        fin = int((np.isfinite(scores[c]) & base).sum())
        cover[c] = fin
        print(f"    {AXIS_OF[c]}  {c:16s} {fin:>10,}  "
              f"{fin / base.sum():6.1%} of base", flush=True)
    lo = min(cover, key=cover.get)
    print(f"    thinnest: {lo} at {cover[lo] / base.sum():.1%} -- reported because "
          f"a candidate\n    ranked on fewer bars is not the same test as one ranked "
          f"on all of them")

    assertions(scores, base, fwd, panel, live)
    if a.selftest:
        print(f"\nOK  assertions pass, {len(CANDIDATES)} candidates built  "
              f"({time.time() - t0:.0f}s)")
        return 0

    print(f"\n  SCREENING {len(CANDIDATES)} candidates x {len(N_LEVELS)} N "
          f"x {len(HORIZONS)} horizons", flush=True)
    res = FN.parallel_map(lambda c, sc: screen(c, sc, base, fwd),
                          [(c, scores[c]) for c in CANDIDATES],
                          workers=a.workers, progress=True)

    print(f"\n  {'axis':>4s} {'candidate':16s} {'N':>3s} {'k*':>3s} "
          f"{'long bp':>9s} {'short bp':>9s} {'spread bp':>10s} {'t':>7s}")
    for c in CANDIDATES:
        for N in N_LEVELS:
            r = res[c][N]
            k = r["peak_horizon"]
            if k is None:
                print(f"  {AXIS_OF[c]:>4s} {c:16s} {N:3d}   --   (no horizon "
                      f"reached {MIN_BARS} bars)")
                continue
            h = r["horizons"][k]
            print(f"  {AXIS_OF[c]:>4s} {c:16s} {N:3d} {k:3d} "
                  f"{h['long_bp']:+9.1f} {h['short_bp']:+9.1f} "
                  f"{h['spread_bp']:+10.1f} {h['t']:+7.2f}", flush=True)

    json.dump({"purpose": ("D288 phase 2: the two-leg event response of 31 "
                           "pre-registered candidates. NO GATE IS APPLIED HERE -- "
                           "the best-of-31 floor and the mechanism re-derivation "
                           "read this file."),
               "pre_registration": "docs/decisions/D288-the-mine-with-a-mechanism-gate.md",
               "n_candidates": len(CANDIDATES), "axes": AXIS_OF,
               "n_levels": list(N_LEVELS), "horizons": list(HORIZONS),
               "base_cells": int(base.sum()), "coverage": cover,
               "results": {c: {str(N): res[c][N] for N in N_LEVELS} for c in CANDIDATES},
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    print(f"  NOTHING IS PROMOTED BY THIS FILE. Gate 0 (independence), gate A "
          f"(best-of-31\n  floor) and gate B (the re-derivation) run next, in that "
          f"order.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
