"""D470 stage 0 -- can a state known at the entry concentrate the overnight index drift enough to pay the micro cost? Four declared two-sided
gates (continuation, prior overnight leg, 200-session average, trailing-tercile realised vol) on ES-W1 and NQ-W1 (W2 secondary) from D467's
session tables; per cell the gated component's net Sharpe on all calendar days; D464's exact rotation (N1) and run-length-matched (N2) gate
nulls; a common-offset family-maximum null over the 16 primary cells. Spec committed in b3671b2 BEFORE this file. 2016-2023; 2024+ unread.

    uv run python -u scripts/run_d470_gate_stage0.py --run
    uv run python -u scripts/run_d470_gate_stage0.py --selftest

The state is read at the last 16:00 print before the 18:00 entry: the previous SESSION row (Friday's print for a Sunday-evening entry).
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
D66 = _load("d466c", "run_d466_components.py"); D64 = _load("d464g", "run_d464_arms_as_gates.py")
TABLE = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"; OUT = REPO / "data" / "d470_gate_stage0.json"
START, END = "2016-01-04", "2023-12-29"; ROOTS = ("ES", "NQ"); MULT = {"ES": 5.0, "NQ": 2.0}; COST = 3.0
WINDOWS = {"W1": ("h18_o", "h15_c"), "W2": ("h18_o", "h08_c")}; STATES = ("G-A", "G-B", "G-C", "G-D"); SIDES = {"G-A": ("up", "down"), "G-B": ("up", "down"), "G-C": ("above", "below"), "G-D": ("high", "low")}
SMA_N, SMA_MIN, VOL_N, VOL_MIN, TERC_N, TERC_MIN = 200, 180, 21, 15, 252, 200; N2_DRAWS = 2000; SEED = 470


# ------------------------------------------------------------------------------------------ states
def build_states(t):
    """t: one root's session rows (all rows, sorted by day). Returns a DataFrame on the same index with the state at each row's own 16:00
    print (to be applied to the NEXT row's night) as +1 / -1 / NaN per state."""
    c16 = t["h15_c"]; same = t["contract"].eq(t["contract"].shift(1)); r_s = (c16 / c16.shift(1) - 1).where(same); on = (t["h08_c"] / t["h18_o"] - 1).where(t["same_front"])
    sma = c16.rolling(SMA_N, min_periods=SMA_MIN).mean(); lr = np.log(c16).diff().where(same); vol = lr.rolling(VOL_N, min_periods=VOL_MIN).std()
    q33 = vol.shift(1).rolling(TERC_N, min_periods=TERC_MIN).quantile(1 / 3); q67 = vol.shift(1).rolling(TERC_N, min_periods=TERC_MIN).quantile(2 / 3)
    S = pd.DataFrame(index=t.index)
    S["G-A"] = np.where(r_s.isna(), np.nan, np.where(r_s > 0, 1.0, -1.0)); S["G-B"] = np.where(on.isna(), np.nan, np.where(on > 0, 1.0, -1.0))
    S["G-C"] = np.where(sma.isna() | c16.isna(), np.nan, np.where(c16 > sma, 1.0, -1.0))
    S["G-D"] = np.where(vol.isna() | q33.isna(), np.nan, np.where(vol >= q67, 1.0, np.where(vol <= q33, -1.0, 0.0)))     # 0 = middle tercile, neither side
    return S


def night_frame(t, S, w, mult):
    """Traded nights of window w with the state read at the previous session row; pnl in $ per micro, gross."""
    e, x = WINDOWS[w]; ok = t["same_front"] & t[e].notna() & t[x].notna() & (t[e] > 0)
    d = pd.DataFrame({"day": t["day"], "pnl": (t[x] - t[e]) * mult}); prev = S.shift(1)
    for s in STATES:
        d[s] = prev[s].to_numpy()
    return d[ok].reset_index(drop=True)


# ------------------------------------------------------------------------------------------ nulls
def p95_se(x, n_boot=500, seed=5):
    rng = np.random.default_rng(seed); return float(np.std([np.quantile(rng.choice(x, x.size), .95) for _ in range(n_boot)], ddof=1))


def family_max_rotation(d, cells):
    """Common offset k applied to every state column (3-valued, NaN = undefined) at once; per offset the max over cells of the gated mean."""
    T = len(d); pnl = d["pnl"].to_numpy(); cols = {s: d[s].to_numpy() for s in STATES}; out = np.empty(T - 1)
    for k in range(1, T):
        best = -np.inf
        for s, side_val in cells:
            g = np.roll(cols[s], k) == side_val
            if g.any():
                best = max(best, float(pnl[g].mean()))
        out[k - 1] = best
    return out[np.isfinite(out)]


# ------------------------------------------------------------------------------------------ scoring
def score_root(root, t, cal, log=print):
    S = build_states(t); res = {}; rng = np.random.default_rng(SEED)
    for w in WINDOWS:
        d = night_frame(t, S, w, MULT[root]); pnl = d["pnl"].to_numpy(); base = dict(nights=int(len(d)), gross_mean=float(pnl.mean()), sd=float(pnl.std(ddof=1)), ratio=float(pnl.mean() / pnl.std(ddof=1)))
        series = D66.series_on(cal, d["day"], pnl - COST); base["net_sharpe"] = D66.sharpe(series.to_numpy()); base["net_sharpe_se"] = D66.sharpe_boot(series.to_numpy(), cal); cells = {}
        log(f"\n  {root}-{w}: {base['nights']:,} nights, gross ${base['gross_mean']:+.2f} / sd {base['sd']:.0f} (ratio {100*base['ratio']:.2f}%), ungated net Sharpe {base['net_sharpe']:+.2f} +- {base['net_sharpe_se']:.2f}")
        log(f"    {'cell':12s} {'nights':>6s} {'p':>5s} {'gross$':>7s} {'sd':>5s} {'ratio':>6s} {'hit':>5s} {'cost/mean':>9s} {'net Sharpe':>16s} | N1 rotation p50/p95 | N2 run-length p50/p95 (+-SE) | diff vs other side (SE)")
        for s in STATES:
            defined = ~np.isnan(d[s].to_numpy()); dd = d[defined]; p_all = dd["pnl"].to_numpy()
            for side_lab, side_val in zip(SIDES[s], (1.0, -1.0)):
                g = dd[s].to_numpy() == side_val; other = dd[s].to_numpy() == -side_val
                if g.sum() < 30:
                    continue
                x = p_all[g]; y = p_all[other]; gs = D66.series_on(cal, dd["day"][g], x - COST).to_numpy()
                n1 = D64.rotation_null(g, p_all); n2 = D64.runlength_null(rng, g, p_all, n=N2_DRAWS); se95 = p95_se(n2)
                c = dict(state=s, side=side_lab, nights=int(g.sum()), p=float(g.mean()), gross_mean=float(x.mean()), sd=float(x.std(ddof=1)), ratio=float(x.mean() / x.std(ddof=1)), hit=float((x > 0).mean()), cost_share=float(COST / x.mean()) if x.mean() != 0 else float("inf"),
                         net_sharpe=D66.sharpe(gs), net_sharpe_se=D66.sharpe_boot(gs, cal), N1=dict(n=int(n1.size), p50=float(np.median(n1)), p95=float(np.quantile(n1, .95))), N2=dict(n=int(n2.size), p50=float(np.median(n2)), p95=float(np.quantile(n2, .95)), p95_se=se95),
                         other_mean=float(y.mean()), diff=float(x.mean() - y.mean()), diff_se=float(math.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size)))
                c["clears_N1"] = c["gross_mean"] > c["N1"]["p95"]; c["clears_N2"] = c["gross_mean"] > c["N2"]["p95"] + 2 * se95; c["clears_sharpe"] = c["net_sharpe"] > 0.5; cells[f"{s}:{side_lab}"] = c
                log(f"    {s + ' ' + side_lab:12s} {c['nights']:6,} {100*c['p']:4.0f}% {c['gross_mean']:+7.2f} {c['sd']:5.0f} {100*c['ratio']:+5.2f}% {100*c['hit']:4.1f}% {100*c['cost_share']:+8.0f}% {c['net_sharpe']:+6.2f} +- {c['net_sharpe_se']:.2f}    | {c['N1']['p50']:+6.2f} / {c['N1']['p95']:+6.2f} {'*' if c['clears_N1'] else ' '}    | {c['N2']['p50']:+6.2f} / {c['N2']['p95']:+6.2f} (+-{se95:.2f}) {'*' if c['clears_N2'] else ' '}    | {c['diff']:+6.2f} ({c['diff_se']:.2f})")
        fam = family_max_rotation(d, [(s, v) for s in STATES for v in (1.0, -1.0)]); obs = max(c["gross_mean"] for c in cells.values()); obs_k = max(cells, key=lambda k: cells[k]["gross_mean"])
        for c in cells.values():
            c["clears_family"] = c["gross_mean"] > float(np.quantile(fam, .95)); c["stage1"] = bool(c["clears_sharpe"] and c["clears_N1"] and c["clears_N2"] and c["clears_family"])
        log(f"    FAMILY MAX (common-offset rotation over the 8 cells of {root}-{w}, {fam.size} offsets): p50 {np.median(fam):+.2f}  p95 {np.quantile(fam, .95):+.2f}  p99 {np.quantile(fam, .99):+.2f}   observed best {obs:+.2f} ({obs_k})   share of offsets >= observed {100*(fam >= obs).mean():.1f}%")
        res[w] = dict(base=base, cells=cells, family=dict(n=int(fam.size), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)), p99=float(np.quantile(fam, .99)), observed_best=obs, observed_cell=obs_k, share_ge=float((fam >= obs).mean())))
    return res


