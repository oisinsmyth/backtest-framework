"""D748 Stage 0: the activity keeper, as pre-registered in
docs/decisions/D748-STAGE-0-PRE-REG-the-activity-keeper.md (0de00296).

    python scripts/stage0_d748_activity_keeper.py --selftest
    python scripts/stage0_d748_activity_keeper.py --run        # once; writes data/stage0_d748_activity_keeper.json

Run on the SYSTEM interpreter: fut_day5m.parquet needs pyarrow, which the project venv lacks.

One placeholder trade, 13:30 -> 14:00 ET (fut_day5m bars 54..59), on the candidate micro with the smallest forecast
sigma$ (prior-20 RMS of the window move in points x micro $/point), direction = sign(open_54 - open_0) (long on zero),
stop 4 x sigma-hat with one tick of slippage, cost $3 + the d508_exec effective crossing (D748-A1). It fires only when a cadence's deadline
would otherwise lapse, with one backup eligible session. Variants F (M6E M2K MYM MES MNQ, primary), I (index micros),
M (M6E always). Calendars FULL (D737 + C1 + F2), NO_D737, NONE on 2018-05-14 -> 2023-12-29. In-sample only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

SPEC = REPO / "docs" / "decisions" / "D748-STAGE-0-PRE-REG-the-activity-keeper.md"
FIX = REPO / "data" / "fixtures" / "fut_day5m.parquet"
CAL = REPO / "data" / "fixtures" / "cme_session_calendar.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
OUT = REPO / "data" / "stage0_d748_activity_keeper.json"

SEAL = "2024-01-01"
KA_LO, IN_HI = "2016-01-01", "2023-12-29"
WARM, WIN_LO = "2018-01-01", "2018-05-14"
B_IN, B_OUT = 54, 59                     # 13:30 open .. 14:00 close
LOOK, STOP_K = 20, 4.0
ROOTS = {"6E": "M6E", "RTY": "M2K", "YM": "MYM", "ES": "MES", "NQ": "MNQ"}
VARIANTS = {"F": ("6E", "RTY", "YM", "ES", "NQ"), "I": ("RTY", "YM", "ES", "NQ"), "M": ("6E",)}
KNOWN_SD = {"6E": (8.079, 1983), "RTY": (22.318, 1598), "YM": (24.298, 1970), "ES": (31.971, 1975), "NQ": (50.368, 1972)}
CADENCES = {"C7": ("cal", 7), "W1": ("week", None), "T5": ("ses", 5), "T10": ("ses", 10), "C30": ("cal", 30)}
K1, K2, K3 = -50.0, -150.0, 300.0


class D748Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D748Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ inputs
def specs() -> dict[str, dict[str, float]]:
    r = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]
    out = {}
    for root in ROOTS:
        m = r[root]["micro"]
        need(m["symbol"] == ROOTS[root], f"{root}: micro is {m['symbol']}")
        need(m["default_line"] == "d508_exec", f"{root}: the micro's default line is {m['default_line']}")   # D748-A1
        xt = m["crossing_ticks_rt"]["d508_exec"]["value"]
        out[root] = {"upp": float(m["usd_per_point"]), "tick_usd": float(m["tick_usd"]),
                     "tick_pts": float(m["tick_usd"]) / float(m["usd_per_point"]),
                     "cost": float(m["commission_rt_usd"]["value"]) + float(xt) * float(m["tick_usd"])}
    return out


def no_seal(days: Any, what: str) -> None:
    need(len(days) == 0 or str(max(days)) < SEAL, f"{what} reads a row on or after {SEAL}")


def load_bars() -> pd.DataFrame:
    d = pd.read_parquet(FIX, columns=["root", "day", "bar", "open", "high", "low", "close", "same_front", "present"],
                        filters=[("root", "in", list(ROOTS)), ("day", "<=", IN_HI), ("day", ">=", KA_LO)])
    no_seal(d["day"].unique(), "the bars")
    return d[d["present"] & d["same_front"]].reset_index(drop=True)


def known_answer(d: pd.DataFrame, sp: dict) -> dict[str, Any]:
    out = {}
    for r, g in d.groupby("root"):
        o = g[g.bar == B_IN].set_index("day")["open"]
        c = g[g.bar == B_OUT].set_index("day")["close"]
        mv = (c - o).dropna() * sp[r]["upp"]
        sd, n = float(np.sqrt(np.mean(mv.to_numpy() ** 2))), int(len(mv))
        want, wn = KNOWN_SD[r]
        need(abs(sd - want) <= 0.001 and n == wn, f"known answer {r}: sd ${sd:.3f} n {n}, not ${want} n {wn}")
        out[r] = {"sd_usd": sd, "n": n}
    return out


def windows(d: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Per root, per day: the window's open/close/high/low when bars 54..59 are ALL present, and the session's first open."""
    out = {}
    for r, g in d.groupby("root"):
        w = g[(g.bar >= B_IN) & (g.bar <= B_OUT)]
        cnt = w.groupby("day")["bar"].nunique()
        full = cnt[cnt == B_OUT - B_IN + 1].index
        w = w[w.day.isin(full)].sort_values(["day", "bar"])
        agg = w.groupby("day").agg(hi=("high", "max"), lo=("low", "min"))
        agg["o"] = w[w.bar == B_IN].set_index("day")["open"]
        agg["c"] = w[w.bar == B_OUT].set_index("day")["close"]
        first = g.sort_values(["day", "bar"]).groupby("day")["open"].first()
        agg["o0"] = first.reindex(agg.index)
        out[r] = agg.sort_index()
    return out


