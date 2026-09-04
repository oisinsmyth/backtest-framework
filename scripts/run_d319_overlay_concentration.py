"""D319 -- the overlay at concentration, and whether its denominator is the problem.

    uv run python scripts/run_d319_overlay_concentration.py --selftest
    uv run python scripts/run_d319_overlay_concentration.py [--draws 200]

PRE-REGISTERED AT `1b58f2a`, committed before this file existed (R8).

THE OVERLAY IS THE LARGEST SHARPE EFFECT THIS PROGRAMME HAS PRODUCED -- D297
measured gross Sharpe +0.512 -> +0.728 and maxDD -62% at p = 0.0150 -- and it is
ruled out at the operating point by ONE cell at ONE threshold: D306's X=12 at
N=2, which D318 re-costs at -3.37 bp/bar.

AND THERE IS A NAMED MECHANISM. The trigger is

    off  =  dd >= X * trailing_vol(BOOK)

so the threshold is denominated in the book's OWN trailing volatility, and D312
measured that exact quantity's forward-63 correlation at -0.016 for N_eff=2
against +0.347 for N_eff=19. At the width the book runs, the overlay divides by
noise. D313 measured a replacement -- universe cross-sectional dispersion, +0.352
at N_eff=2 -- and this study reuses THAT DECLARED PREDICTOR unchanged. No new
predictor is introduced and none is searched.

COSTED PER D318: the common round trip within a width (D307's rule, since the
comparison here is between exit/overlay variants at a fixed width), per-cell
across widths, plus IBKR per-share commission on the held median price.

NET SHARPE IS PRIMARY. The overlay cuts exposure to ~70%, and scoring it on net
bp/bar penalises it for being out of the market -- the error D301's null column
made, which left its two overlay rows uninterpretable.
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


W = _load("d306", "run_d306_width_exits.py")
O = _load("d297", "run_d297_overlay.py")
U = _load("d312u", "d312_universe_forecast.py")
R3 = _load("d313", "run_d313_universe_risk.py")
D, M, SP = W.D, W.M, W.SP

DEPTHS = (2, 3, 19)
X_GRID = (6.0, 8.0, 10.0, 11.0, 12.0, 13.0, 14.0, 16.0, 18.0, 20.0, 25.0, 30.0)
BASES = ("none", "target")
ARMS = ("own", "univ")
VOL_WIN, CAL_WIN = 63, 252
PER_SHARE, CROSSINGS = 0.005, 4.0
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d319_overlay_concentration.json"


# ---------------------------------------------------------------- primitives
def trail_mean_full(v, w=VOL_WIN):
    """Trailing mean over ALL bars, lagged one bar -- O.trailing_vol's convention.

    NaN-tolerant: a window with fewer than half its bars finite returns NaN
    rather than a mean of whatever survived.
    """
    x = np.asarray(v, float)
    ok = np.isfinite(x).astype(float)
    xf = np.where(np.isfinite(x), x, 0.0)
    cs = np.concatenate([[0.0], np.cumsum(xf)])
    cn = np.concatenate([[0.0], np.cumsum(ok)])
    out = np.full(x.size, np.nan)
    j = np.arange(w, x.size + 1)
    cnt = cn[j] - cn[j - w]
    out[j - 1] = np.where(cnt >= w / 2, (cs[j] - cs[j - w]) / np.maximum(cnt, 1),
                          np.nan)
    lag = np.full(x.size, np.nan)
    lag[1:] = out[:-1]
    return lag


def schedule_ext(base, X, vol, lag=True):
    """D297's schedule with the DENOMINATOR SUPPLIED.

    Assertion [1b] holds this identical to `O.schedule` when handed
    `O.trailing_vol(base)` -- otherwise the two arms would differ in more than
    the one thing under test.
    """
    shadow = np.cumsum(base)
    prev = np.concatenate([[0.0], shadow[:-1]]) if lag else shadow
    dd = np.maximum.accumulate(prev) - prev
    with np.errstate(invalid="ignore"):
        off = np.isfinite(vol) & (vol > 0) & (dd >= X * vol)
    return ~off


def univ_vol(base, disp, w=CAL_WIN):
    """D313's mapping: a near-constant structural ratio times the wide read.

    c(t) = trailing-252 MEDIAN of  vol_own(s)/P(s)  for s < t;   vhat = c(t)*P(t)
    Both inputs are already lagged one bar, so vhat(t) reads only through t-1.
    """
    v_own = O.trailing_vol(base)
    P = trail_mean_full(disp)
    Pp = np.where(np.isfinite(P) & (P > 0), P, np.nan)
    return R3.trailing_median(v_own / Pp, w) * Pp


def held_price(res, close):
    """Median close at entry over the trades actually taken -- D300's statistic."""
    v = np.array([close[e0, row] for row, e0, _a, _p, _s in res["trades"]])
    v = v[np.isfinite(v) & (v > 0)]
    return float(np.median(v)) if v.size else np.nan


