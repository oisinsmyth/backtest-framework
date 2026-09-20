"""D567 Stage 0 -- the grains at harvest, the merchant avatar (design committed in D567 before this ran).
Diagnostic: reads outcomes on 2011-2023 only; no pre-registration produced; the 2024+ slice of every source
is filtered out before anything is computed. Builds the derived WASDE stocks-to-use fixture
(data/fixtures/wasde_grains_su.csv, public domain) and writes data/stage0_d567_grains.json.

    uv run python -u scripts/stage0_d567_grains_harvest.py
"""
from __future__ import annotations

import glob
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


R64 = _load("d564", "run_d564_basis_momentum.py")
R56, R55 = R64.R56, R64.R55

RAW = REPO / "data" / "raw" / "usda" / "wasde"
FIX_SU = REPO / "data" / "fixtures" / "wasde_grains_su.csv"
OUT = REPO / "data" / "stage0_d567_grains.json"
COT = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
END = "2023-12-29"
YEARS = list(range(2011, 2024))
COMMODITY = {"ZC": "Corn", "ZS": "Oilseed, Soybean", "ZW": "Wheat"}
MY_START_MONTH = {"ZC": 9, "ZS": 9, "ZW": 6}            # marketing year start
STORAGE_CENTS_PER_MONTH = 5.0                          # CBOT storage rate, cents a bushel a month
INTEREST = 0.025                                       # flat, declared; no rate series on disk
# windows: formation = last session before the first month; exit = last session of the last month. The pair must SURVIVE the
# window: T1 = the first listed delivery month strictly after the window's last month (grain contracts expire mid-delivery-
# month), T2 the next listed. The design's stated pairs (X/F for soybeans over Sep-Nov, N/U for wheat over Jun-Aug) cannot
# survive a three-month window and are corrected here: soybeans Sep-Nov hold F/H, wheat Jun-Aug hold U/Z; the design's
# soybean harvest-contract pair is kept as a declared two-month window ending before X expires. The weather window names
# the NEW-CROP contract explicitly (corn Z, soybeans X) because that is where the premium sits.
# entries: (start_month, end_month, t1_rule) with t1_rule "survive" or an explicit month code
WINDOWS = {"ZC": {"harvest": (9, 11, "survive"), "weather": (6, 8, "Z"), "post_harvest": (12, 2, "survive")},
           "ZS": {"harvest": (9, 11, "survive"), "harvest_XF": (9, 10, "X"), "weather": (6, 8, "X"), "post_harvest": (12, 2, "survive")},
           "ZW": {"harvest": (6, 8, "survive"), "post_harvest": (9, 11, "survive")}}
MONTH_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
N_PERM = 4000


# --------------------------------------------------------------------------------------------
# the derived WASDE fixture
# --------------------------------------------------------------------------------------------
def build_su():
    files = sorted(glob.glob(str(RAW / "*.csv")))
    cols = ["ReleaseDate", "Commodity", "Region", "Attribute", "MarketYear", "ProjEstFlag", "Value", "Unit", "ReportDate"]
    parts = []
    for f in files:
        w = pd.read_csv(f, encoding="utf-8", usecols=cols, dtype=str)
        w = w[(w["Region"] == "United States") & w["Commodity"].isin(COMMODITY.values()) & w["Attribute"].isin(["Ending Stocks", "Use, Total", "Production"]) & (w["Unit"] == "Million Bushels")]
        parts.append(w)
    w = pd.concat(parts, ignore_index=True).drop_duplicates()
    # ReleaseDate is ISO in the archives and MM/DD/YYYY in some monthly files; normalise, and check the month
    # against ReportDate ("September 2023") so a day/month swap cannot pass
    def iso(rd, rep):
        rd = str(rd)
        if "/" in rd:
            m, d, y = rd.split("/"); out = f"{y}-{int(m):02d}-{int(d):02d}"
        else:
            out = rd[:10]
        rep_month = pd.Timestamp(str(rep)).month if isinstance(rep, str) and rep else None
        if rep_month is not None and int(out[5:7]) != rep_month:
            raise AssertionError(f"WASDE release date {rd} does not sit in its report month {rep}")
        return out
    w["ReleaseDate"] = [iso(a, b) for a, b in zip(w["ReleaseDate"], w["ReportDate"])]
    w["Value"] = w["Value"].astype(float); w = w[w["MarketYear"].notna()]
    piv = w.pivot_table(index=["ReleaseDate", "Commodity", "MarketYear", "ProjEstFlag"], columns="Attribute", values="Value", aggfunc="first").reset_index()
    piv = piv.rename(columns={"Ending Stocks": "ending_stocks", "Use, Total": "use_total", "Production": "production"})
    piv["stocks_to_use"] = piv["ending_stocks"] / piv["use_total"]
    piv = piv.sort_values(["Commodity", "ReleaseDate", "MarketYear"]).reset_index(drop=True)
    piv.to_csv(FIX_SU, index=False, encoding="utf-8", lineterminator="\n")
    return piv


