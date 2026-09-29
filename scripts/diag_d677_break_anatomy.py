"""D677 DIAG: a strategy diagnostic of D676's root-aware break on CL, NG, GC and SI -- why the trade loses, layer by
layer (entry, exit, friction, where it fires, the root-aware skips) -- and the same break's excess over random entry on
all eight roots (D668's four from their committed JSON). In-sample only, already read by D676's single run; the vault
is never read; CL/NG post-vault data stays sealed until D626's read.

    uv run --with pyarrow python scripts/diag_d677_break_anatomy.py

Reuses D676's runner functions unchanged and asserts it reproduces D676's primary gross, base gross and removed-trade
reads before reporting anything new.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d676_root_aware_break as B  # noqa: E402

M = B.M
OUT = REPO / "data" / "diag_d677_break_anatomy.json"
H = (5, 15, 30, 60, 120)
TRAILS = {"trail_0.25A": 0.25, "trail_0.5A": 0.5, "trail_1A": 1.0, "E2_no_trail": None}
REACH = (0.25, 0.5, 1.0)
DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")


def exit_ix(bb: dict, i: int, D: int, entry: float, stop_lvl: float, A: float, flat: int, tick: float,
            trail: float | None) -> tuple[float, str, int]:
    """B.exit_trade, also returning the exit bar's index (asserted equal in price below)."""
    m, o, h, l, c = bb["m"], bb["o"], bb["h"], bb["l"], bb["c"]
    stop, best = stop_lvl, entry
    for k in range(i + 1, len(m)):
        if m[k] > flat:
            break
        if (D > 0 and l[k] <= stop) or (D < 0 and h[k] >= stop):
            through = (o[k] <= stop) if D > 0 else (o[k] >= stop)
            return float((o[k] if through else stop) - D * tick), "stop", k
        if trail is not None:
            best = max(best, h[k]) if D > 0 else min(best, l[k])
            new = best - D * trail * A
            stop = max(stop, new) if D > 0 else min(stop, new)
    j = np.flatnonzero(m <= flat)
    return float(c[j[-1]]), "flat", int(j[-1])


def mt(x, R) -> dict:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return {"n": int(len(x)), "mean": None, "t": None, "se": None, "sd": None}
    m, t, se = M.mean_t(x, R)
    return {"n": int(len(x)), "mean": m, "t": t, "se": se, "sd": float(x.std(ddof=1))}


def diff(a, b, R) -> dict:
    x, y = mt(a, R), mt(b, R)
    if x["mean"] is None or y["mean"] is None:
        return {"a": x, "b": y, "diff": None, "t": None}
    dd = x["mean"] - y["mean"]
    return {"a": x, "b": y, "diff": dd, "t": dd / np.hypot(x["se"], y["se"])}


def frames() -> dict:
    cst = B.costs()
    g = B.load_fixture()
    cal_all = pd.read_csv(DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    events = pd.read_csv(DATA / "calendar" / "events.csv", encoding="utf-8")
    fc = json.loads((REPO / "data" / "futures_costs.json").read_text(encoding="utf-8"))
    out = {}
    for r in B.ROOTS:
        d, bars = B.day_frame(g, r)
        d = d[d["usable"]].copy()
        d["atr20"] = B.atr_prior(d)
        same = d["contract"] == d["contract"].shift(1)
        d["prior_high"] = d["high"].shift(1).where(same)
        d["prior_low"] = d["low"].shift(1).where(same)
        d["prior_close"] = d["close"].shift(1)
        cal = cal_all[cal_all["root"] == r].set_index("day")
        d = d.join(B.flags(r, d, cal))
        in_window = (d.index >= B.FIRST) & np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)
        d["eligible_base"] = in_window
        d["eligible_primary"] = in_window & ~d["R1_roll"] & ~d["R2_delivery"] & ~d["R3_index_roll"]
        cr = cal.reindex(d.index)
        if r in ("CL", "NG"):
            k = cr["days_to_expiry"].to_numpy(float)
            d["bd_to_delivery"] = [B.business_days_between(s, (pd.Timestamp(s) + pd.Timedelta(days=float(kk))).strftime("%Y-%m-%d"))
                                   if np.isfinite(kk) else np.nan for s, kk in zip(d.index, k)]
        else:
            d["bd_to_delivery"] = [B.business_days_between(s, B.first_notice(c, s)) for c, s in zip(d["contract"], d.index)]
        m = fc["roots"][r]["micro"]
        x = float(m["crossing_ticks_rt"][m["default_line"]]["value"])
        cost = dict(cst[r], crossing_ticks_rt=x, commission_usd=float(m["commission_rt_usd"]["value"]), tick_usd=float(m["tick_usd"]))
        out[r] = (d, bars, B.eia_arm(r, events, d.index), cost)
    return out


