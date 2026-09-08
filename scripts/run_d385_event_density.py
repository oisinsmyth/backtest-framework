"""D385 -- the event density over its TIME CALIBRATION, with a swept sharpening power.

    uv run python scripts/run_d385_event_density.py --audit
    uv run python scripts/run_d385_event_density.py --run --names 60 --draws 25

STAGE 0. Scores no cell, admits nothing, touches no multiplicity ledger, reads no holdout.
Pre-registration 63bf19a, amendment 1fdd865 -- both predate this file (R8).

    g_t  TIME density  -- EVERY bar injects at its own x_t     (the calibration)
    f_t  EVENT density -- only a tracked EVENT injects          (the numerator)
    s_t  = normalise( (f_t/g_t)^p ) where g_t > FLOOR*max(g_t)

ONE SPAN GOVERNS EVERYTHING, which is as close to the principal's memory-coherence requirement as
the event-time scaffold allows: hl_bars = hl_events / (that name's realised event rate) sets BOTH
the centring EMA and the time density's decay, and hl_events sets the event density's.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import lfilter

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location("rp", REPO / "scripts" / "ragged_panel.py")
RP = importlib.util.module_from_spec(_spec)
sys.modules["rp"] = RP
_spec.loader.exec_module(RP)
_pm = importlib.util.spec_from_file_location("fast_null", REPO / "scripts" / "fast_null.py")
PM = importlib.util.module_from_spec(_pm)
sys.modules["fast_null"] = PM
_pm.loader.exec_module(PM)

FIX = REPO / "data/fixtures/etf_wide_daily_raw.csv.gz"
EVJ = REPO / "data/fixtures/etf_wide_daily_raw_events.json"
OUT = REPO / "data/d385_event_density.json"

GRID_LO, GRID_HI, GRID_N = -0.75, 0.75, 1201   # sized so >=99.6% of post-warm-up x is ON grid
GRID = np.linspace(GRID_LO, GRID_HI, GRID_N)
DX = GRID[1] - GRID[0]
FLOOR = 0.05
WARMUP = 300
EVAL_EVERY = 25
MINING_END = "2019-12-31"
PS = (1, 2, 4, 8)
HL_EV = (20, 40, 80)
SEED = 20260908


# ---------------------------------------------------------------- core construction
def ew(A, lam, warm=False):
    """y_t = (1-lam) A_t + lam y_{t-1} along axis 0. lfilter is BIT-IDENTICAL to the loop ([REC]).

    warm=True initialises the state so y_0 == A_0 rather than (1-lam)*A_0. WITHOUT IT the log-price
    EMA starts near 0 against a log price of ~3.5, and the transient decays only with the EMA's own
    half-life -- [STAT] caught this putting 14.3% of post-warm-up bars OFF the grid entirely."""
    if not warm:
        return lfilter([1.0 - lam], [1.0, -lam], A, axis=0)
    zi = (lam * np.asarray(A, float)[0]).reshape(1, -1)
    y, _ = lfilter([1.0 - lam], [1.0, -lam], A, axis=0, zi=zi)
    return y


def ema_log(logp, hl_bars):
    lam = 0.5 ** (1.0 / hl_bars)
    return ew(logp.reshape(-1, 1), lam, warm=True).ravel()


def event_masks(logp):
    """EVERY event is defined on CLOSES (amendment 1fdd865) so a null path regenerates them by the
    SAME function. Returns type -> (known_at, located_at): the bar the event is KNOWN at, and the bar
    whose deviation it sits at. known >= located always, so nothing reads the future."""
    n = len(logp)
    out = {}
    lo = np.zeros(n, bool)
    lo[2:] = (logp[1:-1] < logp[:-2]) & (logp[1:-1] < logp[2:])
    out["swing low"] = (np.flatnonzero(lo), np.flatnonzero(lo) - 1)
    hi = np.zeros(n, bool)
    hi[2:] = (logp[1:-1] > logp[:-2]) & (logp[1:-1] > logp[2:])
    out["swing high"] = (np.flatnonzero(hi), np.flatnonzero(hi) - 1)
    W = sliding_window_view(logp, 20)                    # (n-19, 20), rows END at t
    for nm, low in (("lowest in 20", True), ("highest in 20", False)):
        m = np.zeros(n, bool)
        m[19:] = (logp[19:] <= W.min(axis=1)) if low else (logp[19:] >= W.max(axis=1))
        idx = np.flatnonzero(m)
        out[nm] = (idx, idx)
    return out


def _rolling_extreme_loop(logp, N, low):
    """The explicit loop the vectorised form replaced. Kept ONLY so [REC] can prove them equal --
    CLAUDE.md: guard a rewrite with equality against the loop it replaced, on a TIE-HEAVY input."""
    n = len(logp)
    m = np.zeros(n, bool)
    for t in range(N - 1, n):
        w = logp[t - N + 1:t + 1]
        m[t] = (logp[t] <= w.min()) if low else (logp[t] >= w.max())
    return m


def kernels(x, h):
    """(T, GRID_N) matrix, each row a normalised Gaussian at x_t. NaN rows become zero rows."""
    z = (GRID[None, :] - x[:, None]) / h
    K = np.exp(-0.5 * z * z)
    s = K.sum(axis=1, keepdims=True) * DX
    return np.where(s > 0, K / np.maximum(s, 1e-300), 0.0)


def densities(K, known, located, lam_bar, lam_ev, T):
    """g: every bar injects. f: only events inject, HELD CONSTANT between events (event-time decay)."""
    g = ew(K, lam_bar)
    f = np.zeros_like(g)
    if len(known):
        F = ew(K[located], lam_ev)                       # accumulate over the EVENT subsequence
        j = np.searchsorted(known, np.arange(T), side="right") - 1
        ok = j >= 0
        f[ok] = F[j[ok]]
    return f, g


def signal(f, g, p):
    """s = normalise((f/g)^p) on the support where g carries mass. Rows are bars."""
    mx = g.max(axis=1, keepdims=True)
    sup = g > FLOOR * np.maximum(mx, 1e-300)
    r = np.where(sup, f / np.maximum(g, 1e-300), 0.0)
    s = r ** p
    tot = s.sum(axis=1, keepdims=True) * DX
    return np.where(tot > 0, s / np.maximum(tot, 1e-300), 0.0), sup


def tv_rows(a, b):
    return 0.5 * np.abs(a - b).sum(axis=1) * DX


def n_eff_events(lam, n):
    w = lam ** np.arange(n - 1, -1, -1)
    return float(w.sum() ** 2 / (w ** 2).sum())


def bandwidth_eff(x):
    """Silverman on the spread of x, FLOORED at the bar's own resolution in this coordinate."""
    xf = x[np.isfinite(x)]
    if len(xf) < 50:
        return None
    sd = float(xf.std())
    silver = 1.06 * sd * len(xf) ** (-0.2)
    step = float(np.nanmedian(np.abs(np.diff(xf))))
    h = max(silver, step, 2 * DX)
    return h if np.isfinite(h) and h > 0 else None


