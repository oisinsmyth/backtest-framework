"""D639 s.9: the LETF close-flow POWER step, before any runner (deposit s.6A). The principal, 2026-09-27: "then run the
power study".

    uv run python scripts/power_letf.py      # -> data/letf/power.json + docs/results/LETF_CLOSE_FLOW_POWER.md

WHAT IT READS (D639 s.9, and nothing else):
- the signal's inputs, built exactly as D639 s.3 defines them: A[t-1] per fund, r[t, tau], Q, V, sigma_d, q, I, the
  activation at k = 2, 3, 5;
- the DISPERSION of the tau -> close move: its standard deviation and its autocorrelation, UNSIGNED. The move is
  never multiplied by the flow's direction here, and its mean is never computed. So nothing about whether the flow
  predicts the move is read.

WHAT IT GIVES, per primary cell (tau in 14:30/15:00/15:30 x NQ/ES, k = 3), for H4 (11:00) and H2 (all days):
n (active days); n_eff = n / (1 + 2 sum_{l<=L} (1 - l/(L+1)) rho_l) with Bartlett weights and D639's lag rule on the
unsigned move's autocorrelation; SE = sigma / sqrt(n_eff); MDE at t = 2 (the deposit's) and at Holm's first step with
80% power (z = 2.638 + 0.842), in sigma units and in bp; the plausible effect = the cell's mean round-trip cost in bp
(deposit s.6A's default). A cell whose MDE (t = 2) exceeds it is UNDERPOWERED, and a null there is inconclusive.
Beside it, as CONTEXT and not the pre-registered label: the model's own predicted impact I in bp on the active days
(by construction >= k x cost), since an active day is one where the model claims at least that much.
Signals start at the 21st usable session (V and sigma_d need 20 prior days).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_framework.data.panels import load_panel
from backtest_framework.letf import model as M

REPO = Path(__file__).resolve().parents[1]
LETF = REPO / "data" / "letf"
OUT_JSON = LETF / "power.json"
OUT_MD = REPO / "docs" / "results" / "LETF_CLOSE_FLOW_POWER.md"
RESERVED_FROM = "2025-03-01"
SETS = {"NQ": {"TQQQ": 3, "SQQQ": -3, "QLD": 2, "QID": -2},
        "ES": {"UPRO": 3, "SPXU": -3, "SSO": 2, "SDS": -2, "SPXL": 3, "SPXS": -3}}
RT_POINTS = {"NQ": (3.0 + 2.1342422122227602 * 0.5) / 2.0, "ES": (3.0 + 1.1345161408444429 * 1.25) / 5.0}  # D639 s.3
TAUS = ["14:30", "15:00", "15:30"]
H4_TAU = "11:00"
KS = (2, 3, 5)
Z_HOLM, Z_80 = 2.638, 0.8416  # one-sided 0.05/6, and 80% power
SPLIT = "2024-01-01"  # D639 s.2: the slice no prior line read


def lag_rule(n: int) -> int:
    return int(math.floor(4 * (n / 100) ** (2 / 9)))


def n_eff(x: np.ndarray) -> tuple[float, int, list[float]]:
    """Bartlett-weighted design effect from the series' own autocorrelations, lags 1..L (D639 s.4's rule)."""
    n = len(x)
    L = lag_rule(n)
    xc = x - x.mean()
    den = float((xc * xc).sum())
    rho = [float((xc[:-lg] * xc[lg:]).sum() / den) for lg in range(1, L + 1)]
    deff = 1 + 2 * sum((1 - lg / (L + 1)) * r for lg, r in zip(range(1, L + 1), rho))
    # capped at n: a negative autocorrelation would otherwise count more independent observations than exist, the
    # optimistic side for a power plan
    return min(n / max(deff, 1e-9), float(n)), L, rho


def build_root(root: str) -> dict:
    s = pd.read_csv(LETF / f"phase2_{root}_sessions.csv.gz", encoding="utf-8", dtype={"day": str})
    if (s["day"] >= RESERVED_FROM).any():
        raise RuntimeError("a sealed session reached the power step")
    days = M.trade_days(s)
    s = s.set_index("day")
    nyse = sorted(s.index[s["nyse_open"].astype(bool)])
    usable = pd.Index(days)
    daily_ret = (s.loc[usable, "p1600"] / s.loc[usable, "p_prev_close_same"] - 1).astype(float)
    equiv = s.loc[usable, f"{root.lower()}_equiv_volume"].astype(float)
    daily_ret.index, equiv.index = pd.to_datetime(daily_ret.index), pd.to_datetime(equiv.index)

    aum = pd.read_csv(LETF / "letf_aum_daily.csv.gz", encoding="utf-8", dtype={"date": str})
    aum = aum[aum["ticker"].isin(SETS[root])]
    by = {tk: g.set_index("date")["aum"].astype(float) for tk, g in aum.groupby("ticker")}
    prev_of = {d: nyse[i - 1] for i, d in enumerate(nyse) if i > 0}

    bars_p = load_panel(f"fut_{root}_rth_1m", reserved_from=RESERVED_FROM)
    need = {M.bar_label_ending_at(t) for t in TAUS + [H4_TAU]} | set(TAUS + [H4_TAU]) | {"15:59", "11:59"}
    b = bars_p.frame
    b = b[b["hhmm"].isin(need)].set_index(["day", "hhmm"])["close"].astype(float)

    rows = []
    checked = 0
    for i, d in enumerate(days):
        if i < M.TRAILING_DAYS:
            continue  # V and sigma_d need 20 prior usable sessions
        p = prev_of[d]
        A = {tk: float(by[tk][p]) for tk in SETS[root] if p in by[tk].index}
        if len(A) != len(SETS[root]):
            continue  # a fund without t-1 AUM (none expected in 2016-02 -> 2025-02; counted below)
        if checked < 25 and i % 90 == 0:  # the fast lookup equals the model's aum_prior (test 5's function)
            for tk in SETS[root]:
                assert A[tk] == M.aum_prior(by[tk], d, nyse), (tk, d)
            checked += 1
        V = M.trailing_volume(equiv, d)
        sd = M.trailing_sigma(daily_ret, d)
        prev_close = float(s.at[d, "p_prev_close_same"])
        for tau in TAUS + [H4_TAU]:
            sig = b.get((d, M.bar_label_ending_at(tau)))
            ent = b.get((d, tau))
            ex = b.get((d, "15:59" if tau != H4_TAU else "11:59"))
            if sig is None or ent is None or ex is None:
                continue
            r = M.day_return(sig, prev_close)
            qusd = M.aggregate_flow(SETS[root], A, r)
            q = M.normalised_flow(M.to_contracts(qusd, root, sig), V)
            imp = M.predicted_impact(sd, q, sig)
            rows.append({"day": d, "tau": tau, "abs_q": abs(q), "impact": imp, "impact_bp": imp / sig * 1e4,
                         "move_bp": (ex / ent - 1) * 1e4,
                         "cost_bp": RT_POINTS[root] / ent * 1e4,
                         **{f"active_k{k}": M.is_active(imp, k, RT_POINTS[root]) for k in KS}})
    df = pd.DataFrame(rows)
    out: dict = {"cells": {}, "aum_prior_crosschecks": checked, "signal_days": int(df["day"].nunique())}
    for tau in TAUS + [H4_TAU]:
        g = df[df["tau"] == tau].sort_values("day")
        cell: dict = {"all_days": int(len(g))}
        for k in KS:
            a = g[g[f"active_k{k}"]]
            if len(a) < 30:
                cell[f"k{k}"] = {"n": int(len(a)), "note": "fewer than 30 active days"}
                continue
            x = a["move_bp"].to_numpy(float)  # UNSIGNED: never multiplied by the direction
            ne, L, rho = n_eff(x)
            sig = float(np.std(x, ddof=1))
            se_bp = sig / math.sqrt(ne)
            cost = float(a["cost_bp"].mean())
            cell[f"k{k}"] = {"n": int(len(a)), "active_share": float(len(a) / len(g)), "n_eff": ne, "lag": L,
                             "rho_1": rho[0] if rho else None, "sigma_move_bp": sig, "se_bp": se_bp,
                             "se_sigma": 1 / math.sqrt(ne), "mde_t2_bp": 2 * se_bp, "mde_t2_sigma": 2 / math.sqrt(ne),
                             "mde_holm80_bp": (Z_HOLM + Z_80) * se_bp, "mean_cost_bp": cost,
                             "underpowered_t2": bool(2 * se_bp > cost),
                             "underpowered_holm80": bool((Z_HOLM + Z_80) * se_bp > cost),
                             "n_2024_plus": int((a["day"] >= SPLIT).sum()),
                             "mean_predicted_impact_bp": float(a["impact_bp"].mean()),
                             "powered_for_own_prediction_t2": bool(2 * se_bp <= float(a["impact_bp"].mean()))}
        # H2: all days, quintiles of |q|
        x = g["move_bp"].to_numpy(float)
        ne, L, _ = n_eff(x)
        cell["H2_all_days"] = {"n": int(len(g)), "n_eff": ne, "per_quintile_n": int(len(g) // 5),
                               "se_corr": 1 / math.sqrt(ne), "mde_corr_t2": 2 / math.sqrt(ne)}
        out["cells"][tau] = cell
    return out


def md(res: dict) -> str:
    L = ["# LETF close-flow: the POWER step (D639 s.9)", "",
         "*Generated by `scripts/power_letf.py`, before any runner. It reads the signal's inputs and the unsigned "
         "dispersion of the tau -> close move only; nothing about the move's relation to the flow.*", "",
         "| instrument | tau | k | active days | share | n_eff | sigma (bp) | MDE t=2 (bp) | MDE Holm 80% (bp) | "
         "mean cost (bp) | verdict (D639: vs cost) | active 2024+ | model's own predicted impact (bp; context) |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|"]
    for root in ("NQ", "ES"):
        for tau, cell in res[root]["cells"].items():
            for k in KS:
                c = cell[f"k{k}"]
                if "n_eff" not in c:
                    L.append(f"| {root} | {tau} | {k} | {c['n']} | | | | | | | {c['note']} | |")
                    continue
                v = "UNDERPOWERED" if c["underpowered_t2"] else ("powered (t=2); not at Holm 80%" if c["underpowered_holm80"]
                                                                   else "powered")
                mark = " **(primary)**" if (k == 3 and tau != H4_TAU) else (" (H4 placebo)" if tau == H4_TAU and k == 3 else "")
                L.append(f"| {root} | {tau}{mark} | {k} | {c['n']} | {c['active_share']:.1%} | {c['n_eff']:.0f} | "
                         f"{c['sigma_move_bp']:.1f} | {c['mde_t2_bp']:.2f} | {c['mde_holm80_bp']:.2f} | "
                         f"{c['mean_cost_bp']:.2f} | {v} | {c['n_2024_plus']} | {c['mean_predicted_impact_bp']:.2f} |")
    L += ["", "H2 (all days, |q| quintiles): " + "; ".join(
        f"{root} {tau}: n {res[root]['cells'][tau]['H2_all_days']['n']}, MDE corr {res[root]['cells'][tau]['H2_all_days']['mde_corr_t2']:.3f}"
        for root in ("NQ", "ES") for tau in TAUS), ""]
    return "\n".join(L) + "\n"


def main() -> int:
    res = {root: build_root(root) for root in ("NQ", "ES")}
    res["spec"] = "D639 (e95c0a9) s.9"
    res["rt_cost_points"] = RT_POINTS
    OUT_JSON.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    OUT_MD.write_text(md(res), encoding="utf-8", newline="\n")
    print(md(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
