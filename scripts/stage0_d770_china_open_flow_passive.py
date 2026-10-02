"""D770 Stage 0: gold's China-open fade with real order flow and a passive entry.
Spec: docs/decisions/D770-STAGE-0-PRE-REG-real-flow-and-passive-entry-at-the-china-open.md.

    python scripts/stage0_d770_china_open_flow_passive.py --selftest     # SYSTEM interpreter (databento, pyarrow)
    python scripts/stage0_d770_china_open_flow_passive.py --run --lines temp/d755_other_lines.csv

The candidates and x are D765's (its functions, its extraction cache). The order flow and quotes are the PAID GC/MGC
`tbbo` + `bbo-1m` China window (read-only; never modified): `B` trades are buyer-initiated (+1), `A` seller-initiated
(-1). Every clock is a UTC nanosecond. Beijing is UTC+8.
"""
from __future__ import annotations

import argparse
import datetime as dt
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

SPEC = REPO / "docs" / "decisions" / "D770-STAGE-0-PRE-REG-real-flow-and-passive-entry-at-the-china-open.md"
OUT = REPO / "data" / "stage0_d770_china_open_flow_passive.json"
PAID = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento/china_window_2016_2023")
SEAL_NS = int(pd.Timestamp("2024-01-01", tz="UTC").value)
TICK = 0.1
MULT = 10.0                     # MGC $ per point
COMMISSION = 3.00               # MGC commission a round trip (futures_costs.json, micro commission_rt_usd)
TAKER_COST = 5.93               # D765's MGC cost line (commission + 2.93 crossing ticks)
MISMATCH_TICKS = 2
QUOTE_STALE_NS = 3 * 60 * 10**9
LIFE_MIN, SHORT_LIFE_MIN = 30, 10
WORKERS = 8
UNDEF = 2**63 - 1


class D770Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D770Error(msg)


def bj_ns(day: str, hhmm: str) -> int:
    return C.bj(day, hhmm) * 60 * 10**9


# ================================================================================ reading the paid window
def read(root: str, schema: str, day: str) -> np.ndarray | None:
    import databento as db
    p = PAID / f"{root}_{schema}" / day[:4] / f"{day}.dbn.zst"
    if not p.exists():
        return None
    arrs = list(db.DBNStore.from_bytes(p.read_bytes()).to_ndarray(count=1 << 22))
    a = np.concatenate(arrs) if arrs else None
    if a is None or len(a) == 0:
        return None
    need(bool((a["ts_recv"].astype(np.int64) < SEAL_NS).all()), f"seal: a {root} {schema} record on or after 2024 ({day})")
    return a


def px(v: np.ndarray) -> np.ndarray:
    v = v.astype(np.int64)
    return np.where((v == UNDEF) | (v <= 0), np.nan, v / 1e9)


def quote_at(q: np.ndarray, t: int) -> tuple[float, float]:
    """The best bid and ask at t: the latest bbo-1m record stamped at or before t, no older than 3 minutes."""
    ts = q["ts_recv"].astype(np.int64)
    i = int(np.searchsorted(ts, t, side="right")) - 1
    if i < 0 or ts[i] < t - QUOTE_STALE_NS:
        return float("nan"), float("nan")
    b, a = float(px(q["bid_px_00"][i:i + 1])[0]), float(px(q["ask_px_00"][i:i + 1])[0])
    return (b, a) if np.isfinite(b) and np.isfinite(a) and a > b else (float("nan"), float("nan"))


def first_through(ts: np.ndarray, p: np.ndarray, t0: int, t1: int, level: float, side: int, through: bool) -> int | None:
    """The first trade in [t0, t1) priced through (or at) a resting order: a sell rests at `level` (side -1) and fills
    when price >= level + tick (>= level at the touch); a buy (side +1) mirrors it."""
    m = (ts >= t0) & (ts < t1)
    if not m.any():
        return None
    q = p[m]
    eps = 1e-9
    hit = (q >= level + TICK - eps) if side < 0 and through else (q >= level - eps) if side < 0 else \
          (q <= level - TICK + eps) if through else (q <= level + eps)
    k = np.flatnonzero(hit)
    return int(ts[m][k[0]]) if len(k) else None


