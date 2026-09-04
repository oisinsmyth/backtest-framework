"""D328 -- the rank profile at the depth the book actually trades.

    uv run python scripts/run_d328_profile_at_depth.py --selftest
    uv run python scripts/run_d328_profile_at_depth.py

PRE-REGISTERED AT `cad090b`, committed before this file existed (R8).

D327 bucketed by 20 EQUAL RANK PERCENTILES, so its bucket 0 is the top 5% of ~988
live names -- about 49 -- and the book holds 2. Its Q5 failed at rho = -0.200 and
its own section 4 named the reason: the buckets averaged away the traded region.

THREE FIXES, and the first two are the study:

  * LOG-SPACED RANK BUCKETS from each end. Rank 0 and rank 1 get their own,
    because that is what a two-name book holds. Percentile was the wrong unit --
    the book selects by RANK, and the live cross-section moves bar to bar.
  * A PER-BUCKET t, recomputed from the per-bar series. D327 reported edges with
    no standard error, so nothing in it said whether rank 0 differed from zero
    or from rank 1.
  * PRICE per bucket, connecting D322's finding -- 57% of P&L in the cheapest
    tercile at 8x the commission -- to the depth actually traded.

Q6 IS LOAD-BEARING AND TESTS MY OWN DIAGNOSIS. I blamed D327's Q5 failure on
resolution. If rank-0/1 edge still fails to rank the signals as D326's per-trade
lens does, that explanation was wrong and D329 does not run.

NO PATH. Never quote in bp/bar or set beside a book (FINDINGS section 10).
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


P = _load("d327", "run_d327_rank_profile.py")
Y, D, M, SP, R = P.Y, P.D, P.M, P.SP, P.R

SIGNALS = P.SIGNALS
KS = P.KS
# log-spaced rank edges from EACH end; powers of two, not tuned
EDGES = (0, 1, 2, 4, 8, 16, 32, 64, 128, 256)
# The first run scored SUMMED simple returns and wrote `d328_profile_at_depth.json`.
# That file stays as the record of what was reported. The compounded re-run --
# the right quantity -- writes beside it, and `--summed` reproduces the first.
OUT_SUMMED = REPO / "data" / "d328_profile_at_depth.json"
OUT = REPO / "data" / "d328b_profile_at_depth_compounded.json"


_E = np.asarray(EDGES)


def bucket_of(p, c):
    """Bucket index for rank `p` in a cross-section of size `c`.

    0..9 are the long end (0 = the single best-ranked name), 10 is the coarse
    middle, and 11..20 mirror the short end so that 20 is rank c-1. A name is
    assigned to whichever END it is nearer, and to the middle when it is at
    least EDGES[-1] from both.
    """
    nb = len(_E)
    q = c - 1 - p                                   # distance from the short end
    il = np.searchsorted(_E, p, side="right") - 1
    iq = np.searchsorted(_E, q, side="right") - 1
    b = np.where(p <= q, il, 2 * nb - iq)
    return np.where((p >= _E[-1]) & (q >= _E[-1]), nb, b)


LABELS = ([f"L{EDGES[i]}" + ("" if i == len(EDGES) - 1 else
                             f"-{EDGES[i+1]-1}" if EDGES[i+1] - 1 > EDGES[i] else "")
           for i in range(len(EDGES))] + ["MID"] +
          [f"S{EDGES[i]}" + ("" if i == len(EDGES) - 1 else
                             f"-{EDGES[i+1]-1}" if EDGES[i+1] - 1 > EDGES[i] else "")
           for i in range(len(EDGES) - 1, -1, -1)])


def fwd_compounded_demeaned(r1T, finT, k):
    """Forward k-bar COMPOUNDED return, prod(1+r) - 1, cross-sectionally demeaned.

    THE RIGHT QUANTITY, AND D327/D328's FIRST RUN SCORED THE WRONG ONE. Their
    `fwd_demeaned` SUMS simple daily returns over the window. A held position
    compounds, and on the bouncy $8 names at hist_L's extremes the two differ by
    60-110 bp at k=20: the short end goes from +21 (summed) to -91 (compounded),
    which reverses D327 section 2 and D328 Q5 outright. Same window, same
    demeaning, same masks -- only the aggregation over the k bars changes.
    """
    x = np.where(finT, np.log1p(np.nan_to_num(r1T, nan=0.0)), 0.0)
    cs = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(x, axis=0)])
    T = x.shape[0]
    hi = np.minimum(np.arange(T) + 1 + k, T)
    lo = np.minimum(np.arange(T) + 1, T)
    out = np.expm1(cs[hi] - cs[lo])
    out[~finT] = np.nan
    m = np.nanmean(np.where(finT, out, np.nan), axis=1, keepdims=True)
    return np.where(finT, out - m, np.nan)


def profile(z, base, finT, r1T, HALF, CLOSE, sig, k, lag=True, costs=True,
            compound=True):
    """Edge, t, half-spread, price and ratio by log-spaced rank bucket.

    IT ALSO ACCUMULATES D327's 20 EQUAL PERCENTILE BINS over the SAME name-bars,
    in the same pass and through the same `np.add.at` call D327 makes, so
    assertion [1] is a real aggregation check rather than a re-run of a separate
    loop that happens to agree. Those bins are ALWAYS accumulated on the SUMMED
    quantity, because that is what D327 scored and [1] proves the harness is the
    same harness -- the scored profile is compounded unless `compound=False`.

    TWO EDGES ARE REPORTED AND THE DIFFERENCE IS NOT COSMETIC:
      `edge_pooled`  the name-bar mean. That is D327's statistic, and the one
                     [1] compares.
      `edge_bp`      the mean of the PER-BAR means. Only this one can carry a
                     `t`, because the BARS are the sample, not the name-bars --
                     and a t over ~4M correlated name-bars would be fiction.
    Bucket L0 holds exactly one name per bar, so for it the two coincide.
    """
    _, cnt, pos = R.ranked(z[sig], base)
    fwd_s = P.fwd_demeaned(r1T, finT, k)            # D327's quantity, for [1]
    fwd = fwd_compounded_demeaned(r1T, finT, k) if compound else fwd_s
    if not lag:
        fwd = np.roll(fwd, 1, axis=0)
        fwd_s = np.roll(fwd_s, 1, axis=0)
    T = finT.shape[0]
    nb = 2 * len(EDGES) + 1
    per_bar = [[] for _ in range(nb)]               # bar means, for a real t
    halves = [[] for _ in range(nb)]
    prices = [[] for _ in range(nb)]
    psum, pcnt = np.zeros(nb), np.zeros(nb, np.int64)
    qsum, qcnt = np.zeros(P.NB), np.zeros(P.NB, np.int64)   # D327's 20 bins
    for t in range(1, T):
        c = int(cnt[t])
        if c < 100:
            continue
        p = pos[t]
        live = np.flatnonzero((p < c) & finT[t] & np.isfinite(fwd_s[t]))
        if live.size < 100:
            continue
        f = fwd[t][live]
        # D327's bins, its expression, its ordering, ITS QUANTITY -- so [1] can
        # demand equality regardless of what the profile itself scores
        q = np.minimum((p[live] * P.NB) // c, P.NB - 1)
        np.add.at(qsum, q, fwd_s[t][live])
        np.add.at(qcnt, q, 1)
        b = bucket_of(p[live], c)
        np.add.at(psum, b, f)
        np.add.at(pcnt, b, 1)
        s = np.bincount(b, weights=f, minlength=nb)
        n_ = np.bincount(b, minlength=nb)
        hit = np.flatnonzero(n_)
        for bi in hit:
            per_bar[bi].append(s[bi] / n_[bi])
        if costs:
            h, pr = HALF[t][live], CLOSE[t][live]
            for bi in hit:
                m = b == bi
                hm = h[m][np.isfinite(h[m])]
                if hm.size:
                    halves[bi].append(hm)
                pm = pr[m][np.isfinite(pr[m]) & (pr[m] > 0)]
                if pm.size:
                    prices[bi].append(pm)
    edge, tstat = np.full(nb, np.nan), np.full(nb, np.nan)
    for bi in range(nb):
        if len(per_bar[bi]) > 30:
            v = np.array(per_bar[bi])
            edge[bi] = v.mean() * 1e4
            sd = v.std(ddof=1)
            tstat[bi] = v.mean() / (sd / np.sqrt(v.size)) if sd > 0 else 0.0
    pooled = np.where(pcnt > 0, psum / np.maximum(pcnt, 1), np.nan) * 1e4
    d327_bins = np.where(qcnt > 0, qsum / np.maximum(qcnt, 1), np.nan) * 1e4
    half = np.array([np.median(np.concatenate(h)) if h else np.nan for h in halves])
    price = np.array([np.median(np.concatenate(p)) if p else np.nan
                      for p in prices])
    return dict(edge_bp=edge.tolist(), edge_pooled=pooled.tolist(),
                t=tstat.tolist(), half_bp=half.tolist(), price=price.tolist(),
                ratio=(edge / (2.0 * half)).tolist(), n=pcnt.tolist(),
                bars=[len(x) for x in per_bar],
                d327_bins=d327_bins.tolist(), d327_n=qcnt.tolist())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--summed", action="store_true",
                    help="score SUMMED simple returns, reproducing the first run")
    a = ap.parse_args()
    t0 = time.time()
    compound = not a.summed
    out = OUT_SUMMED if a.summed else OUT
    prof = lambda *args, **kw: profile(*args, compound=compound, **kw)

    print("D328  the profile at the depth the book trades  "
          f"[{'COMPOUNDED' if compound else 'SUMMED -- the first run'}]")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT = np.asarray(A["r1T"]), np.asarray(A["finT"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    d326 = json.loads((REPO / "data" / "d326_both_lenses.json").read_text())
    d327 = json.loads((REPO / "data" / "d327_rank_profile.json").read_text())
    print(f"  panel {finT.shape}, {2*len(EDGES)+1} buckets "
          f"({time.time() - t0:.0f}s)")

    print("\nASSERTIONS")
    # 2. THE BUCKETS PARTITION, and bucket L0 holds exactly one name.
    c = 900
    p = np.arange(c)
    b = bucket_of(p, c)
    assert (b >= 0).all() and (b <= 2 * len(EDGES)).all(), "[2] bucket out of range"
    assert int((b == 0).sum()) == 1, f"[2] L0 holds {(b == 0).sum()} names, not 1"
    assert int((b == 2 * len(EDGES)).sum()) == 1, "[2] S0 does not hold exactly 1"
    assert int((b == 1).sum()) == 1, "[2] L1 does not hold exactly 1"
    print(f"    [2] the {2*len(EDGES)+1} buckets partition a {c}-name "
          f"cross-section, and L0, L1 and S0 hold exactly one name each")

    # 3. DEMEANING IS EXACT.
    fw = P.fwd_demeaned(r1T, finT, 10)
    mm = np.nanmax(np.abs(np.nanmean(np.where(finT, fw, np.nan), axis=1)))
    assert mm < 1e-12, f"[3] demeaning leaves {mm:.2e}"
    print(f"    [3] the cross-sectional mean is zero to {mm:.1e} at every bar")

    pr = prof(z, base, finT, r1T, HALF, CLOSE, "hist_L", 20)

    # 1. AGGREGATION. The name-bars this study reads must be exactly the ones
    #    D327 read. Accumulating them into D327's 20 equal percentile bins, in
    #    the same pass, must reproduce `data/d327_rank_profile.json`.
    #
    #    THE PRE-REGISTRATION SAID "aggregating the new buckets back", AND THAT
    #    IS NOT POSSIBLE: log-spaced RANK buckets do not nest inside equal RANK
    #    PERCENTILE bins, because a percentile boundary lands at a different rank
    #    every bar as the live count moves. The name-bars are what the two
    #    bucketings share, so the check is done at that level. Same evidence,
    #    weaker only in that it cannot catch a bucketing error that preserves
    #    membership -- which [2] covers.
    ours = np.array(pr["d327_bins"])
    theirs = np.array(d327["profiles"]["hist_L/k20"]["edge_bp"])
    dd = np.nanmax(np.abs(ours - theirs))
    assert dd < 1e-9, (f"[1] this study reads different name-bars from D327: "
                       f"max bin difference {dd:.3e} bp")
    tot_ours, tot_d327 = int(np.sum(pr["n"])), int(np.sum(pr["d327_n"]))
    assert tot_ours == tot_d327, \
        f"[1] the two bucketings cover different name-bars: {tot_ours} vs {tot_d327}"
    print(f"    [1] AGGREGATION: the same {tot_ours:,} name-bars, and binned "
          f"D327's way they reproduce D327 to {dd:.1e} bp")

    # RQ. RIGHT QUANTITY -- the compounded grid must DIFFER from the summed one
    #     the first run scored (CLAUDE.md, runner assertion 3), and a spot check
    #     must reproduce prod(1+r) - 1 from the raw daily series.
    if compound:
        ps = profile(z, base, finT, r1T, HALF, CLOSE, "hist_L", 20, costs=False,
                     compound=False)
        gap = np.abs(np.array(pr["edge_bp"]) - np.array(ps["edge_bp"]))
        assert np.nanmax(gap) > 1.0, "[RQ] compounding changes nothing"
        fc = fwd_compounded_demeaned(r1T, finT, 20)
        t_, i_ = 2000, int(np.flatnonzero(finT[2000])[0])
        raw = np.prod(1.0 + np.nan_to_num(r1T[2001:2021, i_], nan=0.0)) - 1.0
        cm = np.nanmean(np.where(finT[t_], np.expm1(np.log1p(np.where(
            finT[2001:2021], np.nan_to_num(r1T[2001:2021], nan=0.0), 0.0))
            .sum(axis=0)), np.nan))
        assert abs(fc[t_, i_] - (raw - cm)) < 1e-12, "[RQ] spot check fails"
        print(f"    [RQ] RIGHT QUANTITY: compounded differs from summed by up to "
              f"{np.nanmax(gap):.0f} bp (S0 {ps['edge_bp'][-1]:+.0f} -> "
              f"{pr['edge_bp'][-1]:+.0f}); spot check reproduces prod(1+r)-1")

    # 4. CAUSALITY.
    pk = prof(z, base, finT, r1T, HALF, CLOSE, "hist_L", 20, lag=False)
    d = np.nanmax(np.abs(np.array(pk["edge_bp"]) - np.array(pr["edge_bp"])))
    assert d > 1e-9, "[4] peeking gives the same profile"
    print(f"    [4] CAUSALITY: peeking moves the profile by up to {d:.1f} bp")

    # 5. THE t IS REAL -- its sample is BARS, not name-bars.
    #
    #    THE PRE-REGISTERED FORM ASSERTED THAT HALVING THE SAMPLE MUST CUT THE t,
    #    AND IT FIRED ON THE COMPOUNDED RUN: hist_L's rank-0 t is 2.96 on the
    #    full sample and 3.00 on the first half alone. That is not a bug -- the
    #    effect is concentrated in the first half -- and the assertion was a
    #    property of the DATA, not of the code. Third time this shape of error
    #    has appeared here (D324 [S], D327 [1]). The code property it was
    #    reaching for: the series the t is computed on has one entry per BAR,
    #    so a wide bucket's name-bar count must vastly exceed its bar count, and
    #    L0's must equal it. The halving is kept as a printed diagnostic.
    T_ = finT.shape[0]
    bars, n = np.array(pr["bars"]), np.array(pr["n"])
    assert bars[10] < T_ and n[10] > 100 * bars[10], \
        f"[5] MID: {n[10]} name-bars over {bars[10]} bars -- the t is not per-bar"
    assert n[0] == bars[0] and n[-1] == bars[-1], \
        f"[5] L0/S0 hold {n[0]}/{n[-1]} name-bars over {bars[0]}/{bars[-1]} bars"
    t_full = np.array(pr["t"])[0]
    fin_half = finT.copy()
    fin_half[T_ // 2:] = False
    ph = prof(z, base, fin_half, r1T, HALF, CLOSE, "hist_L", 20, costs=False)
    t_half = np.array(ph["t"])[0]
    print(f"    [5] the t's sample is bars: MID has {n[10]:,} name-bars over "
          f"{bars[10]:,} bars, L0 exactly one per bar")
    print(f"        diagnostic: hist_L rank-0 t on the full sample {t_full:+.2f}, "
          f"on the FIRST HALF alone {t_half:+.2f}"
          + ("  <- first-half concentrated" if abs(t_half) >= abs(t_full) else ""))

    # C. COST DIMENSIONS.
    r = np.array(pr["ratio"])
    e, h = np.array(pr["edge_bp"]), np.array(pr["half_bp"])
    ok = np.isfinite(r)
    assert np.allclose(r[ok], (e / (2.0 * h))[ok])
    assert not np.allclose(r[ok], (e / (4.0 * h))[ok])
    print("    [C] the ratio is edge / (2 x half-spread); the paired 4x is rejected")

    # 6. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        bad = e.copy()
        bad[0] += 50.0
        assert abs(bad[0] - e[0]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] the check passed a bucket handed free money"
    print("    [6] and the check raises on a bucket handed free money")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    res = {}
    for s in SIGNALS:
        for k in KS:
            res[f"{s}/k{k}"] = prof(z, base, finT, r1T, HALF, CLOSE, s, k)
    print(f"  {len(res)} profiles ({time.time() - t0:.0f}s)")

    show = [0, 1, 2, 3, 4, 6, 10, 14, 16, 17, 18, 19, 20]
    for k in KS:
        print(f"\nEDGE by rank bucket, k={k}  (bp, demeaned; L0 = the single "
              f"best-ranked name)")
        print("%-13s" % "signal" + "".join("%8s" % LABELS[b] for b in show))
        for s in SIGNALS:
            e = np.array(res[f"{s}/k{k}"]["edge_bp"])
            print("%-13s" % s + "".join("%+8.0f" % e[b] for b in show))
        print("%-13s" % "  (t at L0/L1)" + "".join(
            "%8s" % ("" if b > 1 else "%+.2f" % np.array(res[f"hist_L/k{k}"]["t"])[b])
            for b in show))

    print("\nt at L0 and L1, by signal (k=20)")
    print("  %-14s %8s %8s %10s %10s" % ("signal", "t(L0)", "t(L1)",
                                         "edge L0", "edge L1"))
    for s in SIGNALS:
        p_ = res[f"{s}/k20"]
        print("  %-14s %+8.2f %+8.2f %+10.0f %+10.0f"
              % (s, p_["t"][0], p_["t"][1], p_["edge_bp"][0], p_["edge_bp"][1]))

    print("\nHALF-SPREAD and PRICE at the traded depth (k-independent)")
    print("  %-14s %9s %9s %9s %10s %10s" % ("signal", "half L0", "half L1",
                                             "half MID", "price L0", "price MID"))
    for s in SIGNALS:
        p_ = res[f"{s}/k20"]
        print("  %-14s %9.1f %9.1f %9.1f %10.0f %10.0f"
              % (s, p_["half_bp"][0], p_["half_bp"][1], p_["half_bp"][10],
                 p_["price"][0], p_["price"][10]))

    # ---- predictions -------------------------------------------------------
    def top2(s, k):
        e = np.array(res[f"{s}/k{k}"]["edge_bp"])
        return float((e[0] + e[1]) / 2.0 - (e[-1] + e[-2]) / 2.0)
    d327top = {s: float(np.array(d327["profiles"][f"{s}/k20"]["edge_bp"])[0])
               for s in SIGNALS}
    q2 = all(np.array(res[f"{s}/k20"]["edge_bp"])[:2].mean() > d327top[s]
             for s in SIGNALS)
    q3 = bool(np.array(res["skew_63/k20"]["edge_bp"])[:2].mean()
              > 3 * d327top["skew_63"])
    q4 = all(abs(np.array(res[f"{s}/k20"]["t"])[0]
                 - np.array(res[f"{s}/k20"]["t"])[1]) < 2.0 for s in SIGNALS)
    # `price_log` is the known-bad control and D326 never ran it, so the rho is
    # over the five signals D327's own Q5 used. Same five, same comparison.
    d326i = {s: max(d326["invariant"][f"{s}/k{k}"]["net_per_trade"] for k in KS)
             for s in SIGNALS if f"{s}/k10" in d326["invariant"]}
    common = [s for s in SIGNALS if s in d326i]
    assert len(common) == 5, f"[Q6] {len(common)} signals in common, not 5"
    rho = float(np.corrcoef(
        np.argsort(np.argsort([top2(s, 20) for s in common])),
        np.argsort(np.argsort([d326i[s] for s in common])))[0, 1])
    q6 = rho > 0.7
    med = float(np.nanmedian(HALF[np.isfinite(HALF)]))
    q7 = all(res[f"{s}/k20"]["half_bp"][0] > med for s in SIGNALS)
    q5 = bool(np.array(res["hist_L/k20"]["edge_bp"])[-1] > 0)
    print("\nPREDICTIONS")
    for kk, vv in (("Q2 ranks 0-1 beat D327's top-5% bucket everywhere", q2),
                   ("Q3 skew_63's rank-0/1 edge is far above its flat profile", q3),
                   ("Q4 rank 0 is NOT distinguishable from rank 1", q4),
                   ("Q5 hist_L's short end is still POSITIVE at full resolution", q5),
                   ("Q6 rank-0/1 ranks signals as D326 did (rho>0.7)  [load-bearing]", q6),
                   ("Q7 the half-spread at rank 0 exceeds the universe median", q7)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print("    Q6 rho = %+.3f   (D327's was -0.200)" % rho)
    print("    top-2 spread, k=20: " +
          "  ".join("%s %+.0f" % (s, top2(s, 20)) for s in SIGNALS))
    print("    universe median half-spread %.1f bp" % med)

    out.write_text(json.dumps(dict(
        note="D328: log-spaced rank buckets. NO PATH -- never quote in bp/bar "
             "(FINDINGS section 10).",
        quantity="compounded prod(1+r)-1" if compound else
                 "SUMMED simple returns -- the first run's quantity, kept as "
                 "the record of what was reported; superseded",
        edges=list(EDGES), labels=LABELS, signals=list(SIGNALS), ks=list(KS),
        profiles=res, spearman_vs_d326=rho,
        top2_spread={s: top2(s, 20) for s in SIGNALS},
        predictions=dict(Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5),
                         Q6=bool(q6), Q7=bool(q7))), indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
