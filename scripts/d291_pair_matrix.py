"""Within-bar Spearman across every CAPTURABLE candidate, both directions.

    uv run python scripts/d291_pair_matrix.py

Feeds D291's pair-selection rules. D290's independence probe covered only the
top 14 by CV, so 4 of the 13 tier-1 spread candidates had no correlations at all
and could not be considered for pairing.

RANKED WITHIN BAR, not within symbol. The book is purely cross-sectional; D280
part G2 reported a pooled correlation for a cross-sectional book and had to
withdraw it.
"""
from __future__ import annotations
import importlib.util, json, sys
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


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
D68 = _load("d268", "d268_score_independence.py")
B = M.B
OUT = REPO / "data" / "d291_pair_matrix.json"

U = json.loads((REPO / "data" / "d290_unified_rank.json").read_text())["rows"]
CAP = sorted({r["c"] for r in U["spread"] if r["tier"] == 1})
print(f"{len(CAP)} capturable tier-1 spread candidates: {', '.join(CAP)}")

z = np.load(BC.CACHE, allow_pickle=False)
panel, _ = M.RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
base = z["warm"] & panel.live
n, T = base.shape
cols = []
for c in CAP:
    s = np.where(base, z[c], np.nan)
    r = np.full((n, T), np.nan)
    for t in range(T):
        r[:, t] = D68.rankify(s[:, t])
    cols.append(r.reshape(-1))
X = np.vstack(cols)
ok = np.all(np.isfinite(X), axis=0)
X = X[:, ok]
print(f"{X.shape[1]:,} name-bars with all {len(CAP)} finite")
R = np.corrcoef(X)
lam = np.maximum(np.linalg.eigvalsh(R), 0.0)
eff = float(lam.sum() ** 2 / (lam ** 2).sum())
print(f"effective independent: {eff:.2f} of {len(CAP)}\n")
print("       " + " ".join(f"{c[:6]:>7s}" for c in CAP))
for i, c in enumerate(CAP):
    print(f"{c[:6]:>6s} " + " ".join(f"{R[i, j]:+7.2f}" for j in range(len(CAP))))

band = [(CAP[i], CAP[j], float(R[i, j])) for i in range(len(CAP))
        for j in range(i + 1, len(CAP)) if 0.35 <= R[i, j] <= 0.65]
print(f"\nGATE RULE, rho in [0.35, 0.65]: {len(band)} pairs")
for a, b, r in sorted(band, key=lambda x: -x[2]):
    print(f"  {a:16s} + {b:16s} {r:+.3f}")
OUT.write_text(json.dumps({"candidates": CAP, "spearman": R.tolist(),
                           "effective_independent": eff,
                           "gate_band": band, "cells": int(X.shape[1])}, indent=1))
print(f"\nwrote {OUT.relative_to(REPO)}")
