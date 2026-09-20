"""D573 -- HEDGING PRESSURE as published (Basu & Miffre 2013) on the 16 commodity roots with a CFTC series
(spec 563eafa, R8).

Signal at each month-end: the mean of hedgers' hedging pressure, commercial long / (long + short) from the
legacy futures-only report, over the last 13 reports whose RELEASE date (the Friday of the report's week) is
<= the month-end session. Rank ascending, long the lowest ceil(n/3) (hedgers most net short), short the
highest, middle flat; ties by symbol; monthly holds. Four cells: EW/published (PRIMARY), vol-scaled/published,
dollar at minimum size (net), and the DE-MEANED secondary (13-report mean less the 52-report mean). Nulls: N1
D555's purged enumerated time rotation; N3 name randomisation (2,000 draws, p95 bootstrap SE); N2 the family
maximum. PASS needs the primary above N1 AND N3; above N1 and not N3 is recorded as TILT. 2024+ never read.

    python scripts/run_d573_hedging_pressure.py --selftest
    python scripts/run_d573_hedging_pressure.py --run
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


R64 = _load("d564", "run_d564_basis_momentum.py")     # one instance each of D561 / D557 / D556 / D555
R61, R57, R56, R55 = R64.R61, R64.R57, R64.R56, R64.R55

OUT = REPO / "data" / "d573_hedging_pressure.json"
COT = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
ART_D557 = REPO / "data" / "d557_xs_term_structure.json"
SPEC = "563eafa"
PRIMARY, LONG, RESERVED_FROM, ERAS = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM, R55.ERAS
CM16 = [r for r in R55.SECTOR["CM"] if r != "BZ"]        # BZ has no CFTC series
N_REPORTS, MIN_PRESENT = 13, 10                          # Basu & Miffre's R = 13 weeks
N_LONG_REPORTS, MIN_PRESENT_LONG = 52, 40                # the de-meaning window
PRIMARY_CELL = ("ew", "published")
CELL_NAMES = {("ew", "published"): "ew/published", ("vol", "published"): "volscaled/published",
              ("dollar", "dollar"): "sort/dollar", ("dm", "published"): "demeaned/published"}
POINT_RANGE = (0.2, 0.5)
N3_DRAWS, N3_SEED = 2000, 20260920
METALS, HIGH_HP = ["PL", "GC", "PA", "SI"], ["NG", "ZW"]
TIME_HARD_S = 900.0
REQUIRED_OUTPUTS = ["max_drawdown_convention", "spec", "commit", "fixture_sha256", "curve_sha256", "cot_sha256", "windows", "universe",
                    "signal", "eligibility", "cells", "primary", "null_n1", "null_n2", "null_n3", "root_months", "concentration", "per_root",
                    "tilt", "per_era", "per_year", "comparability", "dollar_book", "component_line", "predictions", "verdict", "audits", "timing"]


# --------------------------------------------------------------------------------------------
# the signal, from the COT fixture, keyed on the RELEASE date
# --------------------------------------------------------------------------------------------
def load_cot(roots):
    cot = pd.read_csv(COT, encoding="utf-8", dtype={"code": str, "release_date_nominal": str, "report_date": str})
    cot = cot[(cot["family"] == "legacy") & (cot["category"] == "commercial") & cot["symbol"].isin(roots)].copy()
    cot = cot[cot["release_date_nominal"].notna() & (cot["release_date_nominal"] < RESERVED_FROM) & (cot["report_date"] < RESERVED_FROM)]
    cot["hp"] = cot["long"] / (cot["long"] + cot["short"])
    return cot.sort_values(["symbol", "release_date_nominal"]).reset_index(drop=True)


def hp_at_month_ends(cot, roots, me_days, n_reports, min_present, key="release_date_nominal"):
    """A. Per root, the mean HP over the last n_reports reports whose `key` date <= the month-end session; NaN if
    fewer than min_present are present."""
    n, K = len(roots), len(me_days); out = np.full((n, K), np.nan)
    for i, r in enumerate(roots):
        s = cot[cot["symbol"] == r].sort_values(key)
        dates = s[key].to_numpy(); vals = s["hp"].to_numpy()
        for k, d in enumerate(me_days):
            j = int(np.searchsorted(dates, d, side="right"))
            w = vals[max(0, j - n_reports):j]
            if w.size >= min_present:
                out[i, k] = float(w.mean())
    return out


def hp_cells_pandas(cot, roots, me_days, cells, n_reports, min_present, key="release_date_nominal"):
    """B, for the audit: at given (root, month-end) cells, a boolean-mask pandas route on the raw rows."""
    out = []
    for i, k in cells:
        d = me_days[k]
        s = cot[(cot["symbol"] == roots[i]) & (cot[key] <= d)].sort_values(key).tail(n_reports)
        out.append(float(s["hp"].mean()) if len(s) >= min_present else np.nan)
    return np.array(out)


def audit_signal_second_path(sig_me, cells, values_b, label="release"):
    a = np.array([sig_me[i, k] for i, k in cells])
    bad = np.flatnonzero(~(np.isclose(a, values_b, rtol=0, atol=1e-12) | (np.isnan(a) & np.isnan(values_b))))
    if bad.size:
        raise AssertionError(f"SIGNAL AUDIT ({label}): the two paths differ at {bad.size} of {len(cells)} cells (first cell {cells[bad[0]]})")
    return len(cells)


# --------------------------------------------------------------------------------------------
# N3: name randomisation with the leg counts kept
# --------------------------------------------------------------------------------------------
def n3_draw(member, elig, rng):
    mr = np.zeros_like(member)
    for k in range(member.shape[1]):
        nl = int((member[:, k] == 1).sum()); ns = int((member[:, k] == -1).sum())
        if nl + ns == 0:
            continue
        el = np.flatnonzero(elig[:, k]); pick = rng.choice(el, size=nl + ns, replace=False)
        mr[pick[:nl], k] = 1; mr[pick[nl:], k] = -1
    return mr


def audit_draw_leg_counts(member, draw, elig):
    """(f) A draw keeps every month-end's leg sizes and stays inside the eligible set."""
    if not ((draw == 1).sum(0) == (member == 1).sum(0)).all() or not ((draw == -1).sum(0) == (member == -1).sum(0)).all():
        raise AssertionError("N3 AUDIT: a draw changed a leg size")
    if ((draw != 0) & ~elig).any():
        raise AssertionError("N3 AUDIT: a draw positioned an ineligible root")
    return int((draw != 0).sum())