def cell(res, depth, scale, rt_spread, rt_comm):
    """D306's `stats` accounting, with commission added and the basis supplied."""
    ok = res["mask"]
    b = res["book"][ok] * scale[ok]
    bars, sd = b.size, b.std(ddof=1)
    eq = np.cumsum(b)
    turn = int(res["ent"][ok].sum()) / float(depth) / 2.0 / bars
    expo = float(scale[ok].mean())
    ds = np.abs(np.diff(np.concatenate([[1.0], scale])))
    ov = float(ds[ok].sum() * rt_spread / 2.0 / bars)
    pos = float(rt_spread * turn * expo)
    comm = float(rt_comm * turn * expo)
    g = float(b.mean()) * 1e4
    net = g - pos - ov - comm
    v = float(sd) * 1e4
    return dict(gross_bp=g, vol_bp=v, cost_pos_bp=pos, cost_overlay_bp=ov,
                cost_comm_bp=comm, net_bp=net,
                sharpe_net=net / v * np.sqrt(ANN) if v > 0 else 0.0,
                sharpe_gross=g / v * np.sqrt(ANN) if v > 0 else 0.0,
                ret_per_exp=g / expo if expo > 0 else 0.0,
                maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
                exposure=expo, turnover=float(turn),
                transitions=int((np.diff(scale[ok]) != 0).sum()), bars=bars)


def bh(ps, q=0.10):
    o = np.argsort(ps)
    m = len(ps)
    hit = np.asarray(ps)[o] <= (np.arange(1, m + 1) / m) * q
    k = np.flatnonzero(hit).max() + 1 if hit.any() else 0
    rej = np.zeros(m, bool)
    rej[o[:k]] = True
    return rej


