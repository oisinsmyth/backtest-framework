"""D463 -- market intraday momentum, the last 30 minutes, on ES (primary) / NQ / YM / RTY from the D462 fixtures; lane 13's
falsification criteria; hurdle P (P3/P4/P5) on the C4-sized series through D440's lifecycle model. Spec committed in dd5801c BEFORE
this file. In-sample 2010-06-06 .. 2023-12-29; every bar after END is excluded before anything is computed; no holdout.

    uv run python -u scripts/run_d463_intraday_momentum.py --run
    uv run python -u scripts/run_d463_intraday_momentum.py --selftest

rROD = open(15:30) / close(15:59, previous session) - 1 on same-contract days; trade sign(rROD) from the 15:30 open to the 16:00
print; the path inside the 30 bars from the 1-minute lows (long) / highs (short). Nulls: N1 the sign series rolled by every offset
(exact); N2 i.i.d. signs (10,000). Hurdle P: contracts_t = floor(f * 50,000 / sigma_hat_t), sigma_hat over the prior 21 traded days
(R9), capped at 4x static; MFFU Rapid EOD 50K through D440's simulate_provider with (d_low, d_high, d_end) in dollars per day.
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
FIX = REPO / "data" / "fixtures"; META = FIX / "fut_index_1m.meta.json"; OUT = REPO / "data" / "d463_intraday_momentum.json"; TRADES = REPO / "data" / "d463_trades.csv.gz"
START, END = "2010-06-06", "2023-12-29"; POST = "2018-01-02"; ROOTS = ("ES", "NQ", "YM", "RTY"); PRIMARY = "ES"
MULT = {"ES": 50.0, "NQ": 20.0, "YM": 5.0, "RTY": 50.0}; COST = {"ES": 12.5 + 4.5, "NQ": 5.0 + 4.5, "YM": 5.0 + 4.5, "RTY": 5.0 + 4.5}     # $ per round trip per contract, declared
ENTRY, EXIT, FH_END, OPEN = "15:30", "15:59", "10:00", "09:30"; FULL_DAY = 380; N_WINDOW = 30
ACCOUNT, FRACS, VOL_WINDOW, VOL_CAP, HORIZON_DAYS, N_PATHS = 50_000.0, (0.002, 0.004, 0.007, 0.011), 21, 4.0, 600, 3_000
N2_DRAWS, SEED = 10_000, 463; POST_BETA_FLOOR = 3.0; NW_LAGS = 5


# ------------------------------------------------------------------------------------------ the trades
def usable_start(root):
    """The D462 ADDENDUM's usable window start for the root, from the fixture meta (G5); never earlier than the spec's START."""
    m = json.loads(META.read_text()); u = (m.get("gates") or {}).get(root, {}).get("G5", {}).get("usable_start"); assert u, f"[G] no usable_start for {root} in the fixture meta"
    return max(START, u)


def day_table(root):
    start = usable_start(root)
    b = pd.read_csv(FIX / f"fut_{root}_rth_1m.csv.gz", dtype={"day": str, "hhmm": str, "contract": str}); b = b[(b["day"] >= start) & (b["day"] <= END)]
    assert b["day"].max() <= END and b["day"].min() >= start, "[F] a bar outside the usable window"
    s = pd.read_csv(FIX / "fut_index_sessions.csv.gz", dtype={"day": str, "contract": str}); s = s[(s["root"] == root) & (s["day"] >= start) & (s["day"] <= END)].sort_values("day").reset_index(drop=True)
    s["prev_close"] = s["p1600"].shift(1); s["prev_contract"] = s["contract"].shift(1); s["prev_day"] = s["day"].shift(1)
    w = b[(b["hhmm"] >= ENTRY) & (b["hhmm"] <= EXIT)]; g = w.groupby("day")
    win = pd.DataFrame({"n_win": g.size(), "p1530": g["open"].first(), "lo_path": g["low"].apply(lambda x: x.to_numpy().tolist()), "hi_path": g["high"].apply(lambda x: x.to_numpy().tolist())})
    fh = b[b["hhmm"] == FH_END].groupby("day")["open"].first().rename("p1000")
    d = s.set_index("day").join(win, how="left").join(fh, how="left")
    ok = (d["bars"] >= FULL_DAY) & (d["n_win"] == N_WINDOW) & (d["contract"] == d["prev_contract"]) & d["prev_close"].notna() & d["p1530"].notna() & d["p1600"].notna()
    d = d[ok].copy(); d["rROD"] = d["p1530"] / d["prev_close"] - 1; d["rFH"] = d["p1000"] / d["p0930"] - 1; d["rLH"] = d["p1600"] / d["p1530"] - 1
    d = d[d["rROD"] != 0].copy(); d["side"] = np.sign(d["rROD"]).astype(int)
    lo = np.array(d["lo_path"].tolist()); hi = np.array(d["hi_path"].tolist()); e = d["p1530"].to_numpy()[:, None]; side = d["side"].to_numpy()[:, None]
    excursion = np.where(side > 0, lo - e, e - hi); fav = np.where(side > 0, hi - e, e - lo)
    d["mae_pts"] = np.minimum(excursion.min(axis=1), 0.0); d["mfe_pts"] = np.maximum(fav.max(axis=1), 0.0); d["pnl_pts"] = d["side"] * (d["p1600"] - d["p1530"]); d["pnl_bp"] = d["side"] * d["rLH"] * 1e4
    d["mae_bp"] = d["mae_pts"] / d["p1530"] * 1e4; m = MULT[root]; d["pnl_usd"] = d["pnl_pts"] * m; d["mae_usd"] = d["mae_pts"] * m; d["mfe_usd"] = d["mfe_pts"] * m; d["cost_usd"] = COST[root]; d["net_usd"] = d["pnl_usd"] - COST[root]
    d["cost_bp"] = COST[root] / (d["p1530"] * m) * 1e4; d["net_bp"] = d["pnl_bp"] - d["cost_bp"]; d["root"] = root
    return d.drop(columns=["lo_path", "hi_path"]).reset_index()


# ------------------------------------------------------------------------------------------ statistics
def nw_beta(y, x, lags=NW_LAGS):
    x = np.asarray(x, float); y = np.asarray(y, float); X = np.column_stack([np.ones_like(x), x]); b = np.linalg.lstsq(X, y, rcond=None)[0]; u = y - X @ b; n = len(y)
    S = (X * u[:, None]).T @ (X * u[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1); G = (X[L:] * u[L:, None]).T @ (X[:-L] * u[:-L, None]); S += w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X); V = XtX_inv @ S @ XtX_inv
    return float(b[1]), float(b[1] / math.sqrt(V[1, 1])), int(n)


def rotation_null(sign, rlh_bp):
    """Exact: the sign series rolled by every offset 1..T-1; the strategy mean per trade on the real rLH."""
    T = len(sign); out = np.empty(T - 1)
    for k in range(1, T):
        out[k - 1] = float((np.roll(sign, k) * rlh_bp).mean())
    return out


def sign_null(rng, rlh_bp, n=N2_DRAWS):
    s = rng.choice([-1.0, 1.0], size=(n, len(rlh_bp))); return (s * rlh_bp[None, :]).mean(axis=1)


def block_boot(x, dates, n_boot=1000, seed=7):
    mon = np.array([str(d)[:7] for d in dates]); keys, inv = np.unique(mon, return_inverse=True); sums = np.bincount(inv, weights=x); cnts = np.bincount(inv); rng = np.random.default_rng(seed); m = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); m[b] = sums[pick].sum() / cnts[pick].sum()
    return float(m.std(ddof=1)), float(x.mean())


def per_root_stats(d, rng):
    pnl = d["pnl_bp"].to_numpy(); sign = d["side"].to_numpy().astype(float); rlh = d["rLH"].to_numpy() * 1e4; dates = d["day"].to_numpy()
    rot = rotation_null(sign, rlh); s2 = sign_null(rng, rlh); se_boot, mean = block_boot(pnl, dates)
    beta, t, n = nw_beta(d["rLH"] * 100, d["rROD"] * 100); post = d[d["day"] >= POST]; beta_p, t_p, n_p = nw_beta(post["rLH"] * 100, post["rROD"] * 100)
    bfh, tfh, _ = nw_beta(d["rLH"] * 100, d["rFH"].fillna(0) * 100)
    eras = {}
    for lab, lo, hi in (("2010-14", "2010", "2014"), ("2015-19", "2015", "2019"), ("2020-23", "2020", "2023")):
        e = d[(d["day"] >= lo) & (d["day"] <= hi + "-12-31")]; eras[lab] = dict(n=int(len(e)), mean_bp=float(e["pnl_bp"].mean()) if len(e) else None, hit=float((e["pnl_bp"] > 0).mean()) if len(e) else None, beta=nw_beta(e["rLH"] * 100, e["rROD"] * 100)[0] if len(e) > 50 else None)
    mae = -d["mae_usd"].to_numpy()
    return dict(trades=int(len(d)), first=str(dates[0]), last=str(dates[-1]), mean_bp=float(mean), se_boot_bp=se_boot, median_bp=float(np.median(pnl)), sd_bp=float(pnl.std(ddof=1)), hit=float((pnl > 0).mean()),
                mean_usd=float(d["pnl_usd"].mean()), sd_usd=float(d["pnl_usd"].std(ddof=1)), cost_bp=float(d["cost_bp"].mean()), net_bp=float(d["net_bp"].mean()), net_usd=float(d["net_usd"].mean()),
                always_long_bp=float(rlh.mean()), per_bar_bp=float(mean / N_WINDOW), per_bar_se=float(se_boot / N_WINDOW),
                N1=dict(n=int(rot.size), p50=float(np.median(rot)), p95=float(np.quantile(rot, .95)), p99=float(np.quantile(rot, .99))), N2=dict(n=int(s2.size), p50=float(np.median(s2)), p95=float(np.quantile(s2, .95)), p99=float(np.quantile(s2, .99)), mc_se=float(s2.std(ddof=1) / math.sqrt(s2.size))),
                beta=dict(full=beta, t=t, n=n, post2018=beta_p, t_post=t_p, n_post=n_p, first_half_hour=bfh, t_fh=tfh), eras=eras,
                mae_usd=dict(p50=float(np.quantile(mae, .5)), p90=float(np.quantile(mae, .9)), p99=float(np.quantile(mae, .99)), worst=float(mae.max()), worst_day=str(dates[int(mae.argmax())]), p_gt_1000=float((mae > 1000).mean()), p_gt_2000=float((mae > 2000).mean())),
                mae_bp=dict(p50=float(np.quantile(-d["mae_bp"], .5)), p99=float(np.quantile(-d["mae_bp"], .99)), worst=float((-d["mae_bp"]).max())))


# ------------------------------------------------------------------------------------------ hurdle P through D440's lifecycle model
def sized_days(d, sessions, frac, fixed=None):
    """One row per in-sample session: contracts by the C4 rule (or a FIXED count -- the instrument's own floor, reported beyond the
    declared grid) and the day's (d_low, d_high, d_end) in dollars; flat days are zeros."""
    per = d.set_index("day")[["pnl_usd", "mae_usd", "mfe_usd", "cost_usd"]]; days = sessions["day"].to_numpy(); r = per["pnl_usd"].reindex(days).to_numpy(); traded = np.isfinite(r)
    sig_full = float(np.nanstd(r[traded], ddof=1)); static = frac * ACCOUNT / sig_full; contracts = np.zeros(len(days)); sig_hat = np.full(len(days), np.nan); k = 0; hist = []
    for i in range(len(days)):
        if traded[i]:
            if len(hist) >= VOL_WINDOW:
                sig_hat[i] = float(np.std(hist[-VOL_WINDOW:], ddof=1))
            n = frac * ACCOUNT / sig_hat[i] if np.isfinite(sig_hat[i]) and sig_hat[i] > 0 else static
            contracts[i] = fixed if fixed is not None else math.floor(min(n, VOL_CAP * static)); hist.append(r[i])
    end = np.where(traded, np.nan_to_num(r) - per["cost_usd"].reindex(days).fillna(0).to_numpy(), 0.0) * contracts
    low = np.where(traded, per["mae_usd"].reindex(days).fillna(0).to_numpy() - per["cost_usd"].reindex(days).fillna(0).to_numpy(), 0.0) * contracts; high = np.where(traded, per["mfe_usd"].reindex(days).fillna(0).to_numpy(), 0.0) * contracts
    return pd.DataFrame({"day": days, "contracts": contracts, "d_end": end, "d_low": np.minimum(low, end), "d_high": np.maximum(high, 0.0)})


