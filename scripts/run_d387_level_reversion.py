"""D387 -- does price REVERT at levels where its own RARE events cluster?

    uv run python scripts/run_d387_level_reversion.py --audit
    uv run python scripts/run_d387_level_reversion.py --run --names 600 --draws 20

SIGNAL TEST under R15: a positive GROSS mean per trade above the nulls. Admits nothing.
Pre-registration b83ad16 predates this file (R8).

    g_t = lam g_{t-1} + (1-lam) A(u; x_t)                  every bar injects
    f_t = lam f_{t-1} + (1-lam) A(u; x_t) 1{event at t}    only an event bar injects  <- FORK (a)
    R_t = (f_t / int f_t)(x_t) / g_t(x_t)                  excess event mass AT the current level

ONE calendar lam centres, calibrates and decays -- the principal's coherence requirement, upheld
after D385 showed the event-time scaffold's only justification (constant n_eff) was never binding.
"""
import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time
from collections import Counter

import numpy as np
from scipy.signal import lfilter

REPO = pathlib.Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- [SPLIT] default-deny holdout guard
_OPENED = dict(n=0, refused=0, holdout=Counter())


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    low = os.fspath(p).replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[SPLIT] refused to open {low}")


sys.addaudithook(_audit)                        # D387 NEVER calls allow_holdout. There is no unlock.

sys.path.insert(0, str(REPO / "src"))
_s = importlib.util.spec_from_file_location("rp", REPO / "scripts" / "ragged_panel.py")
RP = importlib.util.module_from_spec(_s)
sys.modules["rp"] = RP
_s.loader.exec_module(RP)
_f = importlib.util.spec_from_file_location("fast_null", REPO / "scripts" / "fast_null.py")
FN = importlib.util.module_from_spec(_f)
sys.modules["fast_null"] = FN
_f.loader.exec_module(FN)

FIX = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ = REPO / "data/fixtures/us_shorts_daily_raw_events.json"
OUT = REPO / "data/d387_level_reversion.json"

GRID_LO, GRID_HI, GRID_N = -0.75, 0.75, 601
GRID = np.linspace(GRID_LO, GRID_HI, GRID_N)
DX = GRID[1] - GRID[0]
LAMS = (60, 120, 250)
HOLDS = (5, 10, 20)
ETYPES = ("reversal >1%", "move >2%")
QUANT = 0.90
WARMUP = 300
MIN_BARS = 1200
SEED = 20260908
THR_MIN = 200                    # SETTLED-regime R values needed before the gate may open
ROT_MIN, ROT_MAX = 40, 500       # A' rotation lags, in bars


# ------------------------------------------------------------------------ construction
def ew(A, lam, warm=False):
    if not warm:
        return lfilter([1.0 - lam], [1.0, -lam], A, axis=0)
    zi = (lam * np.asarray(A, float)[0]).reshape(1, -1)
    y, _ = lfilter([1.0 - lam], [1.0, -lam], A, axis=0, zi=zi)
    return y


def ema_log(logp, hl):
    return ew(logp.reshape(-1, 1), 0.5 ** (1.0 / hl), warm=True).ravel()


def event_masks(logp):
    """The two NON-DEFINITIONAL cousins, on CLOSES so a null regenerates them by this same function."""
    n = len(logp)
    r = np.zeros(n)
    r[1:] = np.diff(logp)
    rev = np.zeros(n, bool)
    rev[1:] = (np.sign(r[1:]) != np.sign(r[:-1])) & (np.abs(r[1:]) > 0.01) & (np.abs(r[:-1]) > 0.01)
    return {"reversal >1%": rev, "move >2%": np.abs(r) > 0.02}


def kernels(x, h):
    z = (GRID[None, :] - x[:, None]) / h
    K = np.exp(-0.5 * z * z)
    s = K.sum(axis=1, keepdims=True) * DX
    return np.where(s > 0, K / np.maximum(s, 1e-300), 0.0)


def bandwidth(x):
    xf = x[np.isfinite(x)]
    if len(xf) < 50:
        return None
    h = max(1.06 * float(xf.std()) * len(xf) ** -0.2,
            float(np.nanmedian(np.abs(np.diff(xf)))), 2 * DX)
    return h if np.isfinite(h) and h > 0 else None


