"""D561 -- three sharpenings of D555's trend book, evaluated separately (spec 72f0c58, R8).

S1  power   the same 12m book on the declared long window 2011-2023, its rotation null enumerated
S2  sizing  a per-root leverage cap on the published book, CAP in {1, 5, 10, 20}, 10 declared
S3  role    trend as an overlay on three bases: its return on the base's worst days, and the
            drawdown of a vol-matched blend, each against the rotation null of the overlay

Imports D555's and D556's machinery; rebuilds D555's primary and D556's cell A in-process and
asserts each reproduces its committed artifact before anything else is scored.
The 2024+ slice is never read.  Usage:  python scripts/run_d561_trend_sharpenings.py [--selftest]
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

OUT = REPO / "data" / "d561_trend_sharpenings.json"
ART_D555 = REPO / "data" / "d555_tsmom_replication.json"
ART_D556 = REPO / "data" / "d556_carry_timing.json"
SPEC = "72f0c58"

PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
CAPS = [1.0, 5.0, 10.0, 20.0]
DECLARED_CAP = 10.0
BASES = ["ES_long", "60_40", "carry_A"]
OVERLAYS = ["trend_12m", "trend_12m_cap10"]
WORST_Q = {"c5": 0.05, "c10": 0.10}
GUARD_OFFSETS = (1, 7, 63, 250, 999, 1500, 1777, 2000, 2010, 3, 11, 101, 333, 444, 555, 666, 777, 888, 1234, 1999)
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "curve_sha256", "windows",
                    "harness", "audits", "s1_power", "s2_sizing", "s3_role", "component_line", "predictions",
                    "verdict", "timing"]


# --------------------------------------------------------------------------------------------
# S2: the capped book
# --------------------------------------------------------------------------------------------
def capped_positions(s12_me: np.ndarray, sig: np.ndarray, me: np.ndarray, g: dict, cap: float):
    """sign x min(0.40 / sigma, cap) at each month-end, held a month. cap = inf is D555's book."""
    T = g["rlog"].shape[1]
    scale_me = np.where(np.isfinite(sig[:, me]) & (sig[:, me] > 0), R55.VOL_TARGET / sig[:, me], 0.0)
    capped_me = np.minimum(scale_me, cap)
    pos = R55.hold_from_month_ends(s12_me.astype(float) * capped_me, me, T, g["span"])
    scale_held = R55.hold_from_month_ends(capped_me, me, T, g["span"])
    binds_me = (scale_me > cap) & (s12_me != 0)
    return pos, scale_held, binds_me


def capped_positions_loop(s12_me, sig, me, g, cap):
    """Second implementation, pure loop over roots and month-ends; never calls hold_from_month_ends."""
    n, T = g["rlog"].shape
    pos = np.zeros((n, T))
    for i in range(n):
        for k, m_ix in enumerate(me):
            v = sig[i, m_ix]
            sc = R55.VOL_TARGET / v if (np.isfinite(v) and v > 0) else 0.0
            w = float(s12_me[i, k]) * min(sc, cap)
            end = me[k + 1] if k + 1 < len(me) else T - 1
            for t in range(m_ix + 1, end + 1):
                pos[i, t] = w if g["span"][i, t] else 0.0
    return pos


def audit_cap(pos_cap, pos_uncapped, s12_me, sig, me, g, cap):
    """(b) of the pre-registration: the capped grid equals the loop bit for bit, and differs from the
    uncapped grid on exactly the (root, month) cells where 0.40/sigma > cap."""
    ref = capped_positions_loop(s12_me, sig, me, g, cap)
    if not np.array_equal(pos_cap, ref):
        raise AssertionError(f"CAP AUDIT: capped grid != loop implementation at cap {cap}")
    n, T = pos_cap.shape
    scale_me = np.where(np.isfinite(sig[:, me]) & (sig[:, me] > 0), R55.VOL_TARGET / sig[:, me], 0.0)
    expect = (scale_me > cap) & (s12_me != 0)
    got = np.zeros_like(expect)
    for k, m_ix in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else T - 1
        seg = slice(m_ix + 1, end + 1)
        got[:, k] = (pos_cap[:, seg] != pos_uncapped[:, seg]).any(1) & g["span"][:, seg].any(1)
    # a month with no session in span cannot show a difference; compare where the hold is live
    live_month = np.zeros_like(expect)
    for k, m_ix in enumerate(me):
        end = me[k + 1] if k + 1 < len(me) else T - 1
        live_month[:, k] = g["span"][:, m_ix + 1:end + 1].any(1)
    if not np.array_equal(got[live_month], expect[live_month]):
        raise AssertionError(f"CAP AUDIT: the cap binds on cells other than 0.40/sigma > {cap}")
    return int(expect[live_month].sum())


# --------------------------------------------------------------------------------------------
# S3: the overlay statistics
# --------------------------------------------------------------------------------------------
def worst_days(b: np.ndarray, q: float) -> np.ndarray:
    n_q = int(math.floor(q * b.size))
    return np.sort(np.argsort(b, kind="stable")[:n_q])


def worst_days_pandas(b: np.ndarray, q: float) -> np.ndarray:
    n_q = int(math.floor(q * b.size))
    rk = pd.Series(b).rank(method="first")
    return np.flatnonzero((rk <= n_q).to_numpy())


def audit_worst_days(b, q):
    a = worst_days(b, q); p = worst_days_pandas(b, q)
    if not np.array_equal(a, p):
        raise AssertionError("WORST-DAY AUDIT: numpy and pandas day sets differ")
    return int(a.size)