def my_label(year):
    return f"{year}/{str(year + 1)[-2:]}"


def su_at(piv, root, formation, my_year):
    """The last report released strictly before the formation session, for the marketing year in progress in the window."""
    c = piv[(piv["Commodity"] == COMMODITY[root]) & (piv["ReleaseDate"] < formation) & (piv["MarketYear"] == my_label(my_year))]
    if c.empty:
        return None
    r = c.sort_values("ReleaseDate").iloc[-1]
    return {"release": r["ReleaseDate"], "flag": r["ProjEstFlag"], "ending_stocks": float(r["ending_stocks"]), "use_total": float(r["use_total"]),
            "su": float(r["stocks_to_use"]), "production": float(r["production"]) if pd.notna(r["production"]) else None}


def production_change_june_july(piv, root, year):
    c = piv[(piv["Commodity"] == COMMODITY[root]) & (piv["MarketYear"] == my_label(year))]
    jun = c[c["ReleaseDate"].str[:7] == f"{year}-06"]; jul = c[c["ReleaseDate"].str[:7] == f"{year}-07"]
    if jun.empty or jul.empty or pd.isna(jun.iloc[0]["production"]) or pd.isna(jul.iloc[0]["production"]):
        return None
    return float(jul.iloc[0]["production"] / jun.iloc[0]["production"] - 1.0)


# --------------------------------------------------------------------------------------------
# the curve
# --------------------------------------------------------------------------------------------
def pick_pair(A, cols, t0, F0, year, m0, m1, y_end, rule):
    """T1 by the survival rule (first delivery strictly after the window's last month) or an explicit new-crop
    month code (the first such delivery at or after the window's first month); T2 the next listed with a settlement."""
    fin = np.isfinite(F0)
    if rule == "survive":
        thr = y_end * 12 + m1 + 1
        cand = np.flatnonzero(fin & (cols >= thr))
    else:
        mcode = MONTH_CODE[rule]
        cand = np.flatnonzero(fin & (cols >= year * 12 + m0) & ((cols % 12 if True else 0) == (mcode % 12)))
    if cand.size == 0:
        return None, None
    j1 = int(cand[0]); later = np.flatnonzero(fin & (cols > cols[j1]))
    return j1, (int(later[0]) if later.size else None)


