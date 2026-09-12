"""D399 -- THE LINE'S POSITION IS SCORED, AND A BREAK RECALCULATES IT INSTEAD OF RATCHETING IT.

    uv run python scripts/d399_recalc_segment.py --selftest     audits only
    uv run python scripts/d399_recalc_segment.py                the grid
    uv run python scripts/d399_recalc_segment.py --chart        chart data for the page

Three changes, all asked for by the principal, and each one is separable from the others so the
grid can say which of them did the work.

1. THE SCORE NOW READS THE POSITION OF THE LINE, not only its gradient. Every D399 score so far
   compared `g_fit` to `g_true` and never looked at where the line sat -- which is how a
   construction whose support line ran 23% under the low kept scoring well. The ground truth
   carries both clicks per line, so the drawn LEVEL at every bar is recoverable, and

       q_g = clip(1 - |g_fit - g_true| / max(|g_true|, DELTA), 0, None)      as before
       q_l = clip(1 - |log(L_fit) - log(L_true)| / LEVEL_TOL, 0, None)       NEW
       quality = q_g * q_l

   The product, not the mean: a line with the right slope in the wrong place is not the line he
   drew, and a mean would let a perfect gradient pay for a line 30% away. `--pos-weight 0`
   recovers the published scorer exactly and is asserted to reproduce 0.3175.

2. THE RATCHET IS GONE. Not replaced, removed. There is no sliding intercept anywhere in this
   file: the line is the OLS fit, gradient AND intercept together, frozen at the bar its segment
   opened, and it is never adjusted while it lives. It is thrown away instead.

3. THE INVALIDATION IS A DECLARED PARAMETER, on both quantities:

       |g_now      - g_seg      | > MAX_DG      the GRADIENT has drifted past its deadband
       |line_now(t) - line_seg(t)| > MAX_DH     the HEIGHT has drifted past its deadband

   `now` is the OLS fit over every pivot confirmed so far in the segment; `seg` is the fit frozen
   when it opened. On either, the segment is invalidated and RECALCULATED -- new gradient and new
   height together -- from the surviving `carry` pivots. Either deadband can be set to NEVER, so
   the grid contains all four corners and can say what each test is worth alone. Without (3), (2)
   is ill-posed: something has to say how far is too far before "recalculate" is a rule and not a
   mood.

   `use_body` is a THIRD, optional invalidator carrying the principal's earlier rule -- a candle
   body closing through the line. It is a declared axis, not part of the mechanism.

CAUSALITY. Every fit reads only pivots confirmed by t-k (D173), and the frozen line is knowable at
the previous close, so a body closing through it at t is genuinely new information. `[L]` re-derives
the line at sampled bars from a truncated rebuild -- the BARS cut at t, pivots recomputed on the
cut -- asserts gradient, level and origin agree, asserts the k=0 build DIFFERS, and asserts the
audit actually compared something -- an earlier version of it passed on zero comparisons because
min_piv=5 left G empty, and a later one exercised a builder nothing else called.

THE INDEPENDENT REVIEW (2026-09-10). Comment-stripped copies of this file were handed to an
agent with the spec and none of my claims. It confirmed causality and both invariants and found
five defects -- the fit's points not in bar order, so the age weight was mis-applied in about half
the fits (D1); the walk resurrecting provisional points (D2); a body close untested on bars whose
candidate fit was nan (D3); whole-series counts in a per-window table (D4); an assertion claimed
in a docstring that did not exist (D5) -- and six suspicions. Each fix and each suspicion's
switch is named where it lives in `recalc_pair`; the self-tests `[S] [V] [L] [Z]` are the
guards that would have caught them. EVERY NUMBER PRODUCED BETWEEN THE WALK GOING IN AND THIS
REVIEW came from the defective code and has been re-run (data/d399_review_fixes.json).
"""

from __future__ import annotations

import argparse
import bisect
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

OUT = REPO / "data" / "d399_recalc_scores.json"
CHART = REPO / "temp" / "d399_recalc_chart.json"
LEVEL_TOL = math.log(1.10)      # a line 10% away from his scores zero on position
PUBLISHED_CAUSAL = 0.3175


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


SV = _load("d399sv", "d399_signed_vol_segment.py")
ols = SV.ols


def wls(x, y, decay_end=1.0):
    """OLS with an EXPONENTIAL AGE WEIGHT on the pivots. `decay_end` is the weight the OLDEST
    pivot carries; the newest always carries 1.0.

        w_i = decay_end ** ((x_new - x_i) / (x_new - x_old))

    Span-normalised deliberately, because that is what "90% at the oldest" means: the oldest point
    gets exactly `decay_end` whether the segment spans eight bars or eighty. A fixed per-bar decay
    would instead make the end weight depend on the span, which is a different and defensible
    choice -- it is not the one that was asked for, and the two disagree most on the long segments
    that matter most.

    `decay_end = 1.0` gives every pivot weight 1 and must reproduce `ols` BIT-IDENTICALLY -- it is
    the control, and `[W]` asserts it rather than trusting the algebra.

    NOTE ON WHAT THIS MOVES. The weighted fit passes through the WEIGHTED centroid, so with
    `anchor_clear` on -- where the intercept comes from body clearance and not from the fit at all
    -- the age weight changes the GRADIENT only. With it off it moves both."""
    n = len(x)
    if n < 2:
        return np.nan, np.nan
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if decay_end == 1.0:
        return ols(x, y)
    span = float(x[-1] - x[0])
    if not np.isfinite(span) or span <= 0.0:
        # RAISED, NOT PAPERED OVER. This used to fall back to plain OLS, which is how an unsorted
        # buffer ran for weeks with the age weight silently off in 29% of fits (review, D1). A
        # non-positive span means the points are not in bar order, and that is the caller's bug.
        raise ValueError(f"wls: x[-1] - x[0] = {span!r} <= 0 -- points not in bar order: {x}")
    w = np.power(float(decay_end), (float(x[-1]) - x) / span)
    return wols(x, y, w)


