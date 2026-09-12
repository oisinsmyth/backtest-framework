"""D499 -- stage 0: hourly reversal around the 23-hour session on eight roots. Does the hour after a large move (top-decile |r_h| for that
hour-of-day, causal) revert, is it larger in thin hours (the 11 lowest-volume entry hours of the 21, fixed by the clock), and does it clear
the fee in ticks? k = 1 primary, k = 2, 3 secondary; exact enumerated common rotation per root and a 16-cell family maximum; the relative-
volume split; the FINDINGS s69 yardstick by hour. Spec committed in 467500f BEFORE this file. 2016-2023; 2024+ unread (raises past END).

    uv run python -u scripts/run_d499_hourly_reversal_stage0.py --run
    uv run python -u scripts/run_d499_hourly_reversal_stage0.py --selftest

Every trade opens at o_{h+1} after hour h closes and exits at c_{h+k}, no later than the 15:59 close; no trade holds the 18:00 -> 09:00
leg as a leg, and the sign is AGAINST the last hour's move. That keeps the record outside BOOK_PROP's closure of the overnight line.
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
OUT = REPO / "data" / "d499_hourly_reversal_stage0.json"; SPEC = "467500f"
START, END = "2016-01-04", "2023-12-29"
ROOTS = ["ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E"]
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "GC": 10.0, "CL": 100.0, "6E": 12_500.0, "ZN": 1_000.0, "ZB": 1_000.0}
TICK = {"ES": 0.25, "NQ": 0.25, "YM": 1.0, "GC": 0.1, "CL": 0.01, "6E": 0.0001, "ZN": 1 / 64, "ZB": 1 / 32}
UNIT = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "GC": "MGC", "CL": "MCL", "6E": "M6E", "ZN": "ZN", "ZB": "ZB"}
FEE = {r: (6.0 if r in ("ZN", "ZB") else 3.0) for r in ROOTS}
SEG = [f"h{h:02d}" for h in [18, 19, 20, 21, 22, 23] + list(range(0, 17))]; LAST_EXIT = SEG.index("h15")          # 21: the 15:59 close
N_ENTRY = LAST_EXIT                                                                                                  # entry hours h18..h14 = indices 0..20
OFF = list(range(0, SEG.index("h08") + 1)); RTH = list(range(SEG.index("h09"), N_ENTRY))                             # US-clock split (secondary)
WARM, MINP, Q, KS, N_THIN = 250, 200, 0.90, (1, 2, 3), 11
N_BOOT, SEED = 500, 499
D66 = _load("d466c", "run_d466_components.py")


# ------------------------------------------------------------------------------------------ data
def load_root(T, root):
    t = T[(T["root"] == root) & T["same_front"] & (T["day"] >= START) & (T["day"] <= END)].sort_values("day")
    assert len(t) and t["day"].max() <= END, "2024+ is unread under this record"
    O = np.column_stack([t[f"{s}_o"].to_numpy(float) for s in SEG]); C = np.column_stack([t[f"{s}_c"].to_numpy(float) for s in SEG]); V = np.column_stack([t[f"{s}_v"].to_numpy(float) for s in SEG])
    bad = (O <= 0) | (C <= 0); O = np.where(bad, np.nan, O); C = np.where(bad, np.nan, C)
    return dict(days=t["day"].to_numpy(), O=O, C=C, V=V)


def signals(O, C, V):
    """r in bp per hour; causal top-decile threshold per hour-of-day (trailing WARM sessions, shifted); relative volume; the trade sign."""
    r = (C / O - 1.0) * 1e4
    q = pd.DataFrame(np.abs(r)).rolling(WARM, min_periods=MINP).quantile(Q).shift(1).to_numpy()
    vmed = pd.DataFrame(V).rolling(WARM, min_periods=MINP).median().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        rel = V / vmed
    trig = np.isfinite(r) & np.isfinite(q) & (np.abs(r) >= q)
    sgn = np.where(trig, -np.sign(r), 0.0)
    return r, q, rel, sgn


def forward(O, C, k, mult):
    """Per entry hour i (0..LAST_EXIT-k): $ per contract and bp from o_{i+1} to c_{i+k}; the $ column is what a LONG earns."""
    m = LAST_EXIT - k + 1; P = np.full((O.shape[0], m), np.nan); F = np.full_like(P, np.nan)
    for i in range(m):
        e, x = O[:, i + 1], C[:, i + k]; P[:, i] = (x - e) * mult; F[:, i] = (x / e - 1.0) * 1e4
    return P, F


def groups(V):
    med = np.nanmedian(V[:, :N_ENTRY], axis=0); order = np.argsort(med, kind="stable")
    return dict(thin=sorted(int(i) for i in order[:N_THIN]), thick=sorted(int(i) for i in order[N_THIN:]))


def cell_trades(days, sgn, rel, P, F, cols, k):
    cols = [i for i in cols if i <= LAST_EXIT - k]; rows = []
    for i in cols:
        s = sgn[:, i]; ok = (s != 0) & np.isfinite(P[:, i])
        idx = np.flatnonzero(ok); rows.append(pd.DataFrame(dict(day=days[idx], hour=SEG[i], i=i, k=k, sign=s[idx], pnl_usd=s[idx] * P[idx, i], f_bp=s[idx] * F[idx, i], rel=rel[idx, i])))
    d = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["day", "hour", "i", "k", "sign", "pnl_usd", "f_bp", "rel"])
    return d.sort_values(["day", "i"]).reset_index(drop=True)


# ------------------------------------------------------------------------------------------ statistics
def trimmed(x, frac=0.01):
    x = np.sort(np.asarray(x, float)); n = len(x); c = int(math.floor(n * frac)); return float(x[c:n - c].mean()) if n - 2 * c > 0 else float("nan")


def boot_se_mean(x, days, n_boot=N_BOOT, seed=SEED):
    mon = np.array([str(d)[:7] for d in days]); keys, inv = np.unique(mon, return_inverse=True); rng = np.random.default_rng(seed); out = np.empty(n_boot); x = np.asarray(x, float)
    g = [x[inv == j] for j in range(keys.size)]
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); out[b] = np.concatenate([g[j] for j in pick]).mean()
    return float(out.std(ddof=1))


def stats(d, root, cal):
    x = d["pnl_usd"].to_numpy(float); n = len(x); tick_usd = TICK[root] * MULT[root]
    if n < 5:
        return dict(n=n)
    mean = float(x.mean()); se = float(x.std(ddof=1) / math.sqrt(n)); seb = boot_se_mean(x, d["day"].to_numpy()); yrs = d["day"].str[:4]
    halves = [float(x[(yrs <= "2019").to_numpy()].mean()) if (yrs <= "2019").any() else np.nan, float(x[(yrs >= "2020").to_numpy()].mean()) if (yrs >= "2020").any() else np.nan]
    daily = pd.Series(x - FEE[root]).groupby(d["day"].to_numpy()).sum(); net = daily.reindex(cal).fillna(0.0).to_numpy()
    skew = float(pd.Series(x).skew()); by_year = {y: float(x[(yrs == y).to_numpy()].mean()) for y in sorted(yrs.unique())}
    return dict(n=n, per_year=float(n / max(1, len(set(s[:4] for s in cal)))), gross_mean_usd=mean, mean_bp=float(d["f_bp"].mean()), median_usd=float(np.median(x)), trimmed_usd=trimmed(x), hit=float((x > 0).mean()), skew=skew,
                mean_ticks=mean / tick_usd, net_A_usd=mean - FEE[root], net_B_usd=mean - FEE[root] - tick_usd, se_plain=se, z_plain=mean / se, se_boot=seb, z_boot=mean / seb if seb > 0 else float("nan"),
                halves_usd=halves, same_sign_halves=bool(np.sign(halves[0]) == np.sign(halves[1]) == np.sign(mean)), by_year_usd=by_year, positive_years=int(sum(v > 0 for v in by_year.values())), n_years=len(by_year),
                component=dict(net_sharpe=D66.sharpe(net), net_sharpe_se=D66.sharpe_boot(net, np.asarray(cal)), gross_sharpe=D66.sharpe(pd.Series(x).groupby(d["day"].to_numpy()).sum().reindex(cal).fillna(0.0).to_numpy()), worst_day_usd=float(net.min()), daily_sd_usd=float(net.std(ddof=1))))


def rotation(sgn, P, cols, k, d_max=None):
    """Exact common rotation of the forward-P&L matrix against the signal matrix by d sessions, d = 1..n-1: the cell's gross mean and its plain z per offset.
    Both matrices keep their hour-of-day structure; what moves is the alignment of a session's moves with the hours that follow them."""
    cols = [i for i in cols if i <= LAST_EXIT - k]; S = sgn[:, cols]; Pc = P[:, cols]; fin = np.isfinite(Pc).astype(float); Pn = np.nan_to_num(Pc); A = np.abs(S)
    n = S.shape[0]; D = n - 1 if d_max is None else min(d_max, n - 1); mean = np.full(D, np.nan); z = np.full(D, np.nan)
    for d in range(1, D + 1):
        Pd = np.roll(Pn, -d, axis=0); Fd = np.roll(fin, -d, axis=0); x = S * Pd; cnt = float((A * Fd).sum())
        if cnt < 5:
            continue
        s1 = float(x.sum()); s2 = float((x * x).sum()); m = s1 / cnt; var = max(s2 / cnt - m * m, 0.0); mean[d - 1] = m; z[d - 1] = m / math.sqrt(var / cnt) if var > 0 else np.nan
    return mean, z


