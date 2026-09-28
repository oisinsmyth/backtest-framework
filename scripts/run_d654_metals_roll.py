"""D654 -- sell the receiving month against the month after it at the end of the gold and silver roll.

    uv run python scripts/run_d654_metals_roll.py --selftest
    uv run python scripts/run_d654_metals_roll.py --power     # placements only, never the event window -> d654_power.json
    uv run python scripts/run_d654_metals_roll.py --run       # the one run -> data/d654_metals_roll.json

PRE-REGISTRATION: docs/decisions/D654-PRE-REG-selling-the-metals-roll-after-first-notice.md (b0d456b), committed before
this file existed.

Cycles are D653's, by importing its own `cycles()`; R and H are therefore identical by construction. Prices are the
settlement strip, filtered before 2024-01-01 and asserted. The trade never holds the expiring month, and every
cycle asserts that R's and H's own deadlines are at least ten business days after the exit.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import build_fut_oi_expiry as d653  # noqa: E402
from backtest_framework.validation import component_series as cs  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402

STRIP = d653._main_checkout(REPO) / "data" / "fixtures" / "fut_settle_strip.csv.gz"
if (REPO / "data" / "fixtures" / "fut_settle_strip.csv.gz").exists():
    STRIP = REPO / "data" / "fixtures" / "fut_settle_strip.csv.gz"
OUT = REPO / "data" / "d654_metals_roll.json"
POWER_OUT = REPO / "data" / "d654_power.json"

RESERVED_FROM, LAST = "2024-01-01", "2023-12-29"
PRIMARY, SECONDARY = ("GC", "SI"), ("HG", "6C")
ROOTS = PRIMARY + SECONDARY
MULT = {"GC": 100.0, "SI": 5000.0, "HG": 25000.0, "6C": 100000.0}
COST = {"GC": 82.77, "SI": 189.50, "HG": 64.02, "6C": 23.40}             # D654 s.1, base
COST_STRESS = {"GC": 153.53, "SI": 366.99, "HG": 116.04, "6C": 34.80}
SERIAL = {"GC": set("FHKNUX"), "SI": set("FGJMQVX"), "HG": set("FGJMQVX"), "6C": set("FGJKNQVX")}
ENTRY, EXIT = -1, 5
K_RANGE = [k for k in range(-60, 41) if abs(k) > 10]
BURN_IN, MIN_TRADED, FILTER_K = 8, 15, 2.0
NO_DELIVERY_BD = 10
MONTH_LETTER = "FGHJKMNQUVXZ"


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ------------------------------------------------------------------ data
def load_oi() -> pd.DataFrame:
    t = pd.read_csv(d653.FIX, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    t = t[t["root"].isin(ROOTS)]
    assert_none_at_or_after(t, "ref", RESERVED_FROM)
    return t


def resolve_rows(g: pd.DataFrame, exp) -> pd.Series:
    """Delivery (year*12+month) for EVERY row, from the code's first expiry on or after that row's own session.
    One resolution per code is wrong: codes recycle each decade (GCG1 is Feb 2011 and Feb 2021), so a code resolved
    once from its first appearance files the later decade's settlements under the old delivery."""
    out = pd.Series(np.nan, index=g.index)
    for code, idx in g.groupby("contract").groups.items():
        m = d653.RE_C.match(code)
        if not m or code not in exp:
            continue
        mon = d653.MONTH[m.group(2)]
        es = np.array(exp[code], dtype="datetime64[ns]")
        refs = g.loc[idx, "ref_ts"].to_numpy("datetime64[ns]")
        j = np.searchsorted(es, refs, side="left")
        ok = j < len(es)
        ey = pd.DatetimeIndex(es[np.clip(j, 0, len(es) - 1)])
        years = np.where(mon >= ey.month, ey.year, ey.year + 1)
        vals = np.where(ok, years * 12 + mon, np.nan)
        out.loc[idx] = vals
    return out


def load_settles(exp) -> dict:
    s = pd.read_csv(STRIP, usecols=["root", "contract", "ref", "settle"], encoding="utf-8")
    s = s[s["root"].isin(ROOTS)]
    s = filter_before(s, "ref", RESERVED_FROM)
    assert_none_at_or_after(s, "ref", RESERVED_FROM)
    s["ref_ts"] = pd.to_datetime(s["ref"])
    out = {}
    for root, g in s.groupby("root"):
        g = g.copy()
        g["dlv"] = resolve_rows(g, exp)
        g = g[g["dlv"].notna()]
        g["dlv"] = g["dlv"].astype(int)
        if g.duplicated(["dlv", "ref_ts"]).any():
            raise GateError(f"[RESOLVE] {root}: two settlements for one (delivery, session)")
        out[root] = g.pivot_table(index="ref_ts", columns="dlv", values="settle", aggfunc="last").sort_index()
    return out


