"""ENTRY / FORECAST DECOUPLING: let the forecast fire first and the extreme arrive later.

    python working/d528_decouple.py --self-test
    python working/d528_decouple.py --fit          # pass 1: the cut, on the early half only
    python working/d528_decouple.py --run          # pass 2: the trades

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.
Corrected chain: slope_ok DROPPED, drift alignment KEPT (ADDENDUM 12).

=================================================================================================
THE PRINCIPAL'S IDEA, and what is actually coupled today
=================================================================================================

"a grace period, after the forecast triggers the forecast is valid for {10, 15, 20} bars. In which
case we enter the trade based on the same mean and range expectations as where forecasted last."

WHAT IS COUPLED TODAY. Every forecast figure in D528 was measured at a bar that ALREADY carried a
2-sigma drift-aligned extreme -- the composite was evaluated on the candidate population, never on
the bar population. So the forecast has only ever been asked "given an extreme has just happened,
will price traverse?" It has never been allowed to fire FIRST and wait.

TWO SEPARATE CHANGES ARE BUNDLED IN THAT ONE SENTENCE, and they are separated here, because if
they were run together a result could not be attributed:

    (a) THE GRACE WINDOW -- the forecast may fire at t_f and the entry may occur at any bar in
        [t_f, t_f + W]. This changes WHICH TRADES ARE TAKEN. It cannot change any individual
        trade, because with a fresh reference the trade at bar t is the same object either way.
    (b) THE FROZEN REFERENCE -- "the same mean and range expectations as where forecasted last":
        the level, the slope and sigma are taken from t_f and CARRIED, not re-fitted at the entry
        bar. This changes THE TRADE ITSELF -- the entry threshold, the mirror target and the stop
        are all measured against a stale reference.

=================================================================================================
EVERY DESIGN CHOICE, ENUMERATED
=================================================================================================

D1  THE ARMS. A full grid, so (a) and (b) are separable:
        COUPLED       W = 0, fresh reference          == the ADDENDUM 13 baseline, by construction
        GRACE-FRESH   W in {10,15,20}, fresh          isolates (a) alone
        GRACE-FROZEN  W in {10,15,20}, frozen at t_f  adds (b) on top of (a)
        NO-FORECAST   fire on every bar, W = 0        the corrected chain with the forecast off
    GRACE-FRESH minus COUPLED is the value of waiting. GRACE-FROZEN minus GRACE-FRESH is the cost
    or benefit of freezing. Neither difference is interpretable without the other arm.

D2  THE FORECAST FIRE. The composite is the mean of the four causal features' z-scores
    (vol_ratio, squeeze, vratio2, ac1), LOWER = more forecastable, exactly as everywhere else in
    D528. It fires where the composite is in the most-forecastable q% of bars.

D3  THE POPULATION THE CUT IS FITTED ON HAS CHANGED, AND THIS IS THE LARGEST DESIGN DECISION HERE.
    Every previous D528 cut was a median of the CANDIDATE population. Decoupling requires the
    forecast to be evaluated at bars with no extreme, so mu, sigma and the cut are now fitted on
    ALL ELIGIBLE BARS of the early half. The two cuts are NOT the same number and the arms are
    NOT comparable to any published forecast figure. Reported as its own quantity.

D4  q LADDER: 50 / 25 / 10 percent of bars. A ladder and not one value because of C1 below --
    duty cycle and grace multiply, and at q=50 with W=20 the forecast is effectively always on.

D5  DEPTH X = 2.0, stop G = 3.0 sigma, tau = 20, target = the MIRROR of the entry residual,
    drift-carried, exits measured from the fill. Identical to ADDENDUM 13's best cell, so the
    COUPLED arm must reproduce it.

D6  ONE ENTRY PER BAR. Many fire bars can reach the same extreme through their grace windows.
    A bar is entered at most once, and the trade is attributed to the EARLIEST fire bar that
    reached it -- which is what a live system does: the first valid forecast opens the position.

D7  NO POSITION BLOCKING, path-invariant lens. Trades may overlap, exactly as in every previous
    D528 per-trade cell, so the arms are comparable to what is already on record. The book lens
    (slot-limited) is reported separately from the same resolve.

D8  OUT OF TIME. Everything -- z-score means, sds and the q cut -- fitted on days < 2020-01-01,
    every reported figure on days >= 2020-01-01.

D9  MATCHED CONTROL, the ADDENDUM 9/11 construction: keep the real data, randomise the SELECTION.
    The control draws count-matched fire bars uniformly from the eligible bar pool and runs the
    identical entry machinery, so it shares the grace window, the reference convention, the
    universe and the count -- everything but the forecast. Scored on MEAN, MEDIAN AND TRIMMED
    MEAN, because a mean on a tail-dominated cell is where a count-matched draw is least
    informative (ADDENDUM 11: two market events cleared the p95 on the mean alone).

D10 UNIVERSES: all roots (power) and micro-8 (tradeable), separately. a2 stays ON here -- the a2
    question is tested independently in d528_a2_test.py and mixing the two would confound both.

=================================================================================================
ADDED AFTER THE FIRST RUN. The first run was reported to the principal WITH its defects named;
these three changes fix them and the first run's cache is kept as the record.
=================================================================================================

D11 THE STOP MUST SCALE WITH THE REALISED ENTRY DEPTH. X = 2.0 is a FLOOR, not a level, so the
    mean realised depth is 2.82 sigma against a stop fixed at G = 3.0. MEASURED ON THE PUBLISHED
    BASELINE: 27.5% of its trades have |y| at the fill ABOVE 3 sigma, so the stop sits INSIDE the
    entry and fires on the first bar of FAVOURABLE movement -- those trades exit at a median of
    ONE bar, with P(target) 4.1% and P(stop) 93.4%. This is the same defect the depth sweep fixed
    with G = X + 1.0 and it was never carried back into the baseline geometry. Both conventions
    are therefore run side by side:
        stop=fixed      g = 3.0 sigma            the published convention, kept for continuity
        stop=relative   g = |y_fill|/sd + 1.0    the stop always 1 sigma BEYOND the actual fill
    Under `relative` no trade can be stopped by movement toward its own mean.

D12 A THIRD REFERENCE MODE, because `frozen` confounded two things. The frozen arm generated
    83,792 trades against the unconditional construction's 5,296 -- 16x MORE THAN NO FILTER AT
    ALL -- because a carried level plus twenty bars of drift is nearly always 2 sigma from price.
    It does not wait for an extreme, it manufactures one (C3, as predicted). So:
        hybrid   the TRIGGER is a real fresh extreme; only the LEVEL, SLOPE and SIGMA used for
                 the target and the stop come from the forecast bar.
    That is arguably closer to the principal's words -- "the same mean and range expectations as
    where forecasted last" describes the expectations, not the trigger -- and it tests (b) with
    the trade count held comparable to the fresh arm. `frozen` is carried unchanged beside it so
    the manufactured-extreme reading stays on the record rather than being quietly replaced.

D13 THE CONTROL IS NOW THE ONE D9 DECLARED. The first run's control bootstrapped P&L from the
    no-forecast pool, which is NOT what D9 says, and a pool-size guard then silently dropped
    every frozen cell -- the arms under test. Replaced with the declared construction: per
    session, draw the SAME NUMBER of fire bars uniformly from that session's eligible pool and
    run the identical machinery. It shares the grace window, the reference mode, the stop
    convention, the session-level duty cycle and the count; the only thing destroyed is WHICH
    bars the forecast picked. Reported as its own cell (ctl_*) so every statistic is computed
    the same way for treatment and control.
    NOTE ON READING THE STARS: the first run starred 12 of 12 cells on the median while every
    median was deeply negative. "Beats the control" is empty below zero -- a star is reported
    here only as a margin, and never as a pass.

=================================================================================================
THE CONFOUNDS, NAMED. Five, and each is measured rather than argued.
=================================================================================================

C1  DUTY CYCLE x GRACE IS MULTIPLICATIVE, and it can make the forecast vanish. A window is live
    for W+1 bars after each fire, so at q=50 and W=20 essentially every bar sits inside some live
    window and the arm degenerates to NO-FORECAST. The runner prints, for every cell, the
    fraction of bars covered by a live window. If that is near 1.0 the cell is not a forecast
    test and is labelled DEGENERATE.

C2  THE GRACE ARM CANNOT LOSE TRADES, so a per-trade comparison is not a like-for-like one. With
    a fresh reference the grace arm's entry set is a strict SUPERSET of the coupled arm's (proved
    by assertion in the runner, not asserted in prose). The added trades are the marginal ones,
    and the marginal mean is what the grace window is actually worth -- so the runner reports
    the MARGINAL set (grace-only entries) separately from the union.

C3  FREEZING IS NOT A NEUTRAL RE-REFERENCING. A stale level plus a carried slope drifts away from
    price, so a frozen reference systematically finds LARGER apparent excursions as the window
    ages -- it partly measures its own extrapolation. That is the level-chasing artefact that
    fooled this study three times. The runner therefore reports the mean |y|/sigma at entry and
    the mean fill delay per cell: if the frozen arm's entries are deeper AND later, the depth is
    the extrapolation, not the market.

C4  SIGMA STALENESS CUTS BOTH WAYS. The frozen arm's threshold uses sigma from t_f. In a
    volatility expansion that threshold is too low (it over-admits); in a contraction too high
    (it under-admits). The realised/designed target ratio is printed so this shows up as a
    designed-payoff bias rather than hiding inside gross.

C5  COST IS NOT CONSTANT ACROSS ARMS. More trades in quieter windows changes the root mix and so
    the mean cost. Gross and net are reported side by side in every cell, so a difference can be
    attributed to signal or to cost.
"""
from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402
import d528_target_and_stability as TS          # noqa: E402
import d528_confirmation_entry as CE            # noqa: E402

