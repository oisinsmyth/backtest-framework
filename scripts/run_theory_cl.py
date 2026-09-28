"""D648's runner: the settlement ledger's mechanism on CL -- inventory risk (x_GM) or square-root impact (x_SR)?
Committed before its one run (R8). The design, the tests and the verdicts are D648's
(`docs/decisions/D648-PRE-REG-cl-inventory-risk-or-square-root-impact.md`); this file only computes them.

    uv run python scripts/run_theory_cl.py --selftest    # synthetic returns only; every audit must raise when broken
    uv run python scripts/run_theory_cl.py --run         # the one run -> data/ledger_theory_cl.json (refuses a second)
    uv run python scripts/run_theory_cl.py --check       # rebuilds and compares byte for byte

Inputs: the predictor panel `ledger_predicted_flow_daily.csv.gz` through D627's `load_flow` (its lag and sign audits),
the volume panel's as-of prices, and `data/cl_minute_bars.csv.gz`. The gitignored panels are read from the main
checkout when this runs in a worktree. Nothing on or after 2025-03-01 is read; A1's 2020-04-01 -> 2020-09-16 is
excluded for CL.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _main_checkout(repo: Path) -> Path:
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


DATA_IN = _main_checkout(REPO) / "data"
H = _load("run_h1a_stage_a", "run_h1a_stage_a.py")   # load_flow + audit_flow (D627), p95_with_se
R = _load("run_h2_ng_stage_a", "run_h2_ng_stage_a.py")  # asof, add_min, fill_end, audit_fill_timing (D630)
PW = _load("ledger_power_theory_cl", "ledger_power_theory_cl.py")  # ols_nw, classify, audit_classifier, the noise
for mod, names in ((H, ("FLOW", "PANEL", "FSHARE")), (R, ("FLOW", "BARS", "PANEL"))):
    for nm in names:
        p = getattr(mod, nm)
        if not p.exists():
            setattr(mod, nm, DATA_IN / p.name)

SPEC = REPO / "docs" / "decisions" / "D648-PRE-REG-cl-inventory-risk-or-square-root-impact.md"
BARS = REPO / "data" / "cl_minute_bars.csv.gz"
OUT = REPO / "data" / "ledger_theory_cl.json"
ROOT, M = "CL", 1_000.0
COST = 21.46 + 10.0
MCL_SCALE, MCL_COST = 0.1, 3.0 + 1.0 + 1.0
CUT, A1, SWITCH = "2025-03-01", ("2020-04-01", "2020-09-16"), "2020-09-17"
T0 = ("13:50", "14:00", "14:10")
T_HOLM, T_HOLM2, T_FORM = 2.2414, 1.96, 2.0
SEED, N_ROT = 648, 1000
EXIT_END, FADE_END, PLC_FILL, PLC_END = "14:30", "15:00", "11:32", "12:20"
MIN_PRIOR, K_PROJ = 100, 1.5
REQUIRED_OUTPUTS = ("n", "T1", "T2", "T3", "performance", "depends", "controls", "t2_variants", "ng_beside",
                    "projected_profit", "h4", "dsr", "deviations")


class TheoryError(RuntimeError):
    pass


# ------------------------------------------------------------------ money and the audits
def money(direction: float, fill: float, exit_px: float) -> float:
    """Gross dollars per full CL contract: + when the price moves the traded way."""
    return float(direction * (exit_px - fill) * M)


def audit_money(fn: Callable[[float, float, float], float] = money) -> None:
    """A $0.10 rise after a buy books +$100 gross and +$68.54 net; after a sell, -$100 (D648 s.6)."""
    if not (math.isclose(fn(1, 50.0, 50.10), 100.0, abs_tol=1e-6)
            and math.isclose(fn(1, 50.0, 50.10) - COST, 68.54, abs_tol=1e-6)
            and math.isclose(fn(-1, 50.0, 50.10), -100.0, abs_tol=1e-6)):
        raise TheoryError("sign audit: the money does not pay the traded way")


def predictors(x: pd.DataFrame) -> pd.DataFrame:
    """D648's x_GM, x_SR and the continuation control, from a panel slice (one row per day)."""
    share = x["q_est"].abs() / x["V_d"]
    return pd.DataFrame({"x_gm": x["sigma_rem_ret"] ** 2 * share * x["p_held"] * M,
                         "x_sr": x["sigma_d"] * np.sqrt(share) * x["p_held"] * M,
                         "mom": x["r_held"].abs() / x["sigma_d"]}, index=x.index)


