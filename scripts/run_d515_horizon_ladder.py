"""D515 -- is the MACD signal real on the failing roots but SLOWER than a seven-hour window?
A SIGNAL measurement, not a trading study: no cost, no flatten, no day-session constraint. edge_sigma = mean(signal x forward)/sd(forward),
D484's dimensionless statistic, imported. Signal = the frozen AGREE state at every hourly segment; forward = open(t+1) -> open(t+1+H).
Horizons 1,2,3,5,8,13,21,34 segments on eight roots. Primary: pooled edge_sigma over YM, CL and 6E at H = 13. Nulls: exact enumerated
rotation of the signal along the SESSION axis, and a 64-cell family maximum. Spec committed in 78fb1f3 BEFORE this file. 2016-2023.

    uv run python -u scripts/run_d515_horizon_ladder.py --run
    uv run python -u scripts/run_d515_horizon_ladder.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d515_horizon_ladder.json"; SPEC = "78fb1f3"
ROOTS = ["ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E"]
SIGNAL_DEAD = ["YM", "CL", "6E"]                       # D513's addendum: gross negative at the arm's horizon
HOLDS = [1, 2, 3, 5, 8, 13, 21, 34]
PRIMARY_H = 13
N_ROT = None                                           # None = enumerate every offset


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D506B = _load("d506b", "d506_macd_breadth.py")
D484 = _load("d484c", "d484_offdiagonal_and_macd.py")
edge_sigma = D484.edge_sigma                           # imported, not re-implemented


# ------------------------------------------------------------------------------------------ the flattened series
def flat_series(d_all, root, window):
    """The AGREE signal and the OPEN price on the continuous 23-segment series, on the sessions build_root keeps.
    Returns (sig_flat, open_flat, n_sessions, nseg) with the session grid preserved so the rotation can roll whole sessions."""
    b = D506B.build_root(d_all, root, window)
    assert b is not None and not b.get("skipped"), f"{root} did not build"
    return b["AGREE"], b["O"], b["AGREE"].shape[0], b["AGREE"].shape[1]


def forward(openg, H):
    """log(open[t+1+H] / open[t+1]) laid on the same (session, segment) grid as the signal, NaN where it runs off the end."""
    flat = openg.ravel()
    with np.errstate(invalid="ignore", divide="ignore"):
        lf = np.log(np.where(flat > 0, flat, np.nan))
    n = len(lf); out = np.full(n, np.nan)
    hi = n - 1 - H
    if hi > 0:
        out[:hi] = lf[1 + H:1 + H + hi] - lf[1:1 + hi]
    return out.reshape(openg.shape)


def cell(sig, openg, H):
    f = forward(openg, H).ravel(); s = sig.ravel()
    m = np.isfinite(s) & np.isfinite(f) & (s != 0)
    n = int(m.sum())
    return dict(H=H, edge_sigma=edge_sigma(s, f), n=n, n_eff=n / H, share_nonzero=float((s != 0).mean()))


def rotation(sig, openg, H, d_max=N_ROT):
    """Exact enumerated rotation: roll the SIGNAL grid along the session axis by k, keeping the price path fixed."""
    f = forward(openg, H).ravel(); ns = sig.shape[0]
    D = ns - 1 if d_max is None else min(d_max, ns - 1); out = np.empty(D)
    for k in range(1, D + 1):
        out[k - 1] = edge_sigma(np.roll(sig, k, axis=0).ravel(), f)
    return out


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D515 -- is the signal real but slower?\n      spec committed in {SPEC} BEFORE this ran; {D506B.IN_LO}..{D506B.IN_HI}; a SIGNAL measurement, no cost and no flatten\n      primary: pooled edge_sigma over {SIGNAL_DEAD} at H = {PRIMARY_H}")
    meta = json.loads(D506B.META.read_text(encoding="utf-8")); specs = meta["specs"]; d_all = pd.read_csv(D506B.FIX)
    S = {}
    for r in ROOTS:
        S[r] = flat_series(d_all, r, specs[r]["day_window"])
    res = dict(spec="D515", commit=SPEC, lo=D506B.IN_LO, hi=D506B.IN_HI, roots=ROOTS, holds=HOLDS,
               signal_dead=SIGNAL_DEAD, primary_H=PRIMARY_H, ladder={}, window={r: specs[r]["day_window"] for r in ROOTS})
    print(f"\n  edge_sigma by root and horizon (segments). The arm's window is ~7; a session is 23.")
    print(f"  {'root':5s} " + " ".join(f"{('H' + str(h)):>8s}" for h in HOLDS) + "   peak H")
    for r in ROOTS:
        sig, og, ns, nseg = S[r]; res["ladder"][r] = {}
        vals = []
        for H in HOLDS:
            c = cell(sig, og, H); res["ladder"][r][str(H)] = c; vals.append(c["edge_sigma"])
        peak = HOLDS[int(np.nanargmax(vals))]; res["ladder"][r]["peak_H"] = peak
        print(f"  {r:5s} " + " ".join(f"{v:+8.4f}" for v in vals) + f"   {peak:>6d}")
    print(f"\n  n_eff at each horizon (n / H), NQ as the example: " + "  ".join(f"H{h} {res['ladder']['NQ'][str(h)]['n_eff']:,.0f}" for h in HOLDS))
    # nulls
    print("\n  N1/N2 -- exact enumerated rotation of the signal along the session axis")
    paths = {}
    for r in ROOTS:
        sig, og, ns, nseg = S[r]
        for H in HOLDS:
            paths[f"{r}-H{H}"] = rotation(sig, og, H)
    D = min(len(v) for v in paths.values()); fam = np.nanmax(np.column_stack([v[:D] for v in paths.values()]), axis=1)
    obs = {k: res["ladder"][k.split("-H")[0]][k.split("-H")[1]]["edge_sigma"] for k in paths}
    best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(paths), n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    for k, v in paths.items():
        r, h = k.split("-H"); res["ladder"][r][h]["n1_p95"] = float(np.quantile(v, .95)); res["ladder"][r][h]["n1_share_ge"] = float((v >= obs[k]).mean())
        res["ladder"][r][h]["clears_n1"] = bool(obs[k] > np.quantile(v, .95))
    f = res["family"]
    print(f"     N2 FAMILY MAXIMUM over {f['n_cells']} cells, {f['n_offsets']:,} offsets: p50 {f['p50']:+.4f}  p95 {f['p95']:+.4f}   observed max {f['observed_max']:+.4f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    clearing = [k for k in paths if obs[k] > np.quantile(paths[k], .95)]
    clearing_fam = [k for k in paths if obs[k] > f["p95"]]
    res["clearing_n1"] = clearing; res["clearing_family"] = clearing_fam
    print(f"     cells clearing their OWN null: {len(clearing)} of {len(paths)} -> {clearing[:12]}")
    print(f"     cells clearing the FAMILY bar: {len(clearing_fam)} -> {clearing_fam}")
    # the primary
    num = 0.0; den = 0
    for r in SIGNAL_DEAD:
        c = res["ladder"][r][str(PRIMARY_H)]; num += c["edge_sigma"] * c["n"]; den += c["n"]
    pooled = num / den
    pth = np.column_stack([paths[f"{r}-H{PRIMARY_H}"][:D] for r in SIGNAL_DEAD])
    w = np.array([res["ladder"][r][str(PRIMARY_H)]["n"] for r in SIGNAL_DEAD], float); w /= w.sum()
    pooled_null = pth @ w
    res["primary"] = dict(pooled_edge=pooled, n=den, p50=float(np.median(pooled_null)), p95=float(np.quantile(pooled_null, .95)),
                          share_ge=float((pooled_null >= pooled).mean()), clears=bool(pooled > np.quantile(pooled_null, .95)))
    p = res["primary"]
    print(f"\n  PRIMARY: pooled edge_sigma over {SIGNAL_DEAD} at H={PRIMARY_H} = {pooled:+.4f} (n {den:,}) against its own rotation p50 {p['p50']:+.4f} p95 {p['p95']:+.4f}; {100*p['share_ge']:.1f}% of offsets at or above; clears {p['clears']}")
    # verdict
    peaks = {r: res["ladder"][r]["peak_H"] for r in ROOTS}
    dead_peaks_long = sum(1 for r in SIGNAL_DEAD if peaks[r] > 8)
    peak_le8 = sum(1 for r in ROOTS if peaks[r] <= 8)
    any_dead_clears = any(res["ladder"][r][str(h)]["clears_n1"] for r in SIGNAL_DEAD for h in HOLDS)
    verdict = ("SLOW-BUT-REAL" if (p["clears"] and pooled > 0 and dead_peaks_long == len(SIGNAL_DEAD))
               else ("NO SIGNAL AT ANY HORIZON" if not any_dead_clears and peak_le8 < 6 else "TRUNCATED AT ABOUT THE RIGHT PLACE"))
    res["verdict"] = verdict; res["peaks"] = peaks
    print(f"\n  peak horizon by root: " + "  ".join(f"{r} H{peaks[r]}" for r in ROOTS))
    print(f"  VERDICT (pre-registered rule): {verdict}")
    print("\nPREDICTIONS")
    print(f"  X-a pooled edge on the signal-dead roots at H=13 in [-0.01, +0.01], not clearing N1      : {pooled:+.4f}; clears {p['clears']}")
    print(f"  X-b edge_sigma peaks at H <= 8 on >= 6 of 8 roots                                        : {peak_le8} of 8")
    nq = [res["ladder"]["NQ"][str(h)]["edge_sigma"] for h in HOLDS]
    print(f"  X-c NQ positive at every H, largest between H=3 and H=8, declining by H=34 without turning negative : " + "  ".join(f"H{h} {v:+.4f}" for h, v in zip(HOLDS, nq)))
    pool_all = lambda h: sum(res["ladder"][r][str(h)]["edge_sigma"] * res["ladder"][r][str(h)]["n"] for r in ROOTS) / sum(res["ladder"][r][str(h)]["n"] for r in ROOTS)
    print(f"  X-d pooled edge over all eight at H=21 and H=34 below its value at H=5                    : H5 {pool_all(5):+.4f}  H21 {pool_all(21):+.4f}  H34 {pool_all(34):+.4f}")
    print(f"  X-e family p95 in [+0.02, +0.05] and at most two cells clear it, one on NQ                : p95 {f['p95']:+.4f}; {len(clearing_fam)} clear -> {clearing_fam}")
    print(f"  X-f the verdict is TRUNCATED AT ABOUT THE RIGHT PLACE                                     : {verdict}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    print("D515 selftest")
    rng = np.random.default_rng(15); ns, nseg = 300, 23
    og = 100 * np.exp(np.cumsum(rng.normal(0, .002, ns * nseg)).reshape(ns, nseg))
    sig = np.sign(rng.normal(0, 1, (ns, nseg)))
    # [A] the forward return is open(t+1) -> open(t+1+H) and never reads the signal's own bar
    f1 = forward(og, 1); flat = np.log(og.ravel())
    assert abs(f1.ravel()[10] - (flat[12] - flat[11])) < 1e-12, "H=1 must be open[t+2]/open[t+1]"
    f3 = forward(og, 3); assert abs(f3.ravel()[10] - (flat[14] - flat[11])) < 1e-12
    assert not np.isfinite(f3.ravel()[-3:]).any(), "the tail must be NaN where the window runs off"
    # [B] a known answer: a signal equal to the sign of the forward move earns a large positive edge
    perfect = np.sign(forward(og, 1)); perfect = np.nan_to_num(perfect)
    e = edge_sigma(perfect.ravel(), forward(og, 1).ravel()); assert e > 0.5, e
    # [C] and it can fail: an unrelated signal is near zero, and the rotation of the perfect one is too
    assert abs(edge_sigma(sig.ravel(), forward(og, 1).ravel())) < 0.08
    rot = rotation(perfect, og, 1, d_max=40); assert abs(np.median(rot)) < 0.1, float(np.median(rot))
    assert (rot >= e).mean() < 0.05
    # [D] edge_sigma is scale-free, so roots with 60x different ticks are comparable
    assert abs(edge_sigma(sig.ravel(), forward(og, 2).ravel() * 1000) - edge_sigma(sig.ravel(), forward(og, 2).ravel())) < 1e-9
    # [E] the rotation rolls SESSIONS, preserving each session's intraday shape
    rolled = np.roll(sig, 5, axis=0); assert np.array_equal(rolled[5], sig[0]) and not np.array_equal(rolled[0], sig[0])
    # [F] n_eff falls as 1/H, which is what overlapping windows require the reader to see
    c1, c8 = cell(sig, og, 1), cell(sig, og, 8)
    assert c8["n_eff"] < c1["n_eff"] / 7, (c1["n_eff"], c8["n_eff"])
    # [G] zero-signal segments are excluded from the statistic, not counted as flat bets
    z = sig.copy(); z[:, :10] = 0.0
    assert cell(z, og, 1)["n"] < cell(sig, og, 1)["n"]
    print(f"  A forward window and its NaN tail  B known answer (perfect signal {e:+.3f})  C unrelated ~0 and the rotation kills the perfect one"
          f"  D scale-free  E rotation rolls sessions  F n_eff falls as 1/H ({c1['n_eff']:,.0f} -> {c8['n_eff']:,.0f})  G zero states excluded\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()
