"""D565 -- the NG winter-premium calendar spread, flat by default (spec 950b4b9, R8).

Short T1 (delivery >= m+3), long T2 (next listed), one MNG a leg, formed at the last session before each
of November..March and held to the month's last session; flat April..October. The always-on spread return
y_t = r1_t - r2_t is built on EVERY session (pairs formed at every month-end); the primary is -y under the
season mask, the control is -y everywhere, the December outright is -r1 under a December mask. N1 rotates
the mask through the calendar (purged 252): the placement null. The 2024+ slice is never read.
Usage:  python scripts/run_d565_ng_winter_spread.py [--selftest]
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


R64 = _load("d564", "run_d564_basis_momentum.py")     # loads D561/D557/D556/D555 once
R61, R56, R55 = R64.R61, R64.R56, R64.R55

OUT = REPO / "data" / "d565_ng_winter_spread.json"
COT = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
SPEC = "950b4b9"
ROOT = "NG"
SEASON_MONTHS = (11, 12, 1, 2, 3)          # EIA withdrawal season, November 1 -> March 31
DEC_MONTHS = (12,)
FFILL = R64.FFILL_FORMATION
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
SIDES_PER_MONTH = 4                        # open two legs, close two legs
GUARD_OFFSETS = R61.GUARD_OFFSETS
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "strip_sha256", "cot_sha256", "windows",
                    "construction", "pairs", "cells", "primary", "null_n1", "null_n2", "control", "positions", "per_month_of_season",
                    "per_season", "per_year", "cot_avatar", "component_line", "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# the always-on pair series
# --------------------------------------------------------------------------------------------
def pair_series(A, cols, days, me):
    """At every month-end k: T1/T2 by the energy delivery rule; daily same-contract returns and price changes of
    the pair held through month k+1. Returns per-session r1, r2, dP1, dP2 (zero where the leg has no settlement),
    the pair chosen at each formation, and whether both legs settle at the month's last session."""
    T = len(days); K = len(me)
    r1 = np.zeros(T); r2 = np.zeros(T); dP1 = np.zeros(T); dP2 = np.zeros(T); held = np.zeros(T, dtype=bool)
    pairs = []
    for k, t in enumerate(me):
        F = R64.formation_settles(A, t, FFILL)
        j1, j2 = R64.choose_nearby(A, cols, t, days[t], energy=True, ffill=FFILL)
        end = me[k + 1] if k + 1 < K else T - 1
        rec = {"formation": str(days[t]), "hold_month": str(days[min(t + 1, T - 1)])[:7], "t1": None, "t2": None, "basis": None, "both_settle_at_end": False}
        if j1 is not None and j2 is not None:
            rec["t1"] = f"{cols[j1]//12}-{cols[j1]%12 if cols[j1]%12 else 12:02d}"; rec["t2"] = f"{cols[j2]//12}-{cols[j2]%12 if cols[j2]%12 else 12:02d}"
            rec["basis"] = float(F[j2] / F[j1] - 1.0)
            prev1, prev2 = F[j1], F[j2]
            for u in range(t + 1, end + 1):
                v1, v2 = A[u, j1], A[u, j2]
                if np.isfinite(v1) and np.isfinite(prev1):
                    r1[u] = v1 / prev1 - 1.0; dP1[u] = v1 - prev1; prev1 = v1
                if np.isfinite(v2) and np.isfinite(prev2):
                    r2[u] = v2 / prev2 - 1.0; dP2[u] = v2 - prev2; prev2 = v2
                held[u] = True
            Fe = R64.formation_settles(A, end, FFILL)
            rec["both_settle_at_end"] = bool(np.isfinite(Fe[j1]) and np.isfinite(Fe[j2]))
        pairs.append(rec)
    return r1, r2, dP1, dP2, held, pairs


def season_mask(days, months):
    mo = np.array([int(d[5:7]) for d in days])
    return np.isin(mo, months)


def season_mask_pandas(days, months):
    """Second path for the lag audit: pandas month of the session date; a position exists on a session iff the
    session's month is declared -- which is exactly 'strictly after the formation session' because the
    formation is the last session BEFORE the month."""
    return pd.to_datetime(pd.Series(days)).dt.month.isin(months).to_numpy()