def forecasts(win: dict[str, pd.DataFrame], sp: dict) -> dict[str, pd.Series]:
    """sigma-hat$ on each complete-window session: RMS of the previous LOOK complete sessions' moves, strictly before."""
    out = {}
    for r, w in win.items():
        m2 = (w["c"] - w["o"]) ** 2
        out[r] = np.sqrt(m2.rolling(LOOK, min_periods=LOOK).mean().shift(1)) * sp[r]["upp"]
    return out


def forecast_loop(win: pd.DataFrame, upp: float, day: str, leak: bool = False) -> float:
    days = list(win.index)
    i = days.index(day)
    lo = i - LOOK + (1 if leak else 0)
    hi = i + (1 if leak else 0)
    if lo < 0:
        return float("nan")
    s = 0.0
    for k in range(lo, hi):
        mv = win["c"].iloc[k] - win["o"].iloc[k]
        s += mv * mv
    return math.sqrt(s / LOOK) * upp


def lag_audit(win: dict, fc: dict, sp: dict, n: int = 200, seed: int = 748) -> None:
    rng = np.random.default_rng(seed)
    pairs = [(r, dd) for r in win for dd in win[r].index[LOOK:]]
    pick = rng.choice(len(pairs), size=min(n, len(pairs)), replace=False)
    for j in pick:
        r, dd = pairs[j]
        a, b = fc[r].loc[dd], forecast_loop(win[r], sp[r]["upp"], dd)
        need(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-9), f"lag audit {r} {dd}: {a} vs {b}")


def calendar() -> pd.DataFrame:
    c = pd.read_csv(CAL, usecols=["root", "day", "is_trading", "is_early_close", "fomc"], encoding="utf-8")
    c = c[(c["day"] >= WARM) & (c["day"] <= IN_HI)].copy()
    for k in ("is_trading", "is_early_close", "fomc"):
        need(set(c[k].dropna().unique()) <= {True, False, 0, 1}, f"calendar {k} is not boolean")
        c[k] = c[k].fillna(False).astype(bool)
    no_seal(c["day"].unique(), "the calendar")
    return c


# ================================================================================ the trade
def keeper_trade(variant: tuple, day: str, win: dict, fc: dict, sp: dict, early: dict) -> dict[str, Any] | None:
    best = None
    for r in variant:
        if day not in win[r].index or early.get((r, day), False):
            continue
        f = fc[r].loc[day]
        if not np.isfinite(f):
            continue
        if best is None or f < best[1]:
            best = (r, f)
    if best is None:
        return None
    r, f = best
    w = win[r].loc[day]
    return trade_pnl(r, float(f), float(w.o), float(w.c), float(w.hi), float(w.lo), float(w.o0), sp[r])


def trade_pnl(r: str, f: float, o: float, c: float, hi: float, lo: float, o0: float, s: dict) -> dict[str, Any]:
    d = 1 if (o - o0) >= 0 else -1
    stop = STOP_K * f / s["upp"]
    adverse = (o - lo) if d == 1 else (hi - o)
    hit = adverse >= stop
    exit_ = (o - d * stop - d * s["tick_pts"]) if hit else c
    gross = d * (exit_ - o) * s["upp"]
    return {"root": r, "dir": d, "forecast": f, "stop_hit": bool(hit), "gross": gross, "net": gross - s["cost"]}


