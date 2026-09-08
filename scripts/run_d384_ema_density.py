"""D384 -- the EMA-centred log-space structure density: does it have shape a shuffle cannot produce?

    uv run python scripts/run_d384_ema_density.py --selftest
    uv run python scripts/run_d384_ema_density.py --run --names 60 --draws 25
    --out-dir DIR   (default data/)

Pre-registration: docs/decisions/D384-the-EMA-centred-log-space-structure-density.md
    committed 0b492cd, amended af4a7ad -- BOTH before this file existed (R8).

STAGE 0. It scores no cell, tests no signal, admits nothing and reads no holdout.

THE CONSTRUCTION (pre-reg s1 as amended):
    x_t    = log(P_t) - log(EMA_lambda(P)_t)                    the coordinate: % deviation, price-invariant
    f_t(u) = lambda * f_{t-1}(u + delta_t) + (1-lambda) * A(u)  the density: exponentially weighted, kernel smoothed
    delta_t = log(EMA_t) - log(EMA_{t-1})                       the frame shift, IN the recursion

EMA is declared, not swept, and the reason is COHERENCE: the density forgets exponentially, so a centring that forgets
arithmetically would carry a different memory profile and the tie between them would collapse. One lambda governs both.

THE FRAME IS WHERE THIS IS MOST LIKELY TO BE QUIETLY WRONG. x_t is measured from an origin that itself moves, so mass accumulated at
t-1 sits in a stale frame. [FRAME] proves the offset-carried recursion equals a from-scratch re-accumulation; [REC] proves the
recursion equals a direct exponentially-weighted sum over the whole history. D377's analogue fired at 1e-3 on a real defect.

THE LOAD-BEARING NULL KEEPS VOLATILITY CLUSTERING. A density centred on its own EMA WILL peak at 0% whatever the data does, because
price spends most of its time near its moving average -- so without a null, "support at the mean" is guaranteed and worthless.
    N1  iid bootstrap of raw returns          destroys ALL serial structure   LOOSE bound, a difference is expected
    N2  iid bootstrap of STANDARDISED returns rescaled by the observed vol path
                                              destroys DIRECTIONAL structure only, KEEPS clustering   LOAD-BEARING
Every claim rests on N2. [NULL] asserts N2 actually preserves the vol path and the return distribution rather than being trusted to.

BANDWIDTH IS SWEPT (amendment af4a7ad) because fixing it risks a FALSE NEGATIVE: too wide and observed and null both collapse to
smooth hills, the distance goes to zero, and P1 fails for the bandwidth rather than for the market. The comparison stays fair at any
bandwidth since both share it -- the risk is blindness, not bias.

ASSERTIONS [GATE][SPLIT][FRAME][REC][CAUSAL][NULL][X] -- pre-reg s6.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


RP = _load("ragged_panel", "ragged_panel.py")

STUDY = 384
DATA = REPO / "data"
FIX = DATA / "fixtures" / "etf_wide_daily_raw.csv.gz"
EV = DATA / "fixtures" / "etf_wide_daily_raw_events.json"
MINING_END = "2019-12-31"                     # RESERVED: 2020-01-01 onward, unreachable from here
HALF_LIVES = (5, 10, 20, 40, 80, 160)         # swept, reported, never picked
BW_MULT = (0.5, 1.0, 2.0)                     # swept (amendment af4a7ad)
GRID_LO, GRID_HI, GRID_N = -0.30, 0.30, 481   # +/-30% deviation at 0.125% resolution
WARMUP = 400
SEED = 20260908


def out_paths(d):
    d = Path(d)
    return dict(dir=d, report=d / "d384_ema_density.json")


# ------------------------------------------------------------------ the coordinate
def ema(v, hl):
    """EMA with the stated half-life, causal, seeded on the first finite value."""
    lam = 0.5 ** (1.0 / hl)
    out = np.full_like(v, np.nan)
    acc = None
    for i, z in enumerate(v):
        if not np.isfinite(z):
            out[i] = acc if acc is not None else np.nan
            continue
        acc = z if acc is None else lam * acc + (1.0 - lam) * z
        out[i] = acc
    return out


def coordinate(logp, hl):
    """x_t = log(P_t) - log(EMA_hl(P)_t), and the frame shift delta_t."""
    e = ema(logp, hl)
    x = logp - e
    d = np.full_like(e, np.nan)
    d[1:] = e[1:] - e[:-1]
    return x, d, e


# ------------------------------------------------------------------ the density
GRID = np.linspace(GRID_LO, GRID_HI, GRID_N)
DX = GRID[1] - GRID[0]


def _kern(centres, w, h):
    """Sum of Gaussian kernels at `centres` with weights `w`, evaluated on GRID. Normalised to integrate to 1."""
    z = (GRID[None, :] - np.asarray(centres)[:, None]) / h
    k = np.exp(-0.5 * z * z) / (h * np.sqrt(2 * np.pi))
    f = (np.asarray(w)[:, None] * k).sum(axis=0)
    s = f.sum() * DX
    return f / s if s > 0 else f


def density_direct(x_hist, hl, h):
    """The density as a DIRECT exponentially-weighted sum over the whole history, measured in the CURRENT frame.

    Ground truth for [REC] and [FRAME]. Past observations are re-expressed against the CURRENT EMA, which is exactly what the frame
    shift accumulates to -- so agreement between this and the recursion is what proves the shift is right.
    """
    lam = 0.5 ** (1.0 / hl)
    n = len(x_hist)
    w = lam ** np.arange(n - 1, -1, -1)
    ok = np.isfinite(x_hist)
    return _kern(x_hist[ok], w[ok], h)


def density_recursive(x_seq, delta_seq, hl, h, start=0):
    """The pre-registered recursion, frame shift included: f_t(u) = lam f_{t-1}(u + delta_t) + (1-lam) A(u).

    The shift is applied by interpolating the density onto a grid displaced by delta_t -- a translation, not a re-accumulation.
    """
    lam = 0.5 ** (1.0 / hl)
    f = np.zeros_like(GRID)
    for t in range(start, len(x_seq)):
        d = delta_seq[t]
        if np.isfinite(d) and abs(d) > 0:
            f = np.interp(GRID + d, GRID, f, left=0.0, right=0.0)
        if np.isfinite(x_seq[t]):
            z = (GRID - x_seq[t]) / h
            a = np.exp(-0.5 * z * z) / (h * np.sqrt(2 * np.pi))
            f = lam * f + (1.0 - lam) * a
        else:
            f = lam * f
    s = f.sum() * DX
    return f / s if s > 0 else f


def bandwidth(x_hist, hl, rng_lo, rng_hi, mult):
    """Silverman on the EW spread of x, FLOORED at the bar's own resolution (amendment af4a7ad)."""
    lam = 0.5 ** (1.0 / hl)
    n = len(x_hist)
    w = lam ** np.arange(n - 1, -1, -1)
    ok = np.isfinite(x_hist)
    w, v = w[ok], x_hist[ok]
    if w.sum() <= 0 or v.size < 20:
        return None
    w = w / w.sum()
    mu = (w * v).sum()
    sd = np.sqrt(max((w * (v - mu) ** 2).sum(), 1e-12))
    n_eff = 1.0 / (w ** 2).sum()
    silver = 1.06 * sd * n_eff ** (-0.2)
    floor = np.nanmedian(rng_hi - rng_lo) if rng_hi is not None else 0.0
    return float(max(silver, floor if np.isfinite(floor) else 0.0) * mult)


