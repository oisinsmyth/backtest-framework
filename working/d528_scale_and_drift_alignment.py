"""Two of the principal's points, tested together on the SHIFTED (causal) detector.

1  HIS BRAINWAVE: causality should BREAK the self-similarity. The oracle was flat across scales
   because it had look-ahead; causally, a SMALLER scale means less CLOCK TIME between the
   estimation half and the trade, so less time for the level to go stale. Prediction: small s
   does better, large s gets knocked around.

2  HIS CORRECTION ON THE DRIFT. I computed -s*slope*d as a COST, but its sign depends on which
   side of the level you enter: short above a FALLING level and the drift is a TAILWIND. So
   condition on ALIGNMENT -- take only excursions where the level drifts TOWARD the price
   (s*slope < 0). Causal, since the slope is the estimation half's.

STRUCTURE, all causal:  history [0,20) -> level [10,20) -> trade [20,31) -> track 20
   span = 51 bars, against the oracle's 21. THE CAUSAL STRUCTURE COSTS THE TOP OF THE LADDER:
   51 bars is 408 minutes at s=8 and 663 at s=13, so s=13 and s=20 do not fit a session at all.

P&L uses the REALISED residual at the exit bar, not the threshold -- the idealised-fill version
in the previous script overstated it by ~24 ticks and must not be reused.

Nothing admitted (R15). No pre-registered statistic is changed.
"""
import sys
import numpy as np

sys.path.insert(0, "scripts")
import d528_mean_reversion_oracle as Q     # noqa: E402

X, TAU = 2.0, 20
H = Q.H_EST
TRADE, HIST = 11, 2 * Q.H_EST
SPAN = HIST + TRADE + TAU
SCALES = (1, 2, 3, 5, 8)
N_SHUF = 40
RNG = np.random.default_rng(528123)


def P(*a):
    print(*a, flush=True)


def fit(seg):
    n = seg.shape[0]
    t = np.arange(n, dtype=np.float64)
    tc = t - t.mean()
    b = (tc[:, None] * (seg - seg.mean(0))).sum(0) / (tc * tc).sum()
    a = seg.mean(0) - b * t.mean()
    r = seg - (a[None, :] + b[None, :] * t[:, None])
    return b, a, r.std(0, ddof=1)


def structures(path, off=0):
    cols = []
    j = off
    while j + HIST + TRADE <= len(path):
        hi = min(j + SPAN, len(path))
        c = np.full(SPAN, np.nan)
        c[:hi - j] = path[j:hi]
        if np.isfinite(c[:HIST + TRADE]).all():
            cols.append(c)
        j += TRADE
    return np.column_stack(cols) if cols else np.zeros((SPAN, 0))


def admit(B, tick):
    b1, _, s1 = fit(B[:H])
    b2, _, s2 = fit(B[H:HIST])
    pooled = np.sqrt(0.5 * (s1 ** 2 + s2 ** 2))
    with np.errstate(invalid="ignore"):
        ok = (np.abs(b1 - b2) * H <= 0.5 * pooled) & (pooled > 0)
    med = np.median(np.abs(np.diff(B[H:HIST], axis=0)), axis=0) / tick
    return np.nan_to_num(ok, nan=False).astype(bool) & (med >= Q.MIN_TICKS)


def level(B):
    b, a, sd = fit(B[H:HIST])
    t = np.arange(SPAN, dtype=np.float64) - H
    return B - (a[None, :] + b[None, :] * t[:, None]), sd, b


def outcome(y, sd, slope, tick, align=None):
    """First excursion in the trade window, trade-correct precedence, REALISED-fill P&L.

    align: None = all, -1 = only where the level drifts TOWARD the price (tailwind),
           +1 = only headwind."""
    M = y.shape[1]
    thr, ext = X * sd, Q.EXT_MULT * X * sd
    R, PN = [], []
    for m in range(M):
        yy = y[:, m]
        j0 = -1
        for j in range(HIST, HIST + TRADE):
            if np.isfinite(yy[j]) and abs(yy[j]) >= thr[m]:
                j0 = j
                break
        if j0 < 0:
            continue
        s = np.sign(yy[j0])
        if align is not None and np.sign(s * slope[m]) != align:
            continue
        seg = yy[j0 + 1:min(j0 + 1 + TAU, SPAN)] * s
        ok = np.isfinite(seg)
        if not ok.any():
            continue
        idx = np.flatnonzero(ok)
        sv = seg[idx]
        hr = np.flatnonzero(sv <= 0)
        he = np.flatnonzero(sv >= ext[m])
        i_r = idx[hr[0]] if len(hr) else 10 ** 9
        i_e = idx[he[0]] if len(he) else 10 ** 9
        ret = i_r < i_e
        d = (min(i_r, i_e) if min(i_r, i_e) < 10 ** 9 else idx[-1]) + 1
        # REALISED residual at the exit bar, not the threshold.
        # P&L = s*(y_entry - y_exit - slope*d). The earlier form used |y_exit|, which on a
        # RETURN (where the residual CROSSES the level and flips sign) SUBTRACTED where it
        # should have ADDED -- understating every winner by 2*|y_exit|.
        y_end = yy[min(j0 + d, SPAN - 1)]
        pnl = s * (yy[j0] - y_end - slope[m] * d)
        R.append(bool(ret))
        PN.append(pnl / tick)
    return np.array(R), np.array(PN)


