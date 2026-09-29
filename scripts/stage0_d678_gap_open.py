"""D678: going with the overnight gap through yesterday's day-session range at the open, on HO, RB, BZ, HG and PL.
Spec: docs/decisions/D678-PRE-REG-the-overnight-gap-through-yesterdays-range-on-ho-rb-bz-hg-pl.md (7914bfde).
In-sample to 2025-02-28; the vault is never read; HO/RB after 2026-09-18 are D626's; CL/NG are not used.

    uv run --with pyarrow python scripts/stage0_d678_gap_open.py --selftest
    uv run --with pyarrow python scripts/stage0_d678_gap_open.py --gates   # data gates only, no outcome
    uv run --with pyarrow python scripts/stage0_d678_gap_open.py --run     # once

D676's levels, ATR, day frame and E4 exit are reused unchanged (their module); friction is counted once (D668-A2).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d676_root_aware_break as B  # noqa: E402

M, C = B.M, B.C
OUT = REPO / "data" / "stage0_d678_gap_open.json"
FIXTURE = REPO / "data" / "fixtures" / "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz"
DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
ROOTS = ("HO", "RB", "BZ", "HG", "PL")
ENERGY = ("HO", "RB", "BZ")
hm = B.hm
SESS = {"HO": {"open": hm("09:00"), "flat": hm("14:25"), "last": hm("13:55")},
        "RB": {"open": hm("09:00"), "flat": hm("14:25"), "last": hm("13:55")},
        "BZ": {"open": hm("09:00"), "flat": hm("14:25"), "last": hm("13:55")},
        "HG": {"open": hm("08:10"), "flat": hm("12:55"), "last": hm("12:25")},
        "PL": {"open": hm("08:20"), "flat": hm("13:00"), "last": hm("12:30")}}
B.SESS.update(SESS)  # D676's day_frame reads its module's SESS
R2_ROOTS = ("HO", "RB", "HG", "PL")  # BZ is financially settled
EIA_ROOTS = ("HO", "RB")
K_ATR, TRAIL, BUFFER_BD = B.K_ATR, B.TRAIL, B.BUFFER_BD
RESERVED_FROM, FIRST, COVID = B.RESERVED_FROM, B.FIRST, B.COVID
N_NULL, N_BOOT, SEED, BATCH = 10_000, 500, 678, 1_000
MIN_TRADES = 100


class D678Error(RuntimeError):
    pass


# ================================================================================ costs (single count, D668-A2)
def costs() -> dict[str, dict[str, float]]:
    j = json.loads((REPO / "data" / "futures_costs.json").read_text(encoding="utf-8"))
    out = {}
    for r in ROOTS:
        f = j["roots"][r]["full"]
        com = float(f["commission_rt_usd"]["value"])
        if com != 6.0:
            raise D678Error(f"{r}: commission {com}, not the declared $6")
        x = float(f["crossing_ticks_rt"]["d507_exec"]["value"])
        out[r] = {"symbol": f["symbol"], "line": "d507_exec", "tick": float(f["tick_points"]), "tick_usd": float(f["tick_usd"]),
                  "usd_per_point": float(f["usd_per_point"]), "crossing_ticks_rt": x, "cost_usd": com + x * float(f["tick_usd"])}
    return out


# ================================================================================ gates
def identity_gate(g: pd.DataFrame, data_root: Path) -> dict[str, Any]:
    import pyarrow.parquet as pq
    d1 = pq.read_table(data_root / "fixtures" / "fut_day1m.parquet", columns=["root", "day", "bar", "open", "high", "low", "close"],
                       filters=[("root", "in", list(ROOTS)), ("day", "<", RESERVED_FROM), ("day", ">=", "2015-09-01")]).to_pandas()
    d1["m"] = 540 + d1["bar"].astype(int)
    out = {}
    for r in ROOTS:
        fl = SESS[r]["flat"]
        a = g[(g["root"] == r) & (g["m"] >= 540) & (g["m"] <= fl) & (g["hhmm"] < "18:00")].set_index(["session", "m"])[["open", "high", "low", "close"]]
        b = d1[(d1["root"] == r) & (d1["m"] <= fl)].rename(columns={"day": "session"}).set_index(["session", "m"])[["open", "high", "low", "close"]]
        j = a.join(b, lsuffix="_g", rsuffix="_d", how="inner")
        mis = int(sum((np.abs(j[f"{c}_g"] - j[f"{c}_d"]) > 1e-6).sum() for c in ("open", "high", "low", "close")))
        out[r] = {"bars_fixture": int(len(a)), "bars_day1m": int(len(b)), "matched": int(len(j)), "price_mismatches": mis,
                  "only_fixture": int(len(a) - len(j)), "only_day1m": int(len(b) - len(j)),
                  "pass": bool(mis == 0 and len(j) >= 0.99 * min(len(a), len(b)))}
    return out


def r2_flags(r: str, d: pd.DataFrame) -> pd.Series:
    if r not in R2_ROOTS:
        return pd.Series(False, index=d.index)
    return pd.Series([B.business_days_between(s, B.first_notice(c, s)) <= BUFFER_BD for c, s in zip(d["contract"], d.index)], index=d.index)


def r2_audit(f: pd.Series, d: pd.DataFrame, r: str) -> None:
    """Second path: pandas business days from the day after the session to the last trade / first notice day."""
    if r not in R2_ROOTS:
        return
    for s in f.index[:: max(1, len(f) // 25)]:
        e = B.first_notice(d.at[s, "contract"], s)
        want = len(pd.bdate_range(pd.Timestamp(s) + pd.Timedelta(days=1), e)) <= BUFFER_BD
        if bool(f.at[s]) != want:
            raise D678Error(f"R2: {r} {s} flagged {f.at[s]}, second path {want}")


# ================================================================================ the trades
def exit_ix(bb: dict, i: int, D: int, entry: float, stop_lvl: float, A: float, flat: int) -> tuple[float, str, int, float]:
    """D676's exit_trade at tick 0, also returning the exit bar and the stop in force (asserted equal in price to
    D676's on every trade)."""
    m, o, h, l, c = bb["m"], bb["o"], bb["h"], bb["l"], bb["c"]
    stop, best = stop_lvl, entry
    for k in range(i + 1, len(m)):
        if m[k] > flat:
            break
        if (D > 0 and l[k] <= stop) or (D < 0 and h[k] >= stop):
            through = (o[k] <= stop) if D > 0 else (o[k] >= stop)
            return float(o[k] if through else stop), "stop", k, stop
        best = max(best, h[k]) if D > 0 else min(best, l[k])
        new = best - D * TRAIL * A
        stop = max(stop, new) if D > 0 else min(stop, new)
    j = np.flatnonzero(m <= flat)
    return float(c[j[-1]]), "flat", int(j[-1]), stop


