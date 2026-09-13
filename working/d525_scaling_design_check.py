"""D525 DESIGN CHECK -- a VOLATILITY-INVARIANT, SCALE-AWARE path statistic on the INTRADAY clock.

    python working/d525_scaling_design_check.py

THE PRINCIPAL'S THREE CORRECTIONS, and what they force.

  "some sort of volatility invariant path efficacy must be taken into account also"
  "the market is fractal in nature ... so the horizon choice has to be intra day"
  "stop pooling, you can not assume a mean over all time will be useful ... time series"

THE STATISTIC.  Keep path efficiency, but read its SCALING rather than its level.  For a window of
N returns, aggregate to scale k and measure

    E(k) = |net| / sum|r_k|        net is INVARIANT to k; only the MEASURED path length shrinks

For a self-similar path with Hurst exponent Hu, a window of N holds N/k increments of typical size
sigma*k^Hu, so sum|r_k| ~ N*sigma*k^(Hu-1) and |net| ~ sigma*N^Hu.  Hence

    log E(k) = (1 - Hu) * log k + const           SLOPE = 1 - Hu

    slope < benchmark  <=>  Hu > 0.5   TRENDING / persistent
    slope > benchmark  <=>  Hu < 0.5   mean-reverting / anti-persistent

THE BENCHMARK IS SIMULATED AT THE SAME N AND THE SAME SCALE SET, NEVER THE THEORETICAL 0.5.
At N=72 the finite-window bias is about +0.03, which is two thirds of the whole Hu=0.50-to-0.55
effect -- so using the closed form would manufacture "mean reversion" out of nothing.  This is
D471's C-is-not-1 lesson in a new place: calibrate, never assume.

This file CHECKS THE DESIGN and answers four questions with measurements.  It runs no study,
reads no holdout, and computes no return as P&L.
"""
import sys
import numpy as np

sys.path.insert(0, "scripts")
import d523_oracle_stage0 as M     # noqa: E402

RNG = np.random.default_rng(525)
NRET = 72                                        # 72 has divisors 1..24; 83 is prime
SCALES = (1, 2, 3, 4, 6, 8, 9, 12, 18, 24)
KMIN_ROBUST = 3


