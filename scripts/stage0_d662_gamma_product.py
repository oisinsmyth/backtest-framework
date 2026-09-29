"""D662 Stage 0: does dealer short gamma multiply the opening shock? The shock x gamma product at the opening-range
break on ES. Written after D662's design (c9a40a5), committed before its one run.

    uv run python scripts/stage0_d662_gamma_product.py --selftest
    uv run python scripts/stage0_d662_gamma_product.py --dry-run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
    uv run python scripts/stage0_d662_gamma_product.py --run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

In-sample only: the bars and G come through run_opening_v2.load_inputs (sealed at 2025-03-01). The break is D645's B3
(run_opening_stages.b3_trade), re-found here with its minute so the 60-minute follow-through can be read without a stop;
the two are asserted equal. F = D x ln(P60 / P_entry) x 1e4. g = -G$ / V20 x 100 (dealer SHORT gamma, $ per 1% over the
prior 20 sessions' mean day-session dollar volume). s_gap = D x (open / prior close - 1) x 100; s_stop = D x (u - w),
u / w the opening range's run beyond the prior high / low (%). Per shock: OLS F = a + b1 g + b2 s + b3 g s (HAC lag 5),
the purged enumerated rotation of g (offsets within +/-10 dropped), the midday placebo (range 12:00-12:29, breaks
12:30-13:59), controls, the model's own size claim (beta on I = sign(g s) sigma_d sqrt(|G$| |s| / V20)), tails, eras,
MDE. Writes data/stage0_d662_gamma_product.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "stage0_d662_gamma_product.json"
ROOT = "ES"
MULT = 50.0
NW_LAG = 5
PURGE = 10
Z80 = 1.959964 + 0.841621
COVID = ("2020-02-01", "2020-04-30")
BREAK_0DTE = "2022-05-16"
MORNING = ("09:30", "09:59", "10:00", "11:29")
MIDDAY = ("12:00", "12:29", "12:30", "13:59")
SHOCKS = ("s_gap", "s_stop")
DECLARED = ("inputs", "sessions", "shocks", "placebo", "verdict", "predictions", "audits")


class D662Error(RuntimeError):
    pass


def hm(s: str) -> int:
    return int(s[:2]) * 60 + int(s[3:])


def load_v2() -> Any:
    sys.path.insert(0, str(REPO / "scripts"))
    import diag_opening_mechanics as M
    return M.load_v2()


# ============================================================================================ the break and F
def find_break(bars: dict[str, np.ndarray], lo_hi: tuple[float, float], first: int, last: int,
               entry_shift: int = 1) -> tuple[int, int, float] | None:
    """(D, entry minute, entry price): the first bar starting first..last whose close lies outside [lo, hi]; entry at
    the close of the bar starting one minute later (B3's convention)."""
    lo, hi = lo_hi
    m, c = bars["m"], bars["c"]
    for i in np.flatnonzero((m >= first) & (m <= last)):
        if c[i] > hi or c[i] < lo:
            D = 1 if c[i] > hi else -1
            eb = int(m[i]) + entry_shift
            k = np.flatnonzero(m == eb)
            if len(k) == 0:
                return None
            return D, eb, float(c[k[0]])
    return None


def follow(bars: dict[str, np.ndarray], eb: int, D: int, entry: float, horizon: int = 60) -> float:
    m, c = bars["m"], bars["c"]
    j = np.flatnonzero(m <= eb + horizon)
    return D * math.log(float(c[j[-1]]) / entry) * 1e4


def range_of(bars: dict[str, np.ndarray], a: int, b: int) -> tuple[float, float] | None:
    sel = (bars["m"] >= a) & (bars["m"] <= b)
    if not sel.any():
        return None
    return float(bars["l"][sel].min()), float(bars["h"][sel].max())


# ============================================================================================ per-session frame
def session_frame(b: pd.DataFrame, tab: pd.DataFrame, G: pd.Series) -> pd.DataFrame:
    x = b[(b["root"] == ROOT) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
    dv = (x["close"] * x["volume"] * MULT).groupby(x["session"]).sum()
    close = x.groupby("session")["close"].last()
    d = tab.copy()
    d["dv"] = dv.reindex(d.index)
    d["sig20"] = (np.log(close / close.shift(1)) * 1e4).shift(1).rolling(20, min_periods=15).std().reindex(d.index)
    d["V20"] = d["dv"].shift(1).rolling(20, min_periods=15).mean()
    d["G"] = G.reindex(d.index)
    d["Gd"] = d["G"] * MULT * d["prior_close"] ** 2 * 0.01
    d["g"] = -d["Gd"] / d["V20"] * 100
    d["gap_pct"] = (d["open"] / d["prior_close"] - 1) * 100
    d["u"] = np.maximum(d["hi_10:00"] / d["prior_high"] - 1, 0) * 100
    d["w"] = np.maximum(1 - d["lo_10:00"] / d["prior_low"], 0) * 100
    ok = (d["usable"] & (d.index >= "2016-01-04") & (d.index < "2025-03-01")
          & np.isfinite(d[["g", "gap_pct", "u", "w", "sig20", "V20", "hi_10:00", "lo_10:00"]]).all(axis=1))
    return d[ok]


def rows_for(d: pd.DataFrame, bars: dict, window: tuple[str, str, str, str], R: Any) -> pd.DataFrame:
    a, b_, f, l = (hm(t) for t in window)
    out = []
    for s in d.index:
        bb = bars.get((ROOT, s))
        if bb is None:
            continue
        lh = (float(d.at[s, "lo_10:00"]), float(d.at[s, "hi_10:00"])) if window == MORNING else range_of(bb, a, b_)
        if lh is None:
            continue
        br = find_break(bb, lh, f, l)
        if br is None:
            continue
        D, eb, entry = br
        out.append({"session": s, "D": D, "eb": eb, "entry": entry, "F": follow(bb, eb, D, entry)})
    r = pd.DataFrame(out).set_index("session")
    r = r.join(d[["g", "gap_pct", "u", "w", "sig20", "V20", "Gd"]], how="inner")
    r["s_gap"] = r["D"] * r["gap_pct"]
    r["s_stop"] = r["D"] * (r["u"] - r["w"])
    for k, mv in (("s_gap", r["gap_pct"].abs()), ("s_stop", (r["u"] - r["w"]).abs())):
        r[f"I_{k}"] = np.sign(r["g"] * r[k]) * r["sig20"] * np.sqrt(r["Gd"].abs() * mv / r["V20"])
    return r


# ============================================================================================ statistics
def batched_b(y: np.ndarray, s: np.ndarray, Gm: np.ndarray) -> np.ndarray:
    """OLS of y on [1, g, s, g s] for every row of Gm (offsets x n) in one batched solve: returns (K, 4)."""
    n = len(y)
    gs = Gm * s
    S = lambda a: a.sum(axis=1)  # noqa: E731
    one = np.full(Gm.shape[0], float(n))
    XtX = np.empty((Gm.shape[0], 4, 4))
    cols = [None, Gm, np.broadcast_to(s, Gm.shape), gs]
    for i in range(4):
        for j in range(i, 4):
            if i == 0 and j == 0:
                v = one
            elif i == 0:
                v = S(cols[j])
            else:
                v = S(cols[i] * cols[j])
            XtX[:, i, j] = XtX[:, j, i] = v
    Xty = np.stack([np.full(Gm.shape[0], y.sum()), S(Gm * y), np.full(Gm.shape[0], (s * y).sum()), S(gs * y)], axis=1)
    return np.linalg.solve(XtX, Xty[..., None])[..., 0]


def loop_b(y: np.ndarray, s: np.ndarray, Gm: np.ndarray) -> np.ndarray:
    """The second implementation: lstsq per offset on the explicit design matrix."""
    return np.array([np.linalg.lstsq(np.column_stack([np.ones(len(y)), g, s, g * s]), y, rcond=None)[0] for g in Gm])


def hac(y: np.ndarray, X: np.ndarray) -> Any:
    return sm.OLS(y, sm.add_constant(X, has_constant="add")).fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAG})


