"""D578 post-mortem: why the in-sample swap-dealer net-short response (+71k a log-point, t 3.7) did not transfer.

Reads only what D577 and D578 already read (the CL disaggregated reports and the 12-24-month strip, in sample and
the 139 forward reports that D578 spent). Computes no return, tests nothing new: it decomposes the in-sample
statistic (by year, era, leverage, leg, statistic family, power) and puts the forward slice beside each cut.
Output data/d578_postmortem.json.
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
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m)
    return m


R78 = _load("d578", "run_d578_sd_net_short_forward.py")
R77, R64, R56, R55, R62 = R78.R77, R78.R64, R78.R56, R78.R55, R78.R62
OUT = REPO / "data" / "d578_postmortem.json"
ROOT = "CL"; H = 8
dl = R78.dl


def ols(y, x, lag):
    ok = np.isfinite(y) & np.isfinite(x)
    if ok.sum() < 12:
        return {"beta": None, "t": None, "n": int(ok.sum())}
    b, t, n = R77.nw_ols(y, x, lag); return {"beta": float(b), "t": float(t), "n": int(n)}


def beta(y, x):
    ok = np.isfinite(y) & np.isfinite(x)
    return float(R77.beta_only(y[ok], x[ok])) if ok.sum() > 5 else None


def series(cot, days, A, cols, lo, hi):
    c = cot[(cot["report_date"] >= lo) & (cot["report_date"] <= hi)]
    piv = c.pivot_table(index="report_date", columns="category", values=["long", "short"], aggfunc="first").sort_index()
    dates = [d for d in piv.index if d >= str(days[0])]; piv = piv.loc[dates]
    logF, logF1, _ = R77.tenor_logprices(A, cols, days, dates, R78.TENOR_LO, R78.TENOR_HI)
    g = lambda side, cat: piv[side][cat].to_numpy(float)
    return {"dates": np.array(dates), "logF": logF, "logF1": logF1,
            "sd_short": g("short", "swap_dealer"), "sd_long": g("long", "swap_dealer"),
            "pm_short": g("short", "producer_merchant"), "pm_long": g("long", "producer_merchant"),
            "mm_long": g("long", "managed_money"), "mm_short": g("short", "managed_money")}


def cuts(S, label, log):
    """Every decomposition of the h=8 net-short response on one slice."""
    d = S["dates"]; x = dl(S["logF"], H); ns = S["sd_short"] - S["sd_long"]; y = dl(ns, H)
    ok = np.isfinite(x) & np.isfinite(y); xx, yy, dd = x[ok], y[ok], d[ok]
    years = np.array([int(s[:4]) for s in dd])
    out = {"n": int(ok.sum()), "reports": [str(d[0]), str(d[-1])]}
    # the headline with the NW lag that the overlap needs
    out["beta_by_nw_lag"] = {str(L): ols(y, x, L) for L in (4, 8, 16, 26)}
    ks, nl = R77.shift_null(y, x, R78.SHIFT_MIN); out["shift_null_net_short"] = R77.blk(beta(y, x), nl)
    # non-overlapping, every phase
    ph = []
    for p in range(H):
        sel = np.arange(y.size) % H == p; o = ols(np.where(sel, y, np.nan), x, 0); ph.append(o)
    bs = [p["beta"] for p in ph if p["beta"] is not None]
    out["nonoverlap_phases"] = {"betas": bs, "min": min(bs), "max": max(bs), "mean": float(np.mean(bs)), "n_per_phase": ph[0]["n"], "share_positive": float(np.mean(np.array(bs) > 0))}
    # rank and robust slopes
    out["spearman_rho"] = float(stats.spearmanr(xx, yy).correlation); out["pearson_r"] = float(np.corrcoef(xx, yy)[0, 1])
    out["sign_agreement"] = float(np.mean(np.sign(xx) == np.sign(yy)))
    ts = stats.theilslopes(yy, xx); out["theil_sen_slope"] = float(ts[0]); out["theil_sen_ci90"] = [float(ts[2]), float(ts[3])]
    rlm = sm.RLM(yy, sm.add_constant(xx), M=sm.robust.norms.HuberT()).fit(); out["huber_slope"] = float(rlm.params[1])
    # contribution by year and leave-one-year-out
    xc, yc = xx - xx.mean(), yy - yy.mean(); contrib = xc * yc; Sxx = float((xc * xc).sum()); Sxy = float(contrib.sum())
    by_year = {}
    for yv in sorted(set(years)):
        m = years == yv
        by_year[str(yv)] = {"n": int(m.sum()), "share_of_Sxy": float(contrib[m].sum() / Sxy), "share_of_Sxx": float((xc[m] ** 2).sum() / Sxx),
                            "within_year_beta": beta(yy[m], xx[m]), "mean_abs_x": float(np.abs(xx[m]).mean()),
                            "loyo_beta": beta(yy[~m], xx[~m])}
    out["by_year"] = by_year
    # eras
    eras = {"2010-2014": (2010, 2014), "2015-2019": (2015, 2019), "2020-2023": (2020, 2023), "2010-2016": (2010, 2016), "2017-2023": (2017, 2023), "2024-2026": (2024, 2026)}
    out["by_era"] = {}
    for k, (a, b) in eras.items():
        m = (years >= a) & (years <= b)
        if m.sum() > 20:
            o = ols(np.where(m, y[ok], np.nan), x[ok], H); o["spearman"] = float(stats.spearmanr(xx[m], yy[m]).correlation); out["by_era"][k] = o
    # rolling three-year beta
    W = 156; rb = [beta(yy[i:i + W], xx[i:i + W]) for i in range(0, yy.size - W + 1, 4)]
    if rb:
        rb = np.array(rb); out["rolling_3y_beta"] = {"n_windows": int(rb.size), "min": float(rb.min()), "max": float(rb.max()), "share_positive": float((rb > 0).mean()), "share_above_30k": float((rb > 30_000).mean())}
    # leverage: the largest |x| windows
    order = np.argsort(-np.abs(xx)); top = order[:10]
    out["top10_abs_x"] = [{"date": str(dd[i]), "x": float(xx[i]), "y": float(yy[i]), "share_of_Sxy": float(contrib[i] / Sxy), "share_of_Sxx": float(xc[i] ** 2 / Sxx)} for i in top]
    q95 = np.percentile(np.abs(xx), 95); m = np.abs(xx) <= q95
    out["beta_ex_top5pct_abs_x"] = {"beta": beta(yy[m], xx[m]), "n": int(m.sum()), "cut": float(q95)}
    ci = np.argsort(-contrib)[: int(0.05 * yy.size)]; m = np.ones(yy.size, bool); m[ci] = False
    out["beta_ex_top5pct_contrib"] = {"beta": beta(yy[m], xx[m]), "n": int(m.sum()), "share_removed": float(contrib[ci].sum() / Sxy)}
    for cut in (0.05, 0.10, 0.15, 0.20):
        m = np.abs(xx) <= cut; o = ols(np.where(m, y[ok], np.nan), x[ok], H); o["spearman"] = float(stats.spearmanr(xx[m], yy[m]).correlation) if m.sum() > 12 else None
        out[f"beta_abs_x_le_{cut:.2f}"] = o
    out["abs_x_quantiles"] = {q: float(np.percentile(np.abs(xx), q)) for q in (50, 75, 90, 95, 99)}; out["max_abs_x"] = float(np.abs(xx).max())
    # the windows that carry the covariance, dated
    tc = np.argsort(-contrib)[:12]
    out["top12_contribution"] = [{"date": str(dd[i]), "x": float(xx[i]), "y": float(yy[i]), "share_of_Sxy": float(contrib[i] / Sxy)} for i in tc]
    # rolling three-year beta sampled at each year end (window ending there)
    out["rolling_3y_beta_at_year_end"] = {}
    for yv in sorted(set(years)):
        last = np.flatnonzero(years == yv)[-1]
        if last + 1 >= W:
            out["rolling_3y_beta_at_year_end"][str(yv)] = beta(yy[last + 1 - W:last + 1], xx[last + 1 - W:last + 1])
    # the last five in-sample years on their own, with their own shift null
    m = years >= years.max() - 4
    if m.sum() > 60:
        ks5, nl5 = R77.shift_null(np.where(m, y[ok], np.nan), x[ok], R78.SHIFT_MIN); o = ols(np.where(m, y[ok], np.nan), x[ok], H); o["shift_null"] = R77.blk(o["beta"], nl5); o["years"] = [int(years.max() - 4), int(years.max())]
        out["last_five_years"] = o
    # legs: short and long separately (net = short - long), overall and by era
    out["legs_h8"] = {leg: ols(dl(S[leg], H), x, H) for leg in ("sd_short", "sd_long", "pm_short", "pm_long", "mm_long", "mm_short")}
    out["legs_by_era"] = {}
    for k, (a, b) in eras.items():
        me = (years >= a) & (years <= b)
        if me.sum() > 20:
            out["legs_by_era"][k] = {leg: ols(np.where(me, dl(S[leg], H)[ok], np.nan), x[ok], H)["beta"] for leg in ("sd_short", "sd_long", "pm_short", "pm_long", "mm_short", "mm_long")}
    out["legs_h8"]["sd_net"] = ols(y, x, H); out["legs_h8"]["pm_net"] = ols(dl(S["pm_short"] - S["pm_long"], H), x, H)
    out["legs_h8"]["mm_net_long"] = ols(dl(S["mm_long"] - S["mm_short"], H), x, H)
    # levels by year
    lv = {}
    for yv in sorted(set(int(s[:4]) for s in d)):
        m = np.array([s[:4] == str(yv) for s in d])
        lv[str(yv)] = {k: float(np.nanmean(S[k][m])) for k in ("sd_short", "sd_long", "pm_short", "pm_long", "mm_long", "mm_short")}
        lv[str(yv)]["sd_net"] = lv[str(yv)]["sd_short"] - lv[str(yv)]["sd_long"]; lv[str(yv)]["pm_net"] = lv[str(yv)]["pm_short"] - lv[str(yv)]["pm_long"]
        lv[str(yv)]["strip_usd"] = float(np.exp(np.nanmean(S["logF"][m]))); lv[str(yv)]["n"] = int(m.sum())
    out["levels_by_year"] = lv
    yrs = sorted(lv); out["level_corr_yearly_sd_net_vs_strip"] = float(np.corrcoef([lv[k]["sd_net"] for k in yrs], [np.log(lv[k]["strip_usd"]) for k in yrs])[0, 1]) if len(yrs) > 3 else None
    out["level_52w"] = ols(dl(ns, 52), dl(S["logF"], 52), 52)
    log(f"  [{label}] n {out['n']}  beta {out['beta_by_nw_lag']['4']['beta']:+,.0f} t(lag4) {out['beta_by_nw_lag']['4']['t']:+.2f} t(lag8) {out['beta_by_nw_lag']['8']['t']:+.2f} t(lag16) {out['beta_by_nw_lag']['16']['t']:+.2f}  "
        f"shift-null rank {out['shift_null_net_short']['pct_rank']:.3f} p95 {out['shift_null_net_short']['p95']:+,.0f}  spearman {out['spearman_rho']:+.3f} theil-sen {out['theil_sen_slope']:+,.0f} huber {out['huber_slope']:+,.0f}  "
        f"non-overlap phases {out['nonoverlap_phases']['min']:+,.0f}..{out['nonoverlap_phases']['max']:+,.0f} ({out['nonoverlap_phases']['share_positive']:.0%} positive)")
    log("    contribution by year: " + " ".join(f"{k}:{v['share_of_Sxy']:+.0%}(b{(v['within_year_beta'] or 0)/1e3:+.0f}k)" for k, v in by_year.items()))
    log("    eras: " + " | ".join(f"{k} b {v['beta']:+,.0f} t {v['t']:+.2f} rho {v['spearman']:+.2f}" for k, v in out["by_era"].items()))
    log("    top |x| windows: " + " ".join(f"{t['date']}({t['x']:+.2f}:{t['share_of_Sxy']:+.0%})" for t in out["top10_abs_x"][:6]))
    log(f"    ex top5% |x| {out['beta_ex_top5pct_abs_x']['beta']:+,.0f}; ex top5% contrib {out['beta_ex_top5pct_contrib']['beta']:+,.0f} (removed {out['beta_ex_top5pct_contrib']['share_removed']:.0%} of Sxy); "
        + " ".join(f"|x|<={c:.2f}: {out[f'beta_abs_x_le_{c:.2f}']['beta']:+,.0f}(t {out[f'beta_abs_x_le_{c:.2f}']['t']:+.2f})" for c in (0.05, 0.10, 0.15, 0.20) if out[f'beta_abs_x_le_{c:.2f}']['beta'] is not None))
    log("    top contribution windows: " + " ".join(f"{t['date']}({t['x']:+.2f}:{t['share_of_Sxy']:+.0%})" for t in out["top12_contribution"][:8]))
    log("    rolling 3y beta at year end: " + " ".join(f"{k}:{v/1e3:+.0f}k" for k, v in out["rolling_3y_beta_at_year_end"].items()))
    if "last_five_years" in out:
        o = out["last_five_years"]; log(f"    last five years {o['years']}: beta {o['beta']:+,.0f} t {o['t']:+.2f} rank {o['shift_null']['pct_rank']:.3f} p95 {o['shift_null']['p95']:+,.0f}")
    log("    legs by era: " + " | ".join(f"{k}: " + " ".join(f"{leg} {v/1e3:+.0f}k" for leg, v in legs.items() if v is not None) for k, legs in out["legs_by_era"].items()))
    log("    legs h8: " + " ".join(f"{k} {v['beta']:+,.0f}(t {v['t']:+.2f})" for k, v in out["legs_h8"].items() if v["beta"] is not None))
    log("    levels: " + " ".join(f"{k}: SDs {v['sd_short']/1e3:.0f}k SDl {v['sd_long']/1e3:.0f}k net {v['sd_net']/1e3:+.0f}k PMnet {v['pm_net']/1e3:+.0f}k ${v['strip_usd']:.0f}" for k, v in lv.items()))
    return out


def main():
    t0 = time.time(); log = print
    log("D578 POST-MORTEM -- decomposing the in-sample SD net-short response and putting the spent forward slice beside it; no return computed")
    cot = pd.read_csv(R77.COT, encoding="utf-8", dtype={"code": str}); cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "disaggregated")].copy()
    df = R62.load_fixture_forward(); live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start); days = g["days"]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[strip["root"] == ROOT]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]
    S_in = series(cot, days, A, cols, "2010-06-01", "2023-12-31"); S_fw = series(cot, days, A, cols, "2024-01-01", "2099-12-31"); S_all = series(cot, days, A, cols, "2010-06-01", "2099-12-31")
    # harness: the in-sample beta equals D578's harness
    art = json.loads((REPO / "data" / "d578_sd_net_short_forward.json").read_text(encoding="utf-8"))
    b8 = R77.audit_ols(dl(S_in["sd_short"] - S_in["sd_long"], H), dl(S_in["logF"], H), H)[0]
    if abs(b8 - art["harness"]["beta_sd_net_8_rebuilt"]) > 1e-6:
        raise AssertionError("harness: in-sample beta differs from D578's")
    res = {"harness_in_sample_beta_8": b8, "in_sample": cuts(S_in, "in-sample 2010-2023", log), "forward": cuts(S_fw, "forward 2024-2026 (spent, D578)", log)}
    # the pooled series: does the forward look like a continuation of the late in-sample?
    res["pooled_2017_2026"] = {}
    d = S_all["dates"]; m = np.array([s >= "2017-01-01" for s in d]); x = dl(S_all["logF"], H); y = dl(S_all["sd_short"] - S_all["sd_long"], H)
    res["pooled_2017_2026"]["sd_net_h8"] = ols(np.where(m, y, np.nan), x, H)
    # the statistic family D577 reported (multiplicity of the 'beside' pick)
    a77 = json.loads((REPO / "data" / "stage0_d577_cl_p9.json").read_text(encoding="utf-8")); fam = []
    for cat, hs in a77["T1"].items():
        for h, v in hs.items():
            fam += [{"stat": f"{cat} gross short h{h}", "t": v["t_nw"]}, {"stat": f"{cat} net short h{h}", "t": v["t_net"]}, {"stat": f"{cat} gross short on F1 h{h}", "t": v["t_F1"]}]
    fam.sort(key=lambda r: -abs(r["t"]))
    res["d577_family"] = {"n_statistics": len(fam), "n_abs_t_ge_2": int(sum(abs(r["t"]) >= 2 for r in fam)), "top": fam[:6], "declared_primary": "SD gross short h4 (t 1.22)", "picked_beside": "SD net short h8 (t 3.71, never ranked against its own shift null in D577)"}
    # power: what forward t the in-sample effect would have produced on 131 reports, and whether the forward point rejects it
    tin = res["in_sample"]["beta_by_nw_lag"]["4"]["t"]; nin = res["in_sample"]["n"]; nfw = res["forward"]["n"]
    bfw, tfw = res["forward"]["beta_by_nw_lag"]["4"]["beta"], res["forward"]["beta_by_nw_lag"]["4"]["t"]; se_fw = abs(bfw / tfw)
    res["power"] = {"expected_forward_t_if_effect_equal": float(tin * np.sqrt(nfw / nin)), "forward_se": se_fw, "forward_ci90": [bfw - 1.645 * se_fw, bfw + 1.645 * se_fw],
                    "z_forward_vs_in_sample_beta": float((bfw - b8) / se_fw), "note": "the pre-registered bar (t >= 2) exceeded the expected t even for an unchanged effect; the point estimate nonetheless rejects the in-sample beta"}
    log(f"  power: an unchanged effect would give forward t ~{res['power']['expected_forward_t_if_effect_equal']:.2f} on {nfw} reports (bar was 2); forward 90% CI [{res['power']['forward_ci90'][0]:+,.0f}, {res['power']['forward_ci90'][1]:+,.0f}] vs in-sample {b8:+,.0f}: z {res['power']['z_forward_vs_in_sample_beta']:+.2f}")
    log(f"  D577 family: {res['d577_family']['n_statistics']} betas reported, {res['d577_family']['n_abs_t_ge_2']} with |t|>=2; top: " + "; ".join(f"{r['stat']} t {r['t']:+.2f}" for r in fam[:4]))
    log(f"  pooled 2017-2026 SD net h8: beta {res['pooled_2017_2026']['sd_net_h8']['beta']:+,.0f} t {res['pooled_2017_2026']['sd_net_h8']['t']:+.2f} n {res['pooled_2017_2026']['sd_net_h8']['n']}")
    res["timing_s"] = round(time.time() - t0, 1); res["no_return_computed"] = True
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")


if __name__ == "__main__":
    main()
