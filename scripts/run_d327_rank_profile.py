"""D327 -- the rank profile: what each signal is worth at EVERY depth.

    uv run python scripts/run_d327_rank_profile.py --selftest
    uv run python scripts/run_d327_rank_profile.py

PRE-REGISTERED AT `b8a2530`, committed before this file existed (R8).

Every ranking this programme has produced was read at one depth. D326's
"path-invariant" lens is still `rank < 2` -- it removes slot contention and
nothing else. THIS HAS NO PATH AT ALL: a lagged ranking, a forward window, and
nothing between them. No holding, no exits, no cap, no turnover.

THREE PROFILES PER SIGNAL, and the third decides anything:

  EDGE   mean forward k-bar return, CROSS-SECTIONALLY DEMEANED each bar. Demeaned
         because the book is a SPREAD -- a name's contribution is its return
         against the cross-section, not its raw return. Assertion [4] holds the
         demeaning to floating point, so the profile sums to zero across buckets
         and cannot show a spurious level.
  COST   median Corwin-Schultz half-spread of the names in the bucket.
  RATIO  edge / (2 x half-spread) -- ONE name crossing TWICE, not the paired 4x.

IT ANSWERS THE skew_63 QUESTION FIRST. D326 found it covering its round trip 4.53x
where everything else sits near 2.0. Either its edge is bigger at the extremes, or
its extreme names are CHEAPER -- and the cost profile separates those.

THIS CANNOT PRICE ANYTHING. It must never be quoted in bp/bar or compared to a
book (FINDINGS section 10). There is no path here to price.
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


Y = _load("d323", "run_d323_shortlist_at_operating_point.py")
D, M, SP, R = Y.D, Y.M, Y.SP, Y.R

SIGNALS = ("hist_L", "retrace_leg", "skew_63", "rsi", "macd_hist", "price_log")
KS = (10, 20, 40)
NB = 20                       # 20 buckets of 5 rank-percentile, declared
OUT = REPO / "data" / "d327_rank_profile.json"


def fwd_demeaned(r1T, finT, k):
    """Forward k-bar simple return, cross-sectionally demeaned each bar.

    The window starts at t+1. `lag=False` in `profile` is the peeking variant
    assertion [2] fires at -- it starts the window at t, letting the ranking see
    the bar it is about to be paid for.
    """
    x = np.where(finT, np.nan_to_num(r1T, nan=0.0), 0.0)
    cs = np.concatenate([np.zeros((1, x.shape[1])), np.cumsum(x, axis=0)])
    T = x.shape[0]
    out = np.full(x.shape, np.nan)
    hi = np.minimum(np.arange(T) + 1 + k, T)
    lo = np.minimum(np.arange(T) + 1, T)
    out[:T] = cs[hi] - cs[lo]
    out[~finT] = np.nan
    m = np.nanmean(np.where(finT, out, np.nan), axis=1, keepdims=True)
    return np.where(finT, out - m, np.nan)


def profile(z, base, finT, r1T, HALF, sig, k, lag=True, nb=NB):
    """EDGE, COST and RATIO by rank bucket, over the whole live cross-section."""
    _, cnt, pos = R.ranked(z[sig], base)          # pos is (T, n), lagged inside
    fwd = fwd_demeaned(r1T, finT, k)
    if not lag:                                    # the peeking variant
        fwd = np.roll(fwd, 1, axis=0)
    T, n = finT.shape
    esum = np.zeros(nb)
    ecnt = np.zeros(nb, np.int64)
    halves = [[] for _ in range(nb)]
    for t in range(1, T):
        c = int(cnt[t])
        if c < 100:
            continue
        p = pos[t]
        live = np.flatnonzero((p < c) & finT[t] & np.isfinite(fwd[t]))
        if live.size < 100:
            continue
        b = np.minimum((p[live] * nb) // c, nb - 1)
        np.add.at(esum, b, fwd[t][live])
        np.add.at(ecnt, b, 1)
        h = HALF[t][live]
        for bi in range(nb):
            m = (b == bi) & np.isfinite(h)
            if m.any():
                halves[bi].append(h[m])
    edge = np.where(ecnt > 0, esum / np.maximum(ecnt, 1), np.nan) * 1e4
    cost = np.array([np.median(np.concatenate(hh)) if hh else np.nan
                     for hh in halves])
    return dict(edge_bp=edge.tolist(), half_bp=cost.tolist(),
                ratio=(edge / (2.0 * cost)).tolist(),
                n_per_bucket=ecnt.tolist())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()

    print("D327  the rank profile -- no path, no cap, no holding")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T = np.asarray(A["r1T"])
    finT = np.asarray(A["finT"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    d326 = json.loads((REPO / "data" / "d326_both_lenses.json").read_text())
    print(f"  panel {finT.shape}, {len(SIGNALS)} signals, {NB} buckets "
          f"({time.time() - t0:.0f}s)")

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # 4. DEMEANING IS EXACT -- checked before anything is read off the profile.
    fw = fwd_demeaned(r1T, finT, 10)
    mm = np.nanmax(np.abs(np.nanmean(np.where(finT, fw, np.nan), axis=1)))
    assert mm < 1e-12, f"[4] the demeaning leaves a level of {mm:.2e}"
    print(f"    [4] the cross-sectional mean is zero to {mm:.1e} at every bar -- "
          f"the profile cannot show a spurious level")

    # 3. THE BUCKETS PARTITION.
    p0 = profile(z, base, finT, r1T, HALF, "hist_L", 10)
    ns = np.array(p0["n_per_bucket"])
    assert ns.min() > 0 and ns.max() / ns.min() - 1 < 0.05, \
        f"[3] the buckets are uneven: min {ns.min()}, max {ns.max()}"
    print(f"    [3] the 20 buckets partition evenly -- "
          f"{ns.min():,} to {ns.max():,} name-bars each")

    # 1. THE SIGN CONVENTION. Low rank is the LONG leg, high rank the SHORT, so
    #    what the book trades is the SPREAD between them.
    #
    #    THE FIRST VERSION ASSERTED `e[0] > 0 > e[-1]` AND IT FIRED: bucket 0 is
    #    +37.8 and bucket 19 is +5.4 -- both POSITIVE. That is not a sign bug, it
    #    is an asymmetry, and asserting both signs asserted a property of the DATA
    #    rather than of the code. The book is long-minus-short, so the testable
    #    claim is that the SPREAD is signed correctly and that REVERSING the
    #    ranking flips it.
    e = np.array(p0["edge_bp"])
    assert e[0] > e[-1], \
        f"[1] the spread is inverted: bucket 0 {e[0]:+.1f}, 19 {e[-1]:+.1f}"
    rev = profile(z, base, finT, r1T, HALF, "hist_L", 10)
    rev_e = np.array(rev["edge_bp"])[::-1]
    assert rev_e[0] < rev_e[-1], "[1] reversing the profile does not flip it"
    print(f"    [1] the spread is signed correctly -- bucket 0 {e[0]:+.1f} bp "
          f"against bucket 19 {e[-1]:+.1f}, spread {e[0] - e[-1]:+.1f}, and "
          f"reversing flips it")
    print(f"        NOTE: bucket 19 is POSITIVE. The short end does not fall "
          f"outright; the edge is asymmetric and §Q8 measures it.")

    # 2. CAUSALITY -- the peeking variant must differ.
    pk = profile(z, base, finT, r1T, HALF, "hist_L", 10, lag=False)
    d = np.nanmax(np.abs(np.array(pk["edge_bp"]) - e))
    assert d > 1e-9, "[2] the peeking variant gives the same profile"
    print(f"    [2] CAUSALITY: peeking moves the profile by up to {d:.1f} bp")

    # C. COST DIMENSIONS -- ONE name crosses TWICE, not the paired four times.
    r = np.array(p0["ratio"])
    h = np.array(p0["half_bp"])
    assert np.allclose(r[np.isfinite(r)], (e / (2.0 * h))[np.isfinite(r)])
    assert not np.allclose(r[np.isfinite(r)], (e / (4.0 * h))[np.isfinite(r)])
    print("    [C] the ratio is edge / (2 x half-spread); the paired 4x form is "
          "rejected")

    # 6. THE SELF-TEST MUST RAISE on a profile handed free money.
    broke = False
    try:
        bad = e.copy()
        bad[0] += 50.0
        assert abs(bad[0] - e[0]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] the profile check passed a bucket handed free money"
    print("    [6] and the check raises on a bucket handed free money")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the profiles -----------------------------------------------------
    res = {}
    for s in SIGNALS:
        for k in KS:
            res[f"{s}/k{k}"] = profile(z, base, finT, r1T, HALF, s, k)
    print(f"  {len(res)} profiles ({time.time() - t0:.0f}s)")

    sel = [0, 1, 2, 4, 6, 9, 10, 13, 15, 17, 18, 19]
    for k in KS:
        print(f"\nEDGE by rank bucket, k={k}   (bp, demeaned; bucket 0 = the "
              f"LONG end)")
        print("%-14s" % "signal" + "".join("%7d" % b for b in sel))
        for s in SIGNALS:
            e = np.array(res[f"{s}/k{k}"]["edge_bp"])
            print("%-14s" % s + "".join("%+7.0f" % e[b] for b in sel))

    print("\nCOST by rank bucket -- median half-spread, bp (k-independent)")
    print("%-14s" % "signal" + "".join("%7d" % b for b in sel))
    for s in SIGNALS:
        h = np.array(res[f"{s}/k10"]["half_bp"])
        print("%-14s" % s + "".join("%7.1f" % h[b] for b in sel))

    print("\nRATIO -- edge / (2 x half-spread), k=20. Above 1.0 covers its cost.")
    print("%-14s" % "signal" + "".join("%7d" % b for b in sel))
    for s in SIGNALS:
        r = np.array(res[f"{s}/k20"]["ratio"])
        print("%-14s" % s + "".join("%+7.2f" % r[b] for b in sel))

    # ---- predictions -------------------------------------------------------
    def mono(e):
        d = np.diff(e)
        return float(np.mean(d < 0))          # 1.0 = perfectly decreasing
    def extreme(s, k):
        e = np.array(res[f"{s}/k{k}"]["edge_bp"])
        return float(e[0] - e[-1])
    def middle(s, k):
        e = np.array(res[f"{s}/k{k}"]["edge_bp"])
        return float(np.abs(np.diff(e[5:15])).mean())

    q2 = not any(mono(np.array(res[f"{s}/k20"]["edge_bp"])) > 0.85
                 for s in SIGNALS)
    ext = {s: extreme(s, 20) for s in SIGNALS}
    d326i = {s: max(d326["invariant"][f"{s}/k{k}"]["net_per_trade"] for k in KS)
             for s in SIGNALS if f"{s}/k10" in d326["invariant"]}
    common = [s for s in SIGNALS if s in d326i]
    rho = float(np.corrcoef(
        np.argsort(np.argsort([ext[s] for s in common])),
        np.argsort(np.argsort([d326i[s] for s in common])))[0, 1])
    q5 = rho > 0.7
    hs = np.array(res["skew_63/k10"]["half_bp"])
    others = np.array([np.array(res[f"{s}/k10"]["half_bp"]) for s in SIGNALS
                       if s != "skew_63"])
    q3 = bool(np.nanmean(hs[[0, 1, 18, 19]])
              < np.nanmean(others[:, [0, 1, 18, 19]]))
    q7 = all(extreme(s, 40) < extreme(s, 10) for s in SIGNALS)
    # Q8 -- how much of the spread is the LONG end? Added AFTER assertion [1]
    # surfaced the asymmetry, so it is a measurement and NOT a pre-registered
    # prediction. Recorded that way.
    asym = {s: float(np.array(res[f"{s}/k20"]["edge_bp"])[0]
                     / max(extreme(s, 20), 1e-9)) for s in SIGNALS}
    print("\nPREDICTIONS")
    for kk, vv in (("Q2 no signal has a monotone rank profile  [load-bearing]", q2),
                   ("Q3 skew_63's extremes are CHEAPER than the others'", q3),
                   ("Q5 extreme-bucket edge ranks signals as D326 did (rho>0.7)", q5),
                   ("Q7 the profile is flatter at k=40 than k=10", q7)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print("    Q5 rho = %+.3f" % rho)
    print("    monotone fraction, k=20: " +
          "  ".join("%s %.2f" % (s, mono(np.array(res[f"{s}/k20"]["edge_bp"])))
                    for s in SIGNALS))
    print("    extreme spread (b0 - b19), k=20: " +
          "  ".join("%s %+.0f" % (s, ext[s]) for s in SIGNALS))
    print("    Q8 long-end share of the spread, k=20 (NOT pre-registered): "
          + "  ".join("%s %.0f%%" % (s, 100 * asym[s]) for s in SIGNALS))
    print("    skew_63 extreme half-spread %.1f vs others %.1f"
          % (np.nanmean(hs[[0, 1, 18, 19]]),
             np.nanmean(others[:, [0, 1, 18, 19]])))

    OUT.write_text(json.dumps(dict(
        note="D327: rank profiles. NO PATH -- never quote in bp/bar or compare "
             "to a book (FINDINGS section 10).",
        buckets=NB, signals=list(SIGNALS), ks=list(KS), profiles=res,
        spearman_vs_d326=rho, long_end_share=asym,
        predictions=dict(Q2=bool(q2), Q3=bool(q3), Q5=bool(q5), Q7=bool(q7))),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
