"""D568 -- the corn post-harvest carry narrowing, flat by default (spec 752041d, R8).

Long T1 (the grains delivery rule, delivery >= m+2), short T2 (next listed), one ZC a leg, positioned on every
session of December, January and February (formed at the last session before December; the pair re-read at
each month-end under the same rule and asserted to survive the window); flat March..November. The always-on
spread return y_t = r1_t - r2_t is built on EVERY session (pairs formed at every month-end); the primary is +y
under the window mask, the secondary is +y under the mask gated on the November stocks-to-use (<= the median
of every prior November's, at least three), the control is +y everywhere. N1 rotates the mask through the
calendar (purged 252, enumerated): the placement null. The 2024+ slice is never read on any source.
Usage:  python scripts/run_d568_corn_post_harvest_carry.py [--selftest]
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


R65 = _load("d565", "run_d565_ng_winter_spread.py")     # loads D564/D561/D557/D556/D555 once
R64, R61, R56, R55 = R65.R64, R65.R61, R65.R56, R65.R55

OUT = REPO / "data" / "d568_corn_post_harvest_carry.json"
COT = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
FIX_SU = REPO / "data" / "fixtures" / "wasde_grains_su.csv"
SPEC = "752041d"
ROOT = "ZC"
COMMODITY = "Corn"
WINDOW_MONTHS = (12, 1, 2)                 # December 1 -> the last session of February
WINDOW_LAST_MONTH = 2
FFILL = R64.FFILL_FORMATION
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
SIDES_PER_WINDOW = 4                       # open two legs, close two legs
MIN_PRIOR_NOVEMBERS = 3
STORAGE_CENTS_PER_MONTH, INTEREST = 5.0, 0.025     # D567's full-carry convention, declared and flat
GUARD_OFFSETS = R61.GUARD_OFFSETS
N_PERM = 4000
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "strip_sha256", "cot_sha256", "wasde_sha256",
                    "wasde_rows_scored", "windows", "construction", "pairs", "cells", "primary", "null_n1", "null_n2", "control",
                    "positions", "per_window", "per_month_of_window", "per_year", "state", "gate", "cot_avatar", "component_line",
                    "predictions", "verdict", "audits", "timing"]

season_mask, season_mask_pandas = R65.season_mask, R65.season_mask_pandas
audit_pairs, audit_mask, audit_right_quantity, monthly_returns = R65.audit_pairs, R65.audit_mask, R65.audit_right_quantity, R65.monthly_returns


def ymlabel(c):
    """Delivery index year*12+month (month 1..12) -> 'YYYY-MM'. A December index is divisible by 12, so the year is
    (c-1)//12, not c//12 -- the earlier form printed December contracts one year late (label only; D571 erratum)."""
    return f"{(c - 1)//12}-{(c - 1)%12 + 1:02d}"


# --------------------------------------------------------------------------------------------
# the always-on pair series (the grains rule)
# --------------------------------------------------------------------------------------------
def pair_series(A, cols, days, me):
    """At every month-end k: T1/T2 by the grains delivery rule (delivery >= m+2); daily same-contract returns and
    price changes of the pair held through month k+1; the T1 delivery index on every held session (for the
    survival audit); the formation settlements and basis of the pair."""
    T = len(days); K = len(me)
    r1 = np.zeros(T); r2 = np.zeros(T); dP1 = np.zeros(T); dP2 = np.zeros(T); held = np.zeros(T, dtype=bool)
    t1_idx = np.full(T, -1, dtype=int); F1_at_formation = np.full(T, np.nan)
    pairs = []
    for k, t in enumerate(me):
        F = R64.formation_settles(A, t, FFILL)
        j1, j2 = R64.choose_nearby(A, cols, t, days[t], energy=False, ffill=FFILL)
        end = me[k + 1] if k + 1 < K else T - 1
        rec = {"formation": str(days[t]), "hold_month": str(days[min(t + 1, T - 1)])[:7], "t1": None, "t2": None, "basis": None,
               "basis_cents": None, "carry_ratio0": None, "F1": None, "both_settle_at_end": False}
        if j1 is not None and j2 is not None:
            rec["t1"] = ymlabel(cols[j1]); rec["t2"] = ymlabel(cols[j2])
            rec["basis"] = float(F[j2] / F[j1] - 1.0); rec["basis_cents"] = float(F[j2] - F[j1]); rec["F1"] = float(F[j1])
            months_between = int(cols[j2] - cols[j1])
            full_carry = (STORAGE_CENTS_PER_MONTH + INTEREST / 12.0 * F[j1]) * months_between
            rec["carry_ratio0"] = float((F[j2] - F[j1]) / full_carry) if full_carry > 0 else None
            prev1, prev2 = F[j1], F[j2]
            for u in range(t + 1, end + 1):
                v1, v2 = A[u, j1], A[u, j2]
                if np.isfinite(v1) and np.isfinite(prev1):
                    r1[u] = v1 / prev1 - 1.0; dP1[u] = v1 - prev1; prev1 = v1
                if np.isfinite(v2) and np.isfinite(prev2):
                    r2[u] = v2 / prev2 - 1.0; dP2[u] = v2 - prev2; prev2 = v2
                held[u] = True; t1_idx[u] = cols[j1]; F1_at_formation[u] = F[j1]
            Fe = R64.formation_settles(A, end, FFILL)
            rec["both_settle_at_end"] = bool(np.isfinite(Fe[j1]) and np.isfinite(Fe[j2]))
        pairs.append(rec)
    return r1, r2, dP1, dP2, held, t1_idx, F1_at_formation, pairs


def pairs_pandas(strip_root, days, me, months_ahead=2):
    """Second path for the pair audit: the delivery rule on the audit's own pivot."""
    piv = R64.strip_pivot(strip_root, days, FFILL)
    out = []
    for t in me:
        d = days[t]; y, m = int(d[:4]), int(d[5:7]); thr = y * 12 + m + months_ahead
        row = piv.loc[d].dropna() if d in piv.index else pd.Series(dtype=float)
        c = sorted(x for x in row.index if x >= thr)
        out.append((ymlabel(c[0]) if c else None, ymlabel(c[1]) if len(c) > 1 else None))
    return out


def window_end_index(day):
    """The month index (year*12+month) of the window's last month for a session inside the window."""
    y, m = int(day[:4]), int(day[5:7])
    return (y + 1) * 12 + WINDOW_LAST_MONTH if m == 12 else y * 12 + WINDOW_LAST_MONTH


