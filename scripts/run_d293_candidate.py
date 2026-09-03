"""D293 -- the confluence book as a candidate, through D290's own stage-1 ladder.

    uv run python scripts/run_d293_candidate.py --selftest
    uv run python scripts/run_d293_candidate.py [--draws 200] [--splits 10]

PRE-REGISTERED AT `49f8730`, CORRECTED AT `1e942ab`, both committed before this
file existed (R8). This runner may not re-search f, the partner pair, the
primary, or add a construction.

STAGE 1 CONSUMES NOTHING SCARCE. Gates nothing, closes nothing, reads no
holdout.

TWO CANDIDATES THROUGH ONE IDENTICAL LADDER, so condition 4 is a fair fight:

    hist_L                                     D290's tier-1 cell
    hist_L x mean-rank(macd_hist, rsi) @ 0.75  the confluence book

Both get D290's grid -- N in {3,5,10,25,50}, 12 horizons, long/short/spread --
and D290's three nulls, each taking the GRID MAXIMUM matched to the observed
grid maximum. D292 compared a book chosen at f=0.75 against hist_L at a FIXED
cell; that asymmetry is the thing this file removes.

THE THREE NULLS, AND WHAT HAD TO CHANGE FOR A THREE-INPUT CANDIDATE:

  rotation      roll ALL THREE inputs within each name's own live bars, with
                INDEPENDENT offsets. Each input keeps its coverage, turnover and
                autocorrelation; every alignment dies.
  permutation   permute the NAME LABELS within a bar and apply that ONE
                permutation to ALL THREE scores. This preserves the
                cross-signal correlation structure EXACTLY -- a name's triple
                moves together -- and destroys only which name holds which
                triple. Permuting the three independently would destroy the
                very thing this study is about, and would be a null for a
                different question.
  tail          pool the 2N' most extreme by the COMPOSITE selection and assign
                the sides at random. Matched-count is not matched-nuisance; this
                pool carries the same volatility and liquidity the composite
                selects on, so what it removes is only the directional claim.

Assertion [4] holds the permutation null to that claim rather than asserting it
in prose.
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


D = _load("d292", "run_d292_third_order.py")
ET = _load("d290et", "d290_entry_test.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M, FN = D.R, D.M, D.FN

OUT = REPO / "data" / "d293_candidate.json"
PRIMARY = "hist_L"
PAIR = ("macd_hist", "rsi")
FRAC = 0.75
N_LEVELS = (3, 5, 10, 25, 50)          # D290's grid, unchanged
HORIZONS = M.HORIZONS                  # D290's 12
CONSTRUCTIONS = ("long", "short", "spread")
MIN_BARS = M.MIN_BARS
SEED = 20260903
CAPTURABLE_T = 2.0


# --------------------------------------------------------------------------
# the book
# --------------------------------------------------------------------------
def rank_all(sa, s1, s2, base, composite):
    """The three rankings, ONCE. Hoisted out of the N loop: the sort does not
    depend on N and the grid reads five N off the same ranking, so ranking
    inside `book` did 15 argsorts per grid call where 3 suffice -- and the grid
    is called 1,200 times per candidate under the nulls."""
    ra = R.ranked(sa, base)
    if not composite:
        return ra, None, None
    return ra, R.ranked(s1, base), R.ranked(s2, base)


def book(ranks, N, T, composite):
    """Fresh-entry indices for one (candidate, N), from pre-computed rankings.

    `composite=False` returns hist_L alone, so the head-to-head runs through
    exactly the same code path and any bug hits both books equally.
    """
    (order_a, cnt_a, _), r1, r2 = ranks
    plan = R.LegPlan(order_a, cnt_a, N, T)
    if plan.cols.size == 0:
        return None
    if composite:
        _, c1, p1 = r1
        _, c2, p2 = r2
        klo, khi = D.op_meanrank(
            R.pct_at(p1, c1, plan.lo, plan.cols),
            R.pct_at(p1, c1, plan.hi, plan.cols),
            R.pct_at(p2, c2, plan.lo, plan.cols),
            R.pct_at(p2, c2, plan.hi, plan.cols), FRAC, N)
    else:
        klo = np.ones(plan.lo.shape, dtype=bool)
        khi = np.ones(plan.hi.shape, dtype=bool)
    return (R.fresh_events(plan, "lo", klo),
            R.fresh_events(plan, "hi", khi), plan, klo, khi)


def cell_stats(fwd, lo_idx, hi_idx, T):
    """Per-horizon (bp, t, bars) for all three constructions.

    The same arithmetic D290 used, in the same order: a control computed by
    slightly different code is not a control for that number.
    """
    lr, lc = lo_idx
    hr, hc = hi_idx
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
        row = {}
        for name, d in (("long", lo), ("short", -hi), ("spread", lo - hi)):
            sd = d.std(ddof=1)
            row[name] = (float(d.mean() * 1e4),
                         float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else 0.0,
                         int(d.size))
        out[k] = row
    return out


def grid(sa, s1, s2, base, fwd, T, composite, ns=N_LEVELS, ranks=None):
    ranks = ranks if ranks is not None else rank_all(sa, s1, s2, base, composite)
    g = {}
    for N in ns:
        b = book(ranks, N, T, composite)
        if b is None:
            continue
        g[N] = cell_stats(fwd, b[0], b[1], T)
    return g


def peak(g, con):
    best = None
    for N, rows in g.items():
        for k, row in rows.items():
            if con in row and (best is None or row[con][1] > best[2][1]):
                best = (N, k, row[con])
    return best


def grid_max_t(g, con):
    b = peak(g, con)
    return -9e9 if b is None else b[2][1]


# --------------------------------------------------------------------------
# the three nulls
# --------------------------------------------------------------------------
def permute_joint(scores, base, rng):
    """ONE permutation of the name labels per bar, applied to ALL THREE scores.

    Preserves the cross-signal correlation structure exactly, because a name's
    whole triple moves together. Permuting the three independently would
    destroy the correlation between them, which is the thing under test.
    """
    outs = [np.full(s.shape, np.nan) for s in scores]
    for t in range(base.shape[1]):
        idx = np.flatnonzero(base[:, t])
        if idx.size > 1:
            p = rng.permutation(idx)
            for o, s in zip(outs, scores):
                o[idx, t] = s[p, t]
    return outs


def tail_grid(sa, s1, s2, base, fwd, T, composite, rng, ns=N_LEVELS):
    """D283's control: the composite's OWN extremes, sides assigned at random."""
    n, T_ = base.shape
    ranks = rank_all(sa, s1, s2, base, composite)
    g = {}
    for N in ns:
        b = book(ranks, N, T_, composite)
        if b is None:
            continue
        (lr, lc), (hr, hc) = b[0], b[1]
        # pool the two legs bar by bar and re-deal the sides
        ev_lo = np.zeros((n, T_), dtype=bool)
        ev_hi = np.zeros((n, T_), dtype=bool)
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
            half = rows.size // 2
            ev_lo[p[:half], allc[a_]] = True
            ev_hi[p[half:2 * half], allc[a_]] = True
        g[N] = cell_stats(fwd, np.nonzero(ev_lo), np.nonzero(ev_hi), T_)
    return g


def name_split_cv(sa, s1, s2, base, fwd, T, composite, splits, rng):
    """Pick the peak cell on half A, SCORE THAT CELL on half B (gate 1f)."""
    n = base.shape[0]
    got = {c: [] for c in CONSTRUCTIONS}
    for _ in range(splits):
        perm = rng.permutation(n)
        a, b = perm[: n // 2], perm[n // 2:]
        ba = np.zeros_like(base)
        ba[a] = base[a]
        bb = np.zeros_like(base)
        bb[b] = base[b]
        ga = grid(sa, s1, s2, ba, fwd, T, composite)
        gb = grid(sa, s1, s2, bb, fwd, T, composite)
        for con in CONSTRUCTIONS:
            pa = peak(ga, con)
            if pa is None:
                continue
            N, k, _ = pa
            row = gb.get(N, {}).get(k)
            if row and con in row:
                got[con].append(row[con][1])
    return {c: (float(np.mean(v)) if v else None,
                float(np.std(v)) if len(v) > 1 else None, len(v))
            for c, v in got.items()}


# --------------------------------------------------------------------------
# runner assertions
# --------------------------------------------------------------------------
def assertions(sa, s1, s2, base, fwd, panel, live):
    print("\n  RUNNER ASSERTIONS", flush=True)
    T = base.shape[1]
    N = 25

    # 0. THE COMPOSITE MUST REDUCE TO ITS PRIMARY when nothing is filtered out.
    #    At f=1.0 mean-rank keeps all N, so the book must equal hist_L alone.
    #    An operator that does not degenerate correctly says nothing when it
    #    does filter.
    order_a, cnt_a, _ = R.ranked(sa, base)
    plan = R.LegPlan(order_a, cnt_a, N, T)
    _, c1, p1 = R.ranked(s1, base)
    _, c2, p2 = R.ranked(s2, base)
    kl, kh = D.op_meanrank(R.pct_at(p1, c1, plan.lo, plan.cols),
                           R.pct_at(p1, c1, plan.hi, plan.cols),
                           R.pct_at(p2, c2, plan.lo, plan.cols),
                           R.pct_at(p2, c2, plan.hi, plan.cols), 1.0, N)
    assert kl.all() and kh.all(), (
        "DEGENERACY FAILED: mean-rank at f=1.0 dropped "
        f"{int((~kl).sum() + (~kh).sum())} names; it must keep all N")
    print(f"    [0] the composite reduces to {PRIMARY} exactly at f=1.0")

    # 1. LAG AUDIT, SECOND IMPLEMENTATION, ALL THREE SCORES. The book ranks on
    #    hist_L at t-1 and filters on macd_hist and rsi at t-1. A filter read at
    #    bar t's own close is look-ahead no primary-only audit would ever see.
    def hand(mask_a, mask_1, mask_2, h_a, h_1, h_2):
        o, c, _ = R.ranked(mask_a, base)
        pl = R.LegPlan(o, c, N, T)
        _, ca, pa = R.ranked(mask_1, base)
        _, cb, pb = R.ranked(mask_2, base)
        klo, _ = D.op_meanrank(R.pct_at(pa, ca, pl.lo, pl.cols),
                               R.pct_at(pa, ca, pl.hi, pl.cols),
                               R.pct_at(pb, cb, pl.lo, pl.cols),
                               R.pct_at(pb, cb, pl.hi, pl.cols), FRAC, N)
        keep_k = max(1, int(round(FRAC * N)))
        checked = 0
        for j in range(0, pl.cols.size, max(1, pl.cols.size // 9)):
            t = int(pl.cols[j])
            if t == 0:
                continue
            q = np.flatnonzero(base[:, t])
            va = h_a[q, t - 1]
            qa = q[np.isfinite(va)]
            if qa.size < 60:
                continue
            pick = qa[np.argsort(h_a[qa, t - 1], kind="stable")[:N]]
            pcts = []
            for src in (h_1, h_2):
                v = src[q, t - 1]
                qq = q[np.isfinite(v)]
                rb = qq[np.argsort(src[qq, t - 1], kind="stable")]
                rank = {int(r): i for i, r in enumerate(rb)}
                pcts.append({r: (rank[r] + 0.5) / len(rb) if r in rank else np.nan
                             for r in map(int, pick)})
            avg = {int(r): (pcts[0][int(r)] + pcts[1][int(r)]) / 2 for r in pick}
            fin = [r for r in avg if np.isfinite(avg[r])]
            want = set(sorted(fin, key=lambda r: (avg[r], r))[:min(keep_k, len(fin))])
            got = {int(r) for r in pl.lo[klo[:, j], j]}
            assert want == got, f"LAG AUDIT FAILED at t={t}: {want ^ got}"
            checked += 1
        return checked

    checked = hand(sa, s1, s2, sa, s1, s2)
    assert checked >= 5, f"lag audit covered only {checked} bars"
    print(f"    [1] lag audit: the primary AND both filters rebuilt from the "
          f"unlagged scores on {checked} bars, identical")

    raised = False
    try:
        hand(sa, np.roll(s1, -1, axis=1), s2, sa, s1, s2)
    except AssertionError:
        raised = True
    assert raised, "the lag audit PASSED a filter read one bar early"
    print(f"    [1b] and it raises when a filter is read one bar early")

    # 2. SIGN AUDIT, IN MONEY, ON ALL THREE CONSTRUCTIONS, THROUGH THE COMPOSITE.
    #    An oracle ranks, after the book's own lag, on MINUS the return the
    #    position is about to earn. Every construction must be strongly
    #    positive -- SHORT is the sign D280 got wrong for five parts on prose.
    f1 = fwd[1].astype(np.float64)
    oracle = np.full(f1.shape, np.nan)
    oracle[:, :-1] = -f1[:, 1:]
    g = grid(oracle, oracle, oracle, base, fwd, T, True, ns=(25,))
    row = g[25][1]
    for con in CONSTRUCTIONS:
        bp = row[con][0]
        assert bp > 100.0, (
            f"SIGN AUDIT FAILED: oracle {con} earns {bp:+.1f} bp through the "
            f"composite; a perfect-foresight book must be strongly positive")
    print(f"    [2] sign audit in money: oracle through the composite earns "
          + ", ".join(f"{c} {row[c][0]:+,.0f} bp" for c in CONSTRUCTIONS))

    # 3. RIGHT QUANTITY, twice. fwd[1] is the one-bar simple return and nothing
    #    else, and the composite book is NOT the primary's book.
    r1 = np.expm1(panel.total_log_returns)
    m = np.isfinite(fwd[1]) & live
    d = np.abs(fwd[1][m].astype(np.float64) - r1[m])
    assert d.max() < 1e-6, f"fwd[1] is not the one-bar return: {d.max():.3e}"
    ba = book(rank_all(sa, s1, s2, base, True), N, T, True)
    bb = book(rank_all(sa, s1, s2, base, False), N, T, False)
    assert ba[0][0].size != bb[0][0].size, (
        "RIGHT QUANTITY FAILED: the composite book has the same event count as "
        f"{PRIMARY} alone -- the filter removed nothing")
    print(f"    [3] right quantity: fwd[1] == expm1(log return) on "
          f"{int(m.sum()):,} cells; composite holds {ba[0][0].size:,} long "
          f"entries against the primary's {bb[0][0].size:,}")

    # 4. THE PERMUTATION NULL MUST PRESERVE THE CROSS-SIGNAL CORRELATION. That
    #    is the whole reason one permutation is applied to all three scores, and
    #    it is a claim about code, so it is checked rather than asserted.
    rng = np.random.default_rng(5)
    pa, pb, pc = permute_joint([sa, s1, s2], base, rng)
    for nm, (x, y, xp, yp) in (("primary/B1", (sa, s1, pa, pb)),
                               ("B1/B2", (s1, s2, pb, pc))):
        got = []
        for t in range(200, T, 601):
            q = np.flatnonzero(base[:, t])
            u, v = x[q, t], y[q, t]
            up, vp = xp[q, t], yp[q, t]
            f = np.isfinite(u) & np.isfinite(v)
            fp = np.isfinite(up) & np.isfinite(vp)
            if f.sum() < 50 or fp.sum() < 50:
                continue
            got.append((float(np.corrcoef(u[f], v[f])[0, 1]),
                        float(np.corrcoef(up[fp], vp[fp])[0, 1])))
        a_ = np.array(got)
        dmax = float(np.abs(a_[:, 0] - a_[:, 1]).max())
        assert dmax < 1e-9, (
            f"PERMUTATION NULL BROKE THE {nm} CORRELATION by {dmax:.2e}; it "
            f"must move a name's whole triple together")
    print(f"    [4] the permutation null preserves the within-bar correlation "
          f"between all three scores, exactly")


# --------------------------------------------------------------------------
def one_candidate(nm, sa, s1, s2, base, fwd, fwd_o, T, live, ats, composite,
                  half, dead, eras, draws, splits, workers):
    """One candidate through the whole ladder."""
    t0 = time.time()
    ranks_obs = rank_all(sa, s1, s2, base, composite)
    gobs = grid(sa, s1, s2, base, fwd, T, composite, ranks=ranks_obs)
    obs = {c: peak(gobs, c) for c in CONSTRUCTIONS}

    cv = name_split_cv(sa, s1, s2, base, fwd, T, composite, splits,
                       np.random.default_rng(SEED + 7))

    rp = R.rotate_plan(live)

    def draw(key, d):
        rng = np.random.default_rng(SEED + 17 * d + (1 if composite else 0))
        out = {}
        rot = [R.rotate(s, rp, rng.integers(1, T, size=live.shape[0]))
               for s in (sa, s1, s2)]
        out["rotation"] = grid(rot[0], rot[1], rot[2], base, fwd, T, composite)
        pj = permute_joint([sa, s1, s2], base, rng)
        out["permutation"] = grid(pj[0], pj[1], pj[2], base, fwd, T, composite)
        out["tail"] = tail_grid(sa, s1, s2, base, fwd, T, composite, rng)
        return {n: {c: grid_max_t(gg, c) for c in CONSTRUCTIONS}
                for n, gg in out.items()}

    res = FN.parallel_map(draw, [(d, d) for d in range(draws)], workers=workers)
    zs = {}
    for nulln in ("rotation", "permutation", "tail"):
        zs[nulln] = {}
        for con in CONSTRUCTIONS:
            arr = np.array([res[d][nulln][con] for d in res
                            if res[d][nulln][con] > -8e9])
            o = obs[con][2][1] if obs[con] else None
            zs[nulln][con] = (None if o is None or arr.size < 5
                              or arr.std(ddof=1) == 0
                              else float((o - arr.mean()) / arr.std(ddof=1)))

    # gate 1e, at each construction's own peak cell
    cap = {}
    for con in CONSTRUCTIONS:
        if not obs[con]:
            continue
        N, k, _ = obs[con]
        b = book(ranks_obs, N, T, composite)
        cs_c = cell_stats(fwd, b[0], b[1], T).get(k, {}).get(con)
        cs_o = cell_stats(fwd_o, b[0], b[1], T).get(k, {}).get(con)
        cap[con] = dict(close=cs_c, open=cs_o,
                        retained=(cs_o[0] / cs_c[0]) if (cs_c and cs_o
                                                         and cs_c[0]) else None)

    # 1g / cost / era, at the SPREAD peak
    extra = {}
    if obs["spread"]:
        N, k, _ = obs["spread"]
        b = book(ranks_obs, N, T, composite)
        plan, klo, khi = b[2], b[3], b[4]
        bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
        for side, rows, mask in (("long", plan.lo, klo), ("short", plan.hi, khi)):
            held_r, held_c = rows[mask], bc[mask]
            v = half[held_r, held_c]
            v = v[np.isfinite(v)]
            n_bar = mask.sum(axis=0)
            fresh = (b[0] if side == "long" else b[1])[0].size
            extra[side] = dict(
                cost_mean=float(v.mean()), cost_median=float(np.median(v)),
                dead=float(dead[held_r].mean()),
                held=float(n_bar[n_bar > 0].mean()),
                turnover=float(fresh / max(n_bar.sum(), 1)),
                run=float(n_bar.sum() / max(fresh, 1)))
        era = {}
        for en, mm in eras.items():
            bb = base & mm[None, :]
            gg = grid(sa, s1, s2, bb, fwd, T, composite, ns=(N,))
            row = gg.get(N, {}).get(k)
            era[en] = None if not row else row["spread"][:2]
        extra["era"] = era
        extra["edge"] = ("corner" if (N == max(N_LEVELS) and k == max(HORIZONS))
                         else "edge" if (N == max(N_LEVELS) or k == max(HORIZONS))
                         else "interior")
    print(f"    {nm}: done in {time.time() - t0:.0f}s", flush=True)
    return dict(observed={c: (obs[c][0], obs[c][1], obs[c][2]) if obs[c] else None
                          for c in CONSTRUCTIONS},
                cv=cv, z=zs, capturability=cap, extra=extra)


def fmt(v, w, d=2):
    return f"{v:+{w}.{d}f}" if v is not None else f"{'--':>{w}s}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--splits", type=int, default=10)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    t0 = time.time()

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == R.BC.cache_key(M.B.FIXTURE), "CACHE IS STALE"
    base = z["warm"] & live
    fwd = M.forward_returns(panel, live)
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fwd_o = ET.open_entry(on, idr, live, HORIZONS)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    last = np.array([np.flatnonzero(live[i]).max() if live[i].any() else -1
                     for i in range(live.shape[0])])
    dead = last < (T - 1)
    yrs = np.array([int(str(dd)[:4]) for dd in panel.dates])
    eras = {"pre2020": yrs < 2020, "2020": yrs == 2020, "post2020": yrs > 2020}
    sa, s1, s2 = z[PRIMARY], z[PAIR[0]], z[PAIR[1]]

    print(f"D293  {PRIMARY} x mean-rank({PAIR[0]}, {PAIR[1]}) @ f={FRAC}   vs   "
          f"{PRIMARY} alone")
    print(f"  grid: {len(N_LEVELS)} N x {len(HORIZONS)} horizons x "
          f"{len(CONSTRUCTIONS)} constructions | base {int(base.sum()):,} cells "
          f"({time.time() - t0:.0f}s)", flush=True)

    assertions(sa, s1, s2, base, fwd, panel, live)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    ats = [np.flatnonzero(live[i]) for i in range(live.shape[0])]
    print(f"\n  LADDER: {a.draws} draws x 3 nulls, {a.splits} name splits, "
          f"{a.workers} threads", flush=True)
    out = {}
    for nm, comp in (("confluence", True), (PRIMARY, False)):
        out[nm] = one_candidate(nm, sa, s1, s2, base, fwd, fwd_o, T, live, ats,
                                comp, half, dead, eras, a.draws, a.splits,
                                a.workers)

    print(f"\n{'=' * 92}")
    print(f"  CONDITIONS 1-3, per construction")
    print(f"{'=' * 92}")
    print(f"  {'candidate':12s} {'con':7s} {'N':>3s} {'k':>3s} | {'bp':>8s} "
          f"{'t':>6s} | {'rot z':>6s} {'perm z':>6s} {'tail z':>6s} "
          f"{'min z':>6s} | {'CV t':>6s} | {'open t':>7s} {'kept':>6s} | 1-3")
    verdict = {}
    for nm in out:
        for con in CONSTRUCTIONS:
            o = out[nm]["observed"][con]
            if not o:
                continue
            N, k, (bp, t_, _) = o
            zz = [out[nm]["z"][x][con] for x in ("rotation", "permutation", "tail")]
            mn = min([v for v in zz if v is not None], default=None)
            cvt = out[nm]["cv"][con][0]
            cp = out[nm]["capturability"].get(con, {})
            oe = cp.get("open")
            ret = cp.get("retained")
            ok = (mn is not None and mn > 0 and cvt is not None and cvt > 0
                  and oe is not None and oe[1] >= CAPTURABLE_T
                  and ret is not None and ret >= 0.5)
            verdict[(nm, con)] = ok
            print(f"  {nm:12s} {con:7s} {N:3d} {k:3d} | {bp:+8.2f} {t_:+6.2f} | "
                  + " ".join(fmt(v, 6) for v in zz) + f" {fmt(mn, 6)} | "
                  f"{fmt(cvt, 6)} | {fmt(oe[1] if oe else None, 7)} "
                  f"{(f'{ret:+6.0%}' if ret is not None else '    --')} | "
                  f"{'PASS' if ok else 'fail'}")

    print(f"\n{'=' * 92}")
    print(f"  CONDITION 4 -- head to head on the SAME ladder")
    print(f"{'=' * 92}")
    print(f"  {'con':7s} | {'confluence':>28s} | {'hist_L alone':>28s} | winner")
    for con in CONSTRUCTIONS:
        a_ = out["confluence"]["observed"][con]
        b_ = out[PRIMARY]["observed"][con]
        if not a_ or not b_:
            continue
        sa_ = f"N={a_[0]} k={a_[1]} {a_[2][0]:+.2f}bp t{a_[2][1]:+.2f}"
        sb_ = f"N={b_[0]} k={b_[1]} {b_[2][0]:+.2f}bp t{b_[2][1]:+.2f}"
        w = "confluence" if a_[2][1] > b_[2][1] else PRIMARY
        print(f"  {con:7s} | {sa_:>28s} | {sb_:>28s} | {w}")

    print(f"\n  gate 1g and cost, at each candidate's SPREAD peak:")
    for nm in out:
        e = out[nm]["extra"]
        if not e:
            continue
        for side in ("long", "short"):
            d_ = e[side]
            print(f"    {nm:12s} {side:5s} | held {d_['held']:5.1f} | turnover "
                  f"{d_['turnover']:5.1%} | run {d_['run']:5.1f} | dead "
                  f"{d_['dead']:5.1%} | half-spread mean {d_['cost_mean']:6.1f} "
                  f"median {d_['cost_median']:6.1f} bp")
        print(f"    {nm:12s} peak is {e['edge']} | era spread t: "
              + ", ".join(f"{k2} {v2[1]:+.2f}" if v2 else f"{k2} --"
                          for k2, v2 in e["era"].items()))

    json.dump({"purpose": "D293: the confluence book and hist_L alone through "
                          "one identical D290 stage-1 ladder, so condition 4 is "
                          "a symmetric comparison.",
               "preregistered": "49f8730", "corrected": "1e942ab",
               "primary": PRIMARY, "pair": list(PAIR), "f": FRAC,
               "n_levels": list(N_LEVELS), "horizons": list(HORIZONS),
               "draws": a.draws, "splits": a.splits,
               "verdict": {f"{k2[0]}|{k2[1]}": v2 for k2, v2 in verdict.items()},
               "results": out}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