def provider_of(h, n_paths):
    lo, hi, en = h["d_low"].to_numpy(float), h["d_high"].to_numpy(float), h["d_end"].to_numpy(float); n = len(en); order = np.arange(min(n_paths, n)).reshape(-1, 1)
    def provider(day, live_idx, _rng):
        j = (order[live_idx, 0] + day) % n; return lo[j], hi[j], en[j]
    return provider, min(n_paths, n)


def hurdle_p(d, sessions, D40, D86, plan, log=print):
    out = {}
    for frac in list(FRACS) + ["1ct"]:
        h = sized_days(d, sessions, 0.007, fixed=1) if frac == "1ct" else sized_days(d, sessions, frac); prov, npth = provider_of(h, N_PATHS); sim = D40.simulate_provider(plan, prov, n_paths=npth, days=HORIZON_DAYS, seed=SEED)
        yrs = h["day"].str[:4]; p5 = []
        for y, g in h.groupby(yrs):
            tot = g["d_end"].sum(); p5.append(float(g["d_end"].max() / tot) if tot > 0 else float("nan"))
        p5 = np.array(p5); ann = h.groupby(yrs)["d_end"].sum()
        c = dict(frac=frac, contracts_mean=float(h["contracts"].mean()), days_traded=int((h["contracts"] > 0).sum()), days_zero_size=int(((h["contracts"] == 0) & (h["d_end"] == 0)).sum()),
                 P3_worst_day_pct=float(h["d_low"].min() / ACCOUNT * 100), P3_days_below_2pct=int((h["d_low"] < -0.02 * ACCOUNT).sum()), P3_share=float((h["d_low"] < -0.02 * ACCOUNT).mean()),
                 P4_fund_life_years=float(sim["fund_days_mean"] / 252.0) if np.isfinite(sim["fund_days_mean"]) else None, P4_alive_at_600d=sim["p_alive_at_horizon"], P4_p_pass=sim["p_pass"], V=sim["V"], V_se=sim["V_se"], p_breached=sim["p_breached"],
                 P5_max_day_share_by_year=[float(x) for x in p5], P5_years_over_40=int(np.nansum(p5 > 0.40)), P5_years=int(np.isfinite(p5).sum()), ann_profit_mean_pct=float(ann.mean() / ACCOUNT * 100))
        out[str(frac)] = c; frac_lab = "1 contract fixed (beyond the grid)" if frac == "1ct" else f"f {100*frac:.1f}%"
        log(f"    {frac_lab}: contracts mean {c['contracts_mean']:.2f} (zero-size days {c['days_zero_size']})  P3 worst day {c['P3_worst_day_pct']:+.2f}% ({c['P3_days_below_2pct']} days < -2%)  P4 funded life {c['P4_fund_life_years'] if c['P4_fund_life_years'] is None else round(c['P4_fund_life_years'], 2)} yr, alive at 600 d {100*c['P4_alive_at_600d']:.0f}%, pass {100*c['P4_p_pass']:.0f}%, V {c['V']:+.0f} +- {c['V_se']:.0f}  P5 years > 40%: {c['P5_years_over_40']}/{c['P5_years']}  ann {c['ann_profit_mean_pct']:+.1f}%")
    return out


