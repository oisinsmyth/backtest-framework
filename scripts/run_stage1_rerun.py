"""D290 -- the stage-1 re-run. 51 candidates, three constructions, three nulls.

    uv run python scripts/run_stage1_rerun.py --selftest
    uv run python scripts/run_stage1_rerun.py [--draws 100] [--splits 10] [--workers 6]

PRE-REGISTERED AT `e21526f`, AMENDED AT `fb6719b`, both committed before this
file existed (R8). This runner may not add a candidate or change a statistic.

STAGE 1 CONSUMES NOTHING SCARCE, so this file GATES NOTHING and CLOSES NOTHING.
It produces a ranking. The holdout is not read and no primitive here has ever
touched it.

CONFLUENCE IS OUT OF SCOPE by the principal's instruction. The 51 are scored
individually and no combination is attempted.

THREE CONSTRUCTIONS, SCORED AS STRATEGIES RATHER THAN AS LEGS OF ONE. D288
reported both legs only descriptively: `hist_L` at N=25 k=25 was long +205.4,
short +149.1, so the SHORT BOOK LOSES 149 bp and the +56.3 spread hides it. Here

    long   P&L = +mean(forward return of the N lowest)
    short  P&L = -mean(forward return of the N highest)      <- NEGATED
    spread P&L = long + short

so a positive number always means the construction MADE money. The short leg's
sign is the one D280 got wrong for five parts, so it is asserted in money below
rather than argued in prose.

THREADS, NOT PROCESSES, AND THAT IS THE RIGHT CALL HERE. The build was
GIL-bound pure Python and went to 8 processes; this runner is `argsort` and
`bincount`, which release the GIL, and six threads share ONE 2.69 GB cache
instead of copying it six times.
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


M = _load("run_mine_neutral", "run_mine_neutral.py")      # rank/legs/bar_sums
BC = _load("d290_build_cache", "d290_build_cache.py")     # the 51 and their axes
SP = _load("d285sp", "d285_spread_estimate.py")
FN = M.FN

OUT = REPO / "data" / "d290_stage1.json"
N_LEVELS = (3, 5, 10, 25, 50)
HORIZONS = M.HORIZONS
MIN_BARS = M.MIN_BARS
CONSTRUCTIONS = ("long", "short", "spread")
SEED = 20260902
CANDIDATES, AXIS_OF = BC.CANDIDATES, BC.AXIS_OF


# --------------------------------------------------------------------------
def leg_means(f, ev, T):
    rows, cols = np.nonzero(ev)
    s, c = M.bar_sums(f, rows, cols, T)
    return s, c


def cell_stats(fwd, ev_lo, ev_hi, T):
    """Per-horizon (effect_bp, t, bars) for all three constructions, one pass."""
    lr, lc = np.nonzero(ev_lo)
    hr, hc = np.nonzero(ev_hi)
    out = {}
    for k in HORIZONS:
        f = fwd[k]
        slo, clo = M.bar_sums(f, lr, lc, T)
        shi, chi = M.bar_sums(f, hr, hc, T)
        m = (clo > 0) & (chi > 0)
        if int(m.sum()) < MIN_BARS:
            continue
        lo = slo[m] / clo[m]
        hi = shi[m] / chi[m]
        series = {"long": lo, "short": -hi, "spread": lo - hi}
        row = {}
        for name, d in series.items():
            sd = d.std(ddof=1)
            row[name] = (float(d.mean() * 1e4),
                         float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else 0.0,
                         int(d.size))
        out[k] = row
    return out


def grid(score, base, fwd, T, ns=N_LEVELS):
    """The full (N, horizon) grid of stats for one score."""
    order, cnt = M.rank_columns(score, base)
    g = {}
    for N in ns:
        ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base.shape)
        g[N] = cell_stats(fwd, ev_lo, ev_hi, T)
    return g


def peak(g, con):
    """The (N, k) cell maximising t for one construction."""
    best = None
    for N, rows in g.items():
        for k, row in rows.items():
            if con not in row:
                continue
            if best is None or row[con][1] > best[2][1]:
                best = (N, k, row[con])
    return best


def grid_max_t(g, con):
    b = peak(g, con)
    return -9e9 if b is None else b[2][1]


# --------------------------------------------------------------------------
# nulls
# --------------------------------------------------------------------------
def rotate(score, ats, off):
    """Roll each symbol's values WITHIN its own live bars. Coverage unchanged,
    autocorrelation unchanged, so TURNOVER is matched -- the nuisance that made
    D279's matched-count control meaningless (it churned 5.6x harder)."""
    out = np.full(score.shape, np.nan)
    for i, at in enumerate(ats):
        if at.size:
            out[i, at] = np.roll(score[i, at], int(off[i]))
    return out


