"""THE WIDE RUN: the same construction on 2010-2026 five-minute bars, NOT the holdout.

    python working/d528_wide.py --self-test
    python working/d528_wide.py --calibrate
    python working/d528_wide.py --run

Nothing admitted (R15). **The reserved slice (2026-04-11 -> 2026-09-09) is NOT read by this file**
-- every run here stops at 2026-04-10. The wide fixture simply covers 2010 onward, which is where
the power is.

WHY THIS RUN. Every promising cell in D528 has been 40-130 trades, and at that size the estimator
cannot resolve the ~$0.50 effect that is actually there: ADDENDUM 7 measured a per-trade sd of
$36.54 against an edge of $0.50, needing ~14,500 trades. `fut_day5m` has 135,179 root-sessions
against the 1-minute fixture's 1,176. That is the missing power.

TWO THINGS CHANGE, AND BOTH ARE HANDLED RATHER THAN ASSUMED.

1  IT IS A TRADE PRICE, NOT A QUOTED MID. `fut_day5m.close` is the last TRADE; the 1-minute
   fixture is the quoted MID, built precisely to avoid bid-ask bounce. The spike finding --
   one-bar excursions revert -- is EXACTLY the shape bounce produces on a trade series, so it
   could be manufactured here. `--calibrate` runs the identical construction on both price series
   over the 7-month window where both exist, and reports the difference. That number is the
   discount to apply to everything in `--run`.

2  THE INDEX DAY SESSION IS MISSING BEFORE 2016. NQ/ES/YM carry 33, 73, 113 sessions in 2010-12
   against 258 later -- the known GLBX archive gap. Those roots are gated to 2016-01-04. GC, 6E
   and CL are complete from 2010; RTY and BTC start when they start.

AND TWO METHOD FIXES CARRIED IN FROM ADDENDUM 11:

  * THE MATCHED CONTROL NOW CARRIES A MEDIAN AND TRIMMED-MEAN COMPANION. A mean on a
    tail-dominated cell is where a count-matched random draw is least informative -- a random draw
    from a fat-tailed pool rarely picks the three largest, so a fat right tail clears p95 for free.
    Every cell below is scored on all three.
  * NO TRUNCATED TRADES. tau=20 bars on an 84-bar session would let a late entry be cut short and
    recorded as a timeout, and timeouts have been profitable throughout -- which would manufacture
    a result. Entries are therefore restricted to bars where the FULL horizon fits.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_detector_diagnosis as D             # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402

FIVE = "data/fixtures/fut_day5m.parquet"
MID1 = "data/fixtures/fut_day1m_mid.parquet"
IS_END = Q.IS_END                      # 2026-04-10 -- the reserved slice starts the day after
H = Z.H
X, G = 2.0, 3.0
# NO-STOP MODE. `O.resolve` places the stop at G sigma from the level, so a G large enough that
# the residual can never reach it removes the stop without touching shared code. Self-test 7
# asserts zero stop-outs here AND that the stop genuinely fires at G=3.0, so "no stop-outs"
# cannot pass trivially. np.inf also works and gives identical outcomes (asserted); 1000 is used
# only so every INTERMEDIATE stays finite, since px_stp_ideal is computed on every row before
# np.where discards it.
G_NOSTOP = 1000.0
TAU = 20
TAU_LADDER = (10, 20, 40)
TARGET, FRAME = "reflect", "drift"
BASE_W5 = 20                           # 20 five-minute bars = 100 minutes, the volume window
TOD_SESSIONS = 20
TOD_MIN = 5
SLOW_HL = 2.0
CUT = 1.0
MIN_BARS = 60
N_DRAW = 400
SEED = 528205
# the known GLBX day-session gap: index roots unusable before 2016
GATE_2016 = {"NQ", "ES", "YM", "RTY", "MNQ", "MES"}
MICRO = ("6E", "BTC", "CL", "ES", "GC", "NQ", "RTY", "YM")


def P(*a):
    print(*a, flush=True)


def features_vec(path, tick, c):
    """Vectorised twin of `d528_detector_diagnosis.features`.

    That function is 93% of the wide run's cost (2.51 ms/session against classify2's 0.18) because
    it loops over every bar. This computes the same four features with sliding windows. Asserted
    bit-identical to the loop in --self-test, on a tie-heavy input as well as a smooth one.
    """
    n = len(path)
    n_t = n - 2 * H
    if n_t <= 0:
        return None
    r = np.diff(path, prepend=path[0])
    t = np.arange(2 * H, n)

    # w  = the H returns ending at t (includes the trigger)
    # wq = the H-1 returns BEFORE the trigger
    W = swv(r, H)                       # W[i] = r[i:i+H]; the window ending at t is W[t-H+1]
    w = W[t - H + 1]
    wq = w[:, :-1]
    sw = wq.std(axis=1, ddof=1)
    med = np.median(np.abs(wq), axis=1)

    # the BASE_W-return baseline ending at t-1, clipped at the start of the series
    sb = np.empty(n_t)
    for k, tt in enumerate(t):
        b0 = max(tt - D.BASE_W + 1, 1)
        seg = r[b0:tt]
        sb[k] = seg.std(ddof=1) if len(seg) > 2 else np.nan

    with np.errstate(invalid="ignore", divide="ignore"):
        vol_ratio = np.where(sb > 0, sw / sb, np.nan)
        jump = np.where(med > 0, np.abs(r[t]) / med, np.nan)
        y = c["flat_y"]
        frac_last = np.where(np.abs(y) > 0, np.abs(r[t]) / np.abs(y), np.nan)
        h = H // 2
        s1 = w[:, :h].std(axis=1, ddof=1)
        s2 = w[:, h:].std(axis=1, ddof=1)
        sig_ratio = np.where(s2 > 0, s1 / s2, np.nan)
    return {"vol_ratio": vol_ratio, "jump": jump, "frac_last": frac_last,
            "sig_ratio": sig_ratio}


def sessions_of(g, price_col):
    """Per day: the longest contiguous run of present, same-front bars, and its first bar index."""
    out = []
    for day, sub in g.groupby("day", sort=True):
        sub = sub.sort_values("bar")
        ok = sub["present"].to_numpy() & sub["same_front"].to_numpy()
        bars = sub["bar"].to_numpy()
        px = sub[price_col].to_numpy(float)
        vol = sub["volume"].to_numpy(float)
        if not ok.any():
            continue
        # longest run of consecutive, ok bars
        best = (0, 0, 0)
        i = 0
        while i < len(bars):
            if not ok[i]:
                i += 1
                continue
            j = i
            while j + 1 < len(bars) and ok[j + 1] and bars[j + 1] == bars[j] + 1:
                j += 1
            if j - i + 1 > best[0]:
                best = (j - i + 1, i, j)
            i = j + 1
        ln, a, b = best
        if ln < MIN_BARS:
            continue
        out.append((day, px[a:b + 1], vol[a:b + 1], int(bars[a])))
    return out


def tod_and_vol(sess):
    """Causal time-of-day volume profile and the fast/slow measures, per session.

    The profile for session k uses sessions [k-TOD_SESSIONS, k) only. `fast` backfills from the
    previous session's same-clock tail, so there is no warm-up and no overnight volume (the
    fixture is day-session only).
    """
    out = []
    hist = []
    slow = None
    prev_u = None
    for (day, px, vol, b0) in sess:
        if len(hist) < TOD_MIN:
            hist.append((b0, vol))
            out.append(None)
            prev_u = None
            continue
        # THE STACK MUST HAVE EXACTLY THE ROWS IT IS FILLED WITH. An earlier version allocated
        # len(hist) rows, filled only the last TOD_SESSIONS of them, then read stack[-TOD_SESSIONS:]
        # -- which for any root with more than 20 sessions of history took ALL-NaN rows, leaving
        # the profile NaN and the volume filter admitting 1% of candidates instead of ~50%.
        width = 84
        recent = hist[-TOD_SESSIONS:]
        stack = np.full((len(recent), width), np.nan)
        for i, (hb0, hv) in enumerate(recent):
            stack[i, hb0:hb0 + len(hv)] = hv
        with np.errstate(invalid="ignore"):
            allnan = np.isnan(stack).all(axis=0)
            tod = np.full(width, np.nan)
            if (~allnan).any():
                tod[~allnan] = np.nanmedian(stack[:, ~allnan], axis=0)
        prof = tod[b0:b0 + len(vol)]
        with np.errstate(invalid="ignore", divide="ignore"):
            u = np.where(prof > 0, vol / prof, np.nan)
        fast = np.full(len(u), np.nan)
        for i in range(len(u)):
            take = u[max(0, i - BASE_W5 + 1):i + 1]
            if len(take) < BASE_W5 and prev_u is not None and len(prev_u) >= BASE_W5 - len(take):
                take = np.concatenate([prev_u[len(prev_u) - (BASE_W5 - len(take)):], take])
            if np.isfinite(take).sum() >= BASE_W5 // 2:
                fast[i] = np.nanmean(take)
        sm = np.nanmean(u) if np.isfinite(u).any() else np.nan
        if np.isfinite(sm):
            a = 1.0 - 0.5 ** (1.0 / SLOW_HL)
            slow = sm if slow is None else a * sm + (1 - a) * slow
        out.append({"fast": fast, "slow": slow})
        hist.append((b0, vol))
        prev_u = u
    return out


def collect(roots, days_max, price_col, src, tau, micro_only=False, stop_g=G):
    # GUARD AGAINST SHADOWING. The stop was first named `g`, which the per-root loop below
    # immediately rebound to a DataFrame -- so the stop distance silently became a 7-column
    # frame and both runs died inside numpy. A scalar check makes that class of bug loud.
    assert np.isscalar(stop_g) and np.isfinite(stop_g) and stop_g > 0, \
        f"stop_g must be a positive scalar, got {type(stop_g).__name__}: {stop_g!r}"
    """The candidate pool over the wide fixture. `src` is the loaded dataframe."""
    sp = Q.specs()
    pool = []
    for r in roots:
        if r not in sp:
            continue
        g = src[src["root"] == r]
        if r in GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        g = g[g["day"] <= days_max]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = sessions_of(g, price_col)
        vols = tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            if vm is None:
                continue
            c = Z.classify2(px, tick)
            if c is None:
                continue
            f = features_vec(px, tick, c)
            if f is None:
                continue
            base = (c["flat_sd"] > 0) & c["slope_ok"] & c["a2ok"]
            with np.errstate(invalid="ignore"):
                base = base & (np.abs(c["flat_y"]) >= X * c["flat_sd"])
            base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
            base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
            base = np.nan_to_num(base, nan=False).astype(bool)
            # NO TRUNCATED TRADES: the full horizon must fit inside the session
            room = np.zeros(len(base), bool)
            room[:max(0, len(px) - 2 * H - tau)] = True
            base = base & room
            if not base.any():
                continue
            tr = O.resolve(px, c, "flat", base, tick, tick_usd, cost_tk,
                           TARGET, FRAME, stop_g, tau, 0, b0, r)
            idx = [i for i in np.flatnonzero(base) if (i + 2 * H) < len(px) - 1][:len(tr)]
            for z, i in zip(tr, idx):
                for k in f:
                    z[k] = float(f[k][i])
                bar5 = i + 2 * H
                z["v_fast"] = float(vm["fast"][bar5]) if bar5 < len(vm["fast"]) else np.nan
                z["v_slow"] = float(vm["slow"]) if vm["slow"] else np.nan
                z["v_chg"] = (z["v_fast"] / z["v_slow"]
                              if (np.isfinite(z["v_fast"]) and z["v_slow"]
                                  and z["v_slow"] > 0) else np.nan)
                z["day_str"] = day
                z["gross"] = z["g_real_tk"] * z["tick_usd"]
                z["net"] = z["gross"] - z["cost_usd"]
                pool.append(z)
    return pool


def spike(z):
    """The 1-minute construction's ABSOLUTE thresholds, applied unchanged."""
    return (np.isfinite(z["vol_ratio"]) and z["vol_ratio"] < 0.913
            and np.isfinite(z["frac_last"]) and z["frac_last"] > 0.8
            and np.isfinite(z["jump"]) and z["jump"] > 3)


