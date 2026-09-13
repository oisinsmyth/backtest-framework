"""D506 -- stage 1: does a signal's directional ACCURACY survive the in-play filter, or does selection only dilute the fee?
Primary T = (2p - 1) - fee/E|M|; primary cell = Delta = T(in play) - T(the rest) for S2 (the log MACD) on YM. Controls V (realised-volatility
matched), W (wrong window), U (the untradeable realised-range bound). Nulls: exact enumerated rotation of the score per root, and a 16-cell
family maximum under shared offsets. Spec committed in 2bea9d9 BEFORE this file. 2016-2023; 2024+ not read.

    uv run python -u scripts/run_d506_inplay_accuracy.py --run
    uv run python -u scripts/run_d506_inplay_accuracy.py --selftest
"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TABLE = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"; META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
OUT = REPO / "data" / "d506_inplay_accuracy.json"; CELLS = REPO / "data" / "d506_cells.csv.gz"; SPEC = "2bea9d9"
START, END = "2016-01-04", "2023-12-29"
ROOTS = ["ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E"]; PRIMARY_ROOT, PRIMARY_SIG = "YM", "S2"
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "GC": 10.0, "CL": 100.0, "6E": 12_500.0, "ZN": 1_000.0, "ZB": 1_000.0}
FEE = {r: (6.0 if r in ("ZN", "ZB") else 3.0) for r in ROOTS}
NIGHT = ["h18", "h19", "h20", "h21", "h22", "h23", "h00", "h01", "h02", "h03", "h04", "h05", "h06", "h07", "h08"]
DAY = ["h09", "h10", "h11", "h12", "h13", "h14", "h15"]
MED_N, THR_N, Q = 20, 250, 0.90                    # trailing medians for the score; trailing window and quantile for the causal threshold
MACD_FAST, MACD_SLOW, MACD_SIG = 12, 26, 9         # D484 §3 B2, canonical, not tuned
ACCOUNT, P3_LIMIT = 50_000.0, 1_000.0              # P3's bar is a loss beyond 2% of the account


# ------------------------------------------------------------------------------------------ signal helpers (D484's definitions)
def ema(x, n):
    a = 2.0 / (n + 1.0); out = np.full(len(x), np.nan); s = np.nan
    for i, v in enumerate(x):
        if not np.isfinite(v):
            continue
        s = v if not np.isfinite(s) else s + a * (v - s); out[i] = s
    return out


def macd_hist(logc):
    m = ema(logc, MACD_FAST) - ema(logc, MACD_SLOW); return m - ema(m, MACD_SIG)


# ------------------------------------------------------------------------------------------ data
def load_root(T, root):
    t = T[(T["root"] == root) & T["same_front"].astype(bool) & (T["day"] >= START) & (T["day"] <= END)].sort_values("day").reset_index(drop=True)
    assert len(t) and t["day"].max() <= END, "a session past the in-sample end reached the measurement"
    mult = MULT[root]; O = t["h09_o"].to_numpy(float); C = t["h15_c"].to_numpy(float)
    dh = t[[f"{s}_h" for s in DAY]].to_numpy(float); dl = t[[f"{s}_l" for s in DAY]].to_numpy(float)
    nh = t[[f"{s}_h" for s in NIGHT]].to_numpy(float); nl = t[[f"{s}_l" for s in NIGHT]].to_numpy(float); nv = t[[f"{s}_v" for s in NIGHT]].to_numpy(float)
    with np.errstate(invalid="ignore"):
        M = (C - O) * mult
        DR = (np.nanmax(dh, axis=1) - np.nanmin(dl, axis=1)) * mult
        NR = (np.nanmax(nh, axis=1) - np.nanmin(nl, axis=1)) * mult
    NV = np.nansum(nv, axis=1)
    return dict(days=t["day"].to_numpy(), O=O, C=C, M=M, DR=DR, NR=NR, NV=NV, root=root)


def build(d):
    """The causal in-play score, its causal threshold, the two signals, and every mask the study reads."""
    NR, NV, C = d["NR"], d["NV"], d["C"]
    mr = pd.Series(NR).rolling(MED_N, min_periods=MED_N).median().shift(1).to_numpy()
    mv = pd.Series(NV).rolling(MED_N, min_periods=MED_N).median().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        rel_r = NR / mr; rel_v = NV / mv; score = np.sqrt(np.clip(rel_r, 0, None) * np.clip(rel_v, 0, None))
    thr = pd.Series(score).rolling(THR_N, min_periods=THR_N).quantile(Q).shift(1).to_numpy()
    med = pd.Series(score).rolling(THR_N, min_periods=THR_N).median().shift(1).to_numpy()
    with np.errstate(invalid="ignore"):
        logc = np.log(np.where(C > 0, C, np.nan))
    s2 = np.concatenate([[np.nan], np.sign(macd_hist(logc))[:-1]])          # the sign at d-1, traded on day d
    s1 = np.ones(len(C))
    usable = np.isfinite(d["M"]) & np.isfinite(score) & np.isfinite(thr) & np.isfinite(med)
    return dict(score=score, thr=thr, med=med, sig={"S1": s1, "S2": s2}, usable=usable,
                in_play=usable & (score >= thr), rest=usable & (score < thr), low=usable & (score < med))


# ------------------------------------------------------------------------------------------ the statistic
def T_stat(M, sig, mask, fee):
    """T = (2p - 1) - fee/E|M| on the masked sessions. p counts a zero move as neither, and zero-signal sessions are excluded."""
    m = mask & np.isfinite(M) & np.isfinite(sig) & (sig != 0)
    n = int(m.sum())
    if n < 20:
        return dict(n=n)
    x = sig[m] * M[m]; aM = np.abs(M[m]); nz = M[m] != 0
    p = float((x[nz] > 0).mean()) if nz.any() else float("nan"); e = float(aM.mean())
    return dict(n=n, p=p, e_absM=e, fee_share=fee / e, T=(2 * p - 1) - fee / e, gross=float(x.mean()), net=float(x.mean() - fee),
                median=float(np.median(x)), sigma=float(x.std(ddof=1)), n_zero=int((~nz).sum()))


def cell_report(days, M, sig, mask, fee, label):
    m = mask & np.isfinite(M) & np.isfinite(sig) & (sig != 0)
    st = T_stat(M, sig, mask, fee); n = st["n"]
    if n < 20:
        return dict(label=label, **st)
    x = sig[m] * M[m]; dd = days[m]; yrs = np.array([t[:4] for t in dd]); k = max(1, n // 100)
    net_daily = x - fee
    by_year = {y: float(x[yrs == y].mean()) for y in sorted(set(yrs))}
    breach_by_year = {y: int((net_daily[yrs == y] < -P3_LIMIT).sum()) for y in sorted(set(yrs))}
    sig_by_year = {y: float(net_daily[yrs == y].std(ddof=1)) if (yrs == y).sum() > 2 else float("nan") for y in sorted(set(yrs))}
    sh = float(net_daily.mean() / net_daily.std(ddof=1) * math.sqrt(252)) if net_daily.std(ddof=1) > 0 else float("nan")
    st.update(label=label, per_year=n / max(1, len(set(yrs))), trimmed=float(np.sort(x)[k:n - k].mean()), ex_top=float(np.sort(x)[:n - k].mean()),
              ex_bottom=float(np.sort(x)[k:].mean()), hit=float((x > 0).mean()), skew=float(pd.Series(x).skew()), kurt=float(pd.Series(x).kurt()),
              net_sharpe_on_traded=sh, worst=float(net_daily.min()), by_year=by_year, positive_years=int(sum(v > 0 for v in by_year.values())),
              n_years=len(by_year), p3a_per_year=float(sum(breach_by_year.values()) / max(1, len(breach_by_year))), breaches_by_year=breach_by_year,
              sigma_by_year=sig_by_year, worst_share_of_budget=float(-net_daily.min() / (0.04 * ACCOUNT)))
    return st


def delta(M, sig, in_play, rest, fee):
    a = T_stat(M, sig, in_play, fee); b = T_stat(M, sig, rest, fee)
    if a.get("n", 0) < 20 or b.get("n", 0) < 20:
        return float("nan"), a, b
    return a["T"] - b["T"], a, b


# ------------------------------------------------------------------------------------------ nulls
def rotation(M, sig, score, thr, usable, fee, d_max=None):
    """Exact common rotation: the SCORE and its causal threshold are rolled together by k sessions against the outcome pair (M, sig),
    k = 1..T-1, enumerated. What moves is the alignment of the in-play state with the session that follows it."""
    n = len(M); D = n - 1 if d_max is None else min(d_max, n - 1); out = np.full(D, np.nan)
    base = np.isfinite(M) & np.isfinite(sig) & (sig != 0)
    for k in range(1, D + 1):
        sc = np.roll(score, k); th = np.roll(thr, k); us = np.roll(usable, k)
        ip = base & us & (sc >= th); rs = base & us & (sc < th)
        if ip.sum() < 20 or rs.sum() < 20:
            continue
        a = T_stat(M, sig, ip, fee); b = T_stat(M, sig, rs, fee)
        if a.get("n", 0) >= 20 and b.get("n", 0) >= 20:
            out[k - 1] = a["T"] - b["T"]
    return out


def rotation_slow(M, sig, score, thr, usable, fee, k):
    n = len(M); ip = []; rs = []
    for t in range(n):
        u = (t - k) % n
        if not (np.isfinite(M[t]) and np.isfinite(sig[t]) and sig[t] != 0 and usable[u]):
            continue
        (ip if score[u] >= thr[u] else rs).append(t)
    f = lambda idx: ((2 * float((sig[idx] * M[idx] > 0)[M[idx] != 0].mean()) - 1) - fee / float(np.abs(M[idx]).mean()))
    return f(np.array(ip)) - f(np.array(rs))


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D506 stage 1 -- does accuracy survive the in-play filter?\n      spec committed in {SPEC} BEFORE this ran; {START}..{END}; 2024+ NOT read; primary = {PRIMARY_SIG} on {PRIMARY_ROOT}")
    T = pd.read_csv(TABLE, dtype={"root": str, "day": str, "prev_day": str, "contract": str, "front_prev": str}); meta = json.loads(META.read_text())
    assert all(meta["gates"][r]["passes"] for r in ROOTS), "a declared root fails D467's gates"
    res = dict(spec="D506", commit=SPEC, start=START, end=END, roots=ROOTS, primary=dict(root=PRIMARY_ROOT, signal=PRIMARY_SIG), cells={}, deltas={}, controls={}, paths={})
    rows = []
    print(f"\n  {'cell':10s} {'group':9s} {'N':>5s} {'p %':>6s} {'E|M| $':>7s} {'fee%':>5s} {'T':>7s} {'gross$':>7s} {'net$':>7s} {'hit':>5s} {'skew':>6s} {'Sharpe':>7s} {'P3a/yr':>7s} {'worst$':>8s}")
    for root in ROOTS:
        d = load_root(T, root); b = build(d); fee = FEE[root]
        for sg in ("S1", "S2"):
            sig = b["sig"][sg]; key = f"{root}-{sg}"
            ip = cell_report(d["days"], d["M"], sig, b["in_play"], fee, f"{key}:in_play")
            rst = cell_report(d["days"], d["M"], sig, b["rest"], fee, f"{key}:rest")
            allc = cell_report(d["days"], d["M"], sig, b["usable"], fee, f"{key}:all")
            dl = ip["T"] - rst["T"] if ip.get("n", 0) >= 20 and rst.get("n", 0) >= 20 else float("nan")
            res["cells"][key] = dict(in_play=ip, rest=rst, all=allc); res["deltas"][key] = dl
            for nm, st in (("in_play", ip), ("rest", rst), ("all", allc)):
                if st.get("n", 0) >= 20:
                    print(f"  {key:10s} {nm:9s} {st['n']:5d} {100*st['p']:6.2f} {st['e_absM']:7.0f} {100*st['fee_share']:5.2f} {st['T']:+7.4f} {st['gross']:+7.2f} {st['net']:+7.2f} {100*st['hit']:4.1f}% {st['skew']:+6.2f} {st['net_sharpe_on_traded']:+7.2f} {st['p3a_per_year']:7.2f} {st['worst']:+8.0f}")
                    rows.append(dict(root=root, signal=sg, group=nm, **{k: v for k, v in st.items() if not isinstance(v, dict)}))
            print(f"  {key:10s} {'DELTA':9s} {dl:+.4f}" + (f"   (p {100*(ip['p']-rst['p']):+.2f} pts, fee term {100*(rst['fee_share']-ip['fee_share']):+.2f} pts)" if np.isfinite(dl) else ""))
            res["paths"][key] = rotation(d["M"], sig, b["score"], b["thr"], b["usable"], fee)
        # controls, on the primary signal of every root
        sig = b["sig"][PRIMARY_SIG]; DRq = np.nanquantile(d["DR"][b["usable"]], 0.9)
        top_dr = b["usable"] & (d["DR"] >= DRq)
        v_hi = cell_report(d["days"], d["M"], sig, top_dr & (b["score"] >= b["thr"]), fee, "V-high")
        v_lo = cell_report(d["days"], d["M"], sig, top_dr & b["low"], fee, "V-low")
        w_sc = np.concatenate([[np.nan], b["score"][:-1]]); w_th = np.concatenate([[np.nan], b["thr"][:-1]])
        w_ip = b["usable"] & np.isfinite(w_sc) & (w_sc >= w_th); w_rs = b["usable"] & np.isfinite(w_sc) & (w_sc < w_th)
        w = (T_stat(d["M"], sig, w_ip, fee), T_stat(d["M"], sig, w_rs, fee))
        u = (T_stat(d["M"], sig, top_dr, fee), T_stat(d["M"], sig, b["usable"] & (d["DR"] < DRq), fee))
        res["controls"][root] = dict(V=dict(high=v_hi, low=v_lo, diff=(v_hi["T"] - v_lo["T"]) if v_hi.get("n", 0) >= 20 and v_lo.get("n", 0) >= 20 else float("nan")),
                                     W=dict(high=w[0], low=w[1], diff=(w[0]["T"] - w[1]["T"]) if w[0].get("n", 0) >= 20 and w[1].get("n", 0) >= 20 else float("nan")),
                                     U=dict(high=u[0], low=u[1], diff=(u[0]["T"] - u[1]["T"]) if u[0].get("n", 0) >= 20 and u[1].get("n", 0) >= 20 else float("nan")))
    # N2 family maximum
    D = min(len(v) for v in res["paths"].values()); Mx = np.column_stack([np.asarray(v[:D], float) for v in res["paths"].values()])
    fam = np.nanmax(Mx, axis=1); fam = fam[np.isfinite(fam)]
    obs = {k: v for k, v in res["deltas"].items() if np.isfinite(v)}; best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(res["paths"]), n_offsets=int(len(fam)), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)), p99=float(np.quantile(fam, .99)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    f = res["family"]
    print(f"\n  N2 FAMILY MAXIMUM over {f['n_cells']} cells, {f['n_offsets']:,} common offsets (exact): p50 {f['p50']:+.4f}  p95 {f['p95']:+.4f}  p99 {f['p99']:+.4f}   observed max {f['observed_max']:+.4f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    pk = f"{PRIMARY_ROOT}-{PRIMARY_SIG}"; path = np.asarray(res["paths"][pk], float); path = path[np.isfinite(path)]
    res["n1"] = dict(p50=float(np.median(path)), p95=float(np.quantile(path, .95)), share_ge=float((path >= res["deltas"][pk]).mean()), n_offsets=int(len(path)))
    print(f"  N1 on the primary {pk}: observed {res['deltas'][pk]:+.4f}  p50 {res['n1']['p50']:+.4f}  p95 {res['n1']['p95']:+.4f}  share of offsets >= observed {100*res['n1']['share_ge']:.1f}%")
    print("\n  CONTROLS (T difference; V is the decider):")
    for root in ROOTS:
        c = res["controls"][root]; print(f"    {root:3s}  V {c['V']['diff']:+.4f} (n {c['V']['high'].get('n', 0)}/{c['V']['low'].get('n', 0)})   W {c['W']['diff']:+.4f}   U {c['U']['diff']:+.4f}")
    # decision
    p = res["cells"][pk]; dl = res["deltas"][pk]; V = res["controls"][PRIMARY_ROOT]["V"]["diff"]
    ok_fam = bool(dl > f["p95"]); ok_v = bool(np.isfinite(V) and np.sign(V) == np.sign(dl) and abs(V) >= 0.5 * abs(dl))
    ok_ca = bool(p["in_play"].get("net_sharpe_on_traded", -9) > 0.5); ok_p3 = bool(p["in_play"].get("p3a_per_year", 9) <= 1.0)
    verdict = "PROCEED" if (ok_fam and ok_v and ok_ca and ok_p3) else ("PICK" if (dl > res["n1"]["p95"] and ok_v) else "CLOSE")
    res["verdict"] = verdict; res["decision_terms"] = dict(family=ok_fam, control_V=ok_v, C_a=ok_ca, P3a=ok_p3)
    print(f"\n  VERDICT (pre-registered rule): {verdict}   terms {res['decision_terms']}")
    # sigma per year and as a share of the index level, since 2024+ is not read
    print("\n  sigma of the traded day move, per year, at one micro (D503's lesson: a pooled figure is a price-level artefact):")
    for root in ROOTS:
        s = res["cells"][f"{root}-S1"]["all"]["sigma_by_year"]; print(f"    {root:3s} " + " ".join(f"{y}:{v:.0f}" for y, v in s.items()))
    print("\nPREDICTIONS")
    ip, rst = p["in_play"], p["rest"]
    print(f"  X-a |dp| < 1.5 pts on the primary and Delta in [+0.005, +0.020]                    : dp {100*(ip['p']-rst['p']):+.2f} pts; Delta {dl:+.4f}")
    print(f"  X-b Delta does not clear the N2 family p95, which lands in [+0.020, +0.045]        : p95 {f['p95']:+.4f}; clears {ok_fam}")
    print(f"  X-c control V is near zero (|diff| < 0.010) on the primary                          : V {V:+.4f}")
    print(f"  X-d the untradeable bound U is at least +0.03 on the primary                        : U {res['controls'][PRIMARY_ROOT]['U']['diff']:+.4f}")
    s1p = {r: res['cells'][f'{r}-S1']['all']['p'] for r in ROOTS}; s2p = {r: res['cells'][f'{r}-S2']['all']['p'] for r in ROOTS}
    print(f"  X-e S1 p in [50, 53]% and S2 p in [50, 52]% on the index roots; none reaches 53.6%  : S1 " + " ".join(f"{r} {100*s1p[r]:.1f}" for r in ("ES", "NQ", "YM")) + "  S2 " + " ".join(f"{r} {100*s2p[r]:.1f}" for r in ("ES", "NQ", "YM")))
    print(f"  X-f P3a higher per traded session but lower per year on the in-play cell            : in play {ip['p3a_per_year']:.2f}/yr vs all {p['all']['p3a_per_year']:.2f}/yr")
    print(f"  X-g the verdict is CLOSE                                                            : {verdict}")
    res["paths"] = {k: None for k in res["paths"]}
    OUT.write_text(json.dumps(res, indent=1, default=float)); pd.DataFrame(rows).to_csv(CELLS, index=False, compression="gzip", float_format="%.5f")
    print(f"\nwrote {OUT.relative_to(REPO)} and {CELLS.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def synth(n=1400, seed=7, acc_boost=0.0, size_boost=1.0):
    """Sessions with a controllable in-play state. `size_boost` scales the day move on in-play sessions (the fee-dilution channel);
    `acc_boost` adds directional accuracy to S2 there (the channel the study is testing)."""
    rng = np.random.default_rng(seed); days = np.array([str(x.date()) for x in pd.bdate_range("2016-01-04", periods=n)])
    state = rng.random(n) < 0.12
    NR = np.exp(rng.normal(0, .3, n)) * np.where(state, 2.2, 1.0) * 100
    NV = np.exp(rng.normal(0, .3, n)) * np.where(state, 2.2, 1.0) * 1000
    scale = np.where(state, size_boost, 1.0) * 40.0
    drift = np.where(state, acc_boost, 0.0)
    M = rng.normal(0, 1, n) * scale + drift * scale
    C = 100 + np.cumsum(rng.normal(0, .5, n)); O = C - M / 10.0
    DR = np.abs(M) * 1.6 + np.abs(rng.normal(0, 5, n))
    return dict(days=days, O=O, C=C, M=M, DR=DR, NR=NR, NV=NV, root="YM"), state


def cmd_selftest():
    print("D506 selftest")
    d, state = synth(); b = build(d)
    # [A] causality: the score, its threshold and the MACD sign never read day d's own day session
    d2 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}
    t0 = 900; rng = np.random.default_rng(3); d2["M"][t0:] = rng.normal(0, 500, len(d2["M"]) - t0); d2["O"][t0:] += 50
    b2 = build(d2); assert np.array_equal(np.nan_to_num(b["score"]), np.nan_to_num(b2["score"])), "the score read the day session"
    assert np.array_equal(np.nan_to_num(b["thr"]), np.nan_to_num(b2["thr"]))
    d3 = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in d.items()}; d3["C"] = d3["C"] * 1.0; d3["C"][500] *= 1.5
    b3 = build(d3); assert np.array_equal(np.nan_to_num(b["sig"]["S2"][:501]), np.nan_to_num(b3["sig"]["S2"][:501])), "S2 at d must not read C(d)"
    assert not np.array_equal(np.nan_to_num(b["sig"]["S2"][501:]), np.nan_to_num(b3["sig"]["S2"][501:])), "S2 must react to a later close"
    # [B] the in-play mask fires on about a decile, never before the warm-up, and recovers the planted state
    assert not b["in_play"][:THR_N].any(); share = b["in_play"][b["usable"]].mean(); assert 0.05 < share < 0.18, share
    assert (state[b["in_play"]].mean() > 0.8), state[b["in_play"]].mean()
    # [C] sign audit in money, and the inverted break
    M, fee = d["M"], FEE["YM"]; st = T_stat(M, np.ones(len(M)), b["usable"], fee)
    assert abs(st["gross"] - M[b["usable"]].mean()) < 1e-9
    flip = T_stat(M, -np.ones(len(M)), b["usable"], fee); assert abs(flip["gross"] + st["gross"]) < 1e-9, "flipping the signal must flip the book"
    assert abs((2 * st["p"] - 1) - (1 - 2 * flip["p"])) < 1e-9, "p must invert with the signal"
    # [D] T responds to the fee term alone when size rises and accuracy does not
    dz, _ = synth(n=5000, acc_boost=0.0, size_boost=3.0); bz = build(dz)          # n large enough that "accuracy unchanged" is tested with power
    dl, a, r = delta(dz["M"], np.ones(len(dz["M"])), bz["in_play"], bz["rest"], fee)
    assert a["fee_share"] < 0.5 * r["fee_share"], (a["fee_share"], r["fee_share"])
    assert abs((2 * a["p"] - 1) - (2 * r["p"] - 1)) < 0.08, "accuracy must be unchanged in this synthetic"
    assert dl > 0, dl
    # [E] and it responds to accuracy when that is what is planted
    da, _ = synth(acc_boost=0.6, size_boost=1.0); ba = build(da)
    dla, aa, ra = delta(da["M"], np.ones(len(da["M"])), ba["in_play"], ba["rest"], fee)
    assert aa["p"] - ra["p"] > 0.15, (aa["p"], ra["p"]); assert dla > 0.25, dla
    # [F] exact rotation against an explicit loop, and a null that is centred near zero on the unplanted case
    dn, _ = synth(acc_boost=0.0, size_boost=1.0); bn = build(dn); sg = np.ones(len(dn["M"]))
    path = rotation(dn["M"], sg, bn["score"], bn["thr"], bn["usable"], fee, d_max=40)
    for k in (1, 11, 29):
        slow = rotation_slow(dn["M"], sg, bn["score"], bn["thr"], bn["usable"], fee, k)
        assert abs(slow - path[k - 1]) < 1e-9, (k, slow, path[k - 1])
    full = rotation(dn["M"], sg, bn["score"], bn["thr"], bn["usable"], fee); full = full[np.isfinite(full)]
    assert abs(np.median(full)) < 0.05, float(np.median(full))
    # the null must be CALIBRATED, not merely uncleared on one draw: an unplanted observation lands in its own top 5% exactly 5% of the time,
    # so a single-seed assertion would be flaky by construction. Five seeds, and the typical draw must be unremarkable.
    shares = []
    for sd in (11, 12, 13, 14, 15):
        ds, _ = synth(seed=sd, acc_boost=0.0, size_boost=1.0); bs = build(ds); s1 = np.ones(len(ds["M"]))
        pth = rotation(ds["M"], s1, bs["score"], bs["thr"], bs["usable"], fee); pth = pth[np.isfinite(pth)]
        ob, _, _ = delta(ds["M"], s1, bs["in_play"], bs["rest"], fee); shares.append(float((pth >= ob).mean()))
    assert np.median(shares) > 0.15, shares
    assert sum(s < 0.05 for s in shares) <= 1, shares
    # [G] the planted accuracy case DOES clear its own null -- the check can fire
    fp = rotation(da["M"], np.ones(len(da["M"])), ba["score"], ba["thr"], ba["usable"], fee); fp = fp[np.isfinite(fp)]
    assert (fp >= dla).mean() < 0.05, float((fp >= dla).mean())
    # [H] P3a counts breaches per year, not in total
    rep = cell_report(dn["days"], dn["M"] * 20, np.ones(len(dn["M"])), bn["usable"], fee, "x")
    assert rep["p3a_per_year"] == sum(rep["breaches_by_year"].values()) / len(rep["breaches_by_year"]) and rep["p3a_per_year"] > 0
    print(f"  A causality (score, threshold, MACD lag)  B mask fires on {100*share:.1f}% and recovers the state  C sign audit and its flip"
          f"  D fee channel only (Delta {dl:+.4f}, p unchanged)  E accuracy channel (Delta {dla:+.4f}, dp {100*(aa['p']-ra['p']):+.1f} pts)"
          f"  F exact rotation, unplanted null centred at {np.median(full):+.4f}, calibrated over 5 seeds (shares {[round(s,2) for s in shares]})  G planted null IS cleared  H P3a is a rate\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