def audit_right_quantity(xg: np.ndarray, xs: np.ndarray, g: np.ndarray, g_plc: np.ndarray, net: np.ndarray,
                         gross: np.ndarray) -> None:
    if np.allclose(xg, xs):
        raise TheoryError("right-quantity: x_GM equals x_SR")
    both = np.isfinite(g) & np.isfinite(g_plc)
    if both.any() and np.allclose(g[both], g_plc[both]):
        raise TheoryError("right-quantity: T1's returns equal the placebo's")
    if not np.allclose(gross - net, COST):
        raise TheoryError("right-quantity: the net is not the gross less $31.46")


# ------------------------------------------------------------------ data
def load(read_returns: bool, bars: pd.DataFrame | None = None) -> dict[str, Any]:
    flow, star = H.load_flow(ROOT)
    keep = ~star["day"].between(*A1)
    need = ["q_est", "V_d", "sigma_d", "sigma_rem_ret", "p_held", "r_held"]
    d = star[keep].dropna(subset=need)
    d = d[d["V_d"] > 0].sort_values("day").reset_index(drop=True)
    d = pd.concat([d, predictors(d)], axis=1)
    d["dir"] = np.sign(d["q_est"]).astype(float)
    d["traded"] = d["signal_day"] == 1
    d["t0_idx"] = d["tau"].map({t: i for i, t in enumerate(T0)})
    d["year"] = d["day"].str[:4]
    d["era"] = np.where(d["day"] >= SWITCH, "B", "A")
    d["aum"] = d["aum_long"] + d["aum_inverse"]
    plc = flow[flow["tau"] == "11:30"].set_index("day").reindex(d["day"])
    pp = predictors(plc)
    for c in ("x_gm", "x_sr", "mom"):
        d[f"plc_{c}"] = pp[c].to_numpy()
    d["plc_dir"] = np.sign(plc["q_est"]).to_numpy()
    d["plc_ym"] = plc["traded_ym"].to_numpy()
    d["plc_traded"] = ((plc["gate_pass"] == 1) & (plc["n_stale"] == 0)).to_numpy()
    out: dict[str, Any] = {"d": d, "excluded_a1": int((~keep).sum())}
    if not read_returns:
        return out
    if bars is None:
        bars = pd.read_csv(BARS, encoding="utf-8", usecols=["day", "ym", "minute", "close"])
    if (bars["day"] >= CUT).any():
        raise TheoryError("a bar on or after the cut is in memory")
    groups = {k: (x["minute"].to_numpy(), x["close"].to_numpy())
              for k, x in bars.sort_values(["day", "ym", "minute"]).groupby(["day", "ym"], sort=False)}
    px = pd.read_csv(R.PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "px_1130", "px_1350"])
    px = px[(px["root"] == ROOT) & (px["kind"] == "outright")].set_index(["day", "ym"])
    if px.index.duplicated().any():
        raise TheoryError("two CL outrights share a (day, month) in the volume panel")
    R.audit_fill_timing()
    empty = (np.array([], dtype=object), np.array([]))

    def start(day: str, ym: Any, col: str) -> float:
        try:
            return float(px.at[(day, ym), col])
        except KeyError:
            return float("nan")

    cols: dict[str, list[float]] = {k: [] for k in ("m_13:50", "m_14:00", "m_14:10", "fade", "s5", "m_plc")}
    for row in d.itertuples(index=False):
        mins, cl = groups.get((row.day, row.traded_ym), empty)
        s1350 = start(row.day, row.traded_ym, "px_1350")
        exit_px = R.asof(mins, cl, EXIT_END, s1350)
        for t in T0:
            cols[f"m_{t}"].append((exit_px - R.asof(mins, cl, R.fill_end(t), s1350)) * M)
        fill = R.asof(mins, cl, R.fill_end(row.tau), s1350)
        cols["fade"].append(-money(row.dir, exit_px, R.asof(mins, cl, FADE_END, s1350)))
        cols["s5"].append(money(row.dir, fill, R.asof(mins, cl, R.add_min(row.tau, 6), s1350)))
        if isinstance(row.plc_ym, str):
            pm, pc = groups.get((row.day, row.plc_ym), empty)
            s1130 = start(row.day, row.plc_ym, "px_1130")
            cols["m_plc"].append((R.asof(pm, pc, PLC_END, s1130) - R.asof(pm, pc, PLC_FILL, s1130)) * M)
        else:
            cols["m_plc"].append(float("nan"))
    for k, v in cols.items():
        d[k] = v
    d["g"] = d["dir"] * d[[f"m_{t}" for t in T0]].to_numpy()[np.arange(len(d)), d["t0_idx"].to_numpy()]
    d["g_plc"] = d["plc_dir"] * d["m_plc"]
    out["d"] = d
    return out


