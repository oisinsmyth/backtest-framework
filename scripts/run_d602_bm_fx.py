"""D602 -- basis momentum on the six CME FX roots in covered-parity space. Pre-registration committed BEFORE this file (see SPEC).

    uv run python scripts/run_d602_bm_fx.py --selftest   # every audit passes a clean case and RAISES on a break
    uv run python scripts/run_d602_bm_fx.py --run        # in-sample 2011-07 .. 2023-12-29; the FX 2024+ slice is NOT read

The strip restricted to the quarterly deliveries; D564's nearby series, eligibility and membership (n_leg 2, min_eligible 4);
the signal BM_fx = sum over the lookback of [ln(1+R1) - ln(1+R2) + dD], dD the change of the covered-parity fair log spread on
the pair chosen the month before, from the D601 OECD 3-month rates dated the month before formation; the paper's raw product
form beside as the named failure mode; the adjustment harness (BM_raw against the twelve-month change of the rate differential
strongly negative, BM_fx near zero) declared void-not-failed; D564's N1 (purge 252) / N2 / N3 nulls; the dollar cell at micro
size for the component line. Output data/d602_bm_fx.json.
"""
from __future__ import annotations

import argparse
import calendar
import importlib.util
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


R83 = _load("d583", "stage0_d583_bm_quarter_end.py"); R64 = R83.R64; R55, R56, R57 = R83.R55, R83.R56, R83.R57; R61 = R64.R61
OUT = REPO / "data" / "d602_bm_fx.json"; RATES = REPO / "data" / "fixtures" / "oecd_ir3tib_monthly.csv"
SPEC = "D602"
FX = ["6A", "6B", "6C", "6E", "6J", "6S"]; CCY = {"6A": "AUD", "6B": "GBP", "6C": "CAD", "6E": "EUR", "6J": "JPY", "6S": "CHF"}
DAYCOUNT = {"USD": 360, "EUR": 360, "JPY": 360, "CHF": 360, "CAD": 360, "GBP": 365, "AUD": 365}
QUARTERLY = "HMUZ"; MONTH_OF = {"H": 3, "M": 6, "U": 9, "Z": 12}
LOOKBACK = R64.LOOKBACK; N_LEG, MIN_ELIGIBLE = 2, 4; FFILL = R64.FFILL_FORMATION; RATE_LAG = 1
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
HARNESS_RAW_MAX, HARNESS_FX_MAX = -0.5, 0.3; N3_DRAWS, N3_SEED = 2000, 602
REQUIRED_OUTPUTS = ("spec", "windows", "universe", "rates", "harness", "audits", "cells", "nulls", "component_line", "eligibility", "predictions", "verdict", "timing_s")
expect_raise = R83.expect_raise


def guard_outputs(res):
    missing = [k for k in REQUIRED_OUTPUTS if k not in res]
    if missing:
        raise AssertionError(f"REQUIRED_OUTPUTS missing: {missing}")


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float); ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return np.nan
    return float(np.corrcoef(pd.Series(a[ok]).rank().to_numpy(), pd.Series(b[ok]).rank().to_numpy())[0, 1])


def third_wednesday(y, m):
    first = calendar.weekday(y, m, 1); d = 1 + (2 - first) % 7 + 14; return pd.Timestamp(y, m, d)


def quarterly_strip(strip):
    """Keep the quarterly deliveries only: the month letter after the two-character root."""
    return strip[strip["contract"].str[2].isin(list(QUARTERLY))].copy()


def load_rates(lag=RATE_LAG):
    """{currency: {YYYY-MM formation month: rate fraction dated `lag` months earlier}} and the filled-cell list."""
    df = pd.read_csv(RATES, encoding="utf-8", dtype={"period": str}); df = df[df["period"] < RESERVED_FROM[:7]]
    out = {}
    for c, g in df.groupby("currency"):
        ser = g.set_index("period")["rate_pct"] / 100.0; out[c] = {}
        for p in ser.index:
            use = (pd.Period(p, "M") + lag).strftime("%Y-%m"); out[c][use] = float(ser[p])
    return out, df[df["filled"] == True][["currency", "period"]].to_dict("records")


def fair_log_spread(day, ym1, ym2, r_usd, r_fx, ccy):
    """D = [ln(1 + r_usd t2) - ln(1 + r_fx t2)] - [ln(1 + r_usd t1) - ln(1 + r_fx t1)], tenors to the third Wednesdays."""
    t0 = pd.Timestamp(str(day)); tau1 = (third_wednesday(*ym1) - t0).days; tau2 = (third_wednesday(*ym2) - t0).days
    bu, bf = DAYCOUNT["USD"], DAYCOUNT[ccy]
    return (np.log1p(r_usd * tau2 / bu) - np.log1p(r_fx * tau2 / bf)) - (np.log1p(r_usd * tau1 / bu) - np.log1p(r_fx * tau1 / bf))


def ym_of_col(col):
    yy, mm = divmod(int(col), 12)
    return (yy - 1, 12) if mm == 0 else (yy, mm)