def interaction(r: pd.DataFrame, k: str) -> dict[str, Any]:
    y, g, s = r["F"].to_numpy(float), r["g"].to_numpy(float), r[k].to_numpy(float)
    f = hac(y, np.column_stack([g, s, g * s]))
    b = batched_b(y, s, g[None, :])[0]
    if not np.allclose(b, f.params, rtol=1e-9, atol=1e-12):
        raise D662Error(f"{k}: the batched OLS differs from statsmodels: {b} vs {f.params}")
    return {"n": int(len(y)), "b": b.tolist(), "t_hac": f.tvalues.tolist(), "se_hac": f.bse.tolist(),
            "b3": float(b[3]), "t3": float(f.tvalues[3]), "p3_one_sided": float(stats.norm.sf(f.tvalues[3])),
            "mde80_b3": float(Z80 * f.bse[3])}


def rotation(d_cal: list[str], g_all: pd.Series, r: pd.DataFrame, k: str) -> dict[str, Any]:
    """Every circular offset of the per-session g series over the session calendar, purged within +/- PURGE."""
    T = len(d_cal)
    pos = pd.Index(d_cal).get_indexer(r.index)
    gv = g_all.reindex(d_cal).to_numpy(float)
    offs = np.array([o for o in range(T) if min(o, T - o) > PURGE or o == 0])
    Gm = gv[(pos[None, :] + offs[:, None]) % T]
    B = batched_b(r["F"].to_numpy(float), r[k].to_numpy(float), Gm)[:, 3]
    obs, null = B[0], B[1:]
    return {"offsets": int(len(null)), "b3_offset0": float(obs), "rank": float((null < obs).mean()),
            "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95)), "p05": float(np.quantile(null, 0.05))}


def controls(r: pd.DataFrame, k: str) -> dict[str, Any]:
    y = r["F"].to_numpy(float)
    fg, fs = hac(y, r[["g"]].to_numpy(float)), hac(y, r[[k]].to_numpy(float))
    out = {"g_alone": {"b": float(fg.params[1]), "t": float(fg.tvalues[1])},
           "s_alone": {"b": float(fs.params[1]), "t": float(fs.tvalues[1])}}
    pw = {}
    for lab, m in (("short_gamma", r["g"] > 0), ("long_gamma", r["g"] <= 0)):
        f = hac(y[m.to_numpy()], r.loc[m, [k]].to_numpy(float))
        pw[lab] = {"n": int(m.sum()), "slope": float(f.params[1]), "se": float(f.bse[1]), "t": float(f.tvalues[1])}
    diff = pw["short_gamma"]["slope"] - pw["long_gamma"]["slope"]
    pw["diff"] = diff
    pw["diff_t"] = diff / math.hypot(pw["short_gamma"]["se"], pw["long_gamma"]["se"])
    out["piecewise"] = pw
    un = hac(y, np.column_stack([r["g"], r[k], r["g"] * r[k].abs()]))
    out["unsigned_product_b3"] = float(un.params[3])
    fi = hac(y, r[[f"I_{k}"]].to_numpy(float))
    ci = fi.conf_int(alpha=0.10)[1]
    out["own_claim"] = {"beta": float(fi.params[1]), "ci90": [float(ci[0]), float(ci[1])], "t": float(fi.tvalues[1]),
                        "powered_null_below_half": bool(ci[1] < 0.5)}
    ip = batched_b(r[f"I_{k}"].to_numpy(float), r[k].to_numpy(float), r["g"].to_numpy(float)[None, :])[0]
    out["paper_implied_b3"] = float(ip[3])
    return out


def tails(r: pd.DataFrame, k: str) -> dict[str, Any]:
    def b3(m: pd.Series) -> float:
        rr = r[m]
        return float(batched_b(rr["F"].to_numpy(float), rr[k].to_numpy(float), rr["g"].to_numpy(float)[None, :])[0, 3])
    idx = r.index.to_series()
    top = r["F"].abs() >= r["F"].abs().quantile(0.99)
    yrs = sorted({s[:4] for s in r.index})
    return {"ex_covid": b3(~idx.between(*COVID)), "ex_top1pct_absF": b3(~top),
            "leave_one_year_out": {y: b3(~idx.str.startswith(y)) for y in yrs},
            "by_year": {y: b3(idx.str.startswith(y)) for y in yrs if idx.str.startswith(y).sum() > 30},
            "pre_0dte": b3(idx < BREAK_0DTE), "post_0dte": b3(idx >= BREAK_0DTE)}


def dist(v: np.ndarray) -> dict[str, float]:
    v = np.sort(v[np.isfinite(v)])
    k = max(1, int(round(0.01 * len(v))))
    return {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)), "sd": float(v.std(ddof=1)),
            "ex_top1pct": float(v[:-k].mean()), "ex_bottom1pct": float(v[k:].mean()), "trimmed": float(v[k:-k].mean()),
            "skew": float(stats.skew(v)), "kurtosis": float(stats.kurtosis(v))}