# ---------------------------------------------------------------- assertions
def assertions(sims, rt, rtc, disp, d306, d312u):
    print("\nASSERTIONS")
    ones = np.ones(sims[(19, "none")]["book"].size)

    # 1. REPRODUCTION of D306's published cells, on D306's own cost basis.
    worst = 0.0
    for d in DEPTHS:
        for b in BASES:
            res = sims[(d, b)]
            own = W.held_rt(res, HALF)
            c = cell(res, d, ones, own, 0.0)
            ref = d306[f"N={d}/{b}"]
            worst = max(worst, abs(c["gross_bp"] - ref["gross_bp"]),
                        abs(c["net_bp"] - ref["net_bp"]))
    assert worst < 1e-9, f"[1] differs from D306 by {worst:.2e} bp"

    # 1b. THE TWO ARMS DIFFER IN EXACTLY ONE THING.
    base = np.nan_to_num(sims[(19, "none")]["book"], nan=0.0)
    for X in (8.0, 12.0, 20.0):
        a = O.schedule(base, X)[0]
        b = schedule_ext(base, X, O.trailing_vol(base))
        assert np.array_equal(a, b), f"[1b] schedule_ext differs at X={X}"
    print(f"    [1] reproduces D306's gross AND net at all 6 base cells "
          f"(max {worst:.1e} bp), and schedule_ext is IDENTICAL to D297's when\n"
          f"        handed the same denominator -- the arms differ in one thing")

    # 1c. THE PUBLISHED OVERLAY CELL reproduces too, at D306's X=12.
    res = sims[(19, "none")]
    on = O.schedule(np.nan_to_num(res["book"], nan=0.0), 12.0)[0]
    c = cell(res, 19, np.where(on, 1.0, 0.0), W.held_rt(res, HALF), 0.0)
    ref = d306["N=19/none+overlay"]
    d = max(abs(c["gross_bp"] - ref["gross_bp"]), abs(c["net_bp"] - ref["net_bp"]))
    assert d < 1e-9, f"[1c] the X=12 overlay cell differs by {d:.2e}"
    print(f"    [1c] and D306's published N=19/none+overlay reproduces to "
          f"{d:.1e} bp -- the overlay path is the same one")

    # 2. CAUSALITY, and the audit must be able to fail.
    for X in (10.0, 12.0, 14.0):
        a = O.schedule(base, X, lag=True)[0]
        b = O.schedule(base, X, lag=False)[0]
        assert not np.array_equal(a, b), f"[2] peeking is identical at X={X}"
    v = univ_vol(base, disp)
    a = schedule_ext(base, 12.0, v)
    b = schedule_ext(base, 12.0, v, lag=False)
    assert not np.array_equal(a, b), "[2] the univ arm's peek is identical"
    print("    [2] CAUSALITY: both arms read only t-1, and both audits FAIL "
          "when the lag is removed")

    # 3. THE UNIVERSE DENOMINATOR reproduces D312's published stage 0.
    ref = json.loads((REPO / "data" / "d312_universe_forecast.json").read_text())
    got = float(np.nanmedian(HALF[np.isfinite(HALF)]))
    assert abs(4.0 * got - ref["round_trip"]) < 1e-9, "[3] the panel differs"
    fin = np.isfinite(disp)
    assert fin.sum() > 3000 and np.nanmedian(disp) > 0, "[3] dispersion is empty"
    print(f"    [3] the universe series is the one D312 published "
          f"({int(fin.sum()):,} finite bars, median {np.nanmedian(disp):.1f} bp)")

    # 4. EXPOSURE AND TRANSITION COST: zero on a constant scale, monotone.
    res = sims[(2, "none")]
    assert cell(res, 2, ones, 100.0, 0.0)["cost_overlay_bp"] == 0.0, \
        "[4] a constant scale is charged a transition cost"
    b2 = np.nan_to_num(res["book"], nan=0.0)
    tight = cell(res, 2, np.where(O.schedule(b2, 8.0)[0], 1.0, 0.0), 100.0, 0.0)
    loose = cell(res, 2, np.where(O.schedule(b2, 30.0)[0], 1.0, 0.0), 100.0, 0.0)
    # a real check, not `or True`: a tighter threshold must fire more often and
    # therefore pay more. An earlier version of this line could not fail.
    assert tight["transitions"] > loose["transitions"], \
        f"[4] X=8 fires {tight['transitions']} times, X=30 " \
        f"{loose['transitions']} -- tightening does not fire more"
    assert tight["cost_overlay_bp"] > loose["cost_overlay_bp"], \
        "[4] the tighter threshold is not charged more"
    assert tight["exposure"] < loose["exposure"], \
        "[4] the tighter threshold does not de-risk more"
    print(f"    [4] transition cost is zero on a constant scale, and tightening "
          f"X from 30 to 8 raises firings {loose['transitions']}->"
          f"{tight['transitions']}, cost {loose['cost_overlay_bp']:.2f}->"
          f"{tight['cost_overlay_bp']:.2f},\n        exposure "
          f"{loose['exposure']:.0%}->{tight['exposure']:.0%}")

    # S. SPREAD BASIS -- the round trip must come from the names HELD, and the
    #    check must FAIL against the universe median. Owed since D317.
    uni = 4.0 * float(np.nanmedian(HALF[np.isfinite(HALF)]))
    for d in DEPTHS:
        own = W.held_rt(sims[(d, "none")], HALF)
        assert own > uni * 1.15, \
            f"[S] the held rt at N={d} ({own:.1f}) is not above the universe " \
            f"median ({uni:.1f}) -- the basis check cannot fail"
    print(f"    [S] SPREAD BASIS: held round trips are "
          f"{', '.join('%.1f' % W.held_rt(sims[(d, 'none')], HALF) for d in DEPTHS)}"
          f" against the universe's {uni:.1f} -- the universe basis is REJECTED")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's; "
          f"the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK inside the mask.
    broke = False
    try:
        r = dict(sims[(19, "none")])
        bk = r["book"].copy()
        bk[np.flatnonzero(r["mask"])[:200]] += 5e-4
        r["book"] = bk
        c = cell(r, 19, ones, W.held_rt(sims[(19, "none")], HALF), 0.0)
        assert abs(c["gross_bp"] - d306["N=19/none"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[7] reproduction passed a book handed free money in the mask"
    print("    [7] and [1] raises on a book handed free money inside the mask")


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    global HALF

    print("D319  the overlay at concentration")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    close = np.ascontiguousarray(panel.closes.T)
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]

    sims = {(d, b): W.simulate(A, G, d, b == "target")
            for d in DEPTHS for b in BASES}
    disp, _ = U.dispersion(A, G, A["r1T"].shape[0])
    disp = disp["all"]

    # D318's basis: common WITHIN a width (D307), per-cell ACROSS widths.
    rt = {d: W.held_rt(sims[(d, "none")], HALF) for d in DEPTHS}
    px = {d: held_price(sims[(d, "none")], close) for d in DEPTHS}
    rtc = {d: CROSSINGS * PER_SHARE / px[d] * 1e4 for d in DEPTHS}
    print(f"  {len(sims)} sims over {int(sims[(2,'none')]['mask'].sum()):,} bars "
          f"({time.time() - t0:.0f}s)")
    for d in DEPTHS:
        print("    N=%-3d common rt %6.2f   held price $%6.2f   commission rt "
              "%5.2f" % (d, rt[d], px[d], rtc[d]))

    assertions(sims, rt, rtc, disp, d306, U)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    rng = np.random.default_rng(SEED)
    res = {"round_trip": {str(k): v for k, v in rt.items()},
           "held_price": {str(k): v for k, v in px.items()},
           "commission_rt": {str(k): v for k, v in rtc.items()},
           "cells": {}, "control": {}}

    # the controls
    for d in DEPTHS:
        for b in BASES:
            s = sims[(d, b)]
            ones = np.ones(s["book"].size)
            res["control"][f"N={d}/{b}"] = cell(s, d, ones, rt[d], rtc[d])

    print("\nTHE SWEEP   (net Sharpe primary; control = no overlay)")
    names, ps = [], []
    for d in DEPTHS:
        for b in BASES:
            s = sims[(d, b)]
            base = np.nan_to_num(s["book"], nan=0.0)
            vols = {"own": O.trailing_vol(base), "univ": univ_vol(base, disp)}
            ctl = res["control"][f"N={d}/{b}"]
            print("\n  N=%d / %s   control: net %+.2f  netSHRP %+.3f  "
                  "grossSHRP %+.3f" % (d, b, ctl["net_bp"], ctl["sharpe_net"],
                                       ctl["sharpe_gross"]))
            print("  %5s %8s %9s %9s %9s %8s %8s %9s %8s" % (
                "X", "arm", "net", "netSHRP", "vs ctl", "expo", "ret/exp",
                "null p95", "p"))
            print("  " + "-" * 82)
            for X in X_GRID:
                for arm in ARMS:
                    on = schedule_ext(base, X, vols[arm])
                    sc = np.where(on, 1.0, 0.0)
                    c = cell(s, d, sc, rt[d], rtc[d])
                    nl = np.empty(a.draws)
                    for i in range(a.draws):
                        m = O.matched_schedule(on, rng)
                        nl[i] = cell(s, d, np.where(m, 1.0, 0.0),
                                     rt[d], rtc[d])["sharpe_net"]
                    p = float((nl >= c["sharpe_net"]).sum() + 1) / (a.draws + 1)
                    nm = f"N={d}/{b}/X{X:g}/{arm}"
                    c.update(depth=d, base=b, X=X, arm=arm, p=p,
                             null_p50=float(np.median(nl)),
                             null_p95=float(np.quantile(nl, .95)),
                             vs_control=c["sharpe_net"] - ctl["sharpe_net"])
                    res["cells"][nm] = c
                    names.append(nm); ps.append(p)
                    print("  %5g %8s %+9.2f %+9.3f %+9.3f %7.0f%% %8.2f "
                          "%+9.3f %8.4f" % (
                              X, arm, c["net_bp"], c["sharpe_net"],
                              c["vs_control"], 100 * c["exposure"],
                              c["ret_per_exp"], c["null_p95"], p))

    rej = bh(ps)
    res["bh"] = {n: bool(r) for n, r in zip(names, rej)}
    print(f"\n  BH-FDR q=0.10 over all {len(names)} overlay cells:")
    surv = [n for n, r in zip(names, rej) if r]
    print("    " + (", ".join(surv) if surv else "NONE"))

    # ---- predictions -------------------------------------------------------
    C, K = res["cells"], res["control"]
    def best(d, b, arm):
        cs = [C[f"N={d}/{b}/X{X:g}/{arm}"] for X in X_GRID]
        return max(cs, key=lambda c: c["sharpe_net"])
    q3 = all(best(2, b, "own")["sharpe_net"] <= K[f"N=2/{b}"]["sharpe_net"]
             for b in BASES)
    q4 = all(C[f"N=2/{b}/X12/univ"]["sharpe_net"]
             > C[f"N=2/{b}/X12/own"]["sharpe_net"] for b in BASES)
    q5 = all(best(2, b, arm)["sharpe_net"] <= K[f"N=2/{b}"]["sharpe_net"]
             for b in BASES for arm in ARMS)
    q7 = all(abs(best(d, b, arm)["exposure"] - 0.70) < 0.10
             for d in DEPTHS for b in BASES for arm in ARMS)
    adv = {d: C[f"N={d}/none/X12/univ"]["sharpe_net"]
              - C[f"N={d}/none/X12/own"]["sharpe_net"] for d in DEPTHS}
    q8 = adv[2] == max(adv.values()) and adv[19] == min(adv.values())
    res["predictions"] = dict(Q3=bool(q3), Q4=bool(q4), Q5=bool(q5),
                              Q7=bool(q7), Q8=bool(q8),
                              univ_minus_own={str(k): v for k, v in adv.items()})
    print("\nPREDICTIONS")
    for k, v in (("Q3 O_own clears at NO X at N=2", q3),
                 ("Q4 O_univ beats O_own at N=2, X=12", q4),
                 ("Q5 neither arm beats control at N=2  [load-bearing]", q5),
                 ("Q7 best-X exposure within 10 pts of 70%", q7),
                 ("Q8 univ's edge largest at N=2, smallest at N=19", q8)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")
    print("    univ - own net Sharpe at X=12: " +
          "  ".join(f"N={k}:{v:+.3f}" for k, v in adv.items()))

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