def cip_correction(ns, tables, roots, days, me, rates, sign=1.0):
    """dD[i, k]: the change of D over the holding month k-1 -> k on the pair chosen at k-1; NaN where a rate or a contract is missing."""
    n, K = ns["R1"].shape; dD = np.full((n, K), np.nan); rate_ok = np.zeros((n, K), dtype=bool)
    for i, r in enumerate(roots):
        cols = tables[r][1]; ccy = CCY[r]
        for k in range(1, K):
            j1, j2 = ns["T1"][i, k - 1], ns["T2"][i, k - 1]
            if j1 < 0 or j2 < 0:
                continue
            m0, m1 = str(days[me[k - 1]])[:7], str(days[me[k]])[:7]
            if not (m0 in rates["USD"] and m0 in rates[ccy] and m1 in rates["USD"] and m1 in rates[ccy]):
                continue
            ym1, ym2 = ym_of_col(cols[j1]), ym_of_col(cols[j2])
            D0 = fair_log_spread(days[me[k - 1]], ym1, ym2, rates["USD"][m0], rates[ccy][m0], ccy); D1 = fair_log_spread(days[me[k]], ym1, ym2, rates["USD"][m1], rates[ccy][m1], ccy)
            dD[i, k] = sign * (D1 - D0); rate_ok[i, k] = True
    return dD, rate_ok


def cip_correction_pandas(ns, tables, roots, days, me, rates_df, lag=RATE_LAG):
    """Second path: a long frame of (root, k, pair, dates) merged with the rate fixture, vectorised arithmetic; never calls cip_correction."""
    n, K = ns["R1"].shape; rows = []
    for i, r in enumerate(roots):
        cols = tables[r][1]
        for k in range(1, K):
            j1, j2 = ns["T1"][i, k - 1], ns["T2"][i, k - 1]
            if j1 >= 0 and j2 >= 0:
                rows.append({"i": i, "k": k, "ccy": CCY[r], "d0": str(days[me[k - 1]]), "d1": str(days[me[k]]), "y1": ym_of_col(cols[j1])[0], "m1": ym_of_col(cols[j1])[1], "y2": ym_of_col(cols[j2])[0], "m2": ym_of_col(cols[j2])[1]})
    f = pd.DataFrame(rows)
    if not len(f):
        return np.full((n, K), np.nan)
    rt = rates_df[rates_df["period"] < RESERVED_FROM[:7]].copy(); rt["use"] = (pd.PeriodIndex(rt["period"], freq="M") + lag).strftime("%Y-%m"); rt["rate"] = rt["rate_pct"] / 100.0
    for tag, col in (("0", "d0"), ("1", "d1")):
        f["use" + tag] = f[col].str[:7]
        f = f.merge(rt[rt["currency"] == "USD"][["use", "rate"]].rename(columns={"use": "use" + tag, "rate": "ru" + tag}), on="use" + tag, how="left")
        f = f.merge(rt[["currency", "use", "rate"]].rename(columns={"currency": "ccy", "use": "use" + tag, "rate": "rf" + tag}), on=["ccy", "use" + tag], how="left")
    tw1 = pd.to_datetime([third_wednesday(y, m) for y, m in zip(f["y1"], f["m1"])]); tw2 = pd.to_datetime([third_wednesday(y, m) for y, m in zip(f["y2"], f["m2"])])
    bu = DAYCOUNT["USD"]; bf = f["ccy"].map(DAYCOUNT).to_numpy(float)
    def D(dcol, ru, rf):
        t0 = pd.to_datetime(f[dcol]).to_numpy(); tau1 = (tw1.to_numpy() - t0) / np.timedelta64(1, "D"); tau2 = (tw2.to_numpy() - t0) / np.timedelta64(1, "D")
        return (np.log1p(ru * tau2 / bu) - np.log1p(rf * tau2 / bf)) - (np.log1p(ru * tau1 / bu) - np.log1p(rf * tau1 / bf))
    dD = D("d1", f["ru1"].to_numpy(float), f["rf1"].to_numpy(float)) - D("d0", f["ru0"].to_numpy(float), f["rf0"].to_numpy(float))
    out = np.full((n, K), np.nan); out[f["i"].to_numpy(), f["k"].to_numpy()] = dD; return out


def audit_cip(a, b):
    if not np.allclose(a, b, atol=1e-12, equal_nan=True):
        raise AssertionError(f"CIP AUDIT: the numpy and pandas corrections disagree on {int((~np.isclose(np.nan_to_num(a, nan=-9), np.nan_to_num(b, nan=-9), atol=1e-12)).sum())} cells")


def signals_fx(R1, R2, dD, stale, rate_ok):
    """BM_fx = sum over the lookback of [ln(1+R1) - ln(1+R2) + dD]; eligible where all twelve of everything are present and nothing stale."""
    n, K = R1.shape; S = np.full((n, K), np.nan); elig = np.zeros((n, K), dtype=bool); term = np.log1p(R1) - np.log1p(R2) + dD
    for k in range(LOOKBACK - 1, K):
        w = term[:, k - LOOKBACK + 1:k + 1]; ok = np.isfinite(w).all(1) & rate_ok[:, k - LOOKBACK + 1:k + 1].all(1) & ~stale[:, k]
        S[ok, k] = w[ok].sum(1); elig[:, k] = ok
    return S, elig


