"""D787 Stage 0 (amended to a disclosed in-sample grid): fade the China open only once it has turned.
Spec: docs/decisions/D787-STAGE-0-PRE-REG-fade-the-china-open-only-once-it-has-turned.md (see its Amendment).

    python scripts/stage0_d787_china_open_turned_fade.py --selftest     # SYSTEM interpreter (databento, pyarrow)
    python scripts/stage0_d787_china_open_turned_fade.py --run

Sessions and books are D786's build (D765's MGC cell through D767's functions; D770's passive cost). For each delay L
the check is at T = 09:30 + L Beijing: the taker enters at the open of the bar at T + 1 and exits at P(15:00); the
passive book rests at the touch at T (paid GC tbbo / bbo-1m, D770's rules at the new clock), filled on a
trade-through within 30 minutes, exit at the 15:00 touch. A flag reads no price stamped after T (asserted by a
reader that raises). The null rotates each cell's flag exactly over the candidate sequence; the family-max null
applies one offset to every cell at once. Nothing on or after 2024-01-01 is read.
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d765_china_open as C  # noqa: E402
import stage0_d767_china_open_fade_filter as F7  # noqa: E402
import stage0_d770_china_open_flow_passive as D7  # noqa: E402
import stage0_d786_china_open_five_filters as D86  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D787-STAGE-0-PRE-REG-fade-the-china-open-only-once-it-has-turned.md"
OUT = REPO / "data" / "stage0_d787_china_open_turned_fade.json"
SEAL = "2024-01-01"
DELAYS = (0, 5, 10, 15, 20, 30)            # 0 is the reproduction check only
GRID_DELAYS = (5, 10, 15, 20, 30)
CONDS = ("K1c", "K1h", "K2")
BOOKS = ("passive", "taker")
LIFE_MIN = 30
TAKER_COST = 5.93
WINTER = (12, 1, 2, 3)
AUCTION_FROM = "2023-05-26"
VOL_N, VOL_MIN = 60, 40
WORKERS, AUDIT_N, SEED = 8, 40, 787      # 14 ran out of memory on the tape reads (first launch, before any output)


class D787Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D787Error(msg)


# ================================================================================ the bar path (outcome-blind flags)
class Blind:
    """D765's Px, refusing any price stamped after the check time T."""

    def __init__(self, R: dict[str, Any], limit: int):
        self.q, self.lim = C.Px(R), limit

    def p(self, t: int) -> float:
        need(t <= self.lim, "outcome-blind: a flag input after the check time was requested")
        return self.q.p(t)


def bar_extremes(R: dict[str, Any], day: str) -> tuple[float, float, set[int]]:
    """The 1-minute bar high and low over the bars starting 09:00 .. 09:29 Beijing, and their contracts."""
    a, b = C.bj(day, "09:00"), C.bj(day, "09:30")
    i0 = int(np.searchsorted(R["S"], a, side="left"))
    i1 = int(np.searchsorted(R["S"], b, side="left"))
    if i1 <= i0:
        return float("nan"), float("nan"), set()
    d = R["df"]
    return (float(d["high"].to_numpy()[i0:i1].max()), float(d["low"].to_numpy()[i0:i1].min()),
            set(int(k) for k in R["K"][i0:i1]))


def window_closes(R: dict[str, Any], day: str, limit: int) -> tuple[list[float], set[int]]:
    """P(t) for t = 09:01 .. 09:30 Beijing, skipping an isolated print rather than voiding the session (D765 voids only
    on the prices a trade uses). Never reads past `limit`."""
    t0 = C.bj(day, "09:00")
    out, ks = [], set()
    for m in range(1, 31):
        need(t0 + m <= limit, "outcome-blind: a window close after the check time was requested")
        i = C.p_at(R, t0 + m)
        if i is None or R["iso_c"][i]:
            continue
        out.append(float(R["C"][i]))
        ks.add(int(R["K"][i]))
    return out, ks