def spike_q(pool):
    """The same CONCEPT at matched selectivity, using this pool's own quantiles.

    0.913 / 0.8 / 3 were the 1-MINUTE pool's own median, ~p77 and ~p57. On 5-minute bars the
    feature distributions differ, so the same absolute numbers cut a different fraction and the
    two runs would not be comparable. This rebuilds the cut at the same quantile POSITIONS --
    declared, not searched -- and both versions are reported with their admission rates so the
    selectivity difference is visible rather than hidden.
    """
    v = np.array([z["vol_ratio"] for z in pool], dtype=float)
    fl = np.array([z["frac_last"] for z in pool], dtype=float)
    jp = np.array([z["jump"] for z in pool], dtype=float)
    qv = float(np.nanpercentile(v, 50))
    qf = float(np.nanpercentile(fl, 77))
    qj = float(np.nanpercentile(jp, 57))

    def fn(z):
        return (np.isfinite(z["vol_ratio"]) and z["vol_ratio"] < qv
                and np.isfinite(z["frac_last"]) and z["frac_last"] > qf
                and np.isfinite(z["jump"]) and z["jump"] > qj)
    return fn, (qv, qf, qj)


def vlevel(z):
    return np.isfinite(z["v_fast"]) and z["v_fast"] >= CUT


