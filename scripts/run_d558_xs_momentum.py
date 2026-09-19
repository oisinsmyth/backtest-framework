"""D558 -- cross-sectional 12-1 momentum AS PUBLISHED (Miffre & Rallis 2007; Fuertes, Miffre & Rallis
2010; Asness, Moskowitz & Pedersen 2013) on the 17 commodity roots of the breadth fixture.

Spec committed in 60aa4fc BEFORE this file (R8). Primary window 2016-01-04..2023-12-29; the long
window 2011-01-03..2023-12-29 is a declared diagnostic; the 2024+ slice is RESERVED AND NOT READ.
Nothing admitted (R15).

    python scripts/run_d558_xs_momentum.py --selftest
    python scripts/run_d558_xs_momentum.py --run        # -> data/d558_xs_momentum.json

Everything not specific to the sort is imported from run_d555_tsmom_replication.py (through
run_d556_carry_timing.py, one instance of each): the return grids, the EW volatility, the month-end
sums, the holds, the book return, the dollar book, the three audits, the enumerated rotation null and
its purge; positions_from_signs and min_size from D556. At each month-end the 17 roots are ranked by
the sum of daily log returns over the 11 calendar months ending the month BEFORE the month-end
(tot12 - tot1, the 1-month cell read without its count floor), the top ceil(n/3) are long, the
bottom ceil(n/3) short, held one month. Three cells: EW/published (primary), vol-scaled/published,
dollar at minimum size (net). Four audits, each proven to raise on a deliberate break.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m


R56 = _load("d556", "run_d556_carry_timing.py")
R55 = R56.R55

OUT = REPO / "data" / "d558_xs_momentum.json"
D555_JSON = REPO / "data" / "d555_tsmom_replication.json"
SPEC = "60aa4fc"
PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
UNIVERSE = list(R55.SECTOR["CM"])          # the 17 commodity roots, ranked together
MIN_ELIGIBLE = 9                           # fewer eligible roots at a month-end -> flat month
LOOKBACK, SKIP = 12, 1                     # 12-1: the 12 calendar months ending at m, less m's own month
CELL_KEYS = [("ew", "published"), ("volscaled", "published"), ("dollar", "dollar")]
CELL_NAMES = {("ew", "published"): "EW/published", ("volscaled", "published"): "vol-scaled/published", ("dollar", "dollar"): "dollar"}
PRIMARY_CELL = ("ew", "published")
POINT_RANGE_NET = (0.15, 0.35)             # the deposit's expected net Sharpe
POINT_RANGE_GROSS = (0.17, 0.37)           # judged gross: net range + the modelled cost (< 0.02)
REQUIRED_OUTPUTS = ["spec", "commit", "fixture_sha256", "windows", "universe", "eligibility", "cells", "primary", "null_n1",
                    "null_n2", "root_month", "concentration", "per_root", "per_era", "per_year", "comparability",
                    "dollar_book", "component_line", "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# the signal and the sort
# --------------------------------------------------------------------------------------------
def month_sum_no_floor(rlog, live, days, me):
    """The sum of the live finite daily log returns over the month-end's own calendar month, read as
    the difference of the SAME cumulative sums signal_at_month_ends uses, over the same
    _window_start boundary, with no count floor. Asserted bit-identical to signal_at_month_ends(L=1)
    wherever that one is finite."""
    n, T = rlog.shape
    fin = np.isfinite(rlog) & live
    r0 = np.where(fin, rlog, 0.0)
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(r0, axis=1)], axis=1)
    out = np.full((n, len(me)), np.nan)
    for k, m_ix in enumerate(me):
        a = R55._window_start(days, m_ix, SKIP)
        out[:, k] = cs[:, m_ix + 1] - cs[:, a]
    return out


def momentum_at_month_ends(g, me):
    """mom[i, k] = tot12 - tot1 where tot12 is finite (>= 240 returns in the 12 calendar months ending at
    the month-end and the root live there); NaN otherwise. Returns (mom, n_voided_by_the_1m_floor)."""
    rlog, live, days = g["rlog"], g["live"], g["days"]
    _, tot12 = R55.signal_at_month_ends(rlog, live, days, me, LOOKBACK)
    _, tot1_floor = R55.signal_at_month_ends(rlog, live, days, me, SKIP)
    tot1 = month_sum_no_floor(rlog, live, days, me)
    fin1 = np.isfinite(tot1_floor)
    if not np.array_equal(tot1[fin1], tot1_floor[fin1]):
        raise AssertionError("the no-floor 1-month sum is not bit-identical to signal_at_month_ends(L=1) where the latter is finite")
    mom = np.where(np.isfinite(tot12), tot12 - tot1, np.nan)
    voided = int((np.isfinite(tot12) & ~fin1).sum())
    return mom, voided, int(fin1.sum())


def rank_membership(mom, roots):
    """Implementation A. sign[i, k] in {+1, 0, -1}: long the top ceil(n_el/3) by momentum descending,
    short the bottom ceil(n_el/3), ties by root symbol alphabetically; flat month under MIN_ELIGIBLE.
    Returns (sign, per-month-end diagnostics)."""
    n, K = mom.shape
    sign = np.zeros((n, K), dtype=int)
    diag = []
    for k in range(K):
        el = np.flatnonzero(np.isfinite(mom[:, k])); n_el = int(len(el))
        if n_el < MIN_ELIGIBLE:
            diag.append({"n_eligible": n_el, "n_leg": 0, "flat": True, "boundary_tie": False})
            continue
        n_leg = int(math.ceil(n_el / 3))
        order = sorted(el.tolist(), key=lambda i: (-mom[i, k], roots[i]))
        longs, shorts = order[:n_leg], order[n_el - n_leg:]
        tie = bool(mom[order[n_leg - 1], k] == mom[order[n_leg], k] or mom[order[n_el - n_leg - 1], k] == mom[order[n_el - n_leg], k])
        sign[longs, k] = 1; sign[shorts, k] = -1
        diag.append({"n_eligible": n_el, "n_leg": n_leg, "flat": False, "boundary_tie": tie})
    return sign, diag


def membership_pandas(rlog, live, days, roots, me):
    """Implementation B (pandas), never calling rank_membership or month_sum_no_floor: per root resample
    the live log returns to calendar months, 12-month rolling sum minus the month's own sum, 12-month
    rolling count >= 240 and live at the month-end for eligibility; then per month-end sort the eligible
    roots on (momentum descending, symbol ascending) with DataFrame.sort_values."""
    idx = pd.to_datetime(days)
    n, K = len(roots), len(me)
    need = R55.MIN_RET_IN_WINDOW
    me_periods = [pd.Timestamp(str(days[m])).to_period("M") for m in me]
    mom = np.full((n, K), np.nan)
    for i in range(n):
        s = pd.Series(np.where(live[i], rlog[i], np.nan), index=idx)
        ms = s.resample("ME").sum(min_count=1).fillna(0.0)
        mc = s.resample("ME").count()
        rs = ms.rolling(LOOKBACK, min_periods=1).sum(); rc = mc.rolling(LOOKBACK, min_periods=1).sum()
        rs.index = rs.index.to_period("M"); rc.index = rc.index.to_period("M"); ms.index = ms.index.to_period("M")
        for k, p in enumerate(me_periods):
            if p in rs.index and rc[p] >= need and live[i, me[k]]:
                mom[i, k] = rs[p] - ms[p]
    sign = np.zeros((n, K), dtype=int)
    frame = pd.DataFrame(mom.T, columns=roots)
    for k in range(K):
        row = frame.iloc[k].dropna()
        if len(row) < MIN_ELIGIBLE:
            continue
        n_leg = int(math.ceil(len(row) / 3))
        srt = row.rename("mom").rename_axis("root").reset_index().sort_values(["mom", "root"], ascending=[False, True])
        for r in srt["root"].iloc[:n_leg]:
            sign[roots.index(r), k] = 1
        for r in srt["root"].iloc[len(row) - n_leg:]:
            sign[roots.index(r), k] = -1
    return sign


def audit_leg_membership(sign_runner, sign_pandas):
    """The runner's long/short/flat membership at every month-end must equal the independent pandas
    path's, cell for cell. Returns the number of positioned cells."""
    if sign_runner.shape != sign_pandas.shape:
        raise AssertionError("LEG AUDIT: membership grids differ in shape")
    bad = np.argwhere(sign_runner != sign_pandas)
    if len(bad):
        i, k = bad[0]
        raise AssertionError(f"LEG AUDIT: {len(bad)} membership cells differ; first at root {i} month-end {k}: "
                             f"runner {sign_runner[i, k]:+d}, pandas {sign_pandas[i, k]:+d}")
    return int((sign_runner != 0).sum())