def session_micro(args: tuple[str, str, float]) -> dict[str, Any]:
    """Everything one session needs from the paid window, for one root (GC or MGC)."""
    root, day, p930_bar = args
    out: dict[str, Any] = {"day": day, "root": root}
    tr, q = read(root, "tbbo", day), read(root, "bbo-1m", day)
    if tr is None or q is None:
        out["why"] = "no_file"
        return out
    ids = np.unique(np.r_[tr["instrument_id"], q["instrument_id"]])
    if len(ids) != 1:
        out["why"] = "two_instruments"
        return out
    ts = tr["ts_recv"].astype(np.int64)
    p = px(tr["price"])
    sz = tr["size"].astype(np.int64)
    sd = tr["side"]
    t0, t30, t31 = bj_ns(day, "09:00"), bj_ns(day, "09:30"), bj_ns(day, "09:31")
    t40, t1000, t15 = bj_ns(day, "09:40"), bj_ns(day, "10:00"), bj_ns(day, "15:00")
    before = np.flatnonzero(ts < t30)
    out["last_px_0930"] = float(p[before[-1]]) if len(before) else float("nan")
    if root == "GC":
        if not (np.isfinite(out["last_px_0930"]) and abs(out["last_px_0930"] - p930_bar) <= MISMATCH_TICKS * TICK + 1e-9):
            out["why"] = "price_mismatch"
            return out
    w = (ts >= t0) & (ts < t30)
    out["B"] = int(sz[w & (sd == b"B")].sum())
    out["S"] = int(sz[w & (sd == b"A")].sum())
    out["N"] = int(sz[w & (sd == b"N")].sum())
    b30, a30 = quote_at(q, t30)
    b31, a31 = quote_at(q, t31)
    b15, a15 = quote_at(q, t15)
    b10, a10 = quote_at(q, t1000)
    out.update({"bid30": b30, "ask30": a30, "bid31": b31, "ask31": a31, "bid15": b15, "ask15": a15, "bid10": b10, "ask10": a10})
    if not all(np.isfinite(v) for v in (b30, a30, b31, a31, b15, a15)):
        out["why"] = "no_quote"
        return out
    # both sides' passive outcomes (side -1: sell at the ask; +1: buy at the bid), every rule
    for side, nm, lvl, ex in ((-1, "sell", a30, a15), (+1, "buy", b30, b15)):
        for rule, thr, life in (("through", True, t1000), ("touch", False, t1000), ("through10", True, t40)):
            ft = first_through(ts, p, t30, life, lvl, side, thr)
            out[f"{nm}_{rule}_filled"] = ft is not None
            out[f"{nm}_{rule}_gross"] = side * (ex - lvl) * MULT if ft is not None else float("nan")
        # unfilled at 10:00: cross at the 10:00 touch (variant)
        if not out[f"{nm}_through_filled"] and np.isfinite(b10) and np.isfinite(a10):
            e = b10 if side < 0 else a10
            out[f"{nm}_cross10_gross"] = side * (ex - e) * MULT
        else:
            out[f"{nm}_cross10_gross"] = out[f"{nm}_through_gross"]
    # Q1: taker on quotes, both sides
    out["sell_taker_gross"] = -1 * (a15 - b31) * MULT
    out["buy_taker_gross"] = +1 * (b15 - a31) * MULT
    out["spread31_ticks"] = (a31 - b31) / TICK
    out["spread15_ticks"] = (a15 - b15) / TICK
    out["why"] = "ok"
    return out


# ================================================================================ the second implementation (audit)
def audit_session(root: str, day: str, rec: dict[str, Any]) -> None:
    """Explicit loops over the raw records: B, S, the 09:30 quote and the primary fill, without the functions above."""
    tr, q = read(root, "tbbo", day), read(root, "bbo-1m", day)
    t0, t30, t1000 = bj_ns(day, "09:00"), bj_ns(day, "09:30"), bj_ns(day, "10:00")
    B = S = 0
    for r in tr:
        t = int(r["ts_recv"])
        if t0 <= t < t30:
            if r["side"] == b"B":
                B += int(r["size"])
            elif r["side"] == b"A":
                S += int(r["size"])
    need(B == rec["B"] and S == rec["S"], f"lag audit: flow differs on {day}")
    bid = ask = None
    for r in q:
        if int(r["ts_recv"]) <= t30:
            bid, ask = int(r["bid_px_00"]) / 1e9, int(r["ask_px_00"]) / 1e9
    need(bid == rec["bid30"] and ask == rec["ask30"], f"lag audit: the 09:30 quote differs on {day}")
    filled = False
    for r in tr:
        t = int(r["ts_recv"])
        if t30 <= t < t1000 and int(r["price"]) / 1e9 >= ask + TICK - 1e-9:
            filled = True
            break
    need(filled == rec["sell_through_filled"], f"lag audit: the sell fill differs on {day}")