def wols(x, y, w):
    """Weighted least squares with explicit weights -- the arithmetic `wls` always did, in the
    same order, so `wls` stays bit-identical to itself; the other age laws hand their weights in
    here."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    w = np.asarray(w, float)
    sw = float(w.sum())
    if sw <= 0.0:
        return np.nan, np.nan
    xm = float((w * x).sum() / sw)
    dx = x - xm
    den = float((w * dx * dx).sum())
    if den <= 0.0:
        return np.nan, np.nan
    ym = float((w * y).sum() / sw)
    b = float((w * dx * (y - ym)).sum() / den)
    return b, float(ym - b * xm)


def age_weights(mode, x, t, p, ext=None, y=None, kind=None, tol=0.025):
    """FIVE ANSWERS TO "WHAT IS AGE?", one weight per pivot, newest last. `p` is the mode's one
    number. Returns None where every weight is 1 (so the unweighted path is used unchanged).

        span      p ** ((x_new - x_i) / (x_new - x_old))   1 at the newest pivot, p at the oldest,
                  whatever the span (the principal's original spec: "90% at the oldest")
        linear    1 - (1 - p) * (x_new - x_i) / span        same endpoints, a straight ramp
        halflife  0.5 ** ((t - x_i) / p)                    age in BARS from today; p is the
                  half-life. A 15-bar segment is barely discounted, a 150-bar one forgets its
                  origin -- which span-normalisation cannot express
        rank      p ** k for the k-th newest pivot          age in SWINGS, blind to bar distance
        respect   1 + (bars after x_i whose extreme came within `tol` of the line of the
                  unweighted slope through pivot i)         evidence, not age: a pivot price has
                  kept returning to counts more. One step, not iterated, so not circular."""
    n = len(x)
    x = np.asarray(x, float)
    if n < 2:
        return None
    if mode in ("span", "linear"):
        if p == 1.0:
            return None
        span = float(x[-1] - x[0])
        if not np.isfinite(span) or span <= 0.0:
            raise ValueError(f"age_weights: span {span!r} <= 0 -- points not in bar order: {x}")
        if mode == "span":
            return np.power(float(p), (float(x[-1]) - x) / span)
        return 1.0 - (1.0 - float(p)) * (float(x[-1]) - x) / span
    if mode == "halflife":
        if not p > 0:
            raise ValueError("halflife must be positive")
        return np.power(0.5, (float(t) - x) / float(p))
    if mode == "rank":
        if p == 1.0:
            return None
        return np.power(float(p), np.arange(n - 1, -1, -1, dtype=float))
    if mode == "respect":
        g0, _c0 = ols(x, y)
        if not np.isfinite(g0):
            return None
        w = np.ones(n)
        for i in range(n):
            a, b = int(x[i]) + 1, int(t)
            if b < a:
                continue
            q = np.arange(a, b + 1, dtype=float)
            line = float(y[i]) + g0 * (q - x[i])
            e = ext[kind][a:b + 1]
            off = e - line
            w[i] += float((np.abs(off[np.isfinite(off)]) <= tol).sum())
        return w
    raise ValueError(f"unknown decay mode {mode!r}")


# --------------------------------------------------------------------------
# 1. the ground truth's own LEVEL, per bar
# --------------------------------------------------------------------------


def true_levels(gt, kind):
    """The drawn line's price at every bar he held it.

    Where two lines overlap -- one ends on the bar the next is drawn -- the NEWER one wins, and
    the choice is not free: the reconstructed per-bar gradient is asserted equal to the ground
    truth's own `g_<kind>` array, so a wrong tie rule fails loudly instead of biasing the score."""
    n = int(gt["n"])
    lvl = np.full(n, np.nan)
    grd = np.full(n, np.nan)
    for L in sorted((x for x in gt["lines"] if x["kind"] == kind), key=lambda x: x["drawn_at"]):
        sg = L["segment"]
        a, b = int(L["drawn_at"]), max(int(L["drawn_at"]), int(L["ended_at"]))
        i = np.arange(a, min(b, n - 1) + 1)
        lvl[i] = np.exp(np.log(sg["p0"]) + L["g_per_bar"] * (i - sg["i0"]))
        grd[i] = L["g_per_bar"]
    ref = np.array([np.nan if v is None else v for v in gt[f"g_{kind}"]], float)
    both = np.isfinite(ref) & np.isfinite(grd)
    assert np.array_equal(np.isfinite(ref), np.isfinite(grd)), (
        f"[T] the reconstructed {kind} coverage is not the ground truth's own")
    assert np.allclose(grd[both], ref[both], rtol=0, atol=1e-12), (
        f"[T] the reconstructed {kind} gradient disagrees with the ground truth's own g_{kind} -- "
        f"the overlap tie rule is wrong")
    return lvl, ref


# --------------------------------------------------------------------------
# 1b. the score, with position
# --------------------------------------------------------------------------


def score_side_pos(g_fit, l_fit, g_true, l_true, seen, delta, pos_weight=1.0,
                   level_tol=LEVEL_TOL, beta2=0.25):
    """`d399_score_causal.score_side` with a POSITION term multiplied into the quality.

    pos_weight = 0 recovers the published scorer exactly; 1 is the full product."""
    f_on = np.isfinite(g_fit) & seen
    if pos_weight > 0:
        f_on = f_on & np.isfinite(l_fit)
    t_on = np.isfinite(g_true) & seen
    TP = int((f_on & t_on).sum())
    FP = int((f_on & ~t_on).sum())
    FN = int((~f_on & t_on).sum())
    TN = int((~f_on & ~t_on & seen).sum())
    if TP == 0:
        return dict(TP=0, FP=FP, FN=FN, TN=TN, precision=0.0, recall=0.0, f_beta=0.0,
                    q_grad=None, q_level=None, quality=None, score=0.0)
    both = f_on & t_on
    gt = g_true[both]
    rel = np.abs(g_fit[both] - gt) / np.maximum(np.abs(gt), delta)
    qg = np.clip(1.0 - rel, 0.0, None)
    if pos_weight > 0:
        with np.errstate(divide="ignore", invalid="ignore"):
            d = np.abs(np.log(l_fit[both]) - np.log(l_true[both]))
        ql = np.clip(1.0 - d / level_tol, 0.0, None)
        ql = np.where(np.isfinite(ql), ql, 0.0)
        q = qg * (ql ** pos_weight)
    else:
        ql = np.full(qg.shape, np.nan)
        q = qg
    quality = float(q.mean())
    P = TP / (TP + FP) if (TP + FP) else 0.0
    R = TP / (TP + FN) if (TP + FN) else 0.0
    F = ((1 + beta2) * P * R / (beta2 * P + R)) if (P + R) > 0 else 0.0
    return dict(TP=TP, FP=FP, FN=FN, TN=TN, precision=round(P, 4), recall=round(R, 4),
                f_beta=round(F, 4), q_grad=round(float(qg.mean()), 4),
                q_level=(round(float(np.nanmean(ql)), 4) if pos_weight > 0 else None),
                quality=round(quality, 4), score=round(quality * F, 4))


# --------------------------------------------------------------------------
# 2 + 3. the construction: freeze, test, recalculate
# --------------------------------------------------------------------------


def _hull_edges(x, y, lower):
    """Monotone chain over points already sorted by x with distinct x -- which a side's pivots
    are. Returns consecutive hull vertices as index pairs (i, j), in increasing i.

    COLLINEAR MIDDLES ARE DROPPED, WITH AN EPSILON. Three pivots in a straight line must become
    ONE edge with the middle counted as a touch. A strict zero test does that only when the cross
    product rounds to exactly 0.0, and on real collinear runs it rounds to +-1e-17 -- so the
    middle was kept or dropped by float noise, the line was anchored on a different pair, and
    `[V]` found 113 of 1,200 intercepts one ULP off the pair enumeration's. The units are bars
    times log-price: a genuine turn has |cross| of order 1e-4 or more, so 1e-9 separates
    collinear from not by five orders of magnitude either way."""
    n = len(x)
    if n < 2:
        return []
    EPS = 1e-9
    h = []
    for p in range(n):
        while len(h) >= 2:
            a, b = h[-2], h[-1]
            cross = (x[b] - x[a]) * (y[p] - y[a]) - (y[b] - y[a]) * (x[p] - x[a])
            if (cross <= EPS) if lower else (cross >= -EPS):
                h.pop()
            else:
                break
        h.append(p)
    return [(h[q], h[q + 1]) for q in range(len(h) - 1)]


def envelope_fit(x, y, kind, tol, decay_end=1.0, w=None):
    """THE LINE A CHARTIST DRAWS: the most-respected edge of the pivots' envelope.

    AGE, ON THE CHOICE ONLY (`decay_end`). The regression's age weight has no meaning here --
    nothing is fitted -- so age enters where the envelope makes its one decision: which of the
    valid edges wins. Each touching pivot supports an edge by

        w_i = decay_end ** ((x_new - x_i) / (x_new - x_old))     1.0 at the newest, decay_end at the oldest

    and the edge with the largest SUM of support wins, longest span on a tie, then first. The
    same span-normalised law as `wls`, so "oldest at 80%" means the same thing on both
    estimators. What it does NOT touch: the candidates (still the hull's edges), validity (an
    old pivot on the wrong side still vetoes -- forgiving it would put the line through a pivot
    and bring back the O(n^3) pair search), and QUALIFICATION -- the returned `touches` is the
    plain count, so `min_touch = 3` still means three real touches rather than 2.7 weighted
    ones. At decay_end = 1.0 every weight is 1 and this is bit-identical to the unweighted
    choice (`audit_envelope_age`). The behavioural change is that a short recent edge now beats
    a long old one at equal touch count -- which is what "older matters less" means, and is
    also what to watch: a candidate that switches edges more readily fires the height test
    more.

    Not a regression. A regression runs through the middle of its points and every repair since --
    the clearance intercept, the age decay, the back-projection check -- has been compensating for
    that. A trendline TOUCHES its anchors. So:

        among every pair of pivots whose connecting line has no pivot on the wrong side of it
        (below, for support; above, for resistance) by more than `tol`,
        take the one the most pivots TOUCH -- sit within `tol` of -- and on a tie the longer span.

    Gradient and level come from the same two pivots; there is no separate offset to generate.
    Every pivot clears the line by construction. `tol` is the width of a wick, a couple of per
    cent, not the height deadband. Returns (g, c, touches); (nan, nan, 0) below two points.

    ON THE HULL, NOT OVER ALL PAIRS. A line through two pivots with every other pivot on one side
    of it is, by definition, an edge of the convex hull -- the lower hull for support, the upper
    for resistance. So the candidates are the hull's edges, ~h of them, found by monotone chain
    in O(n log n), not the n^2 pairs the first version enumerated with an O(n) check each. That
    version was O(n^3), and an envelope segment's buffer grows into the hundreds because its line
    sits under everything and rarely breaks: one name ran past ten minutes.

    ONE DEFINITIONAL CHANGE, stated: the pair enumeration also admitted lines that a pivot dipped
    BELOW by up to `tol` -- near-supporting lines. The hull does not. As tol -> 0 the two sets
    coincide, and `audit_envelope` ([V], run from `--selftest`) asserts the two functions return
    bit-identical (g, c, touches) at tol = 1e-12 on tie-heavy inputs with planted collinear
    triples. An earlier docstring claimed that assertion before it existed (review, D5). At a
    working tol they can differ, and the hull's is the definition from here on. `tol` still
    counts touches. Tie-breaking is unchanged: most touches, then longest span, then the edge
    with the smallest first index -- which is `_hull_edges` order, and was triu order before.

    Collinear middles are dropped from the hull, so three lows in a straight line make ONE edge
    with the middle counted as a touch, which is what a chartist would draw."""
    n = len(x)
    if n < 2:
        return np.nan, np.nan, 0
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    edges = _hull_edges(x, y, lower=(kind == "support"))
    if not edges:
        return np.nan, np.nan, 0
    i = np.array([e[0] for e in edges], int)
    j = np.array([e[1] for e in edges], int)
    dx = x[j] - x[i]
    keep = dx > 0.0
    i, j, dx = i[keep], j[keep], dx[keep]
    if i.size == 0:
        return np.nan, np.nan, 0
    g = (y[j] - y[i]) / dx
    c = y[i] - g * x[i]
    r = y[None, :] - (g[:, None] * x[None, :] + c[:, None])
    valid = ~((r < -tol).any(axis=1) if kind == "support" else (r > tol).any(axis=1))
    if not valid.any():
        return np.nan, np.nan, 0
    hit = np.abs(r) <= tol
    touches = hit.sum(axis=1)
    if w is not None:
        support = (hit * np.asarray(w, float)[None, :]).sum(axis=1)   # the caller's age law
    elif decay_end == 1.0:
        support = touches.astype(float)            # the control: the count itself
    else:
        span = float(x[-1] - x[0])
        if span <= 0.0:
            raise ValueError(f"envelope_fit: span {span!r} <= 0 -- points not in bar order: {x}")
        w = np.power(float(decay_end), (float(x[-1]) - x) / span)
        support = (hit * w[None, :]).sum(axis=1)
    tv = np.where(valid, support, -1.0)
    mt = tv.max()
    cand = valid & (tv == mt)
    dxv = np.where(cand, dx, -np.inf)
    cand &= dxv == dxv.max()
    p = int(np.argmax(cand))                       # first True in triu order
    return float(g[p]), float(c[p]), int(touches[p])


def _envelope_fit_loop(x, y, kind, tol):
    """The original loop, kept ONLY as the reference the vectorised version is checked against."""
    n = len(x)
    if n < 2:
        return np.nan, np.nan, 0
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            if dx <= 0.0:
                continue
            g = (y[j] - y[i]) / dx
            c = y[i] - g * x[i]
            r = y - (g * x + c)
            if kind == "support":
                if (r < -tol).any():
                    continue
            elif (r > tol).any():
                continue
            key = (int((np.abs(r) <= tol).sum()), float(dx))
            if best is None or key > best[0]:
                best = (key, g, c)
    if best is None:
        return np.nan, np.nan, 0
    return float(best[1]), float(best[2]), int(best[0][0])


def _check_sorted(fx, where):
    """[S] EVERY ESTIMATOR HERE ASSUMES ITS POINTS ARRIVE IN BAR ORDER, AND NOTHING CHECKED IT.

    `wls` takes x[-1] as the newest point and x[-1]-x[0] as the span; `_hull_edges` is a monotone
    chain. The independent review found the buffer unsorted in 51-69% of fits: the provisional
    pivot was appended LAST whatever its bar, and the walk inserted at position 0 whatever its bar.
    So the age weight was applied as specified in about half the fits, newer pivots carried weights
    above 1, and the hull returned "no edge" where a six-touch edge existed. Raised, not repaired:
    a caller that hands over an unsorted buffer has a bug upstream of the estimator."""
    n = len(fx)
    for i in range(1, n):
        if not fx[i] > fx[i - 1]:
            raise AssertionError(
                f"[S] fit input not strictly increasing at {where}: x[{i - 1}]={fx[i - 1]!r} "
                f"x[{i}]={fx[i]!r} in {list(fx)}")


def recalc_pair(piv, k, body_log, m, carry, min_piv, max_dg, max_dh, use_body, min_width,
                delta, gate=True, ext_log=None, break_pivot=False, extra_piv=1,
                back_check=True, anchor_clear=False, decay_end=1.0,
                extend_back=False, back_tol=None,
                fit_mode="ols", touch_tol=0.025, min_touch=3,
                height_mode="raw", walk_chain="body_only", max_reach=130, syn_ttl=True,
                stale_w=None, stale_d=0.05, stale_stat="mean", fit_tol=None,
                pair_break=False, pair_draw=False, anchor_mode=None,
                break_depth=0.0, break_bars=1, max_piv=None, decay_mode="span",
                anchor_q=0.15, break_keep=None):
    """BOTH SIDES IN ONE WALK, because support above resistance is not a channel.

    `recalc_events` builds each side in a separate pass, and nothing in it -- or anywhere else in
    this programme -- forbids the support line from sitting ABOVE the resistance line. On the
    body-break cell that happened on 17 of 238 bars, once by 83%. It was never a coding slip: it
    was a missing invariant, and a cell that restarts often enough on `carry` pivots exposed it.

    So the pair is now a fourth invalidator, and the most fundamental one: if the channel has
    inverted (or narrowed past `min_width`), the structure is gone and BOTH segments die together.
    `assert_no_inversion` then holds as a promise rather than a hope.

    min_width = 0.0 forbids only the crossing itself; > 0 demands a channel that wide in log price.

    THE BREAK BAR IS A PIVOT (`break_pivot`). When a body closes through the line, the bar that did
    it is treated as a PROVISIONAL pivot at that side's own extreme -- the high for resistance, the
    low for support. It joins the fit immediately and lives there until one of these happens:

        * the detector confirms a pivot at that same bar -- it was real all along, and it is
          simply absorbed (never counted twice); or
        * another break produces a NEWER provisional point, which supersedes it; or
        * (`syn_ttl`) the detector has had its chance at that bar -- `syn.bar <= t - k` -- and did
          not confirm it. The point was falsified, and the line that rested on it goes DORMANT
          until the next confirmed pivot, exactly as after a drift. Without this the review found
          a provisional alive, unratified, 276 bars after it was made.

    At most one provisional point per side is ever alive. Because it counts toward `min_piv` while
    being weaker evidence than a confirmed pivot, a segment opened by a break must clear
    `min_piv + extra_piv` instead -- which is what pays for it.

    THE FIVE THINGS THE INDEPENDENT REVIEW FOUND, AND WHERE EACH IS FIXED:

      D1  the fit's points were not in bar order   -> `fit_pts` merges by bisect, the walk inserts
          by bisect, every fit passes `_check_sorted`, and `wls` raises on a non-positive span
          instead of silently dropping the age weight.
      D2  the walk resurrected provisionals        -> `old` is taken from the CONFIRMED buffer
          only; the walk's `have` set includes the live provisional; a break on a bar the detector
          already confirmed (possible at k=0) makes no provisional at all.
      D3  a body close was not tested on a bar whose candidate fit was nan -> the gradient and
          height tests need the candidate; the body test needs only the frozen line and now runs
          regardless. `why["nan_fit"]` counts the bars.
      D4  `events` -- every invalidation, provisional, walk and cap as (t, side, kind) -- so a
          caller can count inside its own window instead of over the whole series.
      D5  `[V]` now exists (`audit_envelope`).

    AND THE SUSPICIONS, EACH A DECLARED SWITCH SO THE GRID CAN SAY WHAT IT IS WORTH:

      height_mode  "raw": the height test compares the candidate fit to the frozen fit's OWN raw
                   intercept (`c_raw`), which is what "current fit vs frozen fit" says. "anchored"
                   compares it to the drawn, clearance-anchored line, which made the deadband
                   narrower by the anchor offset on every segment (p90 0.03 of a 0.26 deadband,
                   max 0.54 -- invalidated on the next bar by the anchor alone).
      back_tol     the walk's proximity test is now made against the line BEFORE the candidate
                   joins it; the earlier test was against a refit that already contained the
                   point, which pulls the line toward it.
      walk_chain   "body_only": a segment's walked-in points are handed on to the next segment
                   only when this one ended on a BODY break -- the false-break case the walk exists
                   for. After a drift or a crossing, the next segment may walk into the native
                   points only (carried points count as native). "native_only" never hands them
                   on; "unbounded" always does, which chained s0 back 663 bars.
      max_reach    an absolute cap on how far back the walk may go, in bars. The one new number;
                   `why["max_reach_hit"]` says how often it was the thing that stopped a walk.
      syn_ttl      above.

    IS PRICE STILL RESPECTING THE LINE? (the principal's question, 2026-09-10). Every invalidator
    above asks whether the FIT has moved. None asks whether price is still near the line -- which
    is how a support sat 30% under six months of candles on CRMT: no body can break a line that
    far away, and a candidate fit still full of the old pivots never drifts 30%. So, one
    statistic in the chartist's units, the signed OFFSET of each bar's extreme from the line,

        off_t = log(low_t) - line_t        (support;  line_t - log(high_t) for resistance)

    serves two tests:

      stale_w / stale_d / stale_stat   LIFE. The line dies when the offset over the last
                   `stale_w` bars, summarised by `stale_stat` ("mean": its SMA, the principal's
                   choice; "min": the closest approach, i.e. "no touch in W bars"), exceeds
                   `stale_d`. Dormant until the next confirmed pivot, like a drift: the refit
                   then comes from the carry points, which are the RECENT lows, so the line
                   re-forms where price is. Nothing slides.
      fit_tol      BIRTH. A line is drawn only if the mean |residual| of its founding pivots
                   from it is <= fit_tol -- "too strict" caught before it exists rather than
                   diagnosed after it dies. Applies to the refit and to every walk step.

    A staleness death is SPLIT: if any bar after the line was first drawn came within `stale_d`
    of it, price respected the line and then left (`stale_abandoned`); if none did, the line
    was never confirmed (`stale_unconfirmed`) -- a bad draw that got past the birth check. The
    split says which lever to move: construction, or W.

    THE SEGMENT IS A CHANNEL (the principal, 2026-09-10: "when one is broken it counts as both
    being broken"). Two switches, so each half can be seen on its own:

      pair_break   any invalidation of one side -- gradient, height, body, stale -- resets the
                   OTHER side too, the way the inversion test always has. The broken side keeps
                   its own reason (and its provisional pivot, if a body break made one); the
                   partner is reset as "pair": dormant until its next confirmed pivot, and its
                   walked-in points are not handed on (it did not end on a body break).
      pair_draw    a bar is drawn only when BOTH sides qualify: the channel, or nothing.

    THE HEIGHT FROM ONE PIVOT (the principal, 2026-09-10: "the gradients come out really well,
    the height seems too strict ... it should probably only go directly through one pivot").
    `anchor_mode`:
        "clear"  the intercept that clears EVERY body back to the origin (`anchor_clear`, the
                 earlier rule). Its level is set by the single deepest candle in the stretch --
                 the strictest possible height, one outlier away from price.
        "pivot"  the line keeps the regression gradient and passes THROUGH the one founding pivot
                 that sits outermost against that slope -- lowest for support, highest for
                 resistance -- so every other pivot is on or inside it. No body is consulted in
                 placing it, and the back-projection body check is not applied (a non-pivot body
                 between two pivots may sit through the line); the forward body-break rule polices
                 it from the bar it is drawn.
        "latest" through the NEWEST founding pivot, regression gradient. With "pivot" the age
                 decay pulls the slope onto the newest points and leaves the OLDEST pivot sticking
                 out, so the oldest becomes the anchor and the line hangs on its origin (the
                 principal: "the first pivot points still seem to be prioritised"). Here the
                 height is what price is respecting now; older pivots may sit either side.
        "quantile" the AGE-WEIGHTED q-th quantile (`anchor_q`) of the founding pivots' offsets
                 from the slope, r_i = y_i - g x_i, lowest first for support and highest first
                 for resistance. q = 0 unweighted is "pivot"; q = 0.5 is the weighted median;
                 a small q sits on the recent lows and steps over an old outlier whose age
                 weight is a small share of the mass. The one rule where the age law that steers
                 the slope also chooses the level.
        "raw"    the regression intercept as fitted.
    None means: "clear" if `anchor_clear` else "raw" (the earlier calls unchanged).

    A BREAK NEEDS DEPTH AND PERSISTENCE (the principal, 2026-09-10: "it basically gets broken
    every pull back"). A body counts as through the line only when it closes more than
    `break_depth` beyond it (log price), and the break fires only after `break_bars` CONSECUTIVE
    such closes. A one-day dip of 1% is a pullback; three closes 3% below is a breakdown. The same
    tolerance applies wherever the body rule appears -- the emission guard (or the line would
    vanish during the very pullback it is meant to survive), the back-projection check, and the
    [R] / [Z] assertions, which become "no body more than `break_depth` through a drawn line".
    depth 0 / bars 1 is the earlier rule, bit-identical. `why["body_poke"]` counts the tolerated
    closes.

    MAX PIVOTS CONSIDERED (`max_piv`, the principal, 2026-09-10). The fit is the newest
    `max_piv` confirmed pivots and no more: older ones are dropped from the buffer as newer ones
    arrive, so the slope is the last N swings and the origin drops out of the regression once N
    newer pivots exist -- forgetting, where the age decay only down-weights. The drawn origin
    moves forward with the buffer, and the walk stops adding old points once the buffer is full.
    None is off. `why["max_piv_drop"]` counts the pivots forgotten.

    Returns (G, L, S, why); `why["events"]` is the D4 list.
    """
    assert break_bars >= 1 and break_depth >= 0.0, (break_bars, break_depth)
    assert max_piv is None or max_piv >= 2, max_piv
    assert decay_mode in ("span", "linear", "halflife", "rank", "respect"), decay_mode
    assert decay_mode != "respect" or ext_log is not None, "respect weighting needs the extremes"
    # the halflife and respect laws depend on TODAY, not only on the buffer: the candidate fit
    # cannot be cached on the buffer version under them
    fit_depends_on_t = decay_mode in ("halflife", "respect")
    if anchor_mode is None:
        anchor_mode = "clear" if anchor_clear else "raw"
    assert anchor_mode in ("clear", "pivot", "latest", "quantile", "raw"), anchor_mode
    assert 0.0 <= anchor_q <= 1.0, anchor_q
    assert height_mode in ("raw", "anchored"), height_mode
    assert walk_chain in ("body_only", "native_only", "unbounded"), walk_chain
    assert stale_stat in ("mean", "min"), stale_stat
    assert stale_w is None or ext_log is not None, "staleness needs the bars' extremes"
    G = {kd: np.full(m, np.nan) for kd in ("support", "resistance")}
    L = {kd: np.full(m, np.nan) for kd in ("support", "resistance")}
    S = {kd: np.full(m, -1, int) for kd in ("support", "resistance")}
    why = {"gradient": 0, "height": 0, "body": 0, "inverted": 0, "backproj": 0,
           "extended": 0, "extended_pts": 0, "max_buf": 0, "nan_fit": 0,
           "max_reach_hit": 0, "chain_cut": 0, "walk_prox_stop": 0, "walk_span_stop": 0,
           "syn_made": 0, "syn_confirmed": 0, "syn_superseded": 0, "syn_dropped": 0,
           "syn_prebuffered": 0, "stale": 0, "stale_abandoned": 0, "stale_unconfirmed": 0,
           "unfit": 0, "walk_unfit_stop": 0, "pair": 0, "pair_hidden": 0, "body_poke": 0,
           "max_piv_drop": 0}
    events = []

    st = {}
    for kd in ("support", "resistance"):
        idx, lp = piv[kd]
        order = np.argsort(idx, kind="stable")
        st[kd] = dict(idx=np.asarray(idx, int)[order], lp=np.asarray(lp, float)[order],
                      ptr=0, bx=[], by=[], walked=set(), g=np.nan, c=np.nan, c_raw=np.nan,
                      s0=-1, dormant=False, syn=None, old=[], pending=False, reached=0,
                      touch=0, ver=0, fit_ver=-1, fit_now=(np.nan, np.nan, 0), chk_ver=-1,
                      born=None, touched=False, thru=0)

    def ev(t, kd, kind):
        events.append((int(t), kd, kind))

    def fit_pts(d):
        """The confirmed buffer with the live provisional MERGED IN BAR ORDER (D1)."""
        bx, by = d["bx"], d["by"]
        if d["syn"] is None:
            return list(bx), list(by)
        p = bisect.bisect_left(bx, d["syn"][0])
        return bx[:p] + [d["syn"][0]] + bx[p:], by[:p] + [d["syn"][1]] + by[p:]

    def npiv(d):
        return len(d["bx"]) + (0 if d["syn"] is None else 1)

    def need(d):
        """The +1 is the PRICE OF THE PROVISIONAL POINT, so it is charged only while that point is
        alive. Ratified or superseded-and-gone, the segment goes back to the ordinary min_piv --
        it is not a lasting penalty for having once been broken."""
        return extra_piv if d["syn"] is not None else 0

    def spans_bodies(g, c, s0, t, kd):
        """Does this fit's own span clear the bodies of the bars it was FITTED TO?

        The running body test fires at bar t against the frozen line, so it sees the segment's
        future and never its past. But the fit reaches back to `s0`, and the projection over
        [s0, t] was never checked against anything -- measured, 15% of those bars had the line
        through the body, the worst by 35.7%, while the emitted stretch was clean on all 463.

        Entirely causal: every bar in [s0, t] is closed and known at t. A trend line that cuts
        through the candles it was drawn from is not a trend line, so the fit is REJECTED rather
        than slid clear -- sliding it clear is the ratchet, and the ratchet is gone."""
        if not (use_body and back_check) or anchor_mode in ("pivot", "latest", "quantile"):
            return True
        if not (np.isfinite(g) and np.isfinite(c)):
            return True
        a, b = max(0, int(s0)), min(m - 1, int(t))
        if b < a:
            return True
        q = np.arange(a, b + 1, dtype=float)
        lv = g * q + c
        bo = body_log[kd][a:b + 1]
        ok = np.isfinite(bo)
        if not ok.any():
            return True
        bad = ((bo[ok] < lv[ok] - break_depth) if kd == "support"
               else (bo[ok] > lv[ok] + break_depth))
        return not bool(bad.any())

    def clear_intercept(g, s0, t, kd):
        """The intercept that puts a line of slope `g` just clear of every BODY in [s0, t].

        Not the ratchet. The ratchet slid the intercept bar by bar for as long as the line lived;
        this is chosen ONCE when the segment is fitted and then frozen like everything else, and
        an invalidation still throws the whole line away rather than adjusting it."""
        a, b = max(0, int(s0)), min(m - 1, int(t))
        if b < a:
            return np.nan
        q = np.arange(a, b + 1, dtype=float)
        base = body_log[kd][a:b + 1] - g * q
        base = base[np.isfinite(base)]
        if base.size == 0:
            return np.nan
        return float(base.min()) if kd == "support" else float(base.max())

    def fit(fx, fy, kd, t):
        """One place chooses the estimator. ols: weighted regression. envelope: the most-respected
        edge, which returns its own touch count; the regression reports its point count. Both
        are handed points in bar order, and `[S]` says so. The age law (`decay_mode`) makes the
        weights; `span` at `decay_end` goes through `wls` unchanged, bit for bit."""
        _check_sorted(fx, f"{kd} fit")
        if decay_mode == "span":
            if fit_mode == "envelope":
                return envelope_fit(fx, fy, kd, touch_tol, decay_end)
            g, c = wls(fx, fy, decay_end)
            return g, c, len(fx)
        w = age_weights(decay_mode, fx, t, decay_end, ext=ext_log, y=fy, kind=kd, tol=touch_tol)
        if fit_mode == "envelope":
            return envelope_fit(fx, fy, kd, touch_tol, 1.0, w=w)
        g, c = ols(fx, fy) if w is None else wols(fx, fy, w)
        return g, c, len(fx)

    def pivot_intercept(g, fx, fy, kd):
        """THROUGH ONE PIVOT: the intercept that puts a line of slope `g` through the founding
        pivot outermost against that slope, every other pivot on or inside it."""
        base = np.asarray(fy, float) - g * np.asarray(fx, float)
        if base.size == 0:
            return np.nan
        return float(base.min()) if kd == "support" else float(base.max())

    def place(g, c_raw, s0, t, kd, fx, fy):
        """The drawn intercept for a fitted gradient, by `anchor_mode`."""
        if fit_mode == "envelope" or not np.isfinite(g) or anchor_mode == "raw":
            return c_raw
        if anchor_mode == "pivot":
            return pivot_intercept(g, fx, fy, kd)
        if anchor_mode == "latest":
            return float(fy[-1] - g * fx[-1]) if len(fx) else np.nan   # fx is in bar order
        if anchor_mode == "quantile":
            if len(fx) == 0:
                return np.nan
            r = np.asarray(fy, float) - g * np.asarray(fx, float)
            w = age_weights(decay_mode, fx, t, decay_end, ext=ext_log, y=fy, kind=kd, tol=touch_tol)
            w = np.ones(r.size) if w is None else np.asarray(w, float)
            order = np.argsort(r if kd == "support" else -r, kind="stable")
            cw = np.cumsum(w[order]) / float(w.sum())
            # the first offset at which the weighted mass reaches q (q = 0: the outermost)
            j = int(np.searchsorted(cw, anchor_q, side="left"))
            return float(r[order[min(j, r.size - 1)]])
        return clear_intercept(g, s0, t, kd)

    def offset(g, c, t, kd):
        """The bar's extreme against the line, signed so that 0 is a touch and positive is price
        sitting off the line."""
        e = ext_log[kd][t]
        lv = g * t + c
        return (e - lv) if kd == "support" else (lv - e)

    def fits_pivots(g, c, fx, fy):
        """BIRTH: is the line a fair description of its own pivots? mean |residual| <= fit_tol."""
        if fit_tol is None or not np.isfinite(g) or not np.isfinite(c) or len(fx) == 0:
            return True
        r = np.abs(np.asarray(fy, float) - (g * np.asarray(fx, float) + c))
        return float(r.mean()) <= fit_tol

    def freeze(d, g, c_raw, touch, s0, t, kd, fx=(), fy=()):
        """Freeze a fit as the side's line. The RAW intercept is kept beside the drawn one: the
        height test reads the raw one (`height_mode="raw"`), the chart reads the drawn one."""
        d["s0"], d["g"], d["c_raw"], d["touch"] = int(s0), g, c_raw, touch
        d["born"], d["touched"], d["thru"] = None, False, 0   # a new line: undrawn, untested
        # KEEP THE OLS GRADIENT, REPLACE THE OLS INTERCEPT. An OLS line runs through the centroid
        # of its own pivots, so roughly half of them sit on either side and its back-projection
        # cuts the candles it was fitted to -- measured, rejecting every such fit left ZERO
        # segments on the whole window. The two requirements are incompatible, so the intercept
        # has to come from somewhere other than the fit: `place` (the envelope edge already
        # clears every pivot and is left alone).
        c = place(g, c_raw, s0, t, kd, fx, fy)
        d["c"] = c
        if not spans_bodies(g, c, s0, t, kd):
            why["backproj"] += 1
            ev(t, kd, "backproj")
            d["g"] = d["c"] = d["c_raw"] = np.nan
            d["dormant"] = True          # wait for new information; never slide the line
            return False
        if not fits_pivots(g, c, fx, fy):
            why["unfit"] += 1            # too strict: its own pivots do not sit on it
            ev(t, kd, "unfit")
            d["g"] = d["c"] = d["c_raw"] = np.nan
            d["dormant"] = True
            # AND THE BUFFER SLIDES. The first version only went dormant, and a dormant side
            # never truncates: every fresh pivot was appended, the fit through an ever-longer
            # history had an ever-larger residual, and the side never fit again -- 1,384
            # rejections and zero segments at 2.5%. The points that do not sit on a line are
            # the OLD ones, so keep the newest `carry` and wait for the next pivot, exactly as
            # after a drift.
            if carry > 0 and len(d["bx"]) > carry:
                d["bx"] = d["bx"][-carry:]
                d["by"] = d["by"][-carry:]
                d["walked"] = set()
                d["ver"] += 1
            return False
        return True

    def refit(d, t, kd):
        fx, fy = fit_pts(d)
        s0 = int(fx[0]) if fx else t
        g, c, tn = fit(fx, fy, kd, t) if len(fx) >= 2 else (np.nan, np.nan, 0)
        freeze(d, g, c, tn, s0, t, kd, fx, fy)

    def go_dormant(d):
        d["g"] = d["c"] = d["c_raw"] = np.nan
        d["dormant"] = True
        d["born"], d["touched"], d["thru"] = None, False, 0

    def reset(d, t, kd, bad, new_syn=None):
        """A RESET MUST MAKE PROGRESS, and truncating to `carry` does not guarantee it.

        Measured: with carry=3 the buffer usually ALREADY held three pivots, so the refit came back
        bit-identical on 76% of the 1,282 invalidations -- the construction invalidated the line and
        rebuilt exactly the same one, every bar, forever. It never recalculated anything.

        With a break there IS new information (the provisional pivot), so the segment reopens at
        once. Without one -- a gradient or height drift, where nothing new has arrived -- the side
        goes DORMANT and draws nothing until the next confirmed pivot."""
        # REMEMBER THE INVALIDATED SEGMENT'S CONFIRMED PIVOTS before truncating -- the confirmed
        # ones only (D2): a provisional is not evidence the next segment may walk back into.
        # And only the points this segment may hand on (walk_chain, S3).
        hand_all = walk_chain == "unbounded" or (walk_chain == "body_only" and bad == "body")
        if hand_all:
            d["old"] = list(zip(d["bx"], d["by"]))
        else:
            d["old"] = [(x, y) for x, y in zip(d["bx"], d["by"]) if x not in d["walked"]]
            why["chain_cut"] += len(d["bx"]) - len(d["old"])
        d["pending"] = True
        d["reached"] = 0
        # ON A BREAK, KEEP FEWER (`break_keep`, D460). The hand-drawn set ends a line on a break
        # and does not re-fit through the pivots that failed; carrying `carry` of them across the
        # break re-drew a same-sign line at once and overstayed the principal's end. None = the
        # old behaviour (carry). Drifts and unfits still keep `carry`.
        keep = break_keep if (bad == "body" and break_keep is not None) else carry
        d["bx"] = d["bx"][-keep:] if keep > 0 else []
        d["by"] = d["by"][-keep:] if keep > 0 else []
        d["walked"] = set()                       # carried points are native to the new segment
        d["ver"] += 1                             # truncated, and syn may change below
        if new_syn is not None:
            if d["syn"] is not None:
                why["syn_superseded"] += 1
            why["syn_made"] += 1
            ev(t, kd, "syn_made")
            if new_syn[0] in d["bx"]:
                # the detector confirmed this very bar before the break (k=0 only): nothing
                # provisional about it, and a copy would put one bar in the fit twice (D2)
                d["syn"] = None
                why["syn_confirmed"] += 1
                why["syn_prebuffered"] += 1
                ev(t, kd, "syn_confirmed")
            else:
                d["syn"] = new_syn
            d["dormant"] = False
            refit(d, t, kd)
        else:
            go_dormant(d)

    def walk_back(d, t, kd):
        """CARRY BECOMES A TEST. When a new segment first qualifies, walk the invalidated
        segment's pivots NEWEST FIRST and keep each one that still fits the new trend:

            * the pivot sits within `back_tol` of the line AS IT STANDS before the pivot joins it
              (default: the height deadband, already the declared meaning of "far enough to be a
              different line"); and
            * the line refitted WITH the pivot has a back-projection over [pivot, now] that
              clears every candle body.

        Stop at the first that fails -- trend membership is contiguous in time, and skipping a
        misfit to reach an older point that happens to fit would be cherry-picking. Stop too at
        `max_reach` bars back. Every point examined is in the past, so nothing here can leak.

        What it buys: after a FALSE break the post-break pivots line up with the old ones, the
        walk accepts them, and the line gets its origin back instead of restarting from `carry`
        points. After a genuine reversal the first old pivot fails proximity and the segment
        starts clean, with no special case."""
        tol = max_dh if back_tol is None else back_tol
        d["pending"] = False
        if not d["old"] or not np.isfinite(d["g"]):
            return
        have = set(d["bx"])
        if d["syn"] is not None:
            have.add(d["syn"][0])                   # the live provisional is not an old point (D2)
        for (x, y) in reversed(d["old"]):
            if x in have:
                continue                            # already carried; nothing to decide
            if max_piv is not None and len(d["bx"]) >= max_piv:
                break                               # the buffer is full: nothing older fits
            if max_reach is not None and t - x > max_reach:
                why["max_reach_hit"] += 1
                ev(t, kd, "max_reach")
                break
            if fit_mode == "envelope":
                # THREE OUTCOMES, not two. An old pivot on the WRONG side of the current edge is a
                # break: the trend does not reach past it, stop. One that TOUCHES the edge is
                # evidence the line extends back: accept it. One that sits on the right side but
                # does NOT touch is neither -- it neither contradicts the line nor lies on it --
                # so it is skipped without being added. The first version treated that third
                # case as membership, and since nearly every old pivot is above a support line,
                # buffers grew into the hundreds and an O(n^3) fit was run once per accepted
                # point: past ten minutes on twelve names, twice.
                r0 = y - (d["g"] * x + d["c"])
                if (r0 < -touch_tol) if kd == "support" else (r0 > touch_tol):
                    break
                if abs(r0) > touch_tol:
                    continue
            elif abs(y - (d["g"] * x + d["c"])) > tol:
                why["walk_prox_stop"] += 1
                break                               # it does not belong to this trend (S2)
            # THE TRIAL, IN BAR ORDER (D1): the point goes where its bar puts it, and the line's
            # origin is the earliest point in the fit, not the point just added
            fx, fy = fit_pts(d)
            p = bisect.bisect_left(fx, x)
            tx, ty = fx[:p] + [x] + fx[p:], fy[:p] + [y] + fy[p:]
            g, c_raw, tn = fit(tx, ty, kd, t)
            if not np.isfinite(g):
                break
            s0 = int(tx[0])
            c = place(g, c_raw, s0, t, kd, tx, ty)
            if not np.isfinite(c):
                break
            if not spans_bodies(g, c, s0, t, kd):
                why["walk_span_stop"] += 1
                break                               # the line it makes cuts a candle
            if not fits_pivots(g, c, tx, ty):
                why["walk_unfit_stop"] += 1
                break                               # the line it makes no longer sits on its pivots
            q = bisect.bisect_left(d["bx"], x)
            d["bx"].insert(q, x)
            d["by"].insert(q, y)
            d["walked"].add(x)
            d["g"], d["c"], d["c_raw"], d["s0"], d["touch"] = g, c, c_raw, s0, tn
            d["ver"] += 1                         # a point was inserted
            d["reached"] += 1
            have.add(x)
        if d["reached"]:
            why["extended"] += 1
            why["extended_pts"] += d["reached"]
            ev(t, kd, "extended")
            for _ in range(d["reached"]):
                ev(t, kd, "extended_pt")

    for t in range(m):
        broke = {"support": None, "resistance": None}
        for kd in ("support", "resistance"):
            d = st[kd]
            fresh = False
            while d["ptr"] < d["idx"].size and d["idx"][d["ptr"]] <= t - k:
                bar = int(d["idx"][d["ptr"]])
                # RATIFIED: the detector found a real pivot at the provisional point's own bar.
                # Drop the provisional copy so the same bar is never weighted twice in the fit.
                if d["syn"] is not None and int(d["syn"][0]) == bar:
                    d["syn"] = None
                    why["syn_confirmed"] += 1
                    ev(t, kd, "syn_confirmed")
                d["bx"].append(float(bar))
                d["by"].append(float(d["lp"][d["ptr"]]))
                d["ptr"] += 1
                d["ver"] += 1                     # the fit's inputs changed
                fresh = True
            # FORGET THE OLDEST beyond `max_piv`: the fit is the newest N pivots and no more
            if max_piv is not None and len(d["bx"]) > max_piv:
                n_drop = len(d["bx"]) - max_piv
                gone = d["bx"][:n_drop]
                d["bx"] = d["bx"][n_drop:]
                d["by"] = d["by"][n_drop:]
                d["walked"] -= set(gone)
                d["ver"] += 1
                why["max_piv_drop"] += n_drop
            # FALSIFIED (S4): the detector has now seen every bar it needs to rule on the
            # provisional's bar, and it did not confirm it. The line that rested on it goes
            # dormant -- there is no new information to refit on, only a point withdrawn.
            if syn_ttl and d["syn"] is not None and d["syn"][0] <= t - k:
                d["syn"] = None
                d["ver"] += 1
                why["syn_dropped"] += 1
                ev(t, kd, "syn_dropped")
                go_dormant(d)
            if fresh and d["dormant"]:
                d["dormant"] = False          # new information: a line may be drawn again
                refit(d, t, kd)
            # THE BUFFER INVARIANTS, checked whenever it changed (D1, D2)
            if d["chk_ver"] != d["ver"]:
                _check_sorted(d["bx"], f"{kd} buffer at bar {t}")
                if d["syn"] is not None and d["syn"][0] in d["bx"]:
                    raise AssertionError(
                        f"[S] {kd} bar {t}: provisional at bar {int(d['syn'][0])} duplicates a "
                        f"confirmed pivot in the buffer")
                d["chk_ver"] = d["ver"]
            if d["dormant"] or npiv(d) < 2:
                continue
            if npiv(d) > why["max_buf"]:
                why["max_buf"] = npiv(d)          # the envelope is O(n^3) in this; watch it
            # HOISTED, NOT APPROXIMATED. The candidate fit depends only on the buffer and the
            # provisional pivot, and `ver` moves on every mutation of either -- so between
            # mutations the answer cannot differ and is not recomputed. Called once per BAR this
            # was the whole cost: an O(n^3) envelope fit 4,000 times a side for a buffer that
            # changes ~1,500 times. Same inputs, same call, same output, bit for bit.
            if d["fit_ver"] != d["ver"] or fit_depends_on_t:
                fx, fy = fit_pts(d)
                d["fit_now"] = fit(fx, fy, kd, t)
                d["fit_ver"] = d["ver"]
            g_now, a_now, _tn = d["fit_now"]
            if not np.isfinite(g_now):
                why["nan_fit"] += 1               # S6: counted, and no longer a free pass (D3)
            if not np.isfinite(d["g"]):
                if np.isfinite(g_now):
                    refit(d, t, kd)
                continue
            lvl = d["g"] * t + d["c"]
            ref = lvl if height_mode == "anchored" else d["g"] * t + d["c_raw"]
            bad = None
            # the gradient and height tests need the CANDIDATE fit; the body test needs only the
            # frozen line, and a bar the candidate cannot be fitted on is still a bar a body can
            # close through (D3)
            if np.isfinite(g_now):
                if abs(g_now - d["g"]) > max_dg:
                    bad = "gradient"
                elif abs((g_now * t + a_now) - ref) > max_dh:
                    bad = "height"
            if bad is None and use_body and np.isfinite(lvl):
                b = body_log[kd][t]
                through = np.isfinite(b) and ((b < lvl - break_depth) if kd == "support"
                                              else (b > lvl + break_depth))
                # depth AND persistence: the close must be beyond the tolerance, and must have
                # been so on `break_bars` consecutive bars of this line's life
                d["thru"] = d["thru"] + 1 if through else 0
                if through and d["thru"] >= break_bars:
                    bad = "body"
                elif through or (np.isfinite(b) and ((b < lvl) if kd == "support" else (b > lvl))):
                    why["body_poke"] += 1
                    ev(t, kd, "body_poke")
            if bad is None and stale_w is not None and np.isfinite(lvl):
                # IS PRICE STILL RESPECTING THE LINE? The offset of the last W bars' extremes
                # from the frozen line; every bar in the window is closed and known at t.
                a = max(0, t - int(stale_w) + 1)
                q = np.arange(a, t + 1, dtype=float)
                e = ext_log[kd][a:t + 1]
                lv = d["g"] * q + d["c"]
                off = (e - lv) if kd == "support" else (lv - e)
                off = off[np.isfinite(off)]
                if off.size:
                    stat = float(off.mean()) if stale_stat == "mean" else float(off.min())
                    if stat > stale_d:
                        bad = "stale"
                        # the split: respected-then-left, or never confirmed at all
                        kk = "stale_abandoned" if d["touched"] else "stale_unconfirmed"
                        why[kk] += 1
                        ev(t, kd, kk)
            if bad is not None:
                why[bad] += 1
                ev(t, kd, bad)
                broke[kd] = bad
                ns = None
                if bad == "body" and break_pivot and ext_log is not None:
                    e = ext_log[kd][t]
                    if np.isfinite(e):
                        ns = (float(t), float(e))
                reset(d, t, kd, bad, ns)

        # ONE BROKEN, BOTH BROKEN. The partner of a side that was invalidated this bar is reset
        # too, unless it was invalidated on its own account already.
        if pair_break:
            for kd, other in (("support", "resistance"), ("resistance", "support")):
                if broke[kd] is not None and broke[other] is None:
                    why["pair"] += 1
                    ev(t, other, "pair")
                    reset(st[other], t, other, "pair")
                    broke[other] = "pair"

        # THE PAIR TEST, after both sides have settled for this bar
        ds, dr = st["support"], st["resistance"]
        if np.isfinite(ds["g"]) and np.isfinite(ds["c"]) and np.isfinite(dr["g"]) \
                and np.isfinite(dr["c"]):
            ls, lr = ds["g"] * t + ds["c"], dr["g"] * t + dr["c"]
            if lr - ls < min_width:
                why["inverted"] += 1
                ev(t, "pair", "inverted")
                reset(ds, t, "support", "inverted")
                reset(dr, t, "resistance", "inverted")

        # AND THE GUARD AT EMISSION. Resetting both sides refits them from `carry` pivots each,
        # and that refit can be inverted all over again -- which is exactly how 21 inverted bars
        # survived the invalidator above. A pair that is still crossed is NOT DRAWN AT ALL: both
        # sides report no trend for this bar rather than one of them reporting nonsense.
        ok = {}
        for kd in ("support", "resistance"):
            d = st[kd]
            # THE WALK RUNS ONCE, the first bar the new segment would qualify: with fewer points
            # than that its direction is too noisy to test the past against. Under `syn_ttl` it
            # also waits for the provisional to be ruled on, so no old point is ever accepted
            # against a line the next bar withdraws.
            if extend_back and d["pending"] and not d["dormant"] and np.isfinite(d["g"]) \
                    and npiv(d) >= min_piv + need(d) and (not syn_ttl or d["syn"] is None):
                walk_back(d, t, kd)
            # min_piv + need: a segment opened by a break carries a PROVISIONAL point toward its
            # pivot count, so it has to clear one more than an ordinary segment
            ok[kd] = (not d["dormant"] and np.isfinite(d["g"]) and np.isfinite(d["c"])
                      and npiv(d) >= min_piv + need(d)
                      and not (gate and abs(d["g"]) <= delta)
                      # an envelope line is REAL when enough pivots touch it -- the chartist's
                      # own criterion, and the count the edge was chosen by
                      and (fit_mode != "envelope" or d["touch"] >= min_touch))
            # AND THE SAME GUARD THE BODY TEST NEEDED ALL ALONG. The test fires BEFORE the reset,
            # so whatever the refit produced was being drawn unchecked -- 18% of emitted support
            # bars ran through the body in the cell whose whole point is the body.
            if ok[kd] and use_body:
                lv = d["g"] * t + d["c"]
                b = body_log[kd][t]
                if np.isfinite(b) and ((b < lv - break_depth) if kd == "support"
                                       else (b > lv + break_depth)):
                    ok[kd] = False
        if ok["support"] and ok["resistance"]:
            ls = st["support"]["g"] * t + st["support"]["c"]
            lr = st["resistance"]["g"] * t + st["resistance"]["c"]
            if lr - ls < min_width:
                ok["support"] = ok["resistance"] = False
        # THE CHANNEL OR NOTHING: a side that qualifies alone is not drawn
        if pair_draw and ok["support"] != ok["resistance"]:
            why["pair_hidden"] += 1
            ok["support"] = ok["resistance"] = False
        for kd in ("support", "resistance"):
            if not ok[kd]:
                continue
            d = st[kd]
            G[kd][t] = d["g"]
            L[kd][t] = d["g"] * t + d["c"]
            S[kd][t] = d["s0"]
            # the line's biography, for the staleness split: first drawn here, and respected
            # once a LATER bar comes within stale_d of it
            if d["born"] is None:
                d["born"] = t
            elif ext_log is not None and not d["touched"]:
                o = offset(d["g"], d["c"], t, kd)
                if np.isfinite(o) and abs(o) <= stale_d:
                    d["touched"] = True
    why["events"] = events
    return G, L, S, why


def assert_no_resurrection(G, L, S, body_log, window=None, tol=0.0, bars=1):
    """[Z] A LINE A BODY CLOSED THROUGH IS NEVER DRAWN AGAIN.

    The review found 66 bars where a body closed through a live frozen line while the candidate
    fit was nan, the test was skipped, and on 5 of them the same line came back afterwards (BRO
    resistance, s0 3336: through at 3351, redrawn 3356-3429). This reads the OUTPUT only: every
    drawn line is identified by (s0, gradient, intercept); between the first and last bar it is
    drawn, no body may sit through it. A line killed at t2 and rebuilt identically at t3 would
    fail this too -- which is the livelock the dormancy rule exists to prevent."""
    n_lines = 0
    for kd in ("support", "resistance"):
        on = np.isfinite(L[kd])
        if window is not None:
            on &= window
        idx = np.flatnonzero(on)
        if idx.size == 0:
            continue
        cc = L[kd][idx] - G[kd][idx] * idx
        span, exact = {}, {}
        for j, t in enumerate(idx):
            # grouped on a ROUNDED intercept (the recovered c differs by ULPs bar to bar),
            # evaluated on the exact one -- drawing from the rounded key put the line 5e-9 off
            # and this audit fired on its own rounding at the emission bar
            key = (int(S[kd][t]), float(G[kd][t]), round(float(cc[j]), 8))
            a, b = span.get(key, (t, t))
            span[key] = (min(a, t), max(b, t))
            exact.setdefault(key, float(cc[j]))
        for (s0, g, _cr), (a, b) in span.items():
            c = exact[(s0, g, _cr)]
            q = np.arange(a, b + 1, dtype=float)
            lv = g * q + c
            bo = body_log[kd][a:b + 1]
            fin = np.isfinite(bo)
            deep = np.zeros(q.size, bool)
            deep[fin] = ((bo[fin] < lv[fin] - tol - 1e-9) if kd == "support"
                         else (bo[fin] > lv[fin] + tol + 1e-9))
            # a break needs `bars` CONSECUTIVE closes beyond the depth: a shorter run is a
            # pullback the line is meant to survive, so only a run of that length convicts
            run, worst, at = 0, 0, -1
            for j in range(q.size):
                run = run + 1 if deep[j] else 0
                if run > worst:
                    worst, at = run, j
            if worst >= bars:
                tb = a + at
                raise AssertionError(
                    f"[Z] {kd} line from pivot {s0} (g={g:+.5f}) drawn at {a} and again at {b}, "
                    f"but a body closed through it at bar {tb}")
            n_lines += 1
    return n_lines


def assert_respects_body(L, body_log, window, tol=0.0):
    """[R] A LINE DRAWN UNDER `use_body` MAY NOT RUN THROUGH THE BODY -- by more than `tol`, the
    break depth, once a break needs depth. The invalidator alone did not deliver this -- it fires
    before the reset, and the refit was drawn unchecked."""
    n_ok = 0
    for kd in ("support", "resistance"):
        on = np.isfinite(L[kd]) & window
        if not on.any():
            continue
        lv, b = L[kd][on], body_log[kd][on]
        bad = (b < lv - tol - 1e-12) if kd == "support" else (b > lv + tol + 1e-12)
        if bad.any():
            i = int(np.flatnonzero(on)[int(np.flatnonzero(bad)[0])])
            raise AssertionError(
                f"[R] {kd} runs through the body at bar {i}: line {np.exp(L[kd][i]):.4f} vs body "
                f"{np.exp(body_log[kd][i]):.4f} ({int(bad.sum())} bars)")
        n_ok += int(on.sum())
    return n_ok


def assert_no_inversion(L, window, min_width=0.0):
    """[C] SUPPORT MAY NOT SIT ABOVE RESISTANCE. Asserted wherever both lines are drawn."""
    both = np.isfinite(L["support"]) & np.isfinite(L["resistance"]) & window
    if not both.any():
        return 0
    gap = L["resistance"][both] - L["support"][both]
    if (gap < min_width - 1e-12).any():
        i = int(np.flatnonzero(both)[int(np.argmin(gap))])
        raise AssertionError(
            f"[C] inverted channel at bar {i}: support {np.exp(L['support'][i]):.4f} vs "
            f"resistance {np.exp(L['resistance'][i]):.4f} -- {int((gap < min_width).sum())} bars")
    return int(both.sum())


def recalc_events(pidx, ppx, k, body_log, kind, m, carry, min_piv, max_dg, max_dh,
                  use_body, delta, gate=True):
    """NO RATCHET ANYWHERE. The line is the OLS fit -- gradient AND intercept -- frozen at the bar
    its segment opened. Nothing ever slides it.

    It ends when the fit it was taken from has moved too far away from it, on either quantity:

        |g_now      - g_seg     |  > max_dg      the GRADIENT has drifted past its deadband
        |line_now(t) - line_seg(t)| > max_dh     the HEIGHT has drifted past its deadband

    where `now` is the OLS fit over every pivot confirmed so far in this segment and `seg` is the
    fit frozen when it opened. On either, the segment is invalidated and RECALCULATED from the
    surviving `carry` pivots -- a new gradient and a new height together.

    `use_body` adds the principal's earlier rule as a third invalidator (a body closing through the
    line) and is a declared axis, not part of the mechanism: the grid says whether it earns a place
    beside the two deltas.

    Returns (G, L, SEG, why) -- per-bar gradient, per-bar level in LOG price, segment id, and the
    count of what fired."""
    G = np.full(m, np.nan)
    L = np.full(m, np.nan)
    SEG = np.full(m, -1, int)
    why = {"gradient": 0, "height": 0, "body": 0}
    order = np.argsort(pidx, kind="stable")
    pidx = np.asarray(pidx, int)[order]
    ppx = np.asarray(ppx, float)[order]

    ptr = 0
    buf_x, buf_y = [], []
    g_seg = c_seg = np.nan
    seg_start = -1

    for t in range(m):
        # absorb every pivot the D173 lag says is knowable by now
        while ptr < pidx.size and pidx[ptr] <= t - k:
            buf_x.append(float(pidx[ptr]))
            buf_y.append(float(ppx[ptr]))
            ptr += 1
        if len(buf_x) < 2:
            continue
        g_now, a_now = ols(buf_x, buf_y)
        if not np.isfinite(g_now):
            continue

        if not np.isfinite(g_seg):                       # open the first segment
            seg_start = int(buf_x[0])
            g_seg, c_seg = g_now, a_now
        else:
            lvl_seg = g_seg * t + c_seg                  # frozen when the segment opened
            bad = None
            if abs(g_now - g_seg) > max_dg:
                bad = "gradient"
            elif abs((g_now * t + a_now) - lvl_seg) > max_dh:
                bad = "height"
            elif use_body and np.isfinite(lvl_seg):
                b = body_log[t]
                if np.isfinite(b) and ((b < lvl_seg) if kind == "support" else (b > lvl_seg)):
                    bad = "body"
            if bad is not None:
                why[bad] += 1
                buf_x = buf_x[-carry:] if carry > 0 else []
                buf_y = buf_y[-carry:] if carry > 0 else []
                seg_start = int(buf_x[0]) if buf_x else t
                g_seg, c_seg = ols(buf_x, buf_y) if len(buf_x) >= 2 else (np.nan, np.nan)
                if not np.isfinite(g_seg):
                    continue

        if not (np.isfinite(g_seg) and np.isfinite(c_seg)):
            continue
        if len(buf_x) < min_piv:
            continue
        if gate and abs(g_seg) <= delta:
            continue
        G[t] = g_seg
        L[t] = g_seg * t + c_seg
        SEG[t] = seg_start
    return G, L, SEG, why


# --------------------------------------------------------------------------
# audits
# --------------------------------------------------------------------------


def audit_decay(seed=20260910, draws=200):
    """[W] THE AGE WEIGHT IS A SUPERSET, NOT A REPLACEMENT.

    decay_end = 1.0 must return `ols` bit-identically on random point sets -- it is the control
    every decayed number is read against, and if it drifted by one ULP the comparison would be
    meaningless. decay_end = 0.9 must then DIFFER, or the parameter is decorative.

    Also checks the weight actually lands where it was asked to: the oldest pivot's weight is
    `decay_end` and the newest's is exactly 1."""
    rng = np.random.default_rng([seed, 1])
    same = moved = 0
    for _ in range(draws):
        n = int(rng.integers(2, 12))
        x = np.sort(rng.choice(np.arange(0, 400), size=n, replace=False)).astype(float)
        y = rng.normal(0.0, 1.0, size=n)
        a1, b1 = ols(x, y)
        a2, b2 = wls(x, y, 1.0)
        assert (a1 == a2 or (np.isnan(a1) and np.isnan(a2))), "[W] decay_end=1.0 moved the slope"
        assert (b1 == b2 or (np.isnan(b1) and np.isnan(b2))), "[W] decay_end=1.0 moved the intercept"
        same += 1
        a3, _b3 = wls(x, y, 0.9)
        if np.isfinite(a1) and np.isfinite(a3) and a1 != a3:
            moved += 1
    assert moved > 0, "[W] SELF-TEST FAILED: decay_end=0.9 changed nothing"
    # the weight the caller asked for is the weight the oldest point gets
    x = np.array([10.0, 25.0, 61.0, 77.0])
    span = x[-1] - x[0]
    w = np.power(0.9, (x[-1] - x) / span)
    assert abs(w[0] - 0.9) < 1e-12 and abs(w[-1] - 1.0) < 1e-12, (
        f"[W] the end weights are {w[0]:.6f} and {w[-1]:.6f}, asked for 0.9 and 1.0")
    return same, moved


def audit_scorer_control(h, tl):
    """[B] pos_weight=0 must reproduce the published causal score to the recorded digit."""
    cfg = dict(mode="abs", tau=SV.INC_TAU, floor=0.0, conf_mult=1.0,
               carry=SV.INC_CARRY, min_piv=SV.INC_MINPIV, gate=SV.INC_GATE)
    Gs = h.grads(cfg, strict=True)     # pinned to the strict pivots that produced 0.3175
    sc = []
    for kd in ("support", "resistance"):
        gf = Gs[kd][h.start:h.start + h.n]
        s = score_side_pos(gf, np.full(h.n, np.nan), tl[kd][1], tl[kd][0], h.seen, h.delta,
                           pos_weight=0.0)
        sc.append(s["score"])
    got = round(float(np.mean(sc)), 4)
    assert got == PUBLISHED_CAUSAL, (
        f"[B] pos_weight=0 scores {got}, published {PUBLISHED_CAUSAL} -- the new scorer is not a "
        f"superset of the old one")
    return got


def _pivots_of(bars, k, PVT):
    """The construction's pivot inputs from a bar list -- the same call `d399_new_sample.run_one`
    makes, so the truncated rebuild below is built the way the record is."""
    ps = PVT(bars, k)
    piv = {}
    for kd, sg in (("support", -1), ("resistance", +1)):
        idx = np.array([p.index for p in ps if p.sign == sg], dtype=int)
        lp = np.log(np.array([p.price for p in ps if p.sign == sg], float))
        piv[kd] = (idx, lp)
    return piv


def audit_causal(h, body_log, ext_log, cfg, probe, PVT):
    """[L] Re-derive the line at sampled bars from a SECOND path: cut the BARS to [0, t], rebuild
    every input from that truncation -- pivots, bodies, extremes -- and run `recalc_pair` again.
    Gradient, level AND origin at t must be bit-identical on both sides. Then prove the audit
    RAISES on a k=0 build, and that it compared something.

    This targets `recalc_pair`. The earlier version of this audit exercised `recalc_events`, a
    superseded single-side builder nothing else calls -- the construction that shipped had never
    been under it (review)."""
    G, L, S, _w = recalc_pair(h.piv, h.k, body_log, h.m, ext_log=ext_log, **cfg)
    checked = 0
    for t in probe:
        if not (np.isfinite(G["support"][t]) or np.isfinite(G["resistance"][t])):
            continue
        bars = h.bars[:t + 1]                        # the future deleted outright
        piv2 = _pivots_of(bars, h.k, PVT)
        body2 = {kd: body_log[kd][:t + 1].copy() for kd in body_log}
        ext2 = {kd: ext_log[kd][:t + 1].copy() for kd in ext_log}
        G2, L2, S2, _w2 = recalc_pair(piv2, h.k, body2, t + 1, ext_log=ext2, **cfg)
        for kd in ("support", "resistance"):
            a, b = G[kd][t], G2[kd][t]
            same = (np.isnan(a) and np.isnan(b)) or (a == b and L[kd][t] == L2[kd][t]
                                                     and S[kd][t] == S2[kd][t])
            if not same:
                raise AssertionError(
                    f"[L] {kd} bar {t}: forward walk says g={a!r} level={L[kd][t]!r} "
                    f"s0={S[kd][t]}, the truncated rebuild says g={b!r} level={L2[kd][t]!r} "
                    f"s0={S2[kd][t]} -- the construction reads the future")
            if np.isfinite(a):
                checked += 1
    # the self-test: a k=0 build -- the SAME pivots, each used on the bar it happens instead of
    # k bars later -- must NOT reproduce the lagged one. (The detector itself refuses k=0.)
    Gb, _l2, _s2, _w2 = recalc_pair(h.piv, 0, body_log, h.m, ext_log=ext_log, **cfg)
    assert not np.array_equal(G["support"], Gb["support"], equal_nan=True), (
        "[L] SELF-TEST FAILED: the k=0 leaked build is identical to the lagged one, so the audit "
        "above proves nothing")
    # AN AUDIT THAT CHECKED NOTHING PASSED ONCE ALREADY IN THIS FILE. min_piv=5 against a per-bar
    # invalidation leaves the buffer permanently short, G is nan everywhere, every probe bar is
    # skipped, and the lag audit reports OK on zero comparisons.
    assert checked >= len(probe), (
        f"[L] VACUOUS: only {checked} side-bars carried a gradient, out of {2 * len(probe)} "
        f"probed. The audit passed by checking nothing -- fix the cell, not the assertion")
    return checked


def audit_envelope(seed=20260910, draws=400):
    """[V] THE HULL IS THE PAIR ENUMERATION IT REPLACED, where the two are defined to agree.

    `envelope_fit` (monotone chain, O(n log n)) against `_envelope_fit_loop` (every pair, O(n^3))
    at tol = 1e-12, on TIE-HEAVY inputs: y drawn from six dyadic levels so equal lows are the
    rule, and an exactly collinear triple planted in half the draws (midpoint x on an even span,
    dyadic y -- exact in floats). Ties and collinear runs are where the two can disagree (the
    hull drops a collinear middle with EPS = 1e-9; the loop keeps it as a touch), and the
    assertion is bit-identity of (g, c, touches), not closeness.

    Then the self-test: the same comparison with the hull on the WRONG side must fail, or the
    audit is not reading the result."""
    rng = np.random.default_rng([seed, 2])
    TOL = 1e-12
    same = n_edges = n_collinear = 0
    for _ in range(draws):
        n = int(rng.integers(2, 14))
        x = np.sort(rng.choice(np.arange(0, 120), size=n, replace=False)).astype(float)
        y = rng.integers(0, 6, size=n) / 8.0
        if n >= 3 and rng.random() < 0.5:
            i = int(rng.integers(0, n - 2))
            if (x[i + 2] - x[i]) % 2 == 0:
                x[i + 1] = (x[i] + x[i + 2]) / 2.0
                y[i + 1] = (y[i] + y[i + 2]) / 2.0
                if np.unique(x).size == n:
                    n_collinear += 1
                else:
                    continue
        for kind in ("support", "resistance"):
            a = envelope_fit(x, y, kind, TOL)
            b = _envelope_fit_loop(x, y, kind, TOL)
            ok = all((np.isnan(u) and np.isnan(v)) or u == v for u, v in zip(a[:2], b[:2])) \
                and a[2] == b[2]
            assert ok, (f"[V] hull {a} != pair enumeration {b} on {kind} x={x.tolist()} "
                        f"y={y.tolist()}")
            same += 1
            n_edges += int(a[2] >= 3)
    assert n_collinear >= 20 and n_edges >= 100, (
        f"[V] VACUOUS: {n_collinear} collinear plants, {n_edges} three-touch edges")
    # the self-test: the audit must be able to fail
    x = np.array([0.0, 10.0, 20.0, 30.0])
    y = np.array([0.0, 0.5, 0.0, 0.5])
    a = envelope_fit(x, y, "support", TOL)
    b = _envelope_fit_loop(x, y, "resistance", TOL)
    assert not (a[0] == b[0] and a[1] == b[1] and a[2] == b[2]), (
        "[V] SELF-TEST FAILED: the lower hull equals the upper pair enumeration")
    return same, n_collinear


def audit_envelope_age(seed=20260910, draws=400):
    """[A] THE ENVELOPE'S AGE WEIGHT IS A SUPERSET, NOT A REPLACEMENT.

    decay_end = 1.0 must return the unweighted choice bit-identically on tie-heavy draws (the
    control every weighted number is read against); decay_end = 0.8 must then CHANGE the chosen
    edge on some of them, or the dial is decorative; and the returned touch count must be the
    plain count in both cases. Then the self-test: a hand-built case where a long old edge and a
    short recent edge tie on two touches each, and 0.8 must pick the recent one."""
    rng = np.random.default_rng([seed, 3])
    same = moved = 0
    for _ in range(draws):
        n = int(rng.integers(3, 14))
        x = np.sort(rng.choice(np.arange(0, 120), size=n, replace=False)).astype(float)
        y = rng.integers(0, 6, size=n) / 8.0
        for kind in ("support", "resistance"):
            a = envelope_fit(x, y, kind, 1e-12)
            b = envelope_fit(x, y, kind, 1e-12, 1.0)
            assert all((np.isnan(u) and np.isnan(v)) or u == v for u, v in zip(a, b)), (
                f"[A] decay_end=1.0 is not the unweighted envelope on x={x.tolist()}")
            same += 1
            c = envelope_fit(x, y, kind, 1e-12, 0.8)
            assert c[2] == int(c[2]) and (np.isnan(c[0]) or c[2] >= 2), "[A] touches not a count"
            if np.isfinite(a[0]) and np.isfinite(c[0]) and (a[0] != c[0] or a[1] != c[1]):
                moved += 1
    assert moved > 0, "[A] SELF-TEST FAILED: decay_end=0.8 never changed the chosen edge"
    # the lower hull has two edges, two touches each and the same 40-bar span: the old one (0,40)
    # and the recent one (40,80). Unweighted they tie on touches and span and the FIRST wins. At
    # 0.8 the recent pair weighs 0.8**(40/80)+1 = 1.894 against 0.8+0.8**(40/80) = 1.694, so the
    # recent edge wins. (The first draft of this case put the "recent edge" on (60,80), which is
    # not a support line at all -- the pivot at (40,0) sits below it -- and the test failed on
    # its own geometry, not on the code.)
    x = np.array([0.0, 20.0, 40.0, 60.0, 80.0])
    y = np.array([0.0, 0.5, 0.0, 0.25, 0.25])
    g1, c1, _t1 = envelope_fit(x, y, "support", 1e-12, 1.0)
    g8, c8, t8 = envelope_fit(x, y, "support", 1e-12, 0.8)
    assert g1 == 0.0 and c1 == 0.0, f"[A] SELF-TEST FAILED: unweighted picked g={g1} c={c1}"
    assert g8 == 0.25 / 40 and c8 == -0.25 and t8 == 2, (
        f"[A] SELF-TEST FAILED: weighted picked g={g8} c={c8} touches={t8}, want the (40,80) edge")
    return same, moved


def audit_sorted():
    """[S] the order guard must RAISE, in both places it is installed."""
    fired = 0
    for bad in ([1.0, 3.0, 2.0], [1.0, 2.0, 2.0]):
        try:
            _check_sorted(bad, "self-test")
        except AssertionError:
            fired += 1
    # `wls` sees only its END POINTS: [5, 3, 9] has a positive span and passes it, which is
    # exactly why `_check_sorted` guards every fit and `wls` is only the backstop
    try:
        wls([9.0, 3.0, 5.0], [0.1, 0.2, 0.3], 0.8)
    except ValueError:
        fired += 1
    assert fired == 3, f"[S] SELF-TEST FAILED: only {fired} of 3 bad inputs raised"
    _check_sorted([1.0, 2.0, 5.0], "self-test")      # and a good one passes
    return fired


# --------------------------------------------------------------------------
# the grid
# --------------------------------------------------------------------------

# Both deltas carry a None = NEVER level, so the grid contains all four corners: neither test,
# gradient only, height only, both. Without that the two cannot be told apart -- the first pass
# ran dh at 5-40% and the height test fired ONCE in 96 cells, because with an OLS intercept a
# level move is just the gradient move times the distance from the fit's centroid, so gradient
# always tripped first. The dh range below is an order of magnitude tighter for that reason.
DG_ANNUAL = [4.0, 8.0, 16.0, 32.0, None]   # max gradient delta, annualised percentage points
DH_PCT = [0.5, 1.0, 2.0, 5.0, None]        # max height delta, per cent of price
USE_BODY = [False, True]
MIN_PIVS = [3, 4, 5]
MIN_WIDTH_PCT = [0.0, 5.0]   # 0 forbids only the crossing; 5 demands a channel at least 5% wide
BREAK_PIVOT = [False, True]  # does the breaking bar become a provisional pivot? False is the control
CARRY = 3
INF = float("inf")


def _cell(h, tl, key, blurb, label, note, G, L, S, sl, pos_weight, body_lo, body_hi, lo, hi, n):
    """Pack one construction into the shape scripts/d399_splice_signed_vol_page.py reads."""
    out = dict(key=key, blurb=blurb, label=label, note=note)
    lines, anch, anch1, place, place_a, cuts, grads, nbrk, nlive, parts = (
        {}, {}, {}, {}, {}, {}, {}, {}, {}, {})
    sc = []
    for kd in ("support", "resistance"):
        with np.errstate(over="ignore"):
            px = np.exp(L[kd][sl])
        st = score_side_pos(G[kd][sl], px, tl[kd][1], tl[kd][0], h.seen, h.delta,
                            pos_weight=pos_weight)
        sc.append(st["score"])
        parts[kd] = {k2: st[k2] for k2 in ("TP", "FP", "FN", "precision", "recall", "quality",
                                           "q_grad", "q_level", "score")}
        f = lambda v: [None if not np.isfinite(x) else float(x) for x in v]      # noqa: E731
        lines[kd] = f(px)
        anch[kd] = f(px)                     # already the construction's own line
        anch1[kd] = f(px)
        ref = lo if kd == "support" else hi
        place[kd] = SV.placement(px, ref)
        place_a[kd] = place[kd]
        grads[kd] = f(G[kd][sl])
        seg = S[kd][sl]
        cuts[kd] = [int(i) for i in range(1, n) if seg[i] >= 0 and seg[i] != seg[i - 1]]

        # EACH SEGMENT AS ITS OWN STRAIGHT LINE, ANCHORED AT ITS FIRST PIVOT.
        # The per-bar arrays above only carry the line where the state is EMITTED, which is after
        # min_piv is met -- so the drawn line starts some way after the pivots it was fitted to,
        # and you cannot see what it is anchored on. `s0` is the first x in the fit set, so the
        # segment is emitted here from s0 forward, with `t0` marking where emission actually
        # began. The scored arrays are NOT changed: `support`/`resistance` stay exactly as
        # scored, and only the drawing gains the earlier stretch.
        segs, i = [], 0
        while i < n:
            if not (np.isfinite(px[i]) and seg[i] >= 0):
                i += 1
                continue
            j = i
            while j + 1 < n and seg[j + 1] == seg[i] and np.isfinite(px[j + 1]):
                j += 1
            g = float(G[kd][sl][i])
            c = float(L[kd][sl][i]) - g * (i + h.start)          # log-space intercept
            a = int(seg[i]) - h.start                            # first pivot, window coords
            if np.isfinite(g) and np.isfinite(c):
                segs.append(dict(s0=a, t0=int(i), t1=int(j), g=g, c=c,
                                 anchored_before=bool(a < i)))
            i = j + 1
        out.setdefault("segments", {})[kd] = segs
        bref = body_lo if kd == "support" else body_hi
        liv = np.isfinite(px)
        brk = (px > bref) if kd == "support" else (px < bref)
        nbrk[kd] = int((brk & liv).sum())
        nlive[kd] = int(liv.sum())
        back = (np.arange(n) - np.where(seg >= 0, seg - h.start, np.nan))[liv & (seg >= 0)]
        out.setdefault("reach_bars", {})[kd] = (int(np.nanmedian(back))
                                                if back.size and np.isfinite(back).any() else None)
    out.update(SCORE=round(float(np.mean(sc)), 4), support=lines["support"],
               resistance=lines["resistance"], anchored=anch, anchored_lag1=anch1,
               g_support=grads["support"], g_resistance=grads["resistance"],
               cuts_support=cuts["support"], cuts_resistance=cuts["resistance"],
               n_cuts=len(cuts["support"]) + len(cuts["resistance"]),
               placement=place, placement_anchored=place_a, body_breaks=nbrk, live_bars=nlive,
               parts=parts)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--chart", action="store_true")
    ap.add_argument("--pos-weight", type=float, default=1.0)
    ap.add_argument("--k", type=int, default=None,
                    help="pivot half-width AND D173 lag; 2 or 3 (default 3)")
    ap.add_argument("--no-back-check", dest="back_check", action="store_false",
                    help="allow a fit whose back-projection cuts the bodies it was fitted to")
    ap.add_argument("--decay-end", type=float, default=1.0,
                    help="weight of the OLDEST pivot; the newest is always 1.0 (1.0 = no decay)")
    ap.add_argument("--anchor-clear", action="store_true",
                    help="keep the OLS gradient, take the intercept from body clearance")
    ap.add_argument("--chart-decay", action="store_true",
                    help="one panel per age weight, everything else frozen")
    ap.add_argument("--chart-one", action="store_true",
                    help="one cell only, for the gradient/offset track view")
    ap.add_argument("--dh", type=float, default=30.0,
                    help="height deadband in per cent, for --chart-one")
    ap.add_argument("--chart-deltas", action="store_true",
                    help="panels across the height deadband, on the SYN cell")
    ap.add_argument("--sweep-deltas", action="store_true",
                    help="the two deadbands only, on the principal's chosen SYN cell")
    a = ap.parse_args()

    t0 = time.time()
    h = SV.H(k=a.k)
    gt = h.gt
    tl = {kd: true_levels(gt, kd) for kd in ("support", "resistance")}
    print(f"\n  {h.sym} {h.m} bars in {time.time() - t0:.0f}s | ground truth bars "
          f"{h.first_seen}-{h.seen_to}")
    print(f"  [T] the drawn LEVEL is reconstructed for both sides and its per-bar gradient is "
          f"identical to the ground truth's own g_support / g_resistance  OK")

    op = np.array([b.bar.open for b in h.bars], float)
    cl = np.array([b.bar.close for b in h.bars], float)
    with np.errstate(divide="ignore"):
        body_log = {"support": np.log(np.minimum(op, cl)),
                    "resistance": np.log(np.maximum(op, cl))}
        # the PROVISIONAL pivot takes the bar's own extreme, priced the way every other pivot in
        # the series is priced -- the low for support, the high for resistance, wick not body
        ext_log = {"support": np.log(np.array([b.bar.low for b in h.bars], float)),
                   "resistance": np.log(np.array([b.bar.high for b in h.bars], float))}

    ws, wm = audit_decay()
    print(f"  [W] decay_end=1.0 is BIT-IDENTICAL to ols on {ws} random point sets, decay_end=0.9 "
          f"moves {wm} of them, and the oldest pivot's weight is exactly what was asked for  OK")
    got = audit_scorer_control(h, tl)
    print(f"  [B] the new scorer at pos_weight=0 reproduces the published causal {got}  OK")
    ns_ = audit_sorted()
    print(f"  [S] the bar-order guard raises on {ns_} of 3 unsorted inputs, in both `fit` and "
          f"`wls`  OK")
    vs, vc = audit_envelope()
    print(f"  [V] the hull envelope is BIT-IDENTICAL to the pair enumeration on {vs} tie-heavy "
          f"draws ({vc} with a planted collinear triple), and the audit fails on the wrong "
          f"side  OK")
    as_, am = audit_envelope_age()
    print(f"  [A] the envelope at decay_end=1.0 is BIT-IDENTICAL to the unweighted choice on "
          f"{as_} draws, 0.8 moves the chosen edge on {am} of them, touches stay a count, and "
          f"the hand-built tie goes to the recent edge  OK")

    # THE CHOSEN CELL, not a convenient one: k=1 tie-tolerant, dh 30%, dg off, body, mp 4,
    # provisional pivot, clearance intercept, decay 0.8, the walk, carry 3, review switches at
    # their defaults. [L] and [Z] are worth nothing on a cell nobody draws.
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT
    chosen = dict(carry=3, min_piv=4, max_dg=INF, max_dh=math.log1p(0.30), use_body=True,
                  min_width=0.0, delta=h.delta, break_pivot=True, anchor_clear=True,
                  decay_end=0.80, extend_back=True)
    probe = list(range(h.start, h.start + h.n, 23))
    nchk = audit_causal(h, body_log, ext_log, chosen, probe, PVT)
    print(f"  [L] {nchk} side-bars re-derived from a truncated rebuild -- bars cut at t, pivots "
          f"recomputed on the cut -- gradient, level and origin identical; and the k=0 build "
          f"differs  OK")
    Gz, Lz, Sz, wz = recalc_pair(h.piv, h.k, body_log, h.m, ext_log=ext_log, **chosen)
    nz = assert_no_resurrection(Gz, Lz, Sz, body_log)
    assert_respects_body(Lz, body_log, np.ones(h.m, bool))
    assert_no_inversion(Lz, np.ones(h.m, bool), 0.0)
    print(f"  [Z] {nz} drawn lines over all {h.m} bars, none drawn again after a body closed "
          f"through it; [R] and [C] hold on the whole series; nan candidate fits {wz['nan_fit']}, "
          f"provisionals {wz['syn_made']} made / {wz['syn_confirmed']} ratified / "
          f"{wz['syn_dropped']} dropped  OK")
    if a.selftest:
        return 0

    s, n = h.start, h.n
    sl = slice(s, s + n)
    win = np.zeros(h.m, bool)
    win[sl] = True

    # ---- REFERENCES, scored the SAME way. Without these the grid below is uninterpretable: the
    # published 0.3175 was gradient-only, and adding a position term lowers every score, so a
    # recalc cell can only be judged against the old constructions re-scored under the new rule.
    print(f"\n  THE OLD CONSTRUCTIONS, RE-SCORED WITH POSITION (pos_weight={a.pos_weight:g})")
    print(f"  {'construction':<42s} {'grad only':>10s} {'+position':>10s} {'q_lvl':>7s}")
    refs = []
    for nm, cfg, comb in (
            ("incumbent |r|>0.08, raw OLS line",
             dict(mode="abs", tau=SV.INC_TAU, floor=0.0, conf_mult=1.0, carry=SV.INC_CARRY,
                  min_piv=SV.INC_MINPIV, gate=SV.INC_GATE), None),
            ("channel yardstick, raw OLS line",
             dict(mode="chan", tau=0.20, floor=SV.SCALE_FLOOR, conf_mult=2.0, carry=SV.INC_CARRY,
                  min_piv=5, gate=SV.INC_GATE, share_cuts=False), None)):
        if "share_cuts" in cfg:
            il, ll = h.piv["support"]
            ih, lh = h.piv["resistance"]
            cev = SV.combined_events(il, ll, ih, lh, h.k, cfg["mode"], cfg["tau"], cfg["floor"],
                                     cfg["carry"], cfg["conf_mult"], h.rvol, nwin=50,
                                     share_cuts=cfg["share_cuts"], par_h=None)
            GL = {kd: SV.broadcast_combined(cev, kd, h.m, cfg["min_piv"], cfg["gate"], h.delta)
                  for kd in ("support", "resistance")}
        else:
            GL = {kd: SV.broadcast_line(h.events(kd, cfg), h.m, cfg["min_piv"], cfg["gate"],
                                        h.delta) for kd in ("support", "resistance")}
        g0, g1, lv = [], [], []
        for kd in ("support", "resistance"):
            G, LL, S = GL[kd]
            with np.errstate(over="ignore"):
                px = np.exp(LL[sl])
            st1 = score_side_pos(G[sl], px, tl[kd][1], tl[kd][0], h.seen, h.delta,
                                 pos_weight=a.pos_weight)
            st0 = score_side_pos(G[sl], px, tl[kd][1], tl[kd][0], h.seen, h.delta, pos_weight=0.0)
            g0.append(st0["score"]); g1.append(st1["score"]); lv.append(st1["q_level"] or 0.0)
        r = dict(name=nm, grad_only=round(float(np.mean(g0)), 4),
                 with_pos=round(float(np.mean(g1)), 4), q_level=round(float(np.mean(lv)), 4))
        refs.append(r)
        print(f"  {nm:<42s} {r['grad_only']:>10.4f} {r['with_pos']:>10.4f} {r['q_level']:>7.3f}")

    if a.sweep_deltas:
        # THE PRINCIPAL'S CELL, frozen except for the two deadbands. His pick sat at dh = 5%,
        # which was the LARGEST FINITE VALUE in the grid that produced it -- an optimum at the
        # edge of a grid is not an optimum, so both axes are extended well past it here.
        SW_DG = [8.0, 16.0, 32.0, 64.0, 128.0, None]
        SW_DH = [2.0, 5.0, 10.0, 20.0, 30.0, 40.0, 60.0, None]
        MP, MW = 4, 0.0
        print(f"\n  DELTA SWEEP on dg={SW_DG} %/yr x dh={SW_DH} %")
        print(f"  held: body=Y, break-pivot=ON, min_piv={MP}, min_width={MW:g}%, carry={CARRY} "
              f"-- {len(SW_DG) * len(SW_DH)} cells (R13)\n")
        tab, meta = {}, {}
        for dg in SW_DG:
            for dh in SW_DH:
                cfg = dict(carry=CARRY, min_piv=MP,
                           max_dg=(INF if dg is None else h.DR.h_of_annual(dg)),
                           max_dh=(INF if dh is None else math.log1p(dh / 100)),
                           use_body=True, min_width=math.log1p(MW / 100), delta=h.delta,
                           ext_log=ext_log, break_pivot=True)
                G, L, _S, w = recalc_pair(h.piv, h.k, body_log, h.m, **cfg)
                assert_no_inversion(L, win, cfg["min_width"])
                assert_respects_body(L, body_log, win)
                sc, cov = [], 0
                for kd in ("support", "resistance"):
                    with np.errstate(over="ignore"):
                        lvl = np.exp(L[kd][sl])
                    stt = score_side_pos(G[kd][sl], lvl, tl[kd][1], tl[kd][0], h.seen, h.delta,
                                         pos_weight=a.pos_weight)
                    sc.append(stt["score"])
                    cov += int(np.isfinite(G[kd][sl][h.seen]).sum())
                tab[(dg, dh)] = round(float(np.mean(sc)), 4)
                meta[(dg, dh)] = dict(cov=cov, fired=w["gradient"] + w["height"] + w["body"],
                                      syn=w["syn_made"], ok=w["syn_confirmed"])

        def hdr(vals, lab):
            return f"  {lab:<10s}" + "".join(
                f"{('off' if v is None else f'{v:g}%'):>9s}" for v in vals)

        print(f"  SCORE      (rows = max_dg, cols = max_dh)")
        print(hdr(SW_DH, "dg \\ dh"))
        for dg in SW_DG:
            row = "".join(f"{tab[(dg, dh)]:>9.4f}" for dh in SW_DH)
            print(f"  {('off' if dg is None else f'{dg:g}%/yr'):<10s}{row}")
        print(f"\n  BARS WITH A TREND, of {2 * int(h.seen.sum())} side-bars he saw")
        print(hdr(SW_DH, "dg \\ dh"))
        for dg in SW_DG:
            row = "".join(f"{meta[(dg, dh)]['cov']:>9d}" for dh in SW_DH)
            print(f"  {('off' if dg is None else f'{dg:g}%/yr'):<10s}{row}")
        print(f"\n  INVALIDATIONS over all {h.m} bars")
        print(hdr(SW_DH, "dg \\ dh"))
        for dg in SW_DG:
            row = "".join(f"{meta[(dg, dh)]['fired']:>9d}" for dh in SW_DH)
            print(f"  {('off' if dg is None else f'{dg:g}%/yr'):<10s}{row}")
        best = max(tab, key=lambda kk: tab[kk])
        mb = meta[best]
        print(f"\n  BEST {tab[best]:.4f} at dg={'off' if best[0] is None else f'{best[0]:g}%/yr'}, "
              f"dh={'off' if best[1] is None else f'{best[1]:g}%'}")
        print(f"    your cell (dg=off, dh=5%) scores {tab[(None, 5.0)]:.4f}")
        print(f"    provisional pivots {mb['syn']}, ratified {mb['ok']} "
              f"({100 * mb['ok'] / max(1, mb['syn']):.0f}%)")
        edge = [(g, d) for (g, d) in tab
                if tab[(g, d)] == tab[best] and (d == SW_DH[-2] or g == SW_DG[-2])]
        if edge:
            print(f"    NOTE: the best cell is still at a grid EDGE -- extend before believing it")
        P = REPO / "data" / "d399_delta_sweep.json"
        P.write_text(json.dumps(dict(
            what="D399: the two invalidation deadbands, on the principal's chosen SYN cell",
            held=dict(body=True, break_pivot=True, min_piv=MP, min_width_pct=MW, carry=CARRY),
            dg_annual=SW_DG, dh_pct=SW_DH,
            score={f"{g}|{d}": v for (g, d), v in tab.items()},
            detail={f"{g}|{d}": v for (g, d), v in meta.items()}), indent=1))
        print(f"\n  [P] {P.relative_to(REPO)} written")
        return 0

    if a.chart_one or a.chart_decay:
        a.chart_deltas = True
    if a.chart_deltas:
        a.chart = True
    if a.chart:
        op_w = np.array([b.bar.open for b in h.bars], float)[sl]
        cl_w = np.array([b.bar.close for b in h.bars], float)[sl]
        hi_w = np.array([b.bar.high for b in h.bars], float)[sl]
        lo_w = np.array([b.bar.low for b in h.bars], float)[sl]
        blo_w, bhi_w = np.minimum(op_w, cl_w), np.maximum(op_w, cl_w)
        cells = []
        # the two old constructions, drawn with the line the score now reads
        for key, blurb, cfg, anc, note in (
                ("ols", "The incumbent -- cut on a pivot's residual",
                 dict(mode="abs", tau=SV.INC_TAU, floor=0.0, conf_mult=1.0, carry=SV.INC_CARRY,
                      min_piv=SV.INC_MINPIV, gate=SV.INC_GATE), False,
                 "The line the published 0.3175 was really drawing. Scored on position it is "
                 "0.1717: level quality 0.417, so on average it sits well over half the 10% "
                 "tolerance away from where he drew."),
                ("chan", "Channel yardstick -- cut on a pivot's residual, measured in channel widths",
                 dict(mode="chan", tau=0.20, floor=SV.SCALE_FLOOR, conf_mult=2.0,
                      carry=SV.INC_CARRY, min_piv=5, gate=SV.INC_GATE, share_cuts=False), False,
                 "Still the best of everything here once position is scored: 0.1953. The position "
                 "term did not reorder the constructions, it compressed them.")):
            if "share_cuts" in cfg:
                il, ll = h.piv["support"]
                ih, lh = h.piv["resistance"]
                cev = SV.combined_events(il, ll, ih, lh, h.k, cfg["mode"], cfg["tau"], cfg["floor"],
                                         cfg["carry"], cfg["conf_mult"], h.rvol, nwin=50,
                                         share_cuts=False, par_h=None)
                GL = {kd: SV.broadcast_combined(cev, kd, h.m, cfg["min_piv"], cfg["gate"], h.delta)
                      for kd in ("support", "resistance")}
            else:
                GL = {kd: SV.broadcast_line(h.events(kd, cfg), h.m, cfg["min_piv"], cfg["gate"],
                                            h.delta) for kd in ("support", "resistance")}
            G = {kd: GL[kd][0] for kd in GL}
            S = {kd: GL[kd][2] for kd in GL}
            L = {}
            for kd in ("support", "resistance"):
                L[kd] = (SV.anchor_line(G[kd], S[kd], np.exp(body_log["support"]),
                                        np.exp(body_log["resistance"]), kd, lag=1)
                         if anc else GL[kd][1])
            cells.append(_cell(h, tl, key, blurb, ("anchored" if anc else "raw OLS"), note,
                               G, L, S, sl, a.pos_weight, blo_w, bhi_w, lo_w, hi_w, n))
        # the recalculating construction
        if a.chart_decay:
            # one panel per AGE WEIGHT, everything else frozen at the chosen cell
            rows_syn = tuple(
                (f"dec{int(round(w * 100))}", ("no age weight" if w == 1.0
                                               else f"Oldest pivot at {w * 100:.0f}%"),
                 None, a.dh, True, 4, 0.0, True, "", w)
                for w in (1.0, 0.95, 0.90, 0.80, 0.60))
        else:
            rows_syn = tuple(
                (f"dh{d:g}", f"Height deadband {d:g}%", None, d, True, 4, 0.0, True,
                 "", a.decay_end)
                for d in ((a.dh,) if a.chart_one else (5.0, 10.0, 20.0, 30.0, 40.0)))
        _rows = (rows_syn if a.chart_deltas else (
                ("height", "Recalculate on HEIGHT drift", None, 5.0, False, 3, 0.0, False,
                 "The segment dies when the current fit's LEVEL has moved more than 5% from the "
                 "frozen line -- the gradient may wobble as much as it likes as long as the line "
                 "has not. Best of the whole family at 0.2269, and ahead of both earlier "
                 "constructions on the same position-aware score."),
                ("gradient", "Recalculate on GRADIENT drift", 32.0, None, False, 5, 5.0, False,
                 "The segment dies when the fitted slope has drifted more than 32%/yr from the "
                 "frozen one. 0.2174 -- close behind height, but it fires more often and cuts "
                 "the line at places the slope moved rather than places the line did."),
                ("hgt_body", "+ the body-break rule", 32.0, 5.0, True, 3, 0.0, False,
                 "Adding a candle body closing through the line as a third invalidator: 0.1739. "
                 "The body test fires 292 times and costs half a point of score. This is the "
                 "panel that was drawing an inverted channel and a line through the bodies; both "
                 "are now asserted against, so what you see is what the rule actually produces."),
                ("syn", "+ the break bar becomes a PROVISIONAL pivot", None, 5.0, True, 4, 0.0,
                 True,
                 "The breaking bar is treated as a pivot at its own extreme, kept until the k=3 "
                 "detector ratifies it or a newer break supersedes it, with min_piv+1 charged "
                 "while it lives. 0.1523, the weakest here. 940 provisional points were made and "
                 "only 105 were ever ratified -- 11%. And they feed back: the body test fires 940 "
                 "times with them against 292 without, because the provisional point drags the "
                 "line toward the break and invites the next one."),
        ))
        # the reference rows predate the age weight, so they carry the run's own decay
        _rows = tuple(r if len(r) == 10 else (*r, a.decay_end) for r in _rows)
        for key, blurb, dg, dh, ub, mp, mw, bp, note, dec in _rows:
            cfg = dict(carry=CARRY, min_piv=mp,
                       max_dg=(INF if dg is None else h.DR.h_of_annual(dg)),
                       max_dh=(INF if dh is None else math.log1p(dh / 100)),
                       use_body=ub, min_width=math.log1p(mw / 100), delta=h.delta,
                       ext_log=ext_log, break_pivot=bp,
                       back_check=a.back_check, anchor_clear=a.anchor_clear,
                       decay_end=dec)
            G, L, S, _w = recalc_pair(h.piv, h.k, body_log, h.m, **cfg)
            assert_no_inversion(L, win, cfg["min_width"])
            if ub:
                assert_respects_body(L, body_log, win)
            dgs = "off" if dg is None else f"{dg:g}%/yr"
            dhs = "off" if dh is None else f"{dh:g}%"
            if a.chart_decay:
                note = (f"Oldest pivot weighted {dec * 100:.0f}%, newest 100%, exponential between "
                        f"and normalised across each segment's own span. With the intercept taken "
                        f"from body clearance the weight moves the GRADIENT only. "
                        f"{_w['height']} height invalidations, {_w['body']} body breaks, "
                        f"{_w['syn_made']} provisional pivots.")
            elif a.chart_deltas:
                note = (f"The segment dies when the current fit's level has moved {dh:g}% from the "
                        f"frozen line. Over all {h.m} bars: {_w['height']} height invalidations, "
                        f"{_w['body']} body breaks, {_w['syn_made']} provisional pivots of which "
                        f"{_w['syn_confirmed']} ({100 * _w['syn_confirmed'] / max(1, _w['syn_made']):.0f}%) "
                        f"were ratified by the k=3 detector.")
            cells.append(_cell(h, tl, key, blurb,
                               f"dg={dgs}/dh={dhs}/body={'Y' if ub else 'N'}/mp={mp}"
                               f"/w={mw:g}%{'/SYN' if bp else ''}"
                               f"{'' if dec == 1.0 else f'/decay={dec:g}'}",
                               note, G, L, S, sl, a.pos_weight, blo_w, bhi_w, lo_w, hi_w, n))
        drawn = []
        for L2 in gt["lines"]:
            sg = L2["segment"]
            drawn.append(dict(id=L2["id"], kind=L2["kind"], i0=int(sg["i0"]), i1=int(sg["i1"]),
                              p0=float(sg["p0"]), p1=float(sg["p1"]),
                              drawn_at=int(L2["drawn_at"]), ended_at=int(L2["ended_at"]),
                              g_per_bar=float(L2["g_per_bar"]), live_bars=int(L2["live_bars"])))
        base = cells[0]["SCORE"]
        for c in cells:
            c["delta_vs_control"] = round(c["SCORE"] - base, 4)
        op_all = np.array([b.bar.open for b in h.bars], float)
        hum = SV.human_placement(h, op_all, hi_w, lo_w)
        CHART.parent.mkdir(parents=True, exist_ok=True)
        CHART.write_text(json.dumps(dict(
            symbol=h.sym, start_bar=s, n=n, first_seen=h.first_seen, seen_through=h.seen_to,
            dates=[str(b.timestamp)[:10] for b in h.bars][sl],
            open=list(map(float, op_w)), high=list(map(float, hi_w)),
            low=list(map(float, lo_w)), close=list(map(float, cl_w)),
            human_placement=hum, control_score=base, cells=cells, drawn=drawn,
            page=dict(
                title=("The height deadband" if a.chart_deltas else "Where the line sits"),
                lede1=(
                    ("Every panel is the same construction &mdash; the principal's chosen cell, "
                     "where a break makes that bar a <strong>provisional pivot</strong>, kept "
                     "until the k=3 detector ratifies it or a newer break supersedes it, with "
                     "min_piv+1 charged while it lives. Only the <strong>height deadband</strong> "
                     "varies: how far the current fit's level may drift from the frozen line "
                     "before the segment is thrown away and recalculated.")
                    if a.chart_deltas else
                    "The score now reads the line's <strong>position</strong>, not only its "
                       "gradient. The ground truth carries both clicks per drawn line, so his "
                       "level is known at every bar; quality is now the gradient term "
                       "<em>multiplied by</em> a position term, where a line 10% away scores zero "
                    "on position. Every score roughly halves &mdash; but the ordering of the "
                    "constructions does not change."),
                lede2=(
                    ("Across 42 cells the height deadband has a genuine <strong>interior peak at "
                     "5%</strong> &mdash; 1% and 2% are too twitchy, 20% and 40% hold a dead line "
                     "too long. The gradient deadband is inert beside it: anything looser than "
                     "about 32%/yr, including switching it off entirely, gives the same answer.")
                    if a.chart_deltas else
                    "<strong>The ratchet is gone</strong> &mdash; removed, not replaced. No "
                    "line here slides. Each is the OLS fit, gradient and height together, "
                    "frozen when its segment opened and thrown away when the fit it came from "
                    "drifts too far on either quantity. Of the two deadbands, "
                    "<strong>height is the one that works</strong>. Both sides are walked "
                    "together, so a crossed channel invalidates both and is never drawn. The "
                    "panels run from the plainest rule to the most elaborate, and they get "
                    "<strong>worse in that order</strong>: 0.2269 for a height deadband alone, "
                    "down to 0.1523 once the breaking bar is promoted to a pivot."),
                placelede=("How far each line sits from the bar's own high or low, in per cent. "
                           "The principal's 25 lines get the identical statistic over the bars he "
                           "held them, and they are the benchmark: <b>a support line about 10% "
                           "under the low is what he draws.</b>"))
        )))
        print(f"\n  {'cell':<12s} {'SCORE':>7s} {'q_g':>6s} {'q_lvl':>6s} {'cuts':>5s}")
        for c in cells:
            p = c["parts"]
            print(f"  {c['key']:<12s} {c['SCORE']:>7.4f} "
                  f"{((p['support']['q_grad'] or 0) + (p['resistance']['q_grad'] or 0)) / 2:>6.3f} "
                  f"{((p['support']['q_level'] or 0) + (p['resistance']['q_level'] or 0)) / 2:>6.3f} "
                  f"{c['n_cuts']:>5d}")
        print(f"\n  [P] {CHART.relative_to(REPO)} written")
        return 0

    rows = []
    cfgs = [dict(carry=CARRY, min_piv=mp,
                 max_dg=(INF if dg is None else h.DR.h_of_annual(dg)),
                 max_dh=(INF if dh is None else math.log1p(dh / 100)),
                 use_body=ub, min_width=math.log1p(mw / 100), delta=h.delta,
                 ext_log=ext_log, break_pivot=bp,
                 _dg=dg, _dh=dh, _ub=ub, _mp=mp, _mw=mw, _bp=bp)
            for mp in MIN_PIVS for dg in DG_ANNUAL for dh in DH_PCT for ub in USE_BODY
            for mw in MIN_WIDTH_PCT for bp in BREAK_PIVOT
            if (ub or not bp)      # the break pivot needs a break test to exist
            if not (dg is None and dh is None and not ub)]      # nothing can end a segment
    print(f"\n  {len(cfgs)} cells | max_dg {DG_ANNUAL}%/yr x max_dh {DH_PCT}% x body {USE_BODY} "
          f"x min_piv {MIN_PIVS} (R13)")
    print(f"  scored WITH position (pos_weight={a.pos_weight:g}, a line {100 * (math.exp(LEVEL_TOL) - 1):.0f}% "
          f"away scores zero on position)\n")
    print(f"  {'cell':<34s} {'SCORE':>7s} {'q_g':>6s} {'q_lvl':>6s} {'precS':>6s} {'precR':>6s} "
          f"{'grad':>5s} {'hgt':>5s} {'body':>5s}")
    for cfg in cfgs:
        meta = {kk: cfg.pop(kk) for kk in ("_dg", "_dh", "_ub", "_mp", "_mw", "_bp")}
        cell, sc = {}, []
        G, L, _S, tot_why = recalc_pair(h.piv, h.k, body_log, h.m, **cfg)
        assert_no_inversion(L, win, cfg["min_width"])
        if cfg["use_body"]:
            assert_respects_body(L, body_log, win)
        for kd in ("support", "resistance"):
            with np.errstate(over="ignore"):
                lvl = np.exp(L[kd][sl])
            st = score_side_pos(G[kd][sl], lvl, tl[kd][1], tl[kd][0], h.seen, h.delta,
                                pos_weight=a.pos_weight)
            cell[kd] = st
            sc.append(st["score"])
        cfg.update(meta)
        dgs = "off" if meta["_dg"] is None else f"{meta['_dg']:g}%"
        dhs = "off" if meta["_dh"] is None else f"{meta['_dh']:g}%"
        lab = (f"dg={dgs}/dh={dhs}/body={'Y' if meta['_ub'] else 'N'}"
               f"/mp={meta['_mp']}/w={meta['_mw']:g}%"
               f"{'/SYN' if meta['_bp'] else ''}")
        rows.append(dict(label=lab, SCORE=round(float(np.mean(sc)), 4),
                         why={kk: v for kk, v in tot_why.items() if kk != "events"},
                         support=cell["support"], resistance=cell["resistance"], **meta))
    rows.sort(key=lambda r: -r["SCORE"])
    for r in rows[:20]:
        sp, rs = r["support"], r["resistance"]
        print(f"  {r['label']:<34s} {r['SCORE']:>7.4f} "
              f"{((sp['q_grad'] or 0) + (rs['q_grad'] or 0)) / 2:>6.3f} "
              f"{((sp['q_level'] or 0) + (rs['q_level'] or 0)) / 2:>6.3f} "
              f"{sp['precision']:>6.3f} {rs['precision']:>6.3f} "
              f"{r['why']['gradient']:>5d} {r['why']['height']:>5d} {r['why']['body']:>5d}")

    # WHAT EACH TEST IS WORTH ON ITS OWN -- the four corners of the two deltas, body off
    print(f"\n  EACH INVALIDATOR ALONE (body off, best over the remaining axes)")
    corners = [("gradient only", lambda r: r["_dg"] is not None and r["_dh"] is None),
               ("height only", lambda r: r["_dg"] is None and r["_dh"] is not None),
               ("both deltas", lambda r: r["_dg"] is not None and r["_dh"] is not None)]
    for nm, pred in corners:
        sub = [r for r in rows if not r["_ub"] and pred(r)]
        if sub:
            b = max(sub, key=lambda r: r["SCORE"])
            print(f"    {nm:<16s} {b['SCORE']:>7.4f}  {b['label']:<34s} "
                  f"fired: grad {b['why']['gradient']:>4d} hgt {b['why']['height']:>4d}")
    for nm, pred in (("+ body break", lambda r: r["_ub"] and not r["_bp"]),
                     ("+ break = PIVOT", lambda r: r["_ub"] and r["_bp"])):
        sub = [r for r in rows if pred(r)]
        if not sub:
            continue
        b = max(sub, key=lambda r: r["SCORE"])
        w = b["why"]
        print(f"    {nm:<16s} {b['SCORE']:>7.4f}  {b['label']:<40s} "
              f"fired: grad {w['gradient']:>4d} hgt {w['height']:>4d} body {w['body']:>4d}"
              + (f"  | provisional pivots made {w['syn_made']}, ratified by the k=3 detector "
                 f"{w['syn_confirmed']}, superseded {w['syn_superseded']}" if b["_bp"] else ""))

    print(f"\n  WHAT INVALIDATES A SEGMENT, in the best cell ({rows[0]['label']}):")
    w = rows[0]["why"]
    tw = sum(w[kk] for kk in ("gradient", "height", "body", "inverted")) or 1
    for kk in ("gradient", "height", "body", "inverted"):
        print(f"    {kk:<10s} {w[kk]:>5d}  ({100 * w[kk] / tw:>4.1f}%)")
    OUT.write_text(json.dumps(dict(
        what="D399: position-aware score; freeze-and-recalculate instead of ratchet",
        level_tol_pct=round(100 * (math.exp(LEVEL_TOL) - 1), 1), pos_weight=a.pos_weight,
        published_causal_gradient_only=PUBLISHED_CAUSAL, n_cells=len(rows),
        best=rows[0], references=refs, grid=rows), indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written")
    print(f"  BEST-OF-{len(rows)}. Nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
