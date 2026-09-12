"""D413 EXTRAS -- EXPLORATORY, RUN AFTER THE PRIMARY, AND EVERY ARM CAN ONLY HURT IT.

    uv run python scripts/run_d413_extras.py --run

NOT part of the committed bar. The primary verdict is run_d413_distance_armed_zones.py's and is
not touched here. These arms exist because D413 passed T1, T2 and T3 -- the first construction in
this programme to beat a matched-geometry level control -- and a passing result deserves harder
questions than a failing one, not easier ones.

ARM 1 -- IS IT SHORT-TERM REVERSAL? The construction buys a demand zone when price falls back into
it and sells a supply zone when price rallies into it. That is "fade the move back", and P3 tested
the wrong horizon for it: it measured the trailing TWENTY-day return, and short-term reversal lives
at three to five days. So: stratify the response on the SIGNED TRAILING 5-DAY return at the touch,
and report the correlation. If the whole effect sits in the most-reverted quintile, this is
reversal wearing a supply-and-demand costume.

ARM 2 -- THE MATCHING GAP [MATCH] DOES NOT COVER. LVL matches the (width, distance) geometry
exactly, but nothing checked that the control's zones are TOUCHED at the same rate or at the same
AGE. A real zone sits where price has recently traded and a permuted band may not, so the two
populations can differ in exactly the way that matters -- the response is measured at the touch,
and a different touch-age mix is a different experiment. Measured here rather than assumed.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413", REPO / "scripts" / "run_d413_distance_armed_zones.py")
M = importlib.util.module_from_spec(_s)
sys.modules["d413"] = M
_s.loader.exec_module(M)
Z4, D = M.Z4, M.D

OUT = REPO / "data" / "d413_extras.json"
NQ = 5


def run():
    t0 = time.time()
    print("D413 EXTRAS -- exploratory, after the fact, every arm can only hurt the result\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z = A["Z"]
    g = A["good"]
    r = A["r"]
    tt = A["tt"]
    age = A["idx"] + 1
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))

    # ---------------- ARM 1: short-term reversal
    res = {}
    print("  ARM 1 -- is it short-term reversal?\n")
    for k in (3, 5, 10, 20):
        tr = D.trailing_ret(lg, k)
        v = np.full(len(g), np.nan)
        v[g] = tr[tt[g], Z["i"][g]] * Z["side"][g]      # SIGNED: negative = price reverted into it
        m = g & np.isfinite(v)
        c = float(np.corrcoef(r[m], v[m])[0, 1])
        res[f"corr_trailing{k}"] = c
        print(f"    corr(resp, signed trailing {k:2d}d at touch)  {c:+.4f}   n {int(m.sum()):,}")

    tr5 = D.trailing_ret(lg, 5)
    v = np.full(len(g), np.nan)
    v[g] = tr5[tt[g], Z["i"][g]] * Z["side"][g]
    m = g & np.isfinite(v)
    q = np.quantile(v[m], np.linspace(0, 1, NQ + 1))
    q[-1] += 1e-12
    b = np.clip(np.searchsorted(q, v[m], side="right") - 1, 0, NQ - 1)
    rr = r[m]
    rows = []
    print(f"\n    response by quintile of the SIGNED trailing 5-day return "
          f"(Q1 = most reverted INTO the zone):")
    for j in range(NQ):
        s = b == j
        rows.append(dict(n=int(s.sum()), mean=float(rr[s].mean()),
                         se=float(rr[s].std(ddof=1) / np.sqrt(max(s.sum(), 2))),
                         tr5_mean=float(v[m][s].mean())))
        print(f"      Q{j+1}  n {rows[-1]['n']:7,}  trailing5 {1e4*rows[-1]['tr5_mean']:+8.0f} bp"
              f"   resp {1e4*rows[-1]['mean']:+7.2f} +-{1e4*rows[-1]['se']:.2f} bp")
    res["by_trailing5"] = rows
    pos = sum(1 for x in rows if x["mean"] - 2 * x["se"] > 0)
    print(f"\n    quintiles with a mean more than 2 SE above zero: {pos} of {NQ}")
    print(f"    -> {'NOT explained by reversal alone' if pos >= 3 else 'CONCENTRATED in the reverted tail'}")
    res["quintiles_positive_2se"] = pos

    # ---------------- ARM 2: the matching gap
    print(f"\n  ARM 2 -- does LVL's control population match on TOUCH RATE and AGE?\n")
    HIw, LOw, ok, rows_w = A["HIw"], A["LOw"], A["ok"], A["rows"]
    rng = np.random.default_rng(77)
    side = Z["side"]
    grp = {s: np.where(side == s)[0] for s in (1, -1)}
    rate, a50, a_res = [], [], []
    for _ in range(20):
        w2, d2 = np.empty_like(Z["wid"]), np.empty_like(Z["dist"])
        for s, gg in grp.items():
            p = rng.permutation(gg)
            w2[gg], d2[gg] = Z["wid"][p], Z["dist"][p]
        hi_b = np.where(side > 0, Z["Ca"] - d2, Z["Ca"] + d2 + w2)
        lo_b = np.where(side > 0, Z["Ca"] - d2 - w2, Z["Ca"] + d2)
        idx, has = Z4.touches(HIw, LOw, ok, lo_b, hi_b)
        _, gc, _ = Z4.response(P, Z, rows_w, idx, has, side, M.H)
        rate.append(float(has.mean()))
        a50.append(float(np.median((idx + 1)[has])))
        a_res.append(int(gc.sum()))
    res["match_gap"] = dict(real_touch_rate=float(A["has"].mean()),
                            lvl_touch_rate=float(np.mean(rate)),
                            real_age_p50=float(np.median(age[A["has"]])),
                            lvl_age_p50=float(np.mean(a50)),
                            real_resolved=int(g.sum()), lvl_resolved=float(np.mean(a_res)))
    mg = res["match_gap"]
    print(f"    touch rate    real {100*mg['real_touch_rate']:.1f}%   "
          f"LVL {100*mg['lvl_touch_rate']:.1f}%")
    print(f"    median age    real {mg['real_age_p50']:.0f} bars   LVL {mg['lvl_age_p50']:.1f} bars")
    print(f"    resolved      real {mg['real_resolved']:,}   LVL {mg['lvl_resolved']:,.0f}")
    ok_match = abs(mg["real_age_p50"] - mg["lvl_age_p50"]) <= 1.5 and \
        abs(mg["real_touch_rate"] - mg["lvl_touch_rate"]) <= 0.05
    res["match_gap"]["comparable"] = bool(ok_match)
    print(f"    -> the two populations are {'COMPARABLE' if ok_match else 'NOT comparable, and '
                                           'that is a caveat on T2'}")

    OUT.write_text(json.dumps(dict(exploratory=True, **res), indent=1, default=float),
                   encoding="utf-8")
    print(f"\n  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
