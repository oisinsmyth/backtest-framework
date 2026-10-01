"""D750 Stage 0: a positive-mean keeper, as pre-registered in
docs/decisions/D750-STAGE-0-PRE-REG-a-positive-mean-keeper.md (9a8cf775).

    python scripts/stage0_d750_positive_keeper.py --selftest
    python scripts/stage0_d750_positive_keeper.py --run        # once; writes data/stage0_d750_positive_keeper.json

Run on the SYSTEM interpreter (fut_day5m needs pyarrow). D748's frame is reused READ-ONLY through its module
(scripts/stage0_d748_activity_keeper.py): bars, windows, forecasts, costs (d508_exec), the deadline engine, the breach
checker, the component calendars and the K-readings. The one change: the stop is min(4 sigma-hat$, $40) + one tick.
E1 mean net > 0 at t >= 2 and E2 the exact circular rotation of the direction series, on every eligible session
2016 -> 2023; M1 median net >= 0; D748's K1-K4 on its calendars. In-sample only.
"""
from __future__ import annotations

import argparse
import hashlib
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
import stage0_d748_activity_keeper as K  # noqa: E402  (read-only reuse)

SPEC = REPO / "docs" / "decisions" / "D750-STAGE-0-PRE-REG-a-positive-mean-keeper.md"
OUT = REPO / "data" / "stage0_d750_positive_keeper.json"
D748_OUT = REPO / "data" / "stage0_d748_activity_keeper.json"
CAP = 40.0
ROOTS_I = K.VARIANTS["I"]                                   # RTY YM ES NQ -> M2K MYM MES MNQ
ALL_LO = "2016-01-01"
T_MIN, P_MAX = 2.0, 0.05
KNOWN_I = {"K1_worst_trade": -102.46094, "K2_worst_30d": -174.82524, "K3_cost_per_year": 99.61942}
KNOWN_I_FIRES = ("I|NONE|C7", 384)


class D750Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D750Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ the capped trade
def trade_cap(r: str, f: float, o: float, c: float, hi: float, lo: float, o0: float, s: dict, cap: float) -> dict:
    """D748's trade_pnl with the stop at min(4 sigma-hat$, cap) dollars; cap = inf reproduces it exactly."""
    d = 1 if (o - o0) >= 0 else -1
    stop = min(K.STOP_K * f, cap) / s["upp"]
    adverse = (o - lo) if d == 1 else (hi - o)
    hit = adverse >= stop
    exit_ = (o - d * stop - d * s["tick_pts"]) if hit else c
    gross = d * (exit_ - o) * s["upp"]
    return {"root": r, "dir": d, "forecast": f, "stop_hit": bool(hit), "gross": gross, "net": gross - s["cost"]}


def both_sides(f: float, o: float, c: float, hi: float, lo: float, s: dict, cap: float) -> tuple[float, float, bool, bool]:
    """Net of the long and of the short on one window (for the rotation): (net_long, net_short, hit_long, hit_short)."""
    stop = min(K.STOP_K * f, cap) / s["upp"]
    hl, hs = (o - lo) >= stop, (hi - o) >= stop
    xl = (o - stop - s["tick_pts"]) if hl else c
    xs = (o + stop + s["tick_pts"]) if hs else c
    return (xl - o) * s["upp"] - s["cost"], (o - xs) * s["upp"] - s["cost"], bool(hl), bool(hs)


def choose(roots: tuple, day: str, win: dict, fc: dict, early: dict) -> tuple[str, float] | None:
    best = None
    for r in roots:
        if day not in win[r].index or early.get((r, day), False):
            continue
        f = fc[r].loc[day]
        if not np.isfinite(f):
            continue
        if best is None or f < best[1]:
            best = (r, float(f))
    return best


def keeper_cap(roots: tuple, day: str, win: dict, fc: dict, sp: dict, early: dict, cap: float) -> dict | None:
    ch = choose(roots, day, win, fc, early)
    if ch is None:
        return None
    r, f = ch
    w = win[r].loc[day]
    return trade_cap(r, f, float(w.o), float(w.c), float(w.hi), float(w.lo), float(w.o0), sp[r], cap)


