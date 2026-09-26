"""D631: Stage B of the settlement flow ledger on NG. The deposit's update step (§5.2) on P1, fitted in walk-forward
windows (§8, §10) and judged by the retention rule out of sample (§6).

The specification is `docs/decisions/D631-PRE-REG-stage-b-the-update-step-on-ng.md` (committed 673367c before this
file existed). At each τ ∈ {13:50, 14:00, 14:10}:
    K = p σ² / (p² σ² + R);  Q_hat = μ + K (z − p μ);  σ²_post = (1 − K p) σ²;  Q_rem = (1 − p) Q_hat;
    σ_rem = (1 − p) √σ²_post
with μ = P1 (`q_est`), σ² = `sigma_Q`², and z = the abnormal signed flow 13:30 → τ over the covered held contracts,
residualised on [1, r(τ), flags] with training-window coefficients. p = 0 is Stage A exactly.
RETAINED only if, out of sample: (1) Stage B's partial correlation with the window flow (net of [1, r to 14:28,
flags]) is ≥ 1.10 × Stage A's, with Stage A's > 0; and (2) H2's t over Stage B's trades is not below Stage A's.

Stage A's predictor and dependent are D629's (`run_signed_h1_stage_a.build`); the price machinery is D630's
(`run_h2_ng_stage_a`); the pre-τ flow is `build_signed_pre_tau_panel.py`'s.

    uv run python -W error::RuntimeWarning scripts/run_stage_b_ng.py --selftest | --run | --check
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "decisions" / "D631-PRE-REG-stage-b-the-update-step-on-ng.md"
PRETAU = REPO / "data" / "ledger_signed_pretau_daily.csv.gz"
OUT = REPO / "data" / "ledger_stage_b_ng.json"
T0 = ("13:50", "14:00", "14:10")
TRAIN, TEST = 252, 63
P_GRID = (0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9)
KAPPA = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0)
REQUIRED_OUTPUTS = ("verdict", "clause_flow", "clause_price", "params", "n_oos", "known_answer", "placebo",
                    "raw_z", "full_sample_fit", "error_budget", "h2_oos", "excluded")


class StageBError(RuntimeError):
    pass


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S1 = _load("run_signed_h1_stage_a")   # D629: Stage A's Q and the window flow S
R2 = _load("run_h2_ng_stage_a")       # D630: bars, fills, money
P = S1.P                               # POWER's business days and abnormal sums
H = S1.H                               # D627's audits
FLAGS = S1.FLAGS["NG"]


# ------------------------------------------------------------------ the update step
def kalman(mu: np.ndarray, s2: np.ndarray, z: np.ndarray, p: float, R: float) -> tuple[np.ndarray, np.ndarray]:
    """(Q_rem, σ_rem), deposit lines 380–384. p = 0 returns (μ, σ) exactly."""
    if p == 0.0:
        return mu.copy(), np.sqrt(s2)
    K = p * s2 / (p * p * s2 + R)
    q_hat = mu + K * (z - p * mu)
    return (1.0 - p) * q_hat, (1.0 - p) * np.sqrt((1.0 - K * p) * s2)


def audit_kalman() -> None:
    """Deposit unit test 6's hand case, and no news (z = pμ) leaves Q_rem = (1 − p) μ, with μ's sign."""
    q, s = kalman(np.array([100.0]), np.array([400.0]), np.array([60.0]), 0.5, 100.0)
    if not (math.isclose(q[0], 55.0) and math.isclose(s[0], math.sqrt(50.0))):
        raise StageBError(f"the update step fails the deposit's hand case: {q[0]}, {s[0]}")
    mu = np.array([-120.0, 80.0])
    q, _ = kalman(mu, np.array([900.0, 900.0]), 0.3 * mu, 0.3, 50.0)
    if not np.allclose(q, 0.7 * mu):
        raise StageBError("sign audit: with no news the update moved Q_rem off (1 − p) μ")


def resid(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]


def pcorr(a: np.ndarray, b: np.ndarray, X: np.ndarray) -> float:
    ra, rb = resid(a, X), resid(b, X)
    den = float(np.sqrt((ra @ ra) * (rb @ rb)))
    return float(ra @ rb / den) if den > 0 else float("nan")


# ------------------------------------------------------------------ data
def build(read_signed: bool) -> dict[str, Any]:
    b = S1.build("NG", read_dependent=read_signed)  # D627's lag audit and D629's coverage audit run inside
    d = b["d"].sort_values("day").reset_index(drop=True)
    flow = b["flow"]
    days = b["days"]
    pos = {x: i for i, x in enumerate(days)}
    by_tau = {t: g.set_index("day") for t, g in flow.groupby("tau")}
    for t in T0 + ("11:30",):
        f = by_tau[t].reindex(d["day"])
        k = t.replace(":", "")
        for col in ("q_est", "sigma_Q", "r_held", "I", "snr", "gate_pass", "traded_ym", "sigma_d", "V_d", "p_held",
                    "rt_cost"):
            d[f"{col}_{k}"] = f[col].to_numpy()
    d["tau_star_a"] = d["tau"]
    excluded = {"no_prior_variance": sorted(d.loc[d[[f"sigma_Q_{t.replace(':', '')}" for t in T0]].isna().any(axis=1),
                                                  "day"])}
    d = d.dropna(subset=[f"sigma_Q_{t.replace(':', '')}" for t in T0]).reset_index(drop=True)
    out: dict[str, Any] = {"d": d, "days": days, "excluded": excluded, "flow": flow}
    if not read_signed:
        return out
    pt = pd.read_csv(PRETAU, encoding="utf-8")
    pt = pt[pt["day"] < P.CUT]
    piv = {c: pt.pivot_table(index="day", columns="ym", values=c, aggfunc="sum").reindex(days).fillna(0.0)
           for c in ("net_pre_1350", "net_pre_1400", "net_pre_1410", "net_plcpre_1130")}
    for c, tab in piv.items():
        k = c.split("_")[-1]
        vals = []
        for day, cov in zip(d["day"], d["covered"]):
            now, tr = P.abnormal(tab, days, pos[day], cov.split(";"))
            vals.append(now - tr)
        d[f"z_{k}"] = vals
    # H2 moves at each τ, on that τ's traded contract (D630's fill and exit)
    bars = pd.read_csv(R2.BARS, encoding="utf-8", usecols=["day", "ym", "minute", "close"])
    groups = {k: (g["minute"].to_numpy(), g["close"].to_numpy())
              for k, g in bars.sort_values(["day", "ym", "minute"]).groupby(["day", "ym"], sort=False)}
    px = pd.read_csv(R2.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "px_1350"])
    px = px[(px["root"] == "NG") & (px["kind"] == "outright")].set_index(["day", "ym"])["px_1350"]
    empty = (np.array([], dtype=object), np.array([]))
    for t in T0:
        k = t.replace(":", "")
        mv = []
        for day, ym in zip(d["day"], d[f"traded_ym_{k}"]):
            mins, cl = groups.get((day, ym), empty)
            s0 = float(px.get((day, ym), np.nan))
            mv.append((R2.asof(mins, cl, R2.EXIT_END, s0) - R2.asof(mins, cl, R2.fill_end(t), s0)) * R2.MULT)
        d[f"m_{k}"] = mv
    out["d"] = d
    return out


# ------------------------------------------------------------------ the gate and the walk-forward
def gate(d: pd.DataFrame, k: str, q_rem: np.ndarray, s_rem: np.ndarray) -> np.ndarray:
    """§7.2 on Stage B's own quantities; −1 where the panel's gate is not evaluable."""
    with np.errstate(divide="ignore", invalid="ignore"):  # the panel's order of operations, term for term
        I_b = 0.7 * d[f"sigma_d_{k}"].to_numpy() * np.sqrt(np.abs(q_rem) / d[f"V_d_{k}"].to_numpy()) * \
            d[f"p_held_{k}"].to_numpy()
        snr = np.abs(q_rem) / s_rem
    ok = (I_b >= 3 * d[f"rt_cost_{k}"].to_numpy()) & (snr >= 1.5)
    return np.where(d[f"gate_pass_{k}"].to_numpy() < 0, -1, ok.astype(int))


def tau_star(gates: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """(index of τ* in T0, signal flag): the earliest pass, else 14:10."""
    G = np.column_stack([gates[t] for t in T0])
    passed = G == 1
    idx = np.where(passed.any(axis=1), passed.argmax(axis=1), len(T0) - 1)
    return idx, passed.any(axis=1)


def known_answer(d: pd.DataFrame) -> dict[str, Any]:
    """At p = 0, Stage B's gate is the panel's at every τ, and τ*_B is the panel's τ*, exactly."""
    gates = {}
    for t in T0:
        k = t.replace(":", "")
        q, s = kalman(d[f"q_est_{k}"].to_numpy(), d[f"sigma_Q_{k}"].to_numpy() ** 2, np.zeros(len(d)), 0.0, 1.0)
        gates[t] = gate(d, k, q, s)
        if not np.array_equal(gates[t], d[f"gate_pass_{k}"].to_numpy().astype(int)):
            bad = int((gates[t] != d[f"gate_pass_{k}"].to_numpy()).sum())
            raise StageBError(f"known answer: at p = 0 the gate differs from the panel's at {t} on {bad} days")
    idx, _sig = tau_star(gates)
    mine = np.array(T0)[idx]
    if not np.array_equal(mine, d["tau_star_a"].to_numpy()):
        raise StageBError("known answer: at p = 0, τ*_B differs from the panel's τ*")
    return {"gate_equal_at_every_tau": True, "tau_star_equal": True, "days": int(len(d))}


