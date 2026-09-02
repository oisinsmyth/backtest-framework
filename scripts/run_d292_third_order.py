"""D292 -- third order on the `hist_L` cluster. 80 cells, two operators.

    uv run python scripts/run_d292_third_order.py --selftest
    uv run python scripts/run_d292_third_order.py [--draws 200] [--workers 6]

PRE-REGISTERED AT `e63fa8e`, committed before this file existed (R8). This
runner may not add a cell, move a threshold, or change a statistic.

STAGE 1 CONSUMES NOTHING SCARCE. This file gates nothing, closes nothing, and
does not read the holdout.

THE QUESTION IS "DOES A SECOND FILTER ADD OVER THE FIRST", so THE CONTROL IS THE
PARENTS, not the primary. D291 already answered whether a stack beats `hist_L`
alone: it does not, promotably.

ALL FIVE PARTNERS, NOT THE FOUR THAT SURVIVED D291. `retrace_leg` produced no
second-order survivor and still out-scores `macd_hist` (best z +1.55 vs +1.48),
which produced one. The survivor split is where p=0.05 happened to fall, and
selecting on it would be selecting on noise.

THE STATISTIC IS THE MINIMUM OVER THE TWO PARENTS. A stack that beats its weaker
parent while losing to its stronger one has added nothing, and picking the
parent it beats would be choosing the comparison after seeing it.

    t1 = paired t of (third order - parent_B1)
    t2 = paired t of (third order - parent_B2)
    t_min = min(t1, t2)

AND THE NULLS ARE ASYMMETRIC ON PURPOSE. Rotating B2 asks whether B2's CONTENT
adds to B1, so the comparison that matters under that null is against
parent_B1 -- the parent that does not contain the rotated filter. Hence t1 is
scored against the rotate-B2 null and t2 against the rotate-B1 null. Scoring
t_min against a single pooled null would compare a rotated filter's book to a
parent built from that same rotated filter.

THE TURNOVER AUDIT RUNS FIRST AND ITS OUTCOME IS PRE-COMMITTED. D291's veto arm
was scored and only then found unreadable, because its control churned 2.42x as
hard as the treatment while every statistic was measured on fresh entries. Here
a cell whose control sits outside 0.80-1.25x the treatment's entries per bar is
VOID and reported as void, whichever way its number points.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from itertools import combinations
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


R = _load("r291", "run_d291_confluence.py")          # LegPlan, ranked, rotate...
M = R.M
BC = R.BC
FN = R.FN

OUT = REPO / "data" / "d292_third_order.json"
PRIMARY = "hist_L"
PARTNERS = ("macd_hist", "macd_line", "retrace_leg", "rev_5", "rsi")
FRACTIONS = (0.90, 0.75, 0.50, 0.25)
OPERATORS = ("and", "meanrank")
SEED = 20260903
AUDIT_LO, AUDIT_HI = 0.80, 1.25      # pre-committed; outside this a cell is VOID
CAPTURABLE_T = 2.0


# --------------------------------------------------------------------------
# the two declared operators
# --------------------------------------------------------------------------
def _rank_mask(a, m, smallest):
    """Keep the m[j] best of column j. NaN sorts last and is never kept.

    Rank-based rather than threshold-based so the COUNT is what is controlled.
    A threshold on an average of percentiles does not retain a fixed fraction,
    because the average of two uniforms is not uniform -- and an operator whose
    book size moves with the data is comparing two things at once.
    """
    v = np.where(np.isnan(a), np.inf, a if smallest else -a)
    order = np.argsort(v, axis=0, kind="stable")
    pos = np.empty(order.shape, dtype=np.int32)
    np.put_along_axis(pos, order,
                      np.arange(a.shape[0], dtype=np.int32)[:, None], axis=0)
    nfin = np.isfinite(a).sum(axis=0)
    return pos < np.minimum(m, nfin)[None, :]


def op_and(p1lo, p1hi, p2lo, p2hi, frac, N):
    """Conjunctive: in the top g of BOTH, with g = sqrt(f).

    g = sqrt(f) so that under independence the combined retention is f -- the
    same book size the second-order study used. A naive top-f AND-top-f is the
    N^2/M collapse that left D288's probe holding 0.76 names per bar.
    """
    g = float(np.sqrt(frac))
    with np.errstate(invalid="ignore"):
        return ((p1lo <= g) & (p2lo <= g)), ((p1hi >= 1 - g) & (p2hi >= 1 - g))


def op_meanrank(p1lo, p1hi, p2lo, p2hi, frac, N):
    """Compensatory: average the two percentiles, keep the top f BY RANK.

    Averaging RANKS, not magnitudes, so this stays selection and stays inside
    stage 1's remit. The magnitude blend is stage 3 and is not tested here.
    """
    k = max(1, int(round(frac * N)))
    alo = (p1lo + p2lo) / 2.0
    ahi = (p1hi + p2hi) / 2.0
    kk = np.full(alo.shape[1], k)
    return _rank_mask(alo, kk, True), _rank_mask(ahi, kk, False)


OPS = {"and": op_and, "meanrank": op_meanrank}


def parent_masks(plo, phi, keep_lo, keep_hi):
    """One filter alone, holding EXACTLY the third order's per-bar count.

    Not "that filter at some fraction". The two books must be the same size on
    every bar or the paired difference reads a size gap; matching per bar rather
    than on average is the strictest form available and costs nothing.
    """
    return (_rank_mask(plo, keep_lo.sum(axis=0), True),
            _rank_mask(phi, keep_hi.sum(axis=0), False))


# --------------------------------------------------------------------------
# one cell
# --------------------------------------------------------------------------
def entries_per_bar(counts):
    a = counts[counts > 0]
    return float(a.mean()) if a.size else 0.0


def eval_cell(fk, plan, pcts, b1, b2, opname, frac, T):
    """The third-order book, its two count-matched parents, and t against each.

    Returns the two parent series as well, because the null scores against the
    SAME parents -- rebuilding them under rotation would compare a rotated
    filter's book to a parent built from that same rotated filter.
    """
    N = plan.N
    p1lo, p1hi = pcts[b1]
    p2lo, p2hi = pcts[b2]
    klo, khi = OPS[opname](p1lo, p1hi, p2lo, p2hi, frac, N)
    if not klo.any() or not khi.any():
        return None
    conf = R.spread_sums(fk, plan, klo, khi, T)

    out = {"kept_lo": float(klo.sum(axis=0).mean()),
           "kept_hi": float(khi.sum(axis=0).mean()), "N": N}
    pars, ts = {}, {}
    for tag, (plo, phi) in (("B1", (p1lo, p1hi)), ("B2", (p2lo, p2hi))):
        mlo, mhi = parent_masks(plo, phi, klo, khi)
        par = R.spread_sums(fk, plan, mlo, mhi, T)
        st = R.paired_t(conf[0], conf[1], par[0], par[1],
                        conf[2], conf[3], par[2], par[3])
        if st is None:
            return None
        pars[tag] = par
        ts[tag] = st
        # the pre-committed audit: entries per bar, control against treatment
        out[f"ratio_{tag}"] = (entries_per_bar(par[1]) / entries_per_bar(conf[1])
                               if entries_per_bar(conf[1]) else None)
    out.update(t1=ts["B1"][1], t2=ts["B2"][1],
               d1_bp=ts["B1"][0], d2_bp=ts["B2"][0],
               bars=min(ts["B1"][2], ts["B2"][2]),
               conf_bp=ts["B1"][3], par1_bp=ts["B1"][4], par2_bp=ts["B2"][4])
    out["t_min"] = min(out["t1"], out["t2"])
    r = [out[f"ratio_{t}"] for t in ("B1", "B2")]
    out["void"] = any(v is None or not (AUDIT_LO <= v <= AUDIT_HI) for v in r)
    return out, pars, conf


def null_t(fk, plan, pcts, rot_pct, b_real, rotated_is_first, opname, frac,
           parent, T):
    """The cell with ONE filter rotated, scored against the OTHER's parent.

    `parent` is the observed parent of the UNROTATED filter, held fixed.
    """
    N = plan.N
    prlo, prhi = rot_pct
    pklo, pkhi = pcts[b_real]
    if rotated_is_first:
        klo, khi = OPS[opname](prlo, prhi, pklo, pkhi, frac, N)
    else:
        klo, khi = OPS[opname](pklo, pkhi, prlo, prhi, frac, N)
    if not klo.any() or not khi.any():
        return None
    conf = R.spread_sums(fk, plan, klo, khi, T)
    st = R.paired_t(conf[0], conf[1], parent[0], parent[1],
                    conf[2], conf[3], parent[2], parent[3])
    return None if st is None else st[1]


def cell_list():
    """The 80 declared cells. Enumerated, not chosen."""
    return [(b1, b2, op, f)
            for b1, b2 in combinations(PARTNERS, 2)
            for op in OPERATORS
            for f in FRACTIONS]


# --------------------------------------------------------------------------
# assertions
# --------------------------------------------------------------------------
def assertions(scores, base, fwd, panel, live, plan, pcts, N, k):
    print("\n  RUNNER ASSERTIONS", flush=True)
    T = base.shape[1]
    b1, b2 = "rsi", "macd_hist"

    # 0. SELF-CHECK ON BOTH OPERATORS. With the two filters IDENTICAL, AND at
    #    g=sqrt(f) must reduce to a single gate at g, and MEAN-RANK to a single
    #    top-k by that filter. If an operator does not collapse correctly on the
    #    degenerate input, nothing it produces on two filters is readable.
    plo, phi = pcts[b1]
    for frac in FRACTIONS:
        g = float(np.sqrt(frac))
        klo, _ = op_and(plo, phi, plo, phi, frac, N)
        with np.errstate(invalid="ignore"):
            want = plo <= g
        assert np.array_equal(klo, want), (
            f"AND SELF-CHECK FAILED at f={frac}: filtering by {b1} twice is not "
            f"a single gate at g={g:.3f}")
        mlo, _ = op_meanrank(plo, phi, plo, phi, frac, N)
        single = _rank_mask(plo, np.full(plo.shape[1],
                                         max(1, int(round(frac * N)))), True)
        assert np.array_equal(mlo, single), (
            f"MEAN-RANK SELF-CHECK FAILED at f={frac}: averaging {b1} with "
            f"itself is not a single top-k by {b1}")
    print(f"    [0] self-check: both operators collapse to a single filter when "
          f"B1 == B2, at every f")

    # 1. LAG AUDIT, SECOND IMPLEMENTATION, COVERING ALL THREE SCORES. The book
    #    ranks on A at t-1 and filters on B1 AND B2 at t-1. A filter read at
    #    bar t's own close is look-ahead that an A-only audit never sees.
    sa, s1, s2 = scores[PRIMARY], scores[b1], scores[b2]
    g = float(np.sqrt(0.5))

    def hand_check(mask1, mask2, hand1, hand2):
        """`mask*` build the book; `hand*` rebuild it by hand. They are separate
        arguments ON PURPOSE: feeding the same array to both makes the audit
        agree with itself, which is how [1b] below caught this test being
        vacuous the first time it ran."""
        _, c1, q1 = R.ranked(mask1, base)
        _, c2, q2 = R.ranked(mask2, base)
        a1lo = R.pct_at(q1, c1, plan.lo, plan.cols)
        a2lo = R.pct_at(q2, c2, plan.lo, plan.cols)
        with np.errstate(invalid="ignore"):
            got_mask = (a1lo <= g) & (a2lo <= g)
        checked = 0
        for j in range(0, plan.cols.size, max(1, plan.cols.size // 9)):
            t = int(plan.cols[j])
            if t == 0:
                continue
            q = np.flatnonzero(base[:, t])
            va = sa[q, t - 1]
            qa = q[np.isfinite(va)]
            if qa.size < 60:
                continue
            pick = qa[np.argsort(sa[qa, t - 1], kind="stable")[:N]]
            keep = []
            for r in pick:
                ok = True
                for src in (hand1, hand2):
                    v = src[q, t - 1]
                    qq = q[np.isfinite(v)]
                    rb = qq[np.argsort(src[qq, t - 1], kind="stable")]
                    idx = np.flatnonzero(rb == r)
                    if idx.size == 0 or (idx[0] + 0.5) / rb.size > g:
                        ok = False
                        break
                if ok:
                    keep.append(int(r))
            assert set(keep) == {int(r) for r in plan.lo[got_mask[:, j], j]}, \
                f"LAG AUDIT FAILED at t={t}"
            checked += 1
        return checked

    checked = hand_check(s1, s2, s1, s2)
    assert checked >= 5, f"lag audit covered only {checked} bars"
    print(f"    [1] lag audit: A's picks and BOTH filters rebuilt from the "
          f"unlagged scores on {checked} bars, identical")

    raised = False
    try:
        hand_check(np.roll(s1, -1, axis=1), s2, s1, s2)
    except AssertionError:
        raised = True
    assert raised, "the lag audit PASSED a B1 read one bar early -- it proves nothing"
    print(f"    [1b] and it raises when B1 is read one bar early")

    # 2. SIGN AUDIT, IN MONEY, ON BOTH LEGS, THROUGH BOTH OPERATORS.
    f1 = fwd[1].astype(np.float64)
    oracle = np.full(f1.shape, np.nan)
    oracle[:, :-1] = -f1[:, 1:]
    o_ord, o_cnt, o_pos = R.ranked(oracle, base)
    op_plan = R.LegPlan(o_ord, o_cnt, 25, T)
    olo = R.pct_at(o_pos, o_cnt, op_plan.lo, op_plan.cols)
    ohi = R.pct_at(o_pos, o_cnt, op_plan.hi, op_plan.cols)
    for opname in OPERATORS:
        kl, kh = OPS[opname](olo, ohi, olo, ohi, 0.5, 25)
        s = R.spread_sums(fwd[1], op_plan, kl, kh, T)
        m = (s[1] > 0) & (s[3] > 0)
        lo_bp = float(np.mean(s[0][m] / s[1][m]) * 1e4)
        sh_bp = float(np.mean(-s[2][m] / s[3][m]) * 1e4)
        for nm, v in (("long", lo_bp), ("short", sh_bp)):
            assert v > 100.0, (
                f"SIGN AUDIT FAILED: oracle {nm} leg earns {v:+.1f} bp through "
                f"operator {opname}; it must be strongly positive")
        print(f"    [2] sign audit in money, operator {opname:9s}: oracle earns "
              f"long {lo_bp:+,.0f} bp, short {sh_bp:+,.0f} bp")

    # 3. RIGHT QUANTITY. The third-order book must differ from BOTH parents, and
    #    the parents must differ from each other -- otherwise the statistic is
    #    comparing a book to itself.
    got = eval_cell(fwd[k], plan, pcts, b1, b2, "and", 0.5, T)
    assert got is not None, "the probe cell produced no statistic"
    row, pars, conf = got
    assert not np.array_equal(conf[1], pars["B1"][1]), \
        "RIGHT QUANTITY FAILED: the third-order book equals its B1 parent"
    assert not np.array_equal(conf[1], pars["B2"][1]), \
        "RIGHT QUANTITY FAILED: the third-order book equals its B2 parent"
    assert not np.array_equal(pars["B1"][1], pars["B2"][1]), \
        "RIGHT QUANTITY FAILED: the two parents are the same book"
    print(f"    [3] right quantity: third order holds "
          f"{row['kept_lo']:.1f}/{N} long and differs from both parents, which "
          f"differ from each other")


# --------------------------------------------------------------------------
def fmt(v, w, d=2):
    return f"{v:+{w}.{d}f}" if v is not None else f"{'--':>{w}s}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    t0 = time.time()
    panel, _ = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(M.B.FIXTURE), "CACHE IS STALE -- rebuild"
    base = z["warm"] & live
    fwd = M.forward_returns(panel, live)
    _, peaks = R.pool_and_peaks()
    N, k = peaks[PRIMARY]
    scores = {c: z[c] for c in (PRIMARY,) + PARTNERS}

    order_a, cnt_a, _ = R.ranked(scores[PRIMARY], base)
    plan = R.LegPlan(order_a, cnt_a, N, T)
    Rk = {b: R.ranked(scores[b], base) for b in PARTNERS}
    pcts = {b: (R.pct_at(Rk[b][2], Rk[b][1], plan.lo, plan.cols),
                R.pct_at(Rk[b][2], Rk[b][1], plan.hi, plan.cols))
            for b in PARTNERS}
    cells = cell_list()
    print(f"D292  A = {PRIMARY}  N = {N}  k = {k}   |   "
          f"{len(PARTNERS)} partners -> {len(list(combinations(PARTNERS, 2)))} "
          f"pairs x {len(OPERATORS)} operators x {len(FRACTIONS)} f = "
          f"{len(cells)} cells   ({time.time() - t0:.0f}s)", flush=True)
    assert len(cells) == 80, f"expected the 80 declared cells, built {len(cells)}"

    assertions(scores, base, fwd, panel, live, plan, pcts, N, k)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- observed ----
    print(f"\n  OBSERVED: {len(cells)} cells", flush=True)
    obs, parents = {}, {}
    for i, (b1, b2, opn, f) in enumerate(cells):
        got = eval_cell(fwd[k], plan, pcts, b1, b2, opn, f, T)
        if got is None:
            continue
        row, pars, _ = got
        obs[i] = row
        parents[i] = pars
    nvoid = sum(1 for r in obs.values() if r["void"])
    print(f"  {len(obs)}/{len(cells)} produced a statistic", flush=True)

    # ---- THE PRE-COMMITTED AUDIT, BEFORE ANY NUMBER IS READ ----
    print(f"\n  TURNOVER AUDIT (pre-committed: control entries per bar must sit "
          f"in {AUDIT_LO:.2f}-{AUDIT_HI:.2f}x the treatment's)")
    rr = np.array([r[f"ratio_{t}"] for r in obs.values() for t in ("B1", "B2")
                   if r[f"ratio_{t}"] is not None])
    print(f"    ratio over {rr.size} (cell, parent) pairs: p50 {np.median(rr):.3f}x"
          f"  min {rr.min():.3f}x  max {rr.max():.3f}x")
    print(f"    cells VOID: {nvoid} of {len(obs)}"
          + ("   <- these are reported as void, not as results" if nvoid else
             "   <- Q5 holds"), flush=True)

    # ---- nulls: rotate ONE filter, hold the other, parents FIXED ----
    rp = R.rotate_plan(live)
    by_b = {}
    for i, (b1, b2, opn, f) in enumerate(cells):
        if i not in obs:
            continue
        by_b.setdefault(b1, []).append((i, True))     # b1 rotated -> scores t2
        by_b.setdefault(b2, []).append((i, False))    # b2 rotated -> scores t1

    def null_one(key, task):
        bi, draw = task
        bx = PARTNERS[bi]
        rng = np.random.default_rng(SEED + 131 * bi + 7919 * draw)
        off = rng.integers(1, T, size=live.shape[0])
        cnt_r, pos_r = R.ranked_pos(R.rotate(scores[bx], rp, off), base)
        rot = (R.pct_at(pos_r, cnt_r, plan.lo, plan.cols),
               R.pct_at(pos_r, cnt_r, plan.hi, plan.cols))
        out = {}
        for i, rotated_is_first in by_b.get(bx, []):
            b1, b2, opn, f = cells[i]
            other = b2 if rotated_is_first else b1
            # rotating B1 leaves B2's parent as the honest comparison, and vice versa
            par = parents[i]["B2" if rotated_is_first else "B1"]
            out[(i, rotated_is_first)] = null_t(
                fwd[k], plan, pcts, rot, other, rotated_is_first, opn, f, par, T)
        return out

    tasks = [((bi, d), (bi, d)) for bi in range(len(PARTNERS))
             for d in range(a.draws) if PARTNERS[bi] in by_b]
    print(f"\n  NULLS: {len(tasks)} (filter, draw) tasks -- each rotation feeds "
          f"every cell containing it", flush=True)
    nres = FN.parallel_map(null_one, tasks, workers=a.workers)

    draws = {d: {} for d in range(a.draws)}
    for (bi, d), out in nres.items():
        draws[d].update(out)

    # per-cell null distributions: t1 against rotate-B2, t2 against rotate-B1
    n1 = {i: [] for i in obs}          # rotated_is_first False -> scores t1
    n2 = {i: [] for i in obs}          # rotated_is_first True  -> scores t2
    for d in range(a.draws):
        for (i, rot_first), v in draws[d].items():
            if v is None:
                continue
            (n2 if rot_first else n1)[i].append(v)

    # ---- the two bars ----
    rows = []
    zmat = []
    for i, r in obs.items():
        b1, b2, opn, f = cells[i]
        a1, a2 = np.array(n1[i]), np.array(n2[i])
        if a1.size < 6 or a2.size < 6 or a1.std(ddof=1) == 0 or a2.std(ddof=1) == 0:
            continue
        p1 = float((a1 >= r["t1"]).sum() + 1) / (a1.size + 1)
        p2 = float((a2 >= r["t2"]).sum() + 1) / (a2.size + 1)
        z1 = float((r["t1"] - a1.mean()) / a1.std(ddof=1))
        z2 = float((r["t2"] - a2.mean()) / a2.std(ddof=1))
        rows.append(dict(B1=b1, B2=b2, op=opn, f=f, N=r["N"], k=k, **{
            q: r[q] for q in ("t1", "t2", "t_min", "d1_bp", "d2_bp", "bars",
                              "conf_bp", "par1_bp", "par2_bp", "kept_lo",
                              "kept_hi", "ratio_B1", "ratio_B2", "void")},
            null1_p95=float(np.percentile(a1, 95)),
            null2_p95=float(np.percentile(a2, 95)),
            p1=p1, p2=p2, p_max=max(p1, p2), z1=z1, z2=z2, z_min=min(z1, z2),
            screen=bool(r["t1"] > np.percentile(a1, 95)
                        and r["t2"] > np.percentile(a2, 95) and not r["void"])))
        zmat.append((i, a1, a2))

    # PROMOTION: the joint max-Z floor over all cells, from the same draws
    live_rows = [r for r in rows if not r["void"]]
    per_draw = []
    for d in range(a.draws):
        vals = []
        for (i, a1, a2) in zmat:
            v1 = draws[d].get((i, False))
            v2 = draws[d].get((i, True))
            if v1 is None or v2 is None:
                continue
            zz1 = (v1 - a1.mean()) / a1.std(ddof=1)
            zz2 = (v2 - a2.mean()) / a2.std(ddof=1)
            vals.append(min(zz1, zz2))
        if vals:
            per_draw.append(max(vals))
    floor_z = float(np.percentile(per_draw, 95)) if per_draw else None
    for r in rows:
        r["promote"] = bool(floor_z is not None and r["z_min"] > floor_z
                            and not r["void"])

    rows.sort(key=lambda r: -r["z_min"])
    nscreen = sum(1 for r in rows if r["screen"])
    npro = sum(1 for r in rows if r["promote"])

    print(f"\n  joint max-Z over {len(zmat)} cells, {len(per_draw)} draws: "
          f"p50 {np.percentile(per_draw, 50):+.2f}  "
          f"p95 = PROMOTION FLOOR {floor_z:+.2f}  max {max(per_draw):+.2f}")

    # BH-FDR on the screen p-values, reported beside the count
    pv = np.sort(np.array([r["p_max"] for r in rows if not r["void"]]))
    m = pv.size
    bh = {}
    for q in (0.10, 0.20):
        thr = np.arange(1, m + 1) / m * q
        below = np.flatnonzero(pv <= thr)
        bh[q] = int(below.max() + 1) if below.size else 0

    print(f"\n  TOP 15 BY z_min   (screen = beats BOTH own nulls at p95; "
          f"promotion floor {floor_z:+.2f})")
    print(f"  {'B1':13s} {'B2':13s} {'op':9s} {'f':>5s} | {'t1':>6s} {'t2':>6s} "
          f"{'t_min':>6s} | {'z1':>6s} {'z2':>6s} {'z_min':>6s} | "
          f"{'held':>5s} | {'verdict':>9s}")
    for r in rows[:15]:
        v = ("VOID" if r["void"] else "PROMOTE" if r["promote"]
             else "screen" if r["screen"] else "no")
        print(f"  {r['B1']:13s} {r['B2']:13s} {r['op']:9s} {r['f']:5.2f} | "
              f"{fmt(r['t1'], 6)} {fmt(r['t2'], 6)} {fmt(r['t_min'], 6)} | "
              f"{fmt(r['z1'], 6)} {fmt(r['z2'], 6)} {fmt(r['z_min'], 6)} | "
              f"{r['kept_lo']:5.1f} | {v:>9s}")

    print(f"\n  SCREEN survivors: {nscreen} of {len(live_rows)} live cells   "
          f"(expected by luck at p<0.05 on both nulls: "
          f"{0.0025 * len(live_rows):.2f})")
    print(f"  BH-FDR kept: q=0.10 -> {bh[0.10]}   q=0.20 -> {bh[0.20]}")
    print(f"  PROMOTION: {npro} of {len(live_rows)}")
    print(f"  VOID by the pre-committed turnover audit: {nvoid}")

    json.dump({"purpose": "D292 third order on the hist_L cluster: does a "
                          "SECOND filter add over the first? Control is the "
                          "parents, statistic is the minimum over them, nulls "
                          "rotate the added filter.",
               "preregistered": "e63fa8e", "primary": PRIMARY,
               "partners": list(PARTNERS), "N": N, "k": k,
               "operators": list(OPERATORS), "fractions": list(FRACTIONS),
               "draws": a.draws, "n_cells": len(cells),
               "audit_band": [AUDIT_LO, AUDIT_HI], "n_void": nvoid,
               "promotion_floor_z": floor_z,
               "joint_null": {"p50": float(np.percentile(per_draw, 50)),
                              "p95": floor_z, "max": float(max(per_draw))},
               "n_screen": nscreen, "n_promote": npro, "bh": bh,
               "rows": rows}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