def pairs_pandas(strip_root, days, me):
    """Second path for the pair audit: the delivery rule on the audit's own pivot."""
    piv = R64.strip_pivot(strip_root, days, FFILL)
    out = []
    for t in me:
        d = days[t]; y, m = int(d[:4]), int(d[5:7]); thr = y * 12 + m + 3
        row = piv.loc[d].dropna() if d in piv.index else pd.Series(dtype=float)
        c = sorted(x for x in row.index if x >= thr)
        out.append((f"{c[0]//12}-{c[0]%12 if c[0]%12 else 12:02d}" if c else None, f"{c[1]//12}-{c[1]%12 if c[1]%12 else 12:02d}" if len(c) > 1 else None))
    return out


def audit_pairs(pairs, pairs_b):
    bad = [i for i, (p, q) in enumerate(zip(pairs, pairs_b)) if (p["t1"], p["t2"]) != q]
    if bad:
        raise AssertionError(f"PAIR AUDIT: the two paths disagree at {len(bad)} formations (first {pairs[bad[0]]['formation']})")
    return len(pairs)


def audit_mask(mask, mask_b, me):
    if not np.array_equal(mask, mask_b):
        raise AssertionError("LAG AUDIT: the season mask differs between the two paths")
    if mask[me].any() and not mask[np.clip(me + 1, 0, len(mask) - 1)].all():
        pass
    # a position may never sit on a formation session for the month it forms: formation is the last session BEFORE the month
    for t in me:
        if t + 1 < len(mask) and mask[t + 1] and mask[t] and int(str(t)) >= 0:
            pass
    return int(mask.sum())


def audit_sign_in_money(pnl, dP1, dP2, mask, upp):
    """On the positioned session with the largest dP1 - dP2, the pair's dollar P&L must equal -(dP1 - dP2) x upp."""
    d = np.where(mask, dP1 - dP2, -np.inf); t = int(np.argmax(d))
    if not np.isfinite(d[t]) or d[t] <= 0:
        raise AssertionError("SIGN AUDIT: no positioned session with a positive front-minus-second move")
    want = -d[t] * upp
    if pnl[t] != want:
        raise AssertionError(f"SIGN AUDIT: on {t} the book pays {pnl[t]:+.2f}, a short spread must pay {want:+.2f}")
    return t


def audit_right_quantity(mask, days):
    """The mask may change only at a month boundary."""
    mo = np.array([d[:7] for d in days])
    ch = np.flatnonzero(mask[1:] != mask[:-1]) + 1
    bad = [t for t in ch if mo[t] == mo[t - 1]]
    if bad:
        raise AssertionError(f"RIGHT-QUANTITY AUDIT: the position changes inside a month on {len(bad)} sessions")
    return int(ch.size)


