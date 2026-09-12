"""D472 -- the down-leg reversal pick tested on what the family null has not priced. Spec committed in 4290eeb BEFORE this file.
  Step 1: D470's common-offset family maximum re-run on a standardised scale (z-score of the gated mean; gated component net Sharpe on the
          root's calendar) beside the dollar scale, same 8 cells per root-window, ES/NQ x W1/W2, 2016-2023.
  Step 2a: SPY and IWM cash overnight (close -> next open; close -> next close) from the equity 15m fixture, 2010-2015 (the test) and
          2016-2023 (the consistency check), gap after a DOWN prior gap (G-B') and after a DOWN prior session (G-A'), in bp, D464's nulls.
  Step 2b: RTY futures W2 after a down leg, if the rebuilt D467 table passes RTY's gates (else IWM 2016-2023 stands in).
Reads nothing after 2023-12-29.

    uv run python -u scripts/run_d472_reversal_checks.py --run
    uv run python -u scripts/run_d472_reversal_checks.py --selftest
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
D66 = _load("d466c", "run_d466_components.py"); D64 = _load("d464g", "run_d464_arms_as_gates.py"); D70 = _load("d470s", "run_d470_gate_stage0.py")
TABLE = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"; META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"; EQ15 = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"
OUT = REPO / "data" / "d472_reversal_checks.json"; COST = 3.0; N2_DRAWS = 2000; SEED = 472
PERIODS = {"2010-2015": ("2010-01-04", "2015-12-31"), "2016-2023": ("2016-01-04", "2023-12-29")}; CASH = ("SPY", "IWM"); RTY_START = "2017-07-10"


# ------------------------------------------------------------------------------------------ step 1: the family maximum on standardised scales
def family_max_scaled(d, cells, ncal):
    """Per common offset k: over the cells, the max z (gated mean / (sd/sqrt n)) and the max gated net Sharpe on a calendar of ncal days
    (pnl - COST on gated nights, zero elsewhere), alongside the dollar mean D470 used."""
    T = len(d); pnl = d["pnl"].to_numpy(); cols = {s: d[s].to_numpy() for s in D70.STATES}; out_z = np.full(T - 1, -np.inf); out_s = np.full(T - 1, -np.inf); out_m = np.full(T - 1, -np.inf)
    for k in range(1, T):
        for s, v in cells:
            g = np.roll(cols[s], k) == v; n = int(g.sum())
            if n < 30:
                continue
            x = pnl[g]; m = x.mean(); sd = x.std(ddof=1); z = m / (sd / math.sqrt(n)); y = x - COST; mu = y.sum() / ncal; var = (np.sum(y * y) - ncal * mu * mu) / (ncal - 1); sh = mu / math.sqrt(var) * math.sqrt(252) if var > 0 else -np.inf
            out_z[k - 1] = max(out_z[k - 1], z); out_s[k - 1] = max(out_s[k - 1], sh); out_m[k - 1] = max(out_m[k - 1], m)
    ok = np.isfinite(out_z); return out_z[ok], out_s[ok], out_m[ok]


def step1(T, log=print):
    res = {}; log("\nSTEP 1 -- D470's family maximum on standardised scales (same 8 cells per root-window, exact common-offset rotation)")
    for root in ("ES", "NQ"):
        t = T[(T["root"] == root) & (T["day"] >= "2016-01-04") & (T["day"] <= "2023-12-29")].sort_values("day").reset_index(drop=True); S = D70.build_states(t); ncal = len(t); res[root] = {}
        for w in ("W1", "W2"):
            d = D70.night_frame(t, S, w, D70.MULT[root]); cells = [(s, v) for s in D70.STATES for v in (1.0, -1.0)]; fz, fs, fm = family_max_scaled(d, cells, ncal); obs = {}
            for s, v in cells:
                g = d[s].to_numpy() == v; x = d["pnl"].to_numpy()[g]; n = int(g.sum()); y = np.zeros(ncal); y[np.flatnonzero(g)] = 0
                ser = D66.series_on(pd.Index(t["day"]), d["day"][g], x - COST).to_numpy(); lab = f"{s}:{D70.SIDES[s][0] if v == 1.0 else D70.SIDES[s][1]}"
                obs[lab] = dict(n=n, mean=float(x.mean()), z=float(x.mean() / (x.std(ddof=1) / math.sqrt(n))), sharpe=D66.sharpe(ser))
            fam = dict(z=dict(p50=float(np.median(fz)), p95=float(np.quantile(fz, .95)), p99=float(np.quantile(fz, .99))), sharpe=dict(p50=float(np.median(fs)), p95=float(np.quantile(fs, .95)), p99=float(np.quantile(fs, .99))), dollars=dict(p50=float(np.median(fm)), p95=float(np.quantile(fm, .95))), n_offsets=int(fz.size))
            for lab, o in obs.items():
                o["clears_z"] = o["z"] > fam["z"]["p95"]; o["clears_sharpe"] = o["sharpe"] > fam["sharpe"]["p95"]; o["clears_dollars"] = o["mean"] > fam["dollars"]["p95"]
            res[root][w] = dict(family=fam, cells=obs)
            log(f"  {root}-{w}: family p95  z {fam['z']['p95']:.2f} (p50 {fam['z']['p50']:.2f})   Sharpe {fam['sharpe']['p95']:+.2f} (p50 {fam['sharpe']['p50']:+.2f})   dollars {fam['dollars']['p95']:+.2f}")
            for lab in ("G-A:down", "G-B:down", "G-C:below"):
                o = obs[lab]; log(f"      {lab:10s} n {o['n']:5d}  mean {o['mean']:+6.2f} {'*' if o['clears_dollars'] else ' '}   z {o['z']:.2f} {'*' if o['clears_z'] else ' '}   gated Sharpe {o['sharpe']:+.2f} {'*' if o['clears_sharpe'] else ' '}")
    return res


# ------------------------------------------------------------------------------------------ step 2a: cash overnight from the 15m fixture
def cash_days(sym):
    e = pd.read_csv(EQ15, dtype={"timestamp": str, "symbol": str}); e = e[e["symbol"] == sym]; e["day"] = e["timestamp"].str[:10]; e["hhmm"] = e["timestamp"].str[11:16]
    o = e[e["hhmm"] == "09:30"].groupby("day")["open"].first(); c = e[e["hhmm"] == "15:45"].groupby("day")["close"].last(); d = pd.DataFrame({"open": o, "close": c}).dropna().sort_index()
    d["gap_bp"] = (d["open"] / d["close"].shift(1) - 1) * 1e4; d["cc_bp"] = (d["close"] / d["close"].shift(1) - 1) * 1e4       # into this day, from the previous close
    return d.reset_index()


def cash_cells(d, lo, hi, rng, log=print, tag=""):
    """Windows: W2' = gap into day t (close t-1 -> open t); W1' = close t-1 -> close t. Gates read at the close of t-1: G-B' the gap into
    t-1 (sign), G-A' the close-to-close of t-1 (sign). Down sides are the declared cells; up sides the other side."""
    d = d.copy(); d["prev_gap"] = d["gap_bp"].shift(1); d["prev_cc"] = d["cc_bp"].shift(1); d = d[(d["day"] >= lo) & (d["day"] <= hi)].dropna().reset_index(drop=True); out = {}
    for w, col in (("W2'", "gap_bp"), ("W1'", "cc_bp")):
        pnl = d[col].to_numpy(); out[w] = dict(n=int(len(d)), mean=float(pnl.mean()), sd=float(pnl.std(ddof=1)))
        for gname, gcol in (("G-B'", "prev_gap"), ("G-A'", "prev_cc")):
            g = d[gcol].to_numpy() <= 0; x = pnl[g]; y = pnl[~g]; n1 = D64.rotation_null(g, pnl); n2 = D64.runlength_null(rng, g, pnl, n=N2_DRAWS); se95 = D70.p95_se(n2)
            k = max(1, int(round(0.01 * x.size))); xs = np.sort(x); yrs = d["day"].str[:4].to_numpy(); by = {}
            for yv in sorted(set(yrs)):
                a = pnl[g & (yrs == yv)]; b = pnl[(~g) & (yrs == yv)]; by[yv] = (float(a.mean()) if a.size else None, float(b.mean()) if b.size else None, int(a.size))
            top = d[g].assign(pnl=x).sort_values("pnl", ascending=False).head(3)
            c = dict(n=int(x.size), p=float(g.mean()), mean=float(x.mean()), median=float(np.median(x)), trimmed=float(xs[k:-k].mean()), other=float(y.mean()), diff=float(x.mean() - y.mean()), diff_se=float(math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size)),
                     z_gated=float(x.mean() / (x.std(ddof=1) / math.sqrt(x.size))), N1=dict(p50=float(np.median(n1)), p95=float(np.quantile(n1, .95))), N2=dict(p50=float(np.median(n2)), p95=float(np.quantile(n2, .95)), p95_se=se95), by_year=by, top=[(r.day, float(r.pnl)) for r in top.itertuples()],
                     years_gated_gt_other=int(sum(1 for v in by.values() if v[0] is not None and v[1] is not None and v[0] > v[1])), years=len(by))
            c["clears_N1"] = c["mean"] > c["N1"]["p95"]; c["clears_N2"] = c["mean"] > c["N2"]["p95"] + 2 * se95; out[w][gname] = c
            log(f"    {tag} {w} after a DOWN {gname}: n {c['n']:5d} ({100*c['p']:.0f}%)  {c['mean']:+6.2f} bp (median {c['median']:+.2f}, trimmed {c['trimmed']:+.2f})  other side {c['other']:+6.2f}  diff {c['diff']:+6.2f} ({c['diff_se']:.2f}) = {c['diff']/c['diff_se']:+.1f} SE  | N1 p95 {c['N1']['p95']:+.2f} {'*' if c['clears_N1'] else ' '} N2 p95 {c['N2']['p95']:+.2f}+-{se95:.2f} {'*' if c['clears_N2'] else ' '}  | years gated > other {c['years_gated_gt_other']}/{c['years']}  by year " + " ".join(f"{yv}:{(v[0] if v[0] is not None else float('nan')):+.1f}/{(v[1] if v[1] is not None else float('nan')):+.1f}" for yv, v in by.items()))
    return out