def flags_from(sx: float, closes: list[float], hi: float, lo: float, p30: float, pT: float) -> dict[str, bool]:
    """The three conditions from prices stamped no later than T. sx = sign(x): +1 an up-open (the fade sells)."""
    if sx > 0:
        return {"K1c": pT < max(closes), "K1h": pT < hi, "K2": pT < p30}
    return {"K1c": pT > min(closes), "K1h": pT > lo, "K2": pT > p30}


def path_table(R: dict[str, Any], e: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for day, x in zip(e.index, e["x"].to_numpy(float)):
        need(day < SEAL, "seal: a session on or after 2024")
        sx = 1.0 if x > 0 else -1.0
        hi, lo, kb = bar_extremes(R, day)
        t0 = C.bj(day, "09:00")
        for L in DELAYS:
            T = C.bj(day, "09:30") + L
            bl = Blind(R, T)
            p00, p30, pT = bl.p(t0), bl.p(t0 + 30), bl.p(T)          # the trade's own reference prices (voiding)
            closes, kc = window_closes(R, day, T)                      # the extreme: spikes skipped, not voiding
            q = C.Px(R)
            ent, p15 = q.o(T + 1), q.p(C.bj(day, "15:00"))
            ks = bl.q.k | q.k
            ok = (len(ks) == 1 and kc <= ks and not bl.q.void and not q.void and len(closes) >= 20
                  and all(np.isfinite(v) for v in (p00, p30, pT, ent, p15)))
            okh = ok and np.isfinite(hi) and np.isfinite(lo) and kb == ks
            f = flags_from(sx, closes, hi, lo, p30, pT) if ok else {k: False for k in CONDS}
            if not okh:
                f["K1h"] = False
            rows.append({"day": day, "L": L, "sx": sx, "ok": ok, "okh": okh, "pT": pT, "ent": ent, "p15": p15,
                         "taker_gross": -sx * (p15 - ent) * C.CELLS["mgc"]["mult"] if ok else np.nan,
                         "move": (p15 - ent) * C.CELLS["mgc"]["mult"] if ok else np.nan, **f})
    return pd.DataFrame(rows)


# ================================================================================ the passive book at each clock
def micro_at(args: tuple[str, str, dict[int, float]]) -> list[dict[str, Any]]:
    """D770's session_micro at every delay from one read of the session's files: rest at the touch at T, filled on a
    trade-through within LIFE_MIN, exit at the 15:00 touch. D770's checks: one instrument; the tape's last price
    before T within 2 ticks of the bar P(T); quotes at T, T + 1 and 15:00."""
    D86._install_seal()
    root, day, pbar = args
    need(day < SEAL, "seal: a passive session on or after 2024")
    tr, q = D7.read(root, "tbbo", day), D7.read(root, "bbo-1m", day)
    outs = []
    if tr is None or q is None:
        return [{"day": day, "L": L, "why": "no_file"} for L in pbar]
    if len(np.unique(np.r_[tr["instrument_id"], q["instrument_id"]])) != 1:
        return [{"day": day, "L": L, "why": "two_instruments"} for L in pbar]
    ts = tr["ts_recv"].astype(np.int64)
    p = D7.px(tr["price"])
    b15, a15 = D7.quote_at(q, D7.bj_ns(day, "15:00"))
    for L, pb in pbar.items():
        T = D7.bj_ns(day, "09:30") + L * 60 * 10**9
        o: dict[str, Any] = {"day": day, "L": L}
        before = np.flatnonzero(ts < T)
        last = float(p[before[-1]]) if len(before) else float("nan")
        if not (np.isfinite(last) and np.isfinite(pb) and abs(last - pb) <= D7.MISMATCH_TICKS * D7.TICK + 1e-9):
            o["why"] = "price_mismatch"
            outs.append(o)
            continue
        bT, aT = D7.quote_at(q, T)
        b1, a1 = D7.quote_at(q, T + 60 * 10**9)
        if not all(np.isfinite(v) for v in (bT, aT, b1, a1, b15, a15)):
            o["why"] = "no_quote"
            outs.append(o)
            continue
        life = T + LIFE_MIN * 60 * 10**9
        for side, nm, lvl, ex in ((-1, "sell", aT, a15), (+1, "buy", bT, b15)):
            ft = D7.first_through(ts, p, T, life, lvl, side, True)
            o[f"{nm}_filled"] = ft is not None
            o[f"{nm}_gross"] = side * (ex - lvl) * D7.MULT if ft is not None else float("nan")
            o[f"{nm}_lvl"] = lvl
        o["why"] = "ok"
        outs.append(o)
    return outs


def _micro_chunk(jobs: list[tuple]) -> list[list[dict[str, Any]]]:
    return [micro_at(j) for j in jobs]


def passive_table(jobs: list[tuple], workers: int = WORKERS) -> pd.DataFrame:
    with ProcessPoolExecutor(workers) as ex:
        parts = list(ex.map(_micro_chunk, [jobs[i::workers] for i in range(workers)]))
    res: list[Any] = [None] * len(jobs)
    for i, part in enumerate(parts):
        for j, r in enumerate(part):
            res[i + j * workers] = r
    need([r[0]["day"] for r in res] == [j[1] for j in jobs], "passive: stride reassembly lost the day order")
    return pd.DataFrame([o for r in res for o in r])


def audit_fill(day: str, L: int, rec: dict[str, Any], side: int) -> None:
    """Second implementation of one resting fill: explicit loops over the raw records."""
    D86._install_seal()
    tr, q = D7.read("GC", "tbbo", day), D7.read("GC", "bbo-1m", day)
    T = D7.bj_ns(day, "09:30") + L * 60 * 10**9
    bid = ask = None
    for r in q:
        if int(r["ts_recv"]) <= T:
            bid, ask = int(r["bid_px_00"]) / 1e9, int(r["ask_px_00"]) / 1e9
    lvl = ask if side < 0 else bid
    need(lvl == rec["sell_lvl" if side < 0 else "buy_lvl"], f"lag audit: the resting level differs on {day} L{L}")
    filled = False
    for r in tr:
        t = int(r["ts_recv"])
        if T <= t < T + LIFE_MIN * 60 * 10**9:
            px = int(r["price"]) / 1e9
            if (side < 0 and px >= lvl + D7.TICK - 1e-9) or (side > 0 and px <= lvl - D7.TICK + 1e-9):
                filled = True
                break
    need(filled == rec["sell_filled" if side < 0 else "buy_filled"], f"lag audit: the fill differs on {day} L{L}")


# ================================================================================ statistics
def rot_stats(flag: np.ndarray, g: np.ndarray, valid: np.ndarray, cost: float) -> np.ndarray:
    """Rows k = 0 .. n-1: [sum g / sum |g| over roll(flag, k) & valid, mean net, count]. Exact, every offset."""
    n = len(flag)
    g0 = np.where(valid, g, 0.0)
    a0 = np.abs(g0)
    v0 = valid.astype(float)
    f = flag.astype(float)
    out = np.empty((n, 3))
    for k in range(n):
        r = np.roll(f, k)
        cnt = float(r @ v0)
        sg, sa = float(r @ g0), float(r @ a0)
        out[k] = [sg / sa if sa > 0 else np.nan, sg / cnt - cost if cnt > 0 else np.nan, cnt]
    return out


def pct_within(v: np.ndarray) -> np.ndarray:
    """Each entry's within-distribution percentile (share of the other entries strictly below it)."""
    r = pd.Series(v).rank(method="min").to_numpy() - 1
    return r / max(len(v) - 1, 1)


def gates(g: np.ndarray, net: np.ndarray, days: np.ndarray, sigma: np.ndarray, rank_obs: float, p95: float,
          obs: float) -> dict[str, Any]:
    n = len(g)
    if n < 20:
        return {"reading": "n<20"}
    yr = np.array([d[:4] for d in days])
    years = sorted(set(yr))
    g1 = bool(g.mean() > 0 and F7.tstat(g) >= 2)
    npass = bool(obs > p95)
    va = g / sigma
    win_y = sum(float((g[yr == y] > 0).mean()) >= 0.5 for y in years)
    va_pos = sum(float(np.nanmean(va[yr == y])) > 0 for y in years if np.isfinite(va[yr == y]).any())
    a = np.nanmean(va[np.array([y <= "2019" for y in yr])]) if (yr <= "2019").any() else np.nan
    b = np.nanmean(va[np.array([y >= "2020" for y in yr])]) if (yr >= "2020").any() else np.nan
    y_ok = bool(win_y >= 6 or (va_pos >= 6 and np.isfinite(a) and np.isfinite(b) and a >= 0.5 * b))
    by = pd.Series(net).groupby(yr).sum()
    ex2 = float(by.drop(by.sort_values().index[-2:]).sum()) if len(by) > 2 else float("nan")
    g2 = bool(net.mean() > 0 and F7.tstat(net) >= 2 and ex2 > 0)
    r = "NO EFFECT" if not g1 else "NOT ABOVE NULL" if not npass else "CONCENTRATED" if not y_ok else \
        "NO PRIZE" if not g2 else "SUPPORTED"
    return {"G1": g1, "N": npass, "Y": y_ok, "G2": g2, "reading": r, "win_years": int(win_y), "va_pos_years": int(va_pos),
            "net_total_ex_best2_years": ex2}


def summarise(name: str, flag: np.ndarray, g: np.ndarray, valid: np.ndarray, cost: float, e: pd.DataFrame,
              sigma: np.ndarray, ctrl_mean_net: float) -> tuple[dict[str, Any], np.ndarray]:
    days = e.index.to_numpy()
    kept, skip = flag & valid, ~flag & valid
    rot = rot_stats(flag, g, valid, cost)
    need(int(rot[0, 2]) == int(kept.sum()), f"{name}: rotation offset 0 does not reproduce the kept count")
    gk, gs = g[kept], g[skip]
    obs = float(rot[0, 0])
    nul = rot[1:, 0]
    nul = nul[np.isfinite(nul)]
    p95 = float(np.quantile(nul, 0.95))
    rank = float((nul < obs).mean())
    win = np.isin(e["month"].to_numpy(), WINTER)
    bal = F7.balance(list(days[kept]), list(days[valid])) if kept.sum() >= 20 else {"max_month_dev_pp": float("nan")}
    out = {"cell": name, "valid": int(valid.sum()), "kept": int(kept.sum()), "kept_share": float(kept.sum() / max(valid.sum(), 1)),
           "kept_mean_gross": float(gk.mean()) if len(gk) else None, "kept_t_gross": F7.tstat(gk),
           "kept_mean_net": float(gk.mean() - cost) if len(gk) else None, "kept_t_net": F7.tstat(gk - cost),
           "skipped_mean_gross": float(gs.mean()) if len(gs) else None, "skipped_n": int(skip.sum()),
           "kept_minus_control_net": float(gk.mean() - cost - ctrl_mean_net) if len(gk) else None,
           "sum_g_over_abs": obs, "null_p50": float(np.quantile(nul, 0.5)), "null_p95": p95, "rank": rank,
           "mean_net_null_p50": float(np.nanquantile(rot[1:, 1], 0.5)), "mean_net_null_p95": float(np.nanquantile(rot[1:, 1], 0.95)),
           "rho_flag_absx": C.spearman(flag[valid].astype(float), np.abs(e["x"].to_numpy(float))[valid]),
           "B1_month_gap_pp": bal["max_month_dev_pp"], "net_outside_DecMar": float((g[kept & ~win] - cost).sum()),
           "gates": gates(gk, gk - cost, days[kept], sigma[kept], rank, p95, obs)}
    return out, rot[1:, 0]


def tercile_check(flag, g, valid, e, cost) -> dict[str, Any]:
    ax = np.abs(e["x"].to_numpy(float))
    q1, q2 = np.quantile(ax[valid], [1 / 3, 2 / 3])
    out = {}
    for nm, m in (("small", ax <= q1), ("mid", (ax > q1) & (ax <= q2)), ("large", ax > q2)):
        k, s = flag & valid & m, ~flag & valid & m
        out[nm] = {"kept_n": int(k.sum()), "kept_mean_net": float(g[k].mean() - cost) if k.any() else None,
                   "skipped_n": int(s.sum()), "skipped_mean_net": float(g[s].mean() - cost) if s.any() else None}
    return out


def splits(flag, g, valid, e, cost) -> dict[str, Any]:
    days = e.index.to_numpy()
    kept = flag & valid
    edt = e["edt"].to_numpy(bool)
    win = np.isin(e["month"].to_numpy(), WINTER)
    yr = e["year"].to_numpy()

    def s(m):
        k = kept & m
        return {"n": int(k.sum()), "mean_net": round(float(g[k].mean() - cost), 2) if k.sum() >= 20 else None}
    return {"EST": s(~edt), "EDT": s(edt), "Dec_Mar": s(win), "Apr_Nov": s(~win),
            "years": {y: s(yr == y) for y in sorted(set(yr))},
            "before_shfe_auction": s(days < AUCTION_FROM), "after_shfe_auction": s(days >= AUCTION_FROM)}


def component(e: pd.DataFrame, books: dict[str, tuple[np.ndarray, np.ndarray]]) -> dict[str, Any]:
    import stage0_d777_post_close_fade as P7
    b = P7.load_bars()
    d775 = P7.d775_daily(b)
    _, d777 = P7.daily_book(P7.panel(b, "NQ"), 4.07)
    d777 = d777.groupby(level=0).sum()
    days = e.index.to_numpy()
    base = pd.Series(e["net"].to_numpy(float), index=days)
    out: dict[str, Any] = {"not_computed": "D755's other-lines file (temp/d755_other_lines.csv) no longer exists"}
    for k, (mask, net) in books.items():
        daily = pd.Series(net[mask], index=days[mask])
        out[k] = {nm: round(float(pd.concat([daily, o], axis=1).fillna(0.0).corr().iloc[0, 1]), 3)
                  for nm, o in (("unfiltered_d765_mgc_fade", base), ("d775", d775), ("d777_mnq", d777))}
    return out


# ================================================================================ the study
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D787 is run-once")
    t0 = time.time()
    D86.sign_audit()
    try:
        D86.sign_audit(-1.0)
    except D86.D786Error:
        pass
    else:
        raise D787Error("the sign audit did not raise on a mirrored book")
    B = D86.build()
    rep = D86.reproduce(B)
    e = B["e"]
    cost_p = B["cost_p"]
    days = list(e.index)
    R = B["roots"]["GC"]
    print("D786 build reproduced", f"{time.time() - t0:.0f}s", flush=True)
    P = path_table(R, e)
    print("bar paths built", f"{time.time() - t0:.0f}s", flush=True)
    pbar = {d: dict(zip(g["L"], g["pT"])) for d, g in P.groupby("day", sort=False)}
    M = passive_table([("GC", d, pbar[d]) for d in days])
    print("passive tape read", f"{time.time() - t0:.0f}s", flush=True)
    # lag audit: the resting fill by a second implementation, on sampled (session, delay) pairs
    rng = np.random.default_rng(SEED)
    okM = M[M["why"] == "ok"].reset_index(drop=True)
    for i in sorted(rng.choice(len(okM), size=AUDIT_N, replace=False).tolist()):
        rec = okM.iloc[i].to_dict()
        audit_fill(rec["day"], int(rec["L"]), rec, -1 if i % 2 else +1)
    # lag audit: the extremes and P(T) by explicit loops on sampled sessions
    for i in sorted(rng.choice(len(days), size=AUDIT_N, replace=False).tolist()):
        d = days[i]
        sel = (R["S"] >= C.bj(d, "09:00")) & (R["S"] < C.bj(d, "09:30"))
        hi = max(float(v) for v in R["df"]["high"].to_numpy()[sel]) if sel.any() else float("nan")
        row = P[(P["day"] == d) & (P["L"] == 15)].iloc[0]
        if row["okh"]:
            sx = row["sx"]
            mine = (row["pT"] < hi) if sx > 0 else (row["pT"] > min(float(v) for v in R["df"]["low"].to_numpy()[sel]))
            need(bool(mine) == bool(row["K1h"]), f"lag audit: K1h differs on {d}")
    res: dict[str, Any] = {"spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "reproduced_d786": rep,
                           "passive_cost": cost_p, "exclusions": {}, "controls": {}, "cells": {}}
    books: dict[tuple, dict[str, np.ndarray]] = {}
    for L in DELAYS:
        Pl = P[P["L"] == L].set_index("day").reindex(days)
        Ml = M[M["L"] == L].set_index("day").reindex(days)
        sx = Pl["sx"].to_numpy(float)
        ok = Pl["ok"].to_numpy(bool)
        mok = (Ml["why"] == "ok").to_numpy(bool)
        filled = mok & np.where(sx > 0, Ml["sell_filled"].fillna(False).to_numpy(bool), Ml["buy_filled"].fillna(False).to_numpy(bool))
        gp = np.where(filled, np.where(sx > 0, Ml["sell_gross"].to_numpy(float), Ml["buy_gross"].to_numpy(float)), np.nan)
        gt = Pl["taker_gross"].to_numpy(float)
        sigma = pd.Series(np.where(ok, Pl["move"].to_numpy(float), np.nan)).shift(1).rolling(VOL_N, min_periods=VOL_MIN).std().to_numpy()
        valid_t, valid_p = ok, ok & filled
        res["exclusions"][str(L)] = {"bar_path_invalid": int((~ok).sum()), "passive": Ml["why"].value_counts().to_dict(),
                                     "passive_fill_rate": float(filled[ok & mok].mean()),
                                     "taker_gross_filled_vs_unfilled": [float(np.nanmean(gt[ok & filled])),
                                                                        float(np.nanmean(gt[ok & mok & ~filled]))]}
        books[L] = {"sx": sx, "ok": ok, "gp": gp, "gt": gt, "vt": valid_t, "vp": valid_p, "sigma": sigma, "P": Pl}
        res["controls"][str(L)] = {
            "taker": {"n": int(valid_t.sum()), "mean_gross": float(np.nanmean(gt[valid_t])), "t": F7.tstat(gt[valid_t]),
                      "mean_net": float(np.nanmean(gt[valid_t]) - TAKER_COST)},
            "passive": {"n": int(valid_p.sum()), "mean_gross": float(np.nanmean(gp[valid_p])), "t": F7.tstat(gp[valid_p]),
                        "mean_net": float(np.nanmean(gp[valid_p]) - cost_p)}}
    # right quantity: L = 0 unconditional reproduces D767 taker and D770 passive
    c0 = res["controls"]["0"]
    need(c0["taker"]["n"] == 1697 and round(c0["taker"]["mean_gross"], 2) == 3.14, f"right quantity: L0 taker {c0['taker']}")
    need(c0["passive"]["n"] == 1466 and round(c0["passive"]["mean_gross"], 2) == 2.12, f"right quantity: L0 passive {c0['passive']}")
    need(round(res["controls"]["15"]["taker"]["mean_gross"], 6) != round(c0["taker"]["mean_gross"], 6),
         "right quantity: the 09:46 taker book equals the 09:31 book")
    print("controls:", {L: (round(v["passive"]["mean_net"], 2), round(v["taker"]["mean_net"], 2)) for L, v in res["controls"].items()},
          flush=True)
    nulls, ranks_obs, keys = [], [], []
    for L in GRID_DELAYS:
        bk = books[L]
        for cond in CONDS:
            flag = bk["P"][cond].fillna(False).to_numpy(bool) & bk["ok"]
            for book in BOOKS:
                g, valid, cost = (bk["gp"], bk["vp"], cost_p) if book == "passive" else (bk["gt"], bk["vt"], TAKER_COST)
                key = f"L{L}_{cond}_{book}"
                out, nul = summarise(key, flag, g, valid, cost, e, bk["sigma"], res["controls"][str(L)][book]["mean_net"])
                res["cells"][key] = out
                nulls.append(nul)
                ranks_obs.append(out["rank"])
                keys.append(key)
    # the family-max null: one offset rotates every cell; per offset, the largest within-cell percentile
    U = np.vstack([pct_within(v) for v in nulls])
    fam = U.max(axis=0)
    best = int(np.argmax(ranks_obs))
    res["family_max"] = {"cells": len(keys), "best_cell": keys[best], "best_rank": ranks_obs[best],
                         "family_p95": float(np.quantile(fam, 0.95)), "family_p50": float(np.quantile(fam, 0.5)),
                         "p_family": float((1 + (fam >= ranks_obs[best]).sum()) / (1 + len(fam)))}
    for i, k in enumerate(keys):
        res["cells"][k]["above_family_p95"] = bool(ranks_obs[i] > res["family_max"]["family_p95"])
    # the best passive and taker cells: four groups, terciles, splits, component line
    detail, comp_books = {}, {}
    for book in BOOKS:
        ks = [k for k in keys if k.endswith(book)]
        kb = max(ks, key=lambda k: res["cells"][k]["rank"])
        L = int(kb.split("_")[0][1:])
        cond = kb.split("_")[1]
        bk = books[L]
        flag = bk["P"][cond].fillna(False).to_numpy(bool) & bk["ok"]
        g, valid, cost = (bk["gp"], bk["vp"], cost_p) if book == "passive" else (bk["gt"], bk["vt"], TAKER_COST)
        kept = flag & valid
        dd = e.index.to_numpy()
        detail[kb] = {"four_groups": D86.book_stats(g[kept], g[kept] - cost, dd[kept]),
                      "control_four_groups": D86.book_stats(g[valid], g[valid] - cost, dd[valid]),
                      "absx_terciles": tercile_check(flag, g, valid, e, cost), "splits": splits(flag, g, valid, e, cost)}
        comp_books[kb] = (kept, np.where(kept, g - cost, np.nan))
    res["best_cells"] = detail
    res["component_line"] = component(e, comp_books)
    tri = [k for k in keys if k.endswith("passive") and res["cells"][k]["gates"].get("N") and res["cells"][k]["above_family_p95"]
           and res["cells"][k]["gates"].get("G2") and res["cells"][k]["gates"].get("Y")]
    res["triage_bar_cleared_by"] = tri
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    for k in keys:
        c = res["cells"][k]
        print(f"{k:18s} kept {c['kept']:4d} ({c['kept_share']:.2f}) net {c['kept_mean_net']:+6.2f} t {c['kept_t_net']:+.2f} "
              f"| skip gross {c['skipped_mean_gross']:+6.2f} | vs ctrl {c['kept_minus_control_net']:+.2f} | rank {c['rank']:.3f} "
              f"| {c['gates']['reading']}", flush=True)
    print("family:", res["family_max"], "| triage:", tri, f"| {res['wall_s']}s ->", OUT.relative_to(REPO), flush=True)
    return 0


# ================================================================================ self-test
def selftest() -> int:
    t0 = time.time()
    # the flags, by hand: an up-open back below its peak is kept; at the peak (a tie) it is not; down mirrors
    cl = [100.0, 101.0, 102.0, 101.5]
    need(flags_from(1, cl, 102.2, 99.8, 101.5, 101.9) == {"K1c": True, "K1h": True, "K2": False}, "flags: up-open")
    need(flags_from(1, cl, 102.2, 99.8, 101.5, 102.0)["K1c"] is False, "flags: a tie at the peak was kept")
    dn = [100.0, 99.0, 98.0, 98.5]
    need(flags_from(-1, dn, 100.2, 97.8, 98.5, 98.9) == {"K1c": True, "K1h": True, "K2": True}, "flags: down-open")
    need(flags_from(-1, dn, 100.2, 97.8, 98.5, 97.9) == {"K1c": False, "K1h": True, "K2": False}, "flags: down-open extended")
    # the outcome-blind reader raises on a price after T
    R = C.load_root("GC")
    d = "2022-03-01"
    T = C.bj(d, "09:45")
    bl = Blind(R, T)
    bl.p(T)
    try:
        bl.p(T + 1)
    except D787Error:
        pass
    else:
        raise D787Error("outcome-blind: a P(09:46) request was not refused")
    # the seal: the paid reader refuses a 2024 file; the bar loader's seal is D765's (raises on a 2024 bar)
    try:
        D86.sealed_read(lambda r, s, dd: None)("GC", "tbbo", "2024-01-02")
    except D86.D786Error:
        pass
    else:
        raise D787Error("seal: the paid reader did not refuse a 2024 file")
    need(bool((R["df"]["day"] < SEAL).all()), "seal: the GC bars reach 2024")
    # the null fires: a planted flag that keeps the winners passes, a shuffled one does not
    rng = np.random.default_rng(3)
    n = 1500
    g = rng.standard_t(3, n) * 30 + 2
    valid = rng.random(n) < 0.9
    flag = (g + rng.normal(scale=60, size=n)) > 0
    r1 = rot_stats(flag, g, valid, 3.0)
    need(float((r1[1:, 0] < r1[0, 0]).mean()) > 0.95, "null: a planted flag did not pass")
    shuffled = [rot_stats(rng.permutation(flag), g, valid, 3.0) for _ in range(20)]
    ranks0 = [float((r[1:, 0] < r[0, 0]).mean()) for r in shuffled]
    need(sum(r > 0.95 for r in ranks0) <= 4, f"null: shuffled flags pass too often ({ranks0})")
    need(0.2 < float(np.median(ranks0)) < 0.8, f"null: shuffled flags are not centred ({ranks0})")
    # rot_stats against a loop over np.roll and boolean masks (second implementation), on a tie-heavy input
    gi = np.round(g / 10) * 10
    rs = rot_stats(flag, gi, valid, 3.0)
    for k in (0, 1, 7, 500, n - 1):
        m = np.roll(flag, k) & valid
        need(abs(rs[k, 0] - gi[m].sum() / np.abs(gi[m]).sum()) < 1e-12 and int(rs[k, 2]) == int(m.sum()),
             f"rot_stats differs from the mask loop at offset {k}")
    # the family-max percentile is a percentile
    u = pct_within(np.array([3.0, 1.0, 2.0, 2.0]))
    need(np.allclose(u, [1.0, 0.0, 1 / 3, 1 / 3]), f"pct_within {u}")
    # the passive table: stride == serial, bit for bit, on real sessions at two delays
    days = [x.strftime("%Y-%m-%d") for x in pd.bdate_range("2022-03-01", "2022-03-14")][:8]
    jobs = []
    for dd in days:
        q = C.Px(R)
        jobs.append(("GC", dd, {0: q.p(C.bj(dd, "09:30")), 15: q.p(C.bj(dd, "09:45"))}))
    a = pd.DataFrame([o for j in jobs for o in micro_at(j)])
    b = passive_table(jobs, workers=3)
    need(a.astype(str).equals(b.astype(str)), "passive: chunk != whole")
    need((a["why"] == "ok").sum() >= 8, f"passive: too few real sessions read in the self-test ({a['why'].tolist()})")
    # the fill audit raises on a wrong fill flag
    rec = a[(a["why"] == "ok")].iloc[0].to_dict()
    audit_fill(rec["day"], int(rec["L"]), rec, -1)
    bad = dict(rec)
    bad["sell_filled"] = not rec["sell_filled"]
    try:
        audit_fill(rec["day"], int(rec["L"]), bad, -1)
    except D787Error:
        pass
    else:
        raise D787Error("lag audit: a wrong fill flag was not caught")
    print(f"selftest OK ({time.time() - t0:.0f}s)", flush=True)
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
    return 1


if __name__ == "__main__":
    sys.exit(main())