d = Q.load()
sp = Q.specs()
roots = sorted(set(d["root"]) & set(sp))
P(f"SHIFTED detector across the ladder. x={X} sigma, tau={TAU}, {len(roots)} roots, "
  f"{N_SHUF} shuffles, realised-fill P&L")
P(f"  span {SPAN} bars -- at s=13 that is {SPAN*13} minutes, so the top of the ladder "
  f"CANNOT be measured causally in a session\n")

P("  s (min)  clock gap   windows    exc   P(ret)   null    EXCESS    t      P&L ticks  median")
P("           est->trade                                                    (realised)")
for s in SCALES:
    nw = ne = 0
    Rs, PNs = [], []
    nret = nnull = 0
    for r in roots:
        g = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        paths = Q.session_bars(g, s)
        for day, pth in paths:
            B = structures(pth)
            if B.shape[1] == 0:
                continue
            keep = admit(B, tick)
            if not keep.any():
                continue
            Bk = B[:, keep]
            nw += int(keep.sum())
            y, sd, sl = level(Bk)
            R, PN = outcome(y, sd, sl, tick)
            if len(R) == 0:
                continue
            ne += len(R)
            Rs.append(R); PNs.append(PN)
            rr = np.diff(Bk, axis=0)
            for _ in range(N_SHUF):
                sg = np.where(RNG.integers(0, 2, rr.shape) == 1, 1.0, -1.0)
                Bn = np.vstack([Bk[:1], Bk[:1] + np.nancumsum(np.abs(rr) * sg, axis=0)])
                yn, sdn, sln = level(Bn)
                Rn, _ = outcome(yn, sdn, sln, tick)
                if len(Rn):
                    nret += int(Rn.sum()); nnull += len(Rn)
    if ne < 30:
        P(f"  {s:>7}  {(HIST-H)*s:>9}m   {nw:>8,} {ne:>6,}   too few")
        continue
    R = np.concatenate(Rs); PN = np.concatenate(PNs)
    po, pn = R.mean(), nret / max(nnull, 1)
    se = np.sqrt(po * (1 - po) / len(R) + pn * (1 - pn) / max(nnull, 1))
    P(f"  {s:>7}  {(HIST-H)*s:>9}m   {nw:>8,} {ne:>6,}   {po:.4f}  {pn:.4f}  "
      f"{po-pn:+.4f}  {(po-pn)/se:+5.1f}    {np.nanmean(PN):+8.2f}  {np.nanmedian(PN):+7.2f}")

P("\n  DRIFT ALIGNMENT -- only excursions where the level drifts TOWARD the price (tailwind)")
P("  s (min)   align      exc    P(ret)   EXCESS vs all   P&L ticks   median")
for s in SCALES:
    for al, name in ((-1, "tailwind"), (+1, "headwind")):
        ne = 0
        Rs, PNs = [], []
        for r in roots:
            g = d[d["root"] == r]
            tick = sp[r]["tick_price_units"]
            for day, pth in Q.session_bars(g, s):
                B = structures(pth)
                if B.shape[1] == 0:
                    continue
                keep = admit(B, tick)
                if not keep.any():
                    continue
                y, sd, sl = level(B[:, keep])
                R, PN = outcome(y, sd, sl, tick, align=al)
                if len(R):
                    ne += len(R); Rs.append(R); PNs.append(PN)
        if ne < 30:
            continue
        R = np.concatenate(Rs); PN = np.concatenate(PNs)
        P(f"  {s:>7}   {name:<9} {ne:>6,}   {R.mean():.4f}        --        "
          f"{np.nanmean(PN):+8.2f}  {np.nanmedian(PN):+7.2f}")
