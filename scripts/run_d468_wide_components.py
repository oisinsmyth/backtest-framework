"""D468 -- the wider component scoring: W1 18:00->16:00, W2 18:00->09:00, W3 09:00->16:00, long only, on every root D467 passes, at minimum
size and the cost that size pays; the ledger's admission order in the runner; the common-sign family-maximum null; the assembled
equal-risk book at micro granularity through D440's lifecycle. Spec committed in cff45f2 BEFORE this file. 2016-2023; 2024+ unread.

    uv run python -u scripts/run_d468_wide_components.py --run
    uv run python -u scripts/run_d468_wide_components.py --selftest
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
TABLE = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"; META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
OUT = REPO / "data" / "d468_wide_components.json"; BOOK_OUT = REPO / "data" / "d468_book_days.csv.gz"
START, END = "2016-01-04", "2023-12-29"; ACCOUNT = 50_000.0
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "GC": 10.0, "CL": 100.0, "6E": 12_500.0, "ZN": 1_000.0, "ZB": 1_000.0}; UNIT = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "GC": "MGC", "CL": "MCL", "6E": "M6E", "ZN": "ZN", "ZB": "ZB"}
COST = {r: (6.0 if r in ("ZN", "ZB") else 3.0) for r in MULT}
SEG = [18, 19, 20, 21, 22, 23] + list(range(0, 17)); SEGN = [f"h{h:02d}" for h in SEG]
WINDOWS = {"W1": ("h18", "h15"), "W2": ("h18", "h08"), "W3": ("h09", "h15")}      # entry segment (its open), exit segment (its close); path over entry..exit inclusive
N_NULL, NULL_SEED, N_PATHS, HORIZON_DAYS, SEED = 2000, 11, 3000, 600, 20260912; FRACS = (0.002, 0.004, 0.007, 0.011); ONE_EACH = "1 micro each"
D66 = _load("d466c", "run_d466_components.py")


# ------------------------------------------------------------------------------------------ the constructions
def load_table():
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); meta = json.loads(META.read_text())
    ok = [r for r in MULT if meta["gates"][r]["passes"]]; held = [r for r in MULT if r not in ok]; us = {r: meta["gates"][r]["G5"]["usable_start"] for r in ok}
    return T, ok, held, us


def window_days(t, w, mult, cost):
    """Per same-front session: entry, exit, the window's hourly lows/highs (per-contract $ relative to entry), pnl/mae/mfe/cost in $ per contract."""
    e_seg, x_seg = WINDOWS[w]; i0, i1 = SEGN.index(e_seg), SEGN.index(x_seg); segs = SEGN[i0:i1 + 1]
    t = t[t["same_front"]].copy(); entry = t[f"{e_seg}_o"]; exit_ = t[f"{x_seg}_c"]; ok = entry.notna() & exit_.notna() & (entry > 0)
    t = t[ok]; entry = entry[ok]; exit_ = exit_[ok]
    lows = np.column_stack([(t[f"{s}_l"].to_numpy() - entry.to_numpy()) * mult for s in segs]); highs = np.column_stack([(t[f"{s}_h"].to_numpy() - entry.to_numpy()) * mult for s in segs])
    lows = np.where(np.isnan(lows), 0.0, lows); highs = np.where(np.isnan(highs), 0.0, highs)      # an empty hour inside the window contributes no excursion
    pnl = (exit_.to_numpy() - entry.to_numpy()) * mult
    d = pd.DataFrame({"day": t["day"].to_numpy(), "entry": entry.to_numpy(), "exit": exit_.to_numpy(), "pnl_usd": pnl, "mae_usd": np.minimum(lows.min(axis=1), pnl), "mfe_usd": np.maximum(highs.max(axis=1), 0.0), "cost_usd": cost})
    return d, segs, lows, highs


def build_components(T, ok, us):
    comps = {}
    for r in ok:
        t = T[(T["root"] == r) & (T["day"] >= max(START, us[r])) & (T["day"] <= END)].sort_values("day")
        for w in WINDOWS:
            d, segs, lows, highs = window_days(t, w, MULT[r], COST[r]); comps[f"{r}-{w}"] = dict(root=r, window=w, days=d, segs=segs, lows=lows, highs=highs)
    return comps