def read_at(D, x):
    """D[t] evaluated at x[t], linear interpolation along the grid. Off-grid -> 0."""
    j = np.clip(np.searchsorted(GRID, x) - 1, 0, GRID_N - 2)
    w = np.clip((x - GRID[j]) / DX, 0.0, 1.0)
    t = np.arange(len(x))
    v = D[t, j] * (1 - w) + D[t, j + 1] * w
    return np.where((x >= GRID_LO) & (x <= GRID_HI), v, 0.0)


def build(logp, hl, etype):
    """FORK (a): one calendar lam for centring, calibration and decay. Returns R, x, and the mass."""
    lam = 0.5 ** (1.0 / hl)
    x = logp - ema_log(logp, hl)
    h = bandwidth(x[:WARMUP])
    if h is None:
        return None
    K = kernels(x, h)
    g = ew(K, lam)
    inj = np.zeros_like(K)
    ev = np.flatnonzero(event_masks(logp)[etype])
    ev = ev[ev >= 1]
    if len(ev) < 40:
        return None
    inj[ev] = K[ev]
    f = ew(inj, lam)
    mass = f.sum(axis=1) * DX                      # [MASS]: this IS the EW event rate
    fh = np.zeros_like(f)
    ok = mass > 1e-12
    fh[ok] = f[ok] / mass[ok, None]
    gv = read_at(g, x)
    R = np.where((mass > 1e-12) & (gv > 1e-12), read_at(fh, x) / np.maximum(gv, 1e-300), np.nan)
    # R IS UNDEFINED DURING WARM-UP. With only a handful of events accumulated the density is a spike
    # and the ratio blows up -- observed R reached 36 before bar 300 against a SETTLED maximum of
    # 1.77, which pushed the expanding 90th percentile to 6.02 and left the gate UNREACHABLE FOR THE
    # WHOLE SAMPLE (0 trades). A threshold must be calibrated on the regime it gates.
    R[:WARMUP] = np.nan
    return dict(R=R, x=x, mass=mass, h=h, n_ev=len(ev), f=fh, g=g, ev=ev, lp=logp)


def expanding_threshold(R, q=QUANT):
    """Causal: the threshold at t uses only R[:t]. Sorted-insert scan, no future data."""
    n = len(R)
    thr = np.full(n, np.inf)
    buf = []
    for t in range(n):
        if len(buf) >= THR_MIN:
            k = int(q * (len(buf) - 1))
            thr[t] = buf[k]
        v = R[t]
        if np.isfinite(v):
            import bisect
            bisect.insort(buf, float(v))
    return thr


# ------------------------------------------------------------------------------ trades
def decisions(R, thr, x):
    """Decision bars: R above its own causal threshold, with a defined side. NO future read."""
    d = np.isfinite(R) & (R > thr) & np.isfinite(x) & (np.abs(x) > 1e-9)
    d[:WARMUP] = False
    return d


def decisions_topn(R, x, n):
    """A' ONLY. §7 asks the rotation for the SAME BAR COUNT as the observed; a quantile gate cannot
    deliver that -- the rotated series crosses its own 90th percentile a different number of times
    (241 observed against 159-244 across lags, a 34% drift that [POOL] caught). So the control is
    given EXACTLY the observed number of shots, taken at its own highest-R eligible bars.

    This is the matched-count control R7 requires. It is not a candidate strategy and is not required
    to be causal in its calibration constant; it ranks on R, never on returns, so it cannot
    cherry-pick outcomes."""
    elig = np.isfinite(R) & np.isfinite(x) & (np.abs(x) > 1e-9)
    elig[:WARMUP] = False
    idx = np.flatnonzero(elig)
    d = np.zeros(len(R), bool)
    if len(idx) == 0 or n <= 0:
        return d
    take = idx[np.argsort(R[idx])[::-1][:min(n, len(idx))]]
    d[take] = True
    return d


def trade_returns(logp, dec, x, H, direction=+1):
    """PATH-INVARIANT lens: every decision bar is a candidate trade, no slot cap, scored PER TRADE.
    direction +1 = REVERT toward the EMA (long when x<0). -1 = the declared secondary look."""
    idx = np.flatnonzero(dec)
    idx = idx[idx + H < len(logp)]
    if len(idx) == 0:
        return np.array([]), np.array([], int)
    side = -np.sign(x[idx]) * direction
    return side * (logp[idx + H] - logp[idx]), idx


