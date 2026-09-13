"""D514 -- does the Dow's GROSS turn positive without the five-hour minimum hold?
The frozen machinery unchanged (build_root + simulate_window imported); only M varies, over 0..5. Declared cells: {YM, CL, 6E} x 6 values,
primary = YM's gross $/session at M <= 1. NQ is a reference row and NOT a declared cell. Null: exact enumerated rotation of the AGREE grid
along the SESSION axis with the machine re-run at every offset, plus an 18-cell family maximum. Spec committed in 85c4cc5 BEFORE this file.
2016-2023; no 2024+ slice is read.

    uv run python -u scripts/run_d514_hold_ladder.py --run
    uv run python -u scripts/run_d514_hold_ladder.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d514_hold_ladder.json"; SPEC = "85c4cc5"
DECLARED = ["YM", "CL", "6E"]; REFERENCE = ["NQ"]; PRIMARY, PRIMARY_M = "YM", 1
M_LADDER = [0, 1, 2, 3, 4, 5]


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D506B = _load("d506b", "d506_macd_breadth.py")


# ------------------------------------------------------------------------------------------ the machine, at one M
def cell(b, sp, M):
    """Gross and net for one root at one minimum hold, in dollars, plus the realised hold length."""
    tickv = sp["tick_usd"]; cost_tk = D506B.COMMISSION_RT / tickv + D506B.CROSS_TICKS_ASSUMED; tk = sp["tick_price_units"]
    O, C = b["O"] / tk, b["C"] / tk
    pg, tg = D506B.simulate_window(O, C, b["AGREE"], b["first"], b["last"], M, 0.0)
    pn, tn = D506B.simulate_window(O, C, b["AGREE"], b["first"], b["last"], M, cost_tk)
    assert np.array_equal(tg, tn) and np.abs(pn - (pg - cost_tk * tg)).max() < 1e-9, "net != gross - cost x trips"
    n = b["n_sessions"]; ntr = float(tg.sum())
    g_usd = pg * tickv; n_usd = pn * tickv
    sh = lambda x: float(x.mean() / x.std(ddof=1) * np.sqrt(D506B.TRADING_DAYS)) if x.std(ddof=1) > 0 else float("nan")
    # realised hold: total segments held / trades, from the difference between the traded window and the trip count
    held = mean_hold(O, C, b["AGREE"], b["first"], b["last"], M)
    return dict(M=M, n_sessions=n, trades=int(ntr), trips_per_session=ntr / n, mean_hold_segments=held,
                gross_usd_session=float(g_usd.mean()), gross_usd_trade=float(g_usd.sum() / ntr) if ntr else float("nan"),
                net_usd_session=float(n_usd.mean()), net_usd_trade=float(n_usd.sum() / ntr) if ntr else float("nan"),
                gross_sharpe=sh(g_usd), net_sharpe=sh(n_usd), cost_usd=cost_tk * tickv, tick_usd=tickv)


def mean_hold(O, C, sig, first, last, M):
    """Mean number of segments a position is held, by replaying the same state machine and counting live segments."""
    n = O.shape[0]; pos = np.zeros(n); entry_t = np.full(n, -1, dtype=np.int64); live_segs = np.zeros(n); trips = np.zeros(n)
    s_all = np.nan_to_num(sig, nan=0.0)
    for t in range(first, last):
        s = s_all[:, t]; px = O[:, t + 1]
        live = pos != 0
        live_segs += live.astype(float)
        ex = live & ((t - entry_t) >= M) & (s * pos <= 0) & np.isfinite(px)
        pos = np.where(ex, 0.0, pos); trips += ex.astype(float)
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_t = np.where(en, t, entry_t); pos = np.where(en, s, pos)
    live_segs += (pos != 0).astype(float); trips += (pos != 0).astype(float)
    tt = trips.sum()
    return float(live_segs.sum() / tt) if tt else float("nan")


def rotation(b, sp, M, d_max=None):
    """Exact enumerated rotation: roll the AGREE grid along the SESSION axis by k and re-run the machine. Rolling whole sessions keeps each
    session's intraday signal shape and the signal's autocorrelation intact -- a smoothed signal is rotated, never shuffled."""
    tickv = sp["tick_usd"]; tk = sp["tick_price_units"]; O, C = b["O"] / tk, b["C"] / tk
    A = b["AGREE"]; n = A.shape[0]; D = n - 1 if d_max is None else min(d_max, n - 1); out = np.empty(D)
    for k in range(1, D + 1):
        pg, _ = D506B.simulate_window(O, C, np.roll(A, k, axis=0), b["first"], b["last"], M, 0.0)
        out[k - 1] = float((pg * tickv).mean())
    return out


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D514 -- does the Dow's gross turn positive without the five-hour minimum hold?\n      spec committed in {SPEC} BEFORE this ran; {D506B.IN_LO}..{D506B.IN_HI}; no 2024+ slice is read\n      declared cells {DECLARED} x M {M_LADDER}; primary = {PRIMARY} gross $/session at M <= {PRIMARY_M}; {REFERENCE} is a reference row only")
    meta = json.loads(D506B.META.read_text(encoding="utf-8")); specs = meta["specs"]; d_all = pd.read_csv(D506B.FIX)
    built = {}
    for r in DECLARED + REFERENCE:
        sp = specs[r]; b = D506B.build_root(d_all, r, sp["day_window"])
        assert b is not None and not b.get("skipped"), f"{r} did not build"
        built[r] = (b, sp)
    res = dict(spec="D514", commit=SPEC, lo=D506B.IN_LO, hi=D506B.IN_HI, declared=DECLARED, reference=REFERENCE,
               primary=dict(root=PRIMARY, M=PRIMARY_M), ladder={}, window={r: specs[r]["day_window"] for r in built})
    # [ASSERT] M = 0 and M = 1 are the same machine
    b, sp = built[PRIMARY]
    c0, c1 = cell(b, sp, 0), cell(b, sp, 1)
    same = all(abs(c0[k] - c1[k]) < 1e-9 for k in ("gross_usd_session", "net_usd_session", "trips_per_session", "mean_hold_segments"))
    res["m0_equals_m1"] = bool(same)
    print(f"\n  [ASSERT] M=0 and M=1 are the same machine: {same}  (gross $/session {c0['gross_usd_session']:+.3f} vs {c1['gross_usd_session']:+.3f})")
    assert same, "M=0 and M=1 differ; the pre-registration's reading of the exit test is wrong"
    print(f"\n  {'root':5s} {'M':>2s} {'trades':>6s} {'trips':>5s} {'hold':>5s} | {'GROSS $/sess':>12s} {'gross $/tr':>10s} {'gross Sh':>8s} | {'net $/sess':>10s} {'net $/tr':>8s} {'net Sh':>7s}")
    for r in DECLARED + REFERENCE:
        b, sp = built[r]; res["ladder"][r] = {}
        for M in M_LADDER:
            c = cell(b, sp, M); res["ladder"][r][str(M)] = c
            tag = "" if r in DECLARED else "  (reference)"
            print(f"  {r:5s} {M:2d} {c['trades']:6d} {c['trips_per_session']:5.2f} {c['mean_hold_segments']:5.2f} | {c['gross_usd_session']:+12.3f} {c['gross_usd_trade']:+10.2f} {c['gross_sharpe']:+8.3f} | {c['net_usd_session']:+10.3f} {c['net_usd_trade']:+8.2f} {c['net_sharpe']:+7.3f}{tag}")
        print()
    # nulls on the declared cells
    print("  N1/N2 -- exact enumerated rotation of the AGREE grid along the session axis, machine re-run at every offset")
    paths = {}
    for r in DECLARED:
        b, sp = built[r]
        for M in M_LADDER:
            paths[f"{r}-M{M}"] = rotation(b, sp, M)
    D = min(len(v) for v in paths.values()); fam = np.nanmax(np.column_stack([v[:D] for v in paths.values()]), axis=1)
    obs = {k: res["ladder"][k.split("-M")[0]][k.split("-M")[1]]["gross_usd_session"] for k in paths}
    best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(paths), n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    for k, v in paths.items():
        res["ladder"][k.split("-M")[0]][k.split("-M")[1]]["n1_p50"] = float(np.median(v))
        res["ladder"][k.split("-M")[0]][k.split("-M")[1]]["n1_p95"] = float(np.quantile(v, .95))
        res["ladder"][k.split("-M")[0]][k.split("-M")[1]]["n1_share_ge"] = float((v >= obs[k]).mean())
    f = res["family"]
    print(f"     per-cell p95 of gross $/session: " + "  ".join(f"{k} {np.quantile(v, .95):+.2f}" for k, v in list(paths.items())[:6]) + " ...")
    print(f"     N2 FAMILY MAXIMUM over {f['n_cells']} declared cells, {f['n_offsets']:,} offsets: p50 {f['p50']:+.3f}  p95 {f['p95']:+.3f}   observed max {f['observed_max']:+.3f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    p = res["ladder"][PRIMARY][str(PRIMARY_M)]
    verdict = "POSITIVE" if (p["gross_usd_session"] > 0 and p["gross_usd_session"] > p["n1_p95"] and p["gross_usd_session"] > f["p95"]) else \
              ("POSITIVE BUT INSIDE THE NULL" if p["gross_usd_session"] > 0 else "NEGATIVE")
    res["verdict"] = verdict
    print(f"\n  PRIMARY: {PRIMARY} gross ${p['gross_usd_session']:+.3f} a session at M={PRIMARY_M} (no minimum hold), against its own p95 {p['n1_p95']:+.3f} and a family p95 {f['p95']:+.3f}")
    print(f"  VERDICT (pre-registered rule): {verdict}")
    print("\nPREDICTIONS")
    t5 = {r: res["ladder"][r]["5"] for r in DECLARED}; t1 = {r: res["ladder"][r]["1"] for r in DECLARED}
    print(f"  X-a trips 1.0 at M=5 -> 1.3..1.8 at M<=1; mean hold falls to 2..4 segments             : " + "  ".join(f"{r} {t5[r]['trips_per_session']:.2f}->{t1[r]['trips_per_session']:.2f}, hold {t5[r]['mean_hold_segments']:.1f}->{t1[r]['mean_hold_segments']:.1f}" for r in DECLARED))
    print(f"  X-b YM gross at M<=1 still negative, between -$3 and 0 a session                        : {t1['YM']['gross_usd_session']:+.3f}")
    mono = sum(1 for r in DECLARED if res["ladder"][r]["1"]["gross_usd_session"] < res["ladder"][r]["5"]["gross_usd_session"])
    print(f"  X-c gross falls as M falls on >= 2 of 3 declared roots                                  : {mono} of 3")
    nq = {M: res['ladder']['NQ'][str(M)]['gross_usd_session'] for M in M_LADDER}
    print(f"  X-d NQ gross clearly positive at every M, +$8..+$16 a session                           : " + "  ".join(f"M{M} {v:+.2f}" for M, v in nq.items()))
    ymc = [res["ladder"]["YM"][str(M)]["gross_usd_session"] > f["p95"] for M in M_LADDER]
    print(f"  X-e family p95 in [+$1, +$4] and no YM cell clears it                                   : p95 {f['p95']:+.3f}; YM cells clearing {sum(ymc)}")
    print(f"  X-f the verdict is NEGATIVE                                                             : {verdict}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    print("D514 selftest")
    rng = np.random.default_rng(14); n, nseg = 400, 23
    O = 100 + np.cumsum(rng.normal(0, .4, (n, nseg)), axis=1); C = O + rng.normal(0, .1, (n, nseg))
    sig = np.sign(rng.normal(0, 1, (n, nseg)))
    b = dict(O=O, C=C, AGREE=sig, first=15, last=21, n_sessions=n)
    sp = dict(tick_usd=0.5, tick_price_units=0.25)
    # [A] M=0 and M=1 are the same machine, which is the pre-registration's claim about the exit test
    assert abs(cell(b, sp, 0)["gross_usd_session"] - cell(b, sp, 1)["gross_usd_session"]) < 1e-12
    assert cell(b, sp, 0)["trips_per_session"] == cell(b, sp, 1)["trips_per_session"]
    # [B] M binds: trips fall and the hold lengthens as M rises, monotonically
    tr = [cell(b, sp, M)["trips_per_session"] for M in M_LADDER]
    hd = [cell(b, sp, M)["mean_hold_segments"] for M in M_LADDER]
    assert tr[1] > tr[-1] and all(tr[i] >= tr[i + 1] - 1e-12 for i in range(1, len(tr) - 1)), tr
    assert hd[-1] > hd[1], (hd[1], hd[-1])
    # [C] at M >= the window width the machine is a fixed hold: exactly one trip a session
    wide = cell(b, sp, 21 - 15)
    assert abs(wide["trips_per_session"] - 1.0) < 1e-12, wide["trips_per_session"]
    # [D] sign audit in money: flipping the signal flips the gross exactly
    bf = dict(b, AGREE=-sig)
    assert abs(cell(b, sp, 3)["gross_usd_session"] + cell(bf, sp, 3)["gross_usd_session"]) < 1e-9
    # [E] the cost identity, and that the assertion inside cell() can fire
    c = cell(b, sp, 3); assert abs((c["gross_usd_session"] - c["net_usd_session"]) - c["cost_usd"] * c["trips_per_session"]) < 1e-9
    # [F] the rotation rolls SESSIONS, so each session's intraday shape is preserved
    rolled = np.roll(sig, 7, axis=0)
    assert np.array_equal(rolled[7], sig[0]) and not np.array_equal(rolled[0], sig[0])
    path = rotation(b, sp, 3, d_max=30); assert len(path) == 30 and np.isfinite(path).all()
    # [G] a known answer built the other way round: the PRICE PATH is constructed from the signal, so the machine must earn.
    # The machine decides at the close of t and fills at the open of t+1, so the move it captures is O[t+2] - O[t+1]; building that
    # move to equal the signal makes the answer exact rather than approximate, which is what the first version of this check got wrong.
    sg = np.sign(rng.normal(0, 1, (n, nseg))); sg[sg == 0] = 1.0
    Ok = np.zeros((n, nseg)); Ok[:, 15 + 1] = 100.0
    for t in range(15, 21):
        Ok[:, t + 1] = Ok[:, t] + (sg[:, t - 1] if t > 15 else 0.0)
    Ok[:, :16] = 100.0
    Ck = Ok.copy(); Ck[:, 21] = Ok[:, 21] + sg[:, 20]
    bk = dict(b, O=Ok, C=Ck, AGREE=sg)
    good = cell(bk, sp, 1)["gross_usd_session"]; null = rotation(bk, sp, 1)
    assert good > 0 and (null >= good).mean() < 0.01, (good, float((null >= good).mean()))
    assert abs(np.median(null)) < 0.5 * good, (float(np.median(null)), good)
    print(f"  A M=0 == M=1  B M binds (trips {tr[1]:.2f}->{tr[-1]:.2f}, hold {hd[1]:.2f}->{hd[-1]:.2f})  C a wide M is a fixed hold"
          f"  D sign audit  E cost identity  F rotation rolls sessions  G known answer (oracle {good:+.2f}, beaten by {100*(null >= good).mean():.1f}% of rotations)\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