def audit_survival(mask, t1_idx, days):
    """Every positioned session's T1 delivery month must be strictly after the window's last month."""
    bad = [t for t in np.flatnonzero(mask) if t1_idx[t] <= window_end_index(days[t])]
    if bad:
        raise AssertionError(f"SURVIVAL AUDIT: T1 expires inside the window on {len(bad)} sessions (first {days[bad[0]]}, T1 {ymlabel(t1_idx[bad[0]])})")
    return int(mask.sum())


def audit_sign_in_money_long(pnl, dP1, dP2, mask, upp):
    """On the positioned session with the largest dP1 - dP2, a LONG spread's dollar P&L must equal +(dP1 - dP2) x upp."""
    d = np.where(mask, dP1 - dP2, -np.inf); t = int(np.argmax(d))
    if not np.isfinite(d[t]) or d[t] <= 0:
        raise AssertionError("SIGN AUDIT: no positioned session with a positive front-minus-second move")
    want = d[t] * upp
    if pnl[t] != want:
        raise AssertionError(f"SIGN AUDIT: on {t} the book pays {pnl[t]:+.2f}, a long spread must pay {want:+.2f}")
    return t


# --------------------------------------------------------------------------------------------
# the state variable and the gate
# --------------------------------------------------------------------------------------------
def load_su(end_exclusive=RESERVED_FROM):
    w = pd.read_csv(FIX_SU, encoding="utf-8", dtype={"ReleaseDate": str, "Commodity": str, "MarketYear": str, "ProjEstFlag": str})
    n_all = len(w)
    w = w[w["ReleaseDate"] < end_exclusive].copy()
    if (w["ReleaseDate"] >= end_exclusive).any():
        raise AssertionError("reserved WASDE rows present")
    return w, n_all


def su_before(w, formation, my_year):
    """The last report released strictly before the formation session, for marketing year my_year/my_year+1."""
    c = w[(w["Commodity"] == COMMODITY) & (w["ReleaseDate"] < formation) & (w["MarketYear"] == f"{my_year}/{str(my_year + 1)[-2:]}")]
    if c.empty:
        return None
    r = c.sort_values("ReleaseDate").iloc[-1]
    return {"release": r["ReleaseDate"], "flag": r["ProjEstFlag"], "su": float(r["stocks_to_use"])}


def gate_decisions(su_by_year):
    """su_by_year: {formation year: S/U or None}. Open iff >= MIN_PRIOR_NOVEMBERS prior years are known and
    S/U <= the median of the prior years' values; None where the gate cannot decide."""
    out = {}
    for y in sorted(su_by_year):
        prior = [su_by_year[j] for j in su_by_year if j < y and su_by_year[j] is not None]
        v = su_by_year[y]
        out[y] = None if (v is None or len(prior) < MIN_PRIOR_NOVEMBERS) else bool(v <= float(np.median(prior)))
    return out


def gate_decisions_pandas(su_by_year, shift=1):
    s = pd.Series({y: v for y, v in sorted(su_by_year.items())}, dtype=float)
    med = s.shift(shift).expanding(min_periods=MIN_PRIOR_NOVEMBERS).median() if shift else s.expanding(min_periods=MIN_PRIOR_NOVEMBERS + 1).median()
    return {int(y): (None if (pd.isna(med[y]) or pd.isna(s[y])) else bool(s[y] <= med[y])) for y in s.index}


def audit_gate(a, b):
    if a != b:
        bad = [y for y in a if a.get(y) != b.get(y)]
        raise AssertionError(f"GATE AUDIT: the two paths disagree on {len(bad)} windows (first {bad[0] if bad else '?'})")
    return len(a)


def perm_p(a, b, n=N_PERM, seed=0):
    a = np.asarray(a, float); b = np.asarray(b, float); ok = np.isfinite(a) & np.isfinite(b); a, b = a[ok], b[ok]
    if a.size < 6:
        return float("nan"), float("nan"), int(a.size)
    rng = np.random.default_rng(seed); sa = pd.Series(a); obs = sa.corr(pd.Series(b), method="spearman")
    cnt = sum(1 for _ in range(n) if abs(sa.corr(pd.Series(rng.permutation(b)), method="spearman")) >= abs(obs))
    return float(obs), cnt / n, int(a.size)


