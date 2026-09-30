"""D720 Stage 0: size the direction we already have. Spec:
docs/decisions/D720-STAGE-0-DESIGN-size-the-direction-we-have.md (63b40964), committed before this file existed.

    uv run python scripts/stage0_d720_size_the_direction.py --selftest     # synthetic only; reads no market data
    uv run python scripts/stage0_d720_size_the_direction.py --run          # once -> data/stage0_d720_size.json

Two NQ lines at one MNQ -- L1 the admitted MACD arm (D504/D503 through D669's panel and trade table) and L2 NQ F2
(D711's code at 15:30 through D716's build) -- each trade sized q in {0,1,2,3} MNQ by the walk-forward percentile tau
of D691's full size forecast M1 (D671's features plus ln IV/RV20) on NQ. Oracle first (A), calibration (B), four
declared rules (C), the enumerated rotation of tau (D), the accuracy curve (E), dependence (F); readings per s.4.

THE SEAL. NQ's 2024+ last hour is D716's joint-vault look, so nothing dated 2024-01-01 or later is used:
  * the hourly fixture is cut to sessions <= 2023-12-29 before D504's build;
  * the label's bars, GEX, settlement strip and option rows are cut at 2024-01-01 at read time, by lowering the
    module constants D663 T.RESERVED_FROM, D668 M.RESERVED_FROM and D691 I.CUT for the build, and the run_opening_v2
    module's RESERVED_FROM through a wrapper on D662's load_v2 (which builds a fresh module on every call);
  * D691's IV table is built directly (I.build_iv), never through iv_cached, so no 2024-cut table can land in
    D691's cache;
  * every frame is asserted to hold no session on or after 2024-01-01.
No per-date SqueezeMetrics series is written (the output holds aggregates only).
"""
from __future__ import annotations

import argparse
import contextlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from backtest_framework.validation.episodes import symmetric_trim  # noqa: E402
from backtest_framework.validation.filter_oracle import partial_oracle_score  # noqa: E402
from backtest_framework.validation.hurdle_p import p3  # noqa: E402

OUT = REPO / "data" / "stage0_d720_size.json"
PREREG = "63b40964"
CUT24 = "2024-01-01"
HI = "2023-12-29"
EDGE = 20
RHOS = (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)
N_DRAW, SEED = 200, 720
ACCOUNTS = (50_000.0, 150_000.0)
RULES = ("R0", "R1", "R2", "R3", "R4")


class D720Error(AssertionError):
    pass


def P(*a: Any, **k: Any) -> None:
    print(*a, **k, flush=True)


# ================================================================================ the rules (s.3 C)
def q_of(rule: str, tau: np.ndarray) -> np.ndarray:
    """Contracts per trade from its session's percentile. NaN tau is never passed (the window has finite tau)."""
    t = np.asarray(tau, float)
    if not np.isfinite(t).all():
        raise D720Error("a rule was asked for a trade without a finite tau")
    if rule == "R0":
        return np.ones_like(t)
    if rule == "R1":
        return np.where(t >= 2 / 3, 2.0, 1.0)
    if rule == "R2":
        return np.where(t < 1 / 3, 0.0, 1.0)
    if rule == "R3":
        return np.where(t < 1 / 3, 0.0, np.where(t >= 2 / 3, 2.0, 1.0))
    if rule == "R4":
        return np.where(t >= 0.9, 3.0, np.where(t >= 2 / 3, 2.0, 1.0))
    raise D720Error(f"unknown rule {rule}")


def pooled_terciles(x: np.ndarray) -> np.ndarray:
    """A pooled percentile in [0, 1) (the oracle's and the accuracy curve's; not walk-forward, declared as such)."""
    r = stats.rankdata(x, method="average")
    return (r - 0.5) / len(x)


# ================================================================================ statistics
def sharpe(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def sortino(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    dn = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
    return float(x.mean() / dn * math.sqrt(252)) if dn > 0 else float("nan")


def max_dd(x: np.ndarray) -> float:
    eq = np.cumsum(np.asarray(x, float))
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq))