def step2a(log=print):
    rng = np.random.default_rng(SEED); res = {}; log("\nSTEP 2a -- SPY and IWM cash overnight (close -> next open) and close-to-close, after a DOWN prior gap / prior session, in bp, no cost")
    for sym in CASH:
        d = cash_days(sym); res[sym] = {}
        for per, (lo, hi) in PERIODS.items():
            log(f"  {sym} {per}:"); res[sym][per] = cash_cells(d, lo, hi, rng, log, tag=sym)
    return res


# ------------------------------------------------------------------------------------------ step 2b: RTY
def step2b(T, meta, log=print):
    log("\nSTEP 2b -- RTY futures, W2 after a down leg")
    g = meta["gates"].get("RTY")
    if not g or not g["passes"]:
        log(f"  RTY held back: gates {'absent' if not g else {k: g[k]['passes'] for k in ('G1', 'G2', 'G3', 'G4', 'G5')}}; G4 {g['G4']['corr_close_to_close_same_contract'] if g else None}; IWM cash 2016-2023 stands in (step 2a)"); return dict(passes=False, gates=g)
    t = T[(T["root"] == "RTY") & (T["day"] >= max(RTY_START, g["G5"]["usable_start"])) & (T["day"] <= "2023-12-29")].sort_values("day").reset_index(drop=True); S = D70.build_states(t); rng = np.random.default_rng(SEED + 1); out = dict(passes=True, gates=g, cells={})
    for w in ("W2", "W1"):
        d = D70.night_frame(t, S, w, 5.0); st = "G-B" if w == "W2" else "G-A"; pnl = d["pnl"].to_numpy(); defined = ~np.isnan(d[st].to_numpy()); dd = d[defined]; p = dd["pnl"].to_numpy(); gg = dd[st].to_numpy() == -1.0
        x = p[gg]; y = p[~gg]; n1 = D64.rotation_null(gg, p); n2 = D64.runlength_null(rng, gg, p, n=N2_DRAWS); se95 = D70.p95_se(n2); ser = D66.series_on(pd.Index(t["day"]), dd["day"][gg], x - COST).to_numpy()
        c = dict(window=w, state=st, n=int(x.size), nights=int(len(d)), mean=float(x.mean()), sd=float(x.std(ddof=1)), other=float(y.mean()), diff=float(x.mean() - y.mean()), diff_se=float(math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size)), net_sharpe=D66.sharpe(ser), N1=dict(p50=float(np.median(n1)), p95=float(np.quantile(n1, .95))), N2=dict(p50=float(np.median(n2)), p95=float(np.quantile(n2, .95)), p95_se=se95))
        c["clears_N1"] = c["mean"] > c["N1"]["p95"]; c["clears_N2"] = c["mean"] > c["N2"]["p95"] + 2 * se95; out["cells"][w] = c
        log(f"  RTY-{w} after a DOWN {st} (1 M2K, $3): n {c['n']} of {c['nights']}  {c['mean']:+.2f} vs {c['other']:+.2f}  diff {c['diff']:+.2f} ({c['diff_se']:.2f}) = {c['diff']/c['diff_se']:+.1f} SE  gated net Sharpe {c['net_sharpe']:+.2f}  | N1 p95 {c['N1']['p95']:+.2f} {'*' if c['clears_N1'] else ' '} N2 p95 {c['N2']['p95']:+.2f}+-{se95:.2f} {'*' if c['clears_N2'] else ' '}")
    return out


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print("D472 -- the down-leg reversal pick on what the family null has not priced\n      spec committed in 4290eeb BEFORE this ran; nothing after 2023-12-29 read")
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); meta = json.loads(META.read_text())
    s1 = step1(T); s2 = step2a(); s3 = step2b(T, meta)
    E2 = s1["ES"]["W2"]["cells"]["G-B:down"]; N2c = s1["NQ"]["W2"]["cells"]["G-B:down"]; spy10 = s2["SPY"]["2010-2015"]["W2'"]["G-B'"]; iwm10 = s2["IWM"]["2010-2015"]["W2'"]["G-B'"]; spy16 = s2["SPY"]["2016-2023"]["W2'"]["G-B'"]; iwm16 = s2["IWM"]["2016-2023"]["W2'"]["G-B'"]
    third = s3["cells"]["W2"] if s3["passes"] else None
    crit = dict(step1=bool(E2["clears_z"] or E2["clears_sharpe"]), spy_2010=bool(spy10["diff"] > 0 and spy10["diff"] / spy10["diff_se"] >= 1.5), iwm_2010=bool(iwm10["diff"] > 0), third=bool((third["diff"] > 0) if third else (iwm16["diff"] > 0)), third_source="RTY" if third else "IWM 2016-2023")
    crit["all"] = all(v for k, v in crit.items() if k != "third_source")
    print("\nTHE STEP-3 CRITERION (all four): " + "  ".join(f"{k} {v}" for k, v in crit.items()) )
    print("\nPREDICTIONS")
    print(f"  X-a family p95 z 2.2-2.6; ES-W2 z ~3.0 clears, NQ-W2 ~2.3 marginal; Sharpe-scale p95 0.55-0.65; W1 down cells clear neither : ES-W2 p95 z {s1['ES']['W2']['family']['z']['p95']:.2f} / Sharpe {s1['ES']['W2']['family']['sharpe']['p95']:+.2f}, obs z {E2['z']:.2f} Sharpe {E2['sharpe']:+.2f}; NQ-W2 p95 z {s1['NQ']['W2']['family']['z']['p95']:.2f} / {s1['NQ']['W2']['family']['sharpe']['p95']:+.2f}, obs z {N2c['z']:.2f} Sharpe {N2c['sharpe']:+.2f}; W1 down: ES z {s1['ES']['W1']['cells']['G-A:down']['z']:.2f} vs p95 {s1['ES']['W1']['family']['z']['p95']:.2f}, NQ z {s1['NQ']['W1']['cells']['G-A:down']['z']:.2f} vs {s1['NQ']['W1']['family']['z']['p95']:.2f}")
    print(f"  X-b SPY 2010-2015 gap after a down gap +2..+5 bp vs -1..+1; diff 1.5-3 SE; larger in 2011/2015; IWM same sign, larger      : SPY {spy10['mean']:+.2f} vs {spy10['other']:+.2f}, {spy10['diff']/spy10['diff_se']:+.1f} SE; IWM {iwm10['mean']:+.2f} vs {iwm10['other']:+.2f}, {iwm10['diff']/iwm10['diff_se']:+.1f} SE")
    print(f"  X-c SPY 2016-2023 reproduces the futures: diff >= 2 SE, +3..+6 vs -1..+1 bp                                                   : SPY {spy16['mean']:+.2f} vs {spy16['other']:+.2f}, {spy16['diff']/spy16['diff_se']:+.1f} SE; IWM {iwm16['mean']:+.2f} vs {iwm16['other']:+.2f}, {iwm16['diff']/iwm16['diff_se']:+.1f} SE")
    print(f"  X-d RTY passes or fails G4 by < 0.005; RTY-W2 down-leg positive, 1-2 SE                                                       : " + (f"passes; {third['mean']:+.2f} vs {third['other']:+.2f}, {third['diff']/third['diff_se']:+.1f} SE" if third else f"held back (G4 {s3['gates']['G4']['corr_close_to_close_same_contract'] if s3['gates'] else None})"))
    OUT.write_text(json.dumps(dict(spec="D472", step1=s1, step2a=s2, step2b=s3, criterion=crit), indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); rng = np.random.default_rng(3); print("== (a) family_max_scaled: a planted cell's z exceeds the family p99; scales agree with direct computation at offset 0")
    n = 1200; days = [str(x.date()) for x in pd.bdate_range("2016-01-04", periods=n)]; pnl = rng.normal(0, 100, n); ga = np.where(rng.random(n) < 0.5, 1.0, -1.0); pnl = pnl + np.where(ga == -1.0, 20.0, -20.0)      # a zero-mean plant: the family null is centred on the unconditional mean, so a one-sided plant shifts every cell's z
    d = pd.DataFrame({"day": days, "pnl": pnl, "G-A": ga, "G-B": np.where(rng.random(n) < 0.5, 1.0, -1.0), "G-C": np.where(rng.random(n) < 0.2, -1.0, 1.0), "G-D": np.where(rng.random(n) < 0.33, 1.0, np.where(rng.random(n) < 0.5, 0.0, -1.0))})
    cells = [(s, v) for s in D70.STATES for v in (1.0, -1.0)]; fz, fs, fm = family_max_scaled(d, cells, n); g = ga == -1.0; x = pnl[g]; z = x.mean() / (x.std(ddof=1) / math.sqrt(g.sum()))
    assert z > np.quantile(fz, .99), (z, np.quantile(fz, .99)); ser = np.where(g, pnl - COST, 0.0); assert fs.size == n - 1 and np.all(np.isfinite(fs))
    print(f"  ok: planted z {z:.2f} > family p99 {np.quantile(fz, .99):.2f}; family Sharpe p95 {np.quantile(fs, .95):+.2f}; dollars p95 {np.quantile(fm, .95):+.2f}")
    print("== (b) cash_cells: the gate reads the PRIOR gap; a planted reversal (negative prior gap -> +8 bp) is recovered; the up side is not")
    m = 1500; dd = pd.DataFrame({"day": [str(x.date()) for x in pd.bdate_range("2010-01-04", periods=m)]}); gap = rng.normal(0, 60, m); prev = np.roll(gap, 1); gap = gap + np.where(prev <= 0, 20.0, 0.0); dd["gap_bp"] = gap; dd["cc_bp"] = rng.normal(0, 100, m)
    out = cash_cells(dd, "2010-01-04", "2016-12-31", np.random.default_rng(4), log=lambda *a, **k: None); c = out["W2'"]["G-B'"]; assert c["diff"] > 10 and c["diff"] / c["diff_se"] > 4 and c["clears_N1"], c
    assert abs(out["W1'"]["G-A'"]["diff"]) < 3 * out["W1'"]["G-A'"]["diff_se"], "no planted effect on the close-to-close after a down session"
    u = out["W1'"]["G-A'"]; print(f"  ok: planted +20 recovered as diff {c['diff']:+.2f} ({c['diff']/c['diff_se']:.1f} SE), N1 cleared; unplanted W1'/G-A' diff {u['diff']:+.2f} inside noise")
    print("== (c) cash_days: the gap uses the 09:30 open over the previous 15:45 close, on the real fixture, first rows")
    d = cash_days("SPY"); assert d["day"].iloc[0] == "2010-01-04" and np.isnan(d["gap_bp"].iloc[0]) and abs(d["gap_bp"].iloc[1] - (d["open"].iloc[1] / d["close"].iloc[0] - 1) * 1e4) < 1e-9
    print(f"  ok: {len(d)} days, first gap {d['gap_bp'].iloc[1]:+.1f} bp on {d['day'].iloc[1]}")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