def swap_one_pair(sign_me):
    """The deliberate break for the leg audit: one long and one short exchanged at one month-end."""
    bad = sign_me.copy()
    for k in range(sign_me.shape[1]):
        L = np.flatnonzero(sign_me[:, k] == 1); S = np.flatnonzero(sign_me[:, k] == -1)
        if L.size and S.size:
            bad[L[0], k], bad[S[0], k] = -1, 1
            return bad, k
    raise AssertionError("no month-end with both legs to swap")


def unlagged_grid(sign_me, me, span):
    """Membership placed on the sessions up to and INCLUDING the month-end it was read on."""
    n, T = span.shape
    unl = np.zeros((n, T))
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = sign_me[:, k][:, None]
    return np.where(span, unl, 0.0)


# --------------------------------------------------------------------------------------------
# reporting helpers
# --------------------------------------------------------------------------------------------
def _f(v):
    return float(v) if (v is not None and np.isfinite(v)) else None


def dist_stats(v):
    v = np.asarray(v, dtype=float); n = int(len(v))
    if n < 10:
        return {"n": n}
    srt = np.sort(v); c = max(1, int(round(0.01 * n)))
    wins, losses = v[v > 0], v[v < 0]
    return {"n": n, "mean": float(v.mean()), "median": float(np.median(v)), "ex_top_1pct": float(srt[:-c].mean()),
            "ex_bottom_1pct": float(srt[c:].mean()), "trimmed_1pct_both": float(srt[c:-c].mean()),
            "win_rate": float((v > 0).mean()), "payoff": _f(wins.mean() / (-losses.mean())) if wins.size and losses.size else None,
            "skew": float(pd.Series(v).skew()), "kurt": float(pd.Series(v).kurt()), "trim_count_each_tail": c}


def root_month_contributions(pos, rsimple, sign_me, me, w, roots):
    """Per (root, month-end) P&L contribution in book units: book weight x simple return summed over the
    holding month's sessions inside the window. Sums to the book's total over the window."""
    n, T = pos.shape
    cnt = (pos != 0.0).sum(0)
    wgt = pos / np.where(cnt > 0, cnt, 1.0)[None, :]
    contrib = wgt * rsimple
    rows = []
    for k, m_ix in enumerate(me):
        hi = me[k + 1] if k + 1 < len(me) else T - 1
        sl = slice(m_ix + 1, hi + 1)
        wsl = w[sl]
        if not wsl.any():
            continue
        for i in range(n):
            if sign_me[i, k] != 0:
                rows.append((roots[i], k, int(sign_me[i, k]), float(contrib[i, sl][wsl].sum())))
    return rows


