"""D738 step 3: the five expected-profit filters declared with the principal in D738-A1, scored on D727's k 1.5 NQ follow
(docs/decisions/D738-STAGE-0-PRE-REG-an-expected-profit-filter-on-the-nq-follow.md, amendment A1).

    uv run python scripts/stage0_d738_step3_filters.py --selftest     # synthetic only
    uv run python scripts/stage0_d738_step3_filters.py --run          # once -> data/stage0_d738_filters.json

One template: projected gross = (walk-forward OLS pass-through of gross / sigma$ on the filter's state, fitted on
earlier sessions' trades only, burn-in 100) x sigma$; take iff projected >= 2 x the round-trip cost. The trades and
variables come through step 1's own functions (stage0_d738_follow_oracle), with its seal (a chunked read cut at
2023-12-29; D691's frame under D720's lowered_cut). The null is the exact enumerated rotation of each take mask.
Aggregates only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T7  # noqa: E402
import stage0_d736_earn_when_trading_screen as S736  # noqa: E402
import stage0_d738_follow_oracle as S1  # noqa: E402
from backtest_framework.validation import filter_oracle as FO  # noqa: E402

OUT = REPO / "data" / "stage0_d738_filters.json"
K = 1.5
BURN = 100
TRADED_YEAR_MIN = 10
NW_LAGS = 5
FILTERS = {"F1_VOL": [], "F2_VOL_GAMMA": ["gamma_pct"], "F3_VOL_IVRV": ["ivrv"], "F4_VOL_RELVOL": ["relvol"],
           "F5_ALL": ["gamma_pct", "ivrv", "relvol"]}
P = Z.P


class D738Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D738Error(msg)


# ================================================================================ the template
def walk_forward(y: np.ndarray, X: np.ndarray, leak: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """For trade t (one trade a session, in session order): OLS of y on X over trades before t with every input
    finite. Returns the projected pass-through p[t] (NaN before the burn-in or where X[t] is missing) and the number of
    valid earlier trades. `leak` includes trade t itself: the canary."""
    n = len(y)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    p = np.full(n, np.nan)
    cnt = np.zeros(n, int)
    for t in range(n):
        m = ok.copy()
        m[t + 1 if leak else t:] = False
        cnt[t] = int(m.sum())
        if cnt[t] >= BURN and np.isfinite(X[t]).all():
            b, *_ = np.linalg.lstsq(X[m], y[m], rcond=None)
            p[t] = float(X[t] @ b)
    return p, cnt


def fit_audit(y: np.ndarray, X: np.ndarray, p: np.ndarray, sample: list[int]) -> None:
    """Second implementation: the normal equations on rows strictly before t."""
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    for t in sample:
        if not np.isfinite(p[t]):
            continue
        m = ok.copy()
        m[t:] = False
        A = X[m]
        b = np.linalg.solve(A.T @ A, A.T @ y[m])
        need(math.isclose(float(X[t] @ b), p[t], rel_tol=1e-8, abs_tol=1e-10),
             f"[FIT] trade {t}: the walk-forward pass-through is not the fit on earlier trades")


def rotation(take: np.ndarray, net: np.ndarray, gross: np.ndarray) -> dict[str, Any]:
    """Every circular offset of the take mask over the window's trades (exact). S1 mean net kept; S2 efficiency."""
    n = len(take)
    s1 = np.empty(n)
    s2 = np.empty(n)
    for o in range(n):
        m = np.roll(take, o)
        s1[o] = net[m].mean() if m.any() else np.nan
        g = gross[m]
        s2[o] = g.sum() / np.abs(g).sum() if m.any() and np.abs(g).sum() > 0 else np.nan
    out = {}
    for name, s in (("S1_mean_net", s1), ("S2_efficiency", s2)):
        null = s[1:]
        out[name] = {"observed": float(s[0]), "p": float(np.mean(s >= s[0])), "null_p50": float(np.nanpercentile(null, 50)),
                     "null_p95": float(np.nanpercentile(null, 95)), "offsets": int(n)}
    return out


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=lambda k: ps[k])
    m, run, out = len(order), 0.0, {}
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * ps[k]))
        out[k] = run
    return out


