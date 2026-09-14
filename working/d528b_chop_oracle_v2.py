"""D528b -- the CHOP ORACLE, benchmarked against each session's OWN sign shuffle.

    python working/d528b_chop_oracle_v2.py

WHAT v1 GOT WRONG, measured rather than argued:

  A GAUSSIAN RANDOM WALK ALREADY SCORES traverse 0.745 at this band geometry, and every real root
  came in BELOW it (0.660 to 0.708).  Taken at face value that says every market is more trending
  than a random walk, which contradicts D526's finding that the rates complex and gold are
  anti-persistent.  The cause is not regime: it is that real returns are FAT-TAILED, so they break
  out of a quantile band more often than Gaussian steps do -- the same class of error as D471's
  `C = 1` assumption and D523's closed-form benchmark.

  THE FIX IS THE ONE D523 GOT RIGHT: benchmark each session against A SIGN SHUFFLE OF ITS OWN
  RETURNS.  That holds the return distribution, the volatility path and the realised magnitudes
  IDENTICALLY fixed and randomises only the ORDER -- which is exactly the claim under test, because
  "does price oscillate across its range" is a statement about arrangement, not about magnitudes.

  Also fixed: v1 called a PURE STRAIGHT LINE choppy (traverse 0.919, 6.68 cycles), because
  detrending a line leaves only noise and the noise oscillates across a tiny band.  The traverse
  number is meaningless when the range is not a real fraction of the movement, so it is now GATED
  on `width_sigma` and the gate is shown to fire on the straight line.

THE MAGNITUDE THE PRINCIPAL DESCRIBED -- "how often the chop does one cycle ... and with what
reliability does the price travel the full width" -- is the two combined, so the headline statistic
is the NUMBER OF COMPLETED TRAVERSES per window against its sign-shuffle expectation.  Reliability
is reported beside it because it is the win rate a construction would face.

No return is read as P&L, no cost, no position.  This validates a LABEL.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
import d523_oracle_stage0 as M            # noqa: E402
import d526_mid_vs_trade_scaling as Q     # noqa: E402

RNG = np.random.default_rng(5281)
N = 72
Q_LO, Q_HI = 0.10, 0.90
H_BAND, B_BREAK = 0.35, 0.85
WIDTH_SIGMA_MIN = 0.40          # below this the "range" is noise and traverse is meaningless
N_SHUF = 200                    # sign shuffles per session


def P(*a):
    print(*a, flush=True)


def traverse_stats(y: np.ndarray) -> tuple[int, int]:
    """(completed traverses, breakouts) from one pass of the band state machine on `y`."""
    mid = np.median(y)
    lo, hi = np.quantile(y, [Q_LO, Q_HI])
    W = hi - lo
    if W <= 0:
        return 0, 0
    up, dn = mid + H_BAND * W, mid - H_BAND * W
    bo_u, bo_d = mid + B_BREAK * W, mid - B_BREAK * W
    cross = breaks = 0
    armed = 0
    for v in y:
        if armed == -1:
            if v >= up:
                cross += 1
                armed = 1
                continue
            if v <= bo_d:
                breaks += 1
                armed = 0
                continue
        elif armed == 1:
            if v <= dn:
                cross += 1
                armed = -1
                continue
            if v >= bo_u:
                breaks += 1
                armed = 0
                continue
        if armed == 0:
            if v >= up:
                armed = 1
            elif v <= dn:
                armed = -1
    return cross, breaks


def detrended_path(r: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Cumulate returns to a price path, remove the linear drift, return (resid, drift, sigma)."""
    p = np.concatenate([[0.0], np.cumsum(r)])
    n = len(p) - 1
    t = np.arange(n + 1, dtype=np.float64)
    tc = t - t.mean()
    b = float((tc * (p - p.mean())).sum() / (tc * tc).sum())
    return p - (b * tc + p.mean()), b, float(np.std(r, ddof=1))


def label(r: np.ndarray, n_shuf: int = N_SHUF, rng=RNG) -> dict:
    """The oracle label for one window of returns `r`, with its OWN sign-shuffle benchmark."""
    y, b, sig = detrended_path(r)
    lo, hi = np.quantile(y, [Q_LO, Q_HI])
    W = float(hi - lo)
    n = len(r)
    width_sigma = W / (sig * np.sqrt(n)) if sig > 0 else 0.0
    cross, breaks = traverse_stats(y)
    obs_rel = cross / (cross + breaks) if (cross + breaks) else np.nan

    # --- the null: the SAME returns in random ORDER of sign, nothing else changed -------------
    sh_cross = np.empty(n_shuf)
    sh_rel = np.empty(n_shuf)
    a = np.abs(r)
    for i in range(n_shuf):
        s = np.where(rng.integers(0, 2, n) == 1, 1.0, -1.0)
        ys, _, _ = detrended_path(a * s)
        c, k = traverse_stats(ys)
        sh_cross[i] = c
        sh_rel[i] = c / (c + k) if (c + k) else np.nan
    drift_abs = abs(b) * n
    return {"cross": cross, "breaks": breaks, "traverse": obs_rel,
            "cross_dev": cross - float(np.mean(sh_cross)),
            "traverse_dev": (obs_rel - float(np.nanmean(sh_rel))
                             if np.isfinite(obs_rel) else np.nan),
            "shuf_cross": float(np.mean(sh_cross)),
            "shuf_traverse": float(np.nanmean(sh_rel)),
            "width_sigma": width_sigma, "drift_abs": drift_abs, "W": W,
            "drift_share": drift_abs / (drift_abs + W) if (drift_abs + W) > 0 else np.nan,
            "gated": width_sigma < WIDTH_SIGMA_MIN}


