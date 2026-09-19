"""D562 -- the forward read of D555's trend book on the reserved slice, 2024-01-02 -> fixture end
(spec 04ea121, R8). THIS RUNNER READS THE 2024+ SLICE, on the principal's instruction of 2026-09-19
("settle the forward slice"), and spends it for the trend line and any assembled book containing it.

One construction, fixed since 5ed655b. Primary: the forward gross Sharpe of the 12m published book
against N1-full (signs rotated within each root's full 2011->2026 span, scored on the forward window,
purged 252 both ends). Diagnostics: the dollar component line, the CAP=10 book, D556's carry A, the
overlay statistics against ES / 60-40 / carry A, the AQR harness out of sample.
Usage:  python scripts/run_d562_trend_forward_read.py [--selftest]
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


R61 = _load("d561", "run_d561_trend_sharpenings.py")   # D561 loads D556 which loads D555: one instance of each
R56 = R61.R56
R55 = R61.R55

OUT = REPO / "data" / "d562_trend_forward_read.json"
SPEC = "04ea121"
FWD_START = "2024-01-02"
OVERRIDE = "2099-01-01"
PRIMARY, LONG = R55.PRIMARY, R55.LONG
DECLARED_CAP = R61.DECLARED_CAP
WORST_Q = R61.WORST_Q
GUARD_OFFSETS = R61.GUARD_OFFSETS
REQUIRED_OUTPUTS = ["max_drawdown_convention", "reserved_slice_read", "spec", "commit", "fixture_sha256", "curve_sha256",
                    "aqr_sha256", "windows", "harness", "audits", "cells", "primary", "null_n1_full", "null_n1_window",
                    "root_months", "overlay", "aqr", "component_line", "predictions", "disposition", "verdict", "timing"]


WEEKEND_SESSION_ROOTS = {"BTC": "2026-05-30"}     # CME weekend crypto sessions appear as weekend-dated BTC rows from this date


def load_fixture_forward():
    """D555's loader without the reserved-slice filter and with ONE amendment, declared in the RESULT:
    from 2026-05-30 the fixture carries weekend-dated BTC rows with up to 22 hourly closes (CME's
    weekend crypto sessions). They are dropped like every other weekend-dated row, so BTC's Monday
    return spans the weekend exactly as every other root's does; D555's guard (a weekend row with more
    than three closes is refused) is kept for every other root and for BTC before that date. The
    in-sample rows must equal D555's loader's, row for row -- asserted in run()."""
    cols = ["root", "day", "contract", "same_front", "h18_o"] + [s + "_c" for s in R55.SEGS]
    df = pd.read_csv(R55.FIX, usecols=cols, encoding="utf-8")
    Cc = df[[s + "_c" for s in R55.SEGS]].to_numpy(dtype=float)
    fin = np.isfinite(Cc); has = fin.any(1)
    last_idx = Cc.shape[1] - 1 - np.argmax(fin[:, ::-1], axis=1)
    n_close = fin.sum(1)
    close = np.where(has, Cc[np.arange(len(Cc)), np.clip(last_idx, 0, None)], np.nan)
    df = df[["root", "day", "contract", "same_front", "h18_o"]].copy()
    df["close"] = close; df["n_close"] = n_close
    df["year"] = df["day"].str[:4].astype(int)
    n_before = len(df)
    df = df[df["close"].notna()].copy()
    n_no_close = int(n_before - len(df))
    wd = pd.to_datetime(df["day"]).dt.dayofweek
    wk = (wd >= 5).to_numpy()
    allowed = np.zeros(len(df), dtype=bool)
    for r, d0 in WEEKEND_SESSION_ROOTS.items():
        allowed |= ((df["root"] == r) & (df["day"] >= d0)).to_numpy()
    worst_other = int(df.loc[wk & ~allowed, "n_close"].max()) if (wk & ~allowed).any() else 0
    if worst_other > 3:
        raise AssertionError(f"a weekend-dated row carries {worst_other} hourly closes outside the declared weekend-session roots")
    n_weekend_sessions = int((wk & allowed & (df["n_close"] > 3)).sum())
    df = df[~wk].drop(columns=["n_close"]).copy()
    df.attrs["rows_dropped_no_close"] = n_no_close
    df.attrs["rows_dropped_weekend_stub"] = int(wk.sum()) - n_weekend_sessions
    df.attrs["rows_dropped_weekend_sessions"] = n_weekend_sessions
    return df


def _year_stats(x, days, w):
    out = {}
    for y in sorted(set(d[:4] for d in days[w])):
        m = w & np.array([d[:4] == y for d in days])
        out[y] = {"sharpe": R55.sharpe(x[m]), "sortino": R55.sortino(x[m]), "total": float(x[m].sum()), "n_days": int(m.sum())}
    return out


def score_published(pos, rsimple, g, cbp, w, w_days, label):
    roots, days = g["roots"], g["days"]
    x = R55.book_return(pos, rsimple); turn, rolls, tw = R55.published_cost(pos, cbp, g["roll"]); xn = x - turn
    cnt = (pos != 0.0).sum(0); contrib = pos * rsimple / np.where(cnt > 0, cnt, 1.0)[None, :]
    tot = {r: float(contrib[i][w].sum()) for i, r in enumerate(roots)}
    total = sum(tot.values()); ranked = sorted(tot.items(), key=lambda kv: -kv[1])
    share = lambda k: float(sum(v for _, v in ranked[:k]) / total) if total != 0 else None
    xw = x[w]; t_min = int(np.argmin(xw)); t_max = int(np.argmax(xw))
    per_root = {r: {"total": tot[r], "sharpe": R55.sharpe(contrib[i][w & (pos[i] != 0)]) if (w & (pos[i] != 0)).sum() > 60 else None,
                    "sortino": R55.sortino(contrib[i][w & (pos[i] != 0)]) if (w & (pos[i] != 0)).sum() > 60 else None,
                    "sessions_positioned": int((w & (pos[i] != 0)).sum())} for i, r in enumerate(roots)}
    per_sector = {}
    for sec, lst in R55.SECTOR.items():
        ix = [roots.index(r) for r in lst if r in roots]
        xs = R55.book_return(pos[ix], rsimple[ix])
        per_sector[sec] = {"sharpe": R55.sharpe(xs[w]), "sortino": R55.sortino(xs[w]), "total_contrib": float(sum(tot[roots[j]] for j in ix))}
    return x, xn, contrib, {
        "gross": R55.stats_block(xw, w_days, label), "net": R55.stats_block(xn[w], w_days, label + " net"),
        "net_incl_rolls": R55.sharpe((x - turn - rolls)[w]), "net_incl_rolls_sortino": R55.sortino((x - turn - rolls)[w]),
        "ann_turnover_weight_units": float(tw[w].sum() / (w.sum() / 252)),
        "cost_ann_bp": float(turn[w].sum() / (w.sum() / 252) * 1e4),
        "breakeven_bp_per_side": float(xw.mean() / max(tw[w].mean(), 1e-12) * 1e4),
        "worst_day": {"date": str(w_days[t_min]), "return": float(xw[t_min]), "largest_loser": roots[int(np.argmin(contrib[:, w][:, t_min]))]},
        "best_day": {"date": str(w_days[t_max]), "return": float(xw[t_max]), "largest_winner": roots[int(np.argmax(contrib[:, w][:, t_max]))]},
        "top_share": {"top1": share(1), "top3": share(3), "top5": share(5), "top10": share(10),
                      "roots_to_half": int(next((k for k in range(1, len(ranked) + 1) if sum(v for _, v in ranked[:k]) >= 0.5 * total), len(ranked))) if total > 0 else None,
                      "n_positive_roots": int(sum(1 for v in tot.values() if v > 0)), "ranked": ranked},
        "per_root": per_root, "per_sector": per_sector, "per_year": _year_stats(x, days, w)}


def root_month_table(contrib, pos, days, w):
    idx = pd.to_datetime(days[w])
    rows = []
    for i in range(contrib.shape[0]):
        c = pd.Series(contrib[i][w], index=idx); p = pd.Series(pos[i][w] != 0, index=idx)
        s = c.groupby(c.index.to_period("M")).sum(); n = p.groupby(p.index.to_period("M")).sum()
        rows.append(s[n > 0])
    v = pd.concat(rows).to_numpy(dtype=float)
    if v.size < 20:
        return {"n": int(v.size)}
    srt = np.sort(v); k = max(1, int(round(0.01 * v.size)))
    return {"n": int(v.size), "mean": float(v.mean()), "median": float(np.median(v)), "win": float((v > 0).mean()),
            "payoff": float(v[v > 0].mean() / -v[v < 0].mean()) if (v < 0).any() and (v > 0).any() else None,
            "skew": float(pd.Series(v).skew()), "kurt": float(pd.Series(v).kurt()),
            "mean_ex_top_1pct": float(srt[:-k].mean()), "mean_ex_bottom_1pct": float(srt[k:].mean()),
            "mean_symmetric_trim_1pct": float(srt[k:-k].mean()),
            "top_1pct_share_of_pnl": float(srt[-k:].sum() / v.sum()) if v.sum() != 0 else None}


def run(log=print):
    t_start = time.time()
    log(f"D562 -- THE FORWARD READ: this runner reads the reserved 2024+ slice, on the principal's instruction of "
        f"2026-09-19 ('settle the forward slice'); spec {SPEC} committed BEFORE this runner (R8).\n"
        f"      D555's loader stops at {R55.RESERVED_FROM}; this runner's own loader reads the whole fixture and must match it in sample.")
    prior_reserved = R55.RESERVED_FROM
    df = load_fixture_forward()
    # the in-sample rows must be exactly what D555's loader (reserved filter in place) produces
    ref = R55.load_fixture().reset_index(drop=True)
    ins = df[df["day"] < prior_reserved].reset_index(drop=True)
    if not (len(ref) == len(ins) and ref[["root", "day", "contract"]].equals(ins[["root", "day", "contract"]])
            and np.array_equal(np.nan_to_num(ref["close"].to_numpy()), np.nan_to_num(ins["close"].to_numpy()))):
        raise AssertionError("HARNESS: the forward loader does not reproduce D555's loader on the in-sample rows")
    rows_dropped = {"no_close": df.attrs["rows_dropped_no_close"], "weekend_stub": df.attrs["rows_dropped_weekend_stub"],
                    "weekend_sessions_btc_from_2026_05_30": df.attrs["rows_dropped_weekend_sessions"]}
    log(f"  loader: in-sample rows identical to D555's ({len(ref)} rows); dropped {rows_dropped}")
    last_day = str(df["day"].max())
    if last_day < "2026-01-01":
        raise AssertionError(f"forward slice absent: fixture ends {last_day}")
    live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start)
    roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    fin_share = (np.isfinite(g["rlog"]) & g["live"]).sum() / max(g["live"].sum(), 1)
    if fin_share < 0.97:
        raise AssertionError(f"only {fin_share:.1%} of live sessions carry a return")
    me = R55.month_ends(days); sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    upp, tick_usd, comm_rt, size_name = R56.min_size(g, roots)
    dollar_roots = [r for r in roots if r not in R55.DOLLAR_EXCLUDED]
    wP = R55.window_mask(days, *PRIMARY); wF = days >= FWD_START; wFull = days >= LONG[0]
    dF_days = days[wF]
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    art555 = json.loads(R61.ART_D555.read_text(encoding="utf-8")); art556 = json.loads(R61.ART_D556.read_text(encoding="utf-8"))
    log(f"  fixture: {n} roots x {T} sessions {days[0]}..{days[-1]}; forward window {dF_days[0]}..{dF_days[-1]} = {int(wF.sum())} sessions, "
        f"{int(((me >= np.flatnonzero(wF)[0])).sum())} month-ends")

    # ---- harness: extending the fixture must not move the past ----
    sign_held, pos12, scale_held, sign_dollar = R55.build_positions(g, sig, me, (12,))
    s12_me, _ = R55.signal_at_month_ends(g["rlog"], g["live"], days, me, 12)
    x12 = R55.book_return(pos12, rsimple)
    sh12 = R55.sharpe(x12[wP]); ref12 = art555["primary"]["observed"]
    if abs(sh12 - ref12) > 1e-9:
        raise AssertionError(f"HARNESS: in-sample primary on the extended fixture {sh12:.6f} != D555 artifact {ref12:.6f}")
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8")
    C = R56.carry_grid(g, curve); carry_me = R56.carry_at_month_ends(C, g["live"], me)
    signsA = R56.cell_signs(carry_me, s12_me, None)["A"]
    _, posA, _, sdA = R56.positions_from_signs(signsA, sig, me, g)
    xA = R55.book_return(posA, rsimple)
    shA = R55.sharpe(xA[wP]); refA = art556["primary"]["observed"]
    if abs(shA - refA) > 1e-9:
        raise AssertionError(f"HARNESS: in-sample carry A on the extended fixture {shA:.6f} != D556 artifact {refA:.6f}")
    harness = {"d555_primary_in_sample_rebuilt": sh12, "d555_primary_artifact": ref12,
               "d556_cellA_in_sample_rebuilt": shA, "d556_cellA_artifact": refA, "tolerance": 1e-9}
    log(f"  harness: in-sample primary {sh12:+.4f} (artifact {ref12:+.4f}); carry A {shA:+.4f} (artifact {refA:+.4f}) -- the past did not move")

    # ---- audits, proven to raise ----
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

    # ---- cells on the forward window ----
    pos10, scale10, _ = R61.capped_positions(s12_me, sig, me, g, DECLARED_CAP)
    cells = {}; series = {}
    for name, pos in (("12m/published", pos12), ("12m/published cap10", pos10), ("carry_A/published", posA)):
        x, xn, contrib, entry = score_published(pos, rsimple, g, cbp, wF, dF_days, name + " forward")
        cells[name] = entry; series[name] = dict(gross=x, net=xn, contrib=contrib, pos=pos)
        log(f"  {name:22s} forward gross {entry['gross']['sharpe']:+.3f} / So {entry['gross']['sortino']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f}  "
            f"maxDD {entry['gross']['max_dd']:+.3f}  total {entry['gross']['total']:+.3f}  worst {entry['worst_day']['date']} {entry['worst_day']['return']:+.4f} ({entry['worst_day']['largest_loser']})  "
            f"top3 {entry['top_share']['top3'] if entry['top_share']['top3'] is not None else float('nan'):.2f}  +roots {entry['top_share']['n_positive_roots']}")
    root_months = root_month_table(series["12m/published"]["contrib"], pos12, days, wF)
    # dollar component line, forward
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wF]; d = d[np.isfinite(d)] * upp[i]
        root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]
    sF = np.where(wF[None, :], sign_dollar, 0).astype(int)
    grossD, costD, sidesD = R55.dollar_book(sF, g, upp, comm_rt, tick_usd, dollar_roots)
    g_cd, c_cd, _ = R55.dollar_book(sF, g, upp, comm_rt, tick_usd, cd_roots)
    xgD, xnD = grossD.sum(0), (grossD - costD).sum(0)
    per_root_usd = {r: float((grossD[i] - costD[i])[wF].sum()) for i, r in enumerate(roots)}
    comp = {"gross": R55.stats_block(xgD[wF], dF_days, "12m/dollar forward"), "net": R55.stats_block(xnD[wF], dF_days, "12m/dollar forward net"),
            "cost_total": float(costD.sum(0)[wF].sum()), "sides_total": int(sidesD[:, wF].sum()),
            "roll_sides_total": int((2 * (g["roll"] & (sF != 0)))[:, wF].sum()),
            "C_a_net_sharpe": R55.sharpe(xnD[wF]), "C_c_skew": float(pd.Series(xnD[wF]).skew()), "C_d_sigma_daily_usd": float(xnD[wF].std(ddof=1)),
            "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wF], dF_days, "C-d subset forward"),
                          "net": R55.stats_block((g_cd - c_cd).sum(0)[wF], dF_days, "C-d subset forward net")},
            "per_root_net_usd": dict(sorted(per_root_usd.items(), key=lambda kv: -kv[1])), "sigma_usd_min_size": root_sigma,
            "rho_with_ledger_entry": art555["dollar_book"]["rho_with_ledger_entry"], "entered": False}
    log(f"  12m/dollar forward: net {comp['C_a_net_sharpe']:+.3f} (gross {comp['gross']['sharpe']:+.3f})  skew {comp['C_c_skew']:+.2f}  sigma ${comp['C_d_sigma_daily_usd']:,.0f}  "
        f"C-d sub-book ({len(cd_roots)} roots) net {comp['cd_subset']['net']['sharpe']:+.3f} sigma ${comp['cd_subset']['net']['sd_daily']:,.0f}")

    # ---- overlay bases and worst-day sets, forward ----
    iES, iZN = roots.index("ES"), roots.index("ZN")
    bases = {"ES_long": rsimple[iES], "60_40": 0.6 * rsimple[iES] + 0.4 * rsimple[iZN], "carry_A": xA}
    overlays = {"trend_12m": x12, "trend_12m_cap10": series["12m/published cap10"]["gross"]}
    idx = {}
    for bn, b in bases.items():
        idx[bn] = {q: R61.worst_days(b[wF], WORST_Q[q]) for q in WORST_Q}
        for q in WORST_Q:
            audits[f"worst_days_{bn}_{q}_checked"] = R61.audit_worst_days(b[wF], WORST_Q[q])
    overlay = {"bases": {bn: R55.stats_block(b[wF], dF_days, bn + " forward") for bn, b in bases.items()},
               "overlays": {on: R55.stats_block(x[wF], dF_days, on + " forward") for on, x in overlays.items()},
               "worst_day_years": {bn: {q: R61._year_hist(dF_days, idx[bn][q]) for q in WORST_Q} for bn in bases},
               "worst_day_dates_ES_c5": [str(dF_days[i]) for i in idx["ES_long"]["c5"]], "pairs": {}, "null": {}}
    for on, x in overlays.items():
        for bn, b in bases.items():
            bw, xw = b[wF], x[wF]
            st = R61.overlay_stats(bw, xw, idx[bn])
            blend = 0.5 * (bw / bw.std(ddof=1) + xw / xw.std(ddof=1))
            mb, mx = R61._monthly_sum(bw, dF_days), R61._monthly_sum(xw, dF_days)
            st.update({"rho_daily": float(np.corrcoef(bw, xw)[0, 1]), "rho_monthly": float(np.corrcoef(mb.values, mx.values)[0, 1]),
                       "blend_sharpe": R55.sharpe(blend), "blend_sortino": R55.sortino(blend), "base_sharpe": R55.sharpe(bw), "base_sortino": R55.sortino(bw),
                       "overlay_sharpe": R55.sharpe(xw), "overlay_sortino": R55.sortino(xw),
                       "overlay_return_in_base_worst_5_months": [(str(p), float(mx[p]), float(mb[p])) for p in mb.sort_values().index[:5]]})
            overlay["pairs"][f"{on}|{bn}"] = st

    # ---- N1-full: rotate within the full span, score on the forward window ----
    live_idx_full = [np.flatnonzero(g["span"][i] & wFull) for i in range(n)]
    sign_full = np.where(wFull[None, :], sign_held, 0.0); sd_full = np.where(wFull[None, :], sign_dollar, 0).astype(int)
    L_full = int(wFull.sum())
    for k in GUARD_OFFSETS:
        k = k % (L_full - 1) or 1
        p = R55.rotate_signs(sign_full, live_idx_full, k) * scale_held
        if not np.array_equal(R55.book_return(p, rsimple)[wF], R55.book_return_loop(p[:, wF], rsimple[:, wF])):
            raise AssertionError(f"N1-full exactness guard failed at offset {k}")
    audits["n1_full_exactness_guard_offsets"] = len(GUARD_OFFSETS)
    # a rotated sign at a forward session t under offset k comes from session t-k (mod the root's span): assert on ES
    k_chk = 300; iE = iES; idxE = live_idx_full[iE]
    rot = R55.rotate_signs(sign_full, live_idx_full, k_chk)
    tF = np.flatnonzero(wF)[10]; posE = int(np.flatnonzero(idxE == tF)[0])
    if rot[iE, tF] != sign_full[iE, idxE[posE - k_chk]]:
        raise AssertionError("rotation semantics: the rotated sign is not the sign from k sessions earlier in the root's span")
    audits["rotation_reads_from_k_sessions_earlier"] = True
    nO = L_full - 1
    keys_pub = ["12m/published", "12m/published cap10"]
    null_sh = {k: np.full(nO, np.nan) for k in keys_pub + ["12m/dollar net"]}
    null_so = {k: np.full(nO, np.nan) for k in keys_pub + ["12m/dollar net"]}
    pair_keys = [f"{on}|{bn}" for on in overlays for bn in bases]
    null_ov = {k: {s: np.full(nO, np.nan) for s in ("c5", "c10", "dd_ratio")} for k in pair_keys}
    t0 = time.time()
    log(f"  N1-full: {nO} offsets over the full span, scored on the forward window ...")
    for k in range(1, nO + 1):
        s_rot = R55.rotate_signs(sign_full, live_idx_full, k)
        xr = {"trend_12m": R55.book_return(s_rot * scale_held, rsimple)[wF], "trend_12m_cap10": R55.book_return(s_rot * scale10, rsimple)[wF]}
        null_sh["12m/published"][k - 1] = R55.sharpe(xr["trend_12m"]); null_so["12m/published"][k - 1] = R55.sortino(xr["trend_12m"])
        null_sh["12m/published cap10"][k - 1] = R55.sharpe(xr["trend_12m_cap10"]); null_so["12m/published cap10"][k - 1] = R55.sortino(xr["trend_12m_cap10"])
        sdr = np.sign(R55.rotate_signs(sd_full.astype(float), live_idx_full, k)).astype(int)
        gr, cr, _ = R55.dollar_book(np.where(wF[None, :], sdr, 0), g, upp, comm_rt, tick_usd, dollar_roots)
        xd = (gr - cr).sum(0)[wF]
        null_sh["12m/dollar net"][k - 1] = R55.sharpe(xd); null_so["12m/dollar net"][k - 1] = R55.sortino(xd)
        for on in overlays:
            for bn, b in bases.items():
                st = R61.overlay_stats(b[wF], xr[on], idx[bn])
                for s in ("c5", "c10", "dd_ratio"):
                    null_ov[f"{on}|{bn}"][s][k - 1] = st[s]
        if k % 1000 == 0:
            log(f"    offset {k}/{nO}  {time.time() - t0:.0f}s")
    ks = np.arange(1, nO + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= L_full - R55.NULL_PURGE)
    obs = {"12m/published": cells["12m/published"]["gross"]["sharpe"], "12m/published cap10": cells["12m/published cap10"]["gross"]["sharpe"],
           "12m/dollar net": comp["C_a_net_sharpe"]}
    obs_so = {"12m/published": cells["12m/published"]["gross"]["sortino"], "12m/published cap10": cells["12m/published cap10"]["gross"]["sortino"],
              "12m/dollar net": comp["net"]["sortino"]}
    n1 = {"offsets_enumerated": nO, "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keep.sum()), "span_rotated": [LONG[0], str(days[-1])],
          "per_cell": {}, "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_sh["12m/published"].tolist(), "sortino": null_so["12m/published"].tolist()}}
    for key in obs:
        col = null_sh[key][keep]; cols = null_so[key][keep]
        n1["per_cell"][key] = dict(R61._pct(col), observed=obs[key], pct_rank=float((col < obs[key]).mean()),
                                   clears_p95=bool(obs[key] > np.percentile(col, 95)), below_p05=bool(obs[key] < np.percentile(col, 5)),
                                   sortino=dict(R61._pct(cols), observed=obs_so[key], pct_rank=float((cols[np.isfinite(cols)] < obs_so[key]).mean())),
                                   unpurged=dict(R61._pct(null_sh[key]), pct_rank=float((null_sh[key] < obs[key]).mean())))
    for key in pair_keys:
        overlay["null"][key] = {}
        for s in ("c5", "c10", "dd_ratio"):
            col = null_ov[key][s][keep]; o = overlay["pairs"][key][s]
            blk = R61._pct(col); blk["observed"] = o; blk["pct_rank"] = float((col < o).mean())
            blk["below_p05" if s == "dd_ratio" else "clears_p95"] = bool(o < blk["p05"]) if s == "dd_ratio" else bool(o > blk["p95"])
            overlay["null"][key][s] = blk
    primary = n1["per_cell"]["12m/published"]
    log(f"  N1-full primary: observed {primary['observed']:+.3f}  p05 {primary['p05']:+.3f}  p50 {primary['p50']:+.3f}  p95 {primary['p95']:+.3f}  sd {primary['sd']:.3f}  rank {primary['pct_rank']:.3f}")
    for key in pair_keys:
        p = overlay["pairs"][key]; nn = overlay["null"][key]
        log(f"  {key:26s} rho {p['rho_daily']:+.2f}  c5 {p['c5']:+.3f} hit {p['c5_hit']:.2f} (null p50 {nn['c5']['p50']:+.3f} p95 {nn['c5']['p95']:+.3f} rank {nn['c5']['pct_rank']:.3f})  "
            f"DD ratio {p['dd_ratio']:.3f} (p05 {nn['dd_ratio']['p05']:.3f} p50 {nn['dd_ratio']['p50']:.3f} rank {nn['dd_ratio']['pct_rank']:.3f})  base SR {p['base_sharpe']:+.2f} blend {p['blend_sharpe']:+.2f}")

    # ---- N1-window (diagnostic): rotate within the forward window itself ----
    live_idx_F = [np.flatnonzero(g["span"][i] & wF) for i in range(n)]
    sign_F = np.where(wF[None, :], sign_held, 0.0); L_F = int(wF.sum())
    colW = np.full(L_F - 1, np.nan); colWs = np.full(L_F - 1, np.nan)
    for k in range(1, L_F):
        xw_ = R55.book_return(R55.rotate_signs(sign_F, live_idx_F, k) * scale_held, rsimple)[wF]
        colW[k - 1] = R55.sharpe(xw_); colWs[k - 1] = R55.sortino(xw_)
    ksW = np.arange(1, L_F); keepW = (ksW >= R55.NULL_PURGE) & (ksW <= L_F - R55.NULL_PURGE)
    o = obs["12m/published"]
    n1w = {"offsets_enumerated": int(L_F - 1), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(keepW.sum())}
    if keepW.sum() >= 20:
        n1w.update(R61._pct(colW[keepW]), observed=o, pct_rank=float((colW[keepW] < o).mean()), clears_p95=bool(o > np.percentile(colW[keepW], 95)),
                   sortino=dict(R61._pct(colWs[keepW]), observed=obs_so["12m/published"]))
    n1w["unpurged"] = dict(R61._pct(colW), pct_rank=float((colW < o).mean()))
    log(f"  N1-window (diagnostic, {n1w['offsets_after_purge']} offsets): p50 {n1w.get('p50', float('nan')):+.3f} p95 {n1w.get('p95', float('nan')):+.3f} rank {n1w.get('pct_rank', float('nan')):.3f}")

    # ---- AQR harness, forward months ----
    aqr = pd.read_excel(R55.AQR, sheet_name="TSMOM Factors", header=None)
    hdr = int(np.flatnonzero(aqr.iloc[:, 1].astype(str) == "TSMOM")[0])
    cols = ["date"] + [str(c) for c in aqr.iloc[hdr, 1:].tolist()]
    aq = aqr.iloc[hdr + 1:, :].copy(); aq.columns = cols
    aq["date"] = pd.to_datetime(aq["date"], errors="coerce"); aq = aq.dropna(subset=["date"]).set_index("date").astype(float)
    aq["ym"] = aq.index.to_period("M"); aq = aq.set_index("ym")
    mine = pd.Series(x12, index=pd.to_datetime(days)); mine_m = (1.0 + mine).groupby(mine.index.to_period("M")).prod() - 1.0
    ov = [p for p in mine_m.index if p >= pd.Period("2024-01", "M") and p in aq.index]
    a = aq.loc[ov, "TSMOM"]; m = mine_m.loc[ov]
    aqr_out = {"file_sha256": R55.sha256(R55.AQR), "months": len(ov), "first": str(ov[0]), "last": str(ov[-1]),
               "corr_forward": float(np.corrcoef(m.values, a.values)[0, 1]),
               "aqr_sharpe_forward": float(a.mean() / a.std(ddof=1) * math.sqrt(12)), "aqr_sortino_forward": R55.sortino(a.to_numpy(dtype=float), ppy=12.0),
               "aqr_total_forward": float(a.sum()),
               "mine_monthly_sharpe_forward": float(m.mean() / m.std(ddof=1) * math.sqrt(12)), "mine_monthly_sortino_forward": R55.sortino(m.to_numpy(dtype=float), ppy=12.0),
               "monthly": [(str(p), float(m[p]), float(a[p])) for p in ov]}
    log(f"  AQR forward: corr {aqr_out['corr_forward']:+.3f} over {len(ov)} months ({ov[0]}..{ov[-1]}); AQR Sharpe {aqr_out['aqr_sharpe_forward']:+.2f}, mine {aqr_out['mine_monthly_sharpe_forward']:+.2f}")

    # ---- predictions and the declared disposition ----
    c12 = cells["12m/published"]; pES = overlay["pairs"]["trend_12m|ES_long"]; nES = overlay["null"]["trend_12m|ES_long"]
    pCA = overlay["pairs"]["trend_12m|carry_A"]; nCA = overlay["null"]["trend_12m|carry_A"]
    shF = c12["gross"]["sharpe"]
    preds = {
        "P-1": {"claim": "forward gross Sharpe > 0; point +0.3; interval [-0.5, +0.9]", "value": shF, "holds": bool(shF > 0), "in_interval": bool(-0.5 <= shF <= 0.9)},
        "P-2": {"claim": "inside N1-full p05..p95", "p05": primary["p05"], "p95": primary["p95"], "holds": bool(not primary["clears_p95"] and not primary["below_p05"])},
        "P-3": {"claim": "Sortino >= Sharpe if Sharpe > 0", "sharpe": shF, "sortino": c12["gross"]["sortino"],
                "holds": bool(c12["gross"]["sortino"] >= shF) if shF > 0 else None},
        "P-4": {"claim": "monthly corr with AQR TSMOM, 2024-01..2026-05, >= 0.5", "value": aqr_out["corr_forward"], "holds": bool(aqr_out["corr_forward"] >= 0.5)},
        "P-5": {"claim": "c5 on ES forward <= 0; point -0.1; interval [-0.6, +0.2]", "value": pES["c5"], "holds": bool(pES["c5"] <= 0), "in_interval": bool(-0.6 <= pES["c5"] <= 0.2),
                "null_p50": nES["c5"]["p50"], "null_rank": nES["c5"]["pct_rank"]},
        "P-6": {"claim": "c5 on carry A forward < 0 and below N1-full's p20", "value": pCA["c5"], "rank": nCA["c5"]["pct_rank"],
                "holds": bool(pCA["c5"] < 0 and nCA["c5"]["pct_rank"] < 0.20)},
        "P-7": {"claim": "dollar book daily sigma > $500 at minimum size", "value": comp["C_d_sigma_daily_usd"], "holds": bool(comp["C_d_sigma_daily_usd"] > R55.C_D_SIGMA)},
        "P-8": {"claim": "falsifiers: below N1-full p05 -> inverted; above p95 -> passes on the forward slice",
                "below_p05": primary["below_p05"], "clears_p95": primary["clears_p95"]},
    }
    if shF > 0 and pES["c5"] > 0:
        disp = {"outcome": "A", "text": "overlay candidate for the personal book only; vehicle fails C-d for prop"}
    elif shF > 0:
        disp = {"outcome": "B", "text": "return-component candidate for the personal book only, not a hedge; sized by vol target"}
    else:
        disp = {"outcome": "C", "text": "the published trend book did not deliver on the forward slice; closure recommended, the principal's word under R15"}
    disp["slice_spent"] = "the 2024+ slice is spent for the trend line, for carry timing (rebuilt here), and for any assembled book containing either"
    verdict = {"forward": ("INVERTED" if primary["below_p05"] else "PASSES ON THE FORWARD SLICE" if primary["clears_p95"] else
                           ("POSITIVE, INSIDE THE NULL" if shF > 0 else "NON-POSITIVE, INSIDE THE NULL")),
               "harness": "HARNESS OK" if aqr_out["corr_forward"] >= 0.5 else "HARNESS SUSPECT", "disposition": disp["outcome"]}
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else ('n/a' if v.get('holds') is None else 'fails')}" for k, v in preds.items() if k != "P-8"))
    log(f"  VERDICT forward {verdict['forward']} | {verdict['harness']} | disposition {disp['outcome']}: {disp['text']}")

    res = {"max_drawdown_convention": {
               "sign": "negative",
               "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak) in simple-return units "
                       "for the published books; in dollars for the component line; in units of daily sigma for the overlay's vol-matched "
                       "base and blend (dd_ratio is blend over base, both negative, below 1 is shorter). Not a fraction of a compounded peak (D542).",
               "record": "D542"},
           "reserved_slice_read": {"record": "D562", "instruction": "the principal, 2026-09-19: 'settle the forward slice'",
                                   "override": f"load_fixture_forward() reads the whole fixture (D555's loader stops at {prior_reserved}); in-sample rows asserted identical",
                                   "rows_dropped": rows_dropped,
                                   "spent_for": ["the trend line (D555 and every variant)", "carry timing (D556 cell A, rebuilt as a base)",
                                                 "any assembled book containing either"]},
           "spec": "D562", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "curve_sha256": R55.sha256(R56.CURVE), "aqr_sha256": aqr_out["file_sha256"],
           "windows": {"in_sample": PRIMARY, "long": LONG, "forward": [FWD_START, str(days[-1])], "sessions_forward": int(wF.sum()),
                       "month_ends_forward": int((me >= np.flatnonzero(wF)[0]).sum()), "sessions_full_span": L_full},
           "harness": harness, "audits": audits, "cells": cells, "primary": primary, "null_n1_full": n1, "null_n1_window": n1w,
           "root_months": root_months, "overlay": overlay, "aqr": aqr_out, "component_line": comp,
           "predictions": preds, "disposition": disp, "verdict": verdict, "timing": {"wall_s": round(time.time() - t_start, 1)}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: synthetic bars, no fixture read, the reserved filter untouched
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D562 SELF-TEST -- synthetic bars, no fixture read, no slice read\n")
    if R55.RESERVED_FROM != "2024-01-01":
        raise AssertionError("the reserved filter must be untouched outside run()")
    rng = np.random.default_rng(5)
    days = pd.bdate_range("2010-06-07", "2016-12-30").strftime("%Y-%m-%d").to_numpy()
    T = len(days); roots = ["UP", "DOWN", "FLAT"]; n = 3
    drift = np.array([+0.0015, -0.0015, 0.0])
    rlog = drift[:, None] + 0.01 * rng.standard_normal((n, T)); rlog[:, 0] = np.nan
    live = np.ones((n, T), dtype=bool); close = np.exp(np.nancumsum(rlog, axis=1)) * 100.0
    dP = np.diff(close, axis=1, prepend=np.nan); roll = np.zeros((n, T), dtype=bool); roll[:, 300] = True
    g = dict(roots=roots, days=days, close=close, rlog=rlog, dP=dP, roll=roll, live=live, span=live.copy(), nonpositive=[])
    me = R55.month_ends(days); sig = R55.ew_vol(rlog, live)
    rsimple = np.where(np.isfinite(rlog), np.expm1(np.nan_to_num(rlog)), 0.0)
    s12, _ = R55.signal_at_month_ends(rlog, live, days, me, 12)
    sign_held, pos12, scale_held, sign_dollar = R55.build_positions(g, sig, me, (12,))
    wF = days >= "2015-01-01"; wFull = days >= "2011-01-03"
    # [1] rotation within the full span scored on a sub-window: exact against the loop, and the semantics hold
    live_idx = [np.flatnonzero(live[i] & wFull) for i in range(n)]
    sign_full = np.where(wFull[None, :], sign_held, 0.0)
    for k in (1, 7, 63, 250, 999):
        p = R55.rotate_signs(sign_full, live_idx, k) * scale_held
        if not np.array_equal(R55.book_return(p, rsimple)[wF], R55.book_return_loop(p[:, wF], rsimple[:, wF])):
            raise AssertionError("exactness guard")
    k = 300; rot = R55.rotate_signs(sign_full, live_idx, k); tF = np.flatnonzero(wF)[5]; pos_t = int(np.flatnonzero(live_idx[0] == tF)[0])
    if rot[0, tF] != sign_full[0, live_idx[0][pos_t - k]]:
        raise AssertionError("rotation semantics")
    print("  [1] full-span rotation scored on the forward window is bit-identical to the loop; the rotated sign at t is the sign from k sessions earlier")
    # [2] the forward-window score of the UNROTATED book equals the plain book restricted to the window
    x_all = R55.book_return(pos12, rsimple); x_win = R55.book_return_loop(pos12[:, wF], rsimple[:, wF])
    if not np.array_equal(x_all[wF], x_win):
        raise AssertionError("window restriction")
    print("  [2] scoring on the forward window equals the plain book restricted to it")
    # [3] D555's audits pass and RAISE
    s12_pd = R55.signal_pandas(rlog, live, days, roots, me, 12)
    R55.audit_lag(sign_held, s12_pd.astype(float), me, live, T)
    unl = np.zeros_like(sign_held)
    for k_, m_ix in enumerate(me):
        lo = me[k_ - 1] + 1 if k_ > 0 else 0
        unl[:, lo:m_ix + 1] = s12[:, k_][:, None]
    R61._expect_raise(lambda: R55.audit_lag(unl, s12_pd.astype(float), me, live, T), "lag audit on an unlagged grid")
    R55.audit_right_quantity(sign_held, me, T)
    R61._expect_raise(lambda: R55.audit_right_quantity(np.sign(np.nan_to_num(np.cumsum(np.nan_to_num(rlog), axis=1))), me, T), "right-quantity on a daily grid")
    upp = np.full(n, 50.0); sd = sign_dollar.astype(int)
    gross, _, _ = R55.dollar_book(sd, g, upp, np.full(n, 6.0), np.full(n, 12.5), roots)
    R55.audit_sign_in_money(gross, sd, g, upp)
    R61._expect_raise(lambda: R55.audit_sign_in_money(-gross, sd, g, upp), "sign audit on a negated grid")
    print("  [3] lag, right-quantity and sign-in-money audits pass the book and RAISE on the unlagged, daily and negated grids")
    # [4] the root-month table and the year split on the synthetic forward window
    cnt = (pos12 != 0.0).sum(0); contrib = pos12 * rsimple / np.where(cnt > 0, cnt, 1.0)[None, :]
    rm = root_month_table(contrib, pos12, days, wF)
    if rm["n"] != 3 * 24 or not (rm["mean_ex_top_1pct"] < rm["mean"] < rm["mean_ex_bottom_1pct"]):
        raise AssertionError(f"root-month table: {rm}")
    ys = _year_stats(R55.book_return(pos12, rsimple), days, wF)
    if set(ys) != {"2015", "2016"}:
        raise AssertionError("year split")
    print(f"  [4] root-month table: {rm['n']} root-months, trims ordered; year split {sorted(ys)}")
    # [5] worst-day audit RAISES on a shifted base
    b = rng.standard_normal(500); a = R61.worst_days(b, 0.05); p = R61.worst_days_pandas(np.roll(b, 1), 0.05)
    if np.array_equal(a, p):
        raise AssertionError("worst-day audit cannot fail")
    R61.audit_worst_days(b, 0.05)
    print("  [5] worst-day sets agree across numpy and pandas and differ on a shifted base")
    print("\nSELF-TEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
