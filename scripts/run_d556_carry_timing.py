"""D556 -- carry timing AS PUBLISHED (Koijen, Moskowitz, Pedersen & Vrugt 2018) on the 36-root breadth
fixture, off the settlement-strip fixture, with the trend + carry combination.

Spec committed in 60ec9f6 BEFORE the fixture builder and this file (R8). Primary window
2016-01-04..2023-12-29; long window 2011-01-03..2023-12-29 as a declared diagnostic; the 2024+ slice
is RESERVED AND NOT READ. Nothing admitted (R15).

    uv run python scripts/run_d556_carry_timing.py --selftest
    uv run python scripts/run_d556_carry_timing.py --run        # -> data/d556_carry_timing.json

Everything not carry-specific is imported from run_d555_tsmom_replication.py: the return grids, the
EW volatility, the month-end holds, the book return, the dollar book, the three audits, the
enumerated sign rotation and its purge. Cells: A carry sign (primary), B carry demeaned by the
root's own expanding month-end mean, C (sign_trend12 + sign_carry)/2 -- each as the published
return-space book and as the dollar book at minimum size. One new audit: the carry sign at every
month-end is recomputed from the RAW strip by a path that never reads the derived curve table.
"""
from __future__ import annotations

import argparse
import hashlib
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


R55 = _load("d555", "run_d555_tsmom_replication.py")
FB = _load("fut_strip", "build_fut_settle_strip.py")