# ================================================================================ deadlines
def deadline_of(kind: str, n: int | None, last_day: str, last_i: int, ses: list[str], s_i: int) -> int:
    """Index (into ses) of the last session on which a trade still meets the cadence."""
    if kind == "cal":
        lim = (date.fromisoformat(last_day) + timedelta(days=n)).isoformat()
        return int(np.searchsorted(ses, lim, side="right")) - 1
    if kind == "ses":
        return min(last_i + n, len(ses) - 1)
    wk = date.fromisoformat(ses[s_i]).isocalendar()[:2]                 # week: the last session of s's ISO week
    j = s_i
    while j + 1 < len(ses) and date.fromisoformat(ses[j + 1]).isocalendar()[:2] == wk:
        j += 1
    return j


def simulate(cad: str, ses: list[str], elig: np.ndarray, known: set, unknown: set, fire_fn, keeper_on: bool = True) -> dict:
    kind, n = CADENCES[cad]
    last_day, last_i = ses[0], 0
    week_done = {date.fromisoformat(ses[0]).isocalendar()[:2]}
    trade_days, fires, failed, redundant = {ses[0]}, [], 0, 0
    for i in range(1, len(ses)):
        s = ses[i]
        wk = date.fromisoformat(s).isocalendar()[:2]
        fired = False
        if keeper_on and elig[i] and s not in known:
            if kind == "week":
                due = wk not in week_done
            else:
                due = True
            if due:
                dl = deadline_of(kind, n, last_day, last_i, ses, i)
                remaining = int(elig[i + 1: dl + 1].sum()) if dl > i else 0
                if dl < i or remaining <= 1:                                 # past due (a failed fire) or due
                    t = fire_fn(s)
                    if t is None:
                        failed += 1
                    else:
                        fires.append((s, t))
                        fired = True
                        if s in unknown:
                            redundant += 1
        if fired or s in known or s in unknown:
            trade_days.add(s)
            last_day, last_i = s, i
            week_done.add(wk)
    return {"trade_days": trade_days, "fires": fires, "failed": failed, "redundant": redundant}


def breaches(cad: str, ses: list[str], trade_days: set) -> int:
    """Independent checker: gap arithmetic over the trade-day set (start counts as a trade)."""
    kind, n = CADENCES[cad]
    td = sorted(set(trade_days) | {ses[0]})
    end = ses[-1]
    if kind == "week":
        weeks = {}
        for s in ses:
            weeks.setdefault(date.fromisoformat(s).isocalendar()[:2], False)
        for s in td:
            weeks[date.fromisoformat(s).isocalendar()[:2]] = True
        return sum(1 for v in weeks.values() if not v)
    if kind == "cal":
        pts = [date.fromisoformat(x) for x in td]
        b = sum(1 for a, c in zip(pts, pts[1:]) if (c - a).days > n)
        return b + (1 if (date.fromisoformat(end) - pts[-1]).days > n else 0)
    idx = {s: i for i, s in enumerate(ses)}
    ii = [idx[x] for x in td]
    b = sum(1 for a, c in zip(ii, ii[1:]) if c - a > n)
    return b + (1 if len(ses) - 1 - ii[-1] > n else 0)


