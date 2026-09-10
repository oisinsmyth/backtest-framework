"""D418 -- the stop placed on the ZONE. Bar committed in 7f9902e BEFORE this ran.

    uv run python scripts/run_d418_zone_stop.py --run

Path-invariant. D413's 180,050 touches, entry at the touch-day close, time stop at t+5, daily arm
only (D417 section 5: intraday triggering moves stop fills by under a basis point).

THE STOP is anchored on the zone, not the entry -- for a demand trade at the zone's far edge lo_u
(ST-edge, primary); at the midpoint (ST-mid) and a quarter-ATR beyond the edge (ST-buf) as shape.

TWO THINGS THE STRUCTURE IMPLIES:
  VALIDITY  the trade is entered only if the close is on the right side of the stop. Events already
            through the zone at the close are DROPPED and their fixed-exit return is reported --
            a filter knowable at t, unlike D416's.
  CONTROL   the LVL move applied to stops: each entered event's stop distance in ATR units is
            PERMUTED across entered events within side, so the distance distribution is preserved
            exactly and the link to the zone destroyed. Rule minus control is what the zone knows
            beyond how far away it is. 50 draws, averaged per event, paired.

THE BAR, three SEPARATE questions on ST-edge pooled, each able to clear alone:
  T1  the stop beats the fixed exit                 2 paired SE
  T2  the stop beats the distance-permuted control  2 paired SE   -- the zone, or the distance?
  T3  entered events' fixed-exit return exceeds the dropped events'  2 SE   -- a good filter?

THE WALKER takes an explicit per-event stop LEVEL. It is not trusted as a second implementation:
given entry - 1.5*ATR as the level it must reproduce D417's SL1.5 exit bar and price BIT-IDENTICALLY
on every event, asserted before any zone stop is walked -- which also delivers P3 for free.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d417", REPO / "scripts" / "run_d417_exits.py")
X = importlib.util.module_from_spec(_s)
sys.modules["d417"] = X
_s.loader.exec_module(X)                      # the [SPLIT] holdout guard comes with it
C, M, Z4, D = X.C, X.M, X.Z4, X.D

OUT = REPO / "data" / "d418_zone_stop.json"
D413_N, D413_CELL2 = 180050, 26024
HOLD = 5
N_DRAW = 50
VARIANTS = ("edge", "mid", "buf")
PRIMARY = "edge"
BUF = 0.25


# ------------------------------------------------------------------ the walker, explicit level
def walk_stop(OP, HI, LO, CL, E, stop, side, last_close):
    """Exit bar and price for a per-event stop LEVEL, in LONG space: a short is flipped by
    negating prices, so 'stop below' holds for everyone and the mirror is exact by construction.
    Fill at the trigger unless the bar's open is already through it, then at the open (worse).
    Bars with NaN are skipped."""
    s = side[:, None].astype(float)
    o, h, l = s * OP, s * HI, s * LO
    lo_s = np.where(s > 0, l, h)                          # the signed bar's true low
    e = side.astype(float) * E
    st = side.astype(float) * stop
    n, B = o.shape
    exit_bar = np.full(n, -1)
    fill = np.full(n, np.nan)
    done = np.zeros(n, bool)
    for j in range(B):
        ok = ~done & np.isfinite(o[:, j]) & np.isfinite(lo_s[:, j])
        hit = ok & (lo_s[:, j] <= st)
        fill = np.where(hit, np.minimum(st, o[:, j]), fill)
        exit_bar = np.where(hit, j, exit_bar)
        done |= hit
    fill = np.where(done, fill, side.astype(float) * last_close)
    return dict(bar=exit_bar, price=side.astype(float) * fill, early=done)


def assert_FILL(res, stop, side):
    m = res["early"]
    f = side.astype(float) * res["price"]; st = side.astype(float) * stop
    assert np.all(f[m] <= st[m] + 1e-9), "[FILL] a stop filled better than its trigger"
    return True


def assert_SIGN():
    """[SIGN] a valid demand entry stopped at the zone edge loses where the fixed exit won; an
    entry already through the edge is invalid; the supply mirror is exact."""
    E = np.array([99.0, 95.0, 101.0]); side = np.array([1, 1, -1])
    lo = np.array([96.0, 96.0, 102.0]); hi = np.array([98.0, 98.0, 104.0])
    stop = np.where(side > 0, lo, hi)
    valid = side * (E - stop) > 0
    assert valid[0] and not valid[1] and valid[2], f"[SIGN] validity {valid}"
    OP = np.array([[99, 97, 96.5, 99, 101], [95, 96, 97, 98, 99], [101, 103, 103.5, 101, 99]], float)
    HI = np.array([[99.5, 97.5, 98, 100, 103], [96, 97, 98, 99, 100], [102, 104.5, 104, 102, 100]], float)
    LO = np.array([[98, 95, 96, 98.5, 100.5], [94, 95.5, 96.5, 97.5, 98.5], [100, 102.5, 101, 99, 97]], float)
    CL = np.array([[98.5, 96.5, 97.5, 99.5, 103], [95.5, 96.5, 97.5, 98.5, 99.5], [102.5, 103.5, 102, 100, 97]], float)
    last = CL[:, -1]
    r = walk_stop(OP, HI, LO, CL, E, stop, side, last)
    base = side * (np.log(last) - np.log(E))
    rr = side * (np.log(r["price"]) - np.log(E))
    assert r["early"][0] and r["bar"][0] == 1 and abs(r["price"][0] - 96.0) < 1e-9, f"[SIGN] {r['price'][0]}"
    assert rr[0] < 0 < base[0], "[SIGN] the zone stop must lose where the fixed exit won"
    # the supply zone is [102, 104]; its FAR edge -- the invalidation level -- is the TOP, 104.
    # The first version of this line expected 102 and the walker, correctly, said 104.
    assert r["early"][2] and r["bar"][2] == 1 and abs(r["price"][2] - 104.0) < 1e-9, f"[SIGN] short {r['price'][2]}"
    assert rr[2] < 0 < base[2], "[SIGN] the short mirror"
    return True


# ------------------------------------------------------------------ stats
stat = X.stat


def summarise(res, E, side, r_base, mask):
    lgE = np.log(E)
    rr = side * (np.log(res["price"]) - lgE)
    m = mask & np.isfinite(rr) & np.isfinite(r_base)
    early = res["early"] & m
    hold = np.where(res["early"], res["bar"] + 1, HOLD).astype(float)
    return dict(rule=stat(rr[m], "rule"), delta=stat((rr - r_base)[m], "PAIRED rule - fixed"),
                early_share=float(early.sum() / max(m.sum(), 1)), hold_days=float(hold[m].mean()),
                bp_per_day=float(1e4 * rr[m].mean() / hold[m].mean()),
                std_ratio=float(rr[m].std(ddof=1) / r_base[m].std(ddof=1)),
                max_loss=float(1e4 * rr[m].min()),
                cf_early=stat(r_base[early], "fixed-exit return on EARLY-exited"),
                rule_early=stat(rr[early], "RULE return on the SAME early-exited"),
                exit_bar_p50=float(np.median(res["bar"][early])) if early.any() else None), rr


def run():
    t0 = time.time()
    print("D418  the stop placed on the ZONE -- structure vs distance, and the validity filter")
    print("      the bar was committed in 7f9902e BEFORE this ran\n")
    assert_SIGN()
    print("  [SIGN] valid entry stopped at the edge loses where the fixed exit won; a close through "
          "the edge is invalid; the short mirror exact")

    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    t = A["tt"][g]; i = Z["i"][g]; side = Z["side"][g]; r_base = A["r"][g]
    lo, hi = Z["lo"][g], Z["hi"][g]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5); eff = C.path_efficiency(lg); DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    rev = tr5[t, i] * side; ef = eff[t, i]; dv = DV[t, i]
    fin = np.isfinite(rev) & np.isfinite(ef) & np.isfinite(dv)
    cuts = (np.median(rev[fin]), np.median(ef[fin]), np.median(dv[fin]))
    c2 = fin & (rev <= cuts[0]) & (ef > cuts[1]) & (dv > cuts[2])
    N = t.size
    assert N == D413_N and int(c2.sum()) == D413_CELL2, f"[P1] {N} / {int(c2.sum())}"
    print(f"  P1  D413's {N:,} touches and {int(c2.sum()):,} cell-2 events reproduce")

    T = P["CL"].shape[0]
    off = np.arange(1, HOLD + 1)
    rows = t[:, None] + off[None, :]; cols = np.repeat(i[:, None], HOLD, axis=1)
    gth = lambda A_: Z4.gather(A_, rows, cols, T)[0]
    OP, HI, LO, CL = gth(P["OP"]), gth(P["HI"]), gth(P["LO"]), gth(P["CL"])
    E = P["CL"][t, i]; ATR = atr[t, i]
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]

    # ---- the walker must reproduce D417's SL1.5 bit-identically before it is trusted
    ref = X.walk(OP, HI, LO, CL, E, ATR, side, last)["SL1.5"]
    mine = walk_stop(OP, HI, LO, CL, E, np.where(side > 0, E - 1.5 * ATR, E + 1.5 * ATR), side, last)
    assert np.array_equal(ref["bar"], mine["bar"]) and np.array_equal(ref["early"], mine["early"]) \
        and np.allclose(ref["price"], mine["price"], rtol=0, atol=1e-9, equal_nan=True), \
        "[X] the level walker does not reproduce D417's SL1.5"
    print(f"  [X]  the level walker reproduces D417's SL1.5 exit bar and price on all {N:,} events")
    sl15 = mine

    res = dict(variants={}, stage0={})
    S = {}
    for v in VARIANTS:
        if v == "edge":
            stop = np.where(side > 0, lo, hi)
        elif v == "mid":
            stop = 0.5 * (lo + hi)
        else:
            stop = np.where(side > 0, lo - BUF * ATR, hi + BUF * ATR)
        valid = (side * (E - stop) > 0) & np.isfinite(r_base)
        d_atr = np.where(valid, side * (E - stop) / ATR, np.nan)
        rw = walk_stop(OP, HI, LO, CL, E, stop, side, last)
        assert_FILL(rw, stop, side)
        # ---- the distance-permuted control, 50 draws, averaged per event
        rng = np.random.default_rng(418)
        acc = np.zeros(N); cnt = np.zeros(N)
        for k in range(N_DRAW):
            dp = d_atr.copy()
            for sd in (1, -1):
                idx = np.flatnonzero(valid & (side == sd))
                dp[idx] = d_atr[idx][rng.permutation(idx.size)]
            stop_c = np.where(side > 0, E - dp * ATR, E + dp * ATR)
            rc = walk_stop(OP, HI, LO, CL, E, np.where(valid, stop_c, stop), side, last)
            rrc = side * (np.log(rc["price"]) - np.log(E))
            ok = valid & np.isfinite(rrc)
            acc[ok] += rrc[ok]; cnt[ok] += 1
            if k == 0:
                # [MATCH] the permuted distance distribution equals the rule's, exactly
                qa = np.quantile(d_atr[valid], [.1, .25, .5, .75, .9]); qb = np.quantile(dp[valid], [.1, .25, .5, .75, .9])
                assert np.max(np.abs(qa - qb)) < 1e-12, "[MATCH] the control's distances differ from the rule's"
        r_ctrl = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)

        for pop, pm, tag in (("pooled", np.ones(N, bool), "pooled"), ("cell2", c2, "cell 2")):
            m = pm & valid
            summ, rr = summarise(rw, E, side, r_base, m)
            d_ctrl = rr - r_ctrl
            mm = m & np.isfinite(d_ctrl)
            summ.update(dict(
                n_pop=int(pm.sum()), entered=int(m.sum()), drop_share=float(1 - m.sum() / max(pm.sum(), 1)),
                dist_atr=[float(np.quantile(d_atr[m], q)) for q in (.1, .5, .9)],
                delta_ctrl=stat(d_ctrl[mm], "PAIRED rule - distance-permuted control"),
                ctrl=stat(r_ctrl[mm], "control (mean over draws)"),
                base_entered=stat(r_base[m], "fixed exit, ENTERED events"),
                base_dropped=stat(r_base[pm & ~valid & np.isfinite(r_base)], "fixed exit, DROPPED events")))
            a_, b_ = r_base[m], r_base[pm & ~valid & np.isfinite(r_base)]
            dd = a_.mean() - b_.mean(); se = float(np.hypot(a_.std(ddof=1) / np.sqrt(a_.size), b_.std(ddof=1) / np.sqrt(max(b_.size, 2))))
            summ["filter_diff"] = dict(diff=float(1e4 * dd), se=float(1e4 * se), t=float(dd / se) if se > 0 else float("nan"))
            # P3: D417's SL1.5 on the SAME entered events
            s15, _ = summarise(sl15, E, side, r_base, m)
            summ["sl15_same_events"] = dict(delta=s15["delta"], early_share=s15["early_share"])
            S[f"{v}_{pop}"] = summ

    def show(key):
        q = S[key]; r, d, dc, fd = q["rule"], q["delta"], q["delta_ctrl"], q["filter_diff"]
        print(f"  {key:12s} entered {q['entered']:7,} of {q['n_pop']:7,} (drop {100*q['drop_share']:4.1f}%)   "
              f"dist/ATR p10/50/90 {q['dist_atr'][0]:.2f}/{q['dist_atr'][1]:.2f}/{q['dist_atr'][2]:.2f}")
        print(f"  {'':12s} rule {r['mean']:+7.2f}   vs fixed {d['mean']:+7.2f} +-{d['se']:.2f} ({d['t']:+5.1f} SE)   "
              f"vs ctrl {dc['mean']:+7.2f} +-{dc['se']:.2f} ({dc['t']:+5.1f} SE)   early {100*q['early_share']:.1f}%   "
              f"std x{q['std_ratio']:.2f}   bp/d {q['bp_per_day']:+.2f}   win {r['win']:.1f}%")
        print(f"  {'':12s} would-have {q['cf_early'].get('mean', float('nan')):+8.2f}   filled-at "
              f"{q['rule_early'].get('mean', float('nan')):+8.2f}   |   FILTER: entered base "
              f"{q['base_entered']['mean']:+7.2f}   dropped base {q['base_dropped'].get('mean', float('nan')):+7.2f}   "
              f"diff {fd['diff']:+7.2f} +-{fd['se']:.2f} ({fd['t']:+5.1f} SE)   |   D417 SL1.5 on same events: "
              f"{q['sl15_same_events']['delta']['mean']:+6.2f} bp, early {100*q['sl15_same_events']['early_share']:.1f}%")

    print(f"\n  --- POOLED (fixed exit on all {N:,}: {1e4*r_base.mean():+.2f} bp) ---")
    for v in VARIANTS:
        show(f"{v}_pooled")
    print(f"\n  --- CELL 2 secondary (fixed exit on all {int(c2.sum()):,}: {1e4*r_base[c2].mean():+.2f} bp) ---")
    for v in VARIANTS:
        show(f"{v}_cell2")

    # P4
    m4 = c2 & (side * (E - np.where(side > 0, lo, hi)) > 0)
    j = int(np.flatnonzero(m4)[0])
    dates = P["dates"]; syms = P["symbols"]
    stp = lo[j] if side[j] > 0 else hi[j]
    rw = walk_stop(OP[j:j+1], HI[j:j+1], LO[j:j+1], CL[j:j+1], E[j:j+1], np.array([stp]), side[j:j+1], last[j:j+1])
    print(f"\n  P4  {syms[i[j]]} touch {dates[t[j]]} side {side[j]:+d}  zone [{lo[j]:.2f},{hi[j]:.2f}]  "
          f"entry {E[j]:.2f}  stop {stp:.2f} ({side[j]*(E[j]-stp)/ATR[j]:.2f} ATR)  "
          f"exit {'day %d at %.2f' % (rw['bar'][0]+1, rw['price'][0]) if rw['early'][0] else 'time stop'}  "
          f"fixed {1e4*r_base[j]:+.0f} bp")

    # ---- the bar
    Pp = S[f"{PRIMARY}_pooled"]; Pc = S[f"{PRIMARY}_cell2"]
    T1 = bool(Pp["delta"]["t"] > 2.0); T2 = bool(Pp["delta_ctrl"]["t"] > 2.0); T3 = bool(Pp["filter_diff"]["t"] > 2.0)
    s1 = bool(Pc["delta"]["t"] > 2.0); s2 = bool(Pc["delta_ctrl"]["t"] > 2.0); s3 = bool(Pc["filter_diff"]["t"] > 2.0)
    print(f"\n  --- THE BAR (committed 7f9902e), ST-edge pooled ---")
    print(f"    T1 stop beats the fixed exit, 2 paired SE     : {T1}   ({Pp['delta']['mean']:+.2f} bp, {Pp['delta']['t']:+.1f} SE)")
    print(f"    T2 stop beats the distance control, 2 SE      : {T2}   ({Pp['delta_ctrl']['mean']:+.2f} bp, {Pp['delta_ctrl']['t']:+.1f} SE)")
    print(f"    T3 entered beat dropped (the filter), 2 SE     : {T3}   ({Pp['filter_diff']['diff']:+.2f} bp, {Pp['filter_diff']['t']:+.1f} SE)")
    print(f"    secondary cell 2 (cannot clear)               : T1 {s1}  T2 {s2}  T3 {s3}   "
          f"(filter {Pc['filter_diff']['diff']:+.2f} bp, {Pc['filter_diff']['t']:+.1f} SE)")
    print(f"\n  VERDICT: T1 {'CLEARS' if T1 else 'FAILS'}   T2 {'CLEARS' if T2 else 'FAILS'}   T3 {'CLEARS' if T3 else 'FAILS'}")

    OUT.write_text(json.dumps(dict(primary=PRIMARY, buf=BUF, draws=N_DRAW,
                                   bar=dict(T1=T1, T2=T2, T3=T3), secondary_cell2=dict(T1=s1, T2=s2, T3=s3),
                                   stats=S, counts=dict(n=N, cell2=int(c2.sum()))),
                              indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