def vchg(z):
    return np.isfinite(z["v_chg"]) and z["v_chg"] >= CUT


def report(pool, cells, rng, title):
    """Every cell against a matched control scored on MEAN, MEDIAN and TRIMMED mean.

    ADDENDUM 11: a mean on a tail-dominated cell is where a count-matched random draw is least
    informative, so the mean alone let two market events clear p95. All three now travel together.
    """
    gp = np.array([z["gross"] for z in pool])
    P(title)
    P("    cell                        n    P(tgt)  win%   gross $   net $  | MEAN vs p95 |"
      "  MEDIAN vs p95 | TRIMMED vs p95 | top3 share")
    for label, fn in cells:
        rows = [z for z in pool if fn(z)]
        if len(rows) < 30:
            P(f"    {label:<26} {len(rows):>6,}  too few")
            continue
        g = np.array([z["gross"] for z in rows])
        nt = np.array([z["net"] for z in rows])
        kd = np.array([z["kind"] for z in rows])
        k = len(rows)
        idx = rng.integers(0, len(gp), (N_DRAW, k))
        dr = gp[idx]
        m95 = np.percentile(dr.mean(1), 95)
        d95 = np.percentile(np.median(dr, 1), 95)
        lo, hi = np.percentile(dr, [1, 99], axis=1)
        tdr = np.array([d[(d >= l) & (d <= h)].mean() for d, l, h in zip(dr, lo, hi)])
        t95 = np.percentile(tdr, 95)
        l1, h1 = np.percentile(g, [1, 99])
        tg = g[(g >= l1) & (g <= h1)].mean()
        pos = nt[nt > 0]
        top3 = (np.sort(nt)[-3:].sum() / pos.sum()) if len(pos) else np.nan
        def mk(v, p):
            return f"{v:+7.2f}{'*' if v > p else ' '}"
        P(f"    {label:<26} {k:>6,} {(kd==0).mean():>7.1%} {(nt>0).mean():>5.1%} "
          f"{g.mean():>+8.2f} {nt.mean():>+7.2f} | {mk(g.mean(), m95)} | "
          f"{mk(float(np.median(g)), d95)} | {mk(float(tg), t95)} | {top3:>9.1%}")
    P("    * = above the matched control's p95 on that statistic. A cell that clears the MEAN")
    P("      but not the MEDIAN or TRIMMED mean is carried by its tail.")


