"""D627's runner: Stage A, H1a. Does the leveraged funds' predicted rebalance SIZE show up as extra settlement-window
volume? (settlement ledger A8, A9; docs/decisions/D627-PRE-REG-h1a-rebalance-size-and-window-volume.md, committed
505d83b before this file existed).

Every definition here is D627's, and the section numbers below are D627's.

§2 THE REGRESSION, per root (CL, NG). OLS with HC1 standard errors:
    A_t = α + β |Q_t| + γ1 |r_t| + γ2 P_t + Σ δ_k F_k,t + ε_t
  * A_t: window volume (14:28–14:30) summed over the held contracts H_t, minus the mean over the business days
    t-20 … t-1 of the same sum over the same contracts. A contract with no row on a day traded 0.
  * |Q_t|: |q_est| at τ*.
  * |r_t|: |r_held| at τ = 14:28.
  * P_t: 13:30–14:28 volume on H_t, abnormal in the same way.
  * F: the calendar flags.

§3 THE FUTURES SHARE. A4's imputation: M = 50, seed 20260924. On each path, each estimated segment (anchor_prev →
anchor_next, from `ledger_fut_share_daily_a6.csv.gz`) of each fund draws one e ~ N(0, σ_q²), and
f = clip(f_est + e, 0, 1). σ_q is the panel's own. Proven days (σ_q = 0) are not drawn. The paths combine by Rubin's
rules. §3 draws the estimated days of BOTH roots (NG has BOIL 2023 and the carried 2025 days), so the gate reads
Rubin's t on both roots. The f_est reading's t is reported beside it. This interpretation is fixed here, in the
runner committed before the run.

§4 CONTROLS.
  * C1, the time placebo: A^plc on 11:50–12:20 volume, |Q| and |r| at 11:30, P^plc on 10:52–11:50, the same flags.
    It is fitted on the main sample's days that have a clean 11:30 row.
  * C2, the rotation null, on the f_est reading. |Q| is residualised on the controls; the residual is rotated within
    each calendar year by an offset drawn uniformly from [20, n_year − 20] (a year with n_year ≤ 40 is not rotated)
    and added back to the fitted part. 1,000 rotations, seed 627, HC1 each time. The p95's bootstrap SE comes from
    1,000 resamples of the rotation t's.

§5–§6 THE VERDICT, per root:
  * FAIL: Rubin β̄ ≤ 0 or Rubin t < 2.
  * Otherwise UNRESOLVED (control): the placebo has |t| ≥ 2, or t_est ≤ the rotation p95.
  * Otherwise UNRESOLVED (margin): t_est − p95 ≤ 2 × SE(p95).
  * Otherwise PASS.
  The premise is killed only if both roots FAIL.

§7 REPORTED BESIDE: Newey-West t (5 lags) for the main fit and C1; A3's four f readings; TAS volume; the
largest-share contract alone; τ fixed at 14:10; τ* re-derived on the micro cost line; splits by year, CL era,
signal day and roll day; β̂ against the plausible 0.25.

§8 ASSERTIONS (each raises):
  * lag: every NAV/f date is before t; q_est is re-derived from q1 × f; τ* is re-derived from gate_pass.
  * sign: q1 has the sign of r for both funds.
  * right quantity: A_t differs from the placebo's A and from the raw level.
  * REQUIRED_OUTPUTS: the output is written only when every declared key is present.

    uv run python -W error::RuntimeWarning scripts/run_h1a_stage_a.py --selftest   # no in-sample window volume
    uv run python -W error::RuntimeWarning scripts/run_h1a_stage_a.py --run        # the ONE run; refuses a second
    uv run python -W error::RuntimeWarning scripts/run_h1a_stage_a.py --check      # recompute and compare
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FLOW = REPO / "data" / "ledger_predicted_flow_daily.csv.gz"
PANEL = REPO / "data" / "ledger_window_volume_daily.csv.gz"
CAL = REPO / "data" / "ledger_calendar_flags.csv"
FSHARE = REPO / "data" / "ledger_fut_share_daily_a6.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
SPEC = REPO / "docs" / "decisions" / "D627-PRE-REG-h1a-rebalance-size-and-window-volume.md"
OUT = REPO / "data" / "ledger_h1a_stage_a.json"
CUT, TRANSITION, SWITCH = "2025-03-01", ("2020-04-01", "2020-09-16"), "2020-09-17"
N_TRAIL = 20
M_PATHS, MI_SEED = 50, 20260924
N_ROT, ROT_SEED, ROT_MIN = 1000, 627, 20
N_BOOT = 1000
NW_LAGS = 5
CANDIDATES = ("13:50", "14:00", "14:10")
PLAUSIBLE_BETA = 0.25
FUNDS = {"CL": ("UCO", "SCO"), "NG": ("BOIL", "KOLD")}  # (long, inverse)
FLAGS = {"CL": ["index_roll_close", "fund_roll", "expiry", "eia_report", "index_annual_roll", "index_reset"],
         "NG": ["index_roll_close", "fund_roll", "expiry", "eia_report", "ng_spot_last3"]}
REQUIRED_OUTPUTS = ("verdict", "n", "excluded", "main", "placebo", "rotation", "readings", "beside")


class H1aError(RuntimeError):
    pass


def _sm() -> Any:
    import statsmodels.api as sm  # type: ignore[import-untyped]
    return sm


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ estimation
def hc1(y: np.ndarray, X: np.ndarray, j: int = 1) -> tuple[float, float]:
    """(β_j, var_j) under HC1."""
    xtx_inv = np.linalg.inv(X.T @ X)
    b = xtx_inv @ (X.T @ y)
    e = y - X @ b
    n, k = X.shape
    cov = xtx_inv @ ((X * (e * e)[:, None]).T @ X) @ xtx_inv * n / (n - k)
    return float(b[j]), float(cov[j, j])


def fit(y: np.ndarray, X: np.ndarray) -> dict[str, float]:
    """The main statistics for column 1 (|Q|): β, the HC1 t, and the Newey-West t (5 lags) via statsmodels."""
    sm = _sm()
    # a control that is constant in this sample (a flag that never fires in a year or an era) carries no information
    # and makes X'X singular: drop it and say so. The constant (0) and |Q| (1) are never dropped.
    keep = [0, 1] + [j for j in range(2, X.shape[1]) if np.ptp(X[:, j]) > 0]
    dropped = X.shape[1] - len(keep)
    X = X[:, keep]
    b, v = hc1(y, X)
    m = sm.OLS(y, X).fit(cov_type="HC1")
    if not np.isclose(m.tvalues[1], b / np.sqrt(v), rtol=1e-9, atol=0):
        raise H1aError(f"HC1 mismatch: statsmodels {m.tvalues[1]!r} against {b / np.sqrt(v)!r}")
    nw = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAGS})
    return {"beta": b, "se_hc1": float(np.sqrt(v)), "t_hc1": b / float(np.sqrt(v)), "t_nw5": float(nw.tvalues[1]),
            "n": int(len(y)), "k": int(X.shape[1]), "constant_controls_dropped": dropped}


def rubin(betas: np.ndarray, variances: np.ndarray) -> dict[str, float]:
    m = len(betas)
    bbar, ubar = float(betas.mean()), float(variances.mean())
    B = float(betas.var(ddof=1)) if m > 1 else 0.0
    T = ubar + (1 + 1 / m) * B
    r = (1 + 1 / m) * B / ubar if ubar > 0 else float("inf")
    df = (m - 1) * (1 + 1 / r) ** 2 if r > 0 else float("inf")
    return {"beta": bbar, "t": bbar / float(np.sqrt(T)), "U": ubar, "B": B, "T": T, "df": df, "paths": m}


def rotation(y: np.ndarray, X: np.ndarray, years: np.ndarray, rng: np.random.Generator,
             residualise: bool = True) -> np.ndarray:
    """C2 (A9): the HC1 t of |Q| over N_ROT within-year rotations of its residual on the controls."""
    Z = np.delete(X, 1, axis=1)
    q = X[:, 1]
    if residualise:
        coef, *_ = np.linalg.lstsq(Z, q, rcond=None)
        fitted = Z @ coef
    else:
        fitted = np.zeros_like(q)
    resid = q - fitted
    idx_by_year = [np.flatnonzero(years == yv) for yv in np.unique(years)]
    Xr = X.copy()
    ts = np.empty(N_ROT)
    for i in range(N_ROT):
        rq = resid.copy()
        for idx in idx_by_year:
            if len(idx) > 2 * ROT_MIN:
                rq[idx] = np.roll(resid[idx], int(rng.integers(ROT_MIN, len(idx) - ROT_MIN + 1)))
        Xr[:, 1] = fitted + rq
        b, v = hc1(y, Xr)
        ts[i] = b / np.sqrt(v)
    return ts


def p95_with_se(ts: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    boots = np.array([np.quantile(rng.choice(ts, size=len(ts), replace=True), 0.95) for _ in range(N_BOOT)])
    return float(np.quantile(ts, 0.5)), float(np.quantile(ts, 0.95)), float(boots.std(ddof=1))


def verdict(beta_gate: float, t_gate: float, t_plc: float, t_est: float, p95: float, p95_se: float) -> str:
    if not (beta_gate > 0 and t_gate >= 2):
        return "FAIL"
    if abs(t_plc) >= 2 or t_est <= p95:
        return "UNRESOLVED (control)"
    if t_est - p95 <= 2 * p95_se:
        return "UNRESOLVED (margin)"
    return "PASS"


# ------------------------------------------------------------------ data
def _abnormal(piv: pd.DataFrame, days: list[str], helds: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """(sum over H_t on t, mean over t-20..t-1 of the sum over the same H_t). piv: business day × contract, 0-filled."""
    trail = piv.rolling(N_TRAIL, min_periods=N_TRAIL).mean().shift(1)
    now, tr = [], []
    for d, h in zip(days, helds):
        keys = h.split(";")
        now.append(float(piv.loc[d].reindex(keys, fill_value=0.0).sum()))
        t = trail.loc[d].reindex(keys, fill_value=0.0)
        tr.append(float(t.sum()) if t.notna().all() else np.nan)
    return np.array(now), np.array(tr)


def load_flow(root: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = pd.read_csv(FLOW, encoding="utf-8")
    f = f[f["root"] == root]
    if (f["day"] >= CUT).any():
        raise H1aError("a flow row on or after the cut is in memory")
    audit_flow(f)
    return f, f[f["is_tau_star"] == 1].copy()


def audit_flow(f: pd.DataFrame) -> None:
    """The lag and sign audits on the predictor panel (§8). The selftest breaks each input it reads and checks it raises."""
    # lag audit (i): every NAV / f date strictly before t
    for s in ("long", "inverse"):
        if not (f[f"navdate_{s}"] < f["day"]).all():
            raise H1aError(f"lag audit: a {s} NAV/f date is not before its day")
    # lag audit (ii): q_est from q1 x f, never read
    q = f["f_est_long"] * f["q1_long"] + f["f_est_inverse"] * f["q1_inverse"]
    if not np.allclose(q, f["q_est"], rtol=1e-12, atol=1e-9):
        raise H1aError("lag audit: q_est does not re-derive from q1 x f_est")
    # sign audit: both funds buy on a positive return (L(L-1) > 0)
    nz = f["r_held"] != 0
    for s in ("long", "inverse"):
        if (np.sign(f.loc[nz, f"q1_{s}"]) != np.sign(f.loc[nz, "r_held"])).any():
            raise H1aError(f"sign audit: q1_{s} against r")
    # lag audit (iii): τ* re-derived from gate_pass alone
    cand = f[f["tau"].isin(CANDIDATES)].pivot(index="day", columns="tau", values="gate_pass")
    ok = (cand[list(CANDIDATES)] >= 0).all(axis=1)
    mine = {d: next((t for t in CANDIDATES if row[t] == 1), CANDIDATES[-1]) for d, row in cand[ok].iterrows()}
    star = f[f["is_tau_star"] == 1].set_index("day")["tau"].to_dict()
    if mine != star:
        raise H1aError(f"lag audit: τ* re-derived differs on {sum(mine.get(d) != star.get(d) for d in set(mine) | set(star))} days")


def segments(root: str) -> dict[tuple[str, str], tuple[str, str]]:
    """(fund, f date) -> the estimate's segment (anchor_prev, anchor_next), for A4's one-error-per-segment draw."""
    s = pd.read_csv(FSHARE, encoding="utf-8", usecols=["fund", "date", "anchor_prev", "anchor_next"])
    s = s[s["fund"].isin(FUNDS[root])].fillna("")
    return {(fu, d): (a, b) for fu, d, a, b in zip(s["fund"], s["date"], s["anchor_prev"], s["anchor_next"])}


def build(root: str, read_dependent: bool) -> dict[str, Any]:
    flow, star = load_flow(root)
    cal = pd.read_csv(CAL, encoding="utf-8")
    cal = cal[cal["root"] == root].set_index("date")
    bdays = list(cal.index)
    excluded: dict[str, list[str]] = {"no_tau_star": sorted(set(flow["day"]) - set(star["day"]))}
    d = star.copy()
    if root == "CL":
        tr = d["day"].between(*TRANSITION)
        excluded["a1_transition"] = sorted(d.loc[tr, "day"])
        d = d[~tr]
    by_tau = {t: g.set_index("day") for t, g in flow.groupby("tau")}
    d["absr"] = by_tau["14:28"]["r_held"].reindex(d["day"]).abs().to_numpy()
    for fl in FLAGS[root]:
        d[fl] = cal.loc[d["day"], fl].to_numpy()
    cols = ["root", "kind", "day", "ym", "vol_pre", "vol_plc_pre"] + (["vol_win", "vol_plc", "tas_vol"]
                                                                      if read_dependent else [])
    p = pd.read_csv(PANEL, encoding="utf-8", usecols=cols)
    if not read_dependent and "vol_win" in p.columns:
        raise H1aError("the dependent was loaded outside --run")
    p = p[p["root"] == root]
    if (p["day"] >= CUT).any():
        raise H1aError("a panel row on or after the cut is in memory")
    out = p[p["kind"] == "outright"]

    def piv(col: str, frame: pd.DataFrame = out) -> pd.DataFrame:
        return frame.pivot_table(index="day", columns="ym", values=col, aggfunc="sum").reindex(bdays).fillna(0.0)

    days, helds = list(d["day"]), list(d["held"])
    pre_now, pre_tr = _abnormal(piv("vol_pre"), days, helds)
    d["P"] = pre_now - pre_tr
    ppre_now, ppre_tr = _abnormal(piv("vol_plc_pre"), days, helds)
    d["P_plc"] = ppre_now - ppre_tr
    d["absQ"] = d["q_est"].abs()
    d["absQ_plc"] = by_tau["11:30"]["q_est"].reindex(d["day"]).abs().to_numpy()
    d["absr_plc"] = by_tau["11:30"]["r_held"].reindex(d["day"]).abs().to_numpy()
    d["plc_clean"] = (by_tau["11:30"]["n_stale"].reindex(d["day"]) == 0).to_numpy()
    if read_dependent:
        w_now, w_tr = _abnormal(piv("vol_win"), days, helds)
        d["A"], d["win_raw"] = w_now - w_tr, w_now
        pl_now, pl_tr = _abnormal(piv("vol_plc"), days, helds)
        d["A_plc"] = pl_now - pl_tr
        # TAS: the held months' TAS contracts, session open -> 14:30 (A8), abnormal in the same way
        tas = p[p["kind"] == "tas"]
        t_now, t_tr = _abnormal(piv("tas_vol", tas), days, helds)
        d["A_tas"] = t_now - t_tr
        # the largest-share contract alone
        tr_now, tr_tr = _abnormal(piv("vol_win"), days, list(d["traded_ym"]))
        d["A_traded"] = tr_now - tr_tr
    need = ["P", "absr"] + (["A"] if read_dependent else [])
    miss = d[need].isna().any(axis=1)
    excluded["trailing_warm_up_or_missing"] = sorted(d.loc[miss, "day"])
    d = d[~miss].reset_index(drop=True)
    return {"d": d, "excluded": excluded, "flow": flow}


def design_matrix(d: pd.DataFrame, root: str, q: np.ndarray, absr: str = "absr", pre: str = "P") -> np.ndarray:
    cols = [np.ones(len(d)), q, d[absr].to_numpy(float), d[pre].to_numpy(float)] + \
        [d[fl].to_numpy(float) for fl in FLAGS[root]]
    return np.column_stack(cols)


def mi_paths(root: str, d: pd.DataFrame, rng: np.random.Generator) -> list[np.ndarray]:
    """A4: |Q| on each of M paths. One error per (fund, segment); proven days (σ_q = 0) are never drawn."""
    seg = segments(root)
    paths = []
    for _ in range(M_PATHS):
        draws: dict[tuple[str, str, str], float] = {}
        q = np.zeros(len(d))
        for side, fund in zip(("long", "inverse"), FUNDS[root]):
            f = d[f"f_est_{side}"].to_numpy(float).copy()
            sq = d[f"sigma_q_{side}"].to_numpy(float)
            for i, (nd, s) in enumerate(zip(d[f"navdate_{side}"], sq)):
                if s > 0:
                    key = (fund, *seg[(fund, nd)])
                    if key not in draws:
                        draws[key] = float(rng.normal(0.0, s))
                    f[i] = min(max(f[i] + draws[key], 0.0), 1.0)
            q = q + f * d[f"q1_{side}"].to_numpy(float)
        paths.append(np.abs(q))
    return paths


# ------------------------------------------------------------------ the run
def analyse(root: str, d: pd.DataFrame, flow: pd.DataFrame, excluded: dict[str, list[str]]) -> dict[str, Any]:
    y = d["A"].to_numpy(float)
    years = d["day"].str[:4].to_numpy()
    if np.allclose(y, d["A_plc"].to_numpy(float), equal_nan=True) or np.allclose(y, d["win_raw"].to_numpy(float)):
        raise H1aError("right-quantity: A_t equals the placebo's A or the raw level")
    X = design_matrix(d, root, d["absQ"].to_numpy(float))
    est = fit(y, X)
    rng = np.random.default_rng(MI_SEED)
    bs, vs = [], []
    for qp in mi_paths(root, d, rng):
        b, v = hc1(y, design_matrix(d, root, qp))
        bs.append(b)
        vs.append(v)
    rub = rubin(np.array(bs), np.array(vs))
    # C1: the time placebo, on the days with a clean 11:30 row
    dp = d[d["plc_clean"] & d[["A_plc", "P_plc", "absQ_plc", "absr_plc"]].notna().all(axis=1)].reset_index(drop=True)
    plc = fit(dp["A_plc"].to_numpy(float), design_matrix(dp, root, dp["absQ_plc"].to_numpy(float), "absr_plc", "P_plc"))
    # C2: the rotation null on the f_est reading
    rr = np.random.default_rng(ROT_SEED)
    ts = rotation(y, X, years, rr)
    p50, p95, p95_se = p95_with_se(ts, rr)
    verd = verdict(rub["beta"], rub["t"], plc["t_hc1"], est["t_hc1"], p95, p95_se)
    readings = {}
    for rd in ("est", "pit", "lo", "hi"):
        q = (d[f"f_{rd}_long"] * d["q1_long"] + d[f"f_{rd}_inverse"] * d["q1_inverse"]).abs().to_numpy(float)
        readings[rd] = fit(y, design_matrix(d, root, q))
    beside: dict[str, Any] = {}
    beside["tas"] = fit(d["A_tas"].to_numpy(float), X)
    beside["largest_share_contract"] = fit(d["A_traded"].to_numpy(float),
                                           design_matrix(d, root, (d["absQ"] * d["traded_share"]).to_numpy(float)))
    q1410 = flow[flow["tau"] == "14:10"].set_index("day")["q_est"].reindex(d["day"]).abs().to_numpy(float)
    beside["tau_fixed_14:10"] = fit(y, design_matrix(d, root, q1410))
    beside["tau_star_micro"] = micro_tau(root, d, flow, y)
    beside["by_year"] = {yv: fit(y[years == yv], X[years == yv]) for yv in np.unique(years)
                         if (years == yv).sum() > X.shape[1] + 10}
    if root == "CL":
        era_b = (d["day"] >= SWITCH).to_numpy()
        beside["era_a"] = fit(y[~era_b], X[~era_b])
        beside["era_b"] = fit(y[era_b], X[era_b])
    sig = (d["signal_day"] == 1).to_numpy()
    beside["signal_days"] = fit(y[sig], X[sig])
    beside["no_signal_days"] = fit(y[~sig], X[~sig])
    nroll = ((d["index_roll_close"] == 0) & (d["fund_roll"] == 0)).to_numpy()
    Xn = np.delete(X, [3 + FLAGS[root].index("index_roll_close") + 1, 3 + FLAGS[root].index("fund_roll") + 1], axis=1)
    beside["without_roll_days"] = fit(y[nroll], Xn[nroll])
    beside["beta_against_plausible"] = {"beta_rubin": rub["beta"], "plausible": PLAUSIBLE_BETA,
                                        "reading": "contracts of abnormal window volume per contract of predicted P1"}
    beside["newey_west_below_2"] = bool(est["t_nw5"] < 2)
    return {"verdict": verd, "n": int(len(d)), "first": d["day"].iloc[0], "last": d["day"].iloc[-1],
            "excluded": {k: {"n": len(x), "days": x} for k, x in excluded.items()},
            "main": {"rubin": rub, "f_est": est}, "placebo": plc,
            "rotation": {"p50": p50, "p95": p95, "p95_se": p95_se, "t_est": est["t_hc1"],
                         "beats": bool(est["t_hc1"] > p95), "margin": est["t_hc1"] - p95},
            "readings": readings, "beside": beside}


def micro_tau(root: str, d: pd.DataFrame, flow: pd.DataFrame, y: np.ndarray) -> dict[str, Any]:
    """τ* re-derived with the micro cost line (MCL; MNG, hypothetical before 2022), then the main fit on its |Q|."""
    c = json.loads(COSTS.read_text(encoding="utf-8"))["roots"][root]["micro"]
    rt = (float(c["commission_rt_usd"]["value"]) + float(c["crossing_ticks_rt"][c["default_line"]]["value"])
          * float(c["tick_usd"])) / float(c["usd_per_point"])
    g = flow[flow["tau"].isin(CANDIDATES)].copy()
    g["pass_micro"] = (g["gate_pass"] >= 0) & (g["I"].abs() >= 3 * rt) & (g["snr"] >= 1.5)
    piv = g.pivot(index="day", columns="tau", values="pass_micro")
    q = g.pivot(index="day", columns="tau", values="q_est")
    chosen = []
    for day in d["day"]:
        row = piv.loc[day]
        t = next((t for t in CANDIDATES if bool(row[t])), CANDIDATES[-1])
        chosen.append(abs(float(q.loc[day, t])))
    res = fit(y, design_matrix(d, root, np.array(chosen)))
    res["rt_price_units"] = rt
    res["signal_days"] = int(sum(bool(piv.loc[day].any()) for day in d["day"]))
    return res


def run() -> dict[str, Any]:
    out: dict[str, Any] = {"spec": {"record": SPEC.name, "sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()},
                           "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in (FLOW, PANEL, CAL, FSHARE, COSTS)},
                           "cut": CUT, "deviations": [], "roots": {}}
    for root in ("CL", "NG"):
        b = build(root, read_dependent=True)
        r = analyse(root, b["d"], b["flow"], b["excluded"])
        missing = [k for k in REQUIRED_OUTPUTS if k not in r]
        if missing:
            raise H1aError(f"{root}: REQUIRED_OUTPUTS missing {missing}")
        out["roots"][root] = r
    vs = [out["roots"][r]["verdict"] for r in ("CL", "NG")]
    out["premise"] = "KILLED (both roots FAIL)" if all(v == "FAIL" for v in vs) else "not killed"
    return out


# ------------------------------------------------------------------ selftest (no in-sample window volume)
def selftest() -> int:
    P = _load("ledger_power_h1a")
    rng = np.random.default_rng(7)
    # verdict ladder
    assert verdict(-0.1, 3.0, 0.0, 3.0, 1.5, 0.1) == "FAIL"
    assert verdict(0.3, 1.9, 0.0, 3.0, 1.5, 0.1) == "FAIL"
    assert verdict(0.3, 3.0, 2.5, 3.0, 1.5, 0.1) == "UNRESOLVED (control)"
    assert verdict(0.3, 3.0, 0.5, 1.4, 1.5, 0.1) == "UNRESOLVED (control)"
    assert verdict(0.3, 3.0, 0.5, 1.6, 1.5, 0.1) == "UNRESOLVED (margin)"
    assert verdict(0.3, 3.0, 0.5, 3.0, 1.5, 0.1) == "PASS"
    print("  verdict ladder: FAIL / UNRESOLVED (control) / UNRESOLVED (margin) / PASS as D627 §6")
    # Rubin: identical paths give B = 0 and T = U
    rb = rubin(np.array([0.5] * 5), np.array([0.01] * 5))
    assert rb["B"] == 0 and np.isclose(rb["t"], 5.0)
    for root in ("CL", "NG"):
        b = build(root, read_dependent=False)
        d = b["d"]
        ps = P.presample(root)
        expected = ps["k_win_over_pre"] * P.design(root).set_index("day")["pre_trail"].reindex(d["day"]).to_numpy()
        ok = np.isfinite(expected)
        d = d[ok].reset_index(drop=True)
        expected = expected[ok]
        years = d["day"].str[:4].to_numpy()
        X = design_matrix(d, root, d["absQ"].to_numpy(float))
        res = {}
        for beta in (0.5, 0.0):
            y = beta * d["absQ"].to_numpy(float) + expected * P._block(ps["_resid"], len(d), rng)
            yp = expected * P._block(ps["_resid"], len(d), rng)  # the placebo carries no effect
            e = fit(y, X)
            plc = fit(yp, design_matrix(d, root, d["absQ_plc"].fillna(0).to_numpy(float), "absr_plc", "P_plc"))
            ts = rotation(y, X, years, np.random.default_rng(ROT_SEED))
            p50, p95, se = p95_with_se(ts, np.random.default_rng(ROT_SEED))
            res[beta] = verdict(e["beta"], e["t_hc1"], plc["t_hc1"], e["t_hc1"], p95, se)
            if beta == 0.0:
                ts_raw = rotation(y, X, years, np.random.default_rng(ROT_SEED), residualise=False)
                if np.isclose(np.quantile(ts_raw, 0.95), p95):
                    raise H1aError("the rotation's residualising step changed nothing: the check does not read it")
        if res[0.5] != "PASS" or res[0.0] == "PASS":
            raise H1aError(f"{root}: selftest verdicts {res}")
        print(f"  {root}: injected beta 0.5 -> {res[0.5]}; beta 0 -> {res[0.0]} (n {len(d)})")
        # the WHOLE analysis path on synthetic dependents (β = 0.5 in the window, none elsewhere), so the one run
        # cannot be the first time any line of `analyse` executes
        syn = d.copy()
        noise = lambda: expected * P._block(ps["_resid"], len(syn), rng)  # noqa: E731
        syn["A"] = 0.5 * syn["absQ"].to_numpy(float) + noise()
        syn["win_raw"] = syn["A"] + 10 * expected
        syn["A_plc"], syn["A_tas"], syn["A_traded"] = noise(), noise(), noise()
        r = analyse(root, syn, b["flow"], b["excluded"])
        missing = [k for k in REQUIRED_OUTPUTS if k not in r]
        if missing or r["verdict"] != "PASS":
            raise H1aError(f"{root}: synthetic analyse -> {r['verdict']}, missing {missing}")
        print(f"  {root}: analyse() end to end on synthetic data -> {r['verdict']}; Rubin t "
              f"{r['main']['rubin']['t']:.1f}, placebo t {r['placebo']['t_hc1']:.2f}, "
              f"rotation p95 {r['rotation']['p95']:.2f}; every REQUIRED_OUTPUT present")
        # break each input the audits read; audit_flow must raise on every one
        base = b["flow"]
        breaks = {
            "a NAV dated on its own day (AUM[t] for AUM[t-1])":
                lambda f: f.assign(navdate_long=f["day"].where(f.index == f.index[0], f["navdate_long"])),
            "q_est off q1 x f_est": lambda f: f.assign(q_est=f["q_est"] * 1.001),
            "a flipped q1 sign": lambda f: f.assign(q1_inverse=-f["q1_inverse"]),
            "a moved τ*": lambda f: f.assign(is_tau_star=np.where(f["tau"] == "14:28", 1, f["is_tau_star"])),
        }
        audit_flow(base)
        for what, brk in breaks.items():
            try:
                audit_flow(brk(base.copy()))
            except H1aError:
                continue
            raise H1aError(f"the audit did not fire on {what}")
        print(f"  {root}: the lag and sign audits RAISE on each of {len(breaks)} breaks")
    print("selftest: every check passes on its known answer and raises on its break")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run and OUT.exists():
        raise H1aError(f"{OUT.name} exists: H1a has been run once (D627). Use --check to recompute.")
    res = run()
    text = json.dumps(res, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise H1aError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for root, r in res["roots"].items():
        m = r["main"]
        print(f"{root}: {r['verdict']}  n {r['n']}  Rubin beta {m['rubin']['beta']:.4f} t {m['rubin']['t']:.2f} | "
              f"f_est t {m['f_est']['t_hc1']:.2f} NW {m['f_est']['t_nw5']:.2f} | placebo t {r['placebo']['t_hc1']:.2f} | "
              f"rotation p50 {r['rotation']['p50']:.2f} p95 {r['rotation']['p95']:.2f} ± {r['rotation']['p95_se']:.2f}")
    print("premise:", res["premise"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