def root_panels(t: pd.DataFrame, root: str, exp):
    g = t[t["root"] == root].copy()
    g["ref_ts"] = pd.to_datetime(g["ref"])
    res = {c: d653.resolve(c, g.loc[g["contract"] == c, "ref_ts"].iloc[0], exp) for c in g["contract"].unique()}
    g = g[g["contract"].map(lambda c: res.get(c) is not None)].copy()
    g["dlv"] = g["contract"].map(lambda c: res[c][1])
    sessions = np.array(sorted(g["ref_ts"].unique()))
    oi = g.pivot_table(index="ref_ts", columns="dlv", values="oi", aggfunc="last").reindex(sessions)
    cv = g.pivot_table(index="ref_ts", columns="dlv", values="cv", aggfunc="last").reindex(sessions)
    return sessions, oi, cv


def deadline_of(root: str, dlv: int, sessions: np.ndarray, exp_by_dlv: dict) -> pd.Timestamp | None:
    if root in d653.LTD_ROOTS:
        return exp_by_dlv.get(dlv)
    y, m = divmod(dlv - 1, 12)
    m += 1
    py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
    lo, hi = pd.Timestamp(py, pm, 1), pd.Timestamp(y, m, 1)
    s = sessions[(sessions >= lo) & (sessions < hi)]
    if len(s):
        return s[-1]
    # beyond the fixture: the last business day of the prior month, on the plain weekday calendar
    return pd.bdate_range(lo, hi - pd.Timedelta(days=1))[-1]


def expiry_by_dlv(root: str, exp) -> dict:
    out = {}
    for code, es in exp.items():
        if not code.startswith(root) or not d653.RE_C.match(code) or d653.RE_C.match(code).group(1) != root:
            continue
        mon = d653.MONTH[d653.RE_C.match(code).group(2)]
        for e in es:
            y = e.year if mon >= e.month else e.year + 1
            out[y * 12 + mon] = e
    return out


# ------------------------------------------------------------------ the trade
def gross_bp(settle: pd.DataFrame, R: int, H: int, t0, t1, mult: float):
    try:
        r0, r1, h0, h1 = settle.at[t0, R], settle.at[t1, R], settle.at[t0, H], settle.at[t1, H]
    except KeyError:
        return None
    if not all(np.isfinite([r0, r1, h0, h1])) or r0 <= 0:
        return None
    usd = -(r1 - r0) * mult + (h1 - h0) * mult
    return usd, usd / (r0 * mult) * 1e4, r0 * mult


def far_from_delivery(dl_R, dl_H, t_exit) -> bool:
    return all(np.busday_count(t_exit.date(), d.date()) >= NO_DELIVERY_BD for d in (dl_R, dl_H))


def pressure_x(oi, cv, sessions, i, dlv, R) -> float:
    """D654 s.2: (expiring decline d=-30..-2) x (roll share, clipped) / R's cleared volume over d=-6..-2."""
    e30, e2 = oi.iloc[i - 30][dlv], oi.iloc[i - 2][dlv]
    r30, r2 = oi.iloc[i - 30][R], oi.iloc[i - 2][R]
    vols = cv.iloc[i - 6:i - 1][R].fillna(0).to_numpy(float)
    decl = (e30 or 0) - (e2 or 0)
    if not (np.isfinite(decl) and decl > 0 and vols.sum() > 0):
        return float("nan")
    roll = min(max(((r2 if np.isfinite(r2) else 0) - (r30 if np.isfinite(r30) else 0)) / decl, 0.0), 1.0)
    return float(decl * roll / vols.sum())


