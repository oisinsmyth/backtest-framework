"""D464 -- the personal arms as gates on C1's session hold. S1 and S2 states computed on SPY/QQQ/DIA daily bars with the book's own
functions (D234's log_parts, D240's pivots + rolling_fit) gate which nights the 18:00 -> 16:00 ES hold (D449's table) is taken.
Spec committed in 0391331 BEFORE this file. In-sample 2016-01-04 .. 2023-12-29; 2024+ unread; no holdout.

    uv run python -u scripts/run_d464_arms_as_gates.py --run
    uv run python -u scripts/run_d464_arms_as_gates.py --selftest

Gate timing: the state at the close of the entry day (the hold's prev_day) gates the hold entered at 18:00 that evening. S2's gate
is the book's EXPOSURE (in an uptrend episode, <= 63 bars from its onset); the raw state is reported. Nulls: N1 the exact rotation of
the gate series over the hold index; N2 random gates with the real gate's on/off run-length distribution. Hurdle P through D463's
sized_days / provider_of (D440's lifecycle) at whole-ES and whole-MES contracts.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO / "src"))
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.simulator.fills import Bar
from backtest_framework.research.structure import pivots
ETF_FIX = REPO / "data" / "fixtures" / "etf_wide_daily_raw.csv.gz"; HOLDS = REPO / "data" / "fixtures" / "es_c1_holds.csv.gz"; OUT = REPO / "data" / "d464_arms_as_gates.json"
START, END = "2016-01-04", "2023-12-29"; ETFS = ("SPY", "QQQ", "DIA"); PRIMARY_ETF = "SPY"; S2_CAP = 63; K = 3
MULT_ES, MULT_MES, COST_ES, COST_MES = 50.0, 5.0, 17.0, 3.0; SEED, N2_DRAWS = 464, 1000


# ------------------------------------------------------------------------------------------ the arms' states, the book's code
def load_bars(sym):
    df = pd.read_csv(ETF_FIX, dtype={"timestamp": str, "symbol": str}); df = df[df["symbol"] == sym].sort_values("timestamp")
    days = df["timestamp"].str[:10].to_numpy(); bars = [TimestampedBar(timestamp=datetime.fromisoformat(t[:19]), bar=Bar(float(o), float(h), float(l), float(c))) for t, o, h, l, c in zip(df["timestamp"], df["open"], df["high"], df["low"], df["close"])]
    return days, bars


def s1_state(bars, A):
    md, hist = A.log_parts(bars); return (hist > 0) & (md <= 0) & np.isfinite(md) & np.isfinite(hist)


def s2_states(bars, U):
    """(raw UPTREND state, the book's exposure: in an episode and <= S2_CAP bars from its onset)."""
    T = len(bars); ps = pivots(bars, K); li = np.array([p.index for p in ps if p.sign < 0], dtype=int); hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
    g_lo, _ = U.rolling_fit(T, li, np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([]), K); g_hi, _ = U.rolling_fit(T, hj, np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([]), K)
    up = (g_lo > 0) & (g_hi > 0) & np.isfinite(g_lo) & np.isfinite(g_hi); prev = np.zeros_like(up); prev[1:] = up[:-1]; onset = up & ~prev; expo = np.zeros_like(up); i = 0
    while i < T:
        if onset[i]:
            j = i
            while j < T and up[j] and j - i < S2_CAP:
                expo[j] = True; j += 1
            i = j
        else:
            i += 1
    return up, expo


def gates_for(sym, A, U):
    days, bars = load_bars(sym); s1 = s1_state(bars, A); up, expo = s2_states(bars, U)
    return pd.DataFrame({"day": days, "S1": s1, "S2_state": up, "S2": expo}).set_index("day")


# ------------------------------------------------------------------------------------------ holds and statistics
def load_holds():
    h = pd.read_csv(HOLDS, dtype={"day": str, "prev_day": str, "contract": str}); h = h[(h["day"] >= START) & (h["day"] <= END)].sort_values("day").reset_index(drop=True)
    h["pnl_bp"] = h["d_end"] * 1e4; h["mae_bp"] = -h["mae"] * 1e4; h["pnl_usd"] = h["d_end"] * h["entry"] * MULT_ES; h["mae_usd"] = -h["mae"] * h["entry"] * MULT_ES; h["mfe_usd"] = h["d_high"] * h["entry"] * MULT_ES
    return h


def block_boot(x, dates, n_boot=1000, seed=7):
    mon = np.array([str(d)[:7] for d in dates]); keys, inv = np.unique(mon, return_inverse=True); sums = np.bincount(inv, weights=x); cnts = np.bincount(inv); rng = np.random.default_rng(seed); m = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); m[b] = sums[pick].sum() / cnts[pick].sum()
    return float(m.std(ddof=1)), float(x.mean())


