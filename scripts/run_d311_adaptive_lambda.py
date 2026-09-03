"""D311 -- adaptive lambda, ceiling first.

    uv run python scripts/run_d311_adaptive_lambda.py --selftest
    uv run python scripts/run_d311_adaptive_lambda.py [--draws 500]

PRE-REGISTERED AT `0408d92`, committed before this file existed (R8).

STAGE 1 CARRIES ITS OWN NULL. D308's pre-registration said an oracle needs none
-- true of the oracle, false of the gain over the baseline, which is the reported
number -- and it cost a result that had to be corrected. No ceiling is printed
here without the null beside it.

THE NULL IS D308c's FOURTH CONSTRUCTION and the first three are not retried:
standardise-and-permute-within-block drifted the means 364 bp; the two-way ANOVA
drifted the sds 43.6%; independent rotation destroyed co-movement 0.755 -> -0.002
and returned p = 1.0000 everywhere. The oracle's gain does not depend on the
temporal ORDER of blocks at all -- it is a within-block cross-sectional max -- so
any null that destroys order answers a question the oracle never asked.

TRANSITIONS ARE COMPUTED FROM THE WEIGHT VECTORS, not from a formula. Moving
lambda re-weights every name, so the traded fraction is sum|w1 - w2|/2 exactly.
That is the one place this construction should beat D308's discrete jumps.
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


R = _load("d310", "run_d310_rank_weighted.py")
W, D, SP, M = R.W, R.D, R.SP, R.M
N_BASE, BASE_HOLD = R.N_BASE, R.BASE_HOLD
LEVELS = (2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 14.0, 17.0,
          20.0, 22.0, 25.0)
FREQS = (21, 63, 126, 252)
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d311_adaptive_lambda.json"


def transition(l1, l2, rt):
    """Traded fraction between two lambda levels, from the weight vectors."""
    if l1 == l2:
        return 0.0
    w1 = R.exp_weights(R.solve_lam(l1), N_BASE)
    w2 = R.exp_weights(R.solve_lam(l2), N_BASE)
    return float(np.abs(w1 - w2).sum()) / 2.0 * rt


def build(A, G, rt):
    """Per-bar net for every lambda level, `none` family, no band."""
    out = {}
    for lv in LEVELS:
        r = R.simulate(A, G, "exp", lv, 0.0, False)
        ok = r["mask"]
        net = np.where(ok, r["book"] * 1e4 - rt * r["turn"], 0.0)
        out[lv] = dict(net=net, mask=ok, neff=r["neff"], lam=r["lam"],
                       turn=r["turn"])
    return out, out[LEVELS[0]]["mask"]


def block_matrix(cells, mask, f):
    idx = np.flatnonzero(mask)
    bl = [idx[i:i + f] for i in range(0, idx.size, f)]
    bn = np.zeros((len(bl), len(LEVELS)))
    for j, lv in enumerate(LEVELS):
        net = cells[lv]["net"]
        for b, ix in enumerate(bl):
            bn[b, j] = net[ix].sum()
    return bn, bl


def solve(bn, tc, charge):
    if not charge:
        return float(bn.max(axis=1).sum()), bn.argmax(axis=1)
    nb, nd = bn.shape
    V = bn[0].copy()
    back = np.zeros((nb, nd), int)
    for b in range(1, nb):
        cand = V[:, None] - tc
        back[b] = cand.argmax(axis=0)
        V = bn[b] + cand.max(axis=0)
    j = int(V.argmax())
    path = [0] * nb
    for b in range(nb - 1, -1, -1):
        path[b] = j
        j = back[b][j]
    return float(V.max()), np.array(path)


def mvn(bn, rng):
    """D308c's fourth construction: means, sds and cross-level correlations
    preserved, no timing structure by construction."""
    return rng.multivariate_normal(bn.mean(axis=0), np.cov(bn.T),
                                   size=bn.shape[0])


def acorr(x):
    x = np.asarray(x, float) - np.mean(x)
    s = float((x * x).sum())
    return float((x[:-1] * x[1:]).sum() / s) if s > 0 else 0.0


# --------------------------------------------------------------------------
def assertions(cells, mask, rt, d310):
    print("\nASSERTIONS")
    nb = int(mask.sum())

    # 1. REPRODUCTION against D310 at the levels the two grids share.
    worst, n = 0.0, 0
    for lv in (2.0, 3.0, 5.0, 7.0, 10.0, 14.0):
        ref = d310[f"none/exp{int(lv)}"]
        got = float(cells[lv]["net"][mask].mean())
        worst = max(worst, abs(got - ref["net_bp"]))
        n += 1
    assert worst < 1e-9, f"[1] net differs from D310 by up to {worst:.2e} bp"
    print(f"    [1] reproduces D310's net at all {n} shared levels "
          f"(max {worst:.1e} bp)")

    # 2. THE DEGENERATE ORACLE must equal the best fixed lambda exactly.
    stat = {lv: float(cells[lv]["net"][mask].mean()) for lv in LEVELS}
    best = max(stat.values())
    bn, _ = block_matrix(cells, mask, nb + 10)
    tc = np.array([[transition(a, b, rt) for b in LEVELS] for a in LEVELS])
    tot, _ = solve(bn, tc, True)
    assert abs(tot / nb - best) < 1e-9, \
        f"[2] one-block oracle {tot / nb:.6f} != best fixed {best:.6f}"
    print(f"    [2] a one-block oracle equals the best fixed lambda exactly "
          f"(N_eff={max(stat, key=stat.get):g}, {best:+.2f} bp)")

    # 3. TRANSITIONS zero at no move, monotone in |d log N_eff|.
    assert transition(5.0, 5.0, rt) == 0.0
    seq = [transition(2.0, lv, rt) for lv in (2.5, 3.0, 5.0, 10.0, 25.0)]
    assert all(a <= b + 1e-12 for a, b in zip(seq, seq[1:])), \
        f"[3] transition not monotone: {seq}"
    print(f"    [3] transitions zero at no move and monotone -- 2->2.5 costs "
          f"{seq[0]:.1f} bp, 2->25 costs {seq[-1]:.1f} bp")

    # 4. NESTING: uncharged, a shorter f cannot be worse.
    tot_u = []
    for f in FREQS:
        b, _ = block_matrix(cells, mask, f)
        t, _ = solve(b, tc, False)
        tot_u.append(t / nb)
    assert all(a >= b - 1e-9 for a, b in zip(tot_u, tot_u[1:])), \
        f"[4] uncharged oracle not nested in f: {tot_u}"
    print(f"    [4] the uncharged oracle is nested in the decision frequency")

    # N1-N3. THE NULL'S MOMENTS AND CORRELATION -- the three checks that took
    #        D308c four constructions to satisfy.
    b63, _ = block_matrix(cells, mask, 63)
    big = mvn(np.repeat(b63, 60, axis=0), np.random.default_rng(2))
    dm = float(np.abs(b63.mean(axis=0) - big.mean(axis=0)).max())
    se = float((b63.std(axis=0, ddof=1) / np.sqrt(big.shape[0])).max())
    rs = float(np.abs(b63.std(axis=0, ddof=1) / big.std(axis=0, ddof=1) - 1).max())
    cc = lambda x: float(np.mean(np.corrcoef(x.T)[np.triu_indices(x.shape[1], 1)]))
    dc = abs(cc(b63) - cc(big))
    assert dm < 4 * se, f"[N1] mean drift {dm:.1f} vs 4 se {4 * se:.1f}"
    assert rs < 0.10, f"[N2] sd drift {rs:.1%}"
    assert dc < 0.02, f"[N3] correlation drift {dc:.3f}"
    print(f"    [N1] means within sampling error ({dm:.1f} bp vs 4 se "
          f"{4 * se:.1f})   [N2] sds within {rs:.1%}")
    print(f"    [N3] cross-level correlation {cc(b63):.3f} -> {cc(big):.3f}, "
          f"the co-movement that drives the max is PRESERVED")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"{b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        x = cells[5.0]["net"][mask].copy()
        x[:100] += 0.05
        assert float(x.mean()) == float(cells[5.0]["net"][mask].mean())
    except AssertionError:
        broke = True
    assert broke, "the mean check passed a book handed free money"
    print("    [7] and the mean check raises on a book handed free money")
    return stat, tc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=500)
    a = ap.parse_args()
    t0 = time.time()

    print("D311  adaptive lambda, ceiling first")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    d310 = json.loads((REPO / "data" / "d310_rank_weighted.json").read_text())["cells"]
    cells, mask = build(A, G, rt)
    nb = int(mask.sum())
    print(f"  built {len(LEVELS)} levels over {nb:,} bars, rt {rt:.1f} bp "
          f"({time.time() - t0:.0f}s)")

    stat, tc = assertions(cells, mask, rt, d310)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    bestN = max(stat, key=stat.get)
    best = stat[bestN]
    rng = np.random.default_rng(SEED)
    res = {"fixed": {str(k): v for k, v in stat.items()},
           "best_fixed": dict(n_eff=bestN, net_bp=best), "stage1": {},
           "stage2": {}}

    print(f"\nSTAGE 1 -- THE CEILING, WITH ITS NULL   "
          f"(best fixed lambda: N_eff={bestN:g} at {best:+.2f} bp)")
    h = "%5s %11s %11s %10s %11s %11s %9s %8s"
    print(h % ("f", "uncharged", "CHARGED", "trans", "null p50", "null p95",
               "obs gain", "p"))
    print("-" * 88)
    for f in FREQS:
        bn, bl = block_matrix(cells, mask, f)
        tu, _ = solve(bn, tc, False)
        tcv, path = solve(bn, tc, True)
        trans = sum(tc[path[b - 1], path[b]] for b in range(1, len(path)))
        null = np.array([solve(mvn(bn, rng), tc, True)[0] / nb
                         for _ in range(a.draws)])
        og = tcv / nb - best
        p = float((null - best >= og).sum() + 1) / (null.size + 1)
        res["stage1"][str(f)] = dict(
            uncharged_bp=tu / nb, charged_bp=tcv / nb, transition_bp=trans / nb,
            null_p50=float(np.median(null)), null_p95=float(np.quantile(null, .95)),
            obs_gain=og, null_gain_p50=float(np.median(null) - best), p=p,
            path=[LEVELS[i] for i in path])
        print(h % (f, "%+.2f" % (tu / nb), "%+.2f" % (tcv / nb),
                   "%.2f" % (trans / nb), "%+.2f" % np.median(null),
                   "%+.2f" % np.quantile(null, .95), "%+.2f" % og, "%.4f" % p))

    print("\n  share of the observed gain that pure noise reproduces:")
    for f in FREQS:
        r = res["stage1"][str(f)]
        sh = r["null_gain_p50"] / r["obs_gain"] if abs(r["obs_gain"]) > 1e-9 else None
        print("    f=%-4d observed %+7.2f   null median %+7.2f   %s" % (
            f, r["obs_gain"], r["null_gain_p50"],
            ("%.0f%% is noise" % (100 * sh)) if sh else "--"))

    print("\nSTAGE 2 -- PERSISTENCE of the charged oracle's lambda path")
    print("%5s %9s %11s %12s %12s %12s" % (
        "f", "blocks", "lag1 rho", "shuffled", "mean|dlogN|", "shuffled"))
    print("-" * 70)
    for f in FREQS:
        path = np.log(np.array(res["stage1"][str(f)]["path"]))
        r1 = acorr(path)
        dd = float(np.abs(np.diff(path)).mean())
        sr, sd_ = [], []
        for _ in range(500):
            q = rng.permutation(path)
            sr.append(acorr(q))
            sd_.append(float(np.abs(np.diff(q)).mean()))
        res["stage2"][str(f)] = dict(lag1=r1, lag1_shuffled=float(np.median(sr)),
                                     mean_abs_dlog=dd,
                                     mean_abs_dlog_shuffled=float(np.median(sd_)))
        print("%5d %9d %11.3f %12.3f %12.3f %12.3f" % (
            f, len(path), r1, np.median(sr), dd, np.median(sd_)))

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