def fit_window(mu: np.ndarray, s2: np.ndarray, z: np.ndarray, s: np.ndarray, X: np.ndarray) -> tuple[float, float, float]:
    rs = resid(s, X)
    zv = float(np.var(z))
    best, arg = -np.inf, (0.0, 1.0)
    for p in P_GRID:
        for kap in (KAPPA if p > 0 else (1.0,)):
            q, _ = kalman(mu, s2, z, p, kap * zv)
            rq = resid(q, X)
            den = float(np.sqrt((rq @ rq) * (rs @ rs)))
            c = float(rq @ rs / den) if den > 0 else -np.inf
            if c > best:
                best, arg = c, (p, kap)
    return arg[0], arg[1] * zv, best


def walk_forward(d: pd.DataFrame, z_cols: dict[str, str], s_col: str, dep_ctrl: np.ndarray, residualise: bool,
                 taus: tuple[str, ...] = T0) -> dict[str, Any]:
    n = len(d)
    days = d["day"].to_numpy()
    if not (days[1:] > days[:-1]).all():
        raise StageBError("rows are not in strictly increasing date order")
    fl = [d[f].to_numpy(float) for f in FLAGS]
    s = d[s_col].to_numpy(float)
    q_rem = {t: np.full(n, np.nan) for t in taus}
    s_rem = {t: np.full(n, np.nan) for t in taus}
    paths: dict[str, list[dict[str, Any]]] = {t: [] for t in taus}
    start = TRAIN
    while start < n:
        tr, te = np.arange(start - TRAIN, start), np.arange(start, min(start + TEST, n))
        if not days[tr].max() < days[te].min():
            raise StageBError("walk-forward audit: a training row is not before its test block")
        for t in taus:
            k = t.replace(":", "")
            mu, s2 = d[f"q_est_{k}"].to_numpy(), d[f"sigma_Q_{k}"].to_numpy() ** 2
            z = d[z_cols[t]].to_numpy(float)
            if residualise:
                Cz = np.column_stack([np.ones(n), d[f"r_held_{k}"].to_numpy()] + fl)
                z = z - Cz @ np.linalg.lstsq(Cz[tr], z[tr], rcond=None)[0]
            p, R, c = fit_window(mu[tr], s2[tr], z[tr], s[tr], dep_ctrl[tr])
            # D631's amendment: put Q_rem on P1's scale with the training window's SDs (λ = 1 exactly at p = 0)
            q_tr, _s_tr = kalman(mu[tr], s2[tr], z[tr], p, R)
            sd_q = float(np.std(q_tr))
            lam = float(np.std(mu[tr])) / sd_q if p > 0 and sd_q > 0 else 1.0
            paths[t].append({"train_last": str(days[tr][-1]), "test_first": str(days[te][0]), "p": p, "R": R,
                             "lambda": lam, "train_pcorr": c})
            q, sr = kalman(mu[te], s2[te], z[te], p, R)
            q_rem[t][te], s_rem[t][te] = lam * q, lam * sr
        start += TEST
    return {"q_rem": q_rem, "s_rem": s_rem, "paths": paths, "oos": np.isfinite(q_rem[taus[0]])}