def analyse(job: tuple[str, pd.DataFrame, list[str], pd.Series, str]) -> dict[str, Any]:
    name, r, cal, g_all, k = job
    out = {"job": name, "shock": k, "interaction": interaction(r, k), "rotation": rotation(cal, g_all, r, k)}
    if name.startswith("morning"):
        out.update(controls=controls(r, k), tails=tails(r, k), F=dist(r["F"].to_numpy(float)))
    return out


# ============================================================================================ audits
def lag_audit(d: pd.DataFrame, b: pd.DataFrame, G: pd.Series, feature: Callable = None) -> None:
    """g, the gap and the stop run recomputed by a second path from bars that END at 09:59 (every later bar dropped):
    equal to the frame's. A feature that reads a bar at or after 10:00 cannot agree."""
    early = b[(b["root"] == ROOT) & (b["hhmm"] <= "09:59")]
    ref = (feature or _second_path)(early, d)
    for c in ("gap_pct", "u", "w"):
        if not np.allclose(ref[c].reindex(d.index).to_numpy(float), d[c].to_numpy(float), rtol=0, atol=1e-9):
            raise D662Error(f"lag: {c} differs when the bars end at 09:59")
    if feature is None:  # g: from the prior close's G and the prior 20 sessions only
        gd = G.reindex(d.index) * MULT * d["prior_close"] ** 2 * 0.01
        if not np.allclose((-gd / d["V20"] * 100).to_numpy(float), d["g"].to_numpy(float), rtol=0, atol=1e-12):
            raise D662Error("lag: g's second path differs")