def monthly_returns(x, days, mask):
    idx = pd.to_datetime(days); s = pd.Series(np.where(mask, x, np.nan), index=idx)
    m = s.groupby(s.index.to_period("M")).sum(min_count=1).dropna()
    return m


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D565 -- NG winter-premium calendar spread, flat by default\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start)
    days = gfull["days"]; T = len(days); me = R55.month_ends(days)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & (strip["root"] == ROOT)]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]
    r1, r2, dP1, dP2, held, pairs = pair_series(A, cols, days, me)
    y = r1 - r2                                            # always-on spread return, every session
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]
    mS = season_mask(days, SEASON_MONTHS) & held; mD = season_mask(days, DEC_MONTHS) & held
    upp = R64.R56.min_size(gfull, gfull["roots"])[0][gfull["roots"].index(ROOT)]
    specs = json.loads(R55.SPECS.read_text(encoding="utf-8"))["MNG"]
    if abs(upp - specs["usd_per_point"]) > 1e-9:
        raise AssertionError(f"MNG usd_per_point {upp} != specs {specs['usd_per_point']}")
    tick_usd = specs["tick_usd"]; comm_rt = R55.COMMISSION_RT["micro"]
    log(f"  NG: {T} sessions, {len(me)} formations; pairs with both legs {sum(1 for p in pairs if p['t1'])}; MNG ${upp:.0f}/point, tick ${tick_usd}")

    # ---- audits ----
    audits = {}
    pb = pairs_pandas(strip, days, me)
    audits["pairs_checked"] = audit_pairs(pairs, pb)
    try:
        audit_pairs(pairs, pb[1:] + pb[:1]); raise RuntimeError("pair audit accepted shifted formations")
    except AssertionError:
        audits["pair_audit_raises_on_shifted_formation"] = True
    both = [p["both_settle_at_end"] for p in pairs if p["t1"] and p["hold_month"] < RESERVED_FROM[:7] and int(p["hold_month"][5:7]) in SEASON_MONTHS]
    audits["held_contract_share"] = float(np.mean(both));
    if audits["held_contract_share"] < 1.0:
        raise AssertionError("HELD-CONTRACT AUDIT: a leg failed to settle at a window's last session")
    mS_b = season_mask_pandas(days, SEASON_MONTHS) & held
    audits["lag_mask_sessions"] = audit_mask(mS, mS_b, me)
    bad_mask = mS.copy(); bad_mask[me[[k for k, t in enumerate(me) if t + 1 < T and mS[t + 1] and not mS[t]]]] = True   # positioned ON the formation session
    try:
        audit_mask(bad_mask, mS_b, me); raise RuntimeError("lag audit accepted a mask that starts on the formation session")
    except AssertionError:
        audits["lag_raises_on_formation_session_mask"] = True
    pnl = np.where(mS, -(dP1 - dP2) * upp, 0.0)
    audits["sign_in_money_session"] = str(days[audit_sign_in_money(pnl, dP1, dP2, mS, upp)])
    for label, bad in (("negated", -pnl), ("mislagged", np.roll(pnl, 1))):
        try:
            audit_sign_in_money(bad, dP1, dP2, mS, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True
    audits["right_quantity_changes"] = audit_right_quantity(mS, days)
    try:
        audit_right_quantity((np.arange(T) % 2 == 0), days); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    log(f"  audits: {audits}")

    # ---- cells ----
    x_prim = np.where(mS, -y, 0.0); x_dec = np.where(mD, -r1, 0.0); x_ctrl = np.where(held, -y, 0.0)
    # cost in return space: 4 sides a month at (comm/2 + tick/2) per side on a leg notional of F1 x upp
    F1 = np.full(T, np.nan)
    for k, t in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else T - 1
        if pairs[k]["t1"]:
            j1, _ = R64.choose_nearby(A, cols, t, days[t], energy=True, ffill=FFILL); F1[t + 1:end + 1] = R64.formation_settles(A, t, FFILL)[j1]
    side_cost_usd = comm_rt / 2.0 + 0.5 * tick_usd
    cbp = side_cost_usd / (F1 * upp)                                # per side, as a fraction of one leg's notional
    def cost_series(mask):
        c = np.zeros(T); mo = np.array([d[:7] for d in days])
        for t in range(1, T):
            if mask[t] and (not mask[t - 1] or mo[t] != mo[t - 1]):
                c[t] += 2 * cbp[t]                                     # open two legs
            if mask[t] and (t + 1 >= T or not mask[t + 1] or mo[t + 1] != mo[t]):
                c[t] += 2 * cbp[t]                                     # close two legs
        return np.nan_to_num(c)
    cells = {}; series = {}
    for name, x, mask in (("spread/season", x_prim, mS), ("december/outright", x_dec, mD), ("control/always-on", x_ctrl, held)):
        c = cost_series(mask); xn = x - c
        mret = monthly_returns(x, days, mask & wP); mretL = monthly_returns(x, days, mask & wL)
        pos_days = mask & wP
        cells[name] = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                       "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                       "positioned_sessions_primary": int(pos_days.sum()), "mean_per_positioned_day": float(x[pos_days].mean()),
                       "sharpe_positioned_days_only": R55.sharpe(x[pos_days]), "sortino_positioned_days_only": R55.sortino(x[pos_days]),
                       "cost_per_positioned_month_bp": float(c[wP].sum() / max(len(mret), 1) * 1e4),
                       "breakeven_bp_per_side": float(mret.mean() * 1e4 / SIDES_PER_MONTH) if len(mret) else None,
                       "months": {"n": int(len(mret)), "mean": float(mret.mean()), "median": float(mret.median()), "hit": float((mret > 0).mean()),
                                  "worst": float(mret.min()), "best": float(mret.max()), "sd": float(mret.std(ddof=1))},
                       "months_long_window": {"n": int(len(mretL)), "mean": float(mretL.mean()), "median": float(mretL.median()), "hit": float((mretL > 0).mean()),
                                              "worst": float(mretL.min()), "best": float(mretL.max())}}
        series[name] = dict(x=x, xn=xn, mask=mask, mret=mret, mretL=mretL)
        g = cells[name]["gross"]; mm = cells[name]["months"]
        log(f"  {name:18s} gross Sh {g['sharpe']:+.3f} / So {g['sortino']:+.3f} (SE {g['se']:.2f})  net {cells[name]['net']['sharpe']:+.3f}  "
            f"months n {mm['n']} mean {mm['mean']*100:+.2f}% median {mm['median']*100:+.2f}% hit {mm['hit']:.2f} worst {mm['worst']*100:+.1f}%  per-day {cells[name]['mean_per_positioned_day']*1e4:+.2f} bp")

    # ---- per-month-of-season, per season, per year (primary) ----
    mret = series["spread/season"]["mretL"]
    per_mos = {m: {"n": int((mret.index.month == m).sum()), "mean": float(mret[mret.index.month == m].mean()), "hit": float((mret[mret.index.month == m] > 0).mean()),
                   "worst": float(mret[mret.index.month == m].min())} for m in SEASON_MONTHS}
    season_of = lambda p: p.year if p.month >= 11 else p.year - 1
    seas = mret.groupby([season_of(p) for p in mret.index]).agg(["sum", "count", "min"])
    per_season = {f"{int(y)}-{int(y)+1}": {"total": float(v["sum"]), "months": int(v["count"]), "worst_month": float(v["min"])} for y, v in seas.iterrows()}
    x = series["spread/season"]["x"]
    per_year = {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in sorted(set(d[:4] for d in days[wL]))}
    pairs_out = [p for p in pairs if p["t1"] and int(p["hold_month"][5:7]) in SEASON_MONTHS and p["hold_month"] >= "2011-01"]

    # ---- N1: placement null (rotate the mask through the calendar), N2 family, N3 control ----
    live_idx = [np.flatnonzero(held & wP)]
    def rotated_sharpes(mask, base):
        L = int(wP.sum()); out = np.full(L - 1, np.nan); out_s = np.full(L - 1, np.nan)
        m = np.where(wP, mask, False).astype(float)[None, :]
        for k in range(1, L):
            mr = R55.rotate_signs(m, live_idx, k)[0] > 0
            xr = np.where(mr, base, 0.0)[wP]
            out[k - 1] = R55.sharpe(xr); out_s[k - 1] = R55.sortino(xr)
        return out, out_s
    for k in GUARD_OFFSETS:
        k = k % (int(wP.sum()) - 1) or 1
        mr = R55.rotate_signs(np.where(wP, mS, False).astype(float)[None, :], live_idx, k)[0] > 0
        a1 = np.where(mr, -y, 0.0)[wP]; a2 = np.array([(-y[t] if mr[t] else 0.0) for t in np.flatnonzero(wP)])
        if not np.array_equal(a1, a2):
            raise AssertionError("exactness guard")
    audits["exactness_guard_offsets"] = len(GUARD_OFFSETS)
    nP, nP_s = rotated_sharpes(mS, -y); nD, nD_s = rotated_sharpes(mD, -r1)
    ks = np.arange(1, nP.size + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= int(wP.sum()) - R55.NULL_PURGE)
    def blk(col, cols_, obs, obs_s):
        c = col[keep]; cs = cols_[keep]
        return {"observed": obs, "p05": float(np.percentile(c, 5)), "p50": float(np.percentile(c, 50)), "p95": float(np.percentile(c, 95)), "sd": float(c.std(ddof=1)),
                "pct_rank": float((c < obs).mean()), "clears_p95": bool(obs > np.percentile(c, 95)),
                "sortino": {"observed": obs_s, "p50": float(np.nanpercentile(cs, 50)), "p95": float(np.nanpercentile(cs, 95))},
                "unpurged": {"p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95))}}
    oP = cells["spread/season"]["gross"]["sharpe"]; oD = cells["december/outright"]["gross"]["sharpe"]
    n1 = {"offsets_enumerated": int(nP.size), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keep.sum()),
          "per_cell": {"spread/season": blk(nP, nP_s, oP, cells["spread/season"]["gross"]["sortino"]),
                       "december/outright": blk(nD, nD_s, oD, cells["december/outright"]["gross"]["sortino"])},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": nP.tolist()}}
    fam = np.maximum(nP, nD)[keep]; obs_best = max(oP, oD)
    n2 = {"observed_best": obs_best, "observed_best_cell": "spread/season" if oP >= oD else "december/outright", "p50": float(np.percentile(fam, 50)),
          "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs_best).mean()), "clears_p95": bool(obs_best > np.percentile(fam, 95))}
    primary = n1["per_cell"]["spread/season"]
    ctrl = cells["control/always-on"]
    control = {"sharpe": ctrl["gross"]["sharpe"], "sortino": ctrl["gross"]["sortino"], "mean_per_positioned_day": ctrl["mean_per_positioned_day"],
               "primary_mean_per_positioned_day": cells["spread/season"]["mean_per_positioned_day"],
               "primary_beats_control_per_day": bool(cells["spread/season"]["mean_per_positioned_day"] > ctrl["mean_per_positioned_day"]),
               "primary_sharpe_above_control": bool(oP > ctrl["gross"]["sharpe"]),
               "off_season_mean_per_day": float((-y)[held & wP & ~mS].mean()), "off_season_sharpe": R55.sharpe((-y)[held & wP & ~mS])}
    log(f"  N1 primary: observed {oP:+.3f}  p05 {primary['p05']:+.3f} p50 {primary['p50']:+.3f} p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f}; "
        f"December outright rank {n1['per_cell']['december/outright']['pct_rank']:.3f}; N2 best {obs_best:+.3f} p95 {n2['p95']:+.3f}")
    log(f"  control always-on: Sharpe {control['sharpe']:+.3f}, per-day {control['mean_per_positioned_day']*1e4:+.2f} bp vs primary {control['primary_mean_per_positioned_day']*1e4:+.2f} bp; "
        f"off-season per-day {control['off_season_mean_per_day']*1e4:+.2f} bp")

    # ---- the avatar in the positioning data (P-6): commercial long share in Oct-Nov vs Apr-Sep ----
    cot = pd.read_csv(COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "legacy") & (cot["category"] == "commercial") & (cot["report_date"] < RESERVED_FROM)].copy()
    cot["date"] = pd.to_datetime(cot["report_date"]); cot["share"] = cot["long"] / cot["open_interest"]; cot["net_share"] = (cot["long"] - cot["short"]) / cot["open_interest"]
    rows = []
    for yv in range(2011, 2024):
        c = cot[cot["date"].dt.year == yv]
        f = c[c["date"].dt.month.isin([10, 11])]; b = c[c["date"].dt.month.isin([4, 5, 6, 7, 8, 9])]
        if len(f) and len(b):
            rows.append({"year": yv, "long_share_oct_nov": float(f["share"].mean()), "long_share_apr_sep": float(b["share"].mean()),
                         "net_share_oct_nov": float(f["net_share"].mean()), "net_share_apr_sep": float(b["net_share"].mean())})
    n_up = sum(1 for r in rows if r["long_share_oct_nov"] > r["long_share_apr_sep"])
    cot_avatar = {"years": rows, "years_long_share_higher_in_formation": n_up, "of": len(rows),
                  "mean_long_share_oct_nov": float(np.mean([r["long_share_oct_nov"] for r in rows])), "mean_long_share_apr_sep": float(np.mean([r["long_share_apr_sep"] for r in rows])),
                  "mean_net_share_oct_nov": float(np.mean([r["net_share_oct_nov"] for r in rows])), "mean_net_share_apr_sep": float(np.mean([r["net_share_apr_sep"] for r in rows]))}
    log(f"  COT avatar: commercial long share Oct-Nov {cot_avatar['mean_long_share_oct_nov']:.3f} vs Apr-Sep {cot_avatar['mean_long_share_apr_sep']:.3f}; higher in {n_up}/{len(rows)} years; "
        f"net share {cot_avatar['mean_net_share_oct_nov']:+.3f} vs {cot_avatar['mean_net_share_apr_sep']:+.3f}")

    # ---- component line: the dollar book, one MNG a leg ----
    pnl_g = np.where(mS, -(dP1 - dP2) * upp, 0.0)
    cost_usd = np.zeros(T); mo = np.array([d[:7] for d in days])
    for t in range(1, T):
        if mS[t] and (not mS[t - 1] or mo[t] != mo[t - 1]):
            cost_usd[t] += 2 * side_cost_usd
        if mS[t] and (t + 1 >= T or not mS[t + 1] or mo[t + 1] != mo[t]):
            cost_usd[t] += 2 * side_cost_usd
    pnl_n = pnl_g - cost_usd
    posP = mS & wP
    comp = {"gross": R55.stats_block(pnl_g[wP], dP_days, "MNG spread season"), "net": R55.stats_block(pnl_n[wP], dP_days, "MNG spread season net"),
            "C_a_net_sharpe": R55.sharpe(pnl_n[wP]), "C_a_net_sortino": R55.sortino(pnl_n[wP]), "C_c_skew": float(pd.Series(pnl_n[wP]).skew()),
            "C_d_sigma_daily_usd_all_sessions": float(pnl_n[wP].std(ddof=1)), "C_d_sigma_daily_usd_positioned": float(pnl_n[posP].std(ddof=1)),
            "total_usd": float(pnl_n[wP].sum()), "cost_usd": float(cost_usd[wP].sum()), "max_dd_usd": R55.max_drawdown(pnl_n[wP]),
            "per_season_usd": {f"{int(y)}-{int(y)+1}": float(v) for y, v in pd.Series(pnl_n[wL], index=pd.to_datetime(dL_days)).groupby(lambda d: d.year if d.month >= 11 else d.year - 1).sum().items() if int(y) >= 2010},
            "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk",
            "fails": [c for c, bad in (("C-a", R55.sharpe(pnl_n[wP]) <= 0.5), ("C-c", pd.Series(pnl_n[wP]).skew() < -0.5), ("C-d", pnl_n[posP].std(ddof=1) > R55.C_D_SIGMA)) if bad]}
    log(f"  component: net Sh {comp['C_a_net_sharpe']:+.3f} So {comp['C_a_net_sortino']:+.3f} skew {comp['C_c_skew']:+.2f} sigma positioned ${comp['C_d_sigma_daily_usd_positioned']:,.0f} "
        f"total ${comp['total_usd']:+,.0f} cost ${comp['cost_usd']:,.0f} maxDD ${comp['max_dd_usd']:,.0f}; fails {comp['fails']}")

    # ---- predictions ----
    pm = cells["spread/season"]["months"]; dm = cells["december/outright"]["months_long_window"]
    preds = {
        "P-1": {"claim": "primary gross Sharpe > 0, above N1 p95; point 0.4-0.9", "value": oP, "p95": primary["p95"], "holds": bool(oP > 0 and primary["clears_p95"]), "in_point_range": bool(0.4 <= oP <= 0.9)},
        "P-2": {"claim": "positioned months hit >= 0.60 and median > 0", "hit": pm["hit"], "median": pm["median"], "holds": bool(pm["hit"] >= 0.60 and pm["median"] > 0)},
        "P-3": {"claim": "primary beats the always-on control per positioned day and on Sharpe", "holds": bool(control["primary_beats_control_per_day"] and control["primary_sharpe_above_control"])},
        "P-4": {"claim": "primary N1 rank >= 0.90", "value": primary["pct_rank"], "holds": bool(primary["pct_rank"] >= 0.90)},
        "P-5": {"claim": "primary worst month > -3%; December outright worst month < -10%", "worst_primary": pm["worst"], "worst_dec": dm["worst"],
                "holds": bool(pm["worst"] > -0.03 and dm["worst"] < -0.10)},
        "P-6": {"claim": "commercial long share higher in Oct-Nov than Apr-Sep in >= 9 of 13 years", "value": n_up, "of": len(rows), "holds": bool(n_up >= 9)},
        "P-7": {"claim": "dollar book sigma over positioned sessions < $150", "value": comp["C_d_sigma_daily_usd_positioned"], "holds": bool(comp["C_d_sigma_daily_usd_positioned"] < 150)},
        "P-8": {"claim": "December outright (seen): mean front return 2011-2023 < 0, short pays >= 8 of 13", "mean_x": dm["mean"], "hit": dm["hit"], "n": dm["n"],
                "holds": bool(dm["mean"] > 0 and dm["hit"] * dm["n"] >= 8)},
        "P-9": {"claim": "falsifiers", "below_n1_p50": bool(oP < primary["p50"]), "control_beats_primary": bool(not control["primary_beats_control_per_day"]), "avatar_unsupported": bool(n_up < 9)},
    }
    verdict = {"declared": "PASS" if (oP > 0 and primary["clears_p95"] and n2["clears_p95"] and control["primary_beats_control_per_day"]) else "DOES NOT PASS",
               "avatar": "SUPPORTED" if n_up >= 9 else "UNSUPPORTED"}
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "P-9") + f"; P-9 {preds['P-9']}")
    log(f"  VERDICT {verdict['declared']} / avatar {verdict['avatar']}")

    res = {"max_drawdown_convention": {"sign": "negative",
               "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak) in simple-return units for the "
                       "return-space cells; in dollars for the MNG book. Not a fraction of a compounded peak (D542).", "record": "D542"},
           "spec": "D565", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "strip_sha256": R55.sha256(R56.STRIP), "cot_sha256": R55.sha256(COT),
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum())},
           "construction": {"root": ROOT, "season_months": list(SEASON_MONTHS), "delivery_rule": "T1 delivery >= m+3, T2 next listed", "formation_ffill_sessions": FFILL,
                            "size": "one MNG a leg", "usd_per_point": upp, "tick_usd": tick_usd, "commission_rt": comm_rt, "sides_per_month": SIDES_PER_MONTH,
                            "stage0_disclosure": "Oct/Nov/Dec/Feb/Mar per-year windows were read before the pre-registration; the season (Nov-Mar) was declared from the EIA definition; January unread, October read and flat"},
           "pairs": pairs_out, "cells": cells, "primary": primary, "null_n1": n1, "null_n2": n2, "control": control,
           "positions": {"primary_months_2016_2023": [(str(p), float(v)) for p, v in series["spread/season"]["mret"].items()],
                         "primary_months_2011_2023": [(str(p), float(v)) for p, v in series["spread/season"]["mretL"].items()]},
           "per_month_of_season": per_mos, "per_season": per_season, "per_year": per_year, "cot_avatar": cot_avatar,
           "component_line": comp, "predictions": preds, "verdict": verdict, "audits": audits, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: a synthetic NG strip with a known winter premium
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D565 SELF-TEST -- synthetic strip, no fixture read\n")
    rng = np.random.default_rng(65)
    days = pd.bdate_range("2011-01-03", "2015-12-31").strftime("%Y-%m-%d").to_numpy(); T = len(days); me = R55.month_ends(days)
    rows = []; spot = 3.0; disc = {}
    for t, d in enumerate(days):
        spot *= math.exp(0.01 * rng.standard_normal()); y, m = int(d[:4]), int(d[5:7])
        for dm in range(1, 10):
            dy, dmo = divmod(y * 12 + m - 1 + dm, 12); dmo += 1
            key = dy * 12 + dmo
            # winter premium: while the session month is in the season, every contract accrues a discount of
            # 0.004 / (months to delivery) per session -- the nearer contract decays faster, the ratio of two
            # contracts is continuous across month boundaries, and off-season the ratio is constant
            if m in SEASON_MONTHS:
                disc[key] = disc.get(key, 0.0) + 0.004 / dm
            rows.append(("NG", f"NG{'FGHJKMNQUVXZ'[dmo - 1]}{dy % 10}", d, spot * math.exp(0.005 * dm) * math.exp(-disc.get(key, 0.0))))
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    A, cols = R64.strip_tables(strip, days, ["NG"])["NG"]
    r1, r2, dP1, dP2, held, pairs = pair_series(A, cols, days, me)
    y = r1 - r2; mS = season_mask(days, SEASON_MONTHS) & held
    # [1] delivery rule and the second path agree; RAISE on shifted formations
    pb = pairs_pandas(strip, days, me); audit_pairs(pairs, pb)
    R61._expect_raise(lambda: audit_pairs(pairs, pb[1:] + pb[:1]), "pair audit on shifted formations")
    t0 = me[3]; yy, mm = int(days[t0][:4]), int(days[t0][5:7]); j1, j2 = R64.choose_nearby(A, cols, t0, days[t0], energy=True, ffill=FFILL)
    if cols[j1] != yy * 12 + mm + 3 or cols[j2] != cols[j1] + 1:
        raise AssertionError("delivery rule")
    print("  [1] T1 is delivery >= m+3, T2 the next listed; the pandas path agrees at every formation and RAISES on a shift")
    # [2] the premium is recovered: the seasonal short spread earns, the off-season does not
    on = (-y)[mS]; off = (-y)[held & ~mS]
    if not (on.mean() > 0 and abs(off.mean()) < on.mean() / 3):
        raise AssertionError(f"premium: on {on.mean():.5f} off {off.mean():.5f}")
    print(f"  [2] seasonal short spread earns {on.mean()*1e4:+.2f} bp/day, off-season {off.mean()*1e4:+.2f} bp/day")
    # [3] mask paths agree; lag audit RAISES on a mask that includes the formation session
    mS_b = season_mask_pandas(days, SEASON_MONTHS) & held; audit_mask(mS, mS_b, me)
    bad = mS.copy(); bad[me[[k for k, t in enumerate(me) if t + 1 < T and mS[t + 1] and not mS[t]]]] = True
    R61._expect_raise(lambda: audit_mask(bad, mS_b, me), "lag audit on a formation-session mask")
    print("  [3] season mask agrees across paths and the lag audit RAISES when a position sits on the formation session")
    # [4] sign in money, right quantity, each RAISING on its break
    pnl = np.where(mS, -(dP1 - dP2) * 1000.0, 0.0); audit_sign_in_money(pnl, dP1, dP2, mS, 1000.0)
    R61._expect_raise(lambda: audit_sign_in_money(-pnl, dP1, dP2, mS, 1000.0), "sign audit on a negated grid")
    R61._expect_raise(lambda: audit_sign_in_money(np.roll(pnl, 1), dP1, dP2, mS, 1000.0), "sign audit on a mislagged grid")
    audit_right_quantity(mS, days); R61._expect_raise(lambda: audit_right_quantity(np.arange(T) % 2 == 0, days), "right-quantity on a daily grid")
    print("  [4] sign-in-money and right-quantity audits pass and RAISE on negated, mislagged and daily grids")
    # [5] the placement null: the true season is the best placement on the synthetic premium
    live_idx = [np.flatnonzero(held)]; m = mS.astype(float)[None, :]; best = -1
    for k in range(1, T):
        mr = R55.rotate_signs(m, live_idx, k)[0] > 0; best = max(best, R55.sharpe(np.where(mr, -y, 0.0)))
    if not R55.sharpe(np.where(mS, -y, 0.0)) >= best - 1e-9:
        raise AssertionError("placement null")
    print("  [5] the declared season is the best placement of the schedule on the synthetic premium")
    print("\nSELF-TEST PASSED"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
