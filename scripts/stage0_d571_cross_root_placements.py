"""D571 Stage 0 -- the cross-root placement profiles (design committed in D571 before this ran). D570's construction
(a survivable nearby pair, short the nearer, held three months) placed at each of the twelve calendar months on ZC, ZW,
ZL and ZM, with the best placement predicted from the soybean profile; one declared construction a root reported in
full with the twelve placements as its enumerated null. Diagnostic on 2011-2023; nothing from 2024-01-01 on is read.
Writes data/stage0_d571_cross_root.json.

    uv run python -u scripts/stage0_d571_cross_root_placements.py
"""
from __future__ import annotations

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


R70 = _load("d570", "run_d570_soybean_harvest_spread.py")     # fixed_pair_series, pairs_pandas_fixed, audit_survival_fixed, cost helpers
R69, R68, R65, R64, R61, R56, R55 = R70.R69, R70.R68, R70.R65, R70.R64, R70.R61, R70.R56, R70.R55

OUT = REPO / "data" / "stage0_d571_cross_root.json"
ROOTS = ["ZC", "ZW", "ZL", "ZM"]
SOURCE = "ZS"
DECLARED = {"ZC": 7, "ZW": 4, "ZL": 7, "ZM": 7}                                   # the declared construction per root
PRED_SET = {"ZC": {6, 7}, "ZW": {4, 5}, "ZL": {7, 8, 9}, "ZM": {7, 8, 9}}          # predicted best placement
PRED_NEG = {"ZC": [9, 12, 1, 2, 3], "ZW": [1, 2, 3], "ZL": [12, 1, 2, 3, 4], "ZM": [12, 1, 2, 3, 4]}
FALSIFY_OUTSIDE = {"ZC": {5, 6, 7, 8}, "ZW": {3, 4, 5, 6}, "ZL": {6, 7, 8, 9}, "ZM": {6, 7, 8, 9}}
PRIMARY, LONG, RESERVED_FROM = R55.PRIMARY, R55.LONG, R55.RESERVED_FROM
YEARS = list(range(2010, 2024))


def profile(A, cols, days, idx, wP, wL):
    out = {}; series = {}
    for m in range(1, 13):
        r1, r2, dP1, dP2, mask, t1_idx, F1s, recs = R70.fixed_pair_series(A, cols, days, idx, m, YEARS)
        x = np.where(mask, -(r1 - r2), 0.0)
        mret = R68.monthly_returns(x, days, mask & wL)
        wins = {}
        for p, v in mret.items():
            wy = R70.window_year_of(p, m)
            wins[wy] = wins.get(wy, 0.0) + float(v)
        wv = np.array(list(wins.values()))
        out[m] = {"months": [mm for _, mm in R70.hold_months(m)], "pair_first_window": (recs[0]["t1"], recs[0]["t2"]) if recs else None,
                  "sharpe_long": R55.sharpe(x[wL]), "sortino_long": R55.sortino(x[wL]), "sharpe_primary": R55.sharpe(x[wP]), "sortino_primary": R55.sortino(x[wP]),
                  "bp_per_positioned_day_long": float(x[mask & wL].mean() * 1e4) if (mask & wL).any() else None,
                  "windows": int(wv.size), "window_mean": float(wv.mean()) if wv.size else None, "window_hit_short": float((wv > 0).mean()) if wv.size else None}
        series[m] = (r1, r2, dP1, dP2, mask, t1_idx, F1s, recs, x)
    return out, series