def audit_cip_exactness(rng, flip=False):
    """Sign in money for the construction: settlements that follow covered parity exactly (spot constant) give BM_raw != 0 while
    BM_fx == 0 to 1e-12; with the correction's sign flipped BM_fx is twice the raw term and the audit raises."""
    days_ = pd.bdate_range("2012-01-02", "2015-12-31").strftime("%Y-%m-%d").to_numpy(); me_ = R55.month_ends(days_); K = me_.size; T = days_.size
    ru = {str(d)[:7]: 0.01 + 0.0005 * i for i, d in enumerate(days_[me_])}; rf = {str(d)[:7]: 0.02 for d in days_[me_]}   # USD rate rising 5 bp a month
    rates = {"USD": ru, "EUR": rf}; S = 1.25; ccy = "EUR"
    # the quarterly contracts: columns keyed year*12+month like strip_tables; settlement each session by CIP with that session's month rates
    ym = sorted({(int(d[:4]) + (1 if m > 12 else 0), m if m <= 12 else m - 12) for d in days_ for m in (3, 6, 9, 12, 15)}); cols = np.array([y * 12 + m for y, m in ym]); A = np.full((T, cols.size), np.nan)
    for t, d in enumerate(days_):
        mkey = d[:7]
        if mkey not in ru:
            continue
        for j, (y, m) in enumerate(ym):
            tau = (third_wednesday(y, m) - pd.Timestamp(d)).days
            if 0 < tau < 400:
                A[t, j] = S * (1 + ru[mkey] * tau / 360) / (1 + rf[mkey] * tau / 360)
    tables = {"6E": (A, cols)}; ns = R64.nearby_series(tables, ["6E"], days_, me_, ffill=1)
    dD, ok = cip_correction(ns, tables, ["6E"], days_, me_, rates, sign=-1.0 if flip else 1.0); Sfx, e = signals_fx(ns["R1"], ns["R2"], dD, ns["stale"], ok); Sraw, _, er = R64.signals_at_month_ends(ns["R1"], ns["R2"], ns["stale"])
    if not e.any():
        raise RuntimeError("synthetic construction has no eligible month-end")
    if np.nanmax(np.abs(Sfx[e])) > 1e-12 or np.nanmax(np.abs(Sraw[er])) < 1e-6:
        raise AssertionError(f"CIP EXACTNESS: BM_fx max |{np.nanmax(np.abs(Sfx[e])):.2e}| should be 0 on parity settlements while BM_raw is {np.nanmax(np.abs(Sraw[er])):.2e}")
    return float(np.nanmax(np.abs(Sraw[er])))