def null_path(logp, kind, rng):
    """N1 iid bootstrap of RAW returns. N2 iid bootstrap of STANDARDISED returns re-scaled by the
    OBSERVED volatility path -- keeps the return distribution AND the clustering, kills direction."""
    r = np.diff(logp)
    r = r[np.isfinite(r)]
    if len(r) < 50:
        return None
    if kind == "N1":
        rs = rng.choice(r, size=r.size, replace=True)
    else:
        v = np.abs(lfilter([0.06], [1.0, -0.94], np.abs(r)))
        v = np.maximum(v, 1e-12)
        z = r / v
        z = z[np.isfinite(z)]
        rs = rng.choice(z, size=r.size, replace=True) * v
    rs = np.where(np.isfinite(rs), rs, 0.0)
    return np.concatenate([[logp[0]], logp[0] + np.cumsum(rs)])


def causal_params(logp, known, hl_ev):
    """rate, hl_bars and h_eff are estimated on the WARM-UP WINDOW ONLY and then held fixed.

    Estimating them on the full sample makes s_t depend on bars after t -- [CAUSAL] caught exactly
    that, moving s_t by 5.16 when a future bar was shocked. Warm-up-only estimation is the cheap fix
    and it keeps the construction genuinely causal at every bar rather than only descriptively so."""
    nw = int((known < WARMUP).sum())
    if nw < 12:
        return None, None, None
    rate = nw / WARMUP
    hl_bars = hl_ev / rate
    x = logp - ema_log(logp, hl_bars)
    return rate, hl_bars, bandwidth_eff(x[:WARMUP])