def sign_audit(mirror: float = 1.0) -> None:
    """In money: a passive sell filled at 100.0 and covered at 99.0 pays +$10 at one MGC; a B trade adds to B."""
    g = mirror * -1 * (99.0 - 100.0) * MULT
    need(g > 0, "sign audit: a filled passive sell followed by a fall did not pay")


# ================================================================================ the run
def run(lines: Path | None) -> int:
    from backtest_framework.validation import filter_oracle as FO
    from stage0_d755_ecb_press_conference import book
    need(not OUT.exists(), f"{OUT.name} exists: D770 is run-once")
    t_start = time.time()
    sign_audit()
    fm, hol = C._front_map(), C.load_holidays()
    s, _ = C.build_sessions(C.load_root("GC"), "mgc", fm, hol)
    e = s[(s["why"] == "eligible") & (s["x"] != 0)].reset_index(drop=True)
    # D765's bar price at 09:30 (the mismatch check)
    R = C.load_root("GC")
    p930 = [float(R["C"][C.p_at(R, C.bj(d, "09:30"))]) for d in e["day"]]
    jobs = [("GC", d, p) for d, p in zip(e["day"], p930)]
    with ProcessPoolExecutor(WORKERS) as ex:
        gc = list(ex.map(session_micro, jobs, chunksize=8))
    mjobs = [("MGC", d, p) for d, p in zip(e["day"], p930) if d >= "2022-01-03"]
    with ProcessPoolExecutor(WORKERS) as ex:
        mg = list(ex.map(session_micro, mjobs, chunksize=8))
    G = pd.DataFrame(gc)
    counts = G["why"].value_counts().to_dict()
    need(sum(counts.values()) == len(e), "right quantity: sessions read != used + exclusions")
    ok = (G["why"] == "ok").to_numpy()
    e = e[ok].reset_index(drop=True)
    G = G[ok].reset_index(drop=True)
    need((e["day"].to_numpy() == G["day"].to_numpy()).all(), "join: day order")
    rng = np.random.default_rng(770)
    for i in sorted(rng.choice(len(G), size=min(40, len(G)), replace=False)):
        audit_session("GC", G.at[i, "day"], G.iloc[i].to_dict())
    res: dict[str, Any] = {"spec": SPEC.name, "seal": "nothing on or after 2024-01-01", "candidates_read": int(len(ok)),
                           "exclusions": counts, "used": int(len(e))}
    x = e["x"].to_numpy(float)
    side = -np.sign(x)
    gross_taker = side * e["y"].to_numpy(float) * MULT
    net_taker = gross_taker - TAKER_COST
    days = list(e["day"])

    # ---------------- Q1: the quoted cost
    M = pd.DataFrame(mg)
    Mok = M[M["why"] == "ok"].reset_index(drop=True)
    gq = G.set_index("day")
    q1 = {"GC_spread31_ticks_mean": float(G["spread31_ticks"].mean()), "GC_spread31_ticks_median": float(G["spread31_ticks"].median()),
          "GC_spread15_ticks_mean": float(G["spread15_ticks"].mean()), "GC_spread15_ticks_median": float(G["spread15_ticks"].median()),
          "GC_taker_rt_crossing_ticks": float(((G["spread31_ticks"] + G["spread15_ticks"]) / 2).mean()),
          "cost_file_crossing_ticks": 2.93}
    if len(Mok):
        both = Mok.set_index("day").join(gq[["spread31_ticks", "spread15_ticks"]], rsuffix="_gc", how="inner")
        q1.update({"MGC_sessions": int(len(Mok)), "MGC_spread31_ticks_mean": float(Mok["spread31_ticks"].mean()),
                   "MGC_spread15_ticks_mean": float(Mok["spread15_ticks"].mean()),
                   "MGC_taker_rt_crossing_ticks": float(((Mok["spread31_ticks"] + Mok["spread15_ticks"]) / 2).mean()),
                   "MGC_minus_GC_spread15_ticks": float((both["spread15_ticks"] - both["spread15_ticks_gc"]).mean()),
                   "MGC_minus_GC_spread31_ticks": float((both["spread31_ticks"] - both["spread31_ticks_gc"]).mean())})
    res["Q1"] = q1

    # ---------------- the MGC calibration
    adj = 0.0
    cal: dict[str, Any] = {}
    if len(Mok):
        j = Mok.set_index("day").join(gq, rsuffix="_gc", how="inner")
        sd = -np.sign(e.set_index("day").loc[j.index, "x"].to_numpy(float))
        mf = np.where(sd < 0, j["sell_through_filled"], j["buy_through_filled"]).astype(bool)
        gf = np.where(sd < 0, j["sell_through_filled_gc"], j["buy_through_filled_gc"]).astype(bool)
        half_m = (j["ask15"] - j["bid15"]) / 2
        half_g = (j["ask15_gc"] - j["bid15_gc"]) / 2
        adj = float(((half_m - half_g) * MULT).mean())
        mg_g = np.where(sd < 0, j["sell_through_gross"], j["buy_through_gross"])
        gp_g = np.where(sd < 0, j["sell_through_gross_gc"], j["buy_through_gross_gc"])
        mgn = mg_g[np.isfinite(mg_g)] - COMMISSION
        gpn = gp_g[np.isfinite(gp_g)] - COMMISSION - adj
        se = math.sqrt(np.var(mgn, ddof=1) / len(mgn) + np.var(gpn, ddof=1) / len(gpn)) if len(mgn) > 2 and len(gpn) > 2 else float("nan")
        cal = {"sessions": int(len(j)), "fill_agreement": float((mf == gf).mean()), "MGC_fill_rate": float(mf.mean()),
               "GC_fill_rate": float(gf.mean()), "exit_adj_usd": adj, "MGC_book_mean_net": float(mgn.mean()),
               "MGC_book_n": int(len(mgn)), "GCproxy_book_mean_net_same_sessions": float(gpn.mean()),
               "GCproxy_n": int(len(gpn)), "diff_se": se}
        cal["pass"] = bool(cal["fill_agreement"] >= 0.85 and np.isfinite(se) and abs(cal["MGC_book_mean_net"] - cal["GCproxy_book_mean_net_same_sessions"]) <= 2 * se)
    res["calibration"] = cal

    # ---------------- Q2: the real-flow filter (taker, $5.93)
    Bv, Sv = G["B"].to_numpy(float), G["S"].to_numpy(float)
    A = np.where(Bv + Sv > 0, np.sign(x) * (Bv - Sv) / np.maximum(Bv + Sv, 1), np.nan)
    sel = F7.wf_select(A)
    F7.audit_flags(A, sel)
    pool = F7.pool_mask(A)
    third = np.zeros(len(A), bool)
    rot = F7.rotation(A, net_taker, third)
    need(abs(rot[0, 0] - net_taker[sel].mean()) < 1e-9, "right quantity: Q2 rotation offset 0 != observed")
    d1 = rot[1:, 0]
    g1 = {"n": int(len(gross_taker)), "mean_gross": float(gross_taker.mean()), "t_gross": F7.tstat(gross_taker)}
    g1["pass"] = bool(g1["mean_gross"] > 0 and g1["t_gross"] >= 2)
    nul = {"observed": float(rot[0, 0]), "p50": float(np.nanquantile(d1, 0.5)), "p95": float(np.nanquantile(d1, 0.95)),
           "rank": float(np.nanmean(d1 < rot[0, 0])), "offsets": int(len(d1))}
    nul["pass"] = bool(nul["observed"] > nul["p95"])
    impact = np.abs(x) / np.maximum(np.abs(Bv - Sv), 1)
    acc = {"spearman_A_gross": C.spearman(A[pool], gross_taker[pool]), "auc_A_oracle": FO.auc(A[pool], net_taker[pool] > 0),
           "spearman_impact_gross": C.spearman(impact[pool], gross_taker[pool]), "pool": int(pool.sum())}
    eq = e.assign(gross=gross_taker)
    b2 = F7.book_of(eq.set_index("day"), sel, TAKER_COST, 1.0, lines)
    pool_days = [d for d, pp in zip(days, pool) if pp]
    bal = F7.balance([d for d, s_ in zip(days, sel) if s_], pool_days)
    res["Q2"] = {"G1": g1, "N": nul, "accuracy": acc, "balance": bal, "book": b2, "selected": int(sel.sum())}

    # ---------------- Q3: the passive fade
    fs = {r: np.where(side < 0, G[f"sell_{r}_filled"], G[f"buy_{r}_filled"]).astype(bool) for r in ("through", "touch", "through10")}
    gs = {r: np.where(side < 0, G[f"sell_{r}_gross"], G[f"buy_{r}_gross"]).astype(float) for r in ("through", "touch", "through10", "cross10")}
    cost_p = COMMISSION + adj
    filled = fs["through"]
    net_p = gs["through"] - cost_p
    # the exact rotation of the fade side over precomputed two-sided outcomes
    sell_g, buy_g = G["sell_through_gross"].to_numpy(float), G["buy_through_gross"].to_numpy(float)
    n = len(side)
    obs = float(np.nanmean(net_p))
    dist = np.empty(n - 1)
    for k in range(1, n):
        sk = np.roll(side, k)
        g_ = np.where(sk < 0, sell_g, buy_g) - cost_p
        dist[k - 1] = np.nanmean(g_)
    r0 = np.nanmean(np.where(side < 0, sell_g, buy_g) - cost_p)
    need(abs(r0 - obs) < 1e-12, "right quantity: Q3 rotation offset 0 != observed")
    need(bool((fs["through"] <= fs["touch"]).all()), "right quantity: a trade-through fill that is not a touch fill")
    nul3 = {"observed": obs, "p50": float(np.quantile(dist, 0.5)), "p95": float(np.quantile(dist, 0.95)),
            "rank": float(np.mean(dist < obs)), "offsets": int(len(dist))}
    nul3["pass"] = bool(obs > nul3["p95"])
    ep = e.assign(gross=gs["through"])
    b3 = F7.book_of(ep.set_index("day"), filled, cost_p, 1.0, lines)
    all_days_pool = days
    bal3 = F7.balance([d for d, f in zip(days, filled) if f], all_days_pool)
    adv = {"fill_rate": float(filled.mean()), "taker_gross_filled": float(gross_taker[filled].mean()),
           "taker_gross_unfilled": float(gross_taker[~filled].mean()),
           "touch_fill_rate": float(fs["touch"].mean()), "touch_mean_net": float(np.nanmean(gs["touch"] - cost_p)),
           "through10_fill_rate": float(fs["through10"].mean()), "through10_mean_net": float(np.nanmean(gs["through10"] - cost_p)),
           "cross10_mean_net_all": float(np.nanmean(gs["cross10"] - cost_p)),
           "passive_with_A_third_mean_net": float(np.nanmean(net_p[sel & filled])) if (sel & filled).any() else None,
           "passive_with_A_third_n": int((sel & filled).sum())}
    res["Q3"] = {"N": nul3, "balance": bal3, "book": b3, "adverse_selection": adv, "cost_per_trade": cost_p}

    # ---------------- the gates and readings
    hp = F7.holm({"Q2": b2["one_sided_p"], "Q3": b3["one_sided_p"]})
    for q, b, bl in (("Q2", b2, bal), ("Q3", b3, bal3)):
        b["holm_p"] = hp[q]
        res[q]["G2"] = bool(b["book"]["mean_net"] > 0 and np.isfinite(b["t_net"]) and b["t_net"] >= 2 and hp[q] < 0.05
                            and b["net_ex_best_two_years"] > 0)
        res[q]["B1"] = bool(bl["max_month_dev_pp"] <= F7.BALANCE_PP)
        res[q]["B2"] = bool(b["outside_dec_mar"]["total_net"] > 0)
    r2 = res["Q2"]
    res["Q2"]["reading"] = ("NO MECHANISM" if not r2["G1"]["pass"] else "NOT ABOVE NULL" if not r2["N"]["pass"]
                            else "UNBALANCED" if not (r2["B1"] and r2["B2"]) else "MECHANISM ONLY" if not r2["G2"] else "SUPPORTED")
    r3 = res["Q3"]
    res["Q3"]["reading"] = ("NOT ABOVE NULL" if not r3["N"]["pass"] else "UNBALANCED" if not (r3["B1"] and r3["B2"])
                            else "CALIBRATION FAILS" if not cal.get("pass", False) else "NO PRIZE" if not r3["G2"] else "SUPPORTED")
    res["GO"] = bool(res["Q2"]["reading"] == "SUPPORTED" or res["Q3"]["reading"] == "SUPPORTED")
    res["runtime_min"] = round((time.time() - t_start) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"used": res["used"], "exclusions": counts, "Q1": q1, "calibration": cal,
                      "Q2": {"reading": r2["reading"], "G1": g1, "N": nul, "acc": acc, "net": b2["book"]["mean_net"], "t": b2["t_net"]},
                      "Q3": {"reading": r3["reading"], "N": nul3, "net": b3["book"]["mean_net"], "t": b3["t_net"], "n": b3["book"]["trades"],
                             "adverse": adv}, "GO": res["GO"]}, default=float, indent=1), flush=True)
    return 0


