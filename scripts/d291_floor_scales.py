"""D291 -- the floor drawn three ways, on ONE set of null draws.

    uv run python scripts/d291_floor_scales.py

THE PRE-REGISTERED FLOOR IS A MAX-t FLOOR, AND IT IS NOT SCALE-FAIR. Cells here
differ ~7x in the spread of their own nulls (own p95 runs +0.40 to +2.94), so a
single raw-t threshold demands far more of a cell with a tight null than of one
with a wide null. Same bar, different difficulty.

Three readings of the SAME 200 draws:

  MAX-t   p95 of the per-draw maximum RAW t.        <- pre-registered
  MAX-Z   standardise each cell by its OWN null
          first, then take the per-draw maximum.    <- scale-fair
  MIN-p   each cell's empirical p-value against
          its own null, then the per-draw minimum.  <- rank-based, assumes
                                                       nothing about shape

All three control the FAMILY-WISE error rate: the chance that ANY cell clears is
5%, not the chance that a NAMED cell clears. That is the distinction the study
turns on -- 164 cells each given a 5% bar produce 8.2 passes by luck, and
P(at least one passes) is 99.98% before any data is seen.

Standardising a cell by the moments of the same draws that form the null is the
usual studentised-maximum construction. With 200 draws the optimism is small,
and it is disclosed rather than hidden.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
SURF = REPO / "data" / "d291_null_surface.npz"
OUT = REPO / "data" / "d291_floor_scales.json"


def main() -> int:
    if not SURF.exists():
        print(f"no null surface at {SURF}; re-run run_d291_confluence.py")
        return 1
    z = np.load(SURF, allow_pickle=False)
    S = z["surface"]                      # (draws, cells) raw null t
    obs = z["observed_t"]
    kind, A, B = z["cell_kind"], z["cell_A"], z["cell_B"]
    f = z["cell_f"]
    res = json.loads((REPO / "data" / "d291_confluence.json").read_text())
    draws, ncell = S.shape
    print(f"null surface: {draws} draws x {ncell} cells "
          f"({int(np.isfinite(S).sum()):,} finite)")

    ok = np.isfinite(S).sum(axis=0) > 5
    S, obs, kind, A, B, f = S[:, ok], obs[ok], kind[ok], A[ok], B[ok], f[ok]
    mu = np.nanmean(S, axis=0)
    sd = np.nanstd(S, axis=0, ddof=1)
    good = sd > 0
    S, obs, kind, A, B, f = S[:, good], obs[good], kind[good], A[good], B[good], f[good]
    mu, sd = mu[good], sd[good]
    print(f"  usable cells: {S.shape[1]}\n")

    # ------------------------------------------------------------- MAX-t
    mt = np.nanmax(S, axis=1)
    floor_t = float(np.percentile(mt, 95))
    pass_t = obs > floor_t

    # ------------------------------------------------------------- MAX-Z
    Z = (S - mu) / sd
    obs_z = (obs - mu) / sd
    mz = np.nanmax(Z, axis=1)
    floor_z = float(np.percentile(mz, 95))
    pass_z = obs_z > floor_z

    # ------------------------------------------------------------- MIN-p
    # each cell's empirical p against its own null, then the per-draw minimum
    def emp_p(col, v):
        c = col[np.isfinite(col)]
        return (np.sum(c >= v) + 1) / (c.size + 1)

    P = np.empty_like(S)
    for j in range(S.shape[1]):
        col = S[:, j]
        fin = np.isfinite(col)
        order = np.argsort(-col[fin])
        rank = np.empty(fin.sum())
        rank[order] = np.arange(fin.sum())
        P[:, j] = np.nan
        P[fin, j] = (rank + 1) / (fin.sum() + 1)
    obs_p = np.array([emp_p(S[:, j], obs[j]) for j in range(S.shape[1])])
    mp = np.nanmin(P, axis=1)
    floor_p = float(np.percentile(mp, 5))
    pass_p = obs_p < floor_p

    print("THE SAME 200 DRAWS, THREE SCALES\n")
    print(f"  {'scale':7s} | {'floor':>10s} | {'best observed':>14s} | "
          f"{'cells clearing':>14s}")
    print(f"  {'-' * 7}-+-{'-' * 10}-+-{'-' * 14}-+-{'-' * 14}")
    print(f"  {'MAX-t':7s} | {floor_t:+10.2f} | {obs.max():+14.2f} | "
          f"{int(pass_t.sum()):14d}")
    print(f"  {'MAX-Z':7s} | {floor_z:+10.2f} | {obs_z.max():+14.2f} | "
          f"{int(pass_z.sum()):14d}")
    print(f"  {'MIN-p':7s} | {floor_p:10.4f} | {obs_p.min():14.4f} | "
          f"{int(pass_p.sum()):14d}")

    print(f"\n  For reference, the PER-CELL 5% bar (no multiplicity control):")
    per = int((obs_p < 0.05).sum())
    exp_luck = 0.05 * S.shape[1]
    print(f"    cells clearing their own null's p95: {per}")
    print(f"    expected from {S.shape[1]} cells by luck: {exp_luck:.1f}")

    # ------------------------------------------------------- FDR, the STAGE-1
    # instrument. All three floors above control the FAMILY-WISE rate: the
    # chance that ANY cell is a false positive. That is the right question when
    # a study makes ONE claim, and the wrong one when it produces a SHORTLIST
    # to carry forward -- which is all stage 1 does. Benjamini-Hochberg instead
    # bounds the PROPORTION of the shortlist that is false, which is the
    # quantity that actually matters when the cost of a false positive is one
    # more candidate carried to stage 2 and the cost of a false negative is a
    # real signal thrown away.
    m = obs_p.size
    order = np.argsort(obs_p)
    ps = obs_p[order]
    print(f"\n\nFDR -- BENJAMINI-HOCHBERG, the SHORTLIST question")
    print(f"    'what fraction of what I carry forward is noise?'\n")
    print(f"    {'q':>6s} | {'cells kept':>10s} | {'implied false':>13s}")
    fdr_out = {}
    for q in (0.05, 0.10, 0.20, 0.50):
        thr = np.arange(1, m + 1) / m * q
        below = np.flatnonzero(ps <= thr)
        nkeep = int(below.max() + 1) if below.size else 0
        fdr_out[q] = nkeep
        print(f"    {q:6.2f} | {nkeep:10d} | "
              f"{(f'{q * nkeep:.1f}' if nkeep else '-'):>13s}")
    print(f"\n    naive shortlist at p < 0.05: {per} cells, of which "
          f"{exp_luck:.1f} are expected to be noise")
    print(f"    implied false-discovery proportion: "
          f"{(exp_luck / per if per else float('nan')):.0%}")

    print(f"\n\nTOP 10 BY SCALE-FAIR z (each cell against its OWN null)\n")
    print(f"  {'kind':5s} {'A':16s} {'B':16s} {'f':>5s} | {'obs t':>7s} "
          f"{'null mu':>8s} {'null sd':>8s} | {'z':>6s} {'own p':>7s} | "
          f"{'MAX-Z':>6s}")
    for j in np.argsort(-obs_z)[:10]:
        print(f"  {str(kind[j]):5s} {str(A[j]):16s} {str(B[j]):16s} "
              f"{f[j]:5.2f} | {obs[j]:+7.2f} {mu[j]:+8.2f} {sd[j]:8.2f} | "
              f"{obs_z[j]:+6.2f} {obs_p[j]:7.3f} | "
              f"{('PASS' if pass_z[j] else 'no'):>6s}")

    gate = kind == "gate"
    print(f"\n  restricted to the VALID (gate) arm only:")
    for nm, fl, pv, ov in (("MAX-t", floor_t, pass_t, obs),
                           ("MAX-Z", floor_z, pass_z, obs_z)):
        print(f"    {nm}: {int((pv & gate).sum())} of {int(gate.sum())} "
              f"gate cells clear (best {ov[gate].max():+.2f} vs floor "
              f"{fl:+.2f})")

    json.dump({"purpose": "D291: the multiplicity floor redrawn on three "
                          "scales from one set of null draws. The "
                          "pre-registered MAX-t floor is not scale-fair "
                          "across cells whose nulls differ ~7x in spread.",
               "draws": int(draws), "cells": int(S.shape[1]),
               "floor_max_t": floor_t, "floor_max_z": floor_z,
               "floor_min_p": floor_p,
               "best_obs_t": float(obs.max()), "best_obs_z": float(obs_z.max()),
               "best_obs_p": float(obs_p.min()),
               "n_pass_max_t": int(pass_t.sum()),
               "n_pass_max_z": int(pass_z.sum()),
               "n_pass_min_p": int(pass_p.sum()),
               "n_pass_per_cell_only": per,
               "expected_per_cell_by_luck": 0.05 * S.shape[1],
               "rows": [dict(kind=str(kind[j]), A=str(A[j]), B=str(B[j]),
                             f=float(f[j]), t=float(obs[j]),
                             null_mu=float(mu[j]), null_sd=float(sd[j]),
                             z=float(obs_z[j]), own_p=float(obs_p[j]),
                             pass_max_t=bool(pass_t[j]),
                             pass_max_z=bool(pass_z[j]))
                        for j in np.argsort(-obs_z)]},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