def self_test():
    rng = np.random.default_rng(303)
    # 1. THE VECTORISED FEATURES MUST BE BIT-IDENTICAL TO THE LOOP -- the speedup must change no
    #    number. Probed on a smooth path AND a tie-heavy one, where rewrites disagree.
    for nm, p in (("gaussian", 20000 + np.cumsum(rng.normal(0, 3.0, 200))),
                  ("tie-heavy", 20000 + np.cumsum(np.round(rng.normal(0, 1.0, 200) * 4) / 4))):
        c = Z.classify2(p, 0.25)
        a = D.features(p, 0.25, c)
        b = features_vec(p, 0.25, c)
        for k in a:
            x, y = np.asarray(a[k], float), np.asarray(b[k], float)
            both_nan = np.isnan(x) & np.isnan(y)
            assert np.array_equal(np.isnan(x), np.isnan(y)), f"{nm}/{k}: nan pattern differs"
            assert np.array_equal(x[~both_nan], y[~both_nan]), f"{nm}/{k}: values differ"
        P(f"   [1] {nm:<10} features_vec == features, bit-identical on all four            OK")

    # 2. THE INDEX GATE MUST BITE. NQ before 2016 must be excluded and GC must not be.
    assert "NQ" in GATE_2016 and "GC" not in GATE_2016
    P("   [2] index roots gated to 2016-01-04; GC/6E/CL ungated                          OK")

    # 3. NO TRUNCATED TRADES: with tau bars required, an entry may not start closer than tau to
    #    the end of the session, or it would be cut short and scored as a profitable timeout.
    n, tau = 84, 20
    room = np.zeros(n - 2 * H, bool)
    room[:max(0, n - 2 * H - tau)] = True
    last_entry = int(np.flatnonzero(room)[-1]) + 2 * H
    assert last_entry + tau <= n - 1, f"last entry {last_entry} + {tau} overruns {n-1}"
    P(f"   [3] on an {n}-bar session with tau={tau}, last entry is bar {last_entry}; "
      f"{last_entry}+{tau} <= {n-1}   OK")

    # 4. THE RESERVED SLICE IS NEVER READ.
    assert IS_END == "2026-04-10", IS_END
    P(f"   [4] every run stops at {IS_END}; the reserved slice is not read                OK")

    # 5. THE MATCHED CONTROL'S THREE STATISTICS MUST DISAGREE ON A TAIL-DOMINATED CELL -- that
    #    disagreement is the whole point of carrying all three.
    pool = [{"gross": v, "net": v - 4.7, "kind": 0} for v in rng.normal(-1.0, 25.0, 4000)]
    tail = [dict(z) for z in pool[:50]]
    for z in tail[:3]:
        z["gross"] += 400.0
        z["net"] += 400.0
    gp = np.array([z["gross"] for z in pool])
    g = np.array([z["gross"] for z in tail])
    dr = gp[rng.integers(0, len(gp), (400, len(tail)))]
    assert g.mean() > np.percentile(dr.mean(1), 95), "the tail cell should clear the MEAN"
    assert float(np.median(g)) <= np.percentile(np.median(dr, 1), 95), \
        "the tail cell should NOT clear the MEDIAN -- the companion statistic is not working"
    P("   [5] a 3-trade tail clears the MEAN control and fails the MEDIAN control        OK")

    # 6. THE VOLUME PROFILE MUST SURVIVE A LONG HISTORY. With more sessions than TOD_SESSIONS the
    #    profile must still be finite and `fast` must still be produced -- an earlier version
    #    allocated len(hist) rows, filled only the last TOD_SESSIONS, then read the LAST rows,
    #    so every root with >20 sessions got an all-NaN profile and the filter admitted 1% of
    #    candidates instead of ~50%. The bug only appears once history exceeds the window.
    for n_sess in (8, 25, 120):
        sess = [(f"d{i:03d}", np.full(84, 100.0),
                 np.abs(rng.normal(5000, 500, 84)), 0) for i in range(n_sess)]
        vms = tod_and_vol(sess)
        live = [v for v in vms if v is not None]
        assert len(live) == max(0, n_sess - TOD_MIN), \
            f"{n_sess} sessions -> {len(live)} live, wanted {n_sess - TOD_MIN}"
        fin = np.mean([np.isfinite(v["fast"]).mean() for v in live])
        assert fin > 0.9, (f"{n_sess} sessions: only {fin:.1%} of `fast` is finite -- the "
                           f"time-of-day profile is going NaN once history exceeds the window")
        P(f"   [6] {n_sess:>3} sessions -> {len(live):>3} with a profile, "
          f"{fin:.0%} of `fast` finite   OK")

    # 7. NO-STOP MODE MUST PRODUCE ZERO STOP-OUTS.
    #    A note corrected by this very test: an earlier comment claimed infinity would break the
    #    comparison because `y_stp = s*inf` flips sign for a long. It does not -- for s=-1,
    #    `yk - (-inf) = +inf`, and `+inf * -1 = -inf`, which fails `>= 0` exactly as it should.
    #    Both inf and 1000 give zero stop-outs. 1000 is used only so every INTERMEDIATE stays
    #    finite (`px_stp_ideal` is computed on every row before `np.where` discards it).
    pth = 20000 + np.cumsum(rng.normal(0, 3.0, 300))
    c = Z.classify2(pth, 0.25)
    keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none", align=False)
    for gg, want_stops in ((G, True), (G_NOSTOP, False)):
        tr = O.resolve(pth, c, "flat", keep, 0.25, 1.0, 0.0, TARGET, FRAME, gg, TAU, 0, 0, "T")
        n_stop = sum(z["kind"] == 1 for z in tr)
        assert len(tr) > 10, "too few trades to test the stop mode"
        if want_stops:
            assert n_stop > 0, f"G={gg} produced no stop-outs -- the stop is not firing at all"
        else:
            assert n_stop == 0, f"G={gg} still produced {n_stop} stop-outs of {len(tr)}"
        P(f"   [7] G={gg:<8} -> {n_stop:>3} stop-outs of {len(tr)} trades  "
          f"({'stops on' if want_stops else 'NO STOP'})   OK")
    tr_inf = O.resolve(pth, c, "flat", keep, 0.25, 1.0, 0.0, TARGET, FRAME, np.inf, TAU,
                       0, 0, "T")
    n_inf = sum(z["kind"] == 1 for z in tr_inf)
    k_inf = [z["kind"] for z in tr_inf]
    k_1k = [z["kind"] for z in O.resolve(pth, c, "flat", keep, 0.25, 1.0, 0.0, TARGET, FRAME,
                                         G_NOSTOP, TAU, 0, 0, "T")]
    assert n_inf == 0, f"G=inf produced {n_inf} spurious stop-outs"
    assert k_inf == k_1k, "G=inf and G=1000 disagree on outcomes -- they should be identical"
    P(f"   [7] G=inf also gives 0 stop-outs and the SAME outcomes as G=1000 "
      f"({len(tr_inf)} trades)  OK")
    P("\n   all self-tests pass\n")


