"""D719: F2, unchanged, at the commodity settlement windows -- a transfer test on twelve roots (KE deferred, D719-A1),
each at the biggest viable size for a $50k prop account, with the oracle profile reported beside. Spec:
docs/decisions/D719-PRE-REG-f2-at-the-commodity-settlement-windows.md (f4930141, with A1 a1e0a7ed and A2 b00f59b7).

    python scripts/build_d719_commodity_bars.py                              # system python: the bar cache
    uv run python scripts/stage1_d719_commodity_settlement_f2.py --selftest
    uv run python scripts/stage1_d719_commodity_settlement_f2.py --run      # once

Per root: decision T = W - 30 min (W = the settlement window's end), signal the prior 60 minutes' sign, exit at the
close of the window's last minute; a = |F| / sigma_F (252, >= 60, shifted); b = 5-minute realised vol from the band's
open to T; TAKE when tiers((tiers(a) + tiers(b)) / 2) >= 0.8. Size from the burn-in only. Gates: (a) gross HAC t,
Holm across twelve; (b) direction efficiency above the exact p95 of the enumerated input rotation; (c) net > 0.
In-sample 2016-01-04 -> 2023-12-29. Writes data/stage1_d719_commodity_settlement_f2.json (statistics only).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import diag_d711_trims_and_overlap as T0  # noqa: E402
import stage1_d711_f2_mechanism as M  # noqa: E402

E, D, C, P694 = M.E, M.D, M.C, M.P694
FIX = REPO / "data" / "fixtures" / "fut_day1m.parquet"
CACHE = REPO / "temp" / "d719_bars"
STRIP = REPO / "data" / "fixtures" / "fut_settle_strip.csv.gz"
COSTS = REPO / "data" / "futures_costs.json"
OUT = REPO / "data" / "stage1_d719_commodity_settlement_f2.json"
IN_FROM, IN_END, SEAL = "2016-01-04", "2023-12-29", "2024-01-01"
ROOTS = ("CL", "NG", "HO", "RB", "HG", "GC", "SI", "ZC", "ZS", "ZW", "ZL", "ZM")
NOT_INDEPENDENT = ("NG", "CL", "GC", "SI")
W_END = {"CL": "14:30", "NG": "14:30", "HO": "14:30", "RB": "14:30", "HG": "13:00", "GC": "13:30", "SI": "13:25",
         "ZC": "14:15", "ZS": "14:15", "ZW": "14:15", "ZL": "14:15", "ZM": "14:15"}
BAND_OPEN = {r: ("09:30" if r in ("ZC", "ZS", "ZW", "ZL", "ZM") else "09:00") for r in ROOTS}
MICRO_SHARE = {"CL": 0.1, "NG": 0.1, "HG": 0.1, "GC": 0.1, "SI": 0.2, "ZC": 0.1, "ZS": 0.1, "ZW": 0.1, "ZL": 0.1, "ZM": 0.1}
GRAIN_MICRO_TICK = {"ZC": 2.5, "ZS": 2.5, "ZW": 2.5, "ZL": 1.2, "ZM": 2.0}
LOSS_LIMIT, N_FULL_MAX, N_MICRO_MAX = 1000.0, 5, 50
MIN_TRADES = 60
KNOWN_NQ = {"trades": 274, "mean_net": 20.67010517126089}


class D719Error(RuntimeError):
    pass


def hm(t: str, minutes: int) -> str:
    return (pd.Timestamp("2000-01-01 " + t) + pd.Timedelta(minutes=minutes)).strftime("%H:%M")


def mins(t: str) -> int:
    return int(t[:2]) * 60 + int(t[3:])


# ================================================================================ costs
def cost_lines(root: str) -> dict[str, Any]:
    c = json.loads(COSTS.read_text(encoding="utf-8"))["roots"][root]
    f, m = c["full"], c.get("micro") or {}
    out = {"full": {"usd_per_point": float(f["usd_per_point"]), "tick_usd": float(f["tick_usd"]),
                    "cost": float(f["commission_rt_usd"]["value"]) + float(f["crossing_ticks_rt"][f["default_line"]]["value"]) * float(f["tick_usd"])}}
    if m.get("symbol"):
        out["micro"] = {"symbol": m["symbol"], "share": float(m["usd_per_point"]) / float(f["usd_per_point"]),
                        "cost": float(m["commission_rt_usd"]["value"]) + float(m["crossing_ticks_rt"][m["default_line"]]["value"]) * float(m["tick_usd"])}
    elif root in GRAIN_MICRO_TICK:
        out["micro"] = {"symbol": "MZ" + root[1], "share": 0.1, "cost": 3.0 + GRAIN_MICRO_TICK[root],
                        "note": "not in the table: $3 + one micro tick (D719 s.2), band two ticks"}
    if "micro" in out and not math.isclose(out["micro"]["share"], MICRO_SHARE[root], rel_tol=1e-9):
        raise D719Error(f"{root}: the micro's share {out['micro']['share']} is not the declared {MICRO_SHARE[root]}")
    return out


# ================================================================================ the bars
def assert_seal(days: pd.Series | np.ndarray) -> None:
    if (pd.Series(days).astype(str) >= SEAL).any():
        raise D719Error(f"seal: a session on or after {SEAL} reached the build")


def load(root: str) -> dict[str, Any]:
    meta = json.loads((CACHE / "meta.json").read_text(encoding="utf-8"))
    st = FIX.stat()
    if meta["size"] != st.st_size or meta["mtime_ns"] != st.st_mtime_ns:
        raise D719Error("the bar cache is stale against fut_day1m.parquet: rebuild it (build_d719_commodity_bars.py)")
    b = pd.read_csv(CACHE / f"{root}.csv.gz", dtype={"day": str, "contract": str}, encoding="utf-8")
    assert_seal(b["day"])
    if not math.isclose(float(b["close"].sum()), meta["roots"][root]["close_sum"], rel_tol=0, abs_tol=1e-6):
        raise D719Error(f"{root}: the cache's column total is not the fixture's")
    b = b[b["day"] >= IN_FROM]
    lab = {k: hm("09:00", k) for k in range(420)}
    b["hhmm"] = b["bar"].map(lab)
    close = b.pivot(index="day", columns="hhmm", values="close")
    open_ = b.pivot(index="day", columns="hhmm", values="open")
    bo, W = BAND_OPEN[root], W_END[root]
    need = [hm(bo, k) for k in range(mins(W) - mins(bo))]
    have = close.reindex(columns=need).notna().sum(axis=1)
    keep = have >= 0.9 * len(need)
    close, open_ = close[keep], open_[keep]
    contract = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(close.index)
    cv = contract.to_numpy(str)
    guard = np.zeros(len(cv), bool)
    for i in range(len(cv)):  # the roll-guard: the contract must be the modal contract of the next 5 sessions
        nxt = cv[i + 1:i + 6]
        guard[i] = len(nxt) == 0 or pd.Series(nxt).value_counts().index[0] != cv[i]
    return {"root": root, "raw": b, "close": close, "open": open_, "exclude": pd.Series(guard, index=close.index),
            "contract": contract}


def price_at(close: pd.DataFrame, open_: pd.DataFrame, band_open: str, t: str) -> pd.Series:
    return open_[band_open] if t == band_open else close[hm(t, -1)]


def rv_from(close: pd.DataFrame, open_s: pd.Series, band_open: str, T: str, include_T_bar: bool = False) -> pd.Series:
    """ln sqrt(sum of 5-minute r^2, bp^2) from the band's open to T (D702's rv_today with the band's open and T)."""
    end = pd.Timestamp("2000-01-01 " + T) + pd.Timedelta(minutes=5 if include_T_bar else 0)
    grid, t = [], pd.Timestamp("2000-01-01 " + band_open) + pd.Timedelta(minutes=5)
    while t <= end:
        grid.append((t - pd.Timedelta(minutes=1)).strftime("%H:%M"))
        t += pd.Timedelta(minutes=5)
    PG = np.column_stack([open_s.to_numpy(float)] + [close[g].to_numpy(float) for g in grid])
    r5 = 1e4 * np.diff(np.log(PG), axis=1)
    with np.errstate(divide="ignore"):
        return pd.Series(np.log(np.sqrt(np.nansum(r5 * r5, axis=1))), index=close.index)