def name_randomised_null(member, elig, me, T, span, rsimple, w, n_draws, seed, audit_first=5):
    rng = np.random.default_rng(seed); out = np.full(n_draws, np.nan); out_s = np.full(n_draws, np.nan)
    for d in range(n_draws):
        mr = n3_draw(member, elig, rng)
        if d < audit_first:
            audit_draw_leg_counts(member, mr, elig)
        held = R55.hold_from_month_ends(mr.astype(float), me, T, span)
        x = R55.book_return(held, rsimple)[w]; out[d] = R55.sharpe(x); out_s[d] = R55.sortino(x)
    return out, out_s


def null_block_n3(obs, draws, draws_s, obs_s):
    p95 = float(np.percentile(draws, 95)); se = R64._p95_boot_se(draws)
    return {"observed": obs, "draws": int(draws.size), "p05": float(np.percentile(draws, 5)), "p50": float(np.percentile(draws, 50)), "p95": p95, "p95_boot_se": se,
            "pct_rank": float((draws < obs).mean()), "clears_p95": bool(obs > p95), "margin_over_p95": obs - p95, "margin_in_se": (obs - p95) / se if se > 0 else None,
            "unresolved": bool(abs(obs - p95) <= 2 * se), "sortino": {"observed": obs_s, "p50": float(np.percentile(draws_s, 50)), "p95": float(np.percentile(draws_s, 95))}}