def moments(x: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, float)
    s = x.std()
    if s == 0 or len(x) < 3:
        return float("nan"), float("nan")
    z = (x - x.mean()) / s
    return float((z ** 3).mean()), float((z ** 4).mean())


def trade_dist(v: np.ndarray) -> dict[str, Any]:
    v = np.sort(np.asarray(v, float))
    n = len(v)
    if n == 0:
        return {"trades": 0}
    k = max(1, int(n * 0.01))
    sk, ku = moments(v)
    win, loss = v[v > 0], v[v < 0]
    return {"trades": n, "mean": float(v.mean()), "median": float(np.median(v)), "win_rate": float((v > 0).mean()),
            "payoff": float(win.mean() / -loss.mean()) if len(win) and len(loss) else None, "skew": sk,
            "kurtosis": ku, "trim_k_each_side": k, "mean_ex_top1pct": float(v[:-k].mean()),
            "mean_ex_bottom1pct": float(v[k:].mean()), "mean_trimmed_both": float(v[k:-k].mean()) if n > 2 * k else None}


def book(daily: np.ndarray, gross_daily: np.ndarray, per_trade_net: np.ndarray, per_trade_q: np.ndarray,
         years: np.ndarray) -> dict[str, Any]:
    nyr = len(daily) / 252.0
    held = per_trade_q > 0
    by_year = {str(y): float(daily[years == y].sum()) for y in np.unique(years)}
    out = {"net_sharpe": sharpe(daily), "net_sortino": sortino(daily), "gross_sharpe": sharpe(gross_daily),
           "gross_sortino": sortino(gross_daily), "net_usd_a_year": float(daily.sum() / nyr),
           "gross_usd_a_year": float(gross_daily.sum() / nyr), "net_total": float(daily.sum()),
           "max_dd": max_dd(daily), "worst_day": float(daily.min()), "sigma_daily": float(daily.std(ddof=1)),
           "contracts_traded_a_year": float(per_trade_q.sum() / nyr), "trades_taken": int(held.sum()),
           "trade_distribution_per_contract_net": trade_dist(per_trade_net[held] / per_trade_q[held]),
           "trade_distribution_position_net": trade_dist(per_trade_net[held]),
           "net_by_year": by_year, "profitable_years": int(sum(v > 0 for v in by_year.values())),
           "years": len(by_year)}
    for acc in ACCOUNTS:
        pp = p3(daily, account=acc)
        out[f"p3a_breaches_a_year_{int(acc / 1000)}k"] = pp["p3a_breaches_per_year"]
    if len(daily) >= 21 and daily.sum() != 0:
        out["concentration_daily"] = symmetric_trim(daily)
    return out