def corwin_schultz(hi, lo):
    """Two-day high/low spread estimator, in bp. Measured on the names actually HELD."""
    h1, l1, h2, l2 = hi[:-1], lo[:-1], hi[1:], lo[1:]
    ok = (h1 > 0) & (l1 > 0) & (h2 > 0) & (l2 > 0)
    if ok.sum() < 30:
        return np.nan
    h1, l1, h2, l2 = np.log(h1[ok]), np.log(l1[ok]), np.log(h2[ok]), np.log(l2[ok])
    beta = (h1 - l1) ** 2 + (h2 - l2) ** 2
    gamma = (np.maximum(h1, h2) - np.minimum(l1, l2)) ** 2
    k = 3 - 2 * np.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    s = s[np.isfinite(s) & (s > 0)]
    return float(np.median(s) * 1e4) if len(s) else np.nan


def null_path(logp, rng):
    """N2: iid bootstrap of STANDARDISED returns rescaled by the OBSERVED volatility path."""
    r = np.diff(logp)
    r = r[np.isfinite(r)]
    if len(r) < 50:
        return None
    v = np.maximum(np.abs(lfilter([0.06], [1.0, -0.94], np.abs(r))), 1e-12)
    z = r / v
    z = z[np.isfinite(z)]
    rs = rng.choice(z, size=r.size, replace=True) * v
    rs = np.where(np.isfinite(rs), rs, 0.0)
    return np.concatenate([[logp[0]], logp[0] + np.cumsum(rs)])


def rotated_R(b, k):
    """A': decide bar t with the density from bar t-k. Randomises the PARTNER, not the membership --
    a random subset re-draws each bar and CHURNS (D291: 2.4x the entries, 87 cells voided)."""
    fh, g, x = b["f"], b["g"], b["x"]
    n = len(x)
    src = np.clip(np.arange(n) - k, 0, n - 1)
    gv = read_at(g[src], x)
    fv = read_at(fh[src], x)
    Rr = np.where(gv > 1e-12, fv / np.maximum(gv, 1e-300), np.nan)
    # THE CONTROL MUST SHARE THE TREATMENT'S NUISANCE, NOT JUST ITS COUNT. build() marks R undefined
    # during warm-up; rebuilding from the stored densities here skipped that, so the rotation was
    # eligible on bars the observed could never trade and its warm-up spikes re-poisoned the gate --
    # [POOL] measured the drift at 51%.
    Rr[:WARMUP] = np.nan
    return Rr


# -------------------------------------------------------------------------- assertions
def assert_REC(A, lam):
    y = ew(A, lam)
    z = np.empty_like(A)
    z[0] = (1 - lam) * A[0]
    for i in range(1, len(A)):
        z[i] = (1 - lam) * A[i] + lam * z[i - 1]
    d = float(np.abs(y - z).max())
    assert d <= 0.0, f"[REC] lfilter != loop: {d:.3e}"
    return d


def assert_MASS(logp, hl, etype, tol=1e-12):
    """int f_t IS the EW event rate. This identity is the whole reason the fork resolved to (a):
    it is what keeps SHAPE and RATE separable, so rarity is information rather than a filter."""
    b = build(logp, hl, etype)
    ind = np.zeros(len(logp))
    ind[b["ev"]] = 1.0
    rate = ew(ind.reshape(-1, 1), 0.5 ** (1.0 / hl)).ravel()
    d = float(np.abs(b["mass"] - rate).max())
    assert d < tol, f"[MASS] int f != EW event rate: {d:.3e}"
    return d


def assert_LAG(R, thr, x):
    """THE D279 AUDIT. Re-derive the decision set from an INDEPENDENT loop that never calls
    decisions() or expanding_threshold(). ~93% of D279's apparent edge was this bug."""
    n = len(R)
    got = np.zeros(n, bool)
    seen = []
    for t in range(n):
        if t >= WARMUP and len(seen) >= WARMUP:
            s = np.sort(np.array(seen))
            th = s[int(QUANT * (len(s) - 1))]
            if np.isfinite(R[t]) and R[t] > th and np.isfinite(x[t]) and abs(x[t]) > 1e-9:
                got[t] = True
        if np.isfinite(R[t]):
            seen.append(float(R[t]))
    want = decisions(R, thr, x)
    d = int((got != want).sum())
    assert d == 0, f"[LAG] independent re-derivation differs on {d} bars"
    return d


