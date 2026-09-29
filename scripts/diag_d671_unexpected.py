"""D671 diagnostic: the unexpected break (the principal, 2026-09-29: "Lets pull at the unexpected break thread").
Post hoc, DEVELOPMENT (ES, NQ in-sample to 2025-02-28), through D671's own functions (38c33823 / f8806731); it
reproduces D671's committed tier table before reporting. Statistics only; dealer gamma (GEX): SqueezeMetrics.

    uv run python scripts/diag_d671_unexpected.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

A  dose-response: E4 net, P(hold), gain-if-hold, loss-if-fail by quintile of the size tier (walk-forward percentile).
B  robustness of quiet (bottom tercile) vs the rest: by year, side, open class, entry clock; ES longs only.
C  which input carries it: each input's OWN walk-forward percentile (rv5, overnight range, |gap|, gamma) as the tier.
D  a direct surprise measure: the move the break needs from the open, D x (stop - open) / A, over the expected range
   exp(forecast); E4 by its quintile, and quiet x surprise.
E  the null: quiet - rest net difference against an enumerated rotation of the tier series across sessions.
F  cost in bp by tier (a vol tier must not be a price tier); exits: E2 (stop at L, hold to close) by tier.
Every cut is counted and reported (multiplicity).
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d671_break_construction as C  # noqa: E402

M, X, T = C.M, C.X, C.T
OUT = REPO / "data" / "diag_d671_unexpected.json"
N_CUTS = {"n": 0}


def cell(tr: pd.DataFrame, k: np.ndarray, gcol: str = "E4_gross") -> dict:
    N_CUTS["n"] += 1
    n = int(k.sum())
    if n < 5:
        return {"n": n}
    g = tr[gcol].to_numpy(float)[k]
    net = g - tr["cost_bp"].to_numpy(float)[k]
    hold = ~tr["retest"].to_numpy(bool)[k]
    t, _ = C._R.nw_t(net)
    return {"n": n, "net": float(net.mean()), "t": float(t), "p_hold": float(hold.mean()),
            "gain_if_hold": float(g[hold].mean()) if hold.any() else float("nan"),
            "loss_if_fail": float(g[~hold].mean()) if (~hold).any() else float("nan"),
            "cost_bp": float(tr["cost_bp"].to_numpy(float)[k].mean())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    roots = C.ROOTS
    costs = M.micro_costs()
    b, use, Gd, R = M.load_bars(a.data_root, False, roots)
    C._R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=roots)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(a.data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < M.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    cal_all = pd.read_csv(a.data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    frames, sf = {}, {}
    for r in roots:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        frames[r] = d
        on = C.overnight(b, r)
        C.overnight_audit(on)
        sf[r] = C.session_features(d, on, cal_all[cal_all["root"] == r].set_index("day"))
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, M.TICK_PTS[r], M.SEED + M.ROOTS.index(r))
            for r in roots]
    with ProcessPoolExecutor(max_workers=2) as pool:
        got = {o["root"]: o for o in pool.map(M.root_trades, jobs)}
    committed = json.loads((REPO / "data" / "stage0_d671_break_construction.json").read_text(encoding="utf-8"))["roots"]
    out = {"spec": "post hoc diagnostic of D671 (49ddb6e9): the unexpected break", "credit": "dealer gamma (GEX): SqueezeMetrics",
           "roots": {}}
    for r in roots:
        S_, d = sf[r], frames[r]
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        X.TICK = M.TICK_PTS[r]
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        tr["retest"] = [C.retest(bars[(r, s)], int(i), int(D), float(L)) for s, i, D, L in zip(tr["session"], tr["i"], tr["D"], tr["L"])]
        y = S_["y"].to_numpy(float)
        sess = S_.index.to_numpy()
        f, _ = C.size_forecast(S_[list(C.SIZE_FEATS)].to_numpy(float), y)
        tier = C.tiers(f)
        tr["f"] = pd.Series(f, index=sess).reindex(tr["session"]).to_numpy()
        tr["tier"] = pd.Series(tier, index=sess).reindex(tr["session"]).to_numpy()
        win = np.isfinite(tr["tier"].to_numpy(float))
        tb = np.digitize(tr["tier"].to_numpy(float), [1 / 3, 2 / 3])
        # reproduce D671's committed tier table
        for kk, nm in enumerate(("bottom", "middle", "top")):
            k = win & (tb == kk)
            net = (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)[k]
            if abs(net.mean() - committed[r]["by_size_tier"][nm]["net"]) > 1e-9:
                raise SystemExit(f"{r} {nm}: does not reproduce D671")
        quiet, rest = win & (tb == 0), win & (tb > 0)
        res: dict = {}
        # A: dose-response by tier quintile
        tq = np.digitize(tr["tier"].to_numpy(float), [0.2, 0.4, 0.6, 0.8])
        res["A_by_tier_quintile"] = {str(q + 1): cell(tr, win & (tq == q)) for q in range(5)}
        # B: robustness
        yrs = tr["session"].str[:4].to_numpy()
        D = tr["D"].to_numpy(int)
        o, A = tr["open"].to_numpy(float), tr["A"].to_numpy(float)
        ph = d["prior_high"].reindex(tr["session"]).to_numpy(float)
        pl = d["prior_low"].reindex(tr["session"]).to_numpy(float)
        stop = tr["stop"].to_numpy(float)
        beyond_L = np.where(D > 0, o > ph, o < pl)
        beyond_stop = np.where(D > 0, o > stop, o < stop)
        oclass = np.where(beyond_stop, "gap_through", np.where(beyond_L, "gap_inside", "no_gap"))
        mins = tr["minute"].to_numpy(int)
        clock = np.where(mins <= C.hm("09:30"), "open_fill", np.where(mins < C.hm("10:30"), "09:31-10:29", "10:30+"))
        B = {"by_year": {yv: {"quiet": cell(tr, quiet & (yrs == yv)), "rest": cell(tr, rest & (yrs == yv))} for yv in sorted(set(yrs[win]))},
             "by_side": {sd: {"quiet": cell(tr, quiet & (D == v)), "rest": cell(tr, rest & (D == v))} for sd, v in (("long", 1), ("short", -1))},
             "by_open_class": {c: {"quiet": cell(tr, quiet & (oclass == c)), "rest": cell(tr, rest & (oclass == c))} for c in ("no_gap", "gap_inside", "gap_through")},
             "by_clock": {c: {"quiet": cell(tr, quiet & (clock == c)), "rest": cell(tr, rest & (clock == c))} for c in ("open_fill", "09:31-10:29", "10:30+")},
             "open_class_share_quiet": {c: float((oclass[quiet] == c).mean()) for c in ("no_gap", "gap_inside", "gap_through")},
             "open_class_share_rest": {c: float((oclass[rest] == c).mean()) for c in ("no_gap", "gap_inside", "gap_through")}}
        res["B_robustness"] = B
        # C: each input alone as the tier (its own walk-forward percentile among the previous 250 sessions)
        Cc = {}
        for feat in ("rv5", "on_range", "abs_gap", "g"):
            sgn = -1.0 if False else 1.0
            v = S_[feat].to_numpy(float) * sgn
            tf = C.tiers(v)
            tt = pd.Series(tf, index=sess).reindex(tr["session"]).to_numpy()
            ok = win & np.isfinite(tt)
            Cc[feat] = {"bottom_tercile": cell(tr, ok & (tt < 1 / 3)), "middle": cell(tr, ok & (tt >= 1 / 3) & (tt < 2 / 3)),
                        "top_tercile": cell(tr, ok & (tt >= 2 / 3))}
        res["C_single_input_tiers"] = Cc
        # D: a direct surprise measure: the needed move from the open over the expected range
        need = np.maximum(D * (stop - o), 0.0) / A
        exp_range = np.exp(tr["f"].to_numpy(float))
        surprise = need / exp_range
        sq = pd.qcut(pd.Series(surprise[win]).rank(method="first"), 5, labels=False).to_numpy()
        sqa = np.full(len(tr), -1)
        sqa[np.flatnonzero(win)] = sq
        res["D_surprise_quintile"] = {str(q + 1): cell(tr, win & (sqa == q)) for q in range(5)}
        res["D_surprise_median_by_group"] = {"quiet": float(np.median(surprise[quiet])), "rest": float(np.median(surprise[rest]))}
        hi_s = surprise >= np.median(surprise[win])
        res["D_quiet_x_surprise"] = {"quiet_high": cell(tr, quiet & hi_s), "quiet_low": cell(tr, quiet & ~hi_s),
                                     "rest_high": cell(tr, rest & hi_s), "rest_low": cell(tr, rest & ~hi_s)}
        # E: the rotation null for quiet - rest (tier series rotated across sessions against the fixed trades)
        tser = pd.Series(tier, index=sess)
        fin_s = tser.dropna()
        tv, ts_ = fin_s.to_numpy(), fin_s.index
        pos = pd.Series(np.arange(len(ts_)), index=ts_).reindex(tr["session"]).to_numpy()
        okp = np.isfinite(pos)
        netv = (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)
        diffs = []
        for kk in range(21, len(tv) - 21):
            rt = np.roll(tv, kk)
            tt = np.full(len(tr), np.nan)
            tt[okp] = rt[pos[okp].astype(int)]
            q_, r_ = okp & (tt < 1 / 3), okp & (tt >= 1 / 3)
            diffs.append(netv[q_].mean() - netv[r_].mean())
        diffs = np.array(diffs)
        actual = float(netv[quiet].mean() - netv[rest].mean())
        res["E_rotation_null"] = {"quiet_minus_rest": actual, "p50": float(np.median(diffs)), "p95": float(np.quantile(diffs, 0.95)),
                                  "p975": float(np.quantile(diffs, 0.975)), "rank": float((diffs < actual).mean()), "offsets": int(len(diffs))}
        # F: cost by tier; exits
        res["F_cost_bp"] = {"quiet": float(tr["cost_bp"].to_numpy(float)[quiet].mean()), "rest": float(tr["cost_bp"].to_numpy(float)[rest].mean())}
        res["F_E2_by_tier"] = {"quiet": cell(tr, quiet, "E2_gross"), "rest": cell(tr, rest, "E2_gross")}
        res["headline"] = {"quiet": cell(tr, quiet), "rest": cell(tr, rest)}
        if r == "ES":
            res["ES_longs_only"] = {"quiet": cell(tr, quiet & (D > 0)), "middle": cell(tr, win & (tb == 1) & (D > 0)),
                                    "top": cell(tr, win & (tb == 2) & (D > 0))}
        out["roots"][r] = res
    out["cells_computed"] = N_CUTS["n"]
    M.T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT, "cells", N_CUTS["n"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
