"""D733 Stage 0: the pullback entry in an NQ trend. Spec: docs/decisions/D733-STAGE-0-PRE-REG-the-nq-pullback-entry.md,
committed before this file existed.

    uv run python scripts/stage0_d733_pullback_entry.py --selftest
    uv run python scripts/stage0_d733_pullback_entry.py --run --data-root <checkout>/data      # once

NQ one-minute day-session bars, D727's days / sigma_oc (its functions). Everything runs in "u-space": prices multiplied
by the day's locked direction D, so the logic is long-only and a trade's gross is (exit_u - entry_u) x $2. Bar m starts
09:30 + m; the price at minute m is the close of bar m - 1. Nothing dated 2024-01-01 or later is used.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T  # noqa: E402
import stage0_d731_flat_u as F  # noqa: E402

OUT = REPO / "data" / "stage0_d733_pullback_entry.json"
NMIN, TICK, USD, ARM_LO, ARM_HI, DEADLINE = 390, 0.25, 2.0, 30, 270, 330
KARM, VOID, FLOOR = 1.0, 0.8, 0.15
RMINS, TRIGS = (0.25, 0.5), ("a", "b", "c")
PRIMARY = (0.25, "b")
XBINS = ((0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, np.inf))
EDGE = T.EDGE
P = Z.P


class D733Error(AssertionError):
    pass


# ================================================================================ panels
def panels(pn: dict[str, Any]) -> dict[str, np.ndarray]:
    raw = pn["raw"]
    mins = [T.hhmm(m) for m in range(NMIN)]
    piv = {c: raw.pivot(index="day", columns="hhmm", values=c).reindex(index=pn["days"], columns=mins).to_numpy(float)
           for c in ("open", "high", "low")}
    C = pn["C"]
    prevc = np.column_stack([pn["O"], C[:, :-1]])
    Op = np.where(np.isfinite(piv["open"]), piv["open"], prevc)
    H = np.where(np.isfinite(piv["high"]), piv["high"], np.maximum(Op, C))
    L = np.where(np.isfinite(piv["low"]), piv["low"], np.minimum(Op, C))
    return {"Op": Op, "H": H, "L": L, "C": C, "O": pn["O"], "soc": pn["soc"]}


def arm(pp: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """(m0, D) per day: the first minute in 10:00-14:00 with |z| >= 1.0; m0 = -1 if never armed."""
    C, O, s = pp["C"], pp["O"], pp["soc"]
    ms = np.arange(ARM_LO, ARM_HI + 1)
    Pm = C[:, ms - 1]
    z = (Pm - O[:, None]) / (s[:, None] * np.sqrt(ms / NMIN)[None, :])
    hit = np.abs(z) >= KARM
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
    m0 = np.where(first >= 0, ms[np.clip(first, 0, None)], -1)
    D = np.where(first >= 0, np.sign(z[np.arange(len(O)), np.clip(first, 0, None)]), 0.0)
    return m0, D


def uspace(pp: dict[str, np.ndarray], d: int, D: float) -> dict[str, np.ndarray]:
    if D > 0:
        return {"op": pp["Op"][d], "hi": pp["H"][d], "lo": pp["L"][d], "c": pp["C"][d], "O": pp["O"][d]}
    return {"op": -pp["Op"][d], "hi": -pp["L"][d], "lo": -pp["H"][d], "c": -pp["C"][d], "O": -pp["O"][d]}


# ================================================================================ exits
def exit_e1(u: dict[str, np.ndarray], e: int, entry: float, stop: float, from_bar: int) -> tuple[float, bool, int]:
    """(exit price, stopped, exit bar). Stop checked on bars >= from_bar; open beyond the stop fills at the open."""
    for b in range(from_bar, NMIN):
        if u["op"][b] <= stop:
            return u["op"][b] - TICK, True, b
        if u["lo"][b] <= stop:
            return stop - TICK, True, b
    return u["c"][NMIN - 1], False, NMIN - 1


def exit_target(u: dict[str, np.ndarray], entry: float, stop: float, target: float, from_bar: int,
                time_bar: int | None = None) -> float:
    last = NMIN - 1 if time_bar is None else min(time_bar, NMIN - 1)
    for b in range(from_bar, last + 1):
        if u["op"][b] <= stop:
            return u["op"][b] - TICK
        if u["lo"][b] <= stop:
            return stop - TICK
        if u["op"][b] >= target:
            return u["op"][b]
        if u["hi"][b] >= target:
            return target
    return u["c"][last]


# ================================================================================ the day state machine
def simulate_day(u: dict[str, np.ndarray], m0: int, soc: float, rmin: float, trig: str, max_trades: int = 1,
                 wide: bool = False) -> list[dict[str, Any]]:
    O = u["O"]
    hi, lo, c, op = u["hi"], u["lo"], u["c"], u["op"]
    X = float(np.max(hi[:m0]))
    xbar = int(np.argmax(hi[:m0]))
    Lpb = float(np.min(lo[xbar + 1:m0])) if m0 > xbar + 1 else math.inf
    qualified = False
    trades: list[dict[str, Any]] = []
    b = m0
    while b <= DEADLINE and len(trades) < max_trades:
        A = X - O
        Pb = c[b - 1]
        if A <= 0 or Pb <= O or (X - Pb) / A > VOID:
            return trades                                     # void for the day
        if (X - Pb) / A >= rmin and (X - Pb) >= FLOOR * soc:
            qualified = True
        entry = None
        if trig == "a":
            lim = X - rmin * A
            if rmin * A >= FLOOR * soc and lo[b] <= lim:
                entry, fill_bar = (lim if op[b] > lim else op[b]), b
                stop = X - VOID * A - TICK
                from_bar = b
        elif trig == "b":
            if qualified and b % 5 == 0 and b >= 10 and math.isfinite(Lpb):
                if c[b - 1] > np.max(hi[b - 10:b - 5]):
                    entry, fill_bar, from_bar = op[b], b, b + 1
                    stop = Lpb - TICK - (0.1 * soc if wide else 0.0)
        elif trig == "c":
            if qualified and math.isfinite(Lpb) and c[b - 1] >= Lpb + 0.25 * (X - Lpb):
                entry, fill_bar, from_bar = op[b], b, b + 1
                stop = Lpb - TICK - (0.1 * soc if wide else 0.0)
        if entry is not None and entry > stop:
            ex, stopped, xb = exit_e1(u, fill_bar, entry, stop, from_bar)
            R = entry - stop
            t = {"e": int(fill_bar), "entry": float(entry), "stop": float(stop), "X": float(X), "Lpb": float(Lpb),
                 "exit": float(ex), "stopped": bool(stopped), "exit_bar": int(xb), "R": float(R),
                 "x_entry": float((entry - O) / soc), "depth_sigma": float((X - min(Lpb, entry)) / soc),
                 "since_x": int(fill_bar - xbar)}
            trades.append(t)
            if not stopped or max_trades == 1:
                return trades
            # re-entry only once flat: resume after the stop bar with the state rebuilt from the bars to it
            nb = xb + 1
            X = float(np.max(hi[:nb]))
            xbar = int(np.argmax(hi[:nb]))
            Lpb = float(np.min(lo[xbar + 1:nb])) if nb > xbar + 1 else math.inf
            qualified = False
            b = nb
            continue
        if hi[b] > X:
            X, xbar, Lpb, qualified = float(hi[b]), b, math.inf, False
        else:
            Lpb = min(Lpb, float(lo[b]))
        b += 1
    return trades


def trigger_audit(u: dict[str, np.ndarray], m0: int, soc: float, rmin: float, trig: str, t: dict[str, Any],
                  lead: int = 0) -> None:
    """Second implementation from bars truncated at the entry minute e (lead = 1 lets the pullback low read bar e:
    the canary). Checks the stop and the trigger condition at e."""
    e = t["e"]
    hi, lo, c, O = u["hi"], u["lo"], u["c"], u["O"]
    X = float(np.max(hi[:e]))
    xbar = int(np.argmax(hi[:e]))
    A = X - O
    if trig in ("b", "c"):
        want_entry = u["op"][e] if lead == 0 else c[e]           # the lead reads the entry bar's own close
        if not math.isclose(want_entry, t["entry"], abs_tol=1e-9):
            raise D733Error("lag: the entry is not the open of the bar after the trigger")
        Lpb = float(np.min(lo[xbar + 1:e + lead])) if e + lead > xbar + 1 else math.inf
        q = [qq for qq in range(max(xbar + 1, m0), e + 1) if (X - c[qq - 1]) / A >= rmin and (X - c[qq - 1]) >= FLOOR * soc]
        if not q:
            raise D733Error("lag: the trade was never qualified on bars before e")
        if not math.isclose(Lpb - TICK, t["stop"], abs_tol=1e-9):
            raise D733Error("lag: the stop is not the pullback low of bars before e")
        if trig == "b" and not (e % 5 == 0 and c[e - 1] > np.max(hi[e - 10:e - 5])):
            raise D733Error("lag: the 5-minute turn does not hold on bars before e")
        if trig == "c" and not c[e - 1] >= Lpb + 0.25 * (X - Lpb):
            raise D733Error("lag: the bounce does not hold on bars before e")
    else:
        if not (lo[e] <= X - rmin * A + 1e-9):
            raise D733Error("lag: the limit was not reached on its fill bar")


# ================================================================================ the null (vectorised per offset)
def placebo_mean(U: dict[str, np.ndarray], m0: np.ndarray, soc: np.ndarray, Odays: np.ndarray, src_day: np.ndarray,
                 e: np.ndarray, sd: np.ndarray, j: int, cost: float, bins_out: bool = False) -> Any:
    n = len(m0)
    tgt = (src_day + j) % n
    ok = (m0[tgt] >= 0) & (m0[tgt] <= e)
    if not ok.any():
        return (float("nan"), {}) if bins_out else float("nan")
    tg, ee, sdd = tgt[ok], e[ok], sd[ok]
    entry = U["op"][tg, ee]
    stop = entry - sdd * soc[tg]
    lo, op = U["lo"][tg], U["op"][tg]
    bars = np.arange(NMIN)[None, :]
    after = bars >= (ee + 1)[:, None]
    hit = after & (lo <= stop[:, None])
    anyh = hit.any(axis=1)
    fb = hit.argmax(axis=1)
    rows = np.arange(len(tg))
    opf = op[rows, fb]
    ex = np.where(anyh, np.where(opf <= stop, opf - TICK, stop - TICK), U["c"][tg, NMIN - 1])
    net = (ex - entry) * USD - cost
    if not bins_out:
        return float(net.mean())
    x = np.abs((entry - Odays[tg]) / soc[tg])
    out = {}
    for k, (a, bb) in enumerate(XBINS):
        m = (x >= a) & (x < bb)
        out[k] = float(net[m].mean()) if m.sum() >= 1 else float("nan")
    return float(net.mean()), out


def rot(obs: float, null: np.ndarray) -> dict[str, float]:
    a = null[np.isfinite(null)]
    return {"observed": obs, "offsets": int(len(a)), "p05": float(np.quantile(a, 0.05)), "p50": float(np.median(a)),
            "p95": float(np.quantile(a, 0.95)), "p95_se": 0.0, "rank": float((a < obs).mean()),
            "p_high": float((a >= obs).mean())}


def nw_t(x: np.ndarray, lags: int = 5) -> float:
    x = np.asarray(x, float)
    n = len(x)
    if n < 10:
        return float("nan")
    e = x - x.mean()
    S = float((e * e).sum())
    for L in range(1, lags + 1):
        S += 2 * (1 - L / (lags + 1)) * float((e[L:] * e[:-L]).sum())
    se = math.sqrt(max(S, 0.0)) / n
    return float(x.mean() / se) if se > 0 else float("nan")


# ================================================================================ the run
def run(data_root: Path) -> int:
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cost = float(M711.cost_line("NQ")["cost"])
    pn = T.load_root("NQ", data_root)
    ob = T.objects(pn)
    ka = json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8"))["roots"]["NQ"]
    if len(pn["days"]) != ka["days"] or not math.isclose(T.beta_nw(ob["x"][:, 0], ob["y"][:, 0])["beta"],
                                                         ka["clocks"][0]["beta"], rel_tol=0, abs_tol=1e-12):
        raise D733Error("NQ's objects are not D727's")
    pp = panels(pn)
    days, n = pn["days"], len(pn["days"])
    m0, D = arm(pp)
    soc, O = pp["soc"], pp["O"]
    U = {k: np.full((n, NMIN), np.nan) for k in ("op", "hi", "lo", "c")}
    Ou = np.full(n, np.nan)
    us = {}
    for d in range(n):
        if m0[d] < 0:
            continue
        u = uspace(pp, d, D[d])
        us[d] = u
        for k in U:
            U[k][d] = u[k]
        Ou[d] = u["O"]
    P(f"[D733] {n} days, armed {int((m0 >= 0).sum())}")
    cells: dict[str, Any] = {}
    trades: dict[tuple, list] = {}
    rng = np.random.default_rng(733)
    for rmin in RMINS:
        for trig in TRIGS:
            rows = []
            for d, u in us.items():
                tl = simulate_day(u, int(m0[d]), float(soc[d]), rmin, trig)
                if tl:
                    rows.append((d, tl[0]))
            trades[(rmin, trig)] = rows
            smp = [rows[i] for i in rng.choice(len(rows), min(60, len(rows)), replace=False)] if rows else []
            for d, t in smp:
                trigger_audit(us[d], int(m0[d]), float(soc[d]), rmin, trig, t)
            if trig in ("b", "c"):
                fired = False
                for d, t in smp:
                    try:
                        trigger_audit(us[d], int(m0[d]), float(soc[d]), rmin, trig, t, lead=1)
                    except D733Error:
                        fired = True
                        break
                if not fired:
                    raise D733Error(f"({rmin},{trig}): the one-bar-lead canary did not fire")
    P(f"[D733] trades per cell: { {f'{k[0]}{k[1]}': len(v) for k, v in trades.items()} }")
    # ---- per-cell books and the timing null
    null_by_cell = {}
    for (rmin, trig), rows in trades.items():
        key = f"r{rmin}_{trig}"
        dd = np.array([d for d, _ in rows], int)
        g = np.array([(t["exit"] - t["entry"]) * USD for _, t in rows])
        net = g - cost
        gfull = np.full(n, np.nan)
        gfull[dd] = g
        bk, daily = F.book(np.where(np.isfinite(gfull), 1.0, 0.0), gfull, cost, days)
        e = np.array([t["e"] for _, t in rows], int)
        sd = np.array([(t["entry"] - t["stop"]) / soc[d] for d, t in rows])
        xs = np.abs(np.array([t["x_entry"] for _, t in rows]))
        if trig in ("b", "c") and len(rows):
            p0 = placebo_mean(U, m0, soc, Ou, dd, e, sd, 0, cost)
            if not math.isclose(p0, float(net.mean()), rel_tol=0, abs_tol=1e-9):
                raise D733Error(f"{key}: C2's offset 0 does not reproduce the observed trades ({p0} vs {net.mean()})")
        offs = range(EDGE, n - EDGE)
        pooled, binned = [], {k: [] for k in range(len(XBINS))}
        for j in offs:
            mu, bm = placebo_mean(U, m0, soc, Ou, dd, e, sd, j, cost, bins_out=True)
            pooled.append(mu)
            for k in binned:
                binned[k].append(bm.get(k, np.nan))
        pooled = np.array(pooled)
        null_by_cell[key] = pooled
        obs_bins = {}
        for k, (a, b_) in enumerate(XBINS):
            m = (xs >= a) & (xs < b_)
            obs_bins[k] = {"trades": int(m.sum()), "mean_net": float(net[m].mean()) if m.any() else None}
            if m.sum() >= 30:
                obs_bins[k]["rotation"] = rot(float(net[m].mean()), np.array(binned[k]))
        stopped = np.array([t["stopped"] for _, t in rows])
        cells[key] = {"trades": len(rows), "book": bk, "mean_net": float(net.mean()) if len(rows) else None,
                      "nw_t_net": nw_t(net), "C2_pooled": rot(float(net.mean()), pooled), "C2_by_abs_x": obs_bins,
                      "stopped_share": float(stopped.mean()) if len(rows) else None,
                      "entry_hour_counts": pd.Series([T.hhmm(t["e"])[:2] for _, t in rows]).value_counts().sort_index().to_dict()}
        cells[key]["_daily"] = daily
    fam = np.max(np.column_stack(list(null_by_cell.values())), axis=1)
    pkey = f"r{PRIMARY[0]}_{PRIMARY[1]}"
    holm_in = {k: cells[k]["C2_pooled"]["p_high"] for k in cells}
    order = sorted(holm_in, key=holm_in.get)
    holm, run_ = {}, 0.0
    for i, k in enumerate(order):
        run_ = max(run_, min(1.0, holm_in[k] * (len(order) - i)))
        holm[k] = run_
    for k in cells:
        cells[k]["holm_p"] = holm[k]
    out: dict[str, Any] = {"spec": "D733-STAGE-0-PRE-REG-the-nq-pullback-entry.md", "seal": f"nothing on or after {Z.CUT24}",
                           "days": n, "armed": int((m0 >= 0).sum()), "cost": cost, "cells": cells,
                           "family_p95": float(np.quantile(fam[np.isfinite(fam)], 0.95))}
    # ---- primary-cell extras
    prow = trades[PRIMARY]
    pd_ = np.array([d for d, _ in prow], int)
    pg = np.array([(t["exit"] - t["entry"]) * USD for _, t in prow])
    # C1: the same-day follow from arming
    fol = np.array([(us[d]["c"][NMIN - 1] - us[d]["c"][m0[d] - 1]) * USD for d, _ in prow])
    price_gain = np.array([(us[d]["c"][m0[d] - 1] - t["entry"]) * USD for d, t in prow])
    stop_eff = np.array([(t["exit"] - us[d]["c"][NMIN - 1]) * USD for d, t in prow])
    diff = pg - fol
    out["C1_same_day_follow"] = {"mean_follow_gross": float(fol.mean()), "mean_trade_gross": float(pg.mean()),
                                 "mean_diff": float(diff.mean()), "t_diff": float(diff.mean() / (diff.std(ddof=1) / math.sqrt(len(diff)))),
                                 "decomp_entry_price_gain": float(price_gain.mean()), "decomp_stop_effect": float(stop_eff.mean())}
    # C3: turn vs limit at r 0.25
    ta = {d: t for d, t in trades[(0.25, "a")]}
    pair = [((t["exit"] - t["entry"]) - (ta[d]["exit"] - ta[d]["entry"])) * USD for d, t in prow if d in ta]
    pair = np.array(pair)
    out["C3_turn_vs_limit"] = {"days": int(len(pair)), "mean_b_minus_a": float(pair.mean()) if len(pair) else None,
                               "t": float(pair.mean() / (pair.std(ddof=1) / math.sqrt(len(pair)))) if len(pair) > 2 else None}
    out["C3_turn_vs_limit"]["TURN_PAYS"] = bool((out["C3_turn_vs_limit"]["t"] or 0) >= 2)
    # the mirror: the same entry and stop distance, against D
    mir = []
    for d, t in prow:
        u = us[d]
        mu = {"op": -u["op"], "hi": -u["lo"], "lo": -u["hi"], "c": -u["c"], "O": -u["O"]}
        ent = -t["entry"]
        ex, _, _ = exit_e1(mu, t["e"], ent, ent - t["R"], t["e"] + 1)
        mir.append((ex - ent) * USD - cost)
    out["mirror_mean_net"] = float(np.mean(mir))
    # reported exits from the same entries
    rep = {"1R": [], "2R": [], "retest_X": [], "60min": [], "unstopped_close": [], "wide_stop_E1": []}
    mfe_mae = {h: [] for h in ("15", "30", "60", "close")}
    for d, t in prow:
        u, e_, ent, st = us[d], t["e"], t["entry"], t["stop"]
        rep["1R"].append((exit_target(u, ent, st, ent + t["R"], e_ + 1) - ent) * USD - cost)
        rep["2R"].append((exit_target(u, ent, st, ent + 2 * t["R"], e_ + 1) - ent) * USD - cost)
        rep["retest_X"].append((exit_target(u, ent, st, t["X"], e_ + 1) - ent) * USD - cost)
        rep["60min"].append((exit_target(u, ent, st, math.inf, e_ + 1, e_ + 59) - ent) * USD - cost)
        rep["unstopped_close"].append((u["c"][NMIN - 1] - ent) * USD - cost)
        tw = simulate_day(u, int(m0[d]), float(soc[d]), PRIMARY[0], PRIMARY[1], wide=True)
        if tw:
            rep["wide_stop_E1"].append((tw[0]["exit"] - tw[0]["entry"]) * USD - cost)
        for h, hb in (("15", 15), ("30", 30), ("60", 60), ("close", None)):
            last = NMIN - 1 if hb is None else min(e_ + hb - 1, NMIN - 1)
            mfe_mae[h].append(((np.max(u["hi"][e_:last + 1]) - ent) * USD, (np.min(u["lo"][e_:last + 1]) - ent) * USD))
    out["primary_reported_exits"] = {k: {"trades": len(v), "mean_net": float(np.mean(v)) if v else None,
                                         "win": float(np.mean(np.array(v) > 0)) if v else None} for k, v in rep.items()}
    out["primary_mfe_mae"] = {h: {"mean_mfe": float(np.mean([a for a, _ in v])), "mean_mae": float(np.mean([b for _, b in v]))}
                              for h, v in mfe_mae.items()}
    # splits: pullback speed terciles, up/down days, entry hour
    pnet = pg - cost
    speed = np.array([t["depth_sigma"] / max(t["since_x"], 1) for _, t in prow])
    qs = np.quantile(speed, [1 / 3, 2 / 3])
    out["primary_split_speed"] = {nm: float(pnet[m].mean()) for nm, m in
                                  (("slow", speed <= qs[0]), ("mid", (speed > qs[0]) & (speed <= qs[1])), ("fast", speed > qs[1]))}
    dirs = D[pd_]
    out["primary_split_direction"] = {"up_days": float(pnet[dirs > 0].mean()), "down_days": float(pnet[dirs < 0].mean()),
                                      "n_up": int((dirs > 0).sum()), "n_down": int((dirs < 0).sum())}
    # oracles
    o1 = []
    for d, u in us.items():
        mm = int(m0[d])
        X = float(np.max(u["hi"][:mm]))
        A = X - u["O"]
        q = None
        for b in range(mm, DEADLINE + 1):
            if A > 0 and (X - u["c"][b - 1]) / A >= 0.25 and (X - u["c"][b - 1]) >= FLOOR * soc[d]:
                q = b
                break
            if u["hi"][b] > X:
                X = float(u["hi"][b])
                A = X - u["O"]
        if q is None:
            continue
        nx = np.flatnonzero(u["hi"][q:] > X)
        end = q + (int(nx[0]) if len(nx) else NMIN - q)
        ext = float(np.min(u["lo"][q:end])) if end > q else float(u["c"][q - 1])
        o1.append((u["c"][NMIN - 1] - ext) * USD - cost)
    out["O1_perfect_turn_ceiling"] = {"days": len(o1), "mean_net": float(np.mean(o1)) if o1 else None}
    out["O1_NO_ROOM"] = bool(o1 and np.mean(o1) < 2 * cost)
    st = np.array([t["stopped"] for _, t in prow])
    out["O2"] = {"stopped_share": float(st.mean()), "unstopped_only_mean_net": float(pnet[~st].mean()) if (~st).any() else None,
                 "stopped_mean_net": float(pnet[st].mean()) if st.any() else None}
    clocks = np.array([T.CLOCKS])[0]
    betas = np.array([c_["beta"] for c_ in ka["clocks"]])
    o3 = []
    for d, t in prow:
        bj = int(np.argmin(np.abs(clocks - t["e"])))
        o3.append(betas[bj] * t["x_entry"] * soc[d] * USD)
    out["O3_clock_budget_gross"] = float(np.mean(o3))
    out["O3_paying_for_late_entry"] = bool(np.mean(o3) < 8.0)
    # the multi-entry book (path-variant), primary cell
    multi = []
    for d, u in us.items():
        for t in simulate_day(u, int(m0[d]), float(soc[d]), PRIMARY[0], PRIMARY[1], max_trades=3):
            multi.append((d, (t["exit"] - t["entry"]) * USD))
    md = pd.Series([g for _, g in multi], index=[d for d, _ in multi]).groupby(level=0).sum()
    gm = np.full(n, np.nan)
    gm[md.index.to_numpy(int)] = md.to_numpy()
    cnt = pd.Series([1 for _ in multi], index=[d for d, _ in multi]).groupby(level=0).sum()
    out["primary_multi_entry"] = {"trades": len(multi), "days": int(len(md)),
                                  "mean_net_per_trade": float(np.mean([g - cost for _, g in multi])) if multi else None,
                                  "daily_net_sharpe": Z.sharpe(np.nan_to_num(gm) - np.where(np.isfinite(gm), cnt.reindex(range(n)).fillna(0).to_numpy() * cost, 0)),
                                  "max_per_day": int(cnt.max()) if len(cnt) else 0}
    # matched-row decomposition: E1 from every armed 5-minute row vs the trigger rows, by clock hour x |x| bin
    sdm = float(np.median([(t["entry"] - t["stop"]) / soc[d] for d, t in prow]))
    trig_rows = {(d, t["e"]) for d, t in prow}
    recs = []
    for d, u in us.items():
        for e_ in range(int(m0[d]) + (5 - int(m0[d]) % 5) % 5, DEADLINE + 1, 5):
            ent = u["op"][e_]
            ex, _, _ = exit_e1(u, e_, ent, ent - sdm * soc[d], e_ + 1)
            xb = int(np.digitize(abs((ent - u["O"]) / soc[d]), [0.5, 1.0, 1.5]))
            recs.append((T.hhmm(e_)[:2], xb, (d, e_) in trig_rows, (ex - ent) * USD - cost))
    rd = pd.DataFrame(recs, columns=["hour", "xbin", "trig", "net"])
    cellm = rd.groupby(["hour", "xbin", "trig"])["net"].mean().unstack("trig")
    w = rd[rd["trig"]].groupby(["hour", "xbin"]).size()
    if True in cellm.columns and False in cellm.columns:
        dlt = (cellm[True] - cellm[False]).dropna()
        ww = w.reindex(dlt.index).fillna(0)
        out["matched_row_decomposition"] = {"weighted_trigger_minus_other": float((dlt * ww).sum() / ww.sum()) if ww.sum() else None,
                                            "rows": int(len(rd)), "trigger_rows": int(rd["trig"].sum()),
                                            "stop_sigma_used": sdm}
    # ledger line
    arm_, _ = Z.build_arm()
    f2_, _ = Z.build_f2()
    cal = pd.Index(days)
    arm_d = arm_.groupby("day")["net1"].sum().reindex(cal).fillna(0.0).to_numpy()
    f2_d = f2_.groupby("day")["net1"].sum().reindex(cal).fillna(0.0).to_numpy()
    pdaily = cells[pkey]["_daily"]
    out["ledger_rho_primary"] = {"macd_arm": float(np.corrcoef(pdaily, arm_d)[0, 1]), "nq_f2": float(np.corrcoef(pdaily, f2_d)[0, 1])}
    for k in cells:
        cells[k].pop("_daily", None)
    # readings
    pc = cells[pkey]
    bins_ok = [v for v in pc["C2_by_abs_x"].values() if "rotation" in v]
    nbins_above = sum(v["rotation"]["observed"] > v["rotation"]["p95"] for v in bins_ok)
    c1 = out["C1_same_day_follow"]
    edge = ((pc["mean_net"] or -1) > 0 and (pc["nw_t_net"] or 0) >= 2 and pc["C2_pooled"]["observed"] > pc["C2_pooled"]["p95"]
            and nbins_above >= 3 and c1["mean_diff"] >= 0 and c1["t_diff"] >= 1)
    reading = "EDGE" if edge else ("DRIFT ONLY" if (pc["mean_net"] or -1) > 0 else "NOTHING")
    bk = pc["book"]
    go = (edge and pc["C2_pooled"]["observed"] > out["family_p95"] and bk["net_sharpe"] >= 0.4
          and bk["years_positive"] >= 5 and (bk["largest_year_share"] or 1) < 0.5)
    out["reading"] = ("NO ROOM; " if out["O1_NO_ROOM"] else "") + reading
    out["primary_bins_above_p95"] = int(nbins_above)
    out["GO"] = bool(go)
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=Z._json) + "\n", encoding="utf-8", newline="\n")
    P(f"[D733] {out['reading']}; GO {go}; TURN_PAYS {out['C3_turn_vs_limit']['TURN_PAYS']}; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    # a hand-built long day: up to 100, pull back to 96, turn, rise to 110
    O = 90.0
    path = np.concatenate([np.linspace(90, 100, 60), np.linspace(100, 96, 30), np.linspace(96, 110, 300)])
    c = path.copy()
    op = np.r_[O, c[:-1]]
    u = {"op": op, "hi": np.maximum(op, c) + 0.1, "lo": np.minimum(op, c) - 0.1, "c": c, "O": O}
    tl = simulate_day(u, 40, 5.0, 0.25, "b")
    if not tl:
        fails.append("the hand-built pullback day produced no (b) trade")
    else:
        t = tl[0]
        trigger_audit(u, 40, 5.0, 0.25, "b", t)
        if not (t["exit"] > t["entry"] and not t["stopped"]):
            fails.append("sign: a long after a pullback that rises to the close did not pay")
        try:
            trigger_audit(u, 40, 5.0, 0.25, "b", t, lead=1)
            fails.append("the one-bar-lead canary did not fire")
        except D733Error:
            pass
    # a stop on a gapped open fills at the open
    u2 = {"op": np.array([100.0, 100.0, 95.0, 95.0]), "hi": np.array([100.5, 100.5, 95.5, 95.5]),
          "lo": np.array([99.5, 99.5, 94.5, 94.5]), "c": np.array([100.0, 100.0, 95.0, 95.0]), "O": 99.0}
    global NMIN
    old = NMIN
    NMIN = 4
    try:
        ex, st, _ = exit_e1(u2, 0, 100.0, 98.0, 1)
    finally:
        NMIN = old
    if not (st and math.isclose(ex, 95.0 - TICK)):
        fails.append("a gapped stop did not fill at the open less a tick")
    # the void: a day that retraces past 0.8 has no trade
    path3 = np.concatenate([np.linspace(90, 100, 60), np.linspace(100, 91, 60), np.linspace(91, 110, 270)])
    c3 = path3
    op3 = np.r_[O, c3[:-1]]
    u3 = {"op": op3, "hi": np.maximum(op3, c3) + 0.05, "lo": np.minimum(op3, c3) - 0.05, "c": c3, "O": O}
    if simulate_day(u3, 40, 5.0, 0.25, "b"):
        fails.append("a voided day (retrace > 0.8) produced a trade")
    # the null's offset 0 reproduces a (b) trade (vectorised against the loop)
    if tl:
        U = {k: u[k][None, :] for k in ("op", "hi", "lo", "c")}
        t = tl[0]
        p0 = placebo_mean(U, np.array([40]), np.array([5.0]), np.array([O]), np.array([0]), np.array([t["e"]]),
                          np.array([(t["entry"] - t["stop"]) / 5.0]), 0, 4.07)
        if not math.isclose(p0, (t["exit"] - t["entry"]) * USD - 4.07, abs_tol=1e-9):
            fails.append("the vectorised null at offset 0 does not equal the loop's trade")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: a pullback-and-turn day trades and pays, the lag audit passes and its one-bar-lead canary fires; a "
      "gapped stop fills at the open; a retrace past 0.8 voids the day; the vectorised null equals the loop at offset 0")
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
            raise D733Error(f"{OUT.name} exists: D733 runs once")
        return run(a.data_root)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