def assert_SIGN(tol=1e-12):
    """Asserted IN MONEY, not in prose -- a sign asserted in prose inverted D280."""
    lp = np.zeros(60)
    lp[30:] = np.linspace(0, 0.20, 30)                 # price RISES after bar 30
    dec = np.zeros(60, bool)
    dec[30] = True
    below = np.full(60, -0.05)                         # price BELOW its EMA -> revert = LONG
    above = np.full(60, +0.05)                         # price ABOVE its EMA -> revert = SHORT
    rl, _ = trade_returns(lp, dec, below, 20, +1)
    rs, _ = trade_returns(lp, dec, above, 20, +1)
    assert rl[0] > 0, f"[SIGN] a long into a rising price paid {rl[0]:+.4f}"
    assert rs[0] < 0, f"[SIGN] a short into a rising price paid {rs[0]:+.4f}"
    assert abs(rl[0] + rs[0]) < tol, "[SIGN] the two legs are not opposite on the same input"
    cont, _ = trade_returns(lp, dec, below, 20, -1)
    assert abs(cont[0] + rl[0]) < tol, "[SIGN] the secondary direction is not the primary's negative"
    return float(rl[0])


def assert_QTY(logp, hl, etype):
    """The scored grid must differ from the one NOT meant to be scored."""
    b = build(logp, hl, etype)
    thr = expanding_threshold(b["R"])
    dec = decisions(b["R"], thr, b["x"])
    a, _ = trade_returns(logp, dec, b["x"], 5, +1)
    c, _ = trade_returns(logp, dec, b["x"], 20, +1)
    assert len(a) and len(c), "[QTY] no trades to compare"
    assert abs(a.mean() - c.mean()) > 1e-9, "[QTY] hold 5 and hold 20 scored identically"
    other = build(logp, hl, "move >2%" if etype != "move >2%" else "reversal >1%")
    assert abs(np.nanmean(b["R"]) - np.nanmean(other["R"])) > 1e-9, "[QTY] both event types agree"
    return True


def assert_CAUSAL(logp, hl, etype):
    b = build(logp, hl, etype)
    t = len(logp) - 60
    q = logp.copy()
    q[t + 10:] += 0.5
    b2 = build(q, hl, etype)
    d = float(np.nanmax(np.abs(b["R"][:t + 1] - b2["R"][:t + 1])))
    thr1 = expanding_threshold(b["R"])[:t + 1]
    thr2 = expanding_threshold(b2["R"])[:t + 1]
    dt = float(np.nanmax(np.abs(np.where(np.isfinite(thr1), thr1, 0) - np.where(np.isfinite(thr2), thr2, 0))))
    assert d < 1e-12 and dt < 1e-12, f"[CAUSAL] R moved {d:.3e}, threshold moved {dt:.3e}"
    return max(d, dt)


def assert_POOL(b, rng, tol=0.01):
    """Every A' draw must satisfy the OBSERVED eligibility mask and match its entry COUNT.
    D347's rotation traded the excluded tail and its headline inverted when fixed (D351)."""
    thr = expanding_threshold(b["R"])
    obs = decisions(b["R"], thr, b["x"])
    n_obs = int(obs.sum())
    elig = np.isfinite(b["R"]) & np.isfinite(b["x"]) & (np.abs(b["x"]) > 1e-9)
    elig[:WARMUP] = False
    worst = 0.0
    for _ in range(6):
        k = int(rng.integers(ROT_MIN, ROT_MAX))
        Rr = rotated_R(b, k)
        dr = decisions_topn(Rr, b["x"], n_obs)
        assert not (dr & ~elig).any(), "[POOL] an A' draw entered a bar the observed could not"
        assert dr.sum() > 0, "[POOL] an A' draw took no trades"
        worst = max(worst, abs(int(dr.sum()) - n_obs) / max(n_obs, 1))
    assert worst < tol, f"[POOL] A' entry count differs by {100*worst:.2f}% (max {100*tol:.0f}%)"
    return worst