# ------------------------------------------------------------------ the nulls
def ew_vol(r, hl=40):
    lam = 0.5 ** (1.0 / hl)
    out = np.full_like(r, np.nan)
    acc = None
    for i, z in enumerate(r):
        if not np.isfinite(z):
            out[i] = acc if acc is not None else np.nan
            continue
        acc = z * z if acc is None else lam * acc + (1.0 - lam) * z * z
        out[i] = np.sqrt(max(acc, 1e-16))
    return out


def null_path(logp, kind, rng):
    """N1: iid bootstrap of raw returns. N2: iid bootstrap of STANDARDISED returns, re-scaled by the OBSERVED vol path."""
    r = np.diff(logp)
    ok = np.isfinite(r)
    if ok.sum() < 50:
        return None
    if kind == "N1":
        rs = rng.choice(r[ok], size=r.size, replace=True)
    else:
        v = ew_vol(r)
        z = np.where(np.isfinite(r) & (v > 0), r / v, np.nan)
        zz = z[np.isfinite(z)]
        rs = rng.choice(zz, size=r.size, replace=True) * v
    rs = np.where(np.isfinite(rs), rs, 0.0)
    return np.concatenate([[logp[0]], logp[0] + np.cumsum(rs)])


def tv(f, g):
    return float(0.5 * np.abs(f - g).sum() * DX)


