"""D559 -- the momentum x term-structure DOUBLE SORT as published (Fuertes, Miffre & Rallis 2010) on the
17 commodity roots of the breadth fixture, off D556's curve table.

Spec committed in 000eda0 BEFORE this file (R8). Primary window 2016-01-04..2023-12-29; the long
window 2011-01-03..2023-12-29 is a declared diagnostic; the 2024+ slice is RESERVED AND NOT READ.
Nothing admitted (R15).

    python scripts/run_d559_double_sort.py --selftest
    python scripts/run_d559_double_sort.py --run        # -> data/d559_double_sort.json

Everything that is not the double sort itself is imported from run_d556_carry_timing.py (carry at
the month-ends, positions from signs, minimum size, the strip audit) and through it from
run_d555_tsmom_replication.py (the fixture loader, the grids, the EW vol, the month-end signal, the
holds, the book return, the dollar book, the three audits, the enumerated rotation null and its
purge). The sort: at each month-end rank the eligible names by 12-1 momentum, terciles of
ceil(n/3); within the top tercile take the ceil(n_tercile/3) most-backwardated as LONG, within the
bottom tercile the ceil(n_tercile/3) most-contangoed as SHORT; ties by root symbol; fewer than 9
eligible -> flat. Three cells: EW/published (primary), vol-scaled/published, dollar at minimum size.
Two single sorts rebuilt in-process as an unpromotable diagnostic (json `single_sort_check`).
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

OUT = REPO / "data" / "d559_double_sort.json"
SPEC = "000eda0"
PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
CM_ROOTS = sorted(R55.SECTOR["CM"])          # 17 roots, alphabetical -- the tie order
MIN_ELIGIBLE = 9                              # fewer eligible names -> flat month
CELL_KEYS = [("ew", "published"), ("volscaled", "published"), ("minsize", "dollar")]
PRIMARY_CELL = ("ew", "published")
GUARD_OFFSETS = (1, 7, 63, 250, 999, 1500, 1777, 2000, 2010, 3, 11, 101, 333, 444, 555, 666, 777, 888, 1234, 1999)
POINT_RANGE_GROSS = (0.28, 0.45)              # the pre-reg's gross equivalent of the deposit's net 0.25-0.40
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "curve_sha256", "strip_sha256",
                    "windows", "universe", "cells", "primary", "null_n1", "null_n2", "month_end_table", "month_end_summary",
                    "root_month", "concentration", "per_root", "per_year", "per_era", "single_sort_check", "dollar_book",
                    "component_line", "predictions", "verdict", "amendment_unfloored_1m", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# the universe: D555's grids, subset to the 17 commodity rows
# --------------------------------------------------------------------------------------------
def subset_grids(g, roots_keep):
    ix = [g["roots"].index(r) for r in roots_keep]
    out = {"roots": list(roots_keep), "days": g["days"], "nonpositive": [x for x in g["nonpositive"] if x[0] in roots_keep]}
    for k in ("close", "rlog", "dP", "roll", "live", "span"):
        out[k] = g[k][ix]
    return out


def momentum_12_1(g, me):
    """12-1 momentum at the month-ends: tot12 - tot1 from D555's signal (the 11 calendar months ending
    the month before the month-end's own month). NaN where either cell is NaN -- and D555's count floor
    (240 returns per 12 months, so round(240/12) = 20 for the 1-month cell) makes tot1 NaN in any
    calendar month with fewer than 20 returns. The pre-registration declared that and asked for the
    count; the first run showed it is a CALENDAR filter (19-session months), see amendment_unfloored."""
    _, tot12 = R55.signal_at_month_ends(g["rlog"], g["live"], g["days"], me, 12)
    _, tot1 = R55.signal_at_month_ends(g["rlog"], g["live"], g["days"], me, 1)
    mom = tot12 - tot1
    n_12_only = int((np.isfinite(tot12) & ~np.isfinite(tot1)).sum())
    return mom, n_12_only


def momentum_12_1_unfloored(g, me):
    """AMENDMENT, diagnostic and unpromotable: the same tot12 (D555's 240-return floor, live at m) minus
    the plain calendar-month sum of the month-end's own month with NO count floor, so a name is
    eligible exactly when its 12-month cell is finite. The month sum is the difference of the same
    cumulative sums D555's signal uses."""
    rlog, live, days = g["rlog"], g["live"], g["days"]
    _, tot12 = R55.signal_at_month_ends(rlog, live, days, me, 12)
    fin = np.isfinite(rlog) & live
    cs = np.concatenate([np.zeros((rlog.shape[0], 1)), np.cumsum(np.where(fin, rlog, 0.0), axis=1)], axis=1)
    tot1 = np.full_like(tot12, np.nan)
    for k, m_ix in enumerate(me):
        a = R55._window_start(days, m_ix, 1)
        tot1[:, k] = cs[:, m_ix + 1] - cs[:, a]
    return tot12 - tot1


# --------------------------------------------------------------------------------------------
# the sort -- implementation A (plain Python over sorted keys)
# --------------------------------------------------------------------------------------------
def _ranked(idx, vals, roots):
    """Indices sorted by (-value, root symbol): the highest value first, ties alphabetical."""
    return sorted(idx, key=lambda i: (-float(vals[i]), roots[i]))


def _tie_at(order, vals, pos):
    """True when the names at ranks pos and pos+1 (0-based) of `order` carry the same value."""
    return 0 <= pos < len(order) - 1 and float(vals[order[pos]]) == float(vals[order[pos + 1]])


def double_sort(mom_me, carry_me, roots):
    """Membership grid (n x K) in {-1, 0, +1} and a per-month-end diagnostic list."""
    n, K = mom_me.shape
    mem = np.zeros((n, K), dtype=int)
    diag = []
    for k in range(K):
        elig = np.flatnonzero(np.isfinite(mom_me[:, k]) & np.isfinite(carry_me[:, k]))
        missing_mom = [roots[i] for i in range(n) if not np.isfinite(mom_me[i, k])]
        missing_carry = [roots[i] for i in range(n) if not np.isfinite(carry_me[i, k])]
        row = {"k": k, "n_eligible": int(elig.size), "missing_momentum": missing_mom, "missing_carry": missing_carry,
               "n_top": 0, "n_mid": 0, "n_bottom": 0, "n_long": 0, "n_short": 0, "boundary_ties": 0, "flat": False, "flat_reason": None,
               "long": [], "short": []}
        if elig.size < MIN_ELIGIBLE:
            row["flat"] = True; row["flat_reason"] = "fewer_than_9_eligible"; diag.append(row); continue
        order = _ranked(elig, mom_me[:, k], roots)
        n_leg = math.ceil(len(order) / 3)
        top, bottom = order[:n_leg], order[len(order) - n_leg:]
        row["n_top"], row["n_bottom"], row["n_mid"] = len(top), len(bottom), len(order) - 2 * n_leg
        ties = int(_tie_at(order, mom_me[:, k], n_leg - 1)) + int(_tie_at(order, mom_me[:, k], len(order) - n_leg - 1))
        top_c = _ranked(top, carry_me[:, k], roots)
        bot_c = _ranked(bottom, carry_me[:, k], roots)
        c_top, c_bot = math.ceil(len(top_c) / 3), math.ceil(len(bot_c) / 3)
        longs, shorts = top_c[:c_top], bot_c[len(bot_c) - c_bot:]
        ties += int(_tie_at(top_c, carry_me[:, k], c_top - 1)) + int(_tie_at(bot_c, carry_me[:, k], len(bot_c) - c_bot - 1))
        row["boundary_ties"] = ties
        if not longs or not shorts:
            row["flat"] = True; row["flat_reason"] = "empty_corner"; diag.append(row); continue
        for i in longs:
            mem[i, k] = 1
        for i in shorts:
            mem[i, k] = -1
        row["n_long"], row["n_short"] = len(longs), len(shorts)
        row["long"], row["short"] = [roots[i] for i in longs], [roots[i] for i in shorts]
        diag.append(row)
    return mem, diag


def single_sort(sig_me, elig_mask, roots):
    """Terciles on ONE signal under the identical rule: long the top ceil(n/3), short the bottom ceil(n/3)."""
    n, K = sig_me.shape
    mem = np.zeros((n, K), dtype=int)
    for k in range(K):
        elig = np.flatnonzero(elig_mask[:, k])
        if elig.size < MIN_ELIGIBLE:
            continue
        order = _ranked(elig, sig_me[:, k], roots)
        n_leg = math.ceil(len(order) / 3)
        for i in order[:n_leg]:
            mem[i, k] = 1
        for i in order[len(order) - n_leg:]:
            mem[i, k] = -1
    return mem


# --------------------------------------------------------------------------------------------
# the sort -- implementation B (pandas rank / groupby; never calls double_sort)
# --------------------------------------------------------------------------------------------
def membership_pandas(mom_me, carry_me, roots):
    n, K = mom_me.shape
    mem = np.zeros((n, K), dtype=int)
    for k in range(K):
        df = pd.DataFrame({"root": roots, "mom": mom_me[:, k], "carry": carry_me[:, k]}).dropna()
        if len(df) < MIN_ELIGIBLE:
            continue
        df = df.sort_values("root").reset_index(drop=True)                    # ties resolve alphabetically
        df["mrank"] = df["mom"].rank(ascending=False, method="first")
        n_leg = math.ceil(len(df) / 3)
        df["terc"] = np.where(df["mrank"] <= n_leg, "top", np.where(df["mrank"] > len(df) - n_leg, "bottom", "mid"))
        df["crank"] = df.groupby("terc")["carry"].rank(ascending=False, method="first")
        size = df.groupby("terc")["root"].transform("size")
        take = np.ceil(size / 3)
        is_long = (df["terc"] == "top") & (df["crank"] <= take)
        is_short = (df["terc"] == "bottom") & (df["crank"] > size - take)
        if not is_long.any() or not is_short.any():
            continue
        for r in df.loc[is_long, "root"]:
            mem[roots.index(r), k] = 1
        for r in df.loc[is_short, "root"]:
            mem[roots.index(r), k] = -1
    return mem


def audit_corner_membership(mem_a, mem_b, me, days):
    """The runner's membership must equal the independent pandas membership at every month-end."""
    bad = np.argwhere(mem_a != mem_b)
    if bad.size:
        i, k = bad[0]
        raise AssertionError(f"CORNER AUDIT: {bad.shape[0]} cells disagree; first at month-end {days[me[k]]} row {i}: "
                             f"runner {mem_a[i, k]:+d}, pandas {mem_b[i, k]:+d}")
    return int((mem_a != 0).sum())


def unlagged_grid(mem, me, span):
    """Membership applied to the month it was read in (the break for the lag audit)."""
    n, T = span.shape
    unl = np.zeros((n, T))
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = mem[:, k][:, None]
    return np.where(span, unl, 0.0)


def _guard_required(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    if list(res.keys())[0] != "max_drawdown_convention":
        raise AssertionError("max_drawdown_convention is not the first key")


# --------------------------------------------------------------------------------------------
# distribution and concentration helpers
# --------------------------------------------------------------------------------------------
def dist_block(v):
    v = np.asarray(v, dtype=float)
    if v.size == 0:
        return {"n": 0}
    s = np.sort(v); cut = max(1, int(math.ceil(0.01 * v.size)))
    wins, loss = v[v > 0], v[v < 0]
    return {"n": int(v.size), "mean": float(v.mean()), "median": float(np.median(v)),
            "mean_ex_top_1pct": float(s[:-cut].mean()) if v.size > cut else None,
            "mean_ex_bottom_1pct": float(s[cut:].mean()) if v.size > cut else None,
            "mean_trimmed_1pct_both": float(s[cut:-cut].mean()) if v.size > 2 * cut else None,
            "win_rate": float((v > 0).mean()), "payoff": float(wins.mean() / abs(loss.mean())) if wins.size and loss.size else None,
            "skew": float(pd.Series(v).skew()) if v.size > 2 else None, "kurt": float(pd.Series(v).kurt()) if v.size > 3 else None,
            "top_1pct_share_of_total": float(s[-cut:].sum() / v.sum()) if v.sum() != 0 else None}


def root_month_contrib(pos, rsimple, days, w):
    """Per (root, month) contribution to the book return: pos x r / n_positioned, summed within the month."""
    cnt = (pos != 0.0).sum(0)
    contrib = pos * rsimple / np.where(cnt > 0, cnt, 1.0)[None, :]
    ym = np.array([d[:7] for d in days])
    out = []
    for i in range(pos.shape[0]):
        for u in np.unique(ym[w]):
            m = (ym == u) & w & (pos[i] != 0.0)
            if m.any():
                out.append((i, u, float(contrib[i, m].sum()), int(np.sign(pos[i, m][0]))))
    return out, contrib


def concentration(contrib, roots, w):
    tot = {r: float(contrib[i][w].sum()) for i, r in enumerate(roots)}
    total = sum(tot.values())
    order = sorted(tot, key=lambda r: -tot[r])
    absorder = sorted(tot, key=lambda r: -abs(tot[r]))
    abs_total = sum(abs(v) for v in tot.values())
    share = lambda k: float(sum(tot[r] for r in order[:k]) / total) if total != 0 else None
    half = None
    if total > 0:
        acc = 0.0
        for j, r in enumerate(order):
            acc += tot[r]
            if acc >= 0.5 * total:
                half = j + 1; break
    return {"per_root_total_sorted": [(r, tot[r]) for r in order], "book_total": total,
            "top1_share_of_total": share(1), "top5_share_of_total": share(5), "top10_share_of_total": share(10),
            "top1_abs_share": float(abs(tot[absorder[0]]) / abs_total) if abs_total > 0 else None, "top1_abs_root": absorder[0],
            "roots_to_half_pnl": half}


def per_year_sharpe(x, days, w):
    yrs = sorted(set(d[:4] for d in days[w]))
    return {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "sortino": R55.sortino(x[np.array([d[:4] == y for d in days])]), "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in yrs}


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D559 -- momentum x term-structure double sort as published, 17 commodity roots\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    for p in (R56.CURVE, R56.STRIP):
        meta = json.loads(p.with_suffix("").with_suffix(".meta.json").read_text(encoding="utf-8"))
        if not meta.get("all_gates_pass"):
            raise AssertionError(f"{p.name}: gates have not passed")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present after filtering")
    live_start = R55.live_start_by_rule(df); g36 = R55.build_grids(df, live_start)
    g = subset_grids(g36, CM_ROOTS); roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    last_session_read = str(days[-1])
    if last_session_read >= RESERVED_FROM:
        raise AssertionError("a reserved session survived into the grid")
    log(f"  grid: {n} roots x {T} sessions {days[0]}..{days[-1]}  (last session read {last_session_read})")
    me = R55.month_ends(days); sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    curve = curve[curve["ref"] < RESERVED_FROM]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[strip["ref"] < RESERVED_FROM]
    if (curve["ref"] >= RESERVED_FROM).any() or (strip["ref"] >= RESERVED_FROM).any():
        raise AssertionError("reserved rows in the curve or strip")
    C = R56.carry_grid(g, curve)
    carry_me = R56.carry_at_month_ends(C, g["live"], me)
    mom_me, n_12_only = momentum_12_1(g, me)
    elig = np.isfinite(mom_me) & np.isfinite(carry_me)

    # the sort, both implementations
    mem, diag = double_sort(mom_me, carry_me, roots)
    mem_pd = membership_pandas(mom_me, carry_me, roots)
    audits = {}
    audits["corner_cells_checked"] = audit_corner_membership(mem, mem_pd, me, days)
    k_sw = next(k for k in range(len(me)) if (mem[:, k] > 0).any() and (mem[:, k] < 0).any())
    bad = mem.copy(); iL = int(np.flatnonzero(mem[:, k_sw] > 0)[0]); iS = int(np.flatnonzero(mem[:, k_sw] < 0)[0])
    bad[iL, k_sw], bad[iS, k_sw] = -1, 1
    try:
        audit_corner_membership(bad, mem_pd, me, days); raise RuntimeError("corner audit accepted a swapped pair")
    except AssertionError:
        audits["corner_raises_on_swapped_pair"] = True
    upp, tick_usd, comm_rt, size_name = R56.min_size(g, roots)
    dollar_roots = [r for r in roots if r not in R55.DOLLAR_EXCLUDED]
    keep16 = np.array([r in dollar_roots for r in roots])

    # positions and cells
    sign_ew = R55.hold_from_month_ends(mem.astype(float), me, T, g["span"])
    scale_ew = g["span"].astype(float)                       # 1.0 on the span: the rotated sign alone is the position
    sh_v, pos_v, sc_v, sd_v = R56.positions_from_signs(mem.astype(float), sig, me, g)
    sign_dollar = R55.hold_from_month_ends(mem, me, T, g["span"]).astype(int)
    if not np.array_equal(sign_dollar, sd_v):
        raise AssertionError("the dollar sign grid differs from positions_from_signs' sign grid")
    cells = {("ew", "published"): dict(book="published", sign_held=sign_ew, scale_held=scale_ew, pos=sign_ew),
             ("volscaled", "published"): dict(book="published", sign_held=sh_v, scale_held=sc_v, pos=pos_v),
             ("minsize", "dollar"): dict(book="dollar", sign_held=sign_dollar.astype(float), scale_held=None, pos=None)}
    prim = cells[PRIMARY_CELL]

    # audits (a)-(d)
    audits["lag_held_cells"] = R55.audit_lag(sign_ew, mem_pd.astype(float), me, g["span"], T)
    unl = unlagged_grid(mem, me, g["span"])
    try:
        R55.audit_lag(unl, mem_pd.astype(float), me, g["span"], T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(sign_ew, me, T)
    try:
        R55.audit_right_quantity(np.sign(np.nan_to_num(C)), me, T); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    s16 = np.where(keep16[:, None], sign_dollar, 0)
    gross_d, _, _ = R55.dollar_book(s16, g, upp, comm_rt, tick_usd, dollar_roots)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(gross_d, s16, g, upp)
    for label, badg in (("negated", -gross_d), ("mislagged", R55.dollar_book(s16, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, dollar_roots)[0])):
        try:
            R55.audit_sign_in_money(badg, s16, g, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True
    carry_sign_me = np.where(np.isfinite(carry_me), np.sign(carry_me), 0.0)
    breadth_front = {(r, d): f for r, d, f in zip(curve["root"], curve["ref"], curve["front"])}
    audits["carry_from_strip_cells_checked"] = R56.audit_carry_from_strip(carry_sign_me, me, g, strip, breadth_front)
    try:
        R56.audit_carry_from_strip(-carry_sign_me, me, g, strip, breadth_front, n_check=40); raise RuntimeError("carry audit accepted a NEGATED sign grid")
    except AssertionError:
        audits["carry_audit_raises_on_negated_grid"] = True
    x_lag = R55.book_return(sign_ew, rsimple); x_unl = R55.book_return(unl, rsimple)
    audits["pnl_differs_from_unlagged"] = bool(not np.allclose(x_lag, x_unl))
    if not audits["pnl_differs_from_unlagged"]:
        raise AssertionError("lagged and unlagged P&L coincide")
    log(f"  audits: {audits}")

    # windows, cost, per-root sigma
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]

    # the month-end table
    me_in_P = [k for k in range(len(me)) if wP[me[k]]]
    me_table = [dict(row, month_end=str(days[me[row["k"]]])) for row in diag]
    in_p = [row for row in me_table if row["k"] in me_in_P]
    me_summary = {"month_ends_primary": len(in_p), "flat_months_primary": int(sum(r["flat"] for r in in_p)),
                  "flat_fewer_than_9": int(sum(r["flat_reason"] == "fewer_than_9_eligible" for r in in_p)),
                  "flat_empty_corner": int(sum(r["flat_reason"] == "empty_corner" for r in in_p)),
                  "n_eligible_min": int(min(r["n_eligible"] for r in in_p)), "n_eligible_median": float(np.median([r["n_eligible"] for r in in_p])),
                  "n_eligible_max": int(max(r["n_eligible"] for r in in_p)),
                  "tercile_sizes_mode": pd.Series([f"{r['n_top']}/{r['n_mid']}/{r['n_bottom']}" for r in in_p if not r["flat"]]).mode().iloc[0],
                  "corner_sizes_counts": {str(k): int(v) for k, v in pd.Series([f"{r['n_long']}/{r['n_short']}" for r in in_p if not r["flat"]]).value_counts().items()},
                  "boundary_ties_total": int(sum(r["boundary_ties"] for r in in_p)), "month_ends_with_a_boundary_tie": int(sum(r["boundary_ties"] > 0 for r in in_p)),
                  "root_months_missing_momentum": int(sum(len(r["missing_momentum"]) for r in in_p)),
                  "root_months_missing_carry": int(sum(len(r["missing_carry"]) for r in in_p)),
                  "roots_ever_missing_a_signal_primary": sorted(set(x for r in in_p for x in r["missing_momentum"] + r["missing_carry"])),
                  "month_ends_12m_finite_1m_not_all": n_12_only,
                  "long_corner_occupancy": {str(k): int(v) for k, v in pd.Series([x for r in in_p for x in r["long"]]).value_counts().items()},
                  "short_corner_occupancy": {str(k): int(v) for k, v in pd.Series([x for r in in_p for x in r["short"]]).value_counts().items()}}
    log(f"  month-ends in the primary window {me_summary['month_ends_primary']}: flat {me_summary['flat_months_primary']}, n_eligible "
        f"{me_summary['n_eligible_min']}..{me_summary['n_eligible_max']} (median {me_summary['n_eligible_median']}), terciles {me_summary['tercile_sizes_mode']}, "
        f"corners {me_summary['corner_sizes_counts']}, boundary ties {me_summary['boundary_ties_total']}")

    # score every cell
    results_cells, scored = {}, {}
    for key in CELL_KEYS:
        c = cells[key]; cell, book = key; name = f"{cell}/{book}"
        if book == "published":
            x = R55.book_return(c["pos"], rsimple); turn, rolls, tw = R55.published_cost(c["pos"], cbp, g["roll"]); xn = x - turn
            entry = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "net_incl_rolls": R55.sharpe((x - turn - rolls)[wP]),
                     "ann_mean_return": float(x[wP].mean() * 252),
                     "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                     "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                     "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4),
                     "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                     "days_positioned_primary": int(((c["pos"] != 0).any(0) & wP).sum()),
                     "net_notional_share_of_gross": float(np.mean(np.abs(c["pos"][:, wP].sum(0)) / np.maximum(np.abs(c["pos"][:, wP]).sum(0), 1e-12)))}
            scored[key] = dict(gross=x, net=xn)
        else:
            sP = np.where(wP[None, :] & keep16[:, None], c["sign_held"], 0.0).astype(int)
            sL = np.where(wL[None, :] & keep16[:, None], c["sign_held"], 0.0).astype(int)
            gross, cost, sides = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots)
            R55.audit_sign_book(gross, sP, g, upp)
            gb, cb = gross.sum(0), cost.sum(0); xg, xn = gb, gb - cb
            g_cd, c_cd, _ = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, cd_roots)
            gL, _, _ = R55.dollar_book(sL, g, upp, comm_rt, tick_usd, dollar_roots)
            per_root_usd = {r: {"gross": float(gross[i][wP].sum()), "net": float((gross - cost)[i][wP].sum()), "sigma_usd": root_sigma[r],
                                "min_size": size_name[i], "sessions_positioned": int((sP[i] != 0).sum())} for i, r in enumerate(roots) if r in dollar_roots}
            entry = {"gross": R55.stats_block(xg[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "cost_total": float(cb[wP].sum()), "sides_total": int(sides[:, wP].sum()),
                     "roll_sides_total": int((2 * (g["roll"] & (sP != 0)))[:, wP].sum()),
                     "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d"),
                                   "net": R55.stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d net")},
                     "gross_long": R55.stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $"),
                     "per_root_usd": per_root_usd, "untraded_slot": list(R55.DOLLAR_EXCLUDED)}
            scored[key] = dict(gross=xg, net=xn)
        results_cells[name] = entry
        log(f"  {name:20s} gross SR {entry['gross']['sharpe']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}")

    # the dollar book decomposed by root -- BEFORE the component line
    dcell = results_cells["minsize/dollar"]
    pr = dcell["per_root_usd"]; order = sorted(pr, key=lambda r: -pr[r]["gross"]); tot_usd = sum(pr[r]["gross"] for r in pr)
    sig_vals = [pr[r]["sigma_usd"] for r in pr if np.isfinite(pr[r]["sigma_usd"])]
    dollar_decomp = {"per_root_gross_sorted": [(r, pr[r]["gross"], pr[r]["sigma_usd"], pr[r]["min_size"]) for r in order], "book_gross_total": tot_usd,
                     "top_contributor": order[0], "top_contributor_share_of_total": float(pr[order[0]]["gross"] / tot_usd) if tot_usd != 0 else None,
                     "top_contributor_abs_share": float(abs(pr[order[0]]["gross"]) / sum(abs(pr[r]["gross"]) for r in pr)),
                     "sigma_usd_range": [float(min(sig_vals)), float(max(sig_vals))], "sigma_usd_by_root": {r: pr[r]["sigma_usd"] for r in order},
                     "cd_eligible_roots": cd_roots, "untraded_slot": list(R55.DOLLAR_EXCLUDED), "min_size": dict(zip(roots, size_name))}
    log("  dollar book by root (gross $, 2016-2023, sorted): " + ", ".join(f"{r} {pr[r]['gross']:+,.0f}" for r in order))
    log(f"    total {tot_usd:+,.0f}; top contributor {order[0]} share {dollar_decomp['top_contributor_share_of_total']}; sigma/contract/day "
        f"${dollar_decomp['sigma_usd_range'][0]:,.0f}..${dollar_decomp['sigma_usd_range'][1]:,.0f}; C-d-eligible {cd_roots}")
    comp = {"cell": "minsize/dollar", "C_a_net_sharpe": dcell["net"]["sharpe"], "se": dcell["net"]["se"], "gross_sharpe": dcell["gross"]["sharpe"],
            "hit": dcell["net"]["hit"], "C_c_skew": dcell["net"]["skew"], "C_c_pass": bool(dcell["net"]["skew"] >= -0.5),
            "C_d_sigma_usd_day": dcell["net"]["sd_daily"], "C_d_pass": bool(dcell["net"]["sd_daily"] <= R55.C_D_SIGMA),
            "cd_subbook": {"roots": cd_roots, "net_sharpe": dcell["cd_subset"]["net"]["sharpe"], "gross_sharpe": dcell["cd_subset"]["gross"]["sharpe"],
                           "sigma_usd_day": dcell["cd_subset"]["net"]["sd_daily"]},
            "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk",
            "cost_line": "$3 a round trip on a micro, $6 on a full contract, plus one tick crossed; a roll is two sides"}
    log(f"  component line: C-a net {comp['C_a_net_sharpe']:+.3f} (SE {comp['se']:.2f}), gross {comp['gross_sharpe']:+.3f}, hit {comp['hit']:.3f}, "
        f"skew {comp['C_c_skew']:+.2f}, sigma ${comp['C_d_sigma_usd_day']:,.0f}/day; C-d sub-book net {comp['cd_subbook']['net_sharpe']:+.3f}")

    # primary diagnostics: root-months, concentration, per-root, per-year, per-era
    x = scored[PRIMARY_CELL]["gross"]; pos = prim["pos"]
    rm, contrib = root_month_contrib(pos, rsimple, days, wP)
    vals = np.array([v for _, _, v, _ in rm]); legs = np.array([s for _, _, _, s in rm])
    root_month = {"combined": dist_block(vals), "long_leg": dist_block(vals[legs > 0]), "short_leg": dist_block(vals[legs < 0]),
                  "units": "contribution to the book's daily return, summed within the month"}
    conc = concentration(contrib, roots, wP)
    per_root = {}
    for i, r in enumerate(roots):
        xi = contrib[i]; live_i = pos[i] != 0
        per_root[r] = {"total_primary": float(xi[wP].sum()), "total_long_window": float(xi[wL].sum()),
                       "sharpe_primary_when_positioned": R55.sharpe(xi[wP & live_i]) if (wP & live_i).sum() > 60 else None, "sortino_primary_when_positioned": R55.sortino(xi[wP & live_i]) if (wP & live_i).sum() > 60 else None,
                       "months_long_primary": int(sum(1 for i2, _, _, s in rm if i2 == i and s > 0)), "months_short_primary": int(sum(1 for i2, _, _, s in rm if i2 == i and s < 0)),
                       "mean_carry_me": float(np.nanmean(carry_me[i])) if np.isfinite(carry_me[i]).any() else None,
                       "min_size": size_name[i], "sigma_usd_min_size": root_sigma[r]}
    per_year = per_year_sharpe(x, days, wL)
    per_era = {f"{a}..{b}": {"sharpe": R55.sharpe(x[R55.window_mask(days, a, b)]), "sortino": R55.sortino(x[R55.window_mask(days, a, b)]), "n_days": int(R55.window_mask(days, a, b).sum())} for a, b in ERAS}
    log(f"  root-months: combined mean {root_month['combined']['mean']:+.2e} median {root_month['combined']['median']:+.2e} trimmed {root_month['combined']['mean_trimmed_1pct_both']:+.2e}; "
        f"top-1 root {conc['top1_abs_root']} abs share {conc['top1_abs_share']:.3f}; roots to half {conc['roots_to_half_pnl']}")
    log("  per year: " + ", ".join(f"{y} {v['sharpe']:+.2f}" for y, v in per_year.items()))

    # single sorts -- diagnostic, unpromotable, outside the family
    ss = {}
    for nm, sig_me in (("term_structure", carry_me), ("momentum", mom_me)):
        m1 = single_sort(sig_me, elig, roots)
        held = R55.hold_from_month_ends(m1.astype(float), me, T, g["span"])
        xs = R55.book_return(held, rsimple)
        ss[nm] = {"sharpe_primary": R55.sharpe(xs[wP]), "sortino_primary": R55.sortino(xs[wP]), "ann_mean_return": float(xs[wP].mean() * 252), "ann_vol": float(xs[wP].std(ddof=1) * math.sqrt(252)),
                  "max_dd": R55.max_drawdown(xs[wP]), "sharpe_long_window": R55.sharpe(xs[wL]), "sortino_long_window": R55.sortino(xs[wL]),
                  "rho_daily_with_primary": float(np.corrcoef(xs[wP], x[wP])[0, 1]), "per_year": per_year_sharpe(xs, days, wL),
                  "legs": "long the top ceil(n/3), short the bottom ceil(n/3), same eligibility, ties by root symbol",
                  "months_positioned_primary": int(sum(1 for k in me_in_P if (m1[:, k] != 0).any()))}
        scored[("single", nm)] = xs
    ss["rho_between_single_sorts"] = float(np.corrcoef(scored[("single", "term_structure")][wP], scored[("single", "momentum")][wP])[0, 1])
    log(f"  single sorts (diagnostic): term-structure SR {ss['term_structure']['sharpe_primary']:+.6f}, momentum SR {ss['momentum']['sharpe_primary']:+.6f}; "
        f"rho with primary {ss['term_structure']['rho_daily_with_primary']:+.3f} / {ss['momentum']['rho_daily_with_primary']:+.3f}")

    # nulls: exactness guard, corner preservation, timing, enumeration
    live_idx = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    if not all(np.array_equal(live_idx[0], ix) for ix in live_idx[1:]):
        raise AssertionError("the 17 roots do not share one span on the primary window; corner sizes would not be preserved")
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    Tw = int(wP.sum()); idx0 = live_idx[0]
    base = null_cells[PRIMARY_CELL]["sign_held"]; nL0, nS0 = (base > 0).sum(0)[idx0], (base < 0).sum(0)[idx0]
    t0 = time.time()
    for k in GUARD_OFFSETS:
        k = k % (Tw - 1) or 1
        s_rot = R55.rotate_signs(base, live_idx, k)
        p = s_rot * prim["scale_held"]
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"enumeration is not bit-identical to the loop at offset {k}")
        if not (np.array_equal((s_rot > 0).sum(0)[idx0], np.roll(nL0, k % idx0.size)) and np.array_equal((s_rot < 0).sum(0)[idx0], np.roll(nS0, k % idx0.size))):
            raise AssertionError(f"corner sizes not preserved under rotation at offset {k}")
        for key in null_cells:
            if key == PRIMARY_CELL:
                continue
            c = null_cells[key]; sr = R55.rotate_signs(c["sign_held"], live_idx, k)
            if c["book"] == "published":
                R55.book_return(sr * c["scale_held"], rsimple)
            else:
                gg, cc, _ = R55.dollar_book(np.sign(sr).astype(int), g, upp, comm_rt, tick_usd, dollar_roots); (gg - cc).sum(0)
    per_offset = (time.time() - t0) / len(GUARD_OFFSETS); projected = per_offset * (Tw - 1)
    log(f"  exactness guard: {len(GUARD_OFFSETS)} offsets bit-identical against the plain loop; corner sizes preserved\n"
        f"  timing: {per_offset * 1e3:.1f} ms per offset (all 3 cells) -> projected {projected:.0f} s for {Tw - 1} offsets")
    if projected > 15 * 60:
        raise AssertionError(f"projected null wall {projected:.0f}s exceeds 15 minutes; stopping as pre-registered")
    log(f"  enumerating N1/N2 over {Tw - 1} offsets x {len(cells)} cells, purge {R55.NULL_PURGE} ...")
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    names = [f"{a}/{b}" for a, b in keys]
    obs = np.array([results_cells[nm]["gross"]["sharpe"] if b == "published" else results_cells[nm]["net"]["sharpe"] for nm, (a, b) in zip(names, keys)])
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= Tw - R55.NULL_PURGE); null = null_all[keep]
    jP = keys.index(PRIMARY_CELL)
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(null.shape[0]), "per_cell": {},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_all[:, jP].tolist(), "sortino": null_s[:, jP].tolist()}}
    for j, nm in enumerate(names):
        col = null[:, j]
        n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)),
                              "p95": float(np.percentile(col, 95)), "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95)),
                              "sortino": R55.sortino_null_block(scored[keys[j]]["gross" if keys[j][1] == "published" else "net"][wP], null_s[:, j], keep)}
    fam = null.max(1)
    n2 = {"observed_best": float(obs.max()), "observed_best_cell": names[int(obs.argmax())], "p50": float(np.percentile(fam, 50)),
          "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95))}
    primary = n1["per_cell"]["ew/published"]
    log(f"  N1 primary: observed {primary['observed']:+.3f}  p05 {primary['p05']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f}\n"
        f"  N2 family: best {n2['observed_best']:+.3f} ({n2['observed_best_cell']})  p50 {n2['p50']:+.3f}  p95 {n2['p95']:+.3f}")

    # AMENDMENT, made on the first run and recorded in the RESULT: the pre-registered eligibility rule
    # (tot12 - tot1 finite, both through D555's signal function) inherits D555's per-12-month count floor
    # as a 20-return floor on the 1-month cell, and a 19-session calendar month (April 2017, April 2023
    # for every root; most months for livestock, many for the grains, which trade ~243 sessions a year
    # against energy's 258) makes a name ineligible on calendar length, not on its signal. The primary
    # above IS the pre-registered rule and stands; this block re-runs the family with the plain
    # calendar-month sum (no floor) so eligibility is exactly "the 12-month cell is finite". It is a
    # diagnostic, UNPROMOTABLE, outside the declared family and outside the verdict.
    log("  AMENDMENT (diagnostic): eligibility with an unfloored 1-month cell ...")
    momA = momentum_12_1_unfloored(g, me); eligA = np.isfinite(momA) & np.isfinite(carry_me)
    memA, diagA = double_sort(momA, carry_me, roots)
    if not np.array_equal(memA, membership_pandas(momA, carry_me, roots)):
        raise AssertionError("amendment: runner and pandas memberships disagree")
    signA_ew = R55.hold_from_month_ends(memA.astype(float), me, T, g["span"])
    shA, posA_v, scA, sdA = R56.positions_from_signs(memA.astype(float), sig, me, g)
    cellsA = {("ew", "published"): dict(book="published", sign_held=signA_ew, scale_held=scale_ew, pos=signA_ew),
              ("volscaled", "published"): dict(book="published", sign_held=shA, scale_held=scA, pos=posA_v),
              ("minsize", "dollar"): dict(book="dollar", sign_held=sdA.astype(float), scale_held=None, pos=None)}
    amend = {"note": "UNPROMOTABLE diagnostic; not the pre-registered rule; recorded because the pre-registered 20-return floor on the 1-month cell excluded root-months on calendar length",
             "rule": "tot12 (D555 floor, live at m) minus the plain calendar-month sum with no count floor; eligible iff the 12-month cell and the carry are finite",
             "cells": {}, "single_sort_check": {}}
    xA = {}
    for key in CELL_KEYS:
        c = cellsA[key]; cell, book = key; nm = f"{cell}/{book}"
        if book == "published":
            xg = R55.book_return(c["pos"], rsimple); turn, _, _ = R55.published_cost(c["pos"], cbp, g["roll"]); xn = xg - turn
        else:
            sPA = np.where(wP[None, :] & keep16[:, None], c["sign_held"], 0.0).astype(int)
            gr, co, _ = R55.dollar_book(sPA, g, upp, comm_rt, tick_usd, dollar_roots); xg, xn = gr.sum(0), (gr - co).sum(0)
        xA[key] = xg
        amend["cells"][nm] = {"gross_sharpe": R55.sharpe(xg[wP]), "gross_sortino": R55.sortino(xg[wP]), "net_sharpe": R55.sharpe(xn[wP]), "net_sortino": R55.sortino(xn[wP]), "gross_se": R55.block_boot_se(xg[wP], dP_days),
                              "ann_vol": float(xg[wP].std(ddof=1) * math.sqrt(252)), "gross_sharpe_long_window": R55.sharpe(xg[wL]), "gross_sortino_long_window": R55.sortino(xg[wL])}
    inA = [row for row in diagA if row["k"] in me_in_P]
    amend["month_end_summary"] = {"flat_months_primary": int(sum(r["flat"] for r in inA)), "n_eligible_min": int(min(r["n_eligible"] for r in inA)),
                                  "n_eligible_median": float(np.median([r["n_eligible"] for r in inA])), "n_eligible_max": int(max(r["n_eligible"] for r in inA)),
                                  "corner_sizes_counts": {str(k): int(v) for k, v in pd.Series([f"{r['n_long']}/{r['n_short']}" for r in inA if not r["flat"]]).value_counts().items()},
                                  "root_months_missing_momentum": int(sum(len(r["missing_momentum"]) for r in inA)), "boundary_ties_total": int(sum(r["boundary_ties"] for r in inA)),
                                  "membership_cells_changed_vs_preregistered": int((memA[:, me_in_P] != mem[:, me_in_P]).sum())}
    for nm, sig_me in (("term_structure", carry_me), ("momentum", momA)):
        held = R55.hold_from_month_ends(single_sort(sig_me, eligA, roots).astype(float), me, T, g["span"]); xs = R55.book_return(held, rsimple)
        amend["single_sort_check"][nm] = {"sharpe_primary": R55.sharpe(xs[wP]), "sortino_primary": R55.sortino(xs[wP]), "ann_vol": float(xs[wP].std(ddof=1) * math.sqrt(252)),
                                          "rho_daily_with_amended_primary": float(np.corrcoef(xs[wP], xA[PRIMARY_CELL][wP])[0, 1])}
    nullA_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cellsA.items()}
    nullA, keysA = R55.enumerate_null(nullA_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, lambda *_: None)
    nullA = nullA[keep]
    obsA = np.array([amend["cells"][f"{a}/{b}"]["gross_sharpe"] if b == "published" else amend["cells"][f"{a}/{b}"]["net_sharpe"] for a, b in keysA])
    amend["null_n1"] = {f"{a}/{b}": {"observed": float(obsA[j]), "p05": float(np.percentile(nullA[:, j], 5)), "p50": float(np.percentile(nullA[:, j], 50)),
                                     "p95": float(np.percentile(nullA[:, j], 95)), "pct_rank": float((nullA[:, j] < obsA[j]).mean())} for j, (a, b) in enumerate(keysA)}
    famA = nullA.max(1)
    amend["null_n2"] = {"observed_best": float(obsA.max()), "p50": float(np.percentile(famA, 50)), "p95": float(np.percentile(famA, 95)), "pct_rank": float((famA < obsA.max()).mean())}
    amend["rho_daily_amended_vs_preregistered_primary"] = float(np.corrcoef(xA[PRIMARY_CELL][wP], x[wP])[0, 1])
    pA = amend["null_n1"]["ew/published"]
    log(f"    amended primary gross SR {pA['observed']:+.3f}  N1 p50 {pA['p50']:+.3f} p95 {pA['p95']:+.3f} rank {pA['pct_rank']:.3f}; flat months {amend['month_end_summary']['flat_months_primary']}, "
        f"n_eligible {amend['month_end_summary']['n_eligible_min']}..{amend['month_end_summary']['n_eligible_max']}; single sorts "
        f"{amend['single_sort_check']['term_structure']['sharpe_primary']:+.3f} / {amend['single_sort_check']['momentum']['sharpe_primary']:+.3f}; "
        f"rho with the pre-registered primary {amend['rho_daily_amended_vs_preregistered_primary']:+.3f}")

    # predictions
    cE = results_cells["ew/published"]
    sr_ds, mu_ds, vol_ds = cE["gross"]["sharpe"], cE["ann_mean_return"], cE["gross"]["ann_vol"]
    best = max(("term_structure", "momentum"), key=lambda nm: ss[nm]["sharpe_primary"])
    sr_b, mu_b, vol_b = ss[best]["sharpe_primary"], ss[best]["ann_mean_return"], ss[best]["ann_vol"]
    sharpe_uplift = sr_ds - sr_b; mean_uplift_in_best_vol = (mu_ds - mu_b) / vol_b
    preds = {
        "P-1": {"claim": "primary > 0 and above N1 p95; gross point range 0.28-0.45 (deposit net 0.25-0.40 + turnover drag)", "value": sr_ds, "p95": primary["p95"],
                "holds": bool(sr_ds > 0 and primary["clears_p95"]), "in_point_range": bool(POINT_RANGE_GROSS[0] <= sr_ds <= POINT_RANGE_GROSS[1]),
                "gross_minus_net_actual": float(cE["gross"]["sharpe"] - cE["net"]["sharpe"])},
        "P-2": {"claim": "Sharpe uplift over the better single sort < mean-return uplift in that sort's vol units", "better_single_sort": best,
                "sharpe_uplift": float(sharpe_uplift), "mean_return_uplift_ann": float(mu_ds - mu_b), "mean_uplift_in_best_vol_units": float(mean_uplift_in_best_vol),
                "holds": bool(sharpe_uplift < mean_uplift_in_best_vol)},
        "P-3": {"claim": "double sort ann. vol > both single sorts' ann. vol", "vol_double": vol_ds, "vol_term_structure": ss["term_structure"]["ann_vol"],
                "vol_momentum": ss["momentum"]["ann_vol"], "holds": bool(vol_ds > ss["term_structure"]["ann_vol"] and vol_ds > ss["momentum"]["ann_vol"])},
        "P-4": {"claim": "top-1 root abs share of the primary's P&L > 30%", "value": conc["top1_abs_share"], "root": conc["top1_abs_root"],
                "share_of_total_d555_style": conc["top1_share_of_total"], "holds": bool(conc["top1_abs_share"] > 0.30)},
        "P-5": {"claim": "daily rho with each single sort > 0.4", "rho_term_structure": ss["term_structure"]["rho_daily_with_primary"], "rho_momentum": ss["momentum"]["rho_daily_with_primary"],
                "holds": bool(ss["term_structure"]["rho_daily_with_primary"] > 0.4 and ss["momentum"]["rho_daily_with_primary"] > 0.4)},
        "P-6": {"claim": "the 16-root dollar book fails C-d (daily sigma > $500)", "sigma_usd_day": comp["C_d_sigma_usd_day"], "holds": bool(comp["C_d_sigma_usd_day"] > R55.C_D_SIGMA)},
        "P-7": {"claim": "falsifier: gates green and primary below N1 p50 -> the sort did badly on this window",
                "gates_green": bool(all(v is True for k, v in audits.items() if "raises_on" in k)), "primary_below_p50": bool(sr_ds < primary["p50"]),
                "holds": bool(all(v is True for k, v in audits.items() if "raises_on" in k) and sr_ds < primary["p50"])},
    }
    verdict = "PASS" if (sr_ds > 0 and primary["clears_p95"] and n2["clears_p95"]) else "DOES NOT PASS"
    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS in this file are NEGATIVE: minimum of (cumulative daily return - running peak); "
                                                                  "return units for the published books, dollars at minimum size for the dollar books (D542).", "record": "D542"},
           "spec": "D559", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "curve_sha256": R55.sha256(R56.CURVE), "strip_sha256": R55.sha256(R56.STRIP),
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "last_session_read": last_session_read,
                       "sessions_primary": int(wP.sum()), "sessions_grid": int(T), "month_ends": int(len(me))},
           "universe": {"roots": roots, "n": n, "dollar_roots": dollar_roots, "untraded_slot": list(R55.DOLLAR_EXCLUDED), "min_eligible": MIN_ELIGIBLE,
                        "tie_rule": "(-signal, root symbol): ties rank the alphabetically earlier root higher", "ffill_sessions": R56.FFILL_SESSIONS},
           "cells": results_cells, "primary": primary, "null_n1": n1, "null_n2": n2, "month_end_table": me_table, "month_end_summary": me_summary,
           "root_month": root_month, "concentration": conc, "per_root": per_root, "per_year": per_year, "per_era": per_era,
           "single_sort_check": ss, "dollar_book": dollar_decomp, "component_line": comp, "predictions": preds, "verdict": {"declared": verdict},
           "amendment_unfloored_1m": amend,
           "audits": audits, "timing": {"wall_s": round(time.time() - t_start, 1), "null_ms_per_offset": round(per_offset * 1e3, 1), "null_projected_s": round(projected, 1)}}
    _guard_required(res)
    OUT.write_text(json.dumps(res, indent=1, default=R55._json_default), encoding="utf-8")
    log(f"\n  VERDICT {verdict}   -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test -- synthetic grids, no fixture read, no cell scored
# --------------------------------------------------------------------------------------------
def _expect_raise(fn, what):
    try:
        fn()
    except AssertionError:
        return True
    raise RuntimeError(f"{what} did not raise")


def selftest() -> int:
    print("D559 SELF-TEST -- synthetic grids, no fixture read, no cell scored\n")
    rng = np.random.default_rng(559)
    roots = list(CM_ROOTS); n = len(roots)
    days = pd.bdate_range("2011-06-01", "2014-12-31").strftime("%Y-%m-%d").to_numpy(); T = len(days)
    rlog = 0.012 * rng.standard_normal((n, T)); rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool); close = np.exp(np.nancumsum(rlog, 1)) * 60.0
    dP = np.diff(close, axis=1, prepend=np.nan); roll = np.zeros((n, T), dtype=bool); roll[:, 200] = True; roll[5, 500] = True
    g = dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=live.copy(), nonpositive=[])
    me = R55.month_ends(days); K = len(me)

    # [1] the sort on a hand-built month: momentum 17..1 in alphabetical order, carry chosen so the corners are known
    mom = np.arange(n, 0, -1, dtype=float)[:, None]                       # BZ(0) highest ... ZW lowest
    carry = np.zeros((n, 1)); carry[:6, 0] = [0.1, 0.5, 0.3, 0.9, 0.2, 0.7]; carry[11:, 0] = [-0.1, -0.9, -0.3, -0.2, -0.8, -0.5]
    mem, diag = double_sort(mom, carry, roots)
    exp_long = {roots[3], roots[5]}; exp_short = {roots[12], roots[15]}
    assert set(diag[0]["long"]) == exp_long and set(diag[0]["short"]) == exp_short, (diag[0]["long"], diag[0]["short"])
    assert (diag[0]["n_top"], diag[0]["n_mid"], diag[0]["n_bottom"], diag[0]["n_long"], diag[0]["n_short"]) == (6, 5, 6, 2, 2)
    assert np.array_equal(mem, membership_pandas(mom, carry, roots))
    # ties: every signal equal -> alphabetical terciles and alphabetical corners
    memt, dt = double_sort(np.ones((n, 1)), np.ones((n, 1)), roots)
    assert dt[0]["long"] == roots[:2] and dt[0]["short"] == roots[15:17] and dt[0]["boundary_ties"] == 4
    assert np.array_equal(memt, membership_pandas(np.ones((n, 1)), np.ones((n, 1)), roots))
    # 5-name tercile (n = 16 -> 6/4/6) and n = 9 -> 3/3/3 -> 1/1; n = 8 -> flat
    m16 = mom.copy(); m16[0, 0] = np.nan; _, d16 = double_sort(m16, carry, roots)
    assert (d16[0]["n_top"], d16[0]["n_mid"], d16[0]["n_bottom"], d16[0]["n_long"], d16[0]["n_short"]) == (6, 4, 6, 2, 2)
    m9 = np.full((n, 1), np.nan); m9[:9, 0] = np.arange(9, 0, -1); _, d9 = double_sort(m9, carry, roots)
    assert (d9[0]["n_top"], d9[0]["n_mid"], d9[0]["n_bottom"], d9[0]["n_long"], d9[0]["n_short"]) == (3, 3, 3, 1, 1) and d9[0]["missing_momentum"] == roots[9:]
    m8 = m9.copy(); m8[8, 0] = np.nan; mem8, d8 = double_sort(m8, carry, roots)
    assert d8[0]["flat"] and d8[0]["flat_reason"] == "fewer_than_9_eligible" and (mem8 == 0).all()
    assert (membership_pandas(m8, carry, roots) == 0).all()
    print("  [1] the sort: known corners on a hand-built month (6/5/6 -> 2/2), alphabetical ties (4 boundary ties counted), 16 -> 6/4/6, 9 -> 3/3/3 -> 1/1, 8 -> flat; pandas agrees on all")

    # [2] synthetic month-end signals over the whole grid: numpy and pandas memberships agree; the corner audit RAISES on a swapped pair
    mom_me, _ = momentum_12_1(g, me)
    C = np.cumsum(0.02 * rng.standard_normal((n, T)), axis=1); C[:, ::7] = np.nan
    carry_me = R56.carry_at_month_ends(C, live, me)
    mem, diag = double_sort(mom_me, carry_me, roots); mem_pd = membership_pandas(mom_me, carry_me, roots)
    checked = audit_corner_membership(mem, mem_pd, me, days)
    k_sw = next(k for k in range(K) if (mem[:, k] > 0).any() and (mem[:, k] < 0).any())
    bad = mem.copy(); iL = int(np.flatnonzero(mem[:, k_sw] > 0)[0]); iS = int(np.flatnonzero(mem[:, k_sw] < 0)[0]); bad[iL, k_sw], bad[iS, k_sw] = -1, 1
    _expect_raise(lambda: audit_corner_membership(bad, mem_pd, me, days), "corner audit on a swapped pair")
    n_traded = sum(1 for r in diag if not r["flat"])
    momU = momentum_12_1_unfloored(g, me); _, t12 = R55.signal_at_month_ends(rlog, live, days, me, 12)
    both = np.isfinite(mom_me) & np.isfinite(momU)
    assert np.array_equal(np.isfinite(momU), np.isfinite(t12)) and np.allclose(momU[both], mom_me[both]) and np.isfinite(momU).sum() >= np.isfinite(mom_me).sum()
    print(f"  [2] corner-membership audit passes {checked} positioned cells over {n_traded} traded month-ends and RAISES on one long/short pair swapped at one month-end; "
          f"the unfloored 12-1 momentum is finite exactly where the 12-month cell is and equals the floored one where both exist")

    # [3] lag audit on the held EW grid; RAISES on the unlagged grid
    sign_ew = R55.hold_from_month_ends(mem.astype(float), me, T, g["span"])
    held_cells = R55.audit_lag(sign_ew, mem_pd.astype(float), me, g["span"], T)
    unl = unlagged_grid(mem, me, g["span"])
    _expect_raise(lambda: R55.audit_lag(unl, mem_pd.astype(float), me, g["span"], T), "lag audit on the unlagged grid")
    rs = np.where(np.isfinite(rlog), np.expm1(np.nan_to_num(rlog)), 0.0)
    assert not np.allclose(R55.book_return(sign_ew, rs), R55.book_return(unl, rs))
    print(f"  [3] lag audit passes {held_cells} held cells against the independent pandas membership and RAISES on the unlagged grid; the two P&Ls differ")

    # [4] right-quantity audit; RAISES on a daily grid
    ch = R55.audit_right_quantity(sign_ew, me, T)
    _expect_raise(lambda: R55.audit_right_quantity(np.sign(np.nan_to_num(C)), me, T), "right-quantity audit on a daily grid")
    print(f"  [4] right-quantity audit passes ({ch} changes, all on the session after a month-end) and RAISES on a daily grid")

    # [5] sign audit in money on the dollar book's gross grid; RAISES on the negated and on the mis-lagged grid
    upp = np.full(n, 10.0); tick = np.full(n, 1.0); comm = np.full(n, 6.0)
    sd = R55.hold_from_month_ends(mem, me, T, g["span"]).astype(int)
    gross, _, _ = R55.dollar_book(sd, g, upp, comm, tick, roots)
    chk = R55.audit_sign_in_money(gross, sd, g, upp)
    _expect_raise(lambda: R55.audit_sign_in_money(-gross, sd, g, upp), "sign audit on the negated grid")
    g_lag = R55.dollar_book(sd, dict(g, dP=np.roll(dP, 1, axis=1)), upp, comm, tick, roots)[0]
    _expect_raise(lambda: R55.audit_sign_in_money(g_lag, sd, g, upp), "sign audit on the mis-lagged grid")
    print(f"  [5] sign audit in money passes on {chk} roots' best days and RAISES on the negated grid and on the mis-lagged (dP rolled one session) grid")

    # [6] carry-from-strip audit on the month-end carry SIGN; RAISES on the negated sign
    rows = []; front = {}
    for t, d in enumerate(days):
        for i, r in enumerate(roots):
            if not np.isfinite(C[i, t]):
                continue
            f, nx = (f"{r}H3", f"{r}M3") if d < "2013-03-01" else (f"{r}Z4", f"{r}H5")
            rows.append((r, f, d, 100.0)); rows.append((r, nx, d, 100.0 / (1 + C[i, t] * 3 / 12))); front[(r, d)] = f
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    csign = np.where(np.isfinite(carry_me), np.sign(carry_me), 0.0)
    kc = R56.audit_carry_from_strip(csign, me, g, strip, front, n_check=40)
    _expect_raise(lambda: R56.audit_carry_from_strip(-csign, me, g, strip, front, n_check=10), "carry audit on the negated sign")
    print(f"  [6] carry-from-strip audit passes {kc} month-end cells and RAISES on the negated sign grid")

    # [7] the null: rotation with the span scale preserves the corner sizes and is bit-identical to the loop
    w = np.ones(T, dtype=bool); live_idx = [np.flatnonzero(live[i] & w) for i in range(n)]
    nL0, nS0 = (sign_ew > 0).sum(0), (sign_ew < 0).sum(0)
    for k in (1, 17, 250, 400):
        sr = R55.rotate_signs(sign_ew, live_idx, k); p = sr * live.astype(float)
        assert np.array_equal(R55.book_return(p, rs), R55.book_return_loop(p, rs))
        assert np.array_equal((sr > 0).sum(0), np.roll(nL0, k)) and np.array_equal((sr < 0).sum(0), np.roll(nS0, k))
    p_bad = R55.rotate_signs(sign_ew, live_idx, 17) * (sign_ew != 0)        # the in-place membership mask would NOT preserve them
    assert not np.array_equal((p_bad > 0).sum(0), np.roll(nL0, 17))
    print("  [7] rotation with scale = 1.0 on the span preserves the long and short corner sizes at every offset and matches the plain loop bit for bit; the in-place membership mask would not")

    # [8] the single sorts under the same rule; the REQUIRED_OUTPUTS guard fires
    elig = np.isfinite(mom_me) & np.isfinite(carry_me)
    ms = single_sort(mom_me, elig, roots); ts = single_sort(carry_me, elig, roots)
    for k in range(K):
        if elig[:, k].sum() >= MIN_ELIGIBLE:
            nl = math.ceil(elig[:, k].sum() / 3)
            assert (ms[:, k] > 0).sum() == nl and (ms[:, k] < 0).sum() == nl and (ts[:, k] > 0).sum() == nl
            assert set(np.flatnonzero(mem[:, k] > 0)) <= set(np.flatnonzero(ms[:, k] > 0)), "a long corner name must sit in the momentum top tercile"
            assert set(np.flatnonzero(mem[:, k] < 0)) <= set(np.flatnonzero(ms[:, k] < 0))
        else:
            assert (ms[:, k] == 0).all() and (ts[:, k] == 0).all()
    _expect_raise(lambda: _guard_required({"max_drawdown_convention": {}, "spec": "D559"}), "REQUIRED_OUTPUTS guard")
    _expect_raise(lambda: _guard_required({k: None for k in ["spec"] + REQUIRED_OUTPUTS}), "first-key guard")
    print("  [8] single sorts: ceil(n/3) a leg on the same eligibility, and every double-sort corner sits inside its momentum tercile; the REQUIRED_OUTPUTS and first-key guards RAISE")
    print("\n  ALL SELF-TESTS PASSED. No fixture was read and no cell was scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); gq = ap.add_mutually_exclusive_group(required=True)
    gq.add_argument("--run", action="store_true"); gq.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (0 if run() else 1))