def load(price_col):
    cols = ["root", "day", "bar", price_col, "volume", "same_front", "present"]
    f = pd.read_parquet(FIVE, columns=cols)
    f = f[f["day"] <= IS_END]
    assert f["day"].max() <= IS_END, f"load() returned {f['day'].max()}, past {IS_END}"
    return f


def calibrate(g=G):
    """Trade CLOSE vs quoted MID, identical construction, on the window where both exist."""
    rng = np.random.default_rng(SEED)
    sp = Q.specs()
    m = pd.read_parquet(MID1, columns=["root", "day", "bar", "mid", "same_front", "present"])
    # THE RAW PARQUET SPANS PAST THE CUTOFF. `Q.load()` applies IS_END; reading the file directly
    # does not, and an earlier version of this function took `hi` from the file's own max day --
    # 2026-09-09 -- which pulled five months of the RESERVED SLICE into the quoted-MID arm.
    # The cap is applied here explicitly and asserted below.
    m = m[m["day"] <= IS_END]
    lo, hi = m["day"].min(), m["day"].max()
    assert hi <= IS_END, f"calibration window ends {hi}, past the cutoff {IS_END}"
    P("CALIBRATION: trade CLOSE vs quoted MID, identical construction")
    P(f"  overlap window {lo} .. {hi}, micro universe\n")
    f = load("close")
    f = f[(f["day"] >= lo) & (f["day"] <= hi)]
    # ALL roots, not the micro 8: the first attempt had 96 and 88 candidates, far too few to
    # calibrate a price-type difference at all. The mid fixture carries ~35 roots over the same
    # window, which lifts the calibration by more than an order of magnitude.
    roots = sorted(set(m["root"]) & set(f["root"]) & set(sp))

    # build a 5-minute MID series by sampling the 1-minute mid every 5 minutes
    m = m[m["root"].isin(roots) & (m["day"] >= lo) & (m["day"] <= hi)]
    m5 = m[m["bar"] % 5 == 0].copy()
    m5["bar"] = m5["bar"] // 5
    m5 = m5.rename(columns={"mid": "close"})
    m5["volume"] = 1.0                 # volume is not used by the calibration cells
    vol = f[["root", "day", "bar", "volume"]]
    m5 = m5.drop(columns=["volume"]).merge(vol, on=["root", "day", "bar"], how="left")
    m5["volume"] = m5["volume"].fillna(1.0)

    for nm, src in (("TRADE close", f), ("quoted MID", m5)):
        pool = collect(roots, hi, "close", src, TAU, stop_g=g)
        fq, q = spike_q(pool)
        cells = (("pool", lambda z: True),
                 ("spike (1-min thresholds)", spike),
                 ("spike (own quantiles)", fq))
        P(f"  --- {nm} --- {len(pool):,} candidates, {len(roots)} roots")
        P(f"      own-quantile cuts: vol_ratio<{q[0]:.3f}, frac_last>{q[1]:.3f}, jump>{q[2]:.3f}")
        report(pool, cells, rng, "")
        P("")
    P("  The two arms share the window, the roots, the bar size and every parameter. The ONLY")
    P("  difference is the price series, so the gap between them IS the bid-ask bounce.")


