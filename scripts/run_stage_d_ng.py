"""D633: Stage D of the settlement flow ledger on NG. P1 plus the TAS imbalance (deposit §P5: Q5 = + TAS_imb[t, τ],
P5/P6 collapsed), judged by the retention rule on all days (no fitted parameter) with D631's midday control.

The specification is `docs/decisions/D633-PRE-REG-stage-d-the-tas-imbalance-on-ng.md` (committed acab2bd before this
file existed). At each τ:
    μ_D(τ) = P1(τ) + Σ_held TAS_imb(τ);   σ²_D(τ) = σ_Q(τ)² + Var_{t−20..t−1}[Σ_held (TAS_imb(14:30) − TAS_imb(τ))]
RETAINED only if: (1) D's partial correlation with the window flow, net of [1, r to 14:28, flags], is ≥ 1.10 × Stage
A's (> 0); (2) H2's t over D's trades is not below Stage A's (D630: 5.01); (3) D's gain at the window exceeds the same
ledger's gain at midday (11:30 against 11:50–12:20).

The data (per-τ panel columns, D629's flows, D630's moves) and the gate and τ* functions are Stage B's
(`run_stage_b_ng`); the TAS imbalance is `build_tas_imbalance_panel.py`'s.

    uv run python -W error::RuntimeWarning scripts/run_stage_d_ng.py --selftest | --run | --check
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
SPEC = REPO / "docs" / "decisions" / "D633-PRE-REG-stage-d-the-tas-imbalance-on-ng.md"
TASP = REPO / "data" / "ledger_tas_imbalance_daily.csv.gz"
D630_OUT = REPO / "data" / "ledger_h2_ng_stage_a.json"
OUT = REPO / "data" / "ledger_stage_d_ng.json"
N_TRAIL = 20
REQUIRED_OUTPUTS = ("verdict", "clause_flow", "clause_price", "clause_midday", "known_answer", "tas_alone",
                    "mechanism_to_1430", "by_source", "fixed_1410", "d629_puzzle", "h2", "error_budget", "n")


class StageDError(RuntimeError):
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


B = _load("run_stage_b_ng")
R2, H, P = B.R2, B.H, B.P
T0 = B.T0
TAUS = T0 + ("11:30",)
FLAGS = B.FLAGS
SWITCH = "2020-02-11"


def k_of(t: str) -> str:
    return t.replace(":", "")


# ------------------------------------------------------------------ audits
def audit_nested(tas: pd.DataFrame) -> None:
    """Cumulative TAS volume from the open cannot fall as τ moves later: to 13:50 ≤ 14:00 ≤ 14:10 ≤ 14:30."""
    v = tas[["v_to_1350", "v_to_1400", "v_to_1410", "v_to_1430"]].to_numpy()
    if (np.diff(v, axis=1) < 0).any():
        raise StageDError("lag audit: a later span holds less TAS volume than an earlier one")
    if tas.duplicated(["day", "ym"]).any():
        raise StageDError("source audit: a (trade date, month) appears twice")


def trailing_var(x: pd.Series) -> pd.Series:
    """The sample variance over the N_TRAIL prior rows; row t never enters its own value."""
    return x.rolling(N_TRAIL, min_periods=N_TRAIL).var().shift(1)


def audit_trailing() -> None:
    s = pd.Series(np.arange(60, dtype=float) ** 1.5)
    base = trailing_var(s)
    s2 = s.copy()
    s2.iloc[40] += 1e6
    moved = trailing_var(s2)
    if base.iloc[40] != moved.iloc[40] or base.iloc[41] == moved.iloc[41]:
        raise StageDError("lag audit: the trailing variance reads its own day, or ignores the day before")


# ------------------------------------------------------------------ data
def build(read_signed: bool) -> dict[str, Any]:
    b = B.build(read_signed=read_signed)
    d = b["d"]
    flow = b["flow"]
    days_all = sorted(flow["day"].unique())
    held_all = flow.drop_duplicates("day").set_index("day")["held"]
    tas = pd.read_csv(TASP, encoding="utf-8")
    if (tas["day"] >= P.CUT).any():
        raise StageDError("a TAS row on or after the cut is in memory")
    audit_nested(tas)
    cols = [f"net_to_{k}" for k in ("1130", "1350", "1400", "1410", "1430")]
    sums = {}
    for c in cols:
        piv = tas.pivot_table(index="day", columns="ym", values=c, aggfunc="sum").reindex(days_all)
        sums[c] = pd.Series([float(piv.loc[x].reindex(held_all[x].split(";")).fillna(0.0).sum()) for x in days_all],
                            index=days_all)
    for t in TAUS:
        k = k_of(t)
        d[f"q5_{k}"] = sums[f"net_to_{k}"].reindex(d["day"]).to_numpy()
        inc = sums["net_to_1430"] - sums[f"net_to_{k}"]
        d[f"v5_{k}"] = trailing_var(inc).reindex(d["day"]).to_numpy()
    d["q5_1430"] = sums["net_to_1430"].reindex(d["day"]).to_numpy()
    return {"d": d, "excluded": b["excluded"]}


# ------------------------------------------------------------------ the Stage D ledger
def ledger(d: pd.DataFrame, t: str, zero: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """(μ_D, σ_D) at τ. With zero=True, Q5 ≡ 0 and its variance 0: Stage A exactly."""
    k = k_of(t)
    q5 = np.zeros(len(d)) if zero else d[f"q5_{k}"].to_numpy(float)
    v5 = np.zeros(len(d)) if zero else d[f"v5_{k}"].to_numpy(float)
    return d[f"q_est_{k}"].to_numpy() + q5, np.sqrt(d[f"sigma_Q_{k}"].to_numpy() ** 2 + v5)


def known_answer(d: pd.DataFrame) -> dict[str, Any]:
    gates = {}
    for t in T0:
        mu, sg = ledger(d, t, zero=True)
        gates[t] = B.gate(d, k_of(t), mu, sg)
        if not np.array_equal(gates[t], d[f"gate_pass_{k_of(t)}"].to_numpy().astype(int)):
            raise StageDError(f"known answer: with Q5 = 0 the gate differs from the panel's at {t}")
    idx, _s = B.tau_star(gates)
    if not np.array_equal(np.array(T0)[idx], d["tau_star_a"].to_numpy()):
        raise StageDError("known answer: with Q5 = 0, τ*_D differs from the panel's τ*")
    return {"gate_equal_at_every_tau": True, "tau_star_equal": True, "days": int(len(d))}


def score(d: pd.DataFrame, check_d630: bool) -> dict[str, Any]:
    n = len(d)
    fl_ = [d[f].to_numpy(float) for f in FLAGS]
    ctrl = np.column_stack([np.ones(n), d["r"].to_numpy()] + fl_)
    mus, sgs, gates = {}, {}, {}
    for t in TAUS:
        mus[t], sgs[t] = ledger(d, t)
    ok = np.isfinite(np.column_stack([mus[t] for t in TAUS] + [sgs[t] for t in TAUS])).all(axis=1)
    for t in T0:
        gates[t] = np.where(ok, B.gate(d, k_of(t), np.nan_to_num(mus[t]), np.nan_to_num(sgs[t])), -1)
    idx, sig = B.tau_star(gates)
    mu_d = np.column_stack([mus[t] for t in T0])[np.arange(n), idx]
    s = d["S"].to_numpy(float)
    rho_a, rho_d = B.pcorr(d["Q"].to_numpy()[ok], s[ok], ctrl[ok]), B.pcorr(mu_d[ok], s[ok], ctrl[ok])
    flow = {"rho_a": rho_a, "rho_d": rho_d, "ratio": rho_d / rho_a, "pass": bool(rho_a > 0 and rho_d >= 1.10 * rho_a),
            "days": int(ok.sum())}
    M = np.column_stack([d[f"m_{k_of(t)}"].to_numpy(float) for t in T0])
    idx_a = d["tau_star_a"].map({t: i for i, t in enumerate(T0)}).to_numpy()
    g_a = np.sign(d["Q"].to_numpy()) * M[np.arange(n), idx_a]
    g_d = np.sign(mu_d) * M[np.arange(n), idx]
    ta_all = (d["signal_day"].to_numpy() == 1) & np.isfinite(g_a)
    if check_d630:  # right-quantity: Stage A's H2 on all days is D630's, exactly
        d630 = json.loads(D630_OUT.read_text(encoding="utf-8"))["NG"]["gate"]
        mine = R2.mean_t(g_a[ta_all])
        if mine["n"] != d630["n"] or not math.isclose(mine["t"], d630["t"], rel_tol=1e-12):
            raise StageDError(f"Stage A's H2 here ({mine}) is not D630's ({d630})")
    ta = ok & ta_all
    tdd = ok & (sig == 1) & np.isfinite(g_d)
    ha, hd = R2.mean_t(g_a[ta]), R2.mean_t(g_d[tdd])
    price = {"stage_a": ha, "stage_d": hd, "pass": bool(hd["t"] >= ha["t"]), "traded_days_a": int(ta.sum()),
             "traded_days_d": int(tdd.sum()), "overlap_share_of_d": float((ta & tdd).sum() / max(1, tdd.sum())),
             "direction_flips_vs_a_on_common_days": float(np.mean(np.sign(mu_d[ta & tdd]) != np.sign(d["Q"].to_numpy()[ta & tdd])))}
    pm = ok & d["plc_clean"].to_numpy() & np.isfinite(d["S_plc"].to_numpy(float)) & \
        np.isfinite(d["q_est_1130"].to_numpy(float))
    cp = np.column_stack([np.ones(n), d["r_held_1130"].to_numpy()] + fl_)[pm]
    sp = d["S_plc"].to_numpy(float)[pm]
    pa, pd_ = B.pcorr(d["q_est_1130"].to_numpy()[pm], sp, cp), B.pcorr(mus["11:30"][pm], sp, cp)
    midday = {"rho_a_midday": pa, "rho_d_midday": pd_, "gain_window": rho_d - rho_a, "gain_midday": pd_ - pa,
              "n_days": int(pm.sum()), "pass": bool((rho_d - rho_a) > (pd_ - pa))}
    return {"flow": flow, "price": price, "midday": midday, "ok": ok, "mu_d": mu_d, "g_a": g_a, "g_d": g_d,
            "ta": ta, "td": tdd, "ctrl": ctrl, "idx": idx, "sig": sig}


def fit_beside(y: np.ndarray, X: np.ndarray) -> dict[str, float]:
    """Column 1's β, its HC1 t (D627's `hc1`) and the Newey-West t (5 lags, statsmodels). D627's `fit` cross-checks
    HC1 against statsmodels to a relative 1e-9, which a t near zero fails on rounding alone; the reported-beside fits
    use this instead (the gating statistics are partial correlations, not these)."""
    keep = [0, 1] + [j for j in range(2, X.shape[1]) if np.ptp(X[:, j]) > 0]
    X = X[:, keep]
    b, v = H.hc1(y, X)
    nw = H._sm().OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return {"beta": b, "t_hc1": b / float(np.sqrt(v)), "t_nw5": float(nw.tvalues[1]), "n": int(len(y))}


def verdict(sc: dict[str, Any]) -> str:
    if not (sc["flow"]["pass"] and sc["price"]["pass"]):
        return "NOT RETAINED"
    return "RETAINED" if sc["midday"]["pass"] else "UNRESOLVED (midday)"


def analyse(d: pd.DataFrame, check_known: bool = True) -> dict[str, Any]:
    ka = known_answer(d) if check_known else {"skipped": "synthetic data"}
    sc = score(d, check_d630=check_known)
    ok, ctrl, n = sc["ok"], sc["ctrl"], len(d)
    s = d["S"].to_numpy(float)
    idx_a = d["tau_star_a"].map({t: i for i, t in enumerate(T0)}).to_numpy()
    q5_a = np.column_stack([d[f"q5_{k_of(t)}"].to_numpy(float) for t in T0])[np.arange(n), idx_a]

    def fits(q: np.ndarray) -> dict[str, Any]:
        m = ok & np.isfinite(q)
        X = np.column_stack([ctrl[m][:, :1], q[m], ctrl[m][:, 1:]])
        Xj = np.column_stack([ctrl[m][:, :1], q[m], d["Q"].to_numpy()[m], ctrl[m][:, 1:]])
        return {"pcorr": B.pcorr(q[m], s[m], ctrl[m]), "alone": fit_beside(s[m], X), "with_p1": fit_beside(s[m], Xj)}
    tas_alone = fits(q5_a)
    mech = fits(d["q5_1430"].to_numpy(float))
    era = d["day"].to_numpy() < SWITCH
    by_source = {}
    for name, m0 in (("databento_to_2020_02_10", era), ("sierra_from_2020_02_11", ~era)):
        m = ok & m0
        by_source[name] = {"days": int(m.sum()), "rho_a": B.pcorr(d["Q"].to_numpy()[m], s[m], ctrl[m]),
                           "rho_d": B.pcorr(sc["mu_d"][m], s[m], ctrl[m]),
                           "tas_alone_pcorr": B.pcorr(q5_a[m], s[m], ctrl[m])}
    mu10, _s10 = ledger(d, "14:10")
    q10 = d["q_est_1410"].to_numpy()
    fixed = {"rho_a": B.pcorr(q10[ok], s[ok], ctrl[ok]), "rho_d": B.pcorr(mu10[ok], s[ok], ctrl[ok])}
    fl0 = np.column_stack([np.ones(n)] + [d[f].to_numpy(float) for f in FLAGS])
    puzzle = {}
    for name, q in (("p1", d["Q"].to_numpy()), ("mu_d", sc["mu_d"])):
        X = np.column_stack([fl0[ok][:, :1], q[ok], fl0[ok][:, 1:]])
        puzzle[name] = fit_beside(s[ok], X)
    eb = {name: float(np.mean(B.resid(s[ok], np.column_stack([ctrl[ok], q[ok]])) ** 2))
          for name, q in (("stage_a", d["Q"].to_numpy()), ("stage_d", sc["mu_d"]))}
    C = R2._load_cs()

    def groups(g: np.ndarray, m: np.ndarray) -> dict[str, Any]:
        daily, dailyg = np.where(m, g - R2.COST, 0.0)[ok], np.where(m, g, 0.0)[ok]
        return {"mean_gross": float(g[m].mean()), "mean_net": float(g[m].mean() - R2.COST),
                "sharpe_net": C.sharpe(daily), "sortino_net": C.sortino(daily), "sharpe_gross": C.sharpe(dailyg),
                "sortino_gross": C.sortino(dailyg), "distribution": R2.distribution(g[m])}
    return {"verdict": verdict(sc), "clause_flow": sc["flow"], "clause_price": sc["price"],
            "clause_midday": sc["midday"], "known_answer": ka, "tas_alone": tas_alone, "mechanism_to_1430": mech,
            "by_source": by_source, "fixed_1410": fixed, "d629_puzzle": puzzle,
            "sign_agreement_S_tas": float(np.mean(np.sign(s[ok]) == np.sign(q5_a[ok]))),
            "h2": {"stage_a": groups(sc["g_a"], sc["ta"]), "stage_d": groups(sc["g_d"], sc["td"])},
            "error_budget": eb, "n": int(ok.sum()), "first_day": str(d["day"].to_numpy()[ok][0])}


def run() -> dict[str, Any]:
    b = build(read_signed=True)
    r = analyse(b["d"])
    miss = [k for k in REQUIRED_OUTPUTS if k not in r]
    if miss:
        raise StageDError(f"REQUIRED_OUTPUTS missing {miss}")
    ins = (P.FLOW, P.CONTRACTS, P.SIGNED, P.CAL, TASP, R2.BARS, R2.PANEL)
    return {"spec": {"record": SPEC.name, "sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()},
            "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ins}, "deviations": [], "NG": r}


# ------------------------------------------------------------------ selftest (no window flow or price)
def synthetic(d: pd.DataFrame, informative: bool, rng: np.random.Generator) -> pd.DataFrame:
    s = d.copy()
    n = len(s)
    sd = float(np.std(s["q_est_1350"]))
    x = rng.standard_normal(n) * sd
    for k, extra in (("1130", 0.0), ("1350", 0.1), ("1400", 0.2), ("1410", 0.3), ("1430", 0.4)):
        s[f"q5_{k}"] = x + extra * rng.standard_normal(n) * sd
        s[f"v5_{k}"] = (0.1 * sd) ** 2
    p1 = s["q_est_1350"].to_numpy()
    driver = (0.05 * p1 + 0.3 * x) if informative else 0.2 * p1
    s["S"] = driver + 0.1 * sd * rng.standard_normal(n)
    s["S_plc"] = rng.standard_normal(n)
    for t in T0:
        s[f"m_{k_of(t)}"] = 30.0 * np.sign(p1 + x if informative else p1) + rng.standard_normal(n) * 50.0
    return s


def selftest() -> int:
    R2.audit_money()
    audit_trailing()
    print("  money audit; the trailing variance ignores its own day and reads the day before")
    b = build(read_signed=False)
    d = b["d"]
    print("  lag audit: TAS volume is nested 13:50 <= 14:00 <= 14:10 <= 14:30 on every row; no (day, month) twice")
    t = pd.read_csv(TASP, encoding="utf-8")
    broken = t.copy()
    broken["v_to_1350"], broken["v_to_1430"] = t["v_to_1430"], t["v_to_1350"]
    try:
        audit_nested(broken)
    except StageDError:
        print("  the nesting audit RAISES when two spans are swapped")
    else:
        raise StageDError("the nesting audit did not fire")
    print(f"  known answer on the real panel: {known_answer(d)}")
    mu, _sg = ledger(d.assign(q5_1350=d["q5_1350"] + 100.0), "13:50")
    if not np.allclose(mu - ledger(d, "13:50")[0], 100.0, equal_nan=True):
        raise StageDError("sign audit: clients buying TAS does not raise mu_D")
    print("  sign audit: +100 contracts of client TAS buying raises mu_D by 100")
    res = {}
    for informative in (True, False):
        r = analyse(synthetic(d, informative, np.random.default_rng(633)), check_known=False)
        miss = [k for k in REQUIRED_OUTPUTS if k not in r]
        if miss:
            raise StageDError(f"synthetic analyse is missing {miss}")
        res[informative] = (r["verdict"], round(r["clause_flow"]["ratio"], 3))
    if res[True][0] != "RETAINED" or res[False][0] == "RETAINED":
        raise StageDError(f"selftest verdicts {res}")
    print(f"  analyse() end to end: flow carrying TAS -> {res[True]}; flow driven by P1 alone -> {res[False]}")
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
        raise StageDError(f"{OUT.name} exists: Stage D has been run once (D633). Use --check to recompute.")
    res = run()
    text = json.dumps(res, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise StageDError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    r = res["NG"]
    cf, cp, cm = r["clause_flow"], r["clause_price"], r["clause_midday"]
    print(f"NG Stage D: {r['verdict']}  n {r['n']}  flow rho A {cf['rho_a']:.4f} D {cf['rho_d']:.4f} (x{cf['ratio']:.3f})"
          f"  H2 t A {cp['stage_a']['t']:.2f} D {cp['stage_d']['t']:.2f}  gain window {cm['gain_window']:.4f} "
          f"midday {cm['gain_midday']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