def window_outcome(A, cols, days, idx, year, window):
    m0, m1, rule = window
    y_end = year if m1 >= m0 else year + 1
    first = np.flatnonzero((idx.year == year) & (idx.month == m0))
    last = np.flatnonzero((idx.year == y_end) & (idx.month == m1))
    if first.size == 0 or last.size == 0:
        return None
    t0 = first[0] - 1; t1 = last[-1]
    F0 = R64.formation_settles(A, t0, 5); F1 = R64.formation_settles(A, t1, 5)
    j1, j2 = pick_pair(A, cols, t0, F0, year, m0, m1, y_end, rule)
    if j1 is None or j2 is None or not (np.isfinite(F1[j1]) and np.isfinite(F1[j2])):
        return None
    r1 = F1[j1] / F0[j1] - 1.0; r2 = F1[j2] / F0[j2] - 1.0
    basis0 = F0[j2] / F0[j1] - 1.0; basis1 = F1[j2] / F1[j1] - 1.0
    months_between = int(cols[j2] - cols[j1])
    # full carry in price units: storage (cents -> price units: the strip quotes cents a bushel) + interest on the front
    full_carry = (STORAGE_CENTS_PER_MONTH + INTEREST / 12.0 * F0[j1]) * months_between
    return {"formation": str(days[t0]), "exit": str(days[t1]), "t1": f"{cols[j1]//12}-{cols[j1]%12 if cols[j1]%12 else 12:02d}",
            "t2": f"{cols[j2]//12}-{cols[j2]%12 if cols[j2]%12 else 12:02d}", "front": r1, "second": r2, "spread": r1 - r2,
            "basis0": basis0, "basis1": basis1, "d_basis": basis1 - basis0, "basis0_cents": F0[j2] - F0[j1],
            "full_carry_cents": full_carry, "carry_ratio0": (F0[j2] - F0[j1]) / full_carry if full_carry > 0 else None,
            "F1_0": F0[j1], "F1_1": F1[j1]}


def perm_p(a, b, n=N_PERM, seed=0):
    a = np.asarray(a, float); b = np.asarray(b, float); ok = np.isfinite(a) & np.isfinite(b); a, b = a[ok], b[ok]
    if a.size < 6:
        return float("nan"), float("nan"), int(a.size)
    rng = np.random.default_rng(seed); obs = pd.Series(a).corr(pd.Series(b), method="spearman")
    cnt = sum(1 for _ in range(n) if abs(pd.Series(a).corr(pd.Series(rng.permutation(b)), method="spearman")) >= abs(obs))
    return float(obs), cnt / n, int(a.size)


def loyo_residual(v):
    v = np.asarray(v, float); out = np.full(v.size, np.nan)
    for i in range(v.size):
        m = np.ones(v.size, bool); m[i] = False
        if np.isfinite(v[m]).sum() >= 5:
            out[i] = v[i] - np.nanmean(v[m])
    return out


def terciles(state, outcome):
    s = np.asarray(state, float); o = np.asarray(outcome, float); ok = np.isfinite(s) & np.isfinite(o)
    if ok.sum() < 6:
        return None
    q = np.quantile(s[ok], [1 / 3, 2 / 3]); res = {}
    for name, m in (("low", s <= q[0]), ("mid", (s > q[0]) & (s <= q[1])), ("high", s > q[1])):
        mm = m & ok; res[name] = {"n": int(mm.sum()), "state_mean": float(s[mm].mean()) if mm.any() else None, "mean": float(o[mm].mean()) if mm.any() else None,
                                  "hit_pos": float((o[mm] > 0).mean()) if mm.any() else None}
    return res


