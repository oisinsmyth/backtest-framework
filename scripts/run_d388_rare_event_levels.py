"""D388 -- the same question as D387, with an event that is ACTUALLY RARE and ONE GATE for every arm.

    uv run python scripts/run_d388_rare_event_levels.py --audit
    uv run python scripts/run_d388_rare_event_levels.py --run --names 600 --draws 20

SIGNAL TEST under R15. Pre-registration 1c168f3 predates this file (R8).

Two fixes and nothing else (D387's own amendment, 7af1fdb):
  (a) events threshold on the NAME'S OWN SIGMA -- rarity p90/p10 across names 4.37 -> 1.37
  (b) ONE causal expanding gate for observed, N2 and A' alike

Imports the construction from D387 so the shared half is provably identical, including its
default-deny holdout audit hook.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np
from scipy.signal import lfilter

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d387", REPO / "scripts" / "run_d387_level_reversion.py")
D = importlib.util.module_from_spec(_s)
sys.modules["d387"] = D
_s.loader.exec_module(D)                      # installs the [SPLIT] hook; D388 adds no unlock either

GRID, DX, WARMUP, QUANT = D.GRID, D.DX, D.WARMUP, D.QUANT
OUT = REPO / "data/d388_rare_event_levels.json"
LAMS = (60, 120, 250)
HOLDS = (5, 10, 20)
KS = {"move": (2.0, 2.5), "reversal": (1.0, 1.5)}
HL_VOL = 60
SEED = 20260908
MIN_EVENTS = 40


# ------------------------------------------------------------------------- events
def ew_sigma(r, hl=HL_VOL):
    """CAUSAL EW standard deviation of returns, warm-started so it does not begin at zero."""
    lam = 0.5 ** (1.0 / hl)
    v = lfilter([1 - lam], [1, -lam], r * r, zi=np.array([lam * r[0] ** 2]))[0]
    return np.sqrt(np.maximum(v, 1e-24))


def events_sigma(logp, etype, k):
    """Threshold in the NAME'S OWN sigma. An absolute threshold is not a rarity threshold: D387's
    `move >2%` fired on a median 28.3% of bars and above 30% on 282 of 600 names, which made f == g
    and the density flat. In sigma units the rarity spread across names collapses 4.37x -> 1.37x."""
    n = len(logp)
    r = np.zeros(n)
    r[1:] = np.diff(logp)
    sg = ew_sigma(r)
    big = np.abs(r) > k * sg
    if etype == "move":
        m = big.copy()
    else:
        m = np.zeros(n, bool)
        m[1:] = big[1:] & big[:-1] & (np.sign(r[1:]) != np.sign(r[:-1]))
    m[0] = False
    return np.flatnonzero(m)


# -------------------------------------------------------------------- construction
def context(logp, hl):
    """Everything that depends ONLY on (path, lambda): the coordinate, the kernel matrix and the
    TIME density. Shared by both event types and both k levels -- 4 cells per build instead of 1."""
    lam = 0.5 ** (1.0 / hl)
    x = logp - D.ema_log(logp, hl)
    h = D.bandwidth(x[:WARMUP])
    if h is None:
        return None
    K = D.kernels(x, h)
    g = D.ew(K, lam)
    return dict(x=x, h=h, K=K, g=g, gv=D.read_at(g, x), lam=lam, lp=logp)


def build(ctx, ev):
    """The EVENT half: f under plain decay, its shape, and R at the current price."""
    if ctx is None or len(ev) < MIN_EVENTS:
        return None
    K, lam, x = ctx["K"], ctx["lam"], ctx["x"]
    inj = np.zeros_like(K)
    inj[ev] = K[ev]
    f = D.ew(inj, lam)
    mass = f.sum(axis=1) * DX
    ok = mass > 1e-12
    fh = np.zeros_like(f)
    fh[ok] = f[ok] / mass[ok, None]
    R = np.where(ok & (ctx["gv"] > 1e-12), D.read_at(fh, x) / np.maximum(ctx["gv"], 1e-300), np.nan)
    R[:WARMUP] = np.nan
    return dict(R=R, x=x, f=fh, g=ctx["g"], mass=mass, n_ev=len(ev), lp=ctx["lp"], h=ctx["h"])


def shape_of(b, eval_idx):
    """P3 -- DID THE DENSITY HAVE SHAPE? A first-class output, not a diagnostic. D385 and D387 both
    reported a test statistic without ever looking at the object and both times it was flat."""
    f, g = b["f"][eval_idx], b["g"][eval_idx]
    tv = 0.5 * np.abs(f - g).sum(axis=1) * DX
    sup = g > 0.05 * g.max(axis=1, keepdims=True)
    r = np.where(sup, f / np.maximum(g, 1e-300), np.nan)
    with np.errstate(invalid="ignore"):
        cv = np.nanstd(r, axis=1) / np.maximum(np.nanmean(r, axis=1), 1e-12)
    last = b["f"][eval_idx[-1]]
    c = last[1:-1]
    modes = int(((c > last[:-2]) & (c > last[2:]) & (c > 0.05 * last.max())).sum())
    return float(np.median(tv)), float(np.nanmedian(cv)), modes


# -------------------------------------------------------------------------- gate
GATE = D.expanding_threshold          # [GATE1]: the ONE function every arm calls


def decide(R, x):
    return D.decisions(R, GATE(R), x)


# --------------------------------------------------------------------- assertions
def assert_RARE(rates, tol=2.0, min_names=20):
    """The fix, asserted rather than assumed.

    RAISES on too little data rather than skipping. The first version returned (0.0, 0.0) silently
    when every key had fewer than min_names entries -- a self-test that cannot fail, which CLAUDE.md
    calls worse than none."""
    assert rates, "[RARE] no rates supplied"
    worst, worst_max = 0.0, 0.0
    for key, v in rates.items():
        v = np.array(v)
        assert len(v) >= min_names, (
            f"[RARE] only {len(v)} names for {key} -- too few to measure a p90/p10 spread")
        p10, p90 = np.percentile(v, [10, 90])
        worst = max(worst, p90 / max(p10, 1e-9))
        worst_max = max(worst_max, v.max())
        assert p90 / max(p10, 1e-9) < tol, f"[RARE] {key} rarity spread p90/p10 = {p90/p10:.2f}"
        assert v.max() < 0.15, f"[RARE] {key} fires on {100*v.max():.1f}% of bars for some name"
    return worst, worst_max


def assert_GATE1(b):
    """Observed, N2 and A' must call the SAME threshold function, and one cell's decisions must be
    reproducible through each path. D387 gave the nulls a different gate worth up to +126 bp."""
    assert GATE is D.expanding_threshold, "[GATE1] the gate is not the shared function object"
    a = decide(b["R"], b["x"])
    manual = D.decisions(b["R"], D.expanding_threshold(b["R"]), b["x"])
    assert np.array_equal(a, manual), "[GATE1] decide() differs from the explicit gate call"
    rot = D.rotated_R(b, 120)
    r1 = decide(rot, b["x"])
    r2 = D.decisions(rot, GATE(rot), b["x"])
    assert np.array_equal(r1, r2), "[GATE1] the A' arm does not use the same gate"
    return int(a.sum())


def assert_POOL(b, rng, tol=2.0):
    """A' must enter only bars the observed could. Counts are REPORTED, not forced -- one gate means
    they cannot match exactly, and a per-TRADE mean is count-normalised, so the cost is precision not
    bias. The 2x bound still catches D291-style churn (2.4x the entries, 87 cells voided)."""
    obs = decide(b["R"], b["x"])
    n_obs = max(int(obs.sum()), 1)
    elig = np.isfinite(b["R"]) & np.isfinite(b["x"]) & (np.abs(b["x"]) > 1e-9)
    elig[:WARMUP] = False
    worst = 1.0
    for _ in range(6):
        dr = decide(D.rotated_R(b, int(rng.integers(D.ROT_MIN, D.ROT_MAX))), b["x"])
        assert not (dr & ~elig).any(), "[POOL] an A' draw entered a bar the observed could not"
        ratio = max(int(dr.sum()), 1) / n_obs
        worst = max(worst, ratio, 1 / ratio)
    assert worst < tol, f"[POOL] A' count ratio {worst:.2f}x exceeds {tol}x -- churn"
    return worst


def assert_SIGMA(logp):
    """sigma must be causal: shocking a future bar may not move it, and it must not start at zero."""
    r = np.zeros(len(logp))
    r[1:] = np.diff(logp)
    s1 = ew_sigma(r)
    assert s1[0] > 0, "[SIGMA] the EW sd starts at zero -- not warm-started"
    t = len(logp) - 50
    q = logp.copy()
    q[t + 5:] += 0.4
    r2 = np.zeros(len(q))
    r2[1:] = np.diff(q)
    d = float(np.abs(s1[:t] - ew_sigma(r2)[:t]).max())
    assert d < 1e-12, f"[SIGMA] moved {d:.3e} when a future bar was shocked"
    return d


def assert_X(logp, rng):
    """Each break must move the exact SCALAR its assertion compares."""
    fired = {}
    try:                                             # [RARE]: too little data must RAISE, not pass
        assert_RARE({"x": [0.04] * 5})
        fired["RARE_thin"] = False
    except AssertionError:
        fired["RARE_thin"] = True
    try:                                             # [RARE]: a genuinely uneven rate
        assert_RARE({"x": [0.01] * 30 + [0.09] * 30})
        fired["RARE"] = False
    except AssertionError:
        fired["RARE"] = True
    try:                                             # [RARE]: a name firing on most bars
        assert_RARE({"x": [0.05] * 59 + [0.60]})
        fired["RARE_max"] = False
    except AssertionError:
        fired["RARE_max"] = True
    try:                                             # [SIGMA]: an sd that reads forward
        r = np.zeros(len(logp))
        r[1:] = np.diff(logp)
        s = np.roll(ew_sigma(r), -5)
        t = len(logp) - 50
        q = logp.copy()
        q[t + 3:] += 0.4
        r2 = np.zeros(len(q))
        r2[1:] = np.diff(q)
        assert float(np.abs(s[:t] - np.roll(ew_sigma(r2), -5)[:t]).max()) < 1e-12
        fired["SIGMA"] = False
    except AssertionError:
        fired["SIGMA"] = True
    try:                                             # [POOL]: a control that churns
        obs = np.zeros(500, bool)
        obs[:50] = True
        bad = np.zeros(500, bool)
        bad[:150] = True
        ratio = bad.sum() / obs.sum()
        assert max(ratio, 1 / ratio) < 2.0
        fired["POOL"] = False
    except AssertionError:
        fired["POOL"] = True
    bad = [k for k, v in fired.items() if not v]
    assert not bad, f"[X] these audits did NOT raise: {bad}"
    return fired


# --------------------------------------------------------------------------- run
def _cell(ctx, b, nb, rots, hi, lo, H, sym, et, hl, k, eval_idx):
    logp = b["lp"]
    dec = decide(b["R"], b["x"])
    if dec.sum() < 5:
        return None
    r, idx = D.trade_returns(logp, dec, b["x"], H, +1)
    if len(r) < 5:
        return None
    n2 = []
    for z in nb:                                   # SAME gate, on the null's own path
        rr, _ = D.trade_returns(z["lp"], decide(z["R"], z["x"]), z["x"], H, +1)
        if len(rr) >= 5:
            n2.append(float(rr.mean()))
    ap, apn = [], []
    for Rr in rots:                                # SAME gate, on the rotated density
        dr = decide(Rr, b["x"])
        rr, _ = D.trade_returns(logp, dr, b["x"], H, +1)
        if len(rr) >= 5:
            ap.append(float(rr.mean()))
            apn.append(int(dr.sum()))
    tv, cv, modes = shape_of(b, eval_idx)
    pc = lambda v, q: float(np.percentile(v, q)) if len(v) >= 5 else None
    return dict(
        symbol=sym, etype=et, hl=hl, k=k, H=H, n=int(len(r)),
        gross=float(r.mean()), med=float(np.median(r)), win=float((r > 0).mean()),
        sd=float(r.std()),
        skew=float(((r - r.mean()) ** 3).mean() / (r.std() ** 3 + 1e-30)),
        kurt=float(((r - r.mean()) ** 4).mean() / (r.std() ** 4 + 1e-30)),
        trim=D._trim(r), ex_top=D._trim(r, "top"), ex_bot=D._trim(r, "bot"),
        spread_bp=D.corwin_schultz(hi[idx], lo[idx]) if len(idx) > 30 else None,
        px=float(np.median(np.exp(logp[idx]))),
        exposure=float(len(r) * H / max(len(logp), 1)),
        tv_fg=tv, ratio_cv=cv, modes=modes, n_ev=b["n_ev"], h=b["h"],
        rate=float(b["n_ev"] / len(logp)),
        n2_p50=pc(n2, 50), n2_p95=pc(n2, 95),
        n2_sd=float(np.std(n2, ddof=1)) if len(n2) >= 5 else None,
        ap_p50=pc(ap, 50), ap_p95=pc(ap, 95),
        ap_sd=float(np.std(ap, ddof=1)) if len(ap) >= 5 else None,
        ap_count_ratio=float(np.median(apn) / max(len(r), 1)) if apn else None)


def one(sym, pack):
    logp, hi, lo = pack
    rng = np.random.default_rng(SEED + abs(hash(sym)) % 100_000)
    nulls = [q for q in (D.null_path(logp, rng) for _ in range(one.draws)) if q is not None]
    eval_idx = np.arange(WARMUP, len(logp), 25)
    out = []
    for hl in LAMS:
        ctx = context(logp, hl)
        if ctx is None:
            continue
        nctx = [context(q, hl) for q in nulls]
        for et, ks in KS.items():
            for k in ks:
                b = build(ctx, events_sigma(logp, et, k))
                if b is None:
                    continue
                nb = [z for z in (build(c, events_sigma(c["lp"], et, k))
                                  for c in nctx if c is not None) if z is not None]
                rots = [D.rotated_R(b, int(rng.integers(D.ROT_MIN, D.ROT_MAX)))
                        for _ in range(one.rots)]
                for H in HOLDS:
                    c = _cell(ctx, b, nb, rots, hi, lo, H, sym, et, hl, k, eval_idx)
                    if c:
                        out.append(c)
    return out


one.draws, one.rots = 20, 40


def report(rows):
    print("\n  P3 -- DID THE DENSITY HAVE SHAPE? (D387's worst bucket: TV 0.039, CV 0.096, 0 modes)")
    print(f"{'type':>10}{'k':>6}{'lam':>5}{'names':>7}{'rate/100':>10}{'TV(f,g)':>10}"
          f"{'ratio CV':>10}{'modes':>7}{'h/DX':>8}")
    for et, ks in KS.items():
        for k in ks:
            for hl in LAMS:
                q = [r for r in rows if r["etype"] == et and r["k"] == k
                     and r["hl"] == hl and r["H"] == HOLDS[0]]
                if len(q) < 20:
                    continue
                print(f"{et:>10}{k:>6.1f}{hl:>5}{len(q):>7}"
                      f"{100*np.median([r['rate'] for r in q]):>10.2f}"
                      f"{np.median([r['tv_fg'] for r in q]):>10.4f}"
                      f"{np.median([r['ratio_cv'] for r in q]):>10.3f}"
                      f"{np.median([r['modes'] for r in q]):>7.1f}"
                      f"{np.median([r['h'] for r in q])/DX:>8.1f}")

    print("\n  P1 -- GROSS per trade against each null's CENTRE, with a sign test across names")
    print(f"{'type':>10}{'k':>6}{'lam':>5}{'H':>4}{'n':>5}{'GROSS bp':>10}{'net bp':>9}"
          f"{'N2 p50':>9}{'z N2':>7}{'sign p':>10}{'A p50':>9}{'z A':>7}{'signA p':>10}{'cnt':>6}")
    from math import comb
    best = None
    for et, ks in KS.items():
        for k in ks:
            for hl in LAMS:
                for H in HOLDS:
                    q = [r for r in rows if r["etype"] == et and r["k"] == k and r["hl"] == hl
                         and r["H"] == H and r["n2_p50"] is not None and r["ap_p50"] is not None]
                    if len(q) < 20:
                        continue
                    g = 1e4 * np.mean([r["gross"] for r in q])
                    sp = np.nanmedian([r["spread_bp"] for r in q if r["spread_bp"]])
                    z2 = np.array([(r["gross"] - r["n2_p50"]) / max(r["n2_sd"], 1e-12) for r in q])
                    za = np.array([(r["gross"] - r["ap_p50"]) / max(r["ap_sd"], 1e-12) for r in q])
                    sp2 = sum(comb(len(q), i) for i in range(int((z2 > 0).sum()), len(q) + 1)) / 2 ** len(q)
                    spa = sum(comb(len(q), i) for i in range(int((za > 0).sum()), len(q) + 1)) / 2 ** len(q)
                    print(f"{et:>10}{k:>6.1f}{hl:>5}{H:>4}{len(q):>5}{g:>10.1f}{g-sp:>9.1f}"
                          f"{1e4*np.mean([r['n2_p50'] for r in q]):>9.1f}{np.median(z2):>7.2f}"
                          f"{sp2:>10.1e}{1e4*np.mean([r['ap_p50'] for r in q]):>9.1f}"
                          f"{np.median(za):>7.2f}{spa:>10.1e}"
                          f"{np.median([r['ap_count_ratio'] for r in q if r['ap_count_ratio']]):>6.2f}")
                    if best is None or np.median(za) > best[0]:
                        best = (np.median(za), et, k, hl, H, q, spa)
    if best is None:
        print("\n  no cell had enough names")
        return
    za, et, k, hl, H, q, spa = best
    print(f"\n  BEST BY THE A' MARGIN -- the load-bearing null: {et} k={k} lam={hl} H={H}")
    print(f"      z vs A' {za:+.2f}   sign test p {spa:.2e}   n {len(q)}")
    for nm, key in (("mean", "gross"), ("median", "med"), ("trimmed 1% both", "trim"),
                    ("ex-top 1%", "ex_top"), ("ex-bottom 1%", "ex_bot")):
        print(f"      {nm:>18}: {1e4*np.mean([r[key] for r in q]):>9.1f} bp")
    for nm, key in (("win rate", "win"), ("skew", "skew"), ("kurtosis", "kurt")):
        print(f"      {nm:>18}: {np.mean([r[key] for r in q]):>9.3f}")
    tot = np.array(sorted((r["gross"] * r["n"] for r in q), reverse=True))
    if tot.sum() > 0:
        cs = np.cumsum(tot) / tot.sum()
        print(f"      names to half the P&L: {int(np.searchsorted(cs,0.5))+1} of {len(q)}"
              f"   top-10 {100*tot[:10].sum()/tot.sum():.1f}%")
    px = np.array([r["px"] for r in q])
    gr = np.array([r["gross"] for r in q])
    m = px < np.median(px)
    print(f"      by PRICE: cheap {1e4*gr[m].mean():+.1f} bp   dear {1e4*gr[~m].mean():+.1f} bp"
          f"   (median ${np.median(px):.2f})")


def run(n_names, draws, rots, workers):
    t0 = time.time()
    one.draws, one.rots = draws, rots
    print(f"\nRUN -- D388. 2 types x 2 k x {len(LAMS)} lam x {len(HOLDS)} holds, "
          f"N2 {draws} draws, A' {rots} rotations, ONE gate")
    D.RP.assert_gates_passed(D.FIX)
    panel, cleaned = D.load_mined()
    syms, packs = [], {}
    for s in panel.symbols:
        p = D.name_bars(panel, cleaned, s)
        if p is not None:
            syms.append(s)
            packs[s] = p
    rng = np.random.default_rng(SEED)
    syms = list(np.array(syms)[rng.permutation(len(syms))[:n_names]])
    print(f"  [GATE] accepted. {len(syms)} names sampled of {len(packs)} eligible")

    rates = {}
    for s in syms[:min(len(syms), 200)]:
        lp = packs[s][0]
        for et, ks in KS.items():
            for k in ks:
                rates.setdefault(f"{et} k={k}", []).append(
                    len(events_sigma(lp, et, k)) / len(lp))
    sp_, mx_ = assert_RARE(rates)
    print(f"  [RARE]   worst rarity spread p90/p10 {sp_:.2f} (max 2.0); "
          f"worst single-name rate {100*mx_:.1f}%")
    probe = packs[syms[0]][0]
    print(f"  [SIGMA]  EW sd under a future shock: {assert_SIGMA(probe):.3e}")
    ctx0 = context(probe, 120)
    b0 = build(ctx0, events_sigma(probe, "move", 2.0))
    print(f"  [GATE1]  one gate for every arm; observed takes {assert_GATE1(b0)} entries")
    print(f"  [POOL]   worst A' count ratio {assert_POOL(b0, np.random.default_rng(5)):.2f}x")
    print(f"  [MASS]   int f vs the EW event rate: {D.assert_MASS(probe, 120, D.ETYPES[0]):.3e}")
    print(f"  [LAG]    independent re-derivation differs on "
          f"{D.assert_LAG(b0['R'], GATE(b0['R']), b0['x'])} bars")
    print(f"  [SIGN]   long into a rising price pays {D.assert_SIGN():+.4f}")
    print(f"  [REC]    {D.assert_REC(np.repeat(D.kernels(np.zeros(8), 0.02), 5, axis=0), 0.9):.3e}")
    print(f"  [SPLIT]  {D.assert_SPLIT():,} opens seen, holdout refused")
    print(f"  [X]      {assert_X(probe, np.random.default_rng(9))}")

    got = D.FN.parallel_map(one, [(s, packs[s]) for s in syms], workers=workers, progress="D388")
    rows = [r for sub in got.values() for r in sub]
    OUT.write_text(json.dumps(dict(
        study=388, kind="SIGNAL TEST (R15) -- rare events in sigma units, one gate",
        names=len(syms), draws=draws, rots=rots, lams=list(LAMS), holds=list(HOLDS),
        ks={k: list(v) for k, v in KS.items()}, rows=rows), indent=1))
    print(f"\n  wrote {OUT}  ({len(rows)} cells, {time.time()-t0:.0f}s)")
    report(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--names", type=int, default=600)
    ap.add_argument("--draws", type=int, default=20)
    ap.add_argument("--rots", type=int, default=40)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    print("D388  rare events in SIGMA units, ONE gate -- SIGNAL TEST")
    if a.audit:
        run(40, 5, 10, a.workers)
    elif a.run:
        run(a.names, a.draws, a.rots, a.workers)
    else:
        ap.print_help()
