"""POWER for Stage B of the settlement flow ledger on NG (deposit §5.2's update step, judged by §6's retention rule
out of sample under §10's walk-forward). Written before Stage B's pre-registration and runner. It reads NO in-sample
signed flow: the in-sample side is the predictor panel and unsigned volumes. The noise is the pre-sample's.

THE STAGE B PREDICTOR at τ (deposit lines 368–384), for parameters p ∈ [0, 1), R > 0:
    K = p σ² / (p² σ² + R);  Q_hat = μ + K (z − p μ);  Q_rem = (1 − p) Q_hat
with μ = P1 (`q_est`), σ² = its prior variance (`sigma_Q`², A5's form) and z = the abnormal signed pre-window flow
13:30 → τ over the held contracts, residualised on the return and the calendar flags with coefficients fitted in the
training window (D631 §2). p = 0 gives K = 0 and Q_rem = μ: Stage A exactly.

FIT (deposit §8, §10): in each 252-day training window, the (p, R) on a grid that maximises the partial correlation of
Q_rem with the abnormal signed window flow S_win, net of [1, r, flags]; applied unchanged to the next 63 days.
RETENTION, clause 1 (deposit line 417, read net of the controls as A8 read H1a's): the out-of-sample partial correlation
of Stage B's Q_rem with S_win is ≥ 1.10 × Stage A's on the same days, with Stage A's > 0.

SIMULATION, at τ = 13:50 (928 of NG's 1,028 traded days enter at 13:50):
  * Q_true = μ + σ × ε, ε ~ N(0, 1): the ledger's own prior;
  * z = π × Q_true + V_pre × u_z, and S_win = 0.061 × Q_true + V_win × u_w (0.061 is D629's measured window slope);
  * (u_z, u_w) are the pre-sample's abnormal signed pre-window (13:30 → 13:50) and window flows, each over its trailing
    volume and residualised on the day's return, drawn TOGETHER in 10-day blocks (they are correlated);
  * V_pre, V_win: the in-sample trailing unsigned volumes over the held contracts (13:30 → 13:50 from Sierra; the window
    from Databento);
  * π, the visible pre-window flow per contract of Q: 0 (the null: nothing to learn), 0.015, 0.03, 0.06 (D629's
    window slope), and 0.15, 0.3, 0.6, 1.0 to find where retention becomes likely.
Reported: the probability that clause 1 retains Stage B (at π = 0 that is the false-retention rate), the out-of-sample
partial correlations, and the median fitted p. Clause 2 (H2's t not reduced) is a price test and is not simulated.

    uv run python scripts/ledger_power_stage_b.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import ledger_power_signed_h1 as P  # noqa: E402  (business days, coverage, the abnormal-sum helper)

PRETAU = REPO / "data" / "ledger_signed_pretau_daily.csv.gz"
OUT_JSON = REPO / "data" / "ledger_power_stage_b.json"
TAU = "13:50"
TRAIN, TEST, BLOCK, SEED, REPS = 252, 63, 10, 20260927, 100
P_GRID = (0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9)
KAPPA = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)
PIS = (0.0, 0.015, 0.03, 0.06, 0.15, 0.3, 0.6, 1.0)
WIN_SLOPE = 0.061
FLAGS = P.FLAGS["NG"]


class StageBPowerError(RuntimeError):
    pass


def kalman_q_rem(mu: np.ndarray, s2: np.ndarray, z: np.ndarray, p: float, R: float) -> np.ndarray:
    if p == 0.0:
        return mu.copy()
    K = p * s2 / (p * p * s2 + R)
    return (1.0 - p) * (mu + K * (z - p * mu))


def residualiser(X: np.ndarray) -> np.ndarray:
    """M = I − X (X'X)⁺ X' (constant flags dropped by the pseudo-inverse)."""
    return np.eye(len(X)) - X @ np.linalg.pinv(X.T @ X) @ X.T


def partial_corr(a: np.ndarray, b: np.ndarray, M: np.ndarray) -> float:
    ra, rb = M @ a, M @ b
    den = float(np.sqrt((ra @ ra) * (rb @ rb)))
    return float(ra @ rb / den) if den > 0 else 0.0


def walk_forward(mu: np.ndarray, s2: np.ndarray, z_raw: np.ndarray, s_win: np.ndarray, C: np.ndarray
                 ) -> dict[str, Any]:
    """Fit (p, R) in each training window, predict the next TEST days; return the OOS predictors of both stages."""
    n = len(mu)
    qa, qb = np.full(n, np.nan), np.full(n, np.nan)
    fitted = []
    start = TRAIN
    while start < n:
        tr, te = np.arange(start - TRAIN, start), np.arange(start, min(start + TEST, n))
        # z residualised on the controls with training-window coefficients
        coef = np.linalg.pinv(C[tr].T @ C[tr]) @ C[tr].T @ z_raw[tr]
        z = z_raw - C @ coef
        M = residualiser(C[tr])
        rs = M @ s_win[tr]
        z_var = float(np.var(z[tr]))
        best, arg = -np.inf, (0.0, 1.0)
        for p in P_GRID:
            for k in (KAPPA if p > 0 else (1.0,)):
                q = M @ kalman_q_rem(mu[tr], s2[tr], z[tr], p, k * z_var)
                den = float(np.sqrt((q @ q) * (rs @ rs)))
                c = float(q @ rs / den) if den > 0 else -np.inf
                if c > best:
                    best, arg = c, (p, k * z_var)
        fitted.append(arg[0])
        qa[te] = mu[te]
        qb[te] = kalman_q_rem(mu[te], s2[te], z[te], *arg)
        start += TEST
    oos = np.isfinite(qb)
    M = residualiser(C[oos])
    ra, rb = partial_corr(qa[oos], s_win[oos], M), partial_corr(qb[oos], s_win[oos], M)
    return {"rho_a": ra, "rho_b": rb, "retained": bool(ra > 0 and rb >= 1.10 * ra), "p_fitted": fitted,
            "n_oos": int(oos.sum())}


def presample_noise() -> np.ndarray:
    """(u_z, u_w) per pre-sample day, each residualised on the front's return, as D629's POWER built its noise."""
    import statsmodels.api as sm  # type: ignore[import-untyped]
    days = [d for d in P.business_days("NG") if d < P.FIRST_IN]
    first = P.first_days()
    win = P.signed_pivots("NG", "pre", days)
    pt = pd.read_csv(PRETAU, encoding="utf-8")
    pt = pt[pt["day"] < P.FIRST_IN]
    if (pt["day"] >= P.FIRST_IN).any():
        raise StageBPowerError("an in-sample signed row is in memory")
    piv = {c: pt.pivot_table(index="day", columns="ym", values=c, aggfunc="sum").reindex(days).fillna(0.0)
           for c in ("net_pre_1350", "v_pre_1350")}
    hold = P.presample_holdings("NG", days)
    fix = pd.read_csv(P.PRESAMPLE_FIX, encoding="utf-8")
    fix = fix[fix["root"] == "NG"].set_index("day")
    ret = fix["c27"] / fix["c29"].shift(1) - 1.0
    rows = []
    for i, d in enumerate(days):
        if d not in hold:
            continue
        c = [ym for ym in hold[d] if P.covered("NG", ym, i, days, first)]
        if len(c) < len(hold[d]):
            continue
        zn, zt = P.abnormal(piv["net_pre_1350"], days, i, c)
        _v, vz = P.abnormal(piv["v_pre_1350"], days, i, c)
        wn, wt = P.abnormal(win["net_win"], days, i, c)
        _w, vw = P.abnormal(win["v_win"], days, i, c)
        rows.append({"day": d, "uz": (zn - zt) / vz if vz > 0 else np.nan,
                     "uw": (wn - wt) / vw if vw > 0 else np.nan, "r": float(ret.get(d, np.nan))})
    df = pd.DataFrame(rows).dropna()
    X = sm.add_constant(df[["r"]])
    out = np.column_stack([sm.OLS(df[k], X).fit().resid.to_numpy() for k in ("uz", "uw")])
    return out


def design() -> pd.DataFrame:
    f = pd.read_csv(P.FLOW, encoding="utf-8")
    f = f[(f["root"] == "NG") & (f["tau"] == TAU)]
    if (f["day"] >= P.CUT).any():
        raise StageBPowerError("a flow row on or after the cut is in memory")
    f = f.dropna(subset=["sigma_Q"])
    days = P.business_days("NG")
    pos = {d: i for i, d in enumerate(days)}
    held = f.set_index("day")["held"]
    pt = pd.read_csv(PRETAU, encoding="utf-8", usecols=["day", "ym", "v_pre_1350"])  # UNSIGNED volume only
    vp = pt.pivot_table(index="day", columns="ym", values="v_pre_1350", aggfunc="sum").reindex(days).fillna(0.0)
    vw = pd.read_csv(P.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "vol_win"])
    vw = vw[(vw["root"] == "NG") & (vw["kind"] == "outright")]
    vwp = vw.pivot_table(index="day", columns="ym", values="vol_win", aggfunc="sum").reindex(days).fillna(0.0)
    cal = pd.read_csv(P.CAL, encoding="utf-8")
    cal = cal[cal["root"] == "NG"].set_index("date")
    rows = []
    for d, mu, sq, r in zip(f["day"], f["q_est"], f["sigma_Q"], f["r_held"]):
        i = pos[d]
        if i < 20:
            continue
        hs = held[d].split(";")
        rows.append({"day": d, "mu": mu, "s2": sq * sq, "r": r, "V_pre": P.abnormal(vp, days, i, hs)[1],
                     "V_win": P.abnormal(vwp, days, i, hs)[1]})
    out = pd.DataFrame(rows)
    for fl in FLAGS:
        out[fl] = cal.loc[out["day"], fl].to_numpy()
    return out.reset_index(drop=True)


def build() -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    U = presample_noise()
    d = design()
    n = len(d)
    C = np.column_stack([np.ones(n), d["r"].to_numpy()] + [d[fl].to_numpy(float) for fl in FLAGS])
    mu, s2 = d["mu"].to_numpy(), d["s2"].to_numpy()
    # THE CEILING, from the ledger's own prior and no data: Var(Q_true) = Var(μ) + E[σ²]. A perfect observation of
    # Q_true can raise a correlation that μ attains by at most sqrt((Var μ + E σ²) / Var μ) − 1.
    share = float(np.var(mu) / (np.var(mu) + np.mean(s2)))
    ceiling = {"sd_mu": float(np.std(mu)), "rms_sigma_prior": float(np.sqrt(np.mean(s2))),
               "share_of_var_q_true_explained_by_mu": share,
               "max_relative_corr_gain_from_perfect_q": float(np.sqrt(1.0 / share) - 1.0),
               "retention_bar": 0.10}
    res: dict[str, Any] = {"ceiling": ceiling, "n_days": n, "tau": TAU, "median_abs_mu": float(np.median(np.abs(mu))),
                           "median_sigma_prior": float(np.median(np.sqrt(s2))),
                           "median_V_pre": float(d["V_pre"].median()), "median_V_win": float(d["V_win"].median()),
                           "presample_days": int(len(U)),
                           "presample_corr_uz_uw": float(np.corrcoef(U[:, 0], U[:, 1])[0, 1]), "sims": {}}
    for pi in PIS:
        runs = []
        for _ in range(REPS):
            idx = np.empty(n, dtype=int)
            i = 0
            while i < n:
                s = int(rng.integers(0, len(U) - BLOCK))
                k = min(BLOCK, n - i)
                idx[i:i + k] = np.arange(s, s + k)
                i += k
            qt = mu + np.sqrt(s2) * rng.standard_normal(n)
            z = pi * qt + d["V_pre"].to_numpy() * U[idx, 0]
            sw = WIN_SLOPE * qt + d["V_win"].to_numpy() * U[idx, 1]
            runs.append(walk_forward(mu, s2, z, sw, C))
        res["sims"][f"{pi:g}"] = {
            "reps": REPS, "retention_rate": float(np.mean([r["retained"] for r in runs])),
            "rho_a_median": float(np.median([r["rho_a"] for r in runs])),
            "rho_b_median": float(np.median([r["rho_b"] for r in runs])),
            "p_fitted_median": float(np.median([np.median(r["p_fitted"]) for r in runs])),
            "share_windows_p_zero": float(np.mean([np.mean(np.array(r["p_fitted"]) == 0) for r in runs])),
            "n_oos": runs[0]["n_oos"]}
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    out = build()
    text = json.dumps(out, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT_JSON.read_text(encoding="utf-8") != text:
            raise StageBPowerError(f"{OUT_JSON.name} does not reproduce")
        print(f"[check] {OUT_JSON.name} reproduces byte for byte")
        return 0
    OUT_JSON.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k != "sims"}, indent=1))
    for k, v in out["sims"].items():
        print("pi", k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
