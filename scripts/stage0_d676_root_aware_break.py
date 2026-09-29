"""D676: the root-aware break of yesterday's day-session range on CL, NG, GC and SI. Spec:
docs/decisions/D676-PRE-REG-the-root-aware-break-on-cl-ng-gc-si.md (df1865cc) and its amendment D676-A1. In-sample to
2025-02-28; the vault is never read; CL/NG post-vault sealed until 2026-10-10.

    uv run python scripts/stage0_d676_root_aware_break.py --selftest
    uv run python scripts/stage0_d676_root_aware_break.py --gates [--data-root DIR]   # data gates only, no outcome
    uv run python scripts/stage0_d676_root_aware_break.py --run   [--data-root DIR]   # once

Data: data/fixtures/fut_opening_globex_1m_cl_ng_gc_si.csv.gz (build_fut_opening_1m.py --roots CL,NG,GC,SI --breadth),
gated against fut_day1m (identity), coverage and the seal.
"""
from __future__ import annotations

import argparse
import json
import math
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
import stage0_d671_break_construction as C  # noqa: E402

M, X, T = C.M, C.X, C.T
OUT = REPO / "data" / "stage0_d676_root_aware_break.json"
FIXTURE = REPO / "data" / "fixtures" / "fut_opening_globex_1m_cl_ng_gc_si.csv.gz"
ROOTS = ("CL", "NG", "GC", "SI")
RESERVED_FROM, FIRST = "2025-03-01", "2016-01-04"
LETTER = "FGHJKMNQUVXZ"


def hm(s: str) -> int:
    return int(s[:2]) * 60 + int(s[3:])


SESS = {  # open (arm), flat (5 min before settlement), last entry (30 min before flat)
    "CL": {"open": hm("09:00"), "flat": hm("14:25"), "last": hm("13:55")},
    "NG": {"open": hm("09:00"), "flat": hm("14:25"), "last": hm("13:55")},
    "GC": {"open": hm("08:20"), "flat": hm("13:25"), "last": hm("12:55")},
    "SI": {"open": hm("08:25"), "flat": hm("13:20"), "last": hm("12:50")},
}
EIA = {"CL": "EIA_WPSR", "NG": "EIA_NGSR"}
ROLL_MONTHS = {"CL": set(range(1, 13)), "NG": set(range(1, 13)), "GC": {1, 3, 5, 7, 9, 11}, "SI": {2, 4, 6, 8, 11}}
ROLL_BD = (5, 10)
BUFFER_BD = 10
K_ATR, TRAIL, TRAIL_NG_VARIANT = 0.25, 0.25, 0.5
N_N1, POOL, N_BOOT, SEED = 1000, 32, 500, 676
MIN_TRADES = 100
COVID = ("2020-02-01", "2020-04-30")


class D676Error(RuntimeError):
    pass


# ================================================================================ costs
def costs() -> dict[str, dict[str, float]]:
    j = json.loads((REPO / "data" / "futures_costs.json").read_text(encoding="utf-8"))
    out = {}
    for r in ROOTS:
        m = j["roots"][r]["micro"]
        line = m["default_line"]
        x = float(m["crossing_ticks_rt"][line]["value"])
        out[r] = {"symbol": m["symbol"], "line": line, "tick": float(m["tick_points"]), "usd_per_point": float(m["usd_per_point"]),
                  "cost_usd": float(m["commission_rt_usd"]["value"]) + x * float(m["tick_usd"]) + float(m["tick_usd"])}
    return out


# ================================================================================ data and gates
def load_fixture(path: Path = FIXTURE) -> pd.DataFrame:
    g = pd.read_csv(path, encoding="utf-8", dtype={"session": str, "hhmm": str, "et": str})
    g = g[g["session"] < RESERVED_FROM]
    if (g["session"] >= RESERVED_FROM).any():
        raise D676Error("seal")
    g["m"] = g["hhmm"].str[:2].astype(int) * 60 + g["hhmm"].str[3:].astype(int)
    return g.sort_values(["root", "session", "et"], kind="stable").reset_index(drop=True)


