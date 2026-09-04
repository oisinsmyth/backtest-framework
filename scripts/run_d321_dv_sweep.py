"""D321 -- the dollar-volume threshold, swept, with the bar declared in advance.

    uv run python scripts/run_d321_dv_sweep.py --selftest
    uv run python scripts/run_d321_dv_sweep.py [--draws 200]

PRE-REGISTERED AT `1c7299c`, committed before this file existed (R8).

D320's dv25 beat the control designed to kill it -- it cuts held half-spread
18.31 -> 14.61 at an UNCHANGED price, $70.70 -> $72, and its price-matched control
returns +0.305 against its +0.464 -- and it did not survive its own null at
p = 0.119.

THE BAR IS DECLARED AND MAY BE UNREACHABLE. D320's nulls put the lift over control
needed to clear p = 0.05 at +0.142 / +0.207 / +0.097 at the 10th / 25th / 40th
percentile. dv25 posted +0.129 against +0.207. So unless the optimum sits away
from 25, this study cannot succeed on individual significance.

WHAT CAN STILL DECIDE IT IS THE SHAPE. D297's overlay was credible because FOUR
CONTIGUOUS thresholds cleared, not because one cell had a small p. A hump measured
at three points is nothing; the same hump at nineteen is evidence. QA3 is that
test.

THE REAL QUESTION, answered either way: why does dollar volume beat the DIRECT
spread filter at cutting spread? The spread arm conditions on the per-name
Corwin-Schultz estimate D302 measured as noisy, so it discards good names that
merely MEASURED wide. A SPREAD-MATCHED CONTROL -- a direct spread filter
calibrated to the same held half-spread at every threshold -- tests that directly.

[F] FILL IS CARRIED FOR THE FIRST TIME, owed since D320. A filter that starves the
gate makes a NARROWER BOOK AT FULL NOTIONAL, because D306's simulator weights
1/n_t. Turnover therefore divides by the names HELD, not the nominal slots, and
the assertion FAILS against the nominal form.
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


X = _load("d320", "run_d320_tilt_filters.py")
W, D, M, SP = X.W, X.D, X.M, X.SP

DEPTH = 2
PCTS = (5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 25.0, 28.0, 30.0, 33.0,
        35.0, 38.0, 40.0, 45.0, 50.0, 55.0, 60.0)
FILL_FLOOR = 0.85
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d321_dv_sweep.json"


def score(A, keep, G4):
    """One book, costed on the names HELD. G4 = (HALF, CLOSE, DV, finT)."""
    HALF, CLOSE, DV, _ = G4
    res = W.simulate(A, X.gate_with(A, keep), DEPTH, True)
    ok = res["mask"]
    b = res["book"][ok]
    bars = b.size
    e = int(res["ent"][ok].sum())
    held = float(res["held"][ok].mean())
    fill = held / (2.0 * DEPTH)
    hs, px = X.held_median(res, HALF), X.held_median(res, CLOSE)
    dvv = X.held_median(res, DV)
    rt = 4.0 * hs
    rtc = X.CROSSINGS * X.PER_SHARE / px * 1e4 if px > 0 else np.nan
    # [F]: the traded fraction divides by the names HELD, not the nominal slots
    turn_nom = e / float(DEPTH) / 2.0 / bars
    turn_held = e / held / bars
    g = float(b.mean()) * 1e4
    v = float(b.std(ddof=1)) * 1e4
    net_nom = g - (rt + rtc) * turn_nom
    net = g - (rt + rtc) * turn_held
    eq = np.cumsum(b)
    return dict(gross_bp=g, vol_bp=v, net_bp=net, net_nominal_bp=net_nom,
                sharpe_net=net / v * np.sqrt(ANN) if v > 0 else 0.0,
                sharpe_nominal=net_nom / v * np.sqrt(ANN) if v > 0 else 0.0,
                sharpe_gross=g / v * np.sqrt(ANN) if v > 0 else 0.0,
                fill=fill, held_per_bar=held, turnover=turn_held,
                turnover_nominal=turn_nom, round_trip=rt, commission_rt=rtc,
                cost_bp=(rt + rtc) * turn_held,
                held_half_spread=hs, held_price=px, held_dv=dvv,
                breakeven_rt=rt * g / ((rt + rtc) * turn_held)
                if turn_held > 0 else 0.0,
                maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
                entries=e, bars=bars), res


def match(A, V, finT, G4, var, target, key, lo=0.0, hi=70.0, iters=13):
    """Bisect a filter's percentile until `key` matches `target`.

    Both objectives are monotone in the percentile -- a price floor raises held
    price, a spread cut lowers held spread -- so bisection is exact enough.
    """
    up = key == "held_price"
    best = None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        c, _ = score(A, X.keep_mask(V[var], finT, mid, X.BAD_LOW[var]), G4)
        best = c
        if (c[key] < target) == up:
            lo = mid
        else:
            hi = mid
    best["pct"] = 0.5 * (lo + hi)
    return best


def bh(ps, q=0.10):
    o = np.argsort(ps)
    m = len(ps)
    hit = np.asarray(ps)[o] <= (np.arange(1, m + 1) / m) * q
    k = np.flatnonzero(hit).max() + 1 if hit.any() else 0
    rej = np.zeros(m, bool)
    rej[o[:k]] = True
    return rej


def longest_run(flags):
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------- assertions
def assertions(A, V, finT, G4, d320, d320b, d306):
    print("\nASSERTIONS")
    ones = np.ones(finT.shape, bool)

    # 1. REPRODUCTION of D320's dv cells and of D306's unfiltered book.
    c0, _ = score(A, ones, G4)
    assert abs(c0["gross_bp"] - d306["N=2/target"]["gross_bp"]) < 1e-9, \
        "[1] the unfiltered book differs from D306"
    worst = 0.0
    for p in (10.0, 25.0, 40.0):
        c, _ = score(A, X.keep_mask(V["dv"], finT, p, True), G4)
        ref = d320["cells"][f"N=2/dv{p:g}"]
        refb = d320b["cells"][f"N=2/dv{p:g}"]
        worst = max(worst, abs(c["gross_bp"] - ref["gross_bp"]),
                    abs(c["net_nominal_bp"] - ref["net_bp"]),
                    abs(c["net_bp"] - refb["net_adj"]))
    assert worst < 1e-9, f"[1] differs from D320 by {worst:.2e} bp"
    print(f"    [1] the unfiltered book reproduces D306, and dv10/25/40 reproduce "
          f"D320's NOMINAL and D320b's FILL-ADJUSTED nets to {worst:.1e} bp")

    # F. FILL -- and the check must FAIL against the nominal-slot form.
    c, _ = score(A, X.keep_mask(V["dv"], finT, 60.0, True), G4)
    assert c["fill"] < 0.95, f"[F] the 60th-percentile book fills {c['fill']:.0%}"
    r = c["turnover"] / c["turnover_nominal"]
    assert abs(r - 1.0 / c["fill"]) < 1e-9, "[F] the held turnover is not turn/fill"
    assert c["net_bp"] < c["net_nominal_bp"] - 0.5, \
        f"[F] the nominal form does not overstate net: {c['net_bp']:.2f} vs " \
        f"{c['net_nominal_bp']:.2f} -- the assertion cannot fail"
    print(f"    [F] FILL: at the 60th percentile the book fills {c['fill']:.0%}, "
          f"turnover on names HELD is {r:.2f}x the nominal form, and net falls "
          f"{c['net_nominal_bp']:+.2f} -> {c['net_bp']:+.2f}\n"
          f"        -- the nominal-slot form is REJECTED")

    # 2. CAUSALITY.
    raw = np.where(np.isfinite(G4[2]), G4[2], np.nan)
    ok = np.isfinite(raw)
    cs = np.concatenate([np.zeros((1, raw.shape[1])), np.cumsum(np.where(ok, raw, 0.0), 0)])
    cn = np.concatenate([np.zeros((1, raw.shape[1])), np.cumsum(ok, 0)])
    j = np.arange(X.WIN, raw.shape[0] + 1)
    cnt = cn[j] - cn[j - X.WIN]
    unlag = np.full(raw.shape, np.nan)
    with np.errstate(invalid="ignore"):
        unlag[j - 1] = np.where(cnt >= X.WIN / 3,
                                (cs[j] - cs[j - X.WIN]) / np.maximum(cnt, 1), np.nan)
    a = X.keep_mask(V["dv"], finT, 25.0, True)
    b = X.keep_mask(unlag, finT, 25.0, True)
    assert not np.array_equal(a, b), "[2] peeking gives the same exclusion set"
    ca, _ = score(A, a, G4)
    cb, _ = score(A, b, G4)
    assert abs(ca["gross_bp"] - cb["gross_bp"]) > 1e-12, "[2] same book"
    print(f"    [2] CAUSALITY: the peeking variant moves {np.mean(a != b):.1%} of "
          f"name-bars and changes the book -- the audit can fail")

    # 3. THE CONTROLS MATCH AND ARE DISTINCT.
    t, _ = score(A, X.keep_mask(V["dv"], finT, 25.0, True), G4)
    pm = match(A, V, finT, G4, "price", t["held_price"], "held_price")
    sm = match(A, V, finT, G4, "spread", t["held_half_spread"], "held_half_spread")
    assert abs(pm["held_price"] / t["held_price"] - 1) < 0.05, \
        f"[3] price-matched off by {pm['held_price'] / t['held_price'] - 1:+.1%}"
    assert abs(sm["held_half_spread"] / t["held_half_spread"] - 1) < 0.05, \
        f"[3] spread-matched off by " \
        f"{sm['held_half_spread'] / t['held_half_spread'] - 1:+.1%}"
    assert abs(pm["gross_bp"] - t["gross_bp"]) > 1e-9, "[3] price control IS dv25"
    assert abs(sm["gross_bp"] - t["gross_bp"]) > 1e-9, "[3] spread control IS dv25"
    print(f"    [3] at dv25 the price-matched control holds ${pm['held_price']:.0f} "
          f"against ${t['held_price']:.0f} and the SPREAD-matched holds "
          f"{sm['held_half_spread']:.2f} against\n        "
          f"{t['held_half_spread']:.2f} bp -- both match and neither is the "
          f"treatment")

    # 4. THE NULL IS TURNOVER-MATCHED, and the permutation is shown to churn.
    rng = np.random.default_rng(1)
    k = X.keep_mask(V["dv"], finT, 25.0, True)
    e = {}
    for nm, mask in (("treatment", k), ("rotated", np.roll(k, 211, axis=0)),
                     ("permuted", k[:, rng.permutation(k.shape[1])])):
        e[nm] = score(A, mask, G4)[0]["entries"]
    assert abs(e["rotated"] / e["treatment"] - 1.0) < 0.15, f"[4] not matched: {e}"
    # AN EARLIER VERSION OF THIS LINE DEMANDED THE PERMUTATION CHURN >10%, ON
    # D320's spread-filter number of +28.2%. It fails here: the dv exclusion set
    # churns only +4.8% under permutation, because liquid names stay liquid and
    # the set is far less correlated with liveness than the spread set is. That
    # is a property of the FILTER, not a universal, and asserting it was wrong.
    # What is universal, and still falsifiable, is that the rotation must be the
    # better-matched of the two.
    rot_err = abs(e["rotated"] / e["treatment"] - 1.0)
    perm_err = abs(e["permuted"] / e["treatment"] - 1.0)
    assert rot_err < perm_err, \
        f"[4] the rotation is NOT better turnover-matched than the permutation: {e}"
    print(f"    [4] the null is turnover-matched and better so than the "
          f"permutation: treatment {e['treatment']:,}, ROTATED {e['rotated']:,} "
          f"({e['rotated'] / e['treatment'] - 1:+.1%}), permuted "
          f"{e['permuted']:,} ({e['permuted'] / e['treatment'] - 1:+.1%})")
    print(f"        -- note the dv set churns far less under permutation than "
          f"D320's spread set (+28.2%): liquid names stay liquid, so the "
          f"exclusion\n        set is much less correlated with liveness")

    # S. SPREAD BASIS.
    uni = 4.0 * float(np.nanmedian(G4[0][np.isfinite(G4[0])]))
    assert c0["round_trip"] > uni * 1.10, "[S] the basis check cannot fail"
    print(f"    [S] SPREAD BASIS: the held rt of {c0['round_trip']:.1f} rejects "
          f"the universe median {uni:.1f}")

    # C. COST DIMENSIONS.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's; "
          f"the doubled form is rejected")

    # 6. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        res = W.simulate(A, X.gate_with(A, ones), DEPTH, True)
        bk = res["book"].copy()
        bk[np.flatnonzero(res["mask"])[:200]] += 5e-4
        r2 = dict(res, book=bk)
        gg = float(r2["book"][r2["mask"]].mean()) * 1e4
        assert abs(gg - d306["N=2/target"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] reproduction passed a book handed free money in the mask"
    print("    [6] and [1] raises on a book handed free money inside the mask")
    return c0


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print("D321  the dollar-volume sweep")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    finT = np.asarray(A["finT"])
    DV = X.roll_mean_T(CLOSE * VOL)
    V = {"spread": X.roll_mean_T(HALF), "price": X.roll_mean_T(CLOSE), "dv": DV}
    G4 = (HALF, CLOSE, DV, finT)
    d320 = json.loads((REPO / "data" / "d320_tilt_filters.json").read_text())
    d320b = json.loads((REPO / "data" / "d320b_fill_adjusted.json").read_text())
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    print(f"  panel {finT.shape} ({time.time() - t0:.0f}s)")

    ctl = assertions(A, V, finT, G4, d320, d320b, d306)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    rng = np.random.default_rng(SEED)
    ones = np.ones(finT.shape, bool)
    res = {"control": ctl, "cells": {}, "matched": {}}
    k0 = ctl["sharpe_net"]

    print(f"\n  CONTROL: net {ctl['net_bp']:+.2f}  netSHRP {k0:+.3f}  "
          f"fill {ctl['fill']:.0%}  half {ctl['held_half_spread']:.2f}  "
          f"price ${ctl['held_price']:.0f}")
    print("\nTHE SWEEP   (fill-adjusted; * = fill < %.0f%%, confounded with width)"
          % (100 * FILL_FLOOR))
    h = "%1s %5s %8s %8s %7s %9s %9s %9s %8s %8s %8s"
    print(h % ("", "pct", "gross", "NET", "fill", "netSHRP", "vs ctl", "null p95",
               "NEEDED", "p", "half"))
    print("-" * 96)
    names, ps, flags = [], [], []
    for p in PCTS:
        keep = X.keep_mask(V["dv"], finT, p, True)
        c, _ = score(A, keep, G4)
        nl = np.empty(a.draws)
        for i in range(a.draws):
            rk = np.roll(keep, int(rng.integers(63, keep.shape[0] - 63)), axis=0)
            nl[i] = score(A, rk, G4)[0]["sharpe_net"]
        pv = float((nl >= c["sharpe_net"]).sum() + 1) / (a.draws + 1)
        p95 = float(np.quantile(nl, .95))
        c.update(pct=p, p=pv, null_p50=float(np.median(nl)), null_p95=p95,
                 vs_control=c["sharpe_net"] - k0, needed=p95 - k0,
                 ok_fill=bool(c["fill"] >= FILL_FLOOR))
        res["cells"][f"dv{p:g}"] = c
        names.append(f"dv{p:g}"); ps.append(pv)
        flags.append(c["vs_control"] > 0 and c["ok_fill"])
        print(h % ("" if c["ok_fill"] else "*", "%g" % p, "%+.2f" % c["gross_bp"],
                   "%+.2f" % c["net_bp"], "%.0f%%" % (100 * c["fill"]),
                   "%+.3f" % c["sharpe_net"], "%+.3f" % c["vs_control"],
                   "%+.3f" % p95, "%+.3f" % c["needed"], "%.4f" % pv,
                   "%.2f" % c["held_half_spread"]))

    # ---- the two matched controls, at every threshold ----------------------
    print("\nTHE MATCHED CONTROLS -- price (D284's test) and SPREAD (the mechanism)")
    print("  %5s %10s %11s %11s %12s %12s" % (
        "pct", "dv SHRP", "price-m", "spread-m", "vs price-m", "vs spread-m"))
    print("  " + "-" * 66)
    for p in PCTS:
        c = res["cells"][f"dv{p:g}"]
        pm = match(A, V, finT, G4, "price", c["held_price"], "held_price")
        sm = match(A, V, finT, G4, "spread", c["held_half_spread"],
                   "held_half_spread")
        c["vs_price_matched"] = c["sharpe_net"] - pm["sharpe_net"]
        c["vs_spread_matched"] = c["sharpe_net"] - sm["sharpe_net"]
        res["matched"][f"dv{p:g}"] = dict(price=pm, spread=sm)
        print("  %5g %10.3f %11.3f %11.3f %+12.3f %+12.3f" % (
            p, c["sharpe_net"], pm["sharpe_net"], sm["sharpe_net"],
            c["vs_price_matched"], c["vs_spread_matched"]))

    rej = bh(ps)
    n05 = int(sum(x < 0.05 for x in ps))
    res["bh"] = {n: bool(r) for n, r in zip(names, rej)}
    surv = [n for n, r in zip(names, rej) if r]
    print(f"\n  BH-FDR q=0.10 over {len(names)} thresholds: "
          f"{', '.join(surv) if surv else 'NONE'}")
    print(f"  thresholds clearing p<0.05: {n05} against "
          f"{0.05 * len(names):.2f} expected by chance")

    # ---- predictions -------------------------------------------------------
    C = res["cells"]
    run = longest_run(flags)
    qa2 = all(c["p"] >= 0.05 for c in C.values())
    qa3 = run >= 4
    qa4 = all(c.get("vs_spread_matched", -1) > 0 for c in C.values())
    qa5 = all(c["vs_price_matched"] > 0 for c in C.values() if c["ok_fill"])
    qa7 = all(c["sharpe_net"] <= c["sharpe_nominal"] + 1e-12 for c in C.values())
    qa8 = all(C[f"dv{b:g}"]["held_half_spread"] <= C[f"dv{a_:g}"]["held_half_spread"]
              + 1e-9 for a_, b in zip(PCTS, PCTS[1:])) and \
        all(abs(c["held_price"] / ctl["held_price"] - 1) < 0.10 for c in C.values())
    res["predictions"] = dict(QA2=bool(qa2), QA3=bool(qa3), QA4=bool(qa4),
                              QA5=bool(qa5), QA7=bool(qa7), QA8=bool(qa8),
                              longest_contiguous_run=run,
                              clearing_at_05=n05)
    print("\nPREDICTIONS")
    for k, v in (("QA2 no threshold clears its null  [load-bearing]", qa2),
                 ("QA3 >=4 CONTIGUOUS thresholds beat control (D297's shape)", qa3),
                 ("QA4 dv beats the SPREAD-matched control everywhere", qa4),
                 ("QA5 dv beats the price-matched control where fill>=85%", qa5),
                 ("QA7 fill-adjusted advantage < nominal everywhere", qa7),
                 ("QA8 half-spread falls monotonically, price within 10%", qa8)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")
    print(f"    longest contiguous run beating control: {run} of {len(PCTS)}")

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