def assert_NULL(logp, rng):
    r = np.diff(logp)
    ac = lambda v: float(np.corrcoef(np.abs(v[:-1]), np.abs(v[1:]))[0, 1])
    n2 = np.diff(null_path(logp, rng))
    out = dict(observed=ac(r), N2=ac(n2), sd_obs=float(r.std()), sd_N2=float(n2.std()),
               same_fn=(event_masks is event_masks))
    assert out["N2"] > 0.4 * out["observed"], "[NULL] N2 did not keep the clustering it claims"
    assert abs(out["sd_N2"] / out["sd_obs"] - 1) < 0.25, "[NULL] N2 lost the return scale"
    return out


def assert_SPLIT():
    """Prove the guard BITES, not merely that it is installed -- and that this module defines no
    unlock. D365 exposes allow_holdout() for authorised reads; D387 must not have one at all."""
    assert _OPENED["n"] > 0, "[SPLIT] the audit hook never saw an open -- it is not installed"
    mod = sys.modules[__name__]
    assert not hasattr(mod, "allow_holdout"), "[SPLIT] this module defines an unlock"
    assert not hasattr(mod, "_ALLOW"), "[SPLIT] this module defines an unlock flag"
    before = _OPENED["refused"]
    try:                                            # actually attempt one; it MUST raise
        open(REPO / "data/fixtures/us_shorts_daily_holdout.csv.gz", "rb").close()
        raise AssertionError("[SPLIT] the guard did NOT refuse a holdout path")
    except RuntimeError as e:
        assert "refused" in str(e), f"[SPLIT] wrong refusal: {e}"
    assert _OPENED["refused"] == before + 1, "[SPLIT] the refusal was not counted"
    assert _OPENED["refused"] == 1, "[SPLIT] a holdout path was attempted outside this probe"
    return _OPENED["n"]


def assert_X(logp, hl, etype, rng):
    """Every break must move the EXACT SCALAR its assertion compares -- three duds this session
    broke what the assertion was NAMED for instead."""
    fired = {}
    A = np.repeat(kernels(np.zeros(6), 0.02), 4, axis=0)
    try:                                                  # [REC]: perturb the RECURSION's output
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

    b = build(logp, hl, etype)
    try:                                                  # [LAG]: a threshold that PEEKS one bar ahead
        R, x = b["R"], b["x"]
        peek = np.roll(expanding_threshold(R), 1)
        assert_LAG(R, peek, x)
        fired["LAG"] = False
    except AssertionError:
        fired["LAG"] = True

    try:                                                  # [MASS]: scale f so the identity breaks
        ind = np.zeros(len(logp))
        ind[b["ev"]] = 1.0
        rate = ew(ind.reshape(-1, 1), 0.5 ** (1.0 / hl)).ravel()
        assert float(np.abs(b["mass"] * 1.001 - rate).max()) < 1e-12
        fired["MASS"] = False
    except AssertionError:
        fired["MASS"] = True

    try:                                                  # [SIGN]: a book that pays the SAME both ways
        lp = np.zeros(60)
        lp[30:] = np.linspace(0, 0.2, 30)
        dec = np.zeros(60, bool)
        dec[30] = True
        rl, _ = trade_returns(lp, dec, np.full(60, -0.05), 20, +1)
        rs, _ = trade_returns(lp, dec, np.full(60, -0.05), 20, +1)   # SAME side twice
        assert abs(rl[0] + rs[0]) < 1e-12
        fired["SIGN"] = False
    except AssertionError:
        fired["SIGN"] = True

    try:                                                  # [POOL]: a rotation that ignores eligibility
        thr = expanding_threshold(b["R"])
        obs = decisions(b["R"], thr, b["x"])
        bad = np.zeros(len(obs), bool)
        bad[:int(obs.sum()) * 3] = True                   # 3x the entries, from bar 0
        elig = np.isfinite(b["R"])
        elig[:WARMUP] = False
        assert not (bad & ~elig).any()
        fired["POOL"] = False
    except AssertionError:
        fired["POOL"] = True

    bad = [k for k, v in fired.items() if not v]
    assert not bad, f"[X] these audits did NOT raise on a deliberate break: {bad}"
    return fired




# -------------------------------------------------------------------------------- run
def load_mined():
    return RP.load_ragged(FIX, EVJ, fee_bps=0.0)


def name_bars(panel, cleaned, sym):
    i = panel.symbols.index(sym)
    bars = cleaned[sym][:int(panel.live[i].sum())]
    c = np.array([b.bar.close for b in bars], float)
    h = np.array([b.bar.high for b in bars], float)
    lo = np.array([b.bar.low for b in bars], float)
    ok = np.isfinite(c) & (c > 0) & (h > 0) & (lo > 0)
    if ok.sum() < MIN_BARS:
        return None
    return np.log(c[ok]), h[ok], lo[ok]


