"""THE SHIFTED DETECTOR: move A1's stability test entirely into the PAST, then trade forward.

The original A1 tested whether the window's SECOND half agreed with its FIRST -- and the second
half is the half we trade. So it selected windows in which the traded period behaved like the
fitted period, which is conditioning on the outcome. The +0.105 excess may be largely a
restatement of that selection.

THE SHIFT removes the tautology:

    bars [-2H, -H)  and  [-H, 0)     two PAST halves -> the slope-agreement test
    bars [-H, 0)                     the LEVEL and sigma
    bars [0, 11)                     where excursions are counted
    up to tau beyond                 where the return is tracked

Everything the detector reads precedes bar 0. It is fully causal, and it is also the honest test
of whether the original finding survives when the selection no longer peeks.

AND A PREMISE THAT CAN KILL IT FIRST: if A1-slope-passing does not PERSIST from one window to the
next, the shifted test recovers nothing by construction. Measured here alongside.

TRADE-CORRECT PRECEDENCE throughout: an excursion that hits the extend threshold BEFORE the level
is a LOSS, not a return. The pre-registered runner used the permissive order and every P(return)
it published is the permissive one.

Nothing is admitted (R15). No pre-registered statistic is changed.
"""
import sys
import numpy as np

sys.path.insert(0, "scripts")
import d528_mean_reversion_oracle as Q     # noqa: E402

S, PHASE, X, TAU = 5, 0, 2.0, 20
H = Q.H_EST                 # 10
TRADE = 11                  # bars in which an excursion may start, matching the original
HIST = 2 * H                # 20 bars of history: two halves for the stability test
SPAN = HIST + TRADE + TAU * 2
N_SHUF = 50
RNG = np.random.default_rng(52812)


def P(*a):
    print(*a, flush=True)


def fit(seg):
    """(slope, intercept, resid_sd) of a least-squares line on `seg` (n, M)."""
    n = seg.shape[0]
    t = np.arange(n, dtype=np.float64)
    tc = t - t.mean()
    b = (tc[:, None] * (seg - seg.mean(0))).sum(0) / (tc * tc).sum()
    a = seg.mean(0) - b * t.mean()
    r = seg - (a[None, :] + b[None, :] * t[:, None])
    return b, a, r.std(0, ddof=1)


def structures(path, phase_off):
    """(SPAN, M) price blocks whose TRADE windows tile the session."""
    cols = []
    j = phase_off
    while j + HIST + TRADE <= len(path):
        hi = min(j + SPAN, len(path))
        c = np.full(SPAN, np.nan)
        c[:hi - j] = path[j:hi]
        if np.isfinite(c[:HIST + TRADE]).all():
            cols.append(c)
        j += TRADE
    return np.column_stack(cols) if cols else np.zeros((SPAN, 0))


def admit_shifted(B):
    """A1's slope-agreement test on TWO PAST HALVES, plus the causal lattice filter."""
    b1, _, s1 = fit(B[:H])
    b2, _, s2 = fit(B[H:HIST])
    pooled = np.sqrt(0.5 * (s1 ** 2 + s2 ** 2))
    with np.errstate(invalid="ignore"):
        ok = (np.abs(b1 - b2) * H <= 0.5 * pooled) & (pooled > 0)
    return np.nan_to_num(ok, nan=False).astype(bool)


def level_and_trade(B, tick):
    """Level and sigma from bars [H, HIST); excursions counted in [HIST, HIST+TRADE)."""
    b, a, sd = fit(B[H:HIST])
    t = np.arange(SPAN, dtype=np.float64) - H
    y = B - (a[None, :] + b[None, :] * t[:, None])
    return y, sd, b


def outcome(y, sd, slope, tick):
    """First excursion in the trade window; trade-correct precedence; realised P&L in ticks."""
    M = y.shape[1]
    thr = X * sd
    ext = Q.EXT_MULT * thr
    out = {"ret": [], "pnl": []}
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
        seg = yy[j0 + 1:min(j0 + 1 + TAU, SPAN)] * s
        seg = seg[np.isfinite(seg)]
        if len(seg) == 0:
            continue
        hit_r = np.flatnonzero(seg <= 0)
        hit_e = np.flatnonzero(seg >= ext[m])
        i_r = hit_r[0] if len(hit_r) else 10 ** 9
        i_e = hit_e[0] if len(hit_e) else 10 ** 9
        ret = i_r < i_e
        d = (min(i_r, i_e) if min(i_r, i_e) < 10 ** 9 else len(seg) - 1) + 1
        y_end = 0.0 if ret else (ext[m] * s if i_e < 10 ** 9 else yy[j0 + d] * s * s)
        pnl = (abs(yy[j0]) - abs(y_end)) - s * slope[m] * d
        out["ret"].append(bool(ret))
        out["pnl"].append(pnl / tick)
    return np.array(out["ret"]), np.array(out["pnl"])


