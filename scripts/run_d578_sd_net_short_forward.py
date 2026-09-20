"""D578 -- the corrected hedging-flow mapping tested once on the 2024+ CL disaggregated reports, on the principal's word
(spec committed before this runner, R8). Refuses without --principals-word.

Swap-dealer NET short of CL against the 12-24-month strip at eight weeks (h = 4 beside), the ratchet split, the calendar
clause, the producer/merchant net short as the other side, the gross short beside, the two forward episodes the derivation
names, and the scale question. Harness first: the in-sample betas on 2010-2023 recomputed by the same code must equal D577's
artifact to 1e-6. No return is computed anywhere.

    python scripts/run_d578_sd_net_short_forward.py --run --principals-word
"""
from __future__ import annotations

import argparse
import importlib.util
import json
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


R77 = _load("d577", "stage0_d577_cl_hedging_flow_p9.py")   # tenor_logprices(+pandas), nw_ols(+numpy), audit_ols, beta_only, shift_null, blk
R64, R61, R56, R55 = R77.R64, R77.R61, R77.R56, R77.R55
R62 = _load("d562", "run_d562_trend_forward_read.py")        # the forward session calendar

OUT = REPO / "data" / "d578_sd_net_short_forward.json"
ART_D577 = REPO / "data" / "stage0_d577_cl_p9.json"
SPEC = "5f0cfcd"                                               # the pre-registration commit (R8)
ROOT = "CL"
FWD_FROM, IN_TO = "2024-01-01", R55.RESERVED_FROM
TENOR_LO, TENOR_HI = R77.TENOR_LO, R77.TENOR_HI
H_PRIMARY, H_SECOND = 8, 4
SHIFT_MIN = 8
CAL_MONTHS = R77.CAL_MONTHS
EPISODES = {"june_2025_rally": "2025-06-13", "march_2026_spike": "2026-03-01"}
POINT_RANGE = (30_000, 110_000)
IN_SAMPLE_PER_USD = 1_060.0
PRIOR_PER_USD = (18_000, 37_000)


def dl(v, h):
    out = np.full(v.size, np.nan); out[h:] = v[h:] - v[:-h]; return out


def series_on(cot, days, A, cols, lo_date, hi_date):
    """Per-report arrays on the reports in [lo_date, hi_date]: net short SD/PM, gross short SD, the strip and F1 log prices."""
    c = cot[(cot["report_date"] >= lo_date) & (cot["report_date"] <= hi_date)]
    piv = c.pivot_table(index="report_date", columns="category", values=["long", "short"], aggfunc="first").sort_index()
    dates = [d for d in piv.index if d >= str(days[0])]; piv = piv.loc[dates]
    logF, logF1, _ = R77.tenor_logprices(A, cols, days, dates, TENOR_LO, TENOR_HI)
    ns_sd = (piv["short"]["swap_dealer"] - piv["long"]["swap_dealer"]).to_numpy(float)
    ns_pm = (piv["short"]["producer_merchant"] - piv["long"]["producer_merchant"]).to_numpy(float)
    gs_sd = piv["short"]["swap_dealer"].to_numpy(float)
    return dates, logF, logF1, ns_sd, ns_pm, gs_sd