def P(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------------------------
def fgn(n: int, hurst: float, size: int) -> np.ndarray:
    """Fractional Gaussian noise, Davies-Harte exact circulant embedding.  Returns (n, size)."""
    k = np.arange(n + 1, dtype=np.float64)
    g = 0.5 * (np.abs(k + 1) ** (2 * hurst) - 2 * np.abs(k) ** (2 * hurst)
               + np.abs(k - 1) ** (2 * hurst))
    c = np.concatenate([g, g[-2:0:-1]])
    lam = np.fft.fft(c).real
    if lam.min() < -1e-8:
        raise RuntimeError(f"circulant not PSD at hurst={hurst}: min {lam.min():.3e}")
    lam = np.clip(lam, 0, None)
    m = len(c)
    w = (RNG.normal(size=(size, m)) + 1j * RNG.normal(size=(size, m))) / np.sqrt(2 * m)
    out = np.fft.fft(w * np.sqrt(lam)[None, :], axis=1).real[:, :n]
    return (out / out.std(axis=1, keepdims=True)).T


def vol_standardise(R: np.ndarray, w: int = 13) -> np.ndarray:
    """Divide each return by a CENTRED rolling mean of |r|.

    Legitimate for an ORACLE LABEL (it may see the whole session); a causal feature could not
    use the centred form.  This is the principal's 'volatility invariant' requirement made
    explicit: it removes the within-session vol PROFILE, which the raw slope is NOT immune to."""
    a = np.abs(R)
    pad = w // 2
    padded = np.vstack([a[:1].repeat(pad, 0), a, a[-1:].repeat(pad, 0)])
    ker = np.ones(w) / w
    loc = np.apply_along_axis(lambda v: np.convolve(v, ker, mode="valid"), 0, padded)
    loc = np.where(loc > 0, loc, np.nan)
    out = R / loc
    return np.nan_to_num(out, nan=0.0)


def scaling_slope(R: np.ndarray, kmin: int = 1) -> np.ndarray:
    """Slope of log E(k) on log k per column.  R is (N, n_paths).  NaN where net == 0."""
    N, n = R.shape
    net = np.abs(R.sum(0))
    xs, ys = [], []
    for k in SCALES:
        if k < kmin or N % k:
            continue
        agg = R.reshape(N // k, k, n).sum(1)
        path = np.abs(agg).sum(0)
        bad = (net <= 0) | (path <= 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            y = np.log(np.where(bad, np.nan, net) / np.where(bad, np.nan, path))
        ys.append(y)
        xs.append(np.log(k))
    X = np.array(xs)
    Y = np.vstack(ys)
    Xc = X - X.mean()
    return (Xc[:, None] * (Y - Y.mean(0))).sum(0) / (Xc ** 2).sum()


def bench(kmin: int, n: int = 8000, standardise: bool = False) -> float:
    """The SIMULATED random-walk slope at this N and scale set. Never the closed form."""
    R = fgn(NRET, 0.50, n)
    if standardise:
        R = vol_standardise(R)
    return float(np.nanmean(scaling_slope(R, kmin=kmin)))


# =============================================================================================
P("=" * 98)
P("1  DOES THE SLOPE RECOVER THE HURST EXPONENT ON ONE INTRADAY WINDOW OF 72 RETURNS?")
P("=" * 98)
B1, B3 = bench(1), bench(KMIN_ROBUST)
P(f"   SIMULATED random-walk benchmark at N={NRET}:  k>=1 {B1:+.4f}   k>=3 {B3:+.4f}")
P(f"   (the closed form says 0.5000 -- the finite-window bias is {B1-0.5:+.4f}, which is why")
P("    the benchmark is simulated and not assumed)")
P("")
P("   true Hu   slope k>=3   vs benchmark   per-session sd   sessions to resolve at 2 SE")
for hu in (0.40, 0.45, 0.50, 0.55, 0.60, 0.65):
    s = scaling_slope(fgn(NRET, hu, 8000), kmin=KMIN_ROBUST)
    mu, sd = np.nanmean(s), np.nanstd(s, ddof=1)
    gap = mu - B3
    nn = int(np.ceil((2 * sd / abs(gap)) ** 2)) if abs(gap) > 1e-6 else 0
    P(f"    {hu:.2f}      {mu:+.4f}      {gap:+.4f}         {sd:.4f}"
      f"        {nn if nn else '--':>9}")
P("")
P("   Hu=0.55 -- a MILD persistent trend -- resolves in a few dozen sessions, i.e. about a")
P("   MONTH. That is the scale a regime lives on, and it is measured entirely inside the day.")

# =============================================================================================
P("")
P("=" * 98)
P("2  IS IT VOLATILITY-INVARIANT, AND DOES STANDARDISING COST THE SIGNAL?")
P("=" * 98)
base = fgn(NRET, 0.55, 8000)
profiles = {
    "flat vol (reference)":       np.ones(NRET),
    "vol x4 overall":            np.full(NRET, 4.0),
    "U-shaped intraday vol":     1.0 + 2.0 * np.cos(np.linspace(-np.pi, np.pi, NRET)) ** 2,
    "one 10x bar mid-session":   np.where(np.arange(NRET) == NRET // 2, 10.0, 1.0),
    "vol ramp 1 -> 5":           np.linspace(1.0, 5.0, NRET),
}
P("   profile                        RAW slope   drift from ref    STANDARDISED   drift from ref")
r0 = s0 = None
for name, prof in profiles.items():
    R = base * prof[:, None]
    raw = float(np.nanmean(scaling_slope(R, kmin=KMIN_ROBUST)))
    std = float(np.nanmean(scaling_slope(vol_standardise(R), kmin=KMIN_ROBUST)))
    if r0 is None:
        r0, s0 = raw, std
    P(f"   {name:<30}   {raw:+.4f}     {raw-r0:+.4f}          {std:+.4f}       {std-s0:+.4f}")
P("")
sB3 = bench(KMIN_ROBUST, standardise=True)
sig_raw = float(np.nanmean(scaling_slope(base, kmin=KMIN_ROBUST))) - B3
sig_std = float(np.nanmean(scaling_slope(vol_standardise(base), kmin=KMIN_ROBUST))) - sB3
P(f"   AND THE SIGNAL SURVIVES STANDARDISATION: Hu=0.55 sits {sig_raw:+.4f} from its benchmark")
P(f"   raw and {sig_std:+.4f} standardised (benchmarks {B3:+.4f} and {sB3:+.4f} respectively).")
P("   So vol-standardising buys profile-invariance; whether it costs sensitivity is the")
P("   comparison above, and it must be made against the STANDARDISED benchmark, not the raw one.")

# =============================================================================================
P("")
P("=" * 98)
P("3  BID-ASK BOUNCE: does dropping k=1,2 actually fix it? (MEASURED, not assumed)")
P("=" * 98)
P("   Truth is Hu=0.50 throughout. psi/sigma is the half-spread over per-bar sigma.")
P("")
P("   psi/sigma   k>=1 slope   vs k>=1 bench   k>=3 slope   vs k>=3 bench   standardised k>=3")
truth = fgn(NRET, 0.50, 8000)
d1, d3 = [], []
for ps in (0.0, 0.1, 0.25, 0.5, 1.0):
    u = RNG.normal(0, ps, (NRET + 1, truth.shape[1]))
    obs = truth + np.diff(u, axis=0)
    s1 = float(np.nanmean(scaling_slope(obs, kmin=1)))
    s3 = float(np.nanmean(scaling_slope(obs, kmin=KMIN_ROBUST)))
    ss = float(np.nanmean(scaling_slope(vol_standardise(obs), kmin=KMIN_ROBUST)))
    d1.append(s1 - B1)
    d3.append(s3 - B3)
    P(f"     {ps:5.2f}      {s1:+.4f}      {s1-B1:+.4f}       {s3:+.4f}      {s3-B3:+.4f}"
      f"        {ss-sB3:+.4f}")
P("")
P(f"   BOUNCE SENSITIVITY over psi/sigma 0 -> 1:  k>=1 {d1[-1]-d1[0]:+.4f}"
  f"   k>=3 {d3[-1]-d3[0]:+.4f}"
  f"   -> dropping k=1,2 removes {100*(1-abs(d3[-1]-d3[0])/abs(d1[-1]-d1[0])):.0f}% of it")
P("   IT IS A MITIGATION, NOT A FIX. Against the correct benchmark a psi/sigma of 1 still reads")
P("   as strong false mean reversion. A bounce-free price is required: the mid from the bbo-1m")
P("   or tbbo already on disk. ZT and SR3 sit at the high-psi end of this table.")

# =============================================================================================
P("")
P("=" * 98)
P("4  ON THE REAL FIXTURE: is the PER-SESSION slope a TIME SERIES with structure?")
P("=" * 98)
P("   (the principal: a mean over all time throws out the useful part)")
d, info = M.eligible()
by_root = {r: g for r, g in d.groupby("root", sort=True)}
del d
P("")
P(f"   Benchmarks at N={NRET}, k>=3:  raw {B3:+.4f}   vol-standardised {sB3:+.4f}")
P("   A slope BELOW its benchmark means Hu > 0.5, i.e. PERSISTENT / trending.")
P("")
P("   root  sessions   raw slope   vs bench   std slope   vs bench   lag-1 ac   yearly-mean sd")
for r in ("NQ", "ES", "YM", "RTY", "CL", "GC", "ZN", "ZT", "6E", "NG"):
    g = by_root[r]
    bars = g["bar"].to_numpy()
    close = g["close"].to_numpy(np.float64)
    day = g["day"].to_numpy()
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    segs = list(zip(np.concatenate(([0], cut)), np.concatenate((cut, [len(g)]))))
    cols, days = [], []
    for s0_, s1_ in segs:
        b, c = bars[s0_:s1_], close[s0_:s1_]
        if len(b) < NRET + 1 or b[NRET] - b[0] != NRET:
            continue                              # need NRET+1 CONSECUTIVE closes
        cols.append(np.diff(np.log(c[:NRET + 1])))
        days.append(day[s0_])
    if len(cols) < 300:
        continue
    R = np.vstack(cols).T
    sr = scaling_slope(R, kmin=KMIN_ROBUST)
    ss = scaling_slope(vol_standardise(R), kmin=KMIN_ROBUST)
    ok = np.isfinite(sr) & np.isfinite(ss)
    sr, ss = sr[ok], ss[ok]
    yr = np.array([int(x[:4]) for x in days])[ok]
    ym = np.array([sr[yr == y].mean() for y in np.unique(yr)])
    ac = float(np.corrcoef(sr[:-1], sr[1:])[0, 1])
    P(f"   {r:>4}  {len(sr):>8,}   {sr.mean():+.4f}   {sr.mean()-B3:+.4f}"
      f"    {ss.mean():+.4f}   {ss.mean()-sB3:+.4f}   {ac:+.4f}     {ym.std(ddof=1):.4f}"
      f"   (n dropped {int((~ok).sum())})")
P("")
P("   THE LAST TWO COLUMNS ARE THE ANSWER TO 'STOP POOLING': a non-zero lag-1 autocorrelation")
P("   and a yearly-mean spread say the slope is a PERSISTENT STATE with regimes -- an object a")
P("   causal feature could predict, and precisely what a pooled mean over 84,776 sessions")
P("   destroys. Per-session sd from section 1 is about 0.13, so compare the yearly spread to")
P("   0.13/sqrt(sessions per year) rather than to 0.13.")