# ================================================================================ scoring
def score_cell(fires: list, sim: dict, ses: list[str], book_daily: pd.Series) -> dict[str, Any]:
    yrs = (date.fromisoformat(ses[-1]) - date.fromisoformat(ses[0])).days / 365.25
    if not fires:
        return {"fires": 0, "fires_per_year": 0.0, "failed": sim["failed"], "redundant": sim["redundant"]}
    t = pd.DataFrame([dict(day=s, **x) for s, x in fires])
    net = t["net"].to_numpy()
    dts = pd.to_datetime(t["day"])
    roll = min(float(net[(dts >= d0) & (dts < d0 + pd.Timedelta(days=30))].sum()) for d0 in dts)
    kd = pd.Series(net, index=t["day"]).groupby(level=0).sum().reindex(ses, fill_value=0.0)
    bd = book_daily.reindex(ses, fill_value=0.0)
    rho = float(np.corrcoef(kd, bd)[0, 1]) if kd.std() > 0 and bd.std() > 0 else None
    return {"fires": int(len(t)), "fires_per_year": len(t) / yrs, "failed": sim["failed"], "redundant": sim["redundant"],
            "net_mean": float(net.mean()), "net_median": float(np.median(net)), "net_worst": float(net.min()),
            "net_best": float(net.max()), "gross_mean": float(t["gross"].mean()), "stop_hit_rate": float(t["stop_hit"].mean()),
            "worst_30d": roll, "net_per_year": float(net.sum()) / yrs,
            "root_share": {ROOTS[k]: float(v) for k, v in t["root"].value_counts(normalize=True).items()},
            "rho_with_full_book_daily": rho}


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    sp = specs()
    bars = load_bars()
    ka = known_answer(bars, sp)
    win = windows(bars[bars["day"] >= WARM])
    fc = forecasts(win, sp)
    lag_audit(win, fc, sp)
    cal = calendar()
    es = cal[cal.root == "ES"].set_index("day")
    ses = [s for s in es.index if es.loc[s, "is_trading"] and WIN_LO <= s <= IN_HI]
    elig = np.array([not bool(es.loc[s, "fomc"]) and not bool(es.loc[s, "is_early_close"]) for s in ses])
    early = {(r, dd): bool(v) for r, dd, v in cal[["root", "day", "is_early_close"]].itertuples(index=False)}

    import vault_d745_abstention_principle as V
    b = V.in_sample_books()["books"]
    comp = {k: v[(v["session"] >= WIN_LO) & (v["session"] <= IN_HI)] for k, v in b.items()}
    cal_sets = {"FULL": (set(comp["D737"]["session"]), set(comp["C1"]["session"]) | set(comp["F2"]["session"])),
                "NO_D737": (set(), set(comp["C1"]["session"]) | set(comp["F2"]["session"])),
                "NONE": (set(), set())}
    book_daily = pd.concat([v.groupby("session")["net"].sum() for v in comp.values()]).groupby(level=0).sum()

    cells: dict[str, Any] = {}
    for vn, roots in VARIANTS.items():
        fire_fn = (lambda s, roots=roots: keeper_trade(roots, s, win, fc, sp, early))
        for cn, (known, unknown) in cal_sets.items():
            for cad in CADENCES:
                sim = simulate(cad, ses, elig, known, unknown, fire_fn)
                br = breaches(cad, ses, sim["trade_days"])
                c = score_cell(sim["fires"], sim, ses, book_daily)
                c["breaches"] = br
                cells[f"{vn}|{cn}|{cad}"] = c
    # the canary: keeper off under NONE must breach on every cadence
    for cad in CADENCES:
        sim = simulate(cad, ses, elig, set(), set(), lambda s: None, keeper_on=False)
        need(breaches(cad, ses, sim["trade_days"]) > 0, f"keeper-off canary did not breach on {cad}")

    verdict = {vn: readings(cells, vn) for vn in VARIANTS}
    f_cells = [v for k, v in cells.items() if k.startswith("F|") and v["fires"]]
    m6e = float(np.mean([v["root_share"].get("M6E", 0.0) for v in f_cells])) if f_cells else None
    res = {"record": "D748 (0de00296)", "known_answer": ka, "window": [ses[0], ses[-1]], "sessions": len(ses),
           "eligible_sessions": int(elig.sum()), "component_trades_in_window": {k: int(len(v)) for k, v in comp.items()},
           "costs": {ROOTS[r]: round(v["cost"], 3) for r, v in sp.items()}, "cells": cells, "readings": verdict,
           "F_mean_M6E_share_of_fires": m6e, "selector_is_M6E": (m6e is not None and m6e >= 0.95),
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    write_once(OUT, res)
    show(res)
    return 0


def readings(cells: dict, vn: str) -> dict[str, Any]:
    mine = {k: v for k, v in cells.items() if k.startswith(vn + "|")}
    traded = [v for v in mine.values() if v["fires"]]
    k1 = min(v["net_worst"] for v in traded) if traded else 0.0
    k2 = min(v["worst_30d"] for v in traded) if traded else 0.0
    none = {k: v for k, v in mine.items() if "|NONE|" in k}
    top = max(none.items(), key=lambda kv: kv[1]["fires"])
    k3 = -top[1].get("net_per_year", 0.0)
    k4 = sum(v["breaches"] for v in mine.values())
    ok = {"K1": k1 >= K1, "K2": k2 >= K2, "K3": k3 <= K3, "K4": k4 == 0}
    return {"K1_worst_trade": k1, "K2_worst_30d": k2, "K3_cost_per_year": k3, "K3_cadence": top[0],
            "K4_breaches": int(k4), **{f"{k}_holds": v for k, v in ok.items()},
            "reading": ("READY" if all(ok.values()) else "NOT READY: " + ", ".join(k for k, v in ok.items() if not v))}


def strip(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): strip(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [strip(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def write_once(path: Path, doc: dict) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(strip(doc), fh, indent=1)
        fh.write("\n")


def show(res: dict) -> None:
    for vn, r in res["readings"].items():
        print(f"[D748] variant {vn}: {r['reading']}  K1 {r['K1_worst_trade']:.2f}  K2 {r['K2_worst_30d']:.2f}  "
              f"K3 {r['K3_cost_per_year']:.2f} ({r['K3_cadence']})  K4 {r['K4_breaches']}")
    for k, v in res["cells"].items():
        if v["fires"]:
            print(f"  {k:18s} fires/yr {v['fires_per_year']:6.1f} failed {v['failed']} redundant {v['redundant']} "
                  f"breaches {v['breaches']} net mean {v['net_mean']:6.2f} worst {v['net_worst']:7.2f} "
                  f"30d {v['worst_30d']:7.2f} $/yr {v['net_per_year']:7.1f} stop {v['stop_hit_rate']:.3f} {v['root_share']}")
        else:
            print(f"  {k:18s} fires 0 failed {v['failed']} breaches {v['breaches']}")
    print(f"[D748] F's mean M6E share {res['F_mean_M6E_share_of_fires']}; wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    s = {"upp": 2.0, "tick_pts": 0.25, "tick_usd": 0.5, "cost": 3.0}
    up = trade_pnl("NQ", 10.0, 100.0, 104.0, 104.0, 100.0, 99.0, s)            # long (100 > 99), rises 4 points
    dn = trade_pnl("NQ", 10.0, 100.0, 104.0, 104.0, 100.0, 101.0, s)           # short, same rise
    if not (up["dir"] == 1 and math.isclose(up["gross"], 8.0) and dn["dir"] == -1 and math.isclose(dn["gross"], -8.0)):
        fails.append(f"sign in money: {up} {dn}")
    st = trade_pnl("NQ", 10.0, 100.0, 101.0, 100.5, 70.0, 99.0, s)            # stop 4*10/2 = 20 pts, touched
    if not (st["stop_hit"] and math.isclose(st["gross"], -(20.0 + 0.25) * 2.0)):
        fails.append(f"stop exit is not stop + one tick: {st}")
    # lag: the loop agrees with the rolling forecast, and a leak canary disagrees
    rng = np.random.default_rng(1)
    days = [f"2019-{m:02d}-{d:02d}" for m in range(1, 13) for d in range(1, 29)][:120]
    w = pd.DataFrame({"o": 100 + rng.normal(0, 1, 120), "c": 100 + rng.normal(0, 1, 120)}, index=days)
    f = np.sqrt(((w["c"] - w["o"]) ** 2).rolling(LOOK, min_periods=LOOK).mean().shift(1)) * 2.0
    if not all(math.isclose(f.iloc[i], forecast_loop(w, 2.0, days[i]), rel_tol=1e-12) for i in range(LOOK, 120)):
        fails.append("the forecast loop disagrees with the rolling forecast")
    if all(math.isclose(f.iloc[i], forecast_loop(w, 2.0, days[i], leak=True), rel_tol=1e-12) for i in range(LOOK, 120)):
        fails.append("the leak canary agrees")
    try:
        lag_audit({"NQ": w}, {"NQ": f * 0 + 1.0}, {"NQ": {"upp": 2.0}}, n=5)
        fails.append("lag_audit did not raise on a wrong forecast")
    except D748Error:
        pass
    # deadlines: the engine with an always-succeeding keeper never breaches; keeper off does; checker agrees
    ses = pd.bdate_range("2019-01-01", "2020-12-31").strftime("%Y-%m-%d").tolist()
    ses = [x for i, x in enumerate(ses) if i % 17 != 5]                          # holes, like holidays
    elig = np.array([i % 23 != 7 for i in range(len(ses))])                      # some ineligible sessions
    comp = set(ses[::9])
    for cad in CADENCES:
        sim = simulate(cad, ses, elig, set(), comp, lambda s: {"net": -4.0, "gross": -1.0, "root": "6E", "stop_hit": False})
        if breaches(cad, ses, sim["trade_days"]) != 0:
            fails.append(f"{cad}: the keeper breaches")
        off = simulate(cad, ses, elig, set(), set(), lambda s: None, keeper_on=False)
        if breaches(cad, ses, off["trade_days"]) == 0:
            fails.append(f"{cad}: keeper off does not breach")
    if breaches("C7", ["2019-01-01", "2019-01-02", "2019-01-20"], {"2019-01-01"}) != 1:
        fails.append("the C7 checker misses a 19-day gap")
    try:
        no_seal(["2023-12-29", "2024-01-02"], "planted")
        fails.append("the seal did not raise")
    except D748Error:
        pass
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D748Error:
        pass
    for x in fails:
        print(f"[SELFTEST FAIL] {x}")
    print(f"[D748] selftest: {'FAIL' if fails else 'all passed'}")
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
