"""D694 Stage 1: does the break of yesterday's range carry on "coiled" days, quiet in realised range (D672's C1) but
priced for a move by the options market (D691's walk-forward IV/RV20 percentile >= 1/2)? ES and NQ, nothing pooled.
Spec: docs/decisions/D694-STAGE-1-DESIGN-the-break-on-coiled-days.md (8cffb181).

    uv run python scripts/stage1_d694_coiled_break.py --selftest
    uv run python scripts/stage1_d694_coiled_break.py --time     # builds the bundle, times a few offsets, projects
    uv run python scripts/stage1_d694_coiled_break.py --run      # once

In-sample development, 2018-01-09 -> 2025-02-28 (every loader cuts at 2025-03-01; the vault is never read). The MACD
arm's daily series (for the component line's rho) is truncated below 2025-03-01 the moment it is built. Dealer gamma
(GEX): SqueezeMetrics, prior row only, never written per date. The trade is D668's E4 plain break built as D680's runner
builds it, generalised per root; friction once (D668-A2). Writes data/stage1_d694_coiled_break.json (statistics only).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d691_iv_size as D  # noqa: E402

C = D.C
M, T, X = C.M, C.T, C.X
DATA = D.DATA
ROOTS = ("ES", "NQ")
CUT, WINDOW_FROM = "2025-03-01", "2018-01-09"
COVID, ERA_SPLIT = ("2020-02-01", "2020-04-30"), "2022-05-16"
THETA, MIN_COILED, EDGE = 0.5, 60, 21
EP_K, BURN_IN, MIN_FILTERED = 2.0, 40, 30
OUT = REPO / "data" / "stage1_d694_coiled_break.json"
CACHE = REPO / "temp" / "d694_bundle.pkl"
KNOWN_JSON = REPO / "data" / "diag_d677_single_count_index.json"
FROZEN_D680 = REPO / "data" / "FROZEN_vault_d680_nq_compression.json"
D691_JSON = REPO / "data" / "stage0_d691_iv_size.json"
IMPORTED = ("stage0_d691_iv_size.py", "stage0_d671_break_construction.py", "stage0_d668_break_predictor.py",
            "stage0_d666_rebreak.py", "stage0_d663_per_root_gamma_break.py")


class D694Error(RuntimeError):
    pass


# ================================================================================ statistics
def welch(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se), float(se)


def sharpe(x: np.ndarray, per_year: float) -> float:
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(per_year)) if s > 0 else float("nan")


def sortino(x: np.ndarray, per_year: float) -> float:
    dn = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(x.mean() / dn * math.sqrt(per_year)) if dn > 0 else float("nan")


# ================================================================================ the trade (D680's builder, per root)
def cost_lines(r: str) -> dict[str, float]:
    c = M.micro_costs()[r]
    single = 3.0 + c["crossing_ticks"] * c["tick_usd"]
    if abs(c["cost_usd"] - (single + c["tick_usd"])) > 1e-12:
        raise D694Error(f"{r}: the cost file's line is not $3 + crossing + one tick")
    return {"usd_per_point": c["usd_per_point"], "tick": M.TICK_PTS[r], "cost_prereg_usd": c["cost_usd"],
            "cost_single_usd": single, "crossing_ticks": c["crossing_ticks"]}


def gross_bp(D_: int, entry: float, px: float) -> float:
    return D_ * (px / entry - 1) * 1e4


def trades(r: str, d: pd.DataFrame, bars: dict) -> pd.DataFrame:
    """Every plain break of root r: at the level (friction once) and, for the reproduction, with D672's fill ticks."""
    cl = cost_lines(r)
    rows = []
    try:
        for s, rec in d.iterrows():
            bb = bars.get((r, s))
            if bb is None:
                continue
            Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
            X.TICK = cl["tick"]
            p = X.plain_break(bb, Lh, Ll, A)
            if p is None:
                continue
            px, _ = X.exit_trade(bb, p["i"], p["D"], p["entry"], p["L"], A, 0.0, "E4")
            X.TICK = 0.0
            p0 = X.plain_break(bb, Lh, Ll, A)
            if p0 is None or p0["i"] != p["i"] or p0["D"] != p["D"]:
                raise D694Error(f"{r} {s}: the break moved when the fill tick was removed")
            px0, _ = X.exit_trade(bb, p0["i"], p0["D"], p0["entry"], p0["L"], A, 0.0, "E4")
            rows.append({"session": s, "D": p["D"], "entry": p["entry"], "level": p0["entry"],
                         "gross_prereg": gross_bp(p["D"], p["entry"], px), "gross": gross_bp(p0["D"], p0["entry"], px0)})
    finally:
        X.TICK = cl["tick"]
    tr = pd.DataFrame(rows).sort_values("session").reset_index(drop=True)
    tr["net_prereg"] = tr["gross_prereg"] - cl["cost_prereg_usd"] / cl["usd_per_point"] / tr["entry"] * 1e4
    tr["cost"] = cl["cost_single_usd"] / cl["usd_per_point"] / tr["level"] * 1e4
    tr["net"] = tr["gross"] - tr["cost"]
    tr["cost_prereg_bp"] = cl["cost_prereg_usd"] / cl["usd_per_point"] / tr["level"] * 1e4
    return tr