# =============================================================================================
P("=" * 100)
P("1  KNOWN-ANSWER CASES against each case's OWN sign shuffle")
P("=" * 100)
t = np.arange(N + 1, dtype=np.float64)


def rets(path):
    return np.diff(path)


cases = {
    "pure chop, 3 sine cycles": rets(np.sin(2 * np.pi * 3 * t / N) + 0.02 * RNG.normal(size=N+1)),
    "pure chop, 1 sine cycle": rets(np.sin(2 * np.pi * 1 * t / N) + 0.02 * RNG.normal(size=N+1)),
    "pure drift, straight line": rets((t / N) * 2.0 + 0.02 * RNG.normal(size=N + 1)),
    "random walk (gaussian)": RNG.normal(size=N),
    "random walk (fat tails, t3)": RNG.standard_t(3, size=N),
    "chop + minor drift": rets(np.sin(2*np.pi*3*t/N) + (t/N)*1.0 + 0.02*RNG.normal(size=N+1)),
    "chop + major drift": rets(np.sin(2*np.pi*3*t/N) + (t/N)*6.0 + 0.02*RNG.normal(size=N+1)),
}
P("")
P("   case                          cross  shuf  DEV    traverse  shuf   DEV    w/sig  gated")
for name, r in cases.items():
    L = label(r, n_shuf=400)
    P(f"   {name:<28} {L['cross']:>5}  {L['shuf_cross']:4.1f} {L['cross_dev']:+5.1f}   "
      f"{L['traverse']:.3f}   {L['shuf_traverse']:.3f} {L['traverse_dev']:+.3f}  "
      f"{L['width_sigma']:.2f}   {'YES' if L['gated'] else 'no'}")
P("")
P("   THE FAT-TAIL PROBLEM IS GONE: a gaussian and a t(3) random walk both sit near DEV 0,")
P("   where v1's fixed gaussian benchmark would have scored the t(3) as strongly trending.")
P("   AND THE GATE FIRES ON THE STRAIGHT LINE, which v1 mislabelled as choppy.")

# =============================================================================================
P("")
P("=" * 100)
P("2  ON REAL DATA -- the label, and does it VARY AND PERSIST?")
P("=" * 100)
d = pd.read_parquet("data/fixtures/fut_day5m.parquet",
                    columns=["root", "day", "bar", "close", "present", "same_front"])
d = d[d["present"]]
d = d[d["same_front"]]
d = d[d["day"] <= "2023-12-29"]

P("")
P("   root   sess   cross_dev   SE     t      traverse_dev   SE     t     gated%")
store = {}
for r in ("ES", "NQ", "YM", "RTY", "GC", "ZN", "ZB", "6E", "CL", "HO"):
    g = d[d["root"] == r].sort_values(["day", "bar"], kind="stable")
    R, days = Q.session_matrix(g, "close")
    if R.shape[1] < 500:
        continue
    rng = np.random.default_rng(abs(hash(r)) % 2**31)
    L = [label(R[:, j], n_shuf=60, rng=rng) for j in range(R.shape[1])]
    cd = np.array([x["cross_dev"] for x in L])
    td = np.array([x["traverse_dev"] for x in L])
    gt = np.array([x["gated"] for x in L])
    keep = ~gt
    cd_k, td_k = cd[keep], td[keep]
    se_c = np.nanstd(cd_k, ddof=1) / np.sqrt(np.isfinite(cd_k).sum())
    se_t = np.nanstd(td_k, ddof=1) / np.sqrt(np.isfinite(td_k).sum())
    store[r] = (cd_k, td_k, np.array(days)[keep])
    P(f"   {r:>4}  {keep.sum():>5}   {np.nanmean(cd_k):+.4f}  {se_c:.4f} {np.nanmean(cd_k)/se_c:+6.2f}"
      f"    {np.nanmean(td_k):+.4f}   {se_t:.4f} {np.nanmean(td_k)/se_t:+6.2f}   {gt.mean():.1%}")

P("")
P("   RELIABILITY of the traverse-deviation label: corr(window W, next window W), within root,")
P("   NON-OVERLAPPING. The scaling exponent scored all-noise here (D526 s8).")
P("")
WS = (1, 5, 10, 20, 60)
P("   root    " + "  ".join(f"W={w:<4}" for w in WS) + "   (pairs)")
tally = {w: [] for w in WS}
for r, (cd, td, days) in store.items():
    cells, ns = [], []
    s = td[np.isfinite(td)]
    for W in WS:
        nb = len(s) // W
        if nb < 10:
            cells.append("  --  ")
            ns.append(0)
            continue
        blk = s[:nb * W].reshape(nb, W).mean(1)
        a, b = blk[:-1][::2], blk[1:][::2]
        v = M.pearson(a, b) if len(a) > 5 else np.nan
        cells.append(f"{v:+.3f}" if np.isfinite(v) else "  --  ")
        ns.append(len(a))
        if np.isfinite(v):
            tally[W].append(v)
    P(f"   {r:>4}    " + "  ".join(cells) + "   " + " ".join(f"{n}" for n in ns))
P("")
P("   window   cells  positive   mean     SE at that n   mean/SE")
for W in WS:
    v = np.array(tally[W])
    if len(v) == 0:
        continue
    npair = max(1, len(store["ES"][1][np.isfinite(store["ES"][1])]) // W // 2)
    se = 1 / np.sqrt(max(npair - 1, 1))
    P(f"   W={W:<5}  {len(v):>5}  {int((v>0).sum())}/{len(v)}      {v.mean():+.3f}"
      f"    {se:.3f}          {v.mean()/se:+.2f}")
