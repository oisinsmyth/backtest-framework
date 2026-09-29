"""D668 development (ES, NQ): trades a year, a breakdown by year and a statistical analysis (the principal, 2026-09-29:
"How many trades a year? do a breakdown by year and a statistical analysis of the results"). Post hoc, in-sample,
through the D668 runner's own functions and seeds; it reproduces data/stage0_d668_dev_es_nq.json's means before
reporting. Statistics only (licence-guarded); dealer gamma (GEX): SqueezeMetrics.

    uv run python scripts/diag_d668_dev_years.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

Per root, for the unfiltered break and the predictor-filtered book (E4, 1 micro):
  by year: trades, long share, gross / net mean, median net, win rate, payoff, t, sum of net bp, $ net per micro,
           the year's daily $ Sharpe, and the N1 null's mean that year (same clock, same side mix) and the excess.
  overall: trades a year, mean with HAC t and a trade bootstrap 95% CI, the t across YEARLY means (robust to
           within-year dependence), years positive with a sign-test p, without the best / worst year, top-trade
           concentration, lag-1 autocorrelation, $ drawdown and the longest time under water.
Writes data/diag_d668_dev_years.json.
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

OUT = REPO / "data" / "diag_d668_dev_years.json"
B_BOOT = 10_000


def year_rows(tr: pd.DataFrame, mask: np.ndarray, usd_pt: float, sessions: pd.Index, null_by_year: dict[str, float],
              R) -> dict[str, dict]:
    g, net = tr["E4_gross"].to_numpy(float), (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)
    usd = net / 1e4 * tr["entry"].to_numpy(float) * usd_pt
    yrs = tr["session"].str[:4].to_numpy()
    out = {}
    for y in sorted(set(yrs)):
        k = mask & (yrs == y)
        ses_y = sessions[sessions.str.startswith(y)]
        daily = pd.Series(usd[k], index=tr["session"].to_numpy()[k]).reindex(ses_y, fill_value=0.0)
        n = int(k.sum())
        row = {"trades": n, "sessions": int(len(ses_y))}
        if n:
            w, lo = net[k][net[k] > 0], net[k][net[k] <= 0]
            row.update({"long_share": float((tr["D"].to_numpy()[k] > 0).mean()), "gross_mean": float(g[k].mean()),
                        "net_mean": float(net[k].mean()), "net_median": float(np.median(net[k])),
                        "win": float((net[k] > 0).mean()),
                        "payoff": float(w.mean() / -lo.mean()) if len(w) and len(lo) and lo.mean() < 0 else float("nan"),
                        "t_gross": float(g[k].mean() / (g[k].std(ddof=1) / math.sqrt(n))) if n > 2 and g[k].std(ddof=1) > 0 else float("nan"),
                        "sum_net_bp": float(net[k].sum()), "usd_net_per_micro": float(usd[k].sum()),
                        "daily_sharpe_net": float(daily.mean() / daily.std(ddof=1) * math.sqrt(252)) if daily.std(ddof=1) > 0 else float("nan")})
            if y in null_by_year:
                row["n1_null_mean"] = null_by_year[y]
                row["gross_minus_null"] = row["gross_mean"] - null_by_year[y]
        out[y] = row
    return out


def overall(tr: pd.DataFrame, mask: np.ndarray, usd_pt: float, sessions: pd.Index, rng: np.random.Generator, R) -> dict:
    g, net = tr["E4_gross"].to_numpy(float)[mask], (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)[mask]
    usd = net / 1e4 * tr["entry"].to_numpy(float)[mask] * usd_pt
    yrs = tr["session"].str[:4].to_numpy()[mask]
    full = sorted({y for y in yrs if y != "2025"})  # 2025 is two months; the year statistics use full years
    out = {"trades": int(mask.sum()), "trades_per_year": float(mask.sum() / (len(sessions) / 252)),
           "long_share": float((tr["D"].to_numpy()[mask] > 0).mean())}
    for name, x in (("gross", g), ("net", net)):
        t, se = R.nw_t(x)
        boot = np.array([rng.choice(x, len(x)).mean() for _ in range(B_BOOT)])
        ym = np.array([x[yrs == y].mean() for y in full])
        pos = int((ym > 0).sum())
        best, worst = full[int(np.argmax(ym))], full[int(np.argmin(ym))]
        out[name] = {"mean": float(x.mean()), "t_hac": float(t), "boot_ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
                     "yearly_means_t": float(ym.mean() / (ym.std(ddof=1) / math.sqrt(len(ym)))) if len(ym) > 2 else float("nan"),
                     "full_years": len(full), "years_positive": pos,
                     "sign_test_p_one_sided": float(stats.binomtest(pos, len(full), 0.5, alternative="greater").pvalue),
                     "without_best_year": {"year": best, "mean": float(x[yrs != best].mean())},
                     "without_worst_year": {"year": worst, "mean": float(x[yrs != worst].mean())}}
    srt = np.sort(net)[::-1]
    tot = net.sum()
    out["concentration"] = {f"top_{p}pct_share_of_net": float(srt[:max(1, int(round(p / 100 * len(srt))))].sum() / tot) if tot else float("nan")
                            for p in (1, 5, 10)}
    out["lag1_autocorr_net"] = float(np.corrcoef(net[:-1], net[1:])[0, 1]) if len(net) > 3 else float("nan")
    daily = pd.Series(usd, index=tr["session"].to_numpy()[mask]).reindex(sessions, fill_value=0.0)
    cum = daily.cumsum().to_numpy()
    peak = np.maximum.accumulate(np.r_[0.0, cum])[1:]
    under = cum < peak
    runs, cur = [], 0
    for u in under:
        cur = cur + 1 if u else 0
        runs.append(cur)
    out["usd_per_micro"] = {"total": float(cum[-1]), "per_year": float(cum[-1] / (len(sessions) / 252)),
                            "max_drawdown": float((peak - cum).max()), "longest_underwater_sessions": int(max(runs) if runs else 0),
                            "daily_sharpe": float(daily.mean() / daily.std(ddof=1) * math.sqrt(252)),
                            "daily_sortino": float(daily.mean() / math.sqrt(float(np.mean(np.minimum(daily, 0) ** 2))) * math.sqrt(252))}
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
    out = {"spec": "post hoc: D668 development by year (ab49940e)", "credit": "dealer gamma (GEX): SqueezeMetrics", "roots": {}}
    rng = np.random.default_rng(6681)
    for r in active:
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        rows = pd.DataFrame({"D": tr["D"].to_numpy(), "eb": tr["minute"].to_numpy()}, index=tr["session"].to_numpy())
        sym = M.TICK_SYMS[r][0]
        gt = {"tick": M.T.gate_f(ex[sym], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
        tz = M.T.shocks(rows, "09:30", ex[sym], None, None, gt)["s_tick"].astype(float)
        F = M.features(tr, r, frames[r], a7[a7["root"] == r], tz, short[r])
        P = M.predictor(F[list(M.FEATS)].to_numpy(float), tr["E4_gross"].to_numpy(float), tr["cost_bp"].to_numpy(float))
        net = (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)
        c = committed[r]
        if abs(tr["E4_gross"].mean() - c["gate1"]["gross_mean"]) > 1e-9 or int(P["take"].sum()) != c["gate2"]["filtered_trades"] \
                or (P["take"].any() and abs(net[P["take"]].mean() - c["gate2"]["filtered_net_mean"]) > 1e-9):
            raise SystemExit(f"{r}: does not reproduce the committed development run")
        # N1's null mean per year, from the same pool (same clock, same side mix)
        pool, ps = got[r]["pool"], np.array(got[r]["pool_sessions"])
        null_by_year = {y: float(np.nanmean(pool[np.char.startswith(ps.astype(str), y)])) for y in sorted({s[:4] for s in ps})}
        usd_pt = costs[r]["usd_per_point"]
        ses = frames[r].index
        allm = np.ones(len(tr), bool)
        out["roots"][r] = {
            "unfiltered": {"overall": overall(tr, allm, usd_pt, ses, rng, R),
                           "by_year": year_rows(tr, allm, usd_pt, ses, null_by_year, R)},
            "filtered": {"overall": overall(tr, P["take"], usd_pt, ses, rng, R) if P["take"].sum() > 5 else {"trades": int(P["take"].sum())},
                         "by_year": year_rows(tr, P["take"], usd_pt, ses, {}, R),
                         "note": "the predictor forecasts from the 251st trade and trades from 40 forecasts later (mid-2017 on)"}}
    M.T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=lambda v: round(v, 3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