def overlay_stats(b: np.ndarray, x: np.ndarray, idx: dict) -> dict:
    """c_q = mean of x on the base's worst q days / sd(x); DD ratio of the vol-matched blend."""
    sx = float(x.std(ddof=1)); sb = float(b.std(ddof=1))
    out = {}
    for name, ix in idx.items():
        out[name] = float(x[ix].mean() / sx) if sx > 0 else float("nan")
        out[name + "_hit"] = float((x[ix] > 0).mean())
    bs = b / sb; xs = x / sx
    blend = 0.5 * (bs + xs)
    dd_b = R55.max_drawdown(bs); dd_bl = R55.max_drawdown(blend)
    out["dd_ratio"] = float(dd_bl / dd_b) if dd_b < 0 else float("nan")
    out["dd_base_sigma_units"] = float(dd_b); out["dd_blend_sigma_units"] = float(dd_bl)
    return out


def _monthly_sum(x, days_w):
    s = pd.Series(x, index=pd.to_datetime(days_w))
    return s.groupby(s.index.to_period("M")).sum()


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def _pct(col):
    col = col[np.isfinite(col)]
    return {"p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)),
            "p95": float(np.percentile(col, 95)), "sd": float(col.std(ddof=1)), "n": int(col.size)}


def _year_hist(days_w, ix):
    ys = {}
    for i in ix:
        y = days_w[i][:4]; ys[y] = ys.get(y, 0) + 1
    return dict(sorted(ys.items()))


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D561 -- three sharpenings of D555's trend book\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present after filtering")
    live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start)
    roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    me = R55.month_ends(days); sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    upp, tick_usd, comm_rt, size_name = R56.min_size(g, roots)
    dollar_roots = [r for r in roots if r not in R55.DOLLAR_EXCLUDED]
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG)
    dP_days, dL_days = days[wP], days[wL]
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    art555 = json.loads(ART_D555.read_text(encoding="utf-8")); art556 = json.loads(ART_D556.read_text(encoding="utf-8"))

    # ---- harness: rebuild D555's primary and D556's cell A; each must reproduce its artifact ----
    sign_held, pos12, scale_held, sign_dollar = R55.build_positions(g, sig, me, (12,))
    s12_me, _ = R55.signal_at_month_ends(g["rlog"], g["live"], days, me, 12)
    x12 = R55.book_return(pos12, rsimple)
    sh12 = R55.sharpe(x12[wP]); ref12 = art555["primary"]["observed"]
    if abs(sh12 - ref12) > 1e-9:
        raise AssertionError(f"HARNESS: rebuilt D555 primary {sh12:.6f} != artifact {ref12:.6f}")
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    curve = curve[curve["ref"] < RESERVED_FROM]
    C = R56.carry_grid(g, curve); carry_me = R56.carry_at_month_ends(C, g["live"], me)
    signsA = R56.cell_signs(carry_me, s12_me, None)["A"]
    _, posA, _, _ = R56.positions_from_signs(signsA, sig, me, g)
    xA = R55.book_return(posA, rsimple)
    shA = R55.sharpe(xA[wP]); refA = art556["primary"]["observed"]
    if abs(shA - refA) > 1e-9:
        raise AssertionError(f"HARNESS: rebuilt D556 cell A {shA:.6f} != artifact {refA:.6f}")
    harness = {"d555_primary_rebuilt": sh12, "d555_primary_artifact": ref12, "d556_cellA_rebuilt": shA,
               "d556_cellA_artifact": refA, "tolerance": 1e-9}
    log(f"  harness: D555 primary rebuilt {sh12:+.4f} (artifact {ref12:+.4f}); D556 cell A rebuilt {shA:+.4f} (artifact {refA:+.4f})")

    # ---- audits: D555's three, proven to raise ----
    audits = {}
    s12_pd = R55.signal_pandas(g["rlog"], g["live"], days, roots, me, 12)
    audits["lag_held_cells"] = R55.audit_lag(sign_held, s12_pd.astype(float), me, g["span"], T)
    unl = np.zeros_like(sign_held)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0
        unl[:, lo:m_ix + 1] = s12_me[:, k][:, None]
    unl = np.where(g["span"], unl, 0.0)
    try:
        R55.audit_lag(unl, s12_pd.astype(float), me, g["span"], T); raise RuntimeError("lag audit accepted an UNLAGGED book")
    except AssertionError:
        audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(sign_held, me, T)
    try:
        R55.audit_right_quantity(np.sign(np.nan_to_num(np.cumsum(np.nan_to_num(g["rlog"]), axis=1))), me, T)
        raise RuntimeError("right-quantity audit accepted a daily grid")
    except AssertionError:
        audits["right_quantity_raises_on_daily_grid"] = True
    sd12 = sign_dollar.astype(int)
    gross12, _, _ = R55.dollar_book(sd12, g, upp, comm_rt, tick_usd, roots)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(gross12, sd12, g, upp)
    for label, bad in (("negated", -gross12),
                       ("mislagged", R55.dollar_book(sd12, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, roots)[0])):
        try:
            R55.audit_sign_in_money(bad, sd12, g, upp); raise RuntimeError(f"sign audit accepted a {label} grid")
        except AssertionError:
            audits[f"sign_raises_on_{label}_grid"] = True

    # ============================== S1: power ==============================
    log(f"\n  S1 power: the 12m book on {LONG[0]}..{LONG[1]} ({int(wL.sum())} sessions), null enumerated")
    live_idx_L = [np.flatnonzero(g["span"][i] & wL) for i in range(n)]
    cellL = {("12m", "published"): dict(book="published", sign_held=np.where(wL[None, :], sign_held, 0.0), scale_held=scale_held)}
    for k in GUARD_OFFSETS:
        k = k % (int(wL.sum()) - 1) or 1
        p = R55.rotate_signs(cellL[("12m", "published")]["sign_held"], live_idx_L, k) * scale_held
        if not np.array_equal(R55.book_return(p, rsimple)[wL], R55.book_return_loop(p[:, wL], rsimple[:, wL])):
            raise AssertionError(f"S1 exactness guard failed at offset {k}")
    audits["s1_exactness_guard_offsets"] = len(GUARD_OFFSETS)
    nullL, _, nullL_s = R55.enumerate_null(cellL, g, live_idx_L, wL, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    ksL = np.arange(1, nullL.shape[0] + 1)
    keepL = (ksL >= R55.NULL_PURGE) & (ksL <= int(wL.sum()) - R55.NULL_PURGE)
    obsL = R55.sharpe(x12[wL]); obsL_s = R55.sortino(x12[wL])
    colL = nullL[keepL, 0]; colLs = nullL_s[keepL, 0]
    s1 = {"window": LONG, "sessions": int(wL.sum()), "observed": obsL, "observed_sortino": obsL_s,
          "gross": R55.stats_block(x12[wL], dL_days, "12m/published 2011-2023"),
          "null": dict(_pct(colL), pct_rank=float((colL < obsL).mean()), clears_p95=bool(obsL > np.percentile(colL, 95)),
                       offsets_enumerated=int(nullL.shape[0]), purge_sessions=R55.NULL_PURGE, offsets_after_purge=int(keepL.sum())),
          "null_sortino": dict(_pct(colLs), pct_rank=float((colLs[np.isfinite(colLs)] < obsL_s).mean())),
          "null_unpurged": dict(_pct(nullL[:, 0]), pct_rank=float((nullL[:, 0] < obsL).mean()), max=float(nullL[:, 0].max()),
                                argmax_k=int(ksL[int(nullL[:, 0].argmax())])),
          "primary_window_null_for_comparison": {"sd": art555["null_n1"]["per_cell"]["12m/published"].get("sd"),
                                                 "p95": art555["primary"]["p95"], "p50": art555["primary"]["p50"]},
          "offset_profile": {"k": ksL.tolist(), "sharpe": nullL[:, 0].tolist(), "sortino": nullL_s[:, 0].tolist()}}
    # the primary null's sd is not stored in D555's json; recompute it from the stored profile
    profP = np.array(art555["null_n1"]["offset_profile_primary"]["sharpe"], dtype=float)
    ksP = np.arange(1, profP.size + 1); keepP = (ksP >= R55.NULL_PURGE) & (ksP <= int(wP.sum()) - R55.NULL_PURGE)
    s1["primary_window_null_for_comparison"]["sd"] = float(profP[keepP].std(ddof=1))
    s1["sd_ratio_observed"] = float(s1["null"]["sd"] / s1["primary_window_null_for_comparison"]["sd"])
    s1["sd_ratio_predicted"] = float(math.sqrt(int(wP.sum()) / int(wL.sum())))
    log(f"  S1: observed {obsL:+.3f} / Sortino {obsL_s:+.3f}; N1-L p05 {s1['null']['p05']:+.3f} p50 {s1['null']['p50']:+.3f} "
        f"p95 {s1['null']['p95']:+.3f} sd {s1['null']['sd']:.3f} (primary-window sd {s1['primary_window_null_for_comparison']['sd']:.3f}); "
        f"rank {s1['null']['pct_rank']:.3f}")

    # ============================== S2: sizing ==============================
    log(f"\n  S2 sizing: CAP in {CAPS}, declared {DECLARED_CAP}")
    pos_inf, _, _ = capped_positions(s12_me, sig, me, g, math.inf)
    if not np.array_equal(pos_inf, pos12):
        raise AssertionError("CAP = inf is not bit-identical to D555's book")
    audits["cap_inf_equals_uncapped"] = True
    audits["cap_binding_cells_declared_cap"] = audit_cap(*capped_positions(s12_me, sig, me, g, DECLARED_CAP)[:1], pos12, s12_me, sig, me, g, DECLARED_CAP)
    cellsS2 = {}; posS2 = {}; scaleS2 = {}; bindS2 = {}
    for cap in CAPS:
        p, sc, b = capped_positions(s12_me, sig, me, g, cap)
        posS2[cap] = p; scaleS2[cap] = sc; bindS2[cap] = b
        cellsS2[(f"cap{cap:g}", "published")] = dict(book="published", sign_held=np.where(wP[None, :], sign_held, 0.0), scale_held=sc)
    live_idx_P = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    for k in GUARD_OFFSETS:
        k = k % (int(wP.sum()) - 1) or 1
        p = R55.rotate_signs(cellsS2[(f"cap{DECLARED_CAP:g}", "published")]["sign_held"], live_idx_P, k) * scaleS2[DECLARED_CAP]
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"S2 exactness guard failed at offset {k}")
    audits["s2_exactness_guard_offsets"] = len(GUARD_OFFSETS)
    nullS2, keysS2, nullS2_s = R55.enumerate_null(cellsS2, g, live_idx_P, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    ksP2 = np.arange(1, nullS2.shape[0] + 1); keep2 = (ksP2 >= R55.NULL_PURGE) & (ksP2 <= int(wP.sum()) - R55.NULL_PURGE)

    def score_published(pos, label):
        x = R55.book_return(pos, rsimple); turn, rolls, tw = R55.published_cost(pos, cbp, g["roll"]); xn = x - turn
        cnt = (pos != 0.0).sum(0); contrib = pos * rsimple / np.where(cnt > 0, cnt, 1.0)[None, :]
        tot = {r: float(contrib[i][wP].sum()) for i, r in enumerate(roots)}
        total = sum(tot.values()); ranked = sorted(tot.items(), key=lambda kv: -kv[1])
        share = lambda k: float(sum(v for _, v in ranked[:k]) / total) if total != 0 else float("nan")
        xw = x[wP]; t_min = int(np.argmin(xw)); t_max = int(np.argmax(xw))
        worst_root = roots[int(np.argmin(contrib[:, wP][:, t_min]))]
        per_root = {r: {"total_primary": tot[r], "sharpe_primary": R55.sharpe(contrib[i][wP & (pos[i] != 0)]) if (wP & (pos[i] != 0)).sum() > 60 else None,
                        "sortino_primary": R55.sortino(contrib[i][wP & (pos[i] != 0)]) if (wP & (pos[i] != 0)).sum() > 60 else None}
                    for i, r in enumerate(roots)}
        per_sector = {}
        for sec, lst in R55.SECTOR.items():
            ix = [roots.index(r) for r in lst if r in roots]
            xs = R55.book_return(pos[ix], rsimple[ix])
            per_sector[sec] = {"sharpe_primary": R55.sharpe(xs[wP]), "sortino_primary": R55.sortino(xs[wP]), "total_contrib": float(sum(tot[roots[j]] for j in ix))}
        per_era = {f"{a}..{b}": {"sharpe": R55.sharpe(x[R55.window_mask(days, a, b)]), "sortino": R55.sortino(x[R55.window_mask(days, a, b)])} for a, b in ERAS}
        yrs = sorted(set(d[:4] for d in days[wP]))
        per_year = {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "sortino": R55.sortino(x[np.array([d[:4] == y for d in days])])} for y in yrs}
        return x, xn, {"gross": R55.stats_block(xw, dP_days, label), "net": R55.stats_block(xn[wP], dP_days, label + " net"),
                       "net_incl_rolls": R55.sharpe((x - turn - rolls)[wP]), "net_incl_rolls_sortino": R55.sortino((x - turn - rolls)[wP]),
                       "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                       "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                       "breakeven_bp_per_side": float(xw.mean() / max(tw[wP].mean(), 1e-12) * 1e4),
                       "gross_long": R55.stats_block(x[wL], dL_days, label + " 2011-2023"),
                       "worst_day": {"date": str(dP_days[t_min]), "return": float(xw[t_min]), "largest_loser": worst_root},
                       "best_day": {"date": str(dP_days[t_max]), "return": float(xw[t_max])},
                       "top_share": {"top1": share(1), "top3": share(3), "top5": share(5), "top10": share(10),
                                     "roots_to_half": int(next((k for k in range(1, len(ranked) + 1) if sum(v for _, v in ranked[:k]) >= 0.5 * total), len(ranked))) if total > 0 else None,
                                     "ranked": [(r, v) for r, v in ranked]},
                       "per_root": per_root, "per_sector": per_sector, "per_era": per_era, "per_year": per_year}

    s2 = {"caps": CAPS, "declared_cap": DECLARED_CAP, "cells": {}, "reference_uncapped": {}, "null_n1": {}, "null_n2": {}}
    x_ref, _, s2["reference_uncapped"] = score_published(pos12, "12m/published uncapped (D555)")
    xS2 = {}
    obs2 = []
    for j, cap in enumerate(CAPS):
        name = f"cap{cap:g}"
        x, xn, entry = score_published(posS2[cap], f"12m/published {name}")
        xS2[cap] = x
        b = bindS2[cap]; lm = np.zeros_like(b)
        for k, m_ix in enumerate(me):
            end = me[k + 1] if k + 1 < len(me) else T - 1
            lm[:, k] = g["span"][:, m_ix + 1:end + 1].any(1)
        meP = np.array([wP[min(m + 1, T - 1)] for m in me])
        positioned = (s12_me != 0) & lm & meP[None, :]
        entry["binding"] = {"share_of_positioned_root_months": float((b & positioned).sum() / max(positioned.sum(), 1)),
                            "roots": {r: int((b[i] & positioned[i]).sum()) for i, r in enumerate(roots) if (b[i] & positioned[i]).any()},
                            "months_with_any_bind": int((b & positioned).any(0).sum()), "month_ends_in_window": int(positioned.any(0).sum())}
        col = nullS2[keep2, j]; cols = nullS2_s[keep2, j]; o = entry["gross"]["sharpe"]; obs2.append(o)
        s2["null_n1"][name] = dict(_pct(col), observed=o, pct_rank=float((col < o).mean()), clears_p95=bool(o > np.percentile(col, 95)),
                                  sortino=dict(_pct(cols), observed=entry["gross"]["sortino"]),
                                  unpurged={"p50": float(np.percentile(nullS2[:, j], 50)), "p95": float(np.percentile(nullS2[:, j], 95))})
        s2["cells"][name] = entry
        log(f"  {name:6s} gross {o:+.3f} / So {entry['gross']['sortino']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}  "
            f"maxDD {entry['gross']['max_dd']:+.3f}  worst day {entry['worst_day']['return']:+.4f} ({entry['worst_day']['largest_loser']})  "
            f"top3 {entry['top_share']['top3']:.2f}  binds {entry['binding']['share_of_positioned_root_months']:.3f}  "
            f"N1 p50 {s2['null_n1'][name]['p50']:+.3f} p95 {s2['null_n1'][name]['p95']:+.3f} rank {s2['null_n1'][name]['pct_rank']:.3f}")
    fam = nullS2[keep2].max(1); obs2 = np.array(obs2)
    s2["null_n2"] = {"observed_best": float(obs2.max()), "observed_best_cell": f"cap{CAPS[int(obs2.argmax())]:g}",
                     "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)),
                     "pct_rank": float((fam < obs2.max()).mean()), "clears_p95": bool(obs2.max() > np.percentile(fam, 95)),
                     "offsets_after_purge": int(keep2.sum())}
    s2["monotone_in_cap"] = {"sharpes_by_cap": {f"cap{c:g}": s2["cells"][f"cap{c:g}"]["gross"]["sharpe"] for c in CAPS} | {"uncapped": sh12},
                             "holds": bool(all(a < b for a, b in zip(obs2[:-1], obs2[1:])) and obs2[-1] < sh12)}
    ref = s2["reference_uncapped"]
    log(f"  uncapped gross {sh12:+.3f}  worst day {ref['worst_day']['return']:+.4f} ({ref['worst_day']['largest_loser']}, {ref['worst_day']['date']})  "
        f"top3 {ref['top_share']['top3']:.2f}  roots to half {ref['top_share']['roots_to_half']}")
    log(f"  N2 family: best {s2['null_n2']['observed_best']:+.3f} ({s2['null_n2']['observed_best_cell']})  p50 {s2['null_n2']['p50']:+.3f} p95 {s2['null_n2']['p95']:+.3f}")

    # the component line: the dollar book at minimum size, unchanged by a cap; must reproduce D555 section 4
    sP = np.where(wP[None, :], sign_dollar, 0).astype(int)
    grossD, costD, sidesD = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots)
    xgD, xnD = grossD.sum(0), (grossD - costD).sum(0)
    comp = {"note": "one minimum-size contract per root per sign: a leverage cap on the return-space weights does not alter it; "
                    "this is D555 section 4's line re-emitted from the same signs and asserted equal to the artifact",
            "gross": R55.stats_block(xgD[wP], dP_days, "12m/dollar"), "net": R55.stats_block(xnD[wP], dP_days, "12m/dollar net"),
            "cost_total": float(costD.sum(0)[wP].sum()), "sides_total": int(sidesD[:, wP].sum()),
            "C_a_net_sharpe": R55.sharpe(xnD[wP]), "C_c_skew": float(pd.Series(xnD[wP]).skew()), "C_d_sigma_daily_usd": float(xnD[wP].std(ddof=1)),
            "rho_with_ledger_entry": art555["dollar_book"]["rho_with_ledger_entry"], "entered": False}
    refD = art555["cells"]["12m/dollar"]["net"]
    if abs(comp["C_a_net_sharpe"] - refD["sharpe"]) > 1e-9 or abs(comp["C_d_sigma_daily_usd"] - refD["sd_daily"]) > 1e-6:
        raise AssertionError("COMPONENT LINE: the re-emitted dollar book does not reproduce D555's artifact")
    audits["component_line_reproduces_d555"] = True

    # ============================== S3: role ==============================
    log(f"\n  S3 role: overlays {OVERLAYS} on bases {BASES}, 2016-2023")
    iES, iZN = roots.index("ES"), roots.index("ZN")
    bases = {"ES_long": rsimple[iES], "60_40": 0.6 * rsimple[iES] + 0.4 * rsimple[iZN], "carry_A": xA}
    overlays = {"trend_12m": x12, "trend_12m_cap10": xS2[DECLARED_CAP]}
    idx = {}
    for bn, b in bases.items():
        bw = b[wP]
        idx[bn] = {q: worst_days(bw, WORST_Q[q]) for q in WORST_Q}
        for q in WORST_Q:
            audits[f"worst_days_{bn}_{q}_checked"] = audit_worst_days(bw, WORST_Q[q])
    # the audit must raise on a set that is not the worst days
    try:
        a = worst_days(bases["ES_long"][wP], 0.05); p = worst_days_pandas(np.roll(bases["ES_long"][wP], 1), 0.05)
        if np.array_equal(a, p):
            raise RuntimeError("worst-day audit cannot distinguish a shifted base")
        audits["worst_days_audit_can_fail"] = True
    except AssertionError:
        audits["worst_days_audit_can_fail"] = True
    s3 = {"bases": {}, "overlays": {}, "pairs": {}, "null": {}, "worst_day_years": {}}
    for bn, b in bases.items():
        s3["bases"][bn] = R55.stats_block(b[wP], dP_days, bn)
        s3["worst_day_years"][bn] = {q: _year_hist(dP_days, idx[bn][q]) for q in WORST_Q}
    for on, x in overlays.items():
        s3["overlays"][on] = R55.stats_block(x[wP], dP_days, on)
    for on, x in overlays.items():
        for bn, b in bases.items():
            bw, xw = b[wP], x[wP]
            st = overlay_stats(bw, xw, idx[bn])
            blend = 0.5 * (bw / bw.std(ddof=1) + xw / xw.std(ddof=1))
            mb, mx = _monthly_sum(bw, dP_days), _monthly_sum(xw, dP_days)
            st.update({"rho_daily": float(np.corrcoef(bw, xw)[0, 1]), "rho_monthly": float(np.corrcoef(mb.values, mx.values)[0, 1]),
                       "blend_sharpe": R55.sharpe(blend), "blend_sortino": R55.sortino(blend),
                       "base_sharpe": R55.sharpe(bw), "base_sortino": R55.sortino(bw),
                       "overlay_sharpe": R55.sharpe(xw), "overlay_sortino": R55.sortino(xw),
                       "overlay_return_in_base_worst_5_months": [(str(p), float(mx[p])) for p in mb.sort_values().index[:5]]})
            s3["pairs"][f"{on}|{bn}"] = st
    # the overlay null: rotate the overlay's signs (purged), bases fixed
    sign_P = np.where(wP[None, :], sign_held, 0.0)
    nO = int(wP.sum()) - 1
    keys3 = [f"{on}|{bn}" for on in overlays for bn in bases]
    stat_names = ["c5", "c10", "dd_ratio"]
    null3 = {k: {s: np.full(nO, np.nan) for s in stat_names} for k in keys3}
    t0 = time.time()
    for k in range(1, nO + 1):
        s_rot = R55.rotate_signs(sign_P, live_idx_P, k)
        for on in overlays:
            sc = scale_held if on == "trend_12m" else scaleS2[DECLARED_CAP]
            xr = R55.book_return(s_rot * sc, rsimple)[wP]
            for bn, b in bases.items():
                st = overlay_stats(b[wP], xr, idx[bn])
                for s in stat_names:
                    null3[f"{on}|{bn}"][s][k - 1] = st[s]
        if k % 500 == 0:
            log(f"    overlay null offset {k}/{nO}  {time.time() - t0:.0f}s")
    ks3 = np.arange(1, nO + 1); keep3 = (ks3 >= R55.NULL_PURGE) & (ks3 <= int(wP.sum()) - R55.NULL_PURGE)
    for key in keys3:
        s3["null"][key] = {}
        for s in stat_names:
            col = null3[key][s][keep3]; o = s3["pairs"][key][s]
            blk = _pct(col); blk["observed"] = o; blk["pct_rank"] = float((col < o).mean())
            if s == "dd_ratio":
                blk["below_p05"] = bool(o < blk["p05"])
            else:
                blk["clears_p95"] = bool(o > blk["p95"])
            s3["null"][key][s] = blk
    s3["null_meta"] = {"offsets_enumerated": nO, "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keep3.sum()),
                       "monthly_rho_convention": "sums of daily simple returns within the calendar month"}
    for key in keys3:
        p = s3["pairs"][key]; nn = s3["null"][key]
        log(f"  {key:26s} rho {p['rho_daily']:+.2f}  c5 {p['c5']:+.3f} (null p50 {nn['c5']['p50']:+.3f} p95 {nn['c5']['p95']:+.3f}, rank {nn['c5']['pct_rank']:.3f})  "
            f"hit5 {p['c5_hit']:.2f}  DD ratio {p['dd_ratio']:.3f} (null p05 {nn['dd_ratio']['p05']:.3f} p50 {nn['dd_ratio']['p50']:.3f}, rank {nn['dd_ratio']['pct_rank']:.3f})  "
            f"base SR {p['base_sharpe']:+.2f} blend SR {p['blend_sharpe']:+.2f}")

    # ============================== predictions ==============================
    c10 = s2["cells"][f"cap{DECLARED_CAP:g}"]; ref = s2["reference_uncapped"]
    pES = s3["pairs"]["trend_12m|ES_long"]; nES = s3["null"]["trend_12m|ES_long"]
    pCA = s3["pairs"]["trend_12m|carry_A"]; nCA = s3["null"]["trend_12m|carry_A"]
    preds = {
        "S1-P1": {"claim": "sd(N1-L) in [0.38, 0.48]", "value": s1["null"]["sd"], "holds": bool(0.38 <= s1["null"]["sd"] <= 0.48)},
        "S1-P2": {"claim": "N1-L p95 in [0.60, 0.80]; observed inside, rank in [0.80, 0.95]", "p95": s1["null"]["p95"], "rank": s1["null"]["pct_rank"],
                  "holds": bool(0.60 <= s1["null"]["p95"] <= 0.80 and not s1["null"]["clears_p95"] and 0.80 <= s1["null"]["pct_rank"] <= 0.95)},
        "S1-P3": {"claim": "falsifier: observed clears N1-L p95", "fires": bool(s1["null"]["clears_p95"])},
        "S2-P1": {"claim": "cap10 gross Sharpe < +0.304; point 0.10-0.30", "value": c10["gross"]["sharpe"],
                  "holds": bool(c10["gross"]["sharpe"] < sh12), "in_point_range": bool(0.10 <= c10["gross"]["sharpe"] <= 0.30)},
        "S2-P2": {"claim": "cap10 worst day smaller in magnitude than uncapped; kurtosis falls",
                  "worst_cap10": c10["worst_day"]["return"], "worst_uncapped": ref["worst_day"]["return"],
                  "kurt_cap10": c10["gross"]["kurt"], "kurt_uncapped": ref["gross"]["kurt"],
                  "holds": bool(abs(c10["worst_day"]["return"]) < abs(ref["worst_day"]["return"]) and c10["gross"]["kurt"] < ref["gross"]["kurt"])},
        "S2-P3": {"claim": "cap10 top-3 root share < 0.50", "value": c10["top_share"]["top3"], "uncapped": ref["top_share"]["top3"],
                  "holds": bool(c10["top_share"]["top3"] < 0.50)},
        "S2-P4": {"claim": "gross Sharpe rises monotonically with CAP across {1,5,10,20,inf}", "values": s2["monotone_in_cap"]["sharpes_by_cap"],
                  "holds": s2["monotone_in_cap"]["holds"]},
        "S2-P5": {"claim": "no capped cell clears N1 p95; family max does not clear N2",
                  "holds": bool(not any(v["clears_p95"] for v in s2["null_n1"].values()) and not s2["null_n2"]["clears_p95"])},
        "S2-P6": {"claim": "falsifier: cap10 above +0.304", "fires": bool(c10["gross"]["sharpe"] > sh12)},
        "S3-P1": {"claim": "c5 on ES > 0 and above null p95; point 0.15-0.50", "value": pES["c5"], "p95": nES["c5"]["p95"],
                  "holds": bool(pES["c5"] > 0 and nES["c5"]["clears_p95"]), "in_point_range": bool(0.15 <= pES["c5"] <= 0.50)},
        "S3-P2": {"claim": "c5 on carry A > 0; point 0.10-0.40", "value": pCA["c5"], "holds": bool(pCA["c5"] > 0),
                  "in_point_range": bool(0.10 <= pCA["c5"] <= 0.40)},
        "S3-P3": {"claim": "DD ratio on ES below the null's p05", "value": pES["dd_ratio"], "p05": nES["dd_ratio"]["p05"], "holds": nES["dd_ratio"]["below_p05"]},
        "S3-P4": {"claim": "DD ratio on carry A below 1 but not below the null's p05", "value": pCA["dd_ratio"], "p05": nCA["dd_ratio"]["p05"],
                  "holds": bool(pCA["dd_ratio"] < 1.0 and not nCA["dd_ratio"]["below_p05"])},
        "S3-P5": {"claim": "rho(trend, ES) daily in [-0.30, +0.10]", "value": pES["rho_daily"], "holds": bool(-0.30 <= pES["rho_daily"] <= 0.10)},
        "S3-P6": {"claim": "falsifier: c5 on ES inside its null AND DD ratio not below p05 -> diversification, not convexity",
                  "fires": bool(not nES["c5"]["clears_p95"] and not nES["dd_ratio"]["below_p05"])},
    }
    verdict = {"S1": "CLEARS N1-L p95 (not promotable)" if s1["null"]["clears_p95"] else "INSIDE N1-L",
               "S2": "PASS" if (c10["gross"]["sharpe"] > 0 and s2["null_n1"][f"cap{DECLARED_CAP:g}"]["clears_p95"] and s2["null_n2"]["clears_p95"]) else "DOES NOT PASS",
               "S3": "CONVEX beside equities" if (pES["c5"] > 0 and nES["c5"]["clears_p95"]) else "NOT DISTINGUISHED from a random sign book on the base's worst days",
               "harness": "HARNESS OK"}
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else ('FIRES' if v.get('fires') else 'fails')}" for k, v in preds.items()))
    log(f"  VERDICT S1 {verdict['S1']} | S2 {verdict['S2']} | S3 {verdict['S3']}")

    res = {"max_drawdown_convention": {
               "sign": "negative",
               "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak) in simple-return "
                       "units for the published books; in dollars for the component line; in units of daily sigma for S3's "
                       "vol-matched base and blend (dd_ratio is the blend's over the base's, both negative, so below 1 is shorter). "
                       "Not a fraction of a compounded peak (D542).", "record": "D542"},
           "spec": "D561", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "curve_sha256": R55.sha256(R56.CURVE),
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum()),
                       "sessions_long": int(wL.sum())},
           "harness": harness, "audits": audits, "s1_power": s1, "s2_sizing": s2, "s3_role": s3,
           "component_line": comp, "predictions": preds, "verdict": verdict, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(_clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: synthetic bars, no fixture read, no cell scored
# --------------------------------------------------------------------------------------------
def _expect_raise(fn, what):
    try:
        fn()
    except AssertionError:
        return True
    raise AssertionError(f"{what}: did not raise")


def selftest() -> int:
    print("D561 SELF-TEST -- synthetic bars, no fixture read, no cell scored\n")
    rng = np.random.default_rng(3)
    days = pd.bdate_range("2010-06-07", "2014-12-31").strftime("%Y-%m-%d").to_numpy()
    T = len(days); roots = ["UP", "DOWN", "QUIET"]; n = 3
    drift = np.array([+0.0015, -0.0015, 0.0]); vol = np.array([0.01, 0.01, 0.0005])
    rlog = drift[:, None] + vol[:, None] * rng.standard_normal((n, T)); rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool)
    close = np.exp(np.nancumsum(rlog, axis=1)) * 100.0
    dP = np.diff(close, axis=1, prepend=np.nan)
    roll = np.zeros((n, T), dtype=bool); roll[:, 300] = True
    g = dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=live.copy(), nonpositive=[])
    me = R55.month_ends(days); sig = R55.ew_vol(rlog, live)
    rsimple = np.where(np.isfinite(rlog), np.expm1(np.nan_to_num(rlog)), 0.0)
    s12, _ = R55.signal_at_month_ends(rlog, live, days, me, 12)
    sign_held, pos12, scale_held, sign_dollar = R55.build_positions(g, sig, me, (12,))

    # [1] cap = inf reproduces the uncapped book; cap binds only where 0.40/sigma > cap; the loop agrees
    pos_inf, _, _ = capped_positions(s12, sig, me, g, math.inf)
    if not np.array_equal(pos_inf, pos12):
        raise AssertionError("cap=inf != uncapped")
    cap = 10.0
    pos_c, _, binds = capped_positions(s12, sig, me, g, cap)
    n_bind = audit_cap(pos_c, pos12, s12, sig, me, g, cap)
    if n_bind == 0 or not binds[2].any():
        raise AssertionError("the cap never binds on the QUIET root (sigma 0.05% -> 0.40/sigma ~ 800)")
    if binds[0].any():
        raise AssertionError("the cap binds on a 1%-vol root")
    print(f"  [1] cap=inf bit-identical to D555's book; cap=10 binds on {n_bind} QUIET root-months and nowhere else; loop agrees")
    # the cap audit RAISES when the grid is altered off the binding set
    bad = pos_c.copy(); bad[0, me[15] + 3] *= 0.5
    _expect_raise(lambda: audit_cap(bad, pos12, s12, sig, me, g, cap), "cap audit on a perturbed non-binding cell")
    bad2 = pos12.copy()          # the uncapped grid presented as capped: differs nowhere, but expect says QUIET binds
    _expect_raise(lambda: audit_cap(bad2, pos12, s12, sig, me, g, cap), "cap audit on the uncapped grid presented as capped")
    print("  [2] cap audit RAISES on a perturbed non-binding cell and on the uncapped grid presented as capped")

    # [3] worst-day sets: numpy == pandas, ties included; RAISES on a shifted series
    b = rng.standard_normal(1000); b[10:20] = b[10]          # a block of exact ties
    k = audit_worst_days(b, 0.05)
    if k != 50:
        raise AssertionError("worst-day count")
    a = worst_days(b, 0.05); p = worst_days_pandas(np.roll(b, 1), 0.05)
    if np.array_equal(a, p):
        raise AssertionError("worst-day audit cannot fail")
    print("  [3] worst-day sets agree across numpy and pandas on a tie-heavy series, and differ on a shifted one")

    # [4] overlay statistics on known answers: X = -B is perfectly convex (c5 > 0, dd of the blend = 0);
    #     X = +B has c5 < 0 and dd_ratio = 1; X = noise has |c5| small and dd_ratio < 1
    idx = {"c5": worst_days(b, 0.05), "c10": worst_days(b, 0.10)}
    st_neg = overlay_stats(b, -b, idx); st_pos = overlay_stats(b, b, idx); st_noise = overlay_stats(b, rng.standard_normal(1000), idx)
    if not (st_neg["c5"] > 1.0 and st_neg["dd_blend_sigma_units"] == 0.0):
        raise AssertionError("X=-B should be convex with a flat blend")
    if not (st_pos["c5"] < -1.0 and abs(st_pos["dd_ratio"] - 1.0) < 1e-12):
        raise AssertionError("X=+B should mirror the base")
    if not (abs(st_noise["c5"]) < 0.5 and 0.3 < st_noise["dd_ratio"] < 1.0):
        raise AssertionError(f"noise overlay: c5 {st_noise['c5']:.2f} dd_ratio {st_noise['dd_ratio']:.2f}")
    print(f"  [4] overlay stats: X=-B c5 {st_neg['c5']:+.2f} blend DD 0; X=+B c5 {st_pos['c5']:+.2f} ratio 1.000; noise c5 {st_noise['c5']:+.2f} ratio {st_noise['dd_ratio']:.2f}")

    # [5] D555's three audits on the synthetic book, each proven to raise
    s12_pd = R55.signal_pandas(rlog, live, days, roots, me, 12)
    R55.audit_lag(sign_held, s12_pd.astype(float), me, live, T)
    unl = np.zeros_like(sign_held)
    for k_, m_ix in enumerate(me):
        lo = me[k_ - 1] + 1 if k_ > 0 else 0
        unl[:, lo:m_ix + 1] = s12[:, k_][:, None]
    _expect_raise(lambda: R55.audit_lag(unl, s12_pd.astype(float), me, live, T), "lag audit on an unlagged grid")
    R55.audit_right_quantity(sign_held, me, T)
    _expect_raise(lambda: R55.audit_right_quantity(np.sign(np.nan_to_num(np.cumsum(np.nan_to_num(rlog), axis=1))), me, T), "right-quantity on a daily grid")
    upp = np.array([50.0, 50.0, 50.0]); sd = sign_dollar.astype(int)
    gross, _, _ = R55.dollar_book(sd, g, upp, np.full(n, 6.0), np.full(n, 12.5), roots)
    R55.audit_sign_in_money(gross, sd, g, upp)
    _expect_raise(lambda: R55.audit_sign_in_money(-gross, sd, g, upp), "sign audit on a negated grid")
    print("  [5] lag, right-quantity and sign-in-money audits pass the book and RAISE on the unlagged, daily and negated grids")

    # [6] the exactness guard on the capped null against the plain loop
    w = np.ones(T, dtype=bool); live_idx = [np.arange(T) for _ in range(n)]
    for k_ in (1, 7, 63, 250):
        p = R55.rotate_signs(sign_held, live_idx, k_) * scale_held
        if not np.array_equal(R55.book_return(p, rsimple), R55.book_return_loop(p, rsimple)):
            raise AssertionError("exactness guard")
    print("  [6] rotated capped book bit-identical to the plain loop on 4 offsets")
    print("\nSELF-TEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
