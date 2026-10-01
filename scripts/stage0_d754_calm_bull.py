"""D754 Stage 0: the calm bull. Spec: docs/decisions/D754-STAGE-0-PRE-REG-calm-bull-abstention-and-charm-drift.md.

    uv run --no-sync python scripts/stage0_d754_calm_bull.py --selftest
    uv run --no-sync python scripts/stage0_d754_calm_bull.py --run

(A) The NQ vault lines' in-sample books (D737's twin, NQ F2, C1) on calm sessions (NQ rv20 in its walk-forward lowest
third): the level, and the within-year contrast against a within-year permutation null (is it the regime or 2017?).
(B) Long one MES 14:00 -> 16:00 on Fridays with SPX GEX long and above its 250-row median and the S&P above its
200-day average; day, clock and state controls; the 0DTE-era split. Everything is restricted before 2024-01-01.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import forward_f2_c1_ledgers as FW  # noqa: E402  (text-restricted fixture readers)

MAIN_DATA = FW.MAIN_DATA
SPEC = REPO / "docs" / "decisions" / "D754-STAGE-0-PRE-REG-calm-bull-abstention-and-charm-drift.md"
OUT = REPO / "data" / "stage0_d754_calm_bull.json"
SEAL, HI = "2024-01-01", "2023-12-29"
N_PERM, SEED, WF_N = 20000, 754, 250
ZERO_DTE = "2022-05-11"
MES_USD, MES_COST = 5.0, 4.418145176055553
LINES = ("d737_twin", "nq_f2", "c1")


class D754Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D754Error(msg)


# ================================================================================ inputs
def daily_close(root: str) -> pd.Series:
    b = FW.rth_history(FW.rth_raw(root, SEAL))
    need((b["day"] < SEAL).all(), f"seal: a {root} bar on or after 2024-01-01")
    return b.groupby("day")["close"].last()


def rv20(close: pd.Series, canary: bool = False) -> pd.Series:
    """The std of the 20 PRIOR daily log returns (canary: including the session's own)."""
    r = np.log(close).diff()
    s = r.rolling(20).std()
    return s if canary else s.shift(1)


def wf_pct(x: pd.Series, n: int = WF_N) -> pd.Series:
    """Each value's percentile among the previous n finite values (strictly earlier); NaN until n exist."""
    v = x.to_numpy(float)
    out = np.full(len(v), np.nan)
    hist: list[float] = []
    for i, a in enumerate(v):
        if not np.isfinite(a):
            continue
        if len(hist) >= n:
            h = np.array(hist[-n:])
            out[i] = float((h < a).mean())
        hist.append(a)
    return pd.Series(out, index=x.index)


def dix() -> pd.DataFrame:
    """DIX.csv restricted as TEXT to rows dated before 2024-01-01 (the date is the first field)."""
    rows = (MAIN_DATA / "raw" / "squeezemetrics" / "DIX.csv").read_text(encoding="utf-8").splitlines()
    keep = [rows[0]] + [ln for ln in rows[1:] if ln[:10] < SEAL]
    raw = ("\n".join(keep) + "\n").encode("utf-8")
    d = pd.read_csv(io.BytesIO(raw), encoding="utf-8", dtype={"date": str}).set_index("date").sort_index()
    need((d.index < SEAL).all(), "seal: a DIX row on or after 2024-01-01")
    return d


def prior_value(s: pd.Series, days: np.ndarray) -> np.ndarray:
    """The row strictly before each day (D663's gex_prior convention)."""
    idx = s.index.to_numpy()
    pos = np.searchsorted(idx, days, side="left") - 1
    v = s.to_numpy(float)
    return np.where(pos >= 0, v[np.clip(pos, 0, None)], np.nan)


def prior_value_loop(s: pd.Series, day: str) -> float:
    prev = s[s.index < day]
    return float(prev.iloc[-1]) if len(prev) else float("nan")


def lines() -> pd.DataFrame:
    import stage0_d747_night_break_fade as S747
    d = S747.other_lines()
    return pd.DataFrame({k: v.groupby(level=0).sum() for k, v in d.items()})[list(LINES)]


# ================================================================================ statistics
def tstat(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def welch(a: np.ndarray, b: np.ndarray) -> float:
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else float("nan")


def within_year_delta(y: np.ndarray, lab: np.ndarray, yr: np.ndarray) -> tuple[float, dict[str, float]]:
    """Pooled (session-weighted) mean over years of mean(rest) - mean(calm), and the per-year contrasts."""
    per, num, den = {}, 0.0, 0
    for k in np.unique(yr):
        m = yr == k
        c, r = y[m & lab], y[m & ~lab]
        if len(c) == 0 or len(r) == 0:
            continue
        d = float(r.mean() - c.mean())
        per[str(k)] = d
        num += d * m.sum()
        den += int(m.sum())
    return num / den, per


def perm_null(y: np.ndarray, lab: np.ndarray, yr: np.ndarray, n: int, seed: int, pooled: bool = False) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.empty(n)
    groups = [np.flatnonzero(yr == k) for k in np.unique(yr)]
    for i in range(n):
        L = lab.copy()
        if pooled:
            L = rng.permutation(L)
        else:
            for g in groups:
                L[g] = rng.permutation(lab[g])
        out[i] = within_year_delta(y, L, yr)[0]
    return out


def book(g: np.ndarray, days: list[str], cost: float, span_years: float) -> dict[str, Any]:
    n = g - cost
    k = len(n)
    if k < 3:
        return {"trades": k}
    tpy = k / span_years
    srt = np.sort(n)
    cut = max(1, int(round(0.01 * k)))
    dn = math.sqrt(float(np.mean(np.minimum(n, 0) ** 2)))
    eq = np.cumsum(n)
    yrs = pd.Series(n, index=[d[:4] for d in days]).groupby(level=0).sum()
    s = pd.Series(n)
    w, l_ = n[n > 0], n[n <= 0]
    return {"trades": k, "mean_gross": float(g.mean()), "t_gross": tstat(g), "mean_net": float(n.mean()),
            "median_net": float(np.median(n)), "sharpe_net": float(n.mean() / n.std(ddof=1) * math.sqrt(tpy)),
            "sortino_net": float(n.mean() / dn * math.sqrt(tpy)) if dn > 0 else None,
            "sharpe_gross": float(g.mean() / g.std(ddof=1) * math.sqrt(tpy)),
            "max_dd": float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max()), "total_net": float(n.sum()),
            "win_rate": float((n > 0).mean()), "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) and l_.mean() < 0 else None,
            "skew": float(s.skew()), "kurtosis": float(s.kurt()), "mean_abs_gross": float(np.abs(g).mean()),
            "mean_abs_vs_2c": float(np.abs(g).mean() / (2 * cost)), "breakeven_cost": float(g.mean()),
            "mean_ex_top1pct": float(srt[:-cut].mean()), "mean_ex_bottom1pct": float(srt[cut:].mean()),
            "mean_trimmed1pct": float(srt[cut:-cut].mean()) if k > 2 * cut else None,
            "years": {y: round(float(v), 2) for y, v in yrs.items()}, "positive_years": f"{int((yrs > 0).sum())} of {len(yrs)}",
            "largest_year_share": float(yrs.max() / n.sum()) if n.sum() > 0 else None}


# ================================================================================ Part A
def part_a() -> dict[str, Any]:
    nq = daily_close("NQ")
    rv = rv20(nq)
    pct = wf_pct(rv)
    pct_canary = wf_pct(rv20(nq, canary=True))
    L = lines()
    L.index = L.index.astype(str)
    sessions = nq.index[(nq.index >= L.index.min()) & (nq.index <= HI)]
    B = L.reindex(sessions).fillna(0.0)
    B["book"] = B[list(LINES)].sum(axis=1)
    scored = sessions[np.isfinite(pct.reindex(sessions).to_numpy())]
    need((pct.reindex(scored) != pct_canary.reindex(scored)).any(), "lag: the own-return canary changed no percentile")
    calm = (pct.reindex(scored) < 1 / 3).to_numpy()
    yr = np.array([s[:4] for s in scored])
    rvs = rv.reindex(scored).to_numpy(float)
    wy = np.zeros(len(scored), dtype=bool)
    for k in np.unique(yr):
        m = np.flatnonzero(yr == k)
        cut = np.quantile(rvs[m], 1 / 3)
        wy[m] = rvs[m] < cut
    need((wy != calm).any(), "right quantity: the within-year label equals the walk-forward label")
    res: dict[str, Any] = {"scored_sessions": int(len(scored)), "first_scored": str(scored[0]), "calm_share_wf": float(calm.mean()),
                           "wy_calm_share": float(wy.mean()), "series": {}}
    for col in list(LINES) + ["book"]:
        y = B[col].reindex(scored).to_numpy(float)
        d_obs, per = within_year_delta(y, wy, yr)
        nul = perm_null(y, wy, yr, N_PERM, SEED)
        r = {"A1_calm_mean_net_per_session": float(y[calm].mean()), "A1_rest_mean_net_per_session": float(y[~calm].mean()),
             "A1_calm_total": float(y[calm].sum()), "A1_rest_total": float(y[~calm].sum()),
             "A1_calm_trades": int((y[calm] != 0).sum()), "A1_calm_mean_per_trade": float(y[calm][y[calm] != 0].mean()) if (y[calm] != 0).any() else None,
             "A2_delta": d_obs, "A2_null_p50": float(np.median(nul)), "A2_null_p95": float(np.percentile(nul, 95)),
             "A2_p": float((nul >= d_obs).mean()), "A2_years_positive": f"{sum(v > 0 for v in per.values())} of {len(per)}",
             "A2_per_year": {k: round(v, 2) for k, v in per.items()}}
        if col == "book":
            pooled = perm_null(y, wy, yr, 2000, SEED + 1, pooled=True)
            r["canary_pooled_null_p50_p95"] = [float(np.median(pooled)), float(np.percentile(pooled, 95))]
            need(not np.isclose(np.percentile(pooled, 95), r["A2_null_p95"]), "the pooled-years canary gave the same null")
        res["series"][col] = r
    b = res["series"]["book"]
    a1 = b["A1_calm_mean_net_per_session"] <= 0
    a2 = b["A2_delta"] > 0 and b["A2_p"] <= 0.05 and int(b["A2_years_positive"].split(" of ")[0]) >= 5
    res["reading"] = "ABSTAIN SUPPORTED" if (a1 and a2) else ("YEAR ARTEFACT" if a1 else "NOT SUPPORTED")
    return res


# ================================================================================ Part B
def es_minutes() -> pd.DataFrame:
    b = FW.rth_history(FW.rth_raw("ES", SEAL))
    b = b[(b["day"] >= "2016-01-04") & (b["day"] <= HI)]
    cl = b.pivot(index="day", columns="hhmm", values="close").sort_index()
    return cl.ffill(axis=1)


def price_at(cl: pd.DataFrame, hhmm_bar: str) -> pd.Series:
    """The close of the bar starting at `hhmm_bar` (carried forward within the day)."""
    return cl[hhmm_bar]


def part_b() -> dict[str, Any]:
    cl = es_minutes()
    days = cl.index.to_numpy(str)
    p12, p14, p16 = price_at(cl, "11:59"), price_at(cl, "13:59"), price_at(cl, "15:59")
    D = dix()
    gex = D["gex"].astype(float)
    spx = D["price"].astype(float)
    g_prior = prior_value(gex, days)
    g_med = prior_value(gex.rolling(250, min_periods=250).median(), days)
    s_prior = prior_value(spx, days)
    s_sma = prior_value(spx.rolling(200, min_periods=200).mean(), days)
    for d in days[::97]:
        i = int(np.searchsorted(days, d))
        need(math.isclose(prior_value_loop(gex, d), g_prior[i], rel_tol=0, abs_tol=1e-6) or not np.isfinite(g_prior[i]),
             f"lag: GEX at {d} is not the row strictly before")
        need(math.isclose(prior_value_loop(spx, d), s_prior[i], rel_tol=0, abs_tol=1e-9) or not np.isfinite(s_prior[i]),
             f"lag: SPX at {d} is not the row strictly before")
    with np.errstate(invalid="ignore"):
        state = (g_prior >= 0) & (g_prior >= g_med) & (s_prior > s_sma)
    wd = pd.to_datetime(pd.Series(days)).dt.weekday.to_numpy()
    fri, mt = wd == 4, wd <= 3
    need(not (fri & mt).any(), "right quantity: a Friday is also Mon-Thu")
    pm = (p16 - p14).to_numpy(float) * MES_USD
    am = (p14 - p12).to_numpy(float) * MES_USD
    ok = np.isfinite(pm) & np.isfinite(am)
    sel = ok & state & fri
    g = pm[sel]
    span = (pd.Timestamp(HI) - pd.Timestamp("2016-01-04")).days / 365.25
    dsel = days[sel].tolist()
    third = np.array([15 <= int(d[8:]) <= 21 for d in days])
    zero = days >= ZERO_DTE
    mt_g = pm[ok & state & mt]
    res: dict[str, Any] = {
        "state_share_of_sessions": float(np.nanmean(state[ok])), "fridays_in_state": int(sel.sum()),
        "B": book(g, dsel, MES_COST, span),
        "B_C1_mon_thu": {"n": int(len(mt_g)), "mean_gross": float(mt_g.mean()), "t": tstat(mt_g), "welch_t_fri_minus": welch(g, mt_g)},
        "B_C2_friday_12_14": {"n": int(sel.sum()), "mean_gross": float(am[sel].mean()), "t": tstat(am[sel])},
        "B_C3_friday_out_of_state": {"n": int((ok & ~state & fri).sum()), "mean_gross": float(pm[ok & ~state & fri].mean()),
                                     "t": tstat(pm[ok & ~state & fri])},
        "all_days_in_state_14_16": {"n": int((ok & state).sum()), "mean_gross": float(pm[ok & state].mean())},
        "monthly_expiry_fridays": {"n": int((sel & third).sum()), "mean_gross": float(pm[sel & third].mean()) if (sel & third).any() else None},
        "other_fridays": {"n": int((sel & ~third).sum()), "mean_gross": float(pm[sel & ~third].mean()) if (sel & ~third).any() else None},
        "eras": {"pre_0dte": {"n": int((sel & ~zero).sum()), "mean_gross": float(pm[sel & ~zero].mean()), "t": tstat(pm[sel & ~zero])},
                 "zero_dte": {"n": int((sel & zero).sum()), "mean_gross": float(pm[sel & zero].mean()) if (sel & zero).any() else None,
                              "t": tstat(pm[sel & zero]) if (sel & zero).sum() > 2 else None}},
        "O_mean_abs_move": float(np.abs(g).mean()),
    }
    e = res["B"]
    drift = (e["mean_gross"] > 0 and e["t_gross"] >= 2 and res["B_C1_mon_thu"]["welch_t_fri_minus"] >= 1.64
             and e["mean_gross"] > res["B_C1_mon_thu"]["mean_gross"] and e["mean_gross"] > res["B_C2_friday_12_14"]["mean_gross"])
    go = (drift and e["mean_net"] > 0 and int(e["positive_years"].split(" of ")[0]) >= 5 and e["largest_year_share"] is not None
          and e["largest_year_share"] < 0.5 and (res["eras"]["zero_dte"]["mean_gross"] or -1) > 0)
    no_room = res["O_mean_abs_move"] < 2 * MES_COST
    res["readings"] = {"NO_ROOM": bool(no_room), "DRIFT_PRESENT": bool(drift), "GO": bool(go),
                       "reading": "NO ROOM" if no_room else ("DRIFT PRESENT" if drift else "NOTHING")}
    L = lines()
    L.index = L.index.astype(str)
    trade = pd.Series(g - MES_COST, index=dsel)
    alld = sorted(set(L.index) | set(days))
    res["component_corr"] = {c: float(np.corrcoef(trade.reindex(alld, fill_value=0.0), L[c].reindex(alld).fillna(0.0))[0, 1]) for c in LINES}
    return res


# ================================================================================ run / self-test
def sign_audit() -> None:
    cl = pd.DataFrame({"13:59": [5000.0], "15:59": [5004.0]}, index=["2020-01-03"])
    mv = float((price_at(cl, "15:59") - price_at(cl, "13:59")).iloc[0]) * MES_USD
    need(mv == 20.0 and mv - MES_COST > 0, f"sign: a 4-point rise did not pay the long MES ({mv})")


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D754 is run-once")
    t0 = time.time()
    sign_audit()
    res = {"spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "A": part_a(), "B": part_b()}
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    a, b = res["A"], res["B"]
    print("A:", a["reading"], {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk.startswith(("A1_calm_mean", "A1_rest_mean", "A2_delta", "A2_null_p95", "A2_p", "A2_years"))}
                               for k, v in a["series"].items()})
    print("B:", b["readings"], {k: b["B"][k] for k in ("trades", "mean_gross", "t_gross", "mean_net", "positive_years")},
          "MonThu", b["B_C1_mon_thu"], "Fri12-14", b["B_C2_friday_12_14"], "eras", b["eras"])
    return 0


def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D754Error as e:
        fails.append(str(e))
    x = pd.Series(np.arange(300, dtype=float))
    p = wf_pct(x)
    if np.isfinite(p.iloc[:WF_N]).any() or not (p.iloc[WF_N:] == 1.0).all():
        fails.append("wf_pct: a rising series must sit at 1.0 against the strictly earlier window")
    y = np.r_[np.zeros(6), np.ones(6)]
    lab = np.r_[[True] * 3, [False] * 3, [True] * 3, [False] * 3]
    yr = np.array(["a"] * 6 + ["b"] * 6)
    d, per = within_year_delta(y, lab, yr)
    if d != 0.0 or per != {"a": 0.0, "b": 0.0}:
        fails.append(f"within_year_delta: a year-level difference must not leak into the contrast ({d}, {per})")
    y2 = np.r_[np.r_[np.zeros(3), np.ones(3)], np.r_[np.zeros(3), np.ones(3)]]
    if within_year_delta(y2, lab, yr)[0] != 1.0:
        fails.append("within_year_delta: a within-year difference of 1 must read 1")
    s = pd.Series([1.0, 2.0, 3.0], index=["2020-01-01", "2020-01-02", "2020-01-03"])
    if prior_value(s, np.array(["2020-01-03"]))[0] != 2.0 or prior_value_loop(s, "2020-01-03") != 2.0:
        fails.append("prior_value: not the row strictly before")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money; the walk-forward percentile uses strictly earlier values; the "
          "within-year contrast ignores year-level differences and reads a within-year one; prior rows are strictly before")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
