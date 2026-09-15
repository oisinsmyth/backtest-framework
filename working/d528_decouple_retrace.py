"""THE RETRACE ORDER ON TOP OF THE DECOUPLING: forecast fires, extreme arrives later, order rests.

    python working/d528_decouple_retrace.py --self-test
    python working/d528_decouple_retrace.py --build
    python working/d528_decouple_retrace.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.
Corrected chain (slope_ok dropped, drift alignment kept -- ADDENDUM 12). Requires the all-bar
forecast fit from `d528_decouple.py --fit`.

BOTH LENSES, as the principal asked: path-invariant (every signal, no slot cap, scored per TRADE)
and path-variant (the slot-limited book, scored as an equity curve). They are NEVER compared on
the same statistic; their difference is opportunity cost (CLAUDE.md, FINDINGS 10).

ONLY stop_retrace IS BUILT. A passive `limit_bounce` reading was drafted and then removed at the
principal's instruction ("no need for the limit order, I mispoke"). Recorded because the reading
mattered: for a SHORT at the high extreme a sell LIMIT must sit AT OR ABOVE the market, so an
order that fills on a DOWNWARD retrace cannot be a resting limit -- it is a STOP, which becomes a
market order and crosses. The cost line below therefore charges the full crossing on every fill,
with no passive discount anywhere in this file.

=================================================================================================
WHAT IS BEING COMPOSED
=================================================================================================

Three clocks now stack, and the composition is the whole design:

    t_f   the forecast fires (all-bar composite in the most-forecastable q%)
    t_e   the SIGNAL bar: the first bar in [t_f, t_f + W] that closes beyond X sigma, drift
          aligned. W is the grace window -- the decoupling.
    t_x   the FILL bar: the resting stop triggers somewhere in [t_e + 1, t_e + STALE].

=================================================================================================
EVERY DESIGN CHOICE, ENUMERATED (the runner prints these beside the result)
=================================================================================================

E1  THE SIGNAL SET IS EXACTLY THE `fresh` ARM's OF d528_decouple.py -- qual_fresh & live_window
    (fire, W), one entry per bar. So at W=0 this file's `market` arm IS the ADDENDUM 14 baseline
    (self-test [1] asserts it bit-for-bit), and every order type is scored on the SAME signal
    bars. Nothing but the order type varies within a row group.

E2  THE REFERENCE IS FRESH at the signal bar. Frozen expectations were tested in ADDENDUM 14 and
    came back null -- median paired difference exactly 0.00 in all 24 cells -- so they are
    EXCLUDED rather than carried. Adding a null axis to a new test only confounds it.

E3  THE STOP IS DEPTH-RELATIVE: g = |y_fill|/sd + 1.0, measured from the FILL. ADDENDUM 14 found
    the old fixed 3.0 sigma stop sat INSIDE the entry in 27.5% of trades. It matters MORE here:
    a stop_retrace fill is already partway back to the mean, so a fixed stop would sit at a
    different place for every offset and the mode comparison would be void. `in%` must print
    0.0% in every cell and that is asserted in the reporter, not hoped for.

E4  DEPTH X = 2.0 and 3.5. Both, because the depth sweep found stop_retrace's hit x payoff peaks
    at X=3.5 while market's collapses -- depth and confirmation interact, and the grace window
    may interact with either. The (X=3.5, q=10) cell is DECLARED OUT on power before running:
    see CELLS. This is the binding limit of the whole design and it is arithmetic, not luck --
    see the note under R2.

E5  OFFSETS 0.25 and 0.50 sigma (0.50 was stop_retrace's best in the depth sweep). STALENESS 10
    bars (10 beat 5 in every ADDENDUM 13 cell).

E6  GRACE W = 0, 10, 15, 20 -- 0 as the coupled baseline, and the principal's three values.

E7  q = 25 and 10. q=50 excluded: ADDENDUM 14 measured its coverage at 0.80-0.86, so those cells
    were the unconditional construction wearing a forecast's name (C1).

E8  OUT OF TIME. Forecast means, sds and the q cut come from the ALL-BAR early-half fit
    (< 2020-01-01, 3,042,356 bars); every reported figure is on days >= 2020-01-01.

E9  CONTROL: ADDENDUM 14's corrected D13 -- per session, the same number of fire bars drawn
    uniformly from that session's eligible pool, identical machinery, seeded with zlib.crc32 (not
    hash(), which Python randomises per process). Its own ctl_ cell, so every statistic is
    computed the same way for treatment and control.

E10 THE PATH-VARIANT LEG reuses `d528_book_and_sides.run_book` UNCHANGED -- the same slot
    machinery, the same one-position-per-root rule and the same `er_usd` ranking that produced
    the D528 book figures -- at 1 and 3 slots. Its statistics mirror that file's `perf` with ONE
    change, stated because it would otherwise be a silent bug: that function divides
    total_minutes by 420 for a 1-minute clock, and this fixture is 5-minute bars, so the session
    denominator here is total_bars // 84. The guard that raises when the implied session count is
    below the number of days actually traded is kept.

E11 UNIVERSES: all roots (power) and micro-8 (tradeable), separately, on both lenses.

=================================================================================================
THE CONFOUNDS, NAMED. Six, each measured rather than argued.
=================================================================================================

R1  THE FILL RATE IS A CONDITIONAL EVENT and reporting only filled trades is survivorship. The
    runner emits an UNFILLED row for every signal whose stop never triggers, prints the fill rate
    against the SIGNAL count, and prints the signal count against the FORECAST FIRE count, so
    the whole funnel is visible. ADDENDUM 13's rule 1.

R2  THE CLOCKS STACK, AND THE FIRST VERSION OF THIS MASK WAS WRONG IN THE DIRECTION. It reserved
    max(W) bars at the END of the session for a window that looks at the BEGINNING. A backward-
    looking grace window consumes bars BEFORE the signal, so nothing forward needs reserving for
    it; what that mask actually did was keep only the FIRST 14 bars of each session -- precisely
    the bars whose look-back is truncated by the open, which is the confound it existed to
    remove. The guard caught it by refusing to print: 30 of 96 declared cells came back under
    200 rows. Corrected to
        trailing   STALE bars to fill, then TAU to exit   -- the TRADE's own requirement
        leading    max(W)                                 -- a COMPLETE look-back for every w
    and both bounds are asserted per session rather than trusted.

    THE COST OF THAT CORRECTION IS THE STUDY'S BINDING LIMIT, and it is arithmetic. An 84-bar
    session gives 64 candidate bars; 20 go to the leading exclusion and 30 to the trailing
    reservation, leaving FOURTEEN eligible signal bars a session. The grace-window design is
    therefore the one construction in D528 that the 5-minute fixture structurally cannot power,
    because every reservation is denominated in BARS and the session is only 84 of them. A
    390-bar 1-minute session leaves ~320 eligible bars -- a 23x gain on this exact design,
    against the ~5x that a bar count alone would suggest.

R3  DELAY IS TWO NUMBERS and they must be separated: `gdel` = t_e - t_f (how long the FORECAST
    waited) and `fdel` = t_x - t_e (how long the ORDER waited). "This works because a stale
    forecast still holds" and "this works because the turn confirms" are different claims and
    only these two columns tell them apart.

R4  THE RETRACE SURRENDERS PART OF THE MOVE -- the conservation of hit x payoff that has now
    defeated this construction five times. `ysig -> yfill` prints the surrender directly: a fill
    0.5 sigma back has a mirror target 0.5 sigma nearer AND a stop 0.5 sigma closer, so the dial
    moves at both ends and the product is what must be watched.

R5  THE TWO LENSES DISAGREE BY CONSTRUCTION HERE, because the modes differ in HOLDING TIME and
    in FILL DELAY. A stop_retrace signal occupies its slot from the FILL, not the signal, and
    an unfilled signal occupies nothing -- so the confirmation arm can look worse per trade and
    better per slot, or the reverse. That difference IS the opportunity cost and it is the reason
    both legs were asked for.

R6  COST IS CONSTANT ACROSS THESE MODES (every fill crosses; no passive discount), so a net
    difference between order types is a gross difference. It is NOT constant across UNIVERSES or
    across DEPTHS, so gross sits beside net in every cell regardless.
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
import d528_decouple as DC                      # noqa: E402
import d528_book_and_sides as BK                # noqa: E402

H = Z.H
TAU = 20
STOP_BEYOND = 1.0
XS = (2.0, 3.5)
QS = (25, 10)
GRACES = (0, 10, 15, 20)
STALE = 10
COMBOS = (("market", 0.0), ("stop_retrace", 0.25), ("stop_retrace", 0.50))
# THE DECLARED GRID, and (3.5, 10) is excluded A PRIORI on power, not after seeing it. With the
# corrected R2 mask an 84-bar session yields only 14 eligible signal bars; X=3.5 admits ~18% of
# X=2.0's bars and q=10 a further 40%, so that one cell lands near 100 out-of-time trades on
# micro. It is declared out rather than reported thin -- and a guard weakened until it passes is
# not a guard.
CELLS = ((2.0, 25), (2.0, 10), (3.5, 25))
COMMISSION = 3.00
SPLIT = DC.SPLIT
FEATS4 = TS.FEATS4
MICRO = list(W.MICRO)
SHARD = Path("temp/d528_dec_retrace_shards")
FIT = DC.FIT
SEED = 5281213
SLOTS = (1, 3)
BARS_PER_SESSION = 84                  # E10: this fixture's clock, not the 420 of the 1m clock
ACCOUNT, TRAIL = 50_000.0, 2_000.0
TRADING_DAYS = 252


def P(*a):
    print(*a, flush=True)


def resolve_mode(path, c, sig, tick, tick_usd, cost_tk, mode, off, day_idx, b0, root):
    """One trade per signal bar, under one order type. Emits an UNFILLED row when the resting
    stop never triggers (R1) so the fill rate has an honest denominator.

    Reference is FRESH at the signal bar (E2). Target = the MIRROR of the FILL's residual,
    drift-carried. Stop = |y_fill|/sd + STOP_BEYOND sigma, always BEYOND the fill (E3).
    """
    n = len(path)
    out = []
    for i in sig:
        t = int(i) + 2 * H                       # the bar that CLOSED beyond X sigma
        if t + 1 >= n - 1:
            continue
        sd, lvl, slope = c["flat_sd"][i], c["flat_lvl"][i], c["slope"][i]
        y0 = c["flat_y"][i]
        if not np.isfinite(sd) or sd <= 0:
            continue
        s = float(np.sign(y0))                   # +1 high extreme (short), -1 low (long)
        p_sig = path[t]
        # gdel (how long the FORECAST waited) is a property of the CELL, not of the trade, so the
        # caller attaches it. Nothing in here reads q, w or X -- see the note in build().
        miss = {"filled": 0.0, "root": root, "day_idx": day_idx, "i": float(i), "gdel": 0.0}
        if mode == "market":
            t_x, p_x = t, float(p_sig)
        else:
            # a sell STOP `off` sigma BELOW the signal close (mirrored for a long); it fills when
            # price turns back, and a triggered stop is a market order -- realised price, full
            # crossing. ADDENDUM 13 measured the idealised fill at +8.76 ticks/trade of fiction.
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
            # the retrace carried price THROUGH the level: the excursion is gone, so there is no
            # mean-reversion trade left to take. Counted as a non-fill, not as a trade -- taking
            # it would be a momentum bet wearing this construction's name.
            out.append(miss)
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
                    "t_in": float(day_idx * 2000 + b0 + t_x),
                    "t_out": float(day_idx * 2000 + b0 + t_x + d_),
                    "kind": float(kind), "bars": float(d_),
                    "gross_tk": gross_tk, "tick_usd": tick_usd,
                    "gross": gross_tk * tick_usd, "cost": cost, "tgt_usd": tgt_usd,
                    "er_usd": tgt_usd - cost,          # E10 ranking: the principal's rule
                    "ysig": abs(y0) / sd, "yfill": abs(y_fill) / sd, "gsig": gg,
                    "inside": float(abs(y_fill) / sd > gg),
                    "gdel": 0.0, "fdel": float(t_x - t)})
    return out


# ------------------------------------------------------------------------------------------

def self_test():
    rng = np.random.default_rng(11)
    ok = True
    TK = 0.05
    path = np.cumsum(rng.normal(0, 1.0, 400)) + 5000.0
    c = Z.classify2(path, TK)
    keep = DC.qual_fresh(c, TK, 0.5)
    sig = np.flatnonzero(keep)
    fo = np.full(len(keep), -1, np.int64)
    fo[sig] = sig

    # [1] market mode must reproduce d528_decouple's RELATIVE-stop resolve bit-for-bit -- that is
    #     what makes the W=0 market row the ADDENDUM 14 baseline rather than a lookalike.
    a = DC.resolve_frozen(path, c, sig, sig, TK, 1.25, 0.5, 0, 0, "T", stop_mode="relative")
    b = [z for z in resolve_mode(path, c, sig, TK, 1.25, 0.5, "market", 0.0, 0, 0, "T")
         if z["filled"] > 0.5]
    same = (len(a) == len(b) and len(a) > 5
            and all(x["gross"] == y["gross"] and x["kind"] == y["kind"]
                    and x["tgt_usd"] == y["tgt_usd"] for x, y in zip(a, b)))
    P(f"  [1] market == decouple relative-stop resolve: {len(a)} vs {len(b)} -> "
      f"{'OK' if same else 'FAIL'}")
    ok &= same

    # [2] stop_retrace must fill on an extend-then-retrace path and NOT on an extend-only one.
    #     Both directions asserted on the same fixture family: ADDENDUM 13 records a version of
    #     this check built on monotone ramps, which stop_retrace can never fill, so it printed OK
    #     on something incapable of failing.
    def fixture(kind_):
        # An up-drift with a step DOWN at T (the only geometry the drift rule sign(y)*slope < 0
        # admits, so this is a LONG). The post-T path is written DETERMINISTICALLY: the first
        # version left the fixture's own noise in, and with sigma ~0.06 a 0.25-sigma trigger is
        # 0.015 -- which the noise cleared, so the "extend" case filled and the check failed for
        # a reason that had nothing to do with the code under test.
        T = 140
        p = 100.0 + 0.02 * np.arange(200) + rng.normal(0, 0.05, 200)
        p[T:] -= 1.5
        step = -0.30 if kind_ == "extend" else +0.30
        for k in range(1, 200 - T):
            p[T + k] = p[T] + step * min(k, 12)     # monotone away from / back toward the level
        return p, T

    res = {}
    for kd in ("extend", "retrace"):
        p, T = fixture(kd)
        cc = Z.classify2(p, 0.005)
        kp = DC.qual_fresh(cc, 0.005, 0.0)
        assert kp[T - 2 * H], f"fixture [{kd}] produces no signal at T"
        iz = np.array([T - 2 * H])
        f2 = np.full(len(kp), -1, np.int64)
        f2[iz[0]] = iz[0]
        tr = resolve_mode(p, cc, iz, 0.005, 1.0, 0.0, "stop_retrace", 0.25, 0, 0, "T")
        res[kd] = int(sum(z["filled"] for z in tr))
    good = res == {"extend": 0, "retrace": 1}
    P(f"  [2] stop_retrace fills {res} (expected extend 0, retrace 1) -> "
      f"{'OK' if good else 'FAIL'}")
    ok &= good

    # [3] E3: no filled trade may have its stop inside the entry, in ANY order type.
    for mode, off in COMBOS:
        tr = [z for z in resolve_mode(path, c, sig, TK, 1.25, 0.5, mode, off, 0, 0, "T")
              if z["filled"] > 0.5]
        ins = sum(z["inside"] for z in tr)
        if ins:
            ok = False
            P(f"  [3] {mode}@{off}: {int(ins)} of {len(tr)} stops inside the entry -> FAIL")
            break
    else:
        P("  [3] no stop inside the entry in any of the three order types -> OK")

    # [4] R1: an unfilled signal must still emit a row, or the fill rate has no denominator.
    p, T = fixture("extend")
    cc = Z.classify2(p, 0.005)
    iz = np.array([T - 2 * H])
    f2 = np.full(len(DC.qual_fresh(cc, 0.005, 0.0)), -1, np.int64)
    tr = resolve_mode(p, cc, iz, 0.005, 1.0, 0.0, "stop_retrace", 0.25, 0, 0, "T")
    dn = len(tr) == 1 and tr[0]["filled"] == 0.0
    P(f"  [4] an unfilled signal emits a row ({len(tr)} rows, filled "
      f"{tr[0]['filled'] if tr else 'n/a'}) -> {'OK' if dn else 'FAIL'}")
    ok &= dn

    # [5] CAUSALITY: rewriting every bar AFTER the fill must not move the fill bar or its price.
    base = [z for z in resolve_mode(path, c, sig, TK, 1.25, 0.5, "stop_retrace", 0.50,
                                    0, 0, "T") if z["filled"] > 0.5]
    if base:
        z0 = base[0]
        cut = int(z0["i"]) + 2 * H + int(z0["fdel"])
        p3 = path.copy()
        p3[cut + 1:] = p3[cut] + np.cumsum(rng.normal(0, 8.0, len(p3) - cut - 1))
        c3 = Z.classify2(p3, TK)
        n3 = [z for z in resolve_mode(p3, c3, np.array([int(z0["i"])]), TK, 1.25, 0.5,
                                      "stop_retrace", 0.50, 0, 0, "T") if z["filled"] > 0.5]
        cau = len(n3) == 1 and n3[0]["fdel"] == z0["fdel"] and n3[0]["yfill"] == z0["yfill"]
    else:
        cau = False
    P(f"  [5] the fill bar and price survive a rewrite after the fill -> "
      f"{'OK' if cau else 'FAIL'}")
    ok &= cau

    # [6] E10: the book's session denominator must RAISE when it implies fewer sessions than the
    #     book traded. Break what the assertion reads, not its name.
    fake = [{"t_in": 0.0, "t_out": 5.0, "root": "A", "day": f"d{k}", "gross": 1.0,
             "cost": 0.5, "bars": 5.0} for k in range(10)]
    try:
        book_perf(fake, 50.0, 1, total_bars=84.0)       # 84 bars = ONE session, 10 days traded
        P("  [6] the book's session guard did NOT raise on 10 days in 1 session -> FAIL")
        ok = False
    except ValueError:
        P("  [6] the book's session guard raises on 10 days inside 1 session -> OK")

    P(f"\n  {'ALL SELF-TESTS PASS' if ok else 'SELF-TESTS FAILED'}")
    return ok


# ------------------------------------------------------------------------------------------

def build():
    if not FIT.exists():
        P(f"no forecast fit at {FIT}; run d528_decouple.py --fit first")
        return
    fitj = json.loads(FIT.read_text())
    stats, cuts = fitj["stats"], fitj["cuts"]
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"pass 2 -- {len(roots)} roots x {len(XS)} depths x {len(QS)} q x {len(GRACES)} graces "
      f"x {len(COMBOS)} order types, each with its control")
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
            # R2, CORRECTED. The first version reserved max(GRACES) bars at the END of the
            # session for a window that looks at the BEGINNING -- a backward-looking grace window
            # consumes bars BEFORE the signal, not after it. That mask kept only the first 14
            # bars of each session, which is the worst possible choice: those are exactly the
            # bars whose look-back is TRUNCATED by the session open, so W ended up maximally
            # confounded with the thing the reservation was meant to remove.
            #   trailing  the TRADE's own requirement: STALE bars to fill, then TAU to exit
            #   leading   max(GRACES), so EVERY w has a complete look-back at every eligible bar
            room = np.zeros(n_t, bool)
            room[max(GRACES):max(0, len(px) - 2 * H - TAU - STALE)] = True
            if room.any():
                z_ = np.flatnonzero(room)
                assert int(z_.min()) >= max(GRACES), "a signal bar has a truncated look-back"
                assert int(z_.max()) + 2 * H + STALE + TAU <= len(px) - 1, \
                    "a signal bar has no room to fill and exit"
            zs = [(np.asarray(ft[k], np.float64) - stats[k][0]) / stats[k][1] for k in FEATS4]
            comp = np.nanmean(np.vstack(zs), axis=0)
            elig = np.isfinite(comp) & room

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
                for fld in ("kind", "gross", "gross_tk", "tick_usd", "cost", "tgt_usd",
                            "er_usd", "bars", "t_in", "t_out", "ysig", "yfill", "gsig",
                            "inside", "gdel", "fdel"):
                    blk[fld] = np.array([z.get(fld, np.nan) for z in tr], float)
                rows.append(blk)

            quals = {xv: DC.qual_fresh(c, tick, cost_tk, xv=xv) & room for xv in XS}
            # THE OPTIMISATION, and it is also a correctness statement. A trade depends ONLY on
            # (signal bar, mode, offset): the reference is fresh at the signal bar, the target is
            # the mirror of the fill and the stop is relative to the fill, so NEITHER q, NOR w,
            # NOR X is read anywhere inside resolve_mode. q, w and X only SELECT. So each order
            # type is resolved ONCE per session over the union of signal bars and the cells index
            # into it -- 3 resolves a session instead of 96, which took the projected wall time
            # from ~22 min to under 2. The cells are therefore bit-identical to the naive
            # version by construction rather than by a tolerance.
            xmin = min(XS)
            for xv in XS:
                assert not (quals[xv] & ~quals[xmin]).any(), \
                    f"X={xv} admits a bar X={xmin} does not: the signal sets are not nested"
            allsig = np.flatnonzero(quals[xmin])
            bymode = {}
            for (mode, off) in COMBOS:
                tr = resolve_mode(px, c, allsig, tick, tick_usd, cost_tk, mode, off,
                                  di[day], b0, r)
                bymode[(mode, off)] = {int(z["i"]): z for z in tr}
            for q in QS:
                real = (comp <= cuts[str(q)]) & elig
                ei = np.flatnonzero(elig)
                cr = np.random.default_rng(
                    zlib.crc32(f"{SEED}|{r}|{day}|{q}".encode()) & 0xFFFFFFFF)
                ctl = np.zeros(n_t, bool)
                nf = int(real.sum())
                if nf and len(ei):
                    ctl[cr.choice(ei, size=min(nf, len(ei)), replace=False)] = True
                for tag, fire in (("", real), ("ctl", ctl)):
                    for w in GRACES:
                        lw = DC.live_window(fire, w)
                        pf = DC.prev_fire(fire, w)
                        for xv in XS:
                            if (xv, q) not in CELLS:
                                continue
                            sig = np.flatnonzero(quals[xv] & lw)
                            if len(sig) == 0:
                                continue
                            for (mode, off) in COMBOS:
                                src = bymode[(mode, off)]
                                # gdel is the ONE quantity that depends on the cell rather than
                                # the trade, so it is attached here from that cell's own
                                # prev_fire rather than being carried inside the resolve.
                                tr = []
                                for ii in sig:
                                    z = src.get(int(ii))
                                    if z is None:
                                        continue
                                    z = dict(z)
                                    z["gdel"] = (float(int(ii) - int(pf[ii]))
                                                 if pf[ii] >= 0 else 0.0)
                                    tr.append(z)
                                emit(f"{tag}{mode}{off:.2f}_x{xv}_q{q}_w{w}",
                                     tr, len(sig), int(fire.sum()))
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
    """Equity-curve statistics in DOLLARS, gross beside net. Mirrors
    d528_book_and_sides.perf with ONE documented change (E10): the session denominator is
    total_bars // 84 for this 5-minute fixture, where that function uses // 420 for a 1-minute
    clock. Its guard is kept -- if the window implies fewer sessions than the book actually
    traded, every Sharpe below it is wrong, so it RAISES rather than falling back.
    """
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
        raise ValueError(
            f"total_bars={total_bars} implies {nsess} sessions but the book traded on "
            f"{len(ud)} distinct days -- the Sharpe denominator would be wrong")

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


def run():
    sh = sorted(SHARD.glob("*.parquet"))
    if not sh:
        P(f"no shards in {SHARD}; run --build first")
        return
    d = pd.concat([pd.read_parquet(x) for x in sh], ignore_index=True)
    te = d[d["day"] >= SPLIT].copy()

    names = [f"{m}{o:.2f}_x{xv}_q{q}_w{w}" for (xv, q) in CELLS for w in GRACES
             for (m, o) in COMBOS]
    have = te["cell"].value_counts()
    missing = ([c for c in names if int(have.get(c, 0)) < 200]
               + [f"ctl{c}" for c in names if int(have.get("ctl" + c, 0)) < 200])
    if missing:
        raise SystemExit(f"REQUIRED OUTPUTS MISSING: {len(missing)} of {2*len(names)} declared "
                         f"cells under 200 out-of-time rows. First ten: {missing[:10]}")
    P(f"  [GUARD] all {2*len(names)} declared cells present with >= 200 out-of-time rows")
    P("")
    P("THE RETRACE STOP ON TOP OF THE DECOUPLING -- both lenses")
    P(f"  X={XS} q={QS} grace={GRACES} stale={STALE}; stop = |y_fill|/sd + {STOP_BEYOND} sigma")
    P(f"  out of time (>= {SPLIT}); corrected chain; fresh reference (E2); every fill CROSSES")
    P("")
    P("  R1 fill%   against the SIGNAL count; sig/fire shows the funnel above it")
    P("  R3 gdel    bars the FORECAST waited | fdel  bars the ORDER waited -- different claims")
    P("  R4 ysig -> yfill  the part of the move SURRENDERED to obtain the confirmation")
    P("  R5 the lenses disagree BY CONSTRUCTION: a retrace signal occupies its slot from the")
    P("     FILL and an unfilled signal occupies nothing, so per-trade and per-slot can invert.")
    P("     That difference is the opportunity cost and it is never netted into one number.")
    P("")
    # bars per universe, for the book denominator
    bars_all = float(d.groupby("root")["nbars"].first().sum())
    bars_mi = float(d[d["root"].isin(MICRO)].groupby("root")["nbars"].first().sum())

    for uni, label, tb in ((None, "ALL ROOTS", bars_all), (MICRO, "MICRO (tradeable)", bars_mi)):
        sub = te if uni is None else te[te["root"].isin(uni)]
        for xv in XS:
            P("=" * 142)
            P(f"PATH-INVARIANT (per trade)   |   X = {xv}   |   {label}")
            P("")
            P("    cell                          sig  FILL%      n   in%  P(tgt)  win%  ysig"
              " yfill  gdel  fdel  bars   gross$    net$  median trimmed   CTLgr    dgr")
            for q in [qq for (xx, qq) in CELLS if xx == xv]:
                for w in GRACES:
                    for (m, o) in COMBOS:
                        cell = f"{m}{o:.2f}_x{xv}_q{q}_w{w}"
                        g = sub[sub["cell"] == cell]
                        if len(g) < 200:
                            continue
                        fl = g[g["filled"] > 0.5]
                        if len(fl) < 100:
                            continue
                        gr = fl["gross"].to_numpy(float)
                        net = gr - fl["cost"].to_numpy(float)
                        mn, md, tm = three_means(net)
                        ins = float(np.nanmean(fl["inside"]))
                        assert ins == 0.0, f"{cell}: a stop still sits inside the entry"
                        cf = sub[(sub["cell"] == "ctl" + cell) & (sub["filled"] > 0.5)]
                        if len(cf) >= 100:
                            cgr = cf["gross"].mean()
                            cs, ds = f"{cgr:>+7.2f}", f"{gr.mean() - cgr:>+6.2f}"
                        else:
                            cs, ds = f"{'--':>7}", f"{'--':>6}"
                        kd = fl["kind"].to_numpy(float)
                        P(f"    {cell:<26} {len(g):>6,} {g['filled'].mean():>6.1%} "
                          f"{len(fl):>6,} {ins:>5.1%} {(kd == 0).mean():>7.1%} "
                          f"{(gr > 0).mean():>5.1%} {fl['ysig'].mean():>5.2f} "
                          f"{fl['yfill'].mean():>5.2f} {fl['gdel'].mean():>5.2f} "
                          f"{fl['fdel'].mean():>5.2f} {np.median(fl['bars']):>5.0f} "
                          f"{gr.mean():>+8.2f} {mn:>+7.2f} {md:>+7.1f} {tm:>+7.2f} {cs} {ds}")
                P("")

            P(f"PATH-VARIANT (slot-limited book, er_usd ranking)   |   X = {xv}   |   {label}")
            P("")
            P("    cell                       slots      n   days  expo   gross$    net$"
              "  median trimmed  win%  hold  Sh_g   Sh_n     maxDD   xLimit")
            for q in [qq for (xx, qq) in CELLS if xx == xv]:
                for w in GRACES:
                    for (m, o) in COMBOS:
                        cell = f"{m}{o:.2f}_x{xv}_q{q}_w{w}"
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
                            P(f"    {cell:<26} {ns:>4} {pf['n']:>7,} {pf['days']:>6,} "
                              f"{pf['exposure']:>5.1%} {pf['gross_pt']:>+8.2f} "
                              f"{pf['net_pt']:>+7.2f} {pf['median']:>+7.1f} "
                              f"{pf['trim']:>+7.2f} {pf['win']:>5.1%} {pf['hold']:>5.1f} "
                              f"{pf['sharpe_g']:>+5.2f} {pf['sharpe_n']:>+6.2f} "
                              f"{pf['maxdd']:>9,.0f} {pf['dd_x']:>7.1f}x")
                P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not (a.self_test or a.build or a.run):
        ap.error("choose --self-test / --build / --run")
    if a.self_test and not self_test():
        sys.exit(1)
    if a.build:
        build()
    if a.run:
        run()