def traded_year_standard(by: dict[str, float], nby: dict[str, int]) -> dict[str, Any]:
    traded = {y: v for y, v in by.items() if nby.get(y, 0) >= TRADED_YEAR_MIN}
    out: dict[str, Any] = {"traded_years": sorted(traded), "abstention_years": sorted(set(by) - set(traded))}
    if len(traded) < 4:
        out["label"] = "UNDEFINED"
        return out
    st = S736.stats(traded)
    out.update({k: st[k] for k in ("ex2", "ex2_per_year", "years_positive", "years_needed", "best_two", "label")})
    return out


def report(net_d: np.ndarray, gross_d: np.ndarray, taken_d: np.ndarray, days: np.ndarray, net_t: np.ndarray) -> dict[str, Any]:
    years = np.array([d[:4] for d in days])
    by = {y: float(net_d[years == y].sum()) for y in np.unique(years)}
    nby = {y: int((taken_d & (years == y)).sum()) for y in np.unique(years)}
    return {"trades": int(taken_d.sum()), "share": float(taken_d.mean()), "total_net": float(net_d.sum()),
            "mean_net": float(net_t.mean()) if len(net_t) else None,
            "mean_gross": float(gross_d[taken_d].mean()) if taken_d.any() else None,
            "net_sharpe": Z.sharpe(net_d), "net_sortino": Z.sortino(net_d), "gross_sharpe": Z.sharpe(gross_d),
            "gross_sortino": Z.sortino(gross_d), "max_dd": Z.max_dd(net_d), "trade_distribution_net": Z.trade_dist(net_t),
            "net_by_year": by, "trades_by_year": nby, "standard_with_abstention": traded_year_standard(by, nby)}


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; step 3 is run once")
    t0 = time.time()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    cost, usd_pt = float(cl["cost"]), float(cl["usd_per_point"])
    bar = 2 * cost
    pn = T7.panel_from_raw("NQ", S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz"))
    ob = T7.objects(pn)
    days = pn["days"]
    Z.no_session_after(days, "the NQ panel")
    rng = np.random.default_rng(7381)
    smp = [(int(rng.integers(0, len(days))), int(rng.integers(0, len(T7.CLOCKS)))) for _ in range(40)]
    T7.lag_audit(pn, ob, smp)
    bk = {k: S1.book(pn, ob, k, usd_pt, cost) for k in S1.KS}
    S1.known_answers(bk, days, json.loads((REPO / "data" / "stage0_d727_trend_curve.json").read_text(encoding="utf-8")))
    b = bk[K]
    fa = S1.full_day_arrays(pn)
    kp = np.searchsorted(pn["all_days"], days)
    need(np.allclose(fa["s20"][kp], pn["soc"], rtol=0, atol=1e-9), "sigma_oc differs from D727's")
    S1.pit_audit(pn, fa, kp, [int(x) for x in rng.integers(300, len(days), 20)])
    tab, d691 = S1.d691_frame()
    g = tab["V10_gamma_prior"]
    gpct = g.rolling(252, min_periods=252).apply(lambda w: (w[:-1] < w[-1]).mean() + 0.5 * (w[:-1] == w[-1]).mean(), raw=True)
    state_day = {"gamma_pct": gpct.reindex(days).to_numpy(float), "ivrv": tab["V8_ln_iv_rv"].reindex(days).to_numpy(float),
                 "relvol": fa["pct"][kp]}
    js = rng.integers(0, len(days), 60)
    S1.join_audit(state_day["ivrv"], tab["V8_ln_iv_rv"], days, js)
    S1.join_audit(state_day["gamma_pct"], gpct, days, js)
    # the trades, in session order (one a session)
    ti = np.flatnonzero(b["side"] != 0)
    gross_t, net_t = b["gross"][ti], b["net"][ti]
    sig_t = pn["soc"][ti] * usd_pt
    y = gross_t / sig_t
    res_f: dict[str, Any] = {}
    proj, can_decide = {}, {}
    for f, cols in FILTERS.items():
        X = np.column_stack([np.ones(len(ti))] + [state_day[c][ti] for c in cols])
        p, cnt = walk_forward(y, X)
        fit_audit(y, X, p, [int(x) for x in rng.integers(BURN, len(ti), 25)])
        pl, _ = walk_forward(y, X, leak=True)
        try:
            fit_audit(y, X, pl, [int(x) for x in rng.integers(BURN, len(ti), 25)])
        except D738Error:
            res_f.setdefault("_leak_canaries", []).append(f)
        proj[f] = p * sig_t
        can_decide[f] = cnt >= BURN
    need(len(res_f.get("_leak_canaries", [])) == len(FILTERS), "a walk-forward leak canary did not fire")
    start_t = max(int(np.argmax(can_decide[f])) for f in FILTERS)
    start_day = days[ti[start_t]]
    win_d = days >= start_day
    wd = days[win_d]
    tw = np.arange(start_t, len(ti))
    # take-all on the window, and Gate 1
    tall = (b["side"] != 0) & win_d
    x = gross_t[tw]
    e = x - x.mean()
    v = e @ e / len(x)
    for L in range(1, NW_LAGS + 1):
        v += 2 * (1 - L / (NW_LAGS + 1)) * (e[L:] @ e[:-L]) / len(x)
    nw_t = float(x.mean() / math.sqrt(v / len(x)))
    out: dict[str, Any] = {"spec": "D738-A1", "seal": f"nothing on or after {Z.CUT24}; aggregates only",
                           "cost": cost, "bar_usd": bar, "burn_in_trades": BURN, "window_start": str(start_day),
                           "window_trades": int(len(tw)), "window_sessions": int(win_d.sum()),
                           "leak_canaries_fired": res_f["_leak_canaries"], "d691": d691,
                           "gate1": {"mean_gross": float(x.mean()), "nw_t": nw_t, "holds": bool(x.mean() > 0 and nw_t >= 2)},
                           "take_all": report(b["net"][win_d], b["gross"][win_d], tall[win_d], wd, net_t[tw]),
                           "filters": {}}
    ta_mean = float(net_t[tw].mean())
    pvals = {}
    for f in FILTERS:
        pr = proj[f][tw]
        take = np.isfinite(pr) & (pr >= bar)
        missing = int((~np.isfinite(pr)).sum())
        rot = rotation(take, net_t[tw], gross_t[tw])
        pvals[f] = rot["S1_mean_net"]["p"]
        okc = np.isfinite(pr)
        cal = FO.calibration(pr[okc], gross_t[tw][okc])
        acc = FO.assess(np.where(okc, pr, -1e9), take, gross_t[tw], net_t[tw])
        nd = np.zeros(len(days))
        gd = np.zeros(len(days))
        kd = np.zeros(len(days), bool)
        sel = ti[tw][take]
        nd[sel], gd[sel], kd[sel] = b["net"][sel], b["gross"][sel], True
        out["filters"][f] = {"inputs": ["sigma_usd"] + FILTERS[f], "missing_input_trades": missing,
                             "taken": int(take.sum()), "take_rate": float(take.mean()),
                             "book": report(nd[win_d], gd[win_d], kd[win_d], wd, net_t[tw][take]),
                             "rotation": rot, "calibration": {"slope": cal["slope"], "intercept": cal["intercept"],
                                                              "bins": cal["bins"]},
                             "accuracy": {"auc_vs_oracle": acc["auc_vs_oracle_label"],
                                          "spearman_projection_gross": acc["spearman_score_vs_gross"],
                                          "capture": acc["capture"], "confusion": acc["confusion_vs_oracle"]}}
    hp = holm(pvals)
    for f in FILTERS:
        F = out["filters"][f]
        F["holm_p_S1"] = hp[f]
        g2 = (F["book"]["mean_net"] or -1e9) > ta_mean and hp[f] <= 0.05 and F["calibration"]["slope"] > 0
        g3 = F["book"]["standard_with_abstention"].get("label") == "EARNS"
        F["gate2"], F["gate3"] = bool(g2), bool(g3)
        F["size_carried"] = bool(hp[f] <= 0.05 and F["rotation"]["S2_efficiency"]["p"] > 0.05)
        F["reading"] = ("NO MECHANISM" if not out["gate1"]["holds"] else "NOT SUPPORTED" if not g2
                        else "SUPPORTED" if g3 else "FILTER ONLY")
    out["wall_min"] = (time.time() - t0) / 60
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    P(f"[D738-3] window from {start_day} ({len(tw)} trades); Gate 1 {out['gate1']}; "
      + "; ".join(f"{f} {out['filters'][f]['reading']} n{out['filters'][f]['taken']} "
                  f"${out['filters'][f]['book']['mean_net']:.2f} p{out['filters'][f]['holm_p_S1']:.3f}" for f in FILTERS)
      + f"; {out['wall_min']:.1f} min")
    return 0


# ================================================================================ selftest (synthetic only)
def selftest() -> int:
    rng = np.random.default_rng(3)
    n = 600
    s = rng.uniform(20, 400, n)                       # sigma$
    st = rng.normal(size=n)                           # a state
    pt = 0.05 + 0.04 * st                             # true pass-through depends on the state
    gross = pt * s + rng.normal(size=n) * 0.3 * s
    y = gross / s
    X = np.column_stack([np.ones(n), st])
    p, cnt = walk_forward(y, X)
    need(np.isnan(p[:BURN]).all() and np.isfinite(p[BURN:]).all(), "the burn-in is not honoured")
    fit_audit(y, X, p, list(range(BURN, n, 37)))
    pl, _ = walk_forward(y, X, leak=True)
    try:
        fit_audit(y, X, pl, list(range(BURN, n, 37)))
    except D738Error:
        print("  fires: the walk-forward fit including the trade's own session")
    else:
        raise SystemExit("SELFTEST FAILED: the leak canary did not fire")
    cost = 4.0
    proj = p * s
    take = np.isfinite(proj) & (proj >= 2 * cost)
    need(np.all(proj[take] >= 8.0) and not np.any(np.isfinite(proj[~take]) & (proj[~take] >= 8.0)),
         "the take rule is not applied in dollars at 2c")
    net = gross - cost
    w = slice(BURN, n)
    r = rotation(take[w], net[w], gross[w])
    need(r["S1_mean_net"]["p"] <= 0.05, f"a planted filter is not found (p {r['S1_mean_net']['p']})")
    rnd = rng.random(n - BURN) < take[w].mean()
    pr = [rotation(np.roll(rnd, k), rng.normal(size=n - BURN), rng.normal(size=n - BURN))["S1_mean_net"]["p"] for k in range(40)]
    need(0.3 < float(np.mean(pr)) < 0.7, f"the rotation null of a random mask is not centred (mean p {np.mean(pr):.2f})")
    print(f"  a planted filter p {r['S1_mean_net']['p']:.3f}; random masks mean p {np.mean(pr):.2f}; 2c in dollars")
    need(holm({"a": 0.01, "b": 0.04, "c": 0.5}) == {"a": 0.03, "b": 0.08, "c": 0.5}, "holm is wrong")
    sd = traded_year_standard({"2016": 0.0, "2017": 5.0, "2018": 500.0, "2019": 300.0, "2020": 600.0, "2021": 400.0},
                              {"2016": 0, "2017": 3, "2018": 50, "2019": 40, "2020": 60, "2021": 55})
    need(sd["abstention_years"] == ["2016", "2017"] and sd["label"] == "EARNS", f"abstention reading wrong: {sd}")
    print("  abstention years excluded from G1-G3; holm correct")
    print("SELFTEST PASS")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else ap.print_help() or 2)