d = Q.load()
sp = Q.specs()
roots = sorted(set(d["root"]) & set(sp))
P(f"THE SHIFTED DETECTOR. s={S}, x={X} sigma, tau={TAU}, {len(roots)} roots, "
  f"{N_SHUF} shuffles, trade-correct precedence")
P(f"  structure: history [0,{HIST}) -> level [{H},{HIST}) -> trade "
  f"[{HIST},{HIST+TRADE}) -> track {TAU}")
P(f"  window {d['day'].min()} .. {d['day'].max()}\n")

P("1  THE PREMISE -- does A1-slope-passing PERSIST from one window to the next?")
P("   root   windows   P(pass)   P(pass | previous passed)   lift")
persist = []
blocks = []
for r in roots:
    g = d[d["root"] == r]
    tick = sp[r]["tick_price_units"]
    paths = Q.session_bars(g, S)
    if not paths:
        continue
    Bs, seq = [], []
    for day, pth in paths:
        B = structures(pth, PHASE)
        if B.shape[1] == 0:
            continue
        ok = admit_shifted(B)
        seq.append(ok)
        Bs.append((B, ok))
    if not seq:
        continue
    blocks.append((r, tick, Bs))
    allok = np.concatenate(seq)
    cond = [o[1:][o[:-1]] for o in seq if len(o) > 1]
    cond = np.concatenate(cond) if cond else np.zeros(0, bool)
    if len(allok) < 100 or len(cond) < 30:
        continue
    persist.append((r, len(allok), allok.mean(), cond.mean()))
for r, n, p0, p1 in sorted(persist, key=lambda t: -(t[3] - t[2]))[:6]:
    P(f"   {r:>4}  {n:>8,}   {p0:.4f}          {p1:.4f}            {p1-p0:+.4f}")
pa = np.array([p[2] for p in persist]); pb = np.array([p[3] for p in persist])
P(f"   ... {len(persist)} roots.  MEAN P(pass) {pa.mean():.4f}   "
  f"MEAN P(pass|prev) {pb.mean():.4f}   MEAN LIFT {(pb-pa).mean():+.4f}")
P("   A lift near zero means the filter does not persist and the shift cannot recover it.")

P("\n2  THE SHIFTED DETECTOR vs its sign-shuffle null, and vs the non-causal original")
for label, use_filter in (("shifted A1-slope + lattice", True), ("no filter", False)):
    nw = ne = 0
    rets, pnls = [], []
    nret = nnull = 0
    for (r, tick, Bs) in blocks:
        for (B, ok) in Bs:
            keep = ok if use_filter else np.ones(B.shape[1], bool)
            med = np.median(np.abs(np.diff(B[H:HIST], axis=0)), axis=0) / tick
            keep = keep & (med >= Q.MIN_TICKS)
            if not keep.any():
                continue
            Bk = B[:, keep]
            nw += int(keep.sum())
            y, sd, sl = level_and_trade(Bk, tick)
            R, PN = outcome(y, sd, sl, tick)
            if len(R) == 0:
                continue
            ne += len(R)
            rets.append(R); pnls.append(PN)
            rr = np.diff(Bk, axis=0)
            for _ in range(N_SHUF):
                sg = np.where(RNG.integers(0, 2, rr.shape) == 1, 1.0, -1.0)
                Bn = np.vstack([Bk[:1], Bk[:1] + np.nancumsum(np.abs(rr) * sg, axis=0)])
                yn, sdn, sln = level_and_trade(Bn, tick)
                Rn, _ = outcome(yn, sdn, sln, tick)
                if len(Rn):
                    nret += int(Rn.sum()); nnull += len(Rn)
    if ne == 0:
        continue
    R = np.concatenate(rets); PN = np.concatenate(pnls)
    po, pn = R.mean(), nret / max(nnull, 1)
    se = np.sqrt(po * (1 - po) / len(R) + pn * (1 - pn) / max(nnull, 1))
    P(f"   {label:<28} windows {nw:>7,}  exc {ne:>6,}  P(ret) {po:.4f}  "
      f"null {pn:.4f}  EXCESS {po-pn:+.4f} (SE {se:.4f}, t {(po-pn)/se:+.1f})")
    P(f"   {'':<28} mean realised P&L {np.nanmean(PN):+.2f} ticks, "
      f"median {np.nanmedian(PN):+.2f}")
P("\n   BENCHMARKS from the authorised read, same precedence:")
P("     non-causal A1+A2   P(ret) 0.2891 null 0.1842 excess +0.1049   P&L +8.18 ticks")
P("     no filter          P(ret) 0.1679 null 0.1706 excess -0.0027   P&L -4.33 ticks")
