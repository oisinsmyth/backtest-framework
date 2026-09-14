"""D529 -- DATA-DEFINED WINDOWS: segment the session into chop/trend EPISODES with foresight.

    python working/d529_episode_segmentation.py

THE PRINCIPAL'S POINT: a trailing window will not work here. Two separate reasons, and both hold.

  1. A TRAILING WINDOW IS CAUSAL, and the oracle is allowed FORESIGHT. Imposing a trailing window
     on the oracle throws away its entire advantage before the measurement starts. The oracle's job
     is to be the most accurate detector obtainable WITH hindsight; the causal construction comes
     afterwards and separately.
  2. A FIXED LENGTH AVERAGES ACROSS REGIME BOUNDARIES. That is the specific defect that made the
     72-bar label weak: if a session is chop for 40 bars and then trends for 40, one 72-bar number
     reports the blend and neither state is visible. SS3 MEASURES how often that actually happens.

SO THE WINDOWS ARE FOUND, NOT IMPOSED -- the same move that made the traverse statistic work, where
the events came from the bands rather than from the clock.

THE SEGMENTER.  For a candidate segment of length L with returns r:

    eff = |sum r| / sum|r|          z = eff * sqrt(L)
    z >> C  -> TREND      z << C  -> CHOP        C is the random-walk value, SIMULATED per L

    gain(segment) = L * |z - C(L)| / C(L)        long, unambiguous segments earn most
    total = sum of gains - LAMBDA * (number of segments)

and the optimal segmentation is the exact dynamic-programming maximum over all partitions, which
is O(N^2) candidate segments -- trivial at N = 84 and EXACT, so this really is the best detector
this scoring admits rather than a greedy approximation.

LAMBDA IS NOT TUNED TO TASTE. It is calibrated so that a RANDOM WALK yields on average ONE segment,
i.e. the segmenter finds no structure where there is none. That is the same discipline as the
simulated benchmark elsewhere in this line, and it is the only free parameter.

No return is read as P&L, no cost, no position. This designs a LABEL.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
import d526_mid_vs_trade_scaling as Q     # noqa: E402

RNG = np.random.default_rng(529)
LMIN = 8                 # a segment shorter than this cannot express either regime
NBAR = 72


def P(*a):
    print(*a, flush=True)


def C_table(lmax: int, n: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    """(C(L), SD(L)) for z = eff*sqrt(L) under a random walk, SIMULATED per length.

    BOTH ARE NEEDED AND THE SD IS THE ONE THE FIRST VERSION OMITTED.  For a random walk
    `|sum r| ~ sqrt(L)|N(0,1)|` and `sum|r| ~ L*E|r|`, so `z = eff*sqrt(L)` has a distribution
    that is ESSENTIALLY INDEPENDENT OF L -- mean about 1.0, sd about 0.75.  The first version
    scored a segment as `L * |z - C| / C`, which multiplied by L a quantity that already
    aggregates L bars, so a long run of pure noise scored as overwhelming evidence; the
    calibration then drove LAMBDA to 126 and the segmenter could never split anything.  The
    correct per-segment score is the SQUARED t-STATISTIC, with no L weighting at all."""
    C = np.full(lmax + 1, np.nan)
    S = np.full(lmax + 1, np.nan)
    for L in range(LMIN, lmax + 1):
        r = RNG.normal(size=(L, n))
        z = np.abs(r.sum(0)) / np.abs(r).sum(0) * np.sqrt(L)
        C[L], S[L] = z.mean(), z.std(ddof=1)
    return C, S


def C_from_returns(r: np.ndarray, lmax: int, n: int = 600) -> tuple[np.ndarray, np.ndarray]:
    """(C(L), SD(L)) re-estimated from a root's OWN returns by SIGN SHUFFLE.

    Holds the magnitude distribution and the volatility clustering; randomises only the order
    of signs, which is the claim under test."""
    a = np.abs(r).ravel()
    a = a[a > 0]
    C = np.full(lmax + 1, np.nan)
    S = np.full(lmax + 1, np.nan)
    for L in range(LMIN, lmax + 1):
        mag = a[RNG.integers(0, len(a), (L, n))]
        s = np.where(RNG.integers(0, 2, (L, n)) == 1, 1.0, -1.0)
        x = mag * s
        z = np.abs(x.sum(0)) / np.abs(x).sum(0) * np.sqrt(L)
        C[L], S[L] = z.mean(), z.std(ddof=1)
    return C, S


def segment(r: np.ndarray, C: np.ndarray, S: np.ndarray, lam: float) -> list:
    """EXACT dynamic-programming best partition. Returns [(i, j, type, z, t, gain), ...].

    gain = ((z - C(L)) / SD(L))**2  -- the SQUARED t-STATISTIC, with NO L weighting, because
    z already aggregates the segment. type +1 = TREND, -1 = CHOP."""
    n = len(r)
    cs = np.concatenate([[0.0], np.cumsum(r)])
    ca = np.concatenate([[0.0], np.cumsum(np.abs(r))])
    best = np.full(n + 1, -np.inf)
    best[0] = 0.0
    back = np.zeros(n + 1, np.int64)

    def zt(i, j):
        L = j - i
        path = ca[j] - ca[i]
        if path <= 0 or not np.isfinite(C[L]) or not (S[L] > 0):
            return None
        z = abs(cs[j] - cs[i]) / path * np.sqrt(L)
        return z, (z - C[L]) / S[L], L

    for j in range(LMIN, n + 1):
        for i in range(0, j - LMIN + 1):
            v0 = best[i]
            if not np.isfinite(v0):
                continue
            q = zt(i, j)
            if q is None:
                continue
            v = v0 + q[1] ** 2 - lam
            if v > best[j]:
                best[j] = v
                back[j] = i
    if not np.isfinite(best[n]):
        return []
    segs, j = [], n
    while j > 0:
        i = back[j]
        z, tt, L = zt(i, j)
        segs.append((i, j, 1 if tt > 0 else -1, z, tt, tt ** 2))
        j = i
    return segs[::-1]


def calibrate_lambda(C: np.ndarray, S: np.ndarray, target: float = 1.0,
                     n: int = 300, paths=None) -> float:
    """Pick LAMBDA so a RANDOM WALK yields `target` segments on average. The ONLY free
    parameter, and it is fixed by the null rather than by preference.

    In squared-t units a single null segment contributes about 1 (chi-square, 1 df), so the
    calibrated LAMBDA should land in single digits -- if it comes back in the hundreds the
    scoring is mis-scaled, which is exactly how the first version's bug announced itself."""
    if paths is None:
        paths = RNG.normal(size=(NBAR, n))
    lo, hi = 0.0, 60.0
    for _ in range(20):
        mid = 0.5 * (lo + hi)
        k = np.mean([len(segment(paths[:, j], C, S, mid)) for j in range(paths.shape[1])])
        if k > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# =============================================================================================
