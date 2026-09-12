"""D466 -- the components ledger: score every futures construction with a committed daily series against the standard in
docs/COMPONENTS_PROP.md, produce the entry order the standard implies, and report the equal-risk book. Spec committed BEFORE this
file. In-sample 2016-01-04 .. 2023-12-29; 2024+ unread; no holdout.

    uv run python -u scripts/run_d466_components.py --run
    uv run python -u scripts/run_d466_components.py --selftest

Daily P&L in dollars at the instrument's minimum tradable size (MES $5/pt, MNQ $2/pt, MYM $0.50/pt; $3 round trip), zero on flat
days, on the ES session calendar. Sharpe = mean/sd x sqrt(252) over all calendar days, with a monthly block-bootstrap SE.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
HOLDS = REPO / "data" / "fixtures" / "es_c1_holds.csv.gz"; TRADES = REPO / "data" / "d463_trades.csv.gz"; OUT = REPO / "data" / "d466_components.json"
START, END = "2016-01-04", "2023-12-29"; ACCOUNT = 50_000.0; COST = 3.0
MICRO = {"ES": 5.0, "NQ": 2.0, "YM": 0.5}; BAR_SHARPE, BAR_RHO, BAR_SKEW, BAR_SIGMA = 0.5, 0.3, -0.5, 0.01 * ACCOUNT


def sharpe(x):
    x = np.asarray(x, float); s = x.std(ddof=1); return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def sharpe_boot(x, dates, n_boot=1000, seed=7):
    mon = np.array([str(d)[:7] for d in dates]); keys, inv = np.unique(mon, return_inverse=True); rng = np.random.default_rng(seed); out = np.empty(n_boot); x = np.asarray(x, float)
    groups = [x[inv == k] for k in range(keys.size)]
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); out[b] = sharpe(np.concatenate([groups[k] for k in pick]))
    return float(np.nanstd(out, ddof=1))


def series_on(cal, days, pnl):
    s = pd.Series(0.0, index=cal); v = pd.Series(np.asarray(pnl, float), index=days); v = v[v.index.isin(cal)]; s.loc[v.index] = v.values; return s


def build_series():
    """{name: (daily $ series on the ES calendar, active-day mask)}, plus the calendar and the descriptions."""
    h = pd.read_csv(HOLDS, dtype={"day": str, "prev_day": str}); h = h[(h["day"] >= START) & (h["day"] <= END)].sort_values("day")
    t = pd.read_csv(TRADES, dtype={"day": str, "root": str}); t = t[(t["day"] >= START) & (t["day"] <= END)]
    cal = pd.Index(sorted(set(h["day"]) | set(t["day"]))); S = {}; desc = {}
    S["K1"] = series_on(cal, h["day"], h["d_end"] * h["entry"] * MICRO["ES"] - COST); desc["K1"] = "C1: ES 18:00->16:00 hold, every same-contract night, 1 MES"
    for k, root, lab in (("K2", "NQ", "MNQ"), ("K3", "ES", "MES"), ("K4", "YM", "MYM")):
        d = t[t["root"] == root]; S[k] = series_on(cal, d["day"], d["pnl_pts"] * MICRO[root] - COST); desc[k] = f"last-30-min momentum, {root}, 1 {lab}"
    R64 = _load("d464g", "run_d464_arms_as_gates.py"); A = _load("d234a", "run_activation_threshold.py"); U = _load("d240u", "run_uptrend_onset.py"); G = R64.gates_for("SPY", A, U).reindex(h["prev_day"])
    for k, col, lab in (("K5", "S1", "S1"), ("K6", "S2", "S2 exposure")):
        m = G[col].fillna(False).to_numpy(bool); hh = h[m]; S[k] = series_on(cal, hh["day"], hh["d_end"] * hh["entry"] * MICRO["ES"] - COST); desc[k] = f"C1 on {lab} nights (SPY gate), 1 MES -- a gated subset of K1"
    active = {k: (S[k] != 0.0) for k in S}
    return cal, S, active, desc


def score(S, active, cal):
    rows = {}
    for k, s in S.items():
        x = s.to_numpy(); a = active[k].to_numpy()
        rows[k] = dict(days=int(len(x)), active_days=int(a.sum()), sharpe=sharpe(x), sharpe_se=sharpe_boot(x, cal), mean_usd=float(x.mean()), sd_usd=float(x.std(ddof=1)), hit_active=float((x[a] > 0).mean()) if a.any() else float("nan"), skew=float(pd.Series(x).skew()),
                       ann_usd=float(x.mean() * 252), worst_day_usd=float(x.min()), sigma_pct_account=float(x.std(ddof=1) / ACCOUNT * 100))
    return rows


def admission(rows, corr, subsets):
    """The standard's entry order: highest Sharpe first; each admitted only if C-a, C-c, C-d hold and rho < BAR_RHO with every prior entry; a declared subset never enters beside its parent."""
    order = sorted(rows, key=lambda k: -rows[k]["sharpe"]); entered, log = [], []
    for k in order:
        r = rows[k]; why = []
        if not (r["sharpe"] > BAR_SHARPE): why.append(f"C-a Sharpe {r['sharpe']:.2f} <= {BAR_SHARPE}")
        if not (r["skew"] >= BAR_SKEW): why.append(f"C-c skew {r['skew']:.2f} < {BAR_SKEW}")
        if not (r["sd_usd"] <= BAR_SIGMA): why.append(f"C-d sigma ${r['sd_usd']:.0f} > ${BAR_SIGMA:.0f}")
        if subsets.get(k) in entered: why.append(f"gated subset of {subsets[k]}")
        for e in entered:
            if abs(corr.loc[k, e]) >= BAR_RHO: why.append(f"C-b rho({k},{e}) = {corr.loc[k, e]:+.2f}")
        if not why:
            entered.append(k)
        log.append(dict(component=k, sharpe=r["sharpe"], entered=not why, why=why))
    return entered, log


