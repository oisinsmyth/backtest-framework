"""D632: Stage C1 of the settlement flow ledger on NG. P1 plus the leveraged funds' forecast creation flow (deposit
§P3.4 baseline, §P3.5 with h = 0), fitted in walk-forward windows and judged by the retention rule out of sample,
with D631's midday control.

The specification is `docs/decisions/D632-PRE-REG-stage-c1-the-funds-creation-flow-on-ng.md` (committed 6ecdc22
before this file existed). At each τ:
    μ_C1(τ) = P1(τ) + Σ_f L_f ΔCreate_hat_f[t] / (10,000 P_held(τ));  σ²_C1 = σ_Q² + Σ_f (L_f / (10,000 P_held))² s²_f
RETAINED only if, out of sample on D631's blocks:
  (1) C1's partial correlation with the window flow, net of [1, r to 14:28, flags], is ≥ 1.10 × Stage A's (> 0);
  (2) H2's t over C1's trades is not below Stage A's;
  (3) C1's gain at the window exceeds the same ledger's gain at midday (11:30 against 11:50–12:20).

The data (per-τ panel columns, D629's flows, D630's moves) are Stage B's (`run_stage_b_ng.build`), and so are the
gate and τ* functions. The creation flow and its forecast are `ledger_fund_flows`'.

    uv run python -W error::RuntimeWarning scripts/run_stage_c1_ng.py --selftest | --run | --check
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "decisions" / "D632-PRE-REG-stage-c1-the-funds-creation-flow-on-ng.md"
OUT = REPO / "data" / "ledger_stage_c1_ng.json"
TRAIN, TEST = 252, 63
REQUIRED_OUTPUTS = ("verdict", "clause_flow", "clause_price", "clause_midday", "forecast", "known_answer",
                    "same_day_variant", "d629_puzzle", "h2_oos", "error_budget", "n_oos", "days_without_nav")


class StageC1Error(RuntimeError):
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


B = _load("run_stage_b_ng")      # data, gate, τ*
FF = _load("ledger_fund_flows")  # the creation flow and its forecast
R2, H, P = B.R2, B.H, B.P
T0 = B.T0
TAUS = T0 + ("11:30",)
FLAGS = B.FLAGS


def k_of(t: str) -> str:
    return t.replace(":", "")


# ------------------------------------------------------------------ audits
def audit_feature_lag(days: list[str], ret: pd.Series, flow: pd.Series) -> None:
    """Changing the flow or the return ON day t must leave day t's regressors unchanged (they are dated before t)."""
    base = FF.features(days, ret, flow).to_numpy()
    i = len(days) // 2
    f2, r2 = flow.copy(), ret.copy()
    f2.iloc[i] += 1e9
    r2.loc[days[i]] += 0.5
    moved = FF.features(days, r2, f2).to_numpy()
    if not np.array_equal(np.nan_to_num(base[i]), np.nan_to_num(moved[i])):
        raise StageC1Error("lag audit: day t's regressors move with day t's flow or return")
    if np.array_equal(np.nan_to_num(base[i + 1]), np.nan_to_num(moved[i + 1])):
        raise StageC1Error("lag audit: day t+1's regressors ignore day t (the audit cannot fire)")


def audit_sign() -> None:
    """A BOIL creation adds contracts; a KOLD creation subtracts them."""
    for f, want in (("BOIL", 1.0), ("KOLD", -1.0)):
        if np.sign(FF.FUNDS[f] * 1e6 / (FF.MULT * 3.0)) != want:
            raise StageC1Error(f"sign audit: a {f} creation has the wrong sign in contracts")


# ------------------------------------------------------------------ data
def build(read_signed: bool) -> dict[str, Any]:
    b = B.build(read_signed=read_signed)
    d = b["d"]
    days = list(d["day"])
    if not (np.array(days[1:]) > np.array(days[:-1])).all():
        raise StageC1Error("rows are not in strictly increasing date order")
    star = b["flow"][b["flow"]["is_tau_star"] == 1].set_index("day")
    ret = (star["R_day"] - 1.0).reindex(days)
    fl, missing = FF.flows(days)
    audit_feature_lag(days, ret, fl["BOIL"])
    return {"d": d, "flows": fl, "ret": ret, "missing": missing, "excluded": b["excluded"]}


# ------------------------------------------------------------------ the C1 ledger
def forecasts(days: list[str], ret: pd.Series, fl: pd.DataFrame, extra: pd.Series | None = None
              ) -> dict[str, dict[str, Any]]:
    out = {}
    rows = np.arange(len(days))
    for f in FF.FUNDS:
        X = FF.features(days, ret, fl[f])
        if extra is not None:
            X = X.assign(same_day=extra.to_numpy())
        hat, rvar, paths = FF.walk_forward_forecast(X.to_numpy(), fl[f].to_numpy(), rows, TRAIN, TEST)
        out[f] = {"hat": hat, "rvar": rvar, "paths": paths}
    return out


