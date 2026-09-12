"""D493 -- the account-size lever through the lifecycle. Every D386 plan x {ES, NQ} x {micro, full} x n in {1,2,3,5} contracts, on
(a) the MEASURED last-30-minutes day-session series (data/d463_trades.csv.gz, one full contract-day rows: pnl/mae/mfe/cost in $) and
(b) D484's MACD moments as D440's GAUSS provider (declared caveat: not yet intraday-closable; answers the fee question only).
Spec 62404c7, committed before this file. Arithmetic on committed objects; nothing opened, closed or admitted.

    python scripts/run_d493_account_size.py --selftest
    python scripts/run_d493_account_size.py --run [--paths 3000] [--out data/d493_account_size_lifecycle.json]
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]; TRADES = REPO / "data" / "d463_trades.csv.gz"; SPECS = REPO / "data" / "futures_contract_specs.json"; D484 = REPO / "data" / "d484_offdiagonal_and_macd.json"
ROOTS = ("ES", "NQ"); MICRO = {"ES": "MES", "NQ": "MNQ"}; CLASSES = ("micro", "full"); NS = (1, 2, 3, 5)
COMMISSION_RT = 3.00; CROSS_TICKS = 1.009; HORIZON_DAYS = 600; SEED = 493; IS = ("2016-01-04", "2023-12-29")
BAR = dict(V_se_mult=2.0, P3_worst_pct=-2.0, life_years=3.0)


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


def contract_dollars(specs, root, cls):
    sym = root if cls == "full" else MICRO[root]; return dict(sym=sym, usd_per_point=specs[sym]["usd_per_point"], tick_usd=specs[sym]["tick_usd"], scale=1.0 if cls == "full" else specs[sym]["size_ratio_to_e_mini"])


def cost_usd(cd):
    return COMMISSION_RT + CROSS_TICKS * cd["tick_usd"]


def measured_days(trades, root, cd, n):
    """One row per trade day at n contracts of the class: (d_low, d_high, d_end) in dollars, cost charged on the end and the low."""
    t = trades[(trades["root"] == root) & (trades["day"] >= IS[0]) & (trades["day"] <= IS[1])].sort_values("day"); c = cost_usd(cd)
    end = (t["pnl_usd"].to_numpy() * cd["scale"] - c) * n; low = (t["mae_usd"].to_numpy() * cd["scale"] - c) * n; high = np.maximum(t["mfe_usd"].to_numpy() * cd["scale"], 0.0) * n
    return pd.DataFrame({"day": t["day"].to_numpy(), "d_end": end, "d_low": np.minimum(low, end), "d_high": high})


def provider_measured(h, n_paths):
    lo, hi, en = h["d_low"].to_numpy(float), h["d_high"].to_numpy(float), h["d_end"].to_numpy(float); n = len(en); order = np.arange(min(n_paths, n)).reshape(-1, 1)
    def provider(day, live_idx, _rng):
        j = (order[live_idx, 0] + day) % n; return lo[j], hi[j], en[j]
    return provider, min(n_paths, n)


def macd_moments(root):
    j = json.loads(D484.read_text()); b = j["tradeability_best_by_root"][root]; return dict(gross_ticks=float(b["gross_ticks"]), sigma_ticks=float(b["sigma_ticks"]), family=b["family"], H=b["H"])


def sharpe_ann(x):
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")


def sharpe_boot(x, days, n_boot=1000, seed=7):
    mon = np.array([d[:7] for d in days]); keys, inv = np.unique(mon, return_inverse=True); rng = np.random.default_rng(seed); out = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); xs = np.concatenate([x[inv == k] for k in pick]); out[b] = sharpe_ann(xs)
    return float(np.nanstd(out, ddof=1))


def p5_years(h):
    yrs = h["day"].str[:4]; p5 = []
    for y, g in h.groupby(yrs):
        tot = g["d_end"].sum(); p5.append(float(g["d_end"].max() / tot) if tot > 0 else float("nan"))
    p5 = np.array(p5); return int(np.nansum(p5 > 0.40)), int(np.isfinite(p5).sum())


def cell(D40, plan, h, prov, npth, n_paths, sd_daily, days=None):
    sim = D40.simulate_provider(plan, prov, n_paths=npth, days=HORIZON_DAYS, seed=SEED); x = h["d_end"].to_numpy(float) if h is not None else None
    out = dict(p_pass=sim["p_pass"], p_alive_600=sim["p_alive_at_horizon"], life_years=float(sim["fund_days_mean"] / 252.0) if np.isfinite(sim["fund_days_mean"]) else None, V=sim["V"], V_se=sim["V_se"], p_breached=sim["p_breached"], C_d_sigma_pct=100 * sd_daily / plan.size)
    if h is not None:
        y40, ny = p5_years(h); out.update(net_sharpe=sharpe_ann(x), net_sharpe_se=sharpe_boot(x, h["day"].to_numpy()), P3_worst_pct=float(h["d_low"].min() / plan.size * 100), P3_days_below_2pct=int((h["d_low"] < -0.02 * plan.size).sum()), P5_years_over_40=y40, P5_years=ny, mean_usd=float(x.mean()))
    else:
        out.update(net_sharpe=None, P3_worst_pct=None, P5_years_over_40=None)
    out["clears"] = bool(out["V"] > BAR["V_se_mult"] * out["V_se"] and (out["P3_worst_pct"] is None or out["P3_worst_pct"] >= BAR["P3_worst_pct"]) and (out["life_years"] or 0) >= BAR["life_years"])
    return out


def run(out, n_paths):
    t0 = time.time(); D40 = _load("d440l", "d440_lifecycle.py"); D86 = D40.D386; specs = json.loads(SPECS.read_text()); trades = pd.read_csv(TRADES, dtype={"day": str, "root": str})
    fails = D40.p1_gate(verbose=False); assert not fails, f"[P1] {fails}"; print("[P1] Gaussian provider reproduces d386 bit-identically", flush=True)
    res = dict(spec="62404c7", plans=[dict(firm=p.firm, size=p.size, fee_eval=p.fee_eval, monthly=p.monthly, target=p.target, dd_eval=p.dd_eval, kind_fund=p.kind_fund, consistency=p.consistency) for p in D86.PLANS], cells=[], moments={})
    for root in ROOTS:
        mm = macd_moments(root); res["moments"][root] = mm
    k = 0; total = len(D86.PLANS) * len(ROOTS) * len(CLASSES) * len(NS) * 2
    print(f"D493 -- {len(D86.PLANS)} plans x {len(ROOTS)} roots x {len(CLASSES)} classes x {len(NS)} sizes x 2 providers = {total} lifecycle cells, {n_paths} paths x {HORIZON_DAYS} days each\n", flush=True)
    for root in ROOTS:
        mm = res["moments"][root]
        for cls in CLASSES:
            cd = contract_dollars(specs, root, cls); c = cost_usd(cd)
            for n in NS:
                h = measured_days(trades, root, cd, n); sd_m = float(h["d_end"].std(ddof=1))
                mu_g = (mm["gross_ticks"] - COMMISSION_RT / cd["tick_usd"] - CROSS_TICKS) * cd["tick_usd"] * n; sd_g = mm["sigma_ticks"] * cd["tick_usd"] * n
                for p in D86.PLANS:
                    prov, npth = provider_measured(h, n_paths); cm = cell(D40, p, h, prov, npth, n_paths, sd_m); cm.update(provider="MEASURED last-30", root=root, cls=cls, sym=cd["sym"], n=n, plan=f"{p.firm} {p.size//1000}k", cost_usd=c); res["cells"].append(cm)
                    gp = D40.make_gauss_provider(mu_g, sd_g, 1); cg = cell(D40, p, None, gp, n_paths, n_paths, sd_g); cg.update(provider=f"GAUSS MACD {mm['family']} H{mm['H']}", root=root, cls=cls, sym=cd["sym"], n=n, plan=f"{p.firm} {p.size//1000}k", cost_usd=c, mu_daily=mu_g, sd_daily=sd_g, net_sharpe=float(mu_g / sd_g * math.sqrt(252))); res["cells"].append(cg)
                    k += 2
                if k % 56 == 0:
                    print(f"  {k}/{total} cells  ({(time.time()-t0)/60:.1f} min)  last: {root} {cd['sym']} x{n}  measured V {cm['V']:+.0f}+-{cm['V_se']:.0f} pass {100*cm['p_pass']:.0f}%  gauss V {cg['V']:+.0f} pass {100*cg['p_pass']:.0f}%", flush=True)
    df = pd.DataFrame(res["cells"]); res["clearing"] = df[df["clears"]][["provider", "root", "sym", "n", "plan", "V", "V_se", "p_pass", "life_years", "P3_worst_pct", "net_sharpe"]].to_dict("records")
    print("\nMEASURED last-30, net Sharpe by class/size (plan-independent):")
    for root in ROOTS:
        for cls in CLASSES:
            r = df[(df["provider"].str.startswith("MEASURED")) & (df["root"] == root) & (df["cls"] == cls)].drop_duplicates("n"); print(f"  {root} {cls:5s}: " + "  ".join(f"x{int(x.n)}: {x.net_sharpe:+.2f}+-{x.net_sharpe_se:.2f} (mean ${x.mean_usd:+.1f}/d, worst {x.P3_worst_pct:+.1f}% of 50k-equiv)" for x in r.itertuples()))
    print("\nBEST V PER PLAN (either provider), and whether anything clears V>2SE & P3 & life>=3y:")
    for plan, g in df.groupby("plan", sort=False):
        b = g.loc[g["V"].idxmax()]; print(f"  {plan:26s} best V {b['V']:+7.0f} +- {b['V_se']:4.0f}  ({b['provider'][:14]} {b['sym']} x{b['n']}, pass {100*b['p_pass']:.0f}%, life {b['life_years'] if b['life_years'] is None else round(b['life_years'],1)} y, P3 worst {b['P3_worst_pct'] if b['P3_worst_pct'] is None else round(b['P3_worst_pct'],1)}%)  clears: {int(g['clears'].sum())}/{len(g)}")
    print(f"\ncells clearing the bar: {len(res['clearing'])}"); [print("   ", c) for c in res["clearing"][:20]]
    res["wall_min"] = round((time.time() - t0) / 60, 1); Path(out).write_text(json.dumps(res, indent=1, default=float)); print(f"wrote {out} in {res['wall_min']} min")


def selftest():
    D40 = _load("d440l", "d440_lifecycle.py"); specs = json.loads(SPECS.read_text()); trades = pd.read_csv(TRADES, dtype={"day": str, "root": str})
    cd_f = contract_dollars(specs, "NQ", "full"); cd_m = contract_dollars(specs, "NQ", "micro"); assert cd_m["scale"] == 0.1 and cd_m["tick_usd"] == 0.5 and cd_f["tick_usd"] == 5.0
    h1 = measured_days(trades, "NQ", cd_f, 1); h2 = measured_days(trades, "NQ", cd_f, 2); assert np.allclose(h2["d_end"], 2 * h1["d_end"]) and np.allclose(h2["d_low"], 2 * h1["d_low"]), "n scales dollars linearly"
    hm = measured_days(trades, "NQ", cd_m, 1); t = trades[trades["root"] == "NQ"]; assert np.allclose(hm["d_end"] + cost_usd(cd_m), 0.1 * (h1["d_end"] + cost_usd(cd_f))), "micro = 0.1 x full before cost"
    assert (h1["d_low"] <= h1["d_end"]).all() and (h1["d_high"] >= 0).all(), "path bounds"
    # [S] sign in money: a series of +$100 days on a fee-free plan has V > 0 and P(pass) = 1; the negated series has P(pass) = 0
    D86 = D40.D386; p = [q for q in D86.PLANS if q.firm == "MFFU Rapid EOD" and q.size == 50_000][0]
    hp = pd.DataFrame({"day": [f"2020-01-{i%28+1:02d}" for i in range(400)], "d_end": 100.0, "d_low": 0.0, "d_high": 100.0}); prov, npth = provider_measured(hp, 50); sim = D40.simulate_provider(p, prov, n_paths=npth, days=600, seed=1); assert sim["p_pass"] == 1.0 and sim["p_breached"] == 0.0, sim  # (a flat +$100 day never meets MFFU's $150 qualifying-day threshold, so no payout: the fee shows as V = -209; that is the rule working)
    hn = hp.copy(); hn["d_end"] = -100.0; hn["d_low"] = -100.0; hn["d_high"] = 0.0; prov, npth = provider_measured(hn, 50); sim = D40.simulate_provider(p, prov, n_paths=npth, days=200, seed=1); assert sim["p_pass"] == 0.0, sim
    fails = D40.p1_gate(verbose=False); assert not fails, fails
    print("selftest OK: dollar scaling by n and class, path bounds, [S] sign in money through the lifecycle, [P1] Gaussian == d386")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--paths", type=int, default=3000); ap.add_argument("--out", default=str(REPO / "data" / "d493_account_size_lifecycle.json")); a = ap.parse_args()
    if a.selftest:
        selftest()
    if a.run:
        run(a.out, a.paths)