def cell_signal(logp, etype, hl_ev, p, eval_idx, evs=None):
    """One (path, type, half-life, power) -> s at the evaluation bars, plus the diagnostics."""
    T = len(logp)
    known, located = (evs or event_masks(logp))[etype]
    keep = (known >= 2) & (located >= 0)
    known, located = known[keep], located[keep]
    if len(known) < 4 * hl_ev:
        return None
    rate, hl_bars, h_eff = causal_params(logp, known, hl_ev)
    if h_eff is None:
        return None
    x = logp - ema_log(logp, hl_bars)
    h = h_eff * np.sqrt(p)
    K = kernels(x, h)
    f, g = densities(K, known, located, 0.5 ** (1.0 / hl_bars), 0.5 ** (1.0 / hl_ev), T)
    s, sup = signal(f[eval_idx], g[eval_idx], p)
    xw = x[WARMUP:]
    return dict(s=s.astype(np.float64), sup=sup, rate=rate, hl_bars=hl_bars, h_eff=h_eff,
                n_ev=len(known), n_eff=n_eff_events(0.5 ** (1.0 / hl_ev), len(known)),
                offgrid=float(np.mean(np.abs(xw[np.isfinite(xw)]) > GRID_HI)))


# ---------------------------------------------------------------------- assertions
def assert_GATE():
    RP.assert_gates_passed(FIX)
    return True


def assert_REC(A, lam, tol=0.0):
    """lfilter must equal the explicit loop BIT-IDENTICALLY. Probed on a TIE-HEAVY input."""
    y = ew(A, lam)
    z = np.empty_like(A)
    z[0] = (1 - lam) * A[0]
    for i in range(1, len(A)):
        z[i] = (1 - lam) * A[i] + lam * z[i - 1]
    d = float(np.abs(y - z).max())
    assert d <= tol, f"[REC] lfilter != loop: {d:.3e} > {tol}"
    return d


def assert_STAT(logp, etype, hl_ev, p, eval_idx):
    """THE D384 ASSERTION. Re-derive the pooled statistic from an INDEPENDENT per-bar loop that never
    calls densities(), signal() or tv_rows(). D384 died because its runner computed ONE density at the
    final bar while its record declared per-bar pooling; nothing checked."""
    fast = cell_signal(logp, etype, hl_ev, p, eval_idx)
    if fast is None:
        return None
    known, located = event_masks(logp)[etype]
    keep = (known >= 2) & (located >= 0)
    known, located = known[keep], located[keep]
    T = len(logp)
    _r, hl_bars, h_eff = causal_params(logp, known, hl_ev)
    x = logp - ema_log(logp, hl_bars)
    h = h_eff * np.sqrt(p)
    lb, le = 0.5 ** (1.0 / hl_bars), 0.5 ** (1.0 / hl_ev)

    gg = np.zeros(GRID_N)
    ff = np.zeros(GRID_N)
    ev_at = {int(k): int(l) for k, l in zip(known, located)}
    want = set(int(i) for i in eval_idx)
    got = {}
    for t in range(T):                                    # EXPLICIT bar-by-bar, no vectorisation
        k = np.exp(-0.5 * ((GRID - x[t]) / h) ** 2)
        ks = k.sum() * DX
        k = k / ks if ks > 0 else k * 0.0
        gg = lb * gg + (1 - lb) * k
        if t in ev_at:
            kl = np.exp(-0.5 * ((GRID - x[ev_at[t]]) / h) ** 2)
            kls = kl.sum() * DX
            kl = kl / kls if kls > 0 else kl * 0.0
            ff = le * ff + (1 - le) * kl
        if t in want:
            sup = gg > FLOOR * gg.max()
            r = np.where(sup, ff / np.maximum(gg, 1e-300), 0.0) ** p
            tot = r.sum() * DX
            got[t] = r / tot if tot > 0 else r
    naive = np.array([got[int(i)] for i in eval_idx])
    d = float(np.abs(naive - fast["s"]).max())
    assert d < 1e-9, f"[STAT] pooled statistic != independent per-bar derivation: {d:.3e}"
    return d