P("=" * 100)
P("1  CALIBRATION -- C(L) simulated, and LAMBDA fixed so a RANDOM WALK finds ONE segment")
P("=" * 100)
C, S = C_table(NBAR)
P(f"   C(L)  at L = 8, 12, 24, 36, 72:  " + "  ".join(f"{C[L]:.3f}" for L in (8, 12, 24, 36, 72)))
P(f"   SD(L) at L = 8, 12, 24, 36, 72:  " + "  ".join(f"{S[L]:.3f}" for L in (8, 12, 24, 36, 72)))
P(f"   z = eff*sqrt(L) is ESSENTIALLY L-INDEPENDENT, which is why the score must NOT be")
P(f"   weighted by L -- the first version's bug, and it drove LAMBDA to 126.")
LAM = calibrate_lambda(C, S)
rw = [len(segment(RNG.normal(size=NBAR), C, S, LAM)) for _ in range(400)]
P(f"   LAMBDA = {LAM:.2f}  ->  a random walk yields {np.mean(rw):.2f} segments on average "
  f"({np.mean(np.array(rw) == 1):.0%} of paths get exactly 1)")

# =============================================================================================
P("")
P("=" * 100)
P("2  KNOWN-ANSWER CASE -- chop for 36 bars then a trend for 36. Can it find the boundary?")
P("=" * 100)
t = np.arange(NBAR + 1, dtype=np.float64)
half = NBAR // 2
found = []
for _ in range(300):
    chop = np.diff(np.sin(2 * np.pi * 3 * np.arange(half + 1) / half)) * 1.0
    chop = chop + 0.10 * RNG.normal(size=half)
    trend = 0.30 + 0.10 * RNG.normal(size=NBAR - half)
    r = np.concatenate([chop, trend])
    segs = segment(r, C, S, LAM)
    if len(segs) >= 2:
        # the boundary nearest the truth
        bs = [s[0] for s in segs[1:]]
        found.append(min(bs, key=lambda b: abs(b - half)))
    else:
        found.append(np.nan)
