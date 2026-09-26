"""The leveraged NG funds' daily creation flow and Stage C1's creation forecast (settlement ledger deposit §P3.4,
§P3.5; D632). Shared by Stage C1's POWER and its runner.

THE FLOW (USD, per fund f ∈ {BOIL, KOLD}, per NAV date t), from `fund_nav_daily` (D619):
    ΔCreate_f[t] = AUM_f[t] − AUM_f[t−1] × NAV_f[t] / NAV_f[t−1]
The published AUM is used, not NAV × shares: the share count is back-adjusted for reverse splits and rounded to 10
shares, which is worth $0.1–1M a day in the early years. `check_ng_contract_counts` proved that the AUM of date t
holds day t's creations: reading A (the same date's shares) matches the audited quarter-end futures counts on KOLD
30/30 and BOIL 24/27, and reading B (the next date's) on 14/30 and 13/27. With lag_c = 0 (D619: ProShares' 2:00 p.m.
cut-off, NAV struck at 2:30 p.m.), day t's creations are traded at day t's settlement and are NOT known at τ.
UNG is absent: no daily shares count exists for it (the data-gap register's G7).

C1's FORECAST (deposit line 220), per fund, least squares in walk-forward training windows:
    ΔCreate_hat[t] = a0 + a1 · r[t−1] + a2 · (r[t−5] + … + r[t−1]) + a3 · ΔCreate[t−1]
where r is the held index's settlement-to-settlement return on the prior ledger days (`R_day` − 1). A ledger day
with no NAV row (an NYSE holiday on which NYMEX settles) carries a flow of 0 and is counted.
The flow in contracts (deposit line 231): Create_flow = L_f × ΔCreate_f / (10,000 × P_held(τ)).

It reads nothing on or after 2025-03-01, and a guard raises if a row does.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
NAV = REPO / "data" / "fixtures" / "fund_nav_daily.csv.gz"
CUT = "2025-03-01"
FUNDS = {"BOIL": 2, "KOLD": -2}
MULT = 10_000.0


class FundFlowError(RuntimeError):
    pass


def flows(days: list[str]) -> tuple[pd.DataFrame, dict[str, int]]:
    """ledger day × fund creation flow in USD (0 where the fund published no NAV that day), and the count of such
    days per fund."""
    n = pd.read_csv(NAV, encoding="utf-8", usecols=["date", "fund", "nav", "aum"])
    n = n[n["fund"].isin(list(FUNDS)) & (n["date"] < CUT)]
    if (n["date"] >= CUT).any():
        raise FundFlowError("a NAV row on or after the cut is in memory")
    out, missing = {}, {}
    for f in FUNDS:
        g = n[n["fund"] == f].sort_values("date").set_index("date")
        fl = g["aum"] - g["aum"].shift(1) * g["nav"] / g["nav"].shift(1)
        s = fl.reindex(days)
        missing[f] = int(s.isna().sum())
        out[f] = s.fillna(0.0)
    return pd.DataFrame(out, index=days), missing


def features(days: list[str], day_return: pd.Series, flow: pd.Series) -> pd.DataFrame:
    """C1's regressors on each ledger day, from data dated strictly before it."""
    r = day_return.reindex(days)
    return pd.DataFrame({"c": 1.0, "r1": r.shift(1), "r5": r.shift(1).rolling(5, min_periods=5).sum(),
                         "f1": flow.reindex(days).shift(1)}, index=days)


def walk_forward_forecast(X: np.ndarray, y: np.ndarray, rows: np.ndarray, train: int, test: int
                          ) -> tuple[np.ndarray, np.ndarray, list[dict[str, float]]]:
    """(forecast, the training residual variance applied to each test row, the coefficient paths). `rows` are the
    row indices in date order on which the walk-forward runs (the same blocks as the retention comparison)."""
    hat, rvar = np.full(len(y), np.nan), np.full(len(y), np.nan)
    paths = []
    start = train
    while start < len(rows):
        tr, te = rows[start - train:start], rows[start:start + test]
        ok = np.isfinite(X[tr]).all(axis=1)
        b = np.linalg.lstsq(X[tr][ok], y[tr][ok], rcond=None)[0]
        res = y[tr][ok] - X[tr][ok] @ b
        hat[te] = X[te] @ b
        rvar[te] = float(res.var(ddof=X.shape[1]))
        paths.append({"a0": float(b[0]), "a1": float(b[1]), "a2": float(b[2]), "a3": float(b[3])})
        start += test
    return hat, rvar, paths