def identity_gate(g: pd.DataFrame, data_root: Path) -> dict[str, Any]:
    import pyarrow.parquet as pq
    d1 = pq.read_table(data_root / "fixtures" / "fut_day1m.parquet", columns=["root", "day", "bar", "open", "high", "low", "close"],
                       filters=[("root", "in", list(ROOTS)), ("day", "<", RESERVED_FROM), ("day", ">=", "2015-09-01")]).to_pandas()
    d1["m"] = 540 + d1["bar"].astype(int)
    out = {}
    for r in ROOTS:
        a = g[(g["root"] == r) & (g["m"] >= 540) & (g["m"] <= SESS[r]["flat"]) & (g["hhmm"] < "18:00")]
        a = a.set_index(["session", "m"])[["open", "high", "low", "close"]]
        b = d1[(d1["root"] == r) & (d1["m"] <= SESS[r]["flat"])].rename(columns={"day": "session"}).set_index(["session", "m"])[["open", "high", "low", "close"]]
        j = a.join(b, lsuffix="_g", rsuffix="_d", how="inner")
        mis = int(sum((np.abs(j[f"{c}_g"] - j[f"{c}_d"]) > 1e-6).sum() for c in ("open", "high", "low", "close")))
        out[r] = {"bars_fixture": int(len(a)), "bars_day1m": int(len(b)), "matched": int(len(j)), "price_mismatches": mis,
                  "only_fixture": int(len(a) - len(j)), "only_day1m": int(len(b) - len(j)),
                  "pass": bool(mis == 0 and len(j) >= 0.99 * min(len(a), len(b)))}
    return out


def day_frame(g: pd.DataFrame, r: str) -> tuple[pd.DataFrame, dict]:
    """Per session: the day-session OHLC (open bar at the open minute; close = the flat-time bar's close), the
    contract, overnight high/low (bars before the open), coverage; plus bar arrays for the day session."""
    s = SESS[r]
    x = g[g["root"] == r]
    day = x[(x["hhmm"] < "18:00") & (x["m"] >= s["open"]) & (x["m"] <= s["flat"])]
    night = x[(x["hhmm"] >= "18:00") | (x["m"] < s["open"])]
    gd = day.groupby("session", sort=True)
    d = pd.DataFrame({"high": gd["high"].max(), "low": gd["low"].min(), "n_day": gd.size(),
                      "contract": gd["contract"].agg(lambda v: v.mode().iloc[0]),
                      "first_m": gd["m"].min(), "last_m": gd["m"].max()})
    o = day[day["m"] == s["open"]].groupby("session")["open"].first()
    c = day[day["m"] <= s["flat"]].groupby("session")["close"].last()
    d["open"], d["close"] = o.reindex(d.index), c.reindex(d.index)
    gn = night.groupby("session")
    d["on_high"], d["on_low"] = gn["high"].max().reindex(d.index), gn["low"].min().reindex(d.index)
    d["on_last_m"] = night[night["hhmm"] < "18:00"].groupby("session")["m"].max().reindex(d.index)
    n_full = s["flat"] - s["open"] + 1
    d["coverage"] = d["n_day"] / n_full
    d["usable"] = d["open"].notna() & (d["coverage"] >= 0.80)
    bars = {sess: {"m": gg["m"].to_numpy(), "o": gg["open"].to_numpy(float), "h": gg["high"].to_numpy(float),
                   "l": gg["low"].to_numpy(float), "c": gg["close"].to_numpy(float)} for sess, gg in day.groupby("session", sort=False)}
    return d, bars