def fill_audit(bb: dict, k: int, px: float, why: str, stop_at_exit: float | None) -> None:
    """A stop fill is at the stop or at the bar's open through it -- never an extra tick (the double count)."""
    if why == "stop" and not (np.isclose(px, bb["o"][k], rtol=0, atol=1e-12) or (stop_at_exit is not None and np.isclose(px, stop_at_exit, rtol=0, atol=1e-12))):
        raise D678Error(f"fill: a stop filled at {px}, neither the stop nor the bar's open")


def entry_audit(bb: dict, i: int, entry: float, open_m: int) -> None:
    if int(bb["m"][i]) != open_m or entry != float(bb["o"][i]):
        raise D678Error("gap: the trade is not entered at the open bar's open")


def one(bb: dict, i: int, D: int, entry: float, L: float, A: float, flat: int) -> tuple[float, str, int]:
    px, why, k, stop = exit_ix(bb, i, D, entry, L, A, flat)
    ref, _ = B.exit_trade(bb, i, D, entry, L, A, flat, 0.0, TRAIL)
    if px != ref:
        raise D678Error("exit_ix disagrees with D676's exit_trade")
    fill_audit(bb, k, px, why, stop)
    return px, why, k


def root_job(args: tuple) -> dict[str, Any]:
    r, d, bars, cost = args
    s = SESS[r]
    rows, fresh = [], []
    for sess, rec in d.iterrows():
        bb = bars.get(sess)
        if bb is None or not rec["eligible"]:
            continue
        B.flat_audit(bb, s["flat"])
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        i0 = int(np.flatnonzero(bb["m"] == s["open"])[0])
        o = float(bb["o"][i0])
        up, dn = Lh + K_ATR * A, Ll - K_ATR * A
        D = 1 if o > up else -1 if o < dn else 0
        if D:
            L = Lh if D > 0 else Ll
            entry_audit(bb, i0, o, s["open"])
            dist = D * (o - L)
            res = {}
            for side in (1, -1):
                stop = L if side == D else o + D * dist  # the opposite side's stop mirrors the distance to L
                px, why, k = one(bb, i0, side, o, stop, A, s["flat"])
                res[side] = (side * (px / o - 1) * 1e4, why, int(bb["m"][k] - bb["m"][i0]))
            rows.append({"session": sess, "D": D, "entry": o, "A": A, "A_bp": A / o * 1e4, "L": L,
                         "overshoot_A": D * (o - (up if D > 0 else dn)) / A,
                         "gross": res[D][0], "why": res[D][1], "hold_min": res[D][2],
                         "long_gross": res[1][0], "short_gross": res[-1][0],
                         "cost_bp": cost["cost_usd"] / cost["usd_per_point"] / o * 1e4, "tick_bp": cost["tick"] / o * 1e4,
                         "R2": bool(rec["R2"]), "eia": bool(rec["eia"])})
        else:
            t = B.break_scan(bb, Lh, Ll, A, s["open"], s["last"], 0.0)
            if t is None:
                continue
            px, why, k = one(bb, t["i"], t["D"], t["entry"], t["L"], A, s["flat"])
            fresh.append({"session": sess, "D": t["D"], "entry": t["entry"], "A_bp": A / t["entry"] * 1e4,
                          "gross": t["D"] * (px / t["entry"] - 1) * 1e4, "R2": bool(rec["R2"])})
    return {"root": r, "rows": rows, "fresh": fresh}