def night_stats(h, mask):
    g = h[mask]
    if len(g) < 20:
        return dict(n=int(len(g)))
    se, m = block_boot(g["pnl_bp"].to_numpy(), g["day"].to_numpy()); mae = g["mae_usd"].to_numpy()
    return dict(n=int(len(g)), share=float(mask.mean()), mean_bp=m, se_bp=se, sd_bp=float(g["pnl_bp"].std(ddof=1)), median_bp=float(g["pnl_bp"].median()), hit=float((g["pnl_bp"] > 0).mean()),
                mae_bp=dict(p50=float(g["mae_bp"].quantile(.5)), p90=float(g["mae_bp"].quantile(.9)), p99=float(g["mae_bp"].quantile(.99)), worst=float(g["mae_bp"].max())),
                mae_usd=dict(p50=float(np.quantile(mae, .5)), p99=float(np.quantile(mae, .99)), worst=float(mae.max()), worst_day=str(g["day"].iat[int(mae.argmax())])), p_gt_1000=float((mae > 1000).mean()), p_gt_2000=float((mae > 2000).mean()),
                per_bar_bp=float(m / max(float(g["bars"].mean()), 1)))


def rotation_null(gate, pnl):
    T = len(gate); out = np.empty(T - 1)
    for k in range(1, T):
        g = np.roll(gate, k); out[k - 1] = float(pnl[g].mean()) if g.any() else np.nan
    return out[np.isfinite(out)]


def run_lengths(gate):
    on, off = [], []; i = 0; T = len(gate)
    while i < T:
        j = i
        while j < T and gate[j] == gate[i]:
            j += 1
        (on if gate[i] else off).append(j - i); i = j
    return np.array(on), np.array(off)


def runlength_null(rng, gate, pnl, n=N2_DRAWS):
    """Random gates that reproduce the real gate's on-run and off-run length distributions (alternating, starting at random)."""
    on, off = run_lengths(gate); T = len(gate); out = np.empty(n)
    for d in range(n):
        g = np.zeros(T, bool); i = 0; state = bool(rng.integers(0, 2))
        while i < T:
            L = int(rng.choice(on if state else off)); g[i:i + L] = state; i += L; state = not state
        out[d] = float(pnl[g].mean()) if g.any() else np.nan
    return out[np.isfinite(out)]


def hurdle_rows(h, mask, sessions, D63, D40, D86, plan, mult, cost, log):
    """D463's hurdle_p on the gated nights, at the given contract size (ES or MES) -- the dollar columns rescaled."""
    g = h[mask].copy(); d = pd.DataFrame({"day": g["day"], "pnl_usd": g["pnl_usd"] * (mult / MULT_ES), "mae_usd": -g["mae_usd"] * (mult / MULT_ES), "mfe_usd": g["mfe_usd"] * (mult / MULT_ES), "cost_usd": cost})
    return D63.hurdle_p(d, sessions, D40, D86, plan, log=log)


