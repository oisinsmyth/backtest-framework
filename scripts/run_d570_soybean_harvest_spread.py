"""D570 -- the soybean harvest spread on the F/H pair, flat by default (spec 2503321, R8; written as seen).

B (PRIMARY): at the last session before September, T1 = the first listed delivery strictly after November (F),
T2 the next listed (H); short T1 / long T2, one ZS a leg, held on every session of September, October and
November; flat December..August; nothing rolls inside the window. B gated on the August stocks-to-use (<= the
median of prior Augusts) is the declared secondary. A, the rule-rolled cousin (delivery >= m+2, re-read monthly),
is the diagnostic under the same mask and, unmasked, the always-on control. N1 rotates the mask over A's
always-on series (exact, purged 252); N2 places B's exact construction at each of the twelve calendar months.
The 2024+ slice is never read on any source.
Usage:  python scripts/run_d570_soybean_harvest_spread.py [--selftest]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m


R69 = _load("d569", "stage0_d569_soybean_addendum.py")     # loads D568/D565/D564/... once
R68, R65, R64, R61, R56, R55 = R69.R68, R69.R65, R69.R64, R69.R61, R69.R56, R69.R55

OUT = REPO / "data" / "d570_soybean_harvest_spread.json"
SPEC = "2503321"
ROOT = "ZS"
M_START = 9                                # the primary placement: hold September, October, November
HOLD_MONTHS = 3
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
FFILL = R64.FFILL_FORMATION
SIDES_PER_WINDOW = 4
GUARD_OFFSETS = R61.GUARD_OFFSETS
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "strip_sha256", "cot_sha256", "wasde_sha256", "wasde_rows_scored",
                    "windows", "construction", "pairs", "cells", "primary", "null_n1", "null_n2", "control", "positions", "per_window",
                    "per_month_of_window", "per_year", "gate", "cot_record", "component_line", "predictions", "verdict", "audits", "timing"]


def hold_months(m_start):
    """The three (year offset, month) holding months of a placement starting at calendar month m_start."""
    return [(((m_start - 1 + j) // 12), ((m_start - 1 + j) % 12) + 1) for j in range(HOLD_MONTHS)]


def fixed_pair_series(A, cols, days, idx, m_start, years):
    """B's construction at placement m_start: formed at the last session before the first holding month of each year,
    T1 the first listed delivery strictly after the third holding month, T2 the next listed; the pair fixed through
    the window. Returns per-session r1, r2, dP1, dP2, held, T1 delivery index, formation F1, and the window records."""
    T = len(days); r1 = np.zeros(T); r2 = np.zeros(T); dP1 = np.zeros(T); dP2 = np.zeros(T)
    held = np.zeros(T, dtype=bool); t1_idx = np.full(T, -1, dtype=int); F1s = np.full(T, np.nan); recs = []
    hm = hold_months(m_start)
    for y in years:
        yo0, m0 = hm[0]; yo2, m2 = hm[-1]
        first = np.flatnonzero((idx.year == y + yo0) & (idx.month == m0)); last = np.flatnonzero((idx.year == y + yo2) & (idx.month == m2))
        if first.size == 0 or last.size == 0 or first[0] == 0:
            continue
        t0, t1 = first[0] - 1, last[-1]
        if str(days[t1]) >= RESERVED_FROM:
            continue
        F0 = R64.formation_settles(A, t0, FFILL); fin = np.isfinite(F0)
        thr = (y + yo2) * 12 + m2 + 1
        cand = np.flatnonzero(fin & (cols >= thr))
        if cand.size < 2:
            continue
        j1, j2 = int(cand[0]), int(cand[1]); prev1, prev2 = F0[j1], F0[j2]
        for u in range(t0 + 1, t1 + 1):
            v1, v2 = A[u, j1], A[u, j2]
            if np.isfinite(v1) and np.isfinite(prev1):
                r1[u] = v1 / prev1 - 1.0; dP1[u] = v1 - prev1; prev1 = v1
            if np.isfinite(v2) and np.isfinite(prev2):
                r2[u] = v2 / prev2 - 1.0; dP2[u] = v2 - prev2; prev2 = v2
            held[u] = True; t1_idx[u] = cols[j1]; F1s[u] = F0[j1]
        Fe = R64.formation_settles(A, t1, FFILL)
        recs.append({"year": y, "formation": str(days[t0]), "exit": str(days[t1]), "t1": R68.ymlabel(cols[j1]), "t2": R68.ymlabel(cols[j2]),
                     "F1": float(F0[j1]), "basis0_cents": float(F0[j2] - F0[j1]), "both_settle_at_end": bool(np.isfinite(Fe[j1]) and np.isfinite(Fe[j2])),
                     "month_ends_settle": all(bool(np.isfinite(R64.formation_settles(A, e, FFILL)[j1]) and np.isfinite(R64.formation_settles(A, e, FFILL)[j2]))
                                              for e in [np.flatnonzero((idx.year == y + yo) & (idx.month == mm))[-1] for yo, mm in hm])})
    return r1, r2, dP1, dP2, held, t1_idx, F1s, recs


def pairs_pandas_fixed(strip_root, days, recs, m_start):
    """Second path: the survival rule on the audit's own pivot at each recorded formation."""
    piv = R64.strip_pivot(strip_root, days, FFILL); yo2, m2 = hold_months(m_start)[-1]; out = []
    for r in recs:
        thr = (r["year"] + yo2) * 12 + m2 + 1; d = r["formation"]
        row = piv.loc[d].dropna() if d in piv.index else pd.Series(dtype=float)
        c = sorted(x for x in row.index if x >= thr)
        out.append((R68.ymlabel(c[0]) if c else None, R68.ymlabel(c[1]) if len(c) > 1 else None))
    return out