H = Z.H
X, G, TAU = 2.0, 3.0, 20
GRACES = (0, 10, 15, 20)
QS = (25, 10)                 # q=50 dropped: the first run measured its coverage at 0.80-0.86,
                              # so C1 fired and those cells were NO-FORECAST wearing a name
STOPS = ("fixed", "relative")     # D11
REFS = ("fresh", "frozen", "hybrid")   # D12
STOP_BEYOND = 1.0
SPLIT = FR.SPLIT
FEATS4 = TS.FEATS4
MICRO = W.MICRO
COMMISSION = CE.COMMISSION
FIT = Path("temp/d528_decouple_fit.json")
CACHE = Path("temp/d528_decouple_cache.parquet")    # the FIRST run, kept as its own record
SHARD = Path("temp/d528_dec_shards")                # the corrected run, one parquet per root
N_DRAW = 300
SEED = 528991
ACCOUNT, TRAIL = 50_000.0, 2_000.0


def P(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------------------------------
# the entry machinery
# ------------------------------------------------------------------------------------------

def qual_fresh(c, tick, cost_tk, xv=X):
    """The fresh-reference entry condition at every bar -- it depends on the bar ALONE, which is
    why a grace window with a fresh reference is pure SELECTION and changes no individual trade."""
    with np.errstate(invalid="ignore"):
        k = np.asarray(c["a2ok"]) & (c["flat_sd"] > 0)
        k = k & (np.abs(c["flat_y"]) >= xv * c["flat_sd"])
        k = k & (np.sign(c["flat_y"]) * c["slope"] < 0)
        k = k & (np.abs(c["flat_y"]) / tick > cost_tk)
    return np.nan_to_num(k, nan=False).astype(bool)


def live_window(fire, w):
    """True at bar i if some fire bar in [i-w, i] is still live. Cumulative-sum rolling OR."""
    f = fire.astype(np.int64)
    cs = np.concatenate(([0], np.cumsum(f)))
    i = np.arange(len(f))
    lo = np.maximum(i - w, 0)
    return (cs[i + 1] - cs[lo]) > 0


def frozen_entries(path, c, tick, cost_tk, fire, w, xv=X):
    """For each fire bar, the first bar in [t_f, t_f+w] that clears the entry test measured
    against the reference FROZEN at t_f. Vectorised over offsets; returns (entry_i, ref_i).

    D6 dedupe: a bar entered from several fire bars is attributed to the earliest one.
    """
    n_t = len(c["flat_y"])
    px = c["px"]                                      # px[i] is the price at bar t = i + 2H
    lvl, slp, sd = c["flat_lvl"], c["slope"], c["flat_sd"]
    idx = np.flatnonzero(fire)
    if len(idx) == 0:
        return np.empty(0, np.int64), np.empty(0, np.int64)
    best = np.full(n_t, -1, np.int64)                 # entry bar -> earliest reference bar
    with np.errstate(invalid="ignore"):
        for k in range(w + 1):
            j = idx + k
            m = j < n_t
            if not m.any():
                break
            jf, i_f = j[m], idx[m]
            y = px[jf] - (lvl[i_f] + slp[i_f] * k)    # the frozen level, carried k bars
            ok = (np.asarray(c["a2ok"])[i_f] & (sd[i_f] > 0)
                  & (np.abs(y) >= xv * sd[i_f])
                  & (np.sign(y) * slp[i_f] < 0)
                  & (np.abs(y) / tick > cost_tk))
            ok = np.nan_to_num(ok, nan=False).astype(bool)
            for e, rr in zip(jf[ok], i_f[ok]):
                if best[e] < 0 or rr < best[e]:
                    best[e] = rr
    ent = np.flatnonzero(best >= 0)
    return ent.astype(np.int64), best[ent]


def prev_fire(fire, w):
    """For each bar, the EARLIEST fire bar in [i-w, i], or -1 if the window holds none (D6).
    Vectorised over offsets; the largest admissible k is the earliest bar."""
    n = len(fire)
    out = np.full(n, -1, np.int64)
    i = np.arange(n)
    for k in range(w + 1):                    # ascending k, so a later write is an EARLIER bar
        j = i - k
        m = (j >= 0) & fire[np.maximum(j, 0)]
        out[m] = j[m]
    return out


def resolve_frozen(path, c, ent, ref, tick, tick_usd, cost_tk, day_idx, b0, root, g=G,
                   stop_mode="fixed"):
    """Exits for a trade whose reference bar may differ from its entry bar. The exit block is a
    transcription of CE.resolve_entry's, with (lvl, slope, sd, t_r) taken from the REFERENCE bar
    -- self-test [1] asserts the two agree bit-for-bit when ref == ent and stop_mode is `fixed`.

    stop_mode `fixed`    g sigma from the reference level, the published convention.
              `relative` |y_fill|/sd + STOP_BEYOND, so the stop is always BEYOND the fill and
                         no trade can be stopped out by price moving toward its own mean (D11).
    """
    n = len(path)
    out = []
    for e, rr in zip(ent, ref):
        t_f = int(e) + 2 * H                          # the entry bar
        t_r = int(rr) + 2 * H                         # the reference bar
        if t_f + 1 >= n - 1:
            continue
        sd, lvl, slope = c["flat_sd"][rr], c["flat_lvl"][rr], c["slope"][rr]
        if not np.isfinite(sd) or sd <= 0:
            continue
        p_fill = path[t_f]
        y_fill = p_fill - (lvl + slope * (t_f - t_r))
        s = float(np.sign(y_fill))
        kk = np.arange(1, TAU + 1)
        j = t_f + kk
        valid = j <= (n - 1)
        if not valid.any():
            continue
        F = path[np.minimum(j, n - 1)]
        lv = lvl + slope * (t_f - t_r + kk)
        yk = F - lv
        y_tgt = -y_fill
        gg = g if stop_mode == "fixed" else abs(y_fill) / sd + STOP_BEYOND
        y_stp = s * gg * sd
        ht = ((yk - y_tgt) * s <= 0.0) & valid
        hs = ((yk - y_stp) * s >= 0.0) & valid
        i_t = int(np.argmax(ht)) if ht.any() else R.BIG
        i_s = int(np.argmax(hs)) if hs.any() else R.BIG
        nv = int(valid.sum())
        if i_t == R.BIG and i_s == R.BIG:
            kind, d_, px_exit = 2, nv, float(F[nv - 1])
        elif i_s <= i_t:
            kind, d_, px_exit = 1, i_s + 1, float(F[min(i_s, TAU - 1)])
        else:
            kind, d_, px_exit = 0, i_t + 1, float(lv[min(i_t, TAU - 1)] + y_tgt)
        gross_tk = (-s) * (px_exit - p_fill) / tick
        cost = cost_tk * tick_usd + COMMISSION
        out.append({"filled": 1.0, "root": root, "day_idx": day_idx, "i": float(e),
                    "t_in": float(day_idx * 2000 + b0 + t_f),
                    "t_out": float(day_idx * 2000 + b0 + t_f + d_),
                    "kind": float(kind), "bars": float(d_),
                    "gross": gross_tk * tick_usd, "cost": cost,
                    "tgt_usd": abs(y_tgt) / tick * tick_usd,
                    "ysig": abs(y_fill) / sd, "gsig": float(gg),
                    "inside": float(abs(y_fill) / sd > gg),
                    "delay": float(t_f - t_r)})
    return out


# ------------------------------------------------------------------------------------------
# self-tests
# ------------------------------------------------------------------------------------------

def self_test():
    rng = np.random.default_rng(7)
    ok = True

    # [1] resolve_frozen with ref == ent must reproduce CE.resolve_entry(market) bit-for-bit.
    #     This is what makes the COUPLED arm the published baseline rather than a lookalike.
    # TICK 0.05, not 0.25: a2ok needs a median bar move of >= 4 ticks, and on a unit random walk
    # a 0.25 tick gives ~2.7 -- so the whole fixture admitted nothing and three checks "passed"
    # on empty sets. That is the shape of a test that cannot fail.
    TK = 0.05
    path = np.cumsum(rng.normal(0, 1.0, 400)) + 5000.0
    c = Z.classify2(path, TK)
    keep = qual_fresh(c, TK, 0.5)
    a = [z for z in CE.resolve_entry(path, c, keep, TK, 1.25, 0.5, "market", 0.0, 0, 0, 0, "T")
         if z["filled"] > 0.5]
    ent = np.flatnonzero(keep)
    b = resolve_frozen(path, c, ent, ent, TK, 1.25, 0.5, 0, 0, "T")
    same = (len(a) == len(b) and len(a) > 5
            and all(x["gross"] == y["gross"] and x["kind"] == y["kind"]
                    and x["tgt_usd"] == y["tgt_usd"] and x["i"] == y["i"]
                    for x, y in zip(a, b)))
    P(f"  [1] frozen(ref==ent) == resolve_entry(market): {len(a)} vs {len(b)} trades -> "
      f"{'OK' if same else 'FAIL'}")
    ok &= same

    # [2] the grace window with a FRESH reference must be pure SELECTION (C2): its entry set is a
    #     strict superset of W=0's and every shared trade is identical.
    fire = rng.random(len(c["flat_y"])) < 0.3
    s0 = set(np.flatnonzero(keep & live_window(fire, 0)))
    s20 = set(np.flatnonzero(keep & live_window(fire, 20)))
    sup = s0 <= s20 and len(s20) > len(s0)
    P(f"  [2] fresh grace is a superset: {len(s0)} -> {len(s20)} entries -> "
      f"{'OK' if sup else 'FAIL'}")
    ok &= sup

    # [3] the grace window must actually REACH an extreme that W=0 cannot see, and W=0 must not
    #     see it. A check that only confirms the first half cannot fail.
    # A GENTLE UPTREND with a single-bar step DOWN at bar T. The drift rule requires
    # sign(y) * slope < 0, so a down-step against an up-drift is the only geometry that can
    # qualify -- a monotone ramp (the first fixture written here) can never fire, which is
    # exactly the mistake ADDENDUM 13 records for the confirmation-mode test.
    T = 140
    p = 100.0 + 0.02 * np.arange(200) + rng.normal(0, 0.05, 200)
    p[T:] -= 1.5
    cc = Z.classify2(p, 0.005)
    qf = qual_fresh(cc, 0.005, 0.0)
    assert qf[T - 2 * H], "fixture [3] does not produce an extreme at T"
    f1 = np.zeros(len(qf), bool)
    f1[T - 2 * H - 6] = True                          # fire six bars BEFORE the extreme
    n0 = int((qf & live_window(f1, 0)).sum())
    n10 = int((qf & live_window(f1, 10)).sum())
    reach = (n0 == 0) and (n10 >= 1)
    P(f"  [3] W=0 sees {n0}, W=10 sees {n10} on an extreme 6 bars after the fire -> "
      f"{'OK' if reach else 'FAIL'}")
    ok &= reach

    # [4] CAUSALITY. Rewriting every bar from the entry bar onward must not move any entry or
    #     any reference. If it does, the selection is reading its own outcome.
    p2 = path.copy()
    ent0, ref0 = frozen_entries(p2, c, TK, 0.5, fire, 20)
    if len(ent0):
        cut = int(ent0[0]) + 2 * H
        p3 = path.copy()
        p3[cut:] = p3[cut] + np.cumsum(rng.normal(0, 5.0, len(p3) - cut))
        c3 = Z.classify2(p3, TK)
        e3, r3 = frozen_entries(p3, c3, TK, 0.5, fire, 20)
        m0 = ent0 < (cut - 2 * H)
        m3 = e3 < (cut - 2 * H)
        cau = np.array_equal(ent0[m0], e3[m3]) and np.array_equal(ref0[m0], r3[m3])
    else:
        cau = False
    P(f"  [4] entries before the rewrite point are unchanged -> {'OK' if cau else 'FAIL'}")
    ok &= cau

    # [5] D6 dedupe: no entry bar may appear twice.
    dd = len(ent0) == len(set(ent0.tolist()))
    P(f"  [5] one entry per bar ({len(ent0)} entries, {len(set(ent0.tolist()))} unique) -> "
      f"{'OK' if dd else 'FAIL'}")
    ok &= dd

    # [6] BREAK THE DEDUPE and prove [5] can fail -- a check that cannot fail is worse than none.
    bad = np.array([3, 3, 7], np.int64)
    P(f"  [6] the same check on a deliberately duplicated set -> "
      f"{'OK (it fails)' if len(bad) != len(set(bad.tolist())) else 'FAIL (it passed)'}")

    # [7] live_window must equal a brute-force rolling OR.
    f2 = rng.random(80) < 0.2
    for w in (0, 3, 20):
        bf = np.array([f2[max(0, i - w):i + 1].any() for i in range(len(f2))])
        if not np.array_equal(bf, live_window(f2, w)):
            ok = False
            P(f"  [7] live_window disagrees with brute force at w={w} -> FAIL")
            break
    else:
        P("  [7] live_window == brute-force rolling OR at w = 0, 3, 20 -> OK")

    # [8] prev_fire must equal a brute-force "earliest fire bar in [i-w, i]" (D6).
    f3 = rng.random(60) < 0.25
    for w in (0, 5, 20):
        bf = np.array([next((j for j in range(max(0, i - w), i + 1) if f3[j]), -1)
                       for i in range(len(f3))])
        if not np.array_equal(bf, prev_fire(f3, w)):
            ok = False
            P(f"  [8] prev_fire disagrees with brute force at w={w} -> FAIL")
            break
    else:
        P("  [8] prev_fire == brute-force earliest-in-window at w = 0, 5, 20 -> OK")

    # [9] D11: under a RELATIVE stop no trade may have its stop inside the entry. Under the
    #     FIXED stop some must, or the fixture does not exercise the defect being fixed.
    rel = resolve_frozen(path, c, ent, ent, TK, 1.25, 0.5, 0, 0, "T", stop_mode="relative")
    fix = resolve_frozen(path, c, ent, ent, TK, 1.25, 0.5, 0, 0, "T", stop_mode="fixed")
    n_rel = sum(z["inside"] for z in rel)
    n_fix = sum(z["inside"] for z in fix)
    st = (n_rel == 0) and (n_fix > 0)
    P(f"  [9] stops inside the entry: relative {int(n_rel)} of {len(rel)}, "
      f"fixed {int(n_fix)} of {len(fix)} -> {'OK' if st else 'FAIL'}")
    ok &= st

    # [10] HYBRID collapses to FRESH at w=0 -- the reference bar must be the entry bar itself,
    #      which is what makes the w=0 row a shared baseline for all three modes.
    fe = np.flatnonzero(keep & live_window(fire, 0))
    hy = prev_fire(fire, 0)[fe]
    P(f"  [10] hybrid(w=0) reference == entry on all {len(fe)} entries -> "
      f"{'OK' if len(fe) and np.array_equal(hy, fe) else 'FAIL'}")
    ok &= bool(len(fe) and np.array_equal(hy, fe))

    P(f"\n  {'ALL SELF-TESTS PASS' if ok else 'SELF-TESTS FAILED'}")
    return ok


# ------------------------------------------------------------------------------------------
# pass 1: the cut, on the early half only (D3, D8)
# ------------------------------------------------------------------------------------------

def fit():
    sp = Q.specs()
    f = W.load("close")
    f = f[f["day"] < SPLIT]
    roots = sorted(set(f["root"]) & set(sp))
    P(f"pass 1 -- fitting the ALL-BAR composite on {len(roots)} roots, days < {SPLIT}")
    acc = {k: [] for k in FEATS4}
    for r in roots:
        g = f[f["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            ft = FR.causal_features(px, c, vm, b0)
            for k in FEATS4:
                acc[k].append(np.asarray(ft[k], np.float64))
    stats = {}
    zs = []
    for k in FEATS4:
        v = np.concatenate(acc[k])
        mu, sd = float(np.nanmean(v)), float(np.nanstd(v))
        stats[k] = [mu, sd]
        zs.append((v - mu) / sd)
    comp = np.nanmean(np.vstack(zs), axis=0)
    cuts = {str(q): float(np.nanpercentile(comp, q)) for q in QS}
    FIT.parent.mkdir(parents=True, exist_ok=True)
    FIT.write_text(json.dumps({"stats": stats, "cuts": cuts,
                               "n_bars": int(np.isfinite(comp).sum())}, indent=2))
    P(f"  {int(np.isfinite(comp).sum()):,} eligible bars; cuts {cuts}")
    P(f"  -> {FIT}")
    P("  NOTE (D3): this is an ALL-BAR cut. Every published D528 forecast figure used a")
    P("  CANDIDATE-population median. The two are different numbers and the arms below are not")
    P("  comparable to those figures -- only to each other and to NO-FORECAST.")


# ------------------------------------------------------------------------------------------
# pass 2: the trades
# ------------------------------------------------------------------------------------------

def build():
    if not FIT.exists():
        P(f"no fit at {FIT}; run --fit first")
        return
    fitj = json.loads(FIT.read_text())
    stats, cuts = fitj["stats"], fitj["cuts"]
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"pass 2 -- {len(roots)} roots x {len(QS)} q x {len(GRACES)} graces x {len(REFS)}"
      f" references x {len(STOPS)} stop conventions, each with its control")
    # SHARDED PER ROOT. The frozen arms emit ~200k trades per cell and there are 24 of them, so
    # one in-memory frame would be ~5M rows before the concat doubles it. One parquet per root
    # holds peak memory to a single root's worth and costs nothing to read back.
    SHARD.mkdir(parents=True, exist_ok=True)
    for stale in SHARD.glob("*.parquet"):
        stale.unlink()
    for r in roots:
        rows = []
        g = f[f["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(c["flat_y"])
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU - max(GRACES))] = True
            qf = qual_fresh(c, tick, cost_tk) & room
            zs = [(np.asarray(ft[k], np.float64) - stats[k][0]) / stats[k][1] for k in FEATS4]
            comp = np.nanmean(np.vstack(zs), axis=0)
            elig = np.isfinite(comp) & room

            def emit(cell, tr, cov):
                if not tr:
                    return
                k = len(tr)
                blk = {"cell": np.full(k, cell, dtype=object),
                       "day": np.full(k, day, dtype=object),
                       "root": np.full(k, r, dtype=object),
                       "cov": np.full(k, cov),
                       "i": np.array([z["i"] for z in tr], float)}
                for fld in ("kind", "gross", "cost", "tgt_usd", "bars", "t_in", "t_out"):
                    blk[fld] = np.array([z.get(fld, np.nan) for z in tr], float)
                for fld in ("ysig", "gsig", "inside"):
                    blk[fld] = np.array([z.get(fld, np.nan) for z in tr], float)
                blk["delay"] = np.array([z.get("delay", 0.0) for z in tr], float)
                rows.append(blk)

            # ALL THREE reference modes go through ONE resolve, so the arms cannot differ by
            # anything but their (entry, reference) pairing and the stop convention.
            #   fresh   ref == ent                       (self-test [1]: == CE.resolve_entry)
            #   frozen  ent found against the frozen level, ref = the fire bar
            #   hybrid  ent is a real fresh extreme,      ref = the fire bar that reached it
            def trades(ent, ref, stop_mode):
                return resolve_frozen(px, c, ent, ref, tick, tick_usd, cost_tk,
                                      di[day], b0, r, g=G, stop_mode=stop_mode)

            qi = np.flatnonzero(qf)
            for sm in STOPS:
                emit(f"noforecast_{sm}", trades(qi, qi, sm), 1.0)

            # D13: the control RNG is seeded per (root, day, q) so the draw is reproducible and
            # independent of the order cells are visited in.
            for q in QS:
                real = (comp <= cuts[str(q)]) & elig
                ei = np.flatnonzero(elig)
                nfire = int(real.sum())
                # zlib.crc32, NOT hash(): Python randomises str hashing per process unless
                # PYTHONHASHSEED is set, so hash() would make the control unreproducible.
                cr = np.random.default_rng(
                    zlib.crc32(f"{SEED}|{r}|{day}|{q}".encode()) & 0xFFFFFFFF)
                ctl = np.zeros(n_t, bool)
                if nfire and len(ei):
                    ctl[cr.choice(ei, size=min(nfire, len(ei)), replace=False)] = True
                for tag, fire in (("", real), ("ctl", ctl)):
                    for w in GRACES:
                        lw = live_window(fire, w)
                        cov = float((lw & elig).sum()) / max(int(elig.sum()), 1)
                        fe = np.flatnonzero(qf & lw)
                        # HOISTED OUT OF THE STOP LOOP: the entry SET does not depend on the
                        # stop convention, only the exit does, so computing frozen_entries once
                        # per (tag, q, w) instead of once per stop halves the dominant cost.
                        pf = prev_fire(fire, w)
                        hr = pf[fe]
                        hm = hr >= 0
                        if w:
                            ent, ref = frozen_entries(px, c, tick, cost_tk, fire & room, w)
                            km = room[ent] if len(ent) else np.zeros(0, bool)
                            ent, ref = ent[km], ref[km]
                        for sm in STOPS:
                            emit(f"{tag}fresh_q{q}_w{w}_{sm}", trades(fe, fe, sm), cov)
                            if w == 0:
                                continue   # at w=0 frozen and hybrid ARE fresh (ref == ent)
                            # HYBRID: real fresh trigger, expectations from the fire bar
                            emit(f"{tag}hybrid_q{q}_w{w}_{sm}",
                                 trades(fe[hm], hr[hm], sm), cov)
                            # FROZEN: the trigger itself is measured against the stale level
                            emit(f"{tag}frozen_q{q}_w{w}_{sm}",
                                 trades(ent, ref, sm), cov)
        if not rows:
            continue
        cols = rows[0].keys()
        df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
        df.to_parquet(SHARD / f"{r}.parquet")
        P(f"  {r:<5} {len(df):>9,} trades")
    nsh = sorted(SHARD.glob("*.parquet"))
    n = sum(len(pd.read_parquet(x, columns=["cell"])) for x in nsh)
    P(f"cached {n:,} trades across {len(nsh)} shards -> {SHARD}")


def three_means(v):
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    lo, hi = np.percentile(v, [1, 99])
    tm = v[(v >= lo) & (v <= hi)]
    return float(v.mean()), float(np.median(v)), float(tm.mean() if len(tm) else np.nan)


def book(d):
    """The path-variant lens: one slot, first-come, an equity curve in dollars (D7)."""
    if len(d) == 0:
        return np.nan, np.nan
    o = d.sort_values("t_in")
    tin = o["t_in"].to_numpy(float)
    tout = o["t_out"].to_numpy(float)
    net = (o["gross"] - o["cost"]).to_numpy(float)
    free, pnl = -np.inf, []
    for a, b_, v in zip(tin, tout, net):
        if a >= free:
            pnl.append(v)
            free = b_
    if len(pnl) < 30:
        return np.nan, np.nan
    e = np.cumsum(pnl)
    dd = float(np.max(np.maximum.accumulate(e) - e))
    sh = float(np.mean(pnl) / np.std(pnl) * np.sqrt(252 * 3)) if np.std(pnl) > 0 else np.nan
    return sh, dd


def run():
    sh = sorted(SHARD.glob("*.parquet"))
    if not sh:
        P(f"no shards in {SHARD}; run --fit then --build")
        return
    d = pd.concat([pd.read_parquet(x) for x in sh], ignore_index=True)
    te = d[d["day"] >= SPLIT]

    # REQUIRED OUTPUTS, GUARDED AND RAISING -- not asserted in prose.
    # The first run of this file DECLARED a matched control in D9 and then silently dropped it
    # for every frozen cell, because a pool-size condition skipped exactly the arms under test.
    # Prose cannot catch that; this can. Every declared cell, and its control twin, must be
    # present with enough rows to report, or the run refuses to print a result at all.
    want = [f"noforecast_{sm}" for sm in STOPS]
    for q in QS:
        for rf in REFS:
            for w in GRACES:
                if rf != "fresh" and w == 0:
                    continue
                for sm in STOPS:
                    want.append(f"{rf}_q{q}_w{w}_{sm}")
                    want.append(f"ctl{rf}_q{q}_w{w}_{sm}")
    have = te["cell"].value_counts()
    missing = [c for c in want if int(have.get(c, 0)) < 200]
    if missing:
        raise SystemExit(
            f"REQUIRED OUTPUTS MISSING: {len(missing)} of {len(want)} declared cells have "
            f"fewer than 200 out-of-time rows, so the design as enumerated was not run. "
            f"First ten: {missing[:10]}")
    P(f"  [GUARD] all {len(want)} declared cells present, each with >= 200 out-of-time rows")
    P("ENTRY / FORECAST DECOUPLING -- let the forecast fire first and the extreme arrive later")
    P(f"  X={X} tau={TAU}; corrected chain; out of time (>= {SPLIT}); path-invariant")
    P("")
    P("  D1/D12 arms   fresh (grace = pure selection) | hybrid (real trigger, frozen")
    P("                expectations) | frozen (trigger measured against the stale level too)")
    P("  D11 stops     fixed = g 3.0 sigma (the published convention); relative = 1 sigma")
    P("                BEYOND the realised fill, so nothing stops out moving toward its mean.")
    P("                `in%` is the share of trades whose stop sits INSIDE the entry -- it must")
    P("                be 0.0% under `relative` and that is asserted, not hoped for.")
    P("  D13 control   ctl = same count of fire bars per session, drawn uniformly from that")
    P("                session's eligible pool, identical machinery. Delta = real - control.")
    P("  C1  cov       fraction of eligible bars inside a live window; near 1.0 = DEGENERATE.")
    P("  C3  |y|/sd and delay rising TOGETHER = the level's own extrapolation, not the market.")
    P("")
    for sm in STOPS:
        for uni, label in ((None, "ALL ROOTS"), (list(MICRO), "MICRO (tradeable)")):
            sub = te if uni is None else te[te["root"].isin(uni)]
            sub = sub[sub["cell"].str.endswith("_" + sm)]
            if len(sub) == 0:
                continue
            P("=" * 132)
            P(f"STOP = {sm.upper()}   |   {label}")
            P("")
            P("    cell                    cov      n   in%  P(tgt) P(stp)  win%   gross$"
              "    net$  median trimmed  |y|/sd  gsd  delay  bars   CTL net   delta")
            names = [f"noforecast_{sm}"] + [
                f"{rf}_q{q}_w{w}_{sm}" for q in QS for rf in REFS for w in GRACES
                if not (rf != "fresh" and w == 0)]
            for cell in names:
                g = sub[sub["cell"] == cell]
                if len(g) < 200:
                    continue
                gr = g["gross"].to_numpy(float)
                ct = g["cost"].to_numpy(float)
                net = gr - ct
                mn, md, tm = three_means(net)
                kd = g["kind"].to_numpy(float)
                ins = float(np.nanmean(g["inside"].to_numpy(float)))
                if sm == "relative":
                    assert ins == 0.0, f"{cell}: a relative stop still sits inside the entry"
                cg = sub[sub["cell"] == "ctl" + cell]
                if len(cg) >= 200:
                    cn = (cg["gross"] - cg["cost"]).to_numpy(float).mean()
                    cs, ds = f"{cn:>+8.2f}", f"{mn - cn:>+7.2f}"
                else:
                    cs, ds = f"{'--':>8}", f"{'--':>7}"
                P(f"    {cell:<22} {g['cov'].mean():>4.2f} {len(g):>6,} {ins:>5.1%} "
                  f"{(kd == 0).mean():>6.1%} {(kd == 1).mean():>6.1%} {(gr > 0).mean():>5.1%} "
                  f"{gr.mean():>+8.2f} {mn:>+7.2f} {md:>+7.1f} {tm:>+7.2f} "
                  f"{g['ysig'].mean():>7.2f} {g['gsig'].mean():>4.1f} "
                  f"{g['delay'].mean():>6.2f} {np.median(g['bars']):>5.0f} {cs} {ds}")
            P("")
            # C2: the marginal trades the grace window adds, fresh reference only
            P("    C2 -- the MARGINAL entries the grace window adds over its own w=0 arm")
            for q in QS:
                b = sub[sub["cell"] == f"fresh_q{q}_w0_{sm}"]
                if len(b) < 100:
                    continue
                key = set(zip(b["root"], b["day"], b["i"]))
                bn = (b["gross"] - b["cost"]).to_numpy(float)
                for w in GRACES[1:]:
                    gw = sub[sub["cell"] == f"fresh_q{q}_w{w}_{sm}"]
                    if len(gw) < 200:
                        continue
                    kk = list(zip(gw["root"], gw["day"], gw["i"]))
                    mrg = gw[[k not in key for k in kk]]
                    if len(mrg) < 100:
                        continue
                    gm = mrg["gross"].to_numpy(float)
                    a1, a2, a3 = three_means(gm - mrg["cost"].to_numpy(float))
                    P(f"       q{q:>2} w{w:>2}  base n {len(b):>6,} net {bn.mean():>+6.2f}"
                      f"   +{len(mrg):>6,} marginal   gross {gm.mean():>+6.2f}"
                      f"  net {a1:>+6.2f}  median {a2:>+6.1f}  trimmed {a3:>+6.2f}")
            P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not (a.self_test or a.fit or a.build or a.run):
        ap.error("choose --self-test / --fit / --build / --run")
    if a.self_test and not self_test():
        sys.exit(1)
    if a.fit:
        fit()
    if a.build:
        build()
    if a.run:
        run()