# ------------------------------------------------------------------ statistics
def mean_t(x: np.ndarray) -> dict[str, float]:
    x = x[np.isfinite(x)]
    se = float(x.std(ddof=1) / math.sqrt(len(x)))
    return {"n": int(len(x)), "mean": float(x.mean()), "se": se, "t": float(x.mean() / se)}


def zcols(*vs: np.ndarray) -> list[np.ndarray]:
    return [(v - v.mean()) / v.std() for v in vs]


def t2(g: np.ndarray, xg: np.ndarray, xs: np.ndarray, mom: np.ndarray | None, extra: np.ndarray | None = None
       ) -> dict[str, Any]:
    ok = np.isfinite(g) & np.isfinite(xg) & np.isfinite(xs) & (np.isfinite(mom) if mom is not None else True)
    parts = [np.ones(ok.sum())] + zcols(xg[ok], xs[ok]) + (zcols(mom[ok]) if mom is not None else [])
    X = np.column_stack(parts + ([extra[ok]] if extra is not None else []))
    t = PW.ols_nw(g[ok], X)
    b = np.linalg.lstsq(X, g[ok], rcond=None)[0]
    return {"n": int(ok.sum()), "b_gm_per_sd": float(b[1]), "b_sr_per_sd": float(b[2]), "t_gm": float(t[1]),
            "t_sr": float(t[2]), "t_mom": float(t[3]) if mom is not None else None,
            "class": PW.classify(float(t[1]), float(t[2]))}