def rotation_slow(sgn, P, cols, k, d):
    """The same statistic by an explicit loop over trades -- the check that `rotation` is exact."""
    cols = [i for i in cols if i <= LAST_EXIT - k]; n = sgn.shape[0]; xs = []
    for i in cols:
        for t in range(n):
            if sgn[t, i] != 0 and np.isfinite(P[(t + d) % n, i]):
                xs.append(sgn[t, i] * P[(t + d) % n, i])
    x = np.array(xs); m = x.mean(); var = (x * x).mean() - m * m; return float(m), float(m / math.sqrt(var / len(x)))


def beta_by_hour(r, F1):
    out = []
    for i in range(F1.shape[1]):
        ok = np.isfinite(r[:, i]) & np.isfinite(F1[:, i]); a, b = r[ok, i], F1[ok, i]
        out.append(dict(hour=SEG[i], n=int(ok.sum()), beta=float(np.cov(a, b)[0, 1] / a.var(ddof=1)) if ok.sum() > 30 else np.nan, rho=float(np.corrcoef(a, b)[0, 1]) if ok.sum() > 30 else np.nan))
    return out


def pooled_beta(r, F1, cols, d=0):
    """Pooled beta over the group's columns with each column demeaned; F rotated by d sessions (d = 0 is the observed value)."""
    num = 0.0; den = 0.0; n = r.shape[0]
    for i in cols:
        a = r[:, i]; b = np.roll(F1[:, i], -d); ok = np.isfinite(a) & np.isfinite(b); a = a[ok] - a[ok].mean(); b = b[ok] - b[ok].mean(); num += float((a * b).sum()); den += float((a * a).sum())
    return num / den if den > 0 else float("nan")