# ------------------------------------------------------------------------------------------ the study
def run():
    t0 = time.time(); print("D464 -- S1 and S2 as gates on C1's session hold (ES, 2016-2023)\n      the bar was committed in 0391331 BEFORE this ran; 2024+ unread; no holdout\n")
    A = _load("d234a", "run_activation_threshold.py"); U = _load("d240u", "run_uptrend_onset.py"); D63 = _load("d463", "run_d463_intraday_momentum.py"); D40 = _load("d440l", "d440_lifecycle.py"); D86 = D40.D386
    plan = [p for p in D86.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]; rng = np.random.default_rng(SEED)
    h = load_holds(); G = {s: gates_for(s, A, U) for s in ETFS}; res = dict(spec="0391331", start=START, end=END, n_holds=int(len(h)), gates={}, nulls={}, hurdle_P={}, bar={})
    print(f"  holds 2016-2023: {len(h):,} ({h['day'].min()} .. {h['day'].max()});  gate = the state at the close of the entry day (prev_day)")
    masks = {"all": np.ones(len(h), bool)}
    for s in ETFS:
        g = G[s].reindex(h["prev_day"]); masks[f"S1_{s}"] = g["S1"].fillna(False).to_numpy(bool); masks[f"S2_{s}"] = g["S2"].fillna(False).to_numpy(bool); masks[f"S2state_{s}"] = g["S2_state"].fillna(False).to_numpy(bool)
    masks["union_SPY"] = masks["S1_SPY"] | masks["S2_SPY"]; masks["both_SPY"] = masks["S1_SPY"] & masks["S2_SPY"]
    for k, m in masks.items():
        st = night_stats(h, m); res["gates"][k] = st
        if st.get("n", 0) >= 20:
            print(f"  {k:12s} n {st['n']:5,} ({100*st['share']:5.1f}%)  mean {st['mean_bp']:+6.2f} +- {st['se_bp']:4.2f} bp  sd {st['sd_bp']:5.1f}  median {st['median_bp']:+6.2f}  hit {100*st['hit']:.1f}%  MAE bp p50 {st['mae_bp']['p50']:5.1f} p99 {st['mae_bp']['p99']:5.0f} worst {st['mae_bp']['worst']:5.0f}  $ p99 {st['mae_usd']['p99']:6,.0f} worst {st['mae_usd']['worst']:6,.0f} ({st['mae_usd']['worst_day']})  P(> $1k) {100*st['p_gt_1000']:.1f}%  P(> $2k) {100*st['p_gt_2000']:.1f}%")
        else:
            print(f"  {k:12s} n {st.get('n', 0)} -- too few nights")
    pnl = h["pnl_bp"].to_numpy(); ung = res["gates"]["all"]
    for k in ("S1_SPY", "S2_SPY", "S2state_SPY"):
        g = masks[k]; rot = rotation_null(g, pnl); r2 = runlength_null(rng, g, pnl); st = res["gates"][k]
        c = dict(N1=dict(n=int(rot.size), p50=float(np.median(rot)), p95=float(np.quantile(rot, .95)), p99=float(np.quantile(rot, .99))), N2=dict(n=int(r2.size), p50=float(np.median(r2)), p95=float(np.quantile(r2, .95)), mc_se=float(r2.std(ddof=1) / math.sqrt(r2.size))))
        c["G1"] = bool(st["mean_bp"] > 0 and st["mean_bp"] > c["N1"]["p95"] and st["mean_bp"] > c["N2"]["p95"] + 2 * c["N2"]["mc_se"]); c["G2"] = bool(st["mae_bp"]["p99"] < ung["mae_bp"]["p99"]); res["nulls"][k] = c
        print(f"\n  {k}: real {st['mean_bp']:+.2f}  N1 rotation p50 {c['N1']['p50']:+.2f} p95 {c['N1']['p95']:+.2f} (exact, {c['N1']['n']:,})  N2 run-length gates p50 {c['N2']['p50']:+.2f} p95 {c['N2']['p95']:+.2f} +- {c['N2']['mc_se']:.2f}  G1 {c['G1']}  |  MAE p99 gated {st['mae_bp']['p99']:.0f} vs all {ung['mae_bp']['p99']:.0f} bp  G2 {c['G2']}")
    sessions = pd.DataFrame({"day": h["day"]})
    for k in ("all", "S2_SPY", "S1_SPY"):
        for lab, mult, cost in (("ES", MULT_ES, COST_ES), ("MES", MULT_MES, COST_MES)):
            print(f"\n  HURDLE P -- {k} nights, whole {lab} contracts ({'$50' if lab == 'ES' else '$5'}/pt, ${cost:.0f} round trip), MFFU Rapid EOD 50K, 600-day horizon"); res["hurdle_P"][f"{k}|{lab}"] = hurdle_rows(h, masks[k], sessions, D63, D40, D86, plan, mult, cost, print)
    clear = []
    for key, grid in res["hurdle_P"].items():
        if not key.startswith("S2_SPY"):
            continue
        for f, c in grid.items():
            if f != "1ct" and (c["P4_fund_life_years"] or 0) >= 3 and c["V"] > 2 * c["V_se"] and c["P3_worst_day_pct"] >= -2 and c["P5_years_over_40"] == 0:
                clear.append(f"{key}:{f}")
    n2 = res["nulls"]["S2_SPY"]; res["bar"] = dict(G1=n2["G1"], G2=n2["G2"], P4_clearing=clear, candidate=bool(n2["G1"] and n2["G2"] and clear))
    print(f"\nTHE BAR (S2 exposure gate on SPY, ES holds, in-sample)\n  G1 gated mean > 0 and > N1 p95 and > N2 p95 + 2 MC-SE : {n2['G1']}\n  G2 gated MAE p99 < ungated p99                       : {n2['G2']}\n  P4 clearing cells (ES or MES grid)                   : {clear or 'none'}\n  CANDIDATE for the unread slice: {res['bar']['candidate']}")
    a, s1, s2 = res["gates"]["all"], res["gates"]["S1_SPY"], res["gates"]["S2_SPY"]; hp = res["hurdle_P"]
    life = lambda key, f: hp[key][f]["P4_fund_life_years"]
    print("\nPREDICTIONS\n" + f"  X-a unconditional: mean +3..+5, sd 90-110, MAE p99 330-420 bp, P(>$2k) 8-14%      : {a['mean_bp']:+.2f}, {a['sd_bp']:.0f}, {a['mae_bp']['p99']:.0f}, {100*a['p_gt_2000']:.1f}%\n"
          + f"  X-b S2 on 30-45%, mean +3..+6, sd 70-95, p99 250-350, G2 pass; S1 on 12-20%, mean +4..+9, sd 110-150, p99 400-550, G2 fail : S2 {100*s2['share']:.0f}%, {s2['mean_bp']:+.2f}, {s2['sd_bp']:.0f}, {s2['mae_bp']['p99']:.0f}, G2 {res['nulls']['S2_SPY']['G2']};  S1 {100*s1['share']:.0f}%, {s1['mean_bp']:+.2f}, {s1['sd_bp']:.0f}, {s1['mae_bp']['p99']:.0f}, G2 {res['nulls']['S1_SPY']['G2']}\n"
          + f"  X-c N1 p95 +2..+4; G1 fails for S2, a coin for S1                                  : S2 N1 p95 {res['nulls']['S2_SPY']['N1']['p95']:+.2f} G1 {res['nulls']['S2_SPY']['G1']};  S1 N1 p95 {res['nulls']['S1_SPY']['N1']['p95']:+.2f} G1 {res['nulls']['S1_SPY']['G1']}\n"
          + f"  X-d ES: zero size at f <= 0.4%, P3 breaches >= 5%, life < 0.5 yr; MES: sizes 2-5, P3 passes, life 0.5-2 yr, ann +1..+3% : ES all f0.7 life {life('all|ES','0.007')}, MES all f0.7 {hp['all|MES']['0.007']['contracts_mean']:.1f} ct life {life('all|MES','0.007')} ann {hp['all|MES']['0.007']['ann_profit_mean_pct']:+.1f}%\n"
          + f"  X-e S2 lengthens life 1.3-2x at matched f, S1 shortens; neither clears 3 yr        : MES f0.7 life all {life('all|MES','0.007')}  S2 {life('S2_SPY|MES','0.007')}  S1 {life('S1_SPY|MES','0.007')};  clearing {clear or 'none'}\n"
          + f"  X-f QQQ/DIA agree in sign; union ~ S2; intersection < 5%                          : S2 mean SPY {s2['mean_bp']:+.2f} QQQ {res['gates']['S2_QQQ'].get('mean_bp', float('nan')):+.2f} DIA {res['gates']['S2_DIA'].get('mean_bp', float('nan')):+.2f};  union {100*res['gates']['union_SPY']['share']:.0f}%  both {100*res['gates']['both_SPY'].get('share', 0):.1f}%")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (2016-2023; 2024+ unread; no holdout)")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); A = _load("d234a", "run_activation_threshold.py"); U = _load("d240u", "run_uptrend_onset.py")
    print("== (a) S2 on a synthetic: a clean uptrend with rising swing lows and highs is UPTREND after warm-up, and the exposure gate is on for at most 63 bars per episode")
    rng = np.random.default_rng(0); T = 1500; lp = np.cumsum(np.where(np.arange(T) % 20 < 12, 0.004, -0.003)) + rng.normal(0, 0.001, T)      # a sawtooth uptrend: pivots every ~20 bars
    bars = [TimestampedBar(datetime(2015, 1, 1), Bar(float(np.exp(x)), float(np.exp(x + 0.002)), float(np.exp(x - 0.002)), float(np.exp(x)))) for x in lp]
    up, expo = s2_states(bars, U); assert up[600:].mean() > 0.9 and expo.sum() <= (up.astype(int).sum()) and max(run_lengths(expo)[0]) <= S2_CAP, (up[600:].mean(), max(run_lengths(expo)[0]))
    print(f"  UPTREND on {100*up[600:].mean():.0f}% of bars after warm-up; longest exposure run {max(run_lengths(expo)[0])} <= 63")
    print("== (b) S1 on a synthetic V: off in the fall, on when the climb-out begins below the channel, off again above it")
    lp = np.concatenate([np.zeros(1100), -0.0015 * np.arange(1, 121), -0.18 + 0.0015 * np.arange(1, 281)]); T = len(lp)
    bars = [TimestampedBar(datetime(2015, 1, 1), Bar(float(np.exp(x)), float(np.exp(x + 0.001)), float(np.exp(x - 0.001)), float(np.exp(x)))) for x in lp]; s1 = s1_state(bars, A)
    assert not s1[1100:1210].any() and s1[1225:1300].any() and not s1[1380:].any(), (s1[1100:1210].sum(), s1[1225:1300].sum(), s1[1380:].sum())
    print(f"  off during the fall, on for {int(s1[1225:1300].sum())} bars of the climb-out, off after the recovery")
    print("== (c) gate timing, the rotation null at offset 0, the run-length generator")
    h = load_holds(); G = gates_for("SPY", A, U); g = G["S2"].reindex(h["prev_day"]).fillna(False).to_numpy(bool); pnl = h["pnl_bp"].to_numpy()
    assert (G.index < "2016-01-04").sum() > 1000, "warm-up bars missing"; assert abs(float(pnl[np.roll(g, 0)].mean()) - float(pnl[g].mean())) < 1e-12
    on, off = run_lengths(g); rr = np.random.default_rng(1); gg = runlength_null(rr, g, pnl, 50); assert gg.size == 50 and abs(on.mean() - np.mean(run_lengths(g)[0])) < 1e-9
    print(f"  {len(h):,} holds; S2 gate on {100*g.mean():.0f}% of nights; on-run mean {on.mean():.1f} bars, off-run mean {off.mean():.1f}; null draws ok")
    print("== (d) MES dollars are ES dollars / 10")
    assert abs(MULT_MES / MULT_ES - 0.1) < 1e-12
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    run() if a.run else cmd_selftest()