def mean_t(x: np.ndarray) -> dict[str, float]:
    return R2.mean_t(x)


def analyse(d: pd.DataFrame, excluded: dict[str, list[str]], check_known: bool = True) -> dict[str, Any]:
    ka = known_answer(d) if check_known else {"skipped": "synthetic data"}
    n = len(d)
    fl = [d[f].to_numpy(float) for f in FLAGS]
    dep_ctrl = np.column_stack([np.ones(n), d["r"].to_numpy()] + fl)  # D629's controls: r to 14:28 and the flags
    # the residualisation must read r(τ), never r to 14:28
    for t in T0:
        if np.allclose(d[f"r_held_{t.replace(':', '')}"].to_numpy(), d["r"].to_numpy()):
            raise StageBError(f"lag audit: r({t}) equals r to 14:28")
    if np.allclose(d["z_1350"].to_numpy(float), d["z_1410"].to_numpy(float)):
        raise StageBError("right-quantity: z(13:50) equals z(14:10)")
    zc = {t: f"z_{t.replace(':', '')}" for t in T0}
    wf = walk_forward(d, zc, "S", dep_ctrl, residualise=True)
    oos = wf["oos"]
    gates = {t: gate(d, t.replace(":", ""), np.nan_to_num(wf["q_rem"][t]), np.nan_to_num(wf["s_rem"][t])) for t in T0}
    idx, sig_b = tau_star(gates)
    q_b = np.column_stack([wf["q_rem"][t] for t in T0])[np.arange(n), idx]
    Xo = dep_ctrl[oos]
    s = d["S"].to_numpy(float)
    rho_a, rho_b = pcorr(d["Q"].to_numpy()[oos], s[oos], Xo), pcorr(q_b[oos], s[oos], Xo)
    clause_flow = {"rho_a": rho_a, "rho_b": rho_b, "ratio": rho_b / rho_a if rho_a else float("nan"),
                   "pass": bool(rho_a > 0 and rho_b >= 1.10 * rho_a)}
    # clause 2: H2 over each stage's trades, on the OOS days
    M = np.column_stack([d[f"m_{t.replace(':', '')}"].to_numpy(float) for t in T0])
    idx_a = d["tau_star_a"].map({t: i for i, t in enumerate(T0)}).to_numpy()
    sig_a = d["signal_day"].to_numpy() == 1
    g_a = np.sign(d["Q"].to_numpy()) * M[np.arange(n), idx_a]
    g_b = np.sign(q_b) * M[np.arange(n), idx]
    ta, tb = oos & sig_a & np.isfinite(g_a), oos & sig_b & np.isfinite(g_b)
    ha, hb = mean_t(g_a[ta]), mean_t(g_b[tb])
    clause_price = {"stage_a": ha, "stage_b": hb, "pass": bool(hb["t"] >= ha["t"]),
                    "traded_days_a": int(ta.sum()), "traded_days_b": int(tb.sum()),
                    "overlap_share_of_b": float((ta & tb).sum() / max(1, tb.sum()))}
    verdict = "RETAINED" if clause_flow["pass"] and clause_price["pass"] else "NOT RETAINED (inconclusive)"
    params = {t: {"p_median": float(np.median([w["p"] for w in wf["paths"][t]])),
                  "share_windows_p_zero": float(np.mean([w["p"] == 0 for w in wf["paths"][t]])),
                  "windows": wf["paths"][t]} for t in T0}
    # beside: the deposit's raw z, the placebo, the full-sample fit, the error budget, H2's four groups
    wr = walk_forward(d, zc, "S", dep_ctrl, residualise=False)
    gr = {t: gate(d, t.replace(":", ""), np.nan_to_num(wr["q_rem"][t]), np.nan_to_num(wr["s_rem"][t])) for t in T0}
    ir, _sr = tau_star(gr)
    qr = np.column_stack([wr["q_rem"][t] for t in T0])[np.arange(n), ir]
    raw = {"rho_a": rho_a, "rho_b": pcorr(qr[oos], s[oos], Xo)}
    raw["retained_clause_flow"] = bool(rho_a > 0 and raw["rho_b"] >= 1.10 * rho_a)
    pm = (d["plc_clean"].to_numpy() & np.isfinite(d["S_plc"].to_numpy(float)) & np.isfinite(d["z_1130"].to_numpy(float))
          & np.isfinite(d["sigma_Q_1130"].to_numpy(float)) & np.isfinite(d["q_est_1130"].to_numpy(float)))
    dp = d[pm].reset_index(drop=True)
    cp = np.column_stack([np.ones(len(dp)), dp["r_held_1130"].to_numpy()] + [dp[f].to_numpy(float) for f in FLAGS])
    wp = walk_forward(dp, {"11:30": "z_1130"}, "S_plc", cp, residualise=True, taus=("11:30",))
    op = wp["oos"]
    plc = {"rho_a": pcorr(dp["q_est_1130"].to_numpy()[op], dp["S_plc"].to_numpy(float)[op], cp[op]),
           "rho_b": pcorr(wp["q_rem"]["11:30"][op], dp["S_plc"].to_numpy(float)[op], cp[op]), "n_oos": int(op.sum())}
    plc["retains_like_the_rule"] = bool(plc["rho_a"] > 0 and plc["rho_b"] >= 1.10 * plc["rho_a"])
    full = {}
    for t in T0:
        k = t.replace(":", "")
        z = d[zc[t]].to_numpy(float)
        Cz = np.column_stack([np.ones(n), d[f"r_held_{k}"].to_numpy()] + fl)
        z = resid(z, Cz)
        p, R, c = fit_window(d[f"q_est_{k}"].to_numpy(), d[f"sigma_Q_{k}"].to_numpy() ** 2, z, s, dep_ctrl)
        full[t] = {"p": p, "R": R, "pcorr_b": c, "pcorr_a": pcorr(d[f"q_est_{k}"].to_numpy(), s, dep_ctrl)}
    eb = {}
    for name, q in (("stage_a", d["Q"].to_numpy()), ("stage_b", q_b)):
        X = np.column_stack([Xo, q[oos]])
        eb[name] = float(np.mean(resid(s[oos], X) ** 2))
    C = R2._load_cs()

    def groups(g: np.ndarray, m: np.ndarray) -> dict[str, Any]:
        daily = np.where(m, g - R2.COST, 0.0)[oos]
        dailyg = np.where(m, g, 0.0)[oos]
        return {"mean_gross": float(g[m].mean()), "mean_net": float(g[m].mean() - R2.COST),
                "sharpe_net": C.sharpe(daily), "sortino_net": C.sortino(daily), "sharpe_gross": C.sharpe(dailyg),
                "sortino_gross": C.sortino(dailyg), "distribution": R2.distribution(g[m])}
    h2 = {"stage_a": groups(g_a, ta), "stage_b": groups(g_b, tb)}
    return {"verdict": verdict, "clause_flow": clause_flow, "clause_price": clause_price, "params": params,
            "n_oos": int(oos.sum()), "known_answer": ka, "placebo": plc, "raw_z": raw, "full_sample_fit": full,
            "error_budget": eb, "h2_oos": h2, "excluded": {k: {"n": len(v), "days": v} for k, v in excluded.items()},
            "first_oos_day": str(d["day"].to_numpy()[oos][0])}