def audit_survival_fixed(mask, t1_idx, days, m_start):
    yo2, m2 = hold_months(m_start)[-1]; mo = np.array([int(d[:4]) * 12 + int(d[5:7]) for d in days])
    hm = hold_months(m_start)
    bad = []
    for t in np.flatnonzero(mask):
        y, m = int(days[t][:4]), int(days[t][5:7])
        # the window's formation year: the holding month (yo, m) belongs to formation year y - yo
        yo = [o for o, mm in hm if mm == m][0]
        if t1_idx[t] <= (y - yo + yo2) * 12 + m2:
            bad.append(t)
    if bad:
        raise AssertionError(f"SURVIVAL AUDIT: T1 delivers inside the window on {len(bad)} sessions (first {days[bad[0]]})")
    return int(mask.sum())


def cost_series_fixed(mask, F1s, side_cost_usd, upp, T):
    """Four sides a window in return space (per side: cost / one leg's notional at formation)."""
    c = np.zeros(T); cbp = side_cost_usd / (F1s * upp)
    for t in range(1, T):
        if mask[t] and not mask[t - 1]:
            c[t] += 2 * cbp[t]
        if mask[t] and (t + 1 >= T or not mask[t + 1]):
            c[t] += 2 * cbp[t]
    return np.nan_to_num(c)


def cost_series_rolled(mask, t1_idx, F1s, side_cost_usd, upp, T):
    c = np.zeros(T); cbp = side_cost_usd / (F1s * upp); prev = np.r_[-1, t1_idx[:-1]]
    for t in range(1, T):
        if mask[t] and not mask[t - 1]:
            c[t] += 2 * cbp[t]
        if mask[t] and (t + 1 >= T or not mask[t + 1]):
            c[t] += 2 * cbp[t]
        if mask[t] and mask[t - 1] and t1_idx[t] != prev[t]:
            c[t] += 4 * cbp[t]
    return np.nan_to_num(c)


def cost_usd_fixed(mask, side_cost_usd, T):
    c = np.zeros(T)
    for t in range(1, T):
        if mask[t] and not mask[t - 1]:
            c[t] += 2 * side_cost_usd
        if mask[t] and (t + 1 >= T or not mask[t + 1]):
            c[t] += 2 * side_cost_usd
    return c