def rotation(d: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    Mv = d[[f"m_{t}" for t in T0]].to_numpy()
    tr, dr, t0 = d["traded"].to_numpy(), d["dir"].to_numpy(), d["t0_idx"].to_numpy()
    years = d["year"].to_numpy()
    yidx = [np.flatnonzero(years == y) for y in np.unique(years)]
    out = np.empty(N_ROT)
    for i in range(N_ROT):
        a, b, c = tr.copy(), dr.copy(), t0.copy()
        for idx in yidx:
            if len(idx) > 40:
                k = int(rng.integers(20, len(idx) - 20 + 1))
                a[idx], b[idx], c[idx] = np.roll(tr[idx], k), np.roll(dr[idx], k), np.roll(t0[idx], k)
        x = (b * Mv[np.arange(len(d)), c])[a]
        out[i] = mean_t(x)["t"]
    return out


def performance(d: pd.DataFrame, g: np.ndarray, scale: float, cost: float) -> dict[str, Any]:
    C = R._load_cs()
    tr = d["traded"].to_numpy() & np.isfinite(g)
    gg = g * scale
    dg, dn = np.where(tr, gg, 0.0), np.where(tr, gg - cost, 0.0)
    cum = np.cumsum(dn)
    x = np.sort(gg[tr] - cost)
    k = max(1, int(math.ceil(0.01 * len(x))))
    s = pd.Series(x)
    return {"mean_gross": float(gg[tr].mean()), "mean_net": float(gg[tr].mean() - cost),
            "sharpe_gross": C.sharpe(dg), "sortino_gross": C.sortino(dg), "sharpe_net": C.sharpe(dn),
            "sortino_net": C.sortino(dn), "sharpe_net_se": C.sharpe_boot(dn, list(d["day"])),
            "exposure_share_of_days": float(tr.mean()), "daily_vol_net": float(dn.std(ddof=1)),
            "max_drawdown_net": float((cum - np.maximum.accumulate(cum)).min()), "total_net": float(dn.sum()),
            "mean_move_vs_cost": float(gg[tr].mean() / cost), "breakeven_cost": float(gg[tr].mean()),
            "hit_rate_net": float((x > 0).mean()), "skew_daily_net": float(pd.Series(dn).skew()),
            "distribution_net": {"count": int(len(x)), "mean": float(x.mean()), "median": float(np.median(x)),
                                 "win_rate": float((x > 0).mean()),
                                 "payoff": float(x[x > 0].mean() / -x[x < 0].mean()), "skew": float(s.skew()),
                                 "kurtosis_excess": float(s.kurt()), "mean_ex_top_1pct": float(x[:-k].mean()),
                                 "mean_ex_bottom_1pct": float(x[k:].mean()), "mean_trimmed_both": float(x[k:-k].mean())}}


def split(d: pd.DataFrame, g: np.ndarray, key: np.ndarray) -> dict[str, Any]:
    tr = d["traded"].to_numpy() & np.isfinite(g)
    return {str(k): mean_t(g[tr & (key == k)]) for k in pd.unique(key[tr]) if (tr & (key == k)).sum() >= 5}


def projected(d: pd.DataFrame, g: np.ndarray, x: np.ndarray) -> dict[str, Any]:
    """D648 s.4: the scale from PRIOR traded days only (>= MIN_PRIOR), trade when the projection >= K x the round trip."""
    C = R._load_cs()
    tr = np.flatnonzero(d["traded"].to_numpy() & np.isfinite(g))
    gi, xi = g[tr], x[tr]
    sgx, sxx = np.cumsum(gi * xi), np.cumsum(xi * xi)
    b = np.full(len(tr), np.nan)
    b[MIN_PRIOR:] = sgx[MIN_PRIOR - 1:-1] / sxx[MIN_PRIOR - 1:-1]
    out = {}
    for size, scale, cost in (("full", 1.0, COST), ("micro", MCL_SCALE, MCL_COST)):
        take = (b * xi * scale) >= K_PROJ * cost
        dn = np.zeros(len(d))
        dn[tr[take]] = gi[take] * scale - cost
        out[size] = {"trades": int(take.sum()), "net_per_trade": float((gi[take] * scale - cost).mean()) if take.any()
                     else None, "sharpe_net": C.sharpe(dn), "sortino_net": C.sortino(dn)}
    return out


def analyse(d: pd.DataFrame, rng: np.random.Generator, ng: dict[str, Any] | None) -> dict[str, Any]:
    g = d["g"].to_numpy(float)
    tr = d["traded"].to_numpy()
    ok = tr & np.isfinite(g)
    deviations: list[str] = []
    if (tr & ~np.isfinite(g)).any():
        deviations.append(f"{int((tr & ~np.isfinite(g)).sum())} traded days without a fill or exit price")
    audit_right_quantity(d["x_gm"].to_numpy(), d["x_sr"].to_numpy(), g, d["g_plc"].to_numpy(),
                         g[ok] - COST, g[ok])
    # T1
    gate = mean_t(g[ok])
    gate["t_nw5"] = H._sm().OLS(g[ok], np.ones(ok.sum())).fit(cov_type="HAC", cov_kwds={"maxlags": 5}).tvalues[0]
    pm = d["plc_traded"].to_numpy() & np.isfinite(d["g_plc"].to_numpy())
    plc = mean_t(d["g_plc"].to_numpy()[pm])
    ts = rotation(d, rng)
    p50, p95, p95_se = H.p95_with_se(ts, rng)
    c1 = abs(plc["t"]) < 2
    c2 = gate["t"] - p95 > 2 * p95_se
    if not (gate["mean"] > 0 and gate["t"] >= T_HOLM):
        v1 = "FAIL"
    elif not c1 or gate["t"] <= p95:
        v1 = "UNRESOLVED (control)"
    elif not c2:
        v1 = "UNRESOLVED (margin)"
    else:
        v1 = "PASS"
    T1 = {"verdict": v1, "gate": gate, "net_mean": gate["mean"] - COST, "holm_step2_pass": bool(gate["t"] >= T_HOLM2),
          "C1_placebo": plc, "C2_rotation": {"p50": p50, "p95": p95, "p95_se": p95_se, "draws": N_ROT,
                                             "margin": gate["t"] - p95}}
    # T2 and its placebo
    xg, xs, mom = d["x_gm"].to_numpy(), d["x_sr"].to_numpy(), d["mom"].to_numpy()
    main = t2(g, xg, xs, mom)
    c3 = t2(d["g_plc"].to_numpy(), d["plc_x_gm"].to_numpy(), d["plc_x_sr"].to_numpy(), d["plc_mom"].to_numpy())
    T2 = {"verdict": main["class"] if c3["class"] == "NEITHER" else "UNRESOLVED (control)", "main": main,
          "C3_placebo": c3, "reading": "GM is confirmable; NEITHER is not evidence against SR (POWER)"}
    # T3
    fade = mean_t(d["fade"].to_numpy()[ok])
    T3 = {"verdict": "PASS" if fade["mean"] > 0 and fade["t"] >= T_FORM else "FAIL", "fade": fade,
          "share_of_T1_mean_reversed": fade["mean"] / gate["mean"] if gate["mean"] != 0 else None}
    # beside
    years = d["year"].to_numpy()

    def terc(v: np.ndarray) -> np.ndarray:
        return np.digitize(v, np.nanquantile(v[ok], [1 / 3, 2 / 3]))

    by_year = split(d, g, years)
    best = max(by_year, key=lambda y: by_year[y]["mean"] * by_year[y]["n"])
    depends = {"by_year": by_year, "profitable_years": int(sum(v["mean"] > 0 for v in by_year.values())),
               "without_best_year": mean_t(g[ok & (years != best)]), "best_year": best,
               "by_aum_tercile": split(d, g, terc(d["aum"].to_numpy())),
               "by_price_tercile": split(d, g, terc(d["p_held"].to_numpy())),
               "by_t0": split(d, g, d["tau"].to_numpy()), "by_era": split(d, g, d["era"].to_numpy())}
    un = ~tr & np.isfinite(g)
    a_, b_ = g[ok], g[un]
    controls = {"untraded_same_rule": mean_t(b_), "traded_minus_untraded": float(a_.mean() - b_.mean()),
                "welch_t": float((a_.mean() - b_.mean()) / math.sqrt(a_.var(ddof=1) / len(a_) + b_.var(ddof=1) / len(b_)))}
    yfe = pd.get_dummies(d["year"], drop_first=True).to_numpy(float)
    variants = {"year_fixed_effects": t2(g, xg, xs, mom, extra=yfe) if yfe.size else None,
                "without_continuation_control": t2(g, xg, xs, None)}
    for nm, x in (("x_gm_alone", xg), ("x_sr_alone", xs)):
        okx = np.isfinite(g) & np.isfinite(x)
        X = np.column_stack([np.ones(okx.sum()), zcols(x[okx])[0], zcols(mom[okx])[0]])
        tt = PW.ols_nw(g[okx], X)
        bb = np.linalg.lstsq(X, g[okx], rcond=None)[0]
        resid = g[okx] - X @ bb
        variants[nm] = {"t": float(tt[1]), "b_per_sd": float(bb[1]),
                        "r2": float(1 - resid.var() / g[okx].var())}
    absI = 0.7 * xs
    variants["pass_through_of_absI_traded"] = float((g[ok] * absI[ok]).sum() / (absI[ok] ** 2).sum())
    perf = {"full": performance(d, g, 1.0, COST), "micro_mcl": performance(d, g, MCL_SCALE, MCL_COST)}
    proj = {"x_sr": projected(d, g, xs), "x_gm": projected(d, g, xg)}
    s5 = d["s5"].to_numpy()
    h4 = {"share_by_t0_plus_5": float(np.nanmean(s5[ok]) / g[ok].mean())}
    D = R._load_dsr()
    dn = np.where(ok, g - COST, 0.0)
    trials = [dn, np.where(ok, g * MCL_SCALE - MCL_COST, 0.0)]
    srs = [float(x.mean() / x.std(ddof=1)) for x in trials]
    s = pd.Series(dn)
    dsr = {"n_trials": len(srs), "dsr": D.deflated_sharpe_ratio(srs[0], len(dn), float(s.skew()), float(s.kurt()) + 3.0,
                                                                  len(srs), float(np.var(srs, ddof=1)))}
    return {"n": {"tau_star_days": int(len(d)), "traded": int(ok.sum()), "a1_excluded_rows": None},
            "T1": T1, "T2": T2, "T3": T3, "performance": perf, "depends": depends, "controls": controls,
            "t2_variants": variants, "ng_beside": ng, "projected_profit": proj, "h4": h4, "dsr": dsr,
            "deviations": deviations}


def ng_beside() -> dict[str, Any]:
    """T2 on NG's 1,936 tau* days: EXPLORATORY, NG's moves have been read (D630 and the post-hoc scripts)."""
    b = R.build(read_returns=True)
    dn = b["d"]
    g = R.signed(dn)
    flow = b["flow"]
    st = flow[flow["is_tau_star"] == 1].set_index("day").reindex(dn["day"])
    pr = predictors(st.assign(p_held=st["p_held"]))
    pr["x_gm"] = pr["x_gm"] * (R.MULT / M)  # NG's M is 10,000
    pr["x_sr"] = pr["x_sr"] * (R.MULT / M)
    return {"label": "EXPLORATORY: NG is spent for this question", **t2(g, pr["x_gm"].to_numpy(), pr["x_sr"].to_numpy(),
                                                                        pr["mom"].to_numpy())}


# ------------------------------------------------------------------ run, check, selftest
def run() -> dict[str, Any]:
    audit_money()
    PW.audit_classifier()
    L = load(read_returns=True)
    rng = np.random.default_rng(SEED)
    doc = analyse(L["d"], rng, ng_beside())
    doc["n"]["a1_excluded_rows"] = L["excluded_a1"]
    doc["spec"] = SPEC.name
    missing = [k for k in REQUIRED_OUTPUTS if k not in doc]
    if missing:
        raise TheoryError(f"declared outputs missing: {missing}")
    return doc


def synthetic_bars(d: pd.DataFrame, effect: np.ndarray, rng: np.random.Generator) -> pd.DataFrame:
    """Minute bars whose t0+1 -> 14:29 move is dir x effect + pre-sample noise, flat elsewhere (no real return)."""
    U = PW.presample()["_U"]
    u = PW._block(U, len(d), rng)[np.arange(len(d)), d["t0_idx"].to_numpy()]
    sd_px = d["sigma_rem_ret"].to_numpy() * d["p_held"].to_numpy()
    move = (d["dir"].to_numpy() * effect + u * sd_px * M) / M
    plc_move = PW._block(U, len(d), rng)[:, 0] * sd_px  # the placebo window: noise only, no effect
    fade_move = PW._block(U, len(d), rng)[:, 1] * sd_px  # after the settlement: noise only
    rows = []
    for r, mv, pv, fv in zip(d.itertuples(index=False), move, plc_move, fade_move):
        p = float(r.p_held)
        f0 = R.add_min(r.tau, 1)
        for ym in {r.traded_ym, r.plc_ym} - {None}:
            if not isinstance(ym, str):
                continue
            rows += [(r.day, ym, "11:31", p), (r.day, ym, "12:19", p + pv), (r.day, ym, f0, p + pv),
                     (r.day, ym, "14:29", p + pv + mv), (r.day, ym, "14:59", p + pv + mv + fv)]
    b = pd.DataFrame(rows, columns=["day", "ym", "minute", "close"])
    return b.drop_duplicates(["day", "ym", "minute"], keep="last")


def selftest() -> int:
    audit_money()
    try:
        audit_money(lambda dr, f, e: -money(dr, f, e))
    except TheoryError:
        pass
    else:
        raise AssertionError("the sign audit did not fire on a flipped book")
    PW.audit_classifier()
    rng = np.random.default_rng(1)
    base = load(read_returns=False)["d"]
    for truth, want_t1, want_t2 in (("GM", "PASS", "GM"), ("null", None, None)):
        eff = (base["x_gm"] * (0.5 * 0.7 * base["x_sr"]).mean() / base["x_gm"].mean()).to_numpy() \
            if truth == "GM" else np.zeros(len(base))
        bars = synthetic_bars(base, eff, rng)
        d = load(read_returns=True, bars=bars)["d"]
        res = analyse(d, np.random.default_rng(2), None)
        print(f"  synthetic {truth}: T1 {res['T1']['verdict']} (t {res['T1']['gate']['t']:.2f}), "
              f"T2 {res['T2']['verdict']} (t_GM {res['T2']['main']['t_gm']:.2f}, t_SR {res['T2']['main']['t_sr']:.2f})")
        if want_t1 and (res["T1"]["verdict"] != want_t1 or res["T2"]["main"]["class"] != want_t2):
            raise AssertionError(f"selftest: an injected {truth} effect did not give T1 {want_t1} and T2 {want_t2}")
        if truth == "null" and res["T1"]["verdict"] == "PASS":
            raise AssertionError("selftest: T1 passed on no effect")
    g = np.ones(10)
    try:
        audit_right_quantity(np.arange(10.0), np.arange(10.0), g, g * 2, g - COST, g)
    except TheoryError:
        pass
    else:
        raise AssertionError("the right-quantity audit did not fire on x_GM == x_SR")
    try:
        audit_right_quantity(np.arange(10.0), np.arange(10.0) ** 2, g, g * 2, g - COST + 1, g)
    except TheoryError:
        pass
    else:
        raise AssertionError("the right-quantity audit did not fire on a wrong cost")
    try:
        R.audit_fill_timing(lambda t0: t0)
    except Exception:
        pass
    else:
        raise AssertionError("the fill-timing audit did not fire on a fill at t0")
    print("selftest OK: money, classifier, right-quantity and fill-timing audits fire; an injected GM effect gives "
          "T1 PASS and T2 GM; no effect does not pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.run or a.check):
        ap.print_help()
        return 1
    if a.run and OUT.exists():
        raise TheoryError(f"{OUT.name} exists: D648 runs once (use --check)")
    doc = run()
    text = json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise TheoryError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    t1, t2_, t3 = doc["T1"], doc["T2"], doc["T3"]
    print(f"T1 {t1['verdict']}: mean ${t1['gate']['mean']:.2f} t {t1['gate']['t']:.2f} (NW {t1['gate']['t_nw5']:.2f}), "
          f"net ${t1['net_mean']:.2f}; placebo t {t1['C1_placebo']['t']:.2f}; rotation p50/p95 "
          f"{t1['C2_rotation']['p50']:.2f}/{t1['C2_rotation']['p95']:.2f} +- {t1['C2_rotation']['p95_se']:.2f}")
    print(f"T2 {t2_['verdict']}: {t2_['main']}; placebo {t2_['C3_placebo']['class']}")
    print(f"T3 {t3['verdict']}: {t3['fade']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