def _second_path(early: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    rth = early[early["hhmm"] >= "09:30"]
    g = rth.groupby("session")
    o = g["open"].first()
    hi, lo = g["high"].max(), g["low"].min()
    out = pd.DataFrame(index=d.index)
    out["gap_pct"] = (o.reindex(d.index) / d["prior_close"] - 1) * 100
    out["u"] = np.maximum(hi.reindex(d.index) / d["prior_high"] - 1, 0) * 100
    out["w"] = np.maximum(1 - lo.reindex(d.index) / d["prior_low"], 0) * 100
    return out


def _canary(early: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """Measures the gap to the 10:00 bar's close: one bar too late. On bars that end at 09:59 it has nothing to read."""
    out = _second_path(early, d)
    c10 = early[early["hhmm"] == "10:00"].set_index("session")["close"].reindex(d.index)
    out["gap_pct"] = (c10 / d["prior_close"] - 1) * 100
    return out


def b3_audit(r: pd.DataFrame, d: pd.DataFrame, bars: dict, R: Any) -> None:
    """The break equals B3's, and F with B3's stop equals B3's gross where the stop did not fire."""
    for s, rec in r.iterrows():
        t = R.b3_trade(bars[(ROOT, s)], "10:00", float(d.at[s, "hi_10:00"]), float(d.at[s, "lo_10:00"]))
        if t is None or t[3] != rec["D"] or t[0] != rec["entry"]:
            raise D662Error(f"B3: the break on {s} differs from b3_trade's")
        if t[2] == "time":
            m, c = bars[(ROOT, s)]["m"], bars[(ROOT, s)]["c"]
            p60 = float(c[np.flatnonzero(m <= rec["eb"] + 60)[-1]])
            if abs(R.pnl_bp(int(rec["D"]), rec["entry"], p60) - R.pnl_bp(t[3], t[0], t[1])) > 1e-9:
                raise D662Error(f"B3: the 60-minute exit on {s} differs from B3's time exit")


def sign_audit(fol: Callable = follow) -> None:
    m = np.arange(hm("10:00"), hm("12:00"))
    up = {"m": m, "c": np.linspace(100, 101, len(m))}
    if not fol(up, hm("10:05"), 1, float(up["c"][5])) > 0:
        raise D662Error("sign: an up-break followed by a rise does not pay")
    dn = {"m": m, "c": np.linspace(101, 100, len(m))}
    if not fol(dn, hm("10:05"), -1, float(dn["c"][5])) > 0:
        raise D662Error("sign: a down-break followed by a fall does not pay")


def right_quantity(r: pd.DataFrame, bars: dict) -> None:
    f10 = np.array([rec["D"] * math.log(float(bars[(ROOT, s)]["c"][np.flatnonzero(bars[(ROOT, s)]["m"] <= rec["eb"] + 60)[-1]])
                                         / float(bars[(ROOT, s)]["c"][np.flatnonzero(bars[(ROOT, s)]["m"] == hm("10:00"))[0]]))
                    * 1e4 if (bars[(ROOT, s)]["m"] == hm("10:00")).any() else np.nan for s, rec in r.iterrows()])
    if np.allclose(f10[np.isfinite(f10)], r["F"].to_numpy(float)[np.isfinite(f10)]):
        raise D662Error("right quantity: F from the entry equals F from 10:00")


def null_exactness(bat: Callable = batched_b) -> None:
    rng = np.random.default_rng(662)
    n, K = 300, 25
    y = rng.integers(-3, 4, n).astype(float)  # tie-heavy
    s = rng.integers(-2, 3, n).astype(float)
    Gm = rng.integers(-2, 3, (K, n)).astype(float)
    if not np.allclose(bat(y, s, Gm), loop_b(y, s, Gm), rtol=1e-9, atol=1e-9):
        raise D662Error("null: the batched solve differs from the per-offset lstsq")


def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D662Error:
            fired.append(name)
            return
        raise SystemExit(f"SELFTEST FAILED: {name} did not raise")

    sign_audit()
    must_raise("sign-flipped", lambda: sign_audit(lambda bb, eb, D, e, horizon=60: -follow(bb, eb, D, e, horizon)))
    null_exactness()
    must_raise("null-drops-product", lambda: null_exactness(lambda y, s, Gm: np.concatenate(
        [batched_b(y, s, Gm)[:, :3], np.zeros((Gm.shape[0], 1))], axis=1)))
    # the lag audit on a synthetic frame
    sess = [f"2020-01-{i:02d}" for i in range(2, 30)]
    rows = []
    for i, s in enumerate(sess):
        for t in range(hm("09:30"), hm("11:00")):
            p = 100 + i + 0.01 * (t - hm("09:30"))
            rows.append({"root": ROOT, "session": s, "hhmm": f"{t // 60:02d}:{t % 60:02d}", "open": p, "high": p + .1,
                         "low": p - .1, "close": p, "volume": 10})
    b = pd.DataFrame(rows)
    d = pd.DataFrame(index=sess)
    d["prior_close"], d["prior_high"], d["prior_low"] = 99.5 + np.arange(len(sess)), 100.0 + np.arange(len(sess)), 99.0 + np.arange(len(sess))
    d["V20"] = 1e9
    G = pd.Series(np.linspace(-5, 5, len(sess)), index=sess)
    two = _second_path(b[b["hhmm"] <= "09:59"], d)
    d = d.join(two)
    d["g"] = -(G * MULT * d["prior_close"] ** 2 * 0.01) / d["V20"] * 100
    lag_audit(d, b, G)
    must_raise("lag-canary", lambda: lag_audit(d, b, G, feature=_canary))
    must_raise("lag-g", lambda: lag_audit(d.assign(g=d["g"] * 1.01), b, G))
    # B3 reproduction and right quantity, with D645's own b3_trade on synthetic bars
    R = load_v2().R
    m = np.arange(hm("09:30"), hm("12:00"))
    c = np.where(m < hm("10:00"), 100.0, 100.0 + 0.02 * (m - hm("10:00")) + 0.3)
    c = c + 0.01 * np.sin(m)  # distinct closes, so a one-minute entry slip changes the price
    bb = {"m": m, "o": c, "h": c + 0.05, "l": c - 0.05, "c": c}
    bars = {(ROOT, "2020-01-02"): bb}
    dd = pd.DataFrame({"hi_10:00": [100.2], "lo_10:00": [99.8]}, index=["2020-01-02"])

    def rows(shift: int) -> pd.DataFrame:
        D, eb, e = find_break(bb, (99.8, 100.2), hm("10:00"), hm("11:29"), entry_shift=shift)
        return pd.DataFrame({"D": [D], "eb": [eb], "entry": [e], "F": [follow(bb, eb, D, e)]}, index=["2020-01-02"])

    b3_audit(rows(1), dd, bars, R)
    must_raise("b3-entry-slip", lambda: b3_audit(rows(0), dd, bars, R))
    right_quantity(rows(1), bars)
    r10 = rows(1)
    r10["F"] = r10["D"] * np.log(c[np.flatnonzero(m <= r10["eb"].iloc[0] + 60)[-1]] / c[m == hm("10:00")][0]) * 1e4
    must_raise("right-quantity-from-10", lambda: right_quantity(r10, bars))
    print(f"selftest: {len(fired)} audits fire on broken inputs ({', '.join(fired)}); the clean cases pass")
    return 0


# ============================================================================================ build
def build(data_root: Path, dry: bool) -> dict[str, Any]:
    t_start = time.time()
    V = load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(data_root, dry)
    tab = R.session_table(b, use, roots=(ROOT,))[ROOT]
    bars = R.bar_arrays(b)
    d = session_frame(b, tab, Gd[ROOT])
    sign_audit()
    null_exactness()
    lag_audit(d, b, Gd[ROOT])
    morning = rows_for(d, bars, MORNING, R)
    midday = rows_for(d, bars, MIDDAY, R)
    b3_audit(morning, d, bars, R)
    right_quantity(morning, bars)
    cal = list(d.index)
    jobs = [(f"morning_{k}", morning, cal, d["g"], k) for k in SHOCKS] + [(f"midday_{k}", midday, cal, d["g"], k) for k in SHOCKS]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        res = {j[0]: v for j, v in zip(jobs, ex.map(analyse, jobs))}
    wall = time.time() - t0
    p = {k: res[f"morning_{k}"]["interaction"]["p3_one_sided"] for k in SHOCKS}
    order = sorted(p, key=p.get)
    holm, run_max = {}, 0.0
    for i, k in enumerate(order):
        run_max = max(run_max, min(1.0, (len(order) - i) * p[k]))
        holm[k] = run_max
    verdict = {}
    for k in SHOCKS:
        m, pl = res[f"morning_{k}"], res[f"midday_{k}"]
        checks = {"b3_positive_holm": bool(m["interaction"]["b3"] > 0 and holm[k] < 0.05),
                  "rotation_rank_ge_095": bool(m["rotation"]["rank"] >= 0.95),
                  "placebo_abs_t_below_2": bool(abs(pl["interaction"]["t3"]) < 2),
                  "short_slope_steeper": bool(m["controls"]["piecewise"]["diff"] > 0)}
        verdict[k] = {"holm_p": holm[k], "checks": checks,
                      "verdict": "SUPPORTED" if all(checks.values()) else "NOT SUPPORTED",
                      "powered_null_own_claim": m["controls"]["own_claim"]["powered_null_below_half"],
                      "b3_vs_mde": [m["interaction"]["b3"], m["interaction"]["mde80_b3"]],
                      "paper_implied_b3": m["controls"]["paper_implied_b3"]}
    cm = res["morning_s_gap"]
    predictions = {
        "1_gap_not_supported": verdict["s_gap"]["verdict"] == "NOT SUPPORTED",
        "2_stop_not_supported": verdict["s_stop"]["verdict"] == "NOT SUPPORTED",
        "3_gap_own_claim_powered_null": cm["controls"]["own_claim"]["powered_null_below_half"],
        "4_piecewise_no_difference": abs(cm["controls"]["piecewise"]["diff_t"]) < 2,
        "5_placebo_inside_noise": abs(res["midday_s_gap"]["interaction"]["t3"]) < 2,
        "6_b3_in_tails": (abs(cm["tails"]["ex_covid"] - cm["interaction"]["b3"]) > 0.5 * abs(cm["interaction"]["b3"]))}
    doc = {"spec": "D662 (c9a40a5)", "dry_run": dry,
           "inputs": {"sessions_in_frame": len(d), "first": d.index[0], "last": d.index[-1],
                      "short_gamma_share": float((d["g"] > 0).mean()), "g_sd": float(d["g"].std())},
           "sessions": {"morning_breaks": int(len(morning)), "midday_breaks": int(len(midday))},
           "shocks": {k: res[f"morning_{k}"] for k in SHOCKS}, "placebo": {k: res[f"midday_{k}"] for k in SHOCKS},
           "verdict": verdict, "predictions": predictions,
           "audits": ["lag (second path on bars ending 09:59)", "sign in money", "B3 reproduced", "right quantity",
                      "null exactness (batched vs lstsq)", "batched OLS vs statsmodels per fit"],
           "speed": {"jobs": len(jobs), "fanout_wall_s": round(wall, 2)},
           "runtime_min": round((time.time() - t_start) / 60, 2)}
    missing = [k for k in DECLARED if k not in doc]
    if missing:
        raise D662Error(f"declared outputs missing: {missing}")
    if not dry and doc["inputs"]["last"] >= "2025-03-01":
        raise D662Error("a vault session reached the frame")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run and OUT.exists():
        raise SystemExit("D662 Stage 0 runs once: its output exists")
    doc = build(a.data_root, dry=a.dry_run)
    text = json.dumps(doc, indent=1, default=float) + "\n"
    if a.run:
        OUT.write_text(text, encoding="utf-8", newline="\n")
    v = doc["verdict"]
    print(f"{'DRY RUN (synthetic): ' if a.dry_run else ''}breaks {doc['sessions']}; "
          f"gap {v['s_gap']['verdict']} (b3 {doc['shocks']['s_gap']['interaction']['b3']:+.4f}, "
          f"t {doc['shocks']['s_gap']['interaction']['t3']:+.2f}, rank {doc['shocks']['s_gap']['rotation']['rank']:.3f}); "
          f"stop {v['s_stop']['verdict']}; {doc['runtime_min']} min{'' if a.run else '; nothing written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
