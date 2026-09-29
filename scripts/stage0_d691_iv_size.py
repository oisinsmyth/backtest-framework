"""D691 Stage 0: does the prior close's at-the-money implied volatility tell us how far ES and NQ will move, beyond
D671's realised-only size forecast (which already holds SPX dealer gamma)? Spec:
docs/decisions/D691-STAGE-0-DESIGN-implied-vs-realised-vol-as-a-size-predictor.md (7a9e4e69).

    uv run python scripts/stage0_d691_iv_size.py --selftest
    uv run python scripts/stage0_d691_iv_size.py --gates     # the IV table and data gates G1-G5; no outcome is read
    uv run python scripts/stage0_d691_iv_size.py --time      # times the rotation on a few offsets; states the projection
    uv run python scripts/stage0_d691_iv_size.py --run       # once

In-sample to 2025-02-28 (ES's options rows on or after 2025-03-01 are dropped before anything is computed); the vault
is never read. Dealer gamma (GEX): SqueezeMetrics, read to < 2025-03-01 as D663/D671; no per-date series is written.
Reads no break P&L (Stage 1's, if any).
"""
from __future__ import annotations

import argparse
import json
import os
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
import stage0_d671_break_construction as C  # noqa: E402
from backtest_framework.opening.agents import b76_price, implied_vol  # noqa: E402

M, T = C.M, C.T
DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
FIX = DATA / "fixtures"
OUT = REPO / "data" / "stage0_d691_iv_size.json"
GATES_OUT = REPO / "data" / "stage0_d691_gates.json"
CACHE = REPO / "temp"
ROOTS = ("ES", "NQ")
CUT = "2025-03-01"
WINDOW_FROM = "2018-01-09"  # D671's evaluation window
COVID = ("2020-02-01", "2020-04-30")
ERA_SPLIT = "2022-05-16"
MIN_AHEAD, MAX_AHEAD, EXPIRY_HHMM = 2, 15, "16:00"
NW_LAGS, EDGE = 5, 21
SIGN0 = C.SIGN.copy()
SIGN1 = np.append(SIGN0, 1.0)  # ivrv enters with a declared positive sign
OPT_COLS = ["session", "family", "right", "strike", "expiry_date", "expiry_hhmm", "underlying", "settle"]
OPT_DTYPE = {"session": str, "family": str, "right": str, "expiry_date": str, "expiry_hhmm": str, "underlying": str}


class D691Error(RuntimeError):
    pass