def window_year_of(period):
    """The formation year of the window a positioned month belongs to (December y, January/February y+1 -> y)."""
    return period.year if period.month == 12 else period.year - 1


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D568 -- corn post-harvest carry narrowing, flat by default\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ on any source")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start)
    days = gfull["days"]; T = len(days); me = R55.month_ends(days)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & (strip["root"] == ROOT)]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]
    r1, r2, dP1, dP2, held, t1_idx, F1, pairs = pair_series(A, cols, days, me)
    y = r1 - r2                                            # always-on spread return, every session
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]
    mW = season_mask(days, WINDOW_MONTHS) & held
    upp_all, tick_all, comm_all, size_name = R56.min_size(gfull, gfull["roots"])
    i_root = gfull["roots"].index(ROOT); upp, tick_usd, comm_rt = float(upp_all[i_root]), float(tick_all[i_root]), float(comm_all[i_root])
    meta = json.loads(R55.META.read_text(encoding="utf-8"))["specs"][ROOT]
    if meta.get("has_micro", False) or size_name[i_root] != ROOT or abs(upp - 50.0) > 1e-9 or abs(tick_usd - 12.5) > 1e-9:
        raise AssertionError(f"ZC specification: size {size_name[i_root]} upp {upp} tick {tick_usd}")
    log(f"  ZC: {T} sessions, {len(me)} formations; pairs with both legs {sum(1 for p in pairs if p['t1'])}; ${upp:.0f}/point, tick ${tick_usd}, ${comm_rt:.0f} RT (full contract, no micro)")

    # ---- the state variable: the November WASDE before each formation ----
    su_tab, n_wasde_all = load_su()
    su_by_year = {}; su_meta = {}
    for yv in range(2010, 2024):
        f = [p for p in pairs if p["formation"][:7] == f"{yv}-11"]
        if not f:
            su_by_year[yv] = None; continue
        s = su_before(su_tab, f[0]["formation"], yv)
        su_by_year[yv] = s["su"] if s else None; su_meta[yv] = s
    gate = gate_decisions(su_by_year)
    log(f"  WASDE fixture: {n_wasde_all} rows on disk, {len(su_tab)} scored (releases < {RESERVED_FROM}: {su_tab['ReleaseDate'].nunique()} reports "
        f"{su_tab['ReleaseDate'].min()}..{su_tab['ReleaseDate'].max()})")
    log("  gate by formation year: " + " ".join(f"{yv}:{'open' if g else ('FLAT' if g is False else 'n/a')}({su_by_year[yv]:.3f})" if su_by_year[yv] is not None else f"{yv}:none" for yv, g in gate.items()))
    # the gated mask: a positioned session belongs to the window of its formation year
    gate_session = np.zeros(T, dtype=bool)
    for t in np.flatnonzero(mW):
        d = days[t]; yv = int(d[:4]) if int(d[5:7]) == 12 else int(d[:4]) - 1
        gate_session[t] = bool(gate.get(yv) is True)
    mG = mW & gate_session

    # ---- audits ----
    audits = {}
    pb = pairs_pandas(strip, days, me)
    audits["pairs_checked"] = audit_pairs(pairs, pb)
    R61._expect_raise(lambda: audit_pairs(pairs, pb[1:] + pb[:1]), "pair audit on shifted formations"); audits["pair_audit_raises_on_shifted_formation"] = True
    audits["survival_sessions"] = audit_survival(mW, t1_idx, days)
    # the >= m+1 rule's pair at a November formation is December's contract, which expires inside the window
    t1_bad = t1_idx.copy()
    for k, t in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else T - 1
        j1, _ = R64.choose_nearby(A, cols, t, days[t], energy=False, ffill=FFILL)
        if j1 is not None:
            yv, mv = int(days[t][:4]), int(days[t][5:7]); fin = np.isfinite(R64.formation_settles(A, t, FFILL))
            cand = np.flatnonzero(fin & (cols >= yv * 12 + mv + 1))
            if cand.size:
                t1_bad[t + 1:end + 1] = cols[cand[0]]
    R61._expect_raise(lambda: audit_survival(mW, t1_bad, days), "survival audit on the m+1 rule's pair"); audits["survival_raises_on_m_plus_1_pair"] = True
    both = [p["both_settle_at_end"] for p in pairs if p["t1"] and p["hold_month"] < RESERVED_FROM[:7] and int(p["hold_month"][5:7]) in WINDOW_MONTHS and p["hold_month"] >= "2011-01"]
    audits["held_contract_share"] = float(np.mean(both)); audits["held_contract_months"] = len(both)
    if audits["held_contract_share"] < 1.0:
        raise AssertionError("HELD-CONTRACT AUDIT: a leg failed to settle at a positioned month's last session")
    pair_changes_in_window = [(p["formation"], p["t1"], q["t1"]) for p, q in zip(pairs[:-1], pairs[1:])
                              if p["t1"] and q["t1"] and int(q["hold_month"][5:7]) in (1, 2) and (p["t1"], p["t2"]) != (q["t1"], q["t2"])]
    audits["pair_changes_inside_window"] = len(pair_changes_in_window)
    mW_b = season_mask_pandas(days, WINDOW_MONTHS) & held
    audits["lag_mask_sessions"] = audit_mask(mW, mW_b, me)
    bad_mask = mW.copy(); bad_mask[me[[k for k, t in enumerate(me) if t + 1 < T and mW[t + 1] and not mW[t]]]] = True
    R61._expect_raise(lambda: audit_mask(bad_mask, mW_b, me), "lag audit on a formation-session mask"); audits["lag_raises_on_formation_session_mask"] = True
    pnl = np.where(mW, (dP1 - dP2) * upp, 0.0)
    audits["sign_in_money_session"] = str(days[audit_sign_in_money_long(pnl, dP1, dP2, mW, upp)])
    R61._expect_raise(lambda: audit_sign_in_money_long(-pnl, dP1, dP2, mW, upp), "sign audit on a negated grid"); audits["sign_raises_on_negated_grid"] = True
    R61._expect_raise(lambda: audit_sign_in_money_long(np.roll(pnl, 1), dP1, dP2, mW, upp), "sign audit on a mislagged grid"); audits["sign_raises_on_mislagged_grid"] = True
    audits["right_quantity_changes"] = audit_right_quantity(mW, days)
    R61._expect_raise(lambda: audit_right_quantity((np.arange(T) % 2 == 0), days), "right-quantity audit on a daily grid"); audits["right_quantity_raises_on_daily_grid"] = True
    gate_b = gate_decisions_pandas(su_by_year)
    audits["gate_windows_checked"] = audit_gate(gate, gate_b)
    gate_cur = gate_decisions_pandas(su_by_year, shift=0)
    audits["gate_break_current_year_median_changes_decisions"] = bool(gate_cur != gate)
    if gate_cur != gate:
        R61._expect_raise(lambda: audit_gate(gate, gate_cur), "gate audit on a median that includes the current year"); audits["gate_raises_on_current_year_median"] = True
    ks_ = sorted(gate); shifted = {ks_[i]: gate[ks_[i - 1]] if i else None for i in range(len(ks_))}
    R61._expect_raise(lambda: audit_gate(gate, shifted), "gate audit on decisions shifted one window"); audits["gate_raises_on_shifted_decisions"] = True
    log(f"  audits: {audits}")

    # ---- cost in return space ----
    side_cost_usd = comm_rt / 2.0 + 0.5 * tick_usd
    cbp = side_cost_usd / (F1 * upp)                                # per side, as a fraction of one leg's notional
    t1_prev = np.r_[-1, t1_idx[:-1]]
    def cost_series(mask):
        c = np.zeros(T)
        for t in range(1, T):
            if mask[t] and not mask[t - 1]:
                c[t] += 2 * cbp[t]                                     # open two legs
            if mask[t] and (t + 1 >= T or not mask[t + 1]):
                c[t] += 2 * cbp[t]                                     # close two legs
            if mask[t] and mask[t - 1] and t1_idx[t] != t1_prev[t]:
                c[t] += 4 * cbp[t]                                     # the rule changed the pair: roll both legs
        return np.nan_to_num(c)
    def cost_usd_series(mask):
        c = np.zeros(T)
        for t in range(1, T):
            if mask[t] and not mask[t - 1]:
                c[t] += 2 * side_cost_usd
            if mask[t] and (t + 1 >= T or not mask[t + 1]):
                c[t] += 2 * side_cost_usd
            if mask[t] and mask[t - 1] and t1_idx[t] != t1_prev[t]:
                c[t] += 4 * side_cost_usd
        return c

    # ---- cells ----
    cells = {}; series = {}
    for name, mask in (("spread/window", mW), ("spread/window/gated", mG), ("control/always-on", held)):
        x = np.where(mask, y, 0.0); c = cost_series(mask); xn = x - c
        mret = monthly_returns(x, days, mask & wP); mretL = monthly_returns(x, days, mask & wL)
        pos_days = mask & wP
        n_windows_P = len(set(window_year_of(p) for p in mret.index)) if len(mret) else 0
        cells[name] = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                       "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                       "positioned_sessions_primary": int(pos_days.sum()), "mean_per_positioned_day": float(x[pos_days].mean()) if pos_days.any() else None,
                       "sharpe_positioned_days_only": R55.sharpe(x[pos_days]) if pos_days.sum() > 2 else None,
                       "sortino_positioned_days_only": R55.sortino(x[pos_days]) if pos_days.sum() > 2 else None,
                       "cost_per_window_bp": float(c[wP].sum() / max(n_windows_P, 1) * 1e4),
                       "sides_per_window_modelled": SIDES_PER_WINDOW,
                       "breakeven_bp_per_side": float(mret.sum() / max(n_windows_P, 1) * 1e4 / SIDES_PER_WINDOW) if len(mret) else None,
                       "months": {"n": int(len(mret)), "mean": float(mret.mean()), "median": float(mret.median()), "hit": float((mret > 0).mean()),
                                  "worst": float(mret.min()), "best": float(mret.max()), "sd": float(mret.std(ddof=1))} if len(mret) else None,
                       "months_long_window": {"n": int(len(mretL)), "mean": float(mretL.mean()), "median": float(mretL.median()), "hit": float((mretL > 0).mean()),
                                              "worst": float(mretL.min()), "best": float(mretL.max())} if len(mretL) else None}
        series[name] = dict(x=x, xn=xn, c=c, mask=mask, mret=mret, mretL=mretL)
        g = cells[name]["gross"]; mm = cells[name]["months"]
        log(f"  {name:20s} gross Sh {g['sharpe']:+.3f} / So {g['sortino']:+.3f} (SE {g['se']:.2f})  net {cells[name]['net']['sharpe']:+.3f} / {cells[name]['net']['sortino']:+.3f}  "
            + (f"months n {mm['n']} mean {mm['mean']*100:+.2f}% median {mm['median']*100:+.2f}% hit {mm['hit']:.2f} worst {mm['worst']*100:+.2f}%  " if mm else "")
            + f"per-day {(cells[name]['mean_per_positioned_day'] or 0)*1e4:+.2f} bp  cost/window {cells[name]['cost_per_window_bp']:.1f} bp")

    # ---- per window, per month of window, per year (primary, long window) ----
    mretL = series["spread/window"]["mretL"]
    x_prim = series["spread/window"]["x"]
    pnl_g = np.where(mW, (dP1 - dP2) * upp, 0.0); cost_usd = cost_usd_series(mW); pnl_n = pnl_g - cost_usd
    pnl_m = pd.Series(pnl_n, index=pd.to_datetime(days)); pnl_m = pnl_m[mW].groupby(pnl_m[mW].index.to_period("M")).sum()
    per_window = []
    for yv in sorted(set(window_year_of(p) for p in mretL.index)):
        months = mretL[[window_year_of(p) == yv for p in mretL.index]]
        f = [p for p in pairs if p["formation"][:7] == f"{yv}-11"]; f = f[0] if f else None
        pm = pnl_m[[window_year_of(p) == yv for p in pnl_m.index]]
        per_window.append({"window": f"{yv}-{str(yv+1)[-2:]}", "formation_year": yv, "formation": f["formation"] if f else None, "t1": f["t1"] if f else None, "t2": f["t2"] if f else None,
                           "basis0_cents": f["basis_cents"] if f else None, "carry_ratio0": f["carry_ratio0"] if f else None, "F1": f["F1"] if f else None,
                           "su": su_by_year.get(yv), "su_release": su_meta[yv]["release"] if su_meta.get(yv) else None, "gate": gate.get(yv),
                           "months": {str(p): float(v) for p, v in months.items()}, "n_months": int(len(months)), "complete": bool(len(months) == 3),
                           "in_primary": bool(any(str(p) >= PRIMARY[0][:7] for p in months.index)),
                           "ret": float(months.sum()), "usd_net": float(pm.sum()) if len(pm) else None})
    full = [w for w in per_window if w["complete"]]
    per_mos = {m: {"n": int((mretL.index.month == m).sum()), "mean": float(mretL[mretL.index.month == m].mean()), "hit": float((mretL[mretL.index.month == m] > 0).mean()),
                   "worst": float(mretL[mretL.index.month == m].min()), "best": float(mretL[mretL.index.month == m].max())} for m in WINDOW_MONTHS}
    per_year = {yv: {"sharpe": R55.sharpe(x_prim[np.array([d[:4] == yv for d in days])]), "total": float(x_prim[np.array([d[:4] == yv for d in days])].sum())} for yv in sorted(set(d[:4] for d in days[wL]))}
    log("  windows: " + " ".join(f"{w['window']}:{w['ret']*100:+.2f}%{'' if w['complete'] else '*'}{'/G' if w['gate'] else ('/f' if w['gate'] is False else '')}" for w in per_window))
    log("  per month of window: " + "  ".join(f"{m}: mean {v['mean']*100:+.2f}% hit {v['hit']:.2f} worst {v['worst']*100:+.2f}% (n {v['n']})" for m, v in per_mos.items()))

    # ---- the state (seen in Stage 0, recorded) and the real-time gate (unseen) ----
    fw = [w for w in full if 2011 <= w["formation_year"] <= 2022]
    su_v = np.array([w["su"] if w["su"] is not None else np.nan for w in fw]); ret_v = np.array([w["ret"] for w in fw]); cr_v = np.array([w["carry_ratio0"] if w["carry_ratio0"] is not None else np.nan for w in fw])
    rho_su, p_su, n_su = perm_p(su_v, ret_v); rho_cr, p_cr, n_cr = perm_p(cr_v, ret_v, seed=1)
    q = np.nanquantile(su_v, [1 / 3, 2 / 3]); terc = {}
    for name_, m_ in (("low", su_v <= q[0]), ("mid", (su_v > q[0]) & (su_v <= q[1])), ("high", su_v > q[1])):
        terc[name_] = {"n": int(m_.sum()), "su_mean": float(su_v[m_].mean()), "mean": float(ret_v[m_].mean()), "hit": float((ret_v[m_] > 0).mean())}
    state = {"windows": [w["window"] for w in fw], "n": len(fw), "spearman_su_ret": rho_su, "p_su": p_su, "spearman_carry_ratio0_ret": rho_cr, "p_carry": p_cr,
             "tercile_cuts_seen": [float(q[0]), float(q[1])], "terciles": terc, "note": "the per-window returns and the Spearman were SEEN in D567 Stage 0; the terciles are the seen cut"}
    dec = [w for w in full if w["gate"] is not None]
    dec_open = [w for w in dec if w["gate"]]
    gate_out = {"rule": f"open iff the November stocks-to-use <= the median of every prior November's (>= {MIN_PRIOR_NOVEMBERS} prior, fixture from 2010)",
                "decisions": {str(k): v for k, v in gate.items()}, "su_by_year": {str(k): v for k, v in su_by_year.items()},
                "decidable_full_windows": [w["window"] for w in dec], "open_windows": [w["window"] for w in dec_open],
                "ungated_mean_over_decidable": float(np.mean([w["ret"] for w in dec])) if dec else None, "ungated_hit_over_decidable": float(np.mean([w["ret"] > 0 for w in dec])) if dec else None,
                "gated_mean_over_open": float(np.mean([w["ret"] for w in dec_open])) if dec_open else None, "gated_hit_over_open": float(np.mean([w["ret"] > 0 for w in dec_open])) if dec_open else None,
                "flat_windows_mean": float(np.mean([w["ret"] for w in dec if not w["gate"]])) if any(not w["gate"] for w in dec) else None}
    log(f"  state (seen): Spearman S/U->window {rho_su:+.3f} p {p_su:.3f} (n {n_su}); carry ratio->window {rho_cr:+.3f} p {p_cr:.3f}; terciles " + "  ".join(f"{k}: S/U {v['su_mean']:.3f} ret {v['mean']*100:+.2f}% hit {v['hit']:.2f}" for k, v in terc.items()))
    log(f"  gate (unseen): open {gate_out['open_windows']}; gated mean {(gate_out['gated_mean_over_open'] or 0)*100:+.2f}% hit {gate_out['gated_hit_over_open']} vs ungated {(gate_out['ungated_mean_over_decidable'] or 0)*100:+.2f}% hit {gate_out['ungated_hit_over_decidable']} over {len(dec)} decidable windows; flat windows mean {(gate_out['flat_windows_mean'] or 0)*100:+.2f}%")

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
        mr = R55.rotate_signs(np.where(wP, mW, False).astype(float)[None, :], live_idx, k)[0] > 0
        a1 = np.where(mr, y, 0.0)[wP]; a2 = np.array([(y[t] if mr[t] else 0.0) for t in np.flatnonzero(wP)])
        if not np.array_equal(a1, a2):
            raise AssertionError("exactness guard")
    audits["exactness_guard_offsets"] = len(GUARD_OFFSETS)
    nW, nW_s = rotated_sharpes(mW, y); nG, nG_s = rotated_sharpes(mG, y)
    ks = np.arange(1, nW.size + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= int(wP.sum()) - R55.NULL_PURGE)
    def blk(col, cols_, obs, obs_s):
        c = col[keep]; cs = cols_[keep]
        return {"observed": obs, "p05": float(np.percentile(c, 5)), "p50": float(np.percentile(c, 50)), "p95": float(np.percentile(c, 95)), "sd": float(c.std(ddof=1)),
                "pct_rank": float((c < obs).mean()), "clears_p95": bool(obs > np.percentile(c, 95)), "p95_se": 0.0, "enumerated": True,
                "sortino": {"observed": obs_s, "p50": float(np.nanpercentile(cs, 50)), "p95": float(np.nanpercentile(cs, 95))},
                "unpurged": {"p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95))}}
    oW = cells["spread/window"]["gross"]["sharpe"]; oG = cells["spread/window/gated"]["gross"]["sharpe"]
    n1 = {"offsets_enumerated": int(nW.size), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keep.sum()),
          "per_cell": {"spread/window": blk(nW, nW_s, oW, cells["spread/window"]["gross"]["sortino"]),
                       "spread/window/gated": blk(nG, nG_s, oG, cells["spread/window/gated"]["gross"]["sortino"])},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": nW.tolist()}}
    fam = np.maximum(nW, nG)[keep]; obs_best = max(oW, oG)
    n2 = {"observed_best": obs_best, "observed_best_cell": "spread/window" if oW >= oG else "spread/window/gated", "p50": float(np.percentile(fam, 50)),
          "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < obs_best).mean()), "clears_p95": bool(obs_best > np.percentile(fam, 95))}
    primary = n1["per_cell"]["spread/window"]
    ctrl = cells["control/always-on"]
    control = {"sharpe": ctrl["gross"]["sharpe"], "sortino": ctrl["gross"]["sortino"], "net_sharpe": ctrl["net"]["sharpe"], "mean_per_positioned_day": ctrl["mean_per_positioned_day"],
               "primary_mean_per_positioned_day": cells["spread/window"]["mean_per_positioned_day"],
               "primary_beats_control_per_day": bool(cells["spread/window"]["mean_per_positioned_day"] > ctrl["mean_per_positioned_day"]),
               "primary_sharpe_above_control": bool(oW > ctrl["gross"]["sharpe"]),
               "off_window_mean_per_day": float(y[held & wP & ~mW].mean()), "off_window_sharpe": R55.sharpe(y[held & wP & ~mW]),
               "off_window_by_month": {m: float(y[held & wL & (np.array([int(d[5:7]) for d in days]) == m)].mean() * 1e4) for m in range(1, 13)}}
    log(f"  N1 primary: observed {oW:+.3f}  p05 {primary['p05']:+.3f} p50 {primary['p50']:+.3f} p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f} ({keep.sum()} offsets, exact); "
        f"gated cell {oG:+.3f} rank {n1['per_cell']['spread/window/gated']['pct_rank']:.3f}; N2 best {obs_best:+.3f} ({n2['observed_best_cell']}) p95 {n2['p95']:+.3f} rank {n2['pct_rank']:.3f}")
    log(f"  control always-on: Sharpe {control['sharpe']:+.3f} (net {control['net_sharpe']:+.3f}), per-day {control['mean_per_positioned_day']*1e4:+.2f} bp vs primary {control['primary_mean_per_positioned_day']*1e4:+.2f} bp; "
        f"off-window per-day {control['off_window_mean_per_day']*1e4:+.2f} bp (Sharpe {control['off_window_sharpe']:+.2f})")
    log("  always-on by calendar month, bp/day 2011-2023: " + " ".join(f"{m}:{v:+.1f}" for m, v in control["off_window_by_month"].items()))

    # ---- the avatar in the positioning data (P-8): commercial net short share falls through the window ----
    cot = pd.read_csv(COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "legacy") & (cot["category"] == "commercial") & (cot["report_date"] < RESERVED_FROM)].copy()
    cot["net_short_share"] = (cot["short"] - cot["long"]) / cot["open_interest"]; cot = cot.sort_values("report_date")
    rows = []
    for w in per_window:
        if not w["complete"] or w["formation"] is None:
            continue
        end_day = max(days[np.array([d[:7] == f"{w['formation_year']+1}-02" for d in days])])
        c0 = cot[cot["report_date"] < w["formation"]]; c1 = cot[cot["report_date"] < end_day]
        if len(c0) and len(c1):
            rows.append({"window": w["window"], "formation_year": w["formation_year"], "report_at_formation": c0.iloc[-1]["report_date"], "net_short_at_formation": float(c0.iloc[-1]["net_short_share"]),
                         "report_at_end": c1.iloc[-1]["report_date"], "net_short_at_end": float(c1.iloc[-1]["net_short_share"]),
                         "falls": bool(c1.iloc[-1]["net_short_share"] < c0.iloc[-1]["net_short_share"]), "ret": w["ret"]})
    rows12 = [r for r in rows if 2011 <= r["formation_year"] <= 2022]; rowsP = [r for r in rows12 if r["formation_year"] >= 2016]
    n_fall = sum(r["falls"] for r in rows12); n_fall_P = sum(r["falls"] for r in rowsP)
    rho_cot, p_cot, _ = perm_p([r["net_short_at_end"] - r["net_short_at_formation"] for r in rows12], [r["ret"] for r in rows12], seed=2)
    cot_avatar = {"windows": rows, "falls_2011_2022": n_fall, "of": len(rows12), "falls_in_sample": n_fall_P, "of_in_sample": len(rowsP),
                  "mean_change": float(np.mean([r["net_short_at_end"] - r["net_short_at_formation"] for r in rows12])) if rows12 else None,
                  "spearman_change_vs_ret": rho_cot, "p": p_cot}
    log(f"  COT avatar: commercial net short share falls through the window in {n_fall}/{len(rows12)} windows 2011-2022 ({n_fall_P}/{len(rowsP)} in sample); mean change {cot_avatar['mean_change']:+.4f}; "
        f"Spearman(change, window return) {rho_cot:+.3f} p {p_cot:.3f}")

    # ---- component line: the dollar book, one ZC a leg ----
    posP = mW & wP
    per_window_usd = {w["window"]: w["usd_net"] for w in per_window if w["usd_net"] is not None}
    comp = {"gross": R55.stats_block(pnl_g[wP], dP_days, "ZC H/K spread Dec-Feb"), "net": R55.stats_block(pnl_n[wP], dP_days, "ZC H/K spread Dec-Feb net"),
            "C_a_net_sharpe": R55.sharpe(pnl_n[wP]), "C_a_net_sortino": R55.sortino(pnl_n[wP]), "C_c_skew": float(pd.Series(pnl_n[wP]).skew()),
            "C_d_sigma_daily_usd_all_sessions": float(pnl_n[wP].std(ddof=1)), "C_d_sigma_daily_usd_positioned": float(pnl_n[posP].std(ddof=1)),
            "total_usd": float(pnl_n[wP].sum()), "cost_usd": float(cost_usd[wP].sum()), "max_dd_usd": R55.max_drawdown(pnl_n[wP]),
            "hit_positioned_sessions": float((pnl_n[posP] > 0).mean()), "per_window_usd": per_window_usd,
            "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk; expected near zero by instrument and clock (a ZC calendar spread held three months vs an NQ day session)",
            "fails": [c_ for c_, bad in (("C-a", R55.sharpe(pnl_n[wP]) <= 0.5), ("C-c", pd.Series(pnl_n[wP]).skew() < -0.5), ("C-d", pnl_n[posP].std(ddof=1) > R55.C_D_SIGMA)) if bad]}
    log(f"  component: net Sh {comp['C_a_net_sharpe']:+.3f} So {comp['C_a_net_sortino']:+.3f} skew {comp['C_c_skew']:+.2f} sigma positioned ${comp['C_d_sigma_daily_usd_positioned']:,.0f} (all ${comp['C_d_sigma_daily_usd_all_sessions']:,.0f}) "
        f"total ${comp['total_usd']:+,.0f} cost ${comp['cost_usd']:,.0f} maxDD ${comp['max_dd_usd']:,.0f}; fails {comp['fails']}")

    # ---- predictions ----
    pm = cells["spread/window"]["months"]; wfull = [w for w in full if 2011 <= w["formation_year"] <= 2022]
    hit_windows_L = float(np.mean([w["ret"] > 0 for w in wfull])); worst_window_L = float(min(w["ret"] for w in wfull))
    gross_mean_month = pm["mean"]; cost_month = cells["spread/window"]["cost_per_window_bp"] / 3.0 * 1e-4
    preds = {
        "P-1": {"claim": "primary gross Sharpe > 0, above N1 p95; point 0.3-0.9", "value": oW, "p95": primary["p95"], "holds": bool(oW > 0 and primary["clears_p95"]), "in_point_range": bool(0.3 <= oW <= 0.9)},
        "P-2": {"claim": "positioned months hit >= 0.55 and median > 0; windows 2011-2022 hit >= 0.65 (seen)", "hit_months": pm["hit"], "median_month": pm["median"], "hit_windows": hit_windows_L,
                "holds": bool(pm["hit"] >= 0.55 and pm["median"] > 0 and hit_windows_L >= 0.65)},
        "P-3": {"claim": "primary beats the always-on control per positioned day and on Sharpe", "holds": bool(control["primary_beats_control_per_day"] and control["primary_sharpe_above_control"])},
        "P-4": {"claim": "primary N1 rank >= 0.90", "value": primary["pct_rank"], "holds": bool(primary["pct_rank"] >= 0.90)},
        "P-5": {"claim": "primary worst month > -2%; worst window 2011-2022 > -1%", "worst_month": pm["worst"], "worst_window": worst_window_L, "holds": bool(pm["worst"] > -0.02 and worst_window_L > -0.01)},
        "P-6a": {"claim": "seen: Spearman(S/U, window return) 2011-2022 <= -0.3 with the tight tercile above the full", "rho": rho_su, "holds": bool(rho_su <= -0.3 and terc["low"]["mean"] > terc["high"]["mean"])},
        "P-6b": {"claim": "unseen: gated mean per positioned window >= ungated over the decidable windows, and hit likewise",
                 "gated_mean": gate_out["gated_mean_over_open"], "ungated_mean": gate_out["ungated_mean_over_decidable"], "gated_hit": gate_out["gated_hit_over_open"], "ungated_hit": gate_out["ungated_hit_over_decidable"],
                 "holds": bool(dec_open and gate_out["gated_mean_over_open"] >= gate_out["ungated_mean_over_decidable"] and gate_out["gated_hit_over_open"] >= gate_out["ungated_hit_over_decidable"])},
        "P-7": {"claim": "dollar book sigma over positioned sessions < $150", "value": comp["C_d_sigma_daily_usd_positioned"], "holds": bool(comp["C_d_sigma_daily_usd_positioned"] < 150)},
        "P-8": {"claim": "commercial net short share falls through the window in >= 8 of 12 (2011-2022) and >= 4 of 7 in sample", "value": n_fall, "of": len(rows12), "in_sample": n_fall_P, "of_in_sample": len(rowsP),
                "holds": bool(n_fall >= 8 and n_fall_P >= 4)},
        "P-9": {"claim": "modelled cost < 25% of the gross positioned-month mean", "cost_per_month": cost_month, "gross_mean_month": gross_mean_month,
                "holds": bool(gross_mean_month > 0 and cost_month < 0.25 * gross_mean_month)},
        "P-10": {"claim": "falsifiers", "below_n1_p50": bool(oW < primary["p50"]), "control_beats_primary_per_day": bool(not control["primary_beats_control_per_day"]),
                 "avatar_unsupported": bool(not (n_fall >= 8 and n_fall_P >= 4)), "state_is_a_story": bool(oW > 0 and primary["clears_p95"] and not (dec_open and gate_out["gated_mean_over_open"] >= gate_out["ungated_mean_over_decidable"]))},
    }
    verdict = {"declared": "PASS" if (oW > 0 and primary["clears_p95"] and n2["clears_p95"] and control["primary_beats_control_per_day"]) else "DOES NOT PASS",
               "avatar": "SUPPORTED" if preds["P-8"]["holds"] else "UNSUPPORTED",
               "ledger": ("CLEARS C-a" if not comp["fails"] else f"fails {comp['fails']}") + ("; PROVISIONAL under D468 (below family p95)" if not comp["fails"] and not n2["clears_p95"] else "")}
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "P-10") + f"; P-10 {preds['P-10']}")
    log(f"  VERDICT {verdict['declared']} / avatar {verdict['avatar']} / ledger {verdict['ledger']}")

    pairs_out = [p for p in pairs if p["t1"] and int(p["hold_month"][5:7]) in WINDOW_MONTHS and p["hold_month"] >= "2011-01"]
    res = {"max_drawdown_convention": {"sign": "negative",
               "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak) in simple-return units for the "
                       "return-space cells; in dollars for the ZC book. Not a fraction of a compounded peak (D542).", "record": "D542"},
           "spec": "D568", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "strip_sha256": R55.sha256(R56.STRIP), "cot_sha256": R55.sha256(COT), "wasde_sha256": R55.sha256(FIX_SU),
           "wasde_rows_scored": {"on_disk": n_wasde_all, "scored": int(len(su_tab)), "reports_scored": int(su_tab["ReleaseDate"].nunique()), "last_release_scored": su_tab["ReleaseDate"].max()},
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum())},
           "construction": {"root": ROOT, "window_months": list(WINDOW_MONTHS), "delivery_rule": "T1 delivery >= m+2 (grains), T2 next listed; T1 must survive the window", "formation_ffill_sessions": FFILL,
                            "sign": "+1: long T1 / short T2", "size": "one ZC a leg (no micro)", "usd_per_point": upp, "tick_usd": tick_usd, "commission_rt": comm_rt, "sides_per_window": SIDES_PER_WINDOW,
                            "full_carry": {"storage_cents_per_month": STORAGE_CENTS_PER_MONTH, "interest": INTEREST},
                            "stage0_disclosure": "the twelve per-year H/K window returns 2011-2022, their Spearman with S/U, carry ratio and COT net short at formation, and the in-sample S/U terciles were read in D567 Stage 0"},
           "pairs": pairs_out, "cells": cells, "primary": primary, "null_n1": n1, "null_n2": n2, "control": control,
           "positions": {"primary_months_2016_2023": [(str(p), float(v)) for p, v in series["spread/window"]["mret"].items()],
                         "primary_months_2011_2023": [(str(p), float(v)) for p, v in mretL.items()],
                         "gated_months_2016_2023": [(str(p), float(v)) for p, v in series["spread/window/gated"]["mret"].items()]},
           "per_window": per_window, "per_month_of_window": per_mos, "per_year": per_year, "state": state, "gate": gate_out, "cot_avatar": cot_avatar,
           "component_line": comp, "predictions": preds, "verdict": verdict, "audits": audits, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: a synthetic ZC strip (H K N U Z only) with a known post-harvest carry narrowing
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D568 SELF-TEST -- synthetic strip, no fixture read\n")
    rng = np.random.default_rng(68)
    days = pd.bdate_range("2011-01-03", "2016-12-30").strftime("%Y-%m-%d").to_numpy(); T = len(days); me = R55.month_ends(days)
    listed = (3, 5, 7, 9, 12)
    rows = []; spot = 500.0; disc = {}
    for t, d in enumerate(days):
        spot *= math.exp(0.01 * rng.standard_normal()); y_, m_ = int(d[:4]), int(d[5:7])
        cur = y_ * 12 + m_
        for key in range(cur + 1, cur + 16):
            if (key % 12 or 12) not in listed:
                continue
            dm = key - cur
            # the post-harvest narrowing: in December..February every contract accrues a discount proportional to its
            # tenor, so the farther contract loses more than the nearer -- r1 - r2 > 0 -- and the ratio is constant otherwise
            if m_ in WINDOW_MONTHS:
                disc[key] = disc.get(key, 0.0) + 0.0004 * dm
            dy, dmo = divmod(key - 1, 12); dmo += 1
            rows.append(("ZC", f"ZC{'FGHJKMNQUVXZ'[dmo - 1]}{dy % 10}", d, spot * math.exp(0.004 * dm) * math.exp(-disc.get(key, 0.0))))
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    A, cols = R64.strip_tables(strip, days, ["ZC"])["ZC"]
    r1, r2, dP1, dP2, held, t1_idx, F1, pairs = pair_series(A, cols, days, me)
    y = r1 - r2; mW = season_mask(days, WINDOW_MONTHS) & held
    # [1] the grains delivery rule and the second path agree; at a November formation the pair is H/K; RAISE on shifted formations
    pb = pairs_pandas(strip, days, me); audit_pairs(pairs, pb)
    R61._expect_raise(lambda: audit_pairs(pairs, pb[1:] + pb[:1]), "pair audit on shifted formations")
    nov = [p for p in pairs if p["formation"][5:7] == "11"]
    if not all(p["t1"].endswith("-03") and p["t2"].endswith("-05") and int(p["t1"][:4]) == int(p["formation"][:4]) + 1 for p in nov):
        raise AssertionError("November formation is not H/K")
    print("  [1] T1 is delivery >= m+2 (H at a November formation), T2 the next listed (K); the pandas path agrees at every formation and RAISES on a shift")
    # [2] the narrowing is recovered in the window and absent outside it
    on = y[mW]; off = y[held & ~mW]
    if not (on.mean() > 0 and abs(off.mean()) < on.mean() / 5):
        raise AssertionError(f"premium: on {on.mean():.6f} off {off.mean():.6f}")
    print(f"  [2] the long spread earns {on.mean()*1e4:+.2f} bp/day in the window, {off.mean()*1e4:+.2f} bp/day outside it")
    # [3] survival: every positioned session's T1 is after February; RAISES on the m+1 rule's pair
    audit_survival(mW, t1_idx, days)
    t1_bad = t1_idx.copy()
    for k, t in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else T - 1
        yv, mv = int(days[t][:4]), int(days[t][5:7]); fin = np.isfinite(R64.formation_settles(A, t, FFILL)); cand = np.flatnonzero(fin & (cols >= yv * 12 + mv + 1))
        if cand.size:
            t1_bad[t + 1:end + 1] = cols[cand[0]]
    R61._expect_raise(lambda: audit_survival(mW, t1_bad, days), "survival audit on the m+1 rule's pair")
    print("  [3] every positioned session's T1 delivers after the window's last month; the audit RAISES on the m+1 rule's December contract")
    # [4] mask paths agree; lag audit RAISES on a mask that includes the formation session
    mW_b = season_mask_pandas(days, WINDOW_MONTHS) & held; audit_mask(mW, mW_b, me)
    bad = mW.copy(); bad[me[[k for k, t in enumerate(me) if t + 1 < T and mW[t + 1] and not mW[t]]]] = True
    R61._expect_raise(lambda: audit_mask(bad, mW_b, me), "lag audit on a formation-session mask")
    print("  [4] window mask agrees across paths and the lag audit RAISES when a position sits on the formation session")
    # [5] sign in money (LONG), right quantity, each RAISING on its break
    pnl = np.where(mW, (dP1 - dP2) * 50.0, 0.0); audit_sign_in_money_long(pnl, dP1, dP2, mW, 50.0)
    R61._expect_raise(lambda: audit_sign_in_money_long(-pnl, dP1, dP2, mW, 50.0), "sign audit on a negated grid")
    R61._expect_raise(lambda: audit_sign_in_money_long(np.roll(pnl, 1), dP1, dP2, mW, 50.0), "sign audit on a mislagged grid")
    audit_right_quantity(mW, days); R61._expect_raise(lambda: audit_right_quantity(np.arange(T) % 2 == 0, days), "right-quantity on a daily grid")
    print("  [5] sign-in-money (long spread pays +(dP1-dP2) x $50) and right-quantity audits pass and RAISE on negated, mislagged and daily grids")
    # [6] the gate: expanding median of prior Novembers, two paths agree, RAISES on shifted decisions and on a current-year median
    su = {2010: 0.06, 2011: 0.07, 2012: 0.05, 2013: 0.15, 2014: 0.14, 2015: 0.13, 2016: 0.17}
    g = gate_decisions(su); gb = gate_decisions_pandas(su); audit_gate(g, gb)
    if g != {2010: None, 2011: None, 2012: None, 2013: False, 2014: False, 2015: False, 2016: False}:
        raise AssertionError(f"gate decisions {g}")
    # 2014's value sits between the prior median (0.145) and the median that includes itself (0.15): the two rules differ there
    su2 = {2010: 0.15, 2011: 0.14, 2012: 0.16, 2013: 0.10, 2014: 0.15, 2015: 0.14, 2016: 0.12}
    g2 = gate_decisions(su2); audit_gate(g2, gate_decisions_pandas(su2))
    if g2 != {2010: None, 2011: None, 2012: None, 2013: True, 2014: False, 2015: True, 2016: True}:
        raise AssertionError(f"gate decisions {g2}")
    ks_ = sorted(g2); shifted = {ks_[i]: g2[ks_[i - 1]] if i else None for i in range(len(ks_))}
    R61._expect_raise(lambda: audit_gate(g2, shifted), "gate audit on shifted decisions")
    R61._expect_raise(lambda: audit_gate(g2, gate_decisions_pandas(su2, shift=0)), "gate audit on a current-year median")
    print("  [6] the gate opens iff S/U <= the median of >= 3 prior Novembers; the pandas path agrees and the audit RAISES on shifted decisions and on a current-year median")
    # [7] the placement null: the declared window is the best placement on the synthetic narrowing
    live_idx = [np.flatnonzero(held)]; m = mW.astype(float)[None, :]; best = -1
    for k in range(1, T):
        mr = R55.rotate_signs(m, live_idx, k)[0] > 0; best = max(best, R55.sharpe(np.where(mr, y, 0.0)))
    if not R55.sharpe(np.where(mW, y, 0.0)) >= best - 1e-9:
        raise AssertionError("placement null")
    print("  [7] the declared window is the best placement of the schedule on the synthetic narrowing")
    print("\nSELF-TEST PASSED"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
