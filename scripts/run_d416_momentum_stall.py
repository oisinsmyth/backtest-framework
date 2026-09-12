"""D416 -- enter when the momentum stalls. Bar committed in 41c4ef0 BEFORE this ran.

    uv run python scripts/run_d416_momentum_stall.py --run

Path-invariant. D413's 180,050 resolved touches on the full daily universe, read from D413's own
runner -- the event set is D413's, not a rebuild, and P2 asserts the counts reproduce exactly.

THE QUESTION. D414: the first intraday touch is 35 bp too early in cell 2. D415: no intraday
confirmation recovers it. Both left "the daily close or LATER". This asks it conditionally: wait
for the daily momentum INTO the zone to stop, enter at that day's close, hold five days.

THE TRAP (D415's), WITH BOTH CONTROLS. A stall rule is a filter as well as a timing:
  ctrl  time-matched unconditional entry at t+k, k = the rule's own median lag, same events
        -> rule - ctrl is the information in the STALL beyond the information in WAITING
  drop  D413's own touch-day return on the events that never stall inside the window

THE RULES (demand; supply is the mirror via sign), scanned over d = t+1 .. t+L, L = 10:
  S1  up-day       first d with sign*(C_d - O_d) > 0             PRIMARY -- D415's R1 at daily
  S2  higher close first d with sign*(C_d - C_{d-1}) > 0         shape
  S3  ROC turn     first d with sign*(log C_d - log C_{d-3}) >= 0 shape -- a momentum indicator
                                                                    crossing zero
All arms: five-day hold from a daily close, one round trip, so every paired difference is net of
matched costs. THE BAR on S1 pooled: G1 stalls >= 30%; T1 beats the touch-day close by 2 paired
SE; T2 beats the clock by 2 paired SE; T3 dropped not better than kept by 2 SE. All three.
Cell 2 is the declared SECONDARY and cannot clear.

WHAT THE SWEEP SAID BEFORE THE RUN (record section 5): cell 2's marginal per-bar edge after the
touch-day close is +6.3 +9.4 +6.9 +6.1 +1.5 -2.6 -6.3 -- front-loaded from bar 2. A one-day delay
forfeits ~9 bp of 30; two days, ~24. X-e predicts the stall entry loses to the close by > 10 bp.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413c", REPO / "scripts" / "run_d413_combine.py")
C = importlib.util.module_from_spec(_s)
sys.modules["d413c"] = C
_s.loader.exec_module(C)                      # D411's [SPLIT] holdout guard comes with it
M, Z4, D = C.M, C.Z4, C.D

OUT = REPO / "data" / "d416_momentum_stall.json"
D413_N, D413_CELL2 = 180050, 26024
L_PRIMARY, LS = 10, (10, 5, 20)
HOLD = 5
RULES = ("S1", "S2", "S3")
PRIMARY = "S1"
MIN_STALL = 0.30
NEUTRAL_RT_BP = dict(pooled=32.6, cell2=22.9)   # ADDENDUM 2, for reference only; not in a gate


# ------------------------------------------------------------------ stats
def stat(x, label):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if x.size < 2:
        return dict(label=label, n=int(x.size))
    se = x.std(ddof=1) / np.sqrt(x.size)
    return dict(label=label, n=int(x.size), mean=float(1e4 * x.mean()), se=float(1e4 * se),
                t=float(x.mean() / se) if se > 0 else float("nan"),
                median=float(1e4 * np.median(x)), win=float(100 * (x > 0).mean()))


def show(s, indent="  "):
    if "mean" not in s:
        print(f"{indent}{s['label']:44s} n {s['n']:7,}   (too few)")
        return
    print(f"{indent}{s['label']:44s} n {s['n']:7,}   mean {s['mean']:+8.2f} +-{s['se']:5.2f} bp"
          f"   {s['t']:+5.1f} SE   median {s['median']:+7.2f}   >0 {s['win']:.1f}%")


def diff_stat(a, b, label):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        return dict(label=label, n_a=int(a.size), n_b=int(b.size))
    d = a.mean() - b.mean()
    se = float(np.hypot(a.std(ddof=1) / np.sqrt(a.size), b.std(ddof=1) / np.sqrt(b.size)))
    return dict(label=label, n_a=int(a.size), n_b=int(b.size), diff=float(1e4 * d),
                se=float(1e4 * se), t=float(d / se) if se > 0 else float("nan"))


# ------------------------------------------------------------------ the stall scan
def scan(P, t, i, side, L):
    """Stall day per rule for every event, or -1. Fully vectorised over events."""
    T = P["CL"].shape[0]
    off = np.arange(1, L + 1)
    rows = t[:, None] + off[None, :]
    cols = np.repeat(i[:, None], L, axis=1)
    Cd, ok = Z4.gather(P["CL"], rows, cols, T)
    Od, _ = Z4.gather(P["OP"], rows, cols, T)
    Cm1, _ = Z4.gather(P["CL"], rows - 1, cols, T)
    Cm3, _ = Z4.gather(P["CL"], rows - 3, cols, T)
    sg = side[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        s1 = (sg * (Cd - Od) > 0) & ok
        s2 = (sg * (Cd - Cm1) > 0) & ok
        s3 = (sg * (np.log(Cd) - np.log(Cm3)) >= 0) & ok & (Cm3 > 0) & (Cd > 0)
    out = {}
    for R, hit in (("S1", s1), ("S2", s2), ("S3", s3)):
        has = hit.any(axis=1)
        lag = np.where(has, np.argmax(hit, axis=1) + 1, -1)       # in DAYS after t
        out[R] = dict(has=has, s=np.where(has, t + lag, -1), lag=lag)
    return out


def ret5(P, lg, day, i, side):
    """sign * (log C[day+5] - log C[day]); NaN unless eligible at entry and live at exit."""
    T = P["CL"].shape[0]
    ok = (day >= 0) & (day + HOLD < T)
    d0 = np.clip(day, 0, T - 1)
    d1 = np.clip(day + HOLD, 0, T - 1)
    r = side * (lg[d1, i] - lg[d0, i])
    good = ok & P["elig"][d0, i] & P["live"][d1, i] & np.isfinite(r)
    return np.where(good, r, np.nan)


# ------------------------------------------------------------------ assertions
def assert_SIGN():
    """[SIGN] the scanner finds the right day and a rising path pays POSITIVELY, in money."""
    T, n = 30, 1
    CL = np.full((T, n), 100.0)
    OP = np.full((T, n), 100.0)
    # decline into the zone through day 10 (touch), a further down day at 11, an UP day at 12,
    # then a rise.
    for d in range(1, 12):
        OP[d] = CL[d - 1]; CL[d] = CL[d - 1] - 1.0
    OP[12] = CL[11]; CL[12] = CL[11] + 0.5                       # first up-day: 12
    for d in range(13, T):
        OP[d] = CL[d - 1]; CL[d] = CL[d - 1] + 0.8
    Q = dict(CL=CL, OP=OP, elig=np.ones((T, n), bool), live=np.ones((T, n), bool))
    t = np.array([10]); i = np.array([0]); side = np.array([1])
    sc = scan(Q, t, i, side, L_PRIMARY)
    assert sc["S1"]["s"][0] == 12, f"[SIGN] S1 found day {sc['S1']['s'][0]}, expected 12"
    assert sc["S2"]["s"][0] == 12, f"[SIGN] S2 found day {sc['S2']['s'][0]}, expected 12"
    lg = np.log(CL)
    r = ret5(Q, lg, sc["S1"]["s"], i, side)[0]
    assert r > 0, f"[SIGN] a rising path after the stall paid {r:+.4f}"
    # the supply mirror: flip the path
    CLm = 200.0 - CL; OPm = 200.0 - OP
    Qm = dict(CL=CLm, OP=OPm, elig=Q["elig"], live=Q["live"])
    scm = scan(Qm, t, i, np.array([-1]), L_PRIMARY)
    assert scm["S1"]["s"][0] == 12, f"[SIGN] supply S1 found day {scm['S1']['s'][0]}"
    rm = ret5(Qm, np.log(CLm), scm["S1"]["s"], i, np.array([-1]))[0]
    assert rm > 0, f"[SIGN] supply mirror paid {rm:+.4f}"
    return True


def assert_LAG(sc, t):
    """[T+1] every stall day is STRICTLY after the touch day, for every rule."""
    for R in RULES:
        s = sc[R]["s"]; has = sc[R]["has"]
        assert np.all(s[has] > t[has]), f"[T+1] {R}: a stall on or before the touch day"
        assert np.all(sc[R]["lag"][has] >= 1), f"[T+1] {R}: lag < 1"
    return True


# ------------------------------------------------------------------ the study
def run():
    t0 = time.time()
    print("D416  enter when the momentum stalls -- the 'later' question, made conditional")
    print("      the bar was committed in 41c4ef0 BEFORE this ran\n")
    assert_SIGN()
    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))

    t = A["tt"][g]; i = Z["i"][g]; side = Z["side"][g]; r_base = A["r"][g]
    tr5 = D.trailing_ret(lg, 5); eff = C.path_efficiency(lg)
    DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    rev = tr5[t, i] * side; ef = eff[t, i]; dv = DV[t, i]
    fin = np.isfinite(rev) & np.isfinite(ef) & np.isfinite(dv)
    cuts = (np.median(rev[fin]), np.median(ef[fin]), np.median(dv[fin]))
    c2 = fin & (rev <= cuts[0]) & (ef > cuts[1]) & (dv > cuts[2])
    N = t.size
    assert N == D413_N, f"[P2] D413 resolved {D413_N}; this run has {N}"
    assert int(c2.sum()) == D413_CELL2, f"[P2] D413 cell 2 was {D413_CELL2}; this run has {int(c2.sum())}"
    print(f"  P2  D413's {N:,} resolved touches and {int(c2.sum()):,} cell-2 events reproduce exactly")
    print(f"      baseline r_base (D413's entry):  pooled {1e4*r_base.mean():+.2f} bp   "
          f"cell 2 {1e4*r_base[c2].mean():+.2f} bp")

    res = dict(L=L_PRIMARY, rules={}, sweep={})
    sc = scan(P, t, i, side, L_PRIMARY)
    assert_LAG(sc, t)
    print(f"\n  --- P1: stall rate, lag, k, per rule (L = {L_PRIMARY}) ---")
    K = {}
    for R in RULES:
        has, lag = sc[R]["has"], sc[R]["lag"]
        lg_ = lag[has]
        K[R] = int(round(float(np.median(lg_))))
        res["rules"][R] = dict(rate=float(has.mean()), n=int(has.sum()),
                               lag_p10=float(np.quantile(lg_, .1)), lag_p50=float(np.median(lg_)),
                               lag_p90=float(np.quantile(lg_, .9)), at_t1=float((lg_ == 1).mean()),
                               k=K[R], rate_cell2=float(has[c2].mean()), rate_not=float(has[~c2].mean()))
        q = res["rules"][R]
        print(f"  {R}  stalls {100*q['rate']:.1f}%  (n {q['n']:,})   lag p10/50/90 "
              f"{q['lag_p10']:.0f}/{q['lag_p50']:.0f}/{q['lag_p90']:.0f} days   "
              f"at t+1: {100*q['at_t1']:.1f}%   k={q['k']}")
    print(f"  --- P3: stall rate inside cell 2 vs outside ---")
    for R in RULES:
        q = res["rules"][R]
        print(f"  {R}  cell 2 {100*q['rate_cell2']:.1f}%   not cell 2 {100*q['rate_not']:.1f}%")

    # ---- the returns, per rule
    S = {}
    print(f"\n  --- THE TRADES (record section 3); reference neutral round trip "
          f"{NEUTRAL_RT_BP['pooled']} bp pooled, {NEUTRAL_RT_BP['cell2']} bp cell 2 ---")
    for R in RULES:
        has, s = sc[R]["has"], sc[R]["s"]
        k = K[R]
        r_S = ret5(P, lg, s, i, side)
        r_ctrl = ret5(P, lg, np.where(has, t + k, -1), i, side)
        rS_ok = has & np.isfinite(r_S)
        both = rS_ok & np.isfinite(r_ctrl)
        drop = ~has

        def block(mask, tag):
            return dict(
                r_S=stat(r_S[mask & rS_ok], f"{R} {tag} stall entry"),
                r_base=stat(r_base[mask & rS_ok], f"{R} {tag} touch-day close, same events"),
                d_base=stat((r_S - r_base)[mask & rS_ok], f"{R} {tag} PAIRED stall - close"),
                r_ctrl=stat(r_ctrl[mask & both], f"{R} {tag} clock at t+{k}, same events"),
                d_ctrl=stat((r_S - r_ctrl)[mask & both], f"{R} {tag} PAIRED stall - clock"),
                kept=stat(r_base[mask & rS_ok], f"{R} {tag} baseline on KEPT"),
                dropped=stat(r_base[mask & drop], f"{R} {tag} baseline on DROPPED"),
                drop_minus_kept=diff_stat(r_base[mask & drop], r_base[mask & rS_ok],
                                          f"{R} {tag} dropped - kept"))

        S[R] = dict(pooled=block(np.ones(N, bool), "pooled"), cell2=block(c2, "cell 2"), k=k)
        if R == PRIMARY:
            # THE PAIRED DELTA DECOMPOSED BY STALL LAG. This is an ACCOUNTING, not a finding: the
            # lag is a property of the holding period itself (lag 1 means day 1 was an up-day,
            # lag 6+ means days 1-5 were all down), so a baseline stratified by it is conditioned
            # on the future. It explains WHY the average is what it is; it cannot be traded,
            # because the lag is not knowable at t. The stall-clock cell at lag 1 has zero
            # variance by construction (k = 1, so the clock IS that stall day) and its SE is nan.
            lag = sc[R]["lag"]
            bl = {}
            for lab, lo, hi in (("lag1", 1, 1), ("lag2", 2, 2), ("lag3_5", 3, 5), ("lag6_10", 6, 10)):
                for pop, pm in (("pooled", np.ones(N, bool)), ("cell2", c2)):
                    m = pm & both & (lag >= lo) & (lag <= hi)
                    bl[f"{pop}_{lab}"] = dict(
                        n=int(m.sum()), share=float(m.sum() / max((pm & both).sum(), 1)),
                        stall_minus_close=stat((r_S - r_base)[m], f"{pop} {lab} stall - close"),
                        stall_minus_clock=stat((r_S - r_ctrl)[m], f"{pop} {lab} stall - clock"),
                        baseline=stat(r_base[m], f"{pop} {lab} baseline"))
            S[R]["by_lag"] = bl
        tag = "PRIMARY" if R == PRIMARY else "shape"
        for pop in ("pooled", "cell2"):
            print(f"\n  [{R}  {tag}  {pop}]")
            b = S[R][pop]
            for key in ("r_S", "r_base", "d_base", "r_ctrl", "d_ctrl", "dropped"):
                show(b[key])
            dk = b["drop_minus_kept"]
            if "diff" in dk:
                print(f"  {dk['label']:44s} {dk['diff']:+8.2f} +-{dk['se']:5.2f} bp   {dk['t']:+5.1f} SE")

    print(f"\n  --- S1 PAIRED DELTA BY STALL LAG -- an ACCOUNTING conditioned on the future, not a "
          f"finding ---")
    for pop in ("pooled", "cell2"):
        for lab in ("lag1", "lag2", "lag3_5", "lag6_10"):
            b = S[PRIMARY]["by_lag"][f"{pop}_{lab}"]
            sc_, cl_, ba_ = b["stall_minus_close"], b["stall_minus_clock"], b["baseline"]
            print(f"  {pop:6s} {lab:7s} {100*b['share']:5.1f}%  n {b['n']:7,}   "
                  f"stall-close {sc_.get('mean', float('nan')):+8.2f}   "
                  f"stall-clock {cl_.get('mean', float('nan')):+8.2f}   "
                  f"baseline {ba_.get('mean', float('nan')):+8.2f}")

    # ---- P4: look at the object
    j = int(np.flatnonzero(c2 & sc["S1"]["has"] & (sc["S1"]["lag"] >= 2))[0])
    dates = np.array(P["dates"]); syms = np.array(P["symbols"])
    print(f"\n  P4  {syms[i[j]]}  touch {dates[t[j]]}  side {side[j]:+d}  "
          f"S1 stall {dates[sc['S1']['s'][j]]} (lag {sc['S1']['lag'][j]})  "
          f"S2 lag {sc['S2']['lag'][j]}  S3 lag {sc['S3']['lag'][j]}")
    print(f"      r_base {1e4*r_base[j]:+.0f} bp   r_S1 {1e4*ret5(P, lg, sc['S1']['s'], i, side)[j]:+.0f} bp   "
          f"clock t+{K['S1']}: {1e4*ret5(P, lg, t + K['S1'], i, side)[j]:+.0f} bp")

    # ---- the L sweep on S1, shape only
    print(f"\n  --- the L sweep on S1, SHAPE only, cannot clear (R14) ---")
    for L in LS:
        if L == L_PRIMARY:
            continue
        scL = scan(P, t, i, side, L)
        has, s = scL["S1"]["has"], scL["S1"]["s"]
        r_S = ret5(P, lg, s, i, side)
        ok = has & np.isfinite(r_S)
        dp = stat((r_S - r_base)[ok], f"S1 L={L} pooled PAIRED stall - close")
        dc = stat((r_S - r_base)[ok & c2], f"S1 L={L} cell 2 PAIRED stall - close")
        dk = diff_stat(r_base[~has], r_base[ok], f"S1 L={L} pooled dropped - kept")
        res["sweep"][f"L{L}"] = dict(rate=float(has.mean()), pooled=dp, cell2=dc, drop_minus_kept=dk)
        print(f"  L={L:2d}  stalls {100*has.mean():.1f}%")
        show(dp); show(dc)
        if "diff" in dk:
            print(f"  {dk['label']:44s} {dk['diff']:+8.2f} +-{dk['se']:5.2f} bp   {dk['t']:+5.1f} SE")

    # ---- the bar, S1 pooled
    B = S[PRIMARY]["pooled"]
    G1 = bool(res["rules"][PRIMARY]["rate"] >= MIN_STALL)
    T1 = bool(G1 and B["d_base"].get("t", -9) > 2.0)
    T2 = bool(G1 and B["d_ctrl"].get("t", -9) > 2.0)
    T3 = bool(G1 and not (B["drop_minus_kept"].get("t", 9) > 2.0))
    Q = S[PRIMARY]["cell2"]
    s1 = bool(Q["d_base"].get("t", -9) > 2.0); s2 = bool(Q["d_ctrl"].get("t", -9) > 2.0)
    s3 = bool(not (Q["drop_minus_kept"].get("t", 9) > 2.0))
    print(f"\n  --- THE BAR (committed 41c4ef0), S1 pooled ---")
    print(f"    G1 S1 stalls >= {100*MIN_STALL:.0f}%                : {G1}   ({100*res['rules'][PRIMARY]['rate']:.1f}%)")
    print(f"    T1 stall beats touch-day close, 2 SE : {T1}   ({B['d_base'].get('mean', float('nan')):+.2f} bp, {B['d_base'].get('t', float('nan')):+.1f} SE)")
    print(f"    T2 stall beats the clock, 2 SE       : {T2}   ({B['d_ctrl'].get('mean', float('nan')):+.2f} bp, {B['d_ctrl'].get('t', float('nan')):+.1f} SE)")
    print(f"    T3 dropped not better than kept      : {T3}   (dropped - kept {B['drop_minus_kept'].get('diff', float('nan')):+.2f} bp, {B['drop_minus_kept'].get('t', float('nan')):+.1f} SE)")
    print(f"    secondary, cell 2 (cannot clear)     : T1 {s1}  T2 {s2}  T3 {s3}   "
          f"(stall - close {Q['d_base'].get('mean', float('nan')):+.2f} bp, {Q['d_base'].get('t', float('nan')):+.1f} SE)")
    clears = bool(G1 and T1 and T2 and T3)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}   secondary cell 2: "
          f"{'all three' if (s1 and s2 and s3) else 'not all three'}")

    OUT.write_text(json.dumps(dict(
        n=N, cell2=int(c2.sum()), cuts=[float(x) for x in cuts], k=K, stage0=res,
        bar=dict(G1=G1, T1=T1, T2=T2, T3=T3, clears=clears),
        secondary_cell2=dict(T1=s1, T2=s2, T3=s3), stats=S,
        baseline=dict(pooled=float(1e4 * r_base.mean()), cell2=float(1e4 * r_base[c2].mean()))),
        indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