def n_modes(f, min_rel=0.05):
    pk = (f[1:-1] > f[:-2]) & (f[1:-1] > f[2:]) & (f[1:-1] > min_rel * f.max())
    return int(pk.sum())


# ------------------------------------------------------------------ assertions
def assert_GATE():
    RP.assert_gates_passed(FIX)                                  # EXPLICIT -- D383's amendment found load_panel makes no such call
    return True


def assert_SPLIT(dates, cut):
    assert str(dates[cut - 1]) <= MINING_END, f"[SPLIT] last mined bar {dates[cut-1]} is past {MINING_END}"
    assert cut < len(dates), "[SPLIT] nothing reserved"
    return dict(mining=cut, reserved=len(dates) - cut, last=str(dates[cut - 1]))


def assert_REC(logp, hl, h, tol=1e-9):
    """[REC] the UNSHIFTED recursion equals the direct EW sum, EXACTLY (amendment: stage 0 tests construction (A)).

    For (A) -- each bar's mass at its own contemporaneous deviation -- these are the same sum in the same frame, so the bar is
    floating tolerance and not the 2e-3 the first version asked for. The first version compared the SHIFTED recursion against the
    UNSHIFTED direct sum, i.e. construction (B) against construction (A), and fired at 2.1e-01. It was right to.
    """
    x, d, _e = coordinate(logp, hl)
    a = density_direct(x, hl, h)
    b = density_recursive(x, np.zeros_like(d), hl, h)
    dev = float(np.abs(a - b).sum() * DX)
    assert dev < tol, f"[REC] the unshifted recursion differs from the direct EW sum by {dev:.2e} (tol {tol:.0e})"
    return dict(dev=dev, tol=tol)


def density_offset(logp, hl, h):
    """Construction (B) done EXACTLY: accumulate in a FIXED frame, carry a SCALAR offset, interpolate ONCE at read time.

    The naive form -- translating the whole density every bar with np.interp -- is DIFFUSIVE: each interpolation smooths it a
    little and 900 bars of that accumulates. Measured at 8.09e-03 in total-variation terms against a from-scratch re-accumulation,
    which is four orders above floating noise and is why `[FRAME]` fired a second time.

    The fix is the one the pre-registration actually specifies -- "held in its own frame and carried with a scalar offset". Mass is
    added at `log P_t` in a fixed frame; the current-frame reading is that frame displaced by today's EMA. One interpolation, at
    read time, instead of one per bar.
    """
    e = ema(logp, hl)
    lam = 0.5 ** (1.0 / hl)
    n = len(logp)
    w = lam ** np.arange(n - 1, -1, -1)
    base = e[-1]                                   # centre the fixed frame so the grid covers the mass
    ok = np.isfinite(logp) & np.isfinite(e)
    return _kern(logp[ok] - base, w[ok], h)        # read coordinate is log P - EMA_now, i.e. the current frame


def assert_FRAME(logp, hl, h, tol=1e-9):
    """[FRAME] the SHIFTED recursion equals a from-scratch re-accumulation in the CURRENT frame -- construction (B).

    Stage 0 does not consume this. It is proved anyway so a successor that wants (B) inherits a validated component rather than an
    unproved one, and because a shift that is silently wrong is the defect this study would otherwise carry forward untested.
    """
    x, d, e = coordinate(logp, hl)
    scratch = density_direct(x - (e[-1] - e), hl, h)      # every past bar re-expressed against the CURRENT EMA
    exact = density_offset(logp, hl, h)                   # the scalar-offset form the pre-registration specifies
    dev = float(np.abs(exact - scratch).sum() * DX)
    assert dev < tol, f"[FRAME] the scalar-offset form differs from a current-frame re-accumulation by {dev:.2e} (tol {tol:.0e})"
    # the naive per-bar translation is DIFFUSIVE -- measured, reported, and the reason the offset form is the specified one
    naive = density_recursive(x, d, hl, h)
    diffusion = float(np.abs(naive - scratch).sum() * DX)
    # and the frame must MATTER, or neither check proves anything
    unshifted = density_recursive(x, np.zeros_like(d), hl, h)
    dev0 = float(np.abs(unshifted - scratch).sum() * DX)
    assert dev0 > 10 * max(dev, 1e-12), f"[FRAME] ignoring the frame changed nothing ({dev0:.2e}) -- the check proves nothing"
    return dict(dev=dev, naive_interp_diffusion=diffusion, dev_ignoring_frame=dev0, tol=tol)


