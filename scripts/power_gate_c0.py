"""D635 §8: POWER for Gate C0, before its runner exists.

The world: S_win = kappa * (Q_B + AUM_B * Q_G) + noise, on the real observation set and predictors (c0_design.py).
The noise is a month-block bootstrap of the real S_win on NON-hedge days: each draw maps every roll month M to a
random source month M' (the same M' for every root, so the cross-root correlation within a month survives). An
observation's noise is S_win of the same role's contract in M' (BCOM's lead or next of M') on the k-th non-hedge day
(BD11 + k) when the observation is the k-th hedge day. Only non-hedge-day S_win is computed; no hedge-day flow is set
against any Q.

The grid: kappa in {0, 0.02, 0.05, 0.10, 0.25}, 400 draws each. Reported: C0-flow's pass rate (the gate's kappa > 0
with month-clustered t >= 2; the size at kappa = 0), the median t, and the separability rate (|corr| < 0.9 and both
kappa_B and kappa_G with t >= 2). The plausible effect, stated in D635 before this ran: kappa ~ 0.05.

    uv run python -W error::RuntimeWarning scripts/power_gate_c0.py       # -> data/index_reweight/power_c0.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "index_reweight" / "power_c0.json"
KAPPAS = (0.0, 0.02, 0.05, 0.10, 0.25)
DRAWS, SEED = 400, 635
T_BAR = 2.0


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def ols_cluster(X: np.ndarray, y: np.ndarray, g: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """No-intercept OLS with CR1 month-clustered standard errors."""
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    k = X.shape[1]
    meat = np.zeros((k, k))
    groups = np.unique(g)
    for gg in groups:
        s = X[g == gg].T @ u[g == gg]
        meat += np.outer(s, s)
    n, G = len(y), len(groups)
    c = G / (G - 1) * (n - 1) / (n - k)
    V = c * XtX_inv @ meat @ XtX_inv
    return b, b / np.sqrt(np.diag(V))


def gate(Qb: np.ndarray, Qg: np.ndarray, aum: np.ndarray, y: np.ndarray, g: np.ndarray, rho: float) -> dict[str, Any]:
    b2, t2 = ols_cluster(np.column_stack([Qb, Qg]), y, g)
    separable = bool(abs(rho) < 0.9 and t2[0] >= T_BAR and t2[1] >= T_BAR)
    if separable:
        k, t = float(b2[0]), float(t2[0])
    else:
        b1, t1 = ols_cluster((Qb + aum * Qg)[:, None], y, g)
        k, t = float(b1[0]), float(t1[0])
    return {"kappa": k, "t": t, "pass": bool(k > 0 and t >= T_BAR), "separable": separable}


def selftest_cluster() -> None:
    rng = np.random.default_rng(1)
    X = rng.normal(size=(2000, 1))
    g = np.repeat(np.arange(100), 20)
    y = 0.5 * X[:, 0] + rng.normal(size=2000)
    b, t = ols_cluster(X, y, g)
    assert abs(b[0] - 0.5) < 0.1 and t[0] > 5, (b, t)
    y0 = rng.normal(size=2000)
    b0, t0 = ols_cluster(X, y0, g)
    assert abs(t0[0]) < 4, t0


def main() -> int:
    selftest_cluster()
    D = _load("c0_design", "c0_design.py")
    b = D.build()
    o = b["obs"]
    bd, bdays = b["bd"], b["bdays"]
    panel = pd.read_csv(D.PANEL, encoding="utf-8", dtype={"day": str})
    panel = panel[panel["day"] < "2025-03-01"].copy()
    panel["sym"] = panel["sym"].str.split("-").str[0]  # the design's label: root + month + 2-digit year
    if not set(panel["sym"]) & set(b["obs"]["sym"]):
        raise RuntimeError("no contract label is shared by the panel and the design")
    # the non-hedge days, BD12-BD16, of every roll month: the only S_win computed
    nonhedge = {d for d in bdays if 12 <= bd[d] <= 16 and d[:7] in set(o["month"])}
    keep = {(s, d) for s, d in zip(panel["sym"], panel["day"]) if d in nonhedge}
    sw = D.norms(panel, bdays, keep).dropna(subset=["S_win"])
    swd = {(s, d): v for s, d, v in zip(sw["sym"], sw["day"], sw["S_win"])}
    table = D.G.lead_table()
    LET = D.LETTER
    # noise pool: (root, role, month, k) -> S_win on the k-th non-hedge day of that month
    pool: dict[tuple[str, str, str, int], float] = {}
    for comp in D.G.CME_COMPS:
        root = D.G.COMP[comp][1]
        for per in D.months():
            L, N = D.G.lead_next(table[D.G.COMP[comp][2]], per.year, per.month)
            ds = sorted(d for d in nonhedge if d[:7] == str(per))
            for role, c in (("L", L), ("N", N)):
                sym = f"{root}{LET[c[1] - 1]}{str(c[0])[2:]}"
                for k, d in enumerate(ds[:5], start=1):
                    if (sym, d) in swd:
                        pool[(root, role, str(per), k)] = swd[(sym, d)]
    if len(pool) < 1000:
        raise RuntimeError(f"the noise pool holds only {len(pool)} cells")
    o = o.sort_values(["root", "month", "role", "day"]).reset_index(drop=True)
    o["k"] = o.groupby(["root", "month", "role"]).cumcount() + 1
    months = sorted(o["month"].unique())
    Qb, Qg = o["Q_B"].to_numpy(float), o["Q_G"].to_numpy(float)
    aum = o["aum_bn"].to_numpy(float)
    rho = float(np.corrcoef(Qb[(Qb != 0) | (Qg != 0)], Qg[(Qb != 0) | (Qg != 0)])[0, 1])
    keys = list(zip(o["root"], o["role"], o["month"], o["k"]))
    rng = np.random.default_rng(SEED)
    res: dict[str, Any] = {"observations": len(o), "months": len(months), "corr_QB_QG": round(rho, 4),
                           "noise_pool_cells": len(pool), "draws": DRAWS, "seed": SEED, "grid": {}}
    noise_sd = {r: round(float(np.std([v for (rr, *_), v in pool.items() if rr == r])), 1)
                for r in sorted({k[0] for k in pool})}
    res["noise_sd_by_root_contracts"] = noise_sd
    res["signal_scale"] = {"median_abs_Q_comb_nonzero": round(float(np.median(np.abs((Qb + aum * Qg)[(Qb != 0) | (Qg != 0)]))), 1)}
    for kappa in KAPPAS:
        passes, ts, seps, used = [], [], [], []
        for _ in range(DRAWS):
            src = dict(zip(months, rng.choice(months, size=len(months), replace=True)))
            noise = np.array([pool.get((r, ro, src[m], k), np.nan) for r, ro, m, k in keys])
            ok = np.isfinite(noise)
            y = kappa * (Qb + aum * Qg)[ok] + noise[ok]
            gr = gate(Qb[ok], Qg[ok], aum[ok], y, o["month"].to_numpy()[ok], rho)
            passes.append(gr["pass"])
            ts.append(gr["t"])
            seps.append(gr["separable"])
            used.append(int(ok.sum()))
        res["grid"][str(kappa)] = {"pass_rate": round(float(np.mean(passes)), 4), "median_t": round(float(np.median(ts)), 3),
                                   "separable_rate": round(float(np.mean(seps)), 4),
                                   "median_observations_used": int(np.median(used))}
        print(f"kappa {kappa}: pass {res['grid'][str(kappa)]['pass_rate']}, median t "
              f"{res['grid'][str(kappa)]['median_t']}, separable {res['grid'][str(kappa)]['separable_rate']}", flush=True)
    p05 = res["grid"]["0.05"]["pass_rate"]
    res["reading"] = {"size_at_kappa_0": res["grid"]["0.0"]["pass_rate"], "power_at_plausible_0.05": p05,
                      "underpowered_at_plausible": bool(p05 < 0.8)}
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}; noise SD by root {noise_sd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