# --------------------------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------------------------
def run(log=print):
    t_start = time.time()
    log(f"D573 -- hedging pressure as published (Basu & Miffre 2013), {len(CM16)} commodity roots\n      spec {SPEC} committed BEFORE this runner (R8)\n"
        f"      primary {PRIMARY[0]}..{PRIMARY[1]}; long {LONG[0]}..{LONG[1]}; 2024+ NOT READ on any source")
    gates = {}
    for p in (R56.CURVE,):
        meta = json.loads(p.with_suffix("").with_suffix(".meta.json").read_text(encoding="utf-8")); gates[p.name] = bool(meta.get("all_gates_pass"))
        if not gates[p.name]:
            raise AssertionError(f"{p.name}: gates have not passed")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); g_all = R55.build_grids(df, live_start)
    g, _ = R57.sub_grid(g_all, CM16)
    roots, days = g["roots"], g["days"]; n, T = g["rlog"].shape
    me = R55.month_ends(days); me_days = days[me]; sig = R55.ew_vol(g["rlog"], g["live"])
    rsimple = np.where(np.isfinite(g["rlog"]), np.expm1(np.nan_to_num(g["rlog"])), 0.0)
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG); dP_days, dL_days = days[wP], days[wL]
    if not all(int((g["span"][i] & wP).sum()) == int(wP.sum()) for i in range(n)):
        raise AssertionError("the 16 roots do not share one span on the primary window")
    cot = load_cot(roots)
    if (cot["release_date_nominal"] >= RESERVED_FROM).any():
        raise AssertionError("a reserved COT release survived the filter")
    last_read = {"breadth": str(days[-1]), "cot_release": str(cot["release_date_nominal"].max()), "cot_report": str(cot["report_date"].max())}
    log(f"  fixture: {n} roots x {T} sessions; COT legacy commercial rows {len(cot)} on {cot['symbol'].nunique()} roots, last release read {last_read['cot_release']}")

    # ---- the signal, both windows, and the de-meaned signal
    hp13 = hp_at_month_ends(cot, roots, me_days, N_REPORTS, MIN_PRESENT)
    hp52 = hp_at_month_ends(cot, roots, me_days, N_LONG_REPORTS, MIN_PRESENT_LONG)
    dm = hp13 - hp52
    kP = R55.window_mask(me_days, *PRIMARY); kL = R55.window_mask(me_days, *LONG)
    signal = {"definition": "mean over the last 13 reports (release <= month-end) of commercial long / (long + short); de-meaned = minus the 52-report mean",
              "roots": roots, "mean_hp13_by_root_primary": {r: float(np.nanmean(hp13[i][kP])) for i, r in enumerate(roots)},
              "month_ends_with_all_13_primary": int(np.isfinite(hp13[:, kP]).all(0).sum()), "month_ends_primary": int(kP.sum())}
    # membership: rank DESCENDING on -HP == ascending on HP; long the lowest HP (D557's sort with the sign flipped, declared)
    member, diag = R57.membership_at_month_ends(-hp13, roots); member_pd = R57.membership_pandas(-hp13, roots)
    member_dm, diag_dm = R57.membership_at_month_ends(-dm, roots); member_dm_pd = R57.membership_pandas(-dm, roots)
    for k in range(len(me)):
        diag[k]["month_end"] = str(me_days[k]); diag_dm[k]["month_end"] = str(me_days[k])
    upp, tick_usd, comm_rt, size_name = R56.min_size(g, roots); dollar_roots = list(roots)

    # ---- audits, each proven to raise on its deliberate break
    audits = {}
    rng = np.random.default_rng(573)
    fin_cells = [(i, k) for i in range(n) for k in range(len(me)) if kL[k]]
    cells_chk = [fin_cells[j] for j in rng.choice(len(fin_cells), size=300, replace=False)]
    vb = hp_cells_pandas(cot, roots, me_days, cells_chk, N_REPORTS, MIN_PRESENT)
    audits["signal_cells_checked"] = audit_signal_second_path(hp13, cells_chk, vb)
    vb_report = hp_cells_pandas(cot, roots, me_days, cells_chk, N_REPORTS, MIN_PRESENT, key="report_date")
    audits["signal_cells_where_report_keying_differs"] = int((~np.isclose(vb, vb_report, rtol=0, atol=1e-12)).sum())
    R61._expect_raise(lambda: audit_signal_second_path(hp13, cells_chk, vb_report, "report-keyed"), "signal audit on report-date keying"); audits["signal_raises_on_report_date_keying"] = True
    audits["leg_membership_cells"] = R57.audit_leg_membership(member, member_pd, me, days)
    R61._expect_raise(lambda: R57.audit_leg_membership(R57.swap_one_pair(member), member_pd, me, days), "leg audit on a swapped pair"); audits["leg_membership_raises_on_swapped_pair"] = True
    audits["leg_membership_cells_demeaned"] = R57.audit_leg_membership(member_dm, member_dm_pd, me, days)
    sh = R55.hold_from_month_ends(member.astype(float), me, T, g["span"])
    _, pos_vol, sc_vol, sd = R56.positions_from_signs(member.astype(float), sig, me, g)
    if not np.array_equal(sd.astype(float), sh):
        raise AssertionError("held signs differ between the two hold paths")
    sc_ew = R55.hold_from_month_ends(np.ones((n, len(me))), me, T, g["span"]); pos_ew = sh * sc_ew
    sh_dm = R55.hold_from_month_ends(member_dm.astype(float), me, T, g["span"]); pos_dm = sh_dm * sc_ew
    audits["lag_held_cells"] = R55.audit_lag(sh, member_pd.astype(float), me, g["span"], T)
    unl = np.zeros_like(sh)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0; unl[:, lo:m_ix + 1] = member[:, k][:, None]
    unl = np.where(g["span"], unl, 0.0)
    R61._expect_raise(lambda: R55.audit_lag(unl, member_pd.astype(float), me, g["span"], T), "lag audit on an unlagged book"); audits["lag_raises_on_unlagged_book"] = True
    audits["right_quantity_changes"] = R55.audit_right_quantity(sh, me, T)
    R61._expect_raise(lambda: R55.audit_right_quantity(np.sign(rsimple), me, T), "right-quantity on a daily grid"); audits["right_quantity_raises_on_daily_grid"] = True
    sdi = sd.astype(int); gross_a, _, _ = R55.dollar_book(sdi, g, upp, comm_rt, tick_usd, roots)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(gross_a, sdi, g, upp)
    R61._expect_raise(lambda: R55.audit_sign_in_money(-gross_a, sdi, g, upp), "sign audit on a negated grid"); audits["sign_raises_on_negated_grid"] = True
    R61._expect_raise(lambda: R55.audit_sign_in_money(R55.dollar_book(sdi, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, roots)[0], sdi, g, upp), "sign audit on a mislagged grid")
    audits["sign_raises_on_mislagged_grid"] = True
    elig = np.isfinite(hp13); rng3 = np.random.default_rng(1)
    audits["n3_draw_cells_checked"] = audit_draw_leg_counts(member, n3_draw(member, elig, rng3), elig)
    bad_draw = n3_draw(member, elig, rng3); k0 = int(np.flatnonzero((member == 1).sum(0) > 0)[0]); free = np.flatnonzero((bad_draw[:, k0] == 0) & elig[:, k0]); bad_draw[free[0], k0] = 1
    R61._expect_raise(lambda: audit_draw_leg_counts(member, bad_draw, elig), "N3 audit on a draw with an extra long"); audits["n3_raises_on_extra_long"] = True
    x_lag = R55.book_return(pos_ew, rsimple); x_unl = R55.book_return(unl * sc_ew, rsimple)
    if np.allclose(x_lag, x_unl):
        raise AssertionError("lagged and unlagged P&L coincide")
    log(f"  audits: {audits}")

    # ---- eligibility
    def _elig(dg, mask):
        d = [dg[k] for k in range(len(me)) if mask[k]]
        return {"month_ends": len(d), "n_eligible_counts": {str(u): int(c) for u, c in zip(*np.unique([r["n_eligible"] for r in d], return_counts=True))},
                "boundary_ties": int(sum(r["tie_at_boundary"] for r in d)), "flat_months": int(sum(r["flat"] for r in d)),
                "leg_sizes": {str(u): int(c) for u, c in zip(*np.unique([r["n_long"] for r in d], return_counts=True))}}
    eligibility = {"primary": _elig(diag, kP), "long": _elig(diag, kL), "demeaned_primary": _elig(diag_dm, kP), "per_month_end": diag}
    log(f"  eligibility (primary): {eligibility['primary']}; de-meaned: {eligibility['demeaned_primary']['n_eligible_counts']}")

    # ---- cells
    cells = {("ew", "published"): dict(book="published", sign_held=sh, scale_held=sc_ew, pos=pos_ew),
             ("vol", "published"): dict(book="published", sign_held=sh, scale_held=sc_vol, pos=pos_vol),
             ("dollar", "dollar"): dict(book="dollar", sign_held=sd.astype(float), scale_held=None, pos=None),
             ("dm", "published"): dict(book="published", sign_held=sh_dm, scale_held=sc_ew, pos=pos_dm)}
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd)
    root_sigma = {}
    for i, r in enumerate(roots):
        d = g["dP"][i][wP]; d = d[np.isfinite(d)] * upp[i]; root_sigma[r] = float(d.std(ddof=1)) if d.size > 30 else float("nan")
    cd_roots = [r for r in dollar_roots if np.isfinite(root_sigma[r]) and root_sigma[r] <= R55.C_D_SIGMA]
    results_cells, scored, dollar_grids = {}, {}, {}
    for key, c in cells.items():
        name = CELL_NAMES[key]
        if c["book"] == "published":
            x = R55.book_return(c["pos"], rsimple); turn, rolls, tw = R55.published_cost(c["pos"], cbp, g["roll"]); xn = x - turn
            entry = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"), "net_incl_rolls": R55.sharpe((x - turn - rolls)[wP]),
                     "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)), "cost_ann_bp": float(turn[wP].sum() / (wP.sum() / 252) * 1e4),
                     "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4), "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"),
                     "positioned_names_mean": float((c["pos"] != 0).sum(0)[wP].mean())}
            scored[key] = dict(gross=x, net=xn)
        else:
            sP = np.where(wP[None, :], c["sign_held"], 0.0).astype(int); sL = np.where(wL[None, :], c["sign_held"], 0.0).astype(int)
            gross, cost, sides = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots); gb, cb = gross.sum(0), cost.sum(0); xg, xn = gb, gb - cb
            g_cd, c_cd, _ = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, cd_roots); gL, _, _ = R55.dollar_book(sL, g, upp, comm_rt, tick_usd, dollar_roots)
            R55.audit_sign_book(gross, sP, g, upp)
            entry = {"gross": R55.stats_block(xg[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"), "cost_total": float(cb[wP].sum()),
                     "sides_total": int(sides[:, wP].sum()), "roll_sides_total": int((2 * (g["roll"] & (sP != 0)))[:, wP].sum()), "traded_names_mean": float((sP != 0)[:, wP].sum(0).mean()),
                     "cd_subset": {"roots": cd_roots, "gross": R55.stats_block(g_cd.sum(0)[wP], dP_days, name + " C-d"), "net": R55.stats_block((g_cd - c_cd).sum(0)[wP], dP_days, name + " C-d net")},
                     "gross_long": R55.stats_block(gL.sum(0)[wL], dL_days, name + " 2011-2023 $")}
            scored[key] = dict(gross=xg, net=xn); dollar_grids = dict(gross=gross, cost=cost)
        results_cells[name] = entry
        log(f"  {name:20s} gross Sh {entry['gross']['sharpe']:+.3f} / So {entry['gross']['sortino']:+.3f} (SE {entry['gross']['se']:.2f})  net {entry['net']['sharpe']:+.3f} / {entry['net']['sortino']:+.3f}; 2011-23 {entry['gross_long']['sharpe']:+.3f}")

    # ---- groups 2 and 3 on the primary; the tilt table
    x = scored[PRIMARY_CELL]["gross"]; pos = pos_ew
    rm = R57.root_month_table(pos, rsimple, days, wP)
    root_months = {"combined": R57.dist_stats(rm["contrib"].to_numpy()), "long_leg": R57.dist_stats(rm.loc[rm["leg"] == 1, "contrib"].to_numpy()),
                   "short_leg": R57.dist_stats(rm.loc[rm["leg"] == -1, "contrib"].to_numpy()), "unit": "book-return units: sign x simple return / positioned count, summed over the month"}
    cnt = (pos != 0).sum(0); contrib = pos * rsimple / np.where(cnt > 0, cnt, 1)[None, :]
    per_root, tilt = {}, {}
    for i, r in enumerate(roots):
        xi = contrib[i]; li = pos[i] != 0
        per_root[r] = {"total_primary": float(xi[wP].sum()), "total_long": float(xi[wL].sum()), "sharpe_primary": R55.sharpe(xi[wP & li]) if (wP & li).sum() > 60 else None,
                       "months_long": int((member[i, kP] == 1).sum()), "months_short": int((member[i, kP] == -1).sum()), "months_flat": int((member[i, kP] == 0).sum()),
                       "mean_hp13": float(np.nanmean(hp13[i][kP])), "min_size": size_name[i], "sigma_usd_min_size": root_sigma[r]}
        tilt[r] = {"share_long": float((member[i, kP] == 1).mean()), "share_short": float((member[i, kP] == -1).mean()), "mean_hp13": per_root[r]["mean_hp13"]}
    conc = R57.concentration({r: per_root[r]["total_primary"] for r in roots}); conc["n_roots_positive"] = int(sum(per_root[r]["total_primary"] > 0 for r in roots))
    per_era = {f"{a}..{b}": {"sharpe": R55.sharpe(x[R55.window_mask(days, a, b)]), "sortino": R55.sortino(x[R55.window_mask(days, a, b)])} for a, b in ERAS}
    per_year = {y: {"sharpe": R55.sharpe(x[np.array([d[:4] == y for d in days])]), "total": float(x[np.array([d[:4] == y for d in days])].sum())} for y in sorted(set(d[:4] for d in days[wL]))}
    log("  tilt (share of primary month-ends long/short): " + " ".join(f"{r}:{v['share_long']:.2f}/{v['share_short']:.2f}" for r, v in sorted(tilt.items(), key=lambda kv: kv[1]['mean_hp13'])))
    log(f"  root-months: long {root_months['long_leg'].get('mean')}, short {root_months['short_leg'].get('mean')}; top1 {conc['top1_share']}, roots to half {conc['roots_to_half_pnl']}")

    # ---- comparability: D557's term-structure sort rebuilt on the 16 roots
    curve = pd.read_csv(R56.CURVE, dtype={"root": str, "ref": str, "front": str, "next": str}, encoding="utf-8"); curve = curve[curve["ref"] < RESERVED_FROM]
    C = R56.carry_grid(g, curve); carry_me = R56.carry_at_month_ends(C, g["live"], me)
    member_ts, _ = R57.membership_at_month_ends(carry_me, roots); x_ts = R55.book_return(R55.hold_from_month_ends(member_ts.astype(float), me, T, g["span"]) * sc_ew, rsimple)
    mon = lambda s: (1 + s).groupby(s.index.to_period("M")).prod() - 1
    xs = pd.Series(x, index=pd.to_datetime(days)); xts = pd.Series(x_ts, index=pd.to_datetime(days))
    same_long = float(((member == 1) & (member_ts == 1))[:, kP].sum() / max((member == 1)[:, kP].sum(), 1)); same_short = float(((member == -1) & (member_ts == -1))[:, kP].sum() / max((member == -1)[:, kP].sum(), 1))
    d557 = json.loads(ART_D557.read_text(encoding="utf-8"))["cells"]["ew/published"]["gross"]["sharpe"] if ART_D557.exists() else None
    comparability = {"term_structure_16_sharpe_2016_2023": R55.sharpe(x_ts[wP]), "term_structure_16_sortino_2016_2023": R55.sortino(x_ts[wP]), "term_structure_16_sharpe_2011_2023": R55.sharpe(x_ts[wL]),
                     "d557_published_primary_17_roots": d557, "rho_daily_2016_2023": float(np.corrcoef(x[wP], x_ts[wP])[0, 1]), "rho_monthly_2016_2023": float(np.corrcoef(mon(xs[wP]).values, mon(xts[wP]).values)[0, 1]),
                     "share_of_long_leg_also_long_in_term_structure": same_long, "share_of_short_leg_also_short_in_term_structure": same_short}
    log(f"  comparability: term-structure sort on 16 Sh {comparability['term_structure_16_sharpe_2016_2023']:+.3f}; rho daily {comparability['rho_daily_2016_2023']:+.3f} monthly {comparability['rho_monthly_2016_2023']:+.3f}; legs shared {same_long:.2f}/{same_short:.2f}")

    # ---- N1 (purged enumeration, 20 offsets timed first), N2
    live_idx = [np.flatnonzero(g["span"][i] & wP) for i in range(n)]
    null_cells = {k: dict(v, sign_held=np.where(wP[None, :], v["sign_held"], 0.0)) for k, v in cells.items()}
    Tw = int(wP.sum()); probe_ks = [k % (Tw - 1) or 1 for k in R61.GUARD_OFFSETS]
    t0 = time.time()
    for k in probe_ks:
        s_rot = R55.rotate_signs(null_cells[PRIMARY_CELL]["sign_held"], live_idx, k); p = s_rot * sc_ew
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"enumeration not bit-identical at offset {k}")
        if not ((s_rot == 1).sum(0)[wP] == (s_rot == -1).sum(0)[wP]).all():
            raise AssertionError(f"rotated legs are not balanced at offset {k}")
        R55.book_return(s_rot * sc_vol, rsimple); R55.book_return(R55.rotate_signs(null_cells[("dm", "published")]["sign_held"], live_idx, k) * sc_ew, rsimple)
        R55.dollar_book(np.sign(R55.rotate_signs(null_cells[("dollar", "dollar")]["sign_held"], live_idx, k)).astype(int), g, upp, comm_rt, tick_usd, dollar_roots)
    per_offset = (time.time() - t0) / len(probe_ks); projected = per_offset * (Tw - 1)
    log(f"  exactness guard: 20 offsets bit-identical, legs balanced; {per_offset * 1e3:.1f} ms/offset -> projected {projected:.0f} s for {Tw - 1} offsets x 4 cells")
    if projected > TIME_HARD_S:
        raise AssertionError(f"projected null wall {projected:.0f} s > {TIME_HARD_S:.0f} s: stopping as declared")
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    names = [CELL_NAMES[k] for k in keys]
    obs = np.array([results_cells[nm]["gross"]["sharpe"] if b == "published" else results_cells[nm]["net"]["sharpe"] for nm, (a, b) in zip(names, keys)])
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= Tw - R55.NULL_PURGE); null = null_all[keep]; jP = keys.index(PRIMARY_CELL)
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(null.shape[0]), "per_cell": {},
          "offset_profile_primary": {"k": ks.tolist(), "sharpe": null_all[:, jP].tolist()}}
    for j, nm in enumerate(names):
        col = null[:, j]
        n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95)),
                              "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95)), "p95_se": 0.0,
                              "sortino": R55.sortino_null_block(scored[keys[j]]["gross" if keys[j][1] == "published" else "net"][wP], null_s[:, j], keep)}
    fam = null.max(1)
    n2 = {"observed_best": float(obs.max()), "observed_best_cell": names[int(obs.argmax())], "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)),
          "pct_rank": float((fam < obs.max()).mean()), "clears_p95": bool(obs.max() > np.percentile(fam, 95))}
    primary = n1["per_cell"][CELL_NAMES[PRIMARY_CELL]]
    log(f"  N1 primary: observed {primary['observed']:+.3f} p05 {primary['p05']:+.3f} p50 {primary['p50']:+.3f} p95 {primary['p95']:+.3f} rank {primary['pct_rank']:.3f}; "
        f"de-meaned rank {n1['per_cell']['demeaned/published']['pct_rank']:.3f}; N2 best {n2['observed_best']:+.3f} ({n2['observed_best_cell']}) p95 {n2['p95']:+.3f} rank {n2['pct_rank']:.3f}")

    # ---- N3: name randomisation, primary and de-meaned
    t0 = time.time()
    d3, d3s = name_randomised_null(member, elig, me, T, g["span"], rsimple, wP, N3_DRAWS, N3_SEED)
    d3dm, d3dms = name_randomised_null(member_dm, np.isfinite(dm), me, T, g["span"], rsimple, wP, N3_DRAWS, N3_SEED + 1)
    cE = results_cells["ew/published"]; cD = results_cells["demeaned/published"]
    n3 = {"draws": N3_DRAWS, "seed": N3_SEED, "primary": null_block_n3(cE["gross"]["sharpe"], d3, d3s, cE["gross"]["sortino"]),
          "demeaned": null_block_n3(cD["gross"]["sharpe"], d3dm, d3dms, cD["gross"]["sortino"]), "wall_s": round(time.time() - t0, 1)}
    log(f"  N3 primary: observed {n3['primary']['observed']:+.3f} p50 {n3['primary']['p50']:+.3f} p95 {n3['primary']['p95']:+.3f} (SE {n3['primary']['p95_boot_se']:.3f}) rank {n3['primary']['pct_rank']:.3f} margin {n3['primary']['margin_in_se']}; "
        f"de-meaned: observed {n3['demeaned']['observed']:+.3f} p95 {n3['demeaned']['p95']:+.3f} rank {n3['demeaned']['pct_rank']:.3f}")

    # ---- the dollar book by root, BEFORE the component line
    dcell = results_cells["sort/dollar"]; net_grid = dollar_grids["gross"] - dollar_grids["cost"]
    per_root_dollar = {r: float(net_grid[i][wP].sum()) for i, r in enumerate(roots)}; dconc = R57.concentration(per_root_dollar); top_r, top_v = dconc["sorted"][0]
    sig_vals = [root_sigma[r] for r in dollar_roots]
    dollar_decomp = {"per_root_net_usd_sorted": dconc["sorted"], "total_net_usd": dconc["total"], "top_contributor": top_r,
                     "top_contributor_share_of_total": (top_v / dconc["total"]) if dconc["total"] != 0 else None, "total_without_top": float(dconc["total"] - top_v),
                     "sigma_usd_per_contract_range": [float(min(sig_vals)), float(max(sig_vals))], "sigma_usd_per_contract": {r: root_sigma[r] for r in dollar_roots}, "cd_roots": cd_roots}
    log("  dollar book by root (net $): " + ", ".join(f"{r} {v:+,.0f}" for r, v in dconc["sorted"]))
    log(f"    total {dconc['total']:+,.0f}; top {top_r} {top_v:+,.0f} = {dollar_decomp['top_contributor_share_of_total']}; sigma/contract ${min(sig_vals):,.0f}..${max(sig_vals):,.0f}; C-d roots {cd_roots}")
    component = {"dollar": {"C_a_net_sharpe": dcell["net"]["sharpe"], "C_a_net_sortino": dcell["net"]["sortino"], "se": dcell["net"]["se"], "gross_sharpe": dcell["gross"]["sharpe"], "hit": dcell["net"]["hit"],
                            "C_c_skew": dcell["net"]["skew"], "C_d_sigma_usd": dcell["net"]["sd_daily"], "total_usd": dcell["net"]["total"],
                            "fails": [c for c, bad in (("C-a", dcell["net"]["sharpe"] <= 0.5), ("C-c", dcell["net"]["skew"] < -0.5), ("C-d", dcell["net"]["sd_daily"] > R55.C_D_SIGMA)) if bad]},
                 "cd_subbook": {"roots": cd_roots, "C_a_net_sharpe": dcell["cd_subset"]["net"]["sharpe"], "C_a_net_sortino": dcell["cd_subset"]["net"]["sortino"], "C_c_skew": dcell["cd_subset"]["net"]["skew"],
                                "C_d_sigma_usd": dcell["cd_subset"]["net"]["sd_daily"], "total_usd": dcell["cd_subset"]["net"]["total"],
                                "fails": [c for c, bad in (("C-a", dcell["cd_subset"]["net"]["sharpe"] <= 0.5), ("C-c", dcell["cd_subset"]["net"]["skew"] < -0.5), ("C-d", dcell["cd_subset"]["net"]["sd_daily"] > R55.C_D_SIGMA)) if bad]},
                 "published_cells_net": {nm: {"net_sharpe": results_cells[nm]["net"]["sharpe"], "net_sortino": results_cells[nm]["net"]["sortino"], "skew": results_cells[nm]["net"]["skew"]} for nm in ("ew/published", "volscaled/published", "demeaned/published")},
                 "rho_with_ledger_entry": "ABSENT: the MACD arm's per-session P&L series is not on disk"}
    log(f"  component: dollar net Sh {component['dollar']['C_a_net_sharpe']:+.3f} So {component['dollar']['C_a_net_sortino']:+.3f} skew {component['dollar']['C_c_skew']:+.2f} sigma ${component['dollar']['C_d_sigma_usd']:,.0f} fails {component['dollar']['fails']}; "
        f"C-d sub-book net {component['cd_subbook']['C_a_net_sharpe']:+.3f} sigma ${component['cd_subbook']['C_d_sigma_usd']:,.0f} fails {component['cd_subbook']['fails']}")

    # ---- predictions and the verdict
    p3 = n3["primary"]; p3dm = n3["demeaned"]
    metals_long = float(np.mean([tilt[r]["share_long"] for r in METALS])); high_short = float(np.mean([tilt[r]["share_short"] for r in HIGH_HP]))
    preds = {
        "P-1": {"claim": "EW gross Sharpe 2016-2023 > 0; point 0.2-0.5", "value": cE["gross"]["sharpe"], "net": cE["net"]["sharpe"], "holds": bool(cE["gross"]["sharpe"] > 0), "in_point_range": bool(POINT_RANGE[0] <= cE["gross"]["sharpe"] <= POINT_RANGE[1])},
        "P-2": {"claim": "daily rho with the term-structure sort on 16 > 0.4", "value": comparability["rho_daily_2016_2023"], "holds": bool(comparability["rho_daily_2016_2023"] > 0.4)},
        "P-3": {"claim": "PL GC PA SI in the long leg >= 70% of month-ends; NG ZW in the short leg >= 70%", "metals_long_share": metals_long, "per_metal": {r: tilt[r]["share_long"] for r in METALS},
                "high_hp_short_share": high_short, "per_high": {r: tilt[r]["share_short"] for r in HIGH_HP}, "holds": bool(all(tilt[r]["share_long"] >= 0.7 for r in METALS) and all(tilt[r]["share_short"] >= 0.7 for r in HIGH_HP))},
        "P-4": {"claim": "de-meaned cell below the primary; de-meaned above its N3 p95 only if the primary is", "demeaned": cD["gross"]["sharpe"], "primary": cE["gross"]["sharpe"],
                "holds": bool(cD["gross"]["sharpe"] < cE["gross"]["sharpe"] and (not p3dm["clears_p95"] or p3["clears_p95"]))},
        "P-5": {"claim": "long leg root-month mean > short leg's", "long": root_months["long_leg"].get("mean"), "short": root_months["short_leg"].get("mean"), "holds": bool(root_months["long_leg"].get("mean", 0) > root_months["short_leg"].get("mean", 0))},
        "P-6": {"claim": "EW daily skew <= 0", "value": cE["gross"]["skew"], "holds": bool(cE["gross"]["skew"] <= 0)},
        "P-7": {"claim": "dollar book fails C-d; sub-book sigma <= $500", "sigma": dcell["net"]["sd_daily"], "sub_sigma": dcell["cd_subset"]["net"]["sd_daily"], "holds": bool(dcell["net"]["sd_daily"] > R55.C_D_SIGMA and dcell["cd_subset"]["net"]["sd_daily"] <= R55.C_D_SIGMA)},
        "P-8": {"claim": "falsifiers", "below_n1_p50": bool(cE["gross"]["sharpe"] < primary["p50"]), "tilt": bool(primary["clears_p95"] and not p3["clears_p95"]),
                "movement_carries_it": bool(primary["clears_p95"] and p3["clears_p95"] and p3dm["clears_p95"])},
    }
    passes = bool(cE["gross"]["sharpe"] > 0 and primary["clears_p95"] and p3["clears_p95"] and p3["margin_in_se"] is not None and p3["margin_in_se"] > 2 and n2["clears_p95"])
    if passes:
        verdict = "PASS"
    elif cE["gross"]["sharpe"] > 0 and primary["clears_p95"] and p3["unresolved"]:
        verdict = "UNRESOLVED (N3 margin within 2 SE)"
    elif cE["gross"]["sharpe"] > 0 and primary["clears_p95"] and not p3["clears_p95"]:
        verdict = "TILT"
    else:
        verdict = "DOES NOT PASS"
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "P-8") + f"; P-8 {preds['P-8']}")
    log(f"  VERDICT {verdict}")

    res = {"max_drawdown_convention": {"sign": "negative", "note": "Drawdown LEVELS are NEGATIVE: minimum of (cumulative daily return - running peak); return units for the published books, dollars at minimum size for the dollar book (D542).", "record": "D542"},
           "spec": "D573", "commit": SPEC, "fixture_sha256": R55.sha256(R55.FIX), "curve_sha256": R55.sha256(R56.CURVE), "cot_sha256": R55.sha256(COT), "fixture_gates": gates,
           "windows": {"primary": PRIMARY, "long": LONG, "reserved_from": RESERVED_FROM, "sessions_primary": int(wP.sum()), "month_ends_primary": int(kP.sum()), "last_read": last_read},
           "universe": {"ranked_and_traded": roots, "excluded": {"BZ": "no CFTC series"}, "min_size": dict(zip(roots, size_name)), "leg_rule": "n_leg = ceil(n/3); long the LOWEST hedgers' HP; ties by symbol"},
           "signal": signal, "eligibility": eligibility, "cells": results_cells, "primary": primary, "null_n1": n1, "null_n2": n2, "null_n3": n3,
           "root_months": root_months, "concentration": conc, "per_root": per_root, "tilt": tilt, "per_era": per_era, "per_year": per_year, "comparability": comparability,
           "dollar_book": dollar_decomp, "component_line": component, "predictions": preds, "verdict": {"declared": verdict}, "audits": audits,
           "timing": {"wall_s": round(time.time() - t_start, 1), "null_ms_per_offset_probe": round(per_offset * 1e3, 2), "null_projected_s": round(projected, 1), "n3_wall_s": n3["wall_s"]}}
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']['wall_s']}s)")
    return res