def ledger(d: pd.DataFrame, fc: dict[str, dict[str, Any]], t: str) -> tuple[np.ndarray, np.ndarray]:
    """(μ_C1, σ_C1) at τ. With a zero forecast and zero error variance it is (P1, σ_Q): Stage A."""
    k = k_of(t)
    q3 = np.zeros(len(d))
    v3 = np.zeros(len(d))
    for f, L in FF.FUNDS.items():
        conv = L / (FF.MULT * d[f"p_held_{k}"].to_numpy())
        q3 = q3 + fc[f]["hat"] * conv
        v3 = v3 + conv ** 2 * fc[f]["rvar"]
    return d[f"q_est_{k}"].to_numpy() + q3, np.sqrt(d[f"sigma_Q_{k}"].to_numpy() ** 2 + v3)


def zero_forecast(n: int) -> dict[str, dict[str, Any]]:
    return {f: {"hat": np.zeros(n), "rvar": np.zeros(n), "paths": []} for f in FF.FUNDS}


def known_answer(d: pd.DataFrame) -> dict[str, Any]:
    zf = zero_forecast(len(d))
    gates = {}
    for t in T0:
        mu, sg = ledger(d, zf, t)
        gates[t] = B.gate(d, k_of(t), mu, sg)
        if not np.array_equal(gates[t], d[f"gate_pass_{k_of(t)}"].to_numpy().astype(int)):
            raise StageC1Error(f"known answer: with a zero forecast the gate differs from the panel's at {t}")
    idx, _s = B.tau_star(gates)
    if not np.array_equal(np.array(T0)[idx], d["tau_star_a"].to_numpy()):
        raise StageC1Error("known answer: with a zero forecast, τ*_C1 differs from the panel's τ*")
    return {"gate_equal_at_every_tau": True, "tau_star_equal": True, "days": int(len(d))}


def score(d: pd.DataFrame, fc_at: Callable[[str], dict[str, dict[str, Any]]]) -> dict[str, Any]:
    """The three clauses. `fc_at(τ)` gives the forecast used at τ (the same one at every τ for C1; the same-day
    variant fits one per τ)."""
    n = len(d)
    fc0 = fc_at(T0[0])
    oos = np.isfinite(fc0["BOIL"]["hat"]) & np.isfinite(fc0["KOLD"]["hat"])
    fl_ = [d[f].to_numpy(float) for f in FLAGS]
    ctrl = np.column_stack([np.ones(n), d["r"].to_numpy()] + fl_)
    mus, sgs, gates = {}, {}, {}
    for t in TAUS:
        mus[t], sgs[t] = ledger(d, fc_at(t), t)
    for t in T0:
        gates[t] = B.gate(d, k_of(t), np.nan_to_num(mus[t]), np.nan_to_num(sgs[t]))
    idx, sig = B.tau_star(gates)
    mu_c = np.column_stack([mus[t] for t in T0])[np.arange(n), idx]
    s = d["S"].to_numpy(float)
    rho_a, rho_c = B.pcorr(d["Q"].to_numpy()[oos], s[oos], ctrl[oos]), B.pcorr(mu_c[oos], s[oos], ctrl[oos])
    flow = {"rho_a": rho_a, "rho_c1": rho_c, "ratio": rho_c / rho_a, "pass": bool(rho_a > 0 and rho_c >= 1.10 * rho_a)}
    M = np.column_stack([d[f"m_{k_of(t)}"].to_numpy(float) for t in T0])
    idx_a = d["tau_star_a"].map({t: i for i, t in enumerate(T0)}).to_numpy()
    g_a = np.sign(d["Q"].to_numpy()) * M[np.arange(n), idx_a]
    g_c = np.sign(mu_c) * M[np.arange(n), idx]
    ta = oos & (d["signal_day"].to_numpy() == 1) & np.isfinite(g_a)
    tc = oos & sig & np.isfinite(g_c)
    ha, hc = R2.mean_t(g_a[ta]), R2.mean_t(g_c[tc])
    price = {"stage_a": ha, "stage_c1": hc, "pass": bool(hc["t"] >= ha["t"]), "traded_days_a": int(ta.sum()),
             "traded_days_c1": int(tc.sum()), "overlap_share_of_c1": float((ta & tc).sum() / max(1, tc.sum())),
             "direction_flips_vs_a_on_common_days": float(np.mean(np.sign(mu_c[ta & tc]) != np.sign(d["Q"].to_numpy()[ta & tc])))
             if (ta & tc).any() else float("nan")}
    pm = oos & d["plc_clean"].to_numpy() & np.isfinite(d["S_plc"].to_numpy(float)) & np.isfinite(mus["11:30"]) & \
        np.isfinite(d["q_est_1130"].to_numpy(float))
    cp = np.column_stack([np.ones(n), d["r_held_1130"].to_numpy()] + fl_)[pm]
    sp = d["S_plc"].to_numpy(float)[pm]
    pa, pc = B.pcorr(d["q_est_1130"].to_numpy()[pm], sp, cp), B.pcorr(mus["11:30"][pm], sp, cp)
    midday = {"rho_a_midday": pa, "rho_c1_midday": pc, "gain_window": rho_c - rho_a, "gain_midday": pc - pa,
              "n_days": int(pm.sum()), "pass": bool((rho_c - rho_a) > (pc - pa))}
    return {"flow": flow, "price": price, "midday": midday, "oos": oos, "mu_c": mu_c, "g_a": g_a, "g_c": g_c,
            "ta": ta, "tc": tc, "ctrl": ctrl}