# ================================================================================ statistics
def mt(x: np.ndarray, R: Any) -> dict[str, Any]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return {"n": int(len(x)), "mean": None, "t": None, "se": None}
    m, t, se = M.mean_t(x, R)
    return {"n": int(len(x)), "mean": m, "t": t, "se": se}


def four_groups(g: np.ndarray, net: np.ndarray, cost: np.ndarray, per_year: float, sess: np.ndarray, D: np.ndarray) -> dict[str, Any]:
    n = len(net)
    q = np.sort(net)
    k = max(1, int(round(0.01 * n)))
    wins, losses = net[net > 0], net[net <= 0]
    sd = net.std(ddof=1)
    dn = np.sqrt(np.mean(np.minimum(net, 0) ** 2))
    cum = np.cumsum(net)
    top = int(np.argmax(net))
    return {"trades": n, "gross_mean": float(g.mean()), "net_mean": float(net.mean()), "net_median": float(np.median(net)),
            "win": float((net > 0).mean()), "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) else None,
            "skew": float(stats.skew(net)), "kurtosis": float(stats.kurtosis(net)),
            "ex_top1pct": float(q[:-k].mean()), "ex_bottom1pct": float(q[k:].mean()), "trimmed": float(q[k:-k].mean()),
            "sharpe_net_ann": float(net.mean() / sd * np.sqrt(per_year)), "sortino_net_ann": float(net.mean() / dn * np.sqrt(per_year)),
            "sharpe_gross_ann": float(g.mean() / g.std(ddof=1) * np.sqrt(per_year)),
            "max_dd_bp": float(np.max(np.maximum.accumulate(cum) - cum)), "breakeven_cost_bp": float(g.mean()),
            "cost_bp_mean": float(cost.mean()), "top_trade": {"session": str(sess[top]), "D": int(D[top]), "net_bp": float(net[top])}}


def daily_stats(tr: pd.DataFrame, bp: np.ndarray, ses: pd.Index, usd_pt: float) -> dict[str, float]:
    s = M.daily_usd(tr, bp, np.ones(len(tr)), ses, usd_pt)
    sd, dn = s.std(ddof=1), np.sqrt(np.mean(np.minimum(s, 0) ** 2))
    cum = s.cumsum()
    return {"usd_per_year": float(s.mean() * 252), "daily_sharpe": float(s.mean() / sd * np.sqrt(252)) if sd > 0 else None,
            "daily_sortino": float(s.mean() / dn * np.sqrt(252)) if dn > 0 else None, "max_dd_usd": float((cum.cummax() - cum).max())}