def yardstick(O, C, root):
    tick_usd = TICK[root] * MULT[root]; P1, _ = forward(O, C, 1, MULT[root]); rows = []
    for i in range(P1.shape[1]):
        em = float(np.nanmean(np.abs(P1[:, i]))); rows.append(dict(hour=SEG[i], e_abs_move_usd=em, e_abs_move_ticks=em / tick_usd, fee_A_share=FEE[root] / em, fee_B_share=(FEE[root] + tick_usd) / em, breakeven_A=0.5 + FEE[root] / (2 * em), breakeven_B=0.5 + (FEE[root] + tick_usd) / (2 * em)))
    return rows


# ------------------------------------------------------------------------------------------ run
def analyse(data, root, verbose=True):
    O, C, V, days = data["O"], data["C"], data["V"], data["days"]; r, q, rel, sgn = signals(O, C, V); g = groups(V); cal = [str(d) for d in days[WARM:]]
    F = {k: forward(O, C, k, MULT[root]) for k in KS}; P1, F1 = F[1]; res = dict(root=root, unit=UNIT[root], sessions=int(len(days)), groups={k: [SEG[i] for i in v] for k, v in g.items()}, cells={}, m1={}, m3=yardstick(O, C, root), m4={}, us_clock={})
    # M1
    res["m1"]["by_hour"] = beta_by_hour(r, F1)
    for name, cols in list(g.items()) + [("off", OFF), ("rth", RTH)]:
        b = pooled_beta(r, F1, cols); band = np.array([pooled_beta(r, F1, cols, d) for d in range(1, len(days))]); band = band[np.isfinite(band)]
        res["m1"][name] = dict(beta=b, band_p2_5=float(np.quantile(band, .025)), band_p97_5=float(np.quantile(band, .975)), outside=bool(b < np.quantile(band, .025) or b > np.quantile(band, .975)))
    # M2 cells, N1 per cell, M4 within the primary cells
    trades = []
    for k in KS:
        Pk, Fk = F[k]
        for name, cols in g.items():
            d = cell_trades(days, sgn, rel, Pk, Fk, cols, k); trades.append(d.assign(group=name)); st = stats(d, root, cal)
            if st["n"] >= 5:
                nm, nz = rotation(sgn, Pk, cols, k); nz = nz[np.isfinite(nz)]; nm = nm[np.isfinite(nm)]
                st["null"] = dict(n_offsets=int(len(nz)), mean_p50=float(np.median(nm)), mean_p95=float(np.quantile(nm, .95)), z_p50=float(np.median(nz)), z_p95=float(np.quantile(nz, .95)), z_p99=float(np.quantile(nz, .99)), share_ge=float((nz >= st["z_plain"]).mean()))
                st["clears_N1"] = bool(st["z_plain"] > st["null"]["z_p95"]); st["_z_path"] = nz if k == 1 else None
                if k == 1:
                    lo = d[d["rel"] < 1]["pnl_usd"].to_numpy(); hi = d[d["rel"] >= 1]["pnl_usd"].to_numpy()
                    if len(lo) > 5 and len(hi) > 5:
                        se = math.sqrt(lo.var(ddof=1) / len(lo) + hi.var(ddof=1) / len(hi)); res["m4"][name] = dict(n_low=int(len(lo)), n_high=int(len(hi)), low_usd=float(lo.mean()), high_usd=float(hi.mean()), diff_usd=float(lo.mean() - hi.mean()), diff_se=se, diff_z=float((lo.mean() - hi.mean()) / se))
            res["cells"][f"{name}_k{k}"] = st
    for name, cols in (("off", OFF), ("rth", RTH)):
        d = cell_trades(days, sgn, rel, P1, F1, cols, 1); st = stats(d, root, cal)
        if st["n"] >= 5:
            _, nz = rotation(sgn, P1, cols, 1); nz = nz[np.isfinite(nz)]; st["null"] = dict(z_p50=float(np.median(nz)), z_p95=float(np.quantile(nz, .95)), share_ge=float((nz >= st["z_plain"]).mean())); st["clears_N1"] = bool(st["z_plain"] > st["null"]["z_p95"])
        res["us_clock"][name] = st
    if verbose:
        print(f"\n{root} ({UNIT[root]}): {len(days):,} same-front sessions; thin hours {res['groups']['thin']}\n   thick {res['groups']['thick']}")
        for name in ("thin", "thick", "off", "rth"):
            m = res["m1"][name]; print(f"   M1 pooled beta {name:5s} {m['beta']:+.4f}  band [{m['band_p2_5']:+.4f}, {m['band_p97_5']:+.4f}] {'OUTSIDE' if m['outside'] else 'inside'}")
        print(f"   {'cell':10s} {'N':>5s} {'/yr':>5s} {'gross$':>7s} {'bp':>6s} {'med$':>6s} {'trim$':>6s} {'ticks':>6s} {'netA$':>6s} {'netB$':>6s} {'hit':>5s} {'skew':>5s} {'z':>5s} {'N1 p95':>6s} {'>=obs':>5s} {'halves$':>13s} {'yrs+':>4s} {'Sharpe':>12s}")
        for key in list(res["cells"]) + [f"us_{n}" for n in res["us_clock"]]:
            st = res["cells"][key] if key in res["cells"] else res["us_clock"][key[3:]]
            if st["n"] < 5:
                print(f"   {key:10s} {st['n']:5d}  (too few)"); continue
            nl = st.get("null", {}); c = st["component"]
            print(f"   {key:10s} {st['n']:5d} {st['per_year']:5.0f} {st['gross_mean_usd']:+7.2f} {st['mean_bp']:+6.1f} {st['median_usd']:+6.2f} {st['trimmed_usd']:+6.2f} {st['mean_ticks']:+6.2f} {st['net_A_usd']:+6.2f} {st['net_B_usd']:+6.2f} {100*st['hit']:4.1f}% {st['skew']:+5.2f} {st['z_plain']:+5.2f} {nl.get('z_p95', float('nan')):+6.2f} {100*nl.get('share_ge', float('nan')):4.1f}% {st['halves_usd'][0]:+6.2f}/{st['halves_usd'][1]:+6.2f} {st['positive_years']:2d}/{st['n_years']:<2d} {c['net_sharpe']:+5.2f} ({c['net_sharpe_se']:.2f})")
        for name, m in res["m4"].items():
            print(f"   M4 {name:5s} low-relvol {m['low_usd']:+.2f} (n {m['n_low']}) vs high {m['high_usd']:+.2f} (n {m['n_high']}): diff {m['diff_usd']:+.2f} z {m['diff_z']:+.2f}")
        y = res["m3"]; print("   M3 fee A as a share of E|move| by hour: " + " ".join(f"{row['hour'][1:]}:{100*row['fee_A_share']:.0f}%" for row in y) + f"   (E|move| ticks thin {np.mean([y[i]['e_abs_move_ticks'] for i in g['thin']]):.1f}, thick {np.mean([y[i]['e_abs_move_ticks'] for i in g['thick']]):.1f})")
    return res, pd.concat(trades, ignore_index=True)