def permute_bars(score, base, rng):
    """Shuffle the score ACROSS NAMES inside each bar.

    Preserves each bar's cross-sectional distribution exactly, so the market
    REGIME survives -- every name's vol spiked in March 2020 and a per-symbol
    rotation destroys that. Destroys only which name holds which score, which is
    the whole claim of a cross-sectional book. Its mirror weakness is that it
    breaks autocorrelation, hence turnover; that is why it is reported BESIDE
    rotation and not instead of it.
    """
    out = np.full(score.shape, np.nan)
    for t in range(score.shape[1]):
        idx = np.flatnonzero(base[:, t] & np.isfinite(score[:, t]))
        if idx.size > 1:
            out[idx, t] = score[rng.permutation(idx), t]
    return out


def tail_null_grid(score, base, fwd, T, rng, ns=N_LEVELS):
    """D283's control: pool the 2N most extreme by the candidate's OWN score and
    assign the sides AT RANDOM.

    Matched-count is not matched-nuisance. This pool carries the same volatility,
    the same liquidity and the same everything-else the score selects on, because
    it IS the score's own extremes -- so what it removes is only the directional
    claim. D283 measured the tail tax at -14.68/-9.80/-6.58 bp against a
    directional +4.75/+4.66/+3.60, i.e. a whole-universe control is beaten by the
    tax alone. Cheap, too: it reuses the observed ordering and never re-sorts.
    """
    order, cnt = M.rank_columns(score, base)
    n, T_ = base.shape
    g = {}
    for N in ns:
        valid = cnt >= 2 * N
        cols = np.flatnonzero(valid)
        ev_lo = np.zeros((n, T_), dtype=bool)
        ev_hi = np.zeros((n, T_), dtype=bool)
        if cols.size:
            lo_rows = order[:N, cols]
            hi_idx = cnt[cols][None, :] - np.arange(N, 0, -1)[:, None]
            hi_rows = np.take_along_axis(order[:, cols], hi_idx, axis=0)
            pool = np.concatenate([lo_rows, hi_rows], axis=0)      # (2N, ncols)
            for j in range(pool.shape[1]):
                p = rng.permutation(pool[:, j])
                ev_lo[p[:N], cols[j]] = True
                ev_hi[p[N:], cols[j]] = True
        # fresh entries, matching the observed construction
        a, b = ev_lo.copy(), ev_hi.copy()
        a[:, 1:] &= ~ev_lo[:, :-1]
        b[:, 1:] &= ~ev_hi[:, :-1]
        g[N] = cell_stats(fwd, a, b, T)
    return g


# --------------------------------------------------------------------------
def name_split_cv(score, base, fwd, T, splits, rng):
    """Pick the peak cell on half A, SCORE THAT CELL ON HALF B.

    The holdout is a DISJOINT NAME SET over the same period, so this is the
    holdout's own structure at zero cost. Pooled in-sample t is a max-order
    statistic over an unbounded search and is meaningless as a level; this is
    the statistic that is not.
    """
    n = base.shape[0]
    got = {c: [] for c in CONSTRUCTIONS}
    for _ in range(splits):
        perm = rng.permutation(n)
        a, b = perm[: n // 2], perm[n // 2:]
        ba = np.zeros_like(base)
        ba[a] = base[a]
        bb = np.zeros_like(base)
        bb[b] = base[b]
        ga = grid(score, ba, fwd, T)
        gb = grid(score, bb, fwd, T)
        for con in CONSTRUCTIONS:
            pa = peak(ga, con)
            if pa is None:
                continue
            N, k, _ = pa
            row = gb.get(N, {}).get(k)
            if row and con in row:
                got[con].append(row[con][1])          # half-B t at half-A's cell
    return {c: (float(np.mean(v)) if v else None,
                float(np.std(v)) if len(v) > 1 else None, len(v))
            for c, v in got.items()}


def held_spread_bp(score, base, N, half):
    """Corwin-Schultz on the names ACTUALLY HELD, not a fee assumption.

    D285 guessed 15 bp/side and the held names measured 33.81. `half` is the
    per-bar half-spread grid in bp per side.
    """
    order, cnt = M.rank_columns(score, base)
    ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base.shape)
    out = {}
    for name, ev in (("long", ev_lo), ("short", ev_hi)):
        v = half[ev & np.isfinite(half)]
        out[name] = float(np.mean(v)) if v.size else None
    return out