f = np.array(found, dtype=float)
P(f"   true boundary at bar {half}. Found: median {np.nanmedian(f):.0f}, "
  f"mean {np.nanmean(f):.1f}, within +/-4 bars on {np.nanmean(np.abs(f-half) <= 4):.0%} of paths,"
  f" no split at all on {np.mean(np.isnan(f)):.0%}")
ex = segment(np.concatenate([np.diff(np.sin(2*np.pi*3*np.arange(half+1)/half)) + 0.1*RNG.normal(size=half),
                             0.30 + 0.10*RNG.normal(size=NBAR-half)]), C, S, LAM)
P("   one example segmentation:")
for (i, j, ty, z, tt, g) in ex:
    P(f"      bars {i:>3}..{j:<3} L={j-i:<3} {'TREND' if ty > 0 else 'CHOP':<5} "
      f"z={z:.3f} vs C={C[j-i]:.3f}  t={tt:+.2f}  gain {g:.1f}")

# =============================================================================================
P("")
P("=" * 100)
P("3  ON REAL DATA -- and DOES A FIXED 72-BAR WINDOW STRADDLE A BOUNDARY? (the principal's point)")
P("=" * 100)
d = pd.read_parquet("data/fixtures/fut_day5m.parquet",
                    columns=["root", "day", "bar", "close", "present", "same_front"])
d = d[d["present"]]
d = d[d["same_front"]]
d = d[d["day"] <= "2023-12-29"]
P("")
P("   root   sess   segs/sess   % sessions   median   chop share   trend share   C(72) from")
P("                              >1 segment   seg len   of bars      of bars       own returns")
for r in ("ES", "NQ", "GC", "ZN", "CL"):
    g = d[d["root"] == r].sort_values(["day", "bar"], kind="stable")
    R, days = Q.session_matrix(g, "close")
    if R.shape[1] < 300:
        continue
    R = R[:, :800]                              # 800 sessions is plenty for a design read
    Cr, Sr = C_from_returns(R, NBAR)
    lam_r = calibrate_lambda(Cr, Sr, n=200)
    ns, lens, chop_bars, trend_bars, tot = [], [], 0, 0, 0
    for j in range(R.shape[1]):
        segs = segment(R[:, j], Cr, Sr, lam_r)
        if not segs:
            continue
        ns.append(len(segs))
        for (i0, j0, ty, z, tt, gg) in segs:
            lens.append(j0 - i0)
            if ty > 0:
                trend_bars += j0 - i0
            else:
                chop_bars += j0 - i0
            tot += j0 - i0
    ns = np.array(ns)
    P(f"   {r:>4}  {len(ns):>5}    {ns.mean():.2f}       {np.mean(ns > 1):>7.1%}"
      f"      {np.median(lens):>5.0f}    {chop_bars/tot:>7.1%}      {trend_bars/tot:>7.1%}"
      f"        {Cr[72]:.3f}")
P("")
P("   READ THE '>1 SEGMENT' COLUMN. That is the fraction of sessions where ONE 72-bar number")
P("   provably reports a BLEND of two or more regimes -- the principal's objection, measured.")
P("   And the C(72) column is why the benchmark is re-estimated per root: it is not 1.000, and")
P("   it is not even the Gaussian value.")