def verdict(sc: dict[str, Any]) -> str:
    if not (sc["flow"]["pass"] and sc["price"]["pass"]):
        return "NOT RETAINED (inconclusive)"
    return "RETAINED" if sc["midday"]["pass"] else "UNRESOLVED (midday)"


def analyse(d: pd.DataFrame, fl: pd.DataFrame, ret: pd.Series, missing: dict[str, int], check_known: bool = True
            ) -> dict[str, Any]:
    ka = known_answer(d) if check_known else {"skipped": "synthetic data"}
    days = list(d["day"])
    fc = forecasts(days, ret, fl)
    sc = score(d, lambda _t: fc)
    oos = sc["oos"]
    fcast = {}
    for f in FF.FUNDS:
        y, h = fl[f].to_numpy(), fc[f]["hat"]
        m = np.isfinite(h)
        lag = np.r_[np.nan, y[:-1]]
        sse = float(np.sum((y[m] - h[m]) ** 2))
        paths = fc[f]["paths"]
        fcast[f] = {"oos_r2_vs_mean": 1 - sse / float(np.sum((y[m] - y[m].mean()) ** 2)),
                    "oos_r2_vs_zero": 1 - sse / float(np.sum(y[m] ** 2)),
                    "oos_r2_vs_yesterday": 1 - sse / float(np.sum((y[m] - lag[m]) ** 2)),
                    "share_windows_a1_neg": float(np.mean([p["a1"] < 0 for p in paths])),
                    "share_windows_a2_neg": float(np.mean([p["a2"] < 0 for p in paths])),
                    "share_windows_a3_pos": float(np.mean([p["a3"] > 0 for p in paths])),
                    "paths": paths}
    # the same-day variant (NOT the deposit's C1): a separate forecast per τ with the return to τ
    variant = {t: forecasts(days, ret, fl, extra=d[f"r_held_{k_of(t)}"]) for t in TAUS}
    sv = score(d, lambda t: variant[t])
    same_day = {"flow": sv["flow"], "price": {k: v for k, v in sv["price"].items()}, "midday": sv["midday"],
                "verdict_if_it_were_the_rule": verdict(sv)}
    # D629's puzzle: S on the predictor and the flags, NO return control, on the OOS days
    fl_ = np.column_stack([np.ones(len(d))] + [d[f].to_numpy(float) for f in FLAGS])
    puzzle = {}
    for name, q in (("p1", d["Q"].to_numpy()), ("mu_c1", sc["mu_c"])):
        X = np.column_stack([fl_[oos][:, :1], q[oos], fl_[oos][:, 1:]])
        puzzle[name] = H.fit(d["S"].to_numpy(float)[oos], X)
    eb = {}
    s = d["S"].to_numpy(float)
    for name, q in (("stage_a", d["Q"].to_numpy()), ("stage_c1", sc["mu_c"])):
        X = np.column_stack([sc["ctrl"][oos], q[oos]])
        eb[name] = float(np.mean(B.resid(s[oos], X) ** 2))
    C = R2._load_cs()

    def groups(g: np.ndarray, m: np.ndarray) -> dict[str, Any]:
        daily, dailyg = np.where(m, g - R2.COST, 0.0)[oos], np.where(m, g, 0.0)[oos]
        return {"mean_gross": float(g[m].mean()), "mean_net": float(g[m].mean() - R2.COST),
                "sharpe_net": C.sharpe(daily), "sortino_net": C.sortino(daily), "sharpe_gross": C.sharpe(dailyg),
                "sortino_gross": C.sortino(dailyg), "distribution": R2.distribution(g[m])}
    return {"verdict": verdict(sc), "clause_flow": sc["flow"], "clause_price": sc["price"],
            "clause_midday": sc["midday"], "forecast": fcast, "known_answer": ka, "same_day_variant": same_day,
            "d629_puzzle": puzzle, "h2_oos": {"stage_a": groups(sc["g_a"], sc["ta"]),
                                             "stage_c1": groups(sc["g_c"], sc["tc"])},
            "error_budget": eb, "n_oos": int(oos.sum()), "days_without_nav": missing,
            "first_oos_day": str(np.array(days)[oos][0])}


