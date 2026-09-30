"""D713 DIAG -- the MES oracle profile of E (D708's hourly continuation on ES-book short-gamma days). Hindsight and
descriptive only: nothing is fitted, filtered, traded or gated. Design: docs/decisions/D713-DIAG-DESIGN-the-mes-oracle-
profile-of-e.md (04782293, before this runner). The principal: "No go get me the oracle first".

    uv run python scripts/diag_d713_e_oracle_mes.py --run --data-root "<main checkout>/data"

THE CANDIDATES: E through D712's rule path (ES sessions >= 380 bars with G_ES < 0; t = 10:30 .. 14:30 on D689's grid;
side = sign of the last 60 minutes; A1; held 60 minutes). One MES: gross = s (P(t+60) - P(t)) x $5, net = gross - $4.42.
WIN = net > 0; BAR = gross >= $8.84. Every bucket: trades, a year, WIN/BAR rates and lifts, mean gross (day-clustered t),
mean net, the timing term T (D708's per-(year, clock) drift), winners' and losers' mean net, share of the oracle's net.
Plus the hold-length profile (+60, +120 capped at 16:00, to 16:00; and one-a-day 10:30 and 13:30 held to 16:00).
Output data/d713_e_oracle_mes.json: statistics only, no per-date GEX.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import vault_d712_short_gamma_timing as V   # noqa: E402  (D712's rule path; in-sample functions only)

R = V.R
OUT = REPO / "data" / "d713_e_oracle_mes.json"
D712_POWER = REPO / "data" / "vault_d712_power.json"
COST, BAR = 4.42, 8.84
CLOCKS, JS, STEP = V.CLOCKS, V.JS, V.STEP
CLOSE_J = 78


def P(*a, **k):
    print(*a, **k, flush=True)


def terciles(x):
    q = np.nanquantile(x, [1 / 3, 2 / 3])
    return np.where(np.isnan(x), -1, np.digitize(x, q)), [float(v) for v in q]


def quintiles(x):
    q = np.nanquantile(x, [0.2, 0.4, 0.6, 0.8])
    return np.where(np.isnan(x), -1, np.digitize(x, q)), [float(v) for v in q]


def bucket(mask, g, n, tau, di, years, oracle_net_total, base_win, base_bar):
    k = mask
    if k.sum() < 10:
        return {"n": int(k.sum())}
    gg, nn, tt, dd = g[k], n[k], tau[k], di[k]
    win, bar = float((nn > 0).mean()), float((gg >= BAR).mean())
    cg = R.cl_mean(gg, dd)
    ct = R.cl_mean(tt, dd)
    return {"n": int(k.sum()), "per_year": float(k.sum() / years), "win": win, "win_lift": win / base_win, "bar": bar, "bar_lift": bar / base_bar,
            "mean_gross": cg["mean"], "t_gross": cg["t"], "median_gross": float(np.median(gg)), "mean_net": float(nn.mean()),
            "T_timing": ct["mean"], "t_T": ct["t"], "winners_mean_net": float(nn[nn > 0].mean()) if (nn > 0).any() else None,
            "losers_mean_net": float(nn[nn <= 0].mean()) if (nn <= 0).any() else None,
            "share_of_oracle_net": float(nn[nn > 0].sum() / oracle_net_total)}


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    Rr = V.load_rule(data_root, V.IN_FROM, V.IN_END, log=log)
    A = V.rows(Rr["PG"])
    days, G, PG = Rr["days"], Rr["G_ES"], Rr["PG"]
    pop = G < 0
    o = V.score_span(A, days, pop, V.IN_FROM, V.IN_END)
    want = json.loads(D712_POWER.read_text(encoding="utf-8"))["known_answer"]
    if o["trades"] != want["rule_path_in_sample"]["trades"] or o["T"]["mean"] != want["rule_path_in_sample"]["T"]["mean"]:
        raise V.D712Error(f"[REPRO] the rule path's T {o['T']} differs from D712's {want['rule_path_in_sample']['T']}")
    log(f"  E reproduced: {o['trades']} trades, T ${o['T']['mean']:.4f} (D712's rule path)")
    a = o["_arrays"]
    s, di, ci, tau = a["s"], a["di"], a["ci"], a["tau"]
    g = a["gross"]; n = g - COST
    if not np.allclose(n, a["net"]):
        raise V.D712Error("[COST] the net is not gross - $4.42")
    nd = len(days)
    years = len(np.unique([d[:4] for d in days[pop]]))
    yr = np.array([days[d][:4] for d in di])
    # predictors, all known at t (hindsight edges)
    L = np.log(PG)
    dayret = L[:, CLOSE_J] - L[:, 0]
    sig_d = pd.Series(dayret).rolling(20, min_periods=15).std().shift(1).to_numpy()   # prior-only, every rule-path session
    sig_h = sig_d * math.sqrt(60 / 390) * 1e4
    j = np.array([JS[c] for c in ci])
    m = np.log(PG[di, j] / PG[di, j - STEP]) * 1e4
    if not np.array_equal(np.sign(m), s):
        raise V.D712Error("[LAG] the side re-derived from the grid differs from the rule path's")
    msz = np.abs(m) / sig_h[di]
    r5 = 1e4 * np.diff(L, axis=1)
    cum = np.concatenate([np.zeros((nd, 1)), np.nancumsum(r5 * r5, axis=1)], axis=1)
    rv = cum[di, j] / j
    day_so_far = L[di, j] - L[di, 0]
    aligned = np.sign(day_so_far) == s
    Gp = G[di]
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", usecols=["date", "gex"], dtype={"date": str}, encoding="utf-8")
    dix = dix[dix["date"] < V.UNSEEN_FROM].sort_values("date")
    dd_ = dix["date"].to_numpy().astype(str)
    jj = np.searchsorted(dd_, days) - 1
    gspx = np.where(jj >= 0, dix["gex"].to_numpy(float)[np.maximum(jj, 0)], np.nan)
    gsum_short = (gspx + G)[di] < 0
    price = a["P"]
    oracle_total = float(n[n > 0].sum())
    base_win, base_bar = float((n > 0).mean()), float((g >= BAR).mean())
    B = lambda k: bucket(k, g, n, tau, di, years, oracle_total, base_win, base_bar)  # noqa: E731
    prof: dict = {}
    prof["all"] = B(np.ones(len(g), bool))
    prof["1_clock"] = {c: B(ci == i) for i, c in enumerate(CLOCKS)}
    prof["2_side"] = {"long": B(s > 0), "short": B(s < 0)}
    prof["2b_clock_x_side"] = {f"{c} {sd}": B((ci == i) & ((s > 0) if sd == "long" else (s < 0))) for i, c in enumerate(CLOCKS) for sd in ("long", "short")}
    qm, em = terciles(msz)
    prof["3_last_hour_size_tercile"] = {"edges": em, **{str(q): B(qm == q) for q in range(3)}}
    qr, er = terciles(rv)
    prof["4_today_rv_tercile"] = {"edges": er, **{str(q): B(qr == q) for q in range(3)}}
    prof["5_alignment"] = {"with_the_day": B(aligned), "against_the_day": B(~aligned & (day_so_far != 0))}
    qg, eg = quintiles(Gp)
    prof["6_G_ES_quintile_0_most_short"] = {str(q): B(qg == q) for q in range(5)}
    prof["6b_SPX_sign"] = {"G_SUM<0": B(gsum_short), "G_SUM>=0": B(~gsum_short)}
    prof["7_year"] = {y: B(yr == y) for y in sorted(set(yr))}
    qp, ep = terciles(price)
    prof["7b_price_tercile"] = {"edges": ep, **{str(q): B(qp == q) for q in range(3)}}
    prof["8_clock_x_size"] = {f"{c} size{q}": B((ci == i) & (qm == q)) for i, c in enumerate(CLOCKS) for q in range(3)}
    def leaves(x):
        return 1 if (isinstance(x, dict) and "n" in x) else sum(leaves(v) for v in x.values()) if isinstance(x, dict) else 0
    n_buckets = leaves(prof) - 1                          # "all" is not a bucket
    rng = np.random.default_rng(713)
    maxz = np.abs(rng.standard_normal((20000, n_buckets))).max(1)
    # the hold-length profile (descriptive; a different construction)
    holds = {}
    for lab, jx in (("E_+60", j + STEP), ("+120", np.minimum(j + 2 * STEP, CLOSE_J)), ("to_16:00", np.full(len(j), CLOSE_J))):
        gh = s * (PG[di, jx] - PG[di, j]) * 5.0
        ok = np.isfinite(gh)
        fg = R.Q.four_groups(gh[ok], gh[ok] - COST, di[ok], s[ok], days, nd, None, COST)
        holds[lab] = {"trades": int(ok.sum()), "mean_gross": R.cl_mean(gh[ok], di[ok]), "win": float((gh[ok] - COST > 0).mean()),
                      "bar": float((gh[ok] >= BAR).mean()), "daily_net_sharpe": fg.get("net", {}).get("sharpe_daily"),
                      "daily_net_sortino": fg.get("net", {}).get("sortino_daily"), "daily_gross_sharpe": fg.get("gross", {}).get("sharpe_daily"),
                      "note": "overlapping positions within a day" if lab != "E_+60" else "E itself"}
    for lab, c in (("10:30_to_16:00_one_a_day", 0), ("13:30_to_16:00_one_a_day", 3)):
        k = ci == c
        gh = s[k] * (PG[di[k], CLOSE_J] - PG[di[k], JS[c]]) * 5.0
        ok = np.isfinite(gh)
        fg = R.Q.four_groups(gh[ok], gh[ok] - COST, di[k][ok], s[k][ok], days, nd, None, COST)
        holds[lab] = {"trades": int(ok.sum()), "per_year": float(ok.sum() / years), "mean_gross": R.cl_mean(gh[ok], di[k][ok]),
                      "mean_net": float((gh[ok] - COST).mean()), "median_net": float(np.median(gh[ok] - COST)),
                      "win": float((gh[ok] - COST > 0).mean()), "bar": float((gh[ok] >= BAR).mean()),
                      "daily_net_sharpe": fg.get("net", {}).get("sharpe_daily"), "daily_net_sortino": fg.get("net", {}).get("sortino_daily"),
                      "daily_gross_sharpe": fg.get("gross", {}).get("sharpe_daily"),
                      "by_year_net": {y: float((gh[ok] - COST)[np.array([days[d][:4] for d in di[k][ok]]) == y].sum()) for y in sorted(set(yr))}}
    res = {"spec": "D713 DIAG: the MES oracle profile of E (hindsight, descriptive)", "design_commit": "04782293",
           "E": {"trades": o["trades"], "sessions": int(pop.sum()), "T": V.strip_arrays(o)["T"], "net_mes": V.strip_arrays(o)["net_mes"]},
           "oracle": {"win_trades": int((n > 0).sum()), "win_rate": base_win, "bar_rate": base_bar, "oracle_net_total": oracle_total,
                      "take_all_net_total": float(n.sum()), "winners_mean_net": float(n[n > 0].mean()), "losers_mean_net": float(n[n <= 0].mean()),
                      "breakeven_win_rate_at_mean_payoff": float(-n[n <= 0].mean() / (n[n > 0].mean() - n[n <= 0].mean()))},
           "multiplicity": {"buckets": n_buckets, "expected_max_abs_t_p50": float(np.median(maxz)), "p95": float(np.quantile(maxz, 0.95))},
           "profile": prof, "holds": holds, "timing_s": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(res, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)) + "\n", encoding="utf-8", newline="\n")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s; {n_buckets} buckets, max |t| under no effect p50 {res['multiplicity']['expected_max_abs_t_p50']:.2f}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else 1)