# --------------------------------------------------------------------------
# the three runner assertions CLAUDE.md requires
# --------------------------------------------------------------------------
def assertions(scores, base, fwd, panel, live):
    print("\n  RUNNER ASSERTIONS", flush=True)
    T = base.shape[1]

    # 1. LAG AUDIT, SECOND IMPLEMENTATION. The book must rank bar t on the score
    #    at t-1. Rebuilt by hand from the UNLAGGED array so a bug in `lag1`
    #    cannot hide behind itself. D279's first `top_n` ranked on bar t's own
    #    score and 93% of that study's edge was the bug.
    s = scores["hist_L"]
    order, cnt = M.rank_columns(s, base)
    _, _, inlo = M.legs_from_order(order, cnt, 25, base.shape)
    checked = 0
    for t in range(200, T, 401):
        q = np.flatnonzero(base[:, t])
        v = s[q, t - 1]
        fin = np.isfinite(v)
        q, v = q[fin], v[fin]
        if q.size < 60:
            continue
        want = set(q[np.argsort(v, kind="stable")[:25]].tolist())
        assert want == set(np.flatnonzero(inlo[:, t]).tolist()), \
            f"LAG AUDIT FAILED at t={t}"
        checked += 1
    assert checked >= 5, f"lag audit covered only {checked} bars"
    print(f"    [1] lag audit: bottom-25 rebuilt from the unlagged score on "
          f"{checked} bars, identical")

    # 1b. and it must FAIL on a forward-shifted score, or it proves nothing.
    raised = False
    try:
        bad = np.roll(s, -1, axis=1)
        o2, c2 = M.rank_columns(bad, base)
        _, _, ibad = M.legs_from_order(o2, c2, 25, base.shape)
        for t in range(200, T, 401):
            q = np.flatnonzero(base[:, t])
            v = s[q, t - 1]
            fin = np.isfinite(v)
            q, v = q[fin], v[fin]
            if q.size < 60:
                continue
            assert set(q[np.argsort(v, kind="stable")[:25]].tolist()) == \
                set(np.flatnonzero(ibad[:, t]).tolist())
    except AssertionError:
        raised = True
    assert raised, "the lag audit PASSED a look-ahead book -- it proves nothing"
    print(f"    [1b] and it raises on a deliberately forward-shifted score")

    # 2. SIGN AUDIT, IN MONEY, ON ALL THREE CONSTRUCTIONS. An ORACLE score is
    #    built so that after the book's own lag it ranks on MINUS the return the
    #    position is about to earn. Every construction must then be strongly
    #    POSITIVE -- including SHORT, which is the sign D280 got wrong through
    #    five parts on reasoning alone.
    f1 = fwd[1].astype(np.float64)
    oracle = np.full(f1.shape, np.nan)
    oracle[:, :-1] = -f1[:, 1:]
    g = grid(oracle, base, fwd, T, ns=(25,))
    row = g[25][1]
    for con in CONSTRUCTIONS:
        bp, t_, _ = row[con]
        assert bp > 100.0, (
            f"SIGN AUDIT FAILED: oracle {con} earns {bp:+.1f} bp at k=1; a "
            f"perfect-foresight book must be strongly positive on every "
            f"construction, and SHORT is the one that inverts silently")
    print(f"    [2] sign audit in money: oracle earns "
          + ", ".join(f"{c} {row[c][0]:+,.0f} bp" for c in CONSTRUCTIONS))

    # 3. RIGHT QUANTITY. fwd[1] is the one-bar simple return and nothing else.
    r1 = np.expm1(panel.total_log_returns)
    m = np.isfinite(fwd[1]) & live
    d = np.abs(fwd[1][m].astype(np.float64) - r1[m])
    assert d.max() < 1e-6, f"fwd[1] is not the one-bar return: {d.max():.3e}"
    print(f"    [3] right quantity: fwd[1] == expm1(log return) on "
          f"{int(m.sum()):,} cells, max |delta| {d.max():.2e}")