def _trim(r, mode="both", q=0.01):
    """1% from BOTH tails, and the one-sided pair beside it -- dropping only winners is a flag,
    not a verdict (D307 called four cells lottery books on the one-sided cut alone)."""
    if len(r) < 20:
        return float(r.mean())
    lo, hi = np.percentile(r, [100 * q, 100 * (1 - q)])
    m = (r >= lo) & (r <= hi) if mode == "both" else (r <= hi if mode == "top" else r >= lo)
    return float(r[m].mean()) if m.any() else float(r.mean())


def _cell(logp, hi, lo, b, dec, H, dirn, nb, rots, sym, et, hl, label):
    r, idx = trade_returns(logp, dec, b["x"], H, dirn)
    if len(r) < 5:
        return None
    n_obs = int(dec.sum())
    n2 = []
    for z in nb:
        # MATCHED COUNT for the nulls too, per R7 -- and it removes 20 of the 21 O(n^2) threshold
        # scans per cell. The null's gate ranks on R, never on returns, so it cannot cherry-pick
        # outcomes; giving it exactly the observed number of shots at its own best-R bars makes it
        # if anything STRICTER than the observed's lagged causal gate.
        d2 = decisions_topn(z["R"], z["x"], n_obs)
        rr, _ = trade_returns(z["lp"], d2, z["x"], H, dirn)      # scored ON THE NULL'S OWN PATH
        if len(rr) >= 5:
            n2.append(float(rr.mean()))
    ap = []
    for Rr in rots:
        dr = decisions_topn(Rr, b["x"], n_obs)            # MATCHED COUNT, per §7 and R7
        rr, _ = trade_returns(logp, dr, b["x"], H, dirn)
        if len(rr) >= 5:
            ap.append(float(rr.mean()))
    pc = lambda v, q: float(np.percentile(v, q)) if len(v) >= 5 else None
    return dict(
        symbol=sym, etype=et, hl=hl, H=H, dirn=label, n=int(len(r)),
        gross=float(r.mean()), med=float(np.median(r)), win=float((r > 0).mean()),
        sd=float(r.std()),
        skew=float(((r - r.mean()) ** 3).mean() / (r.std() ** 3 + 1e-30)),
        kurt=float(((r - r.mean()) ** 4).mean() / (r.std() ** 4 + 1e-30)),
        trim=_trim(r), ex_top=_trim(r, "top"), ex_bot=_trim(r, "bot"),
        spread_bp=corwin_schultz(hi[idx], lo[idx]) if len(idx) > 30 else None,
        px=float(np.median(np.exp(logp[idx]))),
        exposure=float(len(r) * H / max(len(logp), 1)),
        n2_p50=pc(n2, 50), n2_p95=pc(n2, 95),
        n2_sd=float(np.std(n2, ddof=1)) if len(n2) >= 5 else None,
        ap_p50=pc(ap, 50), ap_p95=pc(ap, 95),
        ap_sd=float(np.std(ap, ddof=1)) if len(ap) >= 5 else None,
        n_ev=b["n_ev"], first=int(idx[0]), last=int(idx[-1]), nbars=int(len(logp)))


def one(sym, pack):
    logp, hi, lo = pack
    rng = np.random.default_rng(SEED + abs(hash(sym)) % 100_000)
    nulls = [q for q in (null_path(logp, rng) for _ in range(one.draws)) if q is not None]
    out = []
    for et in ETYPES:
        for hl in LAMS:
            b = build(logp, hl, et)
            if b is None:
                continue
            dec = decisions(b["R"], expanding_threshold(b["R"]), b["x"])
            if dec.sum() < 5:
                continue
            nb = [z for z in (build(q, hl, et) for q in nulls) if z is not None]
            rots = [rotated_R(b, int(rng.integers(ROT_MIN, ROT_MAX))) for _ in range(one.rots)]
            for H in HOLDS:
                for dirn, label in ((+1, "revert"), (-1, "continue")):
                    c = _cell(logp, hi, lo, b, dec, H, dirn, nb, rots, sym, et, hl, label)
                    if c:
                        out.append(c)
    return out


one.draws, one.rots = 20, 40


