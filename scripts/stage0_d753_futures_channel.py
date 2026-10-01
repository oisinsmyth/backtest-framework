"""D753 Stage 0: the channel level rule carried to daily futures, as pre-registered in
docs/decisions/D753-STAGE-0-PRE-REG-the-channel-level-rule-on-daily-futures.md (e9748192) with A1 (b01254fb).

    uv run --no-sync python scripts/stage0_d753_futures_channel.py --selftest
    uv run --no-sync python scripts/stage0_d753_futures_channel.py --run       # once; writes data/stage0_d753_futures_channel.json

THE LINES are the principal's hand cell (d480_hand_cell.CELL_HAND through d399_recalc_segment.recalc_pair, margin 4%),
drawn per (root, calendar year) on the ratio back-adjusted daily series raised to the power 1/r, r = the previous
year's median ATR20% / c_eq (c_eq = the equity panel's median ATR20%/close on keep_v2 bars 2010-2023). At r = 1 the
transform is the identity. THE RULE is D482's level read (long pos <= 0.10, short >= 0.90), filled at the next session's
open (the 18:00 Globex open), held H = 5 sessions or exited at the next open after a body break of the traded side;
a 3x-round-trip expected-profit gate; no trade spans a roll or a dropped session; one position per root.
C1: gross y = gross / sigma$ above the shared-offset circular rotation of each root's signal series (exact).
E1-E4 economics; X: the channel beats a plain-range control of the channels' median age. In-sample (<= 2023-12-29).
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

SPEC = REPO / "docs" / "decisions" / "D753-STAGE-0-PRE-REG-the-channel-level-rule-on-daily-futures.md"
FIX = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json"
SPECS = REPO / "data" / "futures_contract_specs.json"
STRIP = REPO / "data" / "fixtures" / "fut_settle_strip.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
BOOKS = REPO / "data" / "d748_component_books.csv"
OUT = REPO / "data" / "stage0_d753_futures_channel.json"

SEAL, IN_HI = "2024-01-01", "2023-12-29"
EXCLUDED = ("BZ", "SR3")
H, H_REPORT = 5, (1, 3, 10, 20)
POS_LO, POS_HI = 0.10, 0.90
GATE_K = 3.0
WARM, MIN_PRIOR, MIN_YEAR_OBS = 300, 250, 100
ATR_N, SIG_N = 20, 20
ALPHA, T_MIN, SKEW_MIN, G3_FLOOR = 0.05, 2.0, -0.5, 209.0
EQ_LO, EQ_HI = "2010-01-04", "2023-12-29"
KA_SEEDS = (20260910, 20260911)
SECTORS = {"equity index": ("ES", "NQ", "YM", "RTY", "NKD"), "rates": ("ZT", "ZF", "ZN", "TN", "ZB", "UB"),
           "FX": ("6A", "6B", "6C", "6E", "6J", "6S"), "metals": ("GC", "SI", "HG", "PL", "PA"),
           "energy": ("CL", "HO", "RB", "NG"), "grains/oilseeds": ("ZC", "ZS", "ZW", "ZL", "ZM"),
           "livestock": ("LE", "HE"), "BTC": ("BTC",)}


class D753Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D753Error(msg)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(name: str, filename: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def mods() -> SimpleNamespace:
    RC = _load("d399rc", "d399_recalc_segment.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    HC = _load("d480hc", "d480_hand_cell.py")
    from backtest_framework.research.structure import pivots_tie_tolerant as PVT
    return SimpleNamespace(RC=RC, DR=DR, HC=HC, PVT=PVT)


# ================================================================================ the lines
def bars_of(op, hi, lo, cl) -> list:
    return [SimpleNamespace(bar=SimpleNamespace(open=float(a), high=float(b), low=float(c), close=float(d)))
            for a, b, c, d in zip(op, hi, lo, cl)]


def lines_arrays(M, op, cl, hi, lo, cell: dict, margin: float, scale: float = 1.0) -> dict:
    """d480_hand_cell.lines_from_arrays, copied, returning recalc_pair's events and segment starts too. `scale`
    multiplies every log-distance threshold explicitly (the A1.1 diagnostic only); the run uses scale = 1 on
    transformed prices."""
    RC = M.RC
    m = op.size
    piv = M.HC.pivots_of(M.PVT, bars_of(op, hi, lo, cl), cell["k"])
    with np.errstate(divide="ignore"):
        body = {"support": np.log(np.minimum(op, cl)), "resistance": np.log(np.maximum(op, cl))}
        ext = {"support": np.log(lo), "resistance": np.log(hi)}
    max_dg = RC.INF if cell["dg"] is None else M.DR.h_of_annual(cell["dg"])
    sc = scale
    G, L, S, why = RC.recalc_pair(
        piv, cell["k"], body, m,
        carry=cell["carry"], min_piv=cell["min_piv"], max_dg=max_dg * sc if np.isfinite(max_dg) else max_dg,
        max_dh=math.log1p(cell["dh"] / 100) * sc, use_body=cell["use_body"],
        min_width=math.log1p(cell["min_width"] / 100) * sc, delta=M.DR.DELTA * sc, ext_log=ext,
        break_pivot=cell["break_pivot"], anchor_clear=cell["anchor_clear"],
        decay_end=cell["decay_end"], extend_back=cell["extend_back"],
        back_tol=None, fit_mode=cell["fit_mode"], touch_tol=cell["touch_tol"] * sc,
        min_touch=cell["min_touch"], height_mode=cell["height_mode"],
        walk_chain=cell["walk_chain"], max_reach=cell["max_reach"], syn_ttl=cell["syn_ttl"],
        stale_w=cell["stale_w"], stale_d=math.log1p(cell["stale_d"] / 100) * sc,
        stale_stat=cell["stale_stat"],
        fit_tol=None if cell["fit_tol"] is None else math.log1p(cell["fit_tol"] / 100) * sc,
        pair_break=cell["pair_break"], pair_draw=cell["pair_draw"], anchor_mode=cell["anchor_mode"],
        anchor_q=cell["anchor_q"], decay_mode=cell["decay_mode"],
        break_depth=math.log1p(cell["break_depth"] / 100) * sc, break_bars=cell["break_bars"],
        max_piv=cell["max_piv"], break_keep=cell.get("break_keep"))
    lm = math.log1p(margin / 100) * sc
    L = {"support": L["support"] - lm, "resistance": L["resistance"] + lm}
    drawn = {kd: np.isfinite(L[kd]) for kd in ("support", "resistance")}
    return dict(m=m, G=G, L=L, S=S, drawn=drawn, events=why.get("events", []))


def lines_window(M, op, hi, lo, cl, r: float) -> dict:
    """The hand cell on price ** (1/r); levels returned in LOG ADJUSTED PRICE (r x the transformed log level)."""
    e = 1.0 / r
    o2, h2, l2, c2 = op ** e, hi ** e, lo ** e, cl ** e
    out = lines_arrays(M, o2, c2, h2, l2, M.HC.CELL_HAND, M.HC.MARGIN)
    out["L"] = {kd: r * v for kd, v in out["L"].items()}
    return out


def root_lines_job(args: tuple) -> dict:
    """One root, every traded year (a worker in the pool; also called in-process for chunk == whole)."""
    root, op, hi, lo, cl, years_plan = args
    M = mods()
    n = op.size
    LS, LR = np.full(n, np.nan), np.full(n, np.nan)
    SS, SR = np.full(n, -1), np.full(n, -1)
    BS, BR = np.zeros(n, bool), np.zeros(n, bool)
    RT = np.full(n, np.nan)
    for y, i0, i1, r in years_plan:
        lo_i = max(0, i0 - WARM)
        w = lines_window(M, op[lo_i:i1 + 1], hi[lo_i:i1 + 1], lo[lo_i:i1 + 1], cl[lo_i:i1 + 1], r)
        sl = slice(i0 - lo_i, i1 - lo_i + 1)
        LS[i0:i1 + 1] = w["L"]["support"][sl]
        LR[i0:i1 + 1] = w["L"]["resistance"][sl]
        ss, sr = np.asarray(w["S"]["support"], float)[sl], np.asarray(w["S"]["resistance"], float)[sl]
        SS[i0:i1 + 1] = np.where(np.isfinite(ss), ss + lo_i, -1).astype(int)
        SR[i0:i1 + 1] = np.where(np.isfinite(sr), sr + lo_i, -1).astype(int)
        RT[i0:i1 + 1] = r
        for t, kd, kind in w["events"]:
            g = int(t) + lo_i
            if kind == "body" and i0 <= g <= i1:
                (BS if kd == "support" else BR)[g] = True
    return dict(root=root, LS=LS, LR=LR, SS=SS, SR=SR, BS=BS, BR=BR, RT=RT)


# ================================================================================ the data
SEGS = ["h18", "h19", "h20", "h21", "h22", "h23", "h00", "h01", "h02", "h03", "h04", "h05", "h06",
        "h07", "h08", "h09", "h10", "h11", "h12", "h13", "h14", "h15", "h16"]


def load_sessions() -> pd.DataFrame:
    cols = ["root", "day", "contract"] + [f"{s}_{x}" for s in SEGS for x in "ohlc"]
    df = pd.read_csv(FIX, usecols=cols, encoding="utf-8", dtype={"day": str, "contract": str, "root": str})
    df = df[df["day"] < SEAL].copy()
    O = df[[s + "_o" for s in SEGS]].to_numpy(float)
    Hh = df[[s + "_h" for s in SEGS]].to_numpy(float)
    Ll = df[[s + "_l" for s in SEGS]].to_numpy(float)
    C = df[[s + "_c" for s in SEGS]].to_numpy(float)
    finC, finO = np.isfinite(C), np.isfinite(O)
    rows = np.arange(len(df))
    last = C.shape[1] - 1 - np.argmax(finC[:, ::-1], axis=1)
    first = np.argmax(finO, axis=1)
    with np.errstate(all="ignore"):
        out = pd.DataFrame({"root": df["root"].to_numpy(), "day": df["day"].to_numpy(),
                            "contract": df["contract"].to_numpy(),
                            "o": np.where(finO.any(1), O[rows, first], np.nan),
                            "h": np.nanmax(np.where(np.isfinite(Hh), Hh, -np.inf), axis=1),
                            "l": np.nanmin(np.where(np.isfinite(Ll), Ll, np.inf), axis=1),
                            "c": np.where(finC.any(1), C[rows, last], np.nan),
                            "nclose": finC.sum(1)})
    out = out[np.isfinite(out["c"]) & np.isfinite(out["o"]) & np.isfinite(out["h"]) & np.isfinite(out["l"])]
    wk = pd.to_datetime(out["day"]).dt.dayofweek >= 5
    need(int(out.loc[wk, "nclose"].max()) <= 3 if wk.any() else True, "a weekend-dated row carries a real session")
    out = out[~wk].copy()
    out["year"] = out["day"].str[:4].astype(int)
    need(out["day"].max() < SEAL, "the seal: a futures session on or after 2024-01-01")
    return out.sort_values(["root", "day"]).reset_index(drop=True)


def load_settles(roots: list[str]) -> pd.Series:
    s = pd.read_csv(STRIP, encoding="utf-8", dtype={"root": str, "contract": str, "ref": str})
    s = s[(s["ref"] < SEAL) & s["root"].isin(roots)]
    need(s["ref"].max() < SEAL, "the seal: a settlement on or after 2024-01-01")
    return s.drop_duplicates(["root", "contract", "ref"], keep="last").set_index(["root", "contract", "ref"])["settle"]


def build_root(g: pd.DataFrame, settles: pd.Series | None, root: str) -> dict:
    """Arrays for one root: raw OHLC on the traded contract, the roll flags, the ratio back-adjusted OHLC."""
    bad = (g[["o", "h", "l", "c"]] <= 0).any(axis=1).to_numpy()
    kept = g[~bad].reset_index(drop=True)
    orig_pos = np.flatnonzero(~bad)
    gap_after = np.r_[np.diff(orig_pos) > 1, False]                 # a dropped session follows this one
    day = kept["day"].to_numpy(str)
    ct = kept["contract"].to_numpy(str)
    o, h, l, c = (kept[x].to_numpy(float) for x in "ohlc")
    n = len(kept)
    roll = np.r_[False, ct[1:] != ct[:-1]]
    F = np.ones(n)
    fallback = 0
    for j in np.flatnonzero(roll):
        sn = so = np.nan
        if settles is not None:
            sn = settles.get((root, ct[j], day[j - 1]), np.nan)
            so = settles.get((root, ct[j - 1], day[j - 1]), np.nan)
        if np.isfinite(sn) and np.isfinite(so) and sn > 0 and so > 0:
            F[j] = sn / so
        else:
            F[j] = o[j] / c[j - 1]
            fallback += 1
    mult = np.ones(n)
    acc = 1.0
    for j in range(n - 1, -1, -1):                                  # history before roll j scaled by F[j]
        mult[j] = acc
        if roll[j]:
            acc *= F[j]
    adj = {x: v * mult for x, v in zip("ohlc", (o, h, l, c))}
    return dict(root=root, day=day, year=kept["year"].to_numpy(int), ct=ct, o=o, h=h, l=l, c=c, roll=roll,
                F=F, gap_after=gap_after, adj=adj, n=n, dropped=int(bad.sum()), fallback=fallback)


def stitch_check(R: dict, skip: int | None = None) -> int:
    """Across each roll j, the adjusted close return equals c[j] / (c[j-1] x F[j]); returns the number of failures."""
    ac = R["adj"]["c"]
    fails = 0
    for k, j in enumerate(np.flatnonzero(R["roll"])):
        want = R["c"][j] / (R["c"][j - 1] * R["F"][j])
        got = ac[j] / ac[j - 1]
        if skip is not None and k == skip:
            got = R["c"][j] / R["c"][j - 1]
        if not math.isclose(got, want, rel_tol=1e-10):
            fails += 1
    return fails


def atr_pct(R: dict) -> np.ndarray:
    a = R["adj"]
    pc = np.r_[np.nan, a["c"][:-1]]
    tr = np.nanmax(np.vstack([a["h"] - a["l"], np.abs(a["h"] - pc), np.abs(a["l"] - pc)]), axis=0)
    atr = pd.Series(tr).rolling(ATR_N, min_periods=ATR_N).mean().to_numpy()
    return atr / a["c"]


def sigma_usd(R: dict, upp: float) -> np.ndarray:
    """Prior-20 RMS of the same-contract daily move x $/point, known at the close of t."""
    c, o = R["c"], R["o"]
    dP = np.r_[np.nan, np.where(R["roll"][1:], c[1:] - o[1:], c[1:] - c[:-1])]
    dP[np.r_[False, R["gap_after"][:-1]]] = np.nan
    return np.sqrt(pd.Series(dP * dP).rolling(SIG_N, min_periods=SIG_N).mean().to_numpy()) * upp


def year_plan(R: dict, atrp: np.ndarray, c_eq: float, live_start: int) -> list[tuple]:
    plan = []
    yrs = R["year"]
    for y in sorted(set(yrs.tolist())):
        if y < live_start or y > 2023:
            continue
        idx = np.flatnonzero(yrs == y)
        i0, i1 = int(idx[0]), int(idx[-1])
        prev = atrp[(yrs == y - 1) & np.isfinite(atrp)]
        if i0 < MIN_PRIOR or prev.size < MIN_YEAR_OBS:
            continue
        plan.append((y, i0, i1, float(np.median(prev)) / c_eq))
    return plan


def units(roots: list[str]) -> dict:
    D555 = _load("d555", "run_d555_tsmom_replication.py")
    meta = json.loads(META.read_text(encoding="utf-8"))
    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    costs = json.loads(COSTS.read_text(encoding="utf-8"))["roots"]
    out = {}
    for r in roots:
        sp = meta["specs"][r]
        full_upp = sp["tick_usd_full_contract"] / sp["tick_price_units"]
        if r in D555.MICRO_OF:
            mic = D555.MICRO_OF[r]
            if mic in specs:
                upp, tick_usd = specs[mic]["usd_per_point"], specs[mic]["tick_usd"]
            else:
                need(sp["sized_as"] == mic, f"{r}: sized_as {sp['sized_as']}")
                upp, tick_usd = sp["tick_usd"] / sp["tick_price_units"], sp["tick_usd"]
            ce = costs[r]["micro"]
            size = mic
        else:
            upp, tick_usd = full_upp, sp["tick_usd"]
            ce = costs[r]["full"]
            size = r
        xt = ce["crossing_ticks_rt"][ce["default_line"]]["value"]
        comm = ce["commission_rt_usd"]["value"]
        need(math.isclose(float(ce["tick_usd"]), float(tick_usd), rel_tol=1e-6), f"{r}: tick_usd disagrees with the cost table")
        out[r] = dict(upp=float(upp), tick_usd=float(tick_usd), cost_rt=float(comm + xt * tick_usd), size=size,
                      line=ce["default_line"])
    return out


# ================================================================================ signals, outcomes, selection
def channel_signals(R, LN, u, gate=True) -> tuple[np.ndarray, np.ndarray]:
    lc = np.log(R["adj"]["c"])
    LS, LR = LN["LS"], LN["LR"]
    ok = np.isfinite(LS) & np.isfinite(LR) & (LR > LS)
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = (lc - LS) / (LR - LS)
        mid = 0.5 * (LS + LR)
        dist = R["c"] * np.abs(np.exp(mid - lc) - 1.0) * u["upp"]
    s = np.where(ok & (pos <= POS_LO), 1, np.where(ok & (pos >= POS_HI), -1, 0)).astype(np.int8)
    if gate:
        s = np.where(dist >= GATE_K * u["cost_rt"], s, 0).astype(np.int8)
    return s, pos


def control_signals(R, Lc: int, u, RT, gate=True) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = R["adj"]
    HH = pd.Series(a["h"]).rolling(Lc, min_periods=Lc).max().shift(1).to_numpy()
    LL = pd.Series(a["l"]).rolling(Lc, min_periods=Lc).min().shift(1).to_numpy()
    lc = np.log(a["c"])
    with np.errstate(invalid="ignore", divide="ignore"):
        lh, ll = np.log(HH), np.log(LL)
        pos = (lc - ll) / (lh - ll)
        dist = R["c"] * np.abs(np.exp(0.5 * (lh + ll) - lc) - 1.0) * u["upp"]
    ok = np.isfinite(pos) & np.isfinite(RT) & (lh > ll)
    s = np.where(ok & (pos <= POS_LO), 1, np.where(ok & (pos >= POS_HI), -1, 0)).astype(np.int8)
    if gate:
        s = np.where(dist >= GATE_K * u["cost_rt"], s, 0).astype(np.int8)
    return s, ll, lh


def domain(R, RT, hold: int) -> np.ndarray:
    """Signal dates t that may trade: a traded year (r defined), and no roll or dropped session between t and the
    end of the hold window e + hold + 1 (e = t + 1)."""
    n = R["n"]
    ok = np.isfinite(RT).copy()
    rollc = np.cumsum(R["roll"].astype(int))
    gapc = np.cumsum(R["gap_after"].astype(int))
    for t in range(n):
        if not ok[t]:
            continue
        end = t + 1 + hold + 1
        if end > n - 1:
            ok[t] = False
            continue
        if rollc[end] - rollc[t] > 0 or gapc[end - 1] - (gapc[t - 1] if t > 0 else 0) > 0:
            ok[t] = False
    return ok


def outcomes(R, u, sig_usd, brk_long, brk_short, valid, hold: int) -> dict:
    """For every valid t and both sides: the exit index (the next-free signal index), gross $, cost $, y, how."""
    n = R["n"]
    o, c = R["o"], R["c"]
    ex = np.full((n, 2), -1, int)
    gross = np.full((n, 2), np.nan)
    cost = np.full((n, 2), np.nan)
    how = np.zeros((n, 2), np.int8)                   # 1 time, 2 break
    for t in np.flatnonzero(valid):
        e = t + 1
        for k, s in enumerate((1, -1)):
            brk = brk_long if s == 1 else brk_short
            x_i, x_p, hw = e + hold - 1, c[e + hold - 1], 1
            for v in range(e, e + hold - 1):
                if brk[v]:
                    x_i, x_p, hw = v + 1, o[v + 1], 2
                    break
            ex[t, k] = x_i
            gross[t, k] = s * (x_p - o[e]) * u["upp"]
            cost[t, k] = u["cost_rt"] + (u["tick_usd"] if hw == 2 else 0.0)
            how[t, k] = hw
    y = gross / sig_usd[:, None]
    return dict(ex=ex, gross=gross, cost=cost, how=how, y=y)


def select(s: np.ndarray, valid: np.ndarray, ex: np.ndarray) -> list[int]:
    """Greedy one-position selection by jump pointers: the next signal at or after the last exit index."""
    nz = np.flatnonzero((s != 0) & valid)
    out, nf, p = [], 0, 0
    while True:
        p = bisect.bisect_left(nz, nf, p)
        if p >= nz.size:
            return out
        t = int(nz[p])
        out.append(t)
        nf = int(ex[t, 0 if s[t] > 0 else 1])
        p += 1


def select_loop(s, valid, ex) -> list[int]:
    out, nf = [], 0
    for t in range(s.size):
        if t >= nf and s[t] != 0 and valid[t]:
            out.append(t)
            nf = int(ex[t, 0 if s[t] > 0 else 1])
    return out


def trades_of(root, R, s, sel, oc, u, sig_usd, extra=None) -> list[dict]:
    rows = []
    for t in sel:
        k = 0 if s[t] > 0 else 1
        g, cst = float(oc["gross"][t, k]), float(oc["cost"][t, k])
        rows.append(dict(root=root, t=int(t), day=R["day"][t + 1], exit_day=R["day"][oc["ex"][t, k]] if oc["how"][t, k] == 2
                         else R["day"][oc["ex"][t, k]], year=int(R["day"][t + 1][:4]), side=int(s[t]), gross=g, cost=cst,
                         net=g - cst, y=float(oc["y"][t, k]), how="break" if oc["how"][t, k] == 2 else "time",
                         **(extra(t) if extra else {})))
    return rows


# ================================================================================ statistics
def dist_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"trades": 0}
    net, y = df["net"].to_numpy(), df["y"].to_numpy()
    n = len(net)
    sd = float(net.std(ddof=1)) if n > 1 else float("nan")
    mu = float(net.mean())
    q1, q99 = np.quantile(net, [0.01, 0.99])
    m3 = float(np.mean((net - mu) ** 3)) / float(net.std()) ** 3 if net.std() > 0 else float("nan")
    by = df.groupby("year")["net"].sum()
    best2 = by.sort_values(ascending=False).index[:2].tolist()
    ex2 = float(by.drop(best2).sum())
    ny = len(by)
    wins, losses = net[net > 0], net[net < 0]
    root_tot = df.groupby("root")["net"].sum()
    return {"trades": n, "y_mean": float(y.mean()), "y_t": float(y.mean() / (y.std(ddof=1) / math.sqrt(n))) if n > 1 else None,
            "y_median": float(np.median(y)), "gross_mean": float(df["gross"].mean()), "net_mean": mu,
            "net_t": mu / (sd / math.sqrt(n)) if n > 1 and sd > 0 else None, "net_median": float(np.median(net)),
            "win_rate": float(np.mean(net > 0)), "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) else None,
            "skew": m3, "worst": float(net.min()), "best": float(net.max()),
            "trim_ex_top": float(net[net <= q99].mean()), "trim_ex_bottom": float(net[net >= q1].mean()),
            "trim_both": float(net[(net >= q1) & (net <= q99)].mean()), "breakeven_cost_per_trade": float(df["gross"].mean()),
            "break_exit_share": float(np.mean(df["how"] == "break")), "net_by_year": {int(k): float(v) for k, v in by.items()},
            "years_positive": int((by > 0).sum()), "years": ny, "ex2_total": ex2, "ex2_per_year": ex2 / max(ny - 2, 1),
            "G1": ex2 > 0, "G2": int((by > 0).sum()) >= math.ceil(2 * ny / 3), "G3": ex2 / max(ny - 2, 1) >= G3_FLOOR,
            "top_root_share": float(root_tot.max() / root_tot.sum()) if root_tot.sum() > 0 else None,
            "top_year_share": float(by.max() / by.sum()) if by.sum() > 0 else None}


def book_stats(df: pd.DataFrame, days: list[str]) -> dict:
    d = df.groupby("exit_day")["net"].sum().reindex(days, fill_value=0.0).to_numpy()
    sd = d.std(ddof=1)
    down = math.sqrt(float(np.mean(np.minimum(d, 0.0) ** 2)))
    eq = np.cumsum(d)
    return {"sharpe": float(d.mean() / sd * math.sqrt(252)) if sd > 0 else None,
            "sortino": float(d.mean() / down * math.sqrt(252)) if down > 0 else None,
            "max_dd": float(np.max(np.maximum.accumulate(eq) - eq)), "net_total": float(d.sum())}


# ================================================================================ the rotation
def rotation(per_root: dict, K: int, observed: float) -> dict:
    """per_root[r] = (s, valid, ex, y): shared offset k, each root shifted by k mod its own length."""
    vals = np.empty(K)
    for k in range(K):
        tot, cnt = 0.0, 0
        for r, (s, valid, ex, y) in per_root.items():
            sr = np.roll(s, k % s.size)
            sel = select(sr, valid, ex)
            if sel:
                kk = np.where(sr[sel] > 0, 0, 1)
                yy = y[np.asarray(sel), kk]
                tot += float(yy.sum())
                cnt += len(sel)
        vals[k] = tot / cnt if cnt else np.nan
    need(math.isclose(vals[0], observed, rel_tol=1e-12, abs_tol=1e-15), f"rotation: offset 0 {vals[0]} != observed {observed}")
    fin = vals[np.isfinite(vals)]
    return {"observed": observed, "offsets": int(K), "p_high": float(np.mean(fin >= observed)),
            "p50": float(np.percentile(fin, 50)), "p95": float(np.percentile(fin, 95)), "_vals": vals}


# ================================================================================ equity: c_eq and the known answer
def equity_side(M) -> dict:
    RP = _load("rp", "ragged_panel.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    NS = sys.modules.get("d399ns") or _load("d399ns", "d399_new_sample.py")
    panel, cleaned = RP.load_ragged(*M.DR.MINING, fee_bps=0.0, dividend_bound=True)
    vals = []
    for s in panel.symbols:
        bars = cleaned.get(s)
        if not bars or len(bars) < ATR_N + 2:
            continue
        dd = np.array([b.timestamp.date().isoformat() for b in bars])
        h = np.array([b.bar.high for b in bars], float)
        lo = np.array([b.bar.low for b in bars], float)
        c = np.array([b.bar.close for b in bars], float)
        raw = np.array([getattr(b.bar, "raw_close", b.bar.close) for b in bars], float)
        vol = np.array([b.bar.volume for b in bars], float)
        dv = raw * vol
        okdv = np.isfinite(dv) & (dv > 0)
        if not okdv.any():
            continue
        thr = np.nanpercentile(dv[okdv], UF.DV_PCT)
        keep = (raw >= UF.PX_MIN) & np.isfinite(dv) & (dv >= thr)
        pc = np.r_[np.nan, c[:-1]]
        tr = np.nanmax(np.vstack([h - lo, np.abs(h - pc), np.abs(lo - pc)]), axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            lr = np.abs(np.r_[0.0, np.diff(np.log(c))])
        jump = pd.Series(lr > NS.SPLIT_LR).rolling(ATR_N + 1, min_periods=1).max().to_numpy() > 0
        atrp = pd.Series(tr).rolling(ATR_N, min_periods=ATR_N).mean().to_numpy() / c
        m = keep & ~jump & np.isfinite(atrp) & (dd >= EQ_LO) & (dd <= EQ_HI)
        vals.append(atrp[m])
    allv = np.concatenate(vals)
    c_eq = float(np.median(allv))
    need(0.005 <= c_eq <= 0.08, f"c_eq {c_eq} is implausible")
    # the known answer: the copied line module at r = 1 equals d480_hand_cell's on D399's sampled pairs
    draw1, _ = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW, seed=KA_SEEDS[0])
    draw2, _ = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW, seed=KA_SEEDS[1],
                              exclude=tuple(NS.EXCLUDE) + tuple(s for s, _ in draw1))
    pairs = draw1 + draw2
    for s, st in pairs:
        bars = cleaned[s][: st + NS.WIN]
        ref = M.HC.hand_lines(M.RC, M.DR, M.PVT, bars, M.HC.CELL_HAND, M.HC.MARGIN)
        op = np.array([b.bar.open for b in bars], float)
        hi = np.array([b.bar.high for b in bars], float)
        lo = np.array([b.bar.low for b in bars], float)
        cl = np.array([b.bar.close for b in bars], float)
        mine = lines_window(M, op, hi, lo, cl, 1.0)
        for kd in ("support", "resistance"):
            need(np.array_equal(ref["L"][kd], mine["L"][kd], equal_nan=True), f"known answer: {s} {st} {kd} levels differ")
            need(np.array_equal(np.asarray(ref["G"][kd]), np.asarray(mine["G"][kd]), equal_nan=True), f"known answer: {s} {st} {kd} gradients differ")
    return {"c_eq": c_eq, "c_eq_bars": int(allv.size), "known_answer_pairs": len(pairs),
            "pairs": [[s, int(st)] for s, st in pairs]}


# ================================================================================ the run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    M = mods()
    eq = equity_side(M)
    c_eq = eq["c_eq"]
    print(f"[D753] c_eq {c_eq:.5f} on {eq['c_eq_bars']:,} bars; known answer exact on {eq['known_answer_pairs']} pairs "
          f"({time.time() - t0:.0f}s)", flush=True)

    D555 = _load("d555", "run_d555_tsmom_replication.py")
    sess = load_sessions()
    live = D555.live_start_by_rule(sess.assign(close=sess["c"]))
    roots = sorted(r for r in sess["root"].unique() if r not in EXCLUDED)
    need(len(roots) == 34, f"{len(roots)} roots, not 34")
    settles = load_settles(roots)
    U = units(roots)
    RD, ATRP, SIG, PLAN = {}, {}, {}, {}
    for r in roots:
        R = build_root(sess[sess["root"] == r], settles, r)
        need(stitch_check(R) == 0, f"{r}: the stitch check fails")
        if R["roll"].sum() > 0:
            need(stitch_check(R, skip=0) > 0, f"{r}: the stitch canary did not fire")
        RD[r] = R
        ATRP[r] = atr_pct(R)
        SIG[r] = sigma_usd(R, U[r]["upp"])
        PLAN[r] = year_plan(R, ATRP[r], c_eq, live[r])
    print(f"[D753] {len(roots)} roots built ({time.time() - t0:.0f}s); fallback roll factors "
          f"{sum(R['fallback'] for R in RD.values())} of {sum(int(R['roll'].sum()) for R in RD.values())}; "
          f"dropped sessions {sum(R['dropped'] for R in RD.values())}", flush=True)

    jobs = [(r, RD[r]["adj"]["o"], RD[r]["adj"]["h"], RD[r]["adj"]["l"], RD[r]["adj"]["c"], PLAN[r]) for r in roots]
    with ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as ex:
        LNS = {d["root"]: d for d in ex.map(root_lines_job, jobs)}
    probe = "ZN"
    one = root_lines_job(next(j for j in jobs if j[0] == probe))
    for k in ("LS", "LR", "SS", "SR", "BS", "BR", "RT"):
        need(np.array_equal(one[k], LNS[probe][k], equal_nan=True), f"chunk != whole on {probe} {k}")
    print(f"[D753] lines drawn ({time.time() - t0:.0f}s)", flush=True)

    # the lag audit: a second implementation by truncation at t, and its canary
    rng = np.random.default_rng(753)
    cand = [(r, int(t)) for r in roots for t in np.flatnonzero(np.isfinite(LNS[r]["LS"]) & np.isfinite(LNS[r]["LR"]))]
    pick = [cand[i] for i in rng.choice(len(cand), size=40, replace=False)]
    canary_differs = 0
    for r, t in pick:
        y, i0, i1, rr = next(p for p in PLAN[r] if p[1] <= t <= p[2])
        lo_i = max(0, i0 - WARM)
        a = RD[r]["adj"]
        w = lines_window(M, a["o"][lo_i:t + 1], a["h"][lo_i:t + 1], a["l"][lo_i:t + 1], a["c"][lo_i:t + 1], rr)
        for kd, key in (("support", "LS"), ("resistance", "LR")):
            need(math.isclose(w["L"][kd][t - lo_i], LNS[r][key][t], rel_tol=0, abs_tol=1e-12) or
                 (not np.isfinite(w["L"][kd][t - lo_i]) and not np.isfinite(LNS[r][key][t])),
                 f"lag audit: {r} {t} {kd} truncated {w['L'][kd][t - lo_i]} vs full {LNS[r][key][t]}")
        if t + 1 < RD[r]["n"]:
            lc0, lc1 = math.log(a["c"][t]), math.log(a["c"][t + 1])
            LS_, LR_ = LNS[r]["LS"][t], LNS[r]["LR"][t]
            if (lc0 - LS_) / (LR_ - LS_) != (lc1 - LS_) / (LR_ - LS_):
                canary_differs += 1
    need(canary_differs > 0, "the lag canary (t+1's close) never disagreed")

    # the A1.1 diagnostic: transformed run vs explicit thresholds x r, on one root-year
    yv, i0, i1, rr = PLAN[probe][len(PLAN[probe]) // 2]
    lo_i = max(0, i0 - WARM)
    a = RD[probe]["adj"]
    tw = lines_window(M, a["o"][lo_i:i1 + 1], a["h"][lo_i:i1 + 1], a["l"][lo_i:i1 + 1], a["c"][lo_i:i1 + 1], rr)
    xw = lines_arrays(M, a["o"][lo_i:i1 + 1], a["c"][lo_i:i1 + 1], a["h"][lo_i:i1 + 1], a["l"][lo_i:i1 + 1],
                      M.HC.CELL_HAND, M.HC.MARGIN, scale=rr)
    diag = {}
    for kd in ("support", "resistance"):
        A, B = tw["L"][kd], xw["L"][kd]
        both = np.isfinite(A) & np.isfinite(B)
        diag[kd] = {"drawn_agree": float(np.mean(np.isfinite(A) == np.isfinite(B))),
                    "max_abs_diff": float(np.max(np.abs(A[both] - B[both]))) if both.any() else None}

    # signals and the control's length
    VAL = {r: domain(RD[r], LNS[r]["RT"], H) for r in roots}
    SIGS = {r: channel_signals(RD[r], LNS[r], U[r])[0] for r in roots}
    OC = {r: outcomes(RD[r], U[r], SIG[r], LNS[r]["BS"], LNS[r]["BR"], VAL[r], H) for r in roots}
    SEL = {r: select(SIGS[r], VAL[r], OC[r]["ex"]) for r in roots}
    for r in roots:
        need(SEL[r] == select_loop(SIGS[r], VAL[r], OC[r]["ex"]), f"{r}: jump-pointer selection != loop")
        for t in SEL[r]:
            k = 0 if SIGS[r][t] > 0 else 1
            x = OC[r]["ex"][t, k]
            need(not RD[r]["roll"][t + 1:x + 1].any(), f"{r} {t}: a trade spans a roll")
    ages = [t - max(LNS[r]["SS"][t], LNS[r]["SR"][t]) for r in roots for t in SEL[r]]
    Lc = int(round(float(np.median(ages))))
    need(Lc >= 2, f"control length {Lc}")
    print(f"[D753] channel trades {sum(len(v) for v in SEL.values())}; control length L = {Lc} ({time.time() - t0:.0f}s)", flush=True)

    ch = pd.DataFrame([row for r in roots for row in trades_of(r, RD[r], SIGS[r], SEL[r], OC[r], U[r], SIG[r])])
    need(not ch.empty, "no channel trades")
    obs = float(ch["y"].mean())
    per_root = {r: (SIGS[r], VAL[r], OC[r]["ex"], OC[r]["y"]) for r in roots}
    K = max(SIGS[r].size for r in roots)
    t1 = time.time()
    rot = rotation(per_root, K, obs)
    print(f"[D753] rotation over {K} offsets ({time.time() - t1:.0f}s)", flush=True)
    ks = list(range(0, K, max(1, K // 50)))[:50]
    for k in ks:
        tot, cnt = 0.0, 0
        for r, (s, valid, exx, yy) in per_root.items():
            sr = np.roll(s, k % s.size)
            for t in select_loop(sr, valid, exx):
                tot += yy[t, 0 if sr[t] > 0 else 1]
                cnt += 1
        need(math.isclose(tot / cnt, rot["_vals"][k], rel_tol=1e-9), f"rotation vector != loop at offset {k}")

    # the control
    CS, CO, CSEL = {}, {}, {}
    for r in roots:
        s, ll, lh = control_signals(RD[r], Lc, U[r], LNS[r]["RT"])
        lc = np.log(RD[r]["adj"]["c"])
        rr_ = LNS[r]["RT"]
        CS[r] = s
        oc = outcomes_control(RD[r], U[r], SIG[r], VAL[r], H, ll, lh, lc, rr_)
        CO[r] = oc
        CSEL[r] = select(s, VAL[r], oc["ex"])
    ct = pd.DataFrame([row for r in roots for row in trades_of(r, RD[r], CS[r], CSEL[r], CO[r], U[r], SIG[r])])
    paired = ch.merge(ct, on=["root", "t"], suffixes=("_ch", "_ct"))
    dpair = (paired["y_ch"] - paired["y_ct"]).to_numpy()
    X_pair = {"n": int(dpair.size), "mean_diff_y": float(dpair.mean()) if dpair.size else None,
              "se": float(dpair.std(ddof=1) / math.sqrt(dpair.size)) if dpair.size > 1 else None}
    X_unp = {"mean_diff_y": float(ch["y"].mean() - ct["y"].mean()),
             "se": float(math.sqrt(ch["y"].var(ddof=1) / len(ch) + ct["y"].var(ddof=1) / len(ct)))}
    X_holds = bool(X_pair["n"] > 1 and X_pair["mean_diff_y"] > 2 * X_pair["se"])

    # the readings
    st = dist_stats(ch)
    C1 = rot["p_high"] <= ALPHA
    E = {"E1": bool(st["net_mean"] > 0 and (st["net_t"] or 0) >= T_MIN), "E2": bool(st["net_median"] >= 0),
         "E3": bool(st["skew"] >= SKEW_MIN), "E4": bool(st["G1"] and st["G2"] and st["G3"])}
    if C1 and all(E.values()) and X_holds:
        reading = "GO"
    elif C1 and not X_holds:
        reading = "SIGNAL, NOT THE LINES"
    elif C1:
        reading = "SIGNAL ONLY: " + ", ".join(k for k, v in E.items() if not v)
    else:
        reading = "NOTHING"

    # reported, never chosen from
    rep: dict[str, Any] = {}
    rep["per_sector"] = {sec: dist_stats(ch[ch["root"].isin(rs)]) for sec, rs in SECTORS.items()}
    rep["per_root"] = {r: dist_stats(ch[ch["root"] == r]) for r in roots}
    rep["long"], rep["short"] = dist_stats(ch[ch["side"] > 0]), dist_stats(ch[ch["side"] < 0])
    rep["control"] = dist_stats(ct)
    hv = {}
    for hh in H_REPORT:
        rows = []
        for r in roots:
            val = domain(RD[r], LNS[r]["RT"], hh)
            oc = outcomes(RD[r], U[r], SIG[r], LNS[r]["BS"], LNS[r]["BR"], val, hh)
            rows += trades_of(r, RD[r], SIGS[r], select(SIGS[r], val, oc["ex"]), oc, U[r], SIG[r])
        hv[str(hh)] = dist_stats(pd.DataFrame(rows))
    rep["hold_variants"] = hv
    rows = []
    for r in roots:
        s0 = channel_signals(RD[r], LNS[r], U[r], gate=False)[0]
        rows += trades_of(r, RD[r], s0, select(s0, VAL[r], OC[r]["ex"]), OC[r], U[r], SIG[r])
    rep["no_gate"] = dist_stats(pd.DataFrame(rows))
    alldays = sorted(set(d for r in roots for d in RD[r]["day"]))
    rep["book"] = book_stats(ch, alldays)
    bk = pd.read_csv(BOOKS, dtype={"book": str, "session": str, "net": float}, encoding="utf-8")
    chd = ch.groupby("exit_day")["net"].sum()
    rho = {}
    for b_, g in bk.groupby("book"):
        s_ = g.groupby("session")["net"].sum()
        idx = sorted(set(alldays) & set(pd.date_range(s_.index.min(), s_.index.max()).strftime("%Y-%m-%d")))
        rho[b_] = float(np.corrcoef(chd.reindex(idx, fill_value=0.0), s_.reindex(idx, fill_value=0.0))[0, 1])
    rep["rho_with_components"] = rho

    res = {"record": "D753 (e9748192, A1 b01254fb)", "reading": reading,
           "C1_rotation": {k: v for k, v in rot.items() if not k.startswith("_")}, "E": E,
           "X": {"holds": X_holds, "paired": X_pair, "unpaired": X_unp, "control_length_L": Lc},
           "primary": st, "reported": rep, "c_eq": c_eq, "equity_known_answer": eq,
           "a1_1_diagnostic": {"root_year": [probe, yv], "r": rr, **diag},
           "roots": roots, "units": U, "live_start": {r: live[r] for r in roots},
           "years_traded": {r: [p[0] for p in PLAN[r]] for r in roots},
           "r_by_root_year": {r: {str(p[0]): p[3] for p in PLAN[r]} for r in roots},
           "fallback_roll_factors": {r: RD[r]["fallback"] for r in roots},
           "dropped_sessions": {r: RD[r]["dropped"] for r in roots if RD[r]["dropped"]},
           "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)}
    write_once(OUT, res)
    show(res)
    return 0


def outcomes_control(R, u, sig_usd, valid, hold, ll, lh, lc, RT) -> dict:
    """The control's outcomes: as `outcomes`, the break being a close beyond the range extreme frozen at entry by
    break_depth x r (A1.4)."""
    n = R["n"]
    o, c = R["o"], R["c"]
    bd = math.log1p(3.0 / 100)
    ex = np.full((n, 2), -1, int)
    gross = np.full((n, 2), np.nan)
    cost = np.full((n, 2), np.nan)
    how = np.zeros((n, 2), np.int8)
    for t in np.flatnonzero(valid & np.isfinite(ll) & np.isfinite(lh)):
        e = t + 1
        for k, s in enumerate((1, -1)):
            lvl = (ll[t] - RT[t] * bd) if s == 1 else (lh[t] + RT[t] * bd)
            x_i, x_p, hw = e + hold - 1, c[e + hold - 1], 1
            for v in range(e, e + hold - 1):
                if (s == 1 and lc[v] < lvl) or (s == -1 and lc[v] > lvl):
                    x_i, x_p, hw = v + 1, o[v + 1], 2
                    break
            ex[t, k] = x_i
            gross[t, k] = s * (x_p - o[e]) * u["upp"]
            cost[t, k] = u["cost_rt"] + (u["tick_usd"] if hw == 2 else 0.0)
            how[t, k] = hw
    return dict(ex=ex, gross=gross, cost=cost, how=how, y=gross / sig_usd[:, None])


def _strip(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _strip(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_strip(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def write_once(path: Path, doc: dict) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(_strip(doc), fh, indent=1)
        fh.write("\n")


def show(res: dict) -> None:
    p, rot, X = res["primary"], res["C1_rotation"], res["X"]
    print(f"[D753] {res['reading']}")
    print(f"  C1: y mean {p['y_mean']:.4f} (t {p['y_t']:.2f}); rotation p_high {rot['p_high']:.4f} over {rot['offsets']} "
          f"(p50 {rot['p50']:.4f}, p95 {rot['p95']:.4f})")
    print(f"  E: {res['E']}; trades {p['trades']}; gross ${p['gross_mean']:.2f} net ${p['net_mean']:.2f} (t {p['net_t']:.2f}) "
          f"median ${p['net_median']:.2f}; win {p['win_rate']:.3f}; skew {p['skew']:.2f}; years+ {p['years_positive']}/{p['years']}; "
          f"ex2/yr ${p['ex2_per_year']:.0f}; break exits {p['break_exit_share']:.3f}")
    print(f"  X: holds {X['holds']}; L {X['control_length_L']}; paired {X['paired']}; unpaired {X['unpaired']}")
    print(f"  book: {res['reported']['book']}; rho {res['reported']['rho_with_components']}")
    for sec, s in res["reported"]["per_sector"].items():
        if s.get("trades"):
            print(f"    {sec:16s} n {s['trades']:5d} y {s['y_mean']:7.4f} net ${s['net_mean']:8.2f} median ${s['net_median']:8.2f}")
    print(f"  c_eq {res['c_eq']:.5f}; A1.1 diagnostic {res['a1_1_diagnostic']}; wall {res['wall_s']} s")


# ================================================================================ self-test
def selftest() -> int:
    fails = []
    M = mods()
    rng = np.random.default_rng(7531)
    n = 420
    lp = np.cumsum(rng.normal(0, 0.015, n)) + math.log(100)
    cl = np.exp(lp)
    op = np.exp(np.r_[lp[0], lp[:-1]] + rng.normal(0, 0.003, n))
    hi = np.maximum(op, cl) * np.exp(np.abs(rng.normal(0, 0.006, n)))
    lo = np.minimum(op, cl) * np.exp(-np.abs(rng.normal(0, 0.006, n)))
    # 1. at r = 1 the copied module equals d480's lines_from_arrays exactly
    ref = M.HC.lines_from_arrays(M.RC, op, cl, hi, lo, M.HC.pivots_of(M.PVT, bars_of(op, hi, lo, cl), M.HC.CELL_HAND["k"]),
                                 M.HC.CELL_HAND, M.HC.MARGIN, M.DR.DELTA, M.RC.INF)
    mine = lines_window(M, op, hi, lo, cl, 1.0)
    for kd in ("support", "resistance"):
        if not np.array_equal(ref["L"][kd], mine["L"][kd], equal_nan=True):
            fails.append(f"r = 1 identity fails on {kd}")
    if not any(np.isfinite(mine["L"][kd]).any() for kd in ("support", "resistance")):
        fails.append("no line drawn on the synthetic path (the identity test would be vacuous)")
    # 2. the stitch check and its canary
    g = pd.DataFrame({"day": [f"2015-01-{d:02d}" for d in range(5, 15)], "contract": ["A"] * 5 + ["B"] * 5,
                      "o": np.linspace(100, 109, 10), "h": np.linspace(101, 110, 10), "l": np.linspace(99, 108, 10),
                      "c": np.linspace(100.5, 109.5, 10), "year": 2015})
    R = build_root(g, None, "XX")
    if stitch_check(R) != 0 or stitch_check(R, skip=0) == 0:
        fails.append("the stitch check or its canary")
    if not math.isclose(R["adj"]["c"][4] / R["c"][4], R["F"][5]):
        fails.append("back-adjustment does not scale the pre-roll history by F")
    # 3. sign in money, rolls and the break exit, on a planted root
    Rp = dict(n=12, o=np.arange(100.0, 112.0), c=np.arange(100.5, 112.5), roll=np.zeros(12, bool),
              gap_after=np.zeros(12, bool), day=np.array([f"2015-02-{d:02d}" for d in range(1, 13)]))
    u = dict(upp=2.0, tick_usd=0.5, cost_rt=4.0)
    sig = np.full(12, 10.0)
    RT = np.ones(12)
    val = domain(Rp, RT, 5)
    oc = outcomes(Rp, u, sig, np.zeros(12, bool), np.zeros(12, bool), val, 5)
    if not (oc["gross"][0, 0] > 0 and oc["gross"][0, 1] < 0 and math.isclose(oc["gross"][0, 0], (105.5 - 101.0) * 2.0)):   # enter o[1], five sessions, exit c[5]
        fails.append(f"sign in money: {oc['gross'][0]}")
    brk = np.zeros(12, bool)
    brk[2] = True
    oc2 = outcomes(Rp, u, sig, brk, np.zeros(12, bool), val, 5)
    if not (oc2["how"][0, 0] == 2 and oc2["ex"][0, 0] == 3 and math.isclose(oc2["gross"][0, 0], (103.0 - 101.0) * 2.0)):
        fails.append("the break exit is not at the next open")
    Rp2 = dict(Rp, roll=np.r_[np.zeros(4, bool), True, np.zeros(7, bool)])
    if domain(Rp2, RT, 5)[0]:
        fails.append("a planted roll inside the hold did not block the entry")
    # 4. selection: jump pointers == loop on random signals
    for _ in range(50):
        s = rng.choice([-1, 0, 0, 0, 1], size=200).astype(np.int8)
        v = rng.random(200) < 0.9
        exx = np.minimum(np.arange(200)[:, None] + rng.integers(1, 9, (200, 2)), 199)
        if select(s, v, exx) != select_loop(s, v, exx):
            fails.append("selection: jump pointers != loop")
            break
    # 5. the rotation: offset 0 and a planted aligned series
    n2 = 400
    mv = rng.normal(0, 1, n2)
    y2 = np.column_stack([mv, -mv])
    s2 = np.where(mv >= 0, 1, -1).astype(np.int8)
    ex2 = np.minimum(np.arange(n2)[:, None] + 1, n2 - 1).repeat(2, 1)
    obs = float(np.mean(y2[np.arange(n2), np.where(s2 > 0, 0, 1)]))
    rr = rotation({"P": (s2, np.ones(n2, bool), ex2, y2)}, n2, obs)
    if not rr["p_high"] < 0.01:
        fails.append(f"planted aligned rotation p {rr['p_high']}")
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D753Error:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D753] selftest: {'FAIL' if fails else 'all passed'}")
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
