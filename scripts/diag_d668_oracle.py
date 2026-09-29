"""D668 development (ES, NQ): the oracle (the principal, 2026-09-29: "an oracle version, where when all conditions are
true and you only take profitable trades"). HINDSIGHT, a ceiling only: nothing here is tradeable or selects anything.
Post hoc, in-sample, through the D668 runner's functions and seeds (reproduces ab49940e). Statistics only; dealer
gamma (GEX): SqueezeMetrics.

    uv run python scripts/diag_d668_oracle.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

The four conditions (D666 s.5's confluences plus dealer gamma), each signed by the trade and known at the entry:
  gap   D x overnight gap > 0.10 ATR          gamma  dealers short gamma (prior row)
  a7    D x large-lot signed share > 0         tick   D x constituent TICK z > 0.5
Per root:
  A  realised, by the number of conditions met (0-4), and "all four": trades a year, gross, net, win, $ a year.
  B  the perfect oracle: only the trades that closed net-profitable, on all breaks and inside "all four".
  C  a partial oracle: a score that ranks profitable above unprofitable trades with AUC a (a = 0.55 ... 0.90; the
     label plus Gaussian noise, 500 draws), trading the top half; and the AUC our walk-forward predictor achieved.
  D  by year: all breaks, "all four", and the perfect oracle.
Writes data/diag_d668_oracle.json.
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
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d668_break_predictor as M  # noqa: E402

OUT = REPO / "data" / "diag_d668_oracle.json"
AUCS = (0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.90)
N_DRAW = 500


def book(net: np.ndarray, gross: np.ndarray, usd: np.ndarray, k: np.ndarray, years: float, R) -> dict:
    n = int(k.sum())
    if n == 0:
        return {"trades": 0}
    out = {"trades": n, "trades_per_year": n / years, "gross_mean": float(gross[k].mean()), "net_mean": float(net[k].mean()),
           "net_median": float(np.median(net[k])), "win": float((net[k] > 0).mean()), "usd_per_year": float(usd[k].sum() / years)}
    if n > 5:
        out["t_net"] = float(R.nw_t(net[k])[0])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    active = M.DEV
    costs = M.micro_costs()
    b, use, Gd, R = M.load_bars(a.data_root, False, active)
    M.T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=active)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(a.data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < M.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    frames, short = {}, {}
    for r in active:
        d = M.T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = M.T.gex_prior(gex, d.index)
        short[r] = ((Gd["NQ"].reindex(d.index) < 0) if r == "NQ" else (d["gd_spx"] < 0)).fillna(False)
        frames[r] = d
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, M.TICK_PTS[r], M.SEED + M.ROOTS.index(r))
            for r in active]
    with ProcessPoolExecutor(max_workers=2) as pool:
        got = {o["root"]: o for o in pool.map(M.root_trades, jobs)}
        ex = dict(pool.map(M.T.extract_job, [(s, str(M.T.SC_DATA / f"{s}.scid")) for s in ("TICK-SP", "TICK-NQ")]))
    a7 = pd.read_csv(M.A7_FILES[("ES", "NQ")], encoding="utf-8", dtype={"session": str})
    a7 = a7[a7["session"] < M.RESERVED_FROM]
    committed = json.loads((REPO / "data" / "stage0_d668_dev_es_nq.json").read_text(encoding="utf-8"))["roots"]
    out = {"spec": "post hoc ORACLE (hindsight ceiling) on D668 development (ab49940e)",
           "credit": "dealer gamma (GEX): SqueezeMetrics", "roots": {}}
    rng = np.random.default_rng(6682)
    for r in active:
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        rows = pd.DataFrame({"D": tr["D"].to_numpy(), "eb": tr["minute"].to_numpy()}, index=tr["session"].to_numpy())
        sym = M.TICK_SYMS[r][0]
        gt = {"tick": M.T.gate_f(ex[sym], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
        tz = M.T.shocks(rows, "09:30", ex[sym], None, None, gt)["s_tick"].astype(float)
        F = M.features(tr, r, frames[r], a7[a7["root"] == r], tz, short[r])
        gross = tr["E4_gross"].to_numpy(float)
        net = gross - tr["cost_bp"].to_numpy(float)
        if abs(gross.mean() - committed[r]["gate1"]["gross_mean"]) > 1e-9:
            raise SystemExit(f"{r}: does not reproduce the committed development run")
        P = M.predictor(F[list(M.FEATS)].to_numpy(float), gross, tr["cost_bp"].to_numpy(float))
        usd = net / 1e4 * tr["entry"].to_numpy(float) * costs[r]["usd_per_point"]
        years = len(frames[r]) / 252
        cond = pd.DataFrame({"gap": F["gap"].to_numpy() > 0.10, "gamma": F["short_gamma"].to_numpy() > 0,
                             "a7": F["a7"].to_numpy() > 0, "tick": F["tick"].to_numpy() > 0.5})
        cnt = cond.sum(axis=1).to_numpy()
        allc = cnt == 4
        prof = net > 0
        ones = np.ones(len(tr), bool)
        A = {"condition_share": {c: float(cond[c].mean()) for c in cond},
             "by_count": {str(k): book(net, gross, usd, cnt == k, years, R) for k in range(5)},
             "all_four": book(net, gross, usd, allc, years, R), "all_breaks": book(net, gross, usd, ones, years, R)}
        # each condition alone, met vs not met
        A["each_condition"] = {c: {"met": book(net, gross, usd, cond[c].to_numpy(), years, R),
                                   "not_met": book(net, gross, usd, ~cond[c].to_numpy(), years, R)} for c in cond}
        # every combination of required conditions (15 non-empty subsets): post hoc, a multiplicity of 15 per root
        from itertools import combinations
        A["combinations_required"] = {"+".join(cs): book(net, gross, usd, cond[list(cs)].all(axis=1).to_numpy(), years, R)
                                      for k in range(1, 5) for cs in combinations(cond.columns, k)}
        A["gap_gamma_tick_without_a7"] = book(net, gross, usd, (cond["gap"] & cond["gamma"] & cond["tick"] & ~cond["a7"]).to_numpy(), years, R)
        B = {"all_breaks_profitable_only": book(net, gross, usd, prof, years, R),
             "all_four_profitable_only": book(net, gross, usd, allc & prof, years, R),
             "share_profitable": float(prof.mean())}
        # C: a partial oracle of AUC a, trading the top half of its score
        C = {}
        for auc in AUCS:
            sig = 1.0 / (math.sqrt(2) * stats.norm.ppf(auc))
            nets, wins, achieved = [], [], []
            for _ in range(N_DRAW):
                s = prof.astype(float) + rng.normal(0, sig, len(prof))
                k = s >= np.median(s)
                nets.append(net[k].mean())
                wins.append((net[k] > 0).mean())
                achieved.append(roc_auc_score(prof, s))
            C[f"{auc:.2f}"] = {"net_mean_top_half": float(np.mean(nets)), "win_top_half": float(np.mean(wins)),
                               "usd_per_year_top_half": float(np.mean(nets) / 1e4 * tr["entry"].mean() * costs[r]["usd_per_point"]
                                                               * (len(tr) / 2) / years),
                               "auc_achieved": float(np.mean(achieved))}
        f = np.isfinite(P["yhat"])
        C["our_predictor_auc_on_profitable"] = float(roc_auc_score(prof[f], P["yhat"][f])) if f.sum() > 10 else float("nan")
        C["conditions_count_auc_on_profitable"] = float(roc_auc_score(prof, cnt))
        yrs = tr["session"].str[:4].to_numpy()
        D = {y: {"all_breaks": book(net, gross, usd, yrs == y, 1.0, R),
                 "all_four": book(net, gross, usd, (yrs == y) & allc, 1.0, R),
                 "oracle_profitable_only": book(net, gross, usd, (yrs == y) & prof, 1.0, R)} for y in sorted(set(yrs))}
        out["roots"][r] = {"A_conditions_realised": A, "B_perfect_oracle": B, "C_partial_oracle": C, "D_by_year": D}
    M.T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
