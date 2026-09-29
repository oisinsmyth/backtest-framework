"""D663 post hoc diagnostic (after its RESULT; changes no verdict): mechanics, a statistical review and the edge of the
per-root break x gamma construction. In-sample only through D663's own sealed functions; SqueezeMetrics GEX (credited;
licence-guarded output: statistics only, no per-date series).

    uv run python scripts/diag_d663.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

A  MECHANICS -- do the inputs measure what they claim?
   A1 SPX GEX (prior row) against the carried ES book's gamma (D662's g): correlation, sign agreement, short shares.
   A2 measure validity: does short gamma predict a LARGER move (the damping literature), whatever its direction?
      |F| and the 10:00-16:00 range over the opening range, on g, per root and measure.
   A3 the shock: TICK-SP / TICK-NQ window mean (unsigned) against the root's own move from the open to the entry.
B  STATISTICAL REVIEW
   B1 ES: F on g_spx and g_es_carried jointly. B2 the post-0DTE era alone, with its own purged rotation.
   B3 the tally of break x gamma cells tested (D662 + D663). B4 power: MDE against the slope an edge would need.
C  THE EDGE
   C1 the break trade itself (60-min, no stop), gross and net of the micro round trip, per root.
   C2 net per trade by g quintile, per root and measure; the top quintile's t.
   C3 the slope needed for the top g quintile to clear cost + the vault's 80%-power MDE, against the observed slope.
Writes data/diag_d663.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402
import stage0_d663_per_root_gamma_break as T  # noqa: E402

OUT = REPO / "data" / "diag_d663.json"
Z80 = 1.959964 + 0.841621


def slope_t(y: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    m = np.isfinite(y) & np.isfinite(x)
    f = S.hac(y[m], x[m][:, None])
    return float(f.params[1]), float(f.tvalues[1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(a.data_root, False)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(a.data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < T.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    syms = [T.SHOCK_SYMS["ES"]["tick"], T.SHOCK_SYMS["NQ"]["tick"]]
    with ProcessPoolExecutor(max_workers=2) as pool:
        ex = dict(pool.map(T.extract_job, [(s, str(T.SC_DATA / f"{s}.scid")) for s in syms]))
    for e in ex.values():
        T.assert_sealed(e)
    out: dict = {"spec": "post hoc diagnostic of D663 (64fc0bb)", "credit": "dealer gamma (GEX): SqueezeMetrics",
                 "A": {}, "B": {}, "C": {}}
    frames, rows = {}, {}
    for r in ("ES", "NQ"):
        d = T.root_frame(b, tabs[r], r)
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        d["g_spx"] = -d["gd_spx"] / d["V20"] * 100
        d["gd_own"] = Gd[r].reindex(d.index) * T.MULT[r] * d["prior_close"] ** 2 * 0.01
        d["g_own"] = -d["gd_own"] / d["V20"] * 100
        gt = {"tick": T.gate_f(ex[T.SHOCK_SYMS[r]["tick"]], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
        br = T.breaks(d, bars, r, S.MORNING)
        T.b3_check(r, br, d, bars, R)
        br = br.join(T.shocks(br, "09:30", ex[T.SHOCK_SYMS[r]["tick"]], None, None, gt)).join(
            d[["g_spx", "g_own", "gd_spx", "gd_own", "open", "prior_close"]])
        # the day's expansion after 10:00 over the opening range (a size measure, no direction)
        exp_ = {}
        for s_ in br.index:
            bb = bars[(r, s_)]
            aft = bb["m"] >= T.hm("10:00")
            orng = float(d.at[s_, "hi_10:00"] - d.at[s_, "lo_10:00"])
            exp_[s_] = (bb["h"][aft].max() - bb["l"][aft].min()) / orng if aft.any() and orng > 0 else np.nan
        br["expansion"] = pd.Series(exp_)
        br["ret_open_entry"] = np.log(br["entry"] / br["open"]) * 1e4
        br["cost_bp"] = R.COST_USD[r] / R.USD_PER_POINT[r] / br["entry"] * 1e4
        frames[r], rows[r] = d, br

    # ---------------- A
    d = frames["ES"]
    both = d[["g_spx", "g_own"]].dropna()
    out["A"]["A1_es_gamma_measures"] = {
        "n": int(len(both)), "corr_levels": float(both.corr().iloc[0, 1]),
        "corr_ranks": float(both.rank().corr().iloc[0, 1]),
        "sign_agreement": float((np.sign(both["g_spx"]) == np.sign(both["g_own"])).mean()),
        "short_share_spx": float((both["g_spx"] > 0).mean()), "short_share_es_carried": float((both["g_own"] > 0).mean())}
    val = {}
    for r in ("ES", "NQ"):
        br = rows[r]
        for gcol in ("g_spx", "g_own"):
            y1, x = np.abs(br["F"].to_numpy(float)), br[gcol].to_numpy(float)
            y2 = np.log(br["expansion"].to_numpy(float))
            b1, t1 = slope_t(y1, x)
            b2, t2 = slope_t(y2, x)
            q = pd.qcut(pd.Series(x).rank(method="first"), 5, labels=False).to_numpy()
            ok = np.isfinite(x)
            val[f"{r}_{gcol}"] = {"absF_on_g": {"b": b1, "t": t1}, "log_expansion_on_g": {"b": b2, "t": t2},
                                  "absF_by_g_quintile": {int(k): float(np.nanmean(y1[ok & (q == k)])) for k in range(5)},
                                  "note": "g > 0 = dealers short gamma; the damping literature predicts b > 0"}
    out["A"]["A2_measure_validity_size"] = val
    # A2b: is gamma's size prediction only volatility persistence? |F| on g AND the prior 20 sessions' daily sigma.
    ctl = {}
    for r in ("ES", "NQ"):
        br = rows[r].join(frames[r][["sig20"]])
        for gcol in ("g_spx", "g_own"):
            m = np.isfinite(br[gcol]) & np.isfinite(br["sig20"])
            y = np.abs(br.loc[m, "F"].to_numpy(float))
            X = np.column_stack([br.loc[m, gcol].to_numpy(float), br.loc[m, "sig20"].to_numpy(float)])
            fj = S.hac(y, X)
            ctl[f"{r}_{gcol}"] = {"n": int(m.sum()), "b_g": float(fj.params[1]), "t_g": float(fj.tvalues[1]),
                                  "b_sig20": float(fj.params[2]), "t_sig20": float(fj.tvalues[2]),
                                  "corr_g_sig20": float(np.corrcoef(X[:, 0], X[:, 1])[0, 1])}
    out["A"]["A2b_size_beyond_trailing_vol"] = ctl
    sh = {}
    for r in ("ES", "NQ"):
        br = rows[r]
        unsigned = br["s_tick"] * br["D"]
        m = np.isfinite(unsigned) & np.isfinite(br["ret_open_entry"])
        sh[r] = {"corr_tick_vs_move_open_to_entry": float(np.corrcoef(unsigned[m], br["ret_open_entry"][m])[0, 1]),
                 "signed_shock_mean": float(np.nanmean(br["s_tick"])), "n": int(m.sum())}
    out["A"]["A3_shock_tracks_the_move"] = sh

    # ---------------- B
    br = rows["ES"].dropna(subset=["g_spx", "g_own"])
    f = S.hac(br["F"].to_numpy(float), br[["g_spx", "g_own"]].to_numpy(float))
    out["B"]["B1_es_joint"] = {"n": int(len(br)), "b_spx": float(f.params[1]), "t_spx": float(f.tvalues[1]),
                               "b_es_carried": float(f.params[2]), "t_es_carried": float(f.tvalues[2])}
    era = {}
    for r, gcol in (("ES", "g_spx"), ("ES", "g_own"), ("NQ", "g_own"), ("NQ", "g_spx")):
        dd = frames[r]
        post = dd.index >= "2022-05-16"
        fin = dd.index[post & np.isfinite(dd[gcol])]
        rr = rows[r][rows[r].index.isin(fin)]
        h = T.h1(rr, gcol, list(fin), dd.loc[fin, gcol])
        era[f"{r}_{gcol}"] = {"n": h["n"], "b1": h["b1"], "t": h["t"], "rank": h["rotation"]["rank"],
                              "p95": h["rotation"]["p95"]}
    out["B"]["B2_post_0dte_only"] = era
    out["B"]["B3_break_x_gamma_cells_tested"] = {
        "D662_preregistered": 2, "D662_post_hoc": 1, "D663_preregistered": 4, "D663_controls": 2,
        "any_supported": False,
        "note": "the one t above 2 (D662 post hoc, ES carried, t 2.30) came from ten reported statistics"}

    # ---------------- C
    for r in ("ES", "NQ"):
        br = rows[r]
        net = br["F"] - br["cost_bp"]
        cell = {"trades": int(len(br)), "gross_mean": float(br["F"].mean()), "net_mean": float(net.mean()),
                "net_t": float(net.mean() / (net.std(ddof=1) / math.sqrt(len(net)))), "cost_bp_median": float(br["cost_bp"].median()),
                "by_g_quintile": {}}
        sessions_in = len(frames[r])
        for gcol in ("g_spx", "g_own"):
            x = br[gcol]
            ok = np.isfinite(x)
            q = pd.qcut(x[ok].rank(method="first"), 5, labels=False)
            by = net[ok].groupby(q.to_numpy())
            top = net[ok][q.to_numpy() == 4]
            b1, _ = slope_t(br["F"].to_numpy(float), x.to_numpy(float))
            gq = x[ok].groupby(q.to_numpy()).mean()
            spread = float(gq.iloc[4] - x[ok].mean())  # how far the top quintile's g sits above the mean
            n_top_vault = len(top) * 390 / sessions_in
            mde_top = Z80 * float(top.std(ddof=1)) / math.sqrt(n_top_vault)
            need = (float(br["cost_bp"].median()) + mde_top - float(br["F"].mean())) / spread if spread > 0 else float("nan")
            cell["by_g_quintile"][gcol] = {
                "net_by_quintile": {int(k): float(v) for k, v in by.mean().items()},
                "top_net_mean": float(top.mean()), "top_net_t": float(top.mean() / (top.std(ddof=1) / math.sqrt(len(top)))),
                "top_trades": int(len(top)), "g_top_minus_mean": spread,
                "slope_observed": b1, "slope_needed_for_top_quintile_to_clear_cost_plus_vault_mde": need,
                "vault_mde_top_net": mde_top}
        out["C"][r] = cell
    T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=lambda v: round(v, 4)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
