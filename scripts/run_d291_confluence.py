"""D291 -- confluence at stage 1: gate and veto, one operator, 272 cells.

    uv run python scripts/run_d291_confluence.py --selftest
    uv run python scripts/run_d291_confluence.py [--draws 200] [--workers 6]

PRE-REGISTERED AT `a1fbc14`, CLARIFIED AT `4603b68`, both committed before this
file existed (R8). This runner may not add a cell, move a threshold, or change a
statistic.

STAGE 1 CONSUMES NOTHING SCARCE. This file gates nothing, closes nothing, and
does not read the holdout.

THE OPERATOR IS ONE THING, NOT TWO. Gate and veto are the same construction --
take A's leg, drop the names in the worst fraction of B -- and differ only in
which (A, B) pairs the rule admits and in what the control is:

    long  leg:  N lowest  by A, keep those with  pct_B <= f
    short leg:  N highest by A, keep those with  pct_B >= 1 - f

N and k are INHERITED from A's own D290 spread peak. Only f moves.

THE STATISTIC IS THE PAIRED DIFFERENCE, NOT THE CONFLUENCE'S OWN t. D288's
post-closure probe reported the confluence's number and eyeballed it against a
control; a book holding 12 names is more volatile than one holding 25 for
reasons that have nothing to do with B, so the levels are not comparable and the
difference is.

    per bar:   D[t] = confluence_spread[t] - control_spread[t]
    statistic: t on D

WHY PERCENTILES AND NOT A SCORE CUT. `pct_B` is B's within-bar rank percentile,
so `f` selects a COUNT. Rotating B then changes WHICH names survive but not HOW
MANY -- the null is count-matched by construction rather than by correction.
That is the whole reason the threshold is a percentile.

SPEED. The cost is `rank_columns` (0.28 s on 1573x4187), and the null needs one
per (B, draw) rather than one per (cell, draw): 13 x 200 = 2,600 sorts instead of
272 x 200 = 54,400, a 21x saving from noticing that cells sharing a B share its
rotation. Cells are then evaluated on (N, ncols) gathers -- 50x4187, not
1573x4187 -- because only A's selected names can ever survive a filter. Threaded,
not processed: argsort and bincount release the GIL and one 53 MB pos array per
thread beats copying the cache.
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


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
FN = M.FN

CELLS = json.loads((REPO / "data" / "d291_cells.json").read_text())
RANK = json.loads((REPO / "data" / "d290_unified_rank.json").read_text())
OUT = REPO / "data" / "d291_confluence.json"

FRACTIONS = (0.9, 0.75, 0.5, 0.25)
MIN_BARS = M.MIN_BARS
N_RANDOM = 50                   # random removals behind every veto control
SEED = 20260902
CON = "spread"                  # the pool is tier-1 SPREAD; that is the book


# --------------------------------------------------------------------------
# the pool, and each A's inherited (N, k)
# --------------------------------------------------------------------------
def pool_and_peaks():
    """The 13 capturable tier-1 spread candidates and the (N, k) each inherits.

    Read from D290's unified ranking rather than recomputed, so this study
    cannot quietly land on a different cell than the one that qualified.
    """
    rows = RANK["rows"][CON]
    peaks = {r["c"]: (r["N"], r["k"]) for r in rows if r["tier"] == 1}
    pool = sorted(peaks)
    return pool, peaks


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------
def legs_rows(order_a, cnt_a, N):
    """A's two legs as (N, ncols) row indices plus the columns they live on.

    Only these cells can survive a filter, so everything downstream works on
    50x4187 rather than 1573x4187.
    """
    cols = np.flatnonzero(cnt_a >= 2 * N)
    lo = order_a[:N, cols]
    hi_idx = cnt_a[cols][None, :] - np.arange(N, 0, -1)[:, None]
    hi = np.take_along_axis(order_a[:, cols], hi_idx, axis=0)
    return lo, hi, cols


def pct_at(pos_b, cnt_b, rows, cols):
    """B's rank percentile at A's selected cells. NaN where B is not finite.

    `pos_b` is stored TRANSPOSED as (T, n) -- see `ranked_pos` -- so the bar
    index comes first here.
    """
    p = pos_b[np.broadcast_to(cols[None, :], rows.shape), rows].astype(np.float64)
    c = cnt_b[cols][None, :].astype(np.float64)
    out = (p + 0.5) / np.maximum(c, 1.0)
    out[p >= c] = np.nan                       # B had no finite value there
    return out


def paired_t(a_s, a_n, b_s, b_n, hi_a_s, hi_a_n, hi_b_s, hi_b_n):
    """t on the per-bar difference of two SPREAD books, on their common bars."""
    m = (a_n > 0) & (b_n > 0) & (hi_a_n > 0) & (hi_b_n > 0)
    if int(m.sum()) < MIN_BARS:
        return None
    conf = a_s[m] / a_n[m] - hi_a_s[m] / hi_a_n[m]
    ctrl = b_s[m] / b_n[m] - hi_b_s[m] / hi_b_n[m]
    d = conf - ctrl
    sd = d.std(ddof=1)
    if sd == 0:
        return None
    return (float(d.mean() * 1e4),
            float(d.mean() / (sd / np.sqrt(d.size))),
            int(d.size),
            float(conf.mean() * 1e4),
            float(ctrl.mean() * 1e4))


class LegPlan:
    """A's two legs, and the ONE thing about them that never changes.

    B's rotation and the fraction `f` both move which names are KEPT. Neither
    moves which names A SELECTED, nor the order `np.nonzero` would return them
    in. So the event keys are sorted ONCE per (A, N) here and every book below
    is a boolean gather into that sorted array -- 200 draws x 4 fractions x 2
    legs of sorting, hoisted into one. Hoisting an invariant out of a loop
    changes no float; it just stops recomputing one.
    """

    __slots__ = ("lo", "hi", "cols", "T", "N", "key", "perm")

    def __init__(self, order_a, cnt_a, N, T):
        self.lo, self.hi, self.cols = legs_rows(order_a, cnt_a, N)
        self.T, self.N = T, N
        self.key, self.perm = {}, {}
        for side, rows in (("lo", self.lo), ("hi", self.hi)):
            if rows.size == 0:
                self.key[side] = np.empty(0, np.int64)
                self.perm[side] = np.empty(0, np.intp)
                continue
            bc = np.broadcast_to(self.cols[None, :], rows.shape)
            k = rows.ravel().astype(np.int64) * T + bc.ravel()
            p = np.argsort(k, kind="stable")
            self.key[side], self.perm[side] = k[p], p


def fresh_events(plan, side, keep):
    """Kept membership -> FRESH ENTRIES, matching D290's convention exactly.

    D290 measured every cell on fresh entries, so each entry earns the k-bar
    forward return once. Scoring membership instead would count a name held for
    twenty bars twenty times and is a different statistic wearing the same name.

    SPARSE, AND THE ORDER IS THE POINT. A book holds at most N names per bar, so
    its events are ~40k cells where the dense version allocates and scans three
    1573x4187 booleans -- 6.6M cells, 150x the work, called twice per book and
    fifty times per veto control. `row * T + col` ascending is EXACTLY the C
    order `np.nonzero` returns, so the float sums `bar_sums` accumulates
    downstream happen in the same order and the answer is BIT-IDENTICAL rather
    than merely close.

    HELD-AT-t-1 IS THE PRECEDING ELEMENT, NOT A SEARCH. The keys are sorted and
    unique, so the only place `key - 1` could sit is immediately before it: one
    shifted comparison replaces a binary search over the whole array, turning an
    O(K log K) step into an O(K) one. Bar 0 is guarded separately -- its
    `key - 1` is the PREVIOUS NAME's last bar, a real event that would silently
    mark a genuine entry stale.
    """
    key = plan.key[side][keep.reshape(-1)[plan.perm[side]]]
    if key.size == 0:
        return np.empty(0, np.intp), np.empty(0, np.intp)
    held = np.empty(key.size, bool)
    held[0] = False
    np.equal(key[1:] - 1, key[:-1], out=held[1:])
    fresh = ~held | ((key % plan.T) == 0)
    k = key[fresh]
    return (k // plan.T).astype(np.intp), (k % plan.T).astype(np.intp)


def fresh_events_dense(rows, cols, keep, shape):
    """The obvious (n, T) implementation. KEPT, and used only by the guard.

    `fresh_events` is a sparse rewrite of this, and a rewrite that is merely
    plausible is how D286 shipped a move 10x too small. This is the thing it
    has to equal, BIT-IDENTICALLY.
    """
    n, T = shape
    inl = np.zeros((n, T), dtype=bool)
    bc = np.broadcast_to(cols[None, :], rows.shape)
    inl[rows[keep], bc[keep]] = True
    ev = inl.copy()
    ev[:, 1:] &= ~inl[:, :-1]
    return np.nonzero(ev)


def spread_sums(f, plan, keep_lo, keep_hi, T):
    """Per-bar (sum, count) for both legs of one book."""
    lr, lc = fresh_events(plan, "lo", keep_lo)
    hr, hc = fresh_events(plan, "hi", keep_hi)
    return M.bar_sums(f, lr, lc, T) + M.bar_sums(f, hr, hc, T)


def keep_masks(pos_b, cnt_b, plan, frac):
    """The operator. NaN compares False, so a name B cannot rank is DROPPED --
    the conservative side, and stated because the alternative is silent."""
    plo = pct_at(pos_b, cnt_b, plan.lo, plan.cols)
    phi = pct_at(pos_b, cnt_b, plan.hi, plan.cols)
    with np.errstate(invalid="ignore"):
        return plo <= frac, phi >= 1.0 - frac


# --------------------------------------------------------------------------
# the two controls
# --------------------------------------------------------------------------
def control_matched_n(fk, plan_of, ca, k, keep_lo, keep_hi, T, cache):
    """GATE control: A alone at N' = the mean surviving count.

    Not A at N. A book of 12 names and a book of 25 differ in volatility for
    reasons that have nothing to do with B, and the paired t would read that
    difference as B's contribution.

    MEMOISED ON (A, N', k): 184 gate cells over 13 candidates land on the same
    control again and again, and it does not depend on B at all.
    """
    m = np.concatenate([keep_lo.sum(axis=0), keep_hi.sum(axis=0)])
    npr = max(1, int(round(float(m.mean()))))
    hit = cache.get((ca, npr, k))
    if hit is None:
        p2 = plan_of(ca, npr)
        ones_lo = np.ones(p2.lo.shape, dtype=bool)
        ones_hi = np.ones(p2.hi.shape, dtype=bool)
        hit = spread_sums(fk, p2, ones_lo, ones_hi, T)
        cache[(ca, npr, k)] = hit
    return hit, npr


def control_random_removal(fk, plan, keep_lo, keep_hi, T, rng, reps=N_RANDOM):
    """VETO control: remove the SAME COUNT PER BAR at random, `reps` times.

    One random draw is noise, so this returns the per-bar mean (the paired
    control series) AND the reps' own totals (the permutation distribution).
    ONE set of draws, both readings -- which is what the pre-registration says
    and what two separate generators would have quietly broken.
    """
    N, ncols = plan.lo.shape
    mlo = keep_lo.sum(axis=0)
    mhi = keep_hi.sum(axis=0)
    acc = None
    totals = []
    for _ in range(reps):
        klo = _random_keep(N, ncols, mlo, rng)
        khi = _random_keep(N, ncols, mhi, rng)
        s = spread_sums(fk, plan, klo, khi, T)
        acc = [np.zeros_like(x) for x in s] if acc is None else acc
        for a, b in zip(acc, s):
            a += b
        good = (s[1] > 0) & (s[3] > 0)
        if good.any():
            totals.append(float(np.mean(s[0][good] / s[1][good]
                                        - s[2][good] / s[3][good])))
    return [a / reps for a in acc], np.array(totals)


def _random_keep(N, ncols, m, rng):
    """Keep exactly m[j] of the N rows in column j, chosen uniformly."""
    r = np.argsort(rng.random((N, ncols)), axis=0)
    pos = np.empty_like(r)
    np.put_along_axis(pos, r, np.arange(N, dtype=r.dtype)[:, None], axis=0)
    return pos < m[None, :]


# --------------------------------------------------------------------------
# one (kind, A, B) group -- all four fractions together
# --------------------------------------------------------------------------
def eval_group(fk, pos_b, cnt_b, plan, ca, k, kind, rng, plan_of, cache):
    """All four fractions of one (kind, A, B) group, in one pass.

    GROUPED BECAUSE THE FRACTION IS THE ONLY THING THAT MOVES. A's legs and B's
    percentiles at those legs are identical across f, so deriving them once per
    group instead of once per cell hoists four identical computations into one.

    Returns {f: (row, control_series)}; the control is RETURNED rather than
    recomputed by the caller, which for a veto cell is fifty random books that
    the first draft built twice.
    """
    if plan.cols.size == 0:
        return {}
    T = plan.T
    plo = pct_at(pos_b, cnt_b, plan.lo, plan.cols)
    phi = pct_at(pos_b, cnt_b, plan.hi, plan.cols)
    out = {}
    for frac in FRACTIONS:
        with np.errstate(invalid="ignore"):
            klo, khi = plo <= frac, phi >= 1.0 - frac
        conf = spread_sums(fk, plan, klo, khi, T)
        if kind == "gate":
            ctrl, npr = control_matched_n(fk, plan_of, ca, k, klo, khi, T, cache)
            perm_p = None
        else:
            ctrl, totals = control_random_removal(fk, plan, klo, khi, T, rng)
            npr = None
            good = (conf[1] > 0) & (conf[3] > 0)
            obs = (float(np.mean(conf[0][good] / conf[1][good]
                                 - conf[2][good] / conf[3][good]))
                   if good.any() else None)
            perm_p = (None if obs is None or totals.size == 0
                      else float((totals >= obs).sum() + 1) / (totals.size + 1))
        st = paired_t(conf[0], conf[1], ctrl[0], ctrl[1],
                      conf[2], conf[3], ctrl[2], ctrl[3])
        if st is None:
            continue
        dbp, t, bars, cbp, kbp = st
        out[frac] = (dict(d_bp=dbp, t=t, bars=bars, conf_bp=cbp, ctrl_bp=kbp,
                          kept_lo=float(klo.sum(axis=0).mean()),
                          kept_hi=float(khi.sum(axis=0).mean()),
                          ctrl_n=npr, perm_p=perm_p, N=plan.N), ctrl)
    return out


def null_group(fk, pos_b, cnt_b, plan, ctrl_of):
    """The group's paired t under a rotated B, against the SAME controls.

    The controls are held fixed because they depend on A and the surviving count
    alone, and `f` being a percentile keeps that count essentially unmoved -- so
    this isolates B's ALIGNMENT and nothing else.
    """
    if plan.cols.size == 0:
        return {}
    T = plan.T
    plo = pct_at(pos_b, cnt_b, plan.lo, plan.cols)
    phi = pct_at(pos_b, cnt_b, plan.hi, plan.cols)
    out = {}
    for frac, ctrl in ctrl_of.items():
        with np.errstate(invalid="ignore"):
            klo, khi = plo <= frac, phi >= 1.0 - frac
        conf = spread_sums(fk, plan, klo, khi, T)
        st = paired_t(conf[0], conf[1], ctrl[0], ctrl[1],
                      conf[2], conf[3], ctrl[2], ctrl[3])
        out[frac] = None if st is None else st[1]
    return out


# --------------------------------------------------------------------------
# the runner assertions CLAUDE.md requires, plus the pre-registered self-gate
# --------------------------------------------------------------------------
def assertions(scores, base, fwd, panel, live, peaks):
    print("\n  RUNNER ASSERTIONS", flush=True)
    shape = base.shape
    T = shape[1]

    # 0. SELF-GATE. Pre-registered as the validity check: gating A with ITSELF
    #    must reproduce A exactly. A's own N lowest sit at percentile ~N/cnt,
    #    far inside every f in the sweep, so any deviation is a harness bug and
    #    nothing below would be readable.
    a = "rsi"
    N, _ = peaks[a]
    order_a, cnt_a, pos_a = ranked(scores[a], base)
    plan = LegPlan(order_a, cnt_a, N, T)
    for frac in FRACTIONS:
        klo, khi = keep_masks(pos_a, cnt_a, plan, frac)
        assert klo.all() and khi.all(), (
            f"SELF-GATE FAILED at f={frac}: gating {a} with itself dropped "
            f"{int((~klo).sum() + (~khi).sum())} of its own picks")
    print(f"    [0] self-gate: {a} filtered by {a} keeps all "
          f"{plan.lo.size + plan.hi.size:,} picks at every f")

    # 1. LAG AUDIT, SECOND IMPLEMENTATION, and it must cover BOTH scores. The
    #    book ranks bar t on A at t-1 AND filters on B at t-1. A filter read at
    #    bar t's own close is look-ahead that an A-only lag audit never sees.
    b = "macd_hist"
    _, cnt_b, pos_b = ranked(scores[b], base)
    sa, sb = scores[a], scores[b]
    cols = plan.cols

    def hand_check(pos_x, cnt_x, sb_read):
        """Rebuild the kept long leg from the RAW arrays, never calling
        `legs_rows`, `pct_at` or `keep_masks`."""
        klo_x, _ = keep_masks(pos_x, cnt_x, plan, 0.5)
        checked = 0
        for j in range(0, cols.size, max(1, cols.size // 9)):
            t = int(cols[j])
            if t == 0:
                continue
            q = np.flatnonzero(base[:, t])
            va = sa[q, t - 1]
            qa = q[np.isfinite(va)]
            if qa.size < 60:
                continue
            pick = qa[np.argsort(sa[qa, t - 1], kind="stable")[:N]]
            vb = sb_read[q, t - 1]
            qb = q[np.isfinite(vb)]
            rb = qb[np.argsort(sb_read[qb, t - 1], kind="stable")]
            rank = {int(r): i for i, r in enumerate(rb)}
            want = {int(r) for r in pick
                    if r in rank and (rank[int(r)] + 0.5) / len(rb) <= 0.5}
            got = {int(r) for r in plan.lo[klo_x[:, j], j]}
            assert want == got, f"LAG AUDIT FAILED at t={t}: {want ^ got}"
            checked += 1
        return checked

    checked = hand_check(pos_b, cnt_b, sb)
    assert checked >= 5, f"lag audit covered only {checked} bars"
    print(f"    [1] lag audit: A's picks AND B's filter rebuilt from the "
          f"unlagged scores on {checked} bars, identical")

    # 1b. and it must FAIL when B is read one bar early, or it proves nothing.
    raised = False
    try:
        _, cnt_x, pos_x = ranked(np.roll(sb, -1, axis=1), base)
        hand_check(pos_x, cnt_x, sb)
    except AssertionError:
        raised = True
    assert raised, "the lag audit PASSED a B read one bar early -- it proves nothing"
    print(f"    [1b] and it raises when B is read one bar early")

    # 2. SIGN AUDIT, IN MONEY, ON BOTH LEGS. An oracle score ranks, after the
    #    book's own lag, on MINUS the return the position is about to earn. The
    #    long leg and the NEGATED short leg must each be strongly positive --
    #    the short sign is the one D280 got wrong for five parts on prose.
    f1 = fwd[1].astype(np.float64)
    oracle = np.full(f1.shape, np.nan)
    oracle[:, :-1] = -f1[:, 1:]
    o_ord, o_cnt, o_pos = ranked(oracle, base)
    op = LegPlan(o_ord, o_cnt, 25, T)
    klo, khi = keep_masks(o_pos, o_cnt, op, 0.5)
    s = spread_sums(fwd[1], op, klo, khi, T)
    m = (s[1] > 0) & (s[3] > 0)
    lo_bp = float(np.mean(s[0][m] / s[1][m]) * 1e4)
    sh_bp = float(np.mean(-s[2][m] / s[3][m]) * 1e4)
    for nm, v in (("long", lo_bp), ("short", sh_bp)):
        assert v > 100.0, (
            f"SIGN AUDIT FAILED: oracle {nm} leg earns {v:+.1f} bp at k=1 "
            f"through the confluence operator; it must be strongly positive")
    print(f"    [2] sign audit in money: oracle through the operator earns "
          f"long {lo_bp:+,.0f} bp, short {sh_bp:+,.0f} bp")

    # 3. RIGHT QUANTITY. The filtered book must differ from the ones it is NOT:
    #    A alone at N, and A alone at the control's N'.
    ones_lo = np.ones(plan.lo.shape, dtype=bool)
    ones_hi = np.ones(plan.hi.shape, dtype=bool)
    a_only = spread_sums(fwd[1], plan, ones_lo, ones_hi, T)
    klo, khi = keep_masks(pos_b, cnt_b, plan, 0.25)
    filt = spread_sums(fwd[1], plan, klo, khi, T)
    assert not np.array_equal(a_only[1], filt[1]), (
        "RIGHT QUANTITY FAILED: the f=0.25 filter removed nothing -- the book "
        "scored is A alone, not a confluence")
    cache = {}
    ctrl, npr = control_matched_n(fwd[1], lambda c, n: LegPlan(order_a, cnt_a, n, T),
                                  a, 1, klo, khi, T, cache)
    assert npr < N and not np.array_equal(ctrl[1], a_only[1]), (
        f"RIGHT QUANTITY FAILED: the matched-N control is A at N={N}, not at "
        f"the surviving count N'={npr}")
    print(f"    [3] right quantity: f=0.25 holds "
          f"{float(klo.sum(axis=0).mean()):.1f}/{N} names, control is A at "
          f"N'={npr}, and all three books differ")

    # 4. THE SPARSE REWRITE EQUALS THE LOOP IT REPLACED, BIT-IDENTICALLY.
    #    `fresh_events` is a rewrite of a dense (n, T) scan, and a rewrite that
    #    is merely plausible is how D286 shipped a move 10x too small. Probed on
    #    the ADJACENCY-HEAVY case (everything held every bar), which is where a
    #    freshness rewrite disagrees.
    ncase = 0
    rngg = np.random.default_rng(11)
    for cand in ("rsi", "price_log", "choch_dist"):
        o2, c2, p2 = ranked(scores[cand], base)
        for NN in (3, 25, 50):
            pl = LegPlan(o2, c2, NN, T)
            if pl.cols.size == 0:
                continue
            cases = [np.ones(pl.lo.shape, bool),          # max adjacency
                     np.zeros(pl.lo.shape, bool),         # empty
                     keep_masks(p2, c2, pl, 0.9)[0],
                     keep_masks(p2, c2, pl, 0.25)[0],
                     rngg.random(pl.lo.shape) < 0.5]
            for keep in cases:
                g = fresh_events(pl, "lo", keep)
                d = fresh_events_dense(pl.lo, pl.cols, keep, shape)
                assert np.array_equal(g[0], d[0]) and np.array_equal(g[1], d[1]), \
                    f"SPARSE REWRITE DIFFERS from the dense loop: {cand} N={NN}"
                s1 = M.bar_sums(fwd[1], g[0], g[1], T)
                s2 = M.bar_sums(fwd[1], d[0], d[1], T)
                assert (s1[0] == s2[0]).all() and (s1[1] == s2[1]).all(), \
                    f"BAR SUMS DIFFER after the sparse rewrite: {cand} N={NN}"
                ncase += 1
    print(f"    [4] sparse fresh_events == the dense loop, and the float sums "
          f"downstream are bit-identical, on {ncase} cases")

    # 6. THE NULL'S FAST RANKING EQUALS `rank_columns`. `ranked_pos` sorts a
    #    transposed copy so the sort axis is contiguous. Same lag, same mask,
    #    same stable tie-break -- but that is an argument, and this is a check.
    for cand in ("rsi", "price_log", "on_persist"):
        o3, c3, p3 = ranked(scores[cand], base)
        c4, p4 = ranked_pos(scores[cand], base)
        assert np.array_equal(c3, c4) and np.array_equal(p3, p4), (
            f"TRANSPOSED RANKING DIFFERS from rank_columns on {cand}")
    print(f"    [6] transposed ranked_pos == rank_columns, exactly, on 3 "
          f"candidates including the tie-heavy ones")


def ranked(score, base):
    """A's `order` (n, T), the per-bar count, and the TRANSPOSED position.

    Derived from `rank_columns`' own output rather than re-sorted, so A's legs
    and B's percentiles cannot drift apart. `order` is cast to int32 -- the
    panel has 1,573 names, so int64 indices are 26 MB of nothing per candidate.
    """
    order, cnt = M.rank_columns(score, base)
    pos = np.empty(order.shape, dtype=np.int32)
    np.put_along_axis(pos, order,
                      np.arange(order.shape[0], dtype=np.int32)[:, None], axis=0)
    return order.astype(np.int32), cnt, np.ascontiguousarray(pos.T)


def ranked_pos(score, base):
    """Position and count only, TRANSPOSED to (T, n). The null never RANKS by
    B, it only FILTERS by B, so the 53 MB `order` array is never built.

    SORTED ALONG THE CONTIGUOUS AXIS. `rank_columns` sorts axis 0 of a C-order
    (n, T) array, so every one of the 4,187 columns it sorts is strided 33 KB
    apart and the sort thrashes cache. One transpose costs 21 ms and makes the
    sort axis contiguous: 444 ms -> 328 ms per draw, 2,600 draws deep. The lag,
    the mask and the stable tie-break are all unchanged, and assertion [6]
    holds it to `rank_columns`' exact output.
    """
    v = np.ascontiguousarray(np.where(base, M.C.lag1(score), np.nan).T)
    order = np.argsort(v, axis=1, kind="stable")
    pos = np.empty(order.shape, dtype=np.int32)
    np.put_along_axis(pos, order,
                      np.arange(order.shape[1], dtype=np.int32)[None, :], axis=1)
    return np.isfinite(v).sum(axis=1), pos


def rotate_plan(live):
    """Everything a per-symbol rotation needs that does NOT depend on the draw.

    The obvious rotation is a Python loop over 1,573 symbols calling `np.roll`.
    That is GIL-BOUND PURE PYTHON in the middle of a six-thread fan-out, which
    CLAUDE.md says is the one shape threads cannot help. Flattened like this the
    whole rotation is four vectorised gathers and no loop at all.
    """
    ats = [np.flatnonzero(live[i]) for i in range(live.shape[0])]
    at_flat = np.concatenate(ats) if ats else np.empty(0, np.int64)
    lens = np.array([a.size for a in ats])
    start = np.concatenate([[0], np.cumsum(lens)[:-1]])
    rows = np.repeat(np.arange(live.shape[0]), lens)
    jpos = np.arange(at_flat.size) - start[rows]
    return dict(at=at_flat.astype(np.int64), rows=rows,
                jpos=jpos, L=lens[rows], start=start[rows], ats=ats)


def rotate(score, rp, off):
    """Roll each symbol's values WITHIN its own live bars, vectorised.

    Coverage unchanged, autocorrelation unchanged, so TURNOVER is matched. This
    is a permutation of existing values -- no float arithmetic happens, so
    "exact" here is not a tolerance claim.
    """
    out = np.full(score.shape, np.nan)
    src = rp["at"][rp["start"] + (rp["jpos"] - off[rp["rows"]]) % rp["L"]]
    out[rp["rows"], rp["at"]] = score[rp["rows"], src]
    return out


def rotate_loop(score, ats, off):
    """The obvious per-symbol implementation. KEPT, and used only by the guard."""
    out = np.full(score.shape, np.nan)
    for i, at in enumerate(ats):
        if at.size:
            out[i, at] = np.roll(score[i, at], int(off[i]))
    return out


def group_list(pool):
    """The 68 declared (kind, A, B) groups. GATE pairs are ORDERED, so each rho
    pair is two.

    Enumerated from `data/d291_cells.json`, which was committed WITH the
    pre-registration -- the runner enumerates, it does not choose.
    """
    out = []
    for a, b, _rho in CELLS["gate_unordered"]:
        if a in pool and b in pool:
            out.append(("gate", a, b))
            out.append(("gate", b, a))
    for a, b in CELLS["veto"]:
        if a in pool and b in pool:
            out.append(("veto", a, b))
    return out


def fmt(v, w, d=2):
    return f"{v:+{w}.{d}f}" if v is not None else f"{'--':>{w}s}"


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
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(M.B.FIXTURE), (
        "CACHE IS STALE -- rebuild rather than scoring numbers that belong to "
        "code that no longer exists.")
    pool, peaks = pool_and_peaks()
    scores = {c: z[c] for c in pool}
    base = z["warm"] & live
    shape = base.shape
    fwd = M.forward_returns(panel, live)
    groups = group_list(pool)
    ncells = len(groups) * len(FRACTIONS)
    print(f"loaded {len(pool)} capturable tier-1 spread candidates | "
          f"{len(groups)} groups x {len(FRACTIONS)} f = {ncells} cells | base "
          f"{int(base.sum()):,} warm live cells ({time.time() - t0:.0f}s)",
          flush=True)
    assert ncells == 272, f"expected the 272 declared cells, built {ncells}"

    assertions(scores, base, fwd, panel, live, peaks)

    rp = rotate_plan(live)
    off = np.random.default_rng(3).integers(1, T, size=live.shape[0])
    v, w = rotate(scores["rsi"], rp, off), rotate_loop(scores["rsi"], rp["ats"], off)
    assert np.array_equal(np.isnan(v), np.isnan(w)) and \
        np.array_equal(v[~np.isnan(v)], w[~np.isnan(w)]), \
        "VECTORISED ROTATION DIFFERS from the per-symbol loop it replaced"
    print(f"    [5] vectorised rotation == the per-symbol np.roll loop, exactly")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    print(f"\n  ranking {len(pool)} candidates once each", flush=True)
    R = {c: ranked(scores[c], base) for c in pool}
    # A's legs never move -- not across f, not across draws, not across B.
    plans = {c: LegPlan(R[c][0], R[c][1], peaks[c][0], T) for c in pool}

    def plan_of(ca, n):
        return LegPlan(R[ca][0], R[ca][1], n, T)

    # ---- observed ----
    mcache = {}

    def obs_one(key, g):
        kind, ca, cb = g
        N, k = peaks[ca]
        _, cnt_b, pos_b = R[cb]
        rng = np.random.default_rng(SEED + 1000 * pool.index(ca) + pool.index(cb))
        return eval_group(fwd[k], pos_b, cnt_b, plans[ca], ca, k, kind, rng,
                          plan_of, mcache)

    print(f"  OBSERVED: {ncells} cells in {len(groups)} groups, "
          f"{a.workers} threads", flush=True)
    got = FN.parallel_map(obs_one, [(i, g) for i, g in enumerate(groups)],
                          workers=a.workers)
    obs = {(i, f): v[0] for i, d in got.items() for f, v in d.items()}
    ctrls = {i: {f: v[1] for f, v in d.items()} for i, d in got.items()}
    print(f"  {len(obs)}/{ncells} cells evaluated ({time.time() - t0:.0f}s)",
          flush=True)

    # ---- rotate-B null, FACTORED BY B: 13 x draws sorts, not 272 x draws ----
    by_b = {}
    for i, (kind, ca, cb) in enumerate(groups):
        if ctrls.get(i):
            by_b.setdefault(cb, []).append(i)

    def null_one(key, task):
        bi, draw = task
        cb = pool[bi]
        rng = np.random.default_rng(SEED + 131 * bi + 7919 * draw)
        off = rng.integers(1, T, size=live.shape[0])
        cnt_b, pos_b = ranked_pos(rotate(scores[cb], rp, off), base)
        out = {}
        for i in by_b.get(cb, []):
            _, ca, _ = groups[i]
            for f, v in null_group(fwd[peaks[ca][1]], pos_b, cnt_b, plans[ca],
                                   ctrls[i]).items():
                out[(i, f)] = v
        return out

    tasks = [((bi, d), (bi, d)) for bi in range(len(pool))
             for d in range(a.draws) if pool[bi] in by_b]
    print(f"\n  ROTATE-B NULL: {len(tasks)} (B, draw) tasks covering "
          f"{len(obs)} cells x {a.draws} draws", flush=True)
    nres = FN.parallel_map(null_one, tasks, workers=a.workers)

    draws = {d: {} for d in range(a.draws)}
    for (bi, d), out in nres.items():
        draws[d].update(out)

    # ---- the floor: the JOINT max over all cells, per draw ----
    # A Bonferroni over 272 would price 272 INDEPENDENT tests; the pool carries
    # 4.89 effective dimensions. This draws the max from the null's OWN joint
    # distribution, so the real correlation structure prices itself.
    per_cell = {c: [] for c in obs}
    joint = []
    for d in range(a.draws):
        vals = [v for v in draws[d].values() if v is not None]
        if vals:
            joint.append(max(vals))
        for c, v in draws[d].items():
            if v is not None and c in per_cell:
                per_cell[c].append(v)
    floor = float(np.percentile(joint, 95)) if joint else None
    print(f"  joint max-t over {len(obs)} cells, {len(joint)} draws: "
          f"p50 {np.percentile(joint, 50):+.2f}  p95 {floor:+.2f}  "
          f"max {max(joint):+.2f}", flush=True)

    rows = []
    for (i, f), r in obs.items():
        kind, ca, cb = groups[i]
        arr = np.array(per_cell[(i, f)])
        zc = (float((r["t"] - arr.mean()) / arr.std(ddof=1))
              if arr.size > 5 and arr.std(ddof=1) > 0 else None)
        rows.append(dict(kind=kind, A=ca, B=cb, f=f, k=peaks[ca][1], **r,
                         null_p50=float(np.percentile(arr, 50)) if arr.size else None,
                         null_p95=float(np.percentile(arr, 95)) if arr.size else None,
                         null_z=zc,
                         beats_floor=bool(r["t"] > floor) if floor else None))
    rows.sort(key=lambda r: -r["t"])

    json.dump({"purpose": "D291 stage-1 confluence: gate and veto as ONE "
                          "selection operator, scored by the PAIRED DIFFERENCE "
                          "against a matched control, with a rotate-B null and "
                          "an empirical best-of-272 floor.",
               "preregistered": "a1fbc14", "clarified": "4603b68",
               "pool": pool, "peaks": peaks, "fractions": list(FRACTIONS),
               "draws": a.draws, "n_cells": ncells, "n_random": N_RANDOM,
               "joint_floor_p95": floor,
               "joint_null": {"p50": float(np.percentile(joint, 50)),
                              "p95": floor, "max": float(max(joint))},
               "rows": rows}, open(OUT, "w"), indent=1)

    print(f"\n  TOP 15 BY PAIRED t   (floor {floor:+.2f})")
    print(f"  {'kind':5s} {'A':16s} {'B':16s} {'f':>5s} | {'D bp':>8s} "
          f"{'t':>6s} | {'conf':>8s} {'ctrl':>8s} | {'null p95':>8s} "
          f"{'z':>6s} | pass")
    for r in rows[:15]:
        p = "YES" if (r["beats_floor"] and r["t"] >= 2.0) else "no"
        print(f"  {r['kind']:5s} {r['A']:16s} {r['B']:16s} {r['f']:5.2f} | "
              f"{fmt(r['d_bp'], 8)} {fmt(r['t'], 6)} | {fmt(r['conf_bp'], 8)} "
              f"{fmt(r['ctrl_bp'], 8)} | {fmt(r['null_p95'], 8)} "
              f"{fmt(r['null_z'], 6)} | {p}")
    n_pass = sum(1 for r in rows if r["beats_floor"] and r["t"] >= 2.0)
    print(f"\n  {n_pass} of {len(rows)} cells clear both paired t >= 2 and the "
          f"best-of-{ncells} floor")
    print(f"  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