def main():
    t_start = time.time()
    print("D571 STAGE 0 -- cross-root placement profiles; design committed before this ran; 2011-2023 only; 2024+ shut on every source")
    df = R55.load_fixture()
    if (df["day"] >= RESERVED_FROM).any():
        raise AssertionError("reserved slice present")
    live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start)
    days = g["days"]; T = len(days); idx = pd.to_datetime(days); me = R55.month_ends(days)
    wP = R55.window_mask(days, *PRIMARY); wL = R55.window_mask(days, *LONG); dP_days, dL_days = days[wP], days[wL]
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < RESERVED_FROM) & strip["root"].isin(ROOTS + [SOURCE])]
    tables = R64.strip_tables(strip, days, ROOTS + [SOURCE])
    upp_all, tick_all, comm_all, size_name = R56.min_size(g, g["roots"])
    meta = json.loads(R55.META.read_text(encoding="utf-8"))["specs"]

    # the source profile, seen (reprinted from its own computation; asserted against D570's artifact)
    A, cols = tables[SOURCE]; src, _ = profile(A, cols, days, idx, wP, wL)
    d570 = json.loads((REPO / "data" / "d570_soybean_harvest_spread.json").read_text(encoding="utf-8"))["null_n2"]["placements"]
    for m in range(1, 13):
        if abs(src[m]["sharpe_primary"] - d570[str(m)]["sharpe_primary"]) > 1e-9:
            raise AssertionError(f"source profile differs from D570 at m{m}")
    src_vec = np.array([src[m]["sharpe_long"] for m in range(1, 13)])
    print("  ZS source profile (Sharpe 2011-23): " + " ".join(f"m{m}:{src[m]['sharpe_long']:+.2f}" for m in range(1, 13)) + "  [reproduces D570's artifact]")

    res = {"max_drawdown_convention": {"sign": "negative",
                                       "note": "Drawdown LEVELS are NEGATIVE: the minimum of (cumulative daily return - its running peak), simple-return units for the "
                                               "return-space blocks, dollars for the one-contract books. Not a fraction of a compounded peak (D542).", "record": "D542"},
           "design": "D571", "source_profile_ZS": src, "roots": {}, "predictions": {}}
    for root in ROOTS:
        A, cols = tables[root]; i = g["roots"].index(root); upp, tick_usd, comm_rt = float(upp_all[i]), float(tick_all[i]), float(comm_all[i])
        if meta[root].get("has_micro", False) or size_name[i] != root:
            raise AssertionError(f"{root} specification: {size_name[i]}")
        prof, series = profile(A, cols, days, idx, wP, wL)
        vec = np.array([prof[m]["sharpe_long"] for m in range(1, 13)])
        best = int(max(prof, key=lambda m: prof[m]["sharpe_long"])); best_p = int(max(prof, key=lambda m: prof[m]["sharpe_primary"]))
        rho = float(pd.Series(vec).corr(pd.Series(src_vec), method="spearman"))
        # the always-on control: the rolled cousin, short, every month
        ra1, ra2, _, _, heldA, t1A, F1A, _ = R68.pair_series(A, cols, days, me); xC = np.where(heldA, -(ra1 - ra2), 0.0)
        ctrl = {"bp_per_day_long": float(xC[heldA & wL].mean() * 1e4), "sharpe_long": R55.sharpe(xC[wL]), "sharpe_primary": R55.sharpe(xC[wP]),
                "by_calendar_month_bp": {m: float(xC[heldA & wL & (idx.month == m)].mean() * 1e4) for m in range(1, 13)}}
        # the declared construction, in full
        m_dec = DECLARED[root]; r1, r2, dP1, dP2, mask, t1_idx, F1s, recs, x = series[m_dec]
        side = comm_rt / 2.0 + 0.5 * tick_usd
        c = R70.cost_series_fixed(mask, F1s, side, upp, T); xn = x - c
        pnl = np.where(mask, -(dP1 - dP2) * upp, 0.0); cost_usd = R70.cost_usd_fixed(mask, side, T); pnl_n = pnl - cost_usd; posP = mask & wP
        mret = R68.monthly_returns(x, days, mask & wP); mretL = R68.monthly_returns(x, days, mask & wL)
        wins = {}
        for p, v in mretL.items():
            wy = R70.window_year_of(p, m_dec); wins[wy] = wins.get(wy, 0.0) + float(v)
        # audits on the declared construction, each proven to raise
        audits = {}
        pb = R70.pairs_pandas_fixed(strip[strip["root"] == root], days, recs, m_dec); audits["pairs_checked"] = R68.audit_pairs(recs, pb)
        R61._expect_raise(lambda: R68.audit_pairs(recs, pb[1:] + pb[:1]), "pair audit on shifted formations"); audits["pair_audit_raises"] = True
        audits["survival_sessions"] = R70.audit_survival_fixed(mask, t1_idx, days, m_dec)
        R61._expect_raise(lambda: R70.audit_survival_fixed(mask, t1A, days, m_dec), "survival audit on the m+2 rule's pair"); audits["survival_raises"] = True
        both = [r["both_settle_at_end"] and r["month_ends_settle"] for r in recs if r["year"] >= 2011]; audits["held_contract_share"] = float(np.mean(both))
        if audits["held_contract_share"] < 1.0:
            raise AssertionError(f"{root}: HELD-CONTRACT AUDIT")
        mask_b = R68.season_mask_pandas(days, tuple(mm for _, mm in R70.hold_months(m_dec))) & mask; audits["lag_mask_sessions"] = R68.audit_mask(mask, mask_b, me)
        form_ix = [np.flatnonzero(days == r["formation"])[0] for r in recs]; bad = mask.copy(); bad[form_ix] = True
        R61._expect_raise(lambda: R68.audit_mask(bad, mask_b, me), "lag audit on a formation-session mask"); audits["lag_raises"] = True
        audits["sign_in_money_session"] = str(days[R65.audit_sign_in_money(pnl, dP1, dP2, mask, upp)])
        R61._expect_raise(lambda: R65.audit_sign_in_money(-pnl, dP1, dP2, mask, upp), "sign audit on a negated grid")
        R61._expect_raise(lambda: R65.audit_sign_in_money(np.roll(pnl, 1), dP1, dP2, mask, upp), "sign audit on a mislagged grid"); audits["sign_raises"] = True
        audits["right_quantity_changes"] = R68.audit_right_quantity(mask, days)
        R61._expect_raise(lambda: R68.audit_right_quantity(np.arange(T) % 2 == 0, days), "right-quantity on a daily grid"); audits["right_quantity_raises"] = True
        declared = {"placement": m_dec, "months": prof[m_dec]["months"], "pair_first_window": prof[m_dec]["pair_first_window"], "usd_per_point": upp, "tick_usd": tick_usd,
                    "gross": R55.stats_block(x[wP], dP_days, f"{root} m{m_dec}"), "net": R55.stats_block(xn[wP], dP_days, f"{root} m{m_dec} net"), "gross_long": R55.stats_block(x[wL], dL_days, f"{root} m{m_dec} 2011-23"),
                    "months": {"n": int(len(mret)), "mean": float(mret.mean()), "median": float(mret.median()), "hit": float((mret > 0).mean()), "worst": float(mret.min()), "best": float(mret.max())} if len(mret) else None,
                    "months_long": {"n": int(len(mretL)), "mean": float(mretL.mean()), "median": float(mretL.median()), "hit": float((mretL > 0).mean()), "worst": float(mretL.min())} if len(mretL) else None,
                    "per_window": {str(k): v for k, v in wins.items()}, "per_month": {mm: {"mean": float(mretL[mretL.index.month == mm].mean()), "hit": float((mretL[mretL.index.month == mm] > 0).mean())} for _, mm in R70.hold_months(m_dec)},
                    "mean_per_positioned_day": float(x[posP].mean()) if posP.any() else None, "cost_per_window_bp": float(c[wP].sum() / max(len(set(R70.window_year_of(p, m_dec) for p in mret.index)), 1) * 1e4),
                    "dollar": {"C_a_net_sharpe": R55.sharpe(pnl_n[wP]), "C_a_net_sortino": R55.sortino(pnl_n[wP]), "gross_sharpe": R55.sharpe(pnl[wP]), "C_c_skew": float(pd.Series(pnl_n[wP]).skew()),
                               "C_d_sigma_positioned": float(pnl_n[posP].std(ddof=1)), "C_d_sigma_all": float(pnl_n[wP].std(ddof=1)), "total_usd": float(pnl_n[wP].sum()), "gross_usd": float(pnl[wP].sum()),
                               "cost_usd": float(cost_usd[wP].sum()), "max_dd_usd": R55.max_drawdown(pnl_n[wP]), "total_usd_2011_2023": float(pnl_n[wL].sum()),
                               "fails": [k for k, b in (("C-a", R55.sharpe(pnl_n[wP]) <= 0.5), ("C-c", pd.Series(pnl_n[wP]).skew() < -0.5), ("C-d", pnl_n[posP].std(ddof=1) > R55.C_D_SIGMA)) if b]},
                    "rank_of_12_long": int(sum(1 for m in prof if prof[m]["sharpe_long"] < prof[m_dec]["sharpe_long"])), "best_of_12_long": bool(best == m_dec),
                    "rank_of_12_primary": int(sum(1 for m in prof if prof[m]["sharpe_primary"] < prof[m_dec]["sharpe_primary"])), "best_of_12_primary": bool(best_p == m_dec),
                    "above_control_per_day": bool((x[posP].mean() if posP.any() else -1) > xC[heldA & wP].mean())}
        declared["candidate"] = bool(declared["gross"]["sharpe"] > 0 and declared["best_of_12_long"] and declared["above_control_per_day"])
        pred = {"best_long": best, "best_primary": best_p, "predicted_set": sorted(PRED_SET[root]), "best_in_set": bool(best in PRED_SET[root]),
                "falsified_outside": bool(best not in FALSIFY_OUTSIDE[root]), "declared_positive_long": bool(prof[m_dec]["sharpe_long"] > 0),
                "negatives": {m: prof[m]["sharpe_long"] for m in PRED_NEG[root]}, "negatives_hold": bool(all(prof[m]["sharpe_long"] <= 0 for m in PRED_NEG[root])),
                "control_nonpositive": bool(ctrl["bp_per_day_long"] <= 0), "spearman_with_ZS": rho}
        res["roots"][root] = {"profile": prof, "control": ctrl, "declared": declared, "audits": audits}; res["predictions"][root] = pred
        print(f"\n  {root}: profile (Sharpe 2011-23 / 2016-23): " + " ".join(f"m{m}:{prof[m]['sharpe_long']:+.2f}/{prof[m]['sharpe_primary']:+.2f}" for m in range(1, 13)))
        print(f"      best m{best} (2016-23 best m{best_p}); predicted {sorted(PRED_SET[root])} -> {'HOLDS' if pred['best_in_set'] else 'fails'}{' (FALSIFIED)' if pred['falsified_outside'] else ''}; "
              f"negatives {PRED_NEG[root]} -> {'hold' if pred['negatives_hold'] else 'fail'}; control {ctrl['bp_per_day_long']:+.2f} bp/day (Sharpe {ctrl['sharpe_long']:+.2f}); Spearman with ZS {rho:+.2f}")
        dg, dn, dd = declared["gross"], declared["net"], declared["dollar"]; mm_ = declared["months"]
        print(f"      declared m{m_dec} {declared['pair_first_window']}: gross Sh {dg['sharpe']:+.2f} / So {dg['sortino']:+.2f} (SE {dg['se']:.2f}) net {dn['sharpe']:+.2f}; 2011-23 {declared['gross_long']['sharpe']:+.2f}; "
              f"months n {mm_['n']} hit {mm_['hit']:.2f} worst {mm_['worst']*100:+.2f}%; rank {declared['rank_of_12_long']}/11 long, {declared['rank_of_12_primary']}/11 primary; "
              f"$: net Sh {dd['C_a_net_sharpe']:+.2f} skew {dd['C_c_skew']:+.2f} sigma ${dd['C_d_sigma_positioned']:,.0f} total ${dd['total_usd']:+,.0f} cost ${dd['cost_usd']:,.0f} fails {dd['fails']}; candidate {declared['candidate']}")
        print("      per window: " + " ".join(f"{k}:{v*100:+.2f}" for k, v in sorted(wins.items())))
        print("      control by month bp/day: " + " ".join(f"{m}:{v:+.1f}" for m, v in ctrl["by_calendar_month_bp"].items()))
    P = res["predictions"]
    others = sum(1 for r in ("ZW", "ZL", "ZM") if P[r]["best_in_set"])
    supported = bool(P["ZC"]["best_in_set"] and others >= 2 and all(P[r]["control_nonpositive"] for r in ROOTS))
    res["mechanism"] = {"corn_in_set": P["ZC"]["best_in_set"], "others_in_set": others, "controls_nonpositive": [r for r in ROOTS if P[r]["control_nonpositive"]], "supported": supported,
                        "candidates": [r for r in ROOTS if res["roots"][r]["declared"]["candidate"]]}
    res["timing"] = round(time.time() - t_start, 1)
    print(f"\n  MECHANISM {'SUPPORTED' if supported else 'NOT SUPPORTED'}: corn in set {P['ZC']['best_in_set']}, others in set {others}/3, controls <= 0 on {res['mechanism']['controls_nonpositive']}; candidates {res['mechanism']['candidates']}")
    OUT.write_text(json.dumps(R61._clean(res), indent=1), encoding="utf-8")
    print(f"  -> {OUT.relative_to(REPO)}  ({res['timing']}s)")


if __name__ == "__main__":
    main()