def signflip(books: dict[str, pd.DataFrame], dates: np.ndarray, seed: int) -> dict[str, np.ndarray]:
    """Family and per-root null draws: one uniform per date shared by every root; root r is long if u < its long share.
    Values are % of A. Returns {'family': draws, r: draws}."""
    rng = np.random.default_rng(seed)
    pos = {r: np.searchsorted(dates, b["session"].to_numpy()) for r, b in books.items()}
    for r, p in pos.items():
        if len(np.unique(p)) != len(p) or not np.array_equal(dates[p], books[r]["session"].to_numpy()):
            raise D678Error(f"null: {r}'s dates do not map one-to-one")
    cnt = np.zeros(len(dates))
    for r in books:
        cnt[pos[r]] += 1.0
    out = {k: np.empty(N_NULL) for k in ["family", *books]}
    for b0 in range(0, N_NULL, BATCH):
        u = rng.random((BATCH, len(dates)))
        tot = np.zeros((BATCH, len(dates)))
        for r, b in books.items():
            pl = float((b["D"] > 0).mean())
            lv = (b["long_gross"] / b["A_bp"] * 100).to_numpy(float)
            sv = (b["short_gross"] / b["A_bp"] * 100).to_numpy(float)
            longs = u[:, pos[r]] < pl
            mix_check(longs, pl, r)
            v = np.where(longs, lv, sv)
            out[r][b0:b0 + BATCH] = v.mean(axis=1)
            tot[:, pos[r]] += v
        ok = cnt > 0
        out["family"][b0:b0 + BATCH] = (tot[:, ok] / cnt[ok]).mean(axis=1)
    return out


def mix_check(longs: np.ndarray, pl: float, r: str) -> None:
    """The null's long share must match the book's within 0.02."""
    if abs(float(longs.mean()) - pl) > 0.02:
        raise D678Error(f"null: {r}'s side mix {longs.mean():.3f} is not the book's {pl:.3f}")


def null_summary(draws: np.ndarray, score: float, rng: np.random.Generator) -> dict[str, float]:
    q95 = [np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(N_BOOT)]
    return {"p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)), "p95_se": float(np.std(q95, ddof=1)),
            "rank": float((draws < score).mean())}


def date_series(books: dict[str, pd.DataFrame], col: str) -> pd.Series:
    parts = [pd.Series((b[col] / b["A_bp"] * 100).to_numpy(float), index=b["session"].to_numpy()) for b in books.values() if len(b)]
    return pd.concat(parts).groupby(level=0).mean().sort_index()