def book(S, entered, cal):
    if not entered:
        return None
    X = pd.DataFrame({k: S[k] for k in entered}); sd = X.std(ddof=1); w = (1.0 / sd) / (1.0 / sd).sum()      # equal risk contributions (w_k * sd_k equal), weights summing to one micro; unit weights (one micro each) reported beside it
    b = (X * w).sum(axis=1); unit = X.sum(axis=1); eq = b.cumsum(); dd = (eq - eq.cummax()).min(); yrs = {y: sharpe(b[b.index.str[:4] == y]) for y in sorted({d[:4] for d in cal})}
    return dict(components=entered, weights={k: float(w[k]) for k in entered}, sharpe=sharpe(b), sharpe_se=sharpe_boot(b.to_numpy(), cal), sharpe_unit_weights=sharpe(unit), ann_usd=float(b.mean() * 252), sd_usd=float(b.std(ddof=1)), sigma_pct_account=float(b.std(ddof=1) / ACCOUNT * 100),
                worst_day_pct=float(b.min() / ACCOUNT * 100), worst_day=str(b.idxmin()), max_dd_pct=float(dd / ACCOUNT * 100), by_year=yrs)


def run():
    t0 = time.time(); print("D466 -- the components ledger: scoring every futures construction with a committed daily series\n      the standard was committed BEFORE this ran; 2016-2023; 2024+ unread; no holdout\n")
    cal, S, active, desc = build_series(); rows = score(S, active, cal); corr = pd.DataFrame({k: S[k] for k in S}).corr()
    subsets = {"K5": "K1", "K6": "K1"}; entered, log = admission(rows, corr, subsets); bk = book(S, entered, cal); bk_all = book(S, ["K1", "K2", "K3"], cal)
    print(f"  calendar {cal[0]} .. {cal[-1]}, {len(cal):,} days\n")
    for k in S:
        r = rows[k]; print(f"  {k}  {desc[k]:62s} active {r['active_days']:5,}  net Sharpe {r['sharpe']:+.2f} +- {r['sharpe_se']:.2f}  hit {100*r['hit_active']:.1f}%  skew {r['skew']:+.2f}  sd ${r['sd_usd']:.0f}/day ({r['sigma_pct_account']:.2f}%)  ann ${r['ann_usd']:+,.0f}  worst ${r['worst_day_usd']:,.0f}")
    print("\n  correlation (daily, all calendar days):\n" + corr.round(2).to_string())
    print("\n  ADMISSION in the standard's order:")
    for l in log:
        print(f"    {l['component']} Sharpe {l['sharpe']:+.2f}  {'ENTERED' if l['entered'] else 'not entered: ' + '; '.join(l['why'])}")
    if bk:
        print(f"\n  THE EQUAL-RISK BOOK of {entered}: weights {({k: round(v, 2) for k, v in bk['weights'].items()})}  net Sharpe {bk['sharpe']:+.2f} +- {bk['sharpe_se']:.2f} (unit weights {bk['sharpe_unit_weights']:+.2f})  sd ${bk['sd_usd']:.0f}/day ({bk['sigma_pct_account']:.2f}% of the account)  ann ${bk['ann_usd']:+,.0f}  worst day {bk['worst_day_pct']:+.2f}% ({bk['worst_day']})  max DD on closes {bk['max_dd_pct']:+.2f}%\n  by year: " + " ".join(f"{y}:{v:+.2f}" for y, v in bk["by_year"].items()))
    res = dict(spec="D466", start=START, end=END, components=rows, descriptions=desc, correlation=corr.round(4).to_dict(), admission=log, entered=entered, book=bk, book_K1K2K3=bk_all)
    r = rows; print("\nPREDICTIONS\n" + f"  X-a K1 0.55-0.70, K2 0.35-0.50, K3 -0.05..+0.10, K4 < 0, K5/K6 0.35-0.55 : {r['K1']['sharpe']:+.2f} {r['K2']['sharpe']:+.2f} {r['K3']['sharpe']:+.2f} {r['K4']['sharpe']:+.2f} {r['K5']['sharpe']:+.2f} {r['K6']['sharpe']:+.2f}\n"
          + f"  X-b rho(K1,K2) 0.05-0.15; rho(K2,K3) 0.7-0.85; rho(K1,K5), rho(K1,K6) > 0.3   : {corr.loc['K1','K2']:+.2f}; {corr.loc['K2','K3']:+.2f}; {corr.loc['K1','K5']:+.2f} {corr.loc['K1','K6']:+.2f}\n"
          + f"  X-c admits K1 and K2 only; book Sharpe 0.8-1.0, worst day -2..-4%, max DD 6-12%   : {entered}; " + (f"{bk['sharpe']:+.2f}, {bk['worst_day_pct']:+.2f}%, {bk['max_dd_pct']:+.2f}%" if bk else "no book") + "\n"
          + f"  X-d book daily sigma 0.5-0.7% of the account at one micro each                  : " + (f"{bk['sigma_pct_account']:.2f}%" if bk else "-"))
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


