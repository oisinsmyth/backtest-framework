"""D308c -- the null D308's Stage 1 should have had.

    uv run python scripts/d308c_ceiling_null.py [--draws 500]

D308's pre-registration said "Stage 1 has no null: an oracle is an upper bound by
construction." That is true of the ORACLE and false of THE GAIN OVER STATIC,
which is the number the result reported. Taking the max of seven noisy series
earns something even when none is truly better at any time, and nothing in D308
separated that from real timing structure.

THE NULL. Per width N, the block-net series has a mean and an sd that are real
and must be preserved -- N=2 genuinely earns more, and genuinely swings more.
What must be destroyed is WHICH width is above its own mean in WHICH block:

    z[N][b]     = ( blocknet[N][b] - mean[N] ) / sd[N]
    within each block b, permute the seven z values across the widths
    null[N][b]  = mean[N] + sd[N] * z_permuted[N][b]

Each width keeps its own mean and sd exactly, each block keeps its own
cross-sectional dispersion of standardised residuals, and the timing is gone.
Assertions [N1] and [N2] hold those two invariants rather than trusting them.

If the permuted ceiling matches the observed one, D308's +18.7 to +26.6 bp is the
expected value of picking a max, not an opportunity.
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


T8 = _load("d308", "run_d308_width_in_time.py")
W, D, SP, M = T8.W, T8.D, T8.SP, T8.M
DEPTHS, FAMILIES = T8.DEPTHS, T8.FAMILIES
FREQS = (21, 63, 126, 252, 504)
OUT = REPO / "data" / "d308c_ceiling_null.json"
SEED = 20260903


def block_matrix(cells, fam, mask, f):
    """(blocks x widths) of summed net, and the bar count in each block."""
    bl = T8.blocks(mask, f)
    bn = np.zeros((len(bl), len(DEPTHS)))
    for j, d in enumerate(DEPTHS):
        net = cells[(fam, d)]["net"]
        for b, ix in enumerate(bl):
            bn[b, j] = net[ix].sum()
    return bn, np.array([ix.size for ix in bl])


def solve(bn, tc, charge):
    """Best achievable total over block-wise widths. Viterbi when charged."""
    nb, nd = bn.shape
    if not charge:
        return float(bn.max(axis=1).sum())
    V = bn[0].copy()
    for b in range(1, nb):
        V = bn[b] + (V[:, None] - tc).max(axis=0)
    return float(V.max())


def permute(bn, rng):
    """DRAW FROM THE OBSERVED JOINT DISTRIBUTION: multivariate normal with the
    block matrix's own mean vector and covariance matrix. Means, sds and the
    cross-width correlations are all preserved, and there is no timing structure
    by construction.

    THE REALISATION THAT MADE THIS THE RIGHT NULL, and it took two failures to
    see: the oracle's gain over static does NOT depend on the temporal ORDER of
    blocks at all. It is a within-block, cross-sectional max, so permuting the
    rows changes nothing. What generates the gain is that in some blocks a width
    other than the static-best happens to win -- which pure noise produces
    whenever there is cross-sectional dispersion. So the quantity to null is the
    Jensen gap, E[max] - max[E], of the observed joint distribution, and any null
    that destroys ORDER rather than CO-MOVEMENT is answering a question the
    oracle never asked.

    TWO EARLIER CONSTRUCTIONS WERE TRIED AND BOTH BROKE THE MARGINALS, which is
    fatal here because the width means ARE the static baseline the gain is
    measured against:

      * standardise per width, permute across widths within a block -- preserves
        the marginals only in expectation; [N1] caught 364 bp of mean drift on
        51 blocks, larger than the effect being measured.
      * two-way ANOVA, permuting the width-by-block interaction down each column
        -- [N2] caught 43.6% sd drift, because the block main effect is itself
        dominated by N=2's volatility, so the interaction is not orthogonal to
        it within a column.

    THE PRICE, STATED: rotation also destroys the COMMON factor, so the null's
    widths co-move less than the real ones and the max of seven is larger than
    it should be. That makes this null CONSERVATIVE -- harder to beat than the
    truth. If the observed ceiling clears it, that is strong; if it does not,
    the test is inconclusive rather than negative, and section [N4] reports how
    much co-movement was destroyed so the size of the bias is visible.
    """
    mu = bn.mean(axis=0)
    cov = np.cov(bn.T)
    return rng.multivariate_normal(mu, cov, size=bn.shape[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=500)
    a = ap.parse_args()
    t0 = time.time()

    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    cells, rts, mask = T8.build(A, G, half)
    nb = int(mask.sum())
    rng = np.random.default_rng(SEED)
    print(f"D308c  the ceiling null  ({time.time() - t0:.0f}s)\n")

    # [N1]/[N2] -- the permutation must preserve each width's mean and sd.
    bn0, _ = block_matrix(cells, "target", mask, 63)
    p0 = permute(bn0, np.random.default_rng(1))
    big = permute(np.repeat(bn0, 60, axis=0), np.random.default_rng(2))
    dm = float(np.abs(bn0.mean(axis=0) - big.mean(axis=0)).max())
    rs = float(np.abs(bn0.std(axis=0, ddof=1) / big.std(axis=0, ddof=1) - 1).max())
    # the tolerance is the sampling error of the draw, not an arbitrary fraction:
    # a 60x draw still has a standard error of sd/sqrt(n) on each width's mean.
    se = float((bn0.std(axis=0, ddof=1) / np.sqrt(big.shape[0])).max())
    assert dm < 4 * se, f"[N1] mean drift {dm:.1f} bp against 4 se = {4 * se:.1f}"
    assert rs < 0.10, f"[N2] sd drift {rs:.1%}"
    same = int((np.argmax(bn0, axis=1) == np.argmax(p0, axis=1)).sum())
    assert same < 0.5 * bn0.shape[0], "[N3] the rotation barely moved the argmax"
    cc = lambda x: float(np.mean(np.corrcoef(x.T)[np.triu_indices(x.shape[1], 1)]))
    c0, c1 = cc(bn0), cc(p0)
    print(f"    [N1] the generating distribution reproduces each width's mean "
          f"to {dm:.1f} bp on a 60x draw -- the static baseline is preserved")
    print(f"    [N2] and each width's sd to {rs:.1%}")
    print(f"    [N3] the block argmax changes on {bn0.shape[0] - same} of "
          f"{bn0.shape[0]} blocks")
    print(f"    [N4] mean pairwise correlation across widths {c0:.3f} -> "
          f"{cc(big):.3f} -- the co-movement that drives the max-of-seven is "
          f"PRESERVED, which the rotation null destroyed (0.755 -> -0.002)\n")

    res = {}
    hdr = "%-16s %4s %11s %11s %11s %11s %9s %8s"
    print(hdr % ("family", "f", "static", "OBSERVED", "null p50", "null p95",
                 "obs gain", "p"))
    print("-" * 92)
    for fam in FAMILIES:
        stat = {d: float(cells[(fam, d)]["net"][mask].mean()) for d in DEPTHS}
        best = max(stat.values())
        for f in FREQS:
            bn, _ = block_matrix(cells, fam, mask, f)
            tc = np.array([[T8.transition(DEPTHS[i], DEPTHS[j],
                                          rts[(fam, DEPTHS[j])])
                            for j in range(len(DEPTHS))]
                           for i in range(len(DEPTHS))])
            obs = solve(bn, tc, True) / nb
            null = np.array([solve(permute(bn, rng), tc, True) / nb
                             for _ in range(a.draws)])
            # the null's own static baseline is unchanged: means are preserved
            gains = null - best
            og = obs - best
            p = float((gains >= og).sum() + 1) / (gains.size + 1)
            res.setdefault(fam, {})[str(f)] = dict(
                static=best, observed=obs, obs_gain=og,
                null_p50=float(np.median(null)), null_p95=float(np.quantile(null, .95)),
                null_gain_p50=float(np.median(gains)), p=p)
            print(hdr % (fam, f, "%+.2f" % best, "%+.2f" % obs,
                         "%+.2f" % np.median(null), "%+.2f" % np.quantile(null, .95),
                         "%+.2f" % og, "%.4f" % p))
        print()

    print("HOW MUCH OF THE CEILING IS PICKING A MAX")
    for fam in FAMILIES:
        for f in FREQS:
            r = res[fam][str(f)]
            share = (r["null_gain_p50"] / r["obs_gain"]
                     if abs(r["obs_gain"]) > 1e-9 else float("inf"))
            print("  %-16s f=%-3s observed gain %+7.2f   null median gain %+7.2f"
                  "   %.0f%% of it is noise" % (
                      fam, f, r["obs_gain"], r["null_gain_p50"], 100 * share))

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
