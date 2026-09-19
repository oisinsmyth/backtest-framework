"""D557 -- cross-sectional TERM STRUCTURE on commodities AS PUBLISHED (Erb & Harvey 2006; Fuertes,
Miffre & Rallis 2010) on the 17 commodity roots of the breadth fixture, off D556's curve table.

Spec committed in e3a5785 BEFORE this file (R8). Primary window 2016-01-04..2023-12-29; long window
2011-01-03..2023-12-29 as a declared diagnostic; the 2024+ slice is RESERVED AND NEVER READ. Nothing
admitted (R15).

    python scripts/run_d557_xs_term_structure.py --selftest
    python scripts/run_d557_xs_term_structure.py --run        # -> data/d557_xs_term_structure.json

Everything that is not the sort is imported: from D555 the grids, the EW vol, the holds, the book
return, the dollar book, the three audits, the enumerated rotation null and its purge; from D556 the
carry grid, the month-end read (ffill 5 sessions), the vol-scaled positions, the minimum size and
the strip audit. The sort: at each month-end rank the eligible commodities by annualised carry,
long the top ceil(n/3) (most backwardated), short the bottom ceil(n/3), middle flat, ties by root
symbol, fewer than 9 eligible -> flat month. Three declared cells: EW/published (PRIMARY),
vol-scaled/published, dollar at minimum size (scored net). One new audit: the leg membership at
every month-end recomputed by an independent pandas path.
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


R56 = _load("d556", "run_d556_carry_timing.py")      # D556 loads D555 itself: one instance of each
R55 = R56.R55

OUT = REPO / "data" / "d557_xs_term_structure.json"
SPEC = "e3a5785"
PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
CM = list(R55.SECTOR["CM"])                          # the 17 commodity roots, ranked in full
MIN_ELIGIBLE = 9                                     # fewer -> flat month (declared)
LEG_DIVISOR = 3                                      # n_leg = ceil(n_eligible / 3)
PRIMARY_CELL = ("ew", "published")
CELL_NAMES = {("ew", "published"): "ew/published", ("vol", "published"): "volscaled/published",
              ("dollar", "dollar"): "sort/dollar"}
POINT_RANGE_NET = (0.2, 0.4)                         # the deposit's §4
POINT_RANGE_GROSS = (0.2, 0.45)                      # + the modelled cost's < 0.05 Sharpe (declared)
TIME_SOFT_S, TIME_HARD_S = 600.0, 900.0
REQUIRED_OUTPUTS = ["spec", "commit", "fixture_sha256", "curve_sha256", "strip_sha256", "windows", "universe",
                    "eligibility", "cells", "primary", "null_n1", "null_n2", "root_months", "concentration",
                    "per_root", "per_era", "per_year", "comparability", "dollar_book", "component_line",
                    "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# the sort -- implementation A (numpy) and the independent implementation B (pandas)
# --------------------------------------------------------------------------------------------
def membership_at_month_ends(carry_me: np.ndarray, roots):
    """A. member[i, k] in {+1, 0, -1}: rank the eligible (finite) carries descending, ties by root
    symbol ascending (np.lexsort, last key primary), long the top ceil(n/3), short the bottom
    ceil(n/3). Fewer than MIN_ELIGIBLE eligible -> the month-end is flat. Returns (member, diag)."""
    n, K = carry_me.shape
    names = np.array(roots)
    member = np.zeros((n, K), dtype=int)
    diag = []
    for k in range(K):
        v = carry_me[:, k]
        el = np.flatnonzero(np.isfinite(v))
        rec = {"n_eligible": int(el.size), "n_long": 0, "n_short": 0, "flat": False, "tie_at_boundary": False,
               "missing": [str(names[i]) for i in range(n) if i not in set(el.tolist())]}
        if el.size < MIN_ELIGIBLE:
            rec["flat"] = True; diag.append(rec); continue
        n_leg = math.ceil(el.size / LEG_DIVISOR)
        order = el[np.lexsort((names[el], -v[el]))]                # primary key -carry, then symbol
        member[order[:n_leg], k] = 1
        member[order[el.size - n_leg:], k] = -1
        sv = v[order]
        rec["tie_at_boundary"] = bool(sv[n_leg - 1] == sv[n_leg] or sv[el.size - n_leg] == sv[el.size - n_leg - 1])
        rec["n_long"] = int(n_leg); rec["n_short"] = int(n_leg)
        diag.append(rec)
    return member, diag


def membership_pandas(carry_me: np.ndarray, roots) -> np.ndarray:
    """B. Per month-end: a Series over the eligible roots, sorted by symbol, `rank(method="first",
    ascending=False)` (so a tie goes to the earlier symbol), long rank <= n_leg, short rank > n - n_leg.
    Never calls membership_at_month_ends."""
    n, K = carry_me.shape
    out = np.zeros((n, K), dtype=int)
    pos = {r: i for i, r in enumerate(roots)}
    for k in range(K):
        s = pd.Series(carry_me[:, k], index=list(roots)).dropna().sort_index()
        if len(s) < MIN_ELIGIBLE:
            continue
        n_leg = math.ceil(len(s) / LEG_DIVISOR)
        rk = s.rank(method="first", ascending=False)
        for r in s.index[rk <= n_leg]:
            out[pos[r], k] = 1
        for r in s.index[rk > len(s) - n_leg]:
            out[pos[r], k] = -1
    return out


def audit_leg_membership(member_a: np.ndarray, member_b: np.ndarray, me, days):
    """(e) The long/short/flat membership at every month-end must agree between the two paths."""
    bad = np.flatnonzero((member_a != member_b).any(0))
    if bad.size:
        raise AssertionError(f"LEG-MEMBERSHIP AUDIT: the two paths disagree at {bad.size} month-ends "
                             f"(first {days[me[bad[0]]]})")
    if not ((member_a == 1).sum(0) == (member_a == -1).sum(0)).all():
        raise AssertionError("LEG-MEMBERSHIP AUDIT: a long leg and its short leg differ in size")
    return int((member_a != 0).sum())


def swap_one_pair(member: np.ndarray) -> np.ndarray:
    """The deliberate break for (e): at the first month-end with both legs, swap one long with one short."""
    bad = member.copy()
    for k in range(member.shape[1]):
        L = np.flatnonzero(member[:, k] == 1); S = np.flatnonzero(member[:, k] == -1)
        if L.size and S.size:
            bad[L[0], k] = -1; bad[S[0], k] = 1
            return bad
    raise AssertionError("no month-end with both legs to break")


def sub_grid(g, roots_sub):
    ix = [g["roots"].index(r) for r in roots_sub]
    out = {k: (v[ix] if isinstance(v, np.ndarray) and v.ndim == 2 else v) for k, v in g.items()}
    out["roots"] = list(roots_sub)
    return out, ix


# --------------------------------------------------------------------------------------------
# reporting helpers
# --------------------------------------------------------------------------------------------
def root_month_table(pos, rsimple, days, w):
    """One row per (root, calendar month) with a non-zero position inside w; contribution in units of
    book return (sign x simple return / positioned count), so the rows sum to the book."""
    cnt = (pos != 0).sum(0)
    contrib = pos * rsimple / np.where(cnt > 0, cnt, 1)[None, :]
    ym = np.array([d[:7] for d in days])
    rows = []
    for i in range(pos.shape[0]):
        m = w & (pos[i] != 0)
        if not m.any():
            continue
        df = pd.DataFrame({"ym": ym[m], "c": contrib[i][m], "s": np.sign(pos[i][m])})
        agg = df.groupby("ym").agg(c=("c", "sum"), s=("s", "first"), n=("s", "size"))
        for u, row in agg.iterrows():
            rows.append((i, u, float(row["c"]), int(row["s"]), int(row["n"])))
    return pd.DataFrame(rows, columns=["root", "ym", "contrib", "leg", "sessions"])


def dist_stats(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    if x.size < 4:
        return {"n": int(x.size)}
    s = np.sort(x); k = max(1, int(math.floor(0.01 * x.size)))
    wins = x[x > 0]; loss = x[x < 0]
    return {"n": int(x.size), "mean": float(x.mean()), "median": float(np.median(x)),
            "mean_ex_top_1pct": float(s[:-k].mean()), "mean_ex_bottom_1pct": float(s[k:].mean()),
            "mean_trim_1pct_both": float(s[k:-k].mean()), "win_rate": float((x > 0).mean()),
            "payoff": float(wins.mean() / abs(loss.mean())) if wins.size and loss.size else None,
            "skew": float(pd.Series(x).skew()), "kurt": float(pd.Series(x).kurt()),
            "top_1pct_share_of_total": float(s[-k:].sum() / x.sum()) if x.sum() != 0 else None}


def concentration(totals: dict) -> dict:
    v = np.array(sorted(totals.values(), reverse=True)); tot = v.sum()
    share = lambda k: float(v[:k].sum() / tot) if tot != 0 else None
    half = None
    if tot > 0:
        cs = np.cumsum(v); half = int(np.searchsorted(cs, 0.5 * tot) + 1)
    return {"total": float(tot), "top1_share": share(1), "top5_share": share(5), "top10_share": share(10),
            "roots_to_half_pnl": half, "sorted": sorted(totals.items(), key=lambda kv: -kv[1])}


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D557 -- cross-sectional term structure as published, {len(CM)} commodity roots\n"
        f"      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    gates = {}
    for p in (R56.CURVE, R56.STRIP):
        meta = json.loads(p.with_suffix("").with_suffix(".meta.json").read_text(encoding="utf-8"))
        gates[p.name] = bool(meta.get("all_gates_pass"))
        if not gates[p.name]:
            raise AssertionError(f"{p.name}: gates have not passed -- nothing interpretable (P-7)")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present after filtering")
    live_start = R55.live_start_by_rule(df); g_all = R55.build_grids(df, live_start)
    g, cm_ix = sub_grid(g_all, CM)
    roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    me = R55.month_ends(days); sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    curve = curve[curve["ref"] < RESERVED_FROM]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & strip["root"].isin(CM)]
    if (curve["ref"] >= RESERVED_FROM).any() or (strip["ref"] >= RESERVED_FROM).any() or days[-1] >= RESERVED_FROM:
        raise AssertionError("a reserved session survived the filter")
    last_read = {"breadth": str(days[-1]), "curve": str(curve["ref"].max()), "strip": str(strip["ref"].max())}
    log(f"  fixture: {n} roots x {T} sessions {days[0]}..{days[-1]}; last session read {last_read}")
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    if not all(int((g["span"][i] & wP).sum()) == int(wP.sum()) for i in range(n)):
        raise AssertionError("the 17 roots do not share one span on the primary window (pre-reg §0)")

    C = R56.carry_grid(g, curve)
    carry_me = R56.carry_at_month_ends(C, g["live"], me)
    carry_me_pd = R56.carry_at_month_ends_pandas(C, g["live"], days, roots, me)
    if not np.array_equal(np.nan_to_num(carry_me, nan=-1e9), np.nan_to_num(carry_me_pd, nan=-1e9)):
        raise AssertionError("month-end carry: numpy and pandas paths disagree")
    member, diag = membership_at_month_ends(carry_me, roots)
    member_pd = membership_pandas(carry_me_pd, roots)
    me_days = days[me]
    for k, rec in enumerate(diag):
        rec["month_end"] = str(me_days[k])
    upp, tick_usd, comm_rt, size_name = R56.min_size(g, roots)
    dollar_roots = [r for r in roots if r not in R55.DOLLAR_EXCLUDED]

    # ---- audits, each proven to raise on its deliberate break
    audits = {}
    audits["leg_membership_cells"] = audit_leg_membership(member, member_pd, me, days)
    try:
        audit_leg_membership(swap_one_pair(member), member_pd, me, days); raise RuntimeError("leg audit accepted a SWAPPED pair")
    except AssertionError:
        audits["leg_membership_raises_on_swapped_pair"] = True
    signA = np.where(np.isfinite(carry_me), np.sign(carry_me), 0.0)
    breadth_front = {(r, d): f for r, d, f in zip(curve["root"], curve["ref"], curve["front"]) if r in set(CM)}
    audits["carry_from_strip_cells_checked"] = R56.audit_carry_from_strip(signA, me, g, strip, breadth_front)
    try:
        R56.audit_carry_from_strip(-signA, me, g, strip, breadth_front, n_check=40); raise RuntimeError("carry audit accepted a NEGATED grid")
    except AssertionError:
        audits["carry_audit_raises_on_negated_grid"] = True
    # cells
    avg_me = member.astype(float)
    sh, pos_vol, sc_vol, sd = R56.positions_from_signs(avg_me, sig, me, g)
    sc_ew = R55.hold_from_month_ends(np.ones((n, len(me))), me, T, g["span"])     # 1.0 inside the span: sign x scale = membership
    pos_ew = sh * sc_ew
    if not np.array_equal(pos_ew, sh):
        raise AssertionError("EW positions are not the held membership")
    cells = {("ew", "published"): dict(book="published", sign_held=sh, scale_held=sc_ew, pos=pos_ew),
             ("vol", "published"): dict(book="published", sign_held=sh, scale_held=sc_vol, pos=pos_vol),
             ("dollar", "dollar"): dict(book="dollar", sign_held=sd.astype(float), scale_held=None, pos=None)}
    prim = cells[PRIMARY_CELL]
    audits["lag_held_cells"] = R55.audit_lag(sh, member_pd.astype(float), me, g["span"], T)
    unl = np.zeros_like(sh)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = member[:, k][:, None]
    unl = np.where(g["span"], unl, 0.0)
    try:
        R55.audit_lag(unl, member_pd.astype(float), me, g["span"], T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(sh, me, T)
    try:
        R55.audit_right_quantity(np.sign(np.nan_to_num(C)), me, T); raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    sdi = sd.astype(int)
    gross_a, _, _ = R55.dollar_book(sdi, g, upp, comm_rt, tick_usd, roots)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(gross_a, sdi, g, upp)
    for label, bad in (("negated", -gross_a),
                       ("mislagged", R55.dollar_book(sdi, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, roots)[0])):
        try:
            R55.audit_sign_in_money(bad, sdi, g, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True
    x_lag = R55.book_return(pos_ew, rsimple); x_unl = R55.book_return(unl * sc_ew, rsimple)
    audits["pnl_differs_from_unlagged"] = bool(not np.allclose(x_lag, x_unl))
    if not audits["pnl_differs_from_unlagged"]:
        raise AssertionError("lagged and unlagged P&L coincide")
    log(f"  audits: {audits}")

    # ---- eligibility per month-end
    kP = R55.window_mask(me_days, *PRIMARY); kL = R55.window_mask(me_days, *LONG)
    def _elig(mask):
        d = [diag[k] for k in range(len(me)) if mask[k]]
        return {"month_ends": len(d), "n_eligible_counts": {str(u): int(c) for u, c in zip(*np.unique([r["n_eligible"] for r in d], return_counts=True))},
                "boundary_ties": int(sum(r["tie_at_boundary"] for r in d)), "flat_months": int(sum(r["flat"] for r in d)),
                "month_ends_with_missing": [{"month_end": r["month_end"], "missing": r["missing"], "legs": f"{r['n_long']}/{r['n_eligible'] - r['n_long'] - r['n_short']}/{r['n_short']}"} for r in d if r["missing"]],
                "leg_sizes": {str(u): int(c) for u, c in zip(*np.unique([r["n_long"] for r in d], return_counts=True))}}
    eligibility = {"primary": _elig(kP), "long": _elig(kL), "per_month_end": diag,
                   "share_root_months_long": float((member[:, kL] == 1).mean()), "share_root_months_short": float((member[:, kL] == -1).mean())}
    log(f"  eligibility (primary): {eligibility['primary']['n_eligible_counts']} eligible; ties {eligibility['primary']['boundary_ties']}; "
        f"flat {eligibility['primary']['flat_months']}; legs {eligibility['primary']['leg_sizes']}")

    # ---- scoring
    dP_days, dL_days = days[wP], days[wL]
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]
    results_cells, scored, dollar_grids = {}, {}, {}
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
                     "positioned_names_mean": float((c["pos"] != 0).sum(0)[wP].mean()),
                     "dollar_neutral_in_weight": bool(np.allclose(c["pos"].sum(0)[wP], 0.0)) if key[0] == "ew" else False}
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
                     "traded_names_mean": float((sP != 0)[np.array([r in dollar_roots for r in roots])][:, wP].sum(0).mean()),
                     "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d"),
                                   "net": R55.stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d net")},
                     "gross_long": R55.stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $")}
            scored[key] = dict(gross=xg, net=xn); dollar_grids = dict(gross=gross, cost=cost)
        results_cells[name] = entry
        log(f"  {name:20s} gross SR {entry['gross']['sharpe']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}")

    # ---- groups 2 and 3 on the primary
    x = scored[PRIMARY_CELL]["gross"]; pos = prim["pos"]
    rm = root_month_table(pos, rsimple, days, wP)
    root_months = {"combined": dist_stats(rm["contrib"].to_numpy()), "long_leg": dist_stats(rm.loc[rm["leg"] == 1, "contrib"].to_numpy()),
                   "short_leg": dist_stats(rm.loc[rm["leg"] == -1, "contrib"].to_numpy()),
                   "unit": "book-return units: sign x simple return / positioned count, summed over the month's sessions"}
    cnt = (pos != 0).sum(0); contrib = pos * rsimple / np.where(cnt > 0, cnt, 1)[None, :]
    per_root = {}
    for i, r in enumerate(roots):
        xi = contrib[i]; li = pos[i] != 0
        per_root[r] = {"total_primary": float(xi[wP].sum()), "total_long": float(xi[wL].sum()),
                       "sharpe_primary": R55.sharpe(xi[wP & li]) if (wP & li).sum() > 60 else None, "sortino_primary": R55.sortino(xi[wP & li]) if (wP & li).sum() > 60 else None,
                       "months_long": int((member[i, kP] == 1).sum()), "months_short": int((member[i, kP] == -1).sum()),
                       "months_flat": int((member[i, kP] == 0).sum()), "mean_carry_me": float(np.nanmean(carry_me[i][kP])),
                       "min_size": size_name[i], "sigma_usd_min_size": root_sigma[r], "live_start": live_start[r]}
    conc = concentration({r: per_root[r]["total_primary"] for r in roots})
    conc["n_roots_positive"] = int(sum(per_root[r]["total_primary"] > 0 for r in roots))
    per_era = {f"{a}..{b}": {"sharpe": R55.sharpe(x[R55.window_mask(days, a, b)]), "sortino": R55.sortino(x[R55.window_mask(days, a, b)]), "n_days": int(R55.window_mask(days, a, b).sum())} for a, b in ERAS}
    yrs = sorted(set(d[:4] for d in days[wL]))
    per_year = {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "sortino": R55.sortino(x[np.array([d[:4] == y for d in days])]), "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in yrs}
    log(f"  root-months: long {root_months['long_leg'].get('mean')}, short {root_months['short_leg'].get('mean')}; "
        f"top1 {conc['top1_share']}, roots to half {conc['roots_to_half_pnl']}")

    # ---- comparability: D556's cell A restricted to the 17 commodities, rebuilt in-process
    trend12_me, _ = R55.signal_at_month_ends(g["rlog"], g["live"], days, me, 12)
    ct_signs = R56.cell_signs(carry_me, trend12_me, None)["A"]
    _, pos_ct, _, _ = R56.positions_from_signs(ct_signs, sig, me, g)
    x_ct = R55.book_return(pos_ct, rsimple)
    mon = lambda s: (1 + s).groupby(s.index.to_period("M")).prod() - 1
    xs = pd.Series(x, index=pd.to_datetime(days)); xcs = pd.Series(x_ct, index=pd.to_datetime(days))
    mA, mC = mon(xs[wP]), mon(xcs[wP])
    comparability = {"carry_timing_cm_sharpe_2016_2023": R55.sharpe(x_ct[wP]), "carry_timing_cm_sortino_2016_2023": R55.sortino(x_ct[wP]), "carry_timing_cm_sharpe_2011_2023": R55.sharpe(x_ct[wL]), "carry_timing_cm_sortino_2011_2023": R55.sortino(x_ct[wL]),
                     "rho_daily_2016_2023": float(np.corrcoef(x[wP], x_ct[wP])[0, 1]), "rho_monthly_2016_2023": float(np.corrcoef(mA.values, mC.values)[0, 1]),
                     "rho_daily_volscaled_vs_carry_timing": float(np.corrcoef(scored[("vol", "published")]["gross"][wP], x_ct[wP])[0, 1]),
                     "note": "D556 cell A (sign of carry_ann, 0.40/sigma, monthly holds) over the CM indices only; D556's own CM sector figure was -0.26"}
    log(f"  comparability: CM carry timing SR {comparability['carry_timing_cm_sharpe_2016_2023']:+.3f}; rho daily {comparability['rho_daily_2016_2023']:+.3f}, monthly {comparability['rho_monthly_2016_2023']:+.3f}")

    # ---- nulls, purged as declared; 20 offsets timed first
    live_idx = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    Tw = int(wP.sum())
    probe_ks = [k % (Tw - 1) or 1 for k in (1, 7, 63, 250, 999, 1500, 1777, 2000, 2010, 3, 11, 101, 333, 444, 555, 666, 777, 888, 1234, 1999)]
    t0 = time.time()
    for k in probe_ks:
        s_rot = R55.rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k)
        p = s_rot * prim["scale_held"]
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"enumeration not bit-identical at offset {k}")
        if not ((s_rot == 1).sum(0)[wP] == (s_rot == -1).sum(0)[wP]).all():
            raise AssertionError(f"rotated legs are not balanced at offset {k}")
        # the other two cells, as enumerate_null scores them, so the timing is the per-offset cost
        R55.book_return(s_rot * null_cells[("vol", "published")]["scale_held"], rsimple)
        gd, cd_, _ = R55.dollar_book(np.sign(R55.rotate_signs(null_cells[("dollar", "dollar")]["sign_held"], live_idx, k)).astype(int), g, upp, comm_rt, tick_usd, dollar_roots)
    per_offset = (time.time() - t0) / len(probe_ks)
    projected = per_offset * (Tw - 1)
    log(f"  exactness guard: 20 offsets bit-identical against the plain loop, legs balanced; {per_offset * 1e3:.1f} ms/offset -> projected {projected:.0f} s for {Tw - 1} offsets x 3 cells")
    if projected > TIME_HARD_S:
        raise AssertionError(f"projected null wall {projected:.0f} s > {TIME_HARD_S:.0f} s: stopping as declared")
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    names = [CELL_NAMES[k] for k in keys]
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
    primary = n1["per_cell"][CELL_NAMES[PRIMARY_CELL]]
    log(f"  N1 primary: observed {primary['observed']:+.3f}  p05 {primary['p05']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  rank {primary['pct_rank']:.3f}\n"
        f"  N2 family: best {n2['observed_best']:+.3f} ({n2['observed_best_cell']})  p50 {n2['p50']:+.3f}  p95 {n2['p95']:+.3f}  rank {n2['pct_rank']:.3f}")

    # ---- the dollar book decomposed by root, BEFORE the component line
    dcell = results_cells["sort/dollar"]
    net_grid = dollar_grids["gross"] - dollar_grids["cost"]
    per_root_dollar = {r: float(net_grid[i][wP].sum()) for i, r in enumerate(roots) if r in dollar_roots}
    dconc = concentration(per_root_dollar)
    top_r, top_v = dconc["sorted"][0]
    sig_vals = [root_sigma[r] for r in dollar_roots]
    dollar_decomp = {"per_root_net_usd_sorted": dconc["sorted"], "total_net_usd": dconc["total"],
                     "top_contributor": top_r, "top_contributor_share_of_total": (top_v / dconc["total"]) if dconc["total"] != 0 else None,
                     "total_without_top": float(dconc["total"] - top_v),
                     "sigma_usd_per_contract_range": [float(min(sig_vals)), float(max(sig_vals))],
                     "sigma_usd_per_contract": {r: root_sigma[r] for r in dollar_roots}, "cd_roots": cd_roots, "excluded": ["BZ"]}
    log("  dollar book by root (net $, 2016-2023): " + ", ".join(f"{r} {v:+,.0f}" for r, v in dconc["sorted"]))
    log(f"    total {dconc['total']:+,.0f}; top {top_r} {top_v:+,.0f} = {dollar_decomp['top_contributor_share_of_total']}; "
        f"sigma/contract ${min(sig_vals):,.0f}..${max(sig_vals):,.0f}; C-d roots {cd_roots}")
    component = {"C_a_net_sharpe": dcell["net"]["sharpe"], "se": dcell["net"]["se"], "gross_sharpe": dcell["gross"]["sharpe"],
                 "hit": dcell["net"]["hit"], "C_c_skew": dcell["net"]["skew"], "C_c_pass": bool(dcell["net"]["skew"] >= -0.5),
                 "C_d_sigma_usd": dcell["net"]["sd_daily"], "C_d_pass": bool(dcell["net"]["sd_daily"] <= R55.C_D_SIGMA),
                 "C_a_pass": bool(dcell["net"]["sharpe"] > 0.5), "cd_subbook_net_sharpe": dcell["cd_subset"]["net"]["sharpe"],
                 "cd_subbook_sigma_usd": dcell["cd_subset"]["net"]["sd_daily"], "cd_subbook_roots": cd_roots,
                 "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk",
                 "volscaled_dollar_cell": "not a fourth cell: sign(sign x 0.40/sigma) is the membership, the same object as sort/dollar"}
    log(f"  component line: C-a net {component['C_a_net_sharpe']:+.3f} (SE {component['se']:.2f}), gross {component['gross_sharpe']:+.3f}, hit {component['hit']:.3f}, "
        f"skew {component['C_c_skew']:+.2f}, sigma ${component['C_d_sigma_usd']:,.0f}/day; C-d sub-book net {component['cd_subbook_net_sharpe']:+.3f} sigma ${component['cd_subbook_sigma_usd']:,.0f}")

    # ---- predictions
    cE, cV = results_cells["ew/published"], results_cells["volscaled/published"]
    preds = {
        "P-1": {"claim": "EW gross Sharpe 2016-2023 > 0 and above N1 p95; net point range 0.2-0.4 judged on gross as 0.2-0.45",
                "value": cE["gross"]["sharpe"], "net": cE["net"]["sharpe"], "p95": primary["p95"],
                "holds": bool(cE["gross"]["sharpe"] > 0 and primary["clears_p95"]),
                "in_point_range": bool(POINT_RANGE_GROSS[0] <= cE["gross"]["sharpe"] <= POINT_RANGE_GROSS[1])},
        "P-2": {"claim": "|rho| daily 2016-2023 with CM-restricted carry timing > 0.5", "value": comparability["rho_daily_2016_2023"],
                "holds": bool(abs(comparability["rho_daily_2016_2023"]) > 0.5)},
        "P-3": {"claim": "long leg root-month mean contribution > short leg's", "long": root_months["long_leg"]["mean"], "short": root_months["short_leg"]["mean"],
                "holds": bool(root_months["long_leg"]["mean"] > root_months["short_leg"]["mean"])},
        "P-4": {"claim": "EW daily skew < 0", "value": cE["gross"]["skew"], "holds": bool(cE["gross"]["skew"] < 0)},
        "P-5": {"claim": "vol-scaled gross Sharpe within +-0.15 of EW", "ew": cE["gross"]["sharpe"], "vol": cV["gross"]["sharpe"],
                "holds": bool(abs(cV["gross"]["sharpe"] - cE["gross"]["sharpe"]) <= 0.15)},
        "P-6": {"claim": "dollar book fails C-d (daily sigma > $500)", "sigma": dcell["net"]["sd_daily"], "holds": bool(dcell["net"]["sd_daily"] > R55.C_D_SIGMA)},
        "P-7": {"claim": "falsifier: gates green and primary below N1 p50 -> the sort did badly on this window; a gate failing -> nothing interpretable",
                "gates": gates, "primary_below_p50": bool(cE["gross"]["sharpe"] < primary["p50"]),
                "fires_sort_did_badly": bool(all(gates.values()) and cE["gross"]["sharpe"] < primary["p50"])},
    }
    verdict = "PASS" if (cE["gross"]["sharpe"] > 0 and primary["clears_p95"] and n2["clears_p95"]) else "DOES NOT PASS"

    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS in this file are NEGATIVE: minimum of (cumulative daily return - running peak); "
                                                                  "return units for the published books, dollars at minimum size for the dollar books (D542).", "record": "D542"},
           "spec": "D557", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "curve_sha256": R55.sha256(R56.CURVE), "strip_sha256": R55.sha256(R56.STRIP),
           "fixture_gates": gates,
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum()), "sessions_long": int(wL.sum()),
                       "month_ends": int(len(me)), "month_ends_primary": int(kP.sum()), "last_session_read": last_read},
           "universe": {"ranked": roots, "dollar_traded": dollar_roots, "dollar_excluded": ["BZ"], "min_size": dict(zip(roots, size_name)),
                        "min_eligible": MIN_ELIGIBLE, "leg_rule": "n_leg = ceil(n_eligible / 3); ties by root symbol ascending; carry = annualised basis as D556 defines it",
                        "ffill_sessions": R56.FFILL_SESSIONS},
           "eligibility": eligibility, "cells": results_cells, "primary": primary, "null_n1": n1, "null_n2": n2,
           "root_months": root_months, "concentration": conc, "per_root": per_root, "per_era": per_era, "per_year": per_year,
           "comparability": comparability, "dollar_book": dollar_decomp, "component_line": component,
           "predictions": preds, "verdict": {"declared": verdict}, "audits": audits,
           "timing": {"wall_s": round(time.time() - t_start, 1), "null_ms_per_offset_probe": round(per_offset * 1e3, 2), "null_projected_s": round(projected, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(res, indent=1, default=R55._json_default), encoding="utf-8")
    log(f"\n  VERDICT {verdict}   -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: synthetic carries and bars, no fixture read, no cell scored
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D557 SELF-TEST -- synthetic carries and bars, no fixture read, no cell scored\n")
    rng = np.random.default_rng(557)
    days = pd.bdate_range("2012-01-02", "2014-12-31").strftime("%Y-%m-%d").to_numpy(); T = len(days)
    roots = CM[:12]; n = len(roots)                 # real codes: the strip audit's contract parser knows only real roots
    me = R55.month_ends(days); K = len(me)
    # carries: distinct per root, so the sort is known; the drift FOLLOWS the carry so a correct sort earns
    base = np.linspace(0.12, -0.12, n)
    rlog = (base[:, None] * 0.02) + 0.01 * rng.standard_normal((n, T)); rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool)
    close = np.exp(np.nancumsum(rlog, 1)) * 50.0
    dP = np.diff(close, axis=1, prepend=np.nan)
    roll = np.zeros((n, T), dtype=bool); roll[:, 200] = True
    g = dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=live.copy(), nonpositive=[])
    C = np.tile(base[:, None], (1, T)); C[:, ::7] = np.nan
    cm = R56.carry_at_month_ends(C, live, me)
    # [1] the two membership paths agree; 12 eligible -> 4/4/4; ranks follow the carries
    m_a, diag = membership_at_month_ends(cm, roots); m_b = membership_pandas(cm, roots)
    assert np.array_equal(m_a, m_b)
    assert all(d["n_long"] == 4 and d["n_short"] == 4 and d["n_eligible"] == 12 for d in diag)
    assert (m_a[:4] == 1).all() and (m_a[4:8] == 0).all() and (m_a[8:] == -1).all()
    # a boundary tie: roots 3 and 4 share a carry at month-end 3 -> the earlier SYMBOL takes the long leg
    cm2 = cm.copy(); cm2[3, 3] = cm2[4, 3]
    t_a, d2 = membership_at_month_ends(cm2, roots); t_b = membership_pandas(cm2, roots)
    early, late = (3, 4) if roots[3] < roots[4] else (4, 3)
    assert np.array_equal(t_a, t_b) and d2[3]["tie_at_boundary"] and t_a[early, 3] == 1 and t_a[late, 3] == 0
    # ineligibility: three roots without carry at month-end 5 -> 9 eligible -> 3/3/3; four -> 8 -> flat
    cm3 = cm.copy(); cm3[[0, 5, 11], 5] = np.nan
    i_a, d3 = membership_at_month_ends(cm3, roots); i_b = membership_pandas(cm3, roots)
    assert np.array_equal(i_a, i_b) and d3[5]["n_eligible"] == 9 and d3[5]["n_long"] == 3 and (i_a[:, 5] != 0).sum() == 6 and i_a[0, 5] == 0
    assert d3[5]["missing"] == [roots[0], roots[5], roots[11]]
    cm4 = cm3.copy(); cm4[6, 5] = np.nan
    f_a, d4 = membership_at_month_ends(cm4, roots)
    assert d4[5]["flat"] and (f_a[:, 5] == 0).all() and np.array_equal(f_a, membership_pandas(cm4, roots))
    print("  [1] membership: numpy and pandas paths agree; 12 eligible -> 4/4/4 in carry order; a boundary tie goes to the earlier symbol; "
          "a root without carry is excluded (9 eligible -> 3/3/3); 8 eligible -> flat month")
    # [2] the leg-membership audit passes and RAISES on one swapped long/short pair
    audit_leg_membership(m_a, m_b, me, days)
    raised = False
    try:
        audit_leg_membership(swap_one_pair(m_a), m_b, me, days)
    except AssertionError:
        raised = True
    assert raised, "leg audit accepted a swapped pair"
    print("  [2] leg-membership audit passes and RAISES on one long/short pair swapped at one month-end")
    # [3] lag audit
    sig = R55.ew_vol(rlog, live)
    sh, pos_vol, sc_vol, sd = R56.positions_from_signs(m_a.astype(float), sig, me, g)
    sc_ew = R55.hold_from_month_ends(np.ones((n, K)), me, T, g["span"]); pos_ew = sh * sc_ew
    assert np.array_equal(pos_ew, sh)
    R55.audit_lag(sh, m_b.astype(float), me, g["span"], T)
    unl = np.zeros_like(sh)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = m_a[:, k][:, None]
    raised = False
    try:
        R55.audit_lag(unl, m_b.astype(float), me, g["span"], T)
    except AssertionError:
        raised = True
    assert raised, "lag audit accepted an UNLAGGED grid"
    print("  [3] lag audit passes the held membership and RAISES on the unlagged grid")
    # [4] right quantity
    R55.audit_right_quantity(sh, me, T)
    raised = False
    try:
        R55.audit_right_quantity(np.sign(np.nan_to_num(C + 0.001 * rng.standard_normal((n, T)))), me, T)
    except AssertionError:
        raised = True
    assert raised, "right-quantity audit accepted a daily grid"
    print("  [4] right-quantity audit passes the monthly grid and RAISES on a daily one")
    # [5] sign in money on the dollar book
    upp = np.full(n, 10.0); tick = np.full(n, 2.5); comm = np.full(n, 6.0)
    sdi = sd.astype(int)
    gross, cost, sides = R55.dollar_book(sdi, g, upp, comm, tick, roots)
    R55.audit_sign_in_money(gross, sdi, g, upp); R55.audit_sign_book(gross, sdi, g, upp)
    for label, bad in (("NEGATED", -gross), ("MIS-LAGGED", R55.dollar_book(sdi, dict(g, dP=np.roll(dP, 1, axis=1)), upp, comm, tick, roots)[0])):
        raised = False
        try:
            R55.audit_sign_in_money(bad, sdi, g, upp)
        except AssertionError:
            raised = True
        assert raised, f"sign audit accepted a {label} grid"
    assert sdi[0, 200] != 0 and sides[0, 200] >= 2, "a roll while positioned must charge two sides"
    print("  [5] sign audit in money passes the dollar book and RAISES on a negated and on a mis-lagged gross grid; a roll is two sides")
    # [6] the strip audit on the carry SIGN at the month-ends, and its negation
    signA = np.where(np.isfinite(cm), np.sign(cm), 0.0)
    rows = []; front = {}
    for t, d in enumerate(days):
        for i, r in enumerate(roots):
            if not np.isfinite(C[i, t]):
                continue
            f, nx = (f"{r}H3", f"{r}M3") if d < "2013-03-01" else (f"{r}Z4", f"{r}H5")
            rows.append((r, f, d, 100.0)); rows.append((r, nx, d, 100.0 / (1 + C[i, t] * 3 / 12))); front[(r, d)] = f
    strip = pd.DataFrame(rows, columns=["root", "contract", "ref", "settle"])
    kchk = R56.audit_carry_from_strip(signA, me, g, strip, front, n_check=30)
    raised = False
    try:
        R56.audit_carry_from_strip(-signA, me, g, strip, front, n_check=10)
    except AssertionError:
        raised = True
    assert raised, "carry audit accepted a negated grid"
    print(f"  [6] strip audit passes {kchk} month-end carry signs and RAISES on a negated sign grid")
    # [7] enumeration path bit-identical to the loop; rotated legs balanced; a correct sort earns
    rsimple = np.where(np.isfinite(rlog), np.expm1(np.nan_to_num(rlog)), 0.0)
    live_idx = [np.flatnonzero(live[i]) for i in range(n)]
    for k in (1, 5, 77, 400):
        s_rot = R55.rotate_signs(sh, live_idx, k)
        p = s_rot * sc_ew
        assert np.array_equal(R55.book_return(p, rsimple), R55.book_return_loop(p, rsimple))
        assert ((s_rot == 1).sum(0) == (s_rot == -1).sum(0)).all(), "rotated legs unbalanced"
    x = R55.book_return(pos_ew, rsimple)
    assert R55.sharpe(x[me[0] + 1:]) > 1.0, "a sort aligned with the drift did not earn"
    assert np.array_equal(R55.rotate_signs(sh, live_idx, T), sh)
    assert np.allclose(pos_ew.sum(0)[me[0] + 1:], 0.0), "the EW book is not dollar-neutral in weight"
    print(f"  [7] enumeration bit-identical to the loop; rotated legs stay balanced; known sort earns SR {R55.sharpe(x[me[0] + 1:]):+.2f}; "
          f"rotation by L is the identity; EW weights sum to zero")
    # [8] root-month table sums to the book; the trimmed statistics exist
    w = np.ones(T, dtype=bool)
    rm = root_month_table(pos_ew, rsimple, days, w)
    assert abs(rm["contrib"].sum() - x.sum()) < 1e-12
    st = dist_stats(rm["contrib"].to_numpy())
    assert all(k in st for k in ("mean_ex_top_1pct", "mean_ex_bottom_1pct", "mean_trim_1pct_both", "payoff"))
    cc = concentration({r: float(v) for r, v in zip(roots, (pos_ew * rsimple).sum(1))})
    assert cc["roots_to_half_pnl"] is not None and cc["top1_share"] > 0
    print("  [8] root-month contributions sum to the book; trimmed means, payoff and concentration computed")
    print("\n  ALL SELF-TESTS PASSED. No fixture was read and no cell was scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); gq = ap.add_mutually_exclusive_group(required=True)
    gq.add_argument("--run", action="store_true"); gq.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (0 if run() else 1))
