"""D473 -- COMPONENT candidate K7: long the overnight leg (18:00 -> 09:00 print; secondary exit the 09:30 open) on nights that follow a
negative overnight leg. NQ one MNQ $3 (the candidate, chosen on cost share); ES one MES the check root. Spec committed in fb69179 BEFORE
this file.

    uv run python -u scripts/run_d473_downleg_component.py --insample                       # 2016-01-04 .. 2023-12-29, never touches 2024+
    uv run python -u scripts/run_d473_downleg_component.py --forward --principals-word      # READS the reserved 2024+ slices; refuses without the flag
    uv run python -u scripts/run_d473_downleg_component.py --selftest
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
D66 = _load("d466c", "run_d466_components.py"); D64 = _load("d464g", "run_d464_arms_as_gates.py"); D70 = _load("d470s", "run_d470_gate_stage0.py"); D72 = _load("d472r", "run_d472_reversal_checks.py")
TABLE = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"; SESS = REPO / "data" / "fixtures" / "fut_index_sessions.csv.gz"
OUT_IN = REPO / "data" / "d473_downleg_insample.json"; OUT_FWD = REPO / "data" / "d473_downleg_forward.json"
IN_LO, IN_HI = "2016-01-04", "2023-12-29"; FWD_LO, FWD_HI = "2024-01-02", "2026-09-09"; CASH_FWD_LO, CASH_FWD_HI = "2024-01-02", "2026-08-26"
MULT = {"NQ": 2.0, "ES": 5.0}; COST = 3.0; ACCOUNT = 50_000.0; N2_DRAWS = 2000; SEED = 473; BINS = [(-25, 0), (-50, -25), (-100, -50), (-1e9, -100)]


# ------------------------------------------------------------------------------------------ the construction
def k7_frame(T, S, root, lo, hi, mult):
    """One row per session in [lo, hi] (the root's calendar); traded = same-front night with both prints and a DEFINED prior leg <= 0.
    prior_bp = the previous session row's overnight leg in bp (NaN when undefined). Returns (cal, frame of traded-eligible nights)."""
    t = T[(T["root"] == root) & (T["day"] >= lo) & (T["day"] <= hi)].sort_values("day").reset_index(drop=True); cal = pd.Index(t["day"])
    leg = (t["h08_c"] / t["h18_o"] - 1).where(t["same_front"]); prior = leg.shift(1) * 1e4; vol = D70.build_states(t)["G-D"].shift(1)
    s = S[(S["root"] == root)].set_index("day")["p0930"]; p0930 = t["day"].map(s)
    ok = t["same_front"] & t["h18_o"].notna() & t["h08_c"].notna() & (t["h18_o"] > 0) & prior.notna()
    d = pd.DataFrame({"day": t["day"], "entry": t["h18_o"], "exit": t["h08_c"], "exit0930": p0930, "prior_bp": prior, "vol_state": vol, "gate": prior <= 0})[ok].reset_index(drop=True)
    d["pnl"] = (d["exit"] - d["entry"]) * mult; d["pnl0930"] = (d["exit0930"] - d["entry"]) * mult; d["pnl_bp"] = (d["exit"] / d["entry"] - 1) * 1e4
    return cal, d


def component_line(cal, d, pnl_col, rng, cost=COST):
    g = d["gate"].to_numpy(); pnl = d[pnl_col].to_numpy(); okp = np.isfinite(pnl); g = g & okp; other = (~d["gate"].to_numpy()) & okp; x = pnl[g]; y = pnl[other]
    ser = D66.series_on(cal, d["day"][g], x - cost).to_numpy(); gser = D66.series_on(cal, d["day"][g], x).to_numpy(); yrs = np.array([s[:4] for s in cal])
    n1 = D64.rotation_null(g[okp], pnl[okp]); n2 = D64.runlength_null(rng, g[okp], pnl[okp], n=N2_DRAWS); se95 = D70.p95_se(n2)
    c = dict(nights=int(g.sum()), eligible=int(okp.sum()), p=float(g.sum() / okp.sum()), gross_mean=float(x.mean()), sd=float(x.std(ddof=1)), hit=float((x > 0).mean()), skew=float(pd.Series(x).skew()), worst=float(x.min()), best=float(x.max()),
             other_mean=float(y.mean()), diff=float(x.mean() - y.mean()), diff_se=float(math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size)), net_sharpe=D66.sharpe(ser), net_sharpe_se=D66.sharpe_boot(ser, cal), gross_sharpe=D66.sharpe(gser), ann_net=float(ser.mean() * 252),
             cost_share=float(cost / x.mean()) if x.mean() != 0 else float("inf"), by_year={yv: D66.sharpe(ser[yrs == yv]) for yv in sorted(set(yrs))}, N1=dict(p50=float(np.median(n1)), p95=float(np.quantile(n1, .95))), N2=dict(p50=float(np.median(n2)), p95=float(np.quantile(n2, .95)), p95_se=se95),
             q01=float(np.quantile(x, .01)), q001=float(np.quantile(x, .001)), n_below_2pct=int((x - cost < -0.02 * ACCOUNT).sum()), worst_ten=[(dd, float(v)) for dd, v in sorted(zip(d["day"][g], x), key=lambda t: t[1])[:10]], series=ser)
    c["diff_z"] = c["diff"] / c["diff_se"]; c["C_a"] = c["net_sharpe"] > 0.5; c["C_c"] = c["skew"] >= -0.5; c["C_d"] = c["sd"] <= 0.01 * ACCOUNT; c["clears_N1"] = c["gross_mean"] > c["N1"]["p95"]; c["clears_N2"] = c["gross_mean"] > c["N2"]["p95"] + 2 * se95
    return c