def rv_audit(close: pd.DataFrame, open_s: pd.Series, got: pd.Series, band_open: str, T: str, days: list[str]) -> None:
    tm, bo = mins(T), mins(band_open)
    for d in days:
        row = close.loc[d]
        pts = [float(open_s.loc[d])] + [float(row[f"{m // 60:02d}:{m % 60:02d}"]) for m in range(bo + 4, tm, 5)]
        r = 1e4 * np.diff(np.log(np.array(pts)))
        want = math.log(math.sqrt(float(np.nansum(r * r))))
        if not math.isclose(want, float(got.loc[d]), rel_tol=0, abs_tol=1e-9):
            raise D719Error(f"lag: realised volatility to {T} at {d} reads a bar that starts at or after {T}")


def core(close: pd.DataFrame, open_: pd.DataFrame, band_open: str, T: str, W: str, mult: float, exclude: pd.Series) -> pd.DataFrame:
    """Every candidate: gross per FULL contract, side, a, b and the three prices (D711's clock_frame, generalised)."""
    prev, entry, exit_ = price_at(close, open_, band_open, hm(T, -60)), price_at(close, open_, band_open, T), price_at(close, open_, band_open, W)
    F = 1e4 * np.log(entry / prev)
    d = np.sign(F.to_numpy(float))
    pts = d * (exit_ - entry).to_numpy(float)
    ka = np.isfinite(pts) & ~exclude.reindex(F.index).fillna(True).to_numpy(bool)
    cand = ka & (d != 0)
    sig = E.sigma_f5(F)
    X = pd.DataFrame(index=F.index[cand])
    X["P_prev"], X["P_entry"], X["P_exit"] = prev[cand].to_numpy(float), entry[cand].to_numpy(float), exit_[cand].to_numpy(float)
    X["F"] = F[cand].to_numpy(float)
    X["gross"] = d[cand] * (X["P_exit"] - X["P_entry"]).to_numpy(float) * mult
    X["side"] = d[cand]
    X["a"] = (F.abs() / sig).reindex(X.index)
    cl, op = close.reindex(X.index), open_[band_open].reindex(X.index)
    X["b"] = rv_from(cl, op, band_open, T)
    sample = list(X.index[:: max(1, len(X) // 20)])
    rv_audit(cl, op, X["b"], band_open, T, sample)
    E.sigma_audit(F, sig, sample)
    return X


def rq_audit(L: dict[str, Any], X: pd.DataFrame, T: str, W: str, days: list[str], shift: int = 0) -> None:
    """Right quantity from the raw rows: entry = close of the bar starting T - 1, exit = close of the bar starting W - 1,
    the prior price = close of the bar starting T - 61. `shift` moves the minutes: the canary."""
    raw = L["raw"]
    for s in days:
        r = raw[raw["day"] == s].set_index("hhmm")
        try:
            got = (float(r.at[hm(T, -1 + shift), "close"]), float(r.at[hm(W, -1 + shift), "close"]), float(r.at[hm(T, -61 + shift), "close"]))
        except KeyError as e:
            raise D719Error(f"right quantity: {L['root']} at {s} has no bar {e}") from e
        if got != (float(X.at[s, "P_entry"]), float(X.at[s, "P_exit"]), float(X.at[s, "P_prev"])):
            raise D719Error(f"right quantity: {L['root']} at {s} does not trade the bars the record names")


# ================================================================================ size (s.2)
def size(root: str, X: pd.DataFrame, F: dict[str, np.ndarray], burn_mask: np.ndarray | None = None) -> dict[str, Any]:
    sess = X.index.to_numpy(str)
    first = int(np.flatnonzero(F["window"])[0])
    burn = np.zeros(len(X), bool)
    burn[:first] = True
    if burn_mask is not None:
        burn = burn_mask
    if (sess[burn] >= sess[first]).any():
        raise D719Error(f"{root}: the size reads a scored session")
    a = X["a"].to_numpy(float)
    ab = a[burn & np.isfinite(a)]
    top = burn & np.isfinite(a) & (a >= np.quantile(ab, 0.8))
    cl = cost_lines(root)
    mult = cl["full"]["usd_per_point"]
    q = float(np.quantile(np.abs(X["P_exit"] - X["P_entry"]).to_numpy(float)[top] * mult, 0.99))
    n_full = min(N_FULL_MAX, int(LOSS_LIMIT // q))
    if n_full >= 1:
        return {"q99_full_usd": q, "contract": "full", "n": n_full, "share": 1.0, "cost": cl["full"]["cost"], "burn_top_days": int(top.sum())}
    if "micro" in cl:
        mi = cl["micro"]
        n_m = min(N_MICRO_MAX, int(LOSS_LIMIT // (q * mi["share"])))
        if n_m >= 1:
            return {"q99_full_usd": q, "contract": mi["symbol"], "n": n_m, "share": mi["share"], "cost": mi["cost"],
                    "burn_top_days": int(top.sum()), **({"note": mi["note"]} if "note" in mi else {})}
    return {"q99_full_usd": q, "contract": "NOT VIABLE", "n": 0, "share": 1.0, "cost": cl["full"]["cost"], "burn_top_days": int(top.sum())}


# ================================================================================ the per-root study
def profile(X: pd.DataFrame, F: dict[str, np.ndarray], share: float, cost: float, L: dict[str, Any]) -> dict[str, Any]:
    W = F["window"]
    g = X["gross"].to_numpy(float)[W] * share
    net = g - cost
    a, b = X["a"].to_numpy(float)[W], X["b"].to_numpy(float)[W]

    def cell(m: np.ndarray) -> dict[str, Any]:
        return {"n": int(m.sum()), "mean_gross": float(g[m].mean()) if m.any() else None, "mean_net": float(net[m].mean()) if m.any() else None,
                "win_net": float((net[m] > 0).mean()) if m.any() else None, "share_gross_ge_2c": float((g[m] >= 2 * cost).mean()) if m.any() else None}
    out = {"take_everything": cell(np.ones(len(g), bool)) | {"t_gross_hac": D.nw_t(g)[0]}}
    k = max(1, int(round(0.2 * len(g))))
    top = np.zeros(len(g), bool)
    top[np.argsort(-np.abs(g), kind="stable")[:k]] = True
    out["size_only_oracle_top20"] = cell(top)
    for nm, x in (("a_relative_size", a), ("b_realised_vol", b)):
        fin = np.isfinite(x)
        ed = np.quantile(x[fin], [1 / 3, 2 / 3])
        tt = np.where(fin, np.searchsorted(ed, np.where(fin, x, 0), side="right"), -1)
        out[f"terciles_{nm}"] = {f"t{i + 1}": cell(tt == i) for i in range(3)}
    # the D630-style direction: the return since the prior session's window close, held to W
    Pw_prev = pd.Series(X["P_exit"].to_numpy(float), index=X.index).shift(1).to_numpy(float)[W]
    d630 = np.sign(X["P_entry"].to_numpy(float)[W] - Pw_prev)
    g630 = d630 * (X["P_exit"].to_numpy(float) - X["P_entry"].to_numpy(float))[W] * cost_lines(L["root"])["full"]["usd_per_point"] * share
    ok = np.isfinite(g630) & (d630 != 0)
    out["variant_return_since_prior_window"] = {"n": int(ok.sum()), "mean_gross": float(g630[ok].mean()), "t_gross_hac": D.nw_t(g630[ok])[0]}
    op = L["open"][BAND_OPEN[L["root"]]].reindex(X.index).to_numpy(float)[W]
    aligned = np.sign(X["P_entry"].to_numpy(float)[W] - op) == X["side"].to_numpy(float)[W]
    out["day_move_aligned_vs_opposed"] = {"aligned": cell(aligned), "opposed": cell(~aligned)}
    return out


def exit_check(root: str, X: pd.DataFrame, F: dict[str, np.ndarray], contract: pd.Series, tick: float) -> dict[str, Any]:
    s = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    s = s[(s["root"] == root) & (s["ref"] >= IN_FROM) & (s["ref"] <= IN_END)].set_index(["contract", "ref"])["settle"]
    sess = X.index.to_numpy(str)[F["window"]]
    px = X["P_exit"].to_numpy(float)[F["window"]]
    key = list(zip(contract.reindex(sess).to_numpy(str), sess))
    st = s.reindex(key).to_numpy(float)
    ok = np.isfinite(st)
    dist = np.abs(px[ok] - st[ok]) / tick
    return {"matched": int(ok.sum()), "unmatched": int((~ok).sum()), "median_ticks": float(np.median(dist)) if ok.any() else None,
            "share_within_2_ticks": float((dist <= 2 + 1e-9).mean()) if ok.any() else None,
            "flag": bool(ok.any() and (dist <= 2 + 1e-9).mean() < 0.8)}


def january_bd59(sess: np.ndarray) -> np.ndarray:
    s = pd.Series(sess)
    jan = s.str[5:7] == "01"
    rank = s.groupby(s.str[:7]).cumcount() + 1
    return (jan & rank.between(5, 9)).to_numpy()


def root_study(r: str, arm: pd.Series, nq_daily: pd.Series, workers: int) -> dict[str, Any]:
    L = load(r)
    cl = cost_lines(r)
    T, W = hm(W_END[r], -30), W_END[r]
    X = core(L["close"], L["open"], BAND_OPEN[r], T, W, cl["full"]["usd_per_point"], L["exclude"])
    X.attrs.update(root=r, T=T, cost=cl["full"]["cost"])
    rq_audit(L, X, T, W, list(X.index[:: max(1, len(X) // 15)]))
    F = M.f2_on(X)
    M.V.audit_tiers(X, F)
    sz = size(r, X, F)
    share, cost = sz["share"], sz["cost"]
    sess = X.index.to_numpy(str)
    take = F["take"] & F["window"]
    gc = X["gross"].to_numpy(float) * share
    net = gc[take] - cost
    t_g = D.nw_t(gc[take])[0] if take.sum() > 10 else float("nan")
    nul = M.eff_null(X, F, workers)
    wd = sess[F["window"]]
    years = (pd.Timestamp(str(wd[-1])) - pd.Timestamp(str(wd[0]))).days / 365.25
    with M.cost_as(cost):
        bk = E.book(gc, take, sess, X["side"].to_numpy(float), years, arm)
    bk["trims"] = T0.trims(net, gc[take] / float(gc[F["window"]].std(ddof=1)))
    n = max(sz["n"], 1)
    daily = pd.Series(np.where(take, gc - cost, 0.0)[F["window"]] * n, index=wd)
    eq = daily.cumsum().to_numpy()
    prop = {"contracts": sz["n"], "trailing_drawdown_closed_usd": float(np.max(np.maximum.accumulate(np.r_[0, eq])[1:] - eq)),
            "days_below_minus_1000": int((daily < -LOSS_LIMIT).sum()),
            "largest_day_share_of_total_profit": float(daily.max() / daily.sum()) if daily.sum() > 0 else None,
            "note": "closed-trade equity on the trade days; open equity inside the 30-minute hold is not measured"}
    common = daily.index.intersection(nq_daily.index)
    jb = january_bd59(sess)
    ex = take & ~jb
    return {"root": r, "independent": r not in NOT_INDEPENDENT, "clock": {"T": T, "W": W, "band_open": BAND_OPEN[r]},
            "sessions_in_frame": int(len(L["close"])), "candidates": int(len(X)), "window": [str(wd[0]), str(wd[-1])],
            "size": sz, "trades": int(take.sum()), "mean_gross": float(gc[take].mean()) if take.any() else None,
            "t_gross_hac": t_g, "p_one_sided": float(stats.norm.sf(t_g)) if np.isfinite(t_g) else 1.0,
            "mean_net": float(net.mean()) if take.any() else None, "efficiency": nul["efficiency"],
            "rotation": nul["rotation"], "rotation_mean_gross_reported": nul["rotation_mean_gross_reported"],
            "book": bk, "prop_geometry": prop,
            "rho_with_nq_f2_daily": float(np.corrcoef(daily.loc[common], nq_daily.loc[common])[0, 1]) if len(common) > 30 else None,
            "ex_january_bd5_9": {"trades": int(ex.sum()), "mean_net": float((gc[ex] - cost).mean()) if ex.any() else None},
            "exit_vs_settlement": exit_check(r, X, F, L["contract"], cl["full"]["tick_usd"]),
            "oracle_profile": profile(X, F, share, cost, L), "_daily": daily}


def nq_known_answer() -> dict[str, Any]:
    """D719 s.5: the generic core, pointed at D711's NQ frame, reproduces D711's NQ 15:30 book exactly."""
    Ln = M.load_root("NQ")
    Xm = M.clock_frame(Ln, "15:30")
    Xg = core(Ln["close"], Ln["open"], "09:30", "15:30", "16:00", M.cost_line("NQ")["usd_per_point"], Ln["roll"])
    for c in ("P_prev", "P_entry", "P_exit", "gross", "side", "a", "b"):
        if not (Xg.index.equals(Xm.index) and np.array_equal(Xg[c].to_numpy(float), Xm[c].to_numpy(float), equal_nan=True)):
            raise D719Error(f"the generic core differs from D711's clock_frame on NQ 15:30 ({c})")
    F = M.f2_on(Xg)
    k = F["take"] & F["window"]
    got = {"trades": int(k.sum()), "mean_net": float((Xg["gross"].to_numpy(float)[k] - M.cost_line("NQ")["cost"]).mean())}
    if got["trades"] != KNOWN_NQ["trades"] or abs(got["mean_net"] - KNOWN_NQ["mean_net"]) > 1e-9:
        raise D719Error(f"D711's NQ book is not reproduced: {got}")
    return got


def study(workers: int) -> dict[str, Any]:
    t0 = time.time()
    for r in ROOTS:
        cl = cost_lines(r)
        for mult in [cl["full"]["usd_per_point"]] + ([cl["full"]["usd_per_point"] * cl["micro"]["share"]] if "micro" in cl else []):
            for f5, p0, p1 in ((+5.0, 100.0, 101.0), (-5.0, 100.0, 99.0)):
                if not np.sign(f5) * (p1 - p0) * mult > 0:
                    raise D719Error(f"sign: a favourable continuation does not pay on {r}")
    ka = nq_known_answer()
    arm = P694.arm_daily()
    arm = arm[arm.index <= IN_END]
    import vault_d716_nq_f2 as V16
    bd = V16.build()
    Bm = bd["Fn"]["take"] & bd["Fn"]["window"]
    nq_daily = pd.Series(np.where(Bm, bd["net"], 0.0)[bd["Fn"]["window"]], index=bd["sn"][bd["Fn"]["window"]])
    res = {r: root_study(r, arm, nq_daily, workers) for r in ROOTS}
    holm = P694.T.holm({r: res[r]["p_one_sided"] for r in ROOTS})
    counts = {"all": 0, "independent": 0}
    for r in ROOTS:
        x = res[r]
        x["holm_p"] = holm[r]
        a_ = bool((x["mean_gross"] or 0) > 0 and holm[r] < 0.05)
        b_ = bool(x["efficiency"] > x["rotation"]["p95"])
        c_ = bool((x["mean_net"] or -1) > 0)
        x["gates"] = {"a_gross_holm": a_, "b_efficiency_above_rotation_p95": b_, "c_net_positive": c_}
        if x["trades"] < MIN_TRADES or (x["size"]["contract"] == "NOT VIABLE" and a_ and b_):
            x["verdict"] = "UNRESOLVED"
        elif a_ and b_ and c_:
            x["verdict"] = "TRANSFERS"
        elif a_ and b_:
            x["verdict"] = "SIGNAL, NOT FEE"
        else:
            x["verdict"] = "DOES NOT TRANSFER"
        counts["all"] += x["verdict"] == "TRANSFERS"
        counts["independent"] += x["verdict"] == "TRANSFERS" and x["independent"]

    def reading(n: int) -> str:
        return "SUPPORTS" if n >= 3 else ("MIXED" if n >= 1 else "NONE")
    dl = pd.DataFrame({r: res[r]["_daily"] for r in ROOTS}).fillna(0.0)
    rho = dl.corr().round(3).to_dict()
    for r in ROOTS:
        res[r].pop("_daily")
    out = {"spec": "D719 (f4930141) with A1 (a1e0a7ed) and A2 (b00f59b7)", "known_answer_nq": ka,
           "KE": "UNRESOLVED (deferred, D719-A1: no one-minute bars)", "roots": res,
           "family": {"all_twelve": {"transfers": counts["all"], "reading": reading(counts["all"])},
                      "eight_independent": {"transfers": counts["independent"], "reading": reading(counts["independent"])}},
           "rho_between_roots_daily_net": rho, "runtime_min": round((time.time() - t0) / 60, 2)}
    v = {r: res[r]["verdict"] for r in ROOTS}
    out["predictions"] = {
        "1_gross_positive_on_at_least_9": int(sum((res[r]["mean_gross"] or 0) > 0 for r in ROOTS)) >= 9,
        "2_NG_CL_SI_gate_a_positive": all((res[r]["mean_gross"] or 0) > 0 and res[r]["t_gross_hac"] > 0 for r in ("NG", "CL", "SI")),
        "3_full_for_grains_and_HG_micro_for_NG_CL_GC_SI": all(res[r]["size"]["contract"] == "full" for r in ("HG", "ZC", "ZS", "ZW", "ZL", "ZM"))
        and all(res[r]["size"]["contract"] not in ("full", "NOT VIABLE") for r in ("NG", "CL", "GC", "SI")),
        "4_one_to_three_transfer_and_one_signal_not_fee": bool(1 <= counts["all"] <= 3 and "SIGNAL, NOT FEE" in v.values()),
        "6_rho_with_nq_f2_below_0.2": all((res[r]["rho_with_nq_f2_daily"] or 0) < 0.2 for r in ROOTS)}
    en = [r for r in ("CL", "NG", "HO", "RB") if v[r] == "TRANSFERS"]
    out["predictions"]["5_energy_transferring_2022_share_above_0.4"] = all(
        (res[r]["book"].get("by_year", {}).get("2022", {}).get("n", 0) > 0) and _share2022(res[r]) > 0.4 for r in en)
    return out


def _share2022(x: dict[str, Any]) -> float:
    by = x["book"].get("by_year", {})
    tot = sum(v["n"] * v["net"] for v in by.values())
    return float(by["2022"]["n"] * by["2022"]["net"] / tot) if tot > 0 and "2022" in by else 0.0


# ================================================================================ selftest
def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any], exc: tuple = (D719Error,)) -> None:
        try:
            fn()
        except exc:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    rng = np.random.default_rng(719)
    must_raise("a session on or after 2024-01-01", lambda: assert_seal(pd.Series(["2023-12-29", "2024-01-02"])))
    # rv_from on a 09:00 band, its audit, and the canary that reads the bar starting at T
    days = [f"2019-01-{i:02d}" for i in range(1, 11)]
    cols = [hm("09:00", k) for k in range(330)]
    close = pd.DataFrame(100 + np.cumsum(rng.normal(0, 0.05, (10, len(cols))), axis=1), index=days, columns=cols)
    op = pd.Series(100.0, index=days)
    close.loc[:, "14:04"] = close["14:04"] + 5.0
    rv_audit(close, op, rv_from(close, op, "09:00", "14:00"), "09:00", "14:00", days)
    must_raise("a realised volatility that reads the bar starting at T",
               lambda: rv_audit(close, op, rv_from(close, op, "09:00", "14:00", include_T_bar=True), "09:00", "14:00", days))
    if not np.array_equal(rv_from(close, op, "09:30", "13:30").to_numpy(), M.rv_to(close, op, "13:30").to_numpy()):
        raise SystemExit("selftest: rv_from on a 09:30 band differs from D711's rv_to")
    # right quantity on a synthetic root
    raw = pd.DataFrame([(d, c, float(close.at[d, c])) for d in days for c in cols], columns=["day", "hhmm", "close"])
    Ls = {"root": "XX", "raw": raw}
    Xs = pd.DataFrame(index=days)
    Xs["P_entry"], Xs["P_exit"], Xs["P_prev"] = close["13:59"], close["14:29"], close["12:59"]
    rq_audit(Ls, Xs, "14:00", "14:30", days[:4])
    must_raise("an entry one minute late", lambda: rq_audit(Ls, Xs, "14:00", "14:30", days[:4], shift=1))
    # the sizing canary: a burn-in that holds a scored session must raise
    Xz = pd.DataFrame({"a": np.abs(rng.normal(size=600)), "b": rng.normal(size=600), "P_entry": 100.0,
                       "P_exit": 100 + rng.normal(0, 0.3, 600)}, index=[f"s{i:04d}" for i in range(600)])
    Fz = M.f2_on(Xz)
    bad = np.zeros(600, bool)
    bad[:int(np.flatnonzero(Fz["window"])[0]) + 1] = True
    must_raise("a size read from a scored session", lambda: size("HG", Xz, Fz, burn_mask=bad))
    sz = size("HG", Xz, Fz)
    if sz["contract"] not in ("full", "MHG", "NOT VIABLE") or sz["n"] > N_FULL_MAX:
        raise SystemExit(f"selftest: the size rule returned {sz}")
    v = rng.normal(size=600)
    must_raise("a tier that ranks its own value", lambda: C.tier_audit(C.tiers(v, leak=True), v, [300, 450, 599]), (C.D671Error,))
    f5 = pd.Series(rng.normal(size=400), index=[f"d{i:04d}" for i in range(400)])
    must_raise("a sigma that includes today", lambda: E.sigma_audit(f5, E.sigma_f5(f5, leak=True), list(f5.index[100::50])), (E.D703Error,))
    for r in ROOTS:
        cl = cost_lines(r)
        if cl["full"]["cost"] <= 6 or ("micro" in cl and cl["micro"]["cost"] <= 3):
            raise SystemExit(f"selftest: {r}'s cost line is below its commission")
    if cost_lines("GC")["full"]["cost"] < 40 or cost_lines("SI")["micro"]["share"] != 0.2:
        raise SystemExit("selftest: D719-A2's GC line or SIL's one-fifth share")
    if list(january_bd59(np.array(["2019-01-02", "2019-01-03", "2019-01-04", "2019-01-07", "2019-01-08", "2019-01-09"]))) != [False, False, False, False, True, True]:
        raise SystemExit("selftest: january_bd59")
    print(f"selftest OK: {len(fired)} canaries fired: {fired}; rv_from equals D711's rv_to on a 09:30 band; the size rule and "
          "the twelve cost lines behave. The NQ known answer and the cache's column totals run first in --run.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 4))
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 1
    if OUT.exists():
        raise D719Error(f"{OUT.name} exists: D719's run is once")
    out = study(a.workers)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    brief = {r: {k: x[k] for k in ("verdict", "size", "trades", "mean_gross", "t_gross_hac", "holm_p", "mean_net", "efficiency", "gates", "rho_with_nq_f2_daily")}
             | {"rot_p95": x["rotation"]["p95"], "rank": x["rotation"]["rank"], "exit_check": x["exit_vs_settlement"]}
             for r, x in out["roots"].items()}
    print(json.dumps({"family": out["family"], "roots": brief, "predictions": out["predictions"], "runtime_min": out["runtime_min"]},
                     indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
