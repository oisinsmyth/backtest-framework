"""D775 Stage 0: fade the 08:30 CPI and jobs-report impulse on MNQ.
Spec: docs/decisions/D775-STAGE-0-PRE-REG-fade-the-cpi-and-jobs-report-impulse-on-mnq.md.

    python scripts/stage0_d775_cpi_nfp_fade.py --selftest
    python scripts/stage0_d775_cpi_nfp_fade.py --run

Bars are one-minute, stamped at the bar's START (fut_opening_globex_1m*, the session's front, D462): "the close of
bar hh:mm" is the last price before hh:mm + 1 minute. Release days are CPI and EMPSIT at 08:30 ET in
data/calendar/events.csv (D585). In-sample sessions 2016-01-01 .. 2023-12-31 only (asserted).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MAIN = Path("C:/Users/O/Desktop/Projects/Backtest Framework")
FIX = MAIN / "data" / "fixtures"
EVENTS = REPO / "data" / "calendar" / "events.csv"
LINES = REPO / "temp" / "d755_other_lines.csv"
SPEC = REPO / "docs" / "decisions" / "D775-STAGE-0-PRE-REG-fade-the-cpi-and-jobs-report-impulse-on-mnq.md"
OUT = REPO / "data" / "stage0_d775_cpi_nfp_fade.json"
START, SEAL = "2016-01-01", "2024-01-01"
# root: (file, $ per point at one micro, round trip $)
ROOTS = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0, 4.07), "ES": ("fut_opening_globex_1m.csv.gz", 5.0, 4.42),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5, 3.80),
         "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0, 3.76)}
PRIMARY = "NQ"
PRE, ENTRY, EXIT, OPEN_BAR = "08:29", "08:34", "11:00", "09:29"
K_GRID, EXIT_GRID = [1, 3, 5, 10, 15, 30], ["10:30", "11:00", "11:30", "12:00"]
VOL_N, VOL_MIN = 60, 40
N_DRAWS, N_BOOT, WORKERS = 10_000, 200, 4
SEED = 775


def hm(k: int) -> str:
    m = 29 + k
    return f"{8 + m // 60:02d}:{m % 60:02d}"


BARS = sorted({PRE, ENTRY, EXIT, OPEN_BAR, *[hm(k) for k in K_GRID], *EXIT_GRID})


class D775Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D775Error(msg)


# ================================================================================ data
def _load_file(args: tuple[str, tuple[str, ...]]) -> pd.DataFrame:
    fn, roots = args
    parts = []
    for ch in pd.read_csv(FIX / fn, encoding="utf-8", chunksize=2_000_000,
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[ch["root"].isin(roots) & (ch["session"] >= START) & (ch["session"] < SEAL) & ch["hhmm"].isin(BARS)]
        parts.append(ch[ch["et"].str[:10] == ch["session"]])     # same-calendar-day bars only (morning clock)
    d = pd.concat(parts, ignore_index=True)
    need(bool((d["session"] < SEAL).all()), "seal: a session on or after 2024-01-01")
    return d


def load_bars() -> pd.DataFrame:
    jobs: dict[str, list[str]] = {}
    for r, (fn, _, _) in ROOTS.items():
        jobs.setdefault(fn, []).append(r)
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        frames = list(ex.map(_load_file, [(fn, tuple(rs)) for fn, rs in jobs.items()]))
    return pd.concat(frames, ignore_index=True)


def release_days() -> dict[str, str]:
    e = pd.read_csv(EVENTS, encoding="utf-8")
    e = e[e["event"].isin(["CPI", "EMPSIT"]) & (e["datetime_et"].str[11:16] == "08:30")]
    e = e[(e["datetime_et"] >= START) & (e["datetime_et"] < SEAL)]
    return dict(zip(e["datetime_et"].str[:10], e["event"]))


# ================================================================================ sessions
def sessions(b: pd.DataFrame, root: str) -> pd.DataFrame:
    """One row per weekday session: the bar closes needed, the contract count, the fade and its legs."""
    _, mult, _ = ROOTS[root]
    g = b[b["root"] == root]
    px = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    nk = g.groupby("session")["contract"].nunique()
    S = pd.DataFrame(index=px.index)
    for c in BARS:
        S[c] = px[c] if c in px.columns else np.nan
    S["nk"] = nk.reindex(S.index)
    S = S[pd.to_datetime(S.index).weekday < 5].sort_index()
    S["x"] = S[ENTRY] - S[PRE]
    S["side"] = -np.sign(S["x"])
    S["move"] = (S[EXIT] - S[ENTRY]) * mult                      # the unsigned same-clock move, for the vol scale
    S["gross"] = S["side"] * S["move"]
    S["sec"] = S["side"] * (S[EXIT] - S[OPEN_BAR]) * mult        # the declared secondary (09:30 entry)
    S["pre_open"] = S["side"] * (S[OPEN_BAR] - S[ENTRY]) * mult
    S["valid_move"] = S[[ENTRY, EXIT]].notna().all(axis=1) & (S["nk"] == 1)
    mv = S["move"].where(S["valid_move"])
    S["sigma"] = mv.shift(1).rolling(VOL_N, min_periods=VOL_MIN).std()
    S["va"] = S["gross"] / S["sigma"]
    S["ok"] = S["valid_move"] & S[PRE].notna() & (S["x"] != 0)
    S["year"] = S.index.str[:4]
    S["wd"] = pd.to_datetime(S.index).weekday
    return S


def classify(S: pd.DataFrame, rel: dict[str, str]) -> tuple[pd.DataFrame, dict[str, int]]:
    days = sorted(rel)
    counts = {"read": len(days), "used": 0, "no_session": 0, "two_contracts": 0, "missing_bar": 0, "zero_impulse": 0}
    for d in days:
        if d not in S.index:
            counts["no_session"] += 1
            continue
        r = S.loc[d]
        if r["nk"] != 1:
            counts["two_contracts"] += 1
        elif pd.isna(r[PRE]) or pd.isna(r[ENTRY]) or pd.isna(r[EXIT]):
            counts["missing_bar"] += 1
        elif r["x"] == 0:
            counts["zero_impulse"] += 1
        else:
            counts["used"] += 1
    need(counts["read"] == sum(v for k, v in counts.items() if k != "read"), "right quantity: read != used + exclusions")
    U = S[S["ok"]].copy()
    U["event"] = U.index.map(lambda d: rel.get(d, ""))
    U["is_rel"] = U["event"] != ""
    need(int(U["is_rel"].sum()) == counts["used"], "right quantity: the used count disagrees with the panel")
    return U, counts


# ================================================================================ nulls
def _rot_chunk(args: tuple[np.ndarray, np.ndarray, list[int]]) -> np.ndarray:
    f, pos, ks = args
    n = len(f)
    return np.array([f[(pos + k) % n].mean() for k in ks])


def rotation(f: np.ndarray, pos: np.ndarray, workers: int = 1) -> np.ndarray:
    """Means of f over the release labels shifted by every offset k = 0 .. n-1; row 0 is the observed."""
    ks = list(range(len(f)))
    if workers == 1:
        return _rot_chunk((f, pos, ks))
    parts = [ks[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        outs = list(ex.map(_rot_chunk, [(f, pos, p) for p in parts]))
    res = np.empty(len(ks))
    for i, o in enumerate(outs):
        res[i::workers] = o
    return res


def null_summary(obs: float, dist: np.ndarray, boot: bool) -> dict[str, Any]:
    out = {"p50": round(float(np.percentile(dist, 50)), 2), "p95": round(float(np.percentile(dist, 95)), 2),
           "rank": round(float((dist < obs).mean() + 0.5 * (dist == obs).mean()), 4), "n": int(len(dist))}
    if boot:
        rng = np.random.default_rng(SEED + 1)
        bs = [np.percentile(rng.choice(dist, len(dist)), 95) for _ in range(N_BOOT)]
        out["p95_se"] = round(float(np.std(bs, ddof=1)), 3)
    return out


def matched_draws(U: pd.DataFrame, key: list[str], col: str = "gross") -> np.ndarray:
    """Draw, for every release day, a non-release day in the same cell (key) without replacement within a draw."""
    rng = np.random.default_rng(SEED)
    rel, pool = U[U["is_rel"]], U[~U["is_rel"]]
    groups = {k: g[col].to_numpy() for k, g in pool.groupby(key)}
    need_n = rel.groupby(key).size()
    out = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        tot, n = 0.0, 0
        for k, c in need_n.items():
            arr = groups.get(k)
            if arr is None or len(arr) == 0:
                continue
            take = rng.choice(arr, size=min(c, len(arr)), replace=False)
            tot += take.sum()
            n += len(take)
        out[i] = tot / n
    return out


# ================================================================================ statistics
def tstat(x: pd.Series) -> float:
    return float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def trade_stats(g: pd.Series, cost: float) -> dict[str, Any]:
    net = g - cost
    k = max(1, int(round(0.01 * len(g))))
    s = net.sort_values()
    w, lo = net[net > 0], net[net < 0]
    return {"n": int(len(g)), "mean_gross": round(g.mean(), 2), "mean_net": round(net.mean(), 2),
            "median_gross": round(g.median(), 2), "median_net": round(net.median(), 2),
            "t_gross": round(tstat(g), 2), "t_net": round(tstat(net), 2), "win_gross": round(float((g > 0).mean()), 3),
            "payoff_net": round(w.mean() / -lo.mean(), 2) if len(lo) and len(w) else None,
            "skew": round(float(net.skew()), 2), "kurtosis": round(float(net.kurt()), 2),
            "net_ex_top1pct": round(s.iloc[:-k].mean(), 2), "net_ex_bottom1pct": round(s.iloc[k:].mean(), 2),
            "net_trimmed": round(s.iloc[k:-k].mean(), 2), "mean_abs_gross": round(g.abs().mean(), 2),
            "breakeven_cost": round(g.mean(), 2)}


def book(U: pd.DataFrame, cost: float) -> dict[str, Any]:
    """Daily series over every valid session, zero on non-release days."""
    s = pd.Series(0.0, index=U.index)
    rel = U["is_rel"]
    s[rel] = U.loc[rel, "gross"] - cost
    sg = pd.Series(0.0, index=U.index)
    sg[rel] = U.loc[rel, "gross"]
    down = s[s < 0]
    eq = s.cumsum()
    return {"sharpe_net": round(s.mean() / s.std() * math.sqrt(252), 2),
            "sortino_net": round(s.mean() / math.sqrt((down ** 2).sum() / len(s)) * math.sqrt(252), 2),
            "sharpe_gross": round(sg.mean() / sg.std() * math.sqrt(252), 2),
            "max_drawdown": round(float((eq.cummax() - eq).max()), 0), "total_net": round(float(s.sum()), 0),
            "exposure_share_of_days": round(float(rel.mean()), 4), "daily_net": s}


def by(U: pd.DataFrame, key: pd.Series, cost: float) -> dict[str, Any]:
    out = {}
    for k, g in U.groupby(key):
        out[str(k)] = {"n": int(len(g)), "mean_gross": round(g["gross"].mean(), 2),
                       "mean_net": round(g["gross"].mean() - cost, 2), "win": round(float((g["gross"] > 0).mean()), 3),
                       "va_mean": round(g["va"].mean(), 3), "t": round(tstat(g["gross"]), 2)}
    return out


# ================================================================================ audits
def sign_audit(mirror: float = 1.0) -> None:
    """In money: an up impulse (x > 0) followed by a fall pays the fade."""
    p0829, p0834, p1100 = 100.0, 101.0, 100.5
    side = -np.sign(p0834 - p0829) * mirror
    need(side * (p1100 - p0834) * 2.0 > 0, "sign audit: a faded up-impulse followed by a fall must pay")


def audit_sessions(b: pd.DataFrame, root: str, U: pd.DataFrame, n: int = 40) -> None:
    """Second implementation: explicit loops over the raw bar rows (never the pivot) for sampled release days."""
    _, mult, _ = ROOTS[root]
    rel = U[U["is_rel"]]
    pick = rel.index[np.random.default_rng(SEED).choice(len(rel), size=min(n, len(rel)), replace=False)]
    raw = b[b["root"] == root]
    for d in pick:
        rows = raw[raw["session"] == d]
        p = {}
        for r in rows.itertuples(index=False):
            if r.hhmm in (PRE, ENTRY, EXIT):
                p[r.hhmm] = float(r.close)
        x = p[ENTRY] - p[PRE]
        side = -1.0 if x > 0 else 1.0
        g = side * (p[EXIT] - p[ENTRY]) * mult
        need(abs(g - float(U.at[d, "gross"])) < 1e-9, f"lag audit: the fade differs on {d} ({g} vs {U.at[d, 'gross']})")


# ================================================================================ the study
def study(b: pd.DataFrame, root: str, rel: dict[str, str], primary: bool) -> dict[str, Any]:
    _, mult, cost = ROOTS[root]
    S = sessions(b, root)
    U, counts = classify(S, rel)
    audit_sessions(b, root, U)
    R = U[U["is_rel"]]
    f = U["gross"].to_numpy()
    pos = np.flatnonzero(U["is_rel"].to_numpy())
    rot = rotation(f, pos, workers=WORKERS)
    need(abs(rot[0] - R["gross"].mean()) < 1e-9, "right quantity: rotation offset 0 must equal the observed")
    obs = float(R["gross"].mean())
    plc = U.loc[~U["is_rel"], "gross"]
    need(abs(plc.mean() - obs) > 1e-9, "right quantity: the placebo equals the treatment")
    out: dict[str, Any] = {"counts": counts, "primary": trade_stats(R["gross"], cost),
                           "placebo_non_release": {"n": int(len(plc)), "mean_gross": round(plc.mean(), 2),
                                                   "t": round(tstat(plc), 2)},
                           "N_rotation": null_summary(obs, rot[1:], boot=False)}
    out["N_rotation"]["exact"] = True
    U["absx"] = U["x"].abs() * mult
    U["dec"] = U.groupby("year")["absx"].transform(lambda v: pd.qcut(v.rank(method="first"), 10, labels=False))
    R = U[U["is_rel"]]                                          # re-taken: it must carry absx and dec
    out["draws_year_weekday"] = null_summary(obs, matched_draws(U, ["year", "wd"]), boot=True)
    out["draws_year_impulse_decile"] = null_summary(obs, matched_draws(U, ["year", "dec"]), boot=True)
    yr = by(R, R["year"], cost)
    out["by_year"] = yr
    out["by_event"] = by(R, R["event"], cost)
    out["by_impulse_sign"] = by(R, np.where(R["x"] > 0, "up", "down"), cost)
    out["by_abs_impulse_tercile"] = by(R, pd.qcut(R["absx"].rank(method="first"), 3, labels=["low", "mid", "high"]), cost)
    out["by_half"] = by(R, np.where(R["year"] <= "2019", "2016-19", "2020-23"), cost)
    out["by_price_tercile"] = by(R, pd.qcut(R[ENTRY].rank(method="first"), 3, labels=["low", "mid", "high"]), cost)
    sec = R["sec"].dropna()
    out["secondary_0930_entry"] = trade_stats(sec, cost)
    out["split_signed"] = {"pre_open_0835_0930": {"mean": round(R["pre_open"].mean(), 2), "t": round(tstat(R["pre_open"].dropna()), 2)},
                           "post_open_0930_1101": {"mean": round(sec.mean(), 2), "t": round(tstat(sec), 2)},
                           "placebo_pre_open": round(U.loc[~U["is_rel"], "pre_open"].mean(), 2),
                           "placebo_post_open": round(U.loc[~U["is_rel"], "sec"].mean(), 2)}
    grid = {}
    for k in K_GRID:
        for ex in EXIT_GRID:
            e = S.loc[R.index]
            side = -np.sign(e[hm(k)] - e[PRE])
            gg = (side * (e[ex] - e[hm(k)]) * mult).dropna()
            gg = gg[side.loc[gg.index] != 0]
            grid[f"K{k}_{ex}"] = {"n": int(len(gg)), "mean": round(gg.mean(), 2), "t": round(tstat(gg), 2)}
    out["grid_K_exit"] = grid
    bk = book(U, cost)
    daily = bk.pop("daily_net")
    out["book"] = bk
    top = R.assign(net=R["gross"] - cost).nlargest(5, "net")
    bot = R.assign(net=R["gross"] - cost).nsmallest(5, "net")
    out["top5"] = [[d, round(v, 2)] for d, v in zip(top.index, top["net"])]
    out["bottom5"] = [[d, round(v, 2)] for d, v in zip(bot.index, bot["net"])]
    # ---- gates
    t = out["primary"]
    g1 = t["mean_gross"] > 0 and t["t_gross"] >= 2
    n_pass = obs > out["N_rotation"]["p95"]
    years = sorted(yr)
    y_i = sum(yr[y]["win"] >= 0.5 for y in years) >= 6
    va_pos = sum((yr[y]["va_mean"] or 0) > 0 for y in years)
    va_a, va_b = R.loc[R["year"] <= "2019", "va"].mean(), R.loc[R["year"] >= "2020", "va"].mean()
    y_ii = va_pos >= 6 and va_a >= 0.5 * va_b
    net_by_year = {y: yr[y]["mean_net"] * yr[y]["n"] for y in years}
    best2 = sorted(net_by_year, key=net_by_year.get)[-2:]
    net_ex_best2 = float((R.loc[~R["year"].isin(best2), "gross"] - cost).sum())
    ex22 = float(R.loc[R["year"] != "2022", "gross"].mean())
    g2 = t["mean_net"] > 0 and t["t_net"] >= 2 and net_ex_best2 > 0 and ex22 >= 2 * cost
    out["gates"] = {"G1": g1, "N": n_pass,
                    "Y": {"pass": bool(y_i or y_ii), "i_win_years_ge_50pct": int(sum(yr[y]["win"] >= 0.5 for y in years)),
                          "ii_va_positive_years": int(va_pos), "va_2016_19": round(float(va_a), 3),
                          "va_2020_23": round(float(va_b), 3), "i": bool(y_i), "ii": bool(y_ii)},
                    "G2": {"pass": bool(g2), "best_two_years": best2, "net_total_ex_best2": round(net_ex_best2, 0),
                           "mean_gross_ex2022": round(ex22, 2), "bar_2x_cost": round(2 * cost, 2)}}
    out["va_all"] = {"mean": round(R["va"].mean(), 3), "t": round(tstat(R["va"].dropna()), 2)}
    out["reading"] = ("NO EFFECT" if not g1 else "NOT ABOVE NULL" if not n_pass else
                      "CONCENTRATED" if not out["gates"]["Y"]["pass"] else "NO PRIZE" if not g2 else "SUPPORTED")
    if primary and LINES.exists():
        lines = pd.read_csv(LINES, index_col=0, encoding="utf-8")
        j = lines.join(daily.rename("d775"), how="inner")
        out["component_rho"] = {c: round(float(j["d775"].corr(j[c])), 3) for c in lines.columns}
        out["component_rho_days"] = int(len(j))
    return out


def run() -> int:
    t0 = time.time()
    sign_audit()
    try:
        sign_audit(-1.0)
    except D775Error:
        pass
    else:
        raise D775Error("the sign audit did not raise on a mirrored book")
    rel = release_days()
    b = load_bars()
    res: dict[str, Any] = {"spec": SPEC.name, "window": [START, "2023-12-31"], "bars": BARS}
    for root in ROOTS:
        res[root] = study(b, root, rel, primary=(root == PRIMARY))
        p = res[root]
        print(root, p["counts"], "| mean", p["primary"]["mean_gross"], "t", p["primary"]["t_gross"],
              "| N p95", p["N_rotation"]["p95"], "rank", p["N_rotation"]["rank"], "|", p["reading"], flush=True)
    res["reading"] = res[PRIMARY]["reading"]
    res["GO"] = res["reading"] == "SUPPORTED"
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print("READING", res["reading"], "GO", res["GO"], f"{res['wall_s']}s ->", OUT.relative_to(REPO))
    return 0


# ================================================================================ self-test
def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
    except D775Error:
        pass
    else:
        raise D775Error("the sign audit did not raise on a mirrored book")
    # a synthetic two-session panel: one release day fades, one non-release day
    rows = []
    for d, (p29, p34, p1100) in {"2019-03-08": (100.0, 101.0, 100.25), "2019-03-11": (100.0, 99.0, 98.0)}.items():
        for h in BARS:
            v = {PRE: p29, ENTRY: p34, EXIT: p1100}.get(h, p34)
            rows.append({"root": "NQ", "session": d, "et": f"{d} {h}", "hhmm": h, "contract": "NQH9", "close": v})
    b = pd.DataFrame(rows)
    S = sessions(b, "NQ")
    need(abs(S.at["2019-03-08", "gross"] - 1.5) < 1e-9, f"synthetic fade: {S.at['2019-03-08', 'gross']}")
    need(abs(S.at["2019-03-11", "gross"] + 2.0) < 1e-9, "synthetic fade on a down impulse that continues must lose")
    U, counts = classify(S, {"2019-03-08": "EMPSIT"})
    need(counts["used"] == 1 and int(U["is_rel"].sum()) == 1, "synthetic classify")
    audit_sessions(b, "NQ", U, n=1)
    U2 = U.copy()
    U2.loc["2019-03-08", "gross"] = -1.5
    try:
        audit_sessions(b, "NQ", U2, n=1)
    except D775Error:
        pass
    else:
        raise D775Error("the second implementation did not raise on a broken side")
    # a second contract in the window is excluded
    b2 = b.copy()
    b2.loc[(b2["session"] == "2019-03-08") & (b2["hhmm"] == EXIT), "contract"] = "NQM9"
    _, c2 = classify(sessions(b2, "NQ"), {"2019-03-08": "EMPSIT"})
    need(c2["two_contracts"] == 1 and c2["used"] == 0, "two contracts must be excluded")
    # chunk == whole for the rotation on processes, on a tie-heavy input
    rng = np.random.default_rng(1)
    f = rng.integers(-3, 4, size=2003).astype(float)
    pos = np.sort(rng.choice(2003, size=186, replace=False))
    whole, chunk = rotation(f, pos, workers=1), rotation(f, pos, workers=4)
    need(bool(np.array_equal(whole, chunk)), "chunk != whole")
    need(abs(whole[0] - f[pos].mean()) < 1e-12, "offset 0 must be the observed")
    # the whole study end to end on a synthetic random-walk panel (catches reporting-path errors before the run)
    global N_DRAWS
    keep = N_DRAWS
    N_DRAWS = 200
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", "2023-12-29")][::5]
    rows = []
    for d in days:
        p = 100.0 + rng.normal(0, 1)
        for h in BARS:
            p += rng.normal(0, 0.5)
            rows.append({"root": "NQ", "session": d, "et": f"{d} {h}", "hhmm": h, "contract": "NQZ9", "close": round(p, 2)})
    syn = pd.DataFrame(rows)
    rel_syn = {d: ("CPI" if i % 2 else "EMPSIT") for i, d in enumerate(days[::8])}
    res = study(syn, "NQ", rel_syn, primary=False)
    N_DRAWS = keep
    need(res["counts"]["used"] == len(rel_syn), "synthetic study: every release day should be used")
    need(res["reading"] in {"NO EFFECT", "NOT ABOVE NULL", "CONCENTRATED", "NO PRIZE", "SUPPORTED"}, "synthetic reading")
    print("selftest OK: synthetic fades, exclusions, the second implementation raises on a broken side, chunk == whole,"
          f" the whole study on a synthetic panel ({res['counts']['used']} release days, reading {res['reading']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