def run():
    t0 = time.time(); print("D470 stage 0 -- can a state at the entry concentrate the overnight index drift enough to pay the micro cost?\n      spec committed in b3671b2 BEFORE this ran; 2016-2023; 2024+ unread; no holdout; state read at the previous session's 16:00 print")
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); res = {}
    for root in ROOTS:
        t = T[(T["root"] == root) & (T["day"] >= START) & (T["day"] <= END)].sort_values("day").reset_index(drop=True); cal = pd.Index(t["day"]); res[root] = score_root(root, t, cal)
    # predictions
    E, N = res["ES"]["W1"], res["NQ"]["W1"]; bE, bN = E["base"], N["base"]
    def cell(r, w, k):
        return res[r][w]["cells"].get(k)
    stage1 = [(r, w, k) for r in ROOTS for w in WINDOWS for k, c in res[r][w]["cells"].items() if c["stage1"]]
    picks = [(r, w, k) for r in ROOTS for w in WINDOWS for k, c in res[r][w]["cells"].items() if c["clears_sharpe"] and not c["stage1"]]
    print("\nPREDICTIONS")
    print(f"  X-a base rates reproduce D468 (ES-W1 $7.69 / 183 on 1,974; NQ-W1 $10.13 / 287)        : ES {bE['gross_mean']:+.2f} / {bE['sd']:.0f} on {bE['nights']:,}; NQ {bN['gross_mean']:+.2f} / {bN['sd']:.0f} on {bN['nights']:,}")
    ab = [(r, s, cell(r, 'W1', f'{s}:up')) for r in ROOTS for s in ('G-A', 'G-B')]
    print(f"  X-b G-A and G-B sides differ by < 1 SE of the difference                                 : " + "  ".join(f"{r} {s} {c['diff']:+.2f} ({c['diff_se']:.2f})" for r, s, c in ab if c))
    gc = [(r, cell(r, 'W1', 'G-C:below'), cell(r, 'W1', 'G-D:high')) for r in ROOTS]
    print(f"  X-c below-average: gross 1.3-2.0x base, sd 1.4-1.7x, gated net Sharpe < 0.5; G-D high same : " + "  ".join(f"{r} G-C below {c['gross_mean']/res[r]['W1']['base']['gross_mean']:.2f}x / sd {c['sd']/res[r]['W1']['base']['sd']:.2f}x / Sharpe {c['net_sharpe']:+.2f}; G-D high {h['gross_mean']/res[r]['W1']['base']['gross_mean']:.2f}x / {h['sd']/res[r]['W1']['base']['sd']:.2f}x / {h['net_sharpe']:+.2f}" for r, c, h in gc if c and h))
    print(f"  X-d no cell clears all three; ES-W1 family p95 $11-14; best observed at or below it        : stage-1 cells {stage1 or 'none'}; picks {picks or 'none'}; ES-W1 family p95 {E['family']['p95']:+.2f}, best {E['family']['observed_best']:+.2f} ({E['family']['observed_cell']})")
    print(f"  X-e W2 same picture, ratios closer on the below-average / high-vol side                   : ES-W2 G-C below ratio {100*cell('ES','W2','G-C:below')['ratio']:+.2f}% vs W1 {100*cell('ES','W1','G-C:below')['ratio']:+.2f}%; G-D high {100*cell('ES','W2','G-D:high')['ratio']:+.2f}% vs {100*cell('ES','W1','G-D:high')['ratio']:+.2f}%")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) states: continuation, prior overnight leg, the 200-average, the tercile; the state at row i-1 gates night i")
    n = 500; rng = np.random.default_rng(1); days = [str(x.date()) for x in pd.bdate_range("2016-01-04", periods=n)]; px = 2000 + np.cumsum(rng.normal(0, 10, n))
    t = pd.DataFrame({"day": days, "contract": "ESH6", "same_front": True, "h18_o": px - 1.0, "h08_c": px - 0.5, "h15_c": px}); t.loc[10, "contract"] = "ESM6"
    S = build_states(t); d = night_frame(t, S, "W1", 5.0)
    assert np.isnan(S.loc[10, "G-A"]) and np.isnan(S.loc[11, "G-A"]) and S.loc[12, "G-A"] == (1.0 if px[12] > px[11] else -1.0), "continuation needs the same contract on both days"
    assert (S["G-B"] == 1.0).all(), "h08_c > h18_o on every synthetic night"
    assert np.isnan(S.loc[SMA_MIN - 2, "G-C"]) and not np.isnan(S.loc[SMA_N + 1, "G-C"]) and S.loc[SMA_N + 1, "G-C"] == (1.0 if px[SMA_N + 1] > px[2:SMA_N + 2].mean() else -1.0)
    assert d.loc[13, "G-A"] == S.loc[12, "G-A"] and np.isnan(d.loc[12, "G-A"]) and d.loc[13, "day"] == days[13], "the night on row 13 carries row 12's state; row 12's night carries row 11's NaN"
    assert abs(d["pnl"].iloc[0] - 5.0) < 1e-9 and (S["G-D"].dropna().isin([1.0, 0.0, -1.0])).all() and (S["G-D"] == 0.0).sum() > 0
    print(f"  ok: G-A NaN across the roll and on the row after; G-C defined from row {SMA_N}; lag correct; W1 pnl $5 on a 1-point night; G-D has a middle tercile")
    print("== (b) the rotation null rejects a planted alignment and accepts a random gate")
    pnl = rng.normal(5, 100, 1500); g_plant = pnl > 0; g_rand = rng.random(1500) < 0.5
    n1 = D64.rotation_null(g_plant, pnl); assert pnl[g_plant].mean() > np.quantile(n1, .999); n1r = D64.rotation_null(g_rand, pnl); m = pnl[g_rand].mean(); assert np.quantile(n1r, .01) < m < np.quantile(n1r, .99)
    print(f"  ok: planted {pnl[g_plant].mean():+.1f} vs null p99.9 {np.quantile(n1, .999):+.1f}; random {m:+.1f} inside [{np.quantile(n1r, .01):+.1f}, {np.quantile(n1r, .99):+.1f}]")
    print("== (c) the run-length null reproduces the gate's run-length multiset; the family max is >= every single cell's rotation quantile")
    on, off = D64.run_lengths(g_rand); rr = np.random.default_rng(2); g2 = np.zeros(1500, bool); i = 0; st = True
    while i < 1500:
        L = int(rr.choice(on if st else off)); g2[i:i + L] = st; i += L; st = not st
    on2, off2 = D64.run_lengths(g2[:i]); assert set(on2) <= set(on) and set(off2) <= set(off)
    dd = pd.DataFrame({"day": days[:400], "pnl": pnl[:400], "G-A": np.where(rng.random(400) < 0.5, 1.0, -1.0), "G-B": np.where(rng.random(400) < 0.5, 1.0, -1.0), "G-C": np.nan, "G-D": np.where(rng.random(400) < 0.3, 1.0, np.where(rng.random(400) < 0.5, 0.0, -1.0))})
    fam = family_max_rotation(dd, [(s, v) for s in STATES for v in (1.0, -1.0)]); single = D64.rotation_null(dd["G-A"].to_numpy() == 1.0, dd["pnl"].to_numpy()); assert np.quantile(fam, .95) >= np.quantile(single, .95) and fam.size == 399
    print(f"  ok: family-max p95 {np.quantile(fam, .95):+.2f} >= single-cell p95 {np.quantile(single, .95):+.2f}; an undefined state contributes no cell")
    print("== (d) the sqrt(p) arithmetic: a gate on half the nights with the same per-night distribution gives ~0.71x the ungated Sharpe")
    big = rng.normal(8, 100, 200_000); half = np.where(rng.random(big.size) < 0.5, big, 0.0); r = D66.sharpe(half) / D66.sharpe(big); assert 0.65 < r < 0.77, r
    print(f"  ok: ratio {r:.3f} (expected 0.707 on 200,000 synthetic days)")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
