"""D564 -- basis-momentum as published (Boons-Prado 2019, construction as Kwon-Kang-Yun 2021 state it)
on the 17 commodity roots of the settlement strip (spec 2da64b6, R8).

BM(11,0)_t = prod_{s=t-11..t}(1+R1_s) - prod(1+R2_s): twelve monthly returns of the first-nearby minus
the same of the second-nearby, both same-contract settlement-to-settlement returns of the contract chosen
at the prior month-end by the delivery rule (>= m+2, energy >= m+3). High4 long / Low4 short, equal
weight, scored on the nearby return. Family: EW High4/Low4 (PRIMARY), EW terciles, dollar High4/Low4,
the time-series form. Nulls: N1 rotation (purged 252), N2 family max, N3 name-randomised (diagnostic).
The 2024+ slice is never read.  Usage:  python scripts/run_d564_basis_momentum.py [--selftest]
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


R61 = _load("d561", "run_d561_trend_sharpenings.py")   # loads D556 which loads D555: one instance of each
R56 = R61.R56
R55 = R61.R55
R57 = _load("d557", "run_d557_xs_term_structure.py")   # membership helpers, root-month table, concentration
FB = R56.FB                                             # the strip builder: ym(), the contract-month resolver

OUT = REPO / "data" / "d564_basis_momentum.json"
SPEC = "2da64b6"
PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
CM = sorted(R55.SECTOR["CM"])                          # 17 roots, alphabetical -- the tie order
ENERGY = {"CL", "BZ", "HO", "RB", "NG"}                 # contracts expire in the month BEFORE delivery
NON_SEASONAL = ["BZ", "CL", "GC", "HG", "HO", "PA", "PL", "RB", "SI"]
LOOKBACK = 12
N_LEG = 4
MIN_ELIGIBLE = 12
MIN_ELIGIBLE_NS = 7
N_LEG_NS = 3
STALE_SESSIONS = 3
FFILL_FORMATION = 5      # AMENDMENT (recorded in the RESULT): the formation settlement is the last finite one within
                         # 5 sessions ending at the month-end session -- D556's carry_at_month_ends rule. As
                         # pre-registered (ffill = 1) two calendar defects, 2020-06-30 (a truncated archive day)
                         # and 2021-05-31 (Memorial Day, in the session calendar on a Globex evening bar, no
                         # settlements), each voided twelve month-ends for every root. The ffill = 1 primary and
                         # its null are kept beside the amended ones in the json.
N3_DRAWS = 2000
N3_SEED = 564
GUARD_OFFSETS = R61.GUARD_OFFSETS
CELL_KEYS = [("high4low4", "published"), ("terciles", "published"), ("high4low4", "dollar"), ("timeseries", "published")]
CELL_NAMES = {("high4low4", "published"): "EW High4/Low4", ("terciles", "published"): "EW terciles",
              ("high4low4", "dollar"): "dollar High4/Low4", ("timeseries", "published"): "time-series"}
PRIMARY_CELL = ("high4low4", "published")
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "strip_sha256", "curve_sha256",
                    "windows", "universe", "eligibility", "signals", "cells", "primary", "null_n1", "null_n2", "null_n3",
                    "root_months", "concentration", "per_root", "per_era", "per_year", "spreading", "vol_split",
                    "orthogonality", "non_seasonal_diagnostic", "overlay_carry", "harness", "component_line",
                    "amendment", "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# the nearby series from the strip
# --------------------------------------------------------------------------------------------
def strip_tables(strip: pd.DataFrame, days: np.ndarray, roots):
    """Per root: settlements as a (T x C) array over the session calendar, columns keyed by delivery
    month index (year*12 + month) resolved by FB.ym against the row's own year (D526's rule)."""
    day_ix = {d: i for i, d in enumerate(days)}
    out = {}
    for r in roots:
        s = strip[strip["root"] == r]
        key = s["contract"] + "|" + s["ref"].str[:4]
        uniq = key.drop_duplicates()
        res = {}
        for kk in uniq:
            c, y = kk.split("|")
            ymv = FB.ym(c, y + "-01-01")
            res[kk] = None if ymv is None else ymv[0] * 12 + ymv[1]
        deliv = key.map(res)
        ok = deliv.notna() & s["ref"].isin(day_ix)
        s = s[ok]; deliv = deliv[ok].astype(int)
        cols = np.array(sorted(deliv.unique()))
        col_ix = {c: j for j, c in enumerate(cols)}
        A = np.full((len(days), len(cols)), np.nan)
        rows = s["ref"].map(day_ix).to_numpy(); cc = deliv.map(col_ix).to_numpy()
        A[rows, cc] = s["settle"].to_numpy(dtype=float)
        out[r] = (A, cols)
    return out


def formation_settles(A, t, ffill):
    """The settlement row read at formation session t: the last finite settlement per contract within the
    FFILL sessions ending at t (D556's carry_at_month_ends rule). ffill = 1 reads session t alone."""
    row = A[t].copy()
    for w in range(1, max(ffill, 1)):
        if t - w < 0:
            break
        miss = ~np.isfinite(row)
        if not miss.any():
            break
        row[miss] = A[t - w][miss]
    return row


def choose_nearby(A, cols, t, day, energy, ffill=1):
    """(T1 col, T2 col) at formation session t by the delivery rule; None where absent."""
    y, m = int(day[:4]), int(day[5:7])
    thr = y * 12 + m + (3 if energy else 2)
    fin = np.isfinite(formation_settles(A, t, ffill))
    cand = np.flatnonzero(fin & (cols >= thr))
    if cand.size == 0:
        return None, None
    j1 = int(cand[0])
    later = cand[cand > j1]
    return j1, (int(later[0]) if later.size else None)


def is_stale(A, t, j):
    """Settlement unchanged across the STALE_SESSIONS sessions ending at t (all finite and equal)."""
    if j is None or t - STALE_SESSIONS + 1 < 0:
        return False
    v = A[t - STALE_SESSIONS + 1:t + 1, j]
    return bool(np.isfinite(v).all() and np.all(v == v[0]))


def nearby_series(tables, roots, days, me, ffill=1):
    """Monthly first- and second-nearby returns, basis, staleness and the chosen contracts at every
    month-end; and the daily same-contract return / price-change / close grids of the HELD T1 and T2.
    `ffill` is the number of sessions ending at the formation session within which the last finite
    settlement is read (1 = the month-end session alone, as pre-registered; 5 = the amendment)."""
    n, T, K = len(roots), len(days), len(me)
    R1 = np.full((n, K), np.nan); R2 = np.full((n, K), np.nan); basis = np.full((n, K), np.nan)
    T1 = np.full((n, K), -1, dtype=int); T2 = np.full((n, K), -1, dtype=int)
    stale = np.zeros((n, K), dtype=bool)
    r1d = np.zeros((n, T)); r2d = np.zeros((n, T)); dP1 = np.full((n, T), np.nan); close1 = np.full((n, T), np.nan)
    live = np.zeros((n, T), dtype=bool); roll = np.zeros((n, T), dtype=bool)
    held_ok = np.zeros((n, K), dtype=bool)          # T1 chosen at k has a settlement at month-end k+1
    for i, r in enumerate(roots):
        A, cols = tables[r]
        energy = r in ENERGY
        F_prev = None
        for k, t in enumerate(me):
            F = formation_settles(A, t, ffill)
            j1, j2 = choose_nearby(A, cols, t, days[t], energy, ffill)
            if j1 is None:
                F_prev = F; continue
            T1[i, k] = j1; T2[i, k] = -1 if j2 is None else j2
            stale[i, k] = is_stale(A, t, j1) or is_stale(A, t, j2)
            if j2 is not None:
                basis[i, k] = F[j2] / F[j1] - 1.0
            if k > 0 and T1[i, k - 1] >= 0 and F_prev is not None:
                a, b = F_prev[T1[i, k - 1]], F[T1[i, k - 1]]
                R1[i, k] = b / a - 1.0 if (np.isfinite(a) and np.isfinite(b) and a > 0) else np.nan
                if T2[i, k - 1] >= 0:
                    a2, b2 = F_prev[T2[i, k - 1]], F[T2[i, k - 1]]
                    R2[i, k] = b2 / a2 - 1.0 if (np.isfinite(a2) and np.isfinite(b2) and a2 > 0) else np.nan
                held_ok[i, k - 1] = bool(np.isfinite(b))
            F_prev = F
            # daily grids for the holding month k -> k+1 in the contracts chosen at k
            end = me[k + 1] if k + 1 < K else T - 1
            for j, rd in ((j1, r1d), (j2, r2d)):
                if j is None:
                    continue
                prev = F[j]
                for u in range(t + 1, end + 1):
                    v = A[u, j]
                    if np.isfinite(v) and np.isfinite(prev) and prev > 0:
                        rd[i, u] = v / prev - 1.0
                        if rd is r1d:
                            dP1[i, u] = v - prev
                    if np.isfinite(v):
                        prev = v
                    if rd is r1d:
                        close1[i, u] = prev if np.isfinite(prev) else np.nan
            live[i, t + 1:end + 1] = np.isfinite(F[j1])
            if k > 0 and T1[i, k - 1] >= 0 and T1[i, k - 1] != j1 and t + 1 < T:
                roll[i, t + 1] = True
    return dict(R1=R1, R2=R2, basis=basis, T1=T1, T2=T2, stale=stale, held_ok=held_ok,
                r1d=r1d, r2d=r2d, dP1=dP1, close1=close1, live=live, roll=roll)


def signals_at_month_ends(R1, R2, stale):
    """BM(11,0), mom, eligibility: all twelve monthly returns of BOTH series finite and nothing stale."""
    n, K = R1.shape
    BM = np.full((n, K), np.nan); mom = np.full((n, K), np.nan); elig = np.zeros((n, K), dtype=bool)
    for k in range(LOOKBACK - 1, K):
        w1 = R1[:, k - LOOKBACK + 1:k + 1]; w2 = R2[:, k - LOOKBACK + 1:k + 1]
        ok = np.isfinite(w1).all(1) & np.isfinite(w2).all(1) & ~stale[:, k]
        p1 = np.prod(1.0 + w1, axis=1); p2 = np.prod(1.0 + w2, axis=1)
        BM[ok, k] = p1[ok] - p2[ok]; mom[ok, k] = p1[ok] - 1.0; elig[:, k] = ok
    return BM, mom, elig


def strip_pivot(strip_root: pd.DataFrame, days, ffill=1):
    """The audit's own table: the raw rows pivoted to (session x delivery month), reindexed to the session
    calendar, forward-filled within ffill-1 sessions (the same formation rule, pandas' way)."""
    s = strip_root.copy()
    s["deliv"] = [FB.ym(c, ref)[0] * 12 + FB.ym(c, ref)[1] if FB.ym(c, ref) else -1 for c, ref in zip(s["contract"], s["ref"])]
    s = s[s["deliv"] > 0]
    piv = s.pivot_table(index="ref", columns="deliv", values="settle", aggfunc="first").reindex(list(days))
    return piv.ffill(limit=ffill - 1) if ffill > 1 else piv


def bm_pandas(piv: pd.DataFrame, days, me, k, energy):
    """Implementation B for the audit: BM at month-end k for one root, from the audit's own pivot, its own
    contract selection and its own monthly returns; never calls the functions above."""
    ends = [days[m] for m in me]
    def pick(date):
        y, m = int(date[:4]), int(date[5:7]); thr = y * 12 + m + (3 if energy else 2)
        if date not in piv.index:
            return None, None
        row = piv.loc[date].dropna(); c = [d for d in row.index if d >= thr]
        if not c:
            return None, None
        c = sorted(c); return c[0], (c[1] if len(c) > 1 else None)
    g1 = 1.0; g2 = 1.0
    for kk in range(k - LOOKBACK + 1, k + 1):
        d0, d1 = ends[kk - 1], ends[kk]
        c1, c2 = pick(d0)
        if c1 is None or c2 is None or d1 not in piv.index or d0 not in piv.index:
            return None
        a1, b1 = piv.loc[d0, c1], piv.loc[d1, c1]; a2, b2 = piv.loc[d0, c2], piv.loc[d1, c2]
        if not (np.isfinite(a1) and np.isfinite(b1) and np.isfinite(a2) and np.isfinite(b2)):
            return None
        g1 *= b1 / a1; g2 *= b2 / a2
    return g1 - g2


def audit_bm_from_strip(BM, elig, strip, roots, days, me, n_check=300, seed=11, ffill=1, pivots=None):
    rng = np.random.default_rng(seed)
    cells = np.argwhere(elig[:, LOOKBACK - 1:]) + np.array([0, LOOKBACK - 1])
    pick = cells[rng.choice(len(cells), size=min(n_check, len(cells)), replace=False)]
    pivots = {} if pivots is None else pivots
    checked = 0
    for i, k in pick:
        if roots[i] not in pivots:
            pivots[roots[i]] = strip_pivot(strip[strip["root"] == roots[i]], days, ffill)
        ref = bm_pandas(pivots[roots[i]], days, me, int(k), roots[i] in ENERGY)
        if ref is None:
            raise AssertionError(f"BM AUDIT: the second path finds {roots[i]} ineligible at {days[me[k]]}")
        if not np.isclose(ref, BM[i, k], rtol=1e-10, atol=1e-14):
            raise AssertionError(f"BM AUDIT: {roots[i]} {days[me[k]]}: runner {BM[i, k]:.8f} != strip path {ref:.8f}")
        checked += 1
    if checked == 0:
        raise AssertionError("BM AUDIT: nothing checked")
    return checked


def membership_fixed(sig_me, elig, roots, n_leg, min_eligible):
    """A. Long the top n_leg, short the bottom n_leg among eligible roots; ties by symbol ascending."""
    n, K = sig_me.shape; names = np.array(roots)
    member = np.zeros((n, K), dtype=int); diag = []
    for k in range(K):
        el = np.flatnonzero(elig[:, k] & np.isfinite(sig_me[:, k]))
        rec = {"n_eligible": int(el.size), "flat": False, "tie_at_boundary": False}
        if el.size < min_eligible:
            rec["flat"] = True; diag.append(rec); continue
        v = sig_me[:, k]
        order = el[np.lexsort((names[el], -v[el]))]
        member[order[:n_leg], k] = 1; member[order[el.size - n_leg:], k] = -1
        sv = v[order]
        rec["tie_at_boundary"] = bool(sv[n_leg - 1] == sv[n_leg] or sv[el.size - n_leg] == sv[el.size - n_leg - 1])
        diag.append(rec)
    return member, diag


def membership_fixed_pandas(sig_me, elig, roots, n_leg, min_eligible):
    """B. pandas rank(method='first') on the symbol-sorted eligible Series; never calls A."""
    n, K = sig_me.shape; out = np.zeros((n, K), dtype=int); pos = {r: i for i, r in enumerate(roots)}
    for k in range(K):
        s = pd.Series(np.where(elig[:, k], sig_me[:, k], np.nan), index=list(roots)).dropna().sort_index()
        if len(s) < min_eligible:
            continue
        rk = s.rank(method="first", ascending=False)
        for r in s.index[rk <= n_leg]:
            out[pos[r], k] = 1
        for r in s.index[rk > len(s) - n_leg]:
            out[pos[r], k] = -1
    return out


def spearman_rows(a, b, mask):
    """Mean cross-sectional Spearman over month-ends with >= MIN_ELIGIBLE cells, and the pooled value."""
    vals = []; pa = []; pb = []
    for k in range(a.shape[1]):
        m = mask[:, k] & np.isfinite(a[:, k]) & np.isfinite(b[:, k])
        if m.sum() >= MIN_ELIGIBLE:
            vals.append(pd.Series(a[m, k]).corr(pd.Series(b[m, k]), method="spearman"))
            pa.extend(a[m, k].tolist()); pb.extend(b[m, k].tolist())
    return {"mean_cross_sectional": float(np.nanmean(vals)) if vals else None, "n_month_ends": len(vals),
            "pooled": float(pd.Series(pa).corr(pd.Series(pb), method="spearman")) if pa else None}


def name_randomised_null(member, elig, me, T, span, rsimple, w, days, n_draws, seed):
    """N3: keep each month-end's leg sizes, draw which eligible roots fill them."""
    rng = np.random.default_rng(seed)
    n, K = member.shape
    out = np.full(n_draws, np.nan); out_s = np.full(n_draws, np.nan)
    for d in range(n_draws):
        mr = np.zeros_like(member)
        for k in range(K):
            nl = int((member[:, k] == 1).sum()); ns = int((member[:, k] == -1).sum())
            if nl + ns == 0:
                continue
            el = np.flatnonzero(elig[:, k])
            pick = rng.choice(el, size=nl + ns, replace=False)
            mr[pick[:nl], k] = 1; mr[pick[nl:], k] = -1
        held = R55.hold_from_month_ends(mr.astype(float), me, T, span)
        x = R55.book_return(held, rsimple)[w]
        out[d] = R55.sharpe(x); out_s[d] = R55.sortino(x)
    return out, out_s


def _p95_boot_se(v, n_boot=300, seed=1):
    rng = np.random.default_rng(seed); v = v[np.isfinite(v)]
    return float(np.std([np.percentile(rng.choice(v, size=v.size, replace=True), 95) for _ in range(n_boot)], ddof=1))


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D564 -- basis-momentum as published on {len(CM)} commodity roots\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    for p in (R56.CURVE, R56.STRIP):
        meta = json.loads(p.with_suffix("").with_suffix(".meta.json").read_text(encoding="utf-8"))
        if not meta.get("all_gates_pass"):
            raise AssertionError(f"{p.name}: gates have not passed")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present after filtering")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start)
    days = gfull["days"]; T = len(days); me = R55.month_ends(days); K = len(me)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & strip["root"].isin(CM)]
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    curve = curve[curve["ref"] < RESERVED_FROM]
    log(f"  strip: {len(strip):,} rows on {len(CM)} roots, {strip['ref'].min()}..{strip['ref'].max()}; sessions {T}, month-ends {K}")

    # ---- the nearby series ----
    t0 = time.time()
    tables = strip_tables(strip, days, CM)
    ns = nearby_series(tables, CM, days, me, ffill=FFILL_FORMATION)
    BM, mom, elig = signals_at_month_ends(ns["R1"], ns["R2"], ns["stale"])
    ns0 = nearby_series(tables, CM, days, me, ffill=1)                     # as pre-registered, kept beside
    BM0, _, elig0 = signals_at_month_ends(ns0["R1"], ns0["R2"], ns0["stale"])
    n = len(CM)
    span = np.zeros((n, T), dtype=bool)
    for i in range(n):
        ix = np.flatnonzero(ns["live"][i])
        if ix.size:
            span[i, ix[0]:ix[-1] + 1] = True
    rlog1 = np.where(ns["live"] & (ns["r1d"] != 0.0), np.log1p(ns["r1d"]), np.nan)
    g = dict(roots=CM, days=days, close=ns["close1"], rlog=rlog1, dP=ns["dP1"], roll=ns["roll"], live=ns["live"], span=span, nonpositive=[])
    rsimple = ns["r1d"]; rspread = ns["r1d"] - ns["r2d"]
    first_elig = next((k for k in range(K) if elig[:, k].sum() >= MIN_ELIGIBLE), None)
    log(f"  nearby series built in {time.time() - t0:.0f}s; first month-end with >= {MIN_ELIGIBLE} eligible: {days[me[first_elig]] if first_elig is not None else None}; "
        f"stale root-months {int(ns['stale'].sum())}; roll months {int(ns['roll'].sum())}")

    # ---- audits: signal by a second path, held contract, membership, lag, sign, right quantity ----
    audits = {}
    piv_cache = {}
    audits["bm_cells_checked_against_strip"] = audit_bm_from_strip(BM, elig, strip, CM, days, me, ffill=FFILL_FORMATION, pivots=piv_cache)
    try:
        audit_bm_from_strip(-BM, elig, strip, CM, days, me, n_check=20, ffill=FFILL_FORMATION, pivots=piv_cache); raise RuntimeError("BM audit accepted a NEGATED grid")
    except AssertionError:
        audits["bm_audit_raises_on_negated_grid"] = True
    R1_bad = ns["R1"].copy(); R1_bad[:, LOOKBACK + 5] = np.nan
    BM_bad, _, elig_bad = signals_at_month_ends(R1_bad, ns["R2"], ns["stale"])
    # dropping one month's return makes twelve later month-ends ineligible on the runner's path; the strip path
    # still finds them -> the audit must raise on the runner's BM being NaN where the strip path has a value
    try:
        BM_hole = BM.copy(); BM_hole[np.isfinite(BM) & ~elig_bad] = 0.0
        audit_bm_from_strip(BM_hole, elig, strip, CM, days, me, n_check=300, ffill=FFILL_FORMATION, pivots=piv_cache); raise RuntimeError("BM audit accepted a grid with a dropped month")
    except AssertionError:
        audits["bm_audit_raises_on_dropped_month"] = True
    elig_held = elig.copy(); elig_held[:, -1] = False                 # the last month-end has no successor
    held_shortfall = {r: int((elig_held[i] & ~ns["held_ok"][i]).sum()) for i, r in enumerate(CM)}
    held_share = float(ns["held_ok"][elig_held].mean())
    audits["held_contract_settles_at_next_month_end_share"] = held_share
    audits["held_contract_shortfall_by_root"] = {r: v for r, v in held_shortfall.items() if v}
    if held_share < 0.99:
        raise AssertionError(f"HELD-CONTRACT AUDIT: only {held_share:.3%} of positioned root-months have a settlement at the next month-end")

    member, diag = membership_fixed(BM, elig, CM, N_LEG, MIN_ELIGIBLE)
    member_pd = membership_fixed_pandas(BM, elig, CM, N_LEG, MIN_ELIGIBLE)
    audits["leg_membership_cells"] = R57.audit_leg_membership(member, member_pd, me, days)
    try:
        R57.audit_leg_membership(R57.swap_one_pair(member), member_pd, me, days); raise RuntimeError("membership audit accepted a swapped pair")
    except AssertionError:
        audits["membership_raises_on_swapped_pair"] = True
    sign_held = R55.hold_from_month_ends(member.astype(float), me, T, span)
    audits["lag_held_cells"] = R55.audit_lag(sign_held, member_pd.astype(float), me, span, T)
    unl = np.zeros_like(sign_held)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = member[:, k][:, None]
    unl = np.where(span, unl, 0.0)
    try:
        R55.audit_lag(unl, member_pd.astype(float), me, span, T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(sign_held, me, T)
    try:
        R55.audit_right_quantity(np.tile(np.where(np.arange(T) % 2 == 0, 1.0, -1.0), (n, 1)), me, T); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    upp_f, tick_f, comm_f, size_f = R56.min_size(gfull, gfull["roots"])
    ix_full = [gfull["roots"].index(r) for r in CM]
    upp, tick_usd, comm_rt, size_name = upp_f[ix_full], tick_f[ix_full], comm_f[ix_full], [size_f[j] for j in ix_full]
    dollar_roots = [r for r in CM if r not in R55.DOLLAR_EXCLUDED]
    sd = sign_held.astype(int)
    grossD_all, _, _ = R55.dollar_book(sd, g, upp, comm_rt, tick_usd, CM)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(grossD_all, sd, g, upp)
    for label, bad in (("negated", -grossD_all), ("mislagged", R55.dollar_book(sd, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, CM)[0])):
        try:
            R55.audit_sign_in_money(bad, sd, g, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True
    log(f"  audits: {audits}")

    # ---- harness: strip T1 vs breadth front (monthly), basis sign vs -carry_ann sign ----
    idx = pd.to_datetime(days)
    rs_full = np.where(np.isfinite(gfull["rlog"]), np.expm1(np.nan_to_num(gfull["rlog"])), 0.0)
    wL = R55.window_mask(days, *LONG); wP = R55.window_mask(days, *PRIMARY)
    corrs = {}
    for i, r in enumerate(CM):
        b = pd.Series(rs_full[ix_full[i]], index=idx); bm_ = (1.0 + b).groupby(b.index.to_period("M")).prod() - 1.0
        s1 = pd.Series(ns["R1"][i], index=[pd.Timestamp(str(days[m])).to_period("M") for m in me])
        both = pd.concat([bm_, s1], axis=1, keys=["breadth", "t1"]).dropna()
        both = both[(both.index >= pd.Period(LONG[0][:7], "M")) & (both.index <= pd.Period(LONG[1][:7], "M"))]
        corrs[r] = float(both["breadth"].corr(both["t1"])) if len(both) > 24 else None
    Cg = R56.carry_grid(gfull, curve); carry_me_full = R56.carry_at_month_ends(Cg, gfull["live"], me)
    carry_me = carry_me_full[ix_full]
    m_ok = np.isfinite(carry_me) & np.isfinite(ns["basis"]) & (carry_me != 0) & (ns["basis"] != 0)
    sign_agree = float((np.sign(ns["basis"][m_ok]) == -np.sign(carry_me[m_ok])).mean())
    harness = {"t1_vs_breadth_front_monthly_corr_by_root": corrs, "t1_vs_breadth_front_median_corr": float(np.nanmedian([v for v in corrs.values() if v is not None])),
               "basis_sign_vs_minus_carry_ann_agreement": sign_agree, "cells_compared": int(m_ok.sum()),
               "ok": bool(np.nanmedian([v for v in corrs.values() if v is not None]) > 0.9 and sign_agree > 0.8)}
    log(f"  harness: T1 vs breadth front median corr {harness['t1_vs_breadth_front_median_corr']:.3f}; basis sign agrees with -carry_ann on {sign_agree:.1%} of {int(m_ok.sum())} cells -> {'OK' if harness['ok'] else 'SUSPECT'}")

    # ---- cells ----
    sig = R55.ew_vol(rlog1, ns["live"])
    member_t, diag_t = R57.membership_at_month_ends(np.where(elig, BM, np.nan), CM)      # terciles, D557's rule
    BM_dm = np.full_like(BM, np.nan)
    for i in range(n):
        cnt = 0; tot = 0.0
        for k in range(K):
            if elig[i, k] and np.isfinite(BM[i, k]):
                cnt += 1; tot += BM[i, k]
                if cnt >= 12:
                    BM_dm[i, k] = BM[i, k] - tot / cnt
    ts_sign_me = np.where(np.isfinite(BM_dm), np.sign(BM_dm), 0.0)
    ts_sign_held, ts_pos, ts_scale, _ = R56.positions_from_signs(ts_sign_me, sig, me, g)
    ones = np.ones((n, T))
    cells = {("high4low4", "published"): dict(book="published", sign_held=sign_held, scale_held=ones, pos=sign_held),
             ("terciles", "published"): dict(book="published", sign_held=R55.hold_from_month_ends(member_t.astype(float), me, T, span), scale_held=ones, pos=None),
             ("high4low4", "dollar"): dict(book="dollar", sign_held=sign_held, scale_held=None, pos=None),
             ("timeseries", "published"): dict(book="published", sign_held=ts_sign_held, scale_held=ts_scale, pos=ts_pos)}
    cells[("terciles", "published")]["pos"] = cells[("terciles", "published")]["sign_held"]
    dP_days, dL_days = days[wP], days[wL]
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    root_sigma = {}
    for i, r in enumerate(CM):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]
    results_cells, scored = {}, {}
    for key, c in cells.items():
        name = CELL_NAMES[key]
        if c["book"] == "published":
            x = R55.book_return(c["pos"], rsimple); turn, rolls, tw = R55.published_cost(c["pos"], cbp, g["roll"]); xn = x - turn
            entry = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "net_incl_rolls": R55.sharpe((x - turn - rolls)[wP]), "net_incl_rolls_sortino": R55.sortino((x - turn - rolls)[wP]),
                     "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                     "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                     "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4),
                     "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                     "positioned_names_mean": float((c["pos"][:, wP] != 0).sum(0).mean()),
                     "high_minus_low_scale_note": "book_return is half the paper's High-minus-Low; Sharpe is scale-free"}
            scored[key] = dict(gross=x, net=xn)
        else:
            sP = np.where(wP[None, :], c["sign_held"], 0.0).astype(int); sL = np.where(wL[None, :], c["sign_held"], 0.0).astype(int)
            gross, cost, sides = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots)
            gb, cb = gross.sum(0), cost.sum(0); xg, xn = gb, gb - cb
            g_cd, c_cd, _ = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, cd_roots)
            gL, _, _ = R55.dollar_book(sL, g, upp, comm_rt, tick_usd, dollar_roots)
            per_root_usd = {r: float((gross[i] - cost[i])[wP].sum()) for i, r in enumerate(CM)}
            entry = {"gross": R55.stats_block(xg[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"),
                     "cost_total": float(cb[wP].sum()), "sides_total": int(sides[:, wP].sum()),
                     "roll_sides_total": int((2 * (g["roll"] & (sP != 0)))[:, wP].sum()),
                     "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d subset"),
                                   "net": R55.stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d subset net")},
                     "gross_long": R55.stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $"),
                     "per_root_net_usd": dict(sorted(per_root_usd.items(), key=lambda kv: -kv[1])),
                     "largest_root_share": float(max(per_root_usd.values()) / sum(per_root_usd.values())) if sum(per_root_usd.values()) != 0 else None}
            scored[key] = dict(gross=xg, net=xn)
        results_cells[name] = entry
        log(f"  {name:18s} gross {entry['gross']['sharpe']:+.3f} / So {entry['gross']['sortino']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}  maxDD {entry['gross']['max_dd']:+.4g}")

    # ---- primary diagnostics ----
    x = scored[PRIMARY_CELL]["gross"]; pos = sign_held
    rmt = R57.root_month_table(pos, rsimple, days, wP)
    root_months = {"all": R57.dist_stats(rmt["contrib"].to_numpy()), "long_leg": R57.dist_stats(rmt.loc[rmt["leg"] > 0, "contrib"].to_numpy()),
                   "short_leg": R57.dist_stats(rmt.loc[rmt["leg"] < 0, "contrib"].to_numpy())}
    cnt = (pos != 0).sum(0); contrib = pos * rsimple / np.where(cnt > 0, cnt, 1)[None, :]
    totals = {r: float(contrib[i][wP].sum()) for i, r in enumerate(CM)}
    conc = R57.concentration(totals)
    per_root = {r: {"total_primary": totals[r], "total_long": float(contrib[i][wL].sum()),
                    "sharpe_primary": R55.sharpe(contrib[i][wP & (pos[i] != 0)]) if (wP & (pos[i] != 0)).sum() > 60 else None,
                    "sortino_primary": R55.sortino(contrib[i][wP & (pos[i] != 0)]) if (wP & (pos[i] != 0)).sum() > 60 else None,
                    "months_long": int(((member[i] == 1) & (np.array([wP[min(m + 1, T - 1)] for m in me]))).sum()),
                    "months_short": int(((member[i] == -1) & (np.array([wP[min(m + 1, T - 1)] for m in me]))).sum()),
                    "sigma_usd_min_size": root_sigma[r], "min_size": size_name[i]} for i, r in enumerate(CM)}
    n_pos_long = sum(1 for r in CM if per_root[r]["total_long"] > 0)
    per_era = {f"{a}..{b}": {"sharpe": R55.sharpe(x[R55.window_mask(days, a, b)]), "sortino": R55.sortino(x[R55.window_mask(days, a, b)])} for a, b in ERAS}
    first_pos_day = days[np.flatnonzero((pos != 0).any(0))[0]]
    wE1 = R55.window_mask(days, first_pos_day, "2015-12-31")
    per_era["first_half_" + str(first_pos_day) + "..2015-12-31"] = {"sharpe": R55.sharpe(x[wE1]), "sortino": R55.sortino(x[wE1]), "n_days": int(wE1.sum())}
    yrs = sorted(set(d[:4] for d in days[wL]))
    per_year = {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "sortino": R55.sortino(x[np.array([d[:4] == y for d in days])]),
                    "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in yrs}
    meP = np.array([wP[min(m + 1, T - 1)] for m in me])
    eligibility = {"per_month_end": [{"date": str(days[me[k]]), **diag[k], "n_stale": int(ns["stale"][:, k].sum()),
                                      "n_long": int((member[:, k] == 1).sum()), "n_short": int((member[:, k] == -1).sum())} for k in range(K) if meP[k]],
                   "flat_month_ends_primary": int(sum(1 for k in range(K) if meP[k] and diag[k]["flat"])),
                   "ties_at_boundary_primary": int(sum(1 for k in range(K) if meP[k] and diag[k]["tie_at_boundary"])),
                   "mean_eligible_primary": float(np.mean([diag[k]["n_eligible"] for k in range(K) if meP[k]])),
                   "stale_root_months_primary": int(ns["stale"][:, meP].sum()),
                   "t1_changes_primary": int(sum(int(ns["T1"][i, k] != ns["T1"][i, k - 1]) for i in range(n) for k in range(1, K) if meP[k] and ns["T1"][i, k] >= 0 and ns["T1"][i, k - 1] >= 0)),
                   "first_eligible_month_end": str(days[me[first_elig]]) if first_elig is not None else None}
    # spreading return (P-7), vol split (P-6), orthogonality (P-2)
    xs = R55.book_return(pos, rspread)
    spreading = {"gross": R55.stats_block(xs[wP], dP_days, "High4-Low4 spreading"), "long_window": R55.stats_block(xs[wL], dL_days, "spreading 2011-2023")}
    xm = pd.Series(x, index=idx); xm = xm.groupby(xm.index.to_period("M")).sum()
    vol_cs = np.array([np.nanmean(sig[elig[:, k], me[k]]) if elig[:, k].any() else np.nan for k in range(K)])
    rows = []
    for k in range(K - 1):
        if meP[k] and np.isfinite(vol_cs[k]) and (member[:, k] != 0).any():
            p_hold = pd.Timestamp(str(days[me[k + 1]])).to_period("M")
            if p_hold in xm.index:
                rows.append((vol_cs[k], float(xm[p_hold])))
    rows = np.array(rows)
    med = float(np.median(rows[:, 0])) if len(rows) else float("nan")
    hi = rows[rows[:, 0] > med, 1]; lo = rows[rows[:, 0] <= med, 1]
    vol_split = {"n_months": int(len(rows)), "median_cs_ew_vol": med,
                 "high_vol_half": {"mean_monthly": float(hi.mean()), "sharpe": R55.sharpe(hi, 12.0), "sortino": R55.sortino(hi, 12.0), "n": int(hi.size)},
                 "low_vol_half": {"mean_monthly": float(lo.mean()), "sharpe": R55.sharpe(lo, 12.0), "sortino": R55.sortino(lo, 12.0), "n": int(lo.size)}}
    orth = {"bm_vs_basis": spearman_rows(BM, ns["basis"], elig & meP[None, :]), "bm_vs_mom": spearman_rows(BM, mom, elig & meP[None, :]),
            "bm_vs_carry_ann": spearman_rows(BM, carry_me, elig & meP[None, :]), "basis_sign_convention": "F_T2/F_T1 - 1, contango positive (the paper's)"}
    log(f"  T0: Spearman(BM, basis) mean {orth['bm_vs_basis']['mean_cross_sectional']:+.3f} pooled {orth['bm_vs_basis']['pooled']:+.3f}; "
        f"(BM, mom) {orth['bm_vs_mom']['mean_cross_sectional']:+.3f}; turnover {results_cells['EW High4/Low4']['ann_turnover_weight_units']:.1f} wu/yr")
    # non-seasonal diagnostic (High3/Low3 on 9 roots)
    ix_ns = [CM.index(r) for r in NON_SEASONAL]
    mem_ns, diag_ns = membership_fixed(BM[ix_ns], elig[ix_ns], NON_SEASONAL, N_LEG_NS, MIN_ELIGIBLE_NS)
    held_ns = R55.hold_from_month_ends(mem_ns.astype(float), me, T, span[ix_ns])
    x_ns = R55.book_return(held_ns, rsimple[ix_ns])
    non_seasonal = {"roots": NON_SEASONAL, "n_leg": N_LEG_NS, "gross": R55.stats_block(x_ns[wP], dP_days, "non-seasonal High3/Low3"),
                    "flat_month_ends_primary": int(sum(1 for k in range(K) if meP[k] and diag_ns[k]["flat"]))}

    # ---- overlay on D556 carry A (P-5), with the primary's rotation null ----
    s12_me, _ = R55.signal_at_month_ends(gfull["rlog"], gfull["live"], days, me, 12)
    signsA = R56.cell_signs(carry_me_full, s12_me, None)["A"]
    _, posA, _, _ = R56.positions_from_signs(signsA, R55.ew_vol(gfull["rlog"], gfull["live"]), me, gfull)
    xA = R55.book_return(posA, rs_full)
    art556 = json.loads(R61.ART_D556.read_text(encoding="utf-8"))
    if abs(R55.sharpe(xA[wP]) - art556["primary"]["observed"]) > 1e-9:
        raise AssertionError("D556 cell A did not reproduce")
    idxW = {q: R61.worst_days(xA[wP], R61.WORST_Q[q]) for q in R61.WORST_Q}
    audits["worst_days_carry_checked"] = R61.audit_worst_days(xA[wP], 0.05)
    ov = R61.overlay_stats(xA[wP], x[wP], idxW)
    ov.update({"rho_daily": float(np.corrcoef(xA[wP], x[wP])[0, 1]), "base_sharpe": R55.sharpe(xA[wP]), "overlay_sharpe": R55.sharpe(x[wP]),
               "blend_sharpe": R55.sharpe(0.5 * (xA[wP] / xA[wP].std(ddof=1) + x[wP] / x[wP].std(ddof=1)))})

    # ---- nulls ----
    live_idx = [np.flatnonzero(span[i] & wP) for i in range(n)]
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    for k in GUARD_OFFSETS:
        k = k % (int(wP.sum()) - 1) or 1
        p = R55.rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k) * ones
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"exactness guard failed at offset {k}")
    audits["exactness_guard_offsets"] = len(GUARD_OFFSETS)
    log(f"  N1/N2 over {int(wP.sum()) - 1} offsets x {len(cells)} cells ...")
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    names = [CELL_NAMES[k] for k in keys]
    obs = np.array([results_cells[nm]["gross"]["sharpe"] if k[1] == "published" else results_cells[nm]["net"]["sharpe"] for nm, k in zip(names, keys)])
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= int(wP.sum()) - R55.NULL_PURGE)
    null = null_all[keep]; jP = keys.index(PRIMARY_CELL)
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(null.shape[0]), "per_cell": {},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_all[:, jP].tolist(), "sortino": null_s[:, jP].tolist()}}
    for j, nm in enumerate(names):
        col = null[:, j]
        n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95)),
                              "sd": float(col.std(ddof=1)), "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95)),
                              "sortino": R55.sortino_null_block(scored[keys[j]]["gross" if keys[j][1] == "published" else "net"][wP], null_s[:, j], keep),
                              "unpurged": {"p50": float(np.percentile(null_all[:, j], 50)), "p95": float(np.percentile(null_all[:, j], 95)), "max": float(null_all[:, j].max())}}
    fam = null.max(1)
    n2 = {"observed_best": float(obs.max()), "observed_best_cell": names[int(obs.argmax())], "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)),
          "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95))}
    primary = n1["per_cell"][CELL_NAMES[PRIMARY_CELL]]
    log(f"  N1 primary: observed {primary['observed']:+.3f}  p05 {primary['p05']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f}\n"
        f"  N2 family: best {n2['observed_best']:+.3f} ({n2['observed_best_cell']})  p50 {n2['p50']:+.3f}  p95 {n2['p95']:+.3f}")
    # overlay null (primary rotated, carry A fixed)
    nO = int(wP.sum()) - 1; c5n = np.full(nO, np.nan); ddn = np.full(nO, np.nan)
    for k in range(1, nO + 1):
        xr = R55.book_return(R55.rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k), rsimple)[wP]
        st = R61.overlay_stats(xA[wP], xr, idxW); c5n[k - 1] = st["c5"]; ddn[k - 1] = st["dd_ratio"]
    overlay_carry = {"pairs": ov, "null": {"c5": dict(R61._pct(c5n[keep]), observed=ov["c5"], pct_rank=float((c5n[keep] < ov["c5"]).mean())),
                                          "dd_ratio": dict(R61._pct(ddn[keep]), observed=ov["dd_ratio"], pct_rank=float((ddn[keep] < ov["dd_ratio"]).mean()),
                                                           below_p05=bool(ov["dd_ratio"] < np.percentile(ddn[keep], 5)))}}
    log(f"  overlay on carry A: rho {ov['rho_daily']:+.2f}  c5 {ov['c5']:+.3f} (null p50 {overlay_carry['null']['c5']['p50']:+.3f} rank {overlay_carry['null']['c5']['pct_rank']:.3f})  "
        f"DD ratio {ov['dd_ratio']:.3f} (null p05 {overlay_carry['null']['dd_ratio']['p05']:.3f} p50 {overlay_carry['null']['dd_ratio']['p50']:.3f})")
    # N3 name-randomised
    t0 = time.time()
    n3v, n3s = name_randomised_null(np.where(meP[None, :], member, 0), elig, me, T, span, rsimple, wP, days, N3_DRAWS, N3_SEED)
    o = primary["observed"]; p95_3 = float(np.percentile(n3v, 95)); se3 = _p95_boot_se(n3v)
    n3 = {"draws": N3_DRAWS, "seed": N3_SEED, "observed": o, "p05": float(np.percentile(n3v, 5)), "p50": float(np.percentile(n3v, 50)), "p95": p95_3,
          "p95_boot_se": se3, "sd": float(n3v.std(ddof=1)), "pct_rank": float((n3v < o).mean()), "clears_p95": bool(o > p95_3),
          "margin_over_p95_in_se": float((o - p95_3) / se3) if se3 > 0 else None, "unresolved": bool(abs(o - p95_3) < 2 * se3),
          "sortino": {"observed": results_cells[CELL_NAMES[PRIMARY_CELL]]["gross"]["sortino"], "p50": float(np.nanpercentile(n3s, 50)), "p95": float(np.nanpercentile(n3s, 95))},
          "wall_s": round(time.time() - t0, 1)}
    log(f"  N3 name-randomised: p50 {n3['p50']:+.3f}  p95 {n3['p95']:+.3f} (SE {se3:.3f})  rank {n3['pct_rank']:.3f}  {'UNRESOLVED' if n3['unresolved'] else ''}")

    # ---- the amendment: the as-pre-registered (ffill = 1) primary and its null, kept beside ----
    member0, diag0 = membership_fixed(BM0, elig0, CM, N_LEG, MIN_ELIGIBLE)
    span0 = np.zeros((n, T), dtype=bool)
    for i in range(n):
        ix0 = np.flatnonzero(ns0["live"][i])
        if ix0.size:
            span0[i, ix0[0]:ix0[-1] + 1] = True
    held0 = R55.hold_from_month_ends(member0.astype(float), me, T, span0)
    x0 = R55.book_return(held0, ns0["r1d"])
    live_idx0 = [np.flatnonzero(span0[i] & wP) for i in range(n)]
    g0 = dict(g, dP=ns0["dP1"], roll=ns0["roll"], live=ns0["live"], span=span0, close=ns0["close1"])
    null0, _, null0_s = R55.enumerate_null({PRIMARY_CELL: dict(book="published", sign_held=np.where(wP[None, :], held0, 0.0), scale_held=ones)},
                                            g0, live_idx0, wP, ns0["r1d"], upp, comm_rt, tick_usd, dollar_roots, lambda *a: None, with_sortino=True)
    col0 = null0[keep, 0]; o0 = R55.sharpe(x0[wP])
    amendment = {"rule": f"formation settlement = last finite within {FFILL_FORMATION} sessions ending at the month-end (D556's carry_at_month_ends rule); as pre-registered = the month-end session alone",
                 "why": "2020-06-30 is a truncated archive day (237 of ~900 settlements) and 2021-05-31 is Memorial Day (in the session calendar on a Globex evening bar, no settlements); each voided twelve month-ends for every root",
                 "as_pre_registered": {"gross_sharpe": o0, "gross_sortino": R55.sortino(x0[wP]), "flat_month_ends_primary": int(sum(1 for k in range(K) if meP[k] and diag0[k]["flat"])),
                                       "mean_eligible_primary": float(np.mean([diag0[k]["n_eligible"] for k in range(K) if meP[k]])),
                                       "null_n1": {"p05": float(np.percentile(col0, 5)), "p50": float(np.percentile(col0, 50)), "p95": float(np.percentile(col0, 95)),
                                                   "pct_rank": float((col0 < o0).mean()), "clears_p95": bool(o0 > np.percentile(col0, 95))}},
                 "amended": {"gross_sharpe": results_cells[CELL_NAMES[PRIMARY_CELL]]["gross"]["sharpe"], "flat_month_ends_primary": eligibility["flat_month_ends_primary"],
                             "mean_eligible_primary": eligibility["mean_eligible_primary"]}}
    log(f"  amendment: as pre-registered (ffill 1) primary {o0:+.3f}, {amendment['as_pre_registered']['flat_month_ends_primary']} flat month-ends, N1 rank {amendment['as_pre_registered']['null_n1']['pct_rank']:.3f}; "
        f"amended (ffill {FFILL_FORMATION}) {amendment['amended']['gross_sharpe']:+.3f}, {amendment['amended']['flat_month_ends_primary']} flat")

    # ---- component line ----
    dc = results_cells[CELL_NAMES[("high4low4", "dollar")]]
    comp = {"C_a_net_sharpe": dc["net"]["sharpe"], "C_a_net_sortino": dc["net"]["sortino"], "gross_sharpe": dc["gross"]["sharpe"],
            "C_c_skew": dc["net"]["skew"], "C_d_sigma_daily_usd": dc["net"]["sd_daily"], "hit": dc["net"]["hit"], "total_usd": dc["net"]["total"],
            "cd_subset_net_sharpe": dc["cd_subset"]["net"]["sharpe"], "cd_subset_sigma": dc["cd_subset"]["net"]["sd_daily"],
            "largest_root_share": dc["largest_root_share"], "top_roots_usd": list(dc["per_root_net_usd"].items())[:3],
            "n1_rank": n1["per_cell"][CELL_NAMES[("high4low4", "dollar")]]["pct_rank"],
            "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk", "entered": False,
            "fails": [c for c, bad in (("C-a", dc["net"]["sharpe"] <= 0.5), ("C-c", dc["net"]["skew"] < -0.5), ("C-d", dc["net"]["sd_daily"] > R55.C_D_SIGMA)) if bad]}
    log(f"  component: net {comp['C_a_net_sharpe']:+.3f} skew {comp['C_c_skew']:+.2f} sigma ${comp['C_d_sigma_daily_usd']:,.0f} largest root share {comp['largest_root_share']}; fails {comp['fails']}")

    # ---- predictions ----
    prim = results_cells[CELL_NAMES[PRIMARY_CELL]]
    era_keys = list(per_era.keys())
    preds = {
        "P-1": {"claim": "primary gross Sharpe 2016-2023 > 0 and above N1 p95; point 0.25-0.55", "value": prim["gross"]["sharpe"], "p95": primary["p95"],
                "holds": bool(prim["gross"]["sharpe"] > 0 and primary["clears_p95"]), "in_point_range": bool(0.25 <= prim["gross"]["sharpe"] <= 0.55)},
        "P-2": {"claim": "|Spearman(BM, basis)| < 0.7 (point -0.2..+0.2); |Spearman(BM, mom)| < 0.5", "bm_basis": orth["bm_vs_basis"]["mean_cross_sectional"],
                "bm_mom": orth["bm_vs_mom"]["mean_cross_sectional"],
                "holds": bool(abs(orth["bm_vs_basis"]["mean_cross_sectional"]) < 0.7 and abs(orth["bm_vs_mom"]["mean_cross_sectional"]) < 0.5),
                "in_point_range": bool(-0.2 <= orth["bm_vs_basis"]["mean_cross_sectional"] <= 0.2)},
        "P-3": {"claim": "turnover > D557's 5.6 weight-units/yr; point 8-15", "value": prim["ann_turnover_weight_units"],
                "holds": bool(prim["ann_turnover_weight_units"] > 5.6), "in_point_range": bool(8 <= prim["ann_turnover_weight_units"] <= 15)},
        "P-4": {"claim": "M6: Sharpe 2016-2023 >= first half (first positioned day .. 2015-12-31)", "second": prim["gross"]["sharpe"], "first": per_era[era_keys[-1]]["sharpe"],
                "holds": bool(prim["gross"]["sharpe"] >= per_era[era_keys[-1]]["sharpe"])},
        "P-5": {"claim": "c5 on carry A's worst 5% days < 0 (point -0.1..-0.4); DD ratio not below null p05", "c5": ov["c5"], "dd_ratio": ov["dd_ratio"],
                "holds": bool(ov["c5"] < 0 and not overlay_carry["null"]["dd_ratio"]["below_p05"]), "in_point_range": bool(-0.4 <= ov["c5"] <= -0.1)},
        "P-6": {"claim": "monthly return higher in high-vol formation months than low", "high": vol_split["high_vol_half"]["mean_monthly"], "low": vol_split["low_vol_half"]["mean_monthly"],
                "holds": bool(vol_split["high_vol_half"]["mean_monthly"] > vol_split["low_vol_half"]["mean_monthly"])},
        "P-7": {"claim": "High4-Low4 spreading return > 0 on 2016-2023", "value": spreading["gross"]["mean_daily"], "sharpe": spreading["gross"]["sharpe"],
                "holds": bool(spreading["gross"]["mean_daily"] > 0)},
        "P-8": {"claim": "P&L positive on >= 9 of 17 roots over 2011-2023", "n_positive": n_pos_long, "holds": bool(n_pos_long >= 9)},
        "P-9": {"claim": "dollar sigma > $500", "value": comp["C_d_sigma_daily_usd"], "largest_root_share": comp["largest_root_share"], "holds": bool(comp["C_d_sigma_daily_usd"] > R55.C_D_SIGMA)},
        "P-10": {"claim": "falsifiers", "collapsed_into_carry": bool(abs(orth["bm_vs_basis"]["mean_cross_sectional"]) > 0.7), "harness_failed": bool(not harness["ok"]),
                 "below_n1_p50": bool(prim["gross"]["sharpe"] < primary["p50"])},
    }
    verdict = {"declared": "PASS" if (prim["gross"]["sharpe"] > 0 and primary["clears_p95"] and n2["clears_p95"]) else "DOES NOT PASS",
               "harness": "HARNESS OK" if harness["ok"] else "HARNESS SUSPECT",
               "orthogonality": "COLLAPSED INTO CARRY" if preds["P-10"]["collapsed_into_carry"] else "DISTINCT"}
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "P-10") + f"; P-10 {preds['P-10']}")
    log(f"  VERDICT {verdict['declared']} / {verdict['harness']} / {verdict['orthogonality']}")

    res = {"max_drawdown_convention": {
               "sign": "negative",
               "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak) in simple-return units for the "
                       "published books; in dollars for the dollar book; in units of daily sigma for the overlay blend (dd_ratio is blend over base). "
                       "Not a fraction of a compounded peak (D542).", "record": "D542"},
           "spec": "D564", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "strip_sha256": R55.sha256(R56.STRIP), "curve_sha256": R55.sha256(R56.CURVE),
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum()), "sessions_long": int(wL.sum()), "month_ends": K},
           "universe": {"roots": CM, "energy_delivery_rule": "delivery >= m+3", "other_delivery_rule": "delivery >= m+2", "lookback_months": LOOKBACK,
                        "n_leg": N_LEG, "min_eligible": MIN_ELIGIBLE, "stale_sessions": STALE_SESSIONS, "min_size": dict(zip(CM, size_name)), "dollar_roots": dollar_roots},
           "eligibility": eligibility,
           "signals": {"bm_at_month_ends": {r: BM[i].tolist() for i, r in enumerate(CM)}, "month_end_dates": [str(days[m]) for m in me],
                       "eligible": {r: elig[i].tolist() for i, r in enumerate(CM)}, "member_primary": {r: member[i].tolist() for i, r in enumerate(CM)}},
           "cells": results_cells, "primary": primary, "null_n1": n1, "null_n2": n2, "null_n3": n3, "root_months": root_months,
           "concentration": conc, "per_root": per_root, "per_era": per_era, "per_year": per_year, "spreading": spreading, "vol_split": vol_split,
           "orthogonality": orth, "non_seasonal_diagnostic": non_seasonal, "overlay_carry": overlay_carry, "harness": harness,
           "component_line": comp, "amendment": amendment, "predictions": preds, "verdict": verdict, "audits": audits,
           "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: a synthetic strip with known curve dynamics, no fixture read
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D564 SELF-TEST -- synthetic strip, no fixture read, no cell scored\n")
    rng = np.random.default_rng(64)
    days = pd.bdate_range("2012-01-02", "2014-12-31").strftime("%Y-%m-%d").to_numpy()
    T = len(days); me = R55.month_ends(days)
    # three roots: FRONT (front outperforms second: contango decaying -> BM > 0), BACK (the reverse), FLAT (equal)
    roots = ["FRONT", "BACK", "FLAT"]; rows = []
    for r, tilt in zip(roots, (+0.004, -0.004, 0.0)):
        spot = 100.0
        for t, d in enumerate(days):
            spot *= math.exp(0.0002 * rng.standard_normal())
            y, m = int(d[:4]), int(d[5:7])
            for dm in range(1, 8):                                    # seven listed delivery months ahead
                dy, dmo = divmod(y * 12 + m - 1 + dm, 12); dmo += 1
                code = f"{'CL' if r == 'FRONT' else 'GC'}{'FGHJKMNQUVXZ'[dmo - 1]}{dy % 10}"
                # settle: spot x exp(slope x tenor) -- exponential in tenor so every contract's roll return is the
                # same and BM is exactly zero -- times a per-root drift that makes the front outperform (tilt > 0)
                # or underperform the second nearby
                settle = spot * math.exp(0.01 * dm - tilt * (t / T) * dm)
                rows.append((r, code, d, settle))
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    tables = strip_tables(strip, days, roots)                  # the run's own table builder (CL/GC codes resolve in FB.ym)
    # [1] the delivery rule: T1 at least two months ahead (three for energy), T2 the next listed
    A, cols = tables["FRONT"]; t = me[3]; j1, j2 = choose_nearby(A, cols, t, days[t], energy=False)
    y, m = int(days[t][:4]), int(days[t][5:7])
    if cols[j1] != y * 12 + m + 2 or cols[j2] != cols[j1] + 1:
        raise AssertionError("delivery rule")
    j1e, _ = choose_nearby(A, cols, t, days[t], energy=True)
    if cols[j1e] != y * 12 + m + 3:
        raise AssertionError("energy delivery rule")
    print("  [1] T1 is the first delivery >= m+2 (m+3 for energy) with a settlement; T2 the next listed")
    # [2] BM known answers: FRONT > 0, BACK < 0, FLAT ~ 0; eligibility begins after twelve monthly returns
    ns = nearby_series(tables, roots, days, me)
    BM, mom, elig = signals_at_month_ends(ns["R1"], ns["R2"], ns["stale"])
    k_last = len(me) - 1
    if not (elig[:, k_last].all() and BM[0, k_last] > 0 > BM[1, k_last] and abs(BM[2, k_last]) < 1e-9):
        raise AssertionError(f"BM known answer: {BM[:, k_last]}")
    if elig[:, :LOOKBACK].any():
        raise AssertionError("eligible before twelve monthly returns exist")
    print(f"  [2] BM known answers: FRONT {BM[0, k_last]:+.4f} BACK {BM[1, k_last]:+.4f} FLAT {BM[2, k_last]:+.1e}; first eligible month-end index {int(np.flatnonzero(elig.any(0))[0])}")
    # [3] the second path agrees exactly, and RAISES on a negated grid
    ok = 0; pivF = strip_pivot(strip[strip["root"] == "FRONT"], days)
    for k in range(LOOKBACK + 1, len(me)):
        ref = bm_pandas(pivF, days, me, k, energy=False)
        if ref is None or not np.isclose(ref, BM[0, k], rtol=1e-10, atol=1e-14):
            raise AssertionError("second path disagrees")
        ok += 1
    R61._expect_raise(lambda: audit_bm_from_strip(-BM, elig, strip, roots, days, me, n_check=5), "BM audit on a negated grid")
    print(f"  [3] pandas path reproduces BM at {ok} month-ends and RAISES on a negated grid")
    # [3b] the formation rule: a month-end with no settlements voids twelve month-ends at ffill = 1 and none at ffill = 5,
    #      and the two paths agree under the amended rule too
    tables_gap = {r: (A_.copy(), c_) for r, (A_, c_) in tables.items()}
    t_gap = me[20]
    for r in roots:
        tables_gap[r][0][t_gap, :] = np.nan
    ns_g1 = nearby_series(tables_gap, roots, days, me, ffill=1); _, _, elig_g1 = signals_at_month_ends(ns_g1["R1"], ns_g1["R2"], ns_g1["stale"])
    ns_g5 = nearby_series(tables_gap, roots, days, me, ffill=5); BM_g5, _, elig_g5 = signals_at_month_ends(ns_g5["R1"], ns_g5["R2"], ns_g5["stale"])
    voided_1 = int((elig[:, LOOKBACK:] & ~elig_g1[:, LOOKBACK:]).sum()); voided_5 = int((elig[:, LOOKBACK:] & ~elig_g5[:, LOOKBACK:]).sum())
    if not (voided_1 >= 12 * len(roots) and voided_5 == 0):
        raise AssertionError(f"formation rule: voided {voided_1} at ffill 1, {voided_5} at ffill 5")
    strip_gap = strip[strip["ref"] != days[t_gap]]
    piv5 = strip_pivot(strip_gap[strip_gap["root"] == "FRONT"], days, ffill=5)
    for k in (21, 25, 30):
        ref = bm_pandas(piv5, days, me, k, energy=False)
        if ref is None or not np.isclose(ref, BM_g5[0, k], rtol=1e-10, atol=1e-14):
            raise AssertionError("second path disagrees under the amended rule")
    print(f"  [3b] a settlement-less month-end voids {voided_1} root-months at ffill 1 and {voided_5} at ffill 5; the pandas path agrees under the amended rule")
    # [4] staleness: freezing the second contract's settlement over three sessions marks the root stale
    A2 = tables["BACK"][0].copy(); t = me[15]; _, j2 = choose_nearby(A2, tables["BACK"][1], t, days[t], False)
    A2[t - 2:t + 1, j2] = A2[t, j2]
    if not is_stale(A2, t, j2) or is_stale(tables["BACK"][0], t, j2):
        raise AssertionError("staleness")
    print("  [4] staleness filter fires on three repeated settlements and not otherwise")
    # [5] daily nearby return chains within the month and the held contract never expires inside it
    if ns["held_ok"][:, LOOKBACK:k_last - 1].mean() < 0.99:
        raise AssertionError("held contract")
    i = 0; k = 14; t0, t1 = me[k], me[k + 1]; j = ns["T1"][i, k]
    chain = np.prod(1.0 + ns["r1d"][i, t0 + 1:t1 + 1]) - 1.0
    if not np.isclose(chain, A[t1, j] / A[t0, j] - 1.0, rtol=1e-12):
        raise AssertionError("daily chain != monthly return")
    print("  [5] the daily nearby return compounds to the monthly return of the same contract; held contracts settle at the next month-end")
    # [6] membership: two paths agree, RAISE on a swapped pair; hold/lag/right-quantity audits raise
    elig3 = elig.copy(); sig3 = BM.copy()
    mem, _ = membership_fixed(sig3, elig3, roots, 1, 3); mem_pd = membership_fixed_pandas(sig3, elig3, roots, 1, 3)
    R57.audit_leg_membership(mem, mem_pd, me, days)
    R61._expect_raise(lambda: R57.audit_leg_membership(R57.swap_one_pair(mem), mem_pd, me, days), "membership audit on a swapped pair")
    live = ns["live"]; held = R55.hold_from_month_ends(mem.astype(float), me, T, live)
    R55.audit_lag(held, mem_pd.astype(float), me, live, T)
    unl = np.zeros_like(held)
    for kk, m_ix in enumerate(me):
        lo = me[kk - 1] + 1 if kk > 0 else 0
        unl[:, lo:m_ix + 1] = mem[:, kk][:, None]
    R61._expect_raise(lambda: R55.audit_lag(np.where(live, unl, 0.0), mem_pd.astype(float), me, live, T), "lag audit on an unlagged grid")
    daily_break = np.tile(np.where(np.arange(T) % 2 == 0, 1.0, -1.0), (len(roots), 1))   # flips every session
    R61._expect_raise(lambda: R55.audit_right_quantity(daily_break, me, T), "right-quantity on a daily grid")
    if not (mem[0, k_last] == 1 and mem[1, k_last] == -1):
        raise AssertionError("FRONT should be long and BACK short")
    print("  [6] membership paths agree (FRONT long, BACK short) and RAISE on a swapped pair; lag and right-quantity audits raise")
    # [7] the name-randomised null preserves leg counts
    n3, _ = name_randomised_null(mem, elig3, me, T, live, ns["r1d"], np.ones(T, dtype=bool), days, 5, 1)
    if not np.isfinite(n3).all():
        raise AssertionError("N3")
    print("  [7] name-randomised null runs with leg counts preserved")
    print("\nSELF-TEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
