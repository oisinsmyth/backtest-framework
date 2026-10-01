"""D752 Stage 0: the YM open-reversal fade, as pre-registered in
docs/decisions/D752-STAGE-0-PRE-REG-the-ym-open-reversal-fade.md (7af83e82).

    uv run --no-sync python scripts/stage0_d752_ym_open_fade.py --selftest
    uv run --no-sync python scripts/stage0_d752_ym_open_fade.py --run      # once; writes data/stage0_d752_ym_open_fade.json

D727's YM panel, read-only (load_root, objects, lag_audit, money_book). At 11:00 ET (P = the 10:59 bar's close), when
|z| >= 1.0, side = -sign(x): one MYM at D727's cost line ($3.797). m = |P - O|. Brackets checked on each minute
11:00 .. 15:58, the stop assumed first within a bar, the target filled only through a tick, the stop at its price
less a tick, else 15:59's close. B1: target m (the open), stop m. B2: target 0.5 m, stop 1.0 m. E0 (context): held to
15:59. SIGNAL = gross above the exact circular rotation of the side labels (Holm over B1, B2); N1 net > 0 at t >= 2,
N2 median >= 0, N3 skew >= -0.5, N4 D736's G1-G3. In-sample only (<= 2023-12-29).
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
import stage0_d727_trend_curve as T7  # noqa: E402  (read-only)

Z = T7.Z
DATA = REPO / "data"
SPEC = REPO / "docs" / "decisions" / "D752-STAGE-0-PRE-REG-the-ym-open-reversal-fade.md"
OUT = REPO / "data" / "stage0_d752_ym_open_fade.json"
D727_OUT = REPO / "data" / "stage0_d727_trend_curve.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
CLOCK = 90                                   # minutes after 09:30: 11:00
J = T7.CLOCKS.index(CLOCK)
K_TRIG = 1.0
TICK = 1.0                                   # YM tick, points
BRACKETS = {"B1": (1.0, 1.0), "B2": (0.5, 1.0)}   # (target multiple of m, stop multiple of m)
ALPHA, T_MIN, SKEW_MIN, G3_FLOOR = 0.05, 2.0, -0.5, 209.0
KA = {"beta_1100": -0.04741883341788299, "days": 1938, "fc_k1_trades": 1450, "fc_k1_gross": -3.8420689655172415,
      "pc_1100_k1_trades": 790, "pc_1100_k1_gross": -2.658860759493671}


class D752Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D752Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ the bracket
def resolve(side: int, P: float, m: float, hi: np.ndarray, lo: np.ndarray, close_last: float,
            a: float, b: float) -> tuple[float, str]:
    """Exit price and how, scanning minutes in order. Stop first within a bar; target only through a tick."""
    tgt = P + side * a * m                   # in the trade's favour: toward the open for a fade (side = -sign(x))
    stp = P - side * b * m
    for h, l in zip(hi, lo):
        if not (np.isfinite(h) and np.isfinite(l)):
            continue
        stop_hit = (l <= stp) if side == 1 else (h >= stp)
        if stop_hit:
            return stp - side * TICK, "stop"
        tgt_hit = (h >= tgt + TICK) if side == 1 else (l <= tgt - TICK)
        if tgt_hit:
            return tgt, "target"
    return close_last, "time"


# ================================================================================ statistics
def dist(net: np.ndarray, gross: np.ndarray, days: np.ndarray, how: list[str] | None) -> dict[str, Any]:
    n = len(net)
    sd = float(net.std(ddof=1))
    mu = float(net.mean())
    q1, q99 = np.quantile(net, [0.01, 0.99])
    wins, losses = net[net > 0], net[net < 0]
    m3 = float(np.mean((net - mu) ** 3)) / float(net.std()) ** 3
    m4 = float(np.mean((net - mu) ** 4)) / float(net.std()) ** 4 - 3.0
    yrs = np.array([d[:4] for d in days])
    by = {y: float(net[yrs == y].sum()) for y in np.unique(yrs)}
    best2 = sorted(by, key=lambda y: by[y], reverse=True)[:2]
    ex2 = sum(v for y, v in by.items() if y not in best2)
    ny = len(by)
    out = {"trades": n, "net_mean": mu, "net_t": mu / (sd / math.sqrt(n)), "net_median": float(np.median(net)),
           "gross_mean": float(gross.mean()), "gross_median": float(np.median(gross)), "win_rate": float(np.mean(net > 0)),
           "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) else None,
           "skew": m3, "excess_kurtosis": m4, "worst": float(net.min()), "best": float(net.max()),
           "trim_ex_top": float(net[net <= q99].mean()), "trim_ex_bottom": float(net[net >= q1].mean()),
           "trim_both": float(net[(net >= q1) & (net <= q99)].mean()), "breakeven_cost_rt": float(gross.mean()),
           "net_by_year": by, "years_positive": int(sum(v > 0 for v in by.values())), "years": ny,
           "best_two": best2, "ex2_total": ex2, "ex2_per_year": ex2 / max(ny - 2, 1),
           "G1": ex2 > 0, "G2": sum(v > 0 for v in by.values()) >= math.ceil(2 * ny / 3), "G3": ex2 / max(ny - 2, 1) >= G3_FLOOR}
    if how is not None:
        hw = pd.Series(how).value_counts(normalize=True)
        out["exit_shares"] = {k: float(v) for k, v in hw.items()}
    return out


def rotation(side: np.ndarray, gl: np.ndarray, gs: np.ndarray) -> dict[str, Any]:
    n = len(side)
    obs = float(np.where(side > 0, gl, gs).mean())
    vals = np.array([np.where(np.roll(side, k) > 0, gl, gs).mean() for k in range(n)])
    need(vals[0] == obs, "rotation: offset 0 is not the observed")
    return {"observed_gross_mean": obs, "offsets": n, "p_high": float(np.mean(vals >= obs)),
            "p50": float(np.percentile(vals, 50)), "p95": float(np.percentile(vals, 95)), "_vals": vals}


def rotation_loop(side: np.ndarray, gl: np.ndarray, gs: np.ndarray, ks: list[int]) -> list[float]:
    n = len(side)
    return [sum(gl[i] if side[(i - k) % n] > 0 else gs[i] for i in range(n)) / n for k in ks]


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=lambda k: ps[k])
    out, run = {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, ps[k] * (len(ps) - i)))
        out[k] = run
    return out


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    d727 = json.loads(D727_OUT.read_text(encoding="utf-8"))["roots"]["YM"]
    cost, upp = float(d727["cost_usd"]), float(d727["usd_per_point"])
    pn = T7.load_root("YM", DATA)
    ob = T7.objects(pn)
    days = pn["days"]
    Z.no_session_after(days, "the YM panel")
    # the known answer
    bn = T7.beta_nw(ob["x"][:, J], ob["y"][:, J])
    need(len(days) == KA["days"] and abs(bn["beta"] - KA["beta_1100"]) <= 1e-12, f"known answer: beta {bn['beta']}, days {len(days)}")
    hit = np.abs(ob["z"]) >= K_TRIG
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
    rows = np.arange(len(days))
    side_fc = np.where(first >= 0, np.sign(ob["z"][rows, np.clip(first, 0, None)]), 0.0)
    entry_fc = np.where(first >= 0, ob["Pt"][rows, np.clip(first, 0, None)], np.nan)
    fc = T7.money_book(side_fc, entry_fc, ob["close"], upp, cost, days)
    need(fc["trades"] == KA["fc_k1_trades"] and abs(fc["mean_gross"] - KA["fc_k1_gross"]) <= 1e-9, f"known answer: D727 k1 book {fc['trades']} {fc['mean_gross']}")
    zj = ob["z"][:, J]
    follow = np.where(np.abs(zj) >= K_TRIG, np.sign(zj), 0.0)
    pc = T7.money_book(follow, ob["Pt"][:, J], ob["close"], upp, cost, days)
    need(pc["trades"] == KA["pc_1100_k1_trades"] and abs(pc["mean_gross"] - KA["pc_1100_k1_gross"]) <= 1e-9, "known answer: D727 per_clock 11:00 k1")
    # lag: D727's audit at this clock, and its canary
    rng = np.random.default_rng(752)
    sample = [(int(rng.integers(0, len(days))), J) for _ in range(40)]
    T7.lag_audit(pn, ob, sample)
    try:
        T7.lag_audit(pn, ob, sample, shift=1)
        need(False, "the lag canary (11:00's close) did not fire")
    except T7.D727Error:
        pass

    # minute highs/lows aligned to the panel
    mins = [T7.hhmm(m) for m in range(T7.NMIN)]
    raw = pn["raw"]
    H = raw.pivot(index="day", columns="hhmm", values="high").reindex(index=days, columns=mins).to_numpy(float)
    L = raw.pivot(index="day", columns="hhmm", values="low").reindex(index=days, columns=mins).to_numpy(float)
    trig = np.flatnonzero(np.abs(zj) >= K_TRIG)
    P = ob["Pt"][trig, J]
    O = pn["O"][trig]
    x = ob["x"][trig, J]
    side = -np.sign(x).astype(int)
    need(np.all(side != 0), "a triggered session with x = 0")
    m = np.abs(P - O)
    last = ob["close"][trig]
    tdays = days[trig]

    cells: dict[str, Any] = {}
    gl_all, gs_all = {}, {}
    for name, (a, b) in BRACKETS.items():
        res = {s: [resolve(s, P[i], m[i], H[trig[i], CLOCK:T7.NMIN - 1], L[trig[i], CLOCK:T7.NMIN - 1], last[i], a, b)
                   for i in range(len(trig))] for s in (1, -1)}
        gl = np.array([(e - P[i]) * upp for i, (e, _) in enumerate(res[1])])
        gs = np.array([(P[i] - e) * upp for i, (e, _) in enumerate(res[-1])])
        gross = np.where(side > 0, gl, gs)
        how = [res[side[i]][i][1] for i in range(len(trig))]
        net = gross - cost
        c = dist(net, gross, tdays, how)
        rot = rotation(side, gl, gs)
        ks = list(range(0, len(side), max(1, len(side) // 50)))[:50]
        need(all(math.isclose(u, v, rel_tol=1e-12, abs_tol=1e-12) for u, v in
                 zip(rotation_loop(side, gl, gs, ks), [float(np.where(np.roll(side, k) > 0, gl, gs).mean()) for k in ks])),
             "rotation: vector != loop")
        c["rotation"] = {k: v for k, v in rot.items() if not k.startswith("_")}
        daily = pd.Series(0.0, index=days)
        daily.loc[tdays] = net
        c["net_sharpe"], c["net_sortino"], c["max_dd"] = Z.sharpe(daily.to_numpy()), Z.sortino(daily.to_numpy()), Z.max_dd(daily.to_numpy())
        gd = pd.Series(0.0, index=days)
        gd.loc[tdays] = gross
        c["gross_sharpe"], c["gross_sortino"] = Z.sharpe(gd.to_numpy()), Z.sortino(gd.to_numpy())
        cells[name] = c
        gl_all[name], gs_all[name] = gl, gs
    # E0: held to 15:59, no bracket (the mirror of D727's per_clock 11:00 k1 book)
    g0 = side * (last - P) * upp
    e0 = dist(g0 - cost, g0, tdays, None)
    need(abs(e0["gross_mean"] + KA["pc_1100_k1_gross"]) <= 1e-9, "E0 is not the mirror of D727's 11:00 k1 book")
    e0["rotation"] = {k: v for k, v in rotation(side, (last - P) * upp, (P - last) * upp).items() if not k.startswith("_")}
    cells["E0"] = e0

    ph = holm({k: cells[k]["rotation"]["p_high"] for k in BRACKETS})
    readings = {}
    for k in BRACKETS:
        c = cells[k]
        sig = ph[k] <= ALPHA
        n_ok = {"N1": c["net_mean"] > 0 and c["net_t"] >= T_MIN, "N2": c["net_median"] >= 0,
                "N3": c["skew"] >= SKEW_MIN, "N4": bool(c["G1"] and c["G2"] and c["G3"])}
        reading = ("GO" if sig and all(n_ok.values()) else
                   "SIGNAL ONLY: " + ", ".join(n for n, v in n_ok.items() if not v) if sig else "NOTHING")
        readings[k] = {"p_holm": ph[k], "SIGNAL": sig, **n_ok, "reading": reading}

    # the component line: correlation with D737, F2, C1 (in-sample calendars), co-trading with D737
    bk = pd.read_csv(BOOKS, dtype={"book": str, "session": str, "net": float}, encoding="utf-8")
    comp = {}
    for name in BRACKETS:
        daily = pd.Series(0.0, index=days)
        daily.loc[tdays] = np.where(side > 0, gl_all[name], gs_all[name]) - cost
        cr = {}
        for b_, g in bk.groupby("book"):
            s = g.groupby("session")["net"].sum().reindex(days, fill_value=0.0)
            cr[b_] = float(np.corrcoef(daily.to_numpy(), s.to_numpy())[0, 1])
        comp[name] = cr
    d737 = set(bk.loc[bk.book == "D737", "session"])
    co = float(np.mean([d in d737 for d in tdays]))

    res = {"record": "D752 (7af83e82)", "readings": readings, "cells": cells, "component_rho": comp,
           "share_of_fade_sessions_d737_trades": co, "triggered_sessions": int(len(trig)), "panel_sessions": int(len(days)),
           "window": [str(days[0]), str(days[-1])], "cost_usd": cost, "known_answer": KA,
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(T7_strip(res), fh, indent=1)
        fh.write("\n")
    show(res)
    return 0


def T7_strip(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): T7_strip(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [T7_strip(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def show(res: dict) -> None:
    print(f"[D752] {res['triggered_sessions']} triggered of {res['panel_sessions']} sessions {res['window']}; "
          f"D737 trades on {res['share_of_fade_sessions_d737_trades']:.2f} of them")
    for k, r in res["readings"].items():
        print(f"  {k}: {r['reading']}  p_holm {r['p_holm']:.4f}  {({n: r[n] for n in ('N1', 'N2', 'N3', 'N4')})}")
    for k, c in res["cells"].items():
        rot = c["rotation"]
        print(f"  {k}: gross {c['gross_mean']:6.2f} (med {c['gross_median']:6.2f})  net {c['net_mean']:6.2f} t {c['net_t']:5.2f} "
              f"med {c['net_median']:6.2f}  win {c['win_rate']:.3f} payoff {c['payoff']}  skew {c['skew']:5.2f} kurt {c['excess_kurtosis']:5.1f}  "
              f"worst {c['worst']:7.2f}  trims {c['trim_ex_top']:.2f}/{c['trim_ex_bottom']:.2f}/{c['trim_both']:.2f}  "
              f"yrs+ {c['years_positive']}/{c['years']}  G {c['G1']},{c['G2']},{c['G3']}  rot p {rot['p_high']:.3f} p50 {rot['p50']:.2f} p95 {rot['p95']:.2f}  "
              f"{c.get('exit_shares', '')}  Sharpe {c.get('net_sharpe')} Sortino {c.get('net_sortino')}")
    print(f"  rho: {res['component_rho']}")
    print(f"[D752] wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    nan = np.nan
    P, m = 100.0, 10.0
    # short (side -1) after a rise: target 90 (B1), stop 110
    ex, how = resolve(-1, P, m, np.array([101, 102, 95, 92]), np.array([99, 98, 91, 88]), 97.0, 1.0, 1.0)
    if not (how == "target" and ex == 90.0):
        fails.append(f"target-first short: {ex} {how}")
    ex, how = resolve(-1, P, m, np.array([105, 111]), np.array([99, 104]), 97.0, 1.0, 1.0)
    if not (how == "stop" and ex == 111.0):
        fails.append(f"stop short fills at stop + tick: {ex} {how}")
    ex, how = resolve(-1, P, m, np.array([112]), np.array([88]), 97.0, 1.0, 1.0)
    if how != "stop":
        fails.append("same bar: the stop is not assumed first")
    ex, how = resolve(-1, P, m, np.array([101, 102]), np.array([90, 95]), 97.0, 1.0, 1.0)
    if how != "time" or ex != 97.0:
        fails.append(f"a target touched but not traded through filled: {ex} {how}")
    ex, how = resolve(1, P, m, np.array([nan, 111.5]), np.array([nan, 101]), 97.0, 1.0, 1.0)
    if not (how == "target" and ex == 110.0):
        fails.append(f"long target / NaN minute: {ex} {how}")
    ex, how = resolve(1, P, m, np.array([101]), np.array([94]), 97.0, 0.5, 1.0)
    if how != "time":
        fails.append("B2 long: a 6-point dip should not stop at 1.0 m")
    ex, how = resolve(1, P, m, np.array([106.0]), np.array([99.0]), 97.0, 0.5, 1.0)
    if not (how == "target" and ex == 105.0):
        fails.append(f"B2 long target at 0.5 m: {ex} {how}")
    # sign in money: the short after a rise pays when the price falls back
    if not ((P - 90.0) * 0.5 > 0):
        fails.append("sign in money")
    # rotation: offset 0, planted perfect side, vector == loop
    rng = np.random.default_rng(752)
    n = 300
    mv = rng.normal(0, 10, n)
    gl, gs = mv.copy(), -mv
    perfect = np.where(mv >= 0, 1, -1)
    r = rotation(perfect, gl, gs)
    if not r["p_high"] < 0.01:
        fails.append(f"planted perfect side p {r['p_high']}")
    rand = np.where(rng.random(n) < 0.5, 1, -1)
    ks = list(range(0, n, 6))[:50]
    if not all(math.isclose(u, v, rel_tol=1e-12, abs_tol=1e-12) for u, v in
               zip(rotation_loop(rand, gl, gs, ks), [float(np.where(np.roll(rand, k) > 0, gl, gs).mean()) for k in ks])):
        fails.append("rotation vector != loop")
    if holm({"a": 0.01, "b": 0.04}) != {"a": 0.02, "b": 0.04}:
        fails.append(f"holm {holm({'a': 0.01, 'b': 0.04})}")
    try:
        Z.no_session_after(np.array(["2023-12-29", "2024-01-02"]), "planted")
        fails.append("the seal did not raise")
    except Exception:
        pass
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D752Error:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D752] selftest: {'FAIL' if fails else 'all passed'}")
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
