"""D296b -- is the gross peak's LOCATION resolved, or is k=18 a coin flip?

    uv run python scripts/d296_peak_resolution.py [--boot 2000]

D296 prices the SEARCH for the gross peak. This file asks the separate question
the fine grid makes askable for the first time: HOW WELL LOCATED is that peak?

WHY IT MATTERS, AND WHY THE NULL CANNOT ANSWER IT. A grid-max null says the
peak is bigger than chance produces. It says nothing about whether k=18 is
distinguishable from k=16 -- and on this profile the neighbours sit +81.99 (k=17)
and +80.77 (k=19) against k=18's +92.31, a 10 bp step against a standard error
on the level of ~29 bp. R14's fifth amendment already requires the peak's
POSITION to be reported (interior vs edge); the 2026-09-03 amendment goes
further and asks for the profile's SHAPE, "plateau vs spike". That is a claim
about resolution, so it is measured.

TWO INSTRUMENTS.

  PAIRED t, k* vs every other k, on the bars both horizons cover. Neighbouring
  horizons share almost all of their return path, so their difference has a far
  smaller standard error than either level -- an unpaired comparison of two
  overlapping windows would be badly conservative and is the wrong test.

  MOVING-BLOCK BOOTSTRAP over bars, block length 40 = the longest horizon, so a
  block is longer than the overlap any pair of horizons shares. Resample, take
  the argmax on each criterion, and report the DISTRIBUTION of the argmax. If
  k=18 wins 12% of resamples the peak is not located; if it wins 80% it is.

The per-bar series is rebuilt here and held BIT-IDENTICAL to `C.cell_stats`'
published bp and t (assertion [1]), because a resolution claim computed by
slightly different arithmetic is not a claim about that peak.
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


N6 = _load("d296", "d296_criterion_matched_nulls.py")
C, R, M, SP, ET = N6.C, N6.R, N6.M, N6.SP, N6.ET
OUT = REPO / "data" / "d296_peak_resolution.json"
HORIZONS = N6.HORIZONS_FINE
BLOCK = max(HORIZONS)          # a block outlives the longest overlap
SEED = 20260904


def per_bar(fwd, lo_idx, hi_idx, T):
    """The per-bar spread series for every horizon, plus each bar's mask.

    `cell_stats` collapses this to (bp, t) immediately; the resolution question
    needs the series itself, so it is rebuilt from the SAME `M.bar_sums` in the
    SAME order and assertion [1] holds the collapse to `cell_stats`' output.
    """
    lr, lc = lo_idx
    hr, hc = hi_idx
    ser, msk = {}, {}
    for k in HORIZONS:
        f = fwd[k]
        slo, clo = M.bar_sums(f, lr, lc, T)
        shi, chi = M.bar_sums(f, hr, hc, T)
        m = (clo > 0) & (chi > 0)
        ser[k] = slo[m] / clo[m] - shi[m] / chi[m]
        msk[k] = m
    return ser, msk


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    t0 = time.time()

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == R.BC.cache_key(M.B.FIXTURE), "CACHE IS STALE"
    base = z["warm"] & live
    M.HORIZONS = HORIZONS
    C.HORIZONS = HORIZONS
    fwd = M.forward_returns(panel, live)
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    sa, s1, s2 = z[C.PRIMARY], z[C.PAIR[0]], z[C.PAIR[1]]

    ranks = C.rank_all(sa, s1, s2, base, True)
    b = C.book(ranks, N6.N_FIXED, T, True)
    cs = C.cell_stats(fwd, b[0], b[1], T)
    rt_mean, rt_rob = N6.rt_membership(b, half)
    ser, msk = per_bar(fwd, b[0], b[1], T)

    # 1. THE SERIES MUST COLLAPSE TO THE PUBLISHED CELL, BIT-IDENTICALLY.
    for k in HORIZONS:
        d = ser[k]
        sd = d.std(ddof=1)
        bp = float(d.mean() * 1e4)
        t_ = float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else 0.0
        assert bp == cs[k]["spread"][0] and t_ == cs[k]["spread"][1], (
            f"the rebuilt per-bar series does not collapse to cell_stats at "
            f"k={k}: {bp} vs {cs[k]['spread'][0]}")
    print(f"  [1] the per-bar series collapses to C.cell_stats' bp and t "
          f"bit-identically on all {len(HORIZONS)} horizons")

    # common bars, so every horizon is measured on the same sample
    common = np.ones(T, dtype=bool)
    for k in HORIZONS:
        common &= msk[k]
    S = np.column_stack([ser[k][common[msk[k]]] for k in HORIZONS])
    nb = S.shape[0]
    ks = np.array(HORIZONS)
    assert S.shape == (nb, len(HORIZONS))
    print(f"  [2] common sample: {nb:,} bars covered by all {len(HORIZONS)} "
          f"horizons (per-horizon bars ranged "
          f"{min(int(m.sum()) for m in msk.values()):,}-"
          f"{max(int(m.sum()) for m in msk.values()):,})")

    bp = S.mean(axis=0) * 1e4
    se = S.std(axis=0, ddof=1) / np.sqrt(nb) * 1e4
    tt = bp / se
    kstar = int(ks[int(np.argmax(bp))])
    print(f"\n  on the common sample the gross peak is k={kstar} "
          f"({bp.max():+.2f} bp); the level's own standard error is "
          f"{se[int(np.argmax(bp))]:.2f} bp")

    # ------------------------------------------------------- paired comparison
    print(f"\n{'=' * 86}")
    print(f"  PAIRED: k={kstar} MINUS each other horizon, on the common sample")
    print(f"{'=' * 86}")
    print(f"  {'k':>3s} | {'gross bp':>9s} {'t':>6s} | {'diff bp':>8s} "
          f"{'se':>7s} {'paired t':>9s} | {'95% CI of the diff':>24s}")
    j0 = int(np.argmax(bp))
    paired = {}
    for j, k in enumerate(ks):
        d = (S[:, j0] - S[:, j]) * 1e4
        sd = d.std(ddof=1)
        s_e = sd / np.sqrt(nb)
        pt = d.mean() / s_e if s_e > 0 else 0.0
        lo_, hi_ = d.mean() - 1.96 * s_e, d.mean() + 1.96 * s_e
        paired[int(k)] = dict(bp=float(bp[j]), t=float(tt[j]),
                              diff=float(d.mean()), se=float(s_e),
                              paired_t=float(pt), ci=[float(lo_), float(hi_)])
        flag = "" if k == kstar else ("  distinguishable" if lo_ > 0 else "")
        print(f"  {k:3d} | {bp[j]:+9.2f} {tt[j]:+6.2f} | {d.mean():+8.2f} "
              f"{s_e:7.2f} {pt:+9.2f} | [{lo_:+9.2f}, {hi_:+9.2f}]{flag}")

    # ------------------------------------------------------- block bootstrap
    rng = np.random.default_rng(SEED)
    nblk = int(np.ceil(nb / BLOCK))
    starts_max = nb - BLOCK
    win = {c: np.zeros(len(ks), dtype=np.int64)
           for c in ("bp", "t", "bp_per_bar")}
    for _ in range(a.boot):
        st = rng.integers(0, starts_max + 1, size=nblk)
        idx = (st[:, None] + np.arange(BLOCK)[None, :]).ravel()[:nb]
        B = S[idx]
        mu = B.mean(axis=0)
        sd = B.std(axis=0, ddof=1)
        win["bp"][int(np.argmax(mu))] += 1
        win["t"][int(np.argmax(mu / np.maximum(sd, 1e-300)))] += 1
        win["bp_per_bar"][int(np.argmax(mu / ks))] += 1

    print(f"\n{'=' * 86}")
    print(f"  MOVING-BLOCK BOOTSTRAP ({a.boot:,} resamples, block "
          f"{BLOCK} bars): where does the argmax land?")
    print(f"{'=' * 86}")
    print(f"  {'criterion':12s} | {'obs k*':>6s} | share of resamples won, by k "
          f"(only k winning >=2%)")
    boot = {}
    for c, w in win.items():
        share = w / a.boot
        obs_k = int(ks[int(np.argmax({"bp": bp, "t": tt,
                                      "bp_per_bar": bp / ks}[c]))])
        top = [(int(ks[j]), float(share[j])) for j in np.argsort(-share)
               if share[j] >= 0.02]
        boot[c] = dict(obs_k=obs_k, share={int(ks[j]): float(share[j])
                                           for j in range(len(ks))},
                       p_obs=float(share[int(np.flatnonzero(ks == obs_k)[0])]))
        print(f"  {c:12s} | {obs_k:6d} | "
              + "  ".join(f"k={kk} {vv:.0%}" for kk, vv in top))
        print(f"  {'':12s} | {'':6s} | the observed argmax wins "
              f"{boot[c]['p_obs']:.1%} of resamples")

    # the plateau, named by a criterion rather than by eye
    plate = [int(k) for j, k in enumerate(ks)
             if paired[int(k)]["ci"][0] <= 0]
    print(f"\n  NOT DISTINGUISHABLE from k={kstar} at 95% on the paired test: "
          f"k in {plate}")
    print(f"  -> the gross peak is a PLATEAU of {len(plate)} horizons, not a "
          f"located maximum" if len(plate) > 3 else
          f"  -> the gross peak is reasonably well located")

    json.dump({"purpose": "D296b: how well located is the gross peak on the "
                          "refined horizon grid. A grid-max null prices the "
                          "search; it does not say k=18 beats k=16.",
               "horizons": list(map(int, ks)), "common_bars": int(nb),
               "block": int(BLOCK), "boot": a.boot, "kstar": kstar,
               "rt_mean": rt_mean, "rt_robust": rt_rob,
               "paired": {str(k): v for k, v in paired.items()},
               "bootstrap": boot,
               "indistinguishable_from_kstar": plate},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
