"""D291 -- IS THE VETO'S CONTROL TURNOVER-MATCHED? Audit before reading a number.

    uv run python scripts/d291_control_audit.py

CLAUDE.md: "A control must share the treatment's nuisance, not just its count.
Matched-count != matched-turnover (D279)."

The veto keeps the names B ranks well. B's percentile is AUTOCORRELATED, so the
kept set persists and the book re-enters rarely. The random-removal control
keeps a fresh uniform subset EVERY BAR, so a name can be dropped and re-added
on consecutive bars for no reason at all.

Every statistic in this study is measured on FRESH ENTRIES. If the control
re-enters far more often than the treatment, the two books are not being
compared on the same thing, and the paired difference is reading a turnover gap
rather than B's content. This file measures that gap before any veto number is
believed.

The gate's control -- A alone at N' -- is audited the same way, because it is
a persistent book and the prediction is that it matches where the random one
does not.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location(
    "r291", REPO / "scripts" / "run_d291_confluence.py")
R = importlib.util.module_from_spec(spec)
sys.modules["r291"] = R
spec.loader.exec_module(R)
M = R.M
OUT = REPO / "data" / "d291_control_audit.json"


def entries_per_bar(counts):
    """Mean fresh entries per bar, over bars the book is active."""
    a = counts[counts > 0]
    return float(a.mean()) if a.size else 0.0


def main() -> int:
    panel, _ = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    fwd = M.forward_returns(panel, live)
    pool, peaks = R.pool_and_peaks()
    Rk = {c: R.ranked(z[c], base) for c in pool}
    plans = {c: R.LegPlan(Rk[c][0], Rk[c][1], peaks[c][0], T) for c in pool}

    print("VETO: the treatment against its random-removal control\n")
    print(f"  {'A':16s} {'B':14s} {'f':>5s} | {'held/bar':>8s} | "
          f"{'veto ent':>8s} {'rand ent':>8s} {'ratio':>6s} | "
          f"{'veto run':>8s} {'rand run':>8s}")
    rows = []
    for a, b in R.CELLS["veto"]:
        if a not in pool or b not in pool:
            continue
        pl = plans[a]
        _, cnt_b, pos_b = Rk[b]
        k = peaks[a][1]
        for f in R.FRACTIONS:
            klo, khi = R.keep_masks(pos_b, cnt_b, pl, f)
            if not klo.any():
                continue
            conf = R.spread_sums(fwd[k], pl, klo, khi, T)
            rng = np.random.default_rng(4242)
            N, ncols = pl.lo.shape
            mlo, mhi = klo.sum(axis=0), khi.sum(axis=0)
            rlo = R._random_keep(N, ncols, mlo, rng)
            rhi = R._random_keep(N, ncols, mhi, rng)
            rand = R.spread_sums(fwd[k], pl, rlo, rhi, T)
            held = float(mlo.mean())
            ve, re_ = entries_per_bar(conf[1]), entries_per_bar(rand[1])
            row = dict(A=a, B=b, f=f, N=pl.N, held=held,
                       veto_entries=ve, rand_entries=re_,
                       ratio=(re_ / ve) if ve else None,
                       veto_run=(held / ve) if ve else None,
                       rand_run=(held / re_) if re_ else None)
            rows.append(row)
    for row in sorted(rows, key=lambda r: -(r["ratio"] or 0))[:14]:
        print(f"  {row['A']:16s} {row['B']:14s} {row['f']:5.2f} | "
              f"{row['held']:8.1f} | {row['veto_entries']:8.2f} "
              f"{row['rand_entries']:8.2f} {row['ratio']:6.2f}x | "
              f"{row['veto_run']:8.1f} {row['rand_run']:8.1f}")
    rr = np.array([r["ratio"] for r in rows if r["ratio"]])
    print(f"\n  {len(rows)} veto cells: control/treatment entry ratio "
          f"p50 {np.median(rr):.2f}x  min {rr.min():.2f}x  max {rr.max():.2f}x")

    print("\n\nGATE: the treatment against its matched-N control\n")
    print(f"  {'A':16s} {'B':14s} {'f':>5s} | {'gate ent':>8s} "
          f"{'ctrl ent':>8s} {'ratio':>6s} | {'gate run':>8s} {'ctrl run':>8s}")
    grows = []
    mcache = {}
    for a, b, _rho in R.CELLS["gate_unordered"]:
        for ca, cb in ((a, b), (b, a)):
            if ca not in pool or cb not in pool:
                continue
            pl = plans[ca]
            _, cnt_b, pos_b = Rk[cb]
            k = peaks[ca][1]
            for f in R.FRACTIONS:
                klo, khi = R.keep_masks(pos_b, cnt_b, pl, f)
                if not klo.any():
                    continue
                conf = R.spread_sums(fwd[k], pl, klo, khi, T)
                ctrl, npr = R.control_matched_n(
                    fwd[k], lambda c, n: R.LegPlan(Rk[c][0], Rk[c][1], n, T),
                    ca, k, klo, khi, T, mcache)
                ge, ce = entries_per_bar(conf[1]), entries_per_bar(ctrl[1])
                grows.append(dict(A=ca, B=cb, f=f, N=pl.N, npr=npr,
                                  gate_entries=ge, ctrl_entries=ce,
                                  ratio=(ce / ge) if ge else None,
                                  gate_run=(float(klo.sum(axis=0).mean()) / ge)
                                  if ge else None,
                                  ctrl_run=(npr / ce) if ce else None))
    for row in sorted(grows, key=lambda r: -(r["ratio"] or 0))[:8]:
        print(f"  {row['A']:16s} {row['B']:14s} {row['f']:5.2f} | "
              f"{row['gate_entries']:8.2f} {row['ctrl_entries']:8.2f} "
              f"{row['ratio']:6.2f}x | {row['gate_run']:8.1f} "
              f"{row['ctrl_run']:8.1f}")
    gr = np.array([r["ratio"] for r in grows if r["ratio"]])
    print(f"\n  {len(grows)} gate cells: control/treatment entry ratio "
          f"p50 {np.median(gr):.2f}x  min {gr.min():.2f}x  max {gr.max():.2f}x")

    json.dump({"purpose": "D291: whether each control shares the treatment's "
                          "TURNOVER, not merely its count. Every statistic in "
                          "the study is measured on fresh entries.",
               "veto": rows, "gate": grows,
               "veto_ratio_p50": float(np.median(rr)),
               "gate_ratio_p50": float(np.median(gr))},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