def sign_audit(gfn: Callable[[int, float, float], float] = gross_bp) -> None:
    """In money: a long break into a rising day and a short break into its mirror image both pay, by about the same."""
    m = np.arange(570, 960, dtype=float)
    path = 100.0 + 3.0 * (m - 570) / (959 - 570)
    got = []
    old = X.TICK
    X.TICK = 0.0
    try:
        for sgn in (1, -1):
            p = 100.0 + sgn * (path - 100.0)
            bb = {"m": m, "o": p, "h": p + 0.01, "l": p - 0.01, "c": p}
            b = X.plain_break(bb, 100.5, 99.5, 1.0)
            if b is None or b["D"] != sgn:
                raise D694Error("sign: the synthetic break did not fire in the path's direction")
            px, _ = X.exit_trade(bb, b["i"], b["D"], b["entry"], b["L"], 1.0, 0.0, "E4")
            got.append(gfn(b["D"], b["entry"], px))
    finally:
        X.TICK = old
    if not (got[0] > 0 and got[1] > 0 and abs(got[0] - got[1]) / got[0] < 0.1):
        raise D694Error(f"sign: a favourable long and its mirrored short do not both pay ({got})")


def right_quantity(tr: pd.DataFrame) -> None:
    """The gross is at the level (the fill tick removed), and the cost is the single count."""
    drag = float((tr["gross"] - tr["gross_prereg"]).mean())
    if not drag > 0:
        raise D694Error(f"right quantity: the scored gross is not the at-level trade (drag {drag})")
    if not (tr["cost"] < tr["cost_prereg_bp"]).all():
        raise D694Error("right quantity: the cost is not the single count")