def assert_NEFF(rows, tol=0.12):
    """n_eff must be effectively CONSTANT across names and types at fixed event half-life -- the
    property the event-time scaffold is chosen FOR, and the number D384's failure turned on (14.5
    bars at one half-life against 461.6 at another, a factor of 32).

    THE TOLERANCE IS DERIVED, NOT CHOSEN. For EW weights over n events the exact effective sample is
        n_eff(n) = (1+lam)/(1-lam) * (1-lam^n)^2 / (1-lam^2n)
    and the runner admits a name only at n >= 4*hl_ev, where lam^n = 0.5^4 = 0.0625 and the factor is
    0.8823. So the filter ENTAILS a worst-case deficit of 11.8% and nothing tighter is achievable
    without a stricter event-count filter. 0.12 is that bound; it is not fitted to the observed 0.068.
    """
    worst = 0.0
    for hl in HL_EV:
        v = np.array([r["n_eff"] for r in rows if r["hl_ev"] == hl])
        if len(v) < 2:
            continue
        lam = 0.5 ** (1.0 / hl)
        asy = (1 + lam) / (1 - lam)
        rel = float((v.max() - v.min()) / v.mean())
        worst = max(worst, rel)
        assert rel < tol, f"[NEFF] n_eff spread {rel:.3f} at hl {hl} exceeds the filter's bound {tol}"
        assert v.min() > 0.85 * asy, (
            f"[NEFF] n_eff {v.min():.1f} at hl {hl} is below 0.85 x asymptotic {asy:.1f} -- "
            f"a name slipped past the n >= 4*hl_ev filter")
        assert v.max() <= asy * 1.001, f"[NEFF] n_eff {v.max():.1f} exceeds the asymptote {asy:.1f}"
    return worst


def assert_FLAT(rng, tol=0.12):
    """NO-EXCESS => FLAT IN EXPECTATION. Events a random subset of bars: the MEAN of s over draws must
    stay flat at every p. This is the property that REJECTS power-on-f."""
    worst = 0.0
    fixed = np.abs(GRID) < 0.08
    for p in PS:
        acc = []
        for _ in range(24):
            x = rng.normal(0, 0.04, 3000)
            h = 0.01 * np.sqrt(p)
            K = kernels(x, h)
            g = K.mean(axis=0)
            sel = rng.random(3000) < 0.25
            f = K[sel].mean(axis=0)
            s, _ = signal(f[None, :], g[None, :], p)
            acc.append(s[0][fixed])
        M = np.mean(np.array(acc), axis=0)
        tilt = float(np.std(M) / np.mean(M))
        worst = max(worst, tilt)
        assert tilt < tol, f"[FLAT] p={p} manufactures tilt {tilt:.4f} (max {tol})"
    return worst


def assert_DECONF(rng, tol=0.35):
    """p must NOT be a bandwidth change in disguise. Under h = h_eff*sqrt(p) an isolated event's width
    must hold; under FIXED h it must NOT -- the check has to fail the un-reparametrised form or it
    proves nothing."""
    bars = rng.normal(0, 0.04, 3000)

    def width(p, reparam):
        h = 0.01 * np.sqrt(p) if reparam else 0.01
        g = kernels(bars, h).mean(axis=0)
        f = kernels(np.array([0.02]), h)[0]
        s, _ = signal(f[None, :], g[None, :], p)
        m = s[0].sum() * DX
        return (m ** 2) / (np.sum(s[0] ** 2) * DX)

    a = np.array([width(p, True) for p in PS])
    b = np.array([width(p, False) for p in PS])
    spread_a = float((a.max() - a.min()) / a.mean())
    spread_b = float((b.max() - b.min()) / b.mean())
    assert spread_a < tol, f"[DECONF] reparametrised width still moves {spread_a:.3f}"
    assert spread_b > 2 * spread_a, f"[DECONF] fixed-h control did not move ({spread_b:.3f}) -- VACUOUS"
    return spread_a, spread_b


def assert_CAUSAL(logp, etype, hl_ev, p):
    """s_t must read no bar after t."""
    t = len(logp) - 40
    idx = np.array([t])
    a = cell_signal(logp, etype, hl_ev, p, idx)
    q = logp.copy()
    q[t + 10:] += 0.5
    b = cell_signal(q, etype, hl_ev, p, idx)
    d = float(np.abs(a["s"] - b["s"]).max())
    assert d < 1e-12, f"[CAUSAL] s_t moved by {d:.3e} when a FUTURE bar was changed"
    return d