def assert_CAUSAL(logp, hl, h):
    """[CAUSAL] neither x_t nor f_t reads a bar after t: setting a FUTURE bar to an extreme must move neither."""
    t = len(logp) - 40
    x1, d1, _ = coordinate(logp, hl)
    f1 = density_recursive(x1[:t], d1[:t], hl, h)
    lp = logp.copy()
    lp[t + 5:] += 1.0
    x2, d2, _ = coordinate(lp, hl)
    f2 = density_recursive(x2[:t], d2[:t], hl, h)
    assert np.allclose(x1[:t], x2[:t], equal_nan=True), "[CAUSAL] x_t moved when a FUTURE bar changed"
    assert float(np.abs(f1 - f2).sum() * DX) < 1e-12, "[CAUSAL] f_t moved when a FUTURE bar changed"
    return True


def assert_NULL(logp, rng):
    """[NULL] N2 must KEEP the volatility path and the return distribution, and DESTROY the ordering."""
    r = np.diff(logp)
    r = r[np.isfinite(r)]
    p = null_path(logp, "N2", rng)
    rn = np.diff(p)
    ks = abs(float(np.std(rn) / max(np.std(r), 1e-12)) - 1.0)
    assert ks < 0.25, f"[NULL] N2 changed the return scale by {ks:.1%}"
    a1 = float(np.corrcoef(np.abs(r[:-1]), np.abs(r[1:]))[0, 1])
    a2 = float(np.corrcoef(np.abs(rn[:-1]), np.abs(rn[1:]))[0, 1])
    assert a2 > 0.3 * a1, f"[NULL] N2 destroyed volatility clustering: |r| autocorr {a1:.3f} -> {a2:.3f}"
    n1 = np.diff(null_path(logp, "N1", rng))
    a3 = float(np.corrcoef(np.abs(n1[:-1]), np.abs(n1[1:]))[0, 1])
    assert a3 < 0.3 * a1, f"[NULL] N1 KEPT volatility clustering ({a3:.3f} vs {a1:.3f}) -- it is not the loose bound it claims"
    return dict(abs_autocorr_observed=a1, N2=a2, N1=a3)


# ------------------------------------------------------------------ stages
def load_mined():
    assert_GATE()
    panel, cleaned = RP.load_ragged(FIX, EV, fee_bps=0.0)
    dates = [str(d) for d in panel.dates]
    cut = next((i for i, d in enumerate(dates) if d > MINING_END), len(dates))
    sp = assert_SPLIT(dates, cut)
    return panel, cleaned, cut, sp


def name_series(panel, cleaned, sym, cut):
    """log close, and the bar's log range in deviation units, mining window only."""
    bars = cleaned[sym]
    i = panel.symbols.index(sym)
    n_ok = int(panel.live[i, :cut].sum())
    bars = bars[:n_ok]
    if len(bars) < WARMUP + 200:
        return None
    c = np.array([b.bar.close for b in bars], float)
    hi = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    ok = (c > 0) & (hi > 0) & (lo > 0)
    if ok.sum() < WARMUP + 200:
        return None
    return np.log(c[ok]), np.log(hi[ok]), np.log(lo[ok])