# ================================================================================ the rotation
def rotation(dirs: np.ndarray, nl: np.ndarray, ns: np.ndarray) -> dict[str, Any]:
    n = len(dirs)
    obs = float(np.where(dirs > 0, nl, ns).mean())
    means = np.empty(n)
    meds = np.empty(n)
    for k in range(n):
        x = np.where(np.roll(dirs, k) > 0, nl, ns)
        means[k] = x.mean()
        meds[k] = np.median(x)
    need(means[0] == obs, "rotation: offset 0 is not the observed mean")
    return {"observed_mean": obs, "offsets": n, "p_high": float(np.mean(means >= obs)),
            "null_mean_p50": float(np.percentile(means, 50)), "null_mean_p95": float(np.percentile(means, 95)),
            "null_median_p50": float(np.percentile(meds, 50)), "null_median_p95": float(np.percentile(meds, 95)),
            "_means": means}


def rotation_loop(dirs: np.ndarray, nl: np.ndarray, ns: np.ndarray, ks: list[int]) -> list[float]:
    out = []
    n = len(dirs)
    for k in ks:
        s = 0.0
        for i in range(n):
            d = dirs[(i - k) % n]
            s += nl[i] if d > 0 else ns[i]
        out.append(s / n)
    return out


# ================================================================================ statistics
def line_stats(t: pd.DataFrame) -> dict[str, Any]:
    net = t["net"].to_numpy()
    n = len(net)
    sd = float(net.std(ddof=1))
    q_lo, q_hi = np.quantile(net, [0.01, 0.99])
    down = net[net < 0]
    dd = math.sqrt(float(np.mean(np.minimum(net, 0.0) ** 2)))
    yr = t.assign(y=t["day"].str[:4]).groupby("y")["net"].mean()
    return {"n": n, "net_mean": float(net.mean()), "net_t": float(net.mean() / (sd / math.sqrt(n))),
            "net_median": float(np.median(net)), "gross_mean": float(t["gross"].mean()),
            "gross_median": float(t["gross"].median()), "win_rate": float(np.mean(net > 0)),
            "stop_hit_rate": float(t["stop_hit"].mean()), "net_sd": sd, "worst": float(net.min()), "best": float(net.max()),
            "trim_ex_top": float(net[net <= q_hi].mean()), "trim_ex_bottom": float(net[net >= q_lo].mean()),
            "trim_both": float(net[(net >= q_lo) & (net <= q_hi)].mean()),
            "sharpe_ann": float(net.mean() / sd * math.sqrt(252)), "sortino_ann": float(net.mean() / dd * math.sqrt(252)) if dd > 0 else None,
            "losers": int(len(down)), "by_year_mean": {k: float(v) for k, v in yr.items()},
            "years_positive": int((yr > 0).sum()), "years": int(len(yr)),
            "root_share": {K.ROOTS[k]: float(v) for k, v in t["root"].value_counts(normalize=True).items()}}