def drift_table(d: pd.DataFrame, bars: dict, r: str) -> tuple[np.ndarray, int]:
    """Mean forward return (bp) from each minute's close over each horizon (and to the flat bar), over the
    primary-eligible sessions: the same-clock drift a random-side entry would carry."""
    s = B.SESS[r]
    mins = np.arange(s["open"], s["flat"] + 1)
    ses = [x for x in d.index[d["eligible_primary"]] if x in bars]
    C = np.full((len(ses), len(mins)), np.nan)
    for a, x in enumerate(ses):
        bb = bars[x]
        C[a, bb["m"] - s["open"]] = bb["c"]
    C = pd.DataFrame(C).ffill(axis=1).to_numpy()
    mu = np.full((len(mins), len(H) + 1), np.nan)
    for j, h in enumerate(H):
        if h < len(mins):
            mu[: len(mins) - h, j] = np.nanmean(C[:, h:] / C[:, : len(mins) - h] - 1, axis=0) * 1e4
    mu[:, -1] = np.nanmean(C[:, -1:] / C - 1, axis=0) * 1e4
    return mu, s["open"]


def trades(r: str, d: pd.DataFrame, bars: dict, arm: pd.Series, cost: dict) -> pd.DataFrame:
    s = B.SESS[r]
    tick, flat = cost["tick"], s["flat"]
    rows = []
    for sess, rec in d.iterrows():
        bb = bars.get(sess)
        if bb is None or not rec["eligible_base"]:
            continue
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        for kind, am in (("open", s["open"]), ("armed", int(arm[sess]))):
            t = B.break_scan(bb, Lh, Ll, A, am, s["last"], tick)
            if t is None:
                continue
            D, i, entry, L = t["D"], t["i"], t["entry"], t["L"]
            lvl = entry - D * tick
            px, why, k = exit_ix(bb, i, D, entry, L, A, flat, tick, B.TRAIL)
            ref, _ = B.exit_trade(bb, i, D, entry, L, A, flat, tick, B.TRAIL)
            if px != ref:
                raise SystemExit("exit_ix disagrees with D676's exit_trade")
            m, h, l, c = bb["m"], bb["h"], bb["l"], bb["c"]
            row = {"session": sess, "kind": kind, "D": D, "minute": int(m[i]), "A": A, "entry": entry, "level": lvl,
                   "A_bp": A / lvl * 1e4, "open_fill": t["open_fill"],
                   "pretested": bool((D > 0 and rec["on_high"] >= t["stop"]) or (D < 0 and rec["on_low"] <= t["stop"])),
                   "E4_prereg": D * (px / entry - 1) * 1e4, "E4_why": why, "hold_min": int(m[k] - m[i]),
                   "cost_bp": cost["cost_usd"] / cost["usd_per_point"] / entry * 1e4,
                   "commission_bp": cost["commission_usd"] / cost["usd_per_point"] / entry * 1e4,
                   "crossing_bp": cost["crossing_ticks_rt"] * cost["tick_usd"] / cost["usd_per_point"] / entry * 1e4,
                   "tick_bp": tick / entry * 1e4}
            for nm, tr_ in TRAILS.items():  # every exit at the level: no fill ticks
                p0, _, _ = exit_ix(bb, i, D, lvl, L, A, flat, 0.0, tr_)
                row[f"lvl_{nm}"] = D * (p0 / lvl - 1) * 1e4
            jf = np.flatnonzero(m <= flat)[-1]
            row["lvl_hold_to_flat"] = D * (c[jf] / lvl - 1) * 1e4
            for h_ in H:
                kk = np.flatnonzero(m <= m[i] + h_)[-1]
                ok = m[i] + h_ <= flat
                row[f"fwd_{h_}"] = D * (c[kk] / lvl - 1) * 1e4 if ok else np.nan
                row[f"fwdbar_{h_}"] = D * (c[kk] / c[i] - 1) * 1e4 if ok else np.nan
            row["fwd_flat"] = row["lvl_hold_to_flat"]
            row["fwdbar_flat"] = D * (c[jf] / c[i] - 1) * 1e4
            row["break_bar_close"] = D * (c[i] / lvl - 1) * 1e4
            # first touch: +x A from the level before the initial stop (yesterday's level); a bar that does both = stop
            fav = {x: None for x in REACH}
            for q in range(i + 1, jf + 1):
                adv = (l[q] <= L) if D > 0 else (h[q] >= L)
                if adv:
                    break
                for x in REACH:
                    if fav[x] is None and ((D > 0 and h[q] >= lvl + x * A) or (D < 0 and l[q] <= lvl - x * A)):
                        fav[x] = q
            for x in REACH:
                row[f"reach_{x}A"] = fav[x] is not None
            k60 = np.flatnonzero((m > m[i]) & (m <= min(m[i] + 60, flat)))
            if len(k60):
                row["mfe60_A"] = (h[k60].max() - lvl) / A if D > 0 else (lvl - l[k60].min()) / A
                row["mae60_A"] = (lvl - l[k60].min()) / A if D > 0 else (h[k60].max() - lvl) / A
            row["stop_dist_A"] = abs(lvl - L) / A
            for f_ in ("R1_roll", "R2_delivery", "R3_index_roll", "bd_of_month", "bd_to_delivery", "eligible_primary"):
                row[f_] = rec[f_]
            row["eia_day"] = bool(arm[sess] > s["open"])
            row["release_m"] = int(arm[sess]) if arm[sess] > s["open"] else B.hm("10:31")
            rows.append(row)
    return pd.DataFrame(rows)