def dose_response(d, pnl_col):
    out = []
    for lo, hi in BINS:
        m = d["gate"].to_numpy() & (d["prior_bp"].to_numpy() > lo) & (d["prior_bp"].to_numpy() <= hi) & np.isfinite(d[pnl_col].to_numpy()); x = d[pnl_col].to_numpy()[m]
        out.append(dict(bin=f"({lo:.0f}, {hi:.0f}]" if lo > -1e8 else f"<= {hi:.0f}", n=int(m.sum()), mean=float(x.mean()) if x.size else None, se=float(x.std(ddof=1) / math.sqrt(x.size)) if x.size > 1 else None))
    means = [b["mean"] for b in out if b["mean"] is not None]; return out, bool(all(means[i] <= means[i + 1] for i in range(len(means) - 1)))


def regime(d, pnl_col):
    g = d["gate"].to_numpy(); pnl = d[pnl_col].to_numpy(); yrs = d["day"].str[:4].to_numpy(); out = {}
    for yv in sorted(set(yrs)):
        a = pnl[g & (yrs == yv)]; b = pnl[(~g) & (yrs == yv)]; out[yv] = (float(a.mean()) if a.size else None, float(b.mean()) if b.size else None, int(a.size))
    vs = d["vol_state"].to_numpy(); byvol = {}
    for lab, v in (("high", 1.0), ("mid", 0.0), ("low", -1.0)):
        a = pnl[g & (vs == v)]; b = pnl[(~g) & (vs == v)]; byvol[lab] = (float(a.mean()) if a.size else None, float(b.mean()) if b.size else None, int(a.size))
    return out, byvol


def fmt_line(lab, c):
    return (f"  {lab:26s} nights {c['nights']:4d}/{c['eligible']} ({100*c['p']:.0f}%)  gross ${c['gross_mean']:+.2f} sd {c['sd']:.0f}  other ${c['other_mean']:+.2f}  diff {c['diff']:+.2f} ({c['diff_se']:.2f}) = {c['diff_z']:+.1f} SE  hit {100*c['hit']:.1f}%  skew {c['skew']:+.2f}  worst ${c['worst']:,.0f}  "
            f"net Sharpe {c['net_sharpe']:+.2f} +- {c['net_sharpe_se']:.2f} (gross {c['gross_sharpe']:+.2f})  ann ${c['ann_net']:+,.0f}  cost/mean {100*c['cost_share']:.0f}%  | N1 p95 {c['N1']['p95']:+.2f} {'*' if c['clears_N1'] else ' '} N2 p95 {c['N2']['p95']:+.2f}+-{c['N2']['p95_se']:.2f} {'*' if c['clears_N2'] else ' '}  | C-a {c['C_a']} C-c {c['C_c']} C-d {c['C_d']}")