# ================================================================================ self-test
def selftest() -> int:
    sign_audit()
    try:
        sign_audit(-1.0)
        raise SystemExit("FAIL: the sign audit did not raise on a mirrored book")
    except D770Error:
        pass
    ts = np.array([10, 20, 30, 40], dtype=np.int64)
    # a resting sell at 100.0: a print at 100.0 is a touch, 100.1 is through
    p_touch = np.array([99.9, 100.0, 100.0, 99.8])
    p_thru = np.array([99.9, 100.0, 100.1, 99.8])
    need(first_through(ts, p_touch, 0, 100, 100.0, -1, True) is None, "fill: a touch filled under the trade-through rule")
    need(first_through(ts, p_touch, 0, 100, 100.0, -1, False) == 20, "fill: the touch rule missed a touch")
    need(first_through(ts, p_thru, 0, 100, 100.0, -1, True) == 30, "fill: a trade-through did not fill")
    need(first_through(ts, p_thru, 0, 25, 100.0, -1, True) is None, "fill: a print after the order's life filled it")
    p_buy = np.array([100.1, 100.0, 99.9, 100.2])
    need(first_through(ts, p_buy, 0, 100, 100.0, +1, True) == 30 and first_through(ts, p_buy, 0, 100, 100.0, +1, False) == 20,
         "fill: the buy side mirrors wrongly")
    # quote_at reads at or before t and refuses stale quotes
    q = np.zeros(3, dtype=[("ts_recv", "u8"), ("bid_px_00", "i8"), ("ask_px_00", "i8")])
    q["ts_recv"] = [0, 60 * 10**9, 120 * 10**9]
    q["bid_px_00"] = [int(99.9e9), int(100.0e9), int(100.1e9)]
    q["ask_px_00"] = [int(100.0e9), int(100.1e9), int(100.2e9)]
    need(quote_at(q, 90 * 10**9) == (100.0, 100.1), "quote: not the latest at or before t")
    need(all(math.isnan(v) for v in quote_at(q, 120 * 10**9 + QUOTE_STALE_NS + 1)), "quote: a stale quote was used")
    # the rotation helpers are D767's: chunk == whole on 4 processes
    rng = np.random.default_rng(5)
    u, net = rng.normal(size=400), rng.normal(size=400)
    z = np.zeros(400, bool)
    r1 = F7.rotation(u, net, z, workers=1, wf=60, wf_min=40)
    r4 = F7.rotation(u, net, z, workers=4, wf=60, wf_min=40)
    need(np.array_equal(r1, r4, equal_nan=True), "chunk != whole: the rotation on processes differs")
    # a real session from the paid window parses, and the second implementation agrees with it
    day = "2019-07-10"
    rec = session_micro(("GC", day, float("nan")))
    need(rec["why"] == "price_mismatch", "self-test: the mismatch guard did not fire on a NaN bar price")
    tr = read("GC", "tbbo", day)
    p930 = float(px(tr["price"])[np.flatnonzero(tr["ts_recv"].astype(np.int64) < bj_ns(day, "09:30"))[-1]])
    rec = session_micro(("GC", day, p930))
    need(rec["why"] == "ok", f"self-test: {day} did not parse ({rec['why']})")
    audit_session("GC", day, rec)
    bad = dict(rec)
    bad["B"] += 1
    try:
        audit_session("GC", day, bad)
        raise SystemExit("FAIL: the session audit did not raise on a broken flow count")
    except D770Error:
        pass
    print(f"SELFTEST OK: sign in money (raises on a mirrored book); the trade-through and touch rules, both sides, the "
          f"order's life; quotes at or before t, stale refused; chunk == whole on 4 processes; a paid session ({day}: "
          f"B {rec['B']}, S {rec['S']}, spread {rec['spread31_ticks']:.0f}/{rec['spread15_ticks']:.0f} ticks) parses, the "
          f"mismatch guard fires, and the second implementation agrees and raises on a broken count")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lines", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.run:
        return run(a.lines)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