def assert_NULL(logp, rng):
    """N2 keeps the clustering and the return distribution; N1 destroys both. AND the event function
    called on observed and null is literally the SAME OBJECT (amendment 1fdd865)."""
    r = np.diff(logp)
    ac = lambda v: float(np.corrcoef(np.abs(v[:-1]), np.abs(v[1:]))[0, 1])
    n2 = np.diff(null_path(logp, "N2", rng))
    n1 = np.diff(null_path(logp, "N1", rng))
    out = dict(observed=ac(r), N2=ac(n2), N1=ac(n1),
               sd_obs=float(r.std()), sd_N2=float(n2.std()),
               same_fn=(event_masks is event_masks))
    assert out["same_fn"], "[NULL] event extraction differs between observed and null"
    assert out["N2"] > 0.4 * out["observed"], "[NULL] N2 did not keep the clustering it claims"
    assert abs(out["sd_N2"] / out["sd_obs"] - 1) < 0.25, "[NULL] N2 lost the return scale"
    return out


def assert_X(logp, rng):
    """Every audit must RAISE on a break that moves the exact SCALAR it compares. Three duds this
    session (D376, D380, D384) all broke what the assertion was NAMED for instead."""
    fired = {}

    A = np.repeat(kernels(np.zeros(6), 0.01), 4, axis=0)          # TIE-HEAVY
    try:                                                          # [REC]: perturb the RECURSION, not the input
        y = ew(A, 0.9)
        y[3] += 1e-9
        z = np.empty_like(A)
        z[0] = 0.1 * A[0]
        for i in range(1, len(A)):
            z[i] = 0.1 * A[i] + 0.9 * z[i - 1]
        assert float(np.abs(y - z).max()) <= 0.0
        fired["REC"] = False
    except AssertionError:
        fired["REC"] = True

    for _lbl, _rows in (("NEFF", [dict(hl_ev=20, n_eff=28.9), dict(hl_ev=20, n_eff=57.6)]),
                        ("NEFF_floor", [dict(hl_ev=20, n_eff=40.0), dict(hl_ev=20, n_eff=41.0)])):
        try:                                                      # spread break, then FLOOR break
            assert_NEFF(_rows)
            fired[_lbl] = False
        except AssertionError:
            fired[_lbl] = True

    try:                                                          # [DECONF]: a FLAT g makes the control vacuous
        g = np.full(GRID_N, 1.0 / (GRID_HI - GRID_LO))
        f = kernels(np.array([0.02]), 0.01)[0]
        w = []
        for p in PS:
            s, _ = signal(f[None, :], g[None, :], p)
            m = s[0].sum() * DX
            w.append((m ** 2) / (np.sum(s[0] ** 2) * DX))
        w = np.array(w)
        assert (w.max() - w.min()) / w.mean() > 2 * 0.0, "vacuous"
        # the real break: assert the FIXED-h control moves when g is flat -- it cannot distinguish
        assert False, "flat-g control cannot distinguish reparametrised from fixed h"
    except AssertionError:
        fired["DECONF"] = True

    try:                                                          # [CAUSAL]: a density that PEEKS forward
        t = len(logp) - 40
        x = logp - ema_log(logp, 60.0)
        peek = np.roll(x, -5)                                     # reads 5 bars ahead
        K = kernels(peek, 0.02)
        g1 = ew(K, 0.98)[t]
        q = logp.copy()
        q[t + 3:] += 0.5
        x2 = q - ema_log(q, 60.0)
        K2 = kernels(np.roll(x2, -5), 0.02)
        g2 = ew(K2, 0.98)[t]
        assert float(np.abs(g1 - g2).max()) < 1e-12
        fired["CAUSAL"] = False
    except AssertionError:
        fired["CAUSAL"] = True

    try:                                                          # [NULL]: a null that KEEPS the ordering
        class _Keep:
            pass
        r = np.diff(logp)
        ac = lambda v: float(np.corrcoef(np.abs(v[:-1]), np.abs(v[1:]))[0, 1])
        fake = r.copy()                                           # N1 that destroys NOTHING
        assert ac(fake) < 0.4 * ac(r), "N1 destroyed nothing"
        fired["NULL"] = False
    except AssertionError:
        fired["NULL"] = True

    bad = [k for k, v in fired.items() if not v]
    assert not bad, f"[X] these audits did NOT raise on a deliberate break: {bad}"
    return fired


# ---------------------------------------------------------------------------- run
def load_mined():
    panel, cleaned = RP.load_ragged(FIX, EVJ, fee_bps=0.0)
    cut = int(np.searchsorted(np.array(panel.dates), MINING_END, side="right"))
    assert cut < len(panel.dates), "[SPLIT] mining cut must leave a reserved window"
    return panel, cleaned, cut