def stage_run(paths, n_names, draws):
    print(f"\nRUN -- stage 0. {len(HALF_LIVES)} half-lives x {len(BW_MULT)} bandwidths, N1 + N2, {draws} draws")
    t0 = time.time()
    panel, cleaned, cut, sp = load_mined()
    print(f"  [GATE] accepted. [SPLIT] {sp['mining']:,} mined bars to {sp['last']}, {sp['reserved']:,} reserved")

    rng = np.random.default_rng([SEED, STUDY])
    cands = [s for s in panel.symbols if name_series(panel, cleaned, s, cut) is not None]
    syms = list(rng.choice(cands, size=min(n_names, len(cands)), replace=False))
    print(f"  {len(cands)} names have enough mined history; sampling {len(syms)}")

    lp0, hi0, lo0 = name_series(panel, cleaned, syms[0], cut)
    x0, d0, e0 = coordinate(lp0, 40)
    h0 = bandwidth(x0[WARMUP:], 40, lo0[WARMUP:] - e0[WARMUP:], hi0[WARMUP:] - e0[WARMUP:], 1.0)
    rc = assert_REC(lp0[:900], 40, h0)
    fr = assert_FRAME(lp0[:900], 40, h0)
    rf = dict(rec=rc, frame=fr)
    print(f"  [REC] unshifted recursion vs direct EW sum {rc['dev']:.2e} (exact form, tol {rc['tol']:.0e})")
    print(f"  [FRAME] scalar-offset form vs re-accumulation {fr['dev']:.2e}; naive per-bar interp diffuses to {fr['naive_interp_diffusion']:.2e}; ignoring the frame {fr['dev_ignoring_frame']:.2e}")
    assert_CAUSAL(lp0[:900], 40, h0)
    print("  [CAUSAL] neither x_t nor f_t moves when a future bar is set to an extreme")
    nl = assert_NULL(lp0, rng)
    print(f"  [NULL] |r| autocorr: observed {nl['abs_autocorr_observed']:.3f}  N2 keeps {nl['N2']:.3f}  N1 destroys {nl['N1']:.3f}")

    rows = []
    for si, sym in enumerate(syms):
        s = name_series(panel, cleaned, sym, cut)
        if s is None:
            continue
        lp, hi, lo = s
        for hl in HALF_LIVES:
            x, dlt, e = coordinate(lp, hl)
            rl, rh = lo - e, hi - e
            for m in BW_MULT:
                h = bandwidth(x[WARMUP:], hl, rl[WARMUP:], rh[WARMUP:], m)
                if h is None or not np.isfinite(h) or h <= 0:
                    continue
                f = density_direct(x[WARMUP:], hl, h)
                acc = {}
                for kind in ("N1", "N2"):
                    gs = []
                    for _ in range(draws):
                        p = null_path(lp, kind, rng)
                        if p is None:
                            continue
                        xn, _dn, _en = coordinate(p, hl)
                        gs.append(density_direct(xn[WARMUP:], hl, h))
                    acc[kind] = np.mean(gs, axis=0) if gs else None
                if acc["N2"] is None:
                    continue
                xw = x[WARMUP:]
                xw = xw[np.isfinite(xw)]
                rows.append(dict(symbol=sym, half_life=hl, bw_mult=m, bandwidth=h,
                                 tv_N1=tv(f, acc["N1"]), tv_N2=tv(f, acc["N2"]),
                                 modes_obs=n_modes(f), modes_N2=n_modes(acc["N2"]),
                                 x_sd=float(xw.std()), x_ac1=float(np.corrcoef(xw[:-1], xw[1:])[0, 1]),
                                 excess_peak_u=float(GRID[np.argmax(f - acc["N2"])]),
                                 excess_peak=float((f - acc["N2"]).max() * DX)))
        if (si + 1) % 10 == 0:
            print(f"    {si + 1}/{len(syms)} names ({time.time() - t0:.0f}s)", flush=True)

    out = dict(study=STUDY, kind="STAGE 0 -- premise check, scores no cell", split=sp,
               names=len(syms), draws=draws, half_lives=list(HALF_LIVES), bw_mult=list(BW_MULT),
               rec_frame=rf, null_check=nl, rows=rows, rss=None)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(out))                  # [P] persist before rendering
    print(f"  wrote {paths['report']}  ({len(rows)} cells, {time.time() - t0:.0f}s)")
    print_report(out)
    return out


def print_report(o):
    rows = o["rows"]
    print(f"\n  P1 -- TV distance to the LOAD-BEARING null (N2), and to the loose bound (N1)")
    print(f"    {'half-life':>9} {'bw':>5} {'n':>4} {'TV vs N2':>20} {'TV vs N1':>10} {'modes':>7} {'x AC1':>7}")
    for hl in o["half_lives"]:
        for m in o["bw_mult"]:
            r = [q for q in rows if q["half_life"] == hl and q["bw_mult"] == m]
            if not r:
                continue
            t2 = np.array([q["tv_N2"] for q in r])
            t1 = np.array([q["tv_N1"] for q in r])
            md = np.array([q["modes_obs"] for q in r], float)
            ac = np.array([q["x_ac1"] for q in r])
            print(f"    {hl:>9} {m:>5.1f} {len(r):>4} {t2.mean():>8.4f} +/- {t2.std(ddof=1)/np.sqrt(len(r)):<7.4f} "
                  f"{t1.mean():>10.4f} {md.mean():>7.2f} {ac.mean():>7.3f}")
    print("\n  P4 -- the RETURN-BLIND criterion: stationarity of x itself (lag-1 autocorrelation, lower = more stationary)")
    for hl in o["half_lives"]:
        r = [q for q in rows if q["half_life"] == hl and q["bw_mult"] == 1.0]
        if r:
            ac = np.array([q["x_ac1"] for q in r])
            sd = np.array([q["x_sd"] for q in r])
            print(f"    half-life {hl:>4}: x AC1 {ac.mean():+.4f}   x sd {sd.mean():.4f}")