# ================================================================================ build
def frames(g: pd.DataFrame, data_root: Path) -> tuple[dict, dict, dict]:
    events = pd.read_csv(data_root / "calendar" / "events.csv", encoding="utf-8")
    eia_days = set(str(x)[:10] for x in events.loc[events["event"] == "EIA_WPSR", "datetime_et"])
    fr, bars_all, cov = {}, {}, {}
    for r in ROOTS:
        d, bars = B.day_frame(g, r)
        cov[r] = {"sessions": int(len(d)), "unusable": int((~d["usable"]).sum()), "coverage_median": float(d["coverage"].median()),
                  "by_year_usable": {y: round(float(v), 3) for y, v in d["usable"].groupby(d.index.str[:4]).mean().items()},
                  "unusable_list": list(d.index[~d["usable"]])}
        d = d[d["usable"]].copy()
        d["atr20"] = B.atr_prior(d)
        B.atr_audit(d, d["atr20"], list(range(0, len(d), max(1, len(d) // 30))))
        same = d["contract"] == d["contract"].shift(1)
        d["prior_high"] = d["high"].shift(1).where(same)
        d["prior_low"] = d["low"].shift(1).where(same)
        d["R2"] = r2_flags(r, d)
        r2_audit(d["R2"], d, r)
        d["eia"] = [s in eia_days for s in d.index] if r in EIA_ROOTS else False
        d["eligible"] = (d.index >= FIRST) & np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)
        fr[r], bars_all[r] = d, bars
    return fr, bars_all, cov


def build(data_root: Path, gates_only: bool = False) -> dict[str, Any]:
    t0 = time.time()
    cst = costs()
    g = B.load_fixture(FIXTURE)
    out: dict[str, Any] = {"spec": "D678 (7914bfde)", "costs": cst, "data_gates": {"identity": identity_gate(g, data_root)}}
    fr, bars_all, cov = frames(g, data_root)
    out["data_gates"]["coverage"] = {r: {k: v for k, v in c.items() if k != "unusable_list"} for r, c in cov.items()}
    out["data_gates"]["unusable_sessions"] = {r: c["unusable_list"] for r, c in cov.items()}
    out["data_gates"]["seal"] = "no session >= 2025-03-01 (load_fixture raises)"
    if not all(v["pass"] for v in out["data_gates"]["identity"].values()):
        raise D678Error(f"identity gate failed: {out['data_gates']['identity']}")
    if gates_only:
        return out
    with ProcessPoolExecutor(max_workers=5) as pool:
        got = {o["root"]: o for o in pool.map(root_job, [(r, fr[r], bars_all[r], cst[r]) for r in ROOTS])}
    V = M.S.load_v2()
    R = V.R
    rng = np.random.default_rng(SEED)
    all_b = {r: pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True) for r in ROOTS}
    all_f = {r: pd.DataFrame(got[r]["fresh"]).sort_values("session").reset_index(drop=True) for r in ROOTS}
    books = {r: b[~b["R2"]].reset_index(drop=True) for r, b in all_b.items()}
    fresh = {r: f[~f["R2"]].reset_index(drop=True) for r, f in all_f.items()}
    # ------------------------------------------------ Gate 1: the family, in % of A, against the sign-flip null
    fam = date_series(books, "gross")
    dates = fam.index.to_numpy()
    draws = signflip(books, dates, SEED)
    fstat = float(fam.mean())
    ex = ~((fam.index >= COVID[0]) & (fam.index <= COVID[1]))
    fm = mt(fam.to_numpy(), R)
    g1 = {"statistic_pct_A": fstat, "t_hac": fm["t"], "p_one_sided": float(stats.norm.sf(fm["t"])), "dates": int(len(fam)),
          "trades": int(sum(len(b) for b in books.values())), "null": null_summary(draws["family"], fstat, rng),
          "ex_covid": float(fam[ex].mean())}
    g1["checks"] = {"t_one_sided_p_below_0.05": bool(g1["p_one_sided"] < 0.05),
                    "above_null_p95_by_2se": bool(fstat - g1["null"]["p95"] > 2 * g1["null"]["p95_se"]),
                    "positive_ex_covid": bool(g1["ex_covid"] > 0)}
    g1["MECHANISM"] = bool(all(g1["checks"].values()))
    out["gate1_family"] = g1
    # energy / metals halves, reported
    out["family_halves"] = {nm: mt(date_series({r: books[r] for r in rs}, "gross").to_numpy(), R)
                            for nm, rs in (("energy_HO_RB_BZ", ENERGY), ("metals_HG_PL", ("HG", "PL")))}
    # ------------------------------------------------ K8 for the component line
    b_all, use_nq, _gd, R2_ = M.load_bars(data_root, False, ("ES", "NQ"))
    C._R = R2_
    tabs = R2_.session_table(b_all, use_nq, roots=("NQ",))
    k8 = M.k8_daily(tabs["NQ"], tabs["NQ"].index[(tabs["NQ"].index >= FIRST) & (tabs["NQ"].index < RESERVED_FROM)])
    # ------------------------------------------------ per root
    out["roots"], daily, pvals = {}, {}, {}
    for r in ROOTS:
        b, d, cst_r = books[r], fr[r], cst[r]
        ses = d.index[d["eligible"]]
        years = len(ses) / 252
        gb = b["gross"].to_numpy(float)
        net = gb - b["cost_bp"].to_numpy(float)
        tk = b["tick_bp"].to_numpy(float)
        exc = ~b["session"].between(*COVID).to_numpy()
        pct = gb / b["A_bp"].to_numpy(float) * 100
        nm_ = mt(net, R)
        pvals[r] = float(stats.norm.sf(nm_["t"])) if nm_["t"] is not None else 1.0
        D = b["D"].to_numpy(int)
        yrs = b["session"].str[:4].to_numpy()
        ov = b["overshoot_A"].to_numpy(float)
        fr_r = fresh[r]
        fpct = (fr_r["gross"] / fr_r["A_bp"] * 100).to_numpy(float)
        a_, f_ = mt(pct, R), mt(fpct, R)
        rem = all_b[r][all_b[r]["R2"]]
        rec = {"trades": int(len(b)), "per_year": float(len(b) / years), "long_share": float((D > 0).mean()),
               "gross_bp": mt(gb, R), "gross_pct_A": a_, "null_pct_A": null_summary(draws[r], float(pct.mean()), rng),
               "gate2": {"net_bp": nm_, "p_one_sided": pvals[r], "net_plus1tick": float((net - 2 * tk).mean()),
                         "net_ex_covid": float(net[exc].mean()), "trades": int(len(b))},
               "cost_bp": float(b["cost_bp"].mean()), "cost_pct_A": float((b["cost_bp"] / b["A_bp"]).mean() * 100),
               "ATR_bp_median": float(b["A_bp"].median()),
               "secondary_gap_vs_fresh_pct_A": {"gap": a_, "fresh": f_,
                                                "diff": (a_["mean"] - f_["mean"]) if a_["mean"] is not None and f_["mean"] is not None else None,
                                                "t": ((a_["mean"] - f_["mean"]) / np.hypot(a_["se"], f_["se"])) if a_["se"] and f_["se"] else None},
               "reported": {"long": mt(gb[D > 0], R), "short": mt(gb[D < 0], R),
                            "overshoot_below_0.25A": mt(gb[ov < 0.25], R), "overshoot_0.25A_plus": mt(gb[ov >= 0.25], R),
                            "by_year_gross": {y: mt(gb[yrs == y], R) for y in sorted(set(yrs))},
                            "by_year_net": {y: float(net[yrs == y].mean()) for y in sorted(set(yrs))},
                            "share_stopped": float((b["why"] == "stop").mean()), "hold_min_median": float(b["hold_min"].median()),
                            "R2_removed_gross": mt(rem["gross"].to_numpy(float), R) if len(rem) else None},
               "four_groups": four_groups(gb, net, b["cost_bp"].to_numpy(float), len(b) / years, b["session"].to_numpy(), D)}
        if r in EIA_ROOTS:
            e = b["eia"].to_numpy(bool)
            rec["reported"]["eia_days"] = mt(gb[e], R)
            rec["reported"]["other_days"] = mt(gb[~e], R)
        tr = b.assign(entry=b["entry"])
        rec["daily_net"] = daily_stats(tr, net, ses, cst_r["usd_per_point"])
        rec["daily_gross"] = daily_stats(tr, gb, ses, cst_r["usd_per_point"])
        daily[r] = M.daily_usd(tr, net, np.ones(len(tr)), ses, cst_r["usd_per_point"])
        out["roots"][r] = rec
    # component line: correlations
    for r in ROOTS:
        s = daily[r]
        kk = k8.reindex(s.index)
        ok = kk.notna()
        out["roots"][r]["component"] = {"rho_K8": float(np.corrcoef(s[ok], kk[ok])[0, 1]) if ok.sum() > 30 else None,
                                        "rho_other_roots": {o: float(s.corr(daily[o].reindex(s.index).fillna(0.0))) for o in ROOTS if o != r},
                                        "not_rebuilt": ["#2 the MACD day-session arm (ADMITTED)", "#3 the NG winter spread (daily P&L missing)"]}
    # secondary, family
    fg, ff = date_series(books, "gross"), date_series(fresh, "gross")
    a_, f_ = mt(fg.to_numpy(), R), mt(ff.to_numpy(), R)
    out["secondary_family_gap_vs_fresh_pct_A"] = {"gap": a_, "fresh": f_, "diff": a_["mean"] - f_["mean"],
                                                  "t": (a_["mean"] - f_["mean"]) / np.hypot(a_["se"], f_["se"])}
    # verdicts
    h2 = B.T.holm(pvals) if g1["MECHANISM"] else {}
    for r in ROOTS:
        g2 = out["roots"][r]["gate2"]
        ok = bool(g1["MECHANISM"] and h2.get(r, 1.0) < 0.05 and (g2["net_bp"]["mean"] or -1) > 0 and g2["net_plus1tick"] > 0
                  and g2["trades"] >= MIN_TRADES and g2["net_ex_covid"] > 0)
        g2["holm_p"] = h2.get(r)
        g2["pass"] = ok
        out["roots"][r]["verdict"] = "SUPPORTED" if ok else "MECHANISM ONLY" if g1["MECHANISM"] else "NOT SUPPORTED"
    sec = [out["roots"][r]["secondary_gap_vs_fresh_pct_A"]["diff"] for r in ROOTS]
    out["predictions"] = {"1_family_passes_gate1": g1["MECHANISM"],
                          "2_no_root_passes_gate2": not any(out["roots"][r]["gate2"]["pass"] for r in ROOTS),
                          "3_gap_minus_fresh_positive_on_4_of_5": bool(sum((x or -1) > 0 for x in sec) >= 4),
                          "4_gap_gross_positive_on_4_of_5": bool(sum((out["roots"][r]["gross_bp"]["mean"] or -1) > 0 for r in ROOTS) >= 4)}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D678Error, B.D676Error):
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(7)
    d = pd.DataFrame({"high": 100 + rng.random(60) * 3, "low": 99 - rng.random(60) * 3, "close": 100 + rng.normal(0, 1, 60)},
                     index=[f"2019-01-{i:02d}" for i in range(1, 61)])
    a = B.atr_prior(d)
    B.atr_audit(d, a, [30, 45, 59])
    tr_ = pd.concat([d["high"] - d["low"], (d["high"] - d["close"].shift(1)).abs(), (d["low"] - d["close"].shift(1)).abs()], axis=1).max(axis=1)
    must_raise("ATR with the session's own range", lambda: B.atr_audit(d, tr_.rolling(20, min_periods=20).mean(), [30, 45, 59]))
    m = np.arange(hm("09:00"), hm("12:00"))
    up = np.linspace(105, 110, len(m))
    bb = {"m": m, "o": up, "h": up + 0.02, "l": up - 0.02, "c": up}
    entry_audit(bb, 0, float(bb["o"][0]), hm("09:00"))
    must_raise("a gap entry off the open bar's open", lambda: entry_audit(bb, 0, float(bb["o"][0]) + 0.01, hm("09:00")))
    down = np.linspace(105, 95, len(m))
    bd = {"m": m, "o": down, "h": down + 0.02, "l": down - 0.02, "c": down}
    px, why, k, stp = exit_ix(bd, 0, 1, 105.0, 104.0, 4.0, hm("11:59"))
    if why != "stop" or px > 105.0:
        raise SystemExit("selftest: a falling long was not stopped")
    fill_audit(bd, k, px, why, stp)
    must_raise("a stop filled with an extra tick", lambda: fill_audit(bd, k, px - 0.01, why, stp))
    must_raise("a bar after the flat time", lambda: B.flat_audit(bb, hm("10:00")))
    idx = pd.Index(["2019-01-10", "2019-01-22", "2019-02-05"])
    dd = pd.DataFrame({"contract": ["HOG9", "HOG9", "HOH9"]}, index=idx)
    f = r2_flags("HO", dd)
    r2_audit(f, dd, "HO")
    if not bool(f.iloc[1]) or bool(f.iloc[0]):
        raise SystemExit(f"selftest: HO R2 flags {f.tolist()}")
    bad = f.copy()
    bad[:] = False
    must_raise("a session inside the delivery buffer", lambda: r2_audit(bad, dd, "HO"))
    # the null: a real draw passes its side-mix check; an all-long draw against a 50% book raises
    bk = pd.DataFrame({"session": [f"2019-{mm:02d}-{dd:02d}" for mm in range(1, 13) for dd in range(1, 21)],
                       "D": np.where(rng.random(240) < 0.5, 1, -1), "long_gross": 1.0, "short_gross": -1.0, "A_bp": 100.0})
    dr = signflip({"HO": bk}, bk["session"].to_numpy(), 1)
    if not np.isfinite(dr["family"]).all():
        raise SystemExit("selftest: the null produced non-finite draws")
    must_raise("the null's side mix", lambda: mix_check(np.ones((BATCH, 240), bool), 0.5, "HO"))
    print(f"selftest: {len(fired)} canaries fired: {fired}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=DATA)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.gates:
        print(json.dumps(build(a.data_root, gates_only=True)["data_gates"], indent=1, default=float))
        return 0
    if not a.run:
        ap.print_help()
        return 1
    out = build(a.data_root)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"gate1_family": {k: out["gate1_family"][k] for k in ("statistic_pct_A", "t_hac", "MECHANISM")},
                      "verdicts": {r: v["verdict"] for r, v in out["roots"].items()}, "predictions": out["predictions"],
                      "runtime_min": out["runtime_min"]}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