def strip(c):
    return {k: v for k, v in c.items() if k != "series"}


# ------------------------------------------------------------------------------------------ in-sample
def insample():
    t0 = time.time(); print("D473 K7 -- IN-SAMPLE component line, 2016-01-04 .. 2023-12-29 (2024+ untouched)\n      spec committed in fb69179 BEFORE this ran")
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); S = pd.read_csv(SESS, dtype={"root": str, "day": str, "contract": str}); rng = np.random.default_rng(SEED); res = {}
    for root in ("NQ", "ES"):
        cal, d = k7_frame(T, S, root, IN_LO, IN_HI, MULT[root]); c09 = component_line(cal, d, "pnl", rng); c0930 = component_line(cal, d, "pnl0930", rng)
        dose, mono = dose_response(d, "pnl"); byyr, byvol = regime(d, "pnl")
        print(f"\n{root} ({'the candidate' if root == 'NQ' else 'the check root'}), one micro, $3:"); print(fmt_line("K7 exit 09:00 (primary)", c09)); print(fmt_line("K7 exit 09:30 (secondary)", c0930))
        print("  dose-response (exit 09:00), prior leg in bp: " + "  ".join(f"{b['bin']}: n {b['n']} ${b['mean']:+.2f} ({b['se']:.2f})" for b in dose if b['mean'] is not None) + f"   monotone {mono}")
        print("  by year gated / other (n): " + " ".join(f"{y}:{a:+.1f}/{b:+.1f}({n})" for y, (a, b, n) in byyr.items()))
        print("  by trailing-vol tercile gated / other (n): " + " ".join(f"{k}:{(a if a is not None else float('nan')):+.1f}/{(b if b is not None else float('nan')):+.1f}({n})" for k, (a, b, n) in byvol.items()))
        print(f"  tail: worst ${c09['worst']:,.0f}, q1% ${c09['q01']:,.0f}, q0.1% ${c09['q001']:,.0f}, nights below -2% of $50k at one micro: {c09['n_below_2pct']}; worst ten: " + "; ".join(f"{dd} {v:+.0f}" for dd, v in c09["worst_ten"]))
        res[root] = dict(cal=list(cal), K7_0900=strip(c09), K7_0930=strip(c0930), dose=dose, dose_monotone=mono, by_year=byyr, by_vol=byvol, _ser=c09["series"], _d=d)
    # correlations with K1 (ES full session) and the ungated NQ overnight leg, on the NQ calendar
    calN = pd.Index(res["NQ"]["cal"]); dN = res["NQ"]["_d"]; k7 = pd.Series(res["NQ"]["_ser"], index=calN)
    tE = T[(T["root"] == "ES") & (T["day"] >= IN_LO) & (T["day"] <= IN_HI)]; tE = tE[tE["same_front"] & tE["h18_o"].notna() & tE["h15_c"].notna()]; k1 = D66.series_on(calN, tE["day"], (tE["h15_c"] - tE["h18_o"]) * 5.0 - COST)
    ung = D66.series_on(calN, dN["day"], dN["pnl"] - COST); rho_k1 = float(k7.corr(k1)); rho_ung = float(k7.corr(ung)); rho_es = float(k7.corr(pd.Series(res["ES"]["_ser"], index=pd.Index(res["ES"]["cal"])).reindex(calN).fillna(0)))
    print(f"\ncorrelations on the NQ calendar: rho(K7, K1 ES full session) {rho_k1:+.2f}; rho(K7, ungated NQ overnight leg) {rho_ung:+.2f}; rho(K7 NQ, K7 ES) {rho_es:+.2f}")
    N, E = res["NQ"], res["ES"]; c = N["K7_0900"]; s = N["K7_0930"]
    print("\nPREDICTIONS (in-sample)")
    print(f"  X-a NQ K7 net Sharpe +0.62 (SE ~0.25), gross +$13.3, sd ~172, 887 nights; ES +0.70; 09:30 exit mean +10-40% higher, sd +10-20%, Sharpe within +-0.1 : NQ {c['net_sharpe']:+.2f} ({c['net_sharpe_se']:.2f}), ${c['gross_mean']:+.2f}, sd {c['sd']:.0f}, {c['nights']} nights; ES {E['K7_0900']['net_sharpe']:+.2f}; 09:30: mean {100*(s['gross_mean']/c['gross_mean']-1):+.0f}%, sd {100*(s['sd']/c['sd']-1):+.0f}%, Sharpe {s['net_sharpe']-c['net_sharpe']:+.2f}")
    d1 = [b for b in N["dose"] if b["mean"] is not None]; print(f"  X-b dose-response monotone; the <= -100 bin >= 2x the (-25, 0] bin on < 15% of gated nights                                          : monotone {N['dose_monotone']}; bins " + ", ".join(f"{b['bin']} ${b['mean']:+.1f} (n {b['n']})" for b in d1) + (f"; ratio {d1[-1]['mean']/d1[0]['mean']:.1f}x on {100*d1[-1]['n']/c['nights']:.0f}%" if d1[0]['mean'] else ""))
    print(f"  X-c worst night -$800..-$1,300; nights below -2%: 0; q1% -$350..-$500                                                                    : worst ${c['worst']:,.0f}; below -2%: {c['n_below_2pct']}; q1% ${c['q01']:,.0f}")
    print(f"  X-d rho(K7, K1) 0.35-0.55; rho(K7, ungated leg) 0.6-0.75                                                                                 : {rho_k1:+.2f}; {rho_ung:+.2f}")
    OUT_IN.write_text(json.dumps(dict(spec="D473", window=[IN_LO, IN_HI], NQ={k: v for k, v in N.items() if not k.startswith("_") and k != "cal"}, ES={k: v for k, v in E.items() if not k.startswith("_") and k != "cal"}, rho_K1=rho_k1, rho_ungated=rho_ung, rho_ES=rho_es), indent=1, default=float)); print(f"\nwrote {OUT_IN.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ forward (guarded)
def promotion(fut, spy, pooled_z):
    if fut["diff"] < 0 or pooled_z < 0.5 or fut["net_sharpe"] < -0.3:
        return "REMOVED"
    if fut["diff"] > 0 and spy["diff"] > 0 and pooled_z >= 1.5 and fut["net_sharpe"] > 0:
        return "FULL" if (fut["diff_z"] >= 2 or pooled_z >= 2.5) else "PROVISIONAL"
    return "PICK"


def pooled(d1, se1, d2, se2):
    w1, w2 = 1 / se1 ** 2, 1 / se2 ** 2; m = (w1 * d1 + w2 * d2) / (w1 + w2); se = 1 / math.sqrt(w1 + w2); return m, se, m / se


def forward(word):
    if not word:
        print("REFUSED: --forward reads the reserved 2024+ slices (futures 2024-01-02..2026-09-09; cash 2024-01-02..2026-08-26). Re-run with --principals-word only on the principal's word."); return 2
    t0 = time.time(); print(f"D473 K7 -- FORWARD READ on the principal's word: futures {FWD_LO}..{FWD_HI}, cash {CASH_FWD_LO}..{CASH_FWD_HI}\n      rule: PROVISIONAL if diff > 0 on NQ and SPY, pooled z >= 1.5, NQ net Sharpe > 0; FULL if also futures z >= 2 or pooled z >= 2.5; REMOVED if futures diff < 0, pooled z < 0.5 or Sharpe < -0.3")
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); S = pd.read_csv(SESS, dtype={"root": str, "day": str, "contract": str}); rng = np.random.default_rng(SEED + 1); res = {}
    for root in ("NQ", "ES"):
        cal, d = k7_frame(T, S, root, FWD_LO, FWD_HI, MULT[root]); c09 = component_line(cal, d, "pnl", rng); c0930 = component_line(cal, d, "pnl0930", rng); dose, mono = dose_response(d, "pnl"); byyr, _ = regime(d, "pnl")
        g = d["gate"].to_numpy(); xb = d["pnl_bp"].to_numpy()[g]; yb = d["pnl_bp"].to_numpy()[~g]; bp = dict(diff=float(xb.mean() - yb.mean()), se=float(math.sqrt(xb.var(ddof=1) / xb.size + yb.var(ddof=1) / yb.size)), gated=float(xb.mean()), other=float(yb.mean()))
        print(f"\n{root}:"); print(fmt_line("K7 exit 09:00 (primary)", c09)); print(fmt_line("K7 exit 09:30 (secondary)", c0930))
        print("  dose-response: " + "  ".join(f"{b['bin']}: n {b['n']} ${b['mean']:+.2f} ({b['se']:.2f})" for b in dose if b['mean'] is not None) + f"   monotone {mono}"); print("  by year gated / other (n): " + " ".join(f"{y}:{a:+.1f}/{b:+.1f}({n})" for y, (a, b, n) in byyr.items()))
        print(f"  in bp: gated {bp['gated']:+.2f} other {bp['other']:+.2f} diff {bp['diff']:+.2f} ({bp['se']:.2f})"); res[root] = dict(K7_0900=strip(c09), K7_0930=strip(c0930), dose=dose, dose_monotone=mono, by_year=byyr, bp=bp)
    cash = {}
    for sym in ("SPY", "IWM"):
        dd = D72.cash_days(sym); cash[sym] = D72.cash_cells(dd, CASH_FWD_LO, CASH_FWD_HI, rng, log=print, tag=sym)["W2'"]["G-B'"]
    fut = res["NQ"]["K7_0900"]; spy = cash["SPY"]; m, se, z = pooled(res["NQ"]["bp"]["diff"], res["NQ"]["bp"]["se"], spy["diff"], spy["diff_se"]); verdict = promotion(fut, spy, z)
    print(f"\nPOOLED (NQ futures in bp + SPY cash gap in bp, inverse-variance): diff {m:+.2f} bp (SE {se:.2f}) z {z:+.2f}; futures-only z {fut['diff_z']:+.2f}; NQ forward net Sharpe {fut['net_sharpe']:+.2f}\nVERDICT under the declared rule: {verdict}")
    print("\nPREDICTIONS (forward, X-e)\n" + f"  NQ gated +$6..+$16 vs other -$6..+$6; futures z 0.8-2.0; SPY gap +3..+8 bp; pooled z 1.3-2.5; dose monotone in >= 3 of 4; worst -$400..-$900; PROVISIONAL more likely than not : NQ ${fut['gross_mean']:+.2f} vs ${fut['other_mean']:+.2f}, z {fut['diff_z']:+.2f}; SPY {spy['mean']:+.2f} vs {spy['other']:+.2f}; pooled z {z:+.2f}; monotone {res['NQ']['dose_monotone']}; worst ${fut['worst']:,.0f}; {verdict}")
    OUT_FWD.write_text(json.dumps(dict(spec="D473", futures=res, cash=cash, pooled=dict(diff_bp=m, se=se, z=z), verdict=verdict), indent=1, default=float)); print(f"\nwrote {OUT_FWD.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min"); return 0


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) k7_frame: the gate is the PREVIOUS session's leg <= 0; undefined prior (roll night before) is not traded; the 09:30 exit merges by day")
    n = 12; days = [str(x.date()) for x in pd.bdate_range("2020-01-06", periods=n)]; o = np.full(n, 100.0); c8 = np.array([101, 99, 100, 98, 102, 100, 97, 100, 100, 99, 101, 100.0])
    T = pd.DataFrame({"root": "NQ", "day": days, "prev_day": days, "contract": "NQH0", "front_prev": "NQH0", "same_front": True, "h18_o": o, "h08_c": c8, "h15_c": c8 + 1, "bars": 1000}); T.loc[5, "same_front"] = False
    for s in [f"h{h:02d}" for h in [18, 19, 20, 21, 22, 23] + list(range(0, 17))]:
        for f in ("o", "h", "l", "c"):
            if f"{s}_{f}" not in T.columns:
                T[f"{s}_{f}"] = np.nan
        T[f"{s}_v"] = 0; T[f"{s}_n"] = 0
    S = pd.DataFrame({"root": "NQ", "day": days, "p0930": o + 1.5}); cal, d = k7_frame(T, S, "NQ", days[0], days[-1], 2.0); dd = d.set_index("day")
    assert days[0] not in dd.index and dd.loc[days[1], "gate"] == False and dd.loc[days[2], "gate"] == True and dd.loc[days[4], "gate"] == True, "leg into day1 was +1% -> day2 night not gated; leg into day2 -1% -> day3 night gated"
    assert days[5] not in dd.index and days[6] not in dd.index, "the roll night is not traded and the night after it has no defined prior"
    assert abs(dd.loc[days[2], "pnl"] - 0.0) < 1e-9 and abs(dd.loc[days[2], "pnl0930"] - 3.0) < 1e-9 and abs(dd.loc[days[3], "pnl"] - (-4.0)) < 1e-9
    print("  ok: lag, the <= 0 rule (a flat leg gates), the roll gap, and the 09:30 merge ($3 on a 1.5-point move at $2/pt)")
    print("== (b) the promotion rule's four branches")
    f = lambda diff, z, sh: dict(diff=diff, diff_z=z, net_sharpe=sh); s = lambda diff: dict(diff=diff)
    assert promotion(f(5, 1.0, 0.3), s(2), 1.6) == "PROVISIONAL" and promotion(f(5, 2.2, 0.3), s(2), 1.6) == "FULL" and promotion(f(5, 1.0, 0.3), s(2), 2.6) == "FULL" and promotion(f(-1, -0.2, 0.1), s(2), 1.0) == "REMOVED" and promotion(f(5, 1.0, 0.3), s(-1), 1.6) == "PICK" and promotion(f(5, 1.0, -0.5), s(2), 1.6) == "REMOVED" and promotion(f(2, 0.3, 0.1), s(1), 0.4) == "REMOVED"
    m, se, z = pooled(10, 5, 6, 3); assert abs(m - (10 / 25 + 6 / 9) / (1 / 25 + 1 / 9)) < 1e-9 and abs(z - m / se) < 1e-12
    print(f"  ok: PROVISIONAL / FULL (two routes) / REMOVED (three routes) / PICK; pooled {m:.2f} +- {se:.2f}")
    print("== (c) --forward refuses without the principal's word")
    assert forward(False) == 2; print("  ok: refused, nothing read")
    print("== (d) component_line on a synthetic frame: sign in money (a favourable move pays), C-d, the nulls run")
    rng = np.random.default_rng(1); m = 600; days = pd.Index([str(x.date()) for x in pd.bdate_range("2016-01-04", periods=m)]); pr = rng.normal(0, 40, m); pnl = rng.normal(0, 100, m) + np.where(pr <= 0, 25.0, -5.0)
    d = pd.DataFrame({"day": days, "entry": 100.0, "exit": 100 + pnl / 2, "exit0930": 100 + pnl / 2, "prior_bp": pr, "vol_state": 0.0, "gate": pr <= 0, "pnl": pnl, "pnl0930": pnl, "pnl_bp": pnl}); c = component_line(days, d, "pnl", np.random.default_rng(2))
    assert c["diff"] > 15 and c["diff_z"] > 3 and c["clears_N1"] and c["C_d"] and c["gross_mean"] > 0 and abs(c["gross_mean"] - d["pnl"][d["gate"]].mean()) < 1e-9
    print(f"  ok: diff {c['diff']:+.1f} ({c['diff_z']:.1f} SE), N1 cleared, net Sharpe {c['net_sharpe']:+.2f}")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--insample", action="store_true"); g.add_argument("--forward", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--principals-word", action="store_true"); a = ap.parse_args()
    if a.insample:
        insample()
    elif a.forward:
        sys.exit(forward(a.principals_word))
    else:
        cmd_selftest()