# ------------------------------------------------------------------------------------------ run
def run(log=print):
    t0 = time.time(); rng = np.random.default_rng(N3_SEED); warnings.filterwarnings("ignore", category=RuntimeWarning)
    log(f"D602 -- basis momentum on {len(FX)} FX roots in covered-parity space; spec {SPEC} committed BEFORE this runner (R8); primary {PRIMARY[0]}..{PRIMARY[1]}; the FX 2024+ slice NOT READ")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); gfull = R55.build_grids(df, live_start); days = gfull["days"]; T = len(days); me = R55.month_ends(days); K = len(me); n = len(FX)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[(strip["ref"] < RESERVED_FROM) & strip["root"].isin(FX)]; strip_q = quarterly_strip(strip)
    universe = {"roots": FX, "strip_rows_all": int(len(strip)), "strip_rows_quarterly": int(len(strip_q)), "serial_rows_dropped": int(len(strip) - len(strip_q))}
    tables = R64.strip_tables(strip_q, days, FX); ns = R64.nearby_series(tables, FX, days, me, ffill=FFILL); ns0 = R64.nearby_series(tables, FX, days, me, ffill=1)
    rates, filled = load_rates(); rates_df = pd.read_csv(RATES, encoding="utf-8", dtype={"period": str})
    dD, rate_ok = cip_correction(ns, tables, FX, days, me, rates); audit_cip(dD, cip_correction_pandas(ns, tables, FX, days, me, rates_df)); audits = {"cip_second_path": True}
    audits["cip_audit_raises"] = expect_raise(lambda: audit_cip(dD, cip_correction_pandas(ns, tables, FX, days, me, rates_df, lag=0)), "the rate lag removed", log)
    audits["cip_exactness_raw_on_parity"] = audit_cip_exactness(rng); audits["cip_exactness_raises"] = expect_raise(lambda: audit_cip_exactness(rng, True), "the correction's sign flipped", log)
    BMfx, elig = signals_fx(ns["R1"], ns["R2"], dD, ns["stale"], rate_ok); BMraw, _, elig_raw = R64.signals_at_month_ends(ns["R1"], ns["R2"], ns["stale"]); BM0, _, elig0 = R64.signals_at_month_ends(ns0["R1"], ns0["R2"], ns0["stale"])
    # the raw signal by D564's own second path on the quarterly pivot (its delivery rule is D564's, FX is not energy)
    piv = {}; audits["raw_cells_checked_against_strip"] = R64.audit_bm_from_strip(BMraw, elig_raw, strip_q, FX, days, me, ffill=FFILL, pivots=piv)
    audits["raw_audit_raises"] = expect_raise(lambda: R64.audit_bm_from_strip(-BMraw, elig_raw, strip_q, FX, days, me, n_check=20, ffill=FFILL, pivots=piv), "a negated raw grid", log)
    span = np.zeros((n, T), dtype=bool)
    for i in range(n):
        ix = np.flatnonzero(ns["live"][i])
        if ix.size:
            span[i, ix[0]:ix[-1] + 1] = True
    rsimple = ns["r1d"]; rlog1 = np.where(ns["live"] & (rsimple != 0.0), np.log1p(rsimple), np.nan); g = dict(roots=FX, days=days, close=ns["close1"], rlog=rlog1, dP=ns["dP1"], roll=ns["roll"], live=ns["live"], span=span, nonpositive=[])
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG); dP_days, dL_days = days[wP], days[wL]; meP = np.array([wP[min(m + 1, T - 1)] for m in me])
    first_elig = next((k for k in range(K) if elig[:, k].sum() >= MIN_ELIGIBLE), None); log(f"  quarterly strip {universe['strip_rows_quarterly']:,} rows ({universe['serial_rows_dropped']:,} serial rows dropped); first month-end with >= {MIN_ELIGIBLE} eligible {days[me[first_elig]] if first_elig is not None else None}; filled rate cells {filled}")
    # ---- the adjustment harness ----
    diff = np.full((n, K), np.nan)
    for i, r in enumerate(FX):
        for k in range(K):
            mk = str(days[me[k]])[:7]
            if mk in rates["USD"] and mk in rates[CCY[r]]:
                diff[i, k] = rates["USD"][mk] - rates[CCY[r]][mk]
    d12 = np.full((n, K), np.nan); d12[:, LOOKBACK:] = diff[:, LOOKBACK:] - diff[:, :-LOOKBACK]
    both = elig & elig_raw & np.isfinite(d12) & meP[None, :] | (elig & elig_raw & np.isfinite(d12) & (np.arange(K)[None, :] >= (first_elig or 0)))
    rho_raw = spearman(BMraw[both], d12[both]); rho_fx = spearman(BMfx[both], d12[both]); rho_fx_raw = spearman(BMfx[both], BMraw[both])
    lag0, ok0 = cip_correction(ns, tables, FX, days, me, load_rates(lag=0)[0]); BMfx0, e0 = signals_fx(ns["R1"], ns["R2"], lag0, ns["stale"], ok0); rho_lag = spearman(BMfx[elig & e0], BMfx0[elig & e0])
    usd = rates_df[(rates_df["currency"] == "USD") & (rates_df["period"] >= "2021-06") & (rates_df["period"] <= "2023-12")].set_index("period")["rate_pct"]
    harness = {"spearman_raw_vs_d12_diff": rho_raw, "spearman_fx_vs_d12_diff": rho_fx, "bars": {"raw_below": HARNESS_RAW_MAX, "fx_abs_below": HARNESS_FX_MAX}, "holds": bool(rho_raw < HARNESS_RAW_MAX and abs(rho_fx) < HARNESS_FX_MAX), "n_root_months": int(both.sum()),
               "spearman_fx_vs_raw": rho_fx_raw, "spearman_fx_lag1_vs_lag0": rho_lag, "usd_series_2021_06_to_2023_12": {"min": float(usd.min()), "max": float(usd.max()), "largest_monthly_step_pct": float(usd.diff().abs().max())}}
    log(f"  adjustment harness: Spearman(BM_raw, d12 diff) {rho_raw:+.3f} (bar < {HARNESS_RAW_MAX}); Spearman(BM_fx, d12 diff) {rho_fx:+.3f} (bar |.| < {HARNESS_FX_MAX}) -> {'HOLDS' if harness['holds'] else 'FAILS: the trial is VOID'}; Spearman(BM_fx, BM_raw) {rho_fx_raw:+.3f}; lag1 vs lag0 {rho_lag:+.3f}")
    # ---- membership, audits, cells ----
    member, diag = R64.membership_fixed(BMfx, elig, FX, N_LEG, MIN_ELIGIBLE); member_pd = R64.membership_fixed_pandas(BMfx, elig, FX, N_LEG, MIN_ELIGIBLE)
    audits["leg_membership_cells"] = R57.audit_leg_membership(member, member_pd, me, days); audits["membership_raises_on_swapped_pair"] = expect_raise(lambda: R57.audit_leg_membership(R57.swap_one_pair(member), member_pd, me, days), "a swapped pair", log)
    sign_held = R55.hold_from_month_ends(member.astype(float), me, T, span); audits["lag_held_cells"] = R55.audit_lag(sign_held, member_pd.astype(float), me, span, T)
    unl = np.zeros_like(sign_held)
    for k, m_ix in enumerate(me):
        lo = me[k - 1] + 1 if k > 0 else 0; unl[:, lo:m_ix + 1] = member[:, k][:, None]
    audits["lag_raises_on_unlagged_book"] = expect_raise(lambda: R55.audit_lag(np.where(span, unl, 0.0), member_pd.astype(float), me, span, T), "an unlagged book", log)
    audits["right_quantity_changes"] = R55.audit_right_quantity(sign_held, me, T); audits["right_quantity_raises_on_daily_grid"] = expect_raise(lambda: R55.audit_right_quantity(np.tile(np.where(np.arange(T) % 2 == 0, 1.0, -1.0), (n, 1)), me, T), "a daily grid", log)
    upp_f, tick_f, comm_f, size_f = R56.min_size(gfull, gfull["roots"]); ixf = [gfull["roots"].index(r) for r in FX]; upp, tick_usd, comm_rt, size_name = upp_f[ixf], tick_f[ixf], comm_f[ixf], [size_f[j] for j in ixf]
    dollar_roots = [r for r in FX if r not in R55.DOLLAR_EXCLUDED]; sd = sign_held.astype(int); grossD_all, _, _ = R55.dollar_book(sd, g, upp, comm_rt, tick_usd, FX)
    audits["sign_in_money_roots_checked"] = R55.audit_sign_in_money(grossD_all, sd, g, upp)
    audits["sign_raises_on_negated_grid"] = expect_raise(lambda: R55.audit_sign_in_money(-grossD_all, sd, g, upp), "a negated dollar grid", log)
    audits["sign_raises_on_mislagged_grid"] = expect_raise(lambda: R55.audit_sign_in_money(R55.dollar_book(sd, dict(g, dP=np.roll(g["dP"], 1, axis=1)), upp, comm_rt, tick_usd, FX)[0], sd, g, upp), "a mislagged dollar grid", log)
    sig = R55.ew_vol(rlog1, ns["live"]); BM_dm = np.full_like(BMfx, np.nan)
    for i in range(n):
        cnt = 0; tot = 0.0
        for k in range(K):
            if elig[i, k] and np.isfinite(BMfx[i, k]):
                cnt += 1; tot += BMfx[i, k]
                if cnt >= 12:
                    BM_dm[i, k] = BMfx[i, k] - tot / cnt
    ts_sign_held, ts_pos, ts_scale, _ = R56.positions_from_signs(np.where(np.isfinite(BM_dm), np.sign(BM_dm), 0.0), sig, me, g)
    member_raw, diag_raw = R64.membership_fixed(BMraw, elig_raw, FX, N_LEG, MIN_ELIGIBLE); raw_held = R55.hold_from_month_ends(member_raw.astype(float), me, T, span)
    ones = np.ones((n, T))
    cells = {"primary": dict(book="published", sign_held=sign_held, scale_held=ones, pos=sign_held), "timeseries": dict(book="published", sign_held=ts_sign_held, scale_held=ts_scale, pos=ts_pos),
             "raw": dict(book="published", sign_held=raw_held, scale_held=ones, pos=raw_held), "dollar": dict(book="dollar", sign_held=sign_held, scale_held=None, pos=None)}
    cbp = R55.cost_bp_per_side(g, upp, comm_rt, tick_usd); results = {}; scored = {}
    for name, c in cells.items():
        if c["book"] == "published":
            x = R55.book_return(c["pos"], rsimple); turn, rolls, tw = R55.published_cost(c["pos"], cbp, g["roll"]); xn = x - turn
            results[name] = {"gross": R55.stats_block(x[wP], dP_days, name), "net": R55.stats_block(xn[wP], dP_days, name + " net"), "gross_long": R55.stats_block(x[wL], dL_days, name + " 2011-2023"), "ann_turnover_weight_units": float(tw[wP].sum() / (wP.sum() / 252)),
                             "breakeven_bp_per_side": float(x[wP].mean() / max(tw[wP].mean(), 1e-12) * 1e4), "positioned_names_mean": float((c["pos"][:, wP] != 0).sum(0).mean())}
            scored[name] = dict(gross=x, net=xn)
        else:
            sP = np.where(wP[None, :], c["sign_held"], 0.0).astype(int); gross, cost, sides = R55.dollar_book(sP, g, upp, comm_rt, tick_usd, dollar_roots); gb, cb = gross.sum(0), cost.sum(0)
            per_root = {r: float((gross[i] - cost[i])[wP].sum()) for i, r in enumerate(FX)}
            results[name] = {"gross": R55.stats_block(gb[wP], dP_days, name), "net": R55.stats_block((gb - cb)[wP], dP_days, name + " net"), "cost_total": float(cb[wP].sum()), "sides_total": int(sides[:, wP].sum()), "per_root_net_usd": per_root, "min_size": dict(zip(FX, size_name)),
                             "sigma_usd_daily": float((gb - cb)[wP].std(ddof=1))}
            scored[name] = dict(gross=gb, net=gb - cb)
        log(f"  {name:10s} gross {results[name]['gross']['sharpe']:+.3f} / So {results[name]['gross']['sortino']:+.3f} (SE {results[name]['gross']['se']:.2f})  net {results[name]['net']['sharpe']:+.3f}  long {results[name]['gross_long']['sharpe']:+.3f}" if 'gross_long' in results[name] else f"  {name:10s} gross ${results[name]['gross']['mean_daily']:+.0f}/day Sharpe {results[name]['gross']['sharpe']:+.3f} net {results[name]['net']['sharpe']:+.3f}")
    # ---- nulls ----
    live_idx = [np.flatnonzero(span[i] & wP) for i in range(n)]; null_cells = {k: dict(book="published", sign_held=np.where(wP[None, :], v["sign_held"], 0.0), scale_held=v["scale_held"]) for k, v in cells.items() if v["book"] == "published"}
    for k in R61.GUARD_OFFSETS:
        k = k % (int(wP.sum()) - 1) or 1; p = R55.rotate_signs(null_cells["primary"]["sign_held"], live_idx, k) * ones
        if not np.array_equal(R55.book_return(p, rsimple)[wP], R55.book_return_loop(p[:, wP], rsimple[:, wP])):
            raise AssertionError(f"exactness guard failed at offset {k}")
    audits["exactness_guard_offsets"] = len(R61.GUARD_OFFSETS); tn = time.time()
    null_all, keys, null_s = R55.enumerate_null(null_cells, g, live_idx, wP, rsimple, upp, comm_rt, tick_usd, dollar_roots, log, with_sortino=True)
    ks = np.arange(1, null_all.shape[0] + 1); keep = (ks >= R55.NULL_PURGE) & (ks <= int(wP.sum()) - R55.NULL_PURGE); null = null_all[keep]; obs = np.array([results[k]["gross"]["sharpe"] for k in keys])
    n1 = {"offsets_enumerated": int(null_all.shape[0]), "purge_sessions": R55.NULL_PURGE, "offsets_after_purge": int(null.shape[0]), "per_cell": {}, "wall_s": round(time.time() - tn, 1)}
    for j, nm in enumerate(keys):
        col = null[:, j]; n1["per_cell"][nm] = {"observed": float(obs[j]), "p05": float(np.percentile(col, 5)), "p50": float(np.percentile(col, 50)), "p95": float(np.percentile(col, 95)), "pct_rank": float((col < obs[j]).mean()), "clears_p95": bool(obs[j] > np.percentile(col, 95)),
                                                 "sortino": R55.sortino_null_block(scored[nm]["gross"][wP], null_s[:, j], keep)}
    fam_keys = ["primary", "timeseries"]; jf = [keys.index(k) for k in fam_keys]; fam = null[:, jf].max(1); best = obs[jf].max()
    n2 = {"family": fam_keys, "observed_best": float(best), "observed_best_cell": fam_keys[int(obs[jf].argmax())], "p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95)), "pct_rank": float((fam < best).mean()), "clears_p95": bool(best > np.percentile(fam, 95))}
    t3 = time.time(); v3, s3 = R64.name_randomised_null(np.where(meP[None, :], member, 0), elig, me, T, span, rsimple, wP, days, N3_DRAWS, N3_SEED); o = results["primary"]["gross"]["sharpe"]; p95 = float(np.percentile(v3, 95)); se3 = R64._p95_boot_se(v3)
    n3 = {"draws": N3_DRAWS, "p50": float(np.percentile(v3, 50)), "p95": p95, "p95_boot_se": se3, "pct_rank": float((v3 < o).mean()), "clears_p95": bool(o > p95), "unresolved": bool(abs(o - p95) < 2 * se3), "wall_s": round(time.time() - t3, 1)}
    prim = n1["per_cell"]["primary"]; log(f"  N1 primary rank {prim['pct_rank']:.3f} (p05 {prim['p05']:+.3f} p50 {prim['p50']:+.3f} p95 {prim['p95']:+.3f}); raw rank {n1['per_cell']['raw']['pct_rank']:.3f} (p95 {n1['per_cell']['raw']['p95']:+.3f}); N2 best {n2['observed_best']:+.3f} ({n2['observed_best_cell']}) p95 {n2['p95']:+.3f} rank {n2['pct_rank']:.3f}; N3 rank {n3['pct_rank']:.3f} (p95 {n3['p95']:+.3f}, SE {se3:.3f}){' UNRESOLVED' if n3['unresolved'] else ''}")
    # ---- eligibility, distribution, component line ----
    elig_rows = [{"date": str(days[me[k]]), **diag[k]} for k in range(K) if meP[k]]
    eligibility = {"mean_eligible_primary": float(np.mean([d_["n_eligible"] for d_ in elig_rows])), "share_month_ends_ge5": float(np.mean([d_["n_eligible"] >= 5 for d_ in elig_rows])), "flat_month_ends_primary": int(sum(d_["flat"] for d_ in elig_rows)), "flat_share": float(np.mean([d_["flat"] for d_ in elig_rows])),
                   "ties_at_boundary_primary": int(sum(d_["tie_at_boundary"] for d_ in elig_rows)), "stale_root_months_primary": int(ns["stale"][:, meP].sum()), "rate_missing_root_months": int((~rate_ok[:, meP] & (ns["T1"][:, meP] >= 0)).sum()), "first_eligible_month_end": str(days[me[first_elig]]) if first_elig is not None else None}
    x = scored["primary"]["gross"]; rmt = R57.root_month_table(sign_held, rsimple, days, wP); dist = {"all": R57.dist_stats(rmt["contrib"].to_numpy()), "long_leg": R57.dist_stats(rmt.loc[rmt["leg"] > 0, "contrib"].to_numpy()), "short_leg": R57.dist_stats(rmt.loc[rmt["leg"] < 0, "contrib"].to_numpy())}
    cnt = (sign_held != 0).sum(0); contrib = sign_held * rsimple / np.where(cnt > 0, cnt, 1)[None, :]; totals = {r: float(contrib[i][wP].sum()) for i, r in enumerate(FX)}; conc = R57.concentration(totals)
    per_era = {f"{a}..{b}": R55.sharpe(x[R55.window_mask(days, a, b)]) for a, b in R55.ERAS}; yrs = sorted({d[:4] for d in days[wL]}); per_year = {y: R55.sharpe(x[np.array([d[:4] == y for d in days])]) for y in yrs}
    days_cm, T_cm, me_cm, b_cm, _, _, _ = R83.build_book(lambda *_: None); x_cm = b_cm["x"]
    if not np.array_equal(days_cm, days):
        raise AssertionError("commodity and FX session calendars differ")
    xd = scored["dollar"]["net"]; rho_cm = float(np.corrcoef(x[wP], x_cm[wP])[0, 1]); rho_cm_dollar = float(np.corrcoef(xd[wP], x_cm[wP])[0, 1])
    component_line = {"cell": "dollar High2/Low2 at minimum size, $3/$6 RT + one tick, rolls charged", "net": results["dollar"]["net"], "gross": results["dollar"]["gross"], "sigma_usd_daily": results["dollar"]["sigma_usd_daily"], "min_size": results["dollar"]["min_size"],
                      "rho_daily_with_d564_commodity_book": {"published_cell": rho_cm, "dollar_cell": rho_cm_dollar}, "cost_total_usd": results["dollar"]["cost_total"], "per_root_net_usd": results["dollar"]["per_root_net_usd"]}
    log(f"  component line: net Sharpe {results['dollar']['net']['sharpe']:+.3f} / So {results['dollar']['net']['sortino']:+.3f} at sigma ${results['dollar']['sigma_usd_daily']:.0f}/day; rho with D564's commodity book {rho_cm:+.3f}; eligible {eligibility['mean_eligible_primary']:.2f}, flat {eligibility['flat_share']:.1%}, ties {eligibility['ties_at_boundary_primary']}")
    # ---- predictions and the verdict ----
    o_raw = n1["per_cell"]["raw"]; p1 = bool(o > 0 and prim["clears_p95"] and n2["clears_p95"]); raw_pass = bool(obs[keys.index("raw")] > 0 and o_raw["clears_p95"])
    preds = {"P-1": {"claim": "primary gross 2016-2023 > 0, above N1 p95, family above N2 p95; point prior 0.0-0.3", "value": o, "n1_p95": prim["p95"], "n2_p95": n2["p95"], "holds": p1, "in_point_range": bool(0.0 <= o <= 0.3)},
             "P-2": {"claim": "adjustment harness holds", "holds": harness["holds"], "raw": rho_raw, "fx": rho_fx},
             "P-3": {"named_outcome": ("VOID" if not harness["holds"] else "rate momentum, not imbalance" if (raw_pass and not p1) else "the adjustment was immaterial and the effect exists in FX" if (raw_pass and p1 and rho_fx_raw > 0.8) else "the mechanism's prediction" if (p1 and not raw_pass) else "both pass, moderately correlated" if (p1 and raw_pass) else "NOT SUPPORTED on FX"), "raw_pass": raw_pass, "fx_pass": p1, "spearman_fx_raw": rho_fx_raw},
             "P-4": {"claim": "eligible >= 5 on >= 90% of month-ends; flat <= 5%", "holds": bool(eligibility["share_month_ends_ge5"] >= 0.9 and eligibility["flat_share"] <= 0.05), "share_ge5": eligibility["share_month_ends_ge5"], "flat_share": eligibility["flat_share"]},
             "P-5": {"claim": "PRIMARY Sharpe within 0.4 of the LONG one", "primary": o, "long": results["primary"]["gross_long"]["sharpe"], "holds": bool(abs(o - results["primary"]["gross_long"]["sharpe"]) <= 0.4)},
             "P-6": {"claim": "rho with D564's commodity book < 0.3", "rho": rho_cm, "holds": bool(abs(rho_cm) < 0.3)}}
    verdict = "VOID" if not harness["holds"] else ("PASS in sample" if p1 else "NOT SUPPORTED")
    log("  predictions: " + "; ".join(f"{k} {'holds' if v.get('holds') else v.get('named_outcome', 'fails')}" for k, v in preds.items())); log(f"  VERDICT (in sample): {verdict}; forward slice unread")
    res = {"spec": SPEC, "windows": {"primary": list(PRIMARY), "long": list(LONG), "reserved_from": RESERVED_FROM, "forward_slice_read": False}, "universe": universe, "rates": {"fixture": str(RATES.relative_to(REPO)), "lag_months": RATE_LAG, "filled_cells": filled, "daycount": DAYCOUNT},
           "harness": harness, "audits": audits, "cells": results, "nulls": {"n1": n1, "n2": n2, "n3": n3}, "component_line": component_line, "eligibility": eligibility, "root_months": dist, "concentration": conc, "per_root_total_primary": totals, "per_era": per_era, "per_year": per_year,
           "as_preregistered_ffill1": {"primary_sharpe": R55.sharpe(R55.book_return(R55.hold_from_month_ends(R64.membership_fixed(*signals_fx(ns0["R1"], ns0["R2"], cip_correction(ns0, tables, FX, days, me, rates)[0], ns0["stale"], cip_correction(ns0, tables, FX, days, me, rates)[1]), FX, N_LEG, MIN_ELIGIBLE)[0].astype(float), me, T, span), ns0["r1d"])[wP])},
           "predictions": preds, "verdict": verdict, "timing_s": round(time.time() - t0, 1), "construction": {"n_leg": N_LEG, "min_eligible": MIN_ELIGIBLE, "lookback": LOOKBACK, "ffill": FFILL, "quarterly_only": True, "rate_lag": RATE_LAG}}
    guard_outputs(res); audits["required_outputs_guard_raises"] = expect_raise(lambda: guard_outputs({k: v for k, v in res.items() if k != "nulls"}), "a missing declared output", log)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8"); log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return res


def selftest(log=print) -> int:
    rng = np.random.default_rng(2)
    assert third_wednesday(2019, 6) == pd.Timestamp("2019-06-19") and third_wednesday(2024, 3) == pd.Timestamp("2024-03-20"); log("  third Wednesday: 2019-06-19, 2024-03-20")
    s = pd.DataFrame({"root": "6E", "contract": ["6EH1", "6EG1", "6EM1", "6EF2"], "ref": "2010-06-04", "settle": 1.2}); assert list(quarterly_strip(s)["contract"]) == ["6EH1", "6EM1"]; log("  quarterly filter keeps H M U Z only")
    raw_max = audit_cip_exactness(rng); log(f"  CIP exactness: parity settlements give BM_fx = 0 while BM_raw reaches {raw_max:.2e}"); expect_raise(lambda: audit_cip_exactness(rng, True), "the correction's sign flipped", log)
    # a rates fixture-shaped frame: the pandas and numpy corrections agree, and raise when the lag differs
    days_ = pd.bdate_range("2012-01-02", "2014-12-31").strftime("%Y-%m-%d").to_numpy(); me_ = R55.month_ends(days_); K = me_.size; T = days_.size
    ym = sorted({(int(d[:4]) + (1 if m > 12 else 0), m if m <= 12 else m - 12) for d in days_ for m in (3, 6, 9, 12, 15)}); cols = np.array([y * 12 + m for y, m in ym]); A = np.full((T, cols.size), np.nan)
    for t, d in enumerate(days_):
        for j, (y, m) in enumerate(ym):
            tau = (third_wednesday(y, m) - pd.Timestamp(d)).days
            if 0 < tau < 400:
                A[t, j] = 1.3 + 0.001 * j + 0.0001 * t
    tables = {"6E": (A, cols)}; ns = R64.nearby_series(tables, ["6E"], days_, me_, ffill=1)
    per = pd.period_range("2011-01", "2015-12", freq="M").strftime("%Y-%m"); rdf = pd.concat([pd.DataFrame({"currency": c, "area": c, "period": per, "rate_pct": rng.uniform(0, 3, per.size), "filled": False}) for c in ("USD", "EUR")], ignore_index=True)
    rates = {}
    for c, g_ in rdf.groupby("currency"):
        rates[c] = {(pd.Period(p, "M") + RATE_LAG).strftime("%Y-%m"): float(v) / 100 for p, v in zip(g_["period"], g_["rate_pct"])}
    dD, ok = cip_correction(ns, tables, ["6E"], days_, me_, rates); audit_cip(dD, cip_correction_pandas(ns, tables, ["6E"], days_, me_, rdf)); assert ok.sum() > 20; log(f"  CIP correction: numpy and pandas agree on {int(ok.sum())} root-months")
    expect_raise(lambda: audit_cip(dD, cip_correction_pandas(ns, tables, ["6E"], days_, me_, rdf, lag=0)), "the rate lag removed", log)
    expect_raise(lambda: guard_outputs({"spec": 1}), "missing outputs", log); log("  selftest: every audit passes its clean case and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.run:
        run()
    else:
        ap.print_help()
