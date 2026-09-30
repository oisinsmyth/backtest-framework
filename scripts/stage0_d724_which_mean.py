"""D724 Stage 0: which mean NQ respects intraday, how early and how immediately the day's size is known, and whether the
size changes the mean. Spec: docs/decisions/D724-STAGE-0-DESIGN-which-mean-and-when-is-size-known.md, committed before
this file existed.

    uv run python scripts/stage0_d724_which_mean.py --selftest     # synthetic only
    uv run python scripts/stage0_d724_which_mean.py --run          # once -> data/stage0_d724_which_mean.json

NQ day session 2016-01-04 -> 2023-12-29 from fut_NQ_rth_1m (one-minute OHLCV), overnight from fut_opening_globex_1m.
Price at t = the close of the bar starting t-1 (D462), as-of within the session. sigma_d = the mean day range of the
prior 20 sessions. The size forecasts are D691's M1 (F_open) and M1 without the open-time features (F_close), walk-
forward, built with every cut constant lowered to 2024-01-01 (D720's `lowered_cut`). Nothing dated 2024-01-01 or later
is used; no per-date SqueezeMetrics series is written.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402

OUT = REPO / "data" / "stage0_d724_which_mean.json"
LO, HI, CUT24 = "2016-01-04", Z.HI, Z.CUT24
NMIN, MIN_BARS = 390, 380
GRID = list(range(30, 361, 5))            # minutes after 09:30: 10:00 .. 15:30
HS = {"30": 30, "60": 60, "close": None}
ANCH = ("A1_vwap", "A2_open", "A3_prior_close", "A4_overnight_mid", "A5_running_mid", "A6_or_mid",
        "A7_prior_vwap", "A0_lag30")
KS = (0.25, 0.5, 0.75)
MNQ_USD_PT, MNQ_COST = 2.0, None          # the cost comes from D711's cost line (set in run)
EDGE = 20
Q2_T = [30, 90, 150, 210, 270, 330]       # 10:00, 11:00, 12:00, 13:00, 14:00, 15:00
P = Z.P


class D724Error(AssertionError):
    pass


def hhmm(m: int) -> str:
    t = 9 * 60 + 30 + m
    return f"{t // 60:02d}:{t % 60:02d}"


# ================================================================================ panels
def load_panels(data_root: Path) -> dict[str, Any]:
    b = pd.read_csv(data_root / "fixtures" / "fut_NQ_rth_1m.csv.gz", encoding="utf-8",
                    dtype={"day": str, "hhmm": str, "contract": str})
    b = b[(b["day"] >= LO) & (b["day"] <= HI)]
    Z.no_session_after(b["day"].unique(), "the NQ one-minute bars")
    mins = [hhmm(m) for m in range(NMIN)]
    b = b[b["hhmm"].isin(mins)]
    nb = b.groupby("day").size()
    days = np.array(sorted(nb.index[nb >= MIN_BARS]))
    b = b[b["day"].isin(days)]
    piv = {c: b.pivot(index="day", columns="hhmm", values=c).reindex(index=days, columns=mins).to_numpy(float)
           for c in ("open", "high", "low", "close", "volume")}
    con = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(days).to_numpy(str)
    C = pd.DataFrame(piv["close"]).ffill(axis=1).to_numpy(float)
    O = piv["open"]
    O0 = np.where(np.isfinite(O[:, 0]), O[:, 0], C[:, 0])
    H, L, V = piv["high"], piv["low"], np.nan_to_num(piv["volume"], nan=0.0)
    g = pd.read_csv(data_root / "fixtures" / "fut_opening_globex_1m.csv.gz", encoding="utf-8",
                    dtype={"session": str, "hhmm": str}, usecols=["root", "session", "hhmm", "high", "low"])
    g = g[(g["root"] == "NQ") & (g["session"] >= LO) & (g["session"] <= HI)]
    Z.no_session_after(g["session"].unique(), "the NQ overnight bars")
    on = g[(g["hhmm"] >= "18:00") | (g["hhmm"] < "09:30")].groupby("session")
    on_mid = ((on["high"].max() + on["low"].min()) / 2).reindex(days).to_numpy(float)
    on_last = on["hhmm"].agg(lambda v: max((h for h in v if h < "18:00"), default="")).reindex(days)
    if (on_last.fillna("") >= "09:30").any():
        raise D724Error("lag: an overnight bar at or after 09:30")
    rng = np.nanmax(H, axis=1) - np.nanmin(L, axis=1)
    sig = pd.Series(rng).shift(1).rolling(20, min_periods=20).mean().to_numpy(float)
    return {"days": days, "O0": O0, "H": H, "L": L, "C": C, "V": V, "con": con, "on_mid": on_mid, "sig": sig}


def p_at(pn: dict[str, Any], m: int) -> np.ndarray:
    """The price at minute m after 09:30: the 09:30 open at m = 0, else the close of the bar starting m - 1. Never a
    negative index (which would wrap to 15:59: lookahead)."""
    if m < 0:
        raise D724Error(f"p_at: minute {m} is before the open")
    return pn["O0"] if m == 0 else pn["C"][:, m - 1]


def anchors(pn: dict[str, Any]) -> dict[str, np.ndarray]:
    """Each anchor as a [days, grid] matrix, from bars starting before t only."""
    H, L, C, V = pn["H"], pn["L"], pn["C"], pn["V"]
    Hn, Ln = np.nan_to_num(H, nan=-np.inf), np.nan_to_num(L, nan=np.inf)
    tp = np.where(np.isfinite(H) & np.isfinite(L), (np.nan_to_num(H) + np.nan_to_num(L) + C) / 3, C)
    cpv, cv = np.cumsum(tp * V, axis=1), np.cumsum(V, axis=1)
    runmax, runmin = np.maximum.accumulate(Hn, axis=1), np.minimum.accumulate(Ln, axis=1)
    gi = np.array(GRID) - 1                                  # the bar starting t-1 is the last bar read at t
    same = np.r_[False, pn["con"][1:] == pn["con"][:-1]]
    prev_close = np.where(same, np.r_[np.nan, C[:-1, -1]], np.nan)
    full_vwap = cpv[:, -1] / np.where(cv[:, -1] > 0, cv[:, -1], np.nan)
    prev_vwap = np.where(same, np.r_[np.nan, full_vwap[:-1]], np.nan)
    ng = len(GRID)
    rep = lambda v: np.repeat(v[:, None], ng, axis=1)      # noqa: E731
    or_mid = (np.nanmax(H[:, :30], axis=1) + np.nanmin(L[:, :30], axis=1)) / 2
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = cpv[:, gi] / np.where(cv[:, gi] > 0, cv[:, gi], np.nan)
    return {"A1_vwap": vw, "A2_open": rep(pn["O0"]), "A3_prior_close": rep(prev_close),
            "A4_overnight_mid": rep(pn["on_mid"]), "A5_running_mid": (runmax[:, gi] + runmin[:, gi]) / 2,
            "A6_or_mid": rep(or_mid), "A7_prior_vwap": rep(prev_vwap),
            "A0_lag30": np.column_stack([p_at(pn, m - 30) for m in GRID])}


def anchor_audit(pn: dict[str, Any], A: dict[str, np.ndarray], sample: list[tuple[int, int]], shift: int = 0) -> None:
    """Second implementation by minute arithmetic from the raw arrays. `shift` = 1 reads the bar starting at t: the
    canary, which must disagree."""
    H, L, C, V = pn["H"], pn["L"], pn["C"], pn["V"]
    for d, j in sample:
        m = GRID[j] + shift                                  # bars with start minute < m
        hs, ls, cs, vs = H[d, :m], L[d, :m], C[d, :m], V[d, :m]
        ok = np.isfinite(hs) & np.isfinite(ls)
        tp = np.where(ok, (np.nan_to_num(hs) + np.nan_to_num(ls) + cs) / 3, cs)
        want = {"A1_vwap": float((tp * vs).sum() / vs.sum()) if vs.sum() > 0 else np.nan,
                "A5_running_mid": float((np.nanmax(hs) + np.nanmin(ls)) / 2),
                "A0_lag30": float(pn["O0"][d] if m - 30 == 0 else C[d, m - 31])}
        for k, w in want.items():
            got = A[k][d, j]
            if np.isfinite(w) and np.isfinite(got) and not math.isclose(w, got, rel_tol=1e-12, abs_tol=1e-9):
                raise D724Error(f"lag: {k} at day {d}, {hhmm(GRID[j])} reads a bar at or after t")


def price_at(pn: dict[str, Any]) -> np.ndarray:
    return pn["C"][:, np.array(GRID) - 1]


def fwd(pn: dict[str, Any], h: int | None) -> np.ndarray:
    """P(t+h) - P(t), in points; NaN where t+h passes 16:00."""
    C = pn["C"]
    out = np.full((C.shape[0], len(GRID)), np.nan)
    for j, m in enumerate(GRID):
        e = NMIN - 1 if h is None else m + h - 1
        if e <= NMIN - 1:
            out[:, j] = C[:, e] - C[:, m - 1]
    return out


def touched(pn: dict[str, Any], level: np.ndarray, h: int | None) -> np.ndarray:
    """Whether a bar starting in [t, t+h) reaches `level` (True/False; NaN where the window passes 16:00)."""
    H, L = pn["H"], pn["L"]
    out = np.full(level.shape, np.nan)
    for j, m in enumerate(GRID):
        e = NMIN if h is None else m + h
        if e > NMIN:
            continue
        hi, lo = np.nanmax(H[:, m:e], axis=1), np.nanmin(L[:, m:e], axis=1)
        lv = level[:, j]
        fin = np.isfinite(lv) & np.isfinite(hi)
        out[fin, j] = ((lo[fin] <= lv[fin]) & (hi[fin] >= lv[fin])).astype(float)
    return out


# ================================================================================ statistics
def kappa(D: np.ndarray, Y: np.ndarray, mask: np.ndarray | None = None) -> dict[str, float]:
    ok = np.isfinite(D) & np.isfinite(Y) & (True if mask is None else mask)
    x, y = np.where(ok, D, 0.0), np.where(ok, Y, 0.0)
    sxx = float((x * x).sum())
    if sxx == 0:
        return {"kappa": float("nan"), "t": float("nan"), "n": 0}
    b = float((x * y).sum()) / sxx
    e = np.where(ok, y - b * x, 0.0)
    g = (x * e).sum(axis=1)
    se = math.sqrt(float((g * g).sum())) / sxx
    return {"kappa": -b, "t": -b / se if se > 0 else float("nan"), "n": int(ok.sum())}


def kappa_rotation(D: np.ndarray, Y: np.ndarray) -> dict[str, float]:
    """Enumerated rotation of the day index of D against Y; offsets EDGE .. n - EDGE."""
    n = D.shape[0]
    obs = kappa(D, Y)["kappa"]
    if not math.isclose(kappa(np.roll(D, 0, axis=0), Y)["kappa"], obs, rel_tol=0, abs_tol=1e-12):
        raise D724Error("rotation: offset 0 does not reproduce kappa")
    Yz, Yf = np.nan_to_num(Y), np.isfinite(Y)
    null = []
    for k in range(EDGE, n - EDGE):
        Dr = np.roll(D, k, axis=0)
        ok = np.isfinite(Dr) & Yf
        x = np.where(ok, Dr, 0.0)
        sxx = (x * x).sum()
        null.append(-(x * Yz).sum() / sxx if sxx > 0 else np.nan)
    null = np.array(null)
    null = null[np.isfinite(null)]
    return {"observed": obs, "offsets": int(len(null)), "p05": float(np.quantile(null, 0.05)),
            "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)), "p95_se": 0.0,
            "rank": float((null < obs).mean())}


def margin(TA: np.ndarray, TM: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    ok = mask & np.isfinite(TA) & np.isfinite(TM)
    dlt = np.where(ok, TA - TM, 0.0)
    cnt = ok.sum(axis=1)
    n = int(ok.sum())
    if n == 0:
        return {"margin": float("nan"), "t": float("nan"), "n": 0}
    mu = float(dlt.sum() / n)
    g = (np.where(ok, dlt - mu, 0.0)).sum(axis=1)
    se = math.sqrt(float((g * g).sum())) / n
    return {"margin": mu, "touch_anchor": float(np.where(ok, TA, 0).sum() / n),
            "touch_mirror": float(np.where(ok, TM, 0).sum() / n), "t": mu / se if se > 0 else float("nan"),
            "n": n, "days": int((cnt > 0).sum())}


def spear(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    return float(stats.spearmanr(a[ok], b[ok])[0]) if ok.sum() > 10 else float("nan")


def partial_spear(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Spearman of a with b after the ranks of c are regressed out of both."""
    ok = np.isfinite(a) & np.isfinite(b) & np.isfinite(c)
    ra, rb, rc = (stats.rankdata(v[ok]) for v in (a, b, c))
    X = np.column_stack([np.ones(ok.sum()), rc])
    ea = ra - X @ np.linalg.lstsq(X, ra, rcond=None)[0]
    eb = rb - X @ np.linalg.lstsq(X, rb, rcond=None)[0]
    return float(np.corrcoef(ea, eb)[0, 1])