def cmd_selftest():
    t0 = time.time(); print("== (a) sharpe, bootstrap, series_on, admission order on synthetic components")
    rng = np.random.default_rng(3); cal = pd.Index([str(d.date()) for d in pd.bdate_range("2016-01-04", "2023-12-29")]); n = len(cal)
    a = rng.normal(4, 40, n); b = 0.9 * a + rng.normal(0, 20, n); c = rng.normal(3, 40, n); d = rng.normal(-6, 40, n); tol = 3 * math.sqrt(252 / n)      # 3 SE of an annualised Sharpe
    S = {"A": pd.Series(a, cal), "B": pd.Series(b, cal), "C": pd.Series(c, cal), "D": pd.Series(d, cal)}; active = {k: S[k] != 0 for k in S}; rows = score(S, active, cal); corr = pd.DataFrame(S).corr()
    assert abs(rows["A"]["sharpe"] - 4 / 40 * math.sqrt(252)) < tol and rows["A"]["sharpe_se"] > 0 and rows["D"]["sharpe"] < 0
    entered, log = admission(rows, corr, {}); assert "A" in entered and "C" in entered and "B" not in entered and "D" not in entered, (entered, log)
    s = series_on(cal, ["2016-01-05", "2099-01-01"], [10.0, 5.0]); assert s.sum() == 10.0 and (s != 0).sum() == 1
    bk = book(S, entered, cal); rc = [bk["weights"][k] * S[k].std(ddof=1) for k in entered]; assert bk and abs(sum(bk["weights"].values()) - 1) < 1e-9 and max(rc) - min(rc) < 1e-9 and bk["sharpe"] > max(rows["A"]["sharpe"], rows["C"]["sharpe"]) * 0.9
    print(f"  A {rows['A']['sharpe']:.2f} (target {4/40*math.sqrt(252):.2f} +- {tol:.2f}), entered {entered}, B refused on rho {corr.loc['A','B']:.2f}, D refused on Sharpe; book {bk['sharpe']:.2f}")
    print("== (b) a declared subset never enters beside its parent")
    S2 = dict(S); S2["A_sub"] = S["A"].where(rng.random(n) < 0.1, 0.0); active2 = {k: S2[k] != 0 for k in S2}; rows2 = score(S2, active2, cal); corr2 = pd.DataFrame(S2).corr(); e2, l2 = admission(rows2, corr2, {"A_sub": "A"}); assert "A_sub" not in e2
    print(f"  ok: A_sub Sharpe {rows2['A_sub']['sharpe']:.2f} not entered ({[x['why'] for x in l2 if x['component']=='A_sub'][0]})")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
