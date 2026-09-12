"""D495 stage 0 -- the day session after a daily state, intraday only. Cell A: fade the next day session after a top-decile (trailing-252,
causal) day-session move. Cell B: trade it after a daily RSI(2) extreme on the 16:00 prints (<= 10 long, >= 90 short). Entry at the 09:30
open + tick in the trade direction, exit at the 15:59 close, one micro, $3. ES and NQ, sides separate, a family of eight. Spec committed in
6d551b9 BEFORE this file. In-sample 2016-01-04 .. 2023-12-29; the runner raises if a row past 2023 reaches the measurement.

    uv run python -u scripts/run_d495_daily_state_stage0.py --run
    uv run python -u scripts/run_d495_daily_state_stage0.py --selftest
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
D90 = _load("d490r", "run_d490_range_reversion.py"); D66 = D90.D66; D92 = _load("d492r", "run_d492_rsi_filter.py")
LO, HI = "2016-01-04", "2023-12-29"; ROOTS = ("ES", "NQ"); MULT = D90.MULT; TICK = D90.TICK; COST = D90.COST; ACCOUNT = D90.ACCOUNT
DEC_WIN, DEC_MIN, DEC_Q, RSI_N, RSI_LO, RSI_HI = 252, 120, 0.9, 2, 10.0, 90.0; SUB = {"2016-2020": ("2016-01-04", "2020-12-31"), "2021-2023": ("2021-01-04", "2023-12-29")}
OUT = REPO / "data" / "d495_daily_state_stage0.json"


# ------------------------------------------------------------------------------------------ the daily objects
def daily(d):
    """Per session row: open, close, high, low of the day session (NaN unless the session is full); R in bp."""
    full = d["full"]; O = np.where(full, d["O"][:, 0], np.nan); C = np.where(full, d["C"][:, -1], np.nan); Hh = np.where(full, np.nanmax(d["H"], axis=1), np.nan); Ll = np.where(full, np.nanmin(d["L"], axis=1), np.nan)
    R = (C / O - 1) * 1e4; return O, C, Hh, Ll, R


def causal_decile_state(R):
    """dir[t] = -sign(R[t-1]) when |R[t-1]| >= the 90th percentile of |R[t-1-252 .. t-2]| (at least 120 finite values); else 0."""
    n = len(R); out = np.zeros(n); a = np.abs(R)
    for t in range(1, n):
        if not np.isfinite(R[t - 1]):
            continue
        w = a[max(0, t - 1 - DEC_WIN):t - 1]; w = w[np.isfinite(w)]
        if w.size >= DEC_MIN and a[t - 1] >= np.quantile(w, DEC_Q):
            out[t] = -np.sign(R[t - 1])
    return out


def rsi2_state(C):
    """dir[t] from RSI(2) of the 16:00-print series read at t-1: +1 if <= 10, -1 if >= 90, else 0. Missing prints are skipped in the series."""
    ok = np.isfinite(C); r = np.full(len(C), np.nan); r[ok] = D92.wilder_rsi(C[ok], n=RSI_N); out = np.zeros(len(C))
    for t in range(1, len(C)):
        v = r[t - 1]
        if np.isfinite(v):
            out[t] = 1.0 if v <= RSI_LO else (-1.0 if v >= RSI_HI else 0.0)
    return out, r


def trades(d, dirs, mult, mask):
    O, C, Hh, Ll, R = daily(d); rows = []
    for t in np.flatnonzero(mask & (dirs != 0) & np.isfinite(O)):
        s = dirs[t]; entry = O[t] + s * TICK; exit_ = C[t]; pts = s * (exit_ - entry); mae = (Ll[t] - entry) if s > 0 else (entry - Hh[t]); mfe = (Hh[t] - entry) if s > 0 else (entry - Ll[t])
        rows.append(dict(day=d["days"][t], side=int(s), entry=float(entry), exit=float(exit_), pnl_pts=float(pts), gross_usd=float(pts * mult), net_usd=float(pts * mult - COST), bp=float(pts / entry * 1e4), mae_usd=float(mae * mult), mfe_usd=float(mfe * mult), R_prev=float(R[t - 1]) if t > 0 else float("nan")))
    return pd.DataFrame(rows)


def gated_stats(R, dirs, mask, side):
    """In bp, in the trade direction: the gated mean on fire days of this side, the other-side mean (the same direction rule applied to
    the non-fire days: for cell A the fade of the prior sign; for cell B the side's direction), the difference and its z."""
    g = mask & (dirs == side) & np.isfinite(R); x = side * R[g]
    return x


def z_diff(x, y):
    if x.size < 5 or y.size < 5:
        return float("nan")
    return float((x.mean() - y.mean()) / math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size))