def score_all(comps, cal):
    S = {k: D66.series_on(cal, c["days"]["day"], c["days"]["pnl_usd"] - c["days"]["cost_usd"]) for k, c in comps.items()}; G = {k: D66.series_on(cal, c["days"]["day"], c["days"]["pnl_usd"]) for k, c in comps.items()}
    active = {k: (S[k] != 0.0) for k in S}; rows = D66.score(S, active, cal)
    for k in rows:
        g = G[k].to_numpy(); d = comps[k]["days"]; rows[k].update(gross_sharpe=D66.sharpe(g), gross_mean_usd=float(d["pnl_usd"].mean()), cost_usd=float(COST[comps[k]["root"]]), cost_share_of_gross=float(COST[comps[k]["root"]] / d["pnl_usd"].mean()) if d["pnl_usd"].mean() != 0 else float("inf"),
                       cost_share_of_sigma=float(COST[comps[k]["root"]] / d["pnl_usd"].std(ddof=1)), sessions=int(len(d)), by_year={y: D66.sharpe(S[k][S[k].index.str[:4] == y]) for y in sorted({x[:4] for x in cal})}, short_sharpe=D66.sharpe(-G[k].to_numpy() - (active[k].to_numpy() * COST[comps[k]["root"]])))
    return S, G, rows


def family_max_null(S, n=N_NULL, seed=NULL_SEED):
    """One sign vector per session, common across every construction; the max net Sharpe across the family per draw."""
    X = np.column_stack([S[k].to_numpy() for k in S]); rng = np.random.default_rng(seed); out = np.empty(n)
    for b in range(n):
        s = rng.choice([-1.0, 1.0], size=X.shape[0]); Y = X * s[:, None]; out[b] = np.nanmax(Y.mean(axis=0) / Y.std(axis=0, ddof=1) * math.sqrt(252))
    return out


def p95_se(x, n_boot=500, seed=5):
    rng = np.random.default_rng(seed); return float(np.std([np.quantile(rng.choice(x, x.size), .95) for _ in range(n_boot)], ddof=1))


# ------------------------------------------------------------------------------------------ the book
def book_days(comps, entered, cal, contracts):
    """The book's daily (d_end, d_low, d_high) in $: per component, contracts[k] (a Series on cal); hourly path = sum over components of
    the hour's low (high) -- adverse for a trailing floor -- with a component's realised pnl carried after its exit and 0 before its entry."""
    n = len(cal); pos = {d: i for i, d in enumerate(cal)}; H = len(SEGN); low_h = np.zeros((n, H)); high_h = np.zeros((n, H)); end = np.zeros(n); cost = np.zeros(n); ct = np.zeros((n, len(entered)))
    for j, k in enumerate(entered):
        c = comps[k]; d = c["days"]; i0 = SEGN.index(c["segs"][0]); i1 = SEGN.index(c["segs"][-1]); idx = np.array([pos[x] for x in d["day"] if x in pos]); keep = np.array([x in pos for x in d["day"]])
        cts = contracts[k].reindex(d["day"][keep]).fillna(0).to_numpy(); ct[idx, j] = cts; pnl = d["pnl_usd"].to_numpy()[keep] * cts; end[idx] += pnl; cost[idx] += d["cost_usd"].to_numpy()[keep] * cts
        lo = c["lows"][keep] * cts[:, None]; hi = c["highs"][keep] * cts[:, None]
        low_h[idx[:, None], np.arange(i0, i1 + 1)[None, :]] += lo; high_h[idx[:, None], np.arange(i0, i1 + 1)[None, :]] += hi
        if i1 + 1 < H:
            low_h[idx[:, None], np.arange(i1 + 1, H)[None, :]] += pnl[:, None]; high_h[idx[:, None], np.arange(i1 + 1, H)[None, :]] += pnl[:, None]
    d_end = end - cost; d_low = np.minimum(low_h.min(axis=1) - cost, d_end); d_high = np.maximum(high_h.max(axis=1), 0.0)
    return pd.DataFrame({"day": cal, "contracts": ct.sum(axis=1), "d_end": d_end, "d_low": d_low, "d_high": d_high})


