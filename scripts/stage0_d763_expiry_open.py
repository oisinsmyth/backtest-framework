"""D763 Stage 0: the expiry-open fade (prop book), as pre-registered in
docs/decisions/D763-STAGE-0-PRE-REG-the-expiry-open-fade.md (d7f00423).

    python scripts/stage0_d763_expiry_open.py --selftest
    python scripts/stage0_d763_expiry_open.py --run          # once; SYSTEM python (pyarrow); writes data/stage0_d763_expiry_open.json

ES, NQ, YM, RTY from fut_day1m (09:00-15:59 ET, bar 0 = 09:00), 2016-01-04 -> 2023-12-29. x = P09:40 - P09:30 (P09:30 =
the 09:29 bar's close, pre-cash), y = P10:40 - P09:40. E1: delta = rho(x, y | monthly expiry days) - rho(x, y | other
Fridays) against the exact rotation of the expiry label along the ordered expiry-or-control days (count-matched), Holm over
the roots; E2: the fade's gross >= cost at t >= 2. VIX Wednesdays the same, as their own family. In-sample only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "docs" / "decisions" / "D763-STAGE-0-PRE-REG-the-expiry-open-fade.md"
OUT = REPO / "data" / "stage0_d763_expiry_open.json"
FX = REPO / "data" / "fixtures"
DAY1M = FX / "fut_day1m.parquet"
SESS = FX / "fut_index_sessions.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
ROOTS = ("ES", "NQ", "YM", "RTY")
FIRST, SEAL = "2016-01-04", "2024-01-01"
NB = 420
B0930, B0940, B1040, B1600 = 29, 39, 99, 419          # the bar whose close is P_t (the bar starting t-1)
NEED = (B0930, B0940, B1040, B1600)
ALPHA, T_MIN = 0.05, 2.0
VIX_CHECK = ("2018-02-14", "2019-03-19", "2020-03-18")


class D763Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D763Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def seal_check(df: pd.DataFrame, what: str) -> None:
    need(not (df["day"] >= SEAL).any(), f"the seal: a {what} row on or after 2024-01-01")


def clean(x):
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


# ================================================================================ statistics
def rank_avg(a) -> np.ndarray:
    """Average ranks (1-based), ties averaged (scipy's rankdata 'average')."""
    a = np.asarray(a, float)
    s = np.argsort(a, kind="mergesort")
    inv = np.empty(s.size, np.int64)
    inv[s] = np.arange(s.size)
    a_s = a[s]
    obs = np.r_[True, a_s[1:] != a_s[:-1]]
    dense = obs.cumsum()[inv]
    cnt = np.r_[np.nonzero(obs)[0], a.size]
    return 0.5 * (cnt[dense] + cnt[dense - 1] + 1)


def spearman(x, y) -> float:
    if len(x) < 3:
        return float("nan")
    rx, ry = rank_avg(x), rank_avg(y)
    rx, ry = rx - rx.mean(), ry - ry.mean()
    d = math.sqrt(float((rx * rx).sum() * (ry * ry).sum()))
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def delta(x, y, lab) -> float:
    return spearman(x[lab], y[lab]) - spearman(x[~lab], y[~lab])


def overlap(lab) -> np.ndarray:
    """Share of the true expiry days a rotated label re-selects, per offset 1 .. n-1. Expiry days recur near-periodically,
    so some rotations re-select many of them: the full rotation stays exact (a group), but those offsets carry part of
    any real effect, which costs power. Reported, never used to drop offsets (dropping them narrows the null: D763 s.5)."""
    return np.array([(lab & np.roll(lab, k)).sum() / lab.sum() for k in range(1, lab.size)])


def rotation(x, y, lab) -> dict:
    n = lab.size
    obs = delta(x, y, lab)
    null = np.array([delta(x, y, np.roll(lab, k)) for k in range(1, n)])
    ov = overlap(lab)
    return {"delta": obs, "offset0": delta(x, y, np.roll(lab, 0)), "rho_E": spearman(x[lab], y[lab]),
            "rho_C": spearman(x[~lab], y[~lab]), "n_E": int(lab.sum()), "n_C": int((~lab).sum()), "offsets": int(null.size),
            "overlap_p50_p90": [float(np.percentile(ov, 50)), float(np.percentile(ov, 90))],
            "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)),
            "p_one_sided": float((1 + (null <= obs).sum()) / (1 + null.size))}


def holm(ps: dict) -> dict:
    order = sorted(ps, key=lambda k: ps[k])
    out, run_ = {}, 0.0
    for i, k in enumerate(order):
        run_ = max(run_, min(1.0, ps[k] * (len(ps) - i)))
        out[k] = run_
    return out


def dist(x) -> dict:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 3:
        return {"n": int(n)}
    srt = np.sort(x)
    k = int(math.floor(0.01 * n))
    sd = float(x.std(ddof=1))
    w, l = x[x > 0], x[x < 0]
    return {"n": int(n), "mean": float(x.mean()), "t": float(x.mean() / (sd / math.sqrt(n))) if sd > 0 else float("nan"),
            "median": float(np.median(x)), "win": float((x > 0).mean()), "sd": sd,
            "payoff": float(w.mean() / -l.mean()) if w.size and l.size else None,
            "skew": float(pd.Series(x).skew()), "kurt": float(pd.Series(x).kurt()),
            "mean_ex_top1": float(srt[: n - k].mean()) if k else float(x.mean()),
            "mean_ex_bottom1": float(srt[k:].mean()) if k else float(x.mean()),
            "mean_trim_both1": float(srt[k: n - k].mean()) if k else float(x.mean())}


def sharpe_sortino(x: np.ndarray) -> tuple:
    sd = x.std(ddof=1)
    dd = math.sqrt(float(np.mean(np.minimum(x, 0) ** 2)))
    return (float(x.mean() / sd * math.sqrt(252)) if sd > 0 else None, float(x.mean() / dd * math.sqrt(252)) if dd > 0 else None)


# ================================================================================ the calendar
def third_friday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(year=y, month=m, day=1)
    return d + pd.Timedelta(days=(4 - d.weekday()) % 7 + 14)


def prev_session(d: pd.Timestamp, sessions: set) -> pd.Timestamp:
    while d.strftime("%Y-%m-%d") not in sessions:
        d -= pd.Timedelta(days=1)
    return d


def expiry_calendar(sessions: set) -> dict:
    em, eq, ev = [], [], []
    for y in range(2016, 2024):
        for m in range(1, 13):
            e = prev_session(third_friday(y, m), sessions).strftime("%Y-%m-%d")
            em.append(e)
            if m in (3, 6, 9, 12):
                eq.append(e)
            ny, nm = (y, m + 1) if m < 12 else (y + 1, 1)
            tf = third_friday(ny, nm)
            # a reference Friday on or after the seal (only 2024-01-19, a normal trading Friday) is taken as a date: no
            # 2024 data is read to decide it
            ref = tf if tf.strftime("%Y-%m-%d") >= SEAL else prev_session(tf, sessions)
            v = prev_session(ref - pd.Timedelta(days=30), sessions).strftime("%Y-%m-%d")
            ev.append(v)
    return {"E_M": sorted(set(em)), "E_Q": sorted(set(eq)), "E_V": sorted(set(ev))}


def check_calendar(cal: dict, sessions: set) -> None:
    for e in cal["E_M"]:
        d = pd.Timestamp(e)
        if d.weekday() != 4:
            nxt = (d + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            need(d.weekday() == 3 and nxt not in sessions, f"calendar: {e} is neither a Friday nor a Thursday before a closed Friday")
    yrs = pd.Series([e[:4] for e in cal["E_M"]]).value_counts()
    need(bool((yrs == 12).all()) and len(yrs) == 8, f"calendar: E_M per year {yrs.to_dict()}")
    for v in VIX_CHECK:
        need(v in cal["E_V"], f"calendar: VIX expiry {v} not reproduced")


# ================================================================================ data
def load_root(r: str, table=None) -> pd.DataFrame:
    if table is None:
        import pyarrow.parquet as pq
        table = pq.read_table(DAY1M, columns=["root", "contract", "day", "bar", "close", "same_front"],
                              filters=[("root", "=", r), ("day", "<", SEAL), ("day", ">=", FIRST)]).to_pandas()
    seal_check(table, f"{r} day1m")
    return table


def panel(raw: pd.DataFrame) -> dict:
    sf = raw.groupby("day")["same_front"].all()
    con = raw.groupby("day")["contract"].first()
    piv = raw.pivot(index="day", columns="bar", values="close").reindex(columns=range(NB))
    days = piv.index.to_numpy(str)
    Craw = piv.to_numpy(float)
    has = np.isfinite(Craw[:, list(NEED)]).all(1) & sf.reindex(days).to_numpy(bool)
    C = pd.DataFrame(Craw).ffill(axis=1).to_numpy(float)
    P = {"0930": C[:, B0930], "0940": C[:, B0940], "1040": C[:, B1040], "1600": C[:, B1600]}
    conv = con.reindex(days).to_numpy(str)
    prev_close = np.r_[np.nan, P["1600"][:-1]]
    same_prev = np.r_[False, conv[1:] == conv[:-1]]
    gap = np.where(same_prev, P["0930"] - prev_close, np.nan)
    return {"days": days[has], "x": (P["0940"] - P["0930"])[has], "y": (P["1040"] - P["0940"])[has],
            "y_close": (P["1600"] - P["0940"])[has], "gap": gap[has], "p": P["0940"][has], "n_all": int(days.size)}


def lag_audit(raw: pd.DataFrame, pn: dict, sample, xbar: int = B0940) -> None:
    g = {d: s.set_index("bar")["close"] for d, s in raw.groupby("day")}

    def p(day, b):
        s = g[day]
        for bb in range(b, -1, -1):
            if bb in s.index:
                return float(s[bb])
        return float("nan")

    for i in sample:
        d = pn["days"][i]
        for nm, want in (("x", p(d, xbar) - p(d, B0930)), ("y", p(d, B1040) - p(d, B0940)), ("y_close", p(d, B1600) - p(d, B0940))):
            need(math.isclose(want, pn[nm][i], rel_tol=0, abs_tol=1e-9), f"lag: {nm} at {d}: {want} vs {pn[nm][i]}")


# ================================================================================ the run
def family(pn: dict, E: set, weekday: int, cost: float, upp: float, tick_usd: float, bk: pd.DataFrame) -> dict:
    days = pn["days"]
    wd = pd.to_datetime(pd.Series(days)).dt.weekday.to_numpy()
    isE = np.isin(days, list(E))
    unit = isE | (wd == weekday)
    x, y, yc, gap, dd = pn["x"][unit], pn["y"][unit], pn["y_close"][unit], pn["gap"][unit], days[unit]
    lab = isE[unit]
    yrs = np.array([d[:4] for d in dd])
    rot = rotation(x, y, lab)
    need(math.isclose(rot["offset0"], rot["delta"], rel_tol=0, abs_tol=1e-15), "rotation offset 0 != observed")
    side = -np.sign(x)
    g = side * y * upp
    tk = lab & (side != 0)
    tc = (~lab) & (side != 0)
    gE, gC = dist(g[tk]), dist(g[tc])
    welch = (gE["mean"] - gC["mean"]) / math.sqrt(gE["sd"] ** 2 / gE["n"] + gC["sd"] ** 2 / gC["n"]) if gE.get("n", 0) > 2 and gC.get("n", 0) > 2 else None
    e2 = bool(gE.get("n", 0) >= 3 and gE["mean"] >= cost and gE["t"] >= T_MIN)
    tr = pd.DataFrame({"day": dd[tk], "side": side[tk], "gross": g[tk], "net": g[tk] - cost, "p": pn["p"][unit][tk]})
    tr["year"] = tr["day"].str[:4]
    cal = days                                                   # every eligible session of the root
    dn = tr.groupby("day")["net"].sum().reindex(cal, fill_value=0.0).to_numpy()
    dg = tr.groupby("day")["gross"].sum().reindex(cal, fill_value=0.0).to_numpy()
    rho_b = {}
    for b, gb in bk.groupby("book"):
        sb = gb.groupby("session")["net"].sum()
        span = cal[(cal >= max(min(cal), min(sb.index))) & (cal <= min(max(cal), max(sb.index)))]
        s1 = pd.Series(dn, index=cal).reindex(span).to_numpy()
        rho_b[b] = float(np.corrcoef(s1, sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if span.size > 30 and s1.std() > 0 else None
    eqv = np.cumsum(dn)
    top = tr.sort_values("net", ascending=False)
    return {"E1": rot, "E2": {"trades": int(tk.sum()), "gross": gE, "net": dist(g[tk] - cost), "pass": e2,
                              "control_fridays_gross": gC, "welch_t_E_minus_C": welch,
                              "net_plus_one_tick": dist(g[tk] - cost - tick_usd),
                              "daily_net_sharpe_sortino": sharpe_sortino(dn), "daily_gross_sharpe_sortino": sharpe_sortino(dg),
                              "max_dd_usd": float((np.maximum.accumulate(eqv) - eqv).max()), "breakeven_cost_usd": gE.get("mean"),
                              "by_year": {k: {"n": int(len(v)), "net": float(v["net"].sum()), "mean": float(v["net"].mean())} for k, v in tr.groupby("year")},
                              "long_short": {("long" if k > 0 else "short"): dist(v["net"]) for k, v in tr.groupby("side")},
                              "top5": top.head(5)[["day", "net"]].to_dict("records"), "bottom5": top.tail(5)[["day", "net"]].to_dict("records"),
                              "rho_books": rho_b},
            "reported": {"rho_E_y_close": spearman(x[lab], yc[lab]), "rho_C_y_close": spearman(x[~lab], yc[~lab]),
                         "fade_E_y_close_gross": dist((side * yc * upp)[tk]),
                         "rho_E_gap_y": spearman(gap[lab & np.isfinite(gap)], y[lab & np.isfinite(gap)]),
                         "rho_C_gap_y": spearman(gap[~lab & np.isfinite(gap)], y[~lab & np.isfinite(gap)]),
                         "mean_abs_x_E_usd": float(np.mean(np.abs(x[lab])) * upp), "mean_abs_x_C_usd": float(np.mean(np.abs(x[~lab])) * upp),
                         "sd_y_E_usd": float(np.std(y[lab], ddof=1) * upp), "sd_y_C_usd": float(np.std(y[~lab], ddof=1) * upp),
                         "rho_by_year_E": {yr: spearman(x[lab & (yrs == yr)], y[lab & (yrs == yr)]) for yr in sorted(set(yrs))}}}


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    sess = pd.read_csv(SESS, usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    sess = sess[(sess["root"] == "ES") & (sess["day"] < SEAL) & (sess["bars"] >= 200)]
    seal_check(sess, "sessions")
    sessions = set(sess["day"])
    cal = expiry_calendar(sessions)
    check_calendar(cal, sessions)
    costs = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    rng = np.random.default_rng(763)
    out, psM, psV = {}, {}, {}
    for r in ROOTS:
        raw = load_root(r)
        pn = panel(raw)
        n = pn["days"].size
        isE = np.flatnonzero(np.isin(pn["days"], cal["E_M"]))
        samp = list(rng.choice(isE, size=min(20, isE.size), replace=False)) + list(rng.choice(np.arange(n), size=20, replace=False))
        lag_audit(raw, pn, [int(i) for i in samp])
        ce = costs[r]["micro"]
        cost = float(ce["commission_rt_usd"]["value"] + ce["crossing_ticks_rt"][ce["default_line"]]["value"] * ce["tick_usd"])
        upp, tick_usd = float(ce["usd_per_point"]), float(ce["tick_usd"])
        fm = family(pn, set(cal["E_M"]), 4, cost, upp, tick_usd, bk)
        fv = family(pn, set(cal["E_V"]), 2, cost, upp, tick_usd, bk)
        # dose: quarterly against the other monthly expiry days (reported)
        days = pn["days"]
        q = np.isin(days, cal["E_Q"])
        mo = np.isin(days, cal["E_M"]) & ~q
        side = -np.sign(pn["x"])
        fm["reported"]["quarterly"] = {"rho": spearman(pn["x"][q], pn["y"][q]), "n": int(q.sum()),
                                       "fade_gross": dist((side * pn["y"] * upp)[q & (side != 0)])}
        fm["reported"]["other_monthly"] = {"rho": spearman(pn["x"][mo], pn["y"][mo]), "n": int(mo.sum()),
                                           "fade_gross": dist((side * pn["y"] * upp)[mo & (side != 0)])}
        psM[r], psV[r] = fm["E1"]["p_one_sided"], fv["E1"]["p_one_sided"]
        out[r] = {"sessions_all": pn["n_all"], "sessions_eligible": int(n), "cost": cost, "monthly": fm, "vix": fv}
        print(f"[D763] {r} done ({time.time() - t0:.0f} s)", flush=True)
    for fam, ps in (("monthly", psM), ("vix", psV)):
        adj = holm(ps)
        for r in ROOTS:
            f = out[r][fam]
            e1 = bool(f["E1"]["delta"] < 0 and f["E1"]["delta"] < f["E1"]["p05"] and adj[r] < ALPHA)
            f["E1"]["holm_p"], f["E1"]["pass"] = adj[r], e1
            f["reading"] = "NO EFFECT" if not e1 else ("PREMISE HOLDS" if f["E2"]["pass"] else "EFFECT, NO PRIZE")
    res = {"record": "D763 (d7f00423)", "readings": {r: {"monthly": out[r]["monthly"]["reading"], "vix": out[r]["vix"]["reading"]} for r in ROOTS},
           "calendar": {"E_M": len(cal["E_M"]), "E_Q": len(cal["E_Q"]), "E_V": len(cal["E_V"]),
                        "E_M_not_friday": [e for e in cal["E_M"] if pd.Timestamp(e).weekday() != 4],
                        "E_V_not_wednesday": [e for e in cal["E_V"] if pd.Timestamp(e).weekday() != 2]},
           "roots": out, "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(clean(res), fh, indent=1, default=str)
        fh.write("\n")
    show(res)
    return 0


def show(res: dict) -> None:
    print(f"[D763] calendar {res['calendar']}")
    for r, x in res["roots"].items():
        for fam in ("monthly", "vix"):
            f = x[fam]
            e1, e2 = f["E1"], f["E2"]
            g = e2["gross"]
            print(f"[D763] {r} {fam}: {f['reading']}  rho_E {e1['rho_E']:+.3f} (n {e1['n_E']}) rho_C {e1['rho_C']:+.3f} (n {e1['n_C']}); "
                  f"delta {e1['delta']:+.3f} (p05 {e1['p05']:+.3f} p50 {e1['p50']:+.3f} p95 {e1['p95']:+.3f}; p {e1['p_one_sided']:.3f} Holm {e1['holm_p']:.3f})")
            print(f"     E2 n {e2['trades']} gross {g.get('mean', float('nan')):+.2f} (t {g.get('t', float('nan')):.2f}, med {g.get('median', float('nan')):+.2f}) "
                  f"vs cost {x['cost']:.2f}; control gross {e2['control_fridays_gross'].get('mean', float('nan')):+.2f}; Welch {e2['welch_t_E_minus_C']}")
    print(f"[D763] wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    rng = np.random.default_rng(5)
    # ranks: ties averaged, equal to pandas on a tie-heavy input
    a = rng.integers(0, 5, 200).astype(float)
    if not np.allclose(rank_avg(a), pd.Series(a).rank(method="average").to_numpy()):
        fails.append("rank_avg != pandas on ties")
    b = rng.integers(0, 4, 200).astype(float)
    if not math.isclose(spearman(a, b), pd.Series(a).rank().corr(pd.Series(b).rank()), rel_tol=1e-12):
        fails.append("spearman != pandas")
    # the calendar on a synthetic session set: every weekday 2016-2023 except Good Fridays 2019-04-19 and 2022-04-15
    allwd = {d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-01", "2024-02-28")} - {"2019-04-19", "2022-04-15"}
    cal = expiry_calendar(allwd)
    try:
        check_calendar(cal, allwd)
    except D763Error as e:
        fails.append(f"calendar check raised on a valid set: {e}")
    if "2019-04-18" not in cal["E_M"] or "2022-04-14" not in cal["E_M"]:
        fails.append("Good Friday substitution")
    bad = dict(cal, E_V=[v for v in cal["E_V"] if v != "2019-03-19"])
    try:
        check_calendar(bad, allwd)
        fails.append("calendar check did not raise on a missing VIX date")
    except D763Error:
        pass
    # sign in money
    if float(-np.sign(2.0) * (-1.0) * 5.0) != 5.0:
        fails.append("sign in money")
    # the seal
    try:
        seal_check(pd.DataFrame({"day": ["2024-01-02"]}), "test")
        fails.append("seal did not raise")
    except D763Error:
        pass
    # the lag audit on synthetic raw rows: passes on the truth, raises when x is read one bar late
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2016-01-04", periods=12)]
    px = 100 + np.cumsum(rng.normal(0, 0.5, (12, NB)), axis=1)
    raw = pd.DataFrame({"day": np.repeat(days, NB), "bar": np.tile(np.arange(NB), 12), "close": px.ravel(),
                        "contract": "ESH6", "same_front": True})
    pn = panel(raw)
    try:
        lag_audit(raw, pn, range(12))
    except D763Error as e:
        fails.append(f"lag audit raised on the truth: {e}")
    try:
        lag_audit(raw, pn, range(12), xbar=B0940 + 1)
        fails.append("lag audit did not raise when x is read one bar late")
    except D763Error:
        pass
    # synthetic, on the real calendar's label pattern (third Fridays among Fridays): a planted expiry reversal passes E1;
    # noise fails it about 95 %; and the A1 restriction leaves no offset that re-selects an expiry day
    fr = sorted([d for d in allwd if pd.Timestamp(d).weekday() == 4 and d < SEAL] +
                [e for e in cal["E_M"] if pd.Timestamp(e).weekday() != 4])
    lab = np.isin(fr, cal["E_M"])
    n = lab.size
    ov = overlap(lab)
    if not (ov.size == n - 1 and ov.max() > 0.5 and (ov == 0).any()):
        fails.append("overlap")
    x = rng.normal(size=n)
    y = np.where(lab, -0.6 * x, 0.0) + rng.normal(size=n)
    rt = rotation(x, y, lab)
    if not (rt["delta"] < rt["p05"] and math.isclose(rt["offset0"], rt["delta"], abs_tol=1e-15)):
        fails.append("planted expiry reversal did not pass E1")
    nf = 0
    for s in range(100):
        r2 = np.random.default_rng(100 + s)
        xa, ya = r2.normal(size=n), r2.normal(size=n)
        rr = rotation(xa, ya, lab)
        nf += int(not (rr["delta"] < rr["p05"]))
    print(f"  noise fails E1 {nf} / 100")
    if not 88 <= nf <= 100:
        fails.append(f"noise fails E1 {nf}/100")
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D763] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