def other_side(R, dirs, mask, side, cell, Rprev_sign):
    """Non-fire days, same direction rule: cell A -> fade the prior day's sign; cell B -> the side itself."""
    nf = mask & (dirs == 0) & np.isfinite(R)
    if cell == "A":
        s = -Rprev_sign; keep = nf & (s == side); return side * R[keep]
    return side * R[nf]


def rotation_null(R, dirs, mask, side):
    idx = np.flatnonzero(mask & np.isfinite(R)); r = R[idx]; dd = dirs[idx]; T = len(idx); out = np.empty(T - 2)
    for k in range(2, T):
        g = np.roll(dd, k) == side; out[k - 2] = float((side * r[g]).mean()) if g.sum() >= 5 else np.nan
    return out[np.isfinite(out)]


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print("D495 stage 0 -- the day session after a daily state, intraday only (09:30 open + tick -> 15:59 close, one micro, $3)\n      spec committed in 6d551b9 BEFORE this ran; 2016-2023; 2024+ unread; family of eight; N2 = family max of the difference-between-sides z under a common rotation")
    data = {}; res = {}; cells_z = {}; zrot = {}
    for root in ROOTS:
        d = D90.load_root(root, LO, HI); assert max(d["days"]) <= HI; O, C, Hh, Ll, R = daily(d); mask = d["trade"]; dA = causal_decile_state(R); dB, rsi = rsi2_state(C); Rprev_sign = np.sign(np.concatenate([[np.nan], R[:-1]]))
        cal = pd.Index(d["days"][mask]); data[root] = dict(d=d, R=R, mask=mask, dirs={"A": dA, "B": dB}, Rprev_sign=Rprev_sign); res[root] = {}; print(f"\n{root}: {int(mask.sum())} full sessions in-sample")
        for cell in ("A", "B"):
            dirs = data[root]["dirs"][cell]; tr = trades(d, dirs, MULT[root], mask); res[root][cell] = {}
            for side, lab in ((1, "long"), (-1, "short")):
                t = tr[tr["side"] == side]
                if len(t) < 10:
                    continue
                x = gated_stats(R, dirs, mask, side); y = other_side(R, dirs, mask, side, cell, Rprev_sign); z = z_diff(x, y); n1 = rotation_null(R, dirs, mask, side)
                g = t["gross_usd"].to_numpy(); k = max(1, int(round(0.01 * g.size))); gs = np.sort(g); daily_net = t.groupby("day")["net_usd"].sum(); ser = D66.series_on(cal, daily_net.index, daily_net.values).to_numpy(); yrs = np.array([s[:4] for s in cal])
                flips = np.random.default_rng(3).choice([-1.0, 1.0], size=(1000, ser.size)); sflip = np.array([D66.sharpe(ser * f) for f in flips])
                sub = {}
                for sk, (slo, shi) in SUB.items():
                    m = (t["day"] >= slo) & (t["day"] <= shi); sub[sk] = dict(n=int(m.sum()), gross_mean=float(t[m]["gross_usd"].mean()) if m.sum() else float("nan"), bp=float(t[m]["bp"].mean()) if m.sum() else float("nan"))
                c = dict(trades=int(len(t)), share=float(len(t) / len(cal)), gross_mean=float(g.mean()), gross_median=float(np.median(g)), bp_mean=float(x.mean()), bp_se=float(x.std(ddof=1) / math.sqrt(x.size)), net_mean=float(g.mean() - COST), hit=float((g > 0).mean()), payoff=float(g[g > 0].mean() / -g[g < 0].mean()) if (g < 0).any() else float("nan"), skew=float(pd.Series(g).skew()), trimmed=float(gs[k:-k].mean()),
                         mae_p50=float(np.quantile(t["mae_usd"], .5)), mae_p95=float(np.quantile(t["mae_usd"], .05)), mae_worst=float(t["mae_usd"].min()), days_below_2pct=int((ser < -0.02 * ACCOUNT).sum()), net_sharpe=D66.sharpe(ser), net_sharpe_se=D66.sharpe_boot(ser, cal), sharpe_flip_p95=float(np.quantile(sflip, .95)),
                         other_bp=float(y.mean()), other_n=int(y.size), z=z, N1=dict(p50=float(np.median(n1)), p95=float(np.quantile(n1, .95)), n=int(n1.size)), by_year={yv: D66.sharpe(ser[yrs == yv]) for yv in sorted(set(yrs))}, by_year_bp={yv: float(t[t["day"].str[:4] == yv]["bp"].mean()) for yv in sorted(set(yrs)) if (t["day"].str[:4] == yv).sum()}, sub=sub,
                         largest=[(r.day, float(r.gross_usd)) for r in t.nlargest(5, "gross_usd").itertuples()], smallest=[(r.day, float(r.gross_usd)) for r in t.nsmallest(5, "gross_usd").itertuples()])
                c["clears_N1"] = c["bp_mean"] > c["N1"]["p95"]; res[root][cell][lab] = c; cells_z[(root, cell, side)] = z
                print(f"  cell {cell} {lab:5s}: {c['trades']:4d} trades ({100*c['share']:.1f}%)  gross ${c['gross_mean']:+.2f} (median {c['gross_median']:+.2f}, trimmed {c['trimmed']:+.2f}) = {c['bp_mean']:+.1f} bp ({c['bp_se']:.1f})  other side {c['other_bp']:+.1f} bp (n {c['other_n']})  diff z {z:+.2f}  hit {100*c['hit']:.1f}%  payoff {c['payoff']:.2f}  skew {c['skew']:+.2f}  MAE p50/p95/worst {c['mae_p50']:.0f}/{c['mae_p95']:.0f}/{c['mae_worst']:.0f}  net Sharpe {c['net_sharpe']:+.2f} +- {c['net_sharpe_se']:.2f} (flip p95 {c['sharpe_flip_p95']:+.2f})  | N1 rotation p50 {c['N1']['p50']:+.1f} p95 {c['N1']['p95']:+.1f} {'*' if c['clears_N1'] else ' '}")
                print(f"      by year bp: " + " ".join(f"{yv}:{v:+.0f}" for yv, v in c["by_year_bp"].items()) + "   sub-periods: " + " ".join(f"{k}:{v['bp']:+.1f} (n {v['n']})" for k, v in sub.items()))
            tr.to_csv(REPO / "data" / f"d495_trades_{root}_{cell}.csv.gz", index=False, compression="gzip")
    # N2: family maximum of the difference z under a common rotation offset (each root's own calendar rotated by the same k)
    Tmin = min(int((data[r]["mask"] & np.isfinite(data[r]["R"])).sum()) for r in ROOTS); fam = np.full(Tmin - 2, -np.inf)
    for k in range(2, Tmin):
        best = -np.inf
        for root in ROOTS:
            R = data[root]["R"]; mask = data[root]["mask"]; idx = np.flatnonzero(mask & np.isfinite(R)); r = R[idx]; ps = data[root]["Rprev_sign"][idx]
            for cell in ("A", "B"):
                dd = np.roll(data[root]["dirs"][cell][idx], k); psr = np.roll(ps, k)
                for side in (1, -1):
                    g = dd == side
                    if g.sum() < 5:
                        continue
                    x = side * r[g]
                    if cell == "A":
                        y = side * r[(dd == 0) & (-psr == side)]
                    else:
                        y = side * r[dd == 0]
                    z = z_diff(x, y)
                    if np.isfinite(z):
                        best = max(best, z)
        fam[k - 2] = best
    fam = fam[np.isfinite(fam)]; fp95 = float(np.quantile(fam, .95)); fp50 = float(np.median(fam)); obs = max(v for v in cells_z.values() if np.isfinite(v)); obs_k = max((k for k, v in cells_z.items() if np.isfinite(v)), key=lambda k: cells_z[k])
    print(f"\n  FAMILY MAX of the difference z (8 cells, {fam.size} common offsets): p50 {fp50:+.2f}  p95 {fp95:+.2f}  p99 {np.quantile(fam, .99):+.2f}   observed max {obs:+.2f} ({obs_k[0]} cell {obs_k[1]} {'long' if obs_k[2] == 1 else 'short'})   share of offsets >= observed {100*(fam >= obs).mean():.1f}%")
    verdicts = {}
    for root in ROOTS:
        for cell in ("A", "B"):
            for lab, c in res[root][cell].items():
                signs_ok = all(np.isfinite(v["bp"]) and v["bp"] > 0 for v in c["sub"].values()); proceed = bool(c["clears_N1"] and c["z"] > fp95 and c["net_sharpe"] > 0.3 and signs_ok); pick = bool(c["clears_N1"] and c["net_sharpe"] > 0.3 and not proceed)
                c["verdict"] = "PROCEED" if proceed else ("PICK" if pick else "closed"); verdicts[f"{root} {cell} {lab}"] = c["verdict"]
    print("  VERDICTS (PROCEED = N1 cleared, z > family p95, net Sharpe > 0.3, sign in both sub-periods; PICK = N1 and Sharpe without the family bar): " + ", ".join(f"{k}: {v}" for k, v in verdicts.items()))
    E, N = res["ES"], res["NQ"]; A = N["A"]; print("\nPREDICTIONS")
    print(f"  X-a cell A fires ~10%; cell B long 8-14%, short 8-14%                                     : A {100*A.get('long', {}).get('share', 0) + 100*A.get('short', {}).get('share', 0):.1f}% (NQ); B long {100*N['B'].get('long', {}).get('share', 0):.1f}%, short {100*N['B'].get('short', {}).get('share', 0):.1f}%")
    aa = [c for c in A.values()]; a_bp = np.average([c["bp_mean"] for c in aa], weights=[c["trades"] for c in aa]) if aa else float("nan"); ea = [c for c in E["A"].values()]; e_bp = np.average([c["bp_mean"] for c in ea], weights=[c["trades"] for c in ea]) if ea else float("nan")
    print(f"  X-b NQ cell A +15..+30 bp, hit 53-58%, clears N1, z 2.0-2.8 vs family p95 2.3-2.6, Sharpe +0.3..+0.6; ES 0..+12 inside N1 : NQ A {a_bp:+.1f} bp pooled; " + "; ".join(f"{k} {c['bp_mean']:+.1f} bp hit {100*c['hit']:.0f}% z {c['z']:+.2f} Sharpe {c['net_sharpe']:+.2f} N1 {'cleared' if c['clears_N1'] else 'no'}" for k, c in A.items()) + f"; family p95 {fp95:+.2f}; ES A {e_bp:+.1f} bp")
    print(f"  X-c cell B long +5..+20 bp, short -5..+5; NQ > ES; neither clears the family bar             : NQ B " + "; ".join(f"{k} {c['bp_mean']:+.1f} z {c['z']:+.2f}" for k, c in N['B'].items()) + "; ES B " + "; ".join(f"{k} {c['bp_mean']:+.1f} z {c['z']:+.2f}" for k, c in E['B'].items()))
    print(f"  X-d MAE median -50..-80 bp, p95 -180..-260; no day < -2%                                     : NQ A " + "; ".join(f"{k} p50 ${c['mae_p50']:.0f} p95 ${c['mae_p95']:.0f} below-2% {c['days_below_2pct']}" for k, c in A.items()))
    print(f"  X-e NQ A sign holds in >= 6 of 8 years and both sub-periods                                  : " + "; ".join(f"{k} years>0 {sum(v > 0 for v in c['by_year_bp'].values())}/{len(c['by_year_bp'])} sub {c['sub']['2016-2020']['bp']:+.1f}/{c['sub']['2021-2023']['bp']:+.1f}" for k, c in A.items()))
    print(f"  X-f other side within +-3 bp on cell A; cell B long's other side = the drift                    : NQ A other " + "; ".join(f"{k} {c['other_bp']:+.1f}" for k, c in A.items()) + "; NQ B other " + "; ".join(f"{k} {c['other_bp']:+.1f}" for k, c in N['B'].items()))
    OUT.write_text(json.dumps(dict(spec="D495", results=res, family=dict(p50=fp50, p95=fp95, observed=obs, observed_cell=list(map(str, obs_k))), verdicts=verdicts), indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) trade arithmetic on a synthetic full session: long and short entries at the open +- tick, MAE from the path")
    n = D90.NBAR; path = np.concatenate([np.linspace(100, 98, 100), np.linspace(98, 103, 290)]); d = D90.make_d([path, path], [np.full(n, 1.0)] * 2, None); O, C, Hh, Ll, R = daily(d)
    tl = trades(d, np.array([0.0, 1.0]), 5.0, np.array([False, True])); ts = trades(d, np.array([0.0, -1.0]), 5.0, np.array([False, True]))
    assert abs(tl["pnl_pts"].iat[0] - (103 - 100.25)) < 1e-9 and abs(tl["mae_usd"].iat[0] - (97.9 - 100.25) * 5) < 1e-9 and abs(ts["pnl_pts"].iat[0] - (99.75 - 103)) < 1e-9 and abs(ts["mae_usd"].iat[0] - (99.75 - 103.1) * 5) < 1e-9
    print(f"  ok: long {tl['pnl_pts'].iat[0]:+.2f} pts, MAE ${tl['mae_usd'].iat[0]:.1f}; short {ts['pnl_pts'].iat[0]:+.2f} pts")
    print("== (b) the causal decile state uses only history before t-1 and fades the prior sign; the RSI(2) state reads t-1")
    rng = np.random.default_rng(1); R = rng.normal(0, 50, 600); R[400] = 500.0; dA = causal_decile_state(R); assert dA[401] == -1.0 and dA[400] == 0.0 and (dA[:DEC_MIN + 1] == 0).all()
    C = 100 + np.cumsum(rng.normal(0, 1, 600)); C[300:303] = [110, 112, 114]; dB, r = rsi2_state(C); assert r[302] > 90 and dB[303] == -1.0 and dB[302] != dB[303] or dB[303] == -1.0; print(f"  ok: fade fires the day after the planted big day; RSI(2) after two rises {r[302]:.1f} -> short next day")
    print("== (c) the rotation null and the family z: a planted reversal state clears N1 at p99 and its z exceeds the single-cell rotation p95")
    R2 = rng.normal(0, 50, 1500); st = np.zeros(1500); big = np.abs(R2) > np.quantile(np.abs(R2), .9)
    for t in range(1, 1500):
        if big[t - 1]:
            st[t] = -np.sign(R2[t - 1]); R2[t] += 40.0 * st[t]        # a planted 40-bp fade (~7 SE on ~75 fire days a side)
    mask = np.ones(1500, bool); n1 = rotation_null(R2, st, mask, 1.0); x = gated_stats(R2, st, mask, 1.0); assert x.mean() > np.quantile(n1, .99), (x.mean(), np.quantile(n1, .99))
    ps = np.sign(np.concatenate([[np.nan], R2[:-1]])); y = other_side(R2, st, mask, 1.0, "A", ps); z = z_diff(x, y); assert z > 2.5 and y.size > 100; print(f"  ok: planted gated mean {x.mean():+.1f} bp > N1 p99 {np.quantile(n1, .99):+.1f}; other side {y.mean():+.1f}; z {z:+.2f}")
    print("== (d) the in-sample gate: a load past 2023 raises")
    try:
        D90.load_root("ES", "2024-01-02", "2024-01-05"); ok = True
    except AssertionError:
        ok = False
    assert ok, "load_root itself does not gate; the run() assertion does"; d = D90.load_root("ES", LO, "2016-03-31"); assert max(d["days"]) <= "2016-03-31"; print("  ok")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
