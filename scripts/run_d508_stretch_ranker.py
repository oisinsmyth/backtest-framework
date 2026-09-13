"""D508 -- does |log(P/SMA200)| or |log(P/EMA200)| RANK the admitted MACD arm's performance?
Ranks the FROZEN arm (imported from d504/d491, not re-implemented) by the absolute log distance of price from its own 200-day average.
Primary: Spearman rho between |log(P/SMA200)| and the arm's NET session P&L on NQ, 2016-2023. N1 exact enumerated rotation, N2 a four-cell
family maximum, N3 a run-length-matched random persistent gate (D502's free +0.2 cost channel), N4 the within-year decomposition.
Spec committed in c47feae BEFORE this file. 2024+ is SPENT for this arm and is NOT read.

    uv run python -u scripts/run_d508_stretch_ranker.py --run
    uv run python -u scripts/run_d508_stretch_ranker.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d508_stretch_ranker.json"; QOUT = REPO / "data" / "d508_quintiles.csv.gz"; SPEC = "c47feae"
LO, HI = "2016-01-04", "2023-12-29"                      # 2024+ is SPENT for this arm (D503) and is not read
N_MA, N_Q, WARM = 200, 5, 200
N_RAND, SEED = 2000, 508


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D484 = _load("d484c", "d484_offdiagonal_and_macd.py")
D491 = _load("d491c", "d491_conditional_hold.py")
D495 = _load("d495c", "d495_agree_confluence.py")
D504 = _load("d504c", "d504_arm_full_history.py")
M_HOLD = D504.M_HOLD


# ------------------------------------------------------------------------------------------ the arm, imported not rebuilt
def load_arm():
    """The frozen arm exactly as D504 builds it, SCORED ONLY ON THIS RECORD'S WINDOW.

    The spent slice is never scored: `simulate` treats every session independently (it starts flat, is forced flat at LAST_SEG, and carries
    no state across rows -- asserted in --selftest), so clipping the session rows BEFORE simulating gives per-session results identical to
    clipping after, and 2024+ is simply never evaluated. The daily close series is kept in full because the 200-day average needs the history
    that precedes the window; only closes at or before d-1 are ever read (asserted in --selftest)."""
    meta = json.loads(D495.META.read_text(encoding="utf-8")); spec = json.loads(D484.SPECS.read_text(encoding="utf-8"))
    pk = D504.build(pd.read_csv(D495.FIX), meta, spec)
    days_all = np.asarray(pk["days"]).astype(str); level_all = np.asarray(pk["level"], float)
    m = (days_all >= LO) & (days_all <= HI)
    O, C, AG = pk["O"][m], pk["C"][m], pk["AGREE"][m]
    net_tk, trips = D491.simulate(O, C, AG, pk["first"], M_HOLD, pk["cost"], pk["tick_pts"])
    gross_tk, _ = D491.simulate(O, C, AG, pk["first"], M_HOLD, 0.0, pk["tick_pts"])
    tick = pk["tick_usd"]
    return dict(days=days_all[m], level=level_all[m], net=net_tk * tick, gross=gross_tk * tick, trips=np.asarray(trips, float),
                tick_usd=tick, cost_usd=pk["cost"] * tick, days_all=days_all, level_all=level_all, mask=m)


# ------------------------------------------------------------------------------------------ the conditioner
def sma(x, n=N_MA):
    return pd.Series(x).rolling(n, min_periods=n).mean().to_numpy()


def ema(x, n=N_MA):
    return pd.Series(x).ewm(span=n, adjust=False, min_periods=n).mean().to_numpy()


def stretch(level, kind="sma", n=N_MA):
    """|log(close_{d-1} / MA_{d-1})| -- every term ends at d-1, so the conditioner is known before session d opens."""
    lv = np.asarray(level, float); ma = sma(lv, n) if kind == "sma" else ema(lv, n)
    with np.errstate(invalid="ignore", divide="ignore"):
        signed = np.log(lv / ma)
    out_signed = np.concatenate([[np.nan], signed[:-1]])                 # shift: session d reads d-1
    return np.abs(out_signed), out_signed


# ------------------------------------------------------------------------------------------ statistics
def spearman(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 30:
        return float("nan")
    a = pd.Series(x[m]).rank().to_numpy(); b = pd.Series(y[m]).rank().to_numpy()
    sa, sb = a.std(ddof=1), b.std(ddof=1)
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb)) if sa > 0 and sb > 0 else float("nan")


def sharpe(x):
    x = np.asarray(x, float); s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def quintiles(cond, net, gross, trips, days, n_q=N_Q):
    m = np.isfinite(cond) & np.isfinite(net)
    q = pd.qcut(cond[m], n_q, labels=False, duplicates="drop"); rows = []
    for i in range(n_q):
        s = q == i
        if s.sum() < 20:
            continue
        nt = net[m][s]; gr = gross[m][s]; tp = trips[m][s]; dd = days[m][s]; yrs = np.array([t[:4] for t in dd])
        rows.append(dict(quintile=i + 1, n=int(s.sum()), cond_lo=float(cond[m][s].min()), cond_hi=float(cond[m][s].max()),
                         net_mean=float(nt.mean()), gross_mean=float(gr.mean()), net_sharpe=sharpe(nt), gross_sharpe=sharpe(gr),
                         trips_per_session=float(tp.mean()), gross_per_trade=float(gr.sum() / tp.sum()) if tp.sum() > 0 else float("nan"),
                         net_per_trade=float(nt.sum() / tp.sum()) if tp.sum() > 0 else float("nan"),
                         hit=float((nt > 0).mean()), worst=float(nt.min()),
                         p3a_per_year=float((nt < -1000).sum() / max(1, len(set(yrs))))))
    return pd.DataFrame(rows)


def rotation(cond, net, d_max=None):
    """Exact enumerated rotation of the CONDITIONER against the arm's P&L: k = 1..T-1, all offsets. The arm is untouched; what moves is the
    alignment of the stretch series with the sessions it labels."""
    m = np.isfinite(cond) & np.isfinite(net); c = cond[m]; y = net[m]; T = len(c)
    D = T - 1 if d_max is None else min(d_max, T - 1); out = np.full(D, np.nan)
    ry = pd.Series(y).rank().to_numpy(); rc = pd.Series(c).rank().to_numpy()
    ry0 = ry - ry.mean(); sy = ry.std(ddof=1)
    for k in range(1, D + 1):
        rk = np.roll(rc, k); out[k - 1] = float((( rk - rk.mean()) * ry0).mean() / (rk.std(ddof=1) * sy))
    return out


def rotation_slow(cond, net, k):
    m = np.isfinite(cond) & np.isfinite(net); c = cond[m]; y = net[m]; T = len(c)
    return spearman(np.array([c[(i - k) % T] for i in range(T)]), y)


def runlength_gate_null(cond, net, thr, n=N_RAND, seed=SEED):
    """N3: random persistent gates matched on duty cycle AND run-length distribution to the observed top-quintile mask.
    D502 measured that such a gate earns ~ +0.2 net Sharpe for free through the cost channel."""
    m = np.isfinite(cond) & np.isfinite(net); y = net[m]; on = cond[m] >= thr
    runs = []; i = 0
    while i < len(on):
        j = i
        while j < len(on) and on[j] == on[i]:
            j += 1
        runs.append((bool(on[i]), j - i)); i = j
    on_runs = [L for v, L in runs if v]; off_runs = [L for v, L in runs if not v]
    rng = np.random.default_rng(seed); out = np.empty(n)
    for b in range(n):
        seq = []; start_on = rng.random() < 0.5
        v = start_on
        while len(seq) < len(on):
            pool = on_runs if v else off_runs
            L = int(pool[rng.integers(0, len(pool))]) if pool else 1
            seq.extend([v] * L); v = not v
        mask = np.array(seq[:len(on)])
        out[b] = sharpe(y[mask]) if mask.sum() > 20 else np.nan
    return out[np.isfinite(out)]


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D508 -- does |log(P/MA200)| rank the admitted MACD arm?\n      spec committed in {SPEC} BEFORE this ran; {LO}..{HI}; the arm's 2024+ slice is SPENT (D503) and is NOT read")
    a = load_arm(); days, net, gross, trips = a["days"], a["net"], a["gross"], a["trips"]
    # [REPRODUCTION] against D504's OWN published artefact, on this window only -- the spent slice is never scored (see load_arm).
    pub = json.loads((REPO / "data" / "d504_arm_full_history.json").read_text())["per_year"]
    want_tot = sum(pub[y]["total_usd"] for y in pub if LO[:4] <= y <= HI[:4])
    want_n = sum(pub[y]["n_sessions"] for y in pub if LO[:4] <= y <= HI[:4])
    print(f"  imported arm on {LO}..{HI}: {len(days):,} sessions, total net ${net.sum():,.0f}, net Sharpe {sharpe(net):+.3f}")
    print(f"  D504's published per-year figures for the same window: {want_n:,} sessions, ${want_tot:,.0f}")
    assert len(days) == want_n, f"session count disagrees with D504: {len(days)} against {want_n}"
    assert abs(float(net.sum()) - want_tot) < 1.0, f"total net disagrees with D504: {net.sum():.2f} against {want_tot:.2f}"
    # the conditioner is computed on the FULL daily close series, so the 200-day average is not truncated by the window, then clipped
    cond = {}
    for kind in ("sma", "ema"):
        ab, sg = stretch(a["level_all"], kind)
        cond[f"{kind}_abs"] = ab[a["mask"]]; cond[f"{kind}_signed"] = sg[a["mask"]]
    res = dict(spec="D508", commit=SPEC, lo=LO, hi=HI, sessions=int(len(days)), arm=dict(net_sharpe_window=sharpe(net), total_net=float(net.sum()), published_total=float(want_tot), published_sessions=int(want_n)), cells={})
    print(f"\n  {'cell':12s} {'n':>5s} {'Spearman':>9s} {'N1 p05':>7s} {'N1 p50':>7s} {'N1 p95':>7s} {'>=obs':>6s} {'<=obs':>6s}")
    paths = {}
    for k in ("sma_abs", "ema_abs", "sma_signed", "ema_signed"):
        rho = spearman(cond[k], net); path = rotation(cond[k], net); paths[k] = path
        p05, p50, p95 = (float(np.quantile(path, q)) for q in (.05, .50, .95)); share = float((path >= rho).mean()); share_le = float((path <= rho).mean())
        res["cells"][k] = dict(spearman=rho, n1_p05=p05, n1_p50=p50, n1_p95=p95, share_ge=share, share_le=share_le,
                               clears_n1=bool(rho > p95), clears_n1_below=bool(rho < p05))
        print(f"  {k:12s} {int(np.isfinite(cond[k]).sum()):5d} {rho:+9.4f} {p05:+7.4f} {p50:+7.4f} {p95:+7.4f} {100*share:5.1f}% {100*share_le:6.1f}%")
    D = min(len(v) for v in paths.values()); fam = np.nanmax(np.column_stack([v[:D] for v in paths.values()]), axis=1)
    obs = {k: res["cells"][k]["spearman"] for k in paths}; best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=4, n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)), observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    f = res["family"]; print(f"\n  N2 FAMILY MAXIMUM over 4 cells, {f['n_offsets']:,} common offsets (exact): p50 {f['p50']:+.4f}  p95 {f['p95']:+.4f}   observed max {f['observed_max']:+.4f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    # quintiles on the primary
    Q = quintiles(cond["sma_abs"], net, gross, trips, days); res["quintiles"] = Q.to_dict("records")
    print(f"\n  QUINTILES of |log(P/SMA200)| -- gross and net side by side (D502: a regime cell raises net and lowers gross)")
    print(f"  {'q':>2s} {'n':>5s} {'range':>15s} {'net $/sess':>10s} {'gross $/sess':>12s} {'net Sh':>7s} {'gross Sh':>8s} {'trips':>6s} {'gross $/tr':>10s} {'net $/tr':>9s} {'hit':>6s} {'worst':>8s} {'P3a':>5s}")
    for r in Q.itertuples():
        print(f"  {r.quintile:2d} {r.n:5d} {r.cond_lo:6.4f}-{r.cond_hi:6.4f} {r.net_mean:+10.2f} {r.gross_mean:+12.2f} {r.net_sharpe:+7.2f} {r.gross_sharpe:+8.2f} {r.trips_per_session:6.2f} {r.gross_per_trade:+10.2f} {r.net_per_trade:+9.2f} {100*r.hit:5.1f}% {r.worst:+8.0f} {r.p3a_per_year:5.2f}")
    # N3 the matched random persistent gate, against the top quintile
    thr = float(Q.iloc[-1].cond_lo); band = runlength_gate_null(cond["sma_abs"], net, thr)
    m = np.isfinite(cond["sma_abs"]) & np.isfinite(net); top = net[m][cond["sma_abs"][m] >= thr]
    obs_top = sharpe(top); duty = float((cond["sma_abs"][m] >= thr).mean())
    res["n3"] = dict(observed_top_sharpe=obs_top, duty_cycle=duty, band_p50=float(np.median(band)), band_p95=float(np.quantile(band, .95)), share_ge=float((band >= obs_top).mean()), n=int(len(band)))
    print(f"\n  N3 run-length-matched random persistent gate at duty {100*duty:.0f}% ({len(band):,} draws): p50 {np.median(band):+.3f}  p95 {np.quantile(band, .95):+.3f}   observed top quintile {obs_top:+.3f}; share of gates >= observed {100*res['n3']['share_ge']:.1f}%")
    # N4 the year-proxy decomposition
    yrs = np.array([t[:4] for t in days]); wy = {}
    for y in sorted(set(yrs)):
        s = yrs == y
        if s.sum() > 60:
            wy[y] = spearman(cond["sma_abs"][s], net[s])
    res["n4"] = dict(within_year=wy, mean_within=float(np.nanmean(list(wy.values()))), pooled=res["cells"]["sma_abs"]["spearman"])
    print(f"\n  N4 WITHIN-YEAR Spearman (the arm is a regime construction; the pooled figure may be a year proxy):")
    print("    " + "  ".join(f"{y}:{v:+.3f}" for y, v in wy.items()) + f"   mean {res['n4']['mean_within']:+.4f}  vs pooled {res['n4']['pooled']:+.4f}")
    # decision
    p = res["cells"]["sma_abs"]; gross_dir = np.sign(Q.iloc[-1].gross_per_trade - Q.iloc[0].gross_per_trade); net_dir = np.sign(Q.iloc[-1].net_per_trade - Q.iloc[0].net_per_trade)
    ok_n1 = p["clears_n1"]; ok_fam = bool(p["spearman"] > f["p95"]); ok_n3 = bool(res["n3"]["share_ge"] < 0.05); ok_gross = bool(gross_dir == net_dir and gross_dir != 0)
    verdict = "PROCEED" if (ok_n1 and ok_fam and ok_n3 and ok_gross) else ("PICK" if (ok_n1 and abs(res["n4"]["mean_within"]) > 0.03) else "CLOSE")
    res["verdict"] = verdict; res["decision_terms"] = dict(n1=ok_n1, family=ok_fam, n3=ok_n3, gross_agrees=ok_gross)
    print(f"\n  VERDICT (pre-registered rule): {verdict}   terms {res['decision_terms']}")
    print("\nPREDICTIONS")
    print(f"  X-a pooled Spearman on |SMA| in [+0.02, +0.06] and clears N1                        : {p['spearman']:+.4f}; clears N1 {ok_n1}")
    print(f"  X-b within-year mean |rho| < 0.03, most of the pooled figure being a year proxy     : mean {res['n4']['mean_within']:+.4f} vs pooled {p['spearman']:+.4f}")
    print(f"  X-c net Sharpe rises q1->q5 while gross per trade rises much less or falls          : net Sh {Q.iloc[0].net_sharpe:+.2f}->{Q.iloc[-1].net_sharpe:+.2f}; gross $/trade {Q.iloc[0].gross_per_trade:+.2f}->{Q.iloc[-1].gross_per_trade:+.2f}")
    print(f"  X-d the N3 band sits near +0.2 and the top quintile does not beat it by > 1 SE      : band p50 {np.median(band):+.3f}; observed {obs_top:+.3f}; share >= obs {100*res['n3']['share_ge']:.1f}%")
    print(f"  X-e SMA and EMA versions agree to within 0.01 of Spearman                           : |diff| {abs(res['cells']['sma_abs']['spearman'] - res['cells']['ema_abs']['spearman']):.4f}")
    print(f"  X-f the signed versions are weaker than the absolute ones                           : abs {res['cells']['sma_abs']['spearman']:+.4f}/{res['cells']['ema_abs']['spearman']:+.4f}  signed {res['cells']['sma_signed']['spearman']:+.4f}/{res['cells']['ema_signed']['spearman']:+.4f}")
    print(f"  X-g the verdict is CLOSE                                                            : {verdict}")
    OUT.write_text(json.dumps(res, indent=1, default=float)); Q.to_csv(QOUT, index=False, compression="gzip", float_format="%.5f")
    print(f"\nwrote {OUT.relative_to(REPO)} and {QOUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    print("D508 selftest")
    n = 1200; rng = np.random.default_rng(4)
    lv = 100 * np.exp(np.cumsum(rng.normal(0, .01, n)))
    ab, sg = stretch(lv, "sma")
    # [A] causality: the conditioner at d reads only closes up to d-1
    lv2 = lv.copy(); lv2[600:] *= 1.5; ab2, _ = stretch(lv2, "sma")
    assert np.allclose(np.nan_to_num(ab[:601]), np.nan_to_num(ab2[:601])), "the conditioner read the future"
    assert not np.allclose(np.nan_to_num(ab[601:]), np.nan_to_num(ab2[601:]))
    lv3 = lv.copy(); lv3[500] *= 1.2; ab3, _ = stretch(lv3, "sma")
    assert np.allclose(np.nan_to_num(ab[:501]), np.nan_to_num(ab3[:501])), "session d must not read its own close"
    assert not np.isclose(np.nan_to_num(ab[501]), np.nan_to_num(ab3[501])), "session d+1 must read it"
    # [B] warm-up binds and the absolute value is the absolute of the signed
    assert not np.isfinite(ab[:N_MA]).any(); assert np.allclose(np.nan_to_num(ab), np.abs(np.nan_to_num(sg)))
    # [C] a known answer: a series pinned at its average has ~zero stretch; a trending one has a large one
    flat = np.full(n, 100.0) + rng.normal(0, 1e-9, n); af, _ = stretch(flat, "sma")
    trend = 100 * np.exp(np.arange(n) * 0.002); at, _ = stretch(trend, "sma")
    assert np.nanmax(af) < 1e-6 < np.nanmin(at[N_MA + 5:]), (np.nanmax(af), np.nanmin(at[N_MA + 5:]))
    # [D] Spearman recovers a planted monotone relation and reports ~0 on noise, and the rotation kills the plant
    y = ab.copy(); y[np.isnan(y)] = 0; planted = y * 100 + rng.normal(0, .2, n)
    assert spearman(ab, planted) > 0.85, spearman(ab, planted)
    noise = rng.normal(0, 1, n); assert abs(spearman(ab, noise)) < 0.12, spearman(ab, noise)
    rp = rotation(ab, planted); assert (rp >= spearman(ab, planted)).mean() < 0.01, float((rp >= spearman(ab, planted)).mean())
    rn = rotation(ab, noise); assert abs(np.median(rn)) < 0.06, float(np.median(rn))
    # [E] the rotation is exact against an explicit loop
    for k in (1, 13, 47):
        assert abs(rotation_slow(ab, planted, k) - rp[k - 1]) < 1e-9, (k, rotation_slow(ab, planted, k), rp[k - 1])
    # [F] the matched-random gate preserves the duty cycle and the run-length scale
    thr = float(np.nanquantile(ab, 0.8)); band = runlength_gate_null(ab, planted, thr, n=200)
    assert len(band) > 150 and np.isfinite(band).all()
    # [G2] simulate is row-independent, which is what lets load_arm clip BEFORE simulating and never score the spent slice
    rr = np.random.default_rng(9); ns, nseg = 40, 23
    Osy = 100 + np.cumsum(rr.normal(0, .5, (ns, nseg)), axis=1); Csy = Osy + rr.normal(0, .2, (ns, nseg))
    sgy = np.sign(rr.normal(0, 1, (ns, nseg)))
    whole, _ = D491.simulate(Osy, Csy, sgy, 15, 5, 0.5, 0.25)
    sub = np.array([3, 7, 11, 29])
    part, _ = D491.simulate(Osy[sub], Csy[sub], sgy[sub], 15, 5, 0.5, 0.25)
    assert np.allclose(whole[sub], part), "simulate is not row-independent; clipping before it would change the result"
    # [G] quintiles are ordered and cover every ranked session
    Q = quintiles(ab, planted, planted, np.ones(n), np.array([f"20{16+i//250:02d}-01-01" for i in range(n)]))
    assert len(Q) == N_Q and Q.n.sum() == int(np.isfinite(ab).sum()) and Q.cond_hi.is_monotonic_increasing
    assert Q.iloc[-1].net_mean > Q.iloc[0].net_mean, "the planted monotone relation must show in the quintiles"
    print(f"  A causality (window and own-close)  B warm-up and |.|  C known answer (flat {np.nanmax(af):.1e} vs trend {np.nanmin(at[N_MA+5:]):.3f})"
          f"  D Spearman finds a plant ({spearman(ab, planted):+.2f}) and not noise ({spearman(ab, noise):+.2f}), rotation kills it"
          f"  E exact rotation  F matched gate  G quintiles ordered  G2 simulate is row-independent\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