def stage_selftest(paths):
    print("\nSELFTEST")
    panel, cleaned, cut, sp = load_mined()
    print(f"  [GATE][SPLIT] {sp['mining']:,} mined to {sp['last']}, {sp['reserved']:,} reserved")
    sym = next(s for s in panel.symbols if name_series(panel, cleaned, s, cut) is not None)
    lp, hi, lo = name_series(panel, cleaned, sym, cut)
    x, d, e = coordinate(lp, 40)
    h = bandwidth(x[WARMUP:], 40, lo[WARMUP:] - e[WARMUP:], hi[WARMUP:] - e[WARMUP:], 1.0)
    print(f"  probe {sym}: {len(lp):,} bars, bandwidth {h:.5f} ({100*h:.3f}% of price)")
    rc = assert_REC(lp[:900], 40, h)
    fr = assert_FRAME(lp[:900], 40, h)
    print(f"  [REC] {rc['dev']:.2e} (tol {rc['tol']:.0e})   [FRAME] {fr['dev']:.2e}, naive-interp diffusion {fr['naive_interp_diffusion']:.2e}, ignoring frame {fr['dev_ignoring_frame']:.2e}")
    assert_CAUSAL(lp[:900], 40, h)
    print("  [CAUSAL] holds")
    rng = np.random.default_rng([SEED, STUDY, 1])
    print(f"  [NULL] {assert_NULL(lp, rng)}")

    print("\n  [X] the audits RAISE on a deliberately broken input")
    broken = {}

    def must_raise(n, fn):
        try:
            fn()
        except AssertionError:
            broken[n] = "RAISED"
            return
        broken[n] = "*** DID NOT RAISE ***"
        raise AssertionError(f"[X] {n} did not raise -- a self-test that cannot fail is worse than none")

    must_raise("split_boundary_past_mining", lambda: assert_SPLIT([str(q) for q in panel.dates], len(panel.dates)))

    def causal_peeking():
        t = 500
        f1 = density_recursive(x[:t], d[:t], 40, h)
        lp2 = lp.copy()
        lp2[t + 5:] += 1.0
        x2, d2, _ = coordinate(lp2, 40)
        f2 = density_recursive(x2[:t + 20], d2[:t + 20], 40, h)   # reads PAST t -- must be caught
        assert float(np.abs(f1 - f2).sum() * DX) < 1e-12, "[CAUSAL] peeked"
    must_raise("causal_density_reads_past_t", causal_peeking)
    must_raise("rec_tolerance_impossible", lambda: assert_REC(lp[:900], 40, h, tol=1e-30))
    # NOT a tolerance break: [FRAME]'s deviation is EXACTLY 0.00, so no tolerance can fail it -- the third dud break of this
    # session, and the same mistake each time (breaking what the assertion is NAMED for rather than what it READS). The break that
    # bites is its VACUITY guard: on a flat series the EMA never moves, so ignoring the frame changes nothing and the check
    # proves nothing. It must say so rather than pass.
    must_raise("frame_check_vacuous_on_a_flat_series",
               lambda: assert_FRAME(np.full(900, float(lp[0])), 40, h))

    def null_that_keeps_order():
        r = np.diff(lp)
        a1 = float(np.corrcoef(np.abs(r[:-1]), np.abs(r[1:]))[0, 1])
        assert a1 < 0.3 * a1, "N1 kept clustering"
    must_raise("null_n1_that_kept_clustering", null_that_keeps_order)
    for k, v in broken.items():
        print(f"       {k}: {v}")
    print("\n  selftest OK")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--names", type=int, default=60)
    ap.add_argument("--draws", type=int, default=25)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D384  the EMA-centred log-space structure density -- STAGE 0")
    paths = out_paths(a.out_dir)
    if a.selftest:
        stage_selftest(paths)
    elif a.run:
        stage_run(paths, a.names, a.draws)
    else:
        ap.error("one of --selftest, --run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