# ================================================================================ a line's sized books
def sized(line: dict[str, Any], tau_tr: np.ndarray, rule: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(daily net, daily gross, per-trade position net, per-trade q) of `rule` on the line's window trades."""
    q = q_of(rule, tau_tr)
    n = len(line["cal"])
    pos_net = q * line["net1"]
    daily = np.bincount(line["sidx"], weights=pos_net, minlength=n)
    gdaily = np.bincount(line["sidx"], weights=q * line["g"], minlength=n)
    return daily, gdaily, pos_net, q


def delta_sharpe(line: dict[str, Any], tau_tr: np.ndarray, rule: str, base: float) -> float:
    return sharpe(sized(line, tau_tr, rule)[0]) - base


def delta_usd(line: dict[str, Any], tau_tr: np.ndarray, rule: str, base: float) -> float:
    return float(sized(line, tau_tr, rule)[0].sum()) - base


def rotation(line: dict[str, Any], tau_cal: np.ndarray, rule: str, stat: str = "sharpe") -> dict[str, Any]:
    """Enumerated rotation of the session tau series against the line's trades, offsets EDGE .. n - EDGE. `stat`:
    "sharpe" (the primary, R1's delta net Sharpe) or "usd" (A1's reported delta net dollars)."""
    n = len(tau_cal)
    r0 = sized(line, tau_cal[line["sidx"]], "R0")[0]
    fn, base = (delta_sharpe, sharpe(r0)) if stat == "sharpe" else (delta_usd, float(r0.sum()))
    obs = fn(line, tau_cal[line["sidx"]], rule, base)
    k0 = fn(line, np.roll(tau_cal, 0)[line["sidx"]], rule, base)
    if not math.isclose(k0, obs, rel_tol=0, abs_tol=1e-9):
        raise D720Error("rotation: offset 0 does not reproduce the observed statistic")
    ks = range(EDGE, n - EDGE)
    null = np.array([fn(line, np.roll(tau_cal, k)[line["sidx"]], rule, base) for k in ks])
    return {"stat": stat, "observed": obs, "offsets": len(null), "p50": float(np.median(null)),
            "p95": float(np.quantile(null, 0.95)), "p95_se": 0.0, "rank": float((null < obs).mean()),
            "above_p95": bool(obs > np.quantile(null, 0.95))}


def calibration(line: dict[str, Any], lab: np.ndarray, name: str) -> list[dict[str, Any]]:
    out = []
    for lo, hi, nm in ((0, 1 / 3, "low"), (1 / 3, 2 / 3, "mid"), (2 / 3, 1.01, "high")):
        m = (lab >= lo) & (lab < hi)
        g, a = line["g"][m], line["absm"][m]
        out.append({"label": name, "tercile": nm, "trades": int(m.sum()),
                    "mean_gross": float(g.mean()) if m.any() else None,
                    "median_gross": float(np.median(g)) if m.any() else None,
                    "mean_abs_move": float(a.mean()) if m.any() else None,
                    "efficiency": float(g.sum() / np.abs(g).sum()) if m.any() and np.abs(g).sum() > 0 else None,
                    "mean_net_per_mnq": float(line["net1"][m].mean()) if m.any() else None,
                    "win_rate": float((line["net1"][m] > 0).mean()) if m.any() else None})
    return out


def accuracy_curve(line: dict[str, Any], y_cal: np.ndarray, base: float) -> list[dict[str, Any]]:
    rng = np.random.default_rng(SEED)
    rows = []
    for rho in RHOS:
        ds = []
        for _ in range(N_DRAW):
            s = partial_oracle_score(y_cal, rho, rng)
            ds.append(delta_sharpe(line, pooled_terciles(s)[line["sidx"]], "R1", base))
        ds = np.array(ds)
        rows.append({"rho": rho, "p05": float(np.quantile(ds, 0.05)), "p50": float(np.median(ds)),
                     "p95": float(np.quantile(ds, 0.95))})
    return rows


# ================================================================================ audits
def join_audit(days_tr: np.ndarray, cal: np.ndarray, sidx: np.ndarray, tau_cal: np.ndarray, tau_tr: np.ndarray) -> None:
    """Second implementation: a trade's tau by a dict keyed on the session DATE, never by position."""
    look = {str(s): float(t) for s, t in zip(cal, tau_cal)}
    want = np.array([look[str(d)] for d in days_tr])
    if not np.array_equal(want, tau_tr):
        raise D720Error("join: a trade's tau is not its own session's")
    if not np.array_equal(cal[sidx], days_tr):
        raise D720Error("join: a trade's session index does not name its session")


def sign_audit_money() -> None:
    """A favourable move pays positively; q = 2 pays twice q = 1; q = 0 pays and costs nothing."""
    line = {"g": np.array([10.0, -6.0]), "net1": np.array([10.0 - 4.0, -6.0 - 4.0]), "sidx": np.array([0, 1]),
            "cal": np.array(["a", "b"])}
    d1 = sized(line, np.array([0.5, 0.5]), "R0")[0]
    d2 = sized(line, np.array([0.9, 0.9]), "R1")[0]
    d0 = sized(line, np.array([0.1, 0.1]), "R2")[0]
    if not (d1[0] > 0 and np.allclose(d2, 2 * d1) and np.all(d0 == 0)):
        raise D720Error("sign: sizing does not pay as declared")
    g2 = sized(line, np.array([0.9, 0.9]), "R1")[1]
    if np.allclose(g2, d2):
        raise D720Error("right quantity: the sized net equals the sized gross")


# ================================================================================ the seal
@contextlib.contextmanager
def lowered_cut(I: Any, S: Any, T: Any, M: Any) -> Iterator[None]:
    """Hold every cut constant in the label's import chain at 2024-01-01 for the build, and restore them."""
    old = (I.CUT, T.RESERVED_FROM, M.RESERVED_FROM, S.load_v2)
    orig = S.load_v2

    def load_v2_cut() -> Any:
        V = orig()
        V.RESERVED_FROM = CUT24
        return V

    I.CUT, T.RESERVED_FROM, M.RESERVED_FROM, S.load_v2 = CUT24, CUT24, CUT24, load_v2_cut
    try:
        yield
    finally:
        I.CUT, T.RESERVED_FROM, M.RESERVED_FROM, S.load_v2 = old


def no_session_after(idx: Any, what: str) -> None:
    s = pd.Index(idx).astype(str)
    if len(s) and (s >= CUT24).any():
        raise D720Error(f"seal: {what} holds a session on or after {CUT24}")


# ================================================================================ builds
def build_label() -> pd.DataFrame:
    import stage0_d662_gamma_product as S
    import stage0_d691_iv_size as I
    C, T, M = I.C, I.T, I.M
    with lowered_cut(I, S, T, M):
        fr = I.frames()["NQ"]
        no_session_after(fr["d"].index, "the NQ frame")
        no_session_after(fr["S"].index, "the NQ features")
        iv, _ = I.build_iv("NQ")
        no_session_after(iv.index, "the NQ IV table")
    if I.CUT != "2025-03-01" or T.RESERVED_FROM != "2025-03-01":
        raise D720Error("the cut constants were not restored")
    dz = I.design(fr, iv)
    sess, F0, y, ivrv = dz["sess"], dz["F0"], dz["y"], dz["ivrv"]
    F1 = np.column_stack([F0, ivrv])
    f1 = I.forecast(F1, y, I.SIGN1)
    idx = list(range(0, len(sess), max(1, len(sess) // 30)))
    old = C.SIGN
    C.SIGN = I.SIGN1
    try:
        C.forecast_audit(f1, F1, y, sess, idx)
        fl, _ = C.size_forecast(F1, y, leak=True)
        try:
            C.forecast_audit(fl, F1, y, sess, idx)
        except C.D671Error:
            pass
        else:
            raise D720Error("the forecast audit did not fire on the leaked canary")
    finally:
        C.SIGN = old
    tau = C.tiers(f1)
    C.tier_audit(tau, f1, idx)
    try:
        C.tier_audit(C.tiers(f1, leak=True), f1, idx)
    except C.D671Error:
        pass
    else:
        raise D720Error("the tier audit did not fire on the leaked canary")
    tau_y = C.tiers(np.where(np.isfinite(y), y, np.nan))
    lab = pd.DataFrame({"f": f1, "tau": tau, "y": y, "tau_y": tau_y}, index=pd.Index(sess, name="session"))
    lab.attrs["spearman_f_y_all"] = float(stats.spearmanr(f1[np.isfinite(f1) & np.isfinite(y)],
                                                          y[np.isfinite(f1) & np.isfinite(y)])[0])
    return lab


def build_arm() -> tuple[pd.DataFrame, dict[str, Any]]:
    import stage0_d669_macd_mechanism as A
    from d484_offdiagonal_and_macd import SPECS
    from d495_agree_confluence import FIX, META
    from d503_forward_book import series_window
    from d504_arm_full_history import FULL_LO, FULL_HI, ROOT, build

    meta = json.loads(Path(META).read_text(encoding="utf-8"))
    spec = json.loads(Path(SPECS).read_text(encoding="utf-8"))
    d_all = pd.read_csv(FIX, encoding="utf-8")
    d_all = d_all[d_all["day"].astype(str) <= HI].copy()           # the seal, before anything is built
    no_session_after(d_all["day"].unique(), "the hourly fixture")
    pk = build(d_all, meta, spec)
    s = series_window(ROOT, d_all, meta, FULL_LO, FULL_HI)
    days_k = np.asarray(pk["days"]).astype(str)
    m = (days_k >= A.LO) & (days_k <= A.HI)
    pn = {"O": pk["O"][m], "C": pk["C"][m], "AGREE": pk["AGREE"][m], "days": days_k[m], "first": pk["first"],
          "tick_pts": pk["tick_pts"], "tick_usd": pk["tick_usd"], "point_usd": pk["point_usd"],
          "cost_ticks": pk["cost"], "cost_usd": pk["cost"] * pk["tick_usd"], "series": s}
    t = A.trade_table(pn)
    A.lag_audit(pn, t)
    bad = t.copy()
    bad.loc[bad.index[0], "entry_t"] = int(bad["entry_t"].iloc[0]) + 1
    try:
        A.lag_audit(pn, bad)
    except A.GateError:
        pass
    else:
        raise D720Error("the arm's lag audit did not fire on a shifted trade")
    A.sign_audit(pn["point_usd"])
    ka = {"trades": int(len(t)), "net_total": float(t["net"].sum()), "gross_total": float(t["g"].sum())}
    fz = json.loads((REPO / "data" / "stage0_d669_macd_mechanism.json").read_text(encoding="utf-8"))["arm"]["performance"]
    if ka["trades"] != fz["trades"] or not math.isclose(ka["net_total"], fz["net_total"], abs_tol=1e-6) \
            or not math.isclose(ka["gross_total"], fz["gross_total"], abs_tol=1e-6):
        raise D720Error(f"the arm's known answer is not reproduced on the cut fixture: {ka} against D669's {fz}")
    if not np.allclose(t["net"].to_numpy(float), t["g"].to_numpy(float) - pn["cost_usd"], atol=1e-6):
        raise D720Error("right quantity: the arm's net is not gross less one round trip")
    tr = pd.DataFrame({"day": t["day"].astype(str).to_numpy(), "g": t["g"].to_numpy(float),
                       "net1": t["net"].to_numpy(float), "absm": np.abs(t["m"].to_numpy(float))})
    return tr, {"known_answer": ka, "cost_usd": float(pn["cost_usd"])}


def build_f2() -> tuple[pd.DataFrame, dict[str, Any]]:
    import vault_d716_nq_f2 as W
    bd = W.build(W.IN_END)
    no_session_after(bd["sn"], "the NQ F2 frame")
    ka = W.in_sample_answers(bd)["nq_own_window"]
    fz = json.loads((REPO / "data" / "vault_d716_power.json").read_text(encoding="utf-8"))["known_answers"]["nq_own_window"]
    if ka["trades"] != fz["trades"] or ka["take_sessions_sha256"] != fz["take_sessions_sha256"] \
            or not math.isclose(ka["mean_net"], fz["mean_net"], abs_tol=1e-9):
        raise D720Error(f"NQ F2's known answer is not reproduced: {ka} against {fz}")
    sn, Fn, Xn = bd["sn"], bd["Fn"], bd["Xn"]
    own = Fn["take"] & Fn["window"] & (sn <= W.IN_END)
    g = Xn["gross"].to_numpy(float)[own]
    cost = float(Xn.attrs["cost"])
    net = bd["net"][own]
    if not np.allclose(net, g - cost):
        raise D720Error("right quantity: F2's net is not gross less one round trip")
    tr = pd.DataFrame({"day": sn[own].astype(str), "g": g, "net1": net, "absm": np.abs(g)})
    return tr, {"known_answer": ka, "cost_usd": cost}


# ================================================================================ the study
def window_line(tr: pd.DataFrame, cal: np.ndarray) -> dict[str, Any]:
    pos = pd.Series(np.arange(len(cal)), index=cal)
    sidx_f = pos.reindex(tr["day"].to_numpy()).to_numpy(float)
    keep = np.isfinite(sidx_f)
    return {"g": tr["g"].to_numpy(float)[keep], "net1": tr["net1"].to_numpy(float)[keep],
            "absm": tr["absm"].to_numpy(float)[keep], "days": tr["day"].to_numpy()[keep],
            "sidx": sidx_f[keep].astype(int), "cal": cal, "dropped": int((~keep).sum()),
            "dropped_in_span": int((~keep & (tr["day"].to_numpy() >= cal[0])).sum())}


def study_line(name: str, tr: pd.DataFrame, lab: pd.DataFrame, cal: np.ndarray) -> dict[str, Any]:
    L = window_line(tr, cal)
    tau_cal = lab["tau"].reindex(cal).to_numpy(float)
    tauy_cal = lab["tau_y"].reindex(cal).to_numpy(float)
    y_cal = lab["y"].reindex(cal).to_numpy(float)
    f_cal = lab["f"].reindex(cal).to_numpy(float)
    tau_tr, tauy_tr = tau_cal[L["sidx"]], tauy_cal[L["sidx"]]
    join_audit(L["days"], cal, L["sidx"], tau_cal, tau_tr)
    years = np.array([s[:4] for s in cal])
    trade_ter = pooled_terciles(L["absm"])
    labels = {"forecast_tau": tau_tr, "oracle_day_tau_y": tauy_tr, "oracle_trade_abs_move": trade_ter}
    base_daily = sized(L, tau_tr, "R0")
    base_sh = sharpe(base_daily[0])
    res: dict[str, Any] = {"trades_in_window": int(len(L["g"])), "trades_outside_calendar": L["dropped"],
                           "trades_dropped_inside_span": L["dropped_in_span"], "sessions": int(len(cal)),
                           "window": [str(cal[0]), str(cal[-1])]}
    res["books"] = {}
    for lname, lt in labels.items():
        res["books"][lname] = {}
        for r in RULES:
            d, gd, pnet, q = sized(L, lt, r)
            b = book(d, gd, pnet, q, years)
            b["delta_vs_R0"] = {"net_usd_a_year": b["net_usd_a_year"] - (base_daily[0].sum() / (len(cal) / 252.0)),
                                "net_sharpe": b["net_sharpe"] - base_sh,
                                "net_sortino": b["net_sortino"] - sortino(base_daily[0]),
                                "max_dd": b["max_dd"] - max_dd(base_daily[0])}
            dyear = {y: float(d[years == y].sum() - base_daily[0][years == y].sum()) for y in np.unique(years)}
            tot = sum(dyear.values())
            b["delta_usd_by_year"] = dyear
            b["delta_years_positive"] = int(sum(v > 0 for v in dyear.values()))
            b["delta_largest_year_share"] = float(max(dyear.values()) / tot) if tot > 0 else None
            b["delta_share_2020_2022"] = float((dyear.get("2020", 0) + dyear.get("2022", 0)) / tot) if tot > 0 else None
            res["books"][lname][r] = b
    res["calibration"] = calibration(L, tau_tr, "forecast_tau") + calibration(L, tauy_tr, "oracle_day_tau_y") \
        + calibration(L, trade_ter, "oracle_trade_abs_move")
    t0 = time.time()
    res["rotation"] = {r: rotation(L, tau_cal, r) for r in ("R1", "R2", "R3", "R4")}
    res["rotation_delta_usd_A1"] = {r: rotation(L, tau_cal, r, "usd") for r in ("R1", "R2", "R3", "R4")}
    res["rotation_wall_s"] = time.time() - t0
    t0 = time.time()
    res["accuracy_curve_R1"] = accuracy_curve(L, y_cal, base_sh)
    res["accuracy_wall_s"] = time.time() - t0
    fin = np.isfinite(f_cal) & np.isfinite(y_cal)
    res["forecast_spearman_with_y_window"] = float(stats.spearmanr(f_cal[fin], y_cal[fin])[0])
    ft = f_cal[L["sidx"]]
    res["forecast_spearman_with_trade_abs_move"] = float(stats.spearmanr(ft, L["absm"])[0])
    res["forecast_spearman_with_trade_gross"] = float(stats.spearmanr(ft, L["g"])[0])
    # the reading (s.4)
    oracle_up = res["books"]["oracle_day_tau_y"]["R1"]["delta_vs_R0"]["net_sharpe"] > 0
    r1 = res["books"]["forecast_tau"]["R1"]
    rot1 = res["rotation"]["R1"]
    ny = len(r1["delta_usd_by_year"])
    lead = (rot1["above_p95"] and r1["delta_years_positive"] >= ny - 1
            and r1["delta_largest_year_share"] is not None and r1["delta_largest_year_share"] <= 0.5)
    res["reading"] = "NO CEILING" if not oracle_up else ("LEAD" if lead else "CEILING ONLY")
    res["_daily"] = {r: sized(L, tau_tr, r)[0] for r in ("R0", "R1")}
    return res


def run() -> int:
    t_start = time.time()
    P("[D720] building the size label (NQ, cut at 2024-01-01) ...")
    lab = build_label()
    no_session_after(lab.index, "the label")
    fin = np.isfinite(lab["tau"].to_numpy(float))
    cal = lab.index[fin].to_numpy(str)
    cal = cal[cal <= HI]
    P(f"[D720] label: {int(fin.sum())} sessions with tau, window {cal[0]} -> {cal[-1]}")
    P("[D720] L1, the MACD arm ...")
    arm, arm_meta = build_arm()
    P("[D720] L2, NQ F2 ...")
    f2, f2_meta = build_f2()
    sign_audit_money()
    out: dict[str, Any] = {"spec": "D720-STAGE-0-DESIGN-size-the-direction-we-have.md", "prereg": PREREG,
                           "seal": f"nothing on or after {CUT24}", "label_sessions_with_tau": int(fin.sum()),
                           "label_spearman_f_y_all_sessions": lab.attrs["spearman_f_y_all"],
                           "evaluation_window": [str(cal[0]), str(cal[-1])], "rules": {
                               "R0": "1", "R1": "2 if tau >= 2/3 else 1", "R2": "0 if tau < 1/3 else 1",
                               "R3": "0/1/2 by tercile", "R4": "3 if tau >= 0.9, 2 if >= 2/3, else 1"}}
    lines = {}
    for name, tr, meta in (("L1_macd_arm", arm, arm_meta), ("L2_nq_f2", f2, f2_meta)):
        P(f"[D720] {name}: study ...")
        res = study_line(name, tr, lab, cal)
        res.update(meta)
        lines[name] = res
    d1, d2 = lines["L1_macd_arm"].pop("_daily"), lines["L2_nq_f2"].pop("_daily")
    years = np.array([s[:4] for s in cal])
    comb = {}
    for r in ("R0", "R1"):
        dd = d1[r] + d2[r]
        comb[r] = {"net_sharpe": sharpe(dd), "net_sortino": sortino(dd), "net_usd_a_year": float(dd.sum() / (len(dd) / 252)),
                   "max_dd": max_dd(dd), "rho_L1_L2": float(np.corrcoef(d1[r], d2[r])[0, 1]),
                   "net_by_year": {y: float(dd[years == y].sum()) for y in np.unique(years)},
                   "p3a_150k": p3(dd, account=150_000.0)["p3a_breaches_per_year"]}
    out["lines"] = lines
    out["combined_L1_L2"] = comb
    out["wall_min"] = (time.time() - t_start) / 60
    OUT.write_text(json.dumps(out, indent=1, default=_json) + "\n", encoding="utf-8", newline="\n")
    for name, res in lines.items():
        P(f"[D720] {name}: {res['reading']}")
    P(f"[D720] wrote {OUT.name} in {out['wall_min']:.1f} min")
    return 0


def _json(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(type(o))


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []

    def must_raise(tag: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D720Error, AssertionError):
            return
        fails.append(tag)

    t = np.array([0.1, 0.4, 0.7, 0.95])
    want = {"R0": [1, 1, 1, 1], "R1": [1, 1, 2, 2], "R2": [0, 1, 1, 1], "R3": [0, 1, 2, 2], "R4": [1, 1, 2, 3]}
    for r, w in want.items():
        if not np.array_equal(q_of(r, t), np.array(w, float)):
            fails.append(f"rule {r}")
    must_raise("a NaN tau", lambda: q_of("R1", np.array([np.nan])))
    sign_audit_money()
    # the join audit fires on a shifted join
    cal = np.array(["2019-01-02", "2019-01-03", "2019-01-04"])
    tau_cal = np.array([0.2, 0.5, 0.9])
    days = np.array(["2019-01-03", "2019-01-04"])
    sidx = np.array([1, 2])
    join_audit(days, cal, sidx, tau_cal, tau_cal[sidx])
    must_raise("a shifted join", lambda: join_audit(days, cal, sidx, tau_cal, tau_cal[sidx - 1]))
    # rotation: offset 0 is the observed statistic, and a label with information beats its rotation
    # (A1) a fee-bound book whose efficiency rises with size: the informative label beats its rotation; with no fee
    # and flat efficiency the same label LOWERS the Sharpe (the statistic is risk-adjusted net, not size knowledge)
    def synth(fee: float, rising: bool) -> tuple[dict[str, Any], np.ndarray]:
        rng = np.random.default_rng(1)
        n = 600
        cal = np.array([f"s{i:04d}" for i in range(n)])
        size = np.exp(rng.normal(0, 0.5, n))
        tau_c = pooled_terciles(size + rng.normal(0, 0.1, n))
        p = np.clip(0.5 + 0.1 * size, 0, 0.9) if rising else 0.6
        g = size * np.where(rng.random(n) < p, 1.0, -1.0) * 20
        return {"g": g, "net1": g - fee, "absm": np.abs(g), "sidx": np.arange(n), "cal": cal}, tau_c

    line, tau_c = synth(8.0, True)
    if not rotation(line, tau_c, "R1")["above_p95"]:
        fails.append("an informative size label on a fee-bound book did not beat its rotation")
    if not rotation(line, tau_c, "R1", "usd")["above_p95"]:
        fails.append("an informative size label did not beat its dollar rotation")
    if rotation(line, np.random.default_rng(2).permutation(tau_c), "R1")["rank"] > 0.99:
        fails.append("an uninformative label sat above 99% of its rotation")
    line0, tau0 = synth(0.0, False)
    if rotation(line0, tau0, "R1")["above_p95"]:
        fails.append("with no fee and flat efficiency, R1 should not beat its rotation (A1)")
    rng = np.random.default_rng(3)
    # lowered_cut holds and restores, even when the body raises
    class Mod:
        pass
    I, S, T, M = Mod(), Mod(), Mod(), Mod()
    I.CUT = T.RESERVED_FROM = M.RESERVED_FROM = "2025-03-01"
    S.load_v2 = lambda: Mod()
    try:
        with lowered_cut(I, S, T, M):
            if not (I.CUT == T.RESERVED_FROM == M.RESERVED_FROM == CUT24 and S.load_v2().RESERVED_FROM == CUT24):
                fails.append("lowered_cut did not hold")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    if not (I.CUT == T.RESERVED_FROM == M.RESERVED_FROM == "2025-03-01") or hasattr(S.load_v2(), "RESERVED_FROM"):
        fails.append("lowered_cut did not restore")
    must_raise("a 2024 session", lambda: no_session_after(["2023-12-29", "2024-01-02"], "x"))
    # the book: trims and P3 run on a synthetic series
    d = rng.normal(5, 100, 400)
    b = book(d, d + 3, d[:50], np.ones(50), np.array(["2019"] * 200 + ["2020"] * 200))
    if b["years"] != 2 or b["trade_distribution_position_net"]["trades"] != 50:
        fails.append("book")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: rules, NaN refusal, sign in money and right quantity, the date join fires on a shift, rotation "
      "offset 0 = observed; an informative label on a fee-bound book beats both rotations, a random one does not, "
      "and with no fee and flat efficiency R1 does not (A1); "
      "lowered_cut holds and restores, the 2024 seal fires, the book runs")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        if OUT.exists():
            raise D720Error(f"{OUT.name} exists: D720 runs once")
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