CURVE = REPO / "data" / "fixtures" / "fut_curve_front_next.csv.gz"
STRIP = REPO / "data" / "fixtures" / "fut_settle_strip.csv.gz"
OUT = REPO / "data" / "d556_carry_timing.json"
SPEC = "60ec9f6"
PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
FFILL_SESSIONS = 5             # a month-end on a no-settlement session reads the last settlement within 5 sessions
DEMEAN_MIN_MONTHS = 12
CELLS = ["A", "B", "C"]
PRIMARY_CELL = ("A", "published")
D555_TREND_SHARPE = 0.304      # D555's primary, for P-3
REQUIRED_OUTPUTS = ["spec", "commit", "fixture_sha256", "curve_sha256", "strip_sha256", "windows", "cells", "primary",
                    "null_n1", "null_n2", "per_root", "per_sector", "per_era", "per_year", "carry_state", "trend_relation",
                    "dollar_book", "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# carry at the month-ends
# --------------------------------------------------------------------------------------------
def carry_grid(g, curve: pd.DataFrame) -> np.ndarray:
    """carry_ann per (root, session) on the breadth grid; NaN where the root has no front/next settlement."""
    n, T = g["rlog"].shape
    day_ix = {d: i for i, d in enumerate(g["days"])}
    root_ix = {r: i for i, r in enumerate(g["roots"])}
    C = np.full((n, T), np.nan)
    c = curve[curve["ref"].isin(day_ix)]
    for r, ref, v in zip(c["root"], c["ref"], c["carry_ann"]):
        if r in root_ix and np.isfinite(v):
            C[root_ix[r], day_ix[ref]] = v
    return C


def carry_at_month_ends(C: np.ndarray, live: np.ndarray, me: np.ndarray) -> np.ndarray:
    """Implementation A (numpy): the last finite carry within FFILL_SESSIONS sessions ending at the
    month-end, NaN otherwise or when the root is not live at the month-end."""
    n = C.shape[0]
    out = np.full((n, len(me)), np.nan)
    for k, m in enumerate(me):
        lo = max(0, m - FFILL_SESSIONS + 1)
        win = C[:, lo:m + 1]
        fin = np.isfinite(win)
        has = fin.any(1)
        last = win.shape[1] - 1 - np.argmax(fin[:, ::-1], axis=1)
        v = np.where(has, win[np.arange(n), np.clip(last, 0, None)], np.nan)
        out[:, k] = np.where(live[:, m], v, np.nan)
    return out


def carry_at_month_ends_pandas(C: np.ndarray, live: np.ndarray, days: np.ndarray, roots, me: np.ndarray) -> np.ndarray:
    """Implementation B (pandas): per root, ffill(limit=FFILL_SESSIONS-1) then read the month-end date."""
    idx = pd.to_datetime(days)
    out = np.full((len(roots), len(me)), np.nan)
    for i in range(len(roots)):
        s = pd.Series(C[i], index=idx).ffill(limit=FFILL_SESSIONS - 1)
        for k, m in enumerate(me):
            if live[i, m]:
                out[i, k] = s.iloc[m]
    return out


def cell_signs(carry_me: np.ndarray, trend12_me: np.ndarray, live_start_k: np.ndarray):
    """A: sign(carry). B: sign(carry - expanding mean of the root's own month-end carry from its live
    start, after DEMEAN_MIN_MONTHS observations). C: (sign_trend12 + sign_A) / 2 -- an ensemble as in
    D555, in {-1, -0.5, 0, +0.5, +1}."""
    A = np.where(np.isfinite(carry_me), np.sign(carry_me), 0.0)
    n, K = carry_me.shape
    B = np.zeros((n, K))
    for i in range(n):
        cnt = 0; tot = 0.0
        for k in range(K):
            v = carry_me[i, k]
            if not np.isfinite(v):
                continue
            cnt += 1; tot += v
            if cnt >= DEMEAN_MIN_MONTHS:
                B[i, k] = np.sign(v - tot / cnt)
    Cc = (trend12_me.astype(float) + A) / 2.0
    Cc = np.where((trend12_me != 0) & (A != 0), Cc, np.where((trend12_me == 0) & (A == 0), 0.0, Cc))
    return {"A": A, "B": B, "C": Cc}


def positions_from_signs(avg_me: np.ndarray, sig: np.ndarray, me: np.ndarray, g):
    T = g["rlog"].shape[1]
    scale_me = np.where(np.isfinite(sig[:, me]) & (sig[:, me] > 0), R55.VOL_TARGET / sig[:, me], 0.0)
    sign_held = R55.hold_from_month_ends(avg_me, me, T, g["span"])
    pos_pub = R55.hold_from_month_ends(avg_me * scale_me, me, T, g["span"])
    scale_held = R55.hold_from_month_ends(scale_me, me, T, g["span"])
    sign_dollar = R55.hold_from_month_ends(np.sign(avg_me).astype(int), me, T, g["span"])
    return sign_held, pos_pub, scale_held, sign_dollar


# --------------------------------------------------------------------------------------------
# the new audit: the carry sign from the RAW strip, never the derived table
# --------------------------------------------------------------------------------------------
def audit_carry_from_strip(signA_me, me, g, strip: pd.DataFrame, breadth_front: dict, n_check=400, seed=7):
    """For a random sample of (root, month-end) cells with a non-zero sign, rebuild sign(F_front - F_next)
    from the strip rows of the session the sign was read on (the month-end or one of the 4 sessions
    before it, whichever last carried the front's settlement). Raises on any disagreement."""
    rng = np.random.default_rng(seed)
    cells = np.argwhere(signA_me != 0)
    pick = cells[rng.choice(len(cells), size=min(n_check, len(cells)), replace=False)]
    by = {k: v for k, v in strip.groupby(["root", "ref"], sort=False)}
    checked = 0
    for i, k in pick:
        r = g["roots"][i]; m = me[k]
        found = False
        for t in range(m, max(-1, m - FFILL_SESSIONS), -1):
            ref = g["days"][t]
            front = breadth_front.get((r, ref))
            grp = by.get((r, ref))
            if front is None or grp is None:
                continue
            gf = grp[grp["contract"] == front]
            if not len(gf):
                continue
            fy = FB.ym(front, ref)
            later = [(FB.ym(c, ref), s) for c, s in zip(grp["contract"], grp["settle"]) if FB.ym(c, ref) is not None and FB.ym(c, ref) > fy]
            if not later:
                continue
            nxt = min(later)
            want = np.sign(float(gf["settle"].iloc[0]) - nxt[1])
            if want != signA_me[i, k]:
                raise AssertionError(f"CARRY AUDIT: {r} at {g['days'][m]}: strip says {want:+.0f}, grid says {signA_me[i, k]:+.0f}")
            found = True; checked += 1
            break
        if not found:
            raise AssertionError(f"CARRY AUDIT: {r} at {g['days'][m]} has a sign but no strip row within {FFILL_SESSIONS} sessions")
    return checked


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def min_size(g, roots):
    meta = json.loads(R55.META.read_text(encoding="utf-8")); specs = json.loads(R55.SPECS.read_text(encoding="utf-8"))
    n = len(roots); upp = np.zeros(n); tick_usd = np.zeros(n); comm_rt = np.zeros(n); size_name = []
    for i, r in enumerate(roots):
        sp = meta["specs"][r]; full_upp = sp["tick_usd_full_contract"] / sp["tick_price_units"]
        if r in R55.MICRO_OF:
            if R55.MICRO_OF[r] in specs:
                m = specs[R55.MICRO_OF[r]]; upp[i] = m["usd_per_point"]; tick_usd[i] = m["tick_usd"]
            else:
                upp[i] = sp["tick_usd"] / sp["tick_price_units"]; tick_usd[i] = sp["tick_usd"]
            comm_rt[i] = R55.COMMISSION_RT["micro"]; size_name.append(R55.MICRO_OF[r])
        else:
            upp[i] = full_upp; tick_usd[i] = sp["tick_usd"]; comm_rt[i] = R55.COMMISSION_RT["full"]; size_name.append(r)
    return upp, tick_usd, comm_rt, size_name


def run(log=print):
    t_start = time.time()
    log(f"D556 -- carry timing as published, 36 roots\n      spec {SPEC} committed BEFORE the fixture and this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    for p in (CURVE, STRIP):
        meta = json.loads(p.with_suffix("").with_suffix(".meta.json").read_text(encoding="utf-8"))
        if not meta.get("all_gates_pass"):
            raise AssertionError(f"{p.name}: gates have not passed")
    df = R55.load_fixture(); live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start)
    roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    me = R55.month_ends(days); sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    curve = pd.read_csv(CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    curve = curve[curve["ref"] < RESERVED_FROM]
    strip = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[strip["ref"] < RESERVED_FROM]
    C = carry_grid(g, curve)
    log(f"  carry present on {np.isfinite(C)[g['live']].mean():.3%} of live sessions")
    carry_me = carry_at_month_ends(C, g["live"], me)
    carry_me_pd = carry_at_month_ends_pandas(C, g["live"], days, roots, me)
    if not np.array_equal(np.nan_to_num(carry_me, nan=-1e9), np.nan_to_num(carry_me_pd, nan=-1e9)):
        raise AssertionError("month-end carry: numpy and pandas paths disagree")
    trend12_me, _ = R55.signal_at_month_ends(g["rlog"], g["live"], days, me, 12)
    signs = cell_signs(carry_me, trend12_me, None)
    upp, tick_usd, comm_rt, size_name = min_size(g, roots)
    dollar_roots = [r for r in roots if r not in R55.DOLLAR_EXCLUDED]

    # audits
    audits = {}
    breadth_front = {(r, d): f for r, d, f in zip(curve["root"], curve["ref"], curve["front"])}
    audits["carry_from_strip_cells_checked"] = audit_carry_from_strip(signs["A"], me, g, strip, breadth_front)
    try:
        audit_carry_from_strip(-signs["A"], me, g, strip, breadth_front, n_check=40); raise RuntimeError("carry audit accepted a NEGATED sign grid")
    except AssertionError:
        audits["carry_audit_raises_on_negated_grid"] = True
    cells = {}
    for c in CELLS:
        sh, pp, sc, sd = positions_from_signs(signs[c], sig, me, g)
        cells[(c, "published")] = dict(book="published", sign_held=sh, scale_held=sc, pos=pp)
        cells[(c, "dollar")] = dict(book="dollar", sign_held=sd.astype(float), scale_held=None, pos=None)
    prim = cells[PRIMARY_CELL]
    audits["lag_held_cells"] = R55.audit_lag(prim["sign_held"], np.where(np.isfinite(carry_me_pd), np.sign(carry_me_pd), 0.0), me, g["span"], T)
    unl = np.zeros_like(prim["sign_held"])
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = signs["A"][:, k][:, None]
    unl = np.where(g["span"], unl, 0.0)
    try:
        R55.audit_lag(unl, np.where(np.isfinite(carry_me_pd), np.sign(carry_me_pd), 0.0), me, g["span"], T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(prim["sign_held"], me, T)
    try:
        R55.audit_right_quantity(np.sign(np.nan_to_num(C)), me, T); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    sdA = cells[("A", "dollar")]["sign_held"].astype(int)
    grossA, _, _ = R55.dollar_book(sdA, g, upp, comm_rt, tick_usd, roots)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(grossA, sdA, g, upp)
    for label, bad in (("negated", -grossA), ("mislagged", R55.dollar_book(sdA, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, roots)[0])):
        try:
            R55.audit_sign_in_money(bad, sdA, g, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True
    x_lag = R55.book_return(prim["pos"], rsimple); x_unl = R55.book_return(unl * prim["scale_held"], rsimple)
    audits["pnl_differs_from_unlagged"] = bool(not np.allclose(x_lag, x_unl))
    log(f"  audits: {audits}")

    # windows and scoring
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]
    results_cells, scored = {}, {}
    for key, c in cells.items():
        cell, book = key; name = f"{cell}/{book}"
        if book == "published":
            x = R55.book_return(c["pos"], rsimple); turn, rolls, tw = R55.published_cost(c["pos"], cbp, g["roll"]); xn = x - turn
            entry = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "net_incl_rolls": R55.sharpe((x - turn - rolls)[wP]),
                     "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                     "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                     "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4),
                     "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023")}
            scored[key] = dict(gross=x, net=xn)
        else:
            sP = np.where(wP[None, :], c["sign_held"], 0.0).astype(int); sL = np.where(wL[None, :], c["sign_held"], 0.0).astype(int)
            gross, cost, sides = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots)
            gb, cb = gross.sum(0), cost.sum(0); xg, xn = gb, gb - cb
            g_cd, c_cd, _ = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, cd_roots)
            gL, _, _ = R55.dollar_book(sL, g, upp, comm_rt, tick_usd, dollar_roots)
            entry = {"gross": R55.stats_block(xg[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "cost_total": float(cb[wP].sum()), "sides_total": int(sides[:, wP].sum()),
                     "roll_sides_total": int((2 * (g["roll"] & (sP != 0)))[:, wP].sum()),
                     "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d"),
                                   "net": R55.stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d net")},
                     "gross_long": R55.stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $")}
            scored[key] = dict(gross=xg, net=xn)
        results_cells[name] = entry
        log(f"  {name:12s} gross SR {entry['gross']['sharpe']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}")

    # diagnostics on the primary
    x = scored[PRIMARY_CELL]["gross"]; pos = prim["pos"]
    per_root = {}
    for i, r in enumerate(roots):
        xi = pos[i] * rsimple[i]; live_i = pos[i] != 0
        per_root[r] = {"sharpe_primary": R55.sharpe(xi[wP & live_i]) if (wP & live_i).sum() > 60 else None,
                       "total_long": float(xi[wL].sum()), "total_primary": float(xi[wP].sum()),
                       "share_long_months": float((signs["A"][i][signs["A"][i] != 0] > 0).mean()) if (signs["A"][i] != 0).any() else None,
                       "mean_carry_me": float(np.nanmean(carry_me[i])) if np.isfinite(carry_me[i]).any() else None,
                       "sign_persistence": _persistence(signs["A"][i]), "min_size": size_name[i], "sigma_usd_min_size": root_sigma[r]}
    n_pos = sum(1 for r in roots if per_root[r]["total_long"] > 0)
    per_sector = {}
    for sec, lst in R55.SECTOR.items():
        ix = [roots.index(r) for r in lst if r in roots]
        xs = R55.book_return(pos[ix], rsimple[ix])
        per_sector[sec] = {"roots": [roots[j] for j in ix], "sharpe_primary": R55.sharpe(xs[wP]), "sharpe_long": R55.sharpe(xs[wL])}
    per_era = {f"{a}..{b}": {"sharpe": R55.sharpe(x[R55.window_mask(days, a, b)])} for a, b in ERAS}
    yrs = sorted(set(d[:4] for d in days[wL]))
    per_year = {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in yrs}
    # carry state: persistence and the share of months positive
    pers = [per_root[r]["sign_persistence"] for r in roots if per_root[r]["sign_persistence"] is not None]
    carry_state = {"median_sign_persistence": float(np.median(pers)), "share_root_months_positive": float((signs["A"][signs["A"] != 0] > 0).mean()),
                   "mean_carry_by_sector": {sec: float(np.nanmean(carry_me[[roots.index(r) for r in lst if r in roots]])) for sec, lst in R55.SECTOR.items()}}
    # relation to trend
    _, pos12, _, _ = R55.build_positions(g, sig, me, (12,))
    x12 = R55.book_return(pos12, rsimple)
    xm = pd.Series(x, index=pd.to_datetime(days)); xm12 = pd.Series(x12, index=pd.to_datetime(days))
    mon = lambda s: (1 + s).groupby(s.index.to_period("M")).prod() - 1
    mA, m12 = mon(xm[wP]), mon(xm12[wP])
    trend_relation = {"rho_daily_2016_2023": float(np.corrcoef(x[wP], x12[wP])[0, 1]), "rho_monthly_2016_2023": float(np.corrcoef(mA.values, m12.values)[0, 1]),
                      "trend12_sharpe_here": R55.sharpe(x12[wP]), "combo_C_sharpe": results_cells["C/published"]["gross"]["sharpe"],
                      "carry_march_2020": float(mA.loc[pd.Period("2020-03", "M")]), "trend_march_2020": float(m12.loc[pd.Period("2020-03", "M")]),
                      "worst_5pct_days_overlap": float(np.mean(np.isin(np.argsort(x[wP])[:int(0.05 * wP.sum())], np.argsort(x12[wP])[:int(0.05 * wP.sum())])))}
    log(f"  rho(carry, trend) daily {trend_relation['rho_daily_2016_2023']:+.3f}; combo C {trend_relation['combo_C_sharpe']:+.3f}; carry Mar-2020 {trend_relation['carry_march_2020']:+.3%}")

    # nulls, purged as declared
    live_idx = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    Tw = int(wP.sum())
    for k in (1, 7, 63, 250, 999, 1500, 2000):
        k = k % (Tw - 1) or 1
        p = R55.rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k) * prim["scale_held"]
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"enumeration not bit-identical at offset {k}")
    log(f"  enumerating N1/N2 over {Tw - 1} offsets x {len(cells)} cells, purge {R55.NULL_PURGE} ...")
    null_all, keys = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log)
    names = [f"{a}/{b}" for a, b in keys]
    obs = np.array([results_cells[nm]["gross"]["sharpe"] if b == "published" else results_cells[nm]["net"]["sharpe"] for nm, (a, b) in zip(names, keys)])
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= Tw - R55.NULL_PURGE); null = null_all[keep]
    jP = keys.index(PRIMARY_CELL)
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(null.shape[0]), "per_cell": {},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_all[:, jP].tolist()}}
    for j, nm in enumerate(names):
        col = null[:, j]
        n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)),
                              "p95": float(np.percentile(col, 95)), "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95))}
    fam = null.max(1)
    n2 = {"observed_best": float(obs.max()), "observed_best_cell": names[int(obs.argmax())], "p50": float(np.percentile(fam, 50)),
          "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95))}
    primary = n1["per_cell"]["A/published"]
    log(f"  N1 primary: observed {primary['observed']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f}\n"
        f"  N2 family: best {n2['observed_best']:+.3f} ({n2['observed_best_cell']})  p50 {n2['p50']:+.3f}  p95 {n2['p95']:+.3f}")

    cA, cC, dA = results_cells["A/published"], results_cells["C/published"], results_cells["A/dollar"]
    cm_sr = per_sector["CM"]["sharpe_primary"]
    preds = {
        "P-1": {"claim": "cell A gross Sharpe 2016-2023 > 0, above N1 p95; point 0.2-0.5", "value": cA["gross"]["sharpe"], "p95": primary["p95"],
                "holds": bool(cA["gross"]["sharpe"] > 0 and primary["clears_p95"]), "in_point_range": bool(0.2 <= cA["gross"]["sharpe"] <= 0.5)},
        "P-2": {"claim": "|rho(carry, trend)| daily 2016-2023 < 0.3; point ~0.1", "value": trend_relation["rho_daily_2016_2023"],
                "holds": bool(abs(trend_relation["rho_daily_2016_2023"]) < 0.3)},
        "P-3": {"claim": "cell C gross Sharpe > max(cell A, D555 12m = +0.304)", "value": cC["gross"]["sharpe"],
                "bar": max(cA["gross"]["sharpe"], D555_TREND_SHARPE), "holds": bool(cC["gross"]["sharpe"] > max(cA["gross"]["sharpe"], D555_TREND_SHARPE))},
        "P-4": {"claim": "cell A daily skew < 0 and March 2020 < 0", "skew": cA["gross"]["skew"], "march_2020": trend_relation["carry_march_2020"],
                "holds": bool(cA["gross"]["skew"] < 0 and trend_relation["carry_march_2020"] < 0)},
        "P-5": {"claim": "turnover < 14.7 weight units a year and median sign persistence > 0.8", "turnover": cA["ann_turnover_weight_units"],
                "persistence": carry_state["median_sign_persistence"],
                "holds": bool(cA["ann_turnover_weight_units"] < 14.7 and carry_state["median_sign_persistence"] > 0.8)},
        "P-6": {"claim": "cell A P&L positive on >= 21 of 36 roots over 2011-2023", "n_positive": n_pos, "holds": bool(n_pos >= 21)},
        "P-7": {"claim": "commodity-only cell A Sharpe < diversified cell A Sharpe", "cm": cm_sr, "all": cA["gross"]["sharpe"], "holds": bool(cm_sr < cA["gross"]["sharpe"])},
        "P-8": {"claim": "falsifier: gates green and primary below N1 p50 -> carry did badly here", "primary_below_p50": bool(cA["gross"]["sharpe"] < primary["p50"])},
    }
    verdict = "PASS" if (cA["gross"]["sharpe"] > 0 and primary["clears_p95"] and n2["clears_p95"]) else "DOES NOT PASS"
    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS in this file are NEGATIVE: minimum of (cumulative daily return - running peak); "
                                                                  "return units for the published books, dollars at minimum size for the dollar books (D542).", "record": "D542"},
           "spec": "D556", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "curve_sha256": R55.sha256(CURVE), "strip_sha256": R55.sha256(STRIP),
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum()), "month_ends": int(len(me))},
           "ffill_sessions": FFILL_SESSIONS, "cells": results_cells, "primary": primary, "null_n1": n1, "null_n2": n2, "per_root": per_root,
           "per_sector": per_sector, "per_era": per_era, "per_year": per_year, "carry_state": carry_state, "trend_relation": trend_relation,
           "dollar_book": {"excluded": list(R55.DOLLAR_EXCLUDED), "roots": dollar_roots, "cd_roots": cd_roots, "min_size": dict(zip(roots, size_name)),
                           "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk"},
           "predictions": preds, "verdict": {"declared": verdict}, "audits": audits, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(res, indent=1, default=R55._json_default), encoding="utf-8")
    log(f"\n  VERDICT {verdict}   -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


def _persistence(s: np.ndarray):
    v = s[s != 0]
    if len(v) < 13:
        return None
    return float((v[1:] == v[:-1]).mean())


# --------------------------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D556 SELF-TEST -- synthetic strip and grids, no fixture read, no cell scored\n")
    days = pd.bdate_range("2012-01-02", "2014-12-31").strftime("%Y-%m-%d").to_numpy(); T = len(days)
    roots = ["CL", "GC"]; n = 2
    rlog = 0.01 * np.random.default_rng(3).standard_normal((n, T)); rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool)
    g = dict(roots=roots, days=days, close=np.exp(np.nancumsum(rlog, 1)) * 50, rlog=rlog, dP=np.zeros((n, T)), roll=np.zeros((n, T), dtype=bool),
             live=live, span=live.copy(), nonpositive=[])
    me = R55.month_ends(days)
    # a curve: CL in backwardation (positive carry), GC in contango (negative), with holes every 7th session
    C = np.tile(np.array([[+0.10], [-0.05]]), (1, T)); C[:, ::7] = np.nan
    cm = carry_at_month_ends(C, live, me); cm_pd = carry_at_month_ends_pandas(C, live, days, roots, me)
    assert np.array_equal(np.nan_to_num(cm, nan=-9), np.nan_to_num(cm_pd, nan=-9)) and np.isfinite(cm).all()
    print("  [1] month-end carry: numpy and pandas paths agree; a hole at the month-end reads the last settlement within 5 sessions")
    tr = np.ones((n, len(me)), dtype=int); tr[1] = -1
    S = cell_signs(cm, tr, None)
    assert (S["A"][0] == 1).all() and (S["A"][1] == -1).all() and (S["C"][0] == 1).all() and (S["C"][1] == -1).all()
    tr2 = -np.ones((n, len(me)), dtype=int)
    assert (cell_signs(cm, tr2, None)["C"][0] == 0).all(), "trend and carry disagreeing must net to flat"
    assert (S["B"][:, :DEMEAN_MIN_MONTHS - 1] == 0).all(), "B must be flat until 12 month-ends exist"
    print("  [2] cell signs: A follows the curve, B waits 12 months, C nets to flat on disagreement")
    # the strip audit: build a synthetic strip consistent with C, then break it
    rows = []; front = {}
    for t, d in enumerate(days):
        for i, r in enumerate(roots):
            if not np.isfinite(C[i, t]):
                continue
            f, nx = (f"{r}H3", f"{r}M3") if d < "2013-03-01" else (f"{r}Z4", f"{r}H5")
            rows.append((r, f, d, 100.0)); rows.append((r, nx, d, 100.0 / (1 + C[i, t] * 3 / 12))); front[(r, d)] = f
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    k = audit_carry_from_strip(S["A"], me, g, strip, front, n_check=30)
    raised = False
    try:
        audit_carry_from_strip(-S["A"], me, g, strip, front, n_check=10)
    except AssertionError:
        raised = True
    assert raised, "carry audit accepted a negated grid"
    print(f"  [3] the strip audit passes {k} cells and RAISES on a negated grid")
    sig = R55.ew_vol(rlog, live)
    sh, pp, sc, sd = positions_from_signs(S["A"], sig, me, g)
    R55.audit_right_quantity(sh, me, T)
    print("  [4] positions hold between month-ends (D555's right-quantity audit passes)")
    print("\n  ALL SELF-TESTS PASSED. No fixture was read and no cell was scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); gq = ap.add_mutually_exclusive_group(required=True)
    gq.add_argument("--run", action="store_true"); gq.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (0 if run() else 1))