def run() -> dict[str, Any]:
    b = build(read_signed=True)
    r = analyse(b["d"], b["excluded"])
    missing = [k for k in REQUIRED_OUTPUTS if k not in r]
    if missing:
        raise StageBError(f"REQUIRED_OUTPUTS missing {missing}")
    ins = (P.FLOW, P.CONTRACTS, P.SIGNED, PRETAU, P.CAL, R2.BARS, R2.PANEL)
    return {"spec": {"record": SPEC.name, "sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()},
            "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ins}, "deviations": [], "NG": r}


# ------------------------------------------------------------------ selftest (no in-sample signed row)
def synthetic(d: pd.DataFrame, informative: bool, rng: np.random.Generator) -> pd.DataFrame:
    """A world with a weak prior and an informative z must be RETAINED; pure-noise z must not."""
    s = d.copy()
    n = len(s)
    # a stationary scale: the real P1 path is tiny in 2017-18, which leaves early training windows without signal
    q_true = rng.standard_normal(n) * 1000.0
    err = rng.standard_normal(n) * 2.0 * np.std(q_true)
    for t in T0:
        k = t.replace(":", "")
        s[f"q_est_{k}"] = q_true + err if informative else q_true
        s[f"sigma_Q_{k}"] = 2.0 * np.std(q_true) if informative else 0.2 * np.std(q_true)
        noise = rng.standard_normal(n) * 0.05 * np.std(q_true)
        s[f"z_{k}"] = (0.4 * q_true + noise) if informative else rng.standard_normal(n) * np.std(q_true)
        s[f"m_{k}"] = 30.0 * np.sign(q_true) + rng.standard_normal(n) * 50.0
    s["Q"] = s["q_est_1350"]
    s["S"] = 0.2 * q_true + rng.standard_normal(n) * 0.2 * np.std(q_true)
    s["z_1130"] = rng.standard_normal(n)
    s["S_plc"] = rng.standard_normal(n)
    return s


def selftest() -> int:
    audit_kalman()
    # the hand case can tell a broken update from the right one: K without p² in its denominator gives 54, not 55
    K_broken = 0.5 * 400.0 / (400.0 + 100.0)
    if math.isclose((1 - 0.5) * (100.0 + K_broken * (60.0 - 50.0)), 55.0):
        raise StageBError("the hand case cannot tell a broken update from the right one")
    print("  the update step: the deposit's hand case (K = 1, Q_hat = 110, Q_rem = 55, sigma_rem = sqrt 50); "
          "no news keeps mu's sign")
    R2.audit_money()
    print("  D630's money audit passes")
    b = build(read_signed=False)
    d = b["d"]
    print(f"  known answer on the real panel: {known_answer(d)}")
    broken = d.copy()
    broken["gate_pass_1350"] = np.where(broken["gate_pass_1350"] == 1, 0, broken["gate_pass_1350"])
    try:
        known_answer(broken)
    except StageBError:
        print("  the known answer RAISES when the panel's gate is altered")
    else:
        raise StageBError("the known answer did not fire on an altered gate")
    rng = np.random.default_rng(631)
    res = {}
    for informative in (True, False):
        syn = synthetic(d, informative, rng)
        r = analyse(syn, b["excluded"], check_known=False)
        missing = [k for k in REQUIRED_OUTPUTS if k not in r]
        if missing:
            raise StageBError(f"synthetic analyse is missing {missing}")
        res[informative] = (r["verdict"], round(r["clause_flow"]["ratio"], 3))
    if res[True][0] != "RETAINED" or res[False][0] == "RETAINED":
        raise StageBError(f"selftest verdicts {res}")
    print(f"  analyse() end to end: informative z -> {res[True]}; noise z -> {res[False]}")
    shuffled = synthetic(d, True, np.random.default_rng(1)).sample(frac=1.0, random_state=3).reset_index(drop=True)
    try:
        walk_forward(shuffled, {t: f"z_{t.replace(':', '')}" for t in T0}, "S",
                     np.ones((len(shuffled), 1)), residualise=False)
    except StageBError:
        print("  the walk-forward audit RAISES on rows out of date order")
    else:
        raise StageBError("the walk-forward audit did not fire")
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
        raise StageBError(f"{OUT.name} exists: Stage B has been run once (D631). Use --check to recompute.")
    res = run()
    text = json.dumps(res, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise StageBError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    r = res["NG"]
    cf, cp = r["clause_flow"], r["clause_price"]
    print(f"NG Stage B: {r['verdict']}  n_oos {r['n_oos']}  flow rho A {cf['rho_a']:.4f} B {cf['rho_b']:.4f} "
          f"(x{cf['ratio']:.3f})  H2 t A {cp['stage_a']['t']:.2f} B {cp['stage_b']['t']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