def main():
    t0 = time.time()
    print("D567 STAGE 0 -- the grains at harvest; design committed before this ran; 2011-2023 only; 2024+ shut")
    piv = build_su()
    piv = piv[piv["ReleaseDate"] <= END]
    print(f"  WASDE fixture: {len(piv)} (report, commodity, marketing-year) rows, {piv['ReleaseDate'].nunique()} reports {piv['ReleaseDate'].min()}..{piv['ReleaseDate'].max()} -> {FIX_SU.relative_to(REPO)}")
    df = R55.load_fixture(); live_start = R55.live_start_by_rule(df); g = R55.build_grids(df, live_start)
    days = g["days"]; idx = pd.to_datetime(days)
    strip = pd.read_csv(R56.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    strip = strip[(strip["ref"] < R55.RESERVED_FROM) & strip["root"].isin(COMMODITY)]
    tables = R64.strip_tables(strip, days, list(COMMODITY))
    cot = pd.read_csv(COT, encoding="utf-8", dtype={"code": str})
    cot = cot[(cot["family"] == "legacy") & (cot["category"] == "commercial") & cot["symbol"].isin(COMMODITY) & (cot["report_date"] < R55.RESERVED_FROM)].copy()
    cot["net_short_share"] = (cot["short"] - cot["long"]) / cot["open_interest"]

    res = {"design": "D567", "years": YEARS, "full_carry": {"storage_cents_per_month": STORAGE_CENTS_PER_MONTH, "interest": INTEREST}, "roots": {}}
    for root in COMMODITY:
        A, cols = tables[root]; out_root = {}
        for wname, months in WINDOWS[root].items():
            rows = []
            for y in YEARS:
                w = window_outcome(A, cols, days, idx, y, months)
                if w is None:
                    continue
                my = y if MY_START_MONTH[root] <= months[0] or wname == "weather" else y - 1
                if wname == "post_harvest" and root in ("ZC", "ZS"):
                    my = y                                # Dec of year y is in MY y/y+1
                if root == "ZW" and wname == "post_harvest":
                    my = y                                # Sep-Nov of year y is in wheat MY y/y+1 (starts June)
                su = su_at(piv, root, w["formation"], my)
                c = cot[(cot["symbol"] == root) & (cot["report_date"] < w["formation"])].sort_values("report_date")
                w.update({"year": y, "marketing_year": my_label(my), "su": su["su"] if su else None, "su_release": su["release"] if su else None, "su_flag": su["flag"] if su else None,
                          "cot_net_short_share": float(c.iloc[-1]["net_short_share"]) if len(c) else None, "cot_date": c.iloc[-1]["report_date"] if len(c) else None,
                          "prod_change_jun_jul": production_change_june_july(piv, root, y) if wname == "weather" else None})
                rows.append(w)
            tab = pd.DataFrame(rows)
            if tab.empty:
                continue
            spread = tab["spread"].to_numpy(); front = tab["front"].to_numpy(); dbas = tab["d_basis"].to_numpy()
            block = {"per_year": rows, "n": int(len(tab)),
                     "T1_calendar": {"spread": {"mean": float(spread.mean()), "hit_neg": float((spread < 0).mean()), "t": float(spread.mean() / spread.std(ddof=1) * math.sqrt(len(spread))), "worst_short": float(spread.max()), "best_short": float(spread.min())},
                                     "front": {"mean": float(front.mean()), "hit_neg": float((front < 0).mean()), "t": float(front.mean() / front.std(ddof=1) * math.sqrt(len(front))), "worst_short": float(front.max())},
                                     "d_basis": {"mean": float(dbas.mean()), "hit_pos": float((dbas > 0).mean())}}}
            su_v = tab["su"].to_numpy(float); cotv = tab["cot_net_short_share"].to_numpy(float); cr = tab["carry_ratio0"].to_numpy(float)
            tests = {}
            for sname, svec in (("su", su_v), ("carry_ratio0", cr), ("cot_net_short", cotv)):
                for oname, ovec in (("spread", spread), ("front", front), ("d_basis", dbas)):
                    rho, p, n = perm_p(svec, ovec); rr, pr, nr = perm_p(svec, loyo_residual(ovec), seed=1)
                    tests[f"{sname}->{oname}"] = {"rho": rho, "p": p, "n": n, "rho_residual": rr, "p_residual": pr}
            block["T2_T4_state"] = tests
            block["terciles_by_su"] = {"spread": terciles(su_v, spread), "front": terciles(su_v, front), "carry_ratio0": terciles(su_v, cr)}
            block["T3_premise"] = {"share_at_full_carry_at_formation": float(np.nanmean(cr >= 0.8)) if np.isfinite(cr).any() else None,
                                   "carry_ratio0_by_su_tercile": terciles(su_v, cr),
                                   "spread_when_high_su_and_below_full_carry": {"n": int(((su_v > np.nanquantile(su_v, 2 / 3)) & (cr < 0.8)).sum()),
                                                                                 "mean": float(spread[(su_v > np.nanquantile(su_v, 2 / 3)) & (cr < 0.8)].mean()) if ((su_v > np.nanquantile(su_v, 2 / 3)) & (cr < 0.8)).any() else None},
                                   "spread_when_high_su_and_at_full_carry": {"n": int(((su_v > np.nanquantile(su_v, 2 / 3)) & (cr >= 0.8)).sum()),
                                                                              "mean": float(spread[(su_v > np.nanquantile(su_v, 2 / 3)) & (cr >= 0.8)].mean()) if ((su_v > np.nanquantile(su_v, 2 / 3)) & (cr >= 0.8)).any() else None}}
            if wname == "weather":
                pc = tab["prod_change_jun_jul"].to_numpy(float); cut = pc < -0.05
                block["T5_weather"] = {"front_mean": float(front.mean()), "front_hit_neg": float((front < 0).mean()), "drought_years": [int(y) for y, c_ in zip(tab["year"], cut) if c_],
                                       "front_mean_non_drought": float(front[~cut & np.isfinite(pc)].mean()) if (~cut & np.isfinite(pc)).any() else None,
                                       "front_mean_drought": float(front[cut].mean()) if cut.any() else None, "prod_change_by_year": [(int(y), None if not np.isfinite(v) else float(v)) for y, v in zip(tab["year"], pc)]}
            out_root[wname] = block
            T1 = block["T1_calendar"]
            print(f"\n  {root} {wname:12s} n {block['n']}  spread mean {T1['spread']['mean']*100:+.2f}% (short pays {T1['spread']['hit_neg']:.2f}, t {T1['spread']['t']:+.2f})  front mean {T1['front']['mean']*100:+.2f}% (hit-neg {T1['front']['hit_neg']:.2f}, t {T1['front']['t']:+.2f})  basis widens in {T1['d_basis']['hit_pos']:.2f}")
            for k_, v in tests.items():
                if k_.startswith("su->") or k_.startswith("carry_ratio0->spread") or k_.startswith("cot_net_short->spread"):
                    print(f"      {k_:26s} rho {v['rho']:+.3f} p {v['p']:.3f} | residual rho {v['rho_residual']:+.3f} p {v['p_residual']:.3f}  (n {v['n']})")
            tc = block["terciles_by_su"]["spread"]
            if tc:
                print("      spread by S/U tercile: " + "  ".join(f"{k}: S/U {v['state_mean']:.3f} spread {v['mean']*100:+.2f}% (n {v['n']})" for k, v in tc.items()))
            print(f"      premise: at full carry (>=80%) at formation in {block['T3_premise']['share_at_full_carry_at_formation']:.2f} of years; high-S/U & below full carry n {block['T3_premise']['spread_when_high_su_and_below_full_carry']['n']} mean {block['T3_premise']['spread_when_high_su_and_below_full_carry']['mean']}; high-S/U & at full carry n {block['T3_premise']['spread_when_high_su_and_at_full_carry']['n']} mean {block['T3_premise']['spread_when_high_su_and_at_full_carry']['mean']}")
            print("      per year: " + " ".join(f"{r['year']}:{r['spread']*100:+.1f}/{r['front']*100:+.1f}" for r in rows))
        res["roots"][root] = out_root
    res["timing"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: None if isinstance(o, float) and not np.isfinite(o) else (float(o) if isinstance(o, np.floating) else int(o) if isinstance(o, np.integer) else str(o))), encoding="utf-8")
    print(f"\n  -> {OUT.relative_to(REPO)}  ({res['timing']}s)")


if __name__ == "__main__":
    main()