def build_cycles(root, t, exp, settles, control: bool = False) -> pd.DataFrame:
    sessions, oi, cv = root_panels(t, root, exp)
    pos = {s: i for i, s in enumerate(sessions)}
    ebd = expiry_by_dlv(root, exp)
    settle = settles[root]
    if not control:
        cy = d653.cycles(t, root, exp, root in d653.LTD_ROOTS, set(), root in d653.index_roots())
        base = [(int(r.dlv), pd.Timestamp(r.deadline), int(r.recv), None if pd.isna(r.hedge) else int(r.hedge))
                for r in cy.itertuples()]
    else:
        base = []
        for y in range(2015, 2024):
            for mi, letter in enumerate(MONTH_LETTER):
                if letter not in SERIAL[root]:
                    continue
                dlv = y * 12 + mi + 1
                if root in d653.LTD_ROOTS:                        # 6C: two business days before the 3rd Wednesday
                    first = pd.Timestamp(y, mi + 1, 1)
                    wed = pd.date_range(first, first + pd.Timedelta(days=27), freq="W-WED")[2]
                    prior = sessions[sessions < wed]
                    D = prior[-2] if len(prior) >= 2 else None
                else:
                    D = deadline_of(root, dlv, sessions, ebd)
                if D is None or D not in pos:
                    continue
                i = pos[D]
                if i - 20 < 0:
                    continue
                at20 = oi.iloc[i - 20]
                later = at20[[k for k in at20.index if k > dlv]].dropna()
                if later.empty:
                    continue
                R = int(later.idxmax())
                later2 = at20[[k for k in at20.index if k > R]].dropna()
                base.append((dlv, D, R, int(later2.idxmax()) if not later2.empty else None))
    rows = []
    for dlv, D, R, H in base:
        if H is None or D not in pos:
            continue
        i = pos[D]
        if i + ENTRY < 0 or i + EXIT >= len(sessions) or i - 30 < 0:
            continue
        t0, t1 = sessions[i + ENTRY], sessions[i + EXIT]
        dl_R, dl_H = deadline_of(root, R, sessions, ebd), deadline_of(root, H, sessions, ebd)
        if dl_R is None or dl_H is None:
            continue
        if not far_from_delivery(dl_R, dl_H, t1):
            raise GateError(f"[DELIVERY] {root} {dlv}: R or H deadline within {NO_DELIVERY_BD} business days of the exit")
        g = gross_bp(settle, R, H, t0, t1, MULT[root])
        if g is None:
            continue
        usd, bp, notional = g
        row = {"root": root, "dlv": dlv, "deadline": D, "entry": t0, "exit": t1, "R": R, "H": H,
               "gross_usd": usd, "gross_bp": bp, "notional": notional, "i": i,
               "cost_bp": COST[root] / notional * 1e4, "cost_stress_bp": COST_STRESS[root] / notional * 1e4}
        if not control:
            m = gross_bp(settle, R, H, sessions[i - 10], t0, MULT[root])
            row["mech_bp"] = -m[1] if m else np.nan          # the push on R - H during the drain (positive = R richer)
            for xd in (1, 3, 10):
                if i + xd < len(sessions) and far_from_delivery(dl_R, dl_H, sessions[i + xd]):
                    gx = gross_bp(settle, R, H, t0, sessions[i + xd], MULT[root])
                    row[f"gross_bp_exit{xd}"] = gx[1] if gx else np.nan
            row["x"] = pressure_x(oi, cv, sessions, i, dlv, R)
        rows.append(row)
    df = pd.DataFrame(rows)
    if len(df):
        df["net_bp"] = df["gross_bp"] - df["cost_bp"]
        df["net_usd"] = df["gross_usd"] - COST[root]
    return df, sessions, ebd


def placements(root, cy, sessions, ebd, settle):
    """k -> list of (cycle index, gross bp) for every allowed shift; never k in [-10, 10]."""
    out = {}
    for k in K_RANGE:
        vals = []
        for j, r in enumerate(cy.itertuples()):
            a, b = r.i + ENTRY + k, r.i + EXIT + k
            if a < 0 or b >= len(sessions):
                continue
            t0, t1 = sessions[a], sessions[b]
            dl_R, dl_H = deadline_of(root, r.R, sessions, ebd), deadline_of(root, r.H, sessions, ebd)
            if not far_from_delivery(dl_R, dl_H, t1):
                continue
            g = gross_bp(settle, r.R, r.H, t0, t1, MULT[root])
            if g is not None:
                vals.append((j, g[1], t0.year))
        out[k] = vals
    return out


