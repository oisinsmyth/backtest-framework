"""ONE authorised in-sample read: does A1 help, and can a CAUSAL rule replace it?

Pre-specified before running. Primary level `half_line`, s=5, phase 0, x=2.0 sigma, tau=20,
pooled over roots, in-sample only (<= 2026-04-10).

ADMISSION VARIANTS -- the first four are diagnostic, the last three are CAUSAL CANDIDATES:
  V0  no filter at all
  V1  A2 only, and A2 made CAUSAL: median |r| over the ESTIMATION HALF >= 4 ticks
  V2  A1 + A2, the current non-causal rule
  V3  A1's SLOPE-agreement half only, + A2
  V4  A1's SIGMA-agreement half only, + A2
  C1  A2 + causal DRIFT filter        |slope|*H/sigma below its median
  C2  A2 + causal CROSSING filter     estimation-half level crossings at or above its median
  C3  A2 + both causal filters
Thresholds for C1/C2 are each feature's own MEDIAN -- a declared split, not a search.

AND THE DRIFT TERM, which the sigma-unit expectancy ignored. Entering short above the level:
    P&L = |y_entry| - sign(y_entry) * slope * holding_bars
so a level that slopes the way you are leaning EATS the target. Because the slope is measured on
the first half and the excursion is in the second, momentum makes sign(y) and slope POSITIVELY
correlated, so the drift is expected to HURT. This measures it.

No pre-registered statistic is changed. Nothing is admitted (R15).
"""
import json
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
import d528_mean_reversion_oracle as Q     # noqa: E402

S, PHASE, X, TAU = 5, 0, 2.0, 20
N, H = Q.N, Q.H_EST
T = N + 1 + max(Q.TAUS)
N_SHUF = 50
RNG = np.random.default_rng(5281)


def P(*a):
    print(*a, flush=True)


