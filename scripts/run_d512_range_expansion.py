"""D512 -- the range-expansion ratio log(EMA50(range)/SMA200(range)) as a ranker of the MACD arm, and whether a POINT range measures
volatility or price. Primary: the day-session LOG range (scale-free), scored with D509's economic statistic (top-minus-bottom quintile in
net $/session). Four cells {day-session, 23-hour} x {log range, point range}; the point versions carry a contamination measurement against
log price. Nulls: the exact enumerated rotation (which D509 proved subsumes a matched-persistence gate), a family maximum, and the
within-year decomposition. The arm and the machinery are imported -- nothing is re-implemented. Spec committed in 711bbe3 BEFORE this file.

    uv run python -u scripts/run_d512_range_expansion.py --run
    uv run python -u scripts/run_d512_range_expansion.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d512_range_expansion.json"; SPEC = "711bbe3"


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D508 = _load("d508c", "run_d508_stretch_ranker.py")
D509 = _load("d509c", "run_d509_quintile_primary.py")
D495 = _load("d495c", "d495_agree_confluence.py")
D484 = _load("d484c", "d484_offdiagonal_and_macd.py")
D503 = _load("d503c", "d503_forward_book.py")
D504 = _load("d504c", "d504_arm_full_history.py")
LO, HI, N_Q = D508.LO, D508.HI, D508.N_Q
FAST, SLOW = 50, 200
DAY_SEGS = list(range(D504.DAY_FIRST_DECIDE, D504.LAST_SEG + 1))        # h09..h15, the segments the arm trades


# ------------------------------------------------------------------------------------------ the daily ranges
def segment_hl():
    """Per-session, per-segment highs and lows in price space, on exactly the sessions D504's build() keeps.
    build() returns opens and closes only, so this reshapes the same `series_window` output the same way and applies the same `keep` mask
    -- asserted against build()'s own day count and close matrix in --selftest rather than assumed."""
    meta = json.loads(D495.META.read_text(encoding="utf-8"))
    s = D503.series_window(D504.ROOT, pd.read_csv(D495.FIX), meta, D504.FULL_LO, D504.FULL_HI)
    nseg = len(D484.SEGMENTS); k = len(s["log_close"]) // nseg
    g = lambda a: np.exp(a[:k * nseg]).reshape(k, nseg)                                   # noqa: E731
    pure = s["pure"][:k * nseg].reshape(k, nseg)
    keep = pure[:, D504.DAY_FIRST_DECIDE:D504.LAST_SEG + 1].all(axis=1)
    return g(s["log_high"])[keep], g(s["log_low"])[keep], g(s["log_close"])[keep], s["days"][:k][keep]


def daily_ranges(hi_seg, lo_seg):
    """Per session: the day-session and 23-hour high-low ranges, in POINTS and as a scale-free LOG range log(high/low)."""
    out = {}
    for name, segs in (("day", DAY_SEGS), ("full", list(range(hi_seg.shape[1])))):
        with np.errstate(invalid="ignore"):
            h = np.nanmax(hi_seg[:, segs], axis=1); l = np.nanmin(lo_seg[:, segs], axis=1)
            out[f"{name}_pts"] = h - l
            out[f"{name}_log"] = np.log(np.where((h > 0) & (l > 0), h / l, np.nan))
    return out


def ema(x, span):
    return pd.Series(x).ewm(span=span, adjust=False, min_periods=span).mean().to_numpy()


def sma(x, n):
    return pd.Series(x).rolling(n, min_periods=n).mean().to_numpy()