def window_year_of(period, m_start=M_START):
    """Formation year of the window a positioned month belongs to."""
    for yo, mm in hold_months(m_start):
        if period.month == mm:
            return period.year - yo
    return None


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D570 -- soybean harvest spread on the F/H pair, flat by default (written as seen)\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ on any source")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start)
    days = gfull["days"]; T = len(days); idx = pd.to_datetime(days); me = R55.month_ends(days)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & (strip["root"] == ROOT)]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]
    years = list(range(2010, 2024))
    r1, r2, dP1, dP2, mB, t1B, F1B, recs = fixed_pair_series(A, cols, days, idx, M_START, years)
    yB = r1 - r2
    ra1, ra2, dPa1, dPa2, heldA, t1A, F1A, pairsA = R68.pair_series(A, cols, days, me)
    yA = ra1 - ra2
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG); dP_days, dL_days = days[wP], days[wL]
    mask_months = R68.season_mask(days, tuple(mm for _, mm in hold_months(M_START)))
    mA = mask_months & heldA
    upp_all, tick_all, comm_all, size_name = R56.min_size(gfull, gfull["roots"]); i_root = gfull["roots"].index(ROOT)
    upp, tick_usd, comm_rt = float(upp_all[i_root]), float(tick_all[i_root]), float(comm_all[i_root])
    meta = json.loads(R55.META.read_text(encoding="utf-8"))["specs"][ROOT]
    if meta.get("has_micro", False) or size_name[i_root] != ROOT or abs(upp - 50.0) > 1e-9 or abs(tick_usd - 12.5) > 1e-9:
        raise AssertionError(f"ZS specification: {size_name[i_root]} {upp} {tick_usd}")
    side_cost_usd = comm_rt / 2.0 + 0.5 * tick_usd
    log(f"  ZS: {T} sessions; B windows {len(recs)} ({recs[0]['year']}..{recs[-1]['year']}); ${upp:.0f}/point, tick ${tick_usd}, ${comm_rt:.0f} RT, no micro")

    # ---- the state variable (August WASDE) and the gate ----
    su_tab, n_wasde_all = R68.load_su(); su_by_year = {}; su_meta = {}
    for r in recs:
        s = R69.su_before(su_tab, r["formation"], r["year"]); su_by_year[r["year"]] = s["su"] if s else None; su_meta[r["year"]] = s
    gate = R68.gate_decisions(su_by_year)
    gate_session = np.zeros(T, dtype=bool)
    for t in np.flatnonzero(mB):
        gate_session[t] = bool(gate.get(window_year_of(pd.Timestamp(str(days[t])))) is True)
    mG = mB & gate_session
    log(f"  WASDE: {n_wasde_all} rows on disk, {len(su_tab)} scored (last {su_tab['ReleaseDate'].max()}); gate " +
        " ".join(f"{y}:{'open' if v else ('FLAT' if v is False else 'n/a')}" for y, v in gate.items()))

    # ---- audits ----
    audits = {}
    pb = pairs_pandas_fixed(strip, days, recs, M_START)
    audits["pairs_checked"] = R68.audit_pairs(recs, pb)
    R61._expect_raise(lambda: R68.audit_pairs(recs, pb[1:] + pb[:1]), "pair audit on shifted formations"); audits["pair_audit_raises_on_shifted_formation"] = True
    audits["survival_sessions"] = audit_survival_fixed(mB, t1B, days, M_START)
    R61._expect_raise(lambda: audit_survival_fixed(mB, t1A, days, M_START), "survival audit on the m+2 rule's pair (X in September)"); audits["survival_raises_on_m_plus_2_pair"] = True
    both = [r["both_settle_at_end"] and r["month_ends_settle"] for r in recs if r["year"] >= 2011]
    audits["held_contract_share"] = float(np.mean(both)); audits["held_contract_windows"] = len(both)
    if audits["held_contract_share"] < 1.0:
        raise AssertionError("HELD-CONTRACT AUDIT")
    mB_b = R68.season_mask_pandas(days, tuple(mm for _, mm in hold_months(M_START))) & mB
    audits["lag_mask_sessions"] = R68.audit_mask(mB, mB_b, me)
    form_ix = [np.flatnonzero(days == r["formation"])[0] for r in recs]
    bad_mask = mB.copy(); bad_mask[form_ix] = True
    R61._expect_raise(lambda: R68.audit_mask(bad_mask, mB_b, me), "lag audit on a formation-session mask"); audits["lag_raises_on_formation_session_mask"] = True
    pnl = np.where(mB, -(dP1 - dP2) * upp, 0.0)
    audits["sign_in_money_session"] = str(days[R65.audit_sign_in_money(pnl, dP1, dP2, mB, upp)])
    R61._expect_raise(lambda: R65.audit_sign_in_money(-pnl, dP1, dP2, mB, upp), "sign audit on a negated grid"); audits["sign_raises_on_negated_grid"] = True
    R61._expect_raise(lambda: R65.audit_sign_in_money(np.roll(pnl, 1), dP1, dP2, mB, upp), "sign audit on a mislagged grid"); audits["sign_raises_on_mislagged_grid"] = True
    audits["right_quantity_changes"] = R68.audit_right_quantity(mB, days)
    R61._expect_raise(lambda: R68.audit_right_quantity(np.arange(T) % 2 == 0, days), "right-quantity on a daily grid"); audits["right_quantity_raises_on_daily_grid"] = True
    audits["gate_windows_checked"] = R68.audit_gate(gate, R68.gate_decisions_pandas(su_by_year))
    gcur = R68.gate_decisions_pandas(su_by_year, shift=0); audits["gate_break_current_year_median_changes_decisions"] = bool(gcur != gate)
    if gcur != gate:
        R61._expect_raise(lambda: R68.audit_gate(gate, gcur), "gate audit on a current-year median"); audits["gate_raises_on_current_year_median"] = True
    ks_ = sorted(gate); shifted = {ks_[j]: gate[ks_[j - 1]] if j else None for j in range(len(ks_))}
    R61._expect_raise(lambda: R68.audit_gate(gate, shifted), "gate audit on shifted decisions"); audits["gate_raises_on_shifted_decisions"] = True
    log(f"  audits: {audits}")

    # ---- cells ----
    cells = {}; series = {}
    defs = (("B/harvest", np.where(mB, -yB, 0.0), mB, cost_series_fixed(mB, F1B, side_cost_usd, upp, T)),
            ("B/harvest/gated", np.where(mG, -yB, 0.0), mG, cost_series_fixed(mG, F1B, side_cost_usd, upp, T)),
            ("A/harvest/rolled", np.where(mA, -yA, 0.0), mA, cost_series_rolled(mA, t1A, F1A, side_cost_usd, upp, T)),
            ("control/A/always-on", np.where(heldA, -yA, 0.0), heldA, cost_series_rolled(heldA, t1A, F1A, side_cost_usd, upp, T)))
    for name, x, mask, c in defs:
        xn = x - c; mret = R68.monthly_returns(x, days, mask & wP); mretL = R68.monthly_returns(x, days, mask & wL); pos = mask & wP
        nwin = len(set(window_year_of(p) for p in mret.index)) if len(mret) else 0
        cells[name] = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"), "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                       "positioned_sessions_primary": int(pos.sum()), "mean_per_positioned_day": float(x[pos].mean()) if pos.any() else None,
                       "sharpe_positioned_days_only": R55.sharpe(x[pos]) if pos.sum() > 2 else None, "cost_per_window_bp": float(c[wP].sum() / max(nwin, 1) * 1e4),
                       "breakeven_bp_per_side": float(mret.sum() / max(nwin, 1) * 1e4 / SIDES_PER_WINDOW) if len(mret) else None,
                       "months": {"n": int(len(mret)), "mean": float(mret.mean()), "median": float(mret.median()), "hit": float((mret > 0).mean()), "worst": float(mret.min()), "best": float(mret.max()), "sd": float(mret.std(ddof=1))} if len(mret) else None,
                       "months_long_window": {"n": int(len(mretL)), "mean": float(mretL.mean()), "median": float(mretL.median()), "hit": float((mretL > 0).mean()), "worst": float(mretL.min()), "best": float(mretL.max())} if len(mretL) else None}
        series[name] = dict(x=x, xn=xn, c=c, mask=mask, mret=mret, mretL=mretL)
        g = cells[name]["gross"]; mm = cells[name]["months"]
        log(f"  {name:20s} gross Sh {g['sharpe']:+.3f} / So {g['sortino']:+.3f} (SE {g['se']:.2f})  net {cells[name]['net']['sharpe']:+.3f} / {cells[name]['net']['sortino']:+.3f}  "
            + (f"months n {mm['n']} mean {mm['mean']*100:+.2f}% median {mm['median']*100:+.2f}% hit {mm['hit']:.2f} worst {mm['worst']*100:+.2f}%  " if mm else "")
            + f"per-day {(cells[name]['mean_per_positioned_day'] or 0)*1e4:+.2f} bp  cost/window {cells[name]['cost_per_window_bp']:.1f} bp")

    # ---- per window, per month, per year (B) ----
    mretL = series["B/harvest"]["mretL"]; xB = series["B/harvest"]["x"]
    cost_usd = cost_usd_fixed(mB, side_cost_usd, T); pnl_n = pnl - cost_usd
    pm_usd = pd.Series(pnl_n, index=idx); pm_usd = pm_usd[mB].groupby(pm_usd[mB].index.to_period("M")).sum()
    per_window = []
    for r in recs:
        if r["year"] < 2011:
            continue
        months = mretL[[window_year_of(p) == r["year"] for p in mretL.index]]; pmu = pm_usd[[window_year_of(p) == r["year"] for p in pm_usd.index]]
        per_window.append({"window": f"{r['year']}", "formation": r["formation"], "exit": r["exit"], "t1": r["t1"], "t2": r["t2"], "F1": r["F1"], "basis0_cents": r["basis0_cents"],
                           "su": su_by_year.get(r["year"]), "su_release": su_meta[r["year"]]["release"] if su_meta.get(r["year"]) else None, "gate": gate.get(r["year"]),
                           "months": {str(p): float(v) for p, v in months.items()}, "ret": float(months.sum()), "usd_net": float(pmu.sum()), "in_primary": bool(r["year"] >= 2016)})
    per_mos = {mm: {"n": int((mretL.index.month == mm).sum()), "mean": float(mretL[mretL.index.month == mm].mean()), "hit": float((mretL[mretL.index.month == mm] > 0).mean()),
                    "worst": float(mretL[mretL.index.month == mm].min()), "best": float(mretL[mretL.index.month == mm].max())} for _, mm in hold_months(M_START)}
    per_year = {yv: {"sharpe": R55.sharpe(xB[np.array([d[:4] == yv for d in days])]), "total": float(xB[np.array([d[:4] == yv for d in days])].sum())} for yv in sorted(set(d[:4] for d in days[wL]))}
    log("  windows: " + " ".join(f"{w['window']}:{w['ret']*100:+.2f}%{'/G' if w['gate'] else ('/f' if w['gate'] is False else '')}" for w in per_window))
    log("  per month: " + "  ".join(f"{m}: mean {v['mean']*100:+.2f}% hit {v['hit']:.2f} worst {v['worst']*100:+.2f}%" for m, v in per_mos.items()))

    # ---- the gate (seen), 2012 ----
    dec = [w for w in per_window if w["gate"] is not None]; opn = [w for w in dec if w["gate"]]
    gate_out = {"rule": "open iff the August stocks-to-use <= the median of every prior August's (>= 3 prior)", "decisions": {str(k): v for k, v in gate.items()}, "su_by_year": {str(k): v for k, v in su_by_year.items()},
                "open_windows": [w["window"] for w in opn], "decidable": [w["window"] for w in dec],
                "ungated_mean": float(np.mean([w["ret"] for w in dec])), "ungated_hit": float(np.mean([w["ret"] > 0 for w in dec])),
                "gated_mean": float(np.mean([w["ret"] for w in opn])) if opn else None, "gated_hit": float(np.mean([w["ret"] > 0 for w in opn])) if opn else None,
                "flat_mean": float(np.mean([w["ret"] for w in dec if not w["gate"]])) if any(not w["gate"] for w in dec) else None,
                "open_in_sample": [w["window"] for w in opn if w["in_primary"]]}
    wv = {w["window"]: w["ret"] for w in per_window}; ex = np.array([v for k, v in wv.items() if k != "2012"]); allv = np.array(list(wv.values()))
    ex2012 = {"mean": float(ex.mean()), "hit": float((ex > 0).mean()), "n": int(ex.size), "share_2012": float(wv["2012"] / allv.sum()) if allv.sum() != 0 else None}
    log(f"  gate (seen): open {gate_out['open_windows']} mean {(gate_out['gated_mean'] or 0)*100:+.2f}% hit {gate_out['gated_hit']} vs ungated {gate_out['ungated_mean']*100:+.2f}% hit {gate_out['ungated_hit']:.2f}; "
        f"ex-2012 mean {ex2012['mean']*100:+.2f}% pays {(ex>0).sum()}/{ex.size}, 2012 share {ex2012['share_2012']:.2f}")

    # ---- N1: the schedule over A's always-on series (exact, purged 252) ----
    live_idx = [np.flatnonzero(heldA & wP)]; L = int(wP.sum())
    m1 = np.where(wP, mA, False).astype(float)[None, :]
    for k in GUARD_OFFSETS:
        k = k % (L - 1) or 1
        mr = R55.rotate_signs(m1, live_idx, k)[0] > 0
        a1 = np.where(mr, -yA, 0.0)[wP]; a2 = np.array([(-yA[t] if mr[t] else 0.0) for t in np.flatnonzero(wP)])
        if not np.array_equal(a1, a2):
            raise AssertionError("exactness guard")
    audits["exactness_guard_offsets"] = len(GUARD_OFFSETS)
    nA = np.full(L - 1, np.nan); nA_s = np.full(L - 1, np.nan)
    for k in range(1, L):
        mr = R55.rotate_signs(m1, live_idx, k)[0] > 0; xr = np.where(mr, -yA, 0.0)[wP]; nA[k - 1] = R55.sharpe(xr); nA_s[k - 1] = R55.sortino(xr)
    ks = np.arange(1, L); keep = (ks >= R55.NULL_PURGE) & (ks <= L - R55.NULL_PURGE); c_ = nA[keep]; cs_ = nA_s[keep]
    oA = cells["A/harvest/rolled"]["gross"]["sharpe"]
    n1 = {"object": "A under the harvest mask, rotated over A always-on", "offsets_enumerated": int(nA.size), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keep.sum()),
          "observed": oA, "p05": float(np.percentile(c_, 5)), "p50": float(np.percentile(c_, 50)), "p95": float(np.percentile(c_, 95)), "sd": float(c_.std(ddof=1)), "pct_rank": float((c_ < oA).mean()),
          "clears_p95": bool(oA > np.percentile(c_, 95)), "p95_se": 0.0, "sortino": {"observed": cells["A/harvest/rolled"]["gross"]["sortino"], "p50": float(np.nanpercentile(cs_, 50)), "p95": float(np.nanpercentile(cs_, 95))},
          "offset_profile": {"k": ks.tolist(), "sharpe": nA.tolist()}}
    log(f"  N1 (schedule on A): observed {oA:+.3f} p05 {n1['p05']:+.3f} p50 {n1['p50']:+.3f} p95 {n1['p95']:+.3f} rank {n1['pct_rank']:.3f} ({keep.sum()} offsets exact)")

    # ---- N2: the construction placed at each of the twelve months ----
    placements = {}
    for m_start in range(1, 13):
        yrs = list(range(2010, 2024))
        pr1, pr2, _, _, pm_, _, _, precs = fixed_pair_series(A, cols, days, idx, m_start, yrs)
        xp = np.where(pm_, -(pr1 - pr2), 0.0)
        if m_start == M_START and not (np.array_equal(xp, np.where(mB, -yB, 0.0))):
            raise AssertionError("N2 BY CONSTRUCTION: placement 9 does not reproduce the primary")
        placements[m_start] = {"sharpe_primary": R55.sharpe(xp[wP]), "sortino_primary": R55.sortino(xp[wP]), "sharpe_long": R55.sharpe(xp[wL]), "sortino_long": R55.sortino(xp[wL]),
                               "mean_per_positioned_day_long": float(xp[pm_ & wL].mean()) if (pm_ & wL).any() else None, "windows": len([r for r in precs if r["year"] >= 2011]),
                               "months": [mm for _, mm in hold_months(m_start)], "pair_first_window": (precs[0]["t1"], precs[0]["t2"]) if precs else None}
    audits["n2_placement_9_reproduces_primary"] = True
    oB = cells["B/harvest"]["gross"]["sharpe"]; oG = cells["B/harvest/gated"]["gross"]["sharpe"]
    sp = {m: v["sharpe_primary"] for m, v in placements.items()}; sl = {m: v["sharpe_long"] for m, v in placements.items()}
    others_p = [v for m, v in sp.items() if m != M_START]; others_l = [v for m, v in sl.items() if m != M_START]
    n2 = {"placements": placements, "primary_rank_of_12": int(sum(1 for v in sp.values() if v < sp[M_START])) , "best_of_12_primary": bool(sp[M_START] > max(others_p)),
          "long_rank_of_12": int(sum(1 for v in sl.values() if v < sl[M_START])), "best_of_12_long": bool(sl[M_START] > max(others_l)),
          "second_best_primary": int(max((m for m in sp if m != M_START), key=lambda m: sp[m])), "median_other_placements_primary": float(np.median(others_p)), "max_other_primary": float(max(others_p)),
          "family_best": max(oB, oG), "family_best_cell": "B/harvest" if oB >= oG else "B/harvest/gated", "family_best_beats_all_other_placements": bool(max(oB, oG) > max(others_p)),
          "placement_11_negative_primary": bool(sp[11] < 0), "placement_11_negative_long": bool(sl[11] < 0)}
    log("  N2 placements (Sharpe 2016-23 / 2011-23): " + " ".join(f"m{m}:{sp[m]:+.2f}/{sl[m]:+.2f}" for m in range(1, 13)))
    log(f"  N2: primary rank {n2['primary_rank_of_12']}/11 others (best of 12: {n2['best_of_12_primary']}); long {n2['long_rank_of_12']}/11 (best: {n2['best_of_12_long']}); second best m{n2['second_best_primary']} {n2['max_other_primary']:+.2f}")

    # ---- control ----
    ctrl = cells["control/A/always-on"]; cA = cells["A/harvest/rolled"]; cB = cells["B/harvest"]
    control = {"sharpe": ctrl["gross"]["sharpe"], "sortino": ctrl["gross"]["sortino"], "net_sharpe": ctrl["net"]["sharpe"], "mean_per_positioned_day": ctrl["mean_per_positioned_day"],
               "B_mean_per_positioned_day": cB["mean_per_positioned_day"], "A_masked_mean_per_positioned_day": cA["mean_per_positioned_day"],
               "B_beats_control": bool(cB["mean_per_positioned_day"] > ctrl["mean_per_positioned_day"]), "control_nonpositive": bool(ctrl["mean_per_positioned_day"] <= 0),
               "B_beats_A_masked": bool(cB["mean_per_positioned_day"] > cA["mean_per_positioned_day"]),
               "off_window_mean_per_day": float((-yA)[heldA & wP & ~mA].mean()), "by_calendar_month_bp_long": {m: float((-yA)[heldA & wL & (idx.month == m)].mean() * 1e4) for m in range(1, 13)}}
    log(f"  control: A always-on {control['mean_per_positioned_day']*1e4:+.2f} bp/day (Sharpe {control['sharpe']:+.2f}); B {control['B_mean_per_positioned_day']*1e4:+.2f}; A masked {control['A_masked_mean_per_positioned_day']*1e4:+.2f}")

    # ---- the COT figure (seen; recorded) ----
    cot = pd.read_csv(R68.COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "legacy") & (cot["category"] == "commercial") & (cot["report_date"] < RESERVED_FROM)].copy().sort_values("report_date")
    cot["nss"] = (cot["short"] - cot["long"]) / cot["open_interest"]; crow = []
    for w in per_window:
        c0 = cot[cot["report_date"] < w["formation"]]; c1 = cot[cot["report_date"] < w["exit"]]
        crow.append({"window": w["window"], "nss_formation": float(c0.iloc[-1]["nss"]), "nss_end": float(c1.iloc[-1]["nss"]), "falls": bool(c1.iloc[-1]["nss"] < c0.iloc[-1]["nss"])})
    cot_record = {"windows": crow, "falls": sum(x["falls"] for x in crow), "of": len(crow), "note": "seen in D569; no avatar claim is made; recorded"}

    # ---- component line ----
    posP = mB & wP
    comp = {"gross": R55.stats_block(pnl[wP], dP_days, "ZS F/H short Sep-Nov"), "net": R55.stats_block(pnl_n[wP], dP_days, "ZS F/H short Sep-Nov net"),
            "C_a_net_sharpe": R55.sharpe(pnl_n[wP]), "C_a_net_sortino": R55.sortino(pnl_n[wP]), "C_c_skew": float(pd.Series(pnl_n[wP]).skew()),
            "C_d_sigma_daily_usd_all_sessions": float(pnl_n[wP].std(ddof=1)), "C_d_sigma_daily_usd_positioned": float(pnl_n[posP].std(ddof=1)),
            "total_usd": float(pnl_n[wP].sum()), "gross_usd": float(pnl[wP].sum()), "cost_usd": float(cost_usd[wP].sum()), "max_dd_usd": R55.max_drawdown(pnl_n[wP]),
            "hit_positioned_sessions": float((pnl_n[posP] > 0).mean()), "per_window_usd": {w["window"]: w["usd_net"] for w in per_window},
            "total_usd_2011_2023": float(pnl_n[wL].sum()),
            "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L is not on disk; expected near zero by instrument and clock",
            "fails": [c for c, bad in (("C-a", R55.sharpe(pnl_n[wP]) <= 0.5), ("C-c", pd.Series(pnl_n[wP]).skew() < -0.5), ("C-d", pnl_n[posP].std(ddof=1) > R55.C_D_SIGMA)) if bad]}
    log(f"  component: net Sh {comp['C_a_net_sharpe']:+.3f} So {comp['C_a_net_sortino']:+.3f} skew {comp['C_c_skew']:+.2f} sigma positioned ${comp['C_d_sigma_daily_usd_positioned']:,.0f} "
        f"total ${comp['total_usd']:+,.0f} (gross ${comp['gross_usd']:+,.0f}, cost ${comp['cost_usd']:,.0f}) maxDD ${comp['max_dd_usd']:,.0f}; fails {comp['fails']}")

    # ---- predictions and verdict ----
    pm = cB["months"]; wL13 = [w for w in per_window]; hit_win = float(np.mean([w["ret"] > 0 for w in wL13])); worst_win = float(min(w["ret"] for w in wL13))
    cost_share = comp["cost_usd"] / comp["gross_usd"] if comp["gross_usd"] > 0 else None
    preds = {
        "P-1": {"claim": "B gross Sharpe 2016-2023 > 0; point 0.5-1.2", "value": oB, "holds": bool(oB > 0), "in_point_range": bool(0.5 <= oB <= 1.2)},
        "P-2": {"claim": "months hit >= 0.60, median > 0; windows 2011-2023 hit >= 0.75", "hit_months": pm["hit"], "median": pm["median"], "hit_windows": hit_win, "holds": bool(pm["hit"] >= 0.60 and pm["median"] > 0 and hit_win >= 0.75)},
        "P-3": {"claim": "B per day > 0 and > A masked; A always-on <= 0", "holds": bool(cB["mean_per_positioned_day"] > 0 and control["B_beats_A_masked"] and control["control_nonpositive"])},
        "P-4": {"claim": "A masked N1 rank >= 0.90 on 2016-2023", "value": n1["pct_rank"], "holds": bool(n1["pct_rank"] >= 0.90)},
        "P-5": {"claim": "B best of twelve placements on both windows; placement 11 negative", "best_primary": n2["best_of_12_primary"], "best_long": n2["best_of_12_long"], "p11_neg": n2["placement_11_negative_primary"],
                "holds": bool(n2["best_of_12_primary"] and n2["best_of_12_long"] and n2["placement_11_negative_primary"])},
        "P-6": {"claim": "seen: gated mean >= ungated, gated hit >= ungated; opens 2016, 2021, 2022, 2023 in sample", "gated_mean": gate_out["gated_mean"], "ungated_mean": gate_out["ungated_mean"], "open_in_sample": gate_out["open_in_sample"],
                "holds": bool(opn and gate_out["gated_mean"] >= gate_out["ungated_mean"] and gate_out["gated_hit"] >= gate_out["ungated_hit"] and gate_out["open_in_sample"] == ["2016", "2021", "2022", "2023"])},
        "P-7": {"claim": "ex-2012 mean >= +0.25%, pays >= 9 of 12; 2012 <= 55% of total", **ex2012, "holds": bool(ex2012["mean"] >= 0.0025 and ex2012["hit"] * ex2012["n"] >= 9 and (ex2012["share_2012"] or 1) <= 0.55)},
        "P-8": {"claim": "worst month 2011-2023 > -1.5%; worst window > -0.5%", "worst_month": cB["months_long_window"]["worst"], "worst_window": worst_win, "holds": bool(cB["months_long_window"]["worst"] > -0.015 and worst_win > -0.005)},
        "P-9": {"claim": "dollar sigma positioned < $150", "value": comp["C_d_sigma_daily_usd_positioned"], "holds": bool(comp["C_d_sigma_daily_usd_positioned"] < 150)},
        "P-10": {"claim": "cost < 20% of gross in dollars 2016-2023", "cost_share": cost_share, "holds": bool(cost_share is not None and cost_share < 0.20)},
        "P-11": {"claim": "falsifiers", "B_not_best_of_12": bool(not n2["best_of_12_primary"]), "A_below_n1_p50": bool(oA < n1["p50"]), "B_per_day_below_A": bool(not control["B_beats_A_masked"]),
                 "gated_hit_below_ungated": bool(opn and gate_out["gated_hit"] < gate_out["ungated_hit"])},
    }
    passes = bool(oB > 0 and n2["best_of_12_primary"] and n1["clears_p95"] and control["B_beats_control"] and control["control_nonpositive"])
    verdict = {"declared": "PASS" if passes else "DOES NOT PASS",
               "ledger": ("CLEARS C-a" if not comp["fails"] else f"fails {comp['fails']}") + ("; entry #4 if PASS" if passes and not comp["fails"] else "") + ("; PROVISIONAL under D468" if (not passes) and (not comp["fails"]) else ""),
               "avatar": "UNSUPPORTED (no claim made; recorded)"}
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "P-11") + f"; P-11 {preds['P-11']}")
    log(f"  VERDICT {verdict['declared']} / ledger {verdict['ledger']}")

    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak), simple-return units for the return-space cells, dollars for the ZS book (D542).", "record": "D542"},
           "spec": "D570", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "strip_sha256": R55.sha256(R56.STRIP), "cot_sha256": R55.sha256(R68.COT), "wasde_sha256": R55.sha256(R68.FIX_SU),
           "wasde_rows_scored": {"on_disk": n_wasde_all, "scored": int(len(su_tab)), "last_release_scored": su_tab["ReleaseDate"].max()},
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum())},
           "construction": {"root": ROOT, "placement_month": M_START, "hold_months": HOLD_MONTHS, "rule": "T1 first delivery strictly after the third holding month, T2 next listed; fixed for the window", "sign": "-1: short T1 / long T2",
                            "size": "one ZS a leg (no micro)", "usd_per_point": upp, "tick_usd": tick_usd, "commission_rt": comm_rt, "sides_per_window": SIDES_PER_WINDOW, "formation_ffill_sessions": FFILL,
                            "written_as_seen": "D567 Stage 0 and D569 addendum read this object's per-year, per-month, gate, control and COT figures on 2011-2023 before this pre-registration"},
           "pairs": [r for r in recs if r["year"] >= 2011], "cells": cells, "primary": {"cell": "B/harvest", "sharpe": oB, "sortino": cB["gross"]["sortino"], "se": cB["gross"]["se"]},
           "null_n1": n1, "null_n2": n2, "control": control,
           "positions": {"B_months_2016_2023": [(str(p), float(v)) for p, v in series["B/harvest"]["mret"].items()], "B_months_2011_2023": [(str(p), float(v)) for p, v in mretL.items()],
                         "gated_months_2016_2023": [(str(p), float(v)) for p, v in series["B/harvest/gated"]["mret"].items()]},
           "per_window": per_window, "per_month_of_window": per_mos, "per_year": per_year, "gate": {**gate_out, "ex_2012": ex2012}, "cot_record": cot_record,
           "component_line": comp, "predictions": preds, "verdict": verdict, "audits": audits, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: a synthetic ZS strip (F H K N Q U X) with a known harvest widening
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D570 SELF-TEST -- synthetic strip, no fixture read\n")
    rng = np.random.default_rng(70)
    days = pd.bdate_range("2011-01-03", "2016-12-30").strftime("%Y-%m-%d").to_numpy(); T = len(days); idx = pd.to_datetime(days); me = R55.month_ends(days)
    listed = (1, 3, 5, 7, 8, 9, 11); rows = []; spot = 1000.0; disc = {}
    for t, d in enumerate(days):
        spot *= math.exp(0.01 * rng.standard_normal()); y_, m_ = int(d[:4]), int(d[5:7]); cur = y_ * 12 + m_
        for key in range(cur + 1, cur + 16):
            if (key % 12 or 12) not in listed:
                continue
            dm = key - cur
            if m_ in (9, 10, 11):
                disc[key] = disc.get(key, 0.0) + 0.004 / dm          # the nearer contract loses more: the short spread pays
            dy, dmo = divmod(key - 1, 12); dmo += 1
            rows.append(("ZS", f"ZS{'FGHJKMNQUVXZ'[dmo - 1]}{dy % 10}", d, spot * math.exp(0.004 * dm) * math.exp(-disc.get(key, 0.0))))
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    A, cols = R64.strip_tables(strip, days, ["ZS"])["ZS"]
    years = list(range(2011, 2017))
    r1, r2, dP1, dP2, mB, t1B, F1B, recs = fixed_pair_series(A, cols, days, idx, M_START, years); yB = r1 - r2
    # [1] the survival rule gives F/H at an August formation; the pandas path agrees; RAISES on a shift
    pb = pairs_pandas_fixed(strip, days, recs, M_START); R68.audit_pairs(recs, pb)
    R61._expect_raise(lambda: R68.audit_pairs(recs, pb[1:] + pb[:1]), "pair audit on shifted formations")
    if not all(r["t1"] == f"{r['year']+1}-01" and r["t2"] == f"{r['year']+1}-03" for r in recs):
        raise AssertionError("pair is not F/H")
    print("  [1] at the last session before September the pair is next January / next March; the pandas path agrees and RAISES on a shift")
    # [2] the widening is recovered in the window; the always-on cousin earns nothing off-window
    ra1, ra2, _, _, heldA, t1A, _, _ = R68.pair_series(A, cols, days, me); yA = ra1 - ra2
    mA = R68.season_mask(days, (9, 10, 11)) & heldA
    on = (-yB)[mB]; off = (-yA)[heldA & ~mA]
    if not (on.mean() > 0 and abs(off.mean()) < on.mean() / 5):
        raise AssertionError(f"premium on {on.mean():.6f} off {off.mean():.6f}")
    print(f"  [2] the short F/H spread earns {on.mean()*1e4:+.2f} bp/day in the window; the rolled cousin {off.mean()*1e4:+.2f} bp/day outside it")
    # [3] survival: RAISES on the m+2 rule's pair (X in September)
    audit_survival_fixed(mB, t1B, days, M_START)
    R61._expect_raise(lambda: audit_survival_fixed(mB, t1A, days, M_START), "survival audit on the m+2 rule's pair")
    print("  [3] every positioned session's T1 delivers after November; the audit RAISES on the m+2 rule's November contract")
    # [4] lag, sign (short), right quantity
    mB_b = R68.season_mask_pandas(days, (9, 10, 11)) & mB; R68.audit_mask(mB, mB_b, me)
    form_ix = [np.flatnonzero(days == r["formation"])[0] for r in recs]; bad = mB.copy(); bad[form_ix] = True
    R61._expect_raise(lambda: R68.audit_mask(bad, mB_b, me), "lag audit on a formation-session mask")
    pnl = np.where(mB, -(dP1 - dP2) * 50.0, 0.0); R65.audit_sign_in_money(pnl, dP1, dP2, mB, 50.0)
    R61._expect_raise(lambda: R65.audit_sign_in_money(-pnl, dP1, dP2, mB, 50.0), "sign audit on a negated grid")
    R61._expect_raise(lambda: R65.audit_sign_in_money(np.roll(pnl, 1), dP1, dP2, mB, 50.0), "sign audit on a mislagged grid")
    R68.audit_right_quantity(mB, days); R61._expect_raise(lambda: R68.audit_right_quantity(np.arange(T) % 2 == 0, days), "right-quantity on a daily grid")
    print("  [4] lag, sign-in-money (short: pays -(dP1-dP2) x $50) and right-quantity audits pass and RAISE on their breaks")
    # [5] the gate (D568's machinery) on values where the two rules differ
    su2 = {2010: 0.15, 2011: 0.14, 2012: 0.16, 2013: 0.10, 2014: 0.15, 2015: 0.14, 2016: 0.12}
    g2 = R68.gate_decisions(su2); R68.audit_gate(g2, R68.gate_decisions_pandas(su2))
    R61._expect_raise(lambda: R68.audit_gate(g2, R68.gate_decisions_pandas(su2, shift=0)), "gate audit on a current-year median")
    print("  [5] the gate's two paths agree and the audit RAISES on a current-year median")
    # [6] N2 by construction and the placement: month 9 reproduces the primary and is the best of twelve on the synthetic widening
    best = None
    for m_start in range(1, 13):
        pr1, pr2, _, _, pm_, _, _, _ = fixed_pair_series(A, cols, days, idx, m_start, years); xp = np.where(pm_, -(pr1 - pr2), 0.0)
        if m_start == M_START and not np.array_equal(xp, np.where(mB, -yB, 0.0)):
            raise AssertionError("placement 9 != primary")
        s = R55.sharpe(xp); best = (s, m_start) if best is None or s > best[0] else best
    if best[1] != M_START:
        raise AssertionError(f"best placement {best}")
    print("  [6] placement 9 reproduces the primary's series exactly and is the best of the twelve placements on the synthetic widening")
    print("\nSELF-TEST PASSED"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
