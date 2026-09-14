"""DOES PRICE DECELERATE AFTER AN ALIGNED EXTREME? The mechanism, measured with real power.

    python working/d528_does_it_decelerate.py --self-test
    python working/d528_does_it_decelerate.py --run

Nothing admitted (R15). Exploratory. The reserved slice stays UNREAD.

WHY THIS AND NOT MORE P&L. `d528_why_zero.py` found the signal sitting in the OVERSHOOT, not the
hit rate: on the `traverse` classifier the realised loss on a stop-out was 1.389 of the stop
distance against a null of 1.659 at s=1, and 1.222 against 1.424 at s=3. If that is real, price
DECELERATES as it extends past an aligned extreme. But those cells held 169 and 210 trades, because
a P&L test throws away most of the data: it needs non-overlapping positions, it collapses a whole
path into one number, and it is dominated by the fill convention.

THE MECHANISM NEEDS NONE OF THAT. Measure, for every admitted excursion and with no exit rule at
all, the mean signed continuation

    g(k) = -s * (P[t+k] - P[t]) / sigma          s = sign(y_t), so g > 0 means REVERSION

against the same quantity on the sign shuffle. This uses EVERY excursion (no overlap rule), is a
drift rather than a hitting probability, so its standard error falls like sqrt(n) with a much
larger n, and the fill convention cannot touch it -- there is no fill.

    g_real(k) - g_null(k) > 0   =>  price reverts after the extreme, beyond its own sign shuffle
    the SHAPE in k              =>  over what horizon, which is what a target and stop need

AND THE ASYMMETRY SEPARATELY, because a mean can hide it. Two one-sided quantities per excursion,
both in sigma units and both over the next TAU bars:

    MFE   max favourable excursion   max_k  -s*(P[t+k] - P[t])      how far the reversion runs
    MAE   max adverse excursion      max_k  +s*(P[t+k] - P[t])      how far it extends first

MAE is the overshoot in its pure form -- the quantity a stop pays for -- and it is the one the P&L
table said was different. MFE/MAE is the geometry any target/stop rule inherits, so measuring both
says whether a viable rule EXISTS before any particular rule is chosen.

Every difference carries a block bootstrap over (root, day) sessions.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402

KS = (1, 2, 3, 5, 10, 20)
TAU = R.TAU
SCALES = (1, 3)
CELLS = (("none", "flat"), ("cross2", "line"), ("ac1neg", "flat"), ("traverse", "flat"),
         ("traverse", "line"))
N_SHUF = 20
N_BOOT = 2000
SEED = 528421


def P(*a):
    print(*a, flush=True)


def excursion_stats(path, c, lvl, keep):
    """Per admitted excursion: g(k) for k in KS, plus MFE and MAE over TAU bars, in sigma units.

    NO exit rule and NO overlap rule -- every admitted bar contributes, which is the whole point.
    Returns (G, MFE, MAE) with G of shape (n_exc, len(KS)).
    """
    idx = np.flatnonzero(keep)
    n = path.shape[-1]
    if len(idx) == 0:
        return np.zeros((0, len(KS))), np.zeros(0), np.zeros(0)
    t = idx + 2 * Z.H
    ok = t < n - 1
    idx, t = idx[ok], t[ok]
    if len(idx) == 0:
        return np.zeros((0, len(KS))), np.zeros(0), np.zeros(0)
    y = c[f"{lvl}_y"][idx]
    sd = c[f"{lvl}_sd"][idx]
    s = np.sign(y)
    p0 = path[t]
    kk = np.arange(1, TAU + 1)
    j = t[:, None] + kk[None, :]
    valid = j <= (n - 1)
    F = path[np.minimum(j, n - 1)]
    # signed continuation in sigma units; +ve = toward the level = reversion
    move = (-s[:, None]) * (F - p0[:, None]) / sd[:, None]
    mv = np.where(valid, move, np.nan)
    G = np.full((len(idx), len(KS)), np.nan)
    for a, k in enumerate(KS):
        if k <= TAU:
            G[:, a] = mv[:, k - 1]
    # MFE and MAE include the ENTRY POINT (k=0, move 0), which floors both at zero. That is the
    # honest trade reading -- you can always exit flat -- and it is what makes MFE/MAE a ratio of
    # two non-negative distances. Without the entry point, MFE is the "best point reached" and is
    # NEGATIVE whenever price never came back at all, which makes the ratio meaningless.
    with np.errstate(invalid="ignore"):
        MFE = np.nanmax(np.where(valid, mv, -np.inf), axis=1)
        MAE = np.nanmax(np.where(valid, -mv, -np.inf), axis=1)
    MFE = np.where(np.isfinite(MFE), np.maximum(MFE, 0.0), np.nan)
    MAE = np.where(np.isfinite(MAE), np.maximum(MAE, 0.0), np.nan)
    return G, MFE, MAE


def boot_se(blocks, rng, n_boot=N_BOOT):
    """Block bootstrap SE of (real mean - null mean) from per-session (sum_r,n_r,sum_n,n_n)."""
    A = np.asarray(blocks, dtype=np.float64)
    if len(A) < 20:
        return np.nan
    nb = len(A)
    G = A[rng.integers(0, nb, (n_boot, nb))]
    nr, nn = G[:, :, 1].sum(1), G[:, :, 3].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(nr > 0, G[:, :, 0].sum(1) / nr, np.nan) - \
              np.where(nn > 0, G[:, :, 2].sum(1) / nn, np.nan)
    return float(np.nanstd(out, ddof=1))


def _engineered(step, rng):
    """A path with ONE engineered extreme, and the stats AT THAT BAR only.

    The bar matters. Entries also fire BEFORE the spike, and for those the spike sits inside the
    forward window and dominates every average -- at one such bar y was -1.49, making it a long,
    and the spike up then registered as a 70-sigma favourable move. Averaging over all entries
    therefore measures the contamination, not the orientation. So the engineered bar is selected
    by max |y| and asserted on alone.
    """
    base = 20000 + np.cumsum(rng.normal(0, 1.0, 60))
    base[-TAU - 1:] = base[-TAU - 2]
    base[-TAU - 1] += 30.0
    base[-TAU:] = base[-TAU - 1] + step * np.arange(1, TAU + 1)
    c = Z.classify2(base, 0.25)
    keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none", align=False)
    idx = np.flatnonzero(keep)
    assert len(idx), "the engineered path produced no entries -- the fixture cannot fire"
    G, f, a = excursion_stats(base, c, "flat", keep)
    q = int(np.argmax(np.abs(c["flat_y"][idx])))       # the spike bar
    return G[q, KS.index(10)], f[q], a[q]


def self_test():
    rng = np.random.default_rng(3)
    # 1. SIGN. At the engineered extreme, g must be POSITIVE when price is built to revert to its
    #    level and NEGATIVE when built to extend. A sign error here would invert every conclusion.
    for name, step, want in (("reverting", -1.2, +1), ("extending", +1.2, -1)):
        g, _, _ = _engineered(step, np.random.default_rng(3))
        assert np.sign(g) == want, f"{name} path gives g(10) = {g:+.3f}, wanted sign {want:+d}"
        P(f"   [1] {name:<10} path -> g(10) = {g:+7.3f} at the engineered bar "
          f"(wanted {want:+d})   OK")

    # 2. A MARTINGALE MUST GIVE ZERO. Sign-shuffled paths have no continuation either way, so
    #    g(k) must be ~0 at every k. This is the invariant the whole comparison rests on.
    rng2 = np.random.default_rng(5)
    acc = np.zeros(len(KS)); cnts = np.zeros(len(KS))
    sq = np.zeros(len(KS))
    for _ in range(80):
        base = 20000 + np.cumsum(rng2.normal(0, 2.0, 300))
        for spath in Z.shuffled(base, rng2, 8):
            c = Z.classify2(spath, 0.25)
            keep = Z.entry_mask(c, "flat", 0.25, 0.0, "none")
            G, _, _ = excursion_stats(spath, c, "flat", keep)
            if len(G):
                acc += np.nansum(G, axis=0)
                sq += np.nansum(G ** 2, axis=0)
                cnts += np.isfinite(G).sum(axis=0)
    g = acc / np.maximum(cnts, 1)
    se = np.sqrt(np.maximum(sq / np.maximum(cnts, 1) - g ** 2, 0)) / np.sqrt(np.maximum(cnts, 1))
    worst = int(np.argmax(np.abs(g / np.maximum(se, 1e-12))))
    P(f"   [2] martingale: g(k) over {int(cnts[0]):,} excursions, worst |t| at k={KS[worst]} "
      f"= {abs(g[worst]/se[worst]):.2f}")
    assert abs(g[worst] / se[worst]) < 4.0, f"g(k) on a martingale is {g[worst]:+.4f}, not 0"
    P("       every k within 4 SE of zero                                                 OK")

    # 3. MFE/MAE ORIENTATION at the engineered bar, and it must INVERT on the mirrored path --
    #    otherwise it is not testing orientation at all.
    _, fr_, ar_ = _engineered(-1.2, np.random.default_rng(3))
    _, fx_, ax_ = _engineered(+1.2, np.random.default_rng(3))
    assert min(fr_, ar_, fx_, ax_) >= 0.0, "MFE/MAE must be non-negative once floored at entry"
    assert fr_ > ar_, f"reverting: MFE {fr_:.2f} should exceed MAE {ar_:.2f}"
    assert fx_ < ax_, (f"extending: MFE {fx_:.2f} still exceeds MAE {ax_:.2f} -- the orientation "
                       f"test cannot fail")
    P(f"   [3] reverting MFE {fr_:.2f} > MAE {ar_:.2f};  extending MFE {fx_:.2f} < "
      f"MAE {ax_:.2f}; both >= 0  OK")
    P("\n   all self-tests pass\n")


def run():
    rng = np.random.default_rng(SEED)
    brng = np.random.default_rng(SEED + 1)
    d = Q.load()
    sp = Q.specs()
    roots = sorted(set(d["root"]) & set(sp))
    P("DOES PRICE DECELERATE AFTER AN ALIGNED EXTREME?")
    P(f"  g(k) = -s*(P[t+k]-P[t])/sigma, so g > 0 means REVERSION. Real minus its sign shuffle.")
    P(f"  Every admitted excursion, no exit rule, no overlap rule, no fill convention.")
    P(f"  {len(roots)} roots, {d['day'].min()} .. {d['day'].max()}, x={Z.X}s, "
      f"{N_SHUF} shuffles, drift-aligned\n")

    for s in SCALES:
        store = {cell: {"g": [np.zeros(0) for _ in KS], "blk": [[] for _ in KS],
                        "mfe": [], "mae": [], "mblk": [], "ablk": []} for cell in CELLS}
        for r in roots:
            g_ = d[d["root"] == r]
            tick = sp[r]["tick_price_units"]
            cost = R.COST.get(r, R.COST_DEFAULT)
            for day, pth in Q.session_bars(g_, s):
                c = Z.classify2(pth, tick)
                if c is None:
                    continue
                Pn = Z.shuffled(pth, rng, N_SHUF)
                cn = Z.classify2(Pn, tick)
                if cn is None:
                    continue
                for (cl, lv) in CELLS:
                    st = store[(cl, lv)]
                    keep = Z.entry_mask(c, lv, tick, cost, cl)
                    G, mfe, mae = excursion_stats(pth, c, lv, keep)
                    Gn_s = np.zeros(len(KS)); Gn_n = np.zeros(len(KS))
                    mfe_n = mae_n = 0.0
                    cnt_n = 0
                    for jj in range(N_SHUF):
                        cj = {k2: (v2[jj] if np.ndim(v2) > 0 and np.shape(v2)[0] == N_SHUF
                                   else v2) for k2, v2 in cn.items()}
                        kj = Z.entry_mask(cj, lv, tick, cost, cl)
                        Gj, fj, aj = excursion_stats(Pn[jj], cj, lv, kj)
                        if len(Gj):
                            Gn_s += np.nansum(Gj, axis=0)
                            Gn_n += np.isfinite(Gj).sum(axis=0)
                            mfe_n += float(np.nansum(fj)); mae_n += float(np.nansum(aj))
                            cnt_n += int(np.isfinite(fj).sum())
                    for a in range(len(KS)):
                        col = G[:, a] if len(G) else np.zeros(0)
                        sr = float(np.nansum(col)); nr = int(np.isfinite(col).sum())
                        if nr or Gn_n[a]:
                            st["blk"][a].append((sr, nr, Gn_s[a], Gn_n[a]))
                    if len(mfe):
                        st["mfe"].append(mfe); st["mae"].append(mae)
                    nfr = int(np.isfinite(mfe).sum()) if len(mfe) else 0
                    if nfr or cnt_n:
                        st["mblk"].append((float(np.nansum(mfe)) if len(mfe) else 0.0, nfr,
                                           mfe_n, cnt_n))
                        st["ablk"].append((float(np.nansum(mae)) if len(mae) else 0.0, nfr,
                                           mae_n, cnt_n))
        P(f"  s={s}   g(k) REAL MINUS NULL, in sigma units (positive = reversion). "
          f"t in brackets.")
        hdr = "    classifier  level    n_exc  " + "  ".join(f"k={k:<2}" for k in KS)
        P(hdr)
        for (cl, lv) in CELLS:
            st = store[(cl, lv)]
            row, trow = [], []
            nexc = 0
            for a in range(len(KS)):
                B = np.asarray(st["blk"][a], dtype=np.float64) if st["blk"][a] else None
                if B is None or B[:, 1].sum() < 50:
                    row.append("     --"); trow.append("      ")
                    continue
                nexc = max(nexc, int(B[:, 1].sum()))
                gr = B[:, 0].sum() / B[:, 1].sum()
                gn = B[:, 2].sum() / max(B[:, 3].sum(), 1)
                se = boot_se(st["blk"][a], brng)
                dif = gr - gn
                row.append(f"{dif:+7.4f}")
                trow.append(f"({dif/se:+4.1f})" if se and np.isfinite(se) and se > 0 else "  --  ")
            P(f"    {cl:<11} {lv:<6} {nexc:>7,}  " + " ".join(row))
            P(f"    {'':<11} {'':<6} {'':>7}  " + " ".join(f"{x:>7}" for x in trow))
        P("")
        P("    THE ASYMMETRY over the next 20 bars, in sigma (MFE = reversion run, "
          "MAE = overshoot)")
        P("    classifier  level     MFE real  null   DIFF    t  |  MAE real  null   DIFF"
          "    t  | MFE/MAE r/n")
        for (cl, lv) in CELLS:
            st = store[(cl, lv)]
            if not st["mblk"]:
                continue
            Bm = np.asarray(st["mblk"], dtype=np.float64)
            Ba = np.asarray(st["ablk"], dtype=np.float64)
            if Bm[:, 1].sum() < 50:
                continue
            fr = Bm[:, 0].sum() / Bm[:, 1].sum(); fn = Bm[:, 2].sum() / max(Bm[:, 3].sum(), 1)
            ar = Ba[:, 0].sum() / Ba[:, 1].sum(); an = Ba[:, 2].sum() / max(Ba[:, 3].sum(), 1)
            sef = boot_se(st["mblk"], brng); sea = boot_se(st["ablk"], brng)
            tf = (fr - fn) / sef if sef and sef > 0 else np.nan
            ta = (ar - an) / sea if sea and sea > 0 else np.nan
            P(f"    {cl:<11} {lv:<6}  {fr:8.3f} {fn:6.3f} {fr-fn:+7.4f} {tf:+5.1f}  |"
              f"  {ar:8.3f} {an:6.3f} {ar-an:+7.4f} {ta:+5.1f}  | "
              f"{fr/ar:.3f} / {fn/an:.3f}")
        P("")
    P("  A viable rule needs MFE/MAE for the real data ABOVE the null's: that ratio is the")
    P("  geometry any target/stop inherits, and it is prior to choosing one.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run:
        run()
    if not (a.self_test or a.run):
        ap.error("choose --self-test or --run")
