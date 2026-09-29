"""D668 development (ES, NQ): the SIZE oracle (the principal, 2026-09-29: "Go for the oracles", after the five-lane
note docs/research/opening-break-predictor-lanes.md). HINDSIGHT, a ceiling only: it prices a perfect or partial
forecast of how BIG the day is (never its direction; the break keeps choosing the side). Post hoc, in-sample, through
the D668 runner's functions and seeds (reproduces ab49940e). Statistics only.

    uv run python scripts/diag_d668_size_oracle.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

Day size, known only after the close: R = RTH (high - low) / ATR20 (primary); T = |close - open| / ATR20 (the trend-day
statistic). Per root:
  A  E4 by quintile of R (and of T), quintiles over ALL sessions: trades, gross, net, P(hold) (never back to yesterday's
     level; the retest split of D681), win rate, gain-if-hold, loss-if-fail.
  B  the perfect size oracle: trade only the breaks on the top 20 / 40 / 60 % of days by R: trades a year, net, $ a year
     per micro, daily Sharpe, the removed trades' net.
  C  a partial size oracle: a forecast whose Spearman correlation with R over all sessions is rho (0.1 ... 0.6; the
     rank of R plus Gaussian noise, 300 draws), trading the breaks on days in the forecast's top half (and top 40 %):
     net, $ a year, and the hold rate of the kept trades (a size forecast must not need direction).
  D  by year: all breaks against the top-40 % perfect size oracle.
Writes data/diag_d668_size_oracle.json.
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
import stage0_d668_break_predictor as M  # noqa: E402

OUT = REPO / "data" / "diag_d668_size_oracle.json"
RHOS = (0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6)
N_DRAW = 300


def retest(bb: dict, i: int, D: int, L: float) -> bool:
    """Did price come back to yesterday's level after the entry (the D681 split)? Hindsight."""
    m, h, l = bb["m"], bb["h"], bb["l"]
    after = np.arange(i + 1, len(m))
    after = after[m[after] <= M.X.LAST_ENTRY]
    return bool(len(after) and ((l[after] <= L).any() if D > 0 else (h[after] >= L).any()))