# ------------------------------------------------------------------------------------------ the study
def run():
    t0 = time.time(); print("D463 -- market intraday momentum, the last 30 minutes, on the D462 fixtures\n      the bar was committed in dd5801c BEFORE this ran; 2010-2023; 2024-2026 unread; no holdout\n")
    meta = json.loads(META.read_text()); roots = [r for r in ROOTS if meta["gates"].get(r, {}).get("passes")]; skipped = [r for r in ROOTS if r not in roots]
    assert PRIMARY in roots, "[G] the primary root's fixture has not passed its gates"; print(f"  roots with all D462 gates passed: {roots}; not run: {skipped} (see the D462 ADDENDUM)")
    D40 = _load("d440l", "d440_lifecycle.py"); D86 = D40.D386; plan = [p for p in D86.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    sessions_all = pd.read_csv(FIX / "fut_index_sessions.csv.gz", dtype={"day": str, "contract": str}); rng = np.random.default_rng(SEED); res = dict(spec="dd5801c", start={r: usable_start(r) for r in roots}, end=END, roots={}, hurdle_P={}, bar={}, not_run=skipped); frames = []
    for root in roots:
        d = day_table(root); frames.append(d); st = per_root_stats(d, rng); res["roots"][root] = st
        print(f"  {root}: {st['trades']:,} trades {st['first']}..{st['last']}  mean {st['mean_bp']:+.2f} +- {st['se_boot_bp']:.2f} bp (median {st['median_bp']:+.2f}, sd {st['sd_bp']:.1f}, hit {100*st['hit']:.1f}%)  ${st['mean_usd']:+.1f}/contract  cost {st['cost_bp']:.2f} bp -> net {st['net_bp']:+.2f} bp (${st['net_usd']:+.1f})  always-long {st['always_long_bp']:+.2f}")
        print(f"       N1 rotation p50 {st['N1']['p50']:+.2f} p95 {st['N1']['p95']:+.2f} p99 {st['N1']['p99']:+.2f} (exact, {st['N1']['n']:,} offsets)   N2 signs p50 {st['N2']['p50']:+.2f} p95 {st['N2']['p95']:+.2f} +- {st['N2']['mc_se']:.2f}   |  beta x100 full {st['beta']['full']:+.2f} (t {st['beta']['t']:+.1f}, n {st['beta']['n']:,})  post-2018 {st['beta']['post2018']:+.2f} (t {st['beta']['t_post']:+.1f})  first-half-hour {st['beta']['first_half_hour']:+.2f} (t {st['beta']['t_fh']:+.1f})")
        print(f"       MAE $/contract p50 {st['mae_usd']['p50']:.0f} p90 {st['mae_usd']['p90']:.0f} p99 {st['mae_usd']['p99']:.0f} worst {st['mae_usd']['worst']:.0f} ({st['mae_usd']['worst_day']});  P(MAE > $1,000) {100*st['mae_usd']['p_gt_1000']:.2f}%  P(> $2,000) {100*st['mae_usd']['p_gt_2000']:.2f}%;  MAE bp p50 {st['mae_bp']['p50']:.1f} p99 {st['mae_bp']['p99']:.0f}   |  eras " + "  ".join(f"{k}: {v['mean_bp']:+.2f} bp hit {100*v['hit']:.0f}% beta {v['beta']:+.2f}" if v["mean_bp"] is not None else f"{k}: -" for k, v in st["eras"].items()))
    pd.concat(frames, ignore_index=True).to_csv(TRADES, index=False, compression="gzip")
    es = [f for f in frames if f["root"].iat[0] == PRIMARY][0]; sess_es = sessions_all[(sessions_all["root"] == PRIMARY) & (sessions_all["day"] >= usable_start(PRIMARY)) & (sessions_all["day"] <= END)].sort_values("day")
    print(f"\n  HURDLE P on {PRIMARY}, MFFU Rapid EOD 50K, C4 sizing (f x $50,000 / sigma_hat over the prior {VOL_WINDOW} traded days, floor to whole contracts, cap {VOL_CAP:.0f}x static), {HORIZON_DAYS}-day horizon")
    res["hurdle_P"] = hurdle_p(es, sess_es, D40, D86, plan)
    st = res["roots"][PRIMARY]; F1 = bool(st["mean_bp"] > 0 and st["mean_bp"] > st["N1"]["p95"] and st["mean_bp"] > st["N2"]["p95"] + 2 * st["N2"]["mc_se"])
    F3 = bool(st["beta"]["full"] > 0 and st["beta"]["t"] > 2 and st["beta"]["post2018"] >= POST_BETA_FLOOR)
    ok_f = [k for k, c in res["hurdle_P"].items() if k != "1ct" and (c["P4_fund_life_years"] or 0) >= 3 and c["V"] > 2 * c["V_se"] and c["P3_worst_day_pct"] >= -2 and c["P5_years_over_40"] == 0]     # the declared grid only; 1ct is reported
    res["bar"] = dict(F1=F1, F3=F3, F3_full_beta_positive_t2=bool(st["beta"]["full"] > 0 and st["beta"]["t"] > 2), F3_post2018_ge_3=bool(st["beta"]["post2018"] >= POST_BETA_FLOOR), hurdle_P_clearing_fracs=ok_f, candidate=bool(F1 and F3 and ok_f))
    print(f"\nTHE BAR ({PRIMARY}, in-sample)\n  F1 gross > 0 and > N1 p95 and > N2 p95 + 2 MC-SE : {F1}   ({st['mean_bp']:+.2f} vs N1 {st['N1']['p95']:+.2f}, N2 {st['N2']['p95']:+.2f})\n  F3 beta > 0 at t > 2 AND post-2018 beta >= 3.0     : {F3}   (full {st['beta']['full']:+.2f} t {st['beta']['t']:+.1f}; post {st['beta']['post2018']:+.2f})\n  hurdle P clearing at some f (P4 >= 3 yr, V > 2 SE, P3 worst <= 2%, P5 0 years > 40%) : {ok_f or 'none'}\n  CANDIDATE for the unread slice: {res['bar']['candidate']}")
    R = res["roots"]; hp = res["hurdle_P"]; nan = float("nan"); gb = lambda r: R[r]["beta"]["full"] if r in R else nan; gm = lambda r: R[r]["mean_bp"] if r in R else nan
    print("\nPREDICTIONS\n" + f"  X-a ES beta +2.5..+6.0 (t 2-5), post-2018 +0.5..+3.5; NQ >= ES; YM, RTY same sign : ES {R['ES']['beta']['full']:+.2f} (t {R['ES']['beta']['t']:+.1f}) post {R['ES']['beta']['post2018']:+.2f};  NQ {gb('NQ'):+.2f}  YM {gb('YM'):+.2f}  RTY {gb('RTY'):+.2f}\n"
          + f"  X-b mean +1.5..+4.0 bp, hit 52-55%, always-long +0.5..+1.5, N1 p95 +1.2..+2.0, N2 p95 +1.0..+1.6 : {R['ES']['mean_bp']:+.2f}, {100*R['ES']['hit']:.1f}%, {R['ES']['always_long_bp']:+.2f}, N1 {R['ES']['N1']['p95']:+.2f}, N2 {R['ES']['N2']['p95']:+.2f};  RTY mean {gm('RTY'):+.2f}\n"
          + f"  X-c sd 18-28 bp; MAE p50 6-10 bp, p99 50-90, worst > 200; P(>$1,000) 2-6%, P(>$2,000) 0.3-1.5% : sd {R['ES']['sd_bp']:.1f}; MAE bp p50 {R['ES']['mae_bp']['p50']:.1f} p99 {R['ES']['mae_bp']['p99']:.0f} worst {R['ES']['mae_bp']['worst']:.0f}; {100*R['ES']['mae_usd']['p_gt_1000']:.2f}% / {100*R['ES']['mae_usd']['p_gt_2000']:.2f}%\n"
          + f"  X-d cost 0.4-0.6 bp; net > 0                                                     : cost {R['ES']['cost_bp']:.2f}  net {R['ES']['net_bp']:+.2f}\n"
          + f"  X-e f=0.2% sizes 0 on most days; P3 breaches at f >= 0.7%; P4 < 1 yr at every f   : " + "  ".join(f"{('1ct' if k == '1ct' else f'f{100*float(k):.1f}%')}: {c['contracts_mean']:.1f} ct, worst {c['P3_worst_day_pct']:+.1f}%, life {c['P4_fund_life_years'] if c['P4_fund_life_years'] is None else round(c['P4_fund_life_years'], 2)} yr" for k, c in hp.items()) + "\n"
          + f"  X-f same sign on all four; strongest 2010-14, weakest 2020-23                    : signs {[(r, int(np.sign(R[r]['beta']['full']))) for r in R]};  ES eras " + " ".join(f"{k} {v['mean_bp']:+.2f}" for k, v in R['ES']['eras'].items()))
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)} and {TRADES.name}   {(time.time()-t0)/60:.1f} min   (2010-2023 only; 2024-2026 unread; no holdout)")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) nw_beta on synthetic; rotation null at offset 0 equals the real mean; sign null is centred")
    rng = np.random.default_rng(1); x = rng.normal(0, 1, 3000); y = 0.05 * x + rng.normal(0, 1, 3000); b, t, n = nw_beta(y, x); assert abs(b - 0.05) < 0.02 and t > 2 and n == 3000
    sign = np.sign(x); rlh = y * 100; real = float((sign * rlh).mean()); rot = rotation_null(sign, rlh); assert abs(float((np.roll(sign, 0) * rlh).mean()) - real) < 1e-12 and rot.size == 2999 and abs(np.median(rot)) < 0.5 * abs(real)
    s2 = sign_null(rng, rlh, 2000); assert abs(s2.mean()) < 0.2 and s2.std() > 0
    print(f"  beta {b:.3f} (t {t:.1f}); real {real:+.2f} vs rotation median {np.median(rot):+.2f}; sign null mean {s2.mean():+.3f}")
    print("== (b) the sized-days rule: whole contracts, the 21-trade sigma, the cap, flat days are zeros; provider rolls the start")
    days = [f"2015-{m:02d}-{d:02d}" for m in range(1, 13) for d in (5, 15, 25)]; d = pd.DataFrame(dict(day=days[:30], pnl_usd=np.where(np.arange(30) % 2 == 0, 400.0, -300.0), mae_usd=-350.0, mfe_usd=500.0, cost_usd=17.0)); sess = pd.DataFrame(dict(day=days))
    h = sized_days(d, sess, 0.004); assert len(h) == 36 and (h["contracts"] % 1 == 0).all() and (h.iloc[30:][["d_end", "d_low", "d_high"]] == 0).all().all() and (h["d_low"] <= h["d_end"]).all() and (h["d_high"] >= 0).all()
    sig = d["pnl_usd"].iloc[:21].std(ddof=1); n21 = math.floor(min(0.004 * ACCOUNT / sig, VOL_CAP * 0.004 * ACCOUNT / d["pnl_usd"].std(ddof=1))); assert h["contracts"].iat[21] == n21, (h["contracts"].iat[21], n21)
    prov, npth = provider_of(h, 5); lo, hi, en = prov(0, np.array([0, 1]), None); assert en[0] == h["d_end"].iat[0] and en[1] == h["d_end"].iat[1]; lo2, hi2, en2 = prov(1, np.array([0]), None); assert en2[0] == h["d_end"].iat[1]
    print(f"  ok: contracts on day 22 = floor(0.4% x 50k / sigma21) = {n21}; flat days zero; provider start rolls")
    print("== (c) day_table on the real fixtures, if built: [F] no bar after END, 30 bars in every window, same-contract days only, MAE <= 0 <= MFE")
    if (FIX / "fut_ES_rth_1m.csv.gz").exists():
        d = day_table("ES"); assert d["day"].max() <= END and (d["n_win"] == N_WINDOW).all() and (d["contract"] == d["prev_contract"]).all() and (d["mae_pts"] <= 0).all() and (d["mfe_pts"] >= 0).all() and (d["side"].abs() == 1).all()
        print(f"  ES: {len(d):,} trade days, {d['day'].min()}..{d['day'].max()}")
    else:
        print("  fixtures not built yet; skipped")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
