"""D513 -- the range-expansion conditioner declared in advance on six roots whose 2024+ slice is UNREAD.
V = log(EMA50(log(high/low)) / SMA200(...)) over each root's OWN day window, every term ending at d-1. The construction conditioned is the
frozen MACD arm, transplanted by the other session's generalised builder (d506_macd_breadth.build_root) -- nothing re-implemented, nothing
re-tuned. Primary: Delta/sigma on YM. Nulls: exact enumerated rotation per root, a six-root family maximum, within-year, and a direction check.
Spec committed in ed2e691 BEFORE this file. THE 2024+ SLICE IS NOT READ UNDER ANY OUTCOME.

    uv run python -u scripts/run_d513_conditioner_unspent_roots.py --run
    uv run python -u scripts/run_d513_conditioner_unspent_roots.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d513_conditioner_unspent_roots.json"; SPEC = "ed2e691"
ROOTS = ["YM", "ZN", "ZB", "GC", "CL", "6E"]          # 2024+ unread on all six; NQ spent (D503), ES overnight spent (D473)
PRIMARY = "YM"
FAST, SLOW, N_Q = 50, 200, 5


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D506B = _load("d506b", "d506_macd_breadth.py")
D509 = _load("d509c", "run_d509_quintile_primary.py")
D512 = _load("d512c", "run_d512_range_expansion.py")


# ------------------------------------------------------------------------------------------ the conditioner, per root
def conditioner(d_all, root, window):
    """V keyed by day, on the SAME filtered rows the arm is built from, but WITHOUT the in-sample date clip so the 200-session average
    has the history that precedes the window. Returns a pandas Series indexed by day."""
    d = d_all[d_all["root"] == root]
    if "same_front" in d.columns:
        d = d[d["same_front"]]
    if "present" in d.columns:
        d = d[d["present"]]
    d = d.sort_values("day", kind="stable")
    first, last = D506B.seg_index(window[0]), D506B.seg_index(window[1])
    segs = D506B.SEGN[first:last + 1]
    hi = d[[f"{s}_h" for s in segs]].to_numpy(float); lo = d[[f"{s}_l" for s in segs]].to_numpy(float)
    with np.errstate(invalid="ignore"):
        h = np.nanmax(hi, axis=1); l = np.nanmin(lo, axis=1)
        rng = np.log(np.where((h > 0) & (l > 0), h / l, np.nan))
    return pd.Series(D512.expansion(rng, FAST, SLOW), index=d["day"].to_numpy())


def standardised(delta, pnl):
    s = float(np.std(pnl, ddof=1))
    return delta / s if s > 0 else float("nan")


def qdiff_std(cond, pnl):
    d, tm, bm, nt, nb = D509.qdiff(cond, pnl)
    return standardised(d, pnl), d, tm, bm, nt, nb


def rotation_std(cond, pnl, d_max=None):
    path = D509.rotation_qdiff(cond, pnl, N_Q, d_max)
    s = float(np.std(pnl, ddof=1))
    return path / s if s > 0 else path


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D513 -- the range-expansion conditioner on six roots whose 2024+ is UNREAD\n      spec committed in {SPEC} BEFORE this ran; {D506B.IN_LO}..{D506B.IN_HI}; the forward slice is NOT read under any outcome\n      primary declared in advance: {PRIMARY}")
    meta = json.loads(D506B.META.read_text(encoding="utf-8"))
    if not meta.get("all_gates_pass"):
        raise D506B.GateError("[FIXTURE] the breadth fixture's gates do not all pass")
    specs = meta["specs"]; d_all = pd.read_csv(D506B.FIX)
    res = dict(spec="D513", commit=SPEC, lo=D506B.IN_LO, hi=D506B.IN_HI, roots=ROOTS, primary=PRIMARY, cells={})
    print(f"\n  {'root':5s} {'sess':>5s} {'window':>7s} {'uncond net Sh':>13s} {'uncond $/trade':>14s} | {'Delta/sig':>9s} {'Delta $':>8s} {'top $':>7s} {'bot $':>7s} {'N1 p95':>7s} {'pct':>6s} {'clears':>6s}")
    paths = {}
    for r in ROOTS:
        sp = specs[r]; b = D506B.build_root(d_all, r, sp["day_window"])
        if b is None or b.get("skipped"):
            print(f"  {r:5s} skipped (under {D506B.MIN_SESSIONS} sessions)"); continue
        m_max = D506B.max_hold_available(b["first"], b["last"])
        if D506B.M_PRIMARY > m_max:
            print(f"  {r:5s} the frozen minimum hold of {D506B.M_PRIMARY} h does not fit its {sp['day_window']} window (max {m_max})"); continue
        tickv = sp["tick_usd"]; cost = D506B.COMMISSION_RT / tickv + D506B.CROSS_TICKS_ASSUMED; tk = sp["tick_price_units"]
        pn, tn = D506B.simulate_window(b["O"] / tk, b["C"] / tk, b["AGREE"], b["first"], b["last"], D506B.M_PRIMARY, cost)
        pg, tg = D506B.simulate_window(b["O"] / tk, b["C"] / tk, b["AGREE"], b["first"], b["last"], D506B.M_PRIMARY, 0.0)
        assert np.abs(pn - (pg - cost * tg)).max() < 1e-9, f"{r}: net != gross - cost x trips"
        days = np.asarray(b["days"]).astype(str)
        V = conditioner(d_all, r, sp["day_window"]).reindex(days).to_numpy()
        assert len(V) == len(days), f"{r}: the conditioner did not align to the arm's sessions"
        net_usd = pn * tickv; gross_usd = pg * tickv
        uncond = D506B.score(pn, tn, tickv, b["n_sessions"])
        ds, d, tm, bm, nt, nb = qdiff_std(V, net_usd)
        path = rotation_std(V, net_usd); path = path[np.isfinite(path)]; paths[r] = path
        p95 = float(np.quantile(path, .95)); pct = float((path <= ds).mean())
        yrs = np.array([t[:4] for t in days]); wy = {}
        for y in sorted(set(yrs)):
            s = yrs == y
            if s.sum() > 100:
                wy[y] = qdiff_std(V[s], net_usd[s])[0]
        vals = [v for v in wy.values() if np.isfinite(v)]
        res["cells"][r] = dict(n_sessions=int(b["n_sessions"]), window=sp["day_window"], sized_as=sp.get("sized_as"), tick_usd=tickv,
                               uncond_net_sharpe=uncond["sharpe"], uncond_usd_per_trade=uncond["mean_usd_per_trade"],
                               delta_std=ds, delta_usd=d, delta_ticks=d / tickv, top_usd=tm, bot_usd=bm, n_top=nt, n_bot=nb,
                               n1_p50=float(np.median(path)), n1_p95=p95, percentile=pct, clears=bool(ds > p95),
                               within_year=wy, within_mean=float(np.mean(vals)) if vals else float("nan"),
                               within_same_sign=int(sum(np.sign(v) == np.sign(ds) for v in vals)), n_years=len(vals))
        c = res["cells"][r]
        print(f"  {r:5s} {b['n_sessions']:5d} {str(sp['day_window']):>7s} {uncond['sharpe']:+13.3f} {uncond['mean_usd_per_trade']:+14.2f} | {ds:+9.3f} {d:+8.2f} {tm:+7.2f} {bm:+7.2f} {p95:+7.3f} {100*pct:5.1f}% {str(c['clears']):>6s}")
    if not paths:
        print("\n  no root produced a cell"); return
    D = min(len(v) for v in paths.values()); fam = np.nanmax(np.column_stack([v[:D] for v in paths.values()]), axis=1)
    obs = {k: res["cells"][k]["delta_std"] for k in paths}; best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(paths), n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    f = res["family"]
    print(f"\n  N2 FAMILY MAXIMUM over {f['n_cells']} roots, {f['n_offsets']:,} common offsets (exact): p50 {f['p50']:+.3f}  p95 {f['p95']:+.3f}   observed max {f['observed_max']:+.3f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    print(f"  single-cell p95 on the primary {res['cells'][PRIMARY]['n1_p95']:+.3f} -> family p95 {f['p95']:+.3f}  (ratio {f['p95']/res['cells'][PRIMARY]['n1_p95']:.2f}x)")
    print("\n  N3 WITHIN-YEAR Delta/sigma:")
    for r, c in res["cells"].items():
        print(f"     {r:5s} " + "  ".join(f"{y}:{v:+.2f}" for y, v in c["within_year"].items()) + f"   mean {c['within_mean']:+.3f}, same sign as pooled in {c['within_same_sign']} of {c['n_years']}")
    pos = sum(1 for c in res["cells"].values() if c["delta_std"] > 0)
    res["n4_direction"] = dict(n_positive=pos, n_cells=len(res["cells"]))
    print(f"\n  N4 DIRECTION: Delta positive on {pos} of {len(res['cells'])} roots (the conditioner's claim is that a compressed range is BAD for a trend construction)")
    p = res["cells"][PRIMARY]
    ok = p["clears"] and p["delta_std"] > f["p95"] and p["delta_std"] > 0 and p["within_same_sign"] * 2 > p["n_years"]
    verdict = "PROCEED" if ok else ("PICK" if (p["clears"] and p["delta_std"] > 0) else "CLOSE")
    res["verdict"] = verdict
    res["decision_terms"] = dict(n1=p["clears"], family=bool(p["delta_std"] > f["p95"]), positive=bool(p["delta_std"] > 0),
                                 within_year_majority=bool(p["within_same_sign"] * 2 > p["n_years"]))
    print(f"\n  VERDICT (pre-registered rule): {verdict}   terms {res['decision_terms']}")
    print("  THE 2024+ SLICE WAS NOT READ. A forward read is a separate record on the principal's explicit word.")
    print("\nPREDICTIONS")
    flat = sum(1 for c in res["cells"].values() if -0.3 <= c["uncond_net_sharpe"] <= 0.3)
    print(f"  X-a the arm is flat or negative on >= 4 of 6 roots (net Sharpe in [-0.3, +0.3])       : {flat} of {len(res['cells'])}")
    print(f"  X-b primary Delta/sigma in [+0.05, +0.30], not clearing an N1 p95 in [+0.30, +0.55]   : {p['delta_std']:+.3f}; p95 {p['n1_p95']:+.3f}; clears {p['clears']}")
    print(f"  X-c family p95 is 1.2x to 1.6x the single-cell p95                                     : {f['p95']/p['n1_p95']:.2f}x")
    print(f"  X-d Delta positive on >= 4 of 6 roots                                                  : {pos} of {len(res['cells'])}")
    same = sum(1 for c in res["cells"].values() if c["within_same_sign"] * 2 > c["n_years"])
    print(f"  X-e the within-year mean keeps the pooled sign on >= 4 roots                           : {same} of {len(res['cells'])}")
    print(f"  X-f the verdict is PICK or CLOSE, not PROCEED                                          : {verdict}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    print("D513 selftest")
    n = 1500; rng = np.random.default_rng(31)
    # [A] the conditioner is D512's, so causality is inherited -- assert it here rather than assume it
    r = np.exp(rng.normal(0, .3, n)) * 0.01
    v = D512.expansion(r, FAST, SLOW); r2 = r.copy(); r2[900:] *= 6
    v2 = D512.expansion(r2, FAST, SLOW)
    assert np.allclose(np.nan_to_num(v[:901]), np.nan_to_num(v2[:901])) and not np.allclose(np.nan_to_num(v[901:]), np.nan_to_num(v2[901:]))
    assert not np.isfinite(v[:SLOW]).any()
    # [B] standardisation: Delta/sigma is invariant to a constant rescaling of the P&L, Delta in dollars is not
    cond = np.abs(np.cumsum(rng.normal(0, .02, n))); pnl = rng.normal(0, 50, n) + np.where(cond >= np.quantile(cond, .8), 40.0, 0.0)
    a1 = qdiff_std(cond, pnl); a2 = qdiff_std(cond, pnl * 7.0)
    assert abs(a1[0] - a2[0]) < 1e-9, (a1[0], a2[0])
    assert abs(a2[1] / a1[1] - 7.0) < 1e-9, "the dollar figure must scale with the contract"
    # [C] the rotation of the standardised statistic equals the standardised rotation
    p_std = rotation_std(cond, pnl, d_max=25); p_raw = D509.rotation_qdiff(cond, pnl, N_Q, 25)
    assert np.allclose(p_std, p_raw / np.std(pnl, ddof=1)), "standardising must commute with rotating"
    # [D] known answer: a planted step clears its own null; an unplanted series typically does not
    full = rotation_std(cond, pnl); full = full[np.isfinite(full)]
    assert (full >= a1[0]).mean() < 0.02, float((full >= a1[0]).mean())
    shares = []
    for sd in (1, 2, 3, 4, 5):
        rr = np.random.default_rng(sd); cc = np.abs(np.cumsum(rr.normal(0, .02, n))); yy = rr.normal(0, 50, n)
        pth = rotation_std(cc, yy); pth = pth[np.isfinite(pth)]; shares.append(float((pth >= qdiff_std(cc, yy)[0]).mean()))
    assert np.median(shares) > 0.15 and sum(s < 0.05 for s in shares) <= 1, shares
    # [E] alignment: a conditioner keyed by day and reindexed to a DIFFERENT day set yields NaN where the arm has no session
    s = pd.Series([1.0, 2.0, 3.0], index=["2016-01-04", "2016-01-05", "2016-01-06"])
    got = s.reindex(np.array(["2016-01-05", "2016-01-07"])).to_numpy()
    assert got[0] == 2.0 and not np.isfinite(got[1]), got
    # [F] the direction check can fail: a conditioner with the opposite sign is not a confirmation
    neg = qdiff_std(-cond, pnl)[0]; assert neg < 0 < a1[0]
    print(f"  A causality inherited and asserted  B standardisation invariant ({a1[0]:+.3f} both scales), dollars scale x7"
          f"  C standardising commutes with rotating  D planted clears ({100*(full >= a1[0]).mean():.1f}%), unplanted typically does not {[round(s,2) for s in shares]}"
          f"  E day alignment yields NaN off-calendar  F the direction check can fail ({neg:+.3f})\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