def run(principals_word, log=print):
    t0 = time.time()
    if not principals_word:
        log("REFUSED: --run reads the reserved CL 2024+ disaggregated reports and settlements; re-run with --principals-word only on the principal's word."); return 2
    instruction = "the principal, 2026-09-20: 'Pre-register the corrected mapping on the 2024+ reports and run it'"
    log(f"D578 -- the corrected hedging-flow mapping on the 2024+ reports, under {instruction}")
    cot = pd.read_csv(R77.COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["symbol"] == ROOT) & (cot["family"] == "disaggregated")].copy()
    df = R62.load_fixture_forward(); live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start); days = g["days"]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[strip["root"] == ROOT]
    A, cols = R64.strip_tables(strip, days, [ROOT])[ROOT]

    # ---- harness: the in-sample betas by this code equal D577's artifact ----
    d_in, F_in, F1_in, sd_in, pm_in, gs_in = series_on(cot, days, A, cols, "2010-06-01", "2023-12-31")
    art = json.loads(ART_D577.read_text(encoding="utf-8"))
    b8 = R77.audit_ols(dl(sd_in, 8), dl(F_in, 8), 8)[0]; b4 = R77.audit_ols(dl(sd_in, 4), dl(F_in, 4), 4)[0]
    ref8, ref4 = art["T1"]["SD"]["8"]["beta_net_short"], art["T1"]["SD"]["4"]["beta_net_short"]
    if abs(b8 - ref8) > 1e-6 or abs(b4 - ref4) > 1e-6:
        raise AssertionError(f"HARNESS: in-sample SD net beta {b8}/{b4} vs artifact {ref8}/{ref4}")
    harness = {"in_sample_reports": len(d_in), "beta_sd_net_8_rebuilt": b8, "d577_artifact_8": ref8, "beta_sd_net_4_rebuilt": b4, "d577_artifact_4": ref4, "tolerance": 1e-6}
    log(f"  harness: in-sample SD net beta(8) {b8:+,.0f} = artifact {ref8:+,.0f}; beta(4) {b4:+,.0f} = {ref4:+,.0f}")

    # ---- the forward sample ----
    dates, logF, logF1, ns_sd, ns_pm, gs_sd = series_on(cot, days, A, cols, FWD_FROM, "2099-12-31")
    if dates[0] < FWD_FROM:
        raise AssertionError("an in-sample report leaked into the forward sample")
    N = len(dates)
    log(f"  forward reports {dates[0]}..{dates[-1]}: {N}; strip sessions to {days[-1]}; strip price present on {int(np.isfinite(logF).sum())} reports; mean strip ${np.exp(np.nanmean(logF)):.0f}")
    audits = {}
    logF_b = R77.tenor_logprices_pandas(strip, days, dates, TENOR_LO, TENOR_HI)
    def audit_tenor(a, b):
        ok = np.isfinite(a) & np.isfinite(b)
        if (np.isfinite(a) != np.isfinite(b)).any() or not np.allclose(a[ok], b[ok], atol=1e-12):
            raise AssertionError("TENOR AUDIT")
        return int(ok.sum())
    audits["tenor_reports_checked"] = audit_tenor(logF, logF_b)
    R61._expect_raise(lambda: audit_tenor(logF, np.roll(logF_b, 1)), "tenor audit on a shifted path"); audits["tenor_audit_raises_on_shift"] = True
    dF8, dF4 = dl(logF, 8), dl(logF, 4)
    rng = np.random.default_rng(578); fake = 1000.0 * dF8 + rng.normal(0, 50, dF8.size)
    bf = R77.audit_ols(fake, dF8, 8)[0]; bn = R77.audit_ols(-fake, dF8, 8)[0]
    if not (850 < bf < 1150 and -1150 < bn < -850):
        raise AssertionError(f"SYNTHETIC-FLOW CHECK: {bf} {bn}")
    audits["synthetic_flow_beta"] = bf; audits["synthetic_flow_negated_beta"] = bn
    def bad():
        a = R77.nw_ols(fake, dF8, 8); b = R77.nw_ols_numpy(fake, -dF8, 8)
        if not np.isclose(a[0], b[0], rtol=1e-9):
            raise AssertionError("mismatch")
    R61._expect_raise(bad, "OLS audit on a negated regressor"); audits["ols_audit_raises_on_negated_regressor"] = True

    # ---- C-1, C-2, C-3, C-7: betas with NW t, shift null, non-overlapping sign ----
    def fit(y, x, h):
        b, t, n = R77.audit_ols(y, x, h); ks, nl = R77.shift_null(y, x, SHIFT_MIN)
        sel = np.arange(y.size) % h == 0; ok = np.isfinite(y[sel]) & np.isfinite(x[sel])
        bno = R77.beta_only(y[sel][ok], x[sel][ok]) if ok.sum() > 5 else float("nan")
        return {"beta": b, "t_nw": t, "n": n, "null": R77.blk(b, nl), "nonoverlap_beta": bno, "nonoverlap_n": int(ok.sum())}
    F_mean = float(np.exp(np.nanmean(logF)))
    c1 = fit(dl(ns_sd, 8), dF8, 8); c2 = fit(dl(ns_sd, 4), dF4, 4); c3 = fit(dl(ns_pm, 8), dF8, 8); c7 = fit(dl(gs_sd, 8), dF8, 8)
    c1["per_usd"] = c1["beta"] / F_mean
    log(f"  C-1 SD net short h8: beta {c1['beta']:+,.0f}/log-point (t {c1['t_nw']:+.2f}, n {c1['n']}) rank {c1['null']['pct_rank']:.3f} [p05 {c1['null']['p05']:+,.0f} p50 {c1['null']['p50']:+,.0f} p95 {c1['null']['p95']:+,.0f}]; "
        f"non-overlap {c1['nonoverlap_beta']:+,.0f} (n {c1['nonoverlap_n']}); {c1['per_usd']:+,.0f} contracts per $1")
    log(f"  C-2 SD net short h4: beta {c2['beta']:+,.0f} (t {c2['t_nw']:+.2f}) rank {c2['null']['pct_rank']:.3f};  C-3 PM net short h8: beta {c3['beta']:+,.0f} (t {c3['t_nw']:+.2f}) rank {c3['null']['pct_rank']:.3f};  "
        f"C-7 SD gross short h8: beta {c7['beta']:+,.0f} (t {c7['t_nw']:+.2f})")

    # ---- C-4 the ratchet on the net line ----
    y8, x8 = dl(ns_sd, 8), dF8; ok = np.isfinite(y8) & np.isfinite(x8); up = ok & (x8 > 0); dn = ok & (x8 < 0)
    bp = R77.beta_only(y8[up], x8[up]) if up.sum() > 10 else float("nan"); bm = R77.beta_only(y8[dn], x8[dn]) if dn.sum() > 10 else float("nan")
    yy, xx = y8[ok], x8[ok]; nlp, nlm = [], []
    for k in range(SHIFT_MIN, yy.size - SHIFT_MIN + 1):
        xr = np.roll(xx, k)
        if (xr > 0).sum() > 10 and (xr < 0).sum() > 10:
            nlp.append(R77.beta_only(yy[xr > 0], xr[xr > 0])); nlm.append(R77.beta_only(yy[xr < 0], xr[xr < 0]))
    c4 = {"beta_rallies": bp, "n_rallies": int(up.sum()), "beta_declines": bm, "n_declines": int(dn.sum()), "asymmetric": bool(np.isfinite(bp) and np.isfinite(bm) and bp > bm),
          "null_rallies": R77.blk(bp, np.array(nlp)), "null_declines": R77.blk(bm, np.array(nlm)), "mean_dns_on_rallies": float(y8[up].mean()), "mean_dns_on_declines": float(y8[dn].mean())}
    log(f"  C-4 ratchet: rallies beta {bp:+,.0f} (n {up.sum()}, rank {c4['null_rallies']['pct_rank']:.2f}) declines {bm:+,.0f} (n {dn.sum()}, rank {c4['null_declines']['pct_rank']:.2f}, inside {c4['null_declines']['inside']}); "
        f"mean dNS on rallies {c4['mean_dns_on_rallies']:+,.0f} vs declines {c4['mean_dns_on_declines']:+,.0f} -> {'asymmetric' if c4['asymmetric'] else 'symmetric'}")

    # ---- C-5 the calendar on the net line ----
    y1 = dl(ns_sd, 1); ok1 = np.isfinite(y1); months = np.array([int(d[5:7]) for d in dates]); mask = np.isin(months, CAL_MONTHS)
    obs = float(y1[ok1 & mask].mean() - y1[ok1 & ~mask].mean()); nl = np.array([float(y1[ok1 & np.roll(mask, k)].mean() - y1[ok1 & ~np.roll(mask, k)].mean()) for k in range(1, 52)])
    c5 = {"mean_pre": float(y1[ok1 & mask].mean()), "mean_other": float(y1[ok1 & ~mask].mean()), "difference": obs, "n_pre": int((ok1 & mask).sum()), "null": R77.blk(obs, nl)}
    log(f"  C-5 calendar: dNS/week pre-redetermination {c5['mean_pre']:+,.0f} vs other {c5['mean_other']:+,.0f} (diff {obs:+,.0f}, rank {c5['null']['pct_rank']:.2f})")

    # ---- C-6 scale ----
    c6 = {"per_usd_forward": c1["per_usd"], "in_sample_per_usd": IN_SAMPLE_PER_USD, "within_3x": bool(IN_SAMPLE_PER_USD / 3 <= c1["per_usd"] <= IN_SAMPLE_PER_USD * 3),
          "prior_per_usd": PRIOR_PER_USD, "prior_over_measured": (PRIOR_PER_USD[0] / c1["per_usd"]) if c1["per_usd"] > 0 else None, "gap_persists_10x": bool(c1["per_usd"] <= 0 or PRIOR_PER_USD[0] / c1["per_usd"] >= 10)}

    # ---- C-8 the two forward episodes ----
    all8 = y8[np.isfinite(y8)]; q75 = float(np.percentile(all8, 75)); eps = {}
    for name, start in EPISODES.items():
        j = next((i for i, d in enumerate(dates) if d > start), None)
        if j is None or j + 8 >= N:
            eps[name] = {"start_report": None, "change_8": None, "top_quartile": None, "note": "not enough reports after the episode"}; continue
        ch = float(ns_sd[j + 8] - ns_sd[j]); eps[name] = {"start_report": dates[j], "end_report": dates[j + 8], "change_8": ch, "q75_of_all_8w_changes": q75, "positive": bool(ch > 0), "top_quartile": bool(ch > q75),
                                                           "strip_change_8": float(logF[j + 8] - logF[j]) if np.isfinite(logF[j]) and np.isfinite(logF[j + 8]) else None}
    c8 = {"episodes": eps, "holds": bool(all(v.get("top_quartile") for v in eps.values()))}
    log("  C-8 episodes: " + "; ".join(f"{k}: dNS(8) {v['change_8']:+,.0f} from {v['start_report']} (strip {v['strip_change_8']:+.3f}) top-quartile {v['top_quartile']}" if v.get("change_8") is not None else f"{k}: {v['note']}" for k, v in eps.items()))
    yearly = {y: {"ns_sd_mean": float(np.mean(ns_sd[[d[:4] == y for d in dates]])), "ns_pm_mean": float(np.mean(ns_pm[[d[:4] == y for d in dates]])), "strip_mean_usd": float(np.exp(np.nanmean(logF[[d[:4] == y for d in dates]])))} for y in sorted(set(d[:4] for d in dates))}
    log("  levels by year (SD net short / PM net short / strip $): " + " ".join(f"{y}:{v['ns_sd_mean']/1e3:+.0f}k/{v['ns_pm_mean']/1e3:+.0f}k/${v['strip_mean_usd']:.0f}" for y, v in yearly.items()))

    # ---- predictions and the verdict ----
    preds = {"C-1": {"beta": c1["beta"], "t": c1["t_nw"], "rank": c1["null"]["pct_rank"], "holds": bool(c1["beta"] > 0 and c1["t_nw"] >= 2 and c1["null"]["above_p95"]), "in_point_range": bool(POINT_RANGE[0] <= c1["beta"] <= POINT_RANGE[1])},
             "C-2": {"beta": c2["beta"], "holds": bool(c2["beta"] > 0)},
             "C-3": {"beta": c3["beta"], "t": c3["t_nw"], "holds": bool(c3["beta"] < 0)},
             "C-4": {"holds": bool(c4["asymmetric"] and c4["null_declines"]["inside"]), "asymmetric": c4["asymmetric"], "declines_inside_null": c4["null_declines"]["inside"]},
             "C-5": {"holds": bool(c5["difference"] > 0 and c5["mean_pre"] > 0), "difference": c5["difference"]},
             "C-6": {"holds": bool(c6["within_3x"] and c6["gap_persists_10x"]), "per_usd": c1["per_usd"], "within_3x": c6["within_3x"], "gap_persists_10x": c6["gap_persists_10x"]},
             "C-7": {"holds": bool(c7["beta"] > 0 and c7["beta"] < c1["beta"]), "gross_beta": c7["beta"], "net_beta": c1["beta"]},
             "C-8": {"holds": c8["holds"], **{k: v.get("top_quartile") for k, v in eps.items()}},
             "C-9": {"does_not_transfer": bool(not (c1["beta"] > 0 and c1["null"]["above_p95"])), "netting_fails": bool(c3["beta"] >= 0), "symmetric_response": False}}
    preds["C-9"]["symmetric_response"] = bool(preds["C-1"]["holds"] and not c4["asymmetric"])
    verdict = "TRANSFERS" if (preds["C-1"]["holds"] and preds["C-3"]["holds"]) else "PARTIAL" if preds["C-1"]["holds"] else "DOES NOT TRANSFER"
    log("\n  predictions: " + ", ".join(f"{k} {'holds' if v.get('holds') else 'fails'}" for k, v in preds.items() if k != "C-9") + f"; C-9 {preds['C-9']}")
    log(f"  FORWARD VERDICT {verdict}")
    res = {"spec": "D578", "commit": SPEC, "instruction": instruction, "windows": {"forward_reports": [dates[0], dates[-1]], "n_forward": N, "in_sample_harness": [d_in[0], d_in[-1]], "strip_last_session": str(days[-1])},
           "construction": {"instrument": "swap-dealer net short (short - long), contracts", "regressor": f"mean log settlement of delivery months m+{TENOR_LO}..m+{TENOR_HI}", "h_primary": H_PRIMARY, "h_second": H_SECOND, "nw_lag": H_PRIMARY, "shift_min": SHIFT_MIN, "no_return_computed": True},
           "harness": harness, "audits": audits, "C1_sd_net_8": c1, "C2_sd_net_4": c2, "C3_pm_net_8": c3, "C4_ratchet": c4, "C5_calendar": c5, "C6_scale": c6, "C7_sd_gross_8": c7, "C8_episodes": c8,
           "levels_by_year": yearly, "predictions": preds, "verdict": {"forward": verdict},
           "spent": {"reports": f"CL disaggregated {dates[0]}..{dates[-1]} for the hedging-flow line", "seen": f"the CL 12-24m settlement path to {days[-1]}"}, "timing": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    log(f"\n  -> {OUT}   ({res['timing']}s)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--principals-word", action="store_true")
    a = ap.parse_args()
    sys.exit(run(a.principals_word))