def filter_rule(cy: pd.DataFrame) -> pd.DataFrame:
    """b from earlier cycles only (exited before this entry), same root; trade iff b > 0 and b x >= 2 x cost."""
    cy = cy.sort_values("entry").reset_index(drop=True)
    bs, trade = [], []
    for j, r in cy.iterrows():
        prior = cy[(cy["exit"] < r["entry"]) & cy["x"].notna()]
        if len(prior) < BURN_IN or not np.isfinite(r["x"]):
            bs.append(np.nan)
            trade.append(False)
            continue
        xx, yy = prior["x"].to_numpy(float), prior["gross_bp"].to_numpy(float)
        b = float((xx * yy).sum() / (xx * xx).sum()) if (xx * xx).sum() > 0 else np.nan
        bs.append(b)
        trade.append(bool(np.isfinite(b) and b > 0 and b * r["x"] >= FILTER_K * r["cost_bp"]))
    cy["b"], cy["trade"] = bs, trade
    return cy


# ------------------------------------------------------------------ statistics
def nw_t(x: np.ndarray, lags: int = 1) -> float:
    e = x - x.mean()
    n = len(x)
    s = float(e @ e) / n
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * float(e[L:] @ e[:-L]) / n
    return float(x.mean() / math.sqrt(s / n)) if s > 0 else float("nan")


def dist(x: np.ndarray) -> dict:
    x = np.sort(np.asarray(x, float))
    n = len(x)
    wins, losses = x[x > 0], x[x < 0]
    return {"n": n, "mean": float(x.mean()), "median": float(np.median(x)), "hit": float((x > 0).mean()),
            "payoff": float(wins.mean() / -losses.mean()) if len(wins) and len(losses) else None,
            "skew": float(pd.Series(x).skew()), "kurtosis": float(pd.Series(x).kurt()),
            "mean_ex_top": float(x[:-1].mean()), "mean_ex_bottom": float(x[1:].mean()),
            "mean_trimmed": float(x[1:-1].mean()), "t_nw": nw_t(x)}


def daily_book(cys: list[pd.DataFrame], settles, cost_col: str | None) -> pd.Series:
    days = pd.DatetimeIndex(sorted(set().union(*[set(settles[r].index) for r in PRIMARY])))
    days = days[(days >= pd.Timestamp("2016-01-04")) & (days <= pd.Timestamp(LAST))]
    pnl = pd.Series(0.0, index=days)
    for cy in cys:
        for r in cy.itertuples():
            s = settles[r.root][[r.R, r.H]].loc[r.entry:r.exit].ffill()
            spread = (-s[r.R] + s[r.H]) * MULT[r.root]
            d = spread.diff().dropna()
            pnl.loc[d.index.intersection(pnl.index)] += d.reindex(d.index.intersection(pnl.index)).to_numpy()
            if cost_col:
                if r.exit in pnl.index:
                    pnl.loc[r.exit] -= COST[r.root]
    return pnl


def perf(pnl: pd.Series) -> dict:
    x = pnl.to_numpy(float)
    cum = np.cumsum(x)
    dd = float((cum - np.maximum.accumulate(cum)).min())
    return {"sharpe": cs.sharpe(x), "sortino": cs.sortino(x), "ann_usd": float(x.mean() * 252),
            "vol_ann_usd": float(x.std(ddof=1) * math.sqrt(252)), "max_dd_usd": dd,
            "exposure": float((x != 0).mean()), "total_usd": float(x.sum())}


# ------------------------------------------------------------------ modes
def assemble():
    exp = d653.load_expiries()
    t = load_oi()
    settles = load_settles(exp)
    return exp, t, settles


def power() -> int:
    exp, t, settles = assemble()
    res = {"reads": "placement offsets |k| > 10 only; the event window's P&L is never computed here"}
    allv, notional = [], []
    for root in PRIMARY:
        cy, sessions, ebd = build_cycles(root, t, exp, settles)
        pl = placements(root, cy, sessions, ebd, settles[root])
        v = [bp for k in K_RANGE for (_, bp, _) in pl[k]]
        allv += v
        res[root] = {"cycles": int(len(cy)), "placement_obs": len(v), "sd_bp": float(np.std(v, ddof=1))}
        notional.append(float(cy["notional"].mean()))
    n = res["GC"]["cycles"] + res["SI"]["cycles"]
    sd = float(np.std(allv, ddof=1))
    cost_bp = float(np.mean([COST[r] / nm * 1e4 for r, nm in zip(PRIMARY, notional)]))
    res["pooled"] = {"cycles": n, "sd_bp": sd, "mde_t2_bp": 2 * sd / math.sqrt(n), "mean_base_cost_bp": cost_bp}
    fw = {"2024-01..2025-02": 13, "with the vault to 2026-09": 13 + 16}
    res["forward"] = {name: {"cycles": m, "mde_t2_bp": 2 * sd / math.sqrt(m),
                             "power_if_gross_equals_cost": d653_norm(cost_bp / (sd / math.sqrt(m)) - 2.0)}
                      for name, m in fw.items()}
    POWER_OUT.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    P(json.dumps(res, indent=1))
    return 0