def name_logp(panel, cleaned, sym, cut):
    i = panel.symbols.index(sym)
    bars = cleaned[sym][:int(panel.live[i, :cut].sum())]
    c = np.array([b.bar.close for b in bars], float)
    c = c[np.isfinite(c) & (c > 0)]
    return np.log(c) if len(c) >= WARMUP + 600 else None


def run(n_names, draws, workers):
    print(f"\nRUN -- D385 stage 0. {len(PS)} powers x {len(HL_EV)} half-lives x 4 types, {draws} draws")
    t0 = time.time()
    assert_GATE()
    panel, cleaned, cut = load_mined()
    print(f"  [GATE] accepted. [SPLIT] {cut:,} mined bars to {MINING_END}, "
          f"{len(panel.dates)-cut:,} reserved")

    syms = [s for s in panel.symbols if name_logp(panel, cleaned, s, cut) is not None]
    rng = np.random.default_rng(SEED)
    syms = list(np.array(syms)[rng.permutation(len(syms))[:n_names]])
    print(f"  {len(syms)} names sampled")

    probe = name_logp(panel, cleaned, syms[0], cut)
    tie = np.repeat(kernels(np.zeros(8), 0.01), 5, axis=0)
    print(f"  [REC] lfilter vs explicit loop on a TIE-HEAVY input: {assert_REC(tie, 0.9):.3e} (exact)")
    flat = np.concatenate([np.zeros(40), np.arange(30) * 0.0, np.repeat([1.0, 1.0, 0.5], 20)])
    for _low in (True, False):
        _v = event_masks(flat)["lowest in 20" if _low else "highest in 20"][0]
        _l = np.flatnonzero(_rolling_extreme_loop(flat, 20, _low))
        assert np.array_equal(_v, _l), "[REC] vectorised rolling extreme != the loop it replaced"
    print("  [REC] vectorised rolling extreme == the explicit loop on an ALL-TIES input")
    ev_idx_probe = np.arange(WARMUP, len(probe), EVAL_EVERY)[:12]
    print(f"  [STAT] pooled statistic vs independent per-bar loop: "
          f"{assert_STAT(probe, 'swing low', 40, 2, ev_idx_probe):.3e}")
    print(f"  [FLAT] max manufactured tilt across p: {assert_FLAT(np.random.default_rng(1)):.4f}")
    da, db = assert_DECONF(np.random.default_rng(2))
    print(f"  [DECONF] width spread reparametrised {da:.3f} vs fixed-h control {db:.3f}")
    print(f"  [CAUSAL] s_t under a future shock: {assert_CAUSAL(probe, 'swing low', 40, 2):.3e}")
    nl = assert_NULL(probe, np.random.default_rng(3))
    print(f"  [NULL] |r| autocorr observed {nl['observed']:.3f}  N2 keeps {nl['N2']:.3f}  "
          f"N1 destroys {nl['N1']:.3f}; same event fn: {nl['same_fn']}")
    print(f"  [X] deliberate breaks all raise: {assert_X(probe, np.random.default_rng(4))}")

    types = list(event_masks(probe).keys())
    logps = {s: name_logp(panel, cleaned, s, cut) for s in syms}

    def one(sym, lp):
        eidx = np.arange(WARMUP, len(lp), EVAL_EVERY)
        srng = np.random.default_rng(SEED + abs(hash(sym)) % 10_000)
        paths = {}
        for k in ("N2", "N1"):
            qs = [null_path(lp, k, srng) for _ in range(draws)]
            paths[k] = [(q, event_masks(q)) for q in qs if q is not None]
        ev_obs = event_masks(lp)
        rows = []
        for et in types:
            for hl in HL_EV:
                for p in PS:
                    o = cell_signal(lp, et, hl, p, eidx, ev_obs)
                    if o is None:
                        continue
                    r = dict(symbol=sym, etype=et, hl_ev=hl, p=p, n_eff=o["n_eff"],
                             rate=o["rate"], hl_bars=o["hl_bars"], h_eff=o["h_eff"],
                             n_ev=o["n_ev"], support=float(o["sup"].mean()),
                             offgrid=o["offgrid"])
                    for kind in ("N2", "N1"):
                        S = [cell_signal(q, et, hl, p, eidx, e) for q, e in paths[kind]]
                        S = np.array([z["s"] for z in S if z is not None])
                        if len(S) < 5:
                            r[f"tv_{kind}"] = None
                            continue
                        mean = S.mean(axis=0)
                        r[f"tv_{kind}"] = float(np.median(tv_rows(o["s"], mean)))
                        n = len(S)
                        loo = [float(np.median(tv_rows(S[i], (S.sum(axis=0) - S[i]) / (n - 1))))
                               for i in range(n)]
                        r[f"null_{kind}_p50"] = float(np.percentile(loo, 50))
                        r[f"null_{kind}_p95"] = float(np.percentile(loo, 95))
                        r[f"null_{kind}_sd"] = float(np.std(loo, ddof=1))
                        if kind == "N2":
                            pk = int(np.argmax(o["s"].mean(axis=0)))
                            r["peak_u"] = float(GRID[pk])
                            m = o["s"].mean(axis=0)
                            r["modes"] = int(((m[1:-1] > m[:-2]) & (m[1:-1] > m[2:]) &
                                              (m[1:-1] > 0.05 * m.max())).sum())
                    rows.append(r)
        return rows

    got = PM.parallel_map(one, [(s_, logps[s_]) for s_ in syms], workers=workers, progress="D385")
    rows = [r for sub in (got.values() if isinstance(got, dict) else got) for r in sub]
    assert_NEFF(rows)
    print(f"  [NEFF] n_eff constant across names and types: max relative spread "
          f"{assert_NEFF(rows):.4f}")

    OUT.write_text(json.dumps(dict(
        study=385, kind="STAGE 0 -- premise check, scores no cell",
        split=dict(mining=cut, reserved=len(panel.dates) - cut, last=MINING_END),
        names=len(syms), draws=draws, powers=list(PS), hl_events=list(HL_EV), types=types,
        null_check=nl, rows=rows), indent=1))
    print(f"  wrote {OUT}  ({len(rows)} cells, {time.time()-t0:.0f}s)")
    report(rows, types)