def book(tr: pd.DataFrame, k: np.ndarray, years: float, usd_pt: float, sessions: pd.Index) -> dict:
    n = int(k.sum())
    if n == 0:
        return {"trades": 0}
    g, net = tr["E4_gross"].to_numpy(float)[k], tr["net"].to_numpy(float)[k]
    hold = ~tr["retest"].to_numpy(bool)[k]
    usd = net / 1e4 * tr["entry"].to_numpy(float)[k] * usd_pt
    daily = pd.Series(usd, index=tr["session"].to_numpy()[k]).reindex(sessions, fill_value=0.0)
    return {"trades": n, "trades_per_year": n / years, "gross": float(g.mean()), "net": float(net.mean()),
            "p_hold": float(hold.mean()), "win": float((net > 0).mean()),
            "gain_if_hold": float(g[hold].mean()) if hold.any() else float("nan"),
            "loss_if_fail": float(g[~hold].mean()) if (~hold).any() else float("nan"),
            "usd_per_year": float(usd.sum() / years),
            "daily_sharpe": float(daily.mean() / daily.std(ddof=1) * math.sqrt(252)) if daily.std(ddof=1) > 0 else float("nan")}


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
    frames = {}
    for r in active:
        d = M.T.root_frame(b, tabs[r], r)
        frames[r] = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, M.TICK_PTS[r], M.SEED + M.ROOTS.index(r))
            for r in active]
    with ProcessPoolExecutor(max_workers=2) as pool:
        got = {o["root"]: o for o in pool.map(M.root_trades, jobs)}
    committed = json.loads((REPO / "data" / "stage0_d668_dev_es_nq.json").read_text(encoding="utf-8"))["roots"]
    out = {"spec": "post hoc SIZE ORACLE (hindsight ceiling) on D668 development (ab49940e)", "roots": {}}
    rng = np.random.default_rng(6683)
    for r in active:
        d = frames[r]
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        if abs(tr["E4_gross"].mean() - committed[r]["gate1"]["gross_mean"]) > 1e-9:
            raise SystemExit(f"{r}: does not reproduce the committed development run")
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        tr["net"] = tr["E4_gross"] - tr["cost_bp"]
        tr["retest"] = [retest(bars[(r, s)], int(i), int(D), float(L)) for s, i, D, L in zip(tr["session"], tr["i"], tr["D"], tr["L"])]
        Rall = ((d["high"] - d["low"]) / d["atr20"]).astype(float)
        Tall = ((d["close"] - d["open"]).abs() / d["atr20"]).astype(float)
        tr["R"], tr["T"] = Rall.reindex(tr["session"]).to_numpy(), Tall.reindex(tr["session"]).to_numpy()
        years, usd_pt, ses = len(d) / 252, costs[r]["usd_per_point"], d.index
        allk = np.ones(len(tr), bool)
        A = {"all_breaks": book(tr, allk, years, usd_pt, ses),
             "day_size_all_sessions": {"R_median": float(Rall.median()), "T_median": float(Tall.median()),
                                       "R_on_break_days_median": float(tr["R"].median()),
                                       "break_day_share_by_R_quintile": {}}}
        for name, allv, tv in (("R", Rall, tr["R"]), ("T", Tall, tr["T"])):
            qs = np.quantile(allv.dropna(), [0.2, 0.4, 0.6, 0.8])
            qi = np.searchsorted(qs, tv.to_numpy(), side="right")
            A[f"by_{name}_quintile"] = {str(q + 1): book(tr, qi == q, years, usd_pt, ses) for q in range(5)}
            if name == "R":
                qa = np.searchsorted(qs, allv.dropna().to_numpy(), side="right")
                ses_q = pd.Series(qa, index=allv.dropna().index)
                A["day_size_all_sessions"]["break_day_share_by_R_quintile"] = {
                    str(q + 1): float(tr["session"].isin(ses_q.index[ses_q == q]).sum() / max((ses_q == q).sum(), 1)) for q in range(5)}
        # B: the perfect size oracle
        B = {}
        for top in (0.2, 0.4, 0.6):
            thr = float(np.quantile(Rall.dropna(), 1 - top))
            k = tr["R"].to_numpy() >= thr
            B[f"top_{int(top * 100)}pct_days"] = {**book(tr, k, years, usd_pt, ses),
                                                  "removed_net": float(tr["net"].to_numpy()[~k].mean())}
        # C: a partial size oracle of rank correlation rho with R over all sessions
        rv = Rall.dropna()
        z = stats.norm.ppf((rv.rank().to_numpy() - 0.5) / len(rv))
        pos = pd.Series(np.arange(len(rv)), index=rv.index)
        ti = pos.reindex(tr["session"]).to_numpy()
        okt = np.isfinite(ti)
        C = {}
        for rho in RHOS:
            sig = math.sqrt(1 / rho ** 2 - 1)  # corr(z, z + e) = rho for e ~ N(0, sig^2); Spearman ~ this for normal scores
            res = {"top50": [], "top40": [], "hold50": [], "usd50": [], "sp": []}
            for _ in range(N_DRAW):
                f = z + rng.normal(0, sig, len(z))
                res["sp"].append(stats.spearmanr(f, rv.to_numpy())[0])
                ft = np.full(len(tr), np.nan)
                ft[okt] = f[ti[okt].astype(int)]
                for key, top in (("top50", 0.5), ("top40", 0.4)):
                    k = okt & (ft >= np.quantile(f, 1 - top))
                    bk = book(tr, k, years, usd_pt, ses)
                    res[key].append(bk["net"])
                    if key == "top50":
                        res["hold50"].append(bk["p_hold"])
                        res["usd50"].append(bk["usd_per_year"])
            C[f"{rho:.2f}"] = {"spearman_achieved": float(np.mean(res["sp"])), "net_top50": float(np.mean(res["top50"])),
                               "net_top40": float(np.mean(res["top40"])), "p_hold_top50": float(np.mean(res["hold50"])),
                               "usd_per_year_top50": float(np.mean(res["usd50"])),
                               "net_top50_p05_p95": [float(np.quantile(res["top50"], 0.05)), float(np.quantile(res["top50"], 0.95))]}
        # D: by year, all breaks vs the top-40 % perfect size oracle
        thr40 = float(np.quantile(Rall.dropna(), 0.6))
        yrs = tr["session"].str[:4].to_numpy()
        Dy = {y: {"all": book(tr, yrs == y, 1.0, usd_pt, ses[ses.str.startswith(y)]),
                  "oracle_top40": book(tr, (yrs == y) & (tr["R"].to_numpy() >= thr40), 1.0, usd_pt, ses[ses.str.startswith(y)])}
              for y in sorted(set(yrs))}
        out["roots"][r] = {"A_by_day_size": A, "B_perfect_size_oracle": B, "C_partial_size_oracle": C, "D_by_year": Dy}
    M.T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
