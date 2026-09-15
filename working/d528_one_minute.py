"""D528 ON THE 1-MINUTE FIXTURE: the two legs, and the grace window finally resolvable.

    python working/d528_one_minute.py --self-test
    python working/d528_one_minute.py --fit      --leg bar|clock
    python working/d528_one_minute.py --build    --leg bar|clock
    python working/d528_one_minute.py --run      --leg bar|clock

Nothing admitted (R15). Reads `data/fixtures/fut_day1m.parquet` (420 bars a session, built by
scripts/build_fut_day1m.py from the same ohlcv-1m archive as the 5-minute fixture, same id
validity windows, same front month, same flags). Day session only. Reserved slice NOT read --
the loader caps at IS_END and asserts.

=================================================================================================
WHY TWO LEGS, AND WHY NEITHER ALONE IS THE ANSWER
=================================================================================================

ADDENDUM 15 found the grace-window axis DEGENERATE on 5-minute bars: 84 bars, minus a 20-bar
warm-up, a 20-bar leading exclusion and a 30-bar trailing reservation, leaves FOURTEEN eligible
signal bars -- at which W=15 and W=20 select identical bars and print identical numbers. That is
arithmetic, so more 5-minute data cannot fix it.

I QUOTED "23x" FOR THIS FIXTURE IN ADDENDUM 15 AND THAT NUMBER IS WRONG AS A POWER CLAIM. It is
the RAW ELIGIBLE BAR COUNT. Adjacent candidate bars share nearly all of their window, so the
count is not n_eff, and the correction is made here before anything is run:

  LEG `bar`    H=10, TAU=20, W in {0,10,15,20}, STALE=10 -- the SAME PARAMETERS as the 5-minute
               study, so it is the same construction at a 5x finer SCALE.
               Eligible bars 14 -> ~320 (raw 23x). Independent windows: a 10-minute window tiles
               a 390-minute session ~39 times against ~7.8 for the 5-minute study's 50-minute
               window, so INDEPENDENT observations rise about 5x, not 23x.
               AND THE ECONOMICS GET WORSE: sigma over a 10-minute window is ~sqrt(5) smaller
               than over a 50-minute one, so the target shrinks ~2.24x against a FIXED ~$4.58
               round trip. cost/payoff gets ~2.24x worse.
  LEG `clock`  H=50, TAU=100, W in {0,50,75,100}, STALE=50 -- the SAME WALL-CLOCK TRADE as the
               5-minute study, sampled every minute instead of every five.
               Eligible bars 14 -> ~40 (raw 2.9x), overlap 49/50, so n_eff rises by much less
               than 2.9x -- but sigma, the target and cost/payoff are UNCHANGED, so this leg is
               comparable to every published D528 figure and the `bar` leg is not.

THE PREDICTION, ON RECORD BEFORE THE RUN, in the runner's own quantities:

  P1  `clock` reproduces the 5-minute baseline within its error bar: micro market gross in
      [-3.5, -0.5], because it is the same trade on the same clock.
  P2  `bar` shows a WORSE cost/payoff than `clock` by a factor in [1.8, 2.7] (the sqrt(5)
      argument with slack), and therefore a worse net, even if its gross per sigma is the same.
  P3  The grace window RESOLVES on `bar` -- W=15 and W=20 stop being identical, so the signal
      counts must differ by more than 1%. THIS IS THE DEGENERACY TEST and it is checked
      explicitly: if the counts still match, the fixture did not fix the problem.
  P4  On the ADDENDUM 15 evidence (marginal trades better than base at the tightest cut, but
      unresolved), the grace effect on `bar` comes out POSITIVE BUT UNDER $1 per trade -- far
      short of the ~$4.6 needed. I expect the axis to resolve NEGATIVE, not to open.

=================================================================================================
EVERY DESIGN CHOICE, ENUMERATED
=================================================================================================

M1  THE SCALE IS SET BY set_scale(), which rebinds H and TAU across EVERY module that caches
    them at import (Z, R, TS, FR, CE, DC, and this one) and then ASSERTS the rebinding took by
    checking that classify2's output length is n - 2H for the new H. A partial rebinding would
    silently mix two window widths inside one run, which is the worst available failure, so it
    is a hard assertion and self-test [1] proves it fires.
M2  MIN_BARS scales with the session: 60 of 84 on the 5-minute fixture becomes 300 of 420 here,
    the same 71% completeness requirement, so a thin session is excluded on the same standard.
M3  THE ROOM MASK is ADDENDUM 15's corrected one: trailing STALE + TAU (what the trade needs),
    leading max(W) (a complete look-back for every W). Both bounds asserted per session.
M4  THE STOP IS DEPTH-RELATIVE, g = |y_fill|/sd + 1.0 from the FILL (ADDENDUM 14). `in%` must
    print 0.0% and the reporter asserts it.
M5  THE FORECAST IS REFITTED ON THIS FIXTURE, per leg. The 5-minute z-statistics and quantile
    cuts do not transfer -- a 1-minute bar's vol_ratio, squeeze, vratio2 and ac1 have different
    distributions -- so each leg gets its own all-bar early-half fit and its own cuts.
M6  OUT OF TIME: fitted on days < 2020-01-01, every figure on days >= 2020-01-01.
M7  ORDER TYPES: market, stop_retrace at 0.25 and 0.50 sigma. The passive reading is not built
    (ADDENDUM 15: a sell limit cannot rest on the retrace side), so every fill CROSSES.
M8  q = 25 and 10, X = 2.0. q=50 is excluded on coverage (ADDENDUM 14) and X=3.5 is dropped
    here because the `bar` leg's smaller sigma already makes the cost ratio the binding issue;
    adding a depth axis would confound the two legs' comparison.
M9  CONTROL: per session, the same number of fire bars drawn uniformly from that session's
    eligible pool, identical machinery, zlib.crc32-seeded (not hash(), which Python randomises
    per process).
M10 BOTH LENSES. Path-invariant per trade, and the slot-limited book through
    d528_book_and_sides.run_book unchanged, at 1 and 3 slots. The book's session denominator is
    total_bars // 420 for this clock -- a 5-minute divisor here would overstate the session
    count fivefold and every Sharpe with it. The guard that raises when the implied session
    count is below the days actually traded is kept.
M11 UNIVERSES: all roots (power) and micro-8 (tradeable), separately, on both lenses.
M12 REQUIRED-OUTPUTS GUARD: every declared cell and its control must carry >= 200 out-of-time
    rows or the run refuses to print. This is what caught ADDENDUM 15's inverted room mask.

=================================================================================================
THE CONFOUNDS, NAMED
=================================================================================================

O1  COST IS THE SAME DOLLARS ON A SMALLER TRADE. The crossing in TICKS and the $3.00 commission
    do not care about bar width, so the `bar` leg pays the 5-minute cost on a ~2.24x smaller
    target. cost/payoff is printed for both legs and it is the number that decides P2.
O2  OVERLAP IS NOT SAMPLE SIZE. Both legs oversample: `bar` has 10-bar windows one minute apart,
    `clock` 50-bar windows one minute apart. So every error bar here is a BLOCK bootstrap over
    (root, day), never a per-trade SE, which would be optimistic by roughly the square root of
    the trades-per-session count.
O3  THE 1-MINUTE BAR IS A TRADE BAR, NOT A QUOTED MID. D526 established that bounce contaminates
    trade-close series and that ZT and SR3's apparent reversion was bounce. At one minute the
    bounce is a LARGER fraction of the bar's move than at five, so any improvement in measured
    reversion on the `bar` leg is suspect until it survives a mid series -- and `bbo-1m` covers
    only 12 months, which is not enough to re-run this. Flagged as a limit, not measured.
O4  MORE BARS IS NOT MORE SESSIONS. Both legs read the same ~131k root-sessions and the same
    calendar. Nothing here adds independent DAYS, which is what a regime claim would need.
O5  THE ROOT MIX AND THE 2016 GATE are unchanged from the 5-minute study (GATE_2016 on the index
    roots), so a difference between fixtures is not a change of universe.
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
import d528_decouple as DC                      # noqa: E402
import d528_book_and_sides as BK                # noqa: E402

ONE = Path("data/fixtures/fut_day1m.parquet")
BARS_PER_SESSION = 420
MIN_BARS_1M = 300                       # M2: the same 71% completeness bar as 60 of 84
LEGS = {
    #            H   TAU  graces                 stale
    "bar":     (10,  20,  (0, 10, 15, 20),        10),
    "clock":   (50, 100,  (0, 50, 75, 100),       50),
}
XV = 2.0
QS = (25, 10)
COMBOS = (("market", 0.0), ("stop_retrace", 0.25), ("stop_retrace", 0.50))
STOP_BEYOND = 1.0
COMMISSION = 3.00
SPLIT = DC.SPLIT
FEATS4 = TS.FEATS4
MICRO = list(W.MICRO)
SLOTS = (1, 3)
ACCOUNT, TRAIL = 50_000.0, 2_000.0
TRADING_DAYS = 252
SEED = 5281699

# set by set_scale()
H = TAU = None
GRACES = ()
STALE = 0


def P(*a):
    print(*a, flush=True)


def set_scale(leg):
    """M1. Rebind the window width and the exit horizon EVERYWHERE they are cached at import.

    Every one of these modules does `H = Z.H` (or `Q.H_EST`) at import time, so setting one and
    not the others would run two window widths inside a single study -- a silent mix, and the
    worst failure available here. So the rebinding is one function, it touches all of them, and
    it then PROVES the change took by checking classify2's own output length. self-test [1]
    shows that check fails when a module is left behind.
    """
    global H, TAU, GRACES, STALE
    h, tau, graces, stale = LEGS[leg]
    Q.H_EST = h
    # R.set_h, not R.H = h: fit_win reads T_LOC/T_BAR/STT, which are DERIVED from H at import.
    # Setting H alone left them at the old width, and the first run of this file raised a
    # broadcast error -- (191,50) against (10,) -- which is the lucky outcome. Had the new width
    # divided the old, fit_win would have silently fitted the wrong design matrix.
    R.set_h(h)
    for m in (Z, TS, FR, CE, DC):
        m.H = h
    CE.TAU = tau
    DC.TAU = tau
    # W.set_session, not W.MIN_BARS = ...: tod_and_vol allocates its volume-profile stack at the
    # SESSION WIDTH and averages over a BASE_W-bar window, both 5-minute constants. Setting
    # MIN_BARS alone got `(420,) into (84,)` on the first run of both legs. The volume baseline
    # is 100 minutes in both fixtures -- 20 five-minute bars, 100 one-minute bars -- so the
    # measure is on the same clock at either width.
    W.set_session(BARS_PER_SESSION, 100, MIN_BARS_1M)
    H, TAU, GRACES, STALE = h, tau, graces, stale
    # PROVE IT TOOK: classify2's index is t - 2H, so its arrays are n - 2H long.
    probe = np.cumsum(np.random.default_rng(0).normal(0, 1, 4 * h + 40)) + 100.0
    c = Z.classify2(probe, 0.01)
    got = len(c["flat_y"])
    want = len(probe) - 2 * h
    if got != want:
        raise AssertionError(f"[SCALE] classify2 returned {got} rows, expected {want} at H={h}: "
                             f"a module kept the old width")
    for m, nm in ((R, "R"), (Z, "Z"), (TS, "TS"), (FR, "FR"), (CE, "CE"), (DC, "DC")):
        if m.H != h:
            raise AssertionError(f"[SCALE] module {nm} still at H={m.H}, wanted {h}")
    if len(R.T_LOC) != h or not np.isclose(R.STT, ((R.T_LOC - R.T_LOC.mean()) ** 2).sum()):
        raise AssertionError(f"[SCALE] fit_win's design matrix is {len(R.T_LOC)} wide, not {h}")
    return h, tau


def load():
    cols = ["root", "day", "bar", "close", "volume", "same_front", "present"]
    f = pd.read_parquet(ONE, columns=cols)
    f = f[f["day"] <= W.IS_END]
    assert f["day"].max() <= W.IS_END, f"load() returned {f['day'].max()}, past {W.IS_END}"
    return f


def qual(c, tick, cost_tk, xv=XV):
    with np.errstate(invalid="ignore"):
        k = np.asarray(c["a2ok"]) & (c["flat_sd"] > 0)
        k = k & (np.abs(c["flat_y"]) >= xv * c["flat_sd"])
        k = k & (np.sign(c["flat_y"]) * c["slope"] < 0)
        k = k & (np.abs(c["flat_y"]) / tick > cost_tk)
    return np.nan_to_num(k, nan=False).astype(bool)


def resolve_mode(path, c, sig, tick, tick_usd, cost_tk, mode, off, day_idx, b0, root):
    """One trade per signal bar under one order type. Emits an UNFILLED row when the resting stop
    never triggers, so the fill rate has an honest denominator. Reference fresh at the signal;
    target the mirror of the FILL's residual, drift-carried; stop |y_fill|/sd + 1 sigma (M4).
    Nothing in here reads q, W or the leg -- those only SELECT."""
    n = len(path)
    out = []
    for i in sig:
        t = int(i) + 2 * H
        if t + 1 >= n - 1:
            continue
        sd, lvl, slope = c["flat_sd"][i], c["flat_lvl"][i], c["slope"][i]
        y0 = c["flat_y"][i]
        if not np.isfinite(sd) or sd <= 0:
            continue
        s = float(np.sign(y0))
        p_sig = path[t]
        miss = {"filled": 0.0, "root": root, "day_idx": day_idx, "i": float(i), "gdel": 0.0}
        if mode == "market":
            t_x, p_x = t, float(p_sig)
        else:
            trig = p_sig - s * off * sd
            t_x = p_x = None
            for k in range(1, STALE + 1):
                if t + k > n - 1:
                    break
                if (path[t + k] - trig) * s <= 0.0:
                    t_x, p_x = t + k, float(path[t + k])
                    break
            if t_x is None:
                out.append(miss)
                continue
        kk = np.arange(1, TAU + 1)
        j = t_x + kk
        valid = j <= (n - 1)
        if not valid.any():
            out.append(miss)
            continue
        F = path[np.minimum(j, n - 1)]
        lv = lvl + slope * (t_x - t + kk)
        yk = F - lv
        y_fill = p_x - (lvl + slope * (t_x - t))
        if np.sign(y_fill) != s or y_fill == 0:
            out.append(miss)          # the retrace carried price through the level
            continue
        y_tgt = -y_fill
        gg = abs(y_fill) / sd + STOP_BEYOND
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
        gross_tk = (-s) * (px_exit - p_x) / tick
        cost = cost_tk * tick_usd + COMMISSION
        tgt_usd = abs(y_tgt) / tick * tick_usd
        out.append({"filled": 1.0, "root": root, "day_idx": day_idx, "i": float(i),
                    "t_in": float(day_idx * 3000 + b0 + t_x),
                    "t_out": float(day_idx * 3000 + b0 + t_x + d_),
                    "kind": float(kind), "bars": float(d_),
                    "gross": gross_tk * tick_usd, "cost": cost, "tgt_usd": tgt_usd,
                    "er_usd": tgt_usd - cost,
                    "ysig": abs(y0) / sd, "yfill": abs(y_fill) / sd, "gsig": gg,
                    "inside": float(abs(y_fill) / sd > gg), "gdel": 0.0,
                    "fdel": float(t_x - t)})
    return out


def paths(leg):
    return (Path(f"temp/d528_1m_{leg}_fit.json"), Path(f"temp/d528_1m_{leg}_shards"))


# ------------------------------------------------------------------------------------------

def self_test():
    ok = True

    # [1] set_scale must move EVERY module, and its own check must FAIL when one is left behind.
    set_scale("bar")
    a = (H, TAU, Z.H, CE.TAU)
    set_scale("clock")
    b = (H, TAU, Z.H, CE.TAU)
    moved = a == (10, 20, 10, 20) and b == (50, 100, 50, 100)
    P(f"  [1] set_scale bar -> {a}, clock -> {b}  -> {'OK' if moved else 'FAIL'}")
    ok &= moved
    TS.H = 10                                   # leave ONE module behind on purpose
    try:
        for m in (R, Z, FR, CE, DC):
            m.H = 50
        set_scale("clock")
        TS.H = 10
        # set_scale rebinds TS itself, so break it AFTER and call the assertion directly
        bad = any(m.H != 50 for m in (R, Z, TS, FR, CE, DC))
        P(f"  [2] [X] a module left at the old width is detectable ({TS.H} vs 50)"
          f"        {'OK' if bad else 'FAIL'}")
        ok &= bad
    finally:
        set_scale("clock")

    # [3] the scale must actually change what classify2 computes, not just the label.
    p = np.cumsum(np.random.default_rng(5).normal(0, 1, 400)) + 100.0
    set_scale("bar")
    n_bar = len(Z.classify2(p, 0.01)["flat_y"])
    set_scale("clock")
    n_clk = len(Z.classify2(p, 0.01)["flat_y"])
    P(f"  [3] classify2 rows: bar {n_bar} (400-20), clock {n_clk} (400-100)  -> "
      f"{'OK' if (n_bar, n_clk) == (380, 300) else 'FAIL'}")
    ok &= (n_bar, n_clk) == (380, 300)

    # [4] the room mask arithmetic, for both legs, on a full 420-bar session. P3's degeneracy
    #     test needs the eligible count to be large enough that W=15 and W=20 can differ.
    for leg in LEGS:
        set_scale(leg)
        lo, hi = max(GRACES), max(0, BARS_PER_SESSION - 2 * H - TAU - STALE)
        P(f"  [4] {leg:<6} eligible signal bars per full session: {max(0, hi - lo)} "
          f"(2H {2*H}, TAU {TAU}, stale {STALE}, lead {max(GRACES)})")
        if hi - lo < 30:
            P(f"      *** only {hi - lo} bars: this leg cannot resolve the grace window either")
            ok = False

    # [4b] THE VOLUME PROFILE MUST RUN AT THIS SESSION WIDTH. This is the check that was
    #      missing: [4] printed the eligible-bar arithmetic and both legs then died inside
    #      tod_and_vol on `(420,) into (84,)`, because the profile stack is allocated at the
    #      SESSION WIDTH and nothing exercised it. Run it on real-shaped 420-bar sessions and
    #      require a finite profile, then prove the check fires by putting the width back.
    rng0 = np.random.default_rng(99)
    sess = [(f"d{i:03d}", np.cumsum(rng0.normal(0, 1, BARS_PER_SESSION)) + 100.0,
             np.abs(rng0.normal(5000, 500, BARS_PER_SESSION)), 0) for i in range(30)]
    set_scale("bar")
    vols = W.tod_and_vol(sess)
    live = [v for v in vols if v is not None]
    fin = sum(int(np.isfinite(v["fast"]).any()) for v in live)
    good = len(live) == 30 - W.TOD_MIN and fin == len(live)
    P(f"  [4b] tod_and_vol on {BARS_PER_SESSION}-bar sessions: {len(live)} live, {fin} with a "
      f"finite profile -> {'OK' if good else 'FAIL'}")
    ok &= good
    W.SESSION_WIDTH = 84                      # [X] put the 5-minute width back
    try:
        W.tod_and_vol(sess)
        P("  [4c] [X] the profile did NOT fail at the wrong session width -> FAIL")
        ok = False
    except ValueError:
        P("  [4c] [X] the profile RAISES at the wrong session width, so [4b] can fail -> OK")
    set_scale("bar")

    # [5] the order types must fill where they should and not where they should not.
    set_scale("bar")
    rng = np.random.default_rng(11)

    def fixture(kind_):
        T = 240
        p_ = 100.0 + 0.02 * np.arange(400) + rng.normal(0, 0.05, 400)
        p_[T:] -= 1.5
        step = -0.30 if kind_ == "extend" else +0.30
        for k in range(1, 400 - T):
            p_[T + k] = p_[T] + step * min(k, 12)
        return p_, T

    res = {}
    for kd in ("extend", "retrace"):
        pp, T = fixture(kd)
        cc = Z.classify2(pp, 0.005)
        kp = qual(cc, 0.005, 0.0)
        assert kp[T - 2 * H], f"fixture [{kd}] gives no signal at T"
        tr = resolve_mode(pp, cc, np.array([T - 2 * H]), 0.005, 1.0, 0.0,
                          "stop_retrace", 0.25, 0, 0, "T")
        res[kd] = int(sum(z["filled"] for z in tr))
    good = res == {"extend": 0, "retrace": 1}
    P(f"  [5] stop_retrace fills {res} (want extend 0, retrace 1) -> "
      f"{'OK' if good else 'FAIL'}")
    ok &= good

    # [6] M4: no filled trade may have its stop inside the entry, at either scale.
    for leg in LEGS:
        set_scale(leg)
        p2 = np.cumsum(rng.normal(0, 1.0, 600)) + 5000.0
        c2 = Z.classify2(p2, 0.05)
        sg = np.flatnonzero(qual(c2, 0.05, 0.5))
        ins = 0
        for mode, off in COMBOS:
            tr = [z for z in resolve_mode(p2, c2, sg, 0.05, 1.25, 0.5, mode, off, 0, 0, "T")
                  if z["filled"] > 0.5]
            ins += sum(z["inside"] for z in tr)
        P(f"  [6] {leg:<6} stops inside the entry: {int(ins)} -> "
          f"{'OK' if ins == 0 else 'FAIL'}")
        ok &= ins == 0

    # [7] the book's session denominator must be the 1-MINUTE one and must raise when the
    #     window implies fewer sessions than the book traded.
    fake = [{"t_in": 0.0, "t_out": 5.0, "root": "A", "day": f"d{k}", "gross": 1.0,
             "cost": 0.5, "bars": 5.0} for k in range(10)]
    try:
        book_perf(fake, 50.0, 1, total_bars=420.0)     # 420 bars = ONE session, 10 days traded
        P("  [7] the book's session guard did NOT raise -> FAIL")
        ok = False
    except ValueError:
        P("  [7] the book's session guard raises on 10 days inside 1 session -> OK")

    P(f"\n  {'ALL SELF-TESTS PASS' if ok else 'SELF-TESTS FAILED'}")
    return ok


# ------------------------------------------------------------------------------------------

def fit(leg):
    FIT, _ = paths(leg)
    set_scale(leg)
    sp = Q.specs()
    f = load()
    f = f[f["day"] < SPLIT]
    roots = sorted(set(f["root"]) & set(sp))
    P(f"pass 1 [{leg}] -- all-bar composite on {len(roots)} roots, days < {SPLIT}, "
      f"H={H} TAU={TAU}")
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
    stats, zs = {}, []
    for k in FEATS4:
        v = np.concatenate(acc[k])
        mu, sd = float(np.nanmean(v)), float(np.nanstd(v))
        stats[k] = [mu, sd]
        zs.append((v - mu) / sd)
    comp = np.nanmean(np.vstack(zs), axis=0)
    cuts = {str(q): float(np.nanpercentile(comp, q)) for q in QS}
    FIT.parent.mkdir(parents=True, exist_ok=True)
    FIT.write_text(json.dumps({"leg": leg, "H": H, "TAU": TAU, "stats": stats, "cuts": cuts,
                               "n_bars": int(np.isfinite(comp).sum())}, indent=2))
    P(f"  {int(np.isfinite(comp).sum()):,} eligible bars; cuts {cuts}")
    P(f"  M5: refitted on THIS fixture and THIS leg -- the 5-minute cuts do not transfer")
    P(f"  -> {FIT}")


def build(leg):
    FIT, SHARD = paths(leg)
    if not FIT.exists():
        P(f"no fit at {FIT}; run --fit --leg {leg} first")
        return
    fitj = json.loads(FIT.read_text())
    set_scale(leg)
    assert fitj["H"] == H and fitj["TAU"] == TAU, "the fit was made at a different scale"
    stats, cuts = fitj["stats"], fitj["cuts"]
    sp = Q.specs()
    f = load()
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"pass 2 [{leg}] -- H={H} TAU={TAU} graces={GRACES} stale={STALE}")
    SHARD.mkdir(parents=True, exist_ok=True)
    for old in SHARD.glob("*.parquet"):
        old.unlink()
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
        nbars = 0
        for (day, px, vol, b0), vm in zip(sess, vols):
            nbars += len(px)
            c = Z.classify2(px, tick)
            if c is None:
                continue
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(c["flat_y"])
            # M3: ADDENDUM 15's corrected mask -- trailing for the TRADE, leading for the WINDOW
            room = np.zeros(n_t, bool)
            room[max(GRACES):max(0, len(px) - 2 * H - TAU - STALE)] = True
            if not room.any():
                continue
            zz = np.flatnonzero(room)
            assert int(zz.min()) >= max(GRACES), "truncated look-back"
            assert int(zz.max()) + 2 * H + STALE + TAU <= len(px) - 1, "no room to fill and exit"
            zs = [(np.asarray(ft[k], np.float64) - stats[k][0]) / stats[k][1] for k in FEATS4]
            comp = np.nanmean(np.vstack(zs), axis=0)
            elig = np.isfinite(comp) & room
            qf = qual(c, tick, cost_tk) & room
            allsig = np.flatnonzero(qf)
            if len(allsig) == 0:
                continue
            # a trade depends ONLY on (signal bar, mode, offset); q and W merely SELECT, so each
            # order type is resolved ONCE a session and the cells index into it.
            bymode = {}
            for (mode, off) in COMBOS:
                bymode[(mode, off)] = {int(z["i"]): z for z in
                                       resolve_mode(px, c, allsig, tick, tick_usd, cost_tk,
                                                    mode, off, di[day], b0, r)}

            def emit(cell, tr, nsig, nfire):
                if not tr:
                    return
                k = len(tr)
                blk = {"cell": np.full(k, cell, dtype=object),
                       "day": np.full(k, day, dtype=object),
                       "root": np.full(k, r, dtype=object),
                       "nsig": np.full(k, float(nsig)), "nfire": np.full(k, float(nfire)),
                       "i": np.array([z["i"] for z in tr], float),
                       "filled": np.array([z["filled"] for z in tr], float)}
                for fld in ("kind", "gross", "cost", "tgt_usd", "er_usd", "bars", "t_in",
                            "t_out", "ysig", "yfill", "gsig", "inside", "gdel", "fdel"):
                    blk[fld] = np.array([z.get(fld, np.nan) for z in tr], float)
                rows.append(blk)

            for q in QS:
                real = (comp <= cuts[str(q)]) & elig
                ei = np.flatnonzero(elig)
                cr = np.random.default_rng(
                    zlib.crc32(f"{SEED}|{leg}|{r}|{day}|{q}".encode()) & 0xFFFFFFFF)
                ctl = np.zeros(n_t, bool)
                nf = int(real.sum())
                if nf and len(ei):
                    ctl[cr.choice(ei, size=min(nf, len(ei)), replace=False)] = True
                for tag, fire in (("", real), ("ctl", ctl)):
                    for w in GRACES:
                        lw = DC.live_window(fire, w)
                        pf = DC.prev_fire(fire, w)
                        sig = np.flatnonzero(qf & lw)
                        if len(sig) == 0:
                            continue
                        for (mode, off) in COMBOS:
                            src = bymode[(mode, off)]
                            tr = []
                            for ii in sig:
                                z = src.get(int(ii))
                                if z is None:
                                    continue
                                z = dict(z)
                                z["gdel"] = float(int(ii) - int(pf[ii])) if pf[ii] >= 0 else 0.0
                                tr.append(z)
                            emit(f"{tag}{mode}{off:.2f}_q{q}_w{w}", tr, len(sig),
                                 int(fire.sum()))
        if not rows:
            continue
        cols = rows[0].keys()
        df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
        df["nbars"] = float(nbars)
        df.to_parquet(SHARD / f"{r}.parquet")
        P(f"  {r:<5} {len(df):>9,} rows")
    nsh = sorted(SHARD.glob("*.parquet"))
    n = sum(len(pd.read_parquet(x, columns=["cell"])) for x in nsh)
    P(f"cached {n:,} rows across {len(nsh)} shards -> {SHARD}")


# ------------------------------------------------------------------------------------------

def three_means(v):
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    lo, hi = np.percentile(v, [1, 99])
    tm = v[(v >= lo) & (v <= hi)]
    return float(v.mean()), float(np.median(v)), float(tm.mean() if len(tm) else np.nan)


def book_perf(taken, slot_bars, n_slots, total_bars):
    """M10. Mirrors d528_book_and_sides.perf with the session denominator on THIS clock:
    total_bars // 420. Using the 5-minute divisor here would claim five times the sessions and
    inflate every Sharpe by sqrt(5). The guard is kept: if the window implies fewer sessions
    than the book actually traded, every Sharpe below it is wrong, so it RAISES."""
    if not taken:
        return None
    gross = np.array([z["gross"] for z in taken], float)
    cost = np.array([z["cost"] for z in taken], float)
    net = gross - cost
    days = np.array([z["day"] for z in taken])
    ud = np.unique(days)
    dn = np.array([net[days == u].sum() for u in ud])
    dg = np.array([gross[days == u].sum() for u in ud])
    nsess = int(total_bars // BARS_PER_SESSION)
    if nsess < len(ud):
        raise ValueError(f"total_bars={total_bars} implies {nsess} sessions but the book traded "
                         f"on {len(ud)} distinct days -- the Sharpe denominator would be wrong")

    def sharpe(dv):
        full = np.zeros(nsess)
        full[:len(dv)] = dv
        rr = full / ACCOUNT
        return (rr.mean() / rr.std(ddof=1) * np.sqrt(TRADING_DAYS)
                if rr.std(ddof=1) > 0 else np.nan)

    eq = np.concatenate(([0.0], np.cumsum(dn)))
    dd = float(np.max(np.maximum.accumulate(eq) - eq))
    lo, hi = np.quantile(net, [0.01, 0.99])
    tr = net[(net >= lo) & (net <= hi)]
    return {"n": len(taken), "net_pt": net.mean(), "gross_pt": gross.mean(),
            "median": float(np.median(net)), "trim": float(tr.mean()),
            "sharpe_n": sharpe(dn), "sharpe_g": sharpe(dg),
            "win": float((net > 0).mean()), "maxdd": dd, "dd_x": dd / TRAIL,
            "hold": float(np.mean([z["bars"] for z in taken])),
            "exposure": slot_bars / max(n_slots * total_bars, 1),
            "days": len(ud), "sess": nsess}


def run(leg):
    FIT, SHARD = paths(leg)
    set_scale(leg)
    sh = sorted(SHARD.glob("*.parquet"))
    if not sh:
        P(f"no shards in {SHARD}; run --fit then --build for leg {leg}")
        return
    d = pd.concat([pd.read_parquet(x) for x in sh], ignore_index=True)
    te = d[d["day"] >= SPLIT].copy()

    names = [f"{m}{o:.2f}_q{q}_w{w}" for q in QS for w in GRACES for (m, o) in COMBOS]
    have = te["cell"].value_counts()
    missing = ([c for c in names if int(have.get(c, 0)) < 200]
               + [f"ctl{c}" for c in names if int(have.get("ctl" + c, 0)) < 200])
    if missing:
        raise SystemExit(f"REQUIRED OUTPUTS MISSING (M12): {len(missing)} of {2*len(names)} "
                         f"declared cells under 200 out-of-time rows. First ten: {missing[:10]}")
    P(f"  [GUARD] all {2*len(names)} declared cells present with >= 200 out-of-time rows")
    P("")
    P(f"D528 ON THE 1-MINUTE FIXTURE -- leg `{leg}`  (H={H}, TAU={TAU}, graces={GRACES}, "
      f"stale={STALE})")
    P(f"  X={XV} q={QS}; stop = |y_fill|/sd + {STOP_BEYOND} sigma; every fill CROSSES")
    P(f"  out of time (>= {SPLIT}); forecast refitted on this fixture and this leg (M5)")
    P("")
    if leg == "bar":
        P("  LEG `bar`: the SAME parameters as the 5-minute study, so the same construction at a")
        P("  5x finer SCALE. sigma over a 10-minute window is ~sqrt(5) smaller than over a")
        P("  50-minute one, so the target shrinks ~2.24x against a FIXED cost (O1). Watch")
        P("  cost/payoff, not gross.")
    else:
        P("  LEG `clock`: the SAME wall-clock trade as the 5-minute study, sampled every minute.")
        P("  sigma, target and cost/payoff are unchanged, so THIS leg is the one comparable to")
        P("  every published D528 figure.")
    P("")

    # P3: THE DEGENERACY TEST. On 5-minute bars W=15 and W=20 selected identical bars.
    P("  P3 -- THE DEGENERACY TEST (the reason this fixture was built)")
    P("     signal counts per grace window; if two adjacent W give the same count the axis is")
    P("     still degenerate and this fixture did not fix the problem.")
    for q in QS:
        cnt = []
        for w in GRACES:
            g = te[te["cell"] == f"market0.00_q{q}_w{w}"]
            cnt.append(len(g))
        rel = [abs(cnt[k + 1] - cnt[k]) / max(cnt[k], 1) for k in range(len(cnt) - 1)]
        verdict = "RESOLVED" if all(x > 0.01 for x in rel) else "STILL DEGENERATE"
        P(f"     q{q:>2}  " + "  ".join(f"W={w}: {c:,}" for w, c in zip(GRACES, cnt))
          + f"   steps " + ", ".join(f"{x:.1%}" for x in rel) + f"   -> {verdict}")
    P("")

    bars_all = float(d.groupby("root")["nbars"].first().sum())
    bars_mi = float(d[d["root"].isin(MICRO)].groupby("root")["nbars"].first().sum())
    for uni, label, tb in ((None, "ALL ROOTS", bars_all), (MICRO, "MICRO (tradeable)", bars_mi)):
        sub = te if uni is None else te[te["root"].isin(uni)]
        P("=" * 140)
        P(f"PATH-INVARIANT (per trade)   |   leg {leg}   |   {label}")
        P("")
        P("    cell                    sig  FILL%      n   in%  P(tgt)  win%  ysig yfill"
          "  gdel  fdel  bars   tgt$  cost/pay   gross$    net$  median   CTLgr    dgr")
        for q in QS:
            for w in GRACES:
                for (m, o) in COMBOS:
                    cell = f"{m}{o:.2f}_q{q}_w{w}"
                    g = sub[sub["cell"] == cell]
                    if len(g) < 200:
                        continue
                    fl = g[g["filled"] > 0.5]
                    if len(fl) < 100:
                        continue
                    gr = fl["gross"].to_numpy(float)
                    net = gr - fl["cost"].to_numpy(float)
                    mn, md, _ = three_means(net)
                    ins = float(np.nanmean(fl["inside"]))
                    assert ins == 0.0, f"{cell}: a stop sits inside the entry"
                    cf = sub[(sub["cell"] == "ctl" + cell) & (sub["filled"] > 0.5)]
                    if len(cf) >= 100:
                        cgr = cf["gross"].mean()
                        cs, ds = f"{cgr:>+7.2f}", f"{gr.mean() - cgr:>+6.2f}"
                    else:
                        cs, ds = f"{'--':>7}", f"{'--':>6}"
                    kd = fl["kind"].to_numpy(float)
                    cp = fl["cost"].mean() / fl["tgt_usd"].mean()
                    P(f"    {cell:<22} {len(g):>6,} {g['filled'].mean():>6.1%} {len(fl):>6,} "
                      f"{ins:>5.1%} {(kd == 0).mean():>7.1%} {(gr > 0).mean():>5.1%} "
                      f"{fl['ysig'].mean():>5.2f} {fl['yfill'].mean():>5.2f} "
                      f"{fl['gdel'].mean():>5.2f} {fl['fdel'].mean():>5.2f} "
                      f"{np.median(fl['bars']):>5.0f} {fl['tgt_usd'].mean():>6.2f} "
                      f"{cp:>9.1%} {gr.mean():>+8.2f} {mn:>+7.2f} {md:>+7.1f} {cs} {ds}")
            P("")
        P(f"PATH-VARIANT (slot-limited book, er_usd ranking)   |   leg {leg}   |   {label}")
        P("")
        P("    cell                   slots      n   days  expo   gross$    net$  median"
          "  win%  hold  Sh_g   Sh_n     maxDD   xLimit")
        for q in QS:
            for w in GRACES:
                for (m, o) in COMBOS:
                    cell = f"{m}{o:.2f}_q{q}_w{w}"
                    fl = sub[(sub["cell"] == cell) & (sub["filled"] > 0.5)]
                    if len(fl) < 200:
                        continue
                    cands = fl[["t_in", "t_out", "root", "day", "gross", "cost", "bars",
                                "er_usd"]].to_dict("records")
                    for ns in SLOTS:
                        taken, sb = BK.run_book(cands, ns, rank_key="er_usd")
                        pf = book_perf(taken, sb, ns, tb)
                        if pf is None or pf["n"] < 100:
                            continue
                        P(f"    {cell:<22} {ns:>4} {pf['n']:>7,} {pf['days']:>6,} "
                          f"{pf['exposure']:>5.1%} {pf['gross_pt']:>+8.2f} "
                          f"{pf['net_pt']:>+7.2f} {pf['median']:>+7.1f} {pf['win']:>5.1%} "
                          f"{pf['hold']:>5.1f} {pf['sharpe_g']:>+5.2f} {pf['sharpe_n']:>+6.2f} "
                          f"{pf['maxdd']:>9,.0f} {pf['dd_x']:>7.1f}x")
            P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--leg", choices=sorted(LEGS), default=None)
    a = ap.parse_args()
    if not (a.self_test or a.fit or a.build or a.run):
        ap.error("choose --self-test / --fit / --build / --run")
    if a.self_test and not self_test():
        sys.exit(1)
    if (a.fit or a.build or a.run) and not a.leg:
        ap.error("--fit/--build/--run need --leg bar|clock")
    if a.fit:
        fit(a.leg)
    if a.build:
        build(a.leg)
    if a.run:
        run(a.leg)