def sized_contracts(comps, entered, cal, frac, D63):
    sessions = pd.DataFrame({"day": cal}); out = {}
    for k in entered:
        d = comps[k]["days"]; h = D63.sized_days(d[d["day"].isin(cal)], sessions, frac / len(entered)) if frac is not None else None
        out[k] = pd.Series(h["contracts"].to_numpy(), index=cal) if h is not None else pd.Series(1.0, index=cal)
    return out


def lifecycle(h, D40, plan, D63):
    prov, npth = D63.provider_of(h, N_PATHS); sim = D40.simulate_provider(plan, prov, n_paths=npth, days=HORIZON_DAYS, seed=SEED); yrs = h["day"].str[:4]; p5 = []
    for y, g in h.groupby(yrs):
        tot = g["d_end"].sum(); p5.append(float(g["d_end"].max() / tot) if tot > 0 else float("nan"))
    p5 = np.array(p5); ann = h.groupby(yrs)["d_end"].sum(); x = h["d_end"].to_numpy(); eq = np.cumsum(x); dd = float((eq - np.maximum.accumulate(eq)).min())
    return dict(contracts_mean=float(h["contracts"].mean()), sharpe=D66.sharpe(x), sharpe_se=D66.sharpe_boot(x, h["day"].to_numpy()), sd_usd=float(x.std(ddof=1)), max_dd_pct=dd / ACCOUNT * 100, P3_worst_day_pct=float(h["d_low"].min() / ACCOUNT * 100), P3_days_below_2pct=int((h["d_low"] < -0.02 * ACCOUNT).sum()),
                P4_fund_life_years=float(sim["fund_days_mean"] / 252.0) if np.isfinite(sim["fund_days_mean"]) else None, P4_alive_at_600d=sim["p_alive_at_horizon"], P4_p_pass=sim["p_pass"], V=sim["V"], V_se=sim["V_se"], p_breached=sim["p_breached"],
                P5_years_over_40=int(np.nansum(p5 > 0.40)), P5_years=int(np.isfinite(p5).sum()), ann_profit_mean_pct=float(ann.mean() / ACCOUNT * 100))