def d653_norm(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def run() -> int:
    exp, t, settles = assemble()
    cys, ctl, nulls, out = {}, {}, {}, {"decision_record": "D654", "last_session": LAST, "cells": {}}
    for root in ROOTS:
        cy, sessions, ebd = build_cycles(root, t, exp, settles)
        cy = filter_rule(cy)
        cys[root] = cy
        c, _, _ = build_cycles(root, t, exp, settles, control=True)
        ctl[root] = c
        nulls[root] = (placements(root, cy.sort_values("i").reset_index(drop=True), sessions, ebd, settles[root]))

    def cell(roots):
        cy = pd.concat([cys[r] for r in roots], ignore_index=True).sort_values("entry")
        cc = pd.concat([ctl[r] for r in roots if len(ctl[r])], ignore_index=True)
        g, n = cy["gross_bp"].to_numpy(float), cy["net_bp"].to_numpy(float)
        # placement null of the pooled mean gross, and of the positive-year count
        means, years = [], []
        for k in K_RANGE:
            vals = [(bp, yr) for r in roots for (_, bp, yr) in nulls[r][k]]
            if len(vals) < 0.5 * len(cy):
                continue
            arr = np.array([v[0] for v in vals])
            means.append(arr.mean())
            yd = pd.DataFrame(vals, columns=["bp", "yr"]).groupby("yr")["bp"].mean()
            years.append(int((yd > 0).sum()))
        means, years = np.array(means), np.array(years)
        yr_obs = cy.groupby(cy["deadline"].dt.year)["gross_bp"].mean()
        cg = cc["gross_bp"].to_numpy(float) if len(cc) else np.array([np.nan])
        welch = (g.mean() - cg.mean()) / math.sqrt(g.var(ddof=1) / len(g) + cg.var(ddof=1) / len(cg)) if len(cc) > 2 else float("nan")
        f = cy[cy["trade"]]
        rec = {
            "cycles": int(len(cy)), "gross": dist(g), "net": dist(n),
            "net_stress_mean_bp": float((cy["gross_bp"] - cy["cost_stress_bp"]).mean()),
            "mean_cost_bp": float(cy["cost_bp"].mean()),
            "gross_usd_mean": float(cy["gross_usd"].mean()), "net_usd_mean": float(cy["net_usd"].mean()),
            "breakeven_round_trip_usd": float(cy["gross_usd"].mean()),
            "placement": {"offsets": int(len(means)), "p05": float(np.percentile(means, 5)),
                          "p50": float(np.percentile(means, 50)), "p95": float(np.percentile(means, 95)),
                          "rank": float((means < g.mean()).mean()),
                          "years_positive_p95": float(np.percentile(years, 95))},
            "years_positive": int((yr_obs > 0).sum()), "years": {int(k): float(v) for k, v in yr_obs.items()},
            "control": {"n": int(len(cc)), "gross_mean_bp": float(np.nanmean(cg)),
                        "gross_t": nw_t(cg) if len(cc) > 2 else None, "welch_t_primary_minus_control": welch},
            "mechanism_drain_push_bp": {"mean": float(cy["mech_bp"].mean()), "t": nw_t(cy["mech_bp"].dropna().to_numpy(float)),
                                        "by_root": {r: float(cys[r]["mech_bp"].mean()) for r in roots}},
            "exits": {f"+{xd}": float(cy[f"gross_bp_exit{xd}"].mean()) for xd in (1, 3, 10) if f"gross_bp_exit{xd}" in cy},
            "by_root": {r: {"cycles": int(len(cys[r])), "gross_mean_bp": float(cys[r]["gross_bp"].mean()),
                            "net_mean_bp": float(cys[r]["net_bp"].mean()), "cost_bp": float(cys[r]["cost_bp"].mean())}
                        for r in roots},
            "largest": [{"root": r.root, "deadline": str(r.deadline.date()), "gross_bp": round(r.gross_bp, 2),
                         "gross_usd": round(r.gross_usd, 1)}
                        for r in cy.reindex(cy["gross_bp"].abs().sort_values(ascending=False).index[:5]).itertuples()],
            "filter": {"eligible_after_burn_in": int(cy["b"].notna().sum()), "traded": int(len(f)),
                       "traded_share": float(len(f) / max(cy["b"].notna().sum(), 1)),
                       "net": dist(f["net_bp"].to_numpy(float)) if len(f) >= 2 else None,
                       "by_root": {r: int(cys[r]["trade"].sum()) for r in roots}},
        }
        rec["bars"] = {
            "B1_net_t_ge_2": bool(rec["net"]["mean"] > 0 and rec["net"]["t_nw"] >= 2.0),
            "B2_above_placement_p95": bool(g.mean() > rec["placement"]["p95"]),
            "B3_above_control_welch_t_ge_2": bool(np.isfinite(welch) and welch >= 2.0),
            "B4_years_at_null_p95": bool(rec["years_positive"] >= rec["placement"]["years_positive_p95"]),
            "B5_median_and_trim_positive": bool(rec["gross"]["median"] > 0 and rec["gross"]["mean_trimmed"] > 0),
        }
        fn = rec["filter"]["net"]
        rec["filter"]["passes"] = bool(fn and len(f) >= MIN_TRADED and fn["mean"] > 0 and fn["t_nw"] >= 2.0
                                       and fn["mean"] > rec["net"]["mean"])
        rec["filter"]["verdict"] = ("UNRESOLVED (fewer than 15 traded)" if len(f) < MIN_TRADED else
                                    ("PASS" if rec["filter"]["passes"] else "FAIL"))
        return rec, cy

    prim, cy_p = cell(PRIMARY)
    out["cells"]["primary_GC_SI"] = prim
    for r in SECONDARY:
        out["cells"][r] = cell((r,))[0]
    b = prim["bars"]
    if all(b.values()):
        route = "all of B1-B5: the unfiltered construction is a personal-book candidate"
    elif b["B2_above_placement_p95"] and b["B3_above_control_welch_t_ge_2"] and b["B5_median_and_trim_positive"]:
        route = ("the premium is real, the average trade does not clear cost: the filtered book decides -> "
                 + prim["filter"]["verdict"])
    elif not (b["B2_above_placement_p95"] and b["B3_above_control_welch_t_ge_2"]):
        route = "B2 or B3 fails: no reverting premium; recommend closing the delivery line"
    else:
        route = "B2 and B3 pass but B4 or B5 fails: reported, no candidate"
    out["route"] = route
    gross_book = daily_book([cys[r] for r in PRIMARY], settles, None)
    net_book = daily_book([cys[r] for r in PRIMARY], settles, "net")
    out["book_GC_SI_one_spread"] = {"gross": perf(gross_book), "net": perf(net_book)}
    series = cs.DailyPnL(name="d654_metals_roll_GC_SI", dates=tuple(d.strftime("%Y-%m-%d") for d in net_book.index),
                         usd=tuple(float(v) for v in net_book.to_numpy()), size_label="one GC and one SI calendar spread",
                         cost_line_usd_rt=float(np.mean([COST[r] for r in PRIMARY])),
                         window=(str(net_book.index[0].date()), LAST), spec="D654",
                         source_sha256=cs.sha256_of(STRIP))
    line = cs.component_line(series)
    out["component_line"] = {k: line[k] for k in ("net_sharpe", "net_sortino", "exposure", "hit_active", "skew",
                                                  "mean_usd", "sd_usd", "worst_day_usd")}
    out["component_line"]["gross_sharpe"] = out["book_GC_SI_one_spread"]["gross"]["sharpe"]
    out["component_line"]["gross_sortino"] = out["book_GC_SI_one_spread"]["gross"]["sortino"]
    out["component_line"]["rho_with_macd_arm"] = "not computable: the arm's daily series is not on disk (D590's gap)"
    out["predictions"] = {
        "1_mechanism_positive_both": all(v > 0 for v in prim["mechanism_drain_push_bp"]["by_root"].values()),
        "2_gross_small_positive": bool(0 < prim["gross"]["mean"] < 10),
        "3_B1_fails": not b["B1_net_t_ge_2"],
        "4_control_inside_null": bool(prim["placement"]["p05"] <= prim["control"]["gross_mean_bp"] <= prim["placement"]["p95"]),
        "5_filter_trades_under_half_and_few_SI": bool(prim["filter"]["traded_share"] < 0.5
                                                        and prim["filter"]["by_root"]["SI"] <= prim["filter"]["by_root"]["GC"]),
        "6_gold_carries_it": bool(prim["by_root"]["GC"]["gross_mean_bp"] > prim["by_root"]["SI"]["gross_mean_bp"]),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    brief = {k: v for k, v in prim.items() if k not in ("years",)}
    P(json.dumps({"primary": brief, "route": route, "book": out["book_GC_SI_one_spread"],
                  "component_line": out["component_line"], "predictions": out["predictions"]}, indent=1, default=str))
    for r in SECONDARY:
        s = out["cells"][r]
        P(f"{r}: cycles {s['cycles']} gross {s['gross']['mean']:+.2f} bp net {s['net']['mean']:+.2f} (t {s['net']['t_nw']:+.2f}) "
          f"placement rank {s['placement']['rank']:.2f} control {s['control']['gross_mean_bp']:+.2f} bars {s['bars']} "
          f"filter {s['filter']['verdict']}")
    return 0


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    n = 0

    def check(label, cond):
        nonlocal n
        if not cond:
            raise AssertionError(f"FAILED: {label}")
        n += 1
        P(f"  ok  {label}")

    def must_raise(label, fn):
        nonlocal n
        try:
            fn()
        except (GateError, AssertionError):
            n += 1
            P(f"  ok  raises: {label}")
            return
        raise AssertionError(f"did NOT raise: {label}")

    exp = d653.load_expiries()
    t = load_oi()
    d = json.loads(d653.OUT.read_text(encoding="utf-8"))["roots"]
    for root in PRIMARY:
        cy = d653.cycles(t, root, exp, False, set(), True)
        check(f"{root}: D653's cycles() gives D653's count ({len(cy)})", len(cy) == d[root]["summary"]["cycles"])

    settle = pd.DataFrame({1: [100.0, 99.0], 2: [101.0, 101.0]}, index=pd.to_datetime(["2019-01-02", "2019-01-09"]))
    usd, bp, _ = gross_bp(settle, 1, 2, settle.index[0], settle.index[1], 100.0)
    check(f"R falling 1.00 against a flat H pays the short-R/long-H position +$100 ({usd:+.0f})", abs(usd - 100.0) < 1e-9 and bp > 0)
    settle2 = pd.DataFrame({1: [100.0, 100.0], 2: [101.0, 102.0]}, index=settle.index)
    check("H rising against a flat R also pays", gross_bp(settle2, 1, 2, settle.index[0], settle.index[1], 100.0)[0] > 0)

    check("an R deadline 5 business days after the exit is refused",
          not far_from_delivery(pd.Timestamp("2019-01-16"), pd.Timestamp("2019-06-28"), pd.Timestamp("2019-01-09")))
    check("R and H deadlines months away are allowed",
          far_from_delivery(pd.Timestamp("2019-03-29"), pd.Timestamp("2019-05-31"), pd.Timestamp("2019-01-09")))

    cy = pd.DataFrame({"entry": pd.date_range("2016-01-01", periods=12, freq="60D"),
                       "exit": pd.date_range("2016-01-10", periods=12, freq="60D"),
                       "x": np.linspace(0.1, 0.5, 12), "gross_bp": np.linspace(1, 12, 12), "cost_bp": 1.0})
    f = filter_rule(cy.copy())
    check("the first eight cycles are burn-in and never traded", not f["trade"].iloc[:8].any() and f["b"].iloc[:8].isna().all())
    cy2 = cy.copy()
    cy2.loc[11, "gross_bp"] = 1e6                               # a future outcome changes nothing that came before it
    f2 = filter_rule(cy2)
    check("b uses only cycles that exited before the entry (a changed LAST outcome leaves every b unchanged)",
          np.allclose(f["b"].to_numpy(float), f2["b"].to_numpy(float), equal_nan=True))
    check("the placement offsets exclude |k| <= 10", min(abs(k) for k in K_RANGE) == 11)
    must_raise("a 2024 settlement past the loader",
               lambda: assert_none_at_or_after(pd.DataFrame({"ref": ["2024-01-02"]}), "ref", RESERVED_FROM))
    P(f"selftest: {n} checks")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--power", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else (power() if a.power else run())


if __name__ == "__main__":
    sys.exit(main())
