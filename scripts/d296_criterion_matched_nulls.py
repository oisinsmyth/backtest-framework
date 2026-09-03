"""D296 -- pricing the OTHER two searches over D293's horizon grid.

    uv run python scripts/d296_criterion_matched_nulls.py --selftest
    uv run python scripts/d296_criterion_matched_nulls.py [--draws 200]

WHY THIS FILE EXISTS. R14's fourth amendment of 2026-09-03 closes with:

    "the multiplicity a grid-max null prices is the search for max `t`;
     selecting k on any other criterion is a different search over the same
     grid and needs its own null."

D290 and D293 ran grid-max nulls on `t`. D294 then re-read the SAME grid on two
other criteria -- gross bp, and cost coverage `gross / round trip` -- and found
the peak somewhere else (k=13-16 rather than k=5). Those peaks are unpriced.
This file prices them, against nulls whose grid maximum is taken ON THE SAME
CRITERION as the observed peak it is matched to.

NOT A NEW SEARCH OVER PARAMETERS. The candidate is FIXED at D293's:

    hist_L x mean-rank(macd_hist, rsi) @ f=0.75, N=25, spread construction

f, N, the pair, the primary and the operator are all inherited and none is
touched. The ONE thing that changes is the horizon grid, which is REFINED --
every integer k in [11, 26] is added to D290's twelve so the gross peak can be
located rather than bracketed. A finer grid is MORE looks, not fewer, and the
null sees exactly the same refined grid, so the refinement pays for itself.

THE SEARCH SPACE BEING PRICED, stated once and used identically four times:

    max over k in HORIZONS_FINE, at N=25, spread    (24 cells)

This is NARROWER than D293's grid-max, which also ranged over five N and three
constructions. A z from this file is therefore NOT comparable to D293's z; it is
comparable only across the four criteria here, which is the whole question. The
D293 full-grid t-null is reported alongside for that reason and no other.

THE FOUR CRITERIA:

    t          the statistic D290/D293 ranked on
    gross bp   total return per entry, which is what dedicated capital wants
    x mean     gross / round trip, Corwin-Schultz aggregated by MEAN
    x robust   gross / round trip, Corwin-Schultz aggregated by MEDIAN

Both aggregations, because D293's cost breakdown showed the mean and the median
half-spread straddle the line: a mean of 65 bp built from a median of 26 is a
universe problem and a mean built from a median of 60 is a strategy problem.

THE ROUND TRIP IS RECOMPUTED ON EVERY NULL BOOK, and that is the only thing that
makes the cost-coverage null different from the gross null. If the null's round
trip were held at the OBSERVED value, `x = gross / rt_obs` would be a constant
multiple of gross, and z is invariant to a common positive scale -- the two
nulls would be the same null wearing two names. Assertion [8] checks exactly
that, so the distinction is verified rather than asserted.

AND THE CROSS-CRITERION TABLE, which is what the amendment is really asking.
"Gross at the k that maximises t" is the number D290's pipeline would have
reported, and it is a statistic OF A SELECTION PROCEDURE, not of a fixed cell.
So its null runs the same procedure: find that DRAW's own t-peak, read gross
there. The diagonal of that table is the criterion-matched null above; the
off-diagonal says whether a t-matched pricing licenses a gross claim.

CAVEAT, STATED NOT HIDDEN. The round trip of the observed book and of the
rotation and permutation nulls is measured over MEMBERSHIP cells (every bar a
name is in the book), which is D294's definition. The tail null re-deals sides
among pooled FRESH ENTRIES and has no membership, so its round trip is measured
over those entry cells. The observed round trip is reported under both cell
definitions so the size of that inconsistency is visible.
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


C = _load("d293", "run_d293_candidate.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M, D, ET, FN = C.R, C.M, C.D, C.ET, C.FN

OUT = REPO / "data" / "d296_criterion_matched_nulls.json"
N_FIXED = 25
CON = "spread"
COMPOSITE = True
SEED = 20260904
CRITERIA = ("t", "bp", "x_mean", "x_robust")

# D290's twelve, plus every integer in [11, 26]. Superset by construction, so
# assertion [5] can hold the shared cells bit-identical to D294's.
HORIZONS_D290 = tuple(M.HORIZONS)
HORIZONS_FINE = tuple(sorted(set(HORIZONS_D290) | set(range(11, 27))))
assert set(HORIZONS_D290) <= set(HORIZONS_FINE)
assert max(HORIZONS_FINE) <= M.MAX_H, "forward_returns only accumulates to MAX_H"


# --------------------------------------------------------------------------
# the round trip, both cell definitions
# --------------------------------------------------------------------------
def rt_membership(b, half):
    """D294's round trip, EXACTLY: 2 x mean half-spread on each leg's held cells."""
    plan, klo, khi = b[2], b[3], b[4]
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    cost = {}
    for side, rows, mask in (("long", plan.lo, klo), ("short", plan.hi, khi)):
        v = half[rows[mask], bc[mask]]
        v = v[np.isfinite(v)]
        if v.size == 0:
            return None, None
        cost[side] = (float(v.mean()), float(np.median(v)))
    return (2 * cost["long"][0] + 2 * cost["short"][0],
            2 * cost["long"][1] + 2 * cost["short"][1])


def rt_events(lo_idx, hi_idx, half):
    """The same arithmetic over FRESH-ENTRY cells. The tail null has no
    membership -- it re-deals sides among pooled entries -- so this is the only
    definition available there."""
    cost = {}
    for side, (rows, cols) in (("long", lo_idx), ("short", hi_idx)):
        v = half[rows, cols]
        v = v[np.isfinite(v)]
        if v.size == 0:
            return None, None
        cost[side] = (float(v.mean()), float(np.median(v)))
    return (2 * cost["long"][0] + 2 * cost["short"][0],
            2 * cost["long"][1] + 2 * cost["short"][1])


# --------------------------------------------------------------------------
# one book -> the four criteria, and their grid maxima
# --------------------------------------------------------------------------
def profile(cs, rt_mean, rt_rob):
    """Per-horizon values of all four criteria, at N=25 on the spread."""
    rows = {}
    for k in HORIZONS_FINE:
        row = cs.get(k)
        if not row or CON not in row:
            continue
        bp, t_, nbar = row[CON]
        rows[k] = dict(bp=bp, t=t_, bars=nbar, bp_per_bar=bp / k,
                       x_mean=bp / rt_mean if rt_mean else None,
                       x_robust=bp / rt_rob if rt_rob else None)
    return rows


def grid_max(rows, crit):
    """The grid maximum ON ONE CRITERION, and where it sits."""
    best = None
    for k, r in rows.items():
        v = r.get(crit)
        if v is None:
            continue
        if best is None or v > best[1]:
            best = (k, v)
    return best


def at_max(rows, maxima):
    """The WHOLE row at each criterion's argmax.

    This is what makes the cross-criterion table properly matched. "Gross at the
    k that maximises t" is a statistic of a SELECTION PROCEDURE, not of a fixed
    cell, so its null must run the same procedure on the null grid: find that
    draw's own t-peak, and read gross there. Comparing a fixed k=5 to a
    grid-max-gross null instead would price a search nobody ran.
    """
    return {s: (None if maxima[s] is None else dict(rows[maxima[s][0]]))
            for s in CRITERIA}


def score_book(sa_, s1_, s2_, base, fwd, T, half):
    """One (possibly nulled) triple of scores -> grid maxima on all four criteria."""
    ranks = C.rank_all(sa_, s1_, s2_, base, COMPOSITE)
    b = C.book(ranks, N_FIXED, T, COMPOSITE)
    if b is None:
        return None
    rtm, rtr = rt_membership(b, half)
    if rtm is None:
        return None
    cs = C.cell_stats(fwd, b[0], b[1], T)
    rows = profile(cs, rtm, rtr)
    mx = {c: grid_max(rows, c) for c in CRITERIA}
    return dict(rows=rows, rt_mean=rtm, rt_robust=rtr, maxima=mx,
                at_max=at_max(rows, mx))


def tail_events(sa_, s1_, s2_, base, T, rng):
    """D293's `tail_grid` body, stopped one step early so the EVENTS are
    returned and the round trip can be measured on them.

    A REWRITE, so assertion [6] holds it bit-identical to `C.tail_grid` on the
    same RNG stream -- the rng is consumed in the same order, one permutation
    per bar with at least two pooled entries, at N=25 only.
    """
    n, T_ = base.shape
    assert T_ == T
    ranks = C.rank_all(sa_, s1_, s2_, base, COMPOSITE)
    b = C.book(ranks, N_FIXED, T, COMPOSITE)
    if b is None:
        return None
    (lr, lc), (hr, hc) = b[0], b[1]
    ev_lo = np.zeros((n, T), dtype=bool)
    ev_hi = np.zeros((n, T), dtype=bool)
    allr = np.concatenate([lr, hr])
    allc = np.concatenate([lc, hc])
    ordc = np.argsort(allc, kind="stable")
    allr, allc = allr[ordc], allc[ordc]
    bounds = np.flatnonzero(np.diff(allc)) + 1
    for a_, b_ in zip(np.r_[0, bounds], np.r_[bounds, allc.size]):
        rows = allr[a_:b_]
        if rows.size < 2:
            continue
        p = rng.permutation(rows)
        half_ = rows.size // 2
        ev_lo[p[:half_], allc[a_]] = True
        ev_hi[p[half_:2 * half_], allc[a_]] = True
    return np.nonzero(ev_lo), np.nonzero(ev_hi)


def score_tail(sa_, s1_, s2_, base, fwd, T, half, rng):
    ev = tail_events(sa_, s1_, s2_, base, T, rng)
    if ev is None:
        return None
    lo_idx, hi_idx = ev
    rtm, rtr = rt_events(lo_idx, hi_idx, half)
    if rtm is None:
        return None
    cs = C.cell_stats(fwd, lo_idx, hi_idx, T)
    rows = profile(cs, rtm, rtr)
    mx = {c: grid_max(rows, c) for c in CRITERIA}
    return dict(rows=rows, rt_mean=rtm, rt_robust=rtr, maxima=mx,
                at_max=at_max(rows, mx))


# --------------------------------------------------------------------------
# runner assertions
# --------------------------------------------------------------------------
def assertions(sa, s1, s2, base, fwd, fwd_d290, panel, live, half):
    """D293's four, imported rather than reimplemented, plus four of this
    file's own. Importing them matters: a lag audit rewritten here would be a
    different audit, and the book under test is the same book."""
    C.assertions(sa, s1, s2, base, fwd, panel, live)
    T = base.shape[1]

    # 5. THE REFINEMENT MUST NOT MOVE THE CELLS IT DID NOT ADD. Adding horizons
    #    means re-running `forward_returns` with a larger HORIZONS set, and a
    #    monkeypatched module global is exactly the kind of "obviously harmless"
    #    change that silently is not. Every D290 horizon must come back
    #    BIT-IDENTICAL, and the profile computed on the fine grid must agree
    #    with D294's published JSON to the last printed digit.
    for k in HORIZONS_D290:
        a_, b_ = fwd[k], fwd_d290[k]
        assert a_.shape == b_.shape
        fa, fb = np.isfinite(a_), np.isfinite(b_)
        assert np.array_equal(fa, fb), f"fwd[{k}] coverage moved under refinement"
        assert np.array_equal(a_[fa], b_[fb]), (
            f"fwd[{k}] VALUES moved under refinement -- the fine grid is not a "
            f"superset of D290's")
    print(f"    [5] the {len(HORIZONS_FINE)}-horizon grid reproduces all "
          f"{len(HORIZONS_D290)} of D290's forward-return arrays bit-identically")

    d294 = json.loads((REPO / "data" / "d294_horizon_cost_profile.json").read_text())
    ref = {r["k"]: r for r in d294["results"]["confluence"]["rows"]}
    sc = score_book(sa, s1, s2, base, fwd, T, half)
    for k, r in ref.items():
        got = sc["rows"][k]
        for f_, g_ in (("bp", "bp"), ("t", "t"), ("x_mean", "x_mean"),
                       ("x_robust", "x_robust")):
            assert abs(got[g_] - r[f_]) < 1e-9, (
                f"D294 disagreement at k={k} on {f_}: {got[g_]} vs {r[f_]}")
    assert abs(sc["rt_mean"] - d294["results"]["confluence"]["round_trip_mean"]) < 1e-9
    assert abs(sc["rt_robust"]
               - d294["results"]["confluence"]["round_trip_robust"]) < 1e-9
    print(f"    [5b] and reproduces D294's published profile and round trip on "
          f"all {len(ref)} shared horizons to <1e-9")

    # 6. THE TWO SPEED REWRITES, GUARDED AGAINST WHAT THEY REPLACE.
    #    `tail_events` is `C.tail_grid` stopped early; `R.rotate` is the
    #    vectorised form of `R.rotate_loop`. Both must be EXACT, and the
    #    rotation is probed on the real score, which is the tie-heavy input.
    ev = tail_events(sa, s1, s2, base, T, np.random.default_rng(11))
    mine = C.cell_stats(fwd, ev[0], ev[1], T)
    theirs = C.tail_grid(sa, s1, s2, base, fwd, T, COMPOSITE,
                         np.random.default_rng(11), ns=(N_FIXED,))[N_FIXED]
    assert set(mine) == set(theirs), "tail rewrite changed the horizon set"
    for k in mine:
        assert mine[k] == theirs[k], f"TAIL REWRITE DIFFERS at k={k}"
    rp_ = R.rotate_plan(live)
    ats = rp_["ats"]
    off = np.random.default_rng(3).integers(1, T, size=live.shape[0])
    for nm, s in (("hist_L", sa), ("macd_hist", s1), ("rsi", s2)):
        a_ = R.rotate(s, rp_, off)
        b_ = R.rotate_loop(s, ats, off)
        fa, fb = np.isfinite(a_), np.isfinite(b_)
        assert np.array_equal(fa, fb) and np.array_equal(a_[fa], b_[fb]), (
            f"VECTORISED ROTATION DIFFERS from the loop on {nm}")
    print(f"    [6] tail rewrite == C.tail_grid and vectorised rotation == "
          f"rotate_loop, bit-identically, on all three scores")

    # 7. RIGHT QUANTITY, ON THE HORIZONS THIS FILE ADDED. Every new k must be
    #    the k-bar compounded return and NOT the (k-1)-bar one -- the grid the
    #    refinement could most easily have scored by accident. Checked against
    #    an independent accumulation of the log returns.
    logr = panel.total_log_returns
    for k in (11, 16, 26):
        acc = np.zeros_like(logr)
        okk = live.copy()
        for j in range(k):
            acc[:, :T - j] += logr[:, j:]
            okk[:, :T - j] &= live[:, j:]
        want = np.where(okk, np.expm1(acc), np.nan).astype(np.float32)
        m = np.isfinite(want) & np.isfinite(fwd[k])
        assert np.array_equal(np.isfinite(want), np.isfinite(fwd[k])), (
            f"fwd[{k}] coverage != an independent k-bar accumulation")
        assert np.array_equal(want[m], fwd[k][m]), f"fwd[{k}] is not k-bar"
        mm = np.isfinite(fwd[k]) & np.isfinite(fwd[k - 1])
        assert not np.array_equal(fwd[k][mm], fwd[k - 1][mm]), (
            f"fwd[{k}] == fwd[{k - 1}] -- the horizon grid is not what it says")
    print(f"    [7] right quantity on the added horizons: fwd[11], fwd[16], "
          f"fwd[26] each == an independent k-bar accumulation and != fwd[k-1]")

    # 8. THE COST-COVERAGE NULL IS A DIFFERENT NULL ONLY BECAUSE THE ROUND TRIP
    #    MOVES. Held at the observed round trip, x is gross times a positive
    #    constant, so its z is gross's z to machine precision. This is the
    #    claim the whole third criterion rests on, so it is computed, not
    #    stated. It must hold, AND the per-draw round trip must actually vary.
    rng = np.random.default_rng(SEED)
    rt_seen, bps, xs = [], [], []
    for _ in range(6):
        pj = C.permute_joint([sa, s1, s2], base, rng)
        s_ = score_book(pj[0], pj[1], pj[2], base, fwd, T, half)
        rt_seen.append(s_["rt_robust"])
        bps.append(s_["maxima"]["bp"][1])
        xs.append(s_["maxima"]["x_robust"][1])
    bps, xs, rt_seen = map(np.array, (bps, xs, rt_seen))
    zb = (sc["maxima"]["bp"][1] - bps.mean()) / bps.std(ddof=1)
    fixed = bps / sc["rt_robust"]
    zf = (sc["maxima"]["x_robust"][1] - fixed.mean()) / fixed.std(ddof=1)
    assert abs(zb - zf) < 1e-9, (
        f"a FIXED round trip did not reduce the cost-coverage z to gross's "
        f"({zb:.6f} vs {zf:.6f}); the scaling argument is wrong")
    spread_rt = float(rt_seen.max() - rt_seen.min())
    assert spread_rt > 1e-6, (
        "the null's round trip never moved, so the cost-coverage null is the "
        "gross null and must not be reported as a separate test")
    print(f"    [8] cost coverage at a FIXED round trip has gross's z exactly "
          f"({zb:+.4f}); the null's own round trip moves over "
          f"{rt_seen.min():.1f}-{rt_seen.max():.1f} bp, which is what makes it "
          f"a different null")


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    t0 = time.time()

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == R.BC.cache_key(M.B.FIXTURE), "CACHE IS STALE"
    base = z["warm"] & live
    fwd_d290 = M.forward_returns(panel, live)          # D290's twelve, for [5]
    M.HORIZONS = HORIZONS_FINE                         # the refinement
    C.HORIZONS = HORIZONS_FINE
    fwd = M.forward_returns(panel, live)
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fwd_o = ET.open_entry(on, idr, live, HORIZONS_FINE)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    last = np.array([np.flatnonzero(live[i]).max() if live[i].any() else -1
                     for i in range(live.shape[0])])
    dead = last < (T - 1)
    sa, s1, s2 = z[C.PRIMARY], z[C.PAIR[0]], z[C.PAIR[1]]

    print(f"D296  criterion-matched grid-max nulls")
    print(f"  candidate: {C.PRIMARY} x mean-rank({C.PAIR[0]}, {C.PAIR[1]}) @ "
          f"f={C.FRAC}, N={N_FIXED}, {CON}   [FIXED, not re-searched]")
    print(f"  search space priced: max over {len(HORIZONS_FINE)} horizons "
          f"{HORIZONS_FINE[0]}..{HORIZONS_FINE[-1]}  (D290 had "
          f"{len(HORIZONS_D290)})")
    print(f"  base {int(base.sum()):,} cells  ({time.time() - t0:.0f}s)",
          flush=True)

    assertions(sa, s1, s2, base, fwd, fwd_d290, panel, live, half)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---------------------------------------------------------------- observed
    obs = score_book(sa, s1, s2, base, fwd, T, half)
    ranks_obs = C.rank_all(sa, s1, s2, base, COMPOSITE)
    b_obs = C.book(ranks_obs, N_FIXED, T, COMPOSITE)
    rt_ev = rt_events(b_obs[0], b_obs[1], half)
    cs_o = C.cell_stats(fwd_o, b_obs[0], b_obs[1], T)

    print(f"\n{'=' * 100}")
    print(f"  THE FINE HORIZON PROFILE   N={N_FIXED}   round trip: mean "
          f"{obs['rt_mean']:.1f} bp, robust(median) {obs['rt_robust']:.1f} bp"
          f"   [entry-cell: {rt_ev[0]:.1f} / {rt_ev[1]:.1f}]")
    print(f"{'=' * 100}")
    print(f"  {'k':>3s} | {'gross bp':>9s} {'t':>6s} {'bars':>6s} | "
          f"{'bp/bar':>7s} | {'x mean':>7s} {'x robust':>9s} | {'open bp':>9s} "
          f"{'open t':>7s} {'kept':>6s} |")
    peaks = {c: obs["maxima"][c] for c in CRITERIA}
    for k in HORIZONS_FINE:
        r = obs["rows"].get(k)
        if r is None:
            continue
        ro = cs_o.get(k, {}).get(CON)
        tags = ("D290 " if k in HORIZONS_D290 else "     ") + " ".join(
            f"<-max {c}" for c in CRITERIA if peaks[c][0] == k)
        kept = f"{ro[0] / r['bp']:+6.0%}" if (ro and r["bp"]) else "    --"
        print(f"  {k:3d} | {r['bp']:+9.2f} {r['t']:+6.2f} {r['bars']:6d} | "
              f"{r['bp_per_bar']:+7.2f} | {r['x_mean']:7.3f} "
              f"{r['x_robust']:9.3f} | "
              f"{(f'{ro[0]:+9.2f}' if ro else '       --')} "
              f"{(f'{ro[1]:+7.2f}' if ro else '     --')} "
              f"{kept} | {tags}")
    print(f"\n  observed grid maxima over the {len(HORIZONS_FINE)}-horizon grid:")
    for c in CRITERIA:
        k, v = peaks[c]
        print(f"    max {c:9s} -> k={k:<3d} value {v:+.4f}   "
              f"(bp {obs['rows'][k]['bp']:+.2f}, t {obs['rows'][k]['t']:+.2f}, "
              f"bp/bar {obs['rows'][k]['bp_per_bar']:+.2f}, "
              f"x robust {obs['rows'][k]['x_robust']:.3f})")

    # gate 1g at the gross peak, so the cost ratio is readable
    k_gross = peaks["bp"][0]
    plan, klo, khi = b_obs[2], b_obs[3], b_obs[4]
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    print(f"\n  gate 1g, at the gross peak k={k_gross} (turnover is not a "
          f"function of k -- one book, held longer):")
    for side, rows, mask, ev in (("long", plan.lo, klo, b_obs[0]),
                                 ("short", plan.hi, khi, b_obs[1])):
        v = half[rows[mask], bc[mask]]
        v = v[np.isfinite(v)]
        nbar = mask.sum(axis=0)
        fresh = ev[0].size
        print(f"    {side:5s} | held {nbar[nbar > 0].mean():5.1f} | entries "
              f"{fresh:6,d} | turnover {fresh / max(nbar.sum(), 1):5.1%}/bar | "
              f"run {nbar.sum() / max(fresh, 1):5.1f} bars | dead "
              f"{dead[rows[mask]].mean():5.1%} | half-spread mean "
              f"{v.mean():6.1f} median {np.median(v):6.1f} bp")
    print(f"    breakeven: the book pays at "
          f"{obs['rows'][k_gross]['bp'] / 4:.1f} bp/side (equal legs); it faces "
          f"{obs['rt_mean'] / 4:.1f} mean / {obs['rt_robust'] / 4:.1f} median")

    # ------------------------------------------------------------------ nulls
    rp = R.rotate_plan(live)
    n_names = live.shape[0]

    def draw(key, d):
        rng = np.random.default_rng(SEED + 17 * d)
        out = {}
        rot = [R.rotate(s, rp, rng.integers(1, T, size=n_names))
               for s in (sa, s1, s2)]
        out["rotation"] = score_book(rot[0], rot[1], rot[2], base, fwd, T, half)
        pj = C.permute_joint([sa, s1, s2], base, rng)
        out["permutation"] = score_book(pj[0], pj[1], pj[2], base, fwd, T, half)
        out["tail"] = score_tail(sa, s1, s2, base, fwd, T, half, rng)
        return {n: (None if s_ is None else
                    dict(maxima={c: s_["maxima"][c] for c in CRITERIA},
                         at_max=s_["at_max"],
                         rt_mean=s_["rt_mean"], rt_robust=s_["rt_robust"]))
                for n, s_ in out.items()}

    print(f"\n  LADDER: {a.draws} draws x 3 nulls x 4 criteria, "
          f"{a.workers} threads", flush=True)
    t1 = time.time()
    res = FN.parallel_map(draw, [(d, d) for d in range(a.draws)],
                          workers=a.workers)
    print(f"    {a.draws} draws in {time.time() - t1:.0f}s", flush=True)

    nulls = {}
    for nn in ("rotation", "permutation", "tail"):
        nulls[nn] = {}
        rts = np.array([res[d][nn]["rt_robust"] for d in sorted(res)
                        if res[d][nn] is not None])
        for c in CRITERIA:
            arr = np.array([res[d][nn]["maxima"][c][1] for d in sorted(res)
                            if res[d][nn] is not None
                            and res[d][nn]["maxima"][c] is not None])
            ks = np.array([res[d][nn]["maxima"][c][0] for d in sorted(res)
                           if res[d][nn] is not None
                           and res[d][nn]["maxima"][c] is not None])
            o = peaks[c][1]
            sd = arr.std(ddof=1) if arr.size > 1 else 0.0
            nulls[nn][c] = dict(
                n=int(arr.size), p50=float(np.percentile(arr, 50)),
                p95=float(np.percentile(arr, 95)), max=float(arr.max()),
                mean=float(arr.mean()), sd=float(sd),
                z=(float((o - arr.mean()) / sd) if sd > 0 else None),
                pct=float((arr >= o).mean()),
                mode_k=int(np.bincount(ks).argmax()))
        nulls[nn]["rt_robust_p50"] = float(np.percentile(rts, 50))
        nulls[nn]["rt_robust_p05_p95"] = [float(np.percentile(rts, 5)),
                                          float(np.percentile(rts, 95))]

    print(f"\n{'=' * 100}")
    print(f"  CRITERION-MATCHED GRID-MAX NULLS  ({a.draws} draws, grid = "
          f"{len(HORIZONS_FINE)} horizons at N={N_FIXED}, {CON})")
    print(f"{'=' * 100}")
    print(f"  {'criterion':10s} {'obs k':>5s} {'observed':>10s} | {'null':12s} "
          f"{'p50':>9s} {'p95':>9s} {'max':>9s} {'z':>7s} {'p':>6s} "
          f"{'null k*':>7s}")
    verdict = {}
    for c in CRITERIA:
        k, o = peaks[c]
        zs = []
        for i, nn in enumerate(("rotation", "permutation", "tail")):
            s_ = nulls[nn][c]
            zs.append(s_["z"])
            head = (f"  {c:10s} {k:5d} {o:+10.4f} | " if i == 0
                    else f"  {'':10s} {'':5s} {'':10s} | ")
            zt = f"{s_['z']:+7.2f}" if s_["z"] is not None else "     --"
            print(head + f"{nn:12s} {s_['p50']:+9.4f} {s_['p95']:+9.4f} "
                  f"{s_['max']:+9.4f} {zt} "
                  f"{s_['pct']:6.3f} {s_['mode_k']:7d}")
        mn = min([v for v in zs if v is not None], default=None)
        worst = max(nulls[nn][c]["pct"] for nn in
                    ("rotation", "permutation", "tail"))
        verdict[c] = dict(k=k, observed=o, min_z=mn, worst_p=worst,
                          clears=bool(mn is not None and mn > 0 and worst < 0.05))
        print(f"  {'':10s} {'':5s} {'':10s} | {'MIN z':12s} "
              f"{'':9s} {'':9s} {'':9s} "
              f"{(f'{mn:+7.2f}' if mn is not None else '     --')} "
              f"{worst:6.3f}   -> {'CLEARS' if verdict[c]['clears'] else 'fails'}")

    # ---------------------------------------------------- cross-criterion table
    # "gross at the k that maximises t" vs a null that also picks its OWN t-peak
    # and reads gross there. The diagonal reproduces the table above.
    cross = {}
    print(f"\n{'=' * 100}")
    print(f"  CROSS-CRITERION: value of R at the k SELECTED BY S, against a "
          f"null that runs the SAME selection")
    print(f"{'=' * 100}")
    print(f"  {'select by S':12s} {'k':>3s} {'report R':10s} {'observed':>10s} | "
          f"{'rot z':>7s} {'perm z':>7s} {'tail z':>7s} {'MIN z':>7s} "
          f"{'worst p':>8s}  verdict")
    for s_sel in CRITERIA:
        ksel = peaks[s_sel][0]
        cross[s_sel] = {}
        for r_rep in CRITERIA:
            o = obs["at_max"][s_sel][r_rep]
            zz, pp = [], []
            cross[s_sel][r_rep] = {}
            for nn in ("rotation", "permutation", "tail"):
                arr = np.array([res[d][nn]["at_max"][s_sel][r_rep]
                                for d in sorted(res)
                                if res[d][nn] is not None
                                and res[d][nn]["at_max"][s_sel] is not None])
                sd = arr.std(ddof=1) if arr.size > 1 else 0.0
                zz.append(float((o - arr.mean()) / sd) if sd > 0 else None)
                pp.append(float((arr >= o).mean()))
                cross[s_sel][r_rep][nn] = dict(
                    n=int(arr.size), p50=float(np.percentile(arr, 50)),
                    p95=float(np.percentile(arr, 95)), max=float(arr.max()),
                    mean=float(arr.mean()), sd=float(sd), z=zz[-1], pct=pp[-1])
            mn = min([v for v in zz if v is not None], default=None)
            wp = max(pp)
            ok = bool(mn is not None and mn > 0 and wp < 0.05)
            cross[s_sel][r_rep]["min_z"] = mn
            cross[s_sel][r_rep]["worst_p"] = wp
            cross[s_sel][r_rep]["clears"] = ok
            mark = "  (criterion-matched)" if s_sel == r_rep else ""
            zt = " ".join((f"{v:+7.2f}" if v is not None else "     --")
                          for v in zz)
            mt = f"{mn:+7.2f}" if mn is not None else "     --"
            print(f"  {s_sel:12s} {ksel:3d} {r_rep:10s} {o:+10.4f} | {zt} {mt} "
                  f"{wp:8.3f}  {'CLEARS' if ok else 'fails'}{mark}")
        print()
    print(f"\n  the null's own round trip (robust), p50 [p5, p95]:")
    for nn in ("rotation", "permutation", "tail"):
        lo_, hi_ = nulls[nn]["rt_robust_p05_p95"]
        print(f"    {nn:12s} {nulls[nn]['rt_robust_p50']:7.1f} bp "
              f"[{lo_:6.1f}, {hi_:6.1f}]   observed "
              f"{obs['rt_robust']:.1f} (membership) / {rt_ev[1]:.1f} (entry)")

    json.dump({"purpose": "D296: R14/4th-amendment(2026-09-03) -- the grid-max "
                          "null D290/D293 ran prices the search for max t. The "
                          "gross and cost-coverage peaks D294 found on the same "
                          "grid are priced here against nulls whose grid "
                          "maximum is taken on the SAME criterion.",
               "candidate": {"primary": C.PRIMARY, "pair": list(C.PAIR),
                             "f": C.FRAC, "N": N_FIXED, "construction": CON},
               "search_space": {"horizons": list(HORIZONS_FINE),
                                "d290_horizons": list(HORIZONS_D290),
                                "note": "N and construction FIXED; narrower "
                                        "than D293's grid-max, so z is not "
                                        "comparable to D293's"},
               "draws": a.draws, "seed": SEED,
               "observed": {"rows": {str(k): v for k, v in obs["rows"].items()},
                            "rt_mean": obs["rt_mean"],
                            "rt_robust": obs["rt_robust"],
                            "rt_mean_entrycells": rt_ev[0],
                            "rt_robust_entrycells": rt_ev[1],
                            "maxima": {c: list(peaks[c]) for c in CRITERIA},
                            "open_entry": {str(k): list(v[CON])
                                           for k, v in cs_o.items()
                                           if CON in v}},
               "nulls": nulls, "cross": cross, "verdict": verdict},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