def family(results):
    """The 16 primary cells share each offset d, d = 1..min(n)-1; the family p95 is the 95th percentile of the per-offset maximum z."""
    paths = {f"{r}-{g}": results[r]["cells"][f"{g}_k1"]["_z_path"] for r in results for g in ("thin", "thick") if results[r]["cells"][f"{g}_k1"].get("_z_path") is not None}
    D = min(len(v) for v in paths.values()); M = np.column_stack([v[:D] for v in paths.values()]); fam = np.nanmax(M, axis=1)
    obs = {k: results[k.split("-")[0]]["cells"][f"{k.split('-')[1]}_k1"]["z_plain"] for k in paths}; best = max(obs, key=obs.get)
    return dict(n_cells=len(paths), n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)), p99=float(np.quantile(fam, .99)), observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()), observed=obs)


def decide(results, fam):
    verdict = "CLOSE"; picks = []; proceed = []
    for r in results:
        for g in ("thin", "thick"):
            st = results[r]["cells"][f"{g}_k1"]; tick_usd = TICK[r] * MULT[r]
            if st["n"] < 5:
                continue
            costB = FEE[r] + tick_usd; ok_cost = st["gross_mean_usd"] >= 1.5 * costB; ok_n1 = st.get("clears_N1", False); ok_fam = st["z_plain"] > fam["p95"]
            if ok_cost and ok_n1 and ok_fam and st["hit"] > 0.5 and st["same_sign_halves"]:
                proceed.append(f"{r}-{g}")
            elif ok_n1 and st["net_B_usd"] > 0:
                picks.append(f"{r}-{g}")
    if proceed:
        verdict = "PROCEED"
    elif picks:
        verdict = "PICK"
    return verdict, proceed, picks