# ================================================================================ statistics
def nw_t(x: np.ndarray, lags: int = NW_LAGS) -> tuple[float, float]:
    """Mean's t with a Newey-West (Bartlett) HAC variance, `lags` lags."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    e = x - x.mean()
    v = e @ e / n
    for L in range(1, lags + 1):
        v += 2 * (1 - L / (lags + 1)) * (e[L:] @ e[:-L]) / n
    se = np.sqrt(v / n)
    return float(x.mean() / se), float(se)


# ================================================================================ the implied volatility (D691 s.1)
def calendar(root: str) -> np.ndarray:
    s = pd.read_csv(FIX / "fut_index_sessions.csv.gz", usecols=["root", "day"], dtype={"root": str, "day": str}, encoding="utf-8")
    return np.array(sorted(s.loc[s["root"] == root, "day"].unique()))


def strip(root: str) -> pd.DataFrame:
    st = pd.read_csv(FIX / "fut_settle_strip.csv.gz", dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    st = st[(st["root"] == root) & (st["ref"] < CUT)]
    return st


def candidates(root: str, tcal: np.ndarray) -> pd.DataFrame:
    """Option rows usable on each session (their settle is the prior business day's), 16:00 expiries MIN_AHEAD to
    MAX_AHEAD sessions ahead, settle > 0. The seal is applied to every chunk before anything is computed."""
    pos = pd.Series(np.arange(len(tcal)), index=tcal)
    parts = []
    for ch in pd.read_csv(FIX / f"fut_{root.lower()}_options_eod.csv.gz", usecols=OPT_COLS, dtype=OPT_DTYPE,
                          chunksize=2_000_000, encoding="utf-8"):
        ch = ch[ch["session"] < CUT]
        if ch.empty:
            continue
        i = ch["session"].map(pos).to_numpy(float)
        n = np.searchsorted(tcal, ch["expiry_date"].to_numpy(str)) - i
        keep = (np.isfinite(i) & (n >= MIN_AHEAD) & (n <= MAX_AHEAD) & (ch["expiry_hhmm"].to_numpy(str) == EXPIRY_HHMM)
                & (ch["settle"].to_numpy(float) > 0))
        parts.append(ch[keep].assign(n_ahead=n[keep].astype(int)))
    c = pd.concat(parts, ignore_index=True)
    if (c["session"] >= CUT).any():
        raise D691Error("seal: an options row on or after 2025-03-01 survived")
    return c


def prior_settle(settle_map: pd.Series, refs: np.ndarray, session: str, contract: str) -> float:
    prev = refs[np.searchsorted(refs, session) - 1]
    return float(settle_map.get((prev, contract), np.nan))


def atm_iv_session(g: pd.DataFrame, F: float) -> dict[str, Any]:
    """One session's IV: the nearest qualifying expiry; at the two strikes bracketing F, the mean of call and put IV
    where both invert; linear in strike to F."""
    e = g["expiry_date"].min()
    x = g[g["expiry_date"] == e]
    tau = (int(x["n_ahead"].iloc[0]) + 1) / 252.0
    K = x["strike"].to_numpy(float)
    near = np.abs(K / F - 1) < 0.05
    x = x[near]
    if x.empty:
        return {"iv": np.nan, "reason": "no strike near F"}
    iv = implied_vol(x["settle"].to_numpy(float), np.full(len(x), F), x["strike"].to_numpy(float), np.full(len(x), tau),
                     x["right"].to_numpy(str) == "C")
    t = pd.DataFrame({"K": x["strike"].to_numpy(float), "right": x["right"].to_numpy(str), "iv": iv})
    t = t.groupby(["K", "right"])["iv"].mean().unstack()
    if not {"C", "P"} <= set(t.columns):
        return {"iv": np.nan, "reason": "one side missing"}
    both = t.dropna(subset=["C", "P"])
    k_iv = ((both["C"] + both["P"]) / 2)
    lo, hi = k_iv[k_iv.index <= F], k_iv[k_iv.index >= F]
    if lo.empty or hi.empty:
        return {"iv": np.nan, "reason": "no bracketing pair"}
    k0, k1 = float(lo.index.max()), float(hi.index.min())
    v0, v1 = float(k_iv.loc[k0]), float(k_iv.loc[k1])
    v = v0 if k1 == k0 else v0 + (v1 - v0) * (F - k0) / (k1 - k0)
    return {"iv": v, "expiry": e, "tau": tau, "k0": k0, "k1": k1, "F": F, "reason": ""}


def build_iv(root: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    tcal = calendar(root)
    st = strip(root)
    settle_map = st.set_index(["ref", "contract"])["settle"]
    refs = np.array(sorted(st["ref"].unique()))
    cand = candidates(root, tcal)
    rows = {}
    for d, g in cand.groupby("session", sort=True):
        und = g.loc[g["expiry_date"] == g["expiry_date"].min(), "underlying"].mode().iloc[0]
        F = prior_settle(settle_map, refs, d, und)
        if not np.isfinite(F):
            rows[d] = {"iv": np.nan, "reason": "no prior settle for the underlying", "underlying": und}
            continue
        r = atm_iv_session(g[g["underlying"] == und], F)
        r["underlying"] = und
        rows[d] = r
    tab = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    return tab, {"tcal": tcal, "refs": refs, "settle_map": settle_map, "cand": cand}


def iv_cached(root: str, need_ctx: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """The IV table, cached in temp/ keyed on the options fixture's, the strip's, the calendar's and this file's mtimes.
    `need_ctx` rebuilds (the round-trip gate needs the option rows) and refreshes the cache."""
    key = ";".join(f"{p.name}:{p.stat().st_mtime_ns}" for p in (FIX / f"fut_{root.lower()}_options_eod.csv.gz",
                                                                FIX / "fut_settle_strip.csv.gz", FIX / "fut_index_sessions.csv.gz",
                                                                Path(__file__)))
    path, kpath = CACHE / f"d691_iv_{root.lower()}.csv", CACHE / f"d691_iv_{root.lower()}.key"
    if not need_ctx and path.exists() and kpath.exists() and kpath.read_text(encoding="utf-8") == key:
        tab = pd.read_csv(path, index_col=0, dtype={"expiry": str, "underlying": str, "reason": str}, encoding="utf-8")
        tab.index = tab.index.astype(str)
        return tab, {}
    tab, ctx = build_iv(root)
    CACHE.mkdir(exist_ok=True)
    tab.to_csv(path, encoding="utf-8")
    kpath.write_text(key, encoding="utf-8")
    return tab, ctx


# ================================================================================ gates (D691 s.3)
def iv_lag_audit(tab: pd.DataFrame, root: str, sessions: list[str], ref_rule: Callable[[np.ndarray, str], str] | None = None) -> None:
    """G3: a second implementation re-derives F and IV for the sampled sessions from the strip's settles dated
    strictly before the session and the option rows usable on it, by a loop that never calls build_iv. `ref_rule`
    replaces the previous-ref rule (the canary passes one that takes the session's own settle)."""
    st = strip(root)
    cand = candidates(root, calendar(root))
    for d in sessions:
        if not np.isfinite(tab.at[d, "iv"]):
            continue
        g = cand[cand["session"] == d]
        und = str(tab.at[d, "underlying"])
        s = st[st["contract"] == und]
        if ref_rule is None:
            s_prev = s[s["ref"] < d]
            F = float(s_prev.sort_values("ref")["settle"].iloc[-1])
        else:
            F = float(s.loc[s["ref"] == ref_rule(s["ref"].to_numpy(str), d), "settle"].iloc[0])
        want = atm_iv_session(g[g["underlying"] == und], F)["iv"]
        if not np.isclose(want, float(tab.at[d, "iv"]), rtol=0, atol=1e-10):
            raise D691Error(f"lag: IV at {d} is not built from the prior settlement ({want} vs {tab.at[d, 'iv']})")


def roundtrip_audit(ctx: dict[str, Any], tab: pd.DataFrame, sessions: list[str]) -> float:
    """G2: price -> IV -> price on the sampled sessions' bracketing options; returns the largest relative error."""
    worst = 0.0
    cand, settle_map, refs = ctx["cand"], ctx["settle_map"], ctx["refs"]
    for d in sessions:
        if not np.isfinite(tab.at[d, "iv"]):
            continue
        und = str(tab.at[d, "underlying"])
        F = prior_settle(settle_map, refs, d, und)
        x = cand[(cand["session"] == d) & (cand["underlying"] == und) & (cand["expiry_date"] == tab.at[d, "expiry"])]
        x = x[x["strike"].isin([tab.at[d, "k0"], tab.at[d, "k1"]])]
        tau = float(tab.at[d, "tau"])
        is_c = x["right"].to_numpy(str) == "C"
        px = x["settle"].to_numpy(float)
        iv = implied_vol(px, np.full(len(x), F), x["strike"].to_numpy(float), np.full(len(x), tau), is_c)
        back = b76_price(np.full(len(x), F), x["strike"].to_numpy(float), iv, np.full(len(x), tau), is_c)
        ok = np.isfinite(back)
        if ok.any():
            worst = max(worst, float(np.max(np.abs(back[ok] - px[ok]) / px[ok])))
    if worst > 1e-6:
        raise D691Error(f"inversion: a price does not round-trip ({worst:.2e})")
    return worst


# ================================================================================ frames (D671's pipeline, unchanged)
def frames() -> dict[str, dict[str, Any]]:
    b, use, _gd, R = M.load_bars(DATA, False, ROOTS)
    C._R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=ROOTS)
    dix = pd.read_csv(DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < CUT].set_index("date")["gex"].astype(float).sort_index()
    cal = pd.read_csv(FIX / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    out = {}
    for r in ROOTS:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        on = C.overnight(b, r)
        C.overnight_audit(on)
        S_ = C.session_features(d, on, cal[cal["root"] == r].set_index("day"))
        target_audit(S_, d)
        out[r] = {"d": d, "S": S_}
    return out


def target_audit(S_: pd.DataFrame, d: pd.DataFrame) -> None:
    """Right quantity: the target is ln((high - low) / ATR20), not a close-to-close return."""
    want = np.log((d["high"] - d["low"]) / d["atr20"]).reindex(S_.index).to_numpy(float)
    if not np.allclose(S_["y"].to_numpy(float), want, equal_nan=True):
        raise D691Error("right quantity: y is not ln(range / ATR20)")


def design(fr: dict[str, Any], iv: pd.DataFrame) -> dict[str, Any]:
    d, S_ = fr["d"], fr["S"]
    sess = S_.index.to_numpy(str)
    ivs = iv["iv"].reindex(S_.index).to_numpy(float)
    rv = d["sig20"].reindex(S_.index).to_numpy(float) / 1e4 * np.sqrt(252.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ivrv = np.log(ivs / rv)
    F0 = S_[list(C.SIZE_FEATS)].to_numpy(float)
    y = S_["y"].to_numpy(float)
    return {"sess": sess, "F0": F0, "y": y, "ivrv": ivrv, "lniv": np.log(ivs), "rv": rv, "iv": ivs,
            "oc": (np.abs(d["close"] - d["open"]) / d["atr20"]).reindex(S_.index).to_numpy(float) if "close" in d else None}


def forecast(F: np.ndarray, y: np.ndarray, sign: np.ndarray) -> np.ndarray:
    old = C.SIGN
    C.SIGN = sign
    try:
        f, _ = C.size_forecast(F, y)
    finally:
        C.SIGN = old
    return f


# ================================================================================ the rotation (processes over offsets[i::N])
_W: dict[str, Any] = {}


def _init(F0: np.ndarray, y: np.ndarray, ivrv: np.ndarray, e0: np.ndarray, ev: np.ndarray, sign1: np.ndarray) -> None:
    _W.update(F0=F0, y=y, ivrv=ivrv, e0=e0, ev=ev, sign1=sign1)


def rot_stat(k: int, F0: np.ndarray, y: np.ndarray, ivrv: np.ndarray, e0: np.ndarray, ev: np.ndarray,
             sign1: np.ndarray = SIGN1) -> float:
    """Mean loss differential with ivrv's finite values rotated by k positions among themselves (NaNs stay put)."""
    fin = np.flatnonzero(np.isfinite(ivrv))
    r = ivrv.copy()
    r[fin] = np.roll(ivrv[fin], k)
    f1 = forecast(np.column_stack([F0, r]), y, sign1)
    d = e0 ** 2 - (y - f1) ** 2
    m = ev & np.isfinite(d)
    return float(d[m].mean())


def _job(offsets: list[int]) -> list[tuple[int, float]]:
    return [(k, rot_stat(k, _W["F0"], _W["y"], _W["ivrv"], _W["e0"], _W["ev"], _W["sign1"])) for k in offsets]


def rotation(F0, y, ivrv, e0, ev, offsets: list[int], workers: int, sign1: np.ndarray = SIGN1) -> dict[int, float]:
    chunks = [offsets[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(F0, y, ivrv, e0, ev, sign1)) as pool:
        res = [kv for part in pool.map(_job, chunks) for kv in part]
    return dict(res)


# ================================================================================ the study
def root_study(r: str, dz: dict[str, Any], workers: int, iv_tab: pd.DataFrame) -> dict[str, Any]:
    sess, F0, y, ivrv = dz["sess"], dz["F0"], dz["y"], dz["ivrv"]
    f0 = forecast(F0, y, SIGN0)
    F1 = np.column_stack([F0, ivrv])
    f1 = forecast(F1, y, SIGN1)
    idx = list(range(0, len(sess), max(1, len(sess) // 30)))
    C.SIGN = SIGN1
    try:
        C.forecast_audit(f1, F1, y, sess, idx)
    finally:
        C.SIGN = SIGN0
    e0, e1 = y - f0, y - f1
    ev = (sess >= WINDOW_FROM) & np.isfinite(e0) & np.isfinite(e1)
    d = e0 ** 2 - e1 ** 2
    t, se = nw_t(d[ev])
    exc = ev & ~((sess >= COVID[0]) & (sess <= COVID[1]))
    fin_n = int(np.isfinite(ivrv).sum())
    offsets = list(range(EDGE, fin_n - EDGE))
    k0 = rot_stat(0, F0, y, ivrv, e0, ev)
    if not np.isclose(k0, float(d[ev].mean()), rtol=0, atol=1e-12):
        raise D691Error(f"rotation: offset 0 gives {k0}, not the actual {d[ev].mean()}")
    t0 = time.time()
    rot = rotation(F0, y, ivrv, e0, ev, offsets, workers)
    wall = time.time() - t0
    null = np.array([rot[k] for k in offsets])
    obs = float(d[ev].mean())

    def sp(f: np.ndarray, m: np.ndarray = ev) -> float:
        mm = m & np.isfinite(f) & np.isfinite(y)
        return float(stats.spearmanr(f[mm], y[mm])[0])
    f_iv = forecast(dz["lniv"][:, None], y, np.array([1.0]))
    f_rv5 = forecast(F0[:, [C.SIZE_FEATS.index("rv5")]], y, np.array([1.0]))
    # without g
    keep = [i for i, n in enumerate(C.SIZE_FEATS) if n != "g"]
    s0n, s1n = SIGN0[keep], np.append(SIGN0[keep], 1.0)
    f0n = forecast(F0[:, keep], y, s0n)
    f1n = forecast(np.column_stack([F0[:, keep], ivrv]), y, s1n)
    dn = (y - f0n) ** 2 - (y - f1n) ** 2
    evn = ev & np.isfinite(dn)
    old = C.SIGN
    C.SIGN = SIGN1
    try:
        _, B1 = C.size_forecast(F1, y)
    finally:
        C.SIGN = old
    last = B1[np.flatnonzero(np.isfinite(B1).all(axis=1))[-1]]
    yrs = pd.Series(sess).str[:4].to_numpy()
    by_year = {yv: float(d[ev & (yrs == yv)].mean()) for yv in sorted(set(yrs[ev]))}
    sec = None
    if dz["oc"] is not None:
        yo = np.log(np.where(dz["oc"] > 0, dz["oc"], np.nan))
        g0, g1 = forecast(F0, yo, SIGN0), forecast(F1, yo, SIGN1)
        ds = (yo - g0) ** 2 - (yo - g1) ** 2
        ms = ev & np.isfinite(ds)
        ts, _ = nw_t(ds[ms])
        sec = {"target": "ln(|open - close| / ATR20)", "dbar": float(ds[ms].mean()), "t_hac": ts, "n": int(ms.sum())}
    win = ev
    cov = float(np.isfinite(dz["iv"][sess >= WINDOW_FROM]).mean())
    res = {
        "n_eval": int(ev.sum()), "window": [str(sess[ev].min()), str(sess[ev].max())],
        "gate_S": {"a_dbar": obs, "a_t_hac": t, "a_se": se, "a_p_one_sided": float(stats.norm.sf(t)),
                   "b_rotation": {"offsets": len(offsets), "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)),
                                  "p95_se": 0.0, "rank": float((null < obs).mean()), "wall_s": round(wall, 1)},
                   "c_dbar_ex_covid": float(d[exc].mean())},
        "mse0": float(np.mean(e0[ev] ** 2)), "mse1": float(np.mean(e1[ev] ** 2)),
        "mse_reduction_pct": float(100 * obs / np.mean(e0[ev] ** 2)),
        "reported": {"spearman_M0": sp(f0), "spearman_M1": sp(f1), "spearman_lnIV_alone": sp(f_iv), "spearman_rv5_alone": sp(f_rv5),
                     "M1_final_slope_on_ivrv": float(last[-1]), "M1_final_slopes": dict(zip(list(C.SIZE_FEATS) + ["ivrv"], map(float, last))),
                     "dbar_by_year": by_year,
                     "dbar_before_after_2022_05_16": [float(d[ev & (sess < ERA_SPLIT)].mean()), float(d[ev & (sess >= ERA_SPLIT)].mean())],
                     "without_g": {"dbar": float(dn[evn].mean()), "t_hac": nw_t(dn[evn])[0]},
                     "secondary_open_close": sec,
                     "iv_coverage_in_window": cov,
                     "deviation": "D665's break |follow-through| secondary target not computed (D691 s.1 lists it as reported)"},
    }
    return res


def gates(iv_tabs: dict[str, pd.DataFrame], ctxs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for r in ROOTS:
        tab = iv_tabs[r]
        w = tab[tab.index >= WINDOW_FROM]
        cov = float(np.isfinite(w["iv"]).mean())
        miss = w[~np.isfinite(w["iv"])]
        if (tab.index >= CUT).any():
            raise D691Error("G4 seal: the IV table holds a session on or after 2025-03-01")
        rng = np.random.default_rng(691)
        samp = sorted(rng.choice(tab.index[np.isfinite(tab["iv"])].to_numpy(), 30, replace=False))
        iv_lag_audit(tab, r, samp)
        worst = roundtrip_audit(ctxs[r], tab, samp[:10]) if ctxs.get(r) else None
        yrs = pd.Series(tab["iv"].to_numpy(float), index=tab.index.str[:4])
        out[r] = {"G1_coverage_in_window": cov, "G1_pass": bool(cov >= 0.95),
                  "missing_by_year": miss.index.str[:4].value_counts().sort_index().to_dict(),
                  "missing_reasons": miss["reason"].value_counts().to_dict() if "reason" in miss else {},
                  "G2_roundtrip_worst_rel": worst, "G3_lag_audit": "passed on 30 sessions", "G4_seal": "held",
                  "G5_median_iv_by_year": {k: round(float(v), 4) for k, v in yrs.groupby(level=0).median().items()},
                  "sessions": int(len(tab))}
    return out


def build(workers: int) -> dict[str, Any]:
    t0 = time.time()
    iv_tabs, ctxs = {}, {}
    for r in ROOTS:
        iv_tabs[r], ctxs[r] = iv_cached(r, need_ctx=True)
    out: dict[str, Any] = {"spec": "D691 (7a9e4e69)", "credit": "dealer gamma (GEX): SqueezeMetrics", "gates": gates(iv_tabs, ctxs)}
    if not all(v["G1_pass"] for v in out["gates"].values()):
        raise D691Error(f"G1 failed: {out['gates']}")
    fr = frames()
    res = {}
    for r in ROOTS:
        dz = design(fr[r], iv_tabs[r])
        rv = dz["rv"]
        fin = np.isfinite(dz["iv"]) & np.isfinite(rv)
        out["gates"][r]["G5_corr_iv_rv20"] = float(np.corrcoef(dz["iv"][fin], rv[fin])[0, 1])
        res[r] = root_study(r, dz, workers, iv_tabs[r])
    t = {r: res[r]["gate_S"]["a_p_one_sided"] for r in ROOTS}
    holm = T.holm(t)
    for r in ROOTS:
        g = res[r]["gate_S"]
        g["holm_p"] = holm[r]
        g["checks"] = {"a_dm_t_holm": bool(g["a_t_hac"] >= 2.0 and holm[r] < 0.05 and g["a_dbar"] > 0),
                       "b_above_rotation_p95": bool(g["a_dbar"] > g["b_rotation"]["p95"]),
                       "c_positive_ex_covid": bool(g["c_dbar_ex_covid"] > 0)}
        res[r]["verdict"] = "SIZE INFORMATION CONFIRMED" if all(g["checks"].values()) else "NOT CONFIRMED"
    out["roots"] = res
    rep = {r: res[r]["reported"] for r in ROOTS}
    out["predictions"] = {
        "1_ES_passes_gate_S": res["ES"]["verdict"] == "SIZE INFORMATION CONFIRMED",
        "2_NQ_gain_smaller_than_ES": bool(res["NQ"]["gate_S"]["a_dbar"] < res["ES"]["gate_S"]["a_dbar"]),
        "3_lnIV_beats_rv5_both": bool(all(rep[r]["spearman_lnIV_alone"] > rep[r]["spearman_rv5_alone"] for r in ROOTS)),
        "4_ivrv_slope_positive_both": bool(all(rep[r]["M1_final_slope_on_ivrv"] > 0 for r in ROOTS)),
        "5_gain_larger_without_g_both": bool(all(rep[r]["without_g"]["dbar"] > res[r]["gate_S"]["a_dbar"] for r in ROOTS))}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D691Error, C.D671Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(3)
    # 1. the IV machinery on a synthetic chain: settles priced at a known vol invert to it, and the bracket interpolates
    F, tau, sig = 5000.0, 6 / 252, 0.18
    Ks = np.arange(4800, 5201, 25.0)
    rows = []
    for K in Ks:
        for right in ("C", "P"):
            px = float(b76_price(np.array([F]), np.array([K]), np.array([sig]), np.array([tau]), np.array([right == "C"]))[0])
            rows.append({"session": "2019-06-03", "strike": K, "right": right, "expiry_date": "2019-06-10", "n_ahead": 5,
                         "settle": px, "underlying": "ESM9"})
    g = pd.DataFrame(rows)
    r = atm_iv_session(g, F)
    if not abs(r["iv"] - sig) < 1e-8:
        raise SystemExit(f"selftest: ATM IV {r['iv']} is not {sig}")
    # 2. the forecast's lag canary (D671's own)
    Fz = rng.normal(size=(400, 2))
    yz = Fz[:, 0] * 0.5 + rng.normal(size=400)
    old = C.SIGN
    C.SIGN = np.array([1.0, 1.0])
    try:
        fl, _ = C.size_forecast(Fz, yz, leak=True)
        must_raise("a forecast fitted on its own row", lambda: C.forecast_audit(fl, Fz, yz, np.array([f"{i:05d}" for i in range(400)]), [300, 350, 399]))
    finally:
        C.SIGN = old
    # 3. the sign audit: a target built to rise with ivrv gives a positive slope and d > 0; noise gives none
    n = 900
    base = rng.normal(size=(n, 6))
    ivx = rng.normal(size=n)
    ysig = base[:, 2] * 0.3 + ivx * 0.6 + rng.normal(size=n) * 0.5
    e0 = ysig - forecast(base, ysig, np.ones(6))
    e1 = ysig - forecast(np.column_stack([base, ivx]), ysig, np.ones(7))
    dd = e0 ** 2 - e1 ** 2
    tt, _ = nw_t(dd[np.isfinite(dd)])
    if not tt > 3:
        raise SystemExit(f"selftest: an injected size signal did not show (t {tt:.2f})")
    ynoise = base[:, 2] * 0.3 + rng.normal(size=n)
    e0n = ynoise - forecast(base, ynoise, np.ones(6))
    e1n = ynoise - forecast(np.column_stack([base, ivx]), ynoise, np.ones(7))
    tn, _ = nw_t((e0n ** 2 - e1n ** 2)[np.isfinite(e1n) & np.isfinite(e0n)])
    if not tn < 3:
        raise SystemExit(f"selftest: noise looked like a size signal (t {tn:.2f})")
    # 4. the right quantity: a close-to-close target is refused
    idx = pd.Index([f"2019-01-{i:02d}" for i in range(1, 11)])
    dfr = pd.DataFrame({"high": np.linspace(101, 110, 10), "low": np.linspace(99, 100, 10), "atr20": 2.0}, index=idx)
    S_ok = pd.DataFrame({"y": np.log((dfr["high"] - dfr["low"]) / dfr["atr20"])}, index=idx)
    target_audit(S_ok, dfr)
    must_raise("a close-to-close target", lambda: target_audit(S_ok.assign(y=rng.normal(size=10)), dfr))
    # 5. the rotation: offset 0 reproduces the actual, and chunk == whole bit for bit
    y5 = ysig
    f05 = forecast(base, y5, np.ones(6))
    e05 = y5 - f05
    ev5 = np.isfinite(e05)
    iv5 = ivx.copy()
    iv5[:5] = np.nan
    one7 = np.ones(7)
    act = forecast(np.column_stack([base, iv5]), y5, one7)
    dact = e05 ** 2 - (y5 - act) ** 2
    k0 = rot_stat(0, base, y5, iv5, e05, ev5, one7)
    if not np.isclose(k0, float(dact[ev5 & np.isfinite(dact)].mean()), rtol=0, atol=1e-12):
        raise SystemExit("selftest: rotation offset 0 does not reproduce the actual")
    serial = {k: rot_stat(k, base, y5, iv5, e05, ev5, one7) for k in (21, 22, 23, 40)}
    par = rotation(base, y5, iv5, e05, ev5, [21, 22, 23, 40], 2, one7)
    if any(serial[k] != par[k] for k in serial):
        raise SystemExit("selftest: the rotation's processes differ from the serial run")
    if len(set(serial.values())) < 2 or max(serial.values()) >= k0:
        raise SystemExit("selftest: rotating an injected signal does not destroy it")
    # 6. the F bookkeeping (the IV lag canary itself fires on real data in --gates)
    lag_ok = np.isclose(r["F"], F)
    if not lag_ok:
        raise SystemExit("selftest: F bookkeeping")
    print(f"selftest: {len(fired)} canaries fired: {fired}; checks passed: ATM IV inverts a known vol, an injected size "
          "signal shows and noise does not, offset 0 reproduces, processes == serial, rotation destroys the signal. "
          "The IV lag canary needs the fixtures and fires in --gates.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.gates:
        iv_tabs, ctxs = {}, {}
        for r in ROOTS:
            iv_tabs[r], ctxs[r] = iv_cached(r, need_ctx=True)
        g = gates(iv_tabs, ctxs)
        # the IV lag canary on real data: taking the session's own settle must be caught
        r0 = "ES"
        tab = iv_tabs[r0]
        some = [s for s in tab.index[np.isfinite(tab["iv"])] if s >= "2019-01-01"][:3]
        try:
            iv_lag_audit(tab, r0, some, ref_rule=lambda refs, d: max(refs[refs <= d]))
        except D691Error:
            g["G3_canary"] = "fired: an IV built on the session's own settle is caught"
        else:
            raise SystemExit("the IV lag canary did not fire on real data")
        GATES_OUT.write_text(json.dumps(g, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(g, indent=1, default=str))
        return 0
    if a.time:
        fr = frames()
        for r in ROOTS:
            tab, _ = iv_cached(r)
            dz = design(fr[r], tab)
            f0 = forecast(dz["F0"], dz["y"], SIGN0)
            e0 = dz["y"] - f0
            ev = (dz["sess"] >= WINDOW_FROM) & np.isfinite(e0)
            t0 = time.time()
            for k in (21, 22, 23):
                rot_stat(k, dz["F0"], dz["y"], dz["ivrv"], e0, ev)
            per = (time.time() - t0) / 3
            n_off = int(np.isfinite(dz["ivrv"]).sum()) - 2 * EDGE
            print(f"{r}: {per:.2f} s an offset x {n_off} offsets / {a.workers} workers = about {per * n_off / a.workers / 60:.1f} min")
        return 0
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D691Error(f"{OUT.name} exists: D691 runs once")
    out = build(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({r: {"verdict": out["roots"][r]["verdict"], **{k: out["roots"][r]["gate_S"][k] for k in ("a_dbar", "a_t_hac", "holm_p", "checks")},
                          "rank": out["roots"][r]["gate_S"]["b_rotation"]["rank"]} for r in ROOTS}, indent=1, default=float))
    print(json.dumps(out["predictions"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