def run() -> dict[str, Any]:
    b = build(read_signed=True)
    r = analyse(b["d"], b["flows"], b["ret"], b["missing"])
    miss = [k for k in REQUIRED_OUTPUTS if k not in r]
    if miss:
        raise StageC1Error(f"REQUIRED_OUTPUTS missing {miss}")
    ins = (P.FLOW, P.CONTRACTS, P.SIGNED, P.CAL, FF.NAV, R2.BARS, R2.PANEL)
    return {"spec": {"record": SPEC.name, "sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()},
            "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ins}, "deviations": [], "NG": r}


# ------------------------------------------------------------------ selftest (no window flow or price)
def synthetic(d: pd.DataFrame, informative: bool, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = d.copy()
    n = len(s)
    sd = float(np.std(s["q_est_1350"]))
    q3c = {}
    usd = {}
    for f, L in FF.FUNDS.items():
        x = np.zeros(n)
        e = rng.standard_normal(n) * sd
        for i in range(1, n):
            x[i] = 0.8 * x[i - 1] + e[i]  # a forecastable creation flow, in contracts
        q3c[f] = x
        usd[f] = x * FF.MULT * s["p_held_1350"].to_numpy() / L
    fl = pd.DataFrame(usd, index=list(s["day"]))
    # the null keeps Stage A's own signal (the real Stage A correlation is 0.137) and gives creations no role, so the
    # ingredient C1 claims is what is broken; a pure-noise null would test only the ratio's fragility near zero
    net = s["q_est_1350"].to_numpy() + q3c["BOIL"] + q3c["KOLD"]
    driver = net if informative else s["q_est_1350"].to_numpy()
    s["S"] = 0.2 * driver + 0.1 * sd * rng.standard_normal(n)
    s["S_plc"] = rng.standard_normal(n)
    for t in T0:
        s[f"m_{k_of(t)}"] = 30.0 * np.sign(driver) + rng.standard_normal(n) * 50.0
    return s, fl


def selftest() -> int:
    audit_sign()
    R2.audit_money()
    print("  sign audits: BOIL creations add contracts, KOLD creations subtract them; D630's money audit passes")
    b = build(read_signed=False)
    d = b["d"]
    print("  lag audit: day t's regressors ignore day t's flow and return, and day t+1's use them")
    print(f"  known answer on the real panel: {known_answer(d)}")
    broken = d.copy()
    broken["p_held_1350"] = broken["p_held_1350"] * 1.5
    zf = zero_forecast(len(d))
    mu, sg = ledger(broken, zf, "13:50")
    if not np.array_equal(B.gate(broken, "1350", mu, sg), broken["gate_pass_1350"].to_numpy().astype(int)):
        print("  the known answer RAISES when an input it reads is altered (P_held x 1.5 moves the gate)")
    else:
        raise StageC1Error("altering P_held did not move the gate: the known answer cannot fire")
    ret = b["ret"]
    res = {}
    for informative in (True, False):
        s, fl = synthetic(d, informative, np.random.default_rng(632))
        r = analyse(s, fl, ret, {"BOIL": 0, "KOLD": 0}, check_known=False)
        miss = [k for k in REQUIRED_OUTPUTS if k not in r]
        if miss:
            raise StageC1Error(f"synthetic analyse is missing {miss}")
        res[informative] = (r["verdict"], round(r["clause_flow"]["ratio"], 3))
    if res[True][0] != "RETAINED" or res[False][0] == "RETAINED":
        raise StageC1Error(f"selftest verdicts {res}")
    print(f"  analyse() end to end: flow driven by P1 + forecastable creations -> {res[True]}; "
          f"by P1 alone -> {res[False]}")
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
        raise StageC1Error(f"{OUT.name} exists: Stage C1 has been run once (D632). Use --check to recompute.")
    res = run()
    text = json.dumps(res, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise StageC1Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    r = res["NG"]
    cf, cp, cm = r["clause_flow"], r["clause_price"], r["clause_midday"]
    print(f"NG Stage C1: {r['verdict']}  n_oos {r['n_oos']}  flow rho A {cf['rho_a']:.4f} C1 {cf['rho_c1']:.4f} "
          f"(x{cf['ratio']:.3f})  H2 t A {cp['stage_a']['t']:.2f} C1 {cp['stage_c1']['t']:.2f}  gain window "
          f"{cm['gain_window']:.4f} midday {cm['gain_midday']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
