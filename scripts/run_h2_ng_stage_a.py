"""D630: H2 on NG, Stage A of the settlement flow ledger. The signed dollar return of one full-size NG contract from
the t0+1 fill to the W_end close, in the direction of the leveraged funds' predicted rebalance, on the ledger's
traded days.

The specification is `docs/decisions/D630-PRE-REG-h2-ng-the-settlement-move-in-the-funds-direction.md` (committed
96b34c2, amended a9f4a4b), both before this file existed.

  gross g_t = dir_t × (exit − fill) × 10,000;  net = g_t − $26 ($16 round trip + one tick of entry slippage)
  fill = the close of bar t0+1 (the last trade before t0+2 min); exit = the close of the 14:29 bar (before 14:30)
Gate (§4 and the amendment): mean g > 0 with t ≥ 2.2414 (Holm, two instruments, CL untested); net mean > 0 (within
one SE below zero is UNRESOLVED (net, potential)); the 11:30 placebo |t| < 2; the rotation null's p95 beaten by more
than 2 bootstrap SEs.

The estimation helpers (the rotation p95 and its SE, the lag audit) are D627's (`run_h1a_stage_a.py`); POWER's noise
drives the selftest (`ledger_power_h2_ng.py`).

    uv run python -W error::RuntimeWarning scripts/run_h2_ng_stage_a.py --selftest | --run | --check
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "decisions" / "D630-PRE-REG-h2-ng-the-settlement-move-in-the-funds-direction.md"
FLOW = REPO / "data" / "ledger_predicted_flow_daily.csv.gz"
BARS = REPO / "data" / "ng_minute_bars.csv.gz"
PANEL = REPO / "data" / "ledger_window_volume_daily.csv.gz"
CAL = REPO / "data" / "ledger_calendar_flags.csv"
OUT = REPO / "data" / "ledger_h2_ng_stage_a.json"
CUT = "2025-03-01"
T0 = ("13:50", "14:00", "14:10")
MULT, RT_USD, SLIP_USD = 10_000.0, 16.0, 10.0
COST = RT_USD + SLIP_USD
MNG_MULT, MNG_COST = 1_000.0, 3.0 + 1.0 + 1.0
T_HOLM = 2.2414
ROT_SEED = 630
EXIT_END, W_START = "14:30", "14:28"
FLAGS = ["index_roll_close", "fund_roll", "expiry", "eia_report", "ng_spot_last3"]
REQUIRED_OUTPUTS = ("verdict", "n", "gate", "net", "placebo", "rotation", "performance", "distribution",
                    "depends", "controls", "variants", "h4", "book_frame", "component_mng", "dsr", "excluded")


class H2Error(RuntimeError):
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


H = _load("run_h1a_stage_a")
P2 = _load("ledger_power_h2_ng")


# ------------------------------------------------------------------ the money, the clock, the verdict
def money(direction: float, fill: float, exit_px: float) -> float:
    """Gross dollars per full-size contract: + when the price moves the traded way."""
    return float(direction * (exit_px - fill) * MULT)


def audit_money(fn: Callable[[float, float, float], float] = money) -> None:
    """A rise of $0.010 after a buy books +$100 gross and +$74 net; after a sell, −$100."""
    if not (math.isclose(fn(1, 2.0, 2.01), 100.0) and math.isclose(fn(1, 2.0, 2.01) - COST, 74.0)
            and math.isclose(fn(-1, 2.0, 2.01), -100.0)):
        raise H2Error("sign audit: the money does not pay the traded way")


def add_min(hhmm: str, k: int) -> str:
    m = int(hhmm[:2]) * 60 + int(hhmm[3:]) + k
    return f"{m // 60:02d}:{m % 60:02d}"


def fill_end(t0: str) -> str:
    """The fill is the close of bar t0+1: the last trade strictly before t0+2 minutes."""
    return add_min(t0, 2)


def audit_fill_timing(fn: Callable[[str], str] = fill_end) -> None:
    for t0 in T0 + ("11:30",):
        e = fn(t0)
        if e != add_min(t0, 2) or add_min(e, -1) <= t0:
            raise H2Error(f"lag audit: the fill for t0 {t0} ends at {e}, not after the bar t0+1")
        if t0 in T0 and e > add_min(W_START, -3):
            raise H2Error(f"§7.3: the fill for {t0} is not complete 3 minutes before W_start")


def asof(minutes: np.ndarray, closes: np.ndarray, end: str, start_px: float) -> float:
    """The last close among bars stamped strictly before `end` (bars are start-stamped, so a bar stamped `end` has not
    begun); `start_px` (the volume panel's as-of price before the block) when no bar qualifies."""
    k = int(np.searchsorted(minutes, end, side="left"))
    return float(closes[k - 1]) if k > 0 else float(start_px)


def verdict(mean_g: float, t: float, net: float, se: float, t_plc: float, t_est: float, p95: float,
            p95_se: float) -> str:
    if not (mean_g > 0 and t >= T_HOLM):
        return "FAIL"
    if abs(t_plc) >= 2 or t_est <= p95:
        return "UNRESOLVED (control)"
    if t_est - p95 <= 2 * p95_se:
        return "UNRESOLVED (margin)"
    if net <= 0:
        return "UNRESOLVED (net, potential)" if net > -se else "REAL, NOT TRADABLE"
    return "PASS"


# ------------------------------------------------------------------ data
def build(read_returns: bool) -> dict[str, Any]:
    flow, star = H.load_flow("NG")  # D627's lag and sign audits on the predictor panel
    by_tau = {t: g.set_index("day") for t, g in flow.groupby("tau")}
    d = star[["day", "tau", "q_est", "I", "traded_ym", "p_held", "signal_day", "aum_long", "aum_inverse",
              "sigma_q_long", "sigma_q_inverse"]].copy().reset_index(drop=True)
    d["dir"] = np.sign(d["q_est"]).astype(float)
    d["traded"] = (d["signal_day"] == 1)
    d["t0_idx"] = d["tau"].map({t: i for i, t in enumerate(T0)})
    d["absI_usd"] = d["I"].abs() * MULT
    d["absI_px"] = d["I"].abs()
    d["aum"] = d["aum_long"] + d["aum_inverse"]
    d["estf"] = (d["sigma_q_long"] > 0) | (d["sigma_q_inverse"] > 0)
    d["year"] = d["day"].str[:4]
    for t in T0:
        d[f"sd_{t}"] = by_tau[t]["sigma_rem_ret"].reindex(d["day"]).to_numpy()
    cal = pd.read_csv(CAL, encoding="utf-8")
    cal = cal[cal["root"] == "NG"].set_index("date")
    d["flagged"] = (cal.loc[d["day"], FLAGS].sum(axis=1) > 0).to_numpy()
    for tau, pre in (("11:30", "plc"), ("14:10", "fx")):
        r = by_tau[tau].reindex(d["day"])
        d[f"{pre}_traded"] = (r["gate_pass"] == 1).to_numpy()
        d[f"{pre}_dir"] = np.sign(r["q_est"]).to_numpy()
        d[f"{pre}_ym"] = r["traded_ym"].to_numpy()
    d["plc_clean"] = (by_tau["11:30"]["n_stale"].reindex(d["day"]) == 0).to_numpy()
    out: dict[str, Any] = {"d": d, "flow": flow}
    if not read_returns:
        return out
    b = pd.read_csv(BARS, encoding="utf-8", usecols=["day", "ym", "minute", "high", "low", "close"])
    if (b["day"] >= CUT).any():
        raise H2Error("a bar on or after the cut is in memory")
    groups = {k: (g["minute"].to_numpy(), g["close"].to_numpy(), g["high"].to_numpy(), g["low"].to_numpy())
              for k, g in b.sort_values(["day", "ym", "minute"]).groupby(["day", "ym"], sort=False)}
    px = pd.read_csv(PANEL, encoding="utf-8", usecols=["root", "kind", "day", "ym", "px_1130", "px_1350", "px_1400",
                                                       "px_1410"])
    px = px[(px["root"] == "NG") & (px["kind"] == "outright")].set_index(["day", "ym"])
    if px.index.duplicated().any():
        raise H2Error("two NG outrights share a (day, month) in the volume panel")
    empty = (np.array([], dtype=object), np.array([]), np.array([]), np.array([]))
    audit_fill_timing()

    def series(day: str, ym: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        return groups.get((day, ym), empty)

    def start(day: str, ym: str, col: str) -> float:
        try:
            return float(px.at[(day, ym), col])
        except KeyError:
            return float("nan")

    cols: dict[str, list[float]] = {k: [] for k in (
        "m_13:50", "m_14:00", "m_14:10", "g_stress", "g_delay", "g_book", "h4_s5", "h4_sW", "fade", "m_plc", "m_fx",
        "hold_min")}
    curve_rows: list[dict[str, float]] = []
    for row in d.itertuples(index=False):
        mins, cl, hi, lo = series(row.day, row.traded_ym)
        s1350 = start(row.day, row.traded_ym, "px_1350")
        exit_px = asof(mins, cl, EXIT_END, s1350)
        for t in T0:
            fill = asof(mins, cl, fill_end(t), s1350)
            cols[f"m_{t}"].append((exit_px - fill) * MULT)
        t0 = row.tau
        fill = asof(mins, cl, fill_end(t0), s1350)
        dr = row.dir
        # the stress fill: the worst close among bars t0+1 .. t0+5 (§7.3)
        cands = [asof(mins, cl, add_min(t0, k), s1350) for k in range(2, 7)]
        worst = max(cands) if dr > 0 else min(cands)
        cols["g_stress"].append(money(dr, worst, exit_px))
        cols["g_delay"].append(money(dr, asof(mins, cl, add_min(t0, 3), s1350), exit_px))
        # the book frame (§7.4): stop at 1 x |I| adverse; early profit at 1 x |I| favourable before W_start
        stop, target = fill - dr * row.absI_px, fill + dr * row.absI_px
        book = exit_px
        held = (int(EXIT_END[:2]) * 60 + int(EXIT_END[3:])) - (int(t0[:2]) * 60 + int(t0[3:]))
        for m, h, lw in zip(mins, hi, lo):
            if m < add_min(t0, 2) or m >= EXIT_END:
                continue
            hit_stop = (lw <= stop) if dr > 0 else (h >= stop)
            hit_tgt = ((h >= target) if dr > 0 else (lw <= target)) and m < W_START
            if hit_stop or hit_tgt:
                book = stop if hit_stop else target
                held = (int(m[:2]) * 60 + int(m[3:])) - (int(t0[:2]) * 60 + int(t0[3:]))
                break
        cols["g_book"].append(money(dr, fill, book))
        cols["hold_min"].append(float(held))
        p0 = start(row.day, row.traded_ym, f"px_{t0[:2]}{t0[3:]}")
        cols["h4_s5"].append(money(dr, p0, asof(mins, cl, add_min(t0, 6), s1350)))
        cols["h4_sW"].append(money(dr, p0, exit_px))
        cols["fade"].append(-money(dr, exit_px, asof(mins, cl, "15:00", s1350)))
        if row.traded:
            cr = {"t0": float(T0.index(t0))}
            for k in range(0, 71, 5):
                e = add_min(t0, k + 1)
                if e <= "15:00":
                    cr[f"+{k}"] = money(dr, p0, asof(mins, cl, e, s1350))
            curve_rows.append(cr)
        # the placebo (11:30 ledger, 11:31 fill, 12:19 close) and the fixed-14:10 variant, on their own contracts
        pm, pc, _ph, _pl = series(row.day, row.plc_ym) if isinstance(row.plc_ym, str) else empty
        s1130 = start(row.day, row.plc_ym, "px_1130") if isinstance(row.plc_ym, str) else float("nan")
        cols["m_plc"].append((asof(pm, pc, "12:20", s1130) - asof(pm, pc, fill_end("11:30"), s1130)) * MULT)
        fm, fc, _fh, _fl = series(row.day, row.fx_ym) if isinstance(row.fx_ym, str) else empty
        sfx = start(row.day, row.fx_ym, "px_1350") if isinstance(row.fx_ym, str) else float("nan")
        cols["m_fx"].append((asof(fm, fc, EXIT_END, sfx) - asof(fm, fc, fill_end("14:10"), sfx)) * MULT)
    for name, vals in cols.items():
        d[name] = vals
    out["d"] = d
    out["curve"] = pd.DataFrame(curve_rows)
    return out


# ------------------------------------------------------------------ statistics
def mean_t(x: np.ndarray) -> dict[str, float]:
    x = x[np.isfinite(x)]
    se = float(x.std(ddof=1) / np.sqrt(len(x)))
    return {"n": int(len(x)), "mean": float(x.mean()), "se": se, "t": float(x.mean() / se)}


def nw_t(x: np.ndarray, lags: int = 5) -> float:
    sm = H._sm()
    x = x[np.isfinite(x)]
    return float(sm.OLS(x, np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags}).tvalues[0])


def distribution(x: np.ndarray) -> dict[str, float]:
    x = np.sort(x[np.isfinite(x)])
    k = max(1, int(math.ceil(0.01 * len(x))))
    w, lo = x[x > 0], x[x < 0]
    s = pd.Series(x)
    return {"count": int(len(x)), "mean": float(x.mean()), "median": float(np.median(x)),
            "win_rate": float((x > 0).mean()), "payoff": float(w.mean() / -lo.mean()) if len(w) and len(lo) else float("nan"),
            "skew": float(s.skew()), "kurtosis_excess": float(s.kurt()),
            "mean_ex_top_1pct": float(x[:-k].mean()), "mean_ex_bottom_1pct": float(x[k:].mean()),
            "mean_trimmed_both": float(x[k:-k].mean()), "trim_k": k}


def performance(d: pd.DataFrame, g: np.ndarray, cost: float) -> dict[str, Any]:
    C = _load_cs()
    daily_g = np.where(d["traded"].to_numpy() & np.isfinite(g), g, 0.0)
    daily_n = np.where(d["traded"].to_numpy() & np.isfinite(g), g - cost, 0.0)
    cum = np.cumsum(daily_n)
    dd = float((cum - np.maximum.accumulate(cum)).min())
    trades = d["traded"].to_numpy() & np.isfinite(g)
    return {"mean_gross": float(g[trades].mean()), "mean_net": float(g[trades].mean() - cost),
            "sharpe_gross": C.sharpe(daily_g), "sortino_gross": C.sortino(daily_g),
            "sharpe_net": C.sharpe(daily_n), "sortino_net": C.sortino(daily_n),
            "exposure_share_of_days": float(trades.mean()), "daily_vol_usd_net": float(daily_n.std(ddof=1)),
            "max_drawdown_usd_net": dd, "total_net_usd": float(daily_n.sum()),
            "mean_move_vs_cost": float(g[trades].mean() / cost), "breakeven_cost_usd_rt": float(g[trades].mean()),
            "_daily_net": daily_n}


def _load_cs() -> Any:
    from backtest_framework.validation import component_series as C
    return C


def signed(d: pd.DataFrame) -> np.ndarray:
    """g on each day at its own τ*, in its own direction."""
    m = d[[f"m_{t}" for t in T0]].to_numpy()
    return d["dir"].to_numpy() * m[np.arange(len(d)), d["t0_idx"].to_numpy()]


def rotation(d: pd.DataFrame, rng: np.random.Generator, n_rot: int = 1000) -> np.ndarray:
    M = d[[f"m_{t}" for t in T0]].to_numpy()
    tr, dr, t0 = d["traded"].to_numpy(), d["dir"].to_numpy(), d["t0_idx"].to_numpy()
    years = d["year"].to_numpy()
    yidx = [np.flatnonzero(years == y) for y in np.unique(years)]
    out = np.empty(n_rot)
    for i in range(n_rot):
        a, b, c = tr.copy(), dr.copy(), t0.copy()
        for idx in yidx:
            if len(idx) > 40:
                k = int(rng.integers(20, len(idx) - 20 + 1))
                a[idx], b[idx], c[idx] = np.roll(tr[idx], k), np.roll(dr[idx], k), np.roll(t0[idx], k)
        x = (b * M[np.arange(len(d)), c])[a]
        out[i] = mean_t(x)["t"]
    return out


def split(d: pd.DataFrame, g: np.ndarray, key: np.ndarray) -> dict[str, Any]:
    tr = d["traded"].to_numpy() & np.isfinite(g)
    res = {}
    for k in pd.unique(key[tr]):
        m = tr & (key == k)
        if m.sum() >= 5:
            res[str(k)] = mean_t(g[m])
    return res


def analyse(d: pd.DataFrame, curve: pd.DataFrame) -> dict[str, Any]:
    g = signed(d)
    tr = d["traded"].to_numpy()
    ok = tr & np.isfinite(g)
    excluded = {"traded_without_a_price": sorted(d.loc[tr & ~np.isfinite(g), "day"])}
    gate = mean_t(g[ok])
    gate["t_nw5"] = nw_t(g[ok])
    net = gate["mean"] - COST
    # right-quantity: the gate's returns are not the placebo's or the fixed-14:10 variant's (the cost arithmetic is
    # the money audit's)
    both = ok & np.isfinite(d["m_plc"].to_numpy())
    if np.allclose(g[both], (d["plc_dir"] * d["m_plc"]).to_numpy()[both]):
        raise H2Error("right-quantity: the gate's returns equal the placebo's")
    fx = (d["fx_dir"] * d["m_fx"]).to_numpy()
    if np.allclose(g[ok], fx[ok], equal_nan=True):
        raise H2Error("right-quantity: the gate's returns equal the fixed-14:10 variant's")
    # C1, the placebo
    pm = d["plc_traded"].to_numpy() & d["plc_clean"].to_numpy()
    pg = (d["plc_dir"] * d["m_plc"]).to_numpy()
    plc = mean_t(pg[pm & np.isfinite(pg)])
    # C2, the rotation
    rr = np.random.default_rng(ROT_SEED)
    ts = rotation(d, rr)
    p50, p95, p95_se = H.p95_with_se(ts, rr)
    verd = verdict(gate["mean"], gate["t"], net, gate["se"], plc["t"], gate["t"], p95, p95_se)
    perf = performance(d, g, COST)
    daily_net = perf.pop("_daily_net")
    years = d["year"].to_numpy()
    by_year = split(d, g, years)
    best_year = max(by_year, key=lambda y: by_year[y]["mean"] * by_year[y]["n"])
    contrib = np.sort(g[ok])[::-1]
    total = contrib.sum()
    half = int(np.searchsorted(np.cumsum(contrib), total / 2) + 1) if total > 0 else None
    k1 = max(1, int(math.ceil(0.01 * ok.sum())))
    idx_sorted = np.argsort(np.where(ok, g, -np.inf))[::-1]
    drop_best = ok.copy()
    drop_best[idx_sorted[:k1]] = False

    def terciles(v: np.ndarray) -> np.ndarray:
        q = np.nanquantile(v[ok], [1 / 3, 2 / 3])
        return np.digitize(v, q)

    iq = np.digitize(d["absI_usd"].to_numpy(), np.quantile(d["absI_usd"], [0.2, 0.4, 0.6, 0.8]))
    allg = np.isfinite(g)
    h3 = [float(g[allg & (iq == k)].mean()) for k in range(5)]
    ym = pd.DataFrame({"y": years[ok], "g": g[ok], "aum": d["aum"].to_numpy()[ok]}).groupby("y").mean()
    depends = {
        "by_year": by_year, "profitable_years": int(sum(v["mean"] > 0 for v in by_year.values())),
        "years": len(by_year), "best_year": best_year,
        "without_best_year": mean_t(g[ok & (years != best_year)]),
        "without_best_1pct_days": mean_t(g[drop_best]),
        "trades_for_half_the_pnl": half,
        "by_price_tercile": split(d, g, terciles(d["p_held"].to_numpy())),
        "by_t0": split(d, g, d["tau"].to_numpy()),
        "by_fund_size_tercile": split(d, g, terciles(d["aum"].to_numpy())),
        "h3_mean_by_absI_quintile_all_days": h3,
        "h3_spearman": float(pd.Series(h3).corr(pd.Series(range(5)), method="spearman")),
        "h3_inversions": int(sum(h3[i + 1] < h3[i] for i in range(4))),
        "h6_yearly_mean_vs_aum_corr": float(ym["g"].corr(ym["aum"])),
        "h6_yearly": {y: {"mean_g": float(r.g), "mean_aum": float(r.aum)} for y, r in ym.iterrows()}}
    un = ~tr & np.isfinite(g)
    a, b = g[ok], g[un]
    welch = (a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    controls = {"untraded_days_same_rule": mean_t(b), "traded_minus_untraded": float(a.mean() - b.mean()),
                "traded_minus_untraded_welch_t": float(welch),
                "without_estimated_f_days": mean_t(g[ok & ~d["estf"].to_numpy()]),
                "estimated_f_days": int((ok & d["estf"].to_numpy()).sum())}
    variant_series = {
        "primary": g, "fixed_14:10": np.where(d["fx_traded"].to_numpy(), fx, np.nan),
        "stress_fill": d["g_stress"].to_numpy(), "one_bar_delay": d["g_delay"].to_numpy(),
        "without_flagged_days": np.where(d["flagged"].to_numpy(), np.nan, g), "book_frame": d["g_book"].to_numpy()}
    variants: dict[str, Any] = {}
    sr_daily = []
    for name, v in variant_series.items():
        mask = (d["fx_traded"].to_numpy() if name == "fixed_14:10" else tr) & np.isfinite(v)
        daily = np.where(mask, v - COST, 0.0)
        variants[name] = {**mean_t(v[mask]), "mean_net": float(v[mask].mean() - COST),
                          "sharpe_net": _load_cs().sharpe(daily), "sortino_net": _load_cs().sortino(daily)}
        sr_daily.append(float(daily.mean() / daily.std(ddof=1)))
    two = np.where(ok, g - 2 * RT_USD - SLIP_USD, 0.0)
    variants["cost_2x"] = {"mean_net": float(g[ok].mean() - 2 * RT_USD - SLIP_USD),
                           "sharpe_net": _load_cs().sharpe(two), "sortino_net": _load_cs().sortino(two)}
    sr_daily.append(float(two.mean() / two.std(ddof=1)))
    variants["one_bar_delay_keeps_share_of_edge"] = float(variants["one_bar_delay"]["mean"] / gate["mean"])
    variants["book_frame_mean_minutes_held"] = float(d.loc[ok, "hold_min"].mean())
    # H4: the share of the move to W_end made by t0+5, overall and by |I| quintile
    s5, sW = d["h4_s5"].to_numpy(), d["h4_sW"].to_numpy()
    h4: dict[str, Any] = {
          "share_by_t0_plus_5": float(np.nanmean(s5[ok]) / np.nanmean(sW[ok])),
          "by_absI_quintile": {str(k): float(np.nanmean(s5[ok & (iq == k)]) / np.nanmean(sW[ok & (iq == k)]))
                               for k in range(5) if (ok & (iq == k)).sum() >= 5},
          "curve_mean_usd": {c: float(curve[c].mean()) for c in curve.columns if c.startswith("+")},
          "post_window_fade": mean_t(d["fade"].to_numpy()[ok])}
    h4["reading"] = "≤ 50% by t0+5 (deposit H4 passes)" if h4["share_by_t0_plus_5"] <= 0.5 else "> 50% by t0+5"
    gm = g[ok] * MNG_MULT / MULT
    dm = np.where(ok, g * MNG_MULT / MULT - MNG_COST, 0.0)
    dg = np.where(ok, g * MNG_MULT / MULT, 0.0)
    comp = {"contract": "MNG, 1,000 MMBtu", "cost_usd": MNG_COST, "mean_gross": float(gm.mean()),
            "mean_net": float(gm.mean() - MNG_COST), "sharpe_net": _load_cs().sharpe(dm),
            "sortino_net": _load_cs().sortino(dm), "sharpe_gross": _load_cs().sharpe(dg),
            "sortino_gross": _load_cs().sortino(dg), "hit_rate_net": float((gm - MNG_COST > 0).mean()),
            "skew_daily_net": float(pd.Series(dm).skew()),
            "correlation_with_ledger_components": "not computable: entries #2 (the MACD arm) and #3 (the NG winter "
                                                  "spread) have no daily P&L on disk"}
    D = _load_dsr()
    s = pd.Series(daily_net)
    sr = float(daily_net.mean() / daily_net.std(ddof=1))
    dsr = {"n_trials": len(sr_daily), "sr_daily_net": sr,
           "dsr": D.deflated_sharpe_ratio(sr, len(daily_net), float(s.skew()), float(s.kurt()) + 3.0,
                                          len(sr_daily), float(np.var(sr_daily, ddof=1))),
           "p_two_sided": float(2 * (1 - D._NORMAL.cdf(abs(gate["t"])))),
           }
    dsr["holm_adjusted_p"] = min(1.0, 2 * dsr["p_two_sided"])
    dsr["programme_bar_0.005_met"] = bool(dsr["holm_adjusted_p"] <= 0.005)
    return {"verdict": verd, "n": gate["n"], "first": d["day"].iloc[0], "last": d["day"].iloc[-1],
            "gate": gate, "net": {"mean_net": net, "cost_usd": COST, "one_se_band": gate["se"],
                                  "within_one_se_below_zero": bool(-gate["se"] < net <= 0)},
            "placebo": plc, "rotation": {"p50": p50, "p95": p95, "p95_se": p95_se, "t_est": gate["t"],
                                         "beats": bool(gate["t"] > p95), "margin": gate["t"] - p95, "draws": len(ts)},
            "performance": perf, "distribution": {"gross": distribution(g[ok]), "net": distribution(g[ok] - COST)},
            "depends": depends, "controls": controls, "variants": variants, "h4": h4,
            "book_frame": {**variants["book_frame"], "flow_reversal_exit": "not built (D630 §7)"},
            "component_mng": comp, "dsr": dsr,
            "excluded": {k: {"n": len(v), "days": v} for k, v in excluded.items()}}


def _load_dsr() -> Any:
    from backtest_framework.validation import dsr as D
    return D


def run() -> dict[str, Any]:
    b = build(read_returns=True)
    g = signed(b["d"])
    tr = b["d"]["traded"].to_numpy()
    if np.isfinite(g[tr]).mean() < 0.99:
        raise H2Error(f"only {np.isfinite(g[tr]).mean():.3f} of traded days have a fill and an exit price")
    r = analyse(b["d"], b["curve"])
    missing = [k for k in REQUIRED_OUTPUTS if k not in r]
    if missing:
        raise H2Error(f"REQUIRED_OUTPUTS missing {missing}")
    return {"spec": {"record": SPEC.name, "sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()},
            "inputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (FLOW, BARS, PANEL, CAL)},
            "cut": CUT, "deviations": [], "NG": r}


# ------------------------------------------------------------------ selftest (no in-sample return after t0)
def synthetic(d: pd.DataFrame, beta: float, rng: np.random.Generator, U: np.ndarray) -> pd.DataFrame:
    s = d.copy()
    n = len(s)
    sd = s[[f"sd_{t}" for t in T0]].to_numpy() * s["p_held"].to_numpy()[:, None] * MULT
    eff = (beta * s["absI_usd"] * s["dir"]).to_numpy()
    M = P2._block(U, n, rng) * sd + eff[:, None]
    for i, t in enumerate(T0):
        s[f"m_{t}"] = M[:, i]
    noise = lambda: (P2._block(U, n, rng)[:, 0] * sd[:, 0])  # noqa: E731
    g = s["dir"].to_numpy() * M[np.arange(n), s["t0_idx"].to_numpy()]
    s["m_plc"], s["m_fx"] = noise(), M[:, 2]
    s["g_stress"], s["g_delay"], s["g_book"] = g - 10.0, g + noise() * 0.1, g
    s["h4_s5"], s["h4_sW"], s["fade"], s["hold_min"] = 0.3 * g, g, noise(), 38.0
    return s


def selftest() -> int:
    for args, want in [((-1, 3, -27, 12, 0, 3, 1.5, .1), "FAIL"), ((30, 1.9, 4, 12, 0, 1.9, 1.5, .1), "FAIL"),
                       ((30, 3, 4, 12, 2.5, 3, 1.5, .1), "UNRESOLVED (control)"),
                       ((30, 3, 4, 12, 0, 3, 3.5, .1), "UNRESOLVED (control)"),
                       ((30, 3, 4, 12, 0, 3, 2.9, .1), "UNRESOLVED (margin)"),
                       ((20, 3, -6, 12, 0, 3, 1.5, .1), "UNRESOLVED (net, potential)"),
                       ((10, 3, -16, 12, 0, 3, 1.5, .1), "REAL, NOT TRADABLE"),
                       ((30, 3, 4, 12, 0, 3, 1.5, .1), "PASS")]:
        got = verdict(*args)
        if got != want:
            raise H2Error(f"verdict{args} = {got}, not {want}")
    print("  verdict ladder: as D630 §6 and its amendment (the net-potential row included)")
    audit_money()
    try:
        audit_money(lambda dr, f, e: dr * (f - e) * MULT)
    except H2Error:
        print("  sign audit in money: +$100 / +$74 net / -$100, and RAISES on a flipped book")
    else:
        raise H2Error("the money audit did not fire on a flipped book")
    audit_fill_timing()
    try:
        audit_fill_timing(lambda t0: add_min(t0, 1))
    except H2Error:
        print("  lag audit: the fill ends after bar t0+1, and RAISES on a fill at t0's own bar")
    else:
        raise H2Error("the fill-timing audit did not fire")
    mins = np.array(["13:49", "13:50", "13:51", "13:52"], dtype=object)
    cl = np.array([1.0, 2.0, 3.0, 99.0])
    if asof(mins, cl, "13:52", 0.5) != 3.0 or asof(mins, cl, "13:49", 0.5) != 0.5:
        raise H2Error("as-of: a bar at or after `end` was used, or the start price was not")
    print("  as-of: a bar stamped at the end is never used; the start price fills an empty block")
    b = build(read_returns=False)
    base = b["flow"]
    for what, brk in {"a NAV dated its own day": lambda f: f.assign(navdate_long=f["day"].where(
                          f.index == f.index[0], f["navdate_long"])),
                      "q_est off q1 x f_est": lambda f: f.assign(q_est=f["q_est"] * 1.001),
                      "a flipped q1 sign": lambda f: f.assign(q1_inverse=-f["q1_inverse"])}.items():
        try:
            H.audit_flow(brk(base.copy()))
        except H.H1aError:
            continue
        raise H2Error(f"D627's audit did not fire on {what}")
    print("  D627's lag and sign audits RAISE on each of 3 breaks")
    U = P2.presample()["_U"]
    res = {}
    for beta in (0.5, 0.0):
        s = synthetic(b["d"], beta, np.random.default_rng(11), U)
        curve = pd.DataFrame({"+0": s.loc[s["traded"], "h4_s5"], "+35": s.loc[s["traded"], "h4_sW"]})
        r = analyse(s, curve)
        missing = [k for k in REQUIRED_OUTPUTS if k not in r]
        if missing:
            raise H2Error(f"synthetic analyse is missing {missing}")
        res[beta] = r["verdict"]
    if res[0.5] != "PASS" or res[0.0] == "PASS":
        raise H2Error(f"selftest verdicts {res}")
    print(f"  analyse() end to end on synthetic data: beta 0.5 -> {res[0.5]}; beta 0 -> {res[0.0]}")
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
        raise H2Error(f"{OUT.name} exists: H2 on NG has been run once (D630). Use --check to recompute.")
    res = run()
    text = json.dumps(res, indent=1, sort_keys=True, default=float) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise H2Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    r = res["NG"]
    print(f"NG H2: {r['verdict']}  n {r['n']}  mean g ${r['gate']['mean']:.2f} (t {r['gate']['t']:.2f}, NW "
          f"{r['gate']['t_nw5']:.2f})  net ${r['net']['mean_net']:.2f}  placebo t {r['placebo']['t']:.2f}  rotation "
          f"p50 {r['rotation']['p50']:.2f} p95 {r['rotation']['p95']:.2f} ± {r['rotation']['p95_se']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