def expansion(rng, fast=FAST, slow=SLOW):
    """V_d = log( EMA_fast(range) / SMA_slow(range) ), both ending at d-1 so the conditioner is known before session d opens."""
    r = np.asarray(rng, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        v = np.log(ema(r, fast) / sma(r, slow))
    return np.concatenate([[np.nan], v[:-1]])                            # shift: session d reads d-1


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D512 -- the range-expansion ratio as a ranker of the MACD arm\n      spec committed in {SPEC} BEFORE this ran; {LO}..{HI}; the arm's 2024+ slice is SPENT and is not scored")
    hi_seg, lo_seg, cl_seg, seg_days = segment_hl()
    a = D508.load_arm(); days, net, gross, trips = a["days"], a["net"], a["gross"], a["trips"]
    assert len(seg_days) == len(a["days_all"]) and (np.asarray(seg_days).astype(str) == a["days_all"]).all(),         "the reshaped high/low grid does not sit on build()'s own sessions"
    assert np.allclose(cl_seg[:, D504.LAST_SEG], a["level_all"], rtol=1e-12), "the reshaped closes disagree with build()'s level"
    pub = json.loads((REPO / "data" / "d504_arm_full_history.json").read_text())["per_year"]
    want_n = sum(pub[y]["n_sessions"] for y in pub if LO[:4] <= y <= HI[:4]); want_tot = sum(pub[y]["total_usd"] for y in pub if LO[:4] <= y <= HI[:4])
    assert len(days) == want_n and abs(float(net.sum()) - want_tot) < 1.0, "the imported arm does not reproduce D504"
    print(f"  arm reproduced: {len(days):,} sessions, ${net.sum():,.0f} (D504 publishes {want_n:,}, ${want_tot:,.0f})")
    rng = daily_ranges(hi_seg, lo_seg); mask = a["mask"]; logpx = np.log(a["level_all"])
    cells = {f"{w}_{k}": expansion(rng[f"{w}_{k}"]) for w in ("day", "full") for k in ("log", "pts")}
    res = dict(spec="D512", commit=SPEC, lo=LO, hi=HI, sessions=int(len(days)), fast=FAST, slow=SLOW, cells={})
    # N4 contamination, measured on the full series before clipping
    print(f"\n  N4 CONTAMINATION -- correlation of the conditioner with log(price):")
    for k, v in cells.items():
        m = np.isfinite(v) & np.isfinite(logpx); rho = float(np.corrcoef(v[m], logpx[m])[0, 1])
        res.setdefault("contamination", {})[k] = rho
        print(f"     {k:9s} rho(V, log price) {rho:+.3f}")
    print(f"\n  {'cell':10s} {'Delta $':>8s} {'top $':>7s} {'bot $':>7s} {'N1 p05':>7s} {'N1 p50':>7s} {'N1 p95':>7s} {'pct':>6s} {'clears':>7s}")
    paths = {}
    for k, v in cells.items():
        c = v[mask]; d, tm, bm, nt, nb = D509.qdiff(c, net); path = D509.rotation_qdiff(c, net); path = path[np.isfinite(path)]; paths[k] = path
        p05, p50, p95 = (float(np.quantile(path, q)) for q in (.05, .50, .95)); pct = float((path <= d).mean())
        res["cells"][k] = dict(delta=d, top_mean=tm, bot_mean=bm, n_top=nt, n_bot=nb, p05=p05, p50=p50, p95=p95, percentile=pct,
                               clears=bool(d > p95), n_offsets=int(path.size))
        print(f"  {k:10s} {d:+8.2f} {tm:+7.2f} {bm:+7.2f} {p05:+7.2f} {p50:+7.2f} {p95:+7.2f} {100*pct:5.1f}% {str(bool(d > p95)):>7s}")
    D = min(len(v) for v in paths.values()); fam = np.nanmax(np.column_stack([v[:D] for v in paths.values()]), axis=1)
    obs = {k: res["cells"][k]["delta"] for k in paths}; best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(paths), n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    f = res["family"]; print(f"\n  N2 FAMILY MAXIMUM over {f['n_cells']} cells, {f['n_offsets']:,} common offsets (exact): p50 {f['p50']:+.2f}  p95 {f['p95']:+.2f}   observed max {f['observed_max']:+.2f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    # the primary's quintile shape
    prim = cells["day_log"][mask]
    Q = D508.quintiles(prim, net, gross, trips, days); res["quintiles"] = Q.to_dict("records")
    mono = D509.rank_corr_small(Q.quintile.to_numpy(float), Q.net_mean.to_numpy())
    res["monotonicity"] = dict(index_vs_mean=mono)
    print(f"\n  QUINTILE SHAPE of the primary (day-session log range), net $/session: " + "  ".join(f"q{int(r.quintile)} {r.net_mean:+.2f}" for r in Q.itertuples()) + f"   monotonicity {mono:+.2f}")
    print(f"  {'q':>2s} {'n':>5s} {'net $':>8s} {'gross $':>8s} {'net Sh':>7s} {'gross $/tr':>10s} {'trips':>6s} {'hit':>6s} {'worst':>8s} {'P3a':>5s}")
    for r in Q.itertuples():
        print(f"  {r.quintile:2d} {r.n:5d} {r.net_mean:+8.2f} {r.gross_mean:+8.2f} {r.net_sharpe:+7.2f} {r.gross_per_trade:+10.2f} {r.trips_per_session:6.2f} {100*r.hit:5.1f}% {r.worst:+8.0f} {r.p3a_per_year:5.2f}")
    # N3 within-year
    yrs = np.array([t[:4] for t in days]); wy = {}
    for y in sorted(set(yrs)):
        s = yrs == y
        if s.sum() > 100:
            wy[y] = D509.qdiff(prim[s], net[s])[0]
    vals = [v for v in wy.values() if np.isfinite(v)]
    res["n3_within_year"] = dict(by_year=wy, mean=float(np.mean(vals)), n_negative=int(sum(v < 0 for v in vals)), n_years=len(vals))
    print(f"\n  N3 WITHIN-YEAR Delta ($/session): " + "  ".join(f"{y}:{v:+.1f}" for y, v in wy.items()) +
          f"\n     mean {res['n3_within_year']['mean']:+.2f}  negative in {res['n3_within_year']['n_negative']} of {res['n3_within_year']['n_years']}  vs pooled {res['cells']['day_log']['delta']:+.2f}")
    p = res["cells"]["day_log"]
    verdict = "PROCEED" if (p["clears"] and p["delta"] > f["p95"] and res["n3_within_year"]["mean"] > 0) else ("PICK" if p["clears"] else "CLOSE")
    res["verdict"] = verdict; res["decision_terms"] = dict(n1=p["clears"], family=bool(p["delta"] > f["p95"]), within_year=bool(res["n3_within_year"]["mean"] > 0))
    print(f"\n  VERDICT (pre-registered rule): {verdict}   terms {res['decision_terms']}")
    print("\nPREDICTIONS")
    cpt = max(res["contamination"]["day_pts"], res["contamination"]["full_pts"]); clg = max(abs(res["contamination"]["day_log"]), abs(res["contamination"]["full_log"]))
    print(f"  X-a point range rho(V, log price) > +0.35; log range |rho| < 0.20                     : point {cpt:+.3f}; log {clg:.3f}")
    print(f"  X-b primary Delta positive, +$5 to +$25 a session                                     : {p['delta']:+.2f}")
    print(f"  X-c N1 p95 in [+20, +35] and Delta does not clear it                                   : p95 {p['p95']:+.2f}; clears {p['clears']}")
    print(f"  X-d within-year mean below +$5 and negative in >= 5 of 8                               : mean {res['n3_within_year']['mean']:+.2f}; negative in {res['n3_within_year']['n_negative']} of {res['n3_within_year']['n_years']}")
    print(f"  X-e day-session and 23-hour agree within $6 on Delta                                   : |diff| {abs(res['cells']['day_log']['delta'] - res['cells']['full_log']['delta']):.2f}")
    print(f"  X-f the verdict is CLOSE                                                               : {verdict}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    print("D512 selftest")
    n = 1200; rng = np.random.default_rng(21)
    # [A] causality: V at d reads only ranges up to d-1
    r = np.exp(rng.normal(0, .3, n)) * 50
    v = expansion(r); r2 = r.copy(); r2[700:] *= 8
    v2 = expansion(r2); assert np.allclose(np.nan_to_num(v[:701]), np.nan_to_num(v2[:701])), "V read the future"
    assert not np.allclose(np.nan_to_num(v[701:]), np.nan_to_num(v2[701:]))
    r3 = r.copy(); r3[600] *= 5; v3 = expansion(r3)
    assert np.allclose(np.nan_to_num(v[:601]), np.nan_to_num(v3[:601])), "session d must not read its own range"
    assert not np.isclose(np.nan_to_num(v[601]), np.nan_to_num(v3[601])), "session d+1 must read it"
    # [B] warm-up binds: nothing before SLOW+1 is finite
    assert not np.isfinite(v[:SLOW]).any()
    # [C] a known answer: a constant range gives V = 0; a step up gives V > 0 then decaying toward 0
    flat = np.full(n, 7.0); vf = expansion(flat); assert np.nanmax(np.abs(vf)) < 1e-12, float(np.nanmax(np.abs(vf)))
    step = np.concatenate([np.full(600, 5.0), np.full(600, 15.0)]); vs = expansion(step)
    assert vs[650] > 0.3 and vs[650] > vs[1100], (vs[650], vs[1100])
    # [D] THE CLAIM THE RECORD RESTS ON: a POINT range on a rising price is contaminated; the LOG range is not
    t = np.arange(n); px = 4500 * np.exp(0.0012 * t)                       # a steadily rising market
    hl_pct = 0.01 * (1 + 0.0 * t)                                          # CONSTANT percentage range
    pts = px * hl_pct; lg = np.log((px * (1 + hl_pct / 2)) / (px * (1 - hl_pct / 2)))
    vp, vl = expansion(pts), expansion(lg); lp = np.log(px)
    mp = np.isfinite(vp) & np.isfinite(lp)
    assert np.nanmean(vp[mp]) > 0.02, f"a point range must drift positive on a rising market: {np.nanmean(vp[mp]):.4f}"
    assert np.nanmax(np.abs(vl[np.isfinite(vl)])) < 1e-9, "a log range must be flat when the percentage range is constant"
    # [E] the primary statistic and its rotation are D509's, imported not copied
    assert D512_uses_d509()
    print(f"  A causality  B warm-up binds  C known answer (flat {np.nanmax(np.abs(vf)):.1e}, step {vs[650]:+.2f} decaying to {vs[1100]:+.2f})"
          f"  D contamination proven: constant %-range on a rising market gives point V {np.nanmean(vp[mp]):+.3f} and log V {np.nanmax(np.abs(vl[np.isfinite(vl)])):.1e}"
          f"  E statistic imported from D509\n  all pass")


def D512_uses_d509():
    import inspect
    return "qdiff" in inspect.getsource(run) and "rotation_qdiff" in inspect.getsource(run)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