def root_diag(r: str, d, bars, arm, cost, R, d676: dict) -> dict:
    tr = trades(r, d, bars, arm, cost)
    prim = tr[(tr["kind"] == "armed") & tr["eligible_primary"].astype(bool)].sort_values("session").reset_index(drop=True)
    base = tr[tr["kind"] == "open"].sort_values("session").reset_index(drop=True)
    # reproduction of D676
    j = d676["roots"][r]
    checks = {"primary_gross": (prim["E4_prereg"].mean(), j["primary"]["gross"]),
              "base_gross": (base["E4_prereg"].mean(), j["removed_by_adjustment"]["R1_roll"]["kept"]["gross"]),
              "R2_removed": (base.loc[base["R2_delivery"].astype(bool), "E4_prereg"].mean(), j["removed_by_adjustment"]["R2_delivery"]["removed"]["gross"]),
              "R3_removed": (base.loc[base["R3_index_roll"].astype(bool), "E4_prereg"].mean(), j["removed_by_adjustment"]["R3_index_roll"]["removed"]["gross"])}
    for k, (a, b) in checks.items():
        if abs(a - b) > 1e-9:
            raise SystemExit(f"{r}: {k} does not reproduce D676 ({a} vs {b})")
    mu, m0 = drift_table(d, bars, r)
    out: dict = {"reproduces_D676": {k: v[0] for k, v in checks.items()}, "trades": int(len(prim))}
    # 1. the friction ladder (primary book)
    lv = prim["lvl_trail_0.25A"].to_numpy(float)
    g = prim["E4_prereg"].to_numpy(float)
    single = lv - prim["commission_bp"].to_numpy(float) - prim["crossing_bp"].to_numpy(float)
    out["ladder"] = {"at_level_gross": mt(lv, R), "fill_ticks_drag": float(g.mean() - lv.mean()), "prereg_gross": mt(g, R),
                     "cost_bp": float(prim["cost_bp"].mean()), "of_which_commission": float(prim["commission_bp"].mean()),
                     "of_which_crossing": float(prim["crossing_bp"].mean()), "of_which_extra_tick": float(prim["tick_bp"].mean()),
                     "prereg_net": mt(g - prim["cost_bp"].to_numpy(float), R),
                     "single_count_net_(level_minus_commission_and_crossing)": mt(single, R),
                     "ATR_bp_median": float(prim["A_bp"].median()),
                     "cost_pct_of_ATR": float((prim["cost_bp"] / prim["A_bp"]).median() * 100),
                     "all_friction_pct_of_ATR": float(((prim["cost_bp"] + (lv - g)) / prim["A_bp"]).median() * 100)}
    # 2. the entry: does price continue after the break? (from the level, drift at the same clock removed)
    cont = {}
    for j_, h_ in enumerate(list(H) + ["flat"]):
        f = prim[f"fwd_{h_}"].to_numpy(float)
        fb = prim[f"fwdbar_{h_}"].to_numpy(float)
        ctrl = prim["D"].to_numpy(float) * mu[np.clip(prim["minute"].to_numpy(int) - m0, 0, len(mu) - 1), j_]
        cont[str(h_)] = {"from_level": mt(f, R), "from_break_bar_close": mt(fb, R), "same_clock_drift": float(np.nanmean(ctrl)),
                         "from_level_minus_drift": mt(f - ctrl, R), "share_positive": float(np.nanmean(f > 0)),
                         "in_ATR_pct": float(np.nanmean(f / prim["A_bp"].to_numpy(float)) * 100)}
    out["continuation"] = cont
    out["break_bar_close_from_level"] = mt(prim["break_bar_close"], R)
    out["reach_before_initial_stop"] = {f"{x}A": float(prim[f"reach_{x}A"].mean()) for x in REACH}
    out["mfe60_A_median"] = float(prim["mfe60_A"].median())
    out["mae60_A_median"] = float(prim["mae60_A"].median())
    out["initial_stop_distance_A_median"] = float(prim["stop_dist_A"].median())
    # 3. the exit
    st = prim["E4_why"] == "stop"
    early = st & (prim["hold_min"] <= 15)
    out["exit"] = {"grid_at_level": {nm: mt(prim[f"lvl_{nm}"], R) for nm in list(TRAILS) + ["hold_to_flat"]},
                   "share_stopped": float(st.mean()), "hold_min_median": float(prim["hold_min"].median()),
                   "stopped_within_15min": {"share": float(early.mean()), "gross": mt(prim.loc[early, "E4_prereg"], R)},
                   "stopped_later": mt(prim.loc[st & ~early, "E4_prereg"], R), "reached_flat": mt(prim.loc[~st, "E4_prereg"], R)}
    # 4. where it fires
    of = prim["open_fill"].astype(bool)
    pt = prim["pretested"].astype(bool)
    mb = pd.cut(prim["minute"] - B.SESS[r]["open"], [-1, 29, 119, 10_000], labels=["first_30min", "30-120min", "after_120min"])
    out["where"] = {"open_fill_gap": {"share": float(of.mean()), "E4_prereg": mt(prim.loc[of, "E4_prereg"], R), "at_level": mt(prim.loc[of, "lvl_trail_0.25A"], R),
                                      "fwd60_minus_drift": None},
                    "intraday_fresh": {"share": float((~of & ~pt).mean()), "E4_prereg": mt(prim.loc[~of & ~pt, "E4_prereg"], R),
                                       "at_level": mt(prim.loc[~of & ~pt, "lvl_trail_0.25A"], R)},
                    "intraday_pretested_overnight": {"share": float((~of & pt).mean()), "E4_prereg": mt(prim.loc[~of & pt, "E4_prereg"], R),
                                                     "at_level": mt(prim.loc[~of & pt, "lvl_trail_0.25A"], R)},
                    "by_entry_time": {str(b): {"share": float((mb == b).mean()), "E4_prereg": mt(prim.loc[mb == b, "E4_prereg"], R)} for b in mb.cat.categories},
                    "long": mt(prim.loc[prim["D"] > 0, "fwd_flat"], R), "short": mt(prim.loc[prim["D"] < 0, "fwd_flat"], R)}
    ctrl60 = prim["D"].to_numpy(float) * mu[np.clip(prim["minute"].to_numpy(int) - m0, 0, len(mu) - 1), H.index(60)]
    for nm, msk in (("long", prim["D"] > 0), ("short", prim["D"] < 0)):
        out["where"][f"{nm}_fwd60_minus_drift"] = mt((prim["fwd_60"].to_numpy(float) - ctrl60)[msk.to_numpy()], R)
    out["where"]["open_fill_gap"]["fwd60_minus_drift"] = mt((prim["fwd_60"].to_numpy(float) - ctrl60)[of.to_numpy()], R)
    # 5. the root-aware skips, on the base book (armed at the open, every session with levels)
    g0 = base["E4_prereg"].to_numpy(float)
    sk = {}
    for f_ in ("R2_delivery", "R3_index_roll"):
        k = base[f_].astype(bool).to_numpy()
        sk[f_] = diff(g0[k], g0[~k], R)
    # R2 as a profile: gross by business days to delivery
    bdd = base["bd_to_delivery"].to_numpy(float)
    sk["R2_profile_by_bd_to_delivery"] = {lab: mt(g0[(bdd >= lo) & (bdd <= hi)], R) for lab, lo, hi in
                                          (("0-5", 0, 5), ("6-10", 6, 10), ("11-15", 11, 15), ("16-20", 16, 20), ("21-30", 21, 30), ("31+", 31, 999))}
    # R3 placebo: every 6-business-day window of the month in the same roll months, window [b, b+5]
    bdm = base["bd_of_month"].to_numpy(int)
    mon = base["session"].str[5:7].astype(int).to_numpy()
    inm = np.isin(mon, list(B.ROLL_MONTHS[r]))
    wins = {}
    for b in range(1, 18):
        k = inm & (bdm >= b) & (bdm <= b + 5)
        wins[b] = float(g0[k].mean() - g0[~k].mean())
    act = wins[B.ROLL_BD[0]]
    sk["R3_window_placebo"] = {"declared_window_diff": act, "all_windows": wins,
                               "rank_from_most_negative": int(sum(v < act for v in wins.values()) + 1), "windows": len(wins)}
    sk["gross_by_bd_of_month"] = {int(b): mt(g0[bdm == b], R) for b in range(1, 24) if (bdm == b).sum() >= 20}
    yrs = base["session"].str[:4].to_numpy()
    k3 = base["R3_index_roll"].astype(bool).to_numpy()
    by = {y: (float(g0[k3 & (yrs == y)].mean()), float(g0[~k3 & (yrs == y)].mean())) for y in sorted(set(yrs)) if (k3 & (yrs == y)).sum() >= 10}
    sk["R3_by_year_removed_vs_kept"] = {"years": by, "years_removed_below_kept": int(sum(a < b for a, b in by.values())), "of": len(by)}
    if r in B.EIA:
        eia = base["eia_day"].astype(bool).to_numpy()
        pre = (base["minute"] < base["release_m"]).to_numpy()
        sk["R4_eia_vs_clock_control"] = {"eia_day_pre_release": mt(g0[eia & pre], R), "eia_day_post_release": mt(g0[eia & ~pre], R),
                                         "other_days_before_10:31": mt(g0[~eia & pre], R), "other_days_after_10:31": mt(g0[~eia & ~pre], R)}
    out["skips"] = sk
    out["_prim"] = prim
    return out


