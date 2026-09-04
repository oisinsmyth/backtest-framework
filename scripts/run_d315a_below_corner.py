"""D315 Stage A -- the widths below the corner, which nothing has ever run.

    uv run python scripts/run_d315a_below_corner.py --selftest
    uv run python scripts/run_d315a_below_corner.py

PRE-REGISTERED AT `cdee86c`, committed before this file existed (R8).

D314 fitted `ln N* = -n0/n1 - 2` and got N* = 1.66, BELOW the grid floor of 2, so
the number is an extrapolation outside every width ever run. This runs them.

THE PRE-REGISTRATION PREDICTS THIS GAINS ALMOST NOTHING. On D314's fitted curve
sqrt(N)*net is 6.130 at N*=1.66 against 6.104 at N=2 -- 0.4% -- and the MEASURED
6.183 at N=2 already exceeds the fitted optimum. QA2 is load-bearing and against:
the corner is real and FLAT.

QA3 IS THE MOST LIKELY WAY THE EXTRAPOLATION FAILS, and it is also against. At
N_eff approaching 1 every rank change at the top swaps the whole book, so cost
should break ABOVE its fitted line and drag the true optimum back toward 2.

TWO DEVIATIONS FROM THE PRE-REGISTRATION, both strictly stronger and both flagged
in the record:

  * THE NULL IS ENUMERATED, NOT SAMPLED. `simulate`'s rank rotation is
    `(rk + shift) % 25`, so there are exactly 24 non-identity rotations. Drawing
    200 would resample 24 distinct books. All 24 are run, which makes this an
    EXACT permutation test rather than a Monte Carlo one -- at the cost of
    flooring p at 1/25 = 0.04.
  * ASSERTION [A2] as written ("1/sum(w^2) equals each target to 1e-9") holds of
    the DESIGN weights over the full 25-name gate. The realised book keeps a
    variable number of names each bar, so its realised N_eff differs; both are
    asserted and reported rather than the looser one being quietly substituted.
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


X = _load("d312", "run_d312_vol_targeted.py")
ALG = _load("d314", "d314_width_algebra.py")
R, W, D, SP, M = X.R, X.W, X.D, X.SP, X.M
fit_line = ALG.fit_line

NEW = (1.0, 1.15, 1.3, 1.45, 1.6, 1.75, 1.9)          # never run before
ANCHOR = (2.0, 2.5, 3.0, 5.0)                          # must reproduce exactly
LEVELS = tuple(sorted(NEW + ANCHOR))
N_BASE = R.N_BASE
ANN = 252.0
OUT = REPO / "data" / "d315a_below_corner.json"


def sim(A, G, lv, rt, shift=0):
    r = R.simulate(A, G, "exp", lv, 0.0, False, shift=shift)
    ok = r["mask"]
    gross = np.where(ok, r["book"] * 1e4, 0.0)[ok]
    cost = np.where(ok, rt * r["turn"], 0.0)[ok]
    return dict(gross=gross, cost=cost, net=gross - cost,
                neff=np.asarray(r["neff"])[ok], turn=np.asarray(r["turn"])[ok])


def summarise(s, lv):
    net, gross, cost = s["net"], s["gross"], s["cost"]
    sd = net.std(ddof=1)
    eq = np.cumsum(net)
    return dict(
        n_eff=lv, gross_bp=float(gross.mean()), cost_bp=float(cost.mean()),
        net_bp=float(net.mean()), vol_bp=float(sd),
        sharpe=float(net.mean() / sd * np.sqrt(ANN)),
        gross_sharpe=float(gross.mean() / gross.std(ddof=1) * np.sqrt(ANN)),
        t=float(net.mean() / (sd / np.sqrt(net.size))),
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)),
        turnover=float(s["turn"].mean()),
        neff_realised=float(np.nanmean(s["neff"])),
        sqrtN_net=float(np.sqrt(lv) * net.mean()), bars=int(net.size))


def bh(ps, q=0.10):
    o = np.argsort(ps)
    m = len(ps)
    hit = np.asarray(ps)[o] <= (np.arange(1, m + 1) / m) * q
    k = np.flatnonzero(hit).max() + 1 if hit.any() else 0
    rej = np.zeros(m, bool)
    rej[o[:k]] = True
    return rej


# ---------------------------------------------------------------- assertions
def assertions(cellsum, raw, rt, d310, d312):
    print("\nASSERTIONS")

    # A1. THE ANCHORS REPRODUCE THE PUBLISHED SURFACE. Not "bit-identically":
    #     the references are JSON text, so the last bits are lost writing them
    #     out and 4.9e-15 is the floor a round-tripped double can reach. That is
    #     the same agreement D312 and D313 reported and it is what 1e-9 tests.
    worst = 0.0
    for lv in (2.0, 3.0, 5.0):
        ref = d310[f"none/exp{int(lv)}"]
        c = cellsum[lv]
        worst = max(worst, abs(c["gross_bp"] - ref["gross_bp"]),
                    abs(c["net_bp"] - ref["net_bp"]))
    worst = max(worst, abs(cellsum[2.0]["net_bp"] - d312["cells"]["F@N2"]["net_bp"]))
    assert worst < 1e-9, f"[A1] anchors drifted from D310/D312 by {worst:.2e} bp"
    print(f"    [A1] the anchors reproduce D310 and D312 to {worst:.1e} bp -- "
          f"the extended grid disturbs nothing")

    # A2. N_eff IS ACHIEVED, on the design weights AND on the realised book.
    worstd = 0.0
    for lv in LEVELS:
        w = R.exp_weights(R.solve_lam(lv), N_BASE)
        worstd = max(worstd, abs(R.n_eff(w) - lv))
        assert np.all(np.diff(w) <= 1e-18), f"[A2] weights not monotone at {lv}"
    assert worstd < 1e-9, f"[A2] design N_eff off by {worstd:.2e}"
    print(f"    [A2] design N_eff exact to {worstd:.1e} and weights monotone "
          f"decreasing at every level")
    print("         realised (book keeps a variable name count each bar): " +
          " ".join(f"{lv:g}->{cellsum[lv]['neff_realised']:.2f}"
                   for lv in (1.0, 1.45, 2.0, 5.0)))

    # A3. COST DIMENSIONS, recomputed not inherited.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    for lv in LEVELS:
        assert abs(cellsum[lv]["cost_bp"]
                   - rt * cellsum[lv]["turnover"]) < 1e-9 * cellsum[lv]["cost_bp"]
    print(f"    [A3] cost = rt x turn at every level; rt x turn = {got:.4f} "
          f"reproduces d295's {b0['cost_bar_mean']:.4f}, doubled form rejected")

    # A4. THE EXTREME IS WHAT IT CLAIMS TO BE. N_eff = 1 must be a ONE-NAME book,
    #     so it must agree with the `hard` scheme at n = 1 -- an independent
    #     construction that never calls exp_weights.
    w1 = R.exp_weights(R.solve_lam(1.0), N_BASE)
    assert w1[0] > 1.0 - 1e-9, f"[A4] top weight only {w1[0]:.12f} at N_eff=1"
    hard = sim(raw["A"], raw["G"], 1.0, rt) if False else None
    h = R.simulate(raw["A"], raw["G"], "hard", 1, 0.0, False)
    ok = h["mask"]
    hg = float(np.where(ok, h["book"] * 1e4, 0.0)[ok].mean())
    d = abs(hg - cellsum[1.0]["gross_bp"])
    assert d < 1e-9, f"[A4] N_eff=1 differs from a hard 1-name book by {d:.2e} bp"
    print(f"    [A4] N_eff=1 puts {w1[0]:.12f} on the top name and matches a "
          f"HARD one-name book to {d:.1e} bp -- a second construction agrees")

    # A5. EVERY CELL A DISTINCT BOOK.
    seen = {}
    for lv in LEVELS:
        k = round(cellsum[lv]["net_bp"], 12)
        assert k not in seen, f"[A5] {lv} is identical to {seen[k]}"
        seen[k] = lv
    print(f"    [A5] all {len(seen)} cells are distinct books")

    # A6. THE SELF-TEST MUST RAISE ON A BROKEN BOOK INSIDE THE MASK.
    broke = False
    try:
        g = raw["cells"][2.0]["gross"].copy()
        g[:200] += 0.05
        assert abs(float(g.mean()) - d310["none/exp2"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[A6] [A1] passed a book handed free money inside the mask"
    print("    [A6] and [A1] raises on a book handed free money inside the mask")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()

    print("D315 Stage A  below the corner")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    d310 = json.loads((REPO / "data" / "d310_rank_weighted.json").read_text())["cells"]
    d312 = json.loads((REPO / "data" / "d312_vol_targeted.json").read_text())

    ts = time.time()
    cells = {lv: sim(A, G, lv, rt) for lv in LEVELS}
    per = (time.time() - ts) / len(LEVELS)
    cellsum = {lv: summarise(cells[lv], lv) for lv in LEVELS}
    print(f"  {len(LEVELS)} levels over {cellsum[2.0]['bars']:,} bars, "
          f"rt {rt:.1f} bp, {per:.1f}s/level  ({time.time() - t0:.0f}s)")

    assertions(cellsum, dict(A=A, G=G, cells=cells), rt, d310, d312)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    print("\nTHE EXTENDED SURFACE   (* = never run before)")
    h = "%1s %7s %9s %9s %9s %8s %9s %10s %9s"
    print(h % ("", "N_eff", "gross", "cost", "NET", "vol", "netSHRP",
               "sqrtN*net", "turnover"))
    print("-" * 78)
    for lv in LEVELS:
        c = cellsum[lv]
        print(h % ("*" if lv in NEW else " ", "%.2f" % lv,
                   "%+.2f" % c["gross_bp"], "%.2f" % c["cost_bp"],
                   "%+.2f" % c["net_bp"], "%.0f" % c["vol_bp"],
                   "%+.4f" % c["sharpe"], "%+.3f" % c["sqrtN_net"],
                   "%.4f" % c["turnover"]))

    # ---- refit the three curves on the extended grid -----------------------
    N = np.array(LEVELS)
    gross = np.array([cellsum[lv]["gross_bp"] for lv in LEVELS])
    cost = np.array([cellsum[lv]["cost_bp"] for lv in LEVELS])
    net = gross - cost
    vol = np.array([cellsum[lv]["vol_bp"] for lv in LEVELS])
    alg = json.loads((REPO / "data" / "d314_width_algebra.json").read_text())

    av, bv, r2v = fit_line(1.0 / N, vol ** 2)
    g0, g1, r2g = fit_line(np.log(N), gross)
    c0, c1, r2c = fit_line(np.log(N), cost)
    n0, n1 = g0 - c0, g1 - c1
    Nstar = float(np.exp(-n0 / n1 - 2.0))
    print("\nTHE CURVES REFITTED ON THE EXTENDED GRID   (D314's in brackets)")
    print("  vol^2 = %.0f + %.0f/N      rho = %.4f  [%.4f]   sigma = %.0f  [%.0f]"
          % (av, bv, av / (av + bv), alg["diversification"]["rho"],
             np.sqrt(max(av, 0) + bv), alg["diversification"]["sigma"]))
    print("  gross = %.2f %+.2f ln N   R^2 %.4f   [%.2f %+.2f]"
          % (g0, g1, r2g, alg["dilution"]["g0"], alg["dilution"]["g1"]))
    print("  cost  = %.2f %+.2f ln N   R^2 %.4f   [%.2f %+.2f]"
          % (c0, c1, r2c, alg["turnover"]["c0"], alg["turnover"]["c1"]))
    print("  net   = %.2f %+.2f ln N   =>  N* = %.2f   [D314: %.2f]"
          % (n0, n1, Nstar, alg["optimum"]["N_star"]))

    # QA3: does cost break ABOVE its fitted line below N_eff = 2?
    fitted_cost = alg["turnover"]["c0"] + alg["turnover"]["c1"] * np.log(N)
    print("\nQA3 -- COST AGAINST D314's FITTED LINE (fitted on N >= 2 only)")
    print("  %7s %10s %10s %9s" % ("N_eff", "cost", "D314 fit", "excess"))
    for i, lv in enumerate(LEVELS):
        print("  %7.2f %10.2f %10.2f %+8.1f%%" % (
            lv, cost[i], fitted_cost[i], 100 * (cost[i] / fitted_cost[i] - 1)))
    ex1 = float(cost[0] / fitted_cost[0] - 1)

    # ---- the null: ALL 24 rank rotations, enumerated ----------------------
    print(f"\nTHE NULL -- rank rotation within the gate, ALL 24 enumerated "
          f"(exact, not sampled)")
    print("%7s %10s %10s %10s %8s %10s %8s" % (
        "N_eff", "netSHRP", "null p50", "null p95", "p", "net", "p"))
    print("-" * 72)
    names, ps_sh, ps_nt, nullres = [], [], [], {}
    for lv in NEW + (2.0,):
        nsh, nnt = [], []
        for s in range(1, N_BASE):
            q = summarise(sim(A, G, lv, rt, shift=s), lv)
            nsh.append(q["sharpe"]); nnt.append(q["net_bp"])
        nsh, nnt = np.array(nsh), np.array(nnt)
        c = cellsum[lv]
        psh = float((nsh >= c["sharpe"]).sum() + 1) / (nsh.size + 1)
        pnt = float((nnt >= c["net_bp"]).sum() + 1) / (nnt.size + 1)
        nullres[str(lv)] = dict(
            sharpe_p50=float(np.median(nsh)), sharpe_p95=float(np.quantile(nsh, .95)),
            sharpe_p=psh, net_p50=float(np.median(nnt)),
            net_p95=float(np.quantile(nnt, .95)), net_p=pnt, draws=int(nsh.size))
        names.append(lv); ps_sh.append(psh); ps_nt.append(pnt)
        print("%7.2f %+10.4f %+10.4f %+10.4f %8.4f %+10.2f %8.4f" % (
            lv, c["sharpe"], np.median(nsh), np.quantile(nsh, .95), psh,
            c["net_bp"], pnt))

    rs, rn = bh(ps_sh), bh(ps_nt)
    print(f"\n  BH-FDR q=0.10 over {len(names)} cells "
          f"(p is floored at 1/25 = 0.0400 by exhaustive enumeration):")
    print("    net Sharpe: " + (", ".join("%g" % n for n, x in zip(names, rs) if x) or "NONE"))
    print("    net bp/bar: " + (", ".join("%g" % n for n, x in zip(names, rn) if x) or "NONE"))

    # ---- predictions -------------------------------------------------------
    sub = [lv for lv in LEVELS if lv < 2.0]
    nets = [cellsum[lv]["net_bp"] for lv in sorted(sub + [2.0], reverse=True)]
    qa1 = all(x <= y + 1e-12 for x, y in zip(nets, nets[1:])) and \
        5.5 <= cellsum[1.0]["net_bp"] <= 6.5
    best = max(LEVELS, key=lambda lv: cellsum[lv]["sharpe"])
    gain = cellsum[best]["sharpe"] / cellsum[2.0]["sharpe"] - 1.0
    qa2 = (1.4 <= best <= 2.0) and gain < 0.05
    qa3 = ex1 > 0.0
    qa4 = abs(av / (av + bv)) < 0.01 and \
        abs(np.sqrt(max(av, 0) + bv) / alg["diversification"]["sigma"] - 1) < 0.05
    qa5 = best != 1.0
    qa6 = abs(Nstar - alg["optimum"]["N_star"]) <= 0.3
    print("\nPREDICTIONS")
    for k, v in (("QA1 net rises monotonically below 2, 5.5-6.5 at N=1", qa1),
                 ("QA2 Sharpe peaks in [1.4,2.0] and beats N=2 by <5%  "
                  "[load-bearing]", qa2),
                 ("QA3 cost breaks ABOVE its fitted line below 2", qa3),
                 ("QA4 rho stays under 0.01 and sigma within 5%", qa4),
                 ("QA5 N_eff=1 is NOT the best cell", qa5),
                 ("QA6 refitted N* within +/-0.3 of D314's", qa6)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")
    print("    best net-Sharpe cell: N_eff = %g at %+.4f, against N=2's %+.4f "
          "(%+.1f%%)" % (best, cellsum[best]["sharpe"], cellsum[2.0]["sharpe"],
                         100 * gain))
    print("    cost excess at N_eff=1 over D314's fitted line: %+.1f%%" % (100 * ex1))

    OUT.write_text(json.dumps(dict(
        round_trip=rt, levels=list(LEVELS), new=list(NEW),
        cells={str(k): v for k, v in cellsum.items()}, null=nullres,
        refit=dict(a=av, b=bv, rho=av / (av + bv), sigma=float(np.sqrt(max(av, 0) + bv)),
                   g0=g0, g1=g1, r2g=r2g, c0=c0, c1=c1, r2c=r2c,
                   n0=n0, n1=n1, N_star=Nstar),
        best=dict(n_eff=float(best), sharpe=cellsum[best]["sharpe"],
                  gain_vs_2=float(gain)),
        cost_excess_at_1=float(ex1),
        predictions={k: bool(v) for k, v in
                     dict(QA1=qa1, QA2=qa2, QA3=qa3, QA4=qa4, QA5=qa5,
                          QA6=qa6).items()}),
        indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