def fmt_life(lab, c):
    return (f"    {lab:14s} contracts mean {c['contracts_mean']:.2f}  net Sharpe {c['sharpe']:+.2f} +- {c['sharpe_se']:.2f}  sd ${c['sd_usd']:.0f}  maxDD {c['max_dd_pct']:+.1f}%  P3 worst {c['P3_worst_day_pct']:+.2f}% ({c['P3_days_below_2pct']} d < -2%)  "
            f"P4 life {c['P4_fund_life_years'] if c['P4_fund_life_years'] is None else round(c['P4_fund_life_years'], 2)} yr, alive 600 d {100*c['P4_alive_at_600d']:.0f}%, pass {100*c['P4_p_pass']:.0f}%, V {c['V']:+.0f} +- {c['V_se']:.0f}  P5 yrs > 40%: {c['P5_years_over_40']}/{c['P5_years']}  ann {c['ann_profit_mean_pct']:+.1f}%")


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print("D468 -- the wider component scoring on D467's session tables\n      spec committed in cff45f2 BEFORE this ran; 2016-2023 (or usable_start); 2024+ unread; no holdout\n")
    T, ok, held, us = load_table(); print(f"  roots passing D467: {ok}; held back: {held or 'none'}; usable_start {us}")
    comps = build_components(T, ok, us); cal = pd.Index(sorted({d for c in comps.values() for d in c['days']['day']})); print(f"  {len(comps)} constructions on a union calendar of {len(cal):,} sessions\n")
    S, G, rows = score_all(comps, cal); corr = pd.DataFrame({k: S[k] for k in S}).corr()
    print(f"  {'construction':8s} {'unit':4s} {'sessions':>8s}  {'net Sharpe':>16s}  {'gross':>6s}  {'short':>6s}  {'mean$':>6s} {'sd$':>6s} {'cost/mean':>9s} {'cost/sd':>7s}  {'hit':>5s}  {'skew':>5s}  {'worst$':>7s}")
    for k in sorted(rows, key=lambda k: -rows[k]["sharpe"]):
        r = rows[k]; print(f"  {k:8s} {UNIT[comps[k]['root']]:4s} {r['sessions']:8,}  {r['sharpe']:+6.2f} +- {r['sharpe_se']:.2f}      {r['gross_sharpe']:+6.2f}  {r['short_sharpe']:+6.2f}  {r['gross_mean_usd']:+6.2f} {r['sd_usd']:6.0f} {100*r['cost_share_of_gross']:+8.0f}% {100*r['cost_share_of_sigma']:6.2f}%  {100*r['hit_active']:4.1f}%  {r['skew']:+5.2f}  {r['worst_day_usd']:7,.0f}")
    print("\n  by year (net Sharpe):"); yrs = sorted({d[:4] for d in cal})
    for k in sorted(rows, key=lambda k: -rows[k]["sharpe"]):
        print(f"    {k:8s} " + " ".join(f"{y}:{rows[k]['by_year'][y]:+.2f}" for y in yrs))
    null = family_max_null(S); obs_max = max(r["sharpe"] for r in rows.values()); obs_k = max(rows, key=lambda k: rows[k]["sharpe"]); se95 = p95_se(null)
    print(f"\n  FAMILY-MAXIMUM NULL (common sign per session, {N_NULL} draws, {len(rows)} constructions): p50 {np.median(null):+.2f}  p95 {np.quantile(null, .95):+.2f} +- {se95:.2f}  p99 {np.quantile(null, .99):+.2f}   observed max {obs_max:+.2f} ({obs_k})   share of draws >= observed {100*(null >= obs_max).mean():.1f}%")
    subsets = {}; entered, log = D66.admission(rows, corr, subsets); prov_bar = float(np.quantile(null, .95))
    print("\n  ADMISSION in the standard's order:")
    for l in log:
        tag = "ENTERED" + (" (PROVISIONAL: below the family p95)" if l["entered"] and l["sharpe"] < prov_bar else "") if l["entered"] else "not entered: " + "; ".join(l["why"]); print(f"    {l['component']:8s} Sharpe {l['sharpe']:+.2f}  {tag}")
    print("\n  correlation among the top 8 by Sharpe:\n" + corr.loc[sorted(rows, key=lambda k: -rows[k]['sharpe'])[:8], sorted(rows, key=lambda k: -rows[k]['sharpe'])[:8]].round(2).to_string())
    res = dict(spec="D468", start=START, end=END, roots=ok, held_back=held, usable_start=us, calendar_days=int(len(cal)), components=rows, correlation=corr.round(4).to_dict(), family_null=dict(n=N_NULL, p50=float(np.median(null)), p95=prov_bar, p95_se=se95, p99=float(np.quantile(null, .99)), observed_max=obs_max, observed_argmax=obs_k, share_ge_observed=float((null >= obs_max).mean())),
               admission=log, entered=entered, provisional=[k for k in entered if rows[k]["sharpe"] < prov_bar], book=None)
    # the assembled book
    if entered:
        D63 = _load("d463", "run_d463_intraday_momentum.py"); D40 = _load("d440l", "d440_lifecycle.py"); D86 = D40.D386; plan = [p for p in D86.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
        print(f"\n  THE ASSEMBLED BOOK of {entered} -- equal risk at micro granularity, D463's C4 rule per component with budget f/n, through D440's lifecycle (MFFU Rapid EOD 50K)"); bk = {}; tables = []
        for frac in list(FRACS) + [None]:
            lab = ONE_EACH if frac is None else f"f {100*frac:.1f}%"; ct = sized_contracts(comps, entered, cal, frac, D63); h = book_days(comps, entered, list(cal), ct); c = lifecycle(h, D40, plan, D63); bk[lab] = c; print(fmt_life(lab, c)); tables.append(h.assign(f=lab))
        X = pd.DataFrame({k: S[k] for k in entered}); eq = D66.book(S, entered, cal); res["book"] = dict(lifecycle=bk, equal_risk_report=eq, unit_weight_sharpe=D66.sharpe(X.sum(axis=1).to_numpy()))
        print(f"    equal-risk (1/sigma) weights report: Sharpe {eq['sharpe']:+.2f} +- {eq['sharpe_se']:.2f}, worst day {eq['worst_day_pct']:+.2f}%, max DD {eq['max_dd_pct']:+.2f}%; by year " + " ".join(f"{y}:{v:+.2f}" for y, v in eq["by_year"].items()))
        pd.concat(tables, ignore_index=True).to_csv(BOOK_OUT, index=False, compression="gzip", float_format="%.2f")
    else:
        print("\n  no construction entered: no book to assemble")
    # predictions
    g = lambda k: rows[k]["sharpe"] if k in rows else float("nan"); nclear = sum(r["sharpe"] > 0.5 for r in rows.values()); nfam = sum(r["sharpe"] > prov_bar for r in rows.values())
    print("\nPREDICTIONS")
    print(f"  X-a ES-W1 within +-0.03 of K1 +0.37 on 2,043 +- 10 sessions                       : {g('ES-W1'):+.2f} on {rows['ES-W1']['sessions'] if 'ES-W1' in rows else '-'}")
    print(f"  X-b 1-4 clear C-a; family p95 +0.65..+0.90; 0-1 clear it                          : {nclear} clear C-a; p95 {prov_bar:+.2f}; {nfam} clear it")
    print(f"  X-c NQ-W1 +0.40..+0.70; GC-W2 +0.2..+0.5 and GC-W3 < 0; ZN/ZB-W1 <= +0.2; CL-W1 <= 0; 6E-W1 in +-0.3; W2 > W3 on ES/NQ/YM : NQ-W1 {g('NQ-W1'):+.2f}; GC-W2 {g('GC-W2'):+.2f} GC-W3 {g('GC-W3'):+.2f}; ZN {g('ZN-W1'):+.2f} ZB {g('ZB-W1'):+.2f}; CL {g('CL-W1'):+.2f}; 6E {g('6E-W1'):+.2f}; W2 vs W3 " + " ".join(f"{r}:{g(f'{r}-W2'):+.2f}/{g(f'{r}-W3'):+.2f}" for r in ("ES", "NQ", "YM") if f"{r}-W2" in rows))
    cc = lambda a, b: corr.loc[a, b] if a in corr.index and b in corr.index else float("nan")
    print(f"  X-d |rho(W2,W3)| < 0.15 per root; rho(ES,NQ,YM W1) > 0.85; index vs ZN/ZB W1 in -0.4..0; GC, 6E to the rest |rho| < 0.3 : W2/W3 " + " ".join(f"{r}:{cc(f'{r}-W2', f'{r}-W3'):+.2f}" for r in ok) + f"; ES/NQ {cc('ES-W1','NQ-W1'):+.2f} ES/YM {cc('ES-W1','YM-W1'):+.2f}; ES/ZN {cc('ES-W1','ZN-W1'):+.2f} ES/ZB {cc('ES-W1','ZB-W1'):+.2f}; GC/ES {cc('GC-W1','ES-W1'):+.2f} 6E/ES {cc('6E-W1','ES-W1'):+.2f}")
    print(f"  X-e book beats best entry by >= 15% and V(book) > V(best) if >= 2 enter          : entered {entered}" + (f"; book equal-risk {res['book']['equal_risk_report']['sharpe']:+.2f} vs best {max(rows[k]['sharpe'] for k in entered):+.2f}" if entered else ""))
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) window extraction: entry/exit/mae/mfe from a synthetic session row; roll nights and missing prints dropped")
    row = {"root": "ES", "day": "2020-01-02", "prev_day": "2020-01-01", "contract": "ESH0", "front_prev": "ESH0", "same_front": True, "bars": 1380}
    for i, s in enumerate(SEGN):
        row.update({f"{s}_o": 100.0 + i, f"{s}_h": 100.0 + i + 0.5, f"{s}_l": 100.0 + i - 0.5, f"{s}_c": 100.0 + i + 0.25, f"{s}_v": 10, f"{s}_n": 60})
    row2 = dict(row, day="2020-01-03", same_front=False); row3 = dict(row, day="2020-01-06"); row3["h15_c"] = np.nan
    t = pd.DataFrame([row, row2, row3]); d, segs, lows, highs = window_days(t, "W1", 5.0, 3.0)
    assert len(d) == 1 and d["entry"].iat[0] == 100.0 and d["exit"].iat[0] == 100.25 + 21 and abs(d["pnl_usd"].iat[0] - 21.25 * 5) < 1e-9 and abs(d["mae_usd"].iat[0] - (-0.5 * 5)) < 1e-9 and abs(d["mfe_usd"].iat[0] - (21.5 * 5)) < 1e-9 and segs[0] == "h18" and segs[-1] == "h15" and len(segs) == 22
    d2, segs2, _, _ = window_days(t, "W2", 5.0, 3.0); assert d2["exit"].iat[0] == 100.25 + SEGN.index("h08") and segs2[-1] == "h08"; d3, segs3, _, _ = window_days(t, "W3", 5.0, 3.0); assert d3["entry"].iat[0] == 100.0 + SEGN.index("h09") and segs3[0] == "h09"
    print(f"  ok: W1 pnl ${d['pnl_usd'].iat[0]:.2f}, mae ${d['mae_usd'].iat[0]:.2f}, mfe ${d['mfe_usd'].iat[0]:.2f}; roll night and missing 16:00 print dropped; W2 exits at h08 close, W3 enters at h09 open")
    print("== (b) the family-maximum null on 24 pure-noise constructions: p50 in 0.35..0.85 and the observed max inside the null")
    rng = np.random.default_rng(1); cal = pd.Index([str(x.date()) for x in pd.bdate_range("2016-01-04", "2023-12-29")]); S = {f"c{i}": pd.Series(rng.normal(0, 50, len(cal)), index=cal) for i in range(24)}
    null = family_max_null(S, n=300, seed=2); obs = max(D66.sharpe(s.to_numpy()) for s in S.values()); assert 0.35 < np.median(null) < 0.85 and np.quantile(null, .01) < obs < np.quantile(null, .999), (np.median(null), obs)
    print(f"  ok: null p50 {np.median(null):+.2f} p95 {np.quantile(null, .95):+.2f}; observed noise max {obs:+.2f}")
    print("== (c) the book path bound: two components whose lows fall in different hours -> the book's low <= the true low; realised pnl carried after exit")
    cal2 = ["2020-01-02"]; A = dict(root="ES", window="W2", days=pd.DataFrame({"day": cal2, "pnl_usd": [10.0], "mae_usd": [-20.0], "mfe_usd": [15.0], "cost_usd": [3.0]}), segs=SEGN[:SEGN.index("h08") + 1], lows=np.array([[-20.0] + [0.0] * (SEGN.index("h08"))]), highs=np.array([[15.0] + [0.0] * (SEGN.index("h08"))]))
    B = dict(root="NQ", window="W3", days=pd.DataFrame({"day": cal2, "pnl_usd": [-5.0], "mae_usd": [-30.0], "mfe_usd": [0.0], "cost_usd": [3.0]}), segs=SEGN[SEGN.index("h09"):], lows=np.array([[0.0, -30.0] + [0.0] * (len(SEGN) - SEGN.index("h09") - 2)]), highs=np.zeros((1, len(SEGN) - SEGN.index("h09"))))
    h = book_days({"A": A, "B": B}, ["A", "B"], cal2, {"A": pd.Series(1.0, index=cal2), "B": pd.Series(2.0, index=cal2)})
    assert abs(h["d_end"].iat[0] - (10 - 3 + 2 * (-5 - 3))) < 1e-9 and abs(h["d_low"].iat[0] - (10 + 2 * (-30) - 9)) < 1e-9 and abs(h["d_high"].iat[0] - 15.0) < 1e-9, h.to_dict("records")
    print(f"  ok: d_end {h['d_end'].iat[0]:+.0f} (A +10 carried after its exit; B 2 contracts at -5; costs 9), d_low {h['d_low'].iat[0]:+.0f} = A's realised +10 plus B's hour low -60 minus costs, d_high {h['d_high'].iat[0]:+.0f}")
    print("== (d) admission raises on a deliberately broken input: a construction with sd 0 gives NaN Sharpe and never enters")
    S3 = {"z": pd.Series(0.0, index=cal), "g": pd.Series(rng.normal(5, 40, len(cal)), index=cal)}; rows = D66.score(S3, {k: S3[k] != 0 for k in S3}, cal); ent, _ = D66.admission(rows, pd.DataFrame(S3).corr().fillna(0), {}); assert "z" not in ent and "g" in ent
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