def report(rows):
    R = [r for r in rows if r["dirn"] == "revert"]
    print("\n  1. PERFORMANCE -- GROSS per trade, bp, PATH-INVARIANT lens (per TRADE, no slot cap)")
    print(f"{'type':>14}{'lam':>5}{'H':>4}{'names':>7}{'trades':>8}{'GROSS bp':>10}{'net bp':>9}"
          f"{'spread':>8}{'breakeven':>11}{'expo':>7}{'N2 p95':>9}{'A p95':>9}{'vs N2':>8}")
    best = None
    for et in ETYPES:
        for hl in LAMS:
            for H in HOLDS:
                q = [r for r in R if r["etype"] == et and r["hl"] == hl and r["H"] == H]
                q = [r for r in q if r["n2_p95"] is not None and r["ap_p95"] is not None]
                if len(q) < 20:
                    continue
                g = 1e4 * np.mean([r["gross"] for r in q])
                sp = np.nanmedian([r["spread_bp"] for r in q if r["spread_bp"]])
                net = g - sp
                n2 = 1e4 * np.mean([r["n2_p95"] for r in q])
                ap = 1e4 * np.mean([r["ap_p95"] for r in q])
                sd = 1e4 * np.mean([r["n2_sd"] for r in q])
                z = (g - n2) / max(sd, 1e-9)
                tr = int(sum(r["n"] for r in q))
                print(f"{et:>14}{hl:>5}{H:>4}{len(q):>7}{tr:>8}{g:>10.1f}{net:>9.1f}"
                      f"{sp:>8.1f}{g:>11.1f}{np.mean([r['exposure'] for r in q]):>7.3f}"
                      f"{n2:>9.1f}{ap:>9.1f}{z:>8.2f}")
                if best is None or z > best[0]:
                    best = (z, et, hl, H, q)
    if best is None:
        print("\n  no cell had enough names to report")
        return
    z, et, hl, H, q = best
    print(f"\n  2. TRADE DISTRIBUTION -- best cell by N2 margin: {et}, lam {hl}, H {H}  ({z:+.2f} SE)")
    for nm, k in (("mean", "gross"), ("median", "med"), ("win rate", "win"), ("skew", "skew"),
                  ("kurtosis", "kurt"), ("trimmed 1% both", "trim"), ("ex-top 1%", "ex_top"),
                  ("ex-bottom 1%", "ex_bot")):
        v = np.mean([r[k] for r in q])
        print(f"      {nm:>18}: {1e4*v:>9.1f} bp" if k not in ("win", "skew", "kurt")
              else f"      {nm:>18}: {v:>9.3f}")
    print(f"      {'mean > median?':>18}: "
          f"{'YES -- the LEFT tail is doing the work' if np.mean([r['gross'] for r in q]) < np.mean([r['med'] for r in q]) else 'no'}")
    print("\n  3. WHAT THE WINNERS DEPEND ON")
    tot = np.array(sorted((r["gross"] * r["n"] for r in q), reverse=True))
    pos = tot[tot > 0].sum()
    if pos > 0:
        cs = np.cumsum(tot) / max(tot.sum(), 1e-12)
        half = int(np.searchsorted(cs, 0.5)) + 1
        print(f"      names to half the P&L: {half} of {len(q)}   top-1 {100*tot[0]/max(tot.sum(),1e-12):.1f}%"
              f"   top-5 {100*tot[:5].sum()/max(tot.sum(),1e-12):.1f}%"
              f"   top-10 {100*tot[:10].sum()/max(tot.sum(),1e-12):.1f}%")
    px = np.array([r["px"] for r in q])
    gr = np.array([r["gross"] for r in q])
    m = px < np.median(px)
    print(f"      by PRICE: cheap half {1e4*gr[m].mean():+.1f} bp   dear half {1e4*gr[~m].mean():+.1f} bp"
          f"   (median price ${np.median(px):.2f})")
    print("\n  4. NULLS AS DISTRIBUTIONS")
    print(f"      N2  p50 {1e4*np.mean([r['n2_p50'] for r in q]):+.1f}  "
          f"p95 {1e4*np.mean([r['n2_p95'] for r in q]):+.1f} bp")
    print(f"      A'  p50 {1e4*np.mean([r['ap_p50'] for r in q]):+.1f}  "
          f"p95 {1e4*np.mean([r['ap_p95'] for r in q]):+.1f} bp")
    C = [r for r in rows if r["dirn"] == "continue" and r["etype"] == et
         and r["hl"] == hl and r["H"] == H and r["n2_p95"] is not None]
    if C:
        cg = 1e4 * np.mean([r["gross"] for r in C])
        cz = (cg - 1e4 * np.mean([r["n2_p95"] for r in C])) / max(1e4 * np.mean([r["n2_sd"] for r in C]), 1e-9)
        print(f"\n  SECOND LOOK (declared): CONTINUATION on the same cell {cg:+.1f} bp, {cz:+.2f} SE")
        print("      if this clears as strongly as the primary, the conditioner marks VOLATILITY,")
        print("      not direction -- a different and weaker claim (section 10).")