def calendar16() -> pd.DataFrame:
    c = pd.read_csv(K.CAL, usecols=["root", "day", "is_trading", "is_early_close", "fomc"], encoding="utf-8")
    c = c[(c["day"] >= ALL_LO) & (c["day"] <= K.IN_HI)].copy()
    for k in ("is_trading", "is_early_close", "fomc"):
        need(set(c[k].dropna().unique()) <= {True, False, 0, 1}, f"calendar {k} is not boolean")
        c[k] = c[k].fillna(False).astype(bool)
    K.no_seal(c["day"].unique(), "the calendar")
    return c


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    sp = K.specs()
    bars = K.load_bars()
    K.known_answer(bars, sp)

    # --- D748's frame (forecasts warm from 2018-01) for the known answer and K1-K4
    win18 = K.windows(bars[bars["day"] >= K.WARM])
    fc18 = K.forecasts(win18, sp)
    K.lag_audit(win18, fc18, sp)
    cal18 = K.calendar()
    es18 = cal18[cal18.root == "ES"].set_index("day")
    ses = [s for s in es18.index if es18.loc[s, "is_trading"] and K.WIN_LO <= s <= K.IN_HI]
    elig = np.array([not bool(es18.loc[s, "fomc"]) and not bool(es18.loc[s, "is_early_close"]) for s in ses])
    early18 = {(r, dd): bool(v) for r, dd, v in cal18[["root", "day", "is_early_close"]].itertuples(index=False)}
    b = K.read_books()
    comp = {k: v[(v["session"] >= K.WIN_LO) & (v["session"] <= K.IN_HI)] for k, v in b.items()}
    cal_sets = {"FULL": (set(comp["D737"]["session"]), set(comp["C1"]["session"]) | set(comp["F2"]["session"])),
                "NO_D737": (set(), set(comp["C1"]["session"]) | set(comp["F2"]["session"])),
                "NONE": (set(), set())}
    book_daily = pd.concat([v.groupby("session")["net"].sum() for v in comp.values()]).groupby(level=0).sum()

    cells: dict[str, Any] = {}
    for vn, cap in (("I", math.inf), ("I40", CAP)):
        fire = (lambda s, cap=cap: keeper_cap(ROOTS_I, s, win18, fc18, sp, early18, cap))
        for cn, (known, unknown) in cal_sets.items():
            for cad in K.CADENCES:
                sim = K.simulate(cad, ses, elig, known, unknown, fire)
                c = K.score_cell(sim["fires"], sim, ses, book_daily)
                c["breaches"] = K.breaches(cad, ses, sim["trade_days"])
                if c["fires"]:
                    c["net_median"] = float(np.median([x["net"] for _, x in sim["fires"]]))
                cells[f"{vn}|{cn}|{cad}"] = c
    rd = {vn: K.readings(cells, vn) for vn in ("I", "I40")}
    # the known answer: D748's variant I, reproduced with the cap disabled
    d748 = json.loads(D748_OUT.read_text(encoding="utf-8"))["readings"]["I"]
    for k, v in KNOWN_I.items():
        need(abs(rd["I"][k] - v) <= 1e-5 and abs(rd["I"][k] - d748[k]) <= 1e-9, f"known answer {k}: {rd['I'][k]} vs {v}")
    need(rd["I"]["K4_breaches"] == 0 and cells[KNOWN_I_FIRES[0]]["fires"] == KNOWN_I_FIRES[1],
         "known answer: D748's I breaches / fires not reproduced")

    # --- every eligible session, 2016 -> 2023 (forecasts warm from 2016-01)
    win16 = K.windows(bars)
    fc16 = K.forecasts(win16, sp)
    K.lag_audit(win16, fc16, sp)
    cal16 = calendar16()
    es16 = cal16[cal16.root == "ES"].set_index("day")
    early16 = {(r, dd): bool(v) for r, dd, v in cal16[["root", "day", "is_early_close"]].itertuples(index=False)}
    rows, rows_unc, nl, ns, dirs = [], [], [], [], []
    for s in es16.index:
        if not es16.loc[s, "is_trading"] or es16.loc[s, "fomc"] or es16.loc[s, "is_early_close"]:
            continue
        ch = choose(ROOTS_I, s, win16, fc16, early16)
        if ch is None:
            continue
        r, f = ch
        w = win16[r].loc[s]
        o, c, hi, lo, o0 = float(w.o), float(w.c), float(w.hi), float(w.lo), float(w.o0)
        tr = trade_cap(r, f, o, c, hi, lo, o0, sp[r], CAP)
        rows.append(dict(day=s, **tr))
        rows_unc.append(dict(day=s, **trade_cap(r, f, o, c, hi, lo, o0, sp[r], math.inf)))
        a, bb, _, _ = both_sides(f, o, c, hi, lo, sp[r], CAP)
        need(math.isclose(a if tr["dir"] == 1 else bb, tr["net"], rel_tol=0, abs_tol=1e-9), f"{s}: both_sides disagrees")
        nl.append(a)
        ns.append(bb)
        dirs.append(tr["dir"])
    t = pd.DataFrame(rows)
    tu = pd.DataFrame(rows_unc)
    K.no_seal(t["day"].unique(), "the scored sessions")
    nl, ns, dirs = np.array(nl), np.array(ns), np.array(dirs)
    st = line_stats(t)
    rot = rotation(dirs, nl, ns)
    loop = rotation_loop(dirs, nl, ns, list(range(0, len(dirs), max(1, len(dirs) // 50)))[:50])
    vec = [float(np.where(np.roll(dirs, k) > 0, nl, ns).mean()) for k in range(0, len(dirs), max(1, len(dirs) // 50))][:50]
    need(all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(loop, vec)), "rotation: vector != loop")

    E1 = st["net_mean"] > 0 and st["net_t"] >= T_MIN
    E2 = rot["p_high"] <= P_MAX
    M1 = st["net_median"] >= 0
    kk = rd["I40"]
    ok = {"E1": E1, "E2": E2, "M1": M1, "K1": kk["K1_holds"], "K2": kk["K2_holds"], "K3": kk["K3_holds"], "K4": kk["K4_holds"]}
    reading = "POSITIVE KEEPER" if all(ok.values()) else "NOT POSITIVE: " + ", ".join(k for k, v in ok.items() if not v)
    res = {"record": "D750 (9a8cf775)", "reading": reading, "criteria": ok,
           "all_sessions": {"span": [t["day"].min(), t["day"].max()], "capped": st, "uncapped": line_stats(tu),
                            "rotation": {k: v for k, v in rot.items() if not k.startswith("_")}},
           "keeper_readings": rd, "cells": cells, "costs": {K.ROOTS[r]: round(v["cost"], 3) for r, v in sp.items()},
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC),
           "d748_runner_sha256": sha(Path(K.__file__).resolve()), "wall_s": round(time.time() - t0, 1)}
    K.write_once(OUT, res)
    show(res)
    return 0


def show(res: dict) -> None:
    a = res["all_sessions"]
    c, u, r = a["capped"], a["uncapped"], a["rotation"]
    print(f"[D750] {res['reading']}  {res['criteria']}")
    print(f"  all sessions {a['span']}: n {c['n']}  net mean {c['net_mean']:.3f} (t {c['net_t']:.2f})  median {c['net_median']:.3f}  "
          f"gross mean {c['gross_mean']:.3f}  win {c['win_rate']:.3f}  stop {c['stop_hit_rate']:.3f}  worst {c['worst']:.2f}")
    print(f"    trims ex-top {c['trim_ex_top']:.3f} ex-bottom {c['trim_ex_bottom']:.3f} both {c['trim_both']:.3f}  "
          f"Sharpe {c['sharpe_ann']:.2f} Sortino {c['sortino_ann']:.2f}  years+ {c['years_positive']}/{c['years']}  {c['root_share']}")
    print(f"    by year {({k: round(v, 2) for k, v in c['by_year_mean'].items()})}")
    print(f"  uncapped: net mean {u['net_mean']:.3f} (t {u['net_t']:.2f}) median {u['net_median']:.3f} gross {u['gross_mean']:.3f} worst {u['worst']:.2f}")
    print(f"  rotation: p_high {r['p_high']:.4f} over {r['offsets']}; mean p50 {r['null_mean_p50']:.3f} p95 {r['null_mean_p95']:.3f}; "
          f"median p50 {r['null_median_p50']:.3f} p95 {r['null_median_p95']:.3f}")
    for vn, x in res["keeper_readings"].items():
        print(f"  keeper {vn}: {x['reading']}  K1 {x['K1_worst_trade']:.2f} K2 {x['K2_worst_30d']:.2f} K3 {x['K3_cost_per_year']:.2f} K4 {x['K4_breaches']}")
    for k, v in res["cells"].items():
        if k.startswith("I40|") and v["fires"]:
            print(f"    {k:16s} fires/yr {v['fires_per_year']:5.1f} net mean {v['net_mean']:6.2f} median {v['net_median']:6.2f} "
                  f"worst {v['net_worst']:7.2f} 30d {v['worst_30d']:7.2f} $/yr {v['net_per_year']:7.1f} breaches {v['breaches']}")
    print(f"[D750] wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    s = {"upp": 5.0, "tick_pts": 0.1, "tick_usd": 0.5, "cost": 3.76}
    # the cap binds: 4 sigma-hat = $80 > $40; a 20-point (= $100) adverse excursion on a long -> loss $40 + tick + cost
    x = trade_cap("RTY", 20.0, 100.0, 101.0, 100.5, 80.0, 99.0, s, CAP)
    if not (x["stop_hit"] and math.isclose(x["net"], -(40.0 + 0.5) - 3.76)):
        fails.append(f"the cap does not bind as declared: {x}")
    # inside 4 sigma-hat and the cap: no stop, time exit
    y = trade_cap("RTY", 20.0, 100.0, 101.0, 101.5, 99.0, 99.0, s, CAP)
    if y["stop_hit"] or not math.isclose(y["gross"], 5.0):
        fails.append(f"a path inside the stop was stopped: {y}")
    # sign in money: a short on a rising window loses
    z = trade_cap("RTY", 20.0, 100.0, 101.0, 101.5, 99.0, 101.0, s, CAP)
    if not (z["dir"] == -1 and math.isclose(z["gross"], -5.0)):
        fails.append(f"sign in money: {z}")
    # cap = inf reproduces D748's trade_pnl exactly
    rng = np.random.default_rng(750)
    for _ in range(200):
        o = 100 + rng.normal()
        c, hi, lo, o0, f = o + rng.normal(), o + abs(rng.normal()) * 3, o - abs(rng.normal()) * 3, o + rng.normal(), abs(rng.normal()) * 5 + 0.1
        a = trade_cap("RTY", f, o, c, max(hi, c, o), min(lo, c, o), o0, s, math.inf)
        b = K.trade_pnl("RTY", f, o, c, max(hi, c, o), min(lo, c, o), o0, s)
        if a != b:
            fails.append(f"cap = inf differs from D748's trade_pnl: {a} vs {b}")
            break
    # both_sides agrees with trade_cap on the traded side
    for _ in range(200):
        o = 100 + rng.normal()
        c, o0, f = o + rng.normal(), o + rng.normal(), abs(rng.normal()) * 5 + 0.1
        hi, lo = max(o, c) + abs(rng.normal()) * 3, min(o, c) - abs(rng.normal()) * 3
        tr = trade_cap("RTY", f, o, c, hi, lo, o0, s, CAP)
        nl, ns, _, _ = both_sides(f, o, c, hi, lo, s, CAP)
        if not math.isclose(nl if tr["dir"] == 1 else ns, tr["net"], abs_tol=1e-9):
            fails.append("both_sides disagrees with trade_cap")
            break
    # the rotation: offset 0, a planted perfect direction, vector == loop
    n = 400
    mv = rng.normal(0, 10, n)
    nl, ns = mv - 3.0, -mv - 3.0
    perfect = np.where(mv >= 0, 1, -1)
    r = rotation(perfect, nl, ns)
    if not r["p_high"] < 0.01:
        fails.append(f"the planted perfect direction has p {r['p_high']}")
    rand = np.where(rng.random(n) < 0.5, 1, -1)
    ks = list(range(0, n, 8))[:50]
    vec = [float(np.where(np.roll(rand, k) > 0, nl, ns).mean()) for k in ks]
    if not all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(rotation_loop(rand, nl, ns, ks), vec)):
        fails.append("the rotation's vector form differs from its loop")
    try:
        K.no_seal(["2023-12-29", "2024-01-02"], "planted")
        fails.append("the seal did not raise")
    except K.D748Error:
        pass
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D750Error:
        pass
    for f_ in fails:
        print(f"[SELFTEST FAIL] {f_}")
    print(f"[D750] selftest: {'FAIL' if fails else 'all passed'}")
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