def run(micro_only=False, g=G):
    rng = np.random.default_rng(SEED)
    sp = Q.specs()
    f = load("close")
    allr = sorted(set(f["root"]) & set(sp))
    roots = [r for r in allr if r in MICRO] if micro_only else allr
    P("THE WIDE RUN -- 2010-2026 five-minute bars, trade close"
      + ("   ***  NO STOP LOSS  ***" if g >= G_NOSTOP else ""))
    P(f"  {len(roots)} roots{' (micro only)' if micro_only else ''}, "
      f"through {IS_END}; reserved slice NOT read")
    stop_txt = "NONE (target or timeout only)" if g >= G_NOSTOP else f"{g} sigma from the level"
    P(f"  bars identical to the 1-minute construction: H={H}, x={X}, stop={stop_txt}, "
      f"tau={TAU}, target={TARGET}, frame={FRAME}")
    P(f"  index roots gated to 2016-01-04; no truncated trades\n")
    pool = collect(roots, IS_END, "close", f, TAU, stop_g=g)
    P(f"  pool {len(pool):,} candidates")

    def cells_for(pl):
        fq, q = spike_q(pl)
        return (
            ("pool (no filter)", lambda z: True),
            ("spike (1-min thresholds)", spike),
            ("spike (own quantiles)", fq),
            ("spike-q + LEVEL", lambda z: fq(z) and vlevel(z)),
            ("spike-q + CHANGE", lambda z: fq(z) and vchg(z)),
            ("spike-q + LEVEL + CHANGE", lambda z: fq(z) and vlevel(z) and vchg(z)),
            ("LEVEL alone", vlevel),
            ("CHANGE alone", vchg),
        ), q

    cells, q = cells_for(pool)
    P(f"  own-quantile cuts: vol_ratio<{q[0]:.3f}, frac_last>{q[1]:.3f}, jump>{q[2]:.3f}\n")
    report(pool, cells, rng, "=" * 120 + "\n1  THE WIDE POOL, full span\n")

    # THE SPAN EFFECT, ISOLATED. The same run restricted to the 7-month window the 1-minute
    # construction used, so "wide vs narrow" and "5-minute trade vs 1-minute mid" are separable
    # rather than confounded in one number.
    lo7 = "2025-09-11"
    p7 = [z for z in pool if z["day_str"] >= lo7]
    if len(p7) > 200:
        c7, _ = cells_for(p7)
        report(p7, c7, rng,
               f"\n2  THE SAME RUN RESTRICTED TO {lo7} .. {IS_END}, {len(p7):,} candidates\n"
               "   (isolates the SPAN effect: same price series, same bars, narrow window)\n")

    # MICRO ONLY -- the universe the account can actually trade
    pm = [z for z in pool if z["root"] in MICRO]
    if len(pm) > 200:
        cm, _ = cells_for(pm)
        report(pm, cm, rng,
               f"\n3  MICRO UNIVERSE ONLY ({len(MICRO)} roots), {len(pm):,} candidates\n"
               "   (the only roots a $50k account with a $2,000 trailing limit can trade)\n")

    for tau in TAU_LADDER:
        if tau == TAU:
            continue
        pl = collect(roots, IS_END, "close", f, tau, stop_g=g)
        cl, _ = cells_for(pl)
        report(pl, cl, rng,
               f"\n4  TAU = {tau} bars ({tau*5} minutes), {len(pl):,} candidates\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--micro", action="store_true")
    ap.add_argument("--nostop", action="store_true",
                    help="remove the stop entirely: exit on target or timeout only")
    a = ap.parse_args()
    g_use = G_NOSTOP if a.nostop else G
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.calibrate:
        calibrate(g=g_use)
    if a.run or a.micro:
        run(micro_only=a.micro, g=g_use)
    if not (a.self_test or a.calibrate or a.run or a.micro):
        ap.error("choose --self-test, --calibrate, --run or --micro")