# --------------------------------------------------------------------------
def era_masks(dates, base):
    """FINDINGS section 6 records three sign inversions in a single day and calls
    era-splitting reflexive. D288 never did it. Reported, never gates."""
    yrs = np.array([int(str(d)[:4]) for d in dates])
    return {"pre2020": yrs < 2020, "2020": yrs == 2020, "post2020": yrs > 2020}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--splits", type=int, default=10)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    t0 = time.time()
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    if not BC.CACHE.exists():
        raise SystemExit(f"no cache at {BC.CACHE}; run d290_build_cache.py first")
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(M.B.FIXTURE), (
        "CACHE IS STALE -- the fixture or an estimator module changed since it "
        "was built. Rebuild rather than scoring numbers that belong to code "
        "that no longer exists.")
    scores = {c: z[c] for c in CANDIDATES}
    base = z["warm"] & live
    fwd = M.forward_returns(panel, live)
    print(f"loaded {len(CANDIDATES)} candidates + {len(fwd)} horizons in "
          f"{time.time() - t0:.0f}s | base {int(base.sum()):,} warm live cells",
          flush=True)

    assertions(scores, base, fwd, panel, live)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    ats = [np.flatnonzero(live[i]) for i in range(live.shape[0])]
    eras = era_masks(panel.dates, base)
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4   # bp per side

    # ---- observed grid, CV, nulls -- one thread per candidate ----
    def work(c, score):
        rng = np.random.default_rng(SEED + hash(c) % 100000)
        gobs = grid(score, base, fwd, T)
        obs = {con: peak(gobs, con) for con in CONSTRUCTIONS}
        cv = name_split_cv(score, base, fwd, T, a.splits,
                           np.random.default_rng(SEED + 7))
        nulls = {n: {con: [] for con in CONSTRUCTIONS}
                 for n in ("rotation", "permutation", "tail")}
        for _ in range(a.draws):
            off = rng.integers(1, T, size=live.shape[0])
            for nm, gg in (("rotation", grid(rotate(score, ats, off), base, fwd, T)),
                           ("permutation",
                            grid(permute_bars(score, base, rng), base, fwd, T)),
                           ("tail", tail_null_grid(score, base, fwd, T, rng))):
                for con in CONSTRUCTIONS:
                    nulls[nm][con].append(grid_max_t(gg, con))
        zs = {}
        for nm in nulls:
            zs[nm] = {}
            for con in CONSTRUCTIONS:
                arr = np.array([v for v in nulls[nm][con] if v > -8e9])
                o = obs[con][2][1] if obs[con] else None
                if o is None or arr.size < 5 or arr.std(ddof=1) == 0:
                    zs[nm][con] = None
                else:
                    zs[nm][con] = float((o - arr.mean()) / arr.std(ddof=1))
        # era split at each construction's own peak cell
        era = {}
        for con in CONSTRUCTIONS:
            if not obs[con]:
                continue
            N, k, _ = obs[con]
            era[con] = {}
            for en, m in eras.items():
                bb = base & m[None, :]
                gg = grid(score, bb, fwd, T, ns=(N,))
                row = gg.get(N, {}).get(k)
                era[con][en] = None if not row else row[con][:2]
        cost = held_spread_bp(score, base, obs["spread"][0], half) \
            if obs["spread"] else {}
        return {"observed": {c2: (obs[c2][0], obs[c2][1], obs[c2][2])
                             if obs[c2] else None for c2 in CONSTRUCTIONS},
                "cv": cv, "z": zs, "era": era, "cost_bp_per_side": cost,
                "coverage": int((np.isfinite(score) & base).sum())}

    print(f"\n  SCREENING {len(CANDIDATES)} candidates x {len(CONSTRUCTIONS)} "
          f"constructions x {len(N_LEVELS)} N x {len(HORIZONS)} horizons",
          flush=True)
    print(f"  nulls: {a.draws} draws x 3 | CV: {a.splits} name splits | "
          f"{a.workers} threads", flush=True)
    res = FN.parallel_map(lambda c, s: work(c, s),
                          [(c, scores[c]) for c in CANDIDATES],
                          workers=a.workers, progress=True)

    json.dump({"purpose": "D290 stage-1 re-run. A RANKING, not a gate. Nothing "
                          "is closed and the holdout is not read.",
               "pre_registration": "docs/decisions/D290-the-stage-one-rerun.md",
               "n_candidates": len(CANDIDATES), "axes": AXIS_OF,
               "constructions": list(CONSTRUCTIONS), "n_levels": list(N_LEVELS),
               "horizons": list(HORIZONS), "draws": a.draws, "splits": a.splits,
               "base_cells": int(base.sum()), "results": res,
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1, default=float)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    print(f"  NOTHING IS CLOSED OR PROMOTED BY THIS FILE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