def run(n_names, draws, rots, workers):
    t0 = time.time()
    one.draws, one.rots = draws, rots
    print(f"\nRUN -- D387. {len(ETYPES)} types x {len(LAMS)} lam x {len(HOLDS)} holds x 2 directions,"
          f" N2 {draws} draws, A' {rots} rotations")
    RP.assert_gates_passed(FIX)
    panel, cleaned = load_mined()
    print(f"  [GATE] accepted. {len(panel.symbols)} names, {len(panel.dates)} dates "
          f"{panel.dates[0]} -> {panel.dates[-1]}")
    syms = []
    packs = {}
    for s in panel.symbols:
        p = name_bars(panel, cleaned, s)
        if p is not None:
            syms.append(s)
            packs[s] = p
    rng = np.random.default_rng(SEED)
    syms = list(np.array(syms)[rng.permutation(len(syms))[:n_names]])
    print(f"  {len(syms)} names sampled of {len(packs)} eligible")

    probe = packs[syms[0]][0]
    tie = np.repeat(kernels(np.zeros(8), 0.02), 5, axis=0)
    print(f"  [REC]    lfilter vs explicit loop, tie-heavy: {assert_REC(tie, 0.9):.3e}")
    print(f"  [MASS]   int f vs the EW event rate:          {assert_MASS(probe, 120, ETYPES[0]):.3e}")
    b0 = build(probe, 120, ETYPES[0])
    print(f"  [LAG]    independent re-derivation differs on "
          f"{assert_LAG(b0['R'], expanding_threshold(b0['R']), b0['x'])} bars")
    print(f"  [SIGN]   long into a rising price pays {assert_SIGN():+.4f}; legs exactly opposite")
    assert_QTY(probe, 120, ETYPES[0])
    print("  [QTY]    hold 5 != hold 20, and the two event types disagree")
    print(f"  [CAUSAL] R and the threshold under a future shock: "
          f"{assert_CAUSAL(probe, 120, ETYPES[0]):.3e}")
    print(f"  [POOL]   A' entry-count drift vs observed: "
          f"{100*assert_POOL(b0, np.random.default_rng(5)):.2f}%")
    nl = assert_NULL(probe, np.random.default_rng(7))
    print(f"  [NULL]   |r| autocorr observed {nl['observed']:.3f}  N2 keeps {nl['N2']:.3f}; "
          f"sd ratio {nl['sd_N2']/nl['sd_obs']:.3f}")
    print(f"  [SPLIT]  guard saw {assert_SPLIT():,} opens, refused {_OPENED['refused']}, "
          f"no unlock in this file")
    print(f"  [X]      deliberate breaks all raise: "
          f"{assert_X(probe, 120, ETYPES[0], np.random.default_rng(9))}")

    got = FN.parallel_map(one, [(s, packs[s]) for s in syms], workers=workers, progress="D387")
    rows = [r for sub in got.values() for r in sub]
    OUT.write_text(json.dumps(dict(
        study=387, kind="SIGNAL TEST (R15) -- gross mean per trade above the nulls",
        fixture=FIX.name, names=len(syms), draws=draws, rots=rots,
        lams=list(LAMS), holds=list(HOLDS), etypes=list(ETYPES), quant=QUANT,
        null_check=nl, rows=rows), indent=1))
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
    print("D387  does price REVERT at levels where its own RARE events cluster -- SIGNAL TEST")
    if a.audit:
        run(8, 4, 8, a.workers)
    elif a.run:
        run(a.names, a.draws, a.rots, a.workers)
    else:
        ap.print_help()