# ================================================================================ the size labels
def build_labels(data_root: Path) -> pd.DataFrame:
    import stage0_d662_gamma_product as S
    import stage0_d691_iv_size as I
    C, T, M = I.C, I.T, I.M
    with Z.lowered_cut(I, S, T, M):
        fr = I.frames()["NQ"]
        Z.no_session_after(fr["d"].index, "the NQ frame")
        iv, _ = I.build_iv("NQ")
        Z.no_session_after(iv.index, "the NQ IV table")
    if I.CUT != "2025-03-01" or T.RESERVED_FROM != "2025-03-01":
        raise D724Error("the cut constants were not restored")
    dz = I.design(fr, iv)
    sess, F0, y, ivrv = dz["sess"], dz["F0"], dz["y"], dz["ivrv"]
    feats = list(C.SIZE_FEATS)
    close_idx = [feats.index(f) for f in feats if f not in ("on_range", "abs_gap")]
    F_open = np.column_stack([F0, ivrv])
    F_close = np.column_stack([F0[:, close_idx], ivrv])
    s_close = np.append(I.SIGN0[close_idx], 1.0)
    out = {}
    idx = list(range(0, len(sess), max(1, len(sess) // 30)))
    for nm, F, sg in (("F_open", F_open, I.SIGN1), ("F_close", F_close, s_close)):
        f = I.forecast(F, y, sg)
        old = C.SIGN
        C.SIGN = sg
        try:
            C.forecast_audit(f, F, y, sess, idx)
            fl, _ = C.size_forecast(F, y, leak=True)
            try:
                C.forecast_audit(fl, F, y, sess, idx)
            except C.D671Error:
                pass
            else:
                raise D724Error(f"{nm}: the forecast audit did not fire on its canary")
        finally:
            C.SIGN = old
        out[nm] = f
    tau = C.tiers(out["F_open"])
    C.tier_audit(tau, out["F_open"], idx)
    lab = pd.DataFrame({"F_open": out["F_open"], "F_close": out["F_close"], "tau_open": tau, "y": y,
                        "atr20": fr["d"]["atr20"].reindex(fr["S"].index).to_numpy(float)}, index=pd.Index(sess))
    return lab


# ================================================================================ Q2
def f_now(pn: dict[str, Any], j_min: int) -> np.ndarray:
    """ln of the realised variance of the six 5-minute returns over the 30 minutes before t (bp^2)."""
    pts = [p_at(pn, j_min - 30 + 5 * i) for i in range(7)]
    r = 1e4 * np.diff(np.log(np.column_stack(pts)), axis=1)
    with np.errstate(divide="ignore"):
        return np.log((r * r).sum(axis=1))


def q2(pn: dict[str, Any], lab: pd.DataFrame) -> dict[str, Any]:
    days = pn["days"]
    L = lab.reindex(days)
    fo, fc, y, atr = (L[c].to_numpy(float) for c in ("F_open", "F_close", "y", "atr20"))
    sig = pn["sig"]
    C, H, Lw = pn["C"], pn["H"], pn["L"]
    first_hour = np.abs(C[:, 59] - pn["O0"]) / sig
    res: dict[str, Any] = {"early": {"F_close_vs_day_range": spear(fc, y), "F_open_vs_day_range": spear(fo, y),
                                     "F_close_vs_first_hour": spear(fc, first_hour),
                                     "F_open_vs_first_hour": spear(fo, first_hour)}, "grid": []}
    for m in Q2_T:
        fn = f_now(pn, m)
        made = (np.nanmax(H[:, :m], axis=1) - np.nanmin(Lw[:, :m], axis=1))
        frem = (np.exp(fo) * atr - made) / sig
        for hn, h in HS.items():
            e = NMIN - 1 if h is None else m + h - 1
            if e > NMIN - 1:
                continue
            tgt = np.abs(C[:, e] - C[:, m - 1]) / sig
            row = {"t": hhmm(m), "h": hn, "F_close": spear(fc, tgt), "F_open": spear(fo, tgt), "F_now": spear(fn, tgt),
                   "F_rem": spear(frem, tgt), "F_open_partial_given_F_now": partial_spear(fo, tgt, fn)}
            row["reading"] = ("BOTH" if row["F_now"] > row["F_open"] and row["F_open_partial_given_F_now"] >= 0.05 else
                              "IMMEDIATE" if row["F_now"] > row["F_open"] else
                              "EARLY" if row["F_open_partial_given_F_now"] >= 0.05 else "NEITHER")
            res["grid"].append(row)
    return res


def fnow_tercile(pn: dict[str, Any]) -> np.ndarray:
    """F_now at every grid time, as its walk-forward percentile at the same clock among the prior 250 days."""
    import stage0_d671_break_construction as C
    out = np.full((len(pn["days"]), len(GRID)), np.nan)
    for j, m in enumerate(GRID):
        out[:, j] = C.tiers(f_now(pn, m))
    return out


# ================================================================================ the money bridge
def bridge(pn: dict[str, Any], A: np.ndarray, k: float, cost: float) -> dict[str, np.ndarray]:
    """First grid time with |D| >= k: one MNQ toward the anchor level at entry; exit at the close of the first bar
    whose range reaches it, else at t+60, else 15:59."""
    Pm, sig, H, L, C = price_at(pn), pn["sig"], pn["H"], pn["L"], pn["C"]
    n = len(pn["days"])
    g = np.full(n, np.nan)
    for d in range(n):
        if not np.isfinite(sig[d]):
            continue
        dv = (Pm[d] - A[d]) / sig[d]
        hit = np.flatnonzero(np.isfinite(dv) & (np.abs(dv) >= k))
        if not len(hit):
            continue
        j = hit[0]
        m, lvl, s = GRID[j], A[d, j], -np.sign(dv[j])
        e = min(m + 60, NMIN)
        ex = C[d, e - 1]
        for b in range(m, e):
            if np.isfinite(H[d, b]) and L[d, b] <= lvl <= H[d, b]:
                ex = C[d, b]
                break
        g[d] = s * (ex - Pm[d, j]) * MNQ_USD_PT
    return {"gross": g, "net": g - cost}


def bridge_book(g: np.ndarray, net: np.ndarray, days: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    tr = np.isfinite(g) & mask
    daily = np.where(tr, net, 0.0)
    gdaily = np.where(tr, g, 0.0)
    years = np.array([s[:4] for s in days])
    by = {y: float(daily[years == y].sum()) for y in np.unique(years)}
    tot = sum(by.values())
    return {"trades": int(tr.sum()), "net_sharpe": Z.sharpe(daily), "net_sortino": Z.sortino(daily),
            "gross_sharpe": Z.sharpe(gdaily), "gross_sortino": Z.sortino(gdaily),
            "mean_gross": float(g[tr].mean()) if tr.any() else None,
            "net_distribution": Z.trade_dist(net[tr]), "net_by_year": by,
            "years_positive": int(sum(v > 0 for v in by.values())),
            "largest_year_share": float(max(by.values()) / tot) if tot > 0 else None}


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cost = float(M711.cost_line("NQ")["cost"])
    P(f"[D724] panels (NQ one-minute, {LO} -> {HI}) ...")
    pn = load_panels(data_root)
    A = anchors(pn)
    rng = np.random.default_rng(724)
    sample = [(int(rng.integers(21, len(pn["days"]))), int(rng.integers(0, len(GRID)))) for _ in range(60)]
    sample += [(int(rng.integers(21, len(pn["days"]))), 0) for _ in range(10)]   # 10:00, where t - 30 is the open
    anchor_audit(pn, A, sample)
    try:
        anchor_audit(pn, A, sample, shift=1)
    except D724Error:
        pass
    else:
        raise D724Error("the anchor audit did not fire on its canary (a bar starting at t)")
    Pm, sig = price_at(pn), pn["sig"][:, None]
    D = {a: (Pm - A[a]) / sig for a in ANCH}
    Y = {hn: fwd(pn, h) / sig for hn, h in HS.items()}
    P("[D724] size labels ...")
    lab = build_labels(data_root)
    tau = lab["tau_open"].reindex(pn["days"]).to_numpy(float)
    ftau = fnow_tercile(pn)
    out: dict[str, Any] = {"spec": "D724-STAGE-0-DESIGN-which-mean-and-when-is-size-known.md",
                           "seal": f"nothing on or after {CUT24}", "days": int(len(pn["days"])),
                           "window": [str(pn["days"][0]), str(pn["days"][-1])], "mnq_cost": cost, "Q1": {}}
    P("[D724] Q1 ...")
    tod = {"morning": np.array([m < 150 for m in GRID]), "midday": np.array([150 <= m < 270 for m in GRID]),
           "afternoon": np.array([m >= 270 for m in GRID])}
    for a in ANCH:
        mirror = 2 * Pm - A[a]
        big = np.abs(D[a]) >= 0.25
        row: dict[str, Any] = {}
        for hn, h in HS.items():
            TA, TM = touched(pn, A[a], h), touched(pn, mirror, h)
            row[hn] = {"kappa_all": kappa(D[a], Y[hn]), "kappa_stretched": kappa(D[a], Y[hn], big),
                       "touch_margin_stretched": margin(TA, TM, big),
                       "kappa_by_time": {k: kappa(D[a], Y[hn], np.broadcast_to(v, D[a].shape)) for k, v in tod.items()}}
            if hn == "60":
                row["60"]["rotation"] = kappa_rotation(D[a], Y["60"])
                row["_T60"] = (TA, TM)
        out["Q1"][a] = row
    k0 = out["Q1"]["A0_lag30"]["60"]["kappa_all"]["kappa"]
    for a in ANCH:
        r60 = out["Q1"][a]["60"]
        c1 = r60["rotation"]["observed"] > r60["rotation"]["p95"] and (a == "A0_lag30" or r60["kappa_all"]["kappa"] > k0)
        c2 = r60["touch_margin_stretched"]["margin"] > 0 and r60["touch_margin_stretched"]["t"] >= 2
        out["Q1"][a]["reading"] = "RESPECTED" if c1 and c2 else ("WEAK" if c1 or c2 else "NOT RESPECTED")
    resp = [a for a in ANCH if a != "A0_lag30" and out["Q1"][a]["reading"] == "RESPECTED"]
    out["Q1_best"] = max(resp, key=lambda a: out["Q1"][a]["60"]["kappa_all"]["kappa"]) if resp else None
    P("[D724] Q2 ...")
    out["Q2"] = q2(pn, lab)
    P("[D724] Q3 ...")
    q3: dict[str, Any] = {}
    fin = np.isfinite(tau)
    for a in ANCH:
        ok = np.isfinite(D[a]) & np.isfinite(Y["60"])
        x, y = np.where(ok, D[a], 0.0), np.where(ok, Y["60"], 0.0)
        sxy, sxx = (x * y).sum(axis=1), (x * x).sum(axis=1)
        TA, TM = out["Q1"][a].pop("_T60")
        big = np.abs(D[a]) >= 0.25

        def kq(t_: np.ndarray, lo: float, hi: float) -> float:
            m_ = np.isfinite(t_) & (t_ >= lo) & (t_ < hi)
            return float(-sxy[m_].sum() / sxx[m_].sum()) if sxx[m_].sum() > 0 else float("nan")

        per = {}
        for nm, lo, hi in (("quiet", 0, 1 / 3), ("mid", 1 / 3, 2 / 3), ("big", 2 / 3, 1.01)):
            dm = np.isfinite(tau) & (tau >= lo) & (tau < hi)
            per[nm] = {"kappa_60": kq(tau, lo, hi),
                       "touch_margin_60": margin(TA, TM, big & dm[:, None]),
                       "kappa_60_by_F_now_tercile": kappa(D[a], Y["60"], (ftau >= lo) & (ftau < hi))}
        obs = per["quiet"]["kappa_60"] - per["big"]["kappa_60"]
        tf = tau[fin]
        idx = np.flatnonzero(fin)
        null = []
        for k in range(EDGE, len(tf) - EDGE):
            tr_ = np.full(len(tau), np.nan)
            tr_[idx] = np.roll(tf, k)
            null.append(kq(tr_, 0, 1 / 3) - kq(tr_, 2 / 3, 1.01))
        null = np.array(null)
        q3[a] = {"terciles": per, "delta_kappa_quiet_minus_big": obs, "rotation_p05": float(np.quantile(null, 0.05)),
                 "rotation_p50": float(np.median(null)), "rotation_p95": float(np.quantile(null, 0.95)),
                 "rank": float((null < obs).mean())}
    best = {}
    for nm in ("quiet", "big"):
        best[nm] = max((a for a in ANCH if a != "A0_lag30"), key=lambda a: q3[a]["terciles"][nm]["kappa_60"])
    out["Q3"] = {"anchors": q3, "best_anchor_by_tercile": best,
                 "size_changes_the_mean": bool(any(not (0.05 <= q3[a]["rank"] <= 0.95) for a in ANCH)
                                               or best["quiet"] != best["big"])}
    P("[D724] the money bridge ...")
    br: dict[str, Any] = {}
    for a in ANCH:
        br[a] = {}
        for k in KS:
            bb = bridge(pn, A[a], k, cost)
            br[a][str(k)] = {"all": bridge_book(bb["gross"], bb["net"], pn["days"], np.ones(len(tau), bool))}
            for nm, lo, hi in (("quiet", 0, 1 / 3), ("mid", 1 / 3, 2 / 3), ("big", 2 / 3, 1.01)):
                br[a][str(k)][nm] = bridge_book(bb["gross"], bb["net"], pn["days"],
                                                np.isfinite(tau) & (tau >= lo) & (tau < hi))
    out["bridge"] = br
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D724] best respected mean: {out['Q1_best']}; size changes the mean: {out['Q3']['size_changes_the_mean']}; "
      f"wrote {OUT.name} in {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(3)
    nd = 60
    base = 100 + np.cumsum(rng.normal(0, 0.2, (nd, NMIN)), axis=1)
    C = base.copy()
    H, L = C + 0.1, C - 0.1
    V = rng.integers(1, 50, (nd, NMIN)).astype(float)
    pn = {"days": np.array([f"2019-01-{i:02d}" for i in range(1, nd + 1)]), "O0": C[:, 0] - 0.05, "H": H, "L": L,
          "C": C, "V": V, "con": np.array(["NQH9"] * nd), "on_mid": C[:, 0] + 0.3, "sig": np.full(nd, 5.0)}
    A = anchors(pn)
    sample = [(int(rng.integers(1, nd)), int(rng.integers(0, len(GRID)))) for _ in range(30)] + [(5, 0), (6, 0)]
    anchor_audit(pn, A, sample)
    try:
        anchor_audit(pn, A, sample, shift=1)
        fails.append("the anchor canary did not fire")
    except D724Error:
        pass
    # the wrap-around bug: at 10:00 a naive C[:, t-31] reads column -1, the 15:59 close; the audit must catch it
    Abad = dict(A)
    Abad["A0_lag30"] = C[:, np.array(GRID) - 31]
    try:
        anchor_audit(pn, Abad, [(5, 0)])
        fails.append("the audit missed the 10:00 wrap-around (lookahead to 15:59)")
    except D724Error:
        pass
    Pm = price_at(pn)
    mirror = 2 * Pm - A["A1_vwap"]
    if not np.allclose(np.abs(mirror - Pm), np.abs(A["A1_vwap"] - Pm), equal_nan=True):
        fails.append("the mirror is not equidistant")
    # a series that reverts to its open: kappa > 0 and beats its rotation; a random walk does not
    Cr = np.empty((400, NMIN))
    for d in range(400):
        x = np.zeros(NMIN)
        for i in range(1, NMIN):
            x[i] = x[i - 1] - 0.03 * x[i - 1] + rng.normal(0, 0.3)
        Cr[d] = 100 + x
    pr = {"C": Cr, "sig": np.full(400, 5.0)}
    Dm = (price_at(pr) - 100) / 5
    Ym = fwd(pr, 60) / 5
    rot = kappa_rotation(Dm, Ym)
    if not (rot["observed"] > 0 and rot["observed"] > rot["p95"]):
        fails.append("a reverting series did not beat its rotation")
    Cw = 100 + np.cumsum(rng.normal(0, 0.3, (400, NMIN)), axis=1)
    pw = {"C": Cw, "sig": np.full(400, 5.0)}
    rw = kappa_rotation((price_at(pw) - Cw[:, :1]) / 5, fwd(pw, 60) / 5)
    if rw["rank"] > 0.99:
        fails.append("a random walk sat above 99% of its rotation")
    # sign in money: short above the anchor, price falls to it -> positive
    pn2 = dict(pn)
    C2 = np.full((1, NMIN), 110.0)
    C2[0, 40:] = 100.0
    pn2.update({"C": C2, "H": C2 + 0.1, "L": C2 - 0.1, "sig": np.array([5.0]), "days": np.array(["2019-01-01"])})
    b = bridge(pn2, np.full((1, len(GRID)), 100.0), 0.25, 4.07)
    if not (b["gross"][0] > 0 and math.isclose(b["net"][0], b["gross"][0] - 4.07)):
        fails.append("sign in money")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: the anchor lag audit and its canary fire; the mirror is equidistant; a reverting series beats its "
      "rotation, a random walk does not; a trade toward the anchor pays in money, net = gross - cost")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        if OUT.exists():
            raise D724Error(f"{OUT.name} exists: D724 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