def monthly(x, days, w):
    s = pd.Series(x[w], index=pd.to_datetime(days[w]))
    return (1.0 + s).groupby(s.index.to_period("M")).prod() - 1.0


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D558 -- cross-sectional 12-1 momentum as published, {len(UNIVERSE)} commodity roots\n"
        f"      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    df_all = R55.load_fixture()
    if (df_all["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present after filtering")
    last_session_read = str(df_all["day"].max())
    live_start = R55.live_start_by_rule(df_all)          # on the full 36-root frame (its declared exceptions live there)
    days36 = np.array(sorted(df_all["day"].unique()))
    df = df_all[df_all["root"].isin(UNIVERSE)]
    g = R55.build_grids(df, live_start)
    roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    if sorted(roots) != sorted(UNIVERSE) or any(live_start[r] != 2011 for r in roots):
        raise AssertionError("universe or live start is not the declared one")
    absent = sorted(set(days36) - set(days))
    log(f"  grid: {n} roots x {T} sessions {days[0]}..{days[-1]}; sessions in the 36-root frame absent here: {absent}")
    me = R55.month_ends(days)
    me36 = set(days36[R55.month_ends(days36)])
    if set(days[me]) != me36:
        raise AssertionError("month-end sessions differ from the 36-root frame's")
    sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]

    # the signal and the sort
    mom, voided_1m, tot1_ident_cells = momentum_at_month_ends(g, me)
    sign_me, diag = rank_membership(mom, roots)
    sign_pd = membership_pandas(g["rlog"], g["live"], days, roots, me)
    kP = [k for k in range(len(me)) if PRIMARY[0][:7] <= days[me[k]][:7] <= PRIMARY[1][:7]]
    kP_hold = [k for k in range(len(me)) if days[me[k]] >= "2015-12-01" and days[me[k]] < PRIMARY[1]]   # month-ends whose hold lies in the window
    from collections import Counter
    elig = {"month_ends_total": int(len(me)), "month_ends_primary_hold": int(len(kP_hold)),
            "n_eligible_counts_primary": {str(a): int(b) for a, b in sorted(Counter(diag[k]["n_eligible"] for k in kP_hold).items())},
            "leg_size_counts_primary": {str(a): int(b) for a, b in sorted(Counter(diag[k]["n_leg"] for k in kP_hold).items())},
            "boundary_ties_primary": int(sum(diag[k]["boundary_tie"] for k in kP_hold)),
            "flat_months_primary": int(sum(diag[k]["flat"] for k in kP_hold)),
            "boundary_ties_all": int(sum(d["boundary_tie"] for d in diag)), "flat_months_all": int(sum(d["flat"] for d in diag)),
            "flat_months_long_window": int(sum(diag[k]["flat"] for k in range(len(me)) if LONG[0][:7] <= days[me[k]][:7] <= LONG[1][:7])),
            "root_months_voided_by_the_1m_floor_if_applied": voided_1m, "tot1_identity_cells": tot1_ident_cells,
            "per_root_ineligible_primary": {roots[i]: int(sum(1 for k in kP_hold if not np.isfinite(mom[i, k]))) for i in range(n)},
            "per_month_end": [{"month_end": str(days[me[k]]), **diag[k]} for k in range(len(me))]}
    log(f"  eligibility on the {len(kP_hold)} primary holds: n_eligible {elig['n_eligible_counts_primary']}, legs {elig['leg_size_counts_primary']}, "
        f"boundary ties {elig['boundary_ties_primary']}, flat months {elig['flat_months_primary']}; the 1m floor would have voided {voided_1m} root-months")

    # positions
    sh, pp, sc, sd = R56.positions_from_signs(sign_me.astype(float), sig, me, g)
    cells = {("ew", "published"): dict(book="published", sign_held=sh, scale_held=g["span"].astype(float), pos=sh),
             ("volscaled", "published"): dict(book="published", sign_held=sh, scale_held=sc, pos=pp),
             ("dollar", "dollar"): dict(book="dollar", sign_held=sd.astype(float), scale_held=None, pos=None)}
    prim = cells[PRIMARY_CELL]
    upp, tick_usd, comm_rt, size_name = R56.min_size(g, roots)
    dollar_roots = [r for r in roots if r not in R55.DOLLAR_EXCLUDED]

    # audits -- each proven to raise on its break
    audits = {}
    audits["leg_membership_cells_checked"] = audit_leg_membership(sign_me, sign_pd)
    swapped, k_sw = swap_one_pair(sign_me)
    try:
        audit_leg_membership(swapped, sign_pd); raise RuntimeError("leg audit accepted a SWAPPED pair")
    except AssertionError:
        audits["leg_membership_raises_on_swapped_pair"] = True
    audits["lag_held_cells"] = R55.audit_lag(prim["sign_held"], sign_pd.astype(float), me, g["span"], T)
    unl = unlagged_grid(sign_me, me, g["span"])
    try:
        R55.audit_lag(unl, sign_pd.astype(float), me, g["span"], T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(prim["sign_held"], me, T)
    daily_sign = np.sign(np.nan_to_num(np.cumsum(np.nan_to_num(g["rlog"]), axis=1)))
    try:
        R55.audit_right_quantity(daily_sign, me, T); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    sdi = sd.astype(int)
    gross_d, _, _ = R55.dollar_book(sdi, g, upp, comm_rt, tick_usd, dollar_roots)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(gross_d, np.where(np.array([r in dollar_roots for r in roots])[:, None], sdi, 0), g, upp)
    for label, bad in (("negated", -gross_d),
                       ("mislagged", R55.dollar_book(sdi, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, dollar_roots)[0])):
        try:
            R55.audit_sign_in_money(bad, sdi, g, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True
    x_lag = R55.book_return(prim["pos"], rsimple); x_unl = R55.book_return(unl, rsimple)
    audits["pnl_differs_from_unlagged"] = bool(not np.allclose(x_lag, x_unl))
    if not audits["pnl_differs_from_unlagged"]:
        raise AssertionError("lagged and unlagged P&L coincide")
    audits["tot1_no_floor_identical_where_floored_is_finite"] = True
    log(f"  audits: {audits}")

    # scoring
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]
    results_cells, scored = {}, {}
    per_root_dollar = {}
    for key, c in cells.items():
        name = CELL_NAMES[key]
        if c["book"] == "published":
            x = R55.book_return(c["pos"], rsimple); turn, rolls, tw = R55.published_cost(c["pos"], cbp, g["roll"]); xn = x - turn
            entry = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "net_incl_rolls": R55.sharpe((x - turn - rolls)[wP]),
                     "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                     "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                     "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4),
                     "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                     "mean_gross_weight_long_minus_short": float(np.mean((c["pos"] / np.where((c["pos"] != 0).sum(0) > 0, (c["pos"] != 0).sum(0), 1)[None, :]).sum(0)[wP]))}
            scored[key] = dict(gross=x, net=xn)
        else:
            sP = np.where(wP[None, :], c["sign_held"], 0.0).astype(int); sL = np.where(wL[None, :], c["sign_held"], 0.0).astype(int)
            gross, cost, sides = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots)
            gb, cb = gross.sum(0), cost.sum(0); xg, xn = gb, gb - cb
            g_cd, c_cd, _ = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, cd_roots)
            gL, _, _ = R55.dollar_book(sL, g, upp, comm_rt, tick_usd, dollar_roots)
            R55.audit_sign_book(gross, np.where(np.array([r in dollar_roots for r in roots])[:, None], sP, 0), g, upp)
            entry = {"gross": R55.stats_block(xg[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "cost_total": float(cb[wP].sum()), "sides_total": int(sides[:, wP].sum()),
                     "roll_sides_total": int((2 * (g["roll"] & (sP != 0)))[:, wP].sum()),
                     "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d"),
                                   "net": R55.stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d net")},
                     "gross_long": R55.stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $"),
                     "mean_contracts_held": float((sP != 0).sum(0)[wP].mean())}
            scored[key] = dict(gross=xg, net=xn)
            per_root_dollar = {roots[i]: {"net_total": float((gross[i] - cost[i])[wP].sum()), "gross_total": float(gross[i][wP].sum()),
                                          "cost_total": float(cost[i][wP].sum()), "sigma_usd_per_contract": root_sigma[roots[i]],
                                          "min_size": size_name[i]} for i in range(n) if roots[i] in dollar_roots}
        results_cells[name] = entry
        log(f"  {name:22s} gross SR {entry['gross']['sharpe']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}")

    # group 2 and 3 on the primary
    x = scored[PRIMARY_CELL]["gross"]; pos = prim["pos"]
    rm = root_month_contributions(pos, rsimple, sign_me, me, wP, roots)
    v_all = np.array([r[3] for r in rm]); v_long = np.array([r[3] for r in rm if r[2] > 0]); v_short = np.array([r[3] for r in rm if r[2] < 0])
    root_month = {"combined": dist_stats(v_all), "long_leg": dist_stats(v_long), "short_leg": dist_stats(v_short),
                  "sum_of_contributions": float(v_all.sum()), "book_total_primary": float(x[wP].sum()),
                  "share_long": float(len(v_long) / max(len(v_all), 1))}
    if abs(root_month["sum_of_contributions"] - root_month["book_total_primary"]) > 1e-9:
        raise AssertionError("root-month contributions do not sum to the book total")
    per_root = {}
    cnt = (pos != 0.0).sum(0); wgt = pos / np.where(cnt > 0, cnt, 1.0)[None, :]
    for i, r in enumerate(roots):
        xi = wgt[i] * rsimple[i]; held = pos[i] != 0
        per_root[r] = {"total_primary": float(xi[wP].sum()), "total_long_window": float(xi[wL].sum()),
                       "sharpe_primary_when_held": R55.sharpe((pos[i] * rsimple[i])[wP & held]) if (wP & held).sum() > 60 else None, "sortino_primary_when_held": R55.sortino((pos[i] * rsimple[i])[wP & held]) if (wP & held).sum() > 60 else None,
                       "months_long_primary": int(sum(1 for k in kP_hold if sign_me[i, k] > 0)), "months_short_primary": int(sum(1 for k in kP_hold if sign_me[i, k] < 0)),
                       "months_ineligible_primary": elig["per_root_ineligible_primary"][r],
                       "sigma_usd_min_size": root_sigma[r], "min_size": size_name[i],
                       "dollar_net_total": per_root_dollar.get(r, {}).get("net_total")}
    tot = sum(v["total_primary"] for v in per_root.values())
    srt = sorted(per_root.items(), key=lambda kv: -kv[1]["total_primary"])
    if tot > 0:
        vals = [v["total_primary"] for _, v in srt]; cum = np.cumsum(vals)
        conc = {"basis": "winners' share of a positive total", "total": tot, "top1_share": vals[0] / tot, "top5_share": sum(vals[:5]) / tot,
                "top10_share": sum(vals[:10]) / tot, "roots_to_half": int(np.searchsorted(cum, 0.5 * tot) + 1), "ranked": [(r, v["total_primary"]) for r, v in srt]}
    else:
        srt_l = sorted(per_root.items(), key=lambda kv: kv[1]["total_primary"]); vals = [v["total_primary"] for _, v in srt_l]; cum = np.cumsum(vals)
        conc = {"basis": "losers' share of a NEGATIVE total", "total": tot, "top1_share": vals[0] / tot, "top5_share": sum(vals[:5]) / tot,
                "top10_share": sum(vals[:10]) / tot, "roots_to_half": int(np.searchsorted(-cum, -0.5 * tot) + 1), "ranked": [(r, v["total_primary"]) for r, v in srt_l]}
    n_pos_primary = int(sum(1 for v in per_root.values() if v["total_primary"] > 0))
    conc["roots_positive_primary"] = n_pos_primary
    per_era = {f"{a}..{b}": {"sharpe": _f(R55.sharpe(x[R55.window_mask(days, a, b)])), "sortino": _f(R55.sortino(x[R55.window_mask(days, a, b)])), "n_days": int(R55.window_mask(days, a, b).sum())} for a, b in ERAS}
    yrs = sorted(set(d[:4] for d in days[wL]))
    per_year = {}
    for y in yrs:
        my = np.array([d[:4] == y for d in days]); per_year[y] = {"sharpe": _f(R55.sharpe(x[my])), "sortino": _f(R55.sortino(x[my])), "total": float(x[my].sum())}
    log(f"  root-months: combined mean {root_month['combined']['mean']:+.2e} median {root_month['combined']['median']:+.2e} trimmed {root_month['combined']['trimmed_1pct_both']:+.2e}; "
        f"long-leg mean {root_month['long_leg']['mean']:+.2e}, short-leg mean {root_month['short_leg']['mean']:+.2e}")

    # comparability with the CM-restricted time-series momentum book, rebuilt in-process
    _, pos12, _, _ = R55.build_positions(g, sig, me, (12,))
    x12 = R55.book_return(pos12, rsimple)
    mP, m12 = monthly(x, days, wP), monthly(x12, days, wP)
    d555 = json.loads(D555_JSON.read_text(encoding="utf-8"))
    worst = mP.idxmin()
    comparability = {"rho_daily_2016_2023": float(np.corrcoef(x[wP], x12[wP])[0, 1]), "rho_monthly_2016_2023": float(np.corrcoef(mP.values, m12.values)[0, 1]),
                     "cm_tsmom_sharpe_primary": R55.sharpe(x12[wP]), "cm_tsmom_sortino_primary": R55.sortino(x12[wP]), "cm_tsmom_sharpe_long": R55.sharpe(x12[wL]), "cm_tsmom_sortino_long": R55.sortino(x12[wL]),
                     "d555_per_sector_cm_sharpe_primary": d555["per_sector"]["CM"]["sharpe_primary"], "d555_sessions_primary": d555["windows"]["sessions_primary"],
                     "sessions_primary_here": int(wP.sum()), "sessions_absent_here": absent,
                     "worst_month_primary": str(worst), "worst_month_return_primary": float(mP.loc[worst]), "cm_tsmom_return_that_month": float(m12.loc[worst]),
                     "best_month_primary": str(mP.idxmax()), "best_month_return_primary": float(mP.max()),
                     "monthly_returns_primary": {str(p): float(v) for p, v in mP.items()}}
    log(f"  rho with CM TSMOM daily {comparability['rho_daily_2016_2023']:+.3f} monthly {comparability['rho_monthly_2016_2023']:+.3f}; CM TSMOM SR {comparability['cm_tsmom_sharpe_primary']:+.3f} "
        f"(D555 per-sector {comparability['d555_per_sector_cm_sharpe_primary']:+.3f}); worst month {worst} {mP.loc[worst]:+.2%} (TSMOM {m12.loc[worst]:+.2%})")

    # the dollar book decomposed BEFORE the component line
    dsorted = sorted(per_root_dollar.items(), key=lambda kv: -kv[1]["net_total"])
    dnet_total = sum(v["net_total"] for v in per_root_dollar.values())
    sig_vals = [v["sigma_usd_per_contract"] for v in per_root_dollar.values()]
    dollar_decomp = {"excluded": list(R55.DOLLAR_EXCLUDED), "excluded_in_universe": [r for r in R55.DOLLAR_EXCLUDED if r in roots], "roots": dollar_roots,
                     "net_total": dnet_total, "per_root_sorted": [(r, v["net_total"], v["gross_total"], v["cost_total"], v["sigma_usd_per_contract"], v["min_size"]) for r, v in dsorted],
                     "top_contributor": dsorted[0][0], "top_contributor_net": dsorted[0][1][ "net_total"],
                     "top_contributor_share_of_total": _f(dsorted[0][1]["net_total"] / dnet_total) if dnet_total != 0 else None,
                     "sigma_per_contract_min": float(min(sig_vals)), "sigma_per_contract_max": float(max(sig_vals)),
                     "sigma_per_contract_argmin": min(per_root_dollar, key=lambda r: per_root_dollar[r]["sigma_usd_per_contract"]),
                     "sigma_per_contract_argmax": max(per_root_dollar, key=lambda r: per_root_dollar[r]["sigma_usd_per_contract"]),
                     "cd_roots": cd_roots, "min_size": dict(zip(roots, size_name)), "usd_per_point": dict(zip(roots, upp.tolist())),
                     "cost_convention": "$3 RT micro / $6 RT full + one tick crossed, per side = half of each; a roll is two sides",
                     "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk"}
    log("  dollar book by root (net $, 2016-2023):")
    for r, v in dsorted:
        log(f"    {r:3s} {v['min_size']:4s} net {v['net_total']:+10.0f}  gross {v['gross_total']:+10.0f}  cost {v['cost_total']:7.0f}  sigma/contract {v['sigma_usd_per_contract']:7.0f}")
    log(f"    total net {dnet_total:+.0f}; top contributor {dollar_decomp['top_contributor']} share {dollar_decomp['top_contributor_share_of_total']}; "
        f"sigma/contract {dollar_decomp['sigma_per_contract_min']:.0f} ({dollar_decomp['sigma_per_contract_argmin']}) .. {dollar_decomp['sigma_per_contract_max']:.0f} ({dollar_decomp['sigma_per_contract_argmax']})")
    dcell = results_cells["dollar"]
    component_line = {}
    for label, blk_net, blk_gross in (("dollar_16_roots", dcell["net"], dcell["gross"]), ("cd_subbook", dcell["cd_subset"]["net"], dcell["cd_subset"]["gross"])):
        component_line[label] = {"C_a_net_sharpe": blk_net["sharpe"], "se": blk_net["se"], "gross_sharpe": blk_gross["sharpe"], "hit": blk_net["hit"],
                                 "C_c_skew": blk_net["skew"], "C_c_pass": bool(blk_net["skew"] >= -0.5), "C_d_sigma_daily": blk_net["sd_daily"],
                                 "C_d_pass": bool(blk_net["sd_daily"] <= R55.C_D_SIGMA), "C_a_pass": bool(blk_net["sharpe"] > 0.5),
                                 "total_net": blk_net["total"], "max_dd": blk_net["max_dd"], "rho_with_ledger_entry": "ABSENT"}
    component_line["cd_subbook"]["roots"] = cd_roots
    cl = component_line["dollar_16_roots"]
    log(f"  component line (dollar, 16 roots): C-a net {cl['C_a_net_sharpe']:+.3f} (SE {cl['se']:.2f}) gross {cl['gross_sharpe']:+.3f}, hit {cl['hit']:.3f}, "
        f"skew {cl['C_c_skew']:+.2f}, sigma ${cl['C_d_sigma_daily']:,.0f}; C-d sub-book {cd_roots}: net {component_line['cd_subbook']['C_a_net_sharpe']:+.3f}, sigma ${component_line['cd_subbook']['C_d_sigma_daily']:,.0f}")

    # nulls -- exactness guard, timing, then the enumeration
    live_idx = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    if not all(np.array_equal(live_idx[0], ix) for ix in live_idx):
        raise AssertionError("the roots do not share one index set on the primary window")
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    Tw = int(wP.sum())
    for k in (1, 7, 63, 250, 999, 1500, 1777, 2000, 2010, 3, 11, 101, 333, 444, 555, 666, 777, 888, 1234, 1999):
        k = k % (Tw - 1) or 1
        p = R55.rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k) * prim["scale_held"]
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"enumeration not bit-identical at offset {k}")
        col = p[:, wP]
        if not np.array_equal(np.sort((col > 0).sum(0)), np.sort((null_cells[PRIMARY_CELL]["sign_held"][:, wP] > 0).sum(0))):
            raise AssertionError("rotated legs are not the observed legs")
    log("  exactness guard: 20 offsets bit-identical against the plain loop; rotated leg sizes are the observed ones")
    t0 = time.time()
    for k in range(1, 21):
        for key, c in null_cells.items():
            s_rot = R55.rotate_signs(c["sign_held"], live_idx, k)
            if c["book"] == "published":
                R55.sharpe(R55.book_return(s_rot * c["scale_held"], rsimple)[wP])
            else:
                gr, co, _ = R55.dollar_book(np.sign(s_rot).astype(int), g, upp, comm_rt, tick_usd, dollar_roots); R55.sharpe((gr - co).sum(0)[wP])
    per_off = (time.time() - t0) / 20; projected = per_off * (Tw - 1)
    log(f"  timing: {per_off * 1000:.0f} ms per offset x {Tw - 1} offsets -> projected {projected:.0f} s wall")
    if projected > 900:
        raise AssertionError(f"projected null wall {projected:.0f}s exceeds the 15-minute stop declared in the pre-registration")
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    names = [CELL_NAMES[k] for k in keys]
    obs = np.array([results_cells[nm]["gross"]["sharpe"] if b == "published" else results_cells[nm]["net"]["sharpe"] for nm, (a, b) in zip(names, keys)])
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= Tw - R55.NULL_PURGE); null = null_all[keep]
    jP = keys.index(PRIMARY_CELL)
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": int(R55.NULL_PURGE), "offsets_after_purge": int(null.shape[0]), "per_cell": {},
          "per_cell_unpurged": {}, "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_all[:, jP].tolist(), "sortino": null_s[:, jP].tolist()}}
    for j, nm in enumerate(names):
        col = null[:, j]; raw = null_all[:, j]
        n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)),
                              "p95": float(np.percentile(col, 95)), "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95)),
                              "sortino": R55.sortino_null_block(scored[keys[j]]["gross" if keys[j][1] == "published" else "net"][wP], null_s[:, j], keep)}
        n1["per_cell_unpurged"][nm] = {"p05": float(np.percentile(raw, 5)), "p50": float(np.percentile(raw, 50)), "p95": float(np.percentile(raw, 95)),
                                       "pct_rank": float((raw < obs[j]).mean()), "max": float(raw.max()), "argmax_k": int(ks[int(raw.argmax())])}
    fam = null.max(1)
    n2 = {"observed_best": float(obs.max()), "observed_best_cell": names[int(obs.argmax())], "p50": float(np.percentile(fam, 50)),
          "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95))}
    primary = n1["per_cell"][CELL_NAMES[PRIMARY_CELL]]
    log(f"  N1 primary: observed {primary['observed']:+.3f}  p05 {primary['p05']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f}\n"
        f"  N2 family: best {n2['observed_best']:+.3f} ({n2['observed_best_cell']})  p50 {n2['p50']:+.3f}  p95 {n2['p95']:+.3f}  rank {n2['pct_rank']:.3f}")

    # predictions
    cE, cV = results_cells["EW/published"], results_cells["vol-scaled/published"]
    sE, sV = cE["gross"]["sharpe"], cV["gross"]["sharpe"]
    preds = {
        "P-1": {"claim": "EW/published gross Sharpe 2016-2023 > 0 and above N1 p95; deposit point range 0.15-0.35 net, judged gross 0.17-0.37",
                "value": sE, "p95": primary["p95"], "net_value": cE["net"]["sharpe"],
                "holds": bool(sE > 0 and primary["clears_p95"]), "in_point_range_gross": bool(POINT_RANGE_GROSS[0] <= sE <= POINT_RANGE_GROSS[1]),
                "in_point_range_net": bool(POINT_RANGE_NET[0] <= cE["net"]["sharpe"] <= POINT_RANGE_NET[1])},
        "P-2": {"claim": "daily rho with the CM-restricted 12m TSMOM book > 0 and < 0.7", "value": comparability["rho_daily_2016_2023"],
                "monthly": comparability["rho_monthly_2016_2023"], "holds": bool(0 < comparability["rho_daily_2016_2023"] < 0.7)},
        "P-3": {"claim": "the long leg's mean root-month P&L contribution > the short leg's", "long_mean": root_month["long_leg"]["mean"],
                "short_mean": root_month["short_leg"]["mean"], "holds": bool(root_month["long_leg"]["mean"] > root_month["short_leg"]["mean"])},
        "P-4": {"claim": "the primary's worst month is a reversal month: the CM TSMOM return that month is also negative",
                "worst_month": comparability["worst_month_primary"], "primary_return": comparability["worst_month_return_primary"],
                "cm_tsmom_return": comparability["cm_tsmom_return_that_month"], "holds": bool(comparability["cm_tsmom_return_that_month"] < 0)},
        "P-5": {"claim": "vol-scaled cell's gross Sharpe within +/-0.15 of the EW cell's", "ew": sE, "volscaled": sV, "holds": bool(abs(sV - sE) <= 0.15)},
        "P-6": {"claim": "the dollar book fails C-d (daily sigma > $500)", "sigma_daily": dcell["net"]["sd_daily"], "holds": bool(dcell["net"]["sd_daily"] > R55.C_D_SIGMA)},
        "P-7": {"claim": "falsifier: gates green and primary below N1 p50 -> the sort did badly on this window",
                "gates_green": bool(all(v is True for k, v in audits.items() if "raises" in k or "identical" in k)),
                "primary_below_p50": bool(sE < primary["p50"]), "fires": bool(sE < primary["p50"])},
    }
    verdict = "PASS" if (sE > 0 and primary["clears_p95"] and n2["clears_p95"]) else "DOES NOT PASS"
    log("  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds', v.get('fires')) else 'fails'}" for k, v in preds.items()))

    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS in this file are NEGATIVE: minimum of (cumulative daily return - running peak); "
                                                                  "return units for the published books, dollars at minimum size for the dollar books (D542).", "record": "D542"},
           "spec": "D558", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX),
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "last_session_read": last_session_read,
                       "sessions_primary": int(wP.sum()), "sessions_long": int(wL.sum()), "sessions_total": int(T), "month_ends": int(len(me))},
           "universe": {"roots": roots, "n": n, "live_start": {r: live_start[r] for r in roots}, "sessions_absent_vs_36_root_frame": absent,
                        "dollar_excluded": [r for r in R55.DOLLAR_EXCLUDED if r in roots], "min_eligible": MIN_ELIGIBLE, "lookback_months": LOOKBACK, "skip_months": SKIP,
                        "rows_dropped": {"no_close": df_all.attrs["rows_dropped_no_close"], "weekend_stub": df_all.attrs["rows_dropped_weekend_stub"]}},
           "eligibility": elig, "cells": results_cells, "primary": primary, "null_n1": n1, "null_n2": n2, "root_month": root_month, "concentration": conc,
           "per_root": per_root, "per_era": per_era, "per_year": per_year, "comparability": comparability, "dollar_book": dollar_decomp,
           "component_line": component_line, "predictions": preds, "verdict": {"declared": verdict}, "audits": audits,
           "timing": {"wall_s": round(time.time() - t_start, 1), "null_ms_per_offset": round(per_off * 1000, 1), "null_projected_s": round(projected, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    if list(res.keys())[0] != "max_drawdown_convention":
        raise AssertionError("max_drawdown_convention must be the first key")
    OUT.write_text(json.dumps(res, indent=1, default=R55._json_default), encoding="utf-8")
    log(f"\n  VERDICT {verdict}   -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: synthetic bars, no fixture read, no cell scored
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D558 SELF-TEST -- synthetic bars on 12 roots, no fixture read, no cell scored\n")
    rng = np.random.default_rng(558)
    days = pd.bdate_range("2010-06-07", "2014-12-31").strftime("%Y-%m-%d").to_numpy(); T = len(days)
    roots = [f"R{c}" for c in "ABCDEFGHIJKL"]; n = len(roots)
    drift = np.repeat([-0.003, 0.0, +0.003], 4)             # RA-RD the losers, RE-RH flat, RI-RL the winners: groups 8 sd apart over 11 months
    rlog = drift[:, None] + 0.004 * rng.standard_normal((n, T)); rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool)
    close = np.exp(np.nancumsum(rlog, axis=1)) * 100.0
    dP = np.diff(close, axis=1, prepend=np.nan)
    roll = np.zeros((n, T), dtype=bool); roll[:, 300] = True
    g = dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=live.copy(), nonpositive=[])
    me = R55.month_ends(days); sig = R55.ew_vol(rlog, live)

    mom, voided, ident = momentum_at_month_ends(g, me)
    _, t12 = R55.signal_at_month_ends(rlog, live, days, me, 12); _, t1f = R55.signal_at_month_ends(rlog, live, days, me, 1)
    k_last = len(me) - 1
    if not np.isclose(mom[0, k_last], t12[0, k_last] - t1f[0, k_last]):
        raise AssertionError("12-1 is not tot12 - tot1")
    a = R55._window_start(days, me[k_last], 12); b = R55._window_start(days, me[k_last], 1)
    direct = np.nansum(rlog[0, a:b])
    if not np.isclose(mom[0, k_last], direct):
        raise AssertionError("12-1 is not the sum over the 11 months before the month-end's month")
    print(f"  [1] momentum 12-1 = tot12 - tot1 = the 11-month sum ending the month before ({ident} cells bit-identical to the floored 1m read; the floor would void {voided} here)")

    sign_me, diag = rank_membership(mom, roots)
    sign_pd = membership_pandas(rlog, live, days, roots, me)
    if not np.array_equal(sign_me, sign_pd):
        raise AssertionError("runner and pandas memberships disagree")
    d = diag[k_last]
    if not (d["n_eligible"] == 12 and d["n_leg"] == 4 and not d["flat"]):
        raise AssertionError(f"expected 12 eligible -> 4/4/4, got {d}")
    if not ((sign_me[-4:, k_last] == 1).all() and (sign_me[:4, k_last] == -1).all() and (sign_me[4:8, k_last] == 0).all()):
        raise AssertionError("the known drift ordering was not recovered by the sort")
    print("  [2] runner and pandas memberships agree on every month-end; 12 eligible -> 4/4/4 and the four best drifts are long, the four worst short, the middle flat")

    crafted = np.full((n, 3), np.nan)
    crafted[:, 0] = np.arange(n, dtype=float)                       # 12 eligible, distinct
    crafted[:7, 1] = np.arange(7, dtype=float)                      # 7 eligible -> flat month
    crafted[:, 2] = np.array([5, 5, 5, 5, 1, 2, 3, 4, 0, 0, 0, 0], dtype=float)   # 4-way tie at the top and at the bottom
    s_c, d_c = rank_membership(crafted, roots)
    if not (d_c[1]["flat"] and (s_c[:, 1] == 0).all()):
        raise AssertionError("a month with fewer than 9 eligible was not flat")
    if not (s_c[[0, 1, 2, 3], 2] == 1).all() or not (s_c[[8, 9, 10, 11], 2] == -1).all():
        raise AssertionError("tie rule did not resolve alphabetically")
    crafted2 = crafted.copy(); crafted2[:, 2] = np.array([5, 5, 5, 5, 5, 2, 3, 4, 0, 0, 0, 0], dtype=float)   # 5-way tie across the long boundary
    s_c2, d_c2 = rank_membership(crafted2, roots)
    if not (d_c2[2]["boundary_tie"] and not d_c[2]["boundary_tie"] and (s_c2[[0, 1, 2, 3], 2] == 1).all() and s_c2[4, 2] == 0):
        raise AssertionError("boundary tie not counted or not broken alphabetically")
    print("  [3] fewer than 9 eligible -> flat month; a tie across the leg boundary is broken alphabetically and COUNTED (a tie inside a leg is not)")

    sh, pp, sc, sd = R56.positions_from_signs(sign_me.astype(float), sig, me, g)
    R55.audit_lag(sh, sign_pd.astype(float), me, live, T)
    unl = unlagged_grid(sign_me, me, live)
    raised = False
    try:
        R55.audit_lag(unl, sign_pd.astype(float), me, live, T)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("lag audit accepted an UNLAGGED grid")
    print("  [4] lag audit passes the held membership grid and RAISES on the unlagged one")

    R55.audit_right_quantity(sh, me, T)
    raised = False
    try:
        R55.audit_right_quantity(np.sign(np.nan_to_num(rlog)), me, T)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("right-quantity audit accepted a daily grid")
    print("  [5] right-quantity audit passes the monthly grid and RAISES on a daily one")

    upp = np.full(n, 5.0); tick = np.full(n, 1.25); comm = np.full(n, 3.0)
    sdi = sd.astype(int)
    gross, cost, sides = R55.dollar_book(sdi, g, upp, comm, tick, roots)
    R55.audit_sign_in_money(gross, sdi, g, upp)
    for label, bad in (("NEGATED", -gross), ("MIS-LAGGED", R55.dollar_book(sdi, dict(g, dP=np.roll(dP, 1, axis=1)), upp, comm, tick, roots)[0])):
        raised = False
        try:
            R55.audit_sign_in_money(bad, sdi, g, upp)
        except AssertionError:
            raised = True
        if not raised:
            raise AssertionError(f"sign audit accepted a {label} gross grid")
    print("  [6] sign audit in money passes the dollar book and RAISES on a negated and on a mis-lagged gross grid")

    audit_leg_membership(sign_me, sign_pd)
    swapped, k_sw = swap_one_pair(sign_me)
    raised = False
    try:
        audit_leg_membership(swapped, sign_pd)
    except AssertionError:
        raised = True
    if not raised:
        raise AssertionError("leg audit accepted a swapped pair")
    if int((swapped != sign_me).sum()) != 2:
        raise AssertionError("the break did not change exactly two cells")
    print(f"  [7] leg-membership audit passes the runner's grid and RAISES on one long/short pair swapped at month-end {k_sw}")

    rsimple = np.where(np.isfinite(rlog), np.expm1(np.nan_to_num(rlog)), 0.0)
    live_idx = [np.flatnonzero(live[i]) for i in range(n)]
    scale_ew = live.astype(float)
    for k in (1, 5, 77, 400):
        p = R55.rotate_signs(sh, live_idx, k) * scale_ew
        if not np.array_equal(R55.book_return(p, rsimple), R55.book_return_loop(p, rsimple)):
            raise AssertionError("book_return vectorised != loop")
        if not np.array_equal(np.sort((p > 0).sum(0)), np.sort((sh > 0).sum(0))):
            raise AssertionError("rotated legs are not the observed legs")
    if not np.array_equal(R55.rotate_signs(sh, live_idx, T), sh):
        raise AssertionError("rotation by the full length is not the identity")
    x = R55.book_return(sh * scale_ew, rsimple)
    held = (sh != 0).any(0)
    if not R55.sharpe(x[held]) > 1.0:
        raise AssertionError("a known cross-sectional spread did not produce a positive book")
    long_w = (sh > 0).sum(0)[held]; short_w = (sh < 0).sum(0)[held]
    if not np.array_equal(long_w, short_w):
        raise AssertionError("legs are not equal")
    print(f"  [8] enumeration path bit-identical to the loop at 4 offsets; rotated leg sizes are observed ones; rotation by L is the identity; "
          f"known-spread EW book Sharpe {R55.sharpe(x[held]):+.2f} with equal legs on every held session")
    print("\n  ALL SELF-TESTS PASSED. No fixture was read and no cell was scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); gq = ap.add_mutually_exclusive_group(required=True)
    gq.add_argument("--run", action="store_true"); gq.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (0 if run() else 1))