def run():
    t0 = time.time(); print(f"D499 stage 0 -- hourly reversal around the 23-hour session on eight roots\n      spec committed in {SPEC} BEFORE this ran; {START}..{END}; 2024+ unread; k=1 primary; thin = the {N_THIN} lowest-volume entry hours of {N_ENTRY}")
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); meta = json.loads(META.read_text())
    roots = [r for r in ROOTS if meta["gates"][r]["passes"]]; assert roots == ROOTS, f"a root failed D467's gates: {[r for r in ROOTS if r not in roots]}"
    results = {}; trades = []
    for root in ROOTS:
        res, tr = analyse(load_root(T, root), root); results[root] = res; trades.append(tr.assign(root=root))
    fam = family(results); verdict, proceed, picks = decide(results, fam)
    print(f"\nFAMILY MAXIMUM of the plain z over {fam['n_cells']} primary cells, {fam['n_offsets']:,} common offsets (exact): p50 {fam['p50']:+.2f}  p95 {fam['p95']:+.2f}  p99 {fam['p99']:+.2f}   observed max {fam['observed_max']:+.2f} ({fam['observed_argmax']}); share of offsets >= observed {100*fam['share_ge']:.1f}%")
    print("   observed z by cell: " + "  ".join(f"{k}:{v:+.2f}" for k, v in sorted(fam["observed"].items(), key=lambda kv: -kv[1])))
    print(f"\nVERDICT (pre-registered rule): {verdict}" + (f"  proceed cells {proceed}" if proceed else "") + (f"  picks {picks}" if picks else ""))
    # predictions
    c = lambda r, g, k=1: results[r]["cells"][f"{g}_k{k}"]; m1 = lambda r, g: results[r]["m1"][g]
    print("\nPREDICTIONS")
    print("  X-a thin beta on index roots in [-0.08, -0.02], thick within +-0.02; |beta| < 0.03 on ZN/ZB/6E; thin outside its band on >= 2 roots : " + " ".join(f"{r}:{m1(r,'thin')['beta']:+.3f}/{m1(r,'thick')['beta']:+.3f}{'*' if m1(r,'thin')['outside'] else ''}" for r in ROOTS) + f"   (thin outside on {sum(m1(r,'thin')['outside'] for r in ROOTS)} roots)")
    print(f"  X-b NQ thin k1 +4..+10 bp (+$6..+15), hit 52-55%, 200-260/yr; ES thin +2..+6 bp; thick within +-3 bp : NQ {c('NQ','thin')['mean_bp']:+.1f} bp ${c('NQ','thin')['gross_mean_usd']:+.2f} hit {100*c('NQ','thin')['hit']:.1f}% {c('NQ','thin')['per_year']:.0f}/yr; ES thin {c('ES','thin')['mean_bp']:+.1f} bp; thick NQ {c('NQ','thick')['mean_bp']:+.1f} ES {c('ES','thick')['mean_bp']:+.1f}")
    print(f"  X-c family p95 +2.4..+2.9 and no primary cell clears it (CLOSE) : p95 {fam['p95']:+.2f}; observed max {fam['observed_max']:+.2f}; verdict {verdict}")
    sh = lambda r, cols: 100 * np.mean([results[r]["m3"][i]["fee_A_share"] for i in cols]); zn = 100 * min(row["fee_B_share"] for row in results["ZN"]["m3"])
    print("  X-d fee A 4-9% of E|f| thin, 2-4% thick on MNQ/MES/MCL/MGC; fee B on ZN > 30% every hour; thin break-even > 52% : " + " ".join(f"{r}:{sh(r, [SEG.index(h) for h in results[r]['groups']['thin']]):.1f}%/{sh(r, [SEG.index(h) for h in results[r]['groups']['thick']]):.1f}%" for r in ("NQ", "ES", "CL", "GC")) + f"; ZN fee B min share {zn:.0f}%; NQ thin break-even {100*np.mean([results['NQ']['m3'][SEG.index(h)]['breakeven_A'] for h in results['NQ']['groups']['thin']]):.1f}%")
    m4 = [(r, results[r]["m4"].get("thin")) for r in ROOTS]; pos = sum(1 for _, m in m4 if m and m["diff_usd"] > 0); big = sum(1 for _, m in m4 if m and abs(m["diff_z"]) >= 2)
    print(f"  X-e low-relvol reverts more (thin diff > 0) on >= 5 of 8, within 2 SE on all but <= 1 : positive on {pos} of 8; |z| >= 2 on {big}: " + " ".join(f"{r}:{m['diff_usd']:+.2f}({m['diff_z']:+.1f})" for r, m in m4 if m))
    for r in results:
        for k in list(results[r]["cells"]):
            results[r]["cells"][k].pop("_z_path", None)
    OUT.write_text(json.dumps(dict(spec="D499", commit=SPEC, start=START, end=END, roots=ROOTS, warm=WARM, q=Q, n_thin=N_THIN, results=results, family=fam, verdict=verdict, proceed=proceed, picks=picks), indent=1, default=float))
    tr = pd.concat(trades, ignore_index=True)
    for root in ROOTS:
        tr[tr["root"] == root].to_csv(REPO / "data" / f"d499_trades_{root}.csv.gz", index=False, compression="gzip", float_format="%.4f")
    print(f"\nwrote {OUT.relative_to(REPO)} and data/d499_trades_<root>.csv.gz   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def make_synth(n=1500, seed=3, plant=0.5, thin_cols=(1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 2), start_price=20_000.0):
    """A random-walk session table with a planted reversal in the THIN hours (low volume), none in the thick: after a top-decile hour move in a
    thin hour, the next hour returns -plant x that move plus noise."""
    rng = np.random.default_rng(seed); H = len(SEG); sig = np.full(H, 8.0); sig[list(thin_cols)] = 4.0; u = rng.normal(0, 1, (n, H)) * sig / 1e4
    V = np.full((n, H), 1000.0); V[:, list(thin_cols)] = 100.0; V *= rng.uniform(0.5, 1.5, (n, H))
    thr = {i: np.quantile(np.abs(u[:, i]), Q) for i in thin_cols}
    for i in thin_cols:
        big = np.abs(u[:, i]) >= thr[i]; u[big, i + 1] = -plant * u[big, i] + rng.normal(0, 0.5, big.sum()) * sig[i + 1] / 1e4
    O = np.empty((n, H)); C = np.empty((n, H)); p = start_price
    for t in range(n):
        for i in range(H):
            O[t, i] = p; p = p * (1 + u[t, i]); C[t, i] = p
    days = np.array([str(d.date()) for d in pd.bdate_range("2016-01-04", periods=n)]); return dict(days=days, O=O, C=C, V=V)


def cmd_selftest():
    print("D499 selftest")
    d = make_synth(); root = "NQ"; O, C, V, days = d["O"], d["C"], d["V"], d["days"]; r, q, rel, sgn = signals(O, C, V); g = groups(V)
    # [A] the partition is the planted one
    assert set(g["thin"]) == {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 2}, g
    # [B] exit bound: no trade exits after the 15:59 close
    for k in KS:
        Pk, Fk = forward(O, C, k, MULT[root]); tr = cell_trades(days, sgn, rel, Pk, Fk, list(range(N_ENTRY)), k); assert (tr["i"] + k).max() <= LAST_EXIT and (tr["i"] + k).max() == LAST_EXIT
    # [C] causality: the triggers up to t0 do not move when everything after t0 is replaced
    t0 = 500; O2, C2, V2 = O.copy(), C.copy(), V.copy(); rng = np.random.default_rng(9); C2[t0:] = O2[t0:] * (1 + rng.normal(0, 50, C2[t0:].shape) / 1e4); V2[t0:] *= 7
    _, _, _, sgn2 = signals(O2, C2, V2); assert np.array_equal(sgn[:t0], sgn2[:t0]) and not np.array_equal(sgn[t0:], sgn2[t0:])
    # [D] sign audit in money: after a DOWN hour the trade is long, and a rise to the exit pays positively; with an inverted multiplier it would not
    P1, F1 = forward(O, C, 1, MULT[root]); i = 3; t = np.flatnonzero((sgn[:, i] > 0))[0]; assert r[t, i] < 0 and sgn[t, i] == 1.0
    up = C[t, i + 1] > O[t, i + 1]; pnl = sgn[t, i] * P1[t, i]; assert (pnl > 0) == up, (pnl, up)
    Pneg, _ = forward(O, C, 1, -MULT[root]); assert bool(sgn[t, i] * Pneg[t, i] > 0) != bool(up), "the sign audit must fail on an inverted multiplier"
    # [E] the rotation is exact against an explicit loop, on a column set with ties (the planted hours share thresholds)
    mean, z = rotation(sgn, P1, g["thin"], 1, d_max=40)
    for dd in (1, 7, 33):
        ms, zs = rotation_slow(sgn, P1, g["thin"], 1, dd); assert ms == mean[dd - 1] and zs == z[dd - 1], (dd, ms, mean[dd - 1], zs, z[dd - 1])
    # [F] known answer: the planted thin cell clears its own null and the family bar; the thick cell (no plant) does not; without the plant the thin cell does not
    res, _ = analyse(d, root, verbose=False); res2, _ = analyse(make_synth(plant=0.0), root, verbose=False)
    thin, thick = res["cells"]["thin_k1"], res["cells"]["thick_k1"]; assert thin["clears_N1"] and thin["gross_mean_usd"] > 0 and thin["hit"] > 0.5, thin
    assert not thick["clears_N1"], thick["z_plain"]; assert not res2["cells"]["thin_k1"]["clears_N1"], res2["cells"]["thin_k1"]["z_plain"]
    fam = family({"NQ": res, "ES": res2}); assert thin["z_plain"] > fam["p95"] and fam["observed_argmax"] == "NQ-thin", fam
    v, pr, pk = decide({"NQ": res}, fam); assert v == "PROCEED" and pr == ["NQ-thin"], (v, pr, pk)
    v2, _, _ = decide({"NQ": res2}, family({"NQ": res2, "ES": res})); assert v2 in ("CLOSE", "PICK"), v2
    # [G] M1 sees the plant: thin beta negative and outside its band, thick inside
    assert res["m1"]["thin"]["beta"] < -0.15 and res["m1"]["thin"]["outside"] and not res["m1"]["thick"]["outside"], (res["m1"]["thin"], res["m1"]["thick"])
    print(f"  A partition  B exit bound  C causality  D sign audit (and its inverted break)  E exact rotation  F known answer (thin z {thin['z_plain']:+.2f} > N1 p95 {thin['null']['z_p95']:+.2f}, family p95 {fam['p95']:+.2f}; thick {thick['z_plain']:+.2f}; unplanted {res2['cells']['thin_k1']['z_plain']:+.2f})  G M1 (thin beta {res['m1']['thin']['beta']:+.3f})\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