def cross_root(d676: dict) -> dict:
    j668 = json.loads((REPO / "data" / "stage0_d668_break_predictor.json").read_text(encoding="utf-8"))
    rows = {}
    for r in ("ES", "NQ", "YM", "RTY"):
        g1 = j668["roots"][r]["gate1"]
        rows[r] = {"source": f"D668 ({j668['roots'][r]['role']})", "gross": g1["gross_mean"], "n1_p50": g1["n1"]["p50"],
                   "n1_p95": g1["n1"]["p95"], "rank": g1["n1"]["rank"], "cost_bp": j668["roots"][r]["cost_bp_mean"]}
    for r in B.ROOTS:
        g1 = d676["roots"][r]["gate1"]
        rows[r] = {"source": "D676 (evidence)", "gross": g1["gross_mean"], "n1_p50": g1["n1"]["p50"], "n1_p95": g1["n1"]["p95"],
                   "rank": g1["n1"]["rank"], "cost_bp": d676["roots"][r]["four_groups"]["cost_bp_mean"]}
    for v in rows.values():
        v["excess_over_random"] = v["gross"] - v["n1_p50"]
        v["excess_over_cost"] = v["excess_over_random"] / v["cost_bp"]
    fis = {}
    for nm, rs in (("index_4", ("ES", "NQ", "YM", "RTY")), ("energy_metals_4", B.ROOTS), ("all_8", tuple(rows))):
        p = [max(1 - rows[r]["rank"], 1 / 1001) for r in rs]
        x2 = -2 * float(np.sum(np.log(p)))
        fis[nm] = {"chi2": x2, "df": 2 * len(p), "p": float(stats.chi2.sf(x2, 2 * len(p))),
                   "excess_positive": int(sum(rows[r]["excess_over_random"] > 0 for r in rs)), "of": len(rs)}
    return {"roots": rows, "fisher_on_N1_ranks": fis,
            "note": "ES and NQ were D668's development roots; N1 rank floors at 1/1001 for Fisher; descriptive, not a gate"}


def main() -> int:
    t0 = time.time()
    V = M.S.load_v2()
    R = V.R
    d676 = json.loads((REPO / "data" / "stage0_d676_root_aware_break.json").read_text(encoding="utf-8"))
    fr = frames()
    out = {"spec": "D677 DIAG of D676 (df1865cc + A1; result 18117d94)", "roots": {}}
    for r in B.ROOTS:
        d, bars, arm, cost = fr[r]
        res = root_diag(r, d, bars, arm, cost, R, d676)
        res.pop("_prim")
        out["roots"][r] = res
        print(f"{r}: done ({time.time() - t0:.0f}s)", flush=True)
    out["cross_root"] = cross_root(d676)
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.name} in {out['runtime_min']} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