# --------------------------------------------------------------------------------------------
# self-test: synthetic positioning and bars; the NEW audits (signal second path, N3 leg counts) and the sort's direction
# --------------------------------------------------------------------------------------------
def selftest() -> int:
    print("D573 SELF-TEST -- synthetic COT and bars, no fixture read\n")
    rng = np.random.default_rng(573)
    roots = list(CM16); n = len(roots)
    days = pd.bdate_range("2012-01-02", "2016-12-30").strftime("%Y-%m-%d").to_numpy(); T = len(days); me = R55.month_ends(days); me_days = days[me]
    # weekly reports on Tuesdays, released the Friday of the same week; a root-level HP tilt plus a slow wander
    tues = pd.date_range("2011-01-04", "2016-12-27", freq="W-TUE"); level = np.linspace(0.25, 0.6, n)
    rows = []
    for i, r in enumerate(roots):
        wander = np.cumsum(rng.normal(0, 0.01, len(tues)))
        for t, d in enumerate(tues):
            hp = min(max(level[i] + 0.15 * math.sin(t / 26 + i) + wander[t] * 0.3, 0.02), 0.98)
            rows.append((r, d.strftime("%Y-%m-%d"), (d + pd.Timedelta(days=3)).strftime("%Y-%m-%d"), 1000 * hp, 1000 * (1 - hp)))
    cot = pd.DataFrame(rows, columns=["symbol", "report_date", "release_date_nominal", "long", "short"]); cot["hp"] = cot["long"] / (cot["long"] + cot["short"])
    hp13 = hp_at_month_ends(cot, roots, me_days, N_REPORTS, MIN_PRESENT)
    # [1] the signal by a second path agrees; keyed on the REPORT date it differs and the audit RAISES
    cells = [(i, k) for i in range(n) for k in range(2, len(me))]; cells = [cells[j] for j in rng.choice(len(cells), size=120, replace=False)]
    vb = hp_cells_pandas(cot, roots, me_days, cells, N_REPORTS, MIN_PRESENT); audit_signal_second_path(hp13, cells, vb)
    vb_rep = hp_cells_pandas(cot, roots, me_days, cells, N_REPORTS, MIN_PRESENT, key="report_date")
    if not (~np.isclose(vb, vb_rep)).any():
        raise AssertionError("report-date keying changed no cell: the break cannot fire")
    R61._expect_raise(lambda: audit_signal_second_path(hp13, cells, vb_rep, "report-keyed"), "signal audit on report keying")
    print(f"  [1] the 13-report mean agrees across two paths at 120 cells; keyed on the report date it differs at {int((~np.isclose(vb, vb_rep)).sum())} and the audit RAISES")
    # [2] the sort: long the LOWEST HP; the pandas path agrees; RAISES on a swapped pair
    member, diag = R57.membership_at_month_ends(-hp13, roots); member_pd = R57.membership_pandas(-hp13, roots); R57.audit_leg_membership(member, member_pd, me, days)
    k = len(me) - 1; lo = hp13[member[:, k] == 1, k].mean(); hi = hp13[member[:, k] == -1, k].mean()
    if not lo < hi:
        raise AssertionError("long leg does not have the lower HP")
    R61._expect_raise(lambda: R57.audit_leg_membership(R57.swap_one_pair(member), member_pd, me, days), "leg audit on a swapped pair")
    print(f"  [2] long leg mean HP {lo:.3f} < short leg {hi:.3f}; the pandas path agrees and the audit RAISES on a swapped pair")
    # [3] the held grid: lag and right-quantity audits RAISE on their breaks
    span = np.ones((n, T), dtype=bool); sh = R55.hold_from_month_ends(member.astype(float), me, T, span); R55.audit_lag(sh, member_pd.astype(float), me, span, T)
    unl = np.zeros_like(sh)
    for kk, m_ix in enumerate(me):
        lo_ = me[kk - 1] + 1 if kk > 0 else 0; unl[:, lo_:m_ix + 1] = member[:, kk][:, None]
    R61._expect_raise(lambda: R55.audit_lag(unl, member_pd.astype(float), me, span, T), "lag audit on an unlagged book")
    R55.audit_right_quantity(sh, me, T); R61._expect_raise(lambda: R55.audit_right_quantity(rng.choice([-1.0, 1.0], size=(n, T)), me, T), "right-quantity on a daily grid")
    print("  [3] lag and right-quantity audits pass and RAISE on an unlagged and a daily grid")
    # [4] N3 draws keep the leg counts; the audit RAISES on a draw with an extra long
    elig = np.isfinite(hp13); rr = np.random.default_rng(2); dr = n3_draw(member, elig, rr); audit_draw_leg_counts(member, dr, elig)
    bad = dr.copy(); k0 = int(np.flatnonzero((member == 1).sum(0) > 0)[0]); free = np.flatnonzero((bad[:, k0] == 0) & elig[:, k0]); bad[free[0], k0] = 1
    R61._expect_raise(lambda: audit_draw_leg_counts(member, bad, elig), "N3 audit on an extra long")
    print("  [4] a name-randomised draw keeps every leg size and the audit RAISES on a draw with an extra long")
    # [5] on bars whose drift is -(HP - 0.5) the sort earns and beats its N3 (200 draws)
    hp_daily = np.full((n, T), 0.5)
    for i in range(n):
        for kk in range(len(me) - 1):
            if np.isfinite(hp13[i, kk]):
                hp_daily[i, me[kk] + 1:me[kk + 1] + 1] = hp13[i, kk]
    rlog = -0.004 * (hp_daily - 0.5) + 0.01 * rng.standard_normal((n, T)); rsimple = np.expm1(rlog)
    x = R55.book_return(sh, rsimple); w = np.ones(T, dtype=bool)
    d3, _ = name_randomised_null(member, elig, me, T, span, rsimple, w, 200, 5)
    if not (R55.sharpe(x) > np.percentile(d3, 95)):
        raise AssertionError(f"sort {R55.sharpe(x):.2f} does not beat N3 p95 {np.percentile(d3, 95):.2f}")
    print(f"  [5] on synthetic bars the sort earns Sharpe {R55.sharpe(x):+.2f} against an N3 p95 of {np.percentile(d3, 95):+.2f}")
    print("\nSELF-TEST PASSED"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else (run() and 0))
