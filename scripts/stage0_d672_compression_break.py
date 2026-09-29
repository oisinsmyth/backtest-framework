"""D672 Stage 0 (development, ES and NQ): the compression break. Spec: docs/decisions/D672-STAGE-0-DESIGN-the-
compression-break.md (31273d90). D666's plain break + E4, traded only when the compression tier < 1/3 (comp = mean of the
walk-forward percentiles of rv5 and the overnight two-way range; then comp's own walk-forward percentile). Nothing fitted.
In-sample to 2025-02-28; vault sealed. Dealer gamma (GEX, SqueezeMetrics) enters only as a reported split.

    uv run python scripts/stage0_d672_compression_break.py --run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d671_break_construction as C  # noqa: E402

M, X, T = C.M, C.X, C.T
OUT = REPO / "data" / "stage0_d672_compression_break.json"
N_PLACEBO, N_BOOT, SEED = 1000, 500, 672


def tier_of(v: np.ndarray, sess: np.ndarray, tr_sess: pd.Series) -> np.ndarray:
    return pd.Series(C.tiers(v), index=sess).reindex(tr_sess).to_numpy()


def build(data_root: Path) -> dict[str, Any]:
    t0 = time.time()
    roots = C.ROOTS
    costs = M.micro_costs()
    b, use, Gd, R = M.load_bars(data_root, False, roots)
    C._R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=roots)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < M.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    cal_all = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    frames, sf = {}, {}
    for r in roots:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        frames[r] = d
        on = C.overnight(b, r)
        C.overnight_audit(on)
        sf[r] = C.session_features(d, on, cal_all[cal_all["root"] == r].set_index("day"))
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, M.TICK_PTS[r], M.SEED + M.ROOTS.index(r))
            for r in roots]
    with ProcessPoolExecutor(max_workers=2) as pool:
        got = {o["root"]: o for o in pool.map(M.root_trades, jobs)}
    ref671 = json.loads((REPO / "data" / "stage0_d671_break_construction.json").read_text(encoding="utf-8"))["roots"]
    k8 = M.k8_daily(tabs["NQ"], frames["NQ"].index)
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {"spec": "D672 (31273d90), development", "credit": "dealer gamma (GEX): SqueezeMetrics (split only)",
                           "roots": {}}
    c1_daily, keep = {}, {}
    for r in roots:
        S_, d = sf[r], frames[r]
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        X.TICK = M.TICK_PTS[r]
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        tr["retest"] = [C.retest(bars[(r, s)], int(i), int(D), float(L)) for s, i, D, L in zip(tr["session"], tr["i"], tr["D"], tr["L"])]
        sess = S_.index.to_numpy()
        p_rv, p_on = C.tiers(S_["rv5"].to_numpy(float)), C.tiers(S_["on_range"].to_numpy(float))
        comp = (p_rv + p_on) / 2
        ctier = C.tiers(comp)
        C.tier_audit(ctier, comp, list(range(0, len(comp), max(1, len(comp) // 12))))
        tr["ctier"] = pd.Series(ctier, index=sess).reindex(tr["session"]).to_numpy()
        tr["p_rv"] = pd.Series(p_rv, index=sess).reindex(tr["session"]).to_numpy()
        tr["p_on"] = pd.Series(p_on, index=sess).reindex(tr["session"]).to_numpy()
        # D671's evaluation window, for comparability
        f671, _ = C.size_forecast(S_[list(C.SIZE_FEATS)].to_numpy(float), S_["y"].to_numpy(float))
        t671 = pd.Series(C.tiers(f671), index=sess).reindex(tr["session"]).to_numpy()
        win = np.isfinite(t671) & np.isfinite(tr["ctier"].to_numpy(float))
        if abs(float((tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)[np.isfinite(t671)].mean()) - ref671[r]["ablation"]["B0_base"]["net"]) > 1e-9:
            raise SystemExit(f"{r}: does not reproduce D671's B0")
        ses = d.index[d.index >= tr.loc[win, "session"].min()]
        years, usd_pt = len(ses) / 252, costs[r]["usd_per_point"]
        ct = tr["ctier"].to_numpy(float)
        c1, c2, c3 = win & (ct < 1 / 3), win & (ct >= 1 / 3) & (ct < 2 / 3), win & (ct >= 2 / 3)
        books = {nm: C.book(tr, k, "E4_gross", years, usd_pt, ses) for nm, k in
                 (("B0_all_breaks", win), ("C1_compression", c1), ("C2_middle", c2), ("C3_top", c3))}
        netv = (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)
        # placebo: within-year random subsets of B0 with C1's count per year
        yrs = tr["session"].str[:4].to_numpy()
        per_year = {yv: int((c1 & (yrs == yv)).sum()) for yv in np.unique(yrs[win])}
        pools = {yv: np.flatnonzero(win & (yrs == yv)) for yv in per_year}
        draws = np.array([netv[np.concatenate([rng.choice(pools[yv], per_year[yv], replace=False) for yv in per_year if per_year[yv]])].mean()
                          for _ in range(N_PLACEBO)])
        c1net = float(netv[c1].mean())
        q95 = [np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(N_BOOT)]
        placebo = {"c1_net": c1net, "p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)),
                   "p95_se": float(np.std(q95, ddof=1)), "rank": float((draws < c1net).mean())}
        # rotation of the compression tier across sessions
        cs = pd.Series(ctier, index=sess).dropna()
        tv = cs.to_numpy()
        pos = pd.Series(np.arange(len(cs)), index=cs.index).reindex(tr["session"]).to_numpy()
        okp = np.isfinite(pos) & win
        diffs = []
        for kk in range(21, len(tv) - 21):
            rt = np.full(len(tr), np.nan)
            rt[okp] = np.roll(tv, kk)[pos[okp].astype(int)]
            q_, r_ = okp & (rt < 1 / 3), okp & (rt >= 1 / 3)
            diffs.append(netv[q_].mean() - netv[r_].mean())
        diffs = np.array(diffs)
        act = float(netv[c1].mean() - netv[win & ~c1].mean())
        rotation = {"c1_minus_rest": act, "p50": float(np.median(diffs)), "p95": float(np.quantile(diffs, 0.95)),
                    "rank": float((diffs < act).mean()), "offsets": int(len(diffs))}
        # splits of C1
        D = tr["D"].to_numpy(int)
        gd = d["gd_spx"].reindex(tr["session"]).to_numpy(float)
        gser = pd.Series(-d["gd_spx"] / d["V20"], index=d.index)
        g_med = gser.shift(1).rolling(250, min_periods=125).median().reindex(tr["session"]).to_numpy(float)
        g_now = gser.reindex(tr["session"]).to_numpy(float)
        o, A = tr["open"].to_numpy(float), tr["A"].to_numpy(float)
        ph = d["prior_high"].reindex(tr["session"]).to_numpy(float)
        pl = d["prior_low"].reindex(tr["session"]).to_numpy(float)
        stop = tr["stop"].to_numpy(float)
        oclass = np.where(np.where(D > 0, o > stop, o < stop), "gap_through", np.where(np.where(D > 0, o > ph, o < pl), "gap_inside", "no_gap"))
        bk = lambda k, col="E4_gross": C.book(tr, k, col, years, usd_pt, ses)  # noqa: E731
        splits = {"long": bk(c1 & (D > 0)), "short": bk(c1 & (D < 0)),
                  "spx_short_gamma": bk(c1 & (gd < 0)), "spx_long_gamma": bk(c1 & (gd >= 0)),
                  "g_above_median": bk(c1 & (g_now > g_med)), "g_below_median": bk(c1 & (g_now <= g_med)),
                  **{f"class_{c}": bk(c1 & (oclass == c)) for c in ("no_gap", "gap_inside", "gap_through")},
                  "E2_exit": bk(c1, "E2_gross")}
        single = {nm: {"bottom": bk(win & (tr[nm].to_numpy(float) < 1 / 3)), "top": bk(win & (tr[nm].to_numpy(float) >= 2 / 3))}
                  for nm in ("p_rv", "p_on")}
        fg = X.four_groups(tr[c1].reset_index(drop=True), pd.Series(tr.loc[c1, "E4_gross"].to_numpy()), pd.Series(netv[c1]),
                           c1.sum() / years, R, r)
        c1_daily[r] = M.daily_usd(tr, netv, c1.astype(float), ses, usd_pt)
        by_year = {yv: {"B0": C.book(tr, win & (yrs == yv), "E4_gross", 1.0, usd_pt, ses[ses.str.startswith(yv)]),
                        "C1": C.book(tr, c1 & (yrs == yv), "E4_gross", 1.0, usd_pt, ses[ses.str.startswith(yv)])}
                   for yv in sorted(set(yrs[win]))}
        keep[r] = (tr, c1, netv, ses, usd_pt)
        out["roots"][r] = {"window_start": str(ses[0]), "books": books, "placebo": placebo, "rotation": rotation,
                           "c1_splits": splits, "single_input_tiers": single, "four_groups_C1": fg, "by_year": by_year}
    for r in roots:
        tr, c1, netv, ses, usd_pt = keep[r]
        other = {o_: c1_daily[o_] for o_ in roots if o_ != r}
        out["roots"][r]["component_C1"] = M.component(tr, netv, tr["E4_gross"].to_numpy(float), c1.astype(float), ses, usd_pt, k8, other)
    rr = out["roots"]
    nq, es = rr["NQ"], rr["ES"]
    full = [y for y in nq["by_year"] if "2018" <= y <= "2024"]
    out["expectations"] = {
        "1_NQ_C1_net_5_to_9_about_50_per_year_rotation_above_0.95": bool(5 <= nq["books"]["C1_compression"]["net"] <= 9
                                                                         and 35 <= nq["books"]["C1_compression"]["trades_per_year"] <= 65
                                                                         and nq["rotation"]["rank"] > 0.95),
        "2_NQ_C1_sharpe_above_B0_usd_within_40pct": bool(nq["books"]["C1_compression"]["daily_sharpe"] > nq["books"]["B0_all_breaks"]["daily_sharpe"]
                                                         and abs(nq["books"]["C1_compression"]["usd_per_year"] / nq["books"]["B0_all_breaks"]["usd_per_year"] - 1) <= 0.4),
        "3_ES_C1_within_2bp_and_inside_placebo": bool(abs(es["books"]["C1_compression"]["net"]) <= 2 and es["placebo"]["rank"] <= 0.95),
        "4_NQ_C1_positive_5_of_7_full_years": bool(sum(1 for y in full if nq["by_year"][y]["C1"].get("net", -1) > 0) >= 5),
        "5_NQ_short_gamma_better_within_C1": bool(nq["c1_splits"]["spx_short_gamma"].get("net", -99) > nq["c1_splits"]["spx_long_gamma"].get("net", 99))}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    T.licence_guard(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if not a.run:
        ap.print_help()
        return 1
    out = build(a.data_root)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print("expectations", out["expectations"], "runtime", out["runtime_min"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
