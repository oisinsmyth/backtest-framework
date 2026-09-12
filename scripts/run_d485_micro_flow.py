"""D485 -- retail flow stage 0 on the micro-flow fixture: the three premise checks (P1 distinct population, P2 contrarian, P3 the prop-firm
fingerprint) and the one declared four-cell return read (F1/F2 x ES/NQ, against the micro crowd's excess flow), with the exact session
rotation (N1) and the common-offset family maximum (N2). Spec 0651bb9; fixture scripts/build_fut_micro_flow.py.

    python scripts/run_d485_micro_flow.py --selftest
    python scripts/run_d485_micro_flow.py --run [--out data/d485_micro_flow_stage0.json]

Windows: in-sample sessions <= 2026-06-30; the reserve (2026-07-01 .. 2026-09-10) is NOT read by --run.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]; FIX = REPO / "data" / "fixtures" / "fut_micro_flow_5m.csv.gz"; SPECS = REPO / "data" / "futures_contract_specs.json"
IS_END = "2026-06-30"; COST_RT = 3.0; PAIRS = ("ES", "NQ"); MICRO = {"ES": "MES", "NQ": "MNQ"}
CELLS = {"F1": dict(form=(9 * 60 + 30, 10 * 60 + 30), hold=(10 * 60 + 30, 16 * 60)), "F2": dict(form=(9 * 60 + 30, 15 * 60), hold=(15 * 60, 16 * 60))}
RTH = (9 * 60 + 30, 16 * 60); LAST30 = (15 * 60 + 30, 16 * 60); P1_CORR_PASS = 0.80; P1_CORR_ABANDON = 0.90; P1_LOT_PP = 0.15; MIN_BUCKETS = 60


# ------------------------------------------------------------------------------------------ data
def load(in_sample=True):
    T = pd.read_csv(FIX, dtype={"pair": str, "cls": str, "root": str, "contract": str, "session": str}); T = T[T["rth"]]
    T = T[T["session"] <= IS_END] if in_sample else T[T["session"] > IS_END]
    return T


def per_session(T, pair, cls, lo, hi, col_num="buy", col_den=None):
    """Sum of columns over buckets with minute in [lo, hi) per session."""
    b = T[(T["pair"] == pair) & (T["cls"] == cls) & (T["minute"] >= lo) & (T["minute"] < hi)]
    g = b.groupby("session")[["buy", "sell", "vol", "lot1", "n"]].sum(); return g


def oi(g):
    d = g["buy"] + g["sell"]; return ((g["buy"] - g["sell"]) / d.where(d > 0)).astype(float)


def prices(T, pair):
    """Mini prices at the boundaries: first trade at/after minute m (first_px of bucket m) and last trade before minute m (last_px of bucket m-5)."""
    b = T[(T["pair"] == pair) & (T["cls"] == "mini")].set_index(["session", "minute"])
    def first_at(m):
        return b["first_px"].xs(m, level="minute")
    def last_before(m):
        return b["last_px"].xs(m - 5, level="minute")
    return first_at, last_before


# ------------------------------------------------------------------------------------------ premise checks
def premise(T, pair):
    out = {}
    # P1(a) lot share; P1(b) within-session correlation of the two imbalances over RTH buckets
    lot = {}
    for cls in ("mini", "micro"):
        b = T[(T["pair"] == pair) & (T["cls"] == cls)]; lot[cls] = float(b["lot1"].sum() / b["vol"].sum())
    piv = {cls: T[(T["pair"] == pair) & (T["cls"] == cls)].pivot(index="session", columns="minute", values=["buy", "sell"]) for cls in ("mini", "micro")}
    sessions = sorted(set(piv["mini"].index) & set(piv["micro"].index)); cors = []
    for s in sessions:
        o = {}
        for cls in ("mini", "micro"):
            bs = piv[cls].loc[s, "buy"]; ss = piv[cls].loc[s, "sell"]; d = bs + ss; o[cls] = ((bs - ss) / d.where(d > 0)).astype(float)
        both = o["mini"].notna() & o["micro"].notna()
        if both.sum() >= MIN_BUCKETS:
            cors.append(float(np.corrcoef(o["mini"][both], o["micro"][both])[0, 1]))
    cors = np.array(cors); out["P1"] = dict(lot1_share=lot, lot_gap_pp=lot["micro"] - lot["mini"], corr_sessions=int(cors.size), corr_median=float(np.median(cors)), corr_p10=float(np.quantile(cors, .1)), corr_p90=float(np.quantile(cors, .9)),
                                         passes=bool(np.median(cors) <= P1_CORR_PASS and (lot["micro"] - lot["mini"]) >= P1_LOT_PP), corr_passes=bool(np.median(cors) <= P1_CORR_PASS), abandon=bool(np.median(cors) > P1_CORR_ABANDON))
    # P2: OI_day vs the prior session's RTH return
    first_at, last_before = prices(T, pair); r_rth = (last_before(RTH[1]) / first_at(RTH[0]) - 1).rename("r"); r_prev = r_rth.shift(1)
    p2 = {}
    for cls in ("mini", "micro"):
        o = oi(per_session(T, pair, cls, *RTH)); j = pd.concat([o.rename("oi"), r_prev], axis=1).dropna()
        p2[cls] = dict(n=int(len(j)), pearson=float(np.corrcoef(j["oi"], j["r"])[0, 1]), spearman=float(j["oi"].rank().corr(j["r"].rank())), se=float(1 / np.sqrt(len(j))))
    p2["passes"] = bool(p2["micro"]["pearson"] < 0 and p2["micro"]["pearson"] < p2["mini"]["pearson"]); out["P2"] = p2
    # P3(a) last-30 micro sell share vs the rest of the day; (b) cumulative flow 09:30-15:00 vs the last hour's return
    rng = np.random.default_rng(485); p3 = {}
    for cls in ("mini", "micro"):
        a = per_session(T, pair, cls, RTH[0], LAST30[0]); z = per_session(T, pair, cls, *LAST30); j = pd.concat([(a["sell"] / (a["buy"] + a["sell"])).rename("day"), (z["sell"] / (z["buy"] + z["sell"])).rename("last")], axis=1).dropna()
        diff = (j["last"] - j["day"]).to_numpy(); boots = np.array([diff[rng.integers(0, diff.size, diff.size)].mean() for _ in range(2000)])
        f = oi(per_session(T, pair, cls, RTH[0], 15 * 60)); rl = (last_before(RTH[1]) / first_at(15 * 60) - 1); k = pd.concat([f.rename("f"), rl.rename("r")], axis=1).dropna()
        cb = np.array([np.corrcoef(k["f"].to_numpy()[i], k["r"].to_numpy()[i])[0, 1] for i in (rng.integers(0, len(k), len(k)) for _ in range(2000))])
        p3[cls] = dict(n=int(len(j)), sell_share_day=float(j["day"].mean()), sell_share_last30=float(j["last"].mean()), diff_pp=float(diff.mean()), diff_se=float(boots.std(ddof=1)), corr_cum_vs_last_hour=float(np.corrcoef(k["f"], k["r"])[0, 1]), corr_se=float(cb.std(ddof=1)), n_corr=int(len(k)))
    dcorr = p3["micro"]["corr_cum_vs_last_hour"] - p3["mini"]["corr_cum_vs_last_hour"]; dse = float(np.hypot(p3["micro"]["corr_se"], p3["mini"]["corr_se"]))
    p3["a_passes"] = bool(abs(p3["micro"]["diff_pp"]) >= 0.03 and abs(p3["micro"]["diff_pp"]) >= 2 * p3["micro"]["diff_se"]); p3["b_diff"] = dcorr; p3["b_diff_se"] = dse; p3["b_passes"] = bool(abs(dcorr) >= 2 * dse); out["P3"] = p3
    return out


# ------------------------------------------------------------------------------------------ the return read
def cell_series(T, pair, cell):
    """Per session: Dv (z(OI_micro) - z(OI_mini) over the formation window) and the hold return in index points (mini prices)."""
    c = CELLS[cell]; first_at, last_before = prices(T, pair)
    o = {cls: oi(per_session(T, pair, cls, *c["form"])) for cls in ("mini", "micro")}
    z = lambda x: (x - x.mean()) / x.std(ddof=1)
    j = pd.concat([o["micro"].rename("om"), o["mini"].rename("oe"), first_at(c["hold"][0]).rename("entry"), last_before(c["hold"][1]).rename("exit")], axis=1).dropna()
    j["Dv"] = z(j["om"]) - z(j["oe"]); j["move"] = j["exit"] - j["entry"]
    # [F] every formation bucket ends at or before the hold start, by construction of the windows
    assert c["form"][1] <= c["hold"][0], "[F] formation must end before the hold starts"
    return j


def side_diff(Dv, move, usd):
    """Mean hold move (USD at one micro) in the bottom Dv tercile minus the top tercile: the declared family statistic, centred on zero."""
    lo, hi = np.quantile(Dv, [1 / 3, 2 / 3]); return float((move[Dv <= lo].mean() - move[Dv >= hi].mean()) * usd)


def pnl_vec(Dv, move, usd):
    return -np.sign(Dv) * move * usd


def pnl_loop(Dv, move, usd):
    out = np.empty(len(Dv))
    for i in range(len(Dv)):
        pos = -1.0 if Dv[i] > 0 else (1.0 if Dv[i] < 0 else 0.0); out[i] = pos * move[i] * usd
    return out


def block_se(x, sessions, n_boot=2000, seed=7):
    mon = np.array([s[:7] for s in sessions]); keys, inv = np.unique(mon, return_inverse=True); sums = np.bincount(inv, weights=x); cnts = np.bincount(inv); rng = np.random.default_rng(seed); m = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); m[b] = sums[pick].sum() / cnts[pick].sum()
    return float(m.std(ddof=1))


def read_cells(T, specs):
    series = {}; stats = {}
    for pair in PAIRS:
        usd = specs[MICRO[pair]]["usd_per_point"]
        for cell in CELLS:
            j = cell_series(T, pair, cell); Dv = j["Dv"].to_numpy(); mv = j["move"].to_numpy(); sess = j.index.to_numpy()
            g = pnl_vec(Dv, mv, usd); assert np.array_equal(g, pnl_loop(Dv, mv, usd)), "[M] vectorised P&L != loop"; net = g - COST_RT
            k = max(int(round(0.01 * len(g))), 1); srt = np.sort(g); lo, hi = np.quantile(Dv, [1 / 3, 2 / 3])
            stats[f"{pair}/{cell}"] = dict(n=int(len(g)), gross_mean=float(g.mean()), gross_se=block_se(g, sess), net_mean=float(net.mean()), median=float(np.median(g)), hit=float((g > 0).mean()), trim1_mean=float(srt[k:-k].mean()), worst=float(g.min()), worst_session=str(sess[int(g.argmin())]),
                                           spearman=float(pd.Series(Dv).rank().corr(pd.Series(mv).rank())), side_diff_usd=side_diff(Dv, mv, usd),
                                           tercile_move_usd=dict(bottom=float(mv[Dv <= lo].mean() * usd), middle=float(mv[(Dv > lo) & (Dv < hi)].mean() * usd), top=float(mv[Dv >= hi].mean() * usd)), usd_per_point=usd, cost_rt=COST_RT)
            series[f"{pair}/{cell}"] = (Dv, mv, usd, sess)
    return series, stats


def nulls(series):
    """N1 exact rotation per cell (all T-1 offsets); N2 common-offset family maximum of the side difference across the four cells."""
    keys = list(series); Ts = {k: len(series[k][0]) for k in keys}; Tmin = min(Ts.values()); out = {}; fam = np.full(Tmin - 1, -np.inf)
    for k in keys:
        Dv, mv, usd, _ = series[k]; T = len(Dv); sd = np.empty(T - 1); pm = np.empty(T - 1)
        for i in range(1, T):
            d = np.roll(Dv, i); sd[i - 1] = side_diff(d, mv, usd); pm[i - 1] = float(pnl_vec(d, mv, usd).mean())
        out[k] = dict(side_diff=dict(p50=float(np.quantile(sd, .5)), p95=float(np.quantile(sd, .95)), n=int(T - 1)), pnl_mean=dict(p50=float(np.quantile(pm, .5)), p95=float(np.quantile(pm, .95))))
        fam = np.maximum(fam, sd[:Tmin - 1])
    out["family_max_side_diff"] = dict(p50=float(np.quantile(fam, .5)), p95=float(np.quantile(fam, .95)), n_offsets=int(Tmin - 1), cells=keys)
    return out


# ------------------------------------------------------------------------------------------ audits
def audit_sign():
    """[S] in money: a long (Dv < 0) into an up move pays positive; a short (Dv > 0) into an up move pays negative."""
    g = pnl_vec(np.array([-1.0, 1.0]), np.array([2.0, 2.0]), 5.0); assert g[0] == 10.0 and g[1] == -10.0, g; return True


def audit_flip(series):
    """[X] flipping the aggressor sign (buy<->sell) negates every OI, hence Dv, hence the side difference exactly."""
    for k, (Dv, mv, usd, _) in series.items():
        assert abs(side_diff(-Dv, mv, usd) + side_diff(Dv, mv, usd)) < 1e-9, k
    return True


def cmd_selftest():
    audit_sign(); rng = np.random.default_rng(1); Dv = rng.normal(size=300); mv = rng.normal(size=300)
    assert np.array_equal(pnl_vec(Dv, mv, 5.0), pnl_loop(Dv, mv, 5.0)); audit_flip({"x": (Dv, mv, 5.0, None)})
    # rotation null of an independent series is centred on zero; a planted contrarian relation is detected
    sd = [side_diff(np.roll(Dv, i), mv, 5.0) for i in range(1, 300)]; assert abs(np.median(sd)) < 1.0, np.median(sd)
    planted = -0.5 * Dv + rng.normal(size=300) * 0.5; assert side_diff(Dv, planted, 5.0) > np.quantile(sd, .95), "planted contrarian relation must clear the rotation p95"
    print("selftest OK: [S] sign in money, [M] vec==loop, [X] flip negates, rotation centred, planted effect detected")


def cmd_run(out):
    t0 = time.time(); specs = json.loads(SPECS.read_text()); T = load(in_sample=True); print(f"D485 stage 0 -- in-sample sessions <= {IS_END}: {T['session'].nunique()} sessions, {len(T):,} RTH bucket rows", flush=True)
    res = dict(spec="0651bb9", in_sample_end=IS_END, sessions=int(T["session"].nunique()), premise={}, cells={}, nulls={}, audits={})
    for pair in PAIRS:
        res["premise"][pair] = premise(T, pair); p = res["premise"][pair]
        print(f"\n[{pair}] P1 lot-1 share mini {p['P1']['lot1_share']['mini']:.3f} micro {p['P1']['lot1_share']['micro']:.3f} (gap {p['P1']['lot_gap_pp']*100:+.1f} pp); within-session corr(OI_micro, OI_mini) median {p['P1']['corr_median']:.3f} [p10 {p['P1']['corr_p10']:.3f}, p90 {p['P1']['corr_p90']:.3f}] over {p['P1']['corr_sessions']} sessions -> corr passes {p['P1']['corr_passes']}, full P1 passes {p['P1']['passes']}, ABANDON {p['P1']['abandon']}")
        print(f"[{pair}] P2 corr(OI_day, r_prev): micro {p['P2']['micro']['pearson']:+.3f} (spearman {p['P2']['micro']['spearman']:+.3f}) mini {p['P2']['mini']['pearson']:+.3f} (SE ~{p['P2']['micro']['se']:.3f}, n {p['P2']['micro']['n']}) -> passes {p['P2']['passes']}")
        print(f"[{pair}] P3a micro sell share last-30 {p['P3']['micro']['sell_share_last30']:.3f} vs day {p['P3']['micro']['sell_share_day']:.3f} (diff {p['P3']['micro']['diff_pp']*100:+.2f} pp, SE {p['P3']['micro']['diff_se']*100:.2f}); mini diff {p['P3']['mini']['diff_pp']*100:+.2f} pp -> passes {p['P3']['a_passes']}")
        print(f"[{pair}] P3b corr(cumOI 09:30-15:00, r last hour): micro {p['P3']['micro']['corr_cum_vs_last_hour']:+.3f} (SE {p['P3']['micro']['corr_se']:.3f}) mini {p['P3']['mini']['corr_cum_vs_last_hour']:+.3f}; diff {p['P3']['b_diff']:+.3f} +- {p['P3']['b_diff_se']:.3f} -> passes {p['P3']['b_passes']}")
    if any(res["premise"][p]["P1"]["abandon"] for p in PAIRS):
        print("\nP1 ABANDON on at least one pair -- per the pre-registration the return read does not run for that pair; running only pairs that survive", flush=True)
    keep = [p for p in PAIRS if not res["premise"][p]["P1"]["abandon"]]
    if keep:
        global PAIRS_RUN; series, stats = read_cells(T[T["pair"].isin(keep)], specs); res["cells"] = stats; res["nulls"] = nulls(series); res["audits"] = dict(S=audit_sign(), X=audit_flip(series), M=True, F=True)
        print("\ncell            n   gross    net   se   median  hit   trim1  worst   spearman  side_diff   N1 p50/p95      tercile b/m/t")
        for k, s in stats.items():
            n1 = res["nulls"][k]["side_diff"]; t = s["tercile_move_usd"]
            print(f"{k:<12} {s['n']:>4} {s['gross_mean']:>7.2f} {s['net_mean']:>6.2f} {s['gross_se']:>5.2f} {s['median']:>7.2f} {s['hit']:.3f} {s['trim1_mean']:>7.2f} {s['worst']:>7.0f}  {s['spearman']:+.3f}   {s['side_diff_usd']:>8.2f}   {n1['p50']:>6.2f}/{n1['p95']:>6.2f}   {t['bottom']:>6.2f}/{t['middle']:>6.2f}/{t['top']:>6.2f}")
        fm = res["nulls"]["family_max_side_diff"]; print(f"family-max side difference (N2, common offset over {len(stats)} cells, {fm['n_offsets']} offsets): p50 {fm['p50']:.2f}  p95 {fm['p95']:.2f}")
        for k, s in stats.items():
            n1 = res["nulls"][k]["side_diff"]; s["pick"] = bool(s["side_diff_usd"] > n1["p95"] and s["side_diff_usd"] > fm["p95"] and s["gross_mean"] > 0 and s["net_mean"] > 0)
        print("picks:", [k for k, s in stats.items() if s["pick"]] or "none")
    res["wall_s"] = round(time.time() - t0, 1); Path(out).write_text(json.dumps(res, indent=1)); print(f"\nwrote {out} in {res['wall_s']}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--run", action="store_true"); ap.add_argument("--out", default=str(REPO / "data" / "d485_micro_flow_stage0.json")); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        cmd_run(a.out)