def features(Pm, tick):
    """Everything an admission rule may read, plus what A1 reads (non-causal)."""
    W1 = Pm[:H]
    t = np.arange(T, dtype=np.float64)
    tw = t[:H]
    tc = tw - tw.mean()
    b = (tc[:, None] * (W1 - W1.mean(0))).sum(0) / (tc * tc).sum()
    a = W1.mean(0) - b * tw.mean()
    y = Pm - (a[None, :] + b[None, :] * t[:, None])
    sig = y[:H].std(0, ddof=1)
    # CAUSAL features, estimation half only
    with np.errstate(divide="ignore", invalid="ignore"):
        drift = np.abs(b) * H / np.where(sig > 0, sig, np.nan)
    s1 = np.sign(y[:H])
    s1 = np.where(s1 == 0, np.nan, s1)
    cross_est = np.nansum(np.abs(np.diff(s1, axis=0)) > 1.5, axis=0)
    med_ticks_est = np.median(np.abs(np.diff(W1, axis=0)), axis=0) / tick
    # A1's two halves (NON-causal: reads the second half)
    WW = Pm[:N + 1]
    h = (N + 1) // 2
    sl, sg = [], []
    for part in (WW[:h], WW[h:]):
        n_ = part.shape[0]
        tt = np.arange(n_, dtype=np.float64)
        tcc = tt - tt.mean()
        bb = (tcc[:, None] * (part - part.mean(0))).sum(0) / (tcc * tcc).sum()
        rr = part - (part.mean(0) + bb[None, :] * tcc[:, None])
        sl.append(bb)
        sg.append(rr.std(0, ddof=1))
    sig_pool = np.sqrt(0.5 * (sg[0] ** 2 + sg[1] ** 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        a1_slope = np.abs(sl[0] - sl[1]) * (N / 2) <= 0.5 * sig_pool
        ratio = np.where(sg[1] > 0, sg[0] / sg[1], np.inf)
        a1_sigma = (ratio >= 0.5) & (ratio <= 2.0)
    return {"y": y, "sig": sig, "slope": b, "drift": drift, "cross_est": cross_est,
            "a2": med_ticks_est >= Q.MIN_TICKS, "a1_slope": a1_slope & (sig_pool > 0),
            "a1_sigma": a1_sigma & (sig_pool > 0)}


def outcomes_pnl(y, sig, slope, valid, tick):
    """Per FIRST excursion in the measurement half: outcome and REALISED P&L in sigma and ticks."""
    M = y.shape[1]
    thr = X * sig
    ext = Q.EXT_MULT * thr
    res = {k: [] for k in ("ret", "ex", "pnl_sig", "pnl_tick", "col")}
    for m in range(M):
        yy = y[:, m]
        j0 = -1
        for j in range(H, N + 1):
            if valid[j, m] and abs(yy[j]) >= thr[m]:
                j0 = j
                break
        if j0 < 0:
            continue
        s = np.sign(yy[j0])
        hi = min(j0 + 1 + TAU, T)
        seg = yy[j0 + 1:hi] * s
        vv = valid[j0 + 1:hi, m]
        if not vv.any():
            continue
        seg = np.where(vv, seg, np.nan)
        i_ret = np.nanargmin(np.where(seg <= 0, np.arange(len(seg)), np.nan)) \
            if np.nansum(seg <= 0) else -1
        i_ext = np.nanargmin(np.where(seg >= ext[m], np.arange(len(seg)), np.nan)) \
            if np.nansum(seg >= ext[m]) else -1
        ret = (i_ret >= 0) and (i_ext < 0 or i_ret <= i_ext)
        exd = (not ret) and i_ext >= 0
        d = (i_ret if ret else (i_ext if exd else len(seg) - 1)) + 1
        # P&L = |y_entry| - target_move ; the LEVEL moves by slope*d over the hold
        gross = abs(yy[j0]) - (abs(yy[j0]) if ret else (-0.5 * thr[m] if exd else
                                                        abs(yy[min(j0 + d, T - 1)])))
        pnl = (abs(yy[j0]) - abs(yy[min(j0 + d, T - 1)])) - s * slope[m] * d
        res["ret"].append(ret); res["ex"].append(exd)
        res["pnl_sig"].append(pnl / sig[m] if sig[m] > 0 else np.nan)
        res["pnl_tick"].append(pnl / tick)
        res["col"].append(m)
    return {k: np.array(v) for k, v in res.items()}


d = Q.load()
sp = Q.specs()
roots = sorted(set(d["root"]) & set(sp))
P(f"ONE in-sample read. s={S}, phase {PHASE}, x={X} sigma, tau={TAU}, "
  f"{len(roots)} roots, {N_SHUF} shuffles")
P(f"window {d['day'].min()} .. {d['day'].max()}\n")

store = []
for r in roots:
    g = d[d["root"] == r]
    tick = sp[r]["tick_price_units"]
    paths = Q.session_bars(g, S)
    if not paths:
        continue
    Pm, valid, sid = Q.windows_of(paths, PHASE)
    if Pm.shape[1] == 0:
        continue
    f = features(Pm, tick)
    store.append((r, Pm, valid, tick, f))

VARIANTS = {
    "V0 no filter": lambda f: np.ones(len(f["sig"]), bool),
    "V1 A2 only (causal)": lambda f: f["a2"],
    "V2 A1+A2 (current)": lambda f: f["a2"] & f["a1_slope"] & f["a1_sigma"],
    "V3 A1-slope + A2": lambda f: f["a2"] & f["a1_slope"],
    "V4 A1-sigma + A2": lambda f: f["a2"] & f["a1_sigma"],
    "C1 A2 + low drift": lambda f: f["a2"] & (f["drift"] <= np.nanmedian(f["drift"])),
    "C2 A2 + many crossings": lambda f: f["a2"] & (f["cross_est"]
                                                   >= np.nanmedian(f["cross_est"])),
    "C3 A2 + both causal": lambda f: (f["a2"] & (f["drift"] <= np.nanmedian(f["drift"]))
                                      & (f["cross_est"] >= np.nanmedian(f["cross_est"]))),
}

P("  variant                  windows   exc    P(ret)   null    EXCESS   "
  "mean P&L (sig)  (ticks)  drift cost")
for name, rule in VARIANTS.items():
    nw = ne = 0
    rets = []
    pnl_s, pnl_t, drift_cost = [], [], []
    nret = nnull = 0
    for (r, Pm, valid, tick, f) in store:
        keep = rule(f) & (f["sig"] > 0)
        keep = np.nan_to_num(keep, nan=False).astype(bool)
        if not keep.any():
            continue
        nw += int(keep.sum())
        yk, sk, bk, vk = f["y"][:, keep], f["sig"][keep], f["slope"][keep], valid[:, keep]
        o = outcomes_pnl(yk, sk, bk, vk, tick)
        if len(o["ret"]) == 0:
            continue
        ne += len(o["ret"])
        rets.append(o["ret"])
        pnl_s.append(o["pnl_sig"]); pnl_t.append(o["pnl_tick"])
        # the drift term alone, in sigma units, for the same excursions
        # (already folded into pnl; reported separately below via the no-drift variant)
        # --- null: sign shuffle of the SAME admitted windows
        Pk = Pm[:, keep]
        rr = np.diff(Pk, axis=0)
        for _ in range(N_SHUF):
            sg = np.where(RNG.integers(0, 2, rr.shape) == 1, 1.0, -1.0)
            Pn = np.vstack([Pk[:1], Pk[:1] + np.nancumsum(np.abs(rr) * sg, axis=0)])
            fn = features(Pn, tick)
            on = outcomes_pnl(fn["y"], fn["sig"], fn["slope"], vk, tick)
            if len(on["ret"]):
                nret += int(on["ret"].sum()); nnull += len(on["ret"])
    if ne == 0:
        continue
    R = np.concatenate(rets)
    PS = np.concatenate(pnl_s); PT = np.concatenate(pnl_t)
    po = R.mean(); pn = nret / max(nnull, 1)
    se = np.sqrt(po * (1 - po) / len(R) + pn * (1 - pn) / max(nnull, 1))
    P(f"  {name:<24} {nw:>7,} {ne:>6,}  {po:.4f}  {pn:.4f}  {po-pn:+.4f} "
      f"{'*' if abs(po-pn) > 2*se else ' '}   {np.nanmean(PS):+.4f}      "
      f"{np.nanmean(PT):+6.2f}")

P("\n  * marks an excess beyond 2 SE. 'mean P&L' is REALISED and INCLUDES the drift term")
P("  -slope*d, which the sigma-unit expectancy of +0.5683 ignored.")