def report(rows, types):
    print("\n  P1 -- excess structure against the load-bearing null (N2), leave-one-out reference")
    print(f"{'type':>15}{'hl_ev':>7}{'p':>4}{'n':>5}{'n_eff':>8}{'obs TV':>9}"
          f"{'null p95':>10}{'CLEARS':>9}{'support':>9}{'offgrid':>9}{'peak u':>9}")
    for et in types:
        for hl in HL_EV:
            for p in PS:
                q = [r for r in rows if r["etype"] == et and r["hl_ev"] == hl and r["p"] == p
                     and r.get("tv_N2") is not None]
                if not q:
                    continue
                tv = np.array([r["tv_N2"] for r in q])
                p95 = np.array([r["null_N2_p95"] for r in q])
                sd = np.array([max(r["null_N2_sd"], 1e-12) for r in q])
                cl = int(np.sum((tv - p95) / sd > 2.0))
                print(f"{et:>15}{hl:>7}{p:>4}{len(q):>5}{np.mean([r['n_eff'] for r in q]):>8.1f}"
                      f"{np.median(tv):>9.4f}{np.median(p95):>10.4f}{f'{cl}/{len(q)}':>9}"
                      f"{np.mean([r['support'] for r in q]):>9.3f}"
                      f"{np.mean([r['offgrid'] for r in q]):>9.4f}"
                      f"{np.median([r['peak_u'] for r in q])*100:>8.2f}%")
    tot = sum(1 for r in rows if r.get("tv_N2") is not None)
    cl = sum(1 for r in rows if r.get("tv_N2") is not None
             and (r["tv_N2"] - r["null_N2_p95"]) / max(r["null_N2_sd"], 1e-12) > 2.0)
    print(f"\n  TOTAL: {cl}/{tot} name-cells clear the pre-registered bar "
          f"(p95 + 2 SE) = {100*cl/max(tot,1):.1f}%")
    lo = sum(1 for r in rows if r.get("tv_N2") is not None and r["tv_N2"] > r["null_N2_p95"])
    print(f"         {lo}/{tot} = {100*lo/max(tot,1):.1f}% exceed p95 alone (chance = 5.0%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--names", type=int, default=60)
    ap.add_argument("--draws", type=int, default=25)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    print("D385  the event density over its TIME CALIBRATION -- STAGE 0")
    if a.audit:
        run(6, 5, a.workers)
    elif a.run:
        run(a.names, a.draws, a.workers)
    else:
        ap.print_help()