def atr_prior(d: pd.DataFrame) -> pd.Series:
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(), (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.shift(1).rolling(20, min_periods=20).mean()


def atr_audit(d: pd.DataFrame, a: pd.Series, idx: list[int]) -> None:
    """Second path: ATR at session i from sessions i-20 .. i-1 only, by position in a loop."""
    h, l, c = d["high"].to_numpy(float), d["low"].to_numpy(float), d["close"].to_numpy(float)
    for i in idx:
        if i < 21 or not np.isfinite(a.iloc[i]):
            continue
        trs = [max(h[j] - l[j], abs(h[j] - c[j - 1]), abs(l[j] - c[j - 1])) for j in range(i - 20, i)]
        if not np.isclose(np.mean(trs), a.iloc[i], rtol=1e-12, atol=1e-12):
            raise D676Error("lag: the ATR uses the session's own range")


def business_days_between(a: str, b: str) -> int:
    """Weekdays strictly after a up to and including b (0 if b <= a)."""
    if b <= a:
        return 0
    return int(np.busday_count(np.datetime64(a) + 1, np.datetime64(b) + 1))


def contract_month(code: str, session: str) -> tuple[int, int]:
    """GCZ5 on 2015-09-01 -> (2015, 12). The decade is the one that puts the expiry within ~1.5 years after."""
    letter, digit = code[-2], int(code[-1])
    y = int(session[:4])
    for yy in (y, y + 1, y + 2):
        if yy % 10 == digit:
            return yy, LETTER.index(letter) + 1
    raise ValueError(code)


def first_notice(code: str, session: str) -> str:
    """COMEX first notice day: the last business day of the month BEFORE the contract month."""
    yy, mm = contract_month(code, session)
    first_of = pd.Timestamp(year=yy, month=mm, day=1)
    d = first_of - pd.Timedelta(days=1)
    while d.weekday() >= 5:
        d -= pd.Timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def flags(r: str, d: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    idx = d.index
    f = pd.DataFrame(index=idx)
    f["R1_roll"] = d["contract"] != d["contract"].shift(1)
    cr = cal.reindex(idx)
    if r in ("CL", "NG"):
        exp = [(pd.Timestamp(s) + pd.Timedelta(days=float(k))).strftime("%Y-%m-%d") if np.isfinite(k) else None
               for s, k in zip(idx, cr["days_to_expiry"].to_numpy(float))]
        f["R2_delivery"] = [business_days_between(s, e) <= BUFFER_BD if e else False for s, e in zip(idx, exp)]
    else:
        fnd = [first_notice(c, s) for c, s in zip(d["contract"], idx)]
        f["R2_delivery"] = [business_days_between(s, e) <= BUFFER_BD for s, e in zip(idx, fnd)]
    ym = pd.Series(idx.str[:7], index=idx)
    bd = ym.groupby(ym).cumcount() + 1  # business day of the month on the root's own session calendar
    months = pd.Series([int(s[5:7]) for s in idx], index=idx)
    f["R3_index_roll"] = months.isin(ROLL_MONTHS[r]) & bd.between(*ROLL_BD)
    f["bd_of_month"] = bd
    f["cpi"] = cr["cpi"].fillna(False).astype(bool)
    f["empsit"] = cr["empsit"].fillna(False).astype(bool)
    return f


def delivery_audit(f: pd.DataFrame, d: pd.DataFrame, r: str, cal: pd.DataFrame) -> None:
    """A session inside the buffer must be flagged (second path: calendar days to the expiry/FND >= buffer weekdays)."""
    for s in f.index[:: max(1, len(f) // 25)]:
        if r in ("CL", "NG"):
            k = cal["days_to_expiry"].get(s, np.nan)
            if not np.isfinite(k):
                continue
            e = (pd.Timestamp(s) + pd.Timedelta(days=float(k))).strftime("%Y-%m-%d")
        else:
            e = first_notice(d.at[s, "contract"], s)
        want = len(pd.bdate_range(pd.Timestamp(s) + pd.Timedelta(days=1), e)) <= BUFFER_BD
        if bool(f.at[s, "R2_delivery"]) != want:
            raise D676Error(f"delivery buffer: {r} {s} flagged {f.at[s, 'R2_delivery']}, second path {want}")


# ================================================================================ the break and exits
def break_scan(bb: dict, Lh: float, Ll: float, A: float, arm: int, last: int, tick: float) -> dict | None:
    m, o, h, l = bb["m"], bb["o"], bb["h"], bb["l"]
    for i in range(len(m)):
        if m[i] < arm:
            continue
        if m[i] > last:
            return None
        for D, L in ((1, Lh), (-1, Ll)):
            stop = L + D * K_ATR * A
            if (D > 0 and h[i] >= stop) or (D < 0 and l[i] <= stop):
                fill = (max(stop, o[i]) + tick) if D > 0 else (min(stop, o[i]) - tick)
                return {"D": D, "i": i, "entry": float(fill), "L": L, "stop": stop, "minute": int(m[i]),
                        "open_fill": bool((D > 0 and o[i] > stop) or (D < 0 and o[i] < stop))}
    return None


def exit_trade(bb: dict, i: int, D: int, entry: float, stop_lvl: float, A: float, flat: int, tick: float,
               trail: float | None) -> tuple[float, str]:
    """E4 (trail = K x A) or E2 (trail None): from the bar after entry to the flat-time bar; stop first within a bar."""
    m, o, h, l, c = bb["m"], bb["o"], bb["h"], bb["l"], bb["c"]
    stop, best = stop_lvl, entry
    for k in range(i + 1, len(m)):
        if m[k] > flat:
            break
        if (D > 0 and l[k] <= stop) or (D < 0 and h[k] >= stop):
            through = (o[k] <= stop) if D > 0 else (o[k] >= stop)
            return float((o[k] if through else stop) - D * tick), "stop"
        if trail is not None:
            best = max(best, h[k]) if D > 0 else min(best, l[k])
            new = best - D * trail * A
            stop = max(stop, new) if D > 0 else min(stop, new)
    j = np.flatnonzero(m <= flat)
    return float(c[j[-1]]), "flat"


def flat_audit(bb: dict, flat: int) -> None:
    if (bb["m"] > flat).any():
        raise D676Error("flat: a day-session bar after the flat time is in the exit window")


def eia_arm(r: str, events: pd.DataFrame, sessions: pd.Index) -> pd.Series:
    """The arm minute per session: the open, or the release minute + 1 on the root's EIA days (a release at or after
    the flat time leaves the open as the arm)."""
    arm = pd.Series(SESS[r]["open"], index=sessions, dtype=int)
    if r not in EIA:
        return arm
    e = events[events["event"] == EIA[r]]
    for dt in e["datetime_et"]:
        s, mm = str(dt)[:10], hm(str(dt)[11:16])
        if s in arm.index and mm < SESS[r]["flat"]:
            arm[s] = max(arm[s], mm + 1)
    return arm


def eia_audit(t: dict | None, arm_min: int) -> None:
    if t is not None and t["minute"] < arm_min:
        raise D676Error("EIA: a fill before the release was taken")


# ================================================================================ per root
def root_job(args: tuple) -> dict[str, Any]:
    r, d, bars, arm, cost, seed = args
    s = SESS[r]
    tick = cost["tick"]
    rows = []
    for sess, rec in d.iterrows():
        bb = bars.get(sess)
        if bb is None or not rec["eligible_base"]:
            continue
        flat_audit(bb, s["flat"])
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        t_open = break_scan(bb, Lh, Ll, A, s["open"], s["last"], tick)
        t_arm = break_scan(bb, Lh, Ll, A, int(arm[sess]), s["last"], tick)
        eia_audit(t_arm, int(arm[sess]))
        for kind, t in (("open", t_open), ("armed", t_arm)):
            if t is None:
                continue
            rec_ = {"session": sess, "kind": kind, "D": t["D"], "minute": t["minute"], "entry": t["entry"], "L": t["L"], "A": A,
                    "open_fill": t["open_fill"], "cost_bp": cost["cost_usd"] / cost["usd_per_point"] / t["entry"] * 1e4}
            for nm, tr_ in (("E4", TRAIL), ("E2", None), ("E4w", TRAIL_NG_VARIANT)):
                px, why = exit_trade(bb, t["i"], t["D"], t["entry"], t["L"], A, s["flat"], tick, tr_)
                rec_[f"{nm}_gross"] = t["D"] * (px / t["entry"] - 1) * 1e4
                rec_[f"{nm}_why"] = why
            m_, h_, l_ = bb["m"], bb["h"], bb["l"]
            after = np.arange(t["i"] + 1, len(m_))
            after = after[m_[after] <= s["flat"]]
            rec_["retest"] = bool(len(after) and ((l_[after] <= t["L"]).any() if t["D"] > 0 else (h_[after] >= t["L"]).any()))
            rows.append(rec_)
    # N1's pool on every primary-eligible session, from the ARMED trades' clock and side mix
    rng = np.random.default_rng(seed)
    armed = [x for x in rows if x["kind"] == "armed"]
    mins = np.array([x["minute"] for x in armed], dtype=int)
    p_long = float(np.mean([x["D"] > 0 for x in armed])) if armed else 0.5
    pool, pool_side, pool_sess = [], [], []
    for sess, rec in d.iterrows():
        bb = bars.get(sess)
        if bb is None or not rec["eligible_primary"] or not len(mins):
            continue
        A = float(rec["atr20"])
        gg, sd = np.full(POOL, np.nan), np.zeros(POOL, dtype=int)
        for k in range(POOL):
            mn = max(int(mins[rng.integers(0, len(mins))]), int(arm[sess]))
            Dd = 1 if rng.random() < p_long else -1
            sd[k] = Dd
            j = np.flatnonzero((bb["m"] >= mn) & (bb["m"] <= s["last"]))
            if not len(j):
                continue
            kk = int(j[0])
            ent = float(bb["c"][kk]) + Dd * tick
            px, _ = exit_trade(bb, kk, Dd, ent, ent - Dd * (K_ATR * A + tick), A, s["flat"], tick, TRAIL)
            gg[k] = Dd * (px / ent - 1) * 1e4
        pool.append(gg)
        pool_side.append(sd)
        pool_sess.append(sess)
    return {"root": r, "rows": rows, "pool": np.array(pool), "pool_side": np.array(pool_side), "pool_sessions": pool_sess,
            "p_long": p_long}


def build(data_root: Path, gates_only: bool = False) -> dict[str, Any]:
    t0 = time.time()
    cst = costs()
    g = load_fixture()
    out: dict[str, Any] = {"spec": "D676 (df1865cc) + D676-A1", "costs": cst, "data_gates": {"identity": identity_gate(g, data_root)}}
    cal_all = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    events = pd.read_csv(data_root / "calendar" / "events.csv", encoding="utf-8")
    frames, barsd, arms = {}, {}, {}
    cov = {}
    for r in ROOTS:
        d, bars = day_frame(g, r)
        cov[r] = {"sessions": int(len(d)), "unusable": int((~d["usable"]).sum()),
                  "coverage_median": float(d["coverage"].median()),
                  "by_year_usable": {y: round(float(v), 3) for y, v in d["usable"].groupby(d.index.str[:4]).mean().items()}}
        d = d[d["usable"]].copy()
        d["atr20"] = atr_prior(d)
        atr_audit(d, d["atr20"], list(range(0, len(d), max(1, len(d) // 30))))
        same = d["contract"] == d["contract"].shift(1)
        d["prior_high"] = d["high"].shift(1).where(same)
        d["prior_low"] = d["low"].shift(1).where(same)
        d["prior_close"] = d["close"].shift(1)
        cal = cal_all[cal_all["root"] == r].set_index("day")
        fl = flags(r, d, cal)
        delivery_audit(fl, d, r, cal)
        d = d.join(fl)
        in_window = (d.index >= FIRST) & np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)
        d["eligible_base"] = in_window  # every session the break can be computed on (for the removed-trade reads)
        d["eligible_primary"] = in_window & ~d["R1_roll"] & ~d["R2_delivery"] & ~d["R3_index_roll"]
        # the overnight two-way range (secondary)
        d["on_range"] = (d["on_high"] - d["on_low"] - (d["open"] - d["prior_close"]).abs()) / d["atr20"]
        if (d["on_last_m"].dropna() >= SESS[r]["open"]).any():
            raise D676Error(f"overnight: {r} reads a bar at or after the open")
        frames[r], barsd[r] = d, bars
        arms[r] = eia_arm(r, events, d.index)
    out["data_gates"]["coverage"] = cov
    if not all(v["pass"] for v in out["data_gates"]["identity"].values()):
        raise D676Error(f"identity gate failed: {out['data_gates']['identity']}")
    if gates_only:
        return out
    with ProcessPoolExecutor(max_workers=4) as pool:
        got = {o["root"]: o for o in pool.map(root_job, [(r, frames[r], barsd[r], arms[r], cst[r], SEED + i) for i, r in enumerate(ROOTS)])}
    rng = np.random.default_rng(SEED)
    b_all, use_nq, _gd, R = M.load_bars(data_root, False, ("ES", "NQ"))  # NQ only for the rebuilt K8
    C._R = R
    tabs = R.session_table(b_all, use_nq, roots=("NQ",))
    k8 = M.k8_daily(tabs["NQ"], tabs["NQ"].index[(tabs["NQ"].index >= FIRST) & (tabs["NQ"].index < RESERVED_FROM)])
    out["roots"], daily = {}, {}
    for r in ROOTS:
        d = frames[r]
        tr = pd.DataFrame(got[r]["rows"])
        if tr.empty:
            out["roots"][r] = {"note": "no trades"}
            continue
        el = d["eligible_primary"]
        prim = tr[(tr["kind"] == "armed") & tr["session"].map(el).fillna(False).astype(bool)].sort_values("session").reset_index(drop=True)
        ses = d.index[(d.index >= FIRST)]
        years = len(ses) / 252
        usd_pt = cst[r]["usd_per_point"]
        bk = lambda t_, k, col="E4_gross": C.book(t_.assign(retest=t_["retest"]), k, col, years, usd_pt, ses)  # noqa: E731
        ones = np.ones(len(prim), bool)
        g4 = prim["E4_gross"].to_numpy(float)
        net = g4 - prim["cost_bp"].to_numpy(float)
        gm, gt, gse = M.mean_t(g4, R)
        # N1
        n1 = M.n1_draws(got[r]["pool"], got[r]["pool_side"], len(prim), SEED + 100 + ROOTS.index(r))
        q95 = [np.quantile(rng.choice(n1["all"], N_N1), 0.95) for _ in range(N_BOOT)]
        exc = ~prim["session"].between(*COVID).to_numpy()
        tk = cst[r]["tick"] / prim["entry"].to_numpy(float) * 1e4
        g1 = {"trades": int(len(prim)), "gross_mean": gm, "t_hac": gt, "p_one_sided": float(stats.norm.sf(gt)),
              "n1": {"p50": float(np.median(n1["all"])), "p95": float(np.quantile(n1["all"], 0.95)), "p95_se": float(np.std(q95, ddof=1)),
                     "rank": float((n1["all"] < gm).mean())},
              "ex_covid_gross": float(g4[exc].mean()), "mde80": M.Z80 * gse}
        nm_, nt_, _ = M.mean_t(net, R)
        g2 = {"net_mean": nm_, "net_t_hac": nt_, "p_one_sided": float(stats.norm.sf(nt_)) if np.isfinite(nt_) else 1.0,
              "net_plus1tick": float((net - 2 * tk).mean()), "net_ex_covid": float(net[exc].mean())}
        # what each adjustment removed (the break armed at the open on the base-eligible sessions)
        base = tr[(tr["kind"] == "open")].copy()
        base = base.join(d[["R1_roll", "R2_delivery", "R3_index_roll", "cpi", "empsit"]], on="session")
        removed = {}
        for rr_ in ("R1_roll", "R2_delivery", "R3_index_roll"):
            k = base[rr_].to_numpy(bool)
            removed[rr_] = {"removed": bk(base, k), "kept": bk(base, ~k)}
        if r in EIA:
            eia_days = set(s_ for s_ in d.index if arms[r][s_] > SESS[r]["open"])
            ob = base[base["session"].isin(eia_days)]
            refused = ob[ob["minute"] < ob["session"].map(arms[r])]
            ab = tr[(tr["kind"] == "armed") & tr["session"].isin(eia_days)]
            removed["R4_eia"] = {"pre_release_breaks_refused": bk(refused, np.ones(len(refused), bool)),
                                 "armed_after_release": bk(ab, np.ones(len(ab), bool)), "eia_days": len(eia_days)}
        # secondary: quiet overnight
        onr = d["on_range"].to_numpy(float)
        tier = pd.Series(C.tiers(onr), index=d.index)
        C.tier_audit(tier.to_numpy(), onr, list(range(0, len(onr), max(1, len(onr) // 12))))
        prim["tier"] = prim["session"].map(tier).to_numpy(float)
        win = np.isfinite(prim["tier"].to_numpy(float))
        q1 = win & (prim["tier"].to_numpy(float) < 1 / 3)
        rot_s = tier[d["eligible_primary"]]
        cs = rot_s.dropna()
        tv = cs.to_numpy()
        pos = pd.Series(np.arange(len(cs)), index=cs.index).reindex(prim["session"]).to_numpy()
        okp = np.isfinite(pos) & win
        diffs = []
        for kk in range(21, len(tv) - 21):
            rt = np.full(len(prim), np.nan)
            rt[okp] = np.roll(tv, kk)[pos[okp].astype(int)]
            diffs.append(g4[okp & (rt < 1 / 3)].mean() - g4[okp & (rt >= 1 / 3)].mean())
        diffs = np.array(diffs)
        act = float(g4[q1].mean() - g4[win & ~q1].mean())
        sec = {"quiet_third": bk(prim, q1), "rest": bk(prim, win & ~q1),
               "rotation": {"quiet_minus_rest_gross": act, "p50": float(np.median(diffs)), "p95": float(np.quantile(diffs, 0.95)),
                            "rank": float((diffs < act).mean())}}
        yrs = prim["session"].str[:4].to_numpy()
        D = prim["D"].to_numpy(int)
        pj = prim.join(d[["cpi", "empsit"]], on="session")
        rep = {"long": bk(prim, D > 0), "short": bk(prim, D < 0), "E2": bk(prim, ones, "E2_gross"),
               "by_year": {y: bk(prim, yrs == y) for y in sorted(set(yrs))},
               "cpi_days": bk(prim, pj["cpi"].to_numpy(bool)), "empsit_days": bk(prim, pj["empsit"].to_numpy(bool)),
               "open_fill_share": float(prim["open_fill"].mean())}
        if r == "NG":
            rep["NG_trail_0.5A"] = bk(prim, ones, "E4w_gross")
        fg = X.four_groups(prim, pd.Series(g4), pd.Series(net), len(prim) / years, R, r)
        daily[r] = M.daily_usd(prim, net, ones.astype(float), ses, usd_pt)
        out["roots"][r] = {"primary": bk(prim, ones), "gate1": g1, "gate2": g2, "removed_by_adjustment": removed,
                           "secondary_quiet_overnight": sec, "reported": rep, "four_groups": fg,
                           "_comp": (prim, net, g4, ses, usd_pt)}
    for r in ROOTS:
        if "_comp" not in out["roots"].get(r, {}):
            continue
        prim, net, g4, ses, usd_pt = out["roots"][r].pop("_comp")
        others = {o_: daily[o_] for o_ in daily if o_ != r}
        comp = M.component(prim, net, g4, np.ones(len(prim)), ses, usd_pt, k8, others)
        comp["not_rebuilt"] = comp.get("not_rebuilt", []) + ["#3 NG winter spread: daily P&L not rebuilt here (named missing)"]
        out["roots"][r]["component"] = comp
    # verdicts
    rr = out["roots"]
    live = [r for r in ROOTS if "gate1" in rr[r]]
    h1 = T.holm({r: rr[r]["gate1"]["p_one_sided"] for r in live})
    passed = []
    for r in live:
        g1 = rr[r]["gate1"]
        g1["checks"] = {"gross_positive_holm": bool(g1["gross_mean"] > 0 and h1[r] < 0.05),
                        "above_n1_p95": bool(g1["gross_mean"] - g1["n1"]["p95"] > 2 * g1["n1"]["p95_se"]),
                        "positive_ex_covid": bool(g1["ex_covid_gross"] > 0), "holm_p": h1[r]}
        if all(v for k, v in g1["checks"].items() if k != "holm_p"):
            passed.append(r)
    h2 = T.holm({r: rr[r]["gate2"]["p_one_sided"] for r in passed}) if passed else {}
    for r in live:
        g2 = rr[r]["gate2"]
        ok = bool(r in h2 and h2[r] < 0.05 and g2["net_mean"] > 0 and g2["net_plus1tick"] > 0
                  and rr[r]["gate1"]["trades"] >= MIN_TRADES and g2["net_ex_covid"] > 0)
        g2["checks"] = {"pass": ok, "holm_p": h2.get(r)}
        rr[r]["verdict"] = "SUPPORTED" if r in passed and ok else "MECHANISM ONLY" if r in passed else "NOT SUPPORTED"
    sp = {r: rr[r]["secondary_quiet_overnight"]["rotation"]["quiet_minus_rest_gross"] for r in live}
    eia_ok = [rr[r]["removed_by_adjustment"]["R4_eia"]["armed_after_release"].get("gross", -99)
              > rr[r]["removed_by_adjustment"]["R4_eia"]["pre_release_breaks_refused"].get("gross", 99) for r in ("CL", "NG") if r in live]
    out["predictions"] = {
        "1_NG_and_CL_pass_gate1": bool("NG" in passed and "CL" in passed),
        "2_SI_gross_positive_fails_gate2": bool(rr["SI"]["gate1"]["gross_mean"] > 0 and rr["SI"].get("verdict") != "SUPPORTED"),
        "3_GC_fails_gate1": "GC" not in passed,
        "4_quiet_overnight_positive_on_3_of_4": bool(sum(v > 0 for v in sp.values()) >= 3),
        "5_EIA_armed_beats_refused_on_CL_and_NG": bool(eia_ok and all(eia_ok))}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    T.licence_guard(out)
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D676Error:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(7)
    d = pd.DataFrame({"high": 100 + rng.random(60) * 3, "low": 99 - rng.random(60) * 3, "close": 100 + rng.normal(0, 1, 60)},
                     index=[f"2019-01-{i:02d}" for i in range(1, 61)])
    a = atr_prior(d)
    atr_audit(d, a, [30, 45, 59])
    leak = a.copy()
    tr_ = pd.concat([d["high"] - d["low"], (d["high"] - d["close"].shift(1)).abs(), (d["low"] - d["close"].shift(1)).abs()], axis=1).max(axis=1)
    leak[:] = tr_.rolling(20, min_periods=20).mean()  # includes the session's own range
    must_raise("ATR with the session's own range", lambda: atr_audit(d, leak, [30, 45, 59]))
    m = np.arange(hm("09:00"), hm("12:00"))
    up = np.linspace(100, 110, len(m))
    bb = {"m": m, "o": up, "h": up + 0.02, "l": up - 0.02, "c": up}
    t = break_scan(bb, 101.0, 90.0, 4.0, hm("09:00"), hm("11:30"), 0.01)
    if t is None or abs(t["entry"] - (max(t["stop"], bb["o"][t["i"]]) + 0.01)) > 1e-12:
        raise SystemExit("selftest: the fill did not carry the root's tick")
    px, _ = exit_trade(bb, t["i"], 1, t["entry"], t["L"], 4.0, hm("11:59"), 0.01, TRAIL)
    if not px > t["entry"]:
        raise SystemExit("selftest: a long that rises did not pay")
    t_arm = break_scan(bb, 101.0, 90.0, 4.0, hm("10:31"), hm("11:30"), 0.01)
    eia_audit(t_arm, hm("10:31"))
    must_raise("a fill before the EIA release", lambda: eia_audit(t, hm("10:31")))
    must_raise("a bar after the flat time", lambda: flat_audit(bb, hm("10:00")))
    idx = pd.Index(["2019-01-10", "2019-01-15", "2019-02-20"])
    dd = pd.DataFrame({"contract": ["CLG9", "CLG9", "CLJ9"]}, index=idx)
    cal = pd.DataFrame({"days_to_expiry": [12.0, 7.0, 30.0], "cpi": False, "empsit": False}, index=idx)
    f = flags("CL", dd, cal)
    delivery_audit(f, dd, "CL", cal)
    bad = f.copy()
    bad["R2_delivery"] = False
    must_raise("a session inside the delivery buffer", lambda: delivery_audit(bad, dd, "CL", cal))
    if first_notice("GCZ5", "2015-09-01") != "2015-11-30" or first_notice("SIH9", "2019-01-15") != "2019-02-28":
        raise SystemExit("selftest: first notice day")
    if business_days_between("2019-01-10", "2019-01-22") != 8:
        raise SystemExit("selftest: business-day count")
    print(f"selftest: {len(fired)} canaries fired: {fired}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
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
    print(json.dumps({"verdicts": {r: v.get("verdict") for r, v in out["roots"].items()}, "predictions": out["predictions"],
                      "runtime_min": out["runtime_min"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
