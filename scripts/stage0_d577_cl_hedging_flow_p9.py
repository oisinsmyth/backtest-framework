"""D577 Stage 0 -- P9 of the CL hedging-flow derivation (design committed in D577 before this ran): does producer
hedging flow show in the Swap Dealer category or in Producer/Merchant? Positioning outcomes only; the 12-24-month
strip is the regressor; no return is computed; nothing from 2024-01-01 on is read. Writes data/stage0_d577_cl_p9.json.

    uv run python -u scripts/stage0_d577_cl_hedging_flow_p9.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m


R64 = _load("d564", "run_d564_basis_momentum.py")     # strip_tables, strip_pivot; loads D561/D557/D556/D555 once
R61, R56, R55 = R64.R61, R64.R56, R64.R55

OUT = REPO / "data" / "stage0_d577_cl_p9.json"
COT = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
ROOT = "CL"
RESERVED_FROM = R55.RESERVED_FROM
TENOR_LO, TENOR_HI = 12, 24
H_PRIMARY, HS = 4, (2, 4, 8)
NW_LAG = 4
SHIFT_MIN = 8
CAL_MONTHS = (2, 3, 8, 9)                         # 4-8 weeks before the Apr-May and Oct-Nov redeterminations
PRIOR_CONTRACTS_PER_USD = (18_000, 37_000)         # the derivation's section 7 prior, over the response window
CATS = {"PM": "producer_merchant", "SD": "swap_dealer", "MM": "managed_money"}


def tenor_logprices(A, cols, days, dates, lo, hi):
    """Per report date (last session <= date): mean log settlement over delivery months m+lo..m+hi, and log F_1 (m+1)."""
    day_ix = {d: i for i, d in enumerate(days)}
    out = np.full(len(dates), np.nan); f1 = np.full(len(dates), np.nan); used = []
    for j, d in enumerate(dates):
        sess = [x for x in days if x <= d]
        if not sess:
            used.append(None); continue
        t = day_ix[sess[-1]]; used.append(sess[-1])
        m = int(d[:4]) * 12 + int(d[5:7])
        vals = []
        for k in range(lo, hi + 1):
            jc = np.flatnonzero(cols == m + k)
            if jc.size and np.isfinite(A[t, jc[0]]):
                vals.append(np.log(A[t, jc[0]]))
        if len(vals) >= (hi - lo + 1) - 2:
            out[j] = float(np.mean(vals))
        j1 = np.flatnonzero(cols == m + 1)
        if j1.size and np.isfinite(A[t, j1[0]]):
            f1[j] = float(np.log(A[t, j1[0]]))
    return out, f1, used


def tenor_logprices_pandas(strip_root, days, dates, lo, hi):
    """Second path: the strip pivot (ffill 1 = the session alone), the same tenor set."""
    piv = R64.strip_pivot(strip_root, days, 1); out = np.full(len(dates), np.nan)
    for j, d in enumerate(dates):
        sess = [x for x in days if x <= d]
        if not sess or sess[-1] not in piv.index:
            continue
        row = piv.loc[sess[-1]]; m = int(d[:4]) * 12 + int(d[5:7])
        vals = [np.log(row[c]) for c in range(m + lo, m + hi + 1) if c in row.index and np.isfinite(row[c])]
        if len(vals) >= (hi - lo + 1) - 2:
            out[j] = float(np.mean(vals))
    return out


def nw_ols(y, x, lag):
    """Implementation A: statsmodels OLS with HAC (Bartlett, maxlags=lag). Returns beta, t, n."""
    ok = np.isfinite(y) & np.isfinite(x); yy, xx = y[ok], x[ok]
    if ok.sum() < 20:
        return float("nan"), float("nan"), int(ok.sum())
    X = sm.add_constant(xx); res = sm.OLS(yy, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    return float(res.params[1]), float(res.tvalues[1]), int(ok.sum())


def nw_ols_numpy(y, x, lag):
    """Implementation B: normal equations and a hand-rolled Bartlett Newey-West on the score."""
    ok = np.isfinite(y) & np.isfinite(x); yy, xx = y[ok], x[ok]; n = yy.size
    X = np.column_stack([np.ones(n), xx]); beta = np.linalg.solve(X.T @ X, X.T @ yy); e = yy - X @ beta
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lag + 1):
        w = 1 - L / (lag + 1); G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None]); S += w * (G + G.T)
    XtXi = np.linalg.inv(X.T @ X); V = XtXi @ S @ XtXi
    return float(beta[1]), float(beta[1] / np.sqrt(V[1, 1])), int(n)


def audit_ols(y, x, lag):
    a = nw_ols(y, x, lag); b = nw_ols_numpy(y, x, lag)
    if not (np.isclose(a[0], b[0], rtol=1e-9, atol=1e-12) and np.isclose(a[1], b[1], rtol=1e-6, atol=1e-9)):
        raise AssertionError(f"OLS AUDIT: statsmodels {a} vs numpy {b}")
    return a


def beta_only(y, x):
    ok = np.isfinite(y) & np.isfinite(x); yy, xx = y[ok], x[ok]; xc = xx - xx.mean()
    return float((xc * (yy - yy.mean())).sum() / (xc * xc).sum())


def shift_null(y, x, kmin):
    """Circular shift of the regressor against the outcome by every offset in [kmin, N-kmin]; beta at each."""
    ok = np.isfinite(y) & np.isfinite(x); yy, xx = y[ok], x[ok]; N = yy.size
    ks = np.arange(kmin, N - kmin + 1); out = np.array([beta_only(yy, np.roll(xx, int(k))) for k in ks])
    if not np.isclose(beta_only(yy, np.roll(xx, 0)), beta_only(yy, xx)):
        raise AssertionError("shift null: zero offset does not reproduce")
    return ks, out


def blk(obs, null):
    return {"observed": obs, "p05": float(np.percentile(null, 5)), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)), "n_offsets": int(null.size),
            "pct_rank": float((null < obs).mean()), "above_p95": bool(obs > np.percentile(null, 95)), "inside": bool(np.percentile(null, 5) <= obs <= np.percentile(null, 95))}


def main():
    t0 = time.time()
    print("D577 STAGE 0 -- P9: does CL producer hedging flow show in Swap Dealers or Producer/Merchant; design committed before this ran; positioning only; 2024+ shut")
    cot = pd.read_csv(COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "disaggregated") & (cot["report_date"] < RESERVED_FROM)].copy()
    if (cot["report_date"] >= RESERVED_FROM).any():
        raise AssertionError("reserved report present")
    piv = cot.pivot_table(index="report_date", columns="category", values=["long", "short"], aggfunc="first").sort_index()
    oi = cot.groupby("report_date")["open_interest"].first().sort_index()
    df = R55.load_fixture(); live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start); days = g["days"]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & (strip["root"] == ROOT)]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]
    dates = [d for d in piv.index if d >= str(days[0])]
    piv = piv.loc[dates]; oi = oi.loc[dates]
    logF, logF1, used = tenor_logprices(A, cols, days, dates, TENOR_LO, TENOR_HI)
    print(f"  reports {dates[0]}..{dates[-1]}: {len(dates)}; strip sessions {days[0]}..{days[-1]}; strip price present on {int(np.isfinite(logF).sum())} reports")

    # ---- audits ----
    audits = {}
    logF_b = tenor_logprices_pandas(strip, days, dates, TENOR_LO, TENOR_HI)
    def audit_tenor(a, b):
        ok = np.isfinite(a) & np.isfinite(b)
        if (np.isfinite(a) != np.isfinite(b)).any() or not np.allclose(a[ok], b[ok], atol=1e-12):
            raise AssertionError("TENOR AUDIT: the two strip paths disagree")
        return int(ok.sum())
    audits["tenor_reports_checked"] = audit_tenor(logF, logF_b)
    R61._expect_raise(lambda: audit_tenor(logF, np.roll(logF_b, 1)), "tenor audit on a shifted path"); audits["tenor_audit_raises_on_shift"] = True
    short = {c: piv["short"][CATS[c]].to_numpy(float) for c in ("PM", "SD", "MM")}; long_ = {c: piv["long"][CATS[c]].to_numpy(float) for c in ("PM", "SD", "MM")}
    short["PM+SD"] = short["PM"] + short["SD"]; long_["PM+SD"] = long_["PM"] + long_["SD"]
    def dl(v, h):
        out = np.full(v.size, np.nan); out[h:] = v[h:] - v[:-h]; return out
    dF = {h: dl(logF, h) for h in HS}; dF1 = {h: dl(logF1, h) for h in HS}
    # synthetic-flow check: a fabricated short = 1000 x dF + noise recovers +1000; its negation -1000; the OLS audit raises on a negated regressor
    rng = np.random.default_rng(577); fake = 1000.0 * dF[H_PRIMARY] + rng.normal(0, 50, dF[H_PRIMARY].size)
    b_fake = audit_ols(fake, dF[H_PRIMARY], NW_LAG)[0]; b_neg = audit_ols(-fake, dF[H_PRIMARY], NW_LAG)[0]
    if not (900 < b_fake < 1100 and -1100 < b_neg < -900):
        raise AssertionError(f"SYNTHETIC-FLOW CHECK: {b_fake} {b_neg}")
    audits["synthetic_flow_beta"] = b_fake; audits["synthetic_flow_negated_beta"] = b_neg
    def bad_audit():
        a = nw_ols(fake, dF[H_PRIMARY], NW_LAG); b = nw_ols_numpy(fake, -dF[H_PRIMARY], NW_LAG)
        if not np.isclose(a[0], b[0], rtol=1e-9):
            raise AssertionError("mismatch")
    R61._expect_raise(bad_audit, "OLS audit on a negated regressor"); audits["ols_audit_raises_on_negated_regressor"] = True
    ks0, null0 = shift_null(short["SD"][H_PRIMARY:] - short["SD"][:-H_PRIMARY], dF[H_PRIMARY][H_PRIMARY:], SHIFT_MIN); audits["shift_null_offsets"] = int(ks0.size)
    print(f"  audits: {audits}")

    # ---- T1 / T2 per category and horizon ----
    res_t1 = {}; res_t2 = {}
    for c in ("PM", "SD", "PM+SD"):
        res_t1[c] = {}; res_t2[c] = {}
        for h in HS:
            y = dl(short[c], h); ynet = dl(short[c] - long_[c], h); x = dF[h]; x1 = dF1[h]
            b, t, n = audit_ols(y, x, h); bn, tn, _ = audit_ols(ynet, x, h); b1, t1_, _ = audit_ols(y, x1, h)
            # non-overlapping: every h-th report
            sel = np.arange(y.size) % h == 0; bno, tno, nno = nw_ols(y[sel], x[sel], 1)
            ks, nl = shift_null(y, x, SHIFT_MIN)
            res_t1[c][h] = {"beta_short": b, "t_nw": t, "n": n, "beta_net_short": bn, "t_net": tn, "beta_short_on_F1": b1, "t_F1": t1_,
                            "nonoverlap": {"beta": bno, "t": tno, "n": nno}, "null": blk(b, nl)}
            ok = np.isfinite(y) & np.isfinite(x); up = ok & (x > 0); dn = ok & (x < 0)
            bp = beta_only(y[up], x[up]) if up.sum() > 20 else float("nan"); bm = beta_only(y[dn], x[dn]) if dn.sum() > 20 else float("nan")
            # null for the split betas: shift, then split by the shifted regressor's sign
            yy, xx = y[ok], x[ok]; N = yy.size; nlp = []; nlm = []
            for k in range(SHIFT_MIN, N - SHIFT_MIN + 1):
                xr = np.roll(xx, k); nlp.append(beta_only(yy[xr > 0], xr[xr > 0])); nlm.append(beta_only(yy[xr < 0], xr[xr < 0]))
            res_t2[c][h] = {"beta_rallies": bp, "n_rallies": int(up.sum()), "beta_declines": bm, "n_declines": int(dn.sum()), "asymmetric": bool(np.isfinite(bp) and np.isfinite(bm) and bp > bm),
                            "null_rallies": blk(bp, np.array(nlp)), "null_declines": blk(bm, np.array(nlm))}
        r = res_t1[c][H_PRIMARY]; q = res_t2[c][H_PRIMARY]
        print(f"  T1 {c:6s} h4: beta_short {r['beta_short']:+,.0f} contracts/log-point (NW t {r['t_nw']:+.2f}, n {r['n']}) rank {r['null']['pct_rank']:.3f} [p05 {r['null']['p05']:+,.0f} p95 {r['null']['p95']:+,.0f}]; "
              f"net-short beta {r['beta_net_short']:+,.0f} (t {r['t_net']:+.2f}); on F1 {r['beta_short_on_F1']:+,.0f} (t {r['t_F1']:+.2f}); non-overlap {r['nonoverlap']['beta']:+,.0f} (t {r['nonoverlap']['t']:+.2f})")
        print(f"     T2 {c:6s} h4: rallies {q['beta_rallies']:+,.0f} (n {q['n_rallies']}, rank {q['null_rallies']['pct_rank']:.2f}) declines {q['beta_declines']:+,.0f} (n {q['n_declines']}, rank {q['null_declines']['pct_rank']:.2f}) -> {'asymmetric' if q['asymmetric'] else 'symmetric'}")
    bSD, bPM = res_t1["SD"][H_PRIMARY]["beta_short"], res_t1["PM"][H_PRIMARY]["beta_short"]
    share_SD = 1.0 if bPM <= 0 else (bSD / (bSD + bPM) if (bSD + bPM) > 0 else float("nan"))
    print(f"  SD share of the hedger response: {share_SD:.2f}")

    # ---- T3 calendar (P6) with a rotated-mask null ----
    months = np.array([int(d[5:7]) for d in dates]); weeks = np.arange(len(dates))
    res_t3 = {}
    for c in ("PM", "SD", "PM+SD"):
        y = dl(short[c], 1); ok = np.isfinite(y); mask = np.isin(months, CAL_MONTHS)
        obs = float(y[ok & mask].mean() - y[ok & ~mask].mean())
        # rotate the calendar mask by k weeks, 1..51, over the whole series (weekly reports: 52 offsets a year)
        nl = []
        for k in range(1, 52):
            mr = np.roll(mask, k); nl.append(float(y[ok & mr].mean() - y[ok & ~mr].mean()))
        nl = np.array(nl)
        res_t3[c] = {"mean_dshort_pre_redetermination": float(y[ok & mask].mean()), "mean_dshort_other": float(y[ok & ~mask].mean()), "difference": obs, "n_pre": int((ok & mask).sum()),
                     "null": blk(obs, nl)}
        print(f"  T3 {c:6s}: dshort/week pre-redetermination {res_t3[c]['mean_dshort_pre_redetermination']:+,.0f} vs other {res_t3[c]['mean_dshort_other']:+,.0f}; diff {obs:+,.0f} rank {res_t3[c]['null']['pct_rank']:.2f}")

    # ---- T4 scale, levels, natural experiments ----
    F_mean = float(np.exp(np.nanmean(logF)))
    per_usd = {c: res_t1[c][H_PRIMARY]["beta_short"] / F_mean for c in ("PM", "SD", "PM+SD")}     # contracts per $1 (d log F = dF/F)
    years = sorted(set(d[:4] for d in dates))
    levels = {c: {y: {"short": float(np.mean(short[c][[d[:4] == y for d in dates]])), "long": float(np.mean(long_[c][[d[:4] == y for d in dates]])),
                      "net_short": float(np.mean((short[c] - long_[c])[[d[:4] == y for d in dates]]))} for y in years} for c in ("PM", "SD")}
    strip_by_year = {y: float(np.exp(np.nanmean(logF[[d[:4] == y for d in dates]]))) for y in years}
    t4 = {"mean_strip_usd": F_mean, "contracts_per_usd_over_4_reports": per_usd, "prior_contracts_per_usd": PRIOR_CONTRACTS_PER_USD,
          "within_3x_of_prior": bool(PRIOR_CONTRACTS_PER_USD[0] / 3 <= per_usd["PM+SD"] <= PRIOR_CONTRACTS_PER_USD[1] * 3),
          "mean_short_contracts": {c: float(np.mean(short[c])) for c in ("PM", "SD")}, "mean_net_short_contracts": {c: float(np.mean(short[c] - long_[c])) for c in ("PM", "SD")},
          "surveyed_hedged_contracts_12m": [380_000, 950_000], "levels_by_year": levels, "strip_by_year": strip_by_year}
    print(f"  T4: mean strip ${F_mean:.0f}; response PM+SD {per_usd['PM+SD']:+,.0f} contracts per $1 (SD {per_usd['SD']:+,.0f}, PM {per_usd['PM']:+,.0f}) vs prior {PRIOR_CONTRACTS_PER_USD}; "
          f"mean short SD {t4['mean_short_contracts']['SD']:,.0f} PM {t4['mean_short_contracts']['PM']:,.0f}; net short SD {t4['mean_net_short_contracts']['SD']:+,.0f} PM {t4['mean_net_short_contracts']['PM']:+,.0f}")
    print("  levels by year (SD net short / PM net short / strip $): " + " ".join(f"{y}:{levels['SD'][y]['net_short']/1e3:+.0f}k/{levels['PM'][y]['net_short']/1e3:+.0f}k/${strip_by_year[y]:.0f}" for y in years))

    # ---- T5 the other side ----
    mm_net_long = long_["MM"] - short["MM"]; mm_share = mm_net_long / oi.to_numpy(float)
    d_mm = dl(mm_net_long, H_PRIMARY); d_hedge = dl(short["PM+SD"], H_PRIMARY); okm = np.isfinite(d_mm) & np.isfinite(d_hedge)
    t5 = {"mm_net_long_share_mean": float(np.nanmean(mm_share)), "mm_net_long_positive_share_of_reports": float((mm_net_long > 0).mean()),
          "corr_dnetlong_MM_vs_dshort_hedgers_4": float(np.corrcoef(d_mm[okm], d_hedge[okm])[0, 1]), "n": int(okm.sum())}
    print(f"  T5: MM net long share {t5['mm_net_long_share_mean']:+.3f} (positive on {t5['mm_net_long_positive_share_of_reports']:.2f} of reports); corr(dMM net long, d hedger short) {t5['corr_dnetlong_MM_vs_dshort_hedgers_4']:+.2f}")

    # ---- the decision rule ----
    sd = res_t1["SD"][H_PRIMARY]; pm = res_t1["PM"][H_PRIMARY]
    sd_holds = bool(sd["beta_short"] > 0 and sd["null"]["above_p95"] and share_SD >= 0.6)
    pm_holds = bool(pm["beta_short"] > 0 and pm["null"]["above_p95"])
    sd_asym = res_t2["SD"][H_PRIMARY]["asymmetric"]
    verdict = ("P9 SUPPORTED" if (sd_holds and sd_asym) else "P9 SUPPORTED ON RESPONSE, NOT ASYMMETRY" if sd_holds else
               "PRODUCER/MERCHANT-DOMINANT" if (pm_holds and not sd_holds) else "NEITHER CATEGORY RESPONDS")
    preds = {"T1_SD_positive_above_p95": bool(sd["beta_short"] > 0 and sd["null"]["above_p95"]), "T1_SD_t_ge_2": bool(sd["t_nw"] >= 2), "T1_SD_share_ge_0.6": bool(share_SD >= 0.6), "SD_share": share_SD,
             "T2_SD_asymmetric": sd_asym, "T2_SD_declines_inside_null": res_t2["SD"][H_PRIMARY]["null_declines"]["inside"],
             "T3_SD_positive_and_gt_PM": bool(res_t3["SD"]["difference"] > 0 and res_t3["SD"]["difference"] > res_t3["PM"]["difference"]),
             "T4_within_3x_prior": t4["within_3x_of_prior"], "T5_MM_net_long": bool(t5["mm_net_long_share_mean"] > 0), "T5_MM_takes_other_side": bool(t5["corr_dnetlong_MM_vs_dshort_hedgers_4"] < 0)}
    print(f"\n  predictions: {preds}\n  VERDICT {verdict}")
    res = {"design": "D577", "windows": {"reports": [dates[0], dates[-1]], "n_reports": len(dates), "reserved_from": RESERVED_FROM, "strip_sessions": [str(days[0]), str(days[-1])]},
           "construction": {"tenor": [TENOR_LO, TENOR_HI], "h_primary": H_PRIMARY, "nw_lag": NW_LAG, "shift_min": SHIFT_MIN, "calendar_months": list(CAL_MONTHS), "no_return_computed": True},
           "audits": audits, "T1": res_t1, "T2": res_t2, "SD_share": share_SD, "T3": res_t3, "T4": t4, "T5": t5, "predictions": preds, "verdict": verdict, "timing": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    print(f"  -> {OUT.relative_to(REPO)}  ({res['timing']}s)")


if __name__ == "__main__":
    main()