# ================================================================================ frames, labels, forecasts
def load() -> tuple[dict[str, dict[str, Any]], dict]:
    """D691's frames (the same functions and cuts), plus the bar arrays the trades need."""
    b, use, _gd, R = M.load_bars(DATA, False, ROOTS)
    C._R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=ROOTS)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < CUT].set_index("date")["gex"].astype(float).sort_index()
    cal = pd.read_csv(DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    fr = {}
    for r in ROOTS:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        if (d.index >= CUT).any():
            raise D694Error("seal: a session on or after 2025-03-01 reached the frame")
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        on = C.overnight(b, r)
        C.overnight_audit(on)
        S_ = C.session_features(d, on, cal[cal["root"] == r].set_index("day"))
        D.target_audit(S_, d)
        fr[r] = {"d": d, "S": S_}
    return fr, bars


def labels(fr_r: dict[str, Any], iv_tab: pd.DataFrame) -> pd.DataFrame:
    d, S_ = fr_r["d"], fr_r["S"]
    dz = D.design(fr_r, iv_tab)
    sess = dz["sess"]
    step = max(1, len(sess) // 12)
    p_rv, p_on = C.tiers(S_["rv5"].to_numpy(float)), C.tiers(S_["on_range"].to_numpy(float))
    comp = (p_rv + p_on) / 2
    ctier = C.tiers(comp)
    C.tier_audit(ctier, comp, list(range(0, len(comp), step)))
    ivrv = dz["ivrv"]
    p_iv = C.tiers(ivrv)
    C.tier_audit(p_iv, ivrv, list(range(0, len(ivrv), step)))
    lnrv = np.log(dz["rv"])
    p_rv20 = C.tiers(-lnrv)
    F0, y = dz["F0"], dz["y"]
    f0 = D.forecast(F0, y, D.SIGN0)  # = D671's size forecast (D672's window is defined by its tier)
    F1 = np.column_stack([F0, ivrv])
    f1 = D.forecast(F1, y, D.SIGN1)
    old = C.SIGN
    C.SIGN = D.SIGN1
    try:
        C.forecast_audit(f1, F1, y, sess, list(range(0, len(sess), max(1, len(sess) // 25))))
    finally:
        C.SIGN = old
    atr = d["atr20"].reindex(S_.index).to_numpy(float)
    pc = d["prior_close"].reindex(S_.index).to_numpy(float)
    return pd.DataFrame({
        "ctier": ctier, "t671": C.tiers(f0), "p_iv": p_iv, "p_rv20": p_rv20, "ivrv": ivrv, "lniv": dz["lniv"],
        "lnrv": lnrv, "rv5": S_["rv5"].to_numpy(float), "on_range": S_["on_range"].to_numpy(float),
        "lnatr": np.log(atr / pc), "f0": f0, "f1": f1, "P": np.exp(f1) * atr / pc * 1e4, "y": y,
        "open": d["open"].reindex(S_.index).to_numpy(float), "close": d["close"].reindex(S_.index).to_numpy(float)},
        index=pd.Index(sess, name="session"))


def d691_reproduced(lab: pd.DataFrame, r: str) -> float:
    """The feature's identity: D691's registered loss differential from the same table and forecasts."""
    sess = lab.index.to_numpy(str)
    y = lab["y"].to_numpy(float)
    e0, e1 = y - lab["f0"].to_numpy(float), y - lab["f1"].to_numpy(float)
    ev = (sess >= WINDOW_FROM) & np.isfinite(e0) & np.isfinite(e1)
    got = float((e0[ev] ** 2 - e1[ev] ** 2).mean())
    want = json.loads(D691_JSON.read_text(encoding="utf-8"))["roots"][r]["gate_S"]["a_dbar"]
    if abs(got - want) > 1e-12:
        raise D694Error(f"{r}: D691's d-bar not reproduced ({got} vs {want})")
    return got


def bundle_key() -> str:
    parts = [f"{p.name}:{p.stat().st_mtime_ns}" for p in [Path(__file__)] + [REPO / "scripts" / f for f in IMPORTED]]
    parts += [f"{p.name}:{p.stat().st_mtime_ns}" for p in sorted((DATA / "fixtures").glob("*.gz"))]
    parts += [f"{p.name}:{p.read_text(encoding='utf-8')}" for p in sorted((REPO / "temp").glob("d691_iv_*.key"))]
    return hashlib.sha256(";".join(parts).encode()).hexdigest()


def get_bundle() -> dict[str, Any]:
    """Trades and labels per root, cached in temp/ keyed on this runner's, every imported module's and every fixture's
    mtimes and D691's IV cache keys."""
    key = bundle_key()
    if CACHE.exists():
        with CACHE.open("rb") as fh:
            got = pickle.load(fh)
        if got.get("key") == key:
            return got
    fr, bars = load()
    out: dict[str, Any] = {"key": key}
    for r in ROOTS:
        iv_tab, _ = D.iv_cached(r)
        lab = labels(fr[r], iv_tab)
        tr = trades(r, fr[r]["d"], bars)
        for c in lab.columns:
            tr[c] = lab[c].reindex(tr["session"]).to_numpy()
        out[r] = {"tr": tr, "lab": lab}
    CACHE.parent.mkdir(exist_ok=True)
    with CACHE.open("wb") as fh:
        pickle.dump(out, fh)
    return out


def known_answer(tr: pd.DataFrame, r: str) -> dict[str, Any]:
    j = json.loads(KNOWN_JSON.read_text(encoding="utf-8"))["roots"][r]["D672_C1"]
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    got = {"trades": int(c1.sum()), "net_prereg": float(tr.loc[c1, "net_prereg"].mean()),
           "net_single": float(tr.loc[c1, "net"].mean()), "gross_level": float(tr.loc[c1, "gross"].mean())}
    if got["trades"] != j["trades"] or abs(got["net_prereg"] - j["D672_net"][0]) > 1e-9 \
            or abs(got["net_single"] - j["single_count_net"][0]) > 1e-9:
        raise D694Error(f"{r} known answer: {got} against D672 / D672-A1's {j}")
    if r == "NQ":
        ka = json.loads(FROZEN_D680.read_text(encoding="utf-8"))["known_answer"]
        if abs(got["gross_level"] - ka["gross_level"]) > 1e-9:
            raise D694Error(f"NQ known answer: at-level gross {got['gross_level']} vs D680's {ka['gross_level']}")
    return got


# ================================================================================ the expected-profit filter (Gate 2)
def pi_hat(sess: np.ndarray, ratio: np.ndarray, leak: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Walk-forward mean of gross / P over EARLIER trades with finite P (one trade a session, so earlier = earlier
    session); returns (pi_hat, count of earlier trades). `leak` = True includes the trade itself (the canary)."""
    fin = np.isfinite(ratio)
    cs = np.cumsum(np.where(fin, ratio, 0.0))
    cn = np.cumsum(fin)
    if leak:
        s, n = cs, cn
    else:
        s, n = np.r_[0.0, cs[:-1]], np.r_[0, cn[:-1]]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, s / np.maximum(n, 1), np.nan), n


def pi_audit(sess: np.ndarray, ratio: np.ndarray, pi: np.ndarray, idx: list[int]) -> None:
    """Second implementation, keyed on the session DATE: the mean over trades dated strictly before."""
    for i in idx:
        m = (sess < sess[i]) & np.isfinite(ratio)
        want = float(ratio[m].mean()) if m.any() else float("nan")
        if not (np.isnan(want) and np.isnan(pi[i])) and not np.isclose(want, pi[i], rtol=0, atol=1e-12):
            raise D694Error(f"lag: pi-hat at {sess[i]} uses trades that are not strictly earlier")


# ================================================================================ the ingredient null
_W: dict[str, Any] = {}


def residual(lab: pd.DataFrame, fit_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """u = ln IV - OLS fit on ln RV20, rv5, on_range, ln(ATR20 / prior close); OLS over the window, applied wherever
    every term is finite (the rotation's domain F)."""
    Xr = np.column_stack([np.ones(len(lab)), lab[["lnrv", "rv5", "on_range", "lnatr"]].to_numpy(float)])
    yv = lab["lniv"].to_numpy(float)
    F = np.isfinite(Xr).all(axis=1) & np.isfinite(yv) & np.isfinite(lab["ivrv"].to_numpy(float))
    fm = fit_mask & F
    beta, *_ = np.linalg.lstsq(Xr[fm], yv[fm], rcond=None)
    u = np.full(len(lab), np.nan)
    u[F] = yv[F] - Xr[F] @ beta
    return u, F, [float(v) for v in beta]


def top_k_mean(p: np.ndarray, pos: np.ndarray, g: np.ndarray, k: int) -> tuple[float, np.ndarray]:
    """Mean gross of the k C1 trades with the highest p (NaN last; ties to the earlier session)."""
    key = np.where(np.isfinite(p[pos]), p[pos], -np.inf)
    order = np.sort(np.lexsort((pos, -key))[:k])  # back to trade order, so the sum matches a boolean mask's bit for bit
    return float(g[order].mean()), order


def rot_ingredient(k: int, ivrv: np.ndarray, u: np.ndarray, F: np.ndarray, pos: np.ndarray, g: np.ndarray, kk: int) -> float:
    iv = ivrv.copy()
    uu = u[F]
    iv[F] = ivrv[F] + (np.roll(uu, k) - uu)
    return top_k_mean(C.tiers(iv), pos, g, kk)[0]


def rot_whole(k: int, ivrv: np.ndarray, pos: np.ndarray, g: np.ndarray, kk: int) -> float:
    fin = np.isfinite(ivrv)
    iv = ivrv.copy()
    iv[fin] = np.roll(ivrv[fin], k)
    return top_k_mean(C.tiers(iv), pos, g, kk)[0]


def _init(ivrv, u, F, pos, g, kk) -> None:
    _W.update(ivrv=ivrv, u=u, F=F, pos=pos, g=g, kk=kk)


def _job(items: list[tuple[str, int]]) -> list[tuple[str, int, float]]:
    w = _W
    return [(kind, k, rot_ingredient(k, w["ivrv"], w["u"], w["F"], w["pos"], w["g"], w["kk"]) if kind == "ingredient"
             else rot_whole(k, w["ivrv"], w["pos"], w["g"], w["kk"])) for kind, k in items]


def rotations(ivrv, u, F, pos, g, kk, items: list[tuple[str, int]], workers: int) -> dict[tuple[str, int], float]:
    chunks = [items[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(ivrv, u, F, pos, g, kk)) as pool:
        return {(kind, k): v for part in pool.map(_job, chunks) for kind, k, v in part}


# ================================================================================ reporting
def four_groups(t: pd.DataFrame, win_sessions: np.ndarray, usd_pt: float, arm: pd.Series | None,
                other_daily: pd.Series | None = None) -> dict[str, Any]:
    g, net = t["gross"].to_numpy(float), t["net"].to_numpy(float)
    n = len(t)
    if n < 3:
        return {"trades": n}
    lvl = t["level"].to_numpy(float)
    g_usd, n_usd = g * lvl * usd_pt / 1e4, net * lvl * usd_pt / 1e4
    years = len(win_sessions) / 252
    tpy = n / years
    daily = pd.Series(0.0, index=win_sessions)
    daily.loc[t["session"].to_numpy(str)] = n_usd
    dg = pd.Series(0.0, index=win_sessions)
    dg.loc[t["session"].to_numpy(str)] = g_usd
    eq = daily.cumsum().to_numpy()
    k1 = max(1, int(math.floor(0.01 * n)))
    srt = np.sort(net)
    wins, losses = net[net > 0], net[net <= 0]
    yrs = t["session"].str[:4].to_numpy()
    by_year = {y: {"n": int((yrs == y).sum()), "net_bp": float(net[yrs == y].mean())} for y in sorted(set(yrs))}
    tot = float(g_usd.sum())
    gs = np.sort(g_usd)[::-1]
    half = int(np.searchsorted(np.cumsum(gs), tot / 2) + 1) if tot > 0 else None
    side = t["D"].to_numpy(int)
    era = t["session"].to_numpy(str) >= ERA_SPLIT
    best = t.assign(g=g).nlargest(5, "g")
    worst = t.assign(g=g).nsmallest(5, "g")
    out = {
        "trades": n, "trades_per_year": tpy, "exposure_share_of_sessions": n / len(win_sessions),
        "gross_bp": float(g.mean()), "net_bp": float(net.mean()), "t_gross_hac": D.nw_t(g)[0], "t_net_hac": D.nw_t(net)[0],
        "gross_usd_per_trade": float(g_usd.mean()), "net_usd_per_trade": float(n_usd.mean()),
        "per_trade_sharpe_net": sharpe(net, tpy), "per_trade_sortino_net": sortino(net, tpy),
        "per_trade_sharpe_gross": sharpe(g, tpy), "per_trade_sortino_gross": sortino(g, tpy),
        "daily_sharpe_net": sharpe(daily.to_numpy(), 252), "daily_sortino_net": sortino(daily.to_numpy(), 252),
        "daily_sharpe_gross": sharpe(dg.to_numpy(), 252), "daily_sortino_gross": sortino(dg.to_numpy(), 252),
        "daily_vol_usd": float(daily.std(ddof=1)), "max_drawdown_usd": float(np.max(np.maximum.accumulate(eq) - eq)),
        "mean_abs_move_bp": float(np.abs(g).mean()), "two_c_bp": float(2 * t["cost"].mean()),
        "breakeven_cost_bp_round_trip": float(g.mean()), "breakeven_cost_usd_round_trip": float(g_usd.mean()),
        "median_net_bp": float(np.median(net)), "win_rate": float((net > 0).mean()),
        "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) and losses.mean() < 0 else float("nan"),
        "skew": float(stats.skew(net)), "kurtosis_excess": float(stats.kurtosis(net)),
        "trim_1pct_each_tail": {"k": k1, "ex_top": float(srt[:-k1].mean()), "ex_bottom": float(srt[k1:].mean()),
                                "trimmed": float(srt[k1:-k1].mean())},
        "top_trades": [{"session": s, "side": int(dd), "gross_bp": float(v)} for s, dd, v in zip(best["session"], best["D"], best["g"])],
        "worst_trades": [{"session": s, "side": int(dd), "gross_bp": float(v)} for s, dd, v in zip(worst["session"], worst["D"], worst["g"])],
        "top_1_5_10_share_of_gross_usd": [float(gs[:k].sum() / tot) if tot > 0 else float("nan") for k in (1, 5, 10)],
        "trades_to_reach_half_of_gross": half,
        "profitable_years": f"{sum(v['net_bp'] > 0 for v in by_year.values())} of {len(by_year)}", "by_year": by_year,
        "long": {"n": int((side > 0).sum()), "gross_bp": float(g[side > 0].mean()) if (side > 0).any() else float("nan")},
        "short": {"n": int((side < 0).sum()), "gross_bp": float(g[side < 0].mean()) if (side < 0).any() else float("nan")},
        "before_after_2022_05_16_gross_bp": [float(g[~era].mean()) if (~era).any() else float("nan"),
                                             float(g[era].mean()) if era.any() else float("nan")],
        "holding_time": "not computed (the exit function returns no bar index; a listed deviation)"}
    if arm is not None:
        common = daily.index.intersection(arm.index)
        out["rho_with_macd_arm"] = float(np.corrcoef(daily.loc[common], arm.loc[common])[0, 1])
        out["rho_with_macd_arm_days"] = int(len(common))
    if other_daily is not None:
        common = daily.index.intersection(other_daily.index)
        out["rho_with_D680_C1"] = float(np.corrcoef(daily.loc[common], other_daily.loc[common])[0, 1])
    return out


def arm_daily() -> pd.Series:
    """The admitted MACD arm's daily net at one MNQ (D674's build), truncated below 2025-03-01 at once."""
    s = importlib.util.spec_from_file_location("d674r", REPO / "scripts" / "d674_resize_macd_arm.py")
    m = importlib.util.module_from_spec(s)
    sys.modules["d674r"] = m
    s.loader.exec_module(m)
    a = m.arm_daily()
    return a[a.index < CUT]


# ================================================================================ the study
def root_study(r: str, bd: dict[str, Any], arm: pd.Series | None, workers: int) -> dict[str, Any]:
    tr, lab = bd["tr"], bd["lab"]
    cl = cost_lines(r)
    ka = known_answer(tr, r)
    dbar = d691_reproduced(lab, r)
    right_quantity(tr)
    sess_all = lab.index.to_numpy(str)
    lab_ok = (np.isfinite(lab[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1))
    win_sessions = sess_all[lab_ok]
    if win_sessions.min() < WINDOW_FROM:
        raise D694Error(f"{r}: the window starts at {win_sessions.min()}, before {WINDOW_FROM}")
    ts = tr["session"].to_numpy(str)
    win = np.isfinite(tr[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
    ct, piv = tr["ctier"].to_numpy(float), tr["p_iv"].to_numpy(float)
    c1 = win & (ct < 1 / 3)
    coiled, quiet = c1 & (piv >= THETA), c1 & (piv < THETA)
    g = tr["gross"].to_numpy(float)
    n_co = int(coiled.sum())
    exc = ~((ts >= COVID[0]) & (ts <= COVID[1]))
    # Gate 1
    t_a, se_a = D.nw_t(g[coiled])
    wt, wse = welch(g[coiled], g[quiet])
    # the ingredient null: positions (in the session series) of the window's C1 trades
    spos = pd.Series(np.arange(len(sess_all)), index=sess_all)
    c1_idx = np.flatnonzero(c1)
    pos = spos.reindex(ts[c1_idx]).to_numpy(int)
    gc1 = g[c1_idx]
    fit_mask = (sess_all >= win_sessions.min()) & (sess_all <= win_sessions.max())
    u, F, beta = residual(lab, fit_mask)
    ivrv = lab["ivrv"].to_numpy(float)
    obs = float(g[coiled].mean())
    k0, order0 = top_k_mean(C.tiers(ivrv), pos, gc1, n_co)
    if set(c1_idx[order0]) != set(np.flatnonzero(coiled)) or k0 != obs:
        raise D694Error(f"{r}: the top-k rule at the actual labels is not COILED ({k0} vs {obs})")
    if rot_ingredient(0, ivrv, u, F, pos, gc1, n_co) != obs or rot_whole(0, ivrv, pos, gc1, n_co) != obs:
        raise D694Error(f"{r}: offset 0 does not reproduce COILED's mean")
    nF, nfin = int(F.sum()), int(np.isfinite(ivrv).sum())
    items = [("ingredient", k) for k in range(EDGE, nF - EDGE)] + [("whole", k) for k in range(EDGE, nfin - EDGE)]
    t0 = time.time()
    rot = rotations(ivrv, u, F, pos, gc1, n_co, items, workers)
    wall = time.time() - t0
    nul = {kind: np.array([v for (kk, _), v in sorted(rot.items()) if kk == kind]) for kind in ("ingredient", "whole")}

    def dist(x: np.ndarray) -> dict[str, float]:
        return {"offsets": int(len(x)), "p50": float(np.median(x)), "p95": float(np.quantile(x, 0.95)), "p95_se": 0.0,
                "rank": float((x < obs).mean())}
    gate1 = {"a_gross_bp": obs, "a_t_hac": t_a, "a_se": se_a, "a_p_one_sided": float(stats.norm.sf(t_a)),
             "b_ingredient_null": dist(nul["ingredient"]), "b_residual_ols_beta": beta, "b_domain_sessions": nF,
             "b_ivrv_finite_outside_domain": int(nfin - nF),
             "c_quiet_gross_bp": float(g[quiet].mean()), "c_diff_bp": float(g[coiled].mean() - g[quiet].mean()),
             "c_welch_t": wt, "c_welch_se": wse, "d_gross_ex_covid_bp": float(g[coiled & exc].mean()),
             "secondary_null_whole_ivrv": dist(nul["whole"]), "rotation_wall_s": round(wall, 1)}
    # Gate 2: pi-hat from every earlier plain break with finite P
    P = tr["P"].to_numpy(float)
    ratio = np.where(np.isfinite(P) & (P > 0), g / P, np.nan)
    pi, cnt = pi_hat(ts, ratio)
    pi_audit(ts, ratio, pi, list(range(0, len(ts), max(1, len(ts) // 40))))
    take = (cnt >= BURN_IN) & np.isfinite(P) & (pi * P >= EP_K * tr["cost"].to_numpy(float))
    filt = coiled & take
    fnet = tr["net"].to_numpy(float)[filt]
    t2 = D.nw_t(fnet)[0] if len(fnet) > 2 else float("nan")
    gate2 = {"filtered_trades": int(filt.sum()), "filtered_net_bp": float(fnet.mean()) if len(fnet) else float("nan"),
             "t_net_hac": t2, "p_one_sided": float(stats.norm.sf(t2)) if np.isfinite(t2) else float("nan"),
             "net_ex_covid_bp": float(tr["net"].to_numpy(float)[filt & exc].mean()) if (filt & exc).any() else float("nan"),
             "unfiltered_coiled_net_bp": float(tr["net"].to_numpy(float)[coiled].mean())}
    # reported
    usd = cl["usd_per_point"]
    c1_daily = None
    if r == "NQ":
        c1_daily = pd.Series(0.0, index=win_sessions)
        c1_daily.loc[ts[c1]] = (tr["net"].to_numpy(float) * tr["level"].to_numpy(float) * usd / 1e4)[c1]
    books = {"COILED": four_groups(tr[coiled], win_sessions, usd, arm, c1_daily),
             "COILED_ep_filtered": four_groups(tr[filt], win_sessions, usd, arm, c1_daily),
             "QUIET": four_groups(tr[quiet], win_sessions, usd, arm),
             "C1": four_groups(tr[c1], win_sessions, usd, arm), "B0": four_groups(tr[win], win_sessions, usd, arm)}
    grid = {}
    for k in range(3):
        band = win & (ct >= k / 3) & (ct < (k + 1) / 3)
        for nm, m in (("iv_low", band & (piv < THETA)), ("iv_high", band & (piv >= THETA))):
            grid[f"ctier_{k + 1}_{nm}"] = {"n": int(m.sum()), "gross_bp": float(g[m].mean()), "net_bp": float(tr["net"].to_numpy(float)[m].mean())}
    b0 = {nm: {"n": int(m.sum()), "gross_bp": float(g[m].mean())} for nm, m in (("iv_low", win & (piv < THETA)), ("iv_high", win & (piv >= THETA)))}
    rv20 = c1 & (tr["p_rv20"].to_numpy(float) >= THETA)
    ls = lab[lab_ok]
    lco = (ls["ctier"] < 1 / 3) & (ls["p_iv"] >= THETA)
    lqu = (ls["ctier"] < 1 / 3) & (ls["p_iv"] < THETA)
    along = ((ls["close"] / ls["open"] - 1) * 1e4)
    upper = {"coiled_mean_gross_95_upper": obs + 1.959964 * se_a,
             "coiled_minus_quiet_95_upper": gate1["c_diff_bp"] + 1.959964 * wse}
    reported = {
        "known_answer_C1": ka, "d691_dbar_reproduced": dbar, "grid_3x2": grid, "B0_by_iv_half": b0,
        "realised_only_label_C1_and_rv20_high": {"n": int(rv20.sum()), "gross_bp": float(g[rv20].mean())},
        "manipulation_check_mean_y": {"coiled_sessions": float(ls.loc[lco, "y"].mean()), "quiet_sessions": float(ls.loc[lqu, "y"].mean()),
                                      "n": [int(lco.sum()), int(lqu.sum())]},
        "drift_control_always_long_bp": {"coiled_sessions": float(along[lco].mean()), "quiet_sessions": float(along[lqu].mean())},
        "bounds": upper, "power": {"se_coiled_bp": se_a, "mde80_one_sided_5pct_bp": 2.486845 * se_a},
        "window": [str(win_sessions.min()), str(win_sessions.max())], "window_sessions": int(len(win_sessions)),
        "costs_usd": {"single": cl["cost_single_usd"], "prereg_double": cl["cost_prereg_usd"]}}
    return {"counts": {"B0": int(win.sum()), "C1": int(c1.sum()), "COILED": n_co, "QUIET": int(quiet.sum())},
            "gate1": gate1, "gate2": gate2, "books": books, "reported": reported}


def build(workers: int) -> dict[str, Any]:
    t0 = time.time()
    sign_audit()
    bd = get_bundle()
    for r in ROOTS:  # D691's IV lag audit on real data, and its canary
        tab, _ = D.iv_cached(r)
        rng = np.random.default_rng(694)
        samp = sorted(rng.choice(tab.index[np.isfinite(tab["iv"])].to_numpy(), 10, replace=False))
        D.iv_lag_audit(tab, r, samp)
    tab, _ = D.iv_cached("ES")
    some = [s for s in tab.index[np.isfinite(tab["iv"])] if s >= "2019-01-01"][:3]
    try:
        D.iv_lag_audit(tab, "ES", some, ref_rule=lambda refs, d: max(refs[refs <= d]))
    except D.D691Error:
        pass
    else:
        raise D694Error("the IV lag canary did not fire on real data")
    arm = arm_daily()
    res = {r: root_study(r, bd[r], arm, workers) for r in ROOTS}
    h1 = T.holm({r: res[r]["gate1"]["a_p_one_sided"] for r in ROOTS})
    p2 = {r: res[r]["gate2"]["p_one_sided"] for r in ROOTS}
    h2 = T.holm({r: (p if np.isfinite(p) else 1.0) for r, p in p2.items()})
    for r in ROOTS:
        g1, g2 = res[r]["gate1"], res[r]["gate2"]
        g1["holm_p"] = h1[r]
        g1["checks"] = {"a_edge_holm": bool(g1["a_gross_bp"] > 0 and h1[r] < 0.05),
                        "b_above_ingredient_p95": bool(g1["a_gross_bp"] > g1["b_ingredient_null"]["p95"]),
                        "c_coiled_above_quiet": bool(g1["c_diff_bp"] > 0),
                        "d_positive_ex_covid": bool(g1["d_gross_ex_covid_bp"] > 0)}
        g2["holm_p"] = h2[r]
        g2["checks"] = {"filtered_ge_30": bool(g2["filtered_trades"] >= MIN_FILTERED),
                        "net_positive_holm": bool(g2["filtered_net_bp"] > 0 and h2[r] < 0.05),
                        "ex_covid_positive": bool(g2["net_ex_covid_bp"] > 0)}
        pass1, pass2 = all(g1["checks"].values()), all(g2["checks"].values())
        if res[r]["counts"]["COILED"] < MIN_COILED:
            v = "UNRESOLVED"
        elif pass1 and pass2:
            v = "SUPPORTED"
        elif pass1:
            v = "MECHANISM ONLY"
        else:
            v = "NOT SUPPORTED"
        res[r]["verdict"] = v
    rep = {r: res[r]["reported"] for r in ROOTS}
    preds = {
        "1_manipulation_check_both": bool(all(rep[r]["manipulation_check_mean_y"]["coiled_sessions"] > rep[r]["manipulation_check_mean_y"]["quiet_sessions"] for r in ROOTS)),
        "2_NQ_coiled_gross_above_quiet": bool(res["NQ"]["gate1"]["c_diff_bp"] > 0),
        "3_ES_fails_gate1a": not res["ES"]["gate1"]["checks"]["a_edge_holm"],
        "4_no_root_passes_gate2": not any(all(res[r]["gate2"]["checks"].values()) for r in ROOTS),
        "5_NQ_clears_ingredient_p95": bool(res["NQ"]["gate1"]["checks"]["b_above_ingredient_p95"])}
    return {"spec": "D694 (8cffb181)", "credit": "dealer gamma (GEX): SqueezeMetrics", "roots": res, "predictions": preds,
            "deviations": ["holding time not computed (E4's exit function returns no bar index)",
                           "the MACD arm's daily series is D674's build, truncated below 2025-03-01"],
            "runtime_min": round((time.time() - t0) / 60, 2)}


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D694Error, C.D671Error, D.D691Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(694)
    # sign, in money
    sign_audit()
    must_raise("a gross that ignores the side", lambda: sign_audit(lambda D_, e, x: (x / e - 1) * 1e4))
    # right quantity
    tr = pd.DataFrame({"gross_prereg": rng.normal(0, 10, 50)})
    tr["gross"] = tr["gross_prereg"] + 0.5
    tr["cost"], tr["cost_prereg_bp"] = 2.0, 2.5
    right_quantity(tr)
    must_raise("the fill-tick gross scored as the at-level trade", lambda: right_quantity(tr.assign(gross=tr["gross_prereg"])))
    must_raise("the double-counted cost", lambda: right_quantity(tr.assign(cost=2.5)))
    # pi-hat lag
    sess = np.array([f"2019-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(200)])
    ratio = rng.normal(0.03, 0.1, 200)
    ratio[rng.random(200) < 0.1] = np.nan
    pi, _ = pi_hat(sess, ratio)
    pi_audit(sess, ratio, pi, list(range(0, 200, 7)))
    pl, _ = pi_hat(sess, ratio, leak=True)
    must_raise("a pi-hat that includes its own trade", lambda: pi_audit(sess, ratio, pl, list(range(1, 200, 7))))
    # tier lag
    x = rng.normal(size=700)
    C.tier_audit(C.tiers(x), x, list(range(0, 700, 50)))
    must_raise("a tier that ranks its own value", lambda: C.tier_audit(C.tiers(x, leak=True), x, list(range(300, 700, 50))))
    # forecast lag (D671's)
    Fz = rng.normal(size=(400, 2))
    yz = Fz[:, 0] * 0.5 + rng.normal(size=400)
    old = C.SIGN
    C.SIGN = np.array([1.0, 1.0])
    try:
        fl, _ = C.size_forecast(Fz, yz, leak=True)
        must_raise("a forecast fitted on its own row", lambda: C.forecast_audit(fl, Fz, yz, np.array([f"{i:05d}" for i in range(400)]), [300, 350, 399]))
    finally:
        C.SIGN = old
    # the null: offset 0, the top-k identity, chunk == whole, and a rotation that moves the statistic
    n = 900
    ivrv = rng.normal(size=n)
    ivrv[:30] = np.nan
    lab = pd.DataFrame({"lniv": ivrv + 0.3 * rng.normal(size=n), "lnrv": rng.normal(size=n), "rv5": rng.normal(size=n),
                        "on_range": rng.normal(size=n), "lnatr": rng.normal(size=n), "ivrv": ivrv})
    u, F, _ = residual(lab, np.ones(n, bool))
    pos = np.sort(rng.choice(np.arange(300, n), 200, replace=False))
    p_act = C.tiers(ivrv)
    gc1 = rng.normal(size=200) + 2.0 * (p_act[pos] >= 0.5)
    kk = int((p_act[pos] >= 0.5).sum())
    obs = float(gc1[p_act[pos] >= 0.5].mean())
    if top_k_mean(p_act, pos, gc1, kk)[0] != obs:
        raise SystemExit("selftest: the top-k rule does not return the >= 1/2 cell")
    if rot_ingredient(0, ivrv, u, F, pos, gc1, kk) != obs or rot_whole(0, ivrv, pos, gc1, kk) != obs:
        raise SystemExit("selftest: offset 0 does not reproduce the statistic")
    items = [("ingredient", k) for k in (21, 22, 60)] + [("whole", k) for k in (21, 40)]
    serial = {(kind, k): (rot_ingredient(k, ivrv, u, F, pos, gc1, kk) if kind == "ingredient" else rot_whole(k, ivrv, pos, gc1, kk))
              for kind, k in items}
    par = rotations(ivrv, u, F, pos, gc1, kk, items, 2)
    if any(serial[i] != par[i] for i in items):
        raise SystemExit("selftest: the rotation's processes differ from the serial run")
    if max(serial.values()) >= obs:
        raise SystemExit("selftest: rotating an injected label does not destroy it")
    print(f"selftest: {len(fired)} canaries fired: {fired}; checks passed: sign in money, right quantity, pi-hat and "
          "tier lag, top-k identity, offset 0, processes == serial, rotation destroys an injected label. The known "
          "answers, D691's reproduction and the IV lag canary need the fixtures and run in --run.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.time:
        bd = get_bundle()
        for r in ROOTS:
            tr, lab = bd[r]["tr"], bd[r]["lab"]
            ivrv = lab["ivrv"].to_numpy(float)
            sess_all = lab.index.to_numpy(str)
            win = np.isfinite(tr[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
            c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
            pos = pd.Series(np.arange(len(sess_all)), index=sess_all).reindex(tr["session"].to_numpy(str)[c1]).to_numpy(int)
            u, F, _ = residual(lab, np.ones(len(lab), bool))
            gc1 = tr["gross"].to_numpy(float)[c1]
            t0 = time.time()
            for k in (21, 22, 23):
                rot_ingredient(k, ivrv, u, F, pos, gc1, 100)
            per = (time.time() - t0) / 3
            n_items = int(F.sum()) + int(np.isfinite(ivrv).sum()) - 4 * EDGE
            print(f"{r}: {per:.3f} s an offset x {n_items} rotations / {a.workers} workers = about "
                  f"{per * n_items / a.workers / 60:.1f} min (bundle cached)")
        return 0
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D694Error(f"{OUT.name} exists: D694 runs once")
    out = build(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({r: {"verdict": out["roots"][r]["verdict"], "counts": out["roots"][r]["counts"],
                          "gate1": {k: out["roots"][r]["gate1"][k] for k in ("a_gross_bp", "a_t_hac", "holm_p", "c_diff_bp", "checks")},
                          "ingredient_null": out["roots"][r]["gate1"]["b_ingredient_null"],
                          "gate2": out["roots"][r]["gate2"]} for r in ROOTS}, indent=1, default=float))
    print(json.dumps(out["predictions"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
