"""(1) DROP slope_ok, AND (2) IS THE TRAVERSAL TARGET A LEVEL-CHASING ARTEFACT?

    python working/d528_target_and_stability.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.

TWO THINGS THE DRIFT AUDIT MADE URGENT.

(1) `slope_ok` REMOVES 93.1% OF ALL BARS AND BUYS NOTHING. P(traverse | slope_ok) = 0.1470 against
    0.1497 for the bars it rejects -- a difference of 0.0027. It came from the original D528 A1
    test and was carried through eleven addenda without ever being justified against the target.
    Dropping it should multiply the candidate count by roughly 15x at no measured cost, which
    directly attacks the sample-size problem that has crippled every cell in this study.

(2) THE TARGET MAY BE MEASURING THE LEVEL, NOT THE PRICE. Forward traversal is currently defined
    against the [t-H,t) LINE EXTRAPOLATED forward. Drift-aligned excursions traverse at 10.8%
    and ANTI-aligned ones at 35.0% -- a 3.25x gap. But in the anti-aligned cell the level moves
    TOWARD the price, so the residual can traverse because the LEVEL moved, not because price
    reverted. That is the level-chasing artefact identified in ADDENDUM 1, resurfacing in the
    target itself rather than in the trade.

    THREE DEFINITIONS SEPARATE IT. Same sigma throughout (the flat-window sd), so the ONLY thing
    that changes is what the excursion is measured against:

        line    +/-1.5 sigma of the [t-H,t) line, extrapolated over [t, t+H)   <- the current one
        flat    +/-1.5 sigma of the [t-H,t) MEAN, held flat                    <- no slope carried
        price   +/-1.5 sigma of the PRICE AT t                                 <- no level at all

    THE PREDICTION, stated before running: if the aligned/anti-aligned asymmetry is level-chasing,
    it is LARGE under `line`, SMALLER under `flat`, and NEAR ZERO under `price`. If instead the
    asymmetry survives into `price`, the drift-alignment rule is discarding real reversion and the
    rule should be reconsidered rather than the target.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402

H = Z.H
X = 2.0
TRAV_K = 1.5
FEATS4 = ("vol_ratio", "squeeze", "vratio2", "ac1")
SEED = 528709


def P(*a):
    print(*a, flush=True)


def three_targets(path, c):
    """Forward traversal under three reference levels. Same sigma (flat-window sd) throughout,
    so the only difference is WHAT the excursion is measured against."""
    n = len(path)
    n_t = n - 2 * H
    out = {k: np.zeros(n_t, bool) for k in ("line", "flat", "price")}
    ok = np.zeros(n_t, bool)
    if n_t <= 0:
        return out, ok
    F = swv(path, H)
    t = np.arange(2 * H, n)
    valid = t + H <= n
    tv = t[valid]
    m = np.arange(H, dtype=np.float64)
    sd = c["flat_sd"][valid]                      # ONE sigma for all three definitions
    fwd = F[tv]
    with np.errstate(invalid="ignore"):
        # line: the [t-H,t) fit carried forward
        y_line = fwd - (c["a2"][valid][:, None] + c["slope"][valid][:, None] * (H + m))
        # flat: the [t-H,t) mean, held
        y_flat = fwd - c["flat_lvl"][valid][:, None]
        # price: no level at all, measured from the price at t
        y_px = fwd - path[tv][:, None]
        for k, y in (("line", y_line), ("flat", y_flat), ("price", y_px)):
            hit = (y.min(1) <= -TRAV_K * sd) & (y.max(1) >= TRAV_K * sd) & (sd > 0)
            out[k][valid] = np.nan_to_num(hit, nan=False).astype(bool)
        ok[valid] = np.isfinite(sd) & (sd > 0)
    return out, ok


def collect(roots, src, sp):
    rows = []
    for r in roots:
        if r not in sp:
            continue
        g = src[src["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            tg, ok = three_targets(px, c)
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(ok)
            with np.errstate(invalid="ignore"):
                f_slope = np.nan_to_num(c["slope_ok"], nan=False).astype(bool)
                f_a2 = np.asarray(c["a2ok"])
                f_exc = np.nan_to_num(np.abs(c["flat_y"]) >= X * c["flat_sd"],
                                      nan=False).astype(bool)
                f_align = np.nan_to_num(np.sign(c["flat_y"]) * c["slope"] < 0,
                                        nan=False).astype(bool)
                f_feas = np.nan_to_num(np.abs(c["flat_y"]) / tick > cost_tk,
                                       nan=False).astype(bool)
            sel = np.flatnonzero(ok)
            if len(sel) == 0:
                continue
            blk = {"root": np.full(len(sel), r, dtype=object),
                   "day": np.full(len(sel), day, dtype=object),
                   "y_line": tg["line"][sel].astype(float),
                   "y_flat": tg["flat"][sel].astype(float),
                   "y_price": tg["price"][sel].astype(float),
                   "f_slope": f_slope[sel], "f_a2": f_a2[sel], "f_exc": f_exc[sel],
                   "f_align": f_align[sel], "f_feas": f_feas[sel]}
            for k in FEATS4:
                v = ft[k]
                blk[k] = v[sel] if len(v) == n_t else np.full(len(sel), np.nan)
            rows.append(blk)
    cols = rows[0].keys()
    return pd.DataFrame({c: np.concatenate([b[c] for b in rows]) for c in cols})


def lift(df, feat, ycol, rng, n_boot=150):
    v = df[feat].to_numpy(float)
    ok = np.isfinite(v)
    if ok.sum() < 400:
        return (np.nan, np.nan, 0)
    q = np.nanpercentile(v[ok], 20)
    m = ok & (v <= q)
    if m.sum() < 150:
        return (np.nan, np.nan, 0)
    yv = df[ycol].to_numpy(float)
    val = yv[m].mean() - yv.mean()
    keys = (df["root"].astype(str) + "|" + df["day"].astype(str)).to_numpy()
    uk, inv = np.unique(keys, return_inverse=True)
    nb = len(uk)
    bs = np.empty(n_boot)
    for i in range(n_boot):
        pick = np.isin(inv, rng.integers(0, nb, nb))
        bs[i] = (yv[pick & m].mean() - yv[pick].mean()
                 if (pick & m).sum() > 50 else np.nan)
    return (val, float(np.nanstd(bs, ddof=1)), int(m.sum()))


def run():
    rng = np.random.default_rng(SEED)
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    P("(1) DROP slope_ok  AND  (2) IS THE TARGET A LEVEL-CHASING ARTEFACT?")
    P(f"  wide 5-minute fixture, {len(roots)} roots, through {W.IS_END}\n")
    d = collect(roots, f, sp)
    P(f"  {len(d):,} scored bars")
    for k in ("line", "flat", "price"):
        P(f"    base P(traverse, {k:<5}) = {d['y_' + k].mean():.4f}")
    P("")

    # ---------------------------------------------------------------- 2 first: the target
    P("=" * 110)
    P("2  THE ALIGNED / ANTI-ALIGNED ASYMMETRY UNDER THREE TARGET DEFINITIONS")
    P("   Feasible 2-sigma excursions only. If the gap shrinks as the level is removed, the")
    P("   asymmetry was the LEVEL moving, not price reverting.")
    P("")
    exc = (d["f_a2"] & d["f_exc"] & d["f_feas"]).to_numpy(bool)
    al = exc & d["f_align"].to_numpy(bool)
    an = exc & ~d["f_align"].to_numpy(bool)
    P(f"    feasible excursions {int(exc.sum()):,}   aligned {int(al.sum()):,} "
      f"({al.sum()/max(exc.sum(),1):.1%})   anti {int(an.sum()):,}")
    P("")
    P("    target      P(trav | ALIGNED)   P(trav | ANTI)     gap    ratio")
    for k in ("line", "flat", "price"):
        col = "y_" + k
        pa = d.loc[al, col].mean()
        pn = d.loc[an, col].mean()
        P(f"    {k:<10} {pa:>16.4f} {pn:>16.4f} {pn-pa:>+8.4f} {pn/max(pa,1e-9):>8.2f}x")
    P("")
    P("    PREDICTION WAS: large under `line`, smaller under `flat`, near zero under `price`")
    P("    if the asymmetry is level-chasing.")

    # ---------------------------------------------------------------- 1: drop slope_ok
    P("")
    P("=" * 110)
    P("1  DROPPING slope_ok -- what it costs and what it buys")
    P("")
    P("    chain                                   bars      kept   P(trav,line)  P(trav,price)")
    a2 = d["f_a2"].to_numpy(bool)
    sl = d["f_slope"].to_numpy(bool)
    ex = d["f_exc"].to_numpy(bool)
    fe = d["f_feas"].to_numpy(bool)
    ag = d["f_align"].to_numpy(bool)
    for nm, m in (("all scored bars", np.ones(len(d), bool)),
                  ("WITH slope_ok: +a2+exc+feas", sl & a2 & ex & fe),
                  ("WITH slope_ok: +aligned", sl & a2 & ex & fe & ag),
                  ("NO slope_ok:   +a2+exc+feas", a2 & ex & fe),
                  ("NO slope_ok:   +aligned", a2 & ex & fe & ag)):
        P(f"    {nm:<36} {int(m.sum()):>9,} {m.mean():>8.3%} "
          f"{d.loc[m, 'y_line'].mean():>13.4f} {d.loc[m, 'y_price'].mean():>14.4f}")
    gain = (a2 & ex & fe & ag).sum() / max((sl & a2 & ex & fe & ag).sum(), 1)
    P("")
    P(f"    >>> dropping slope_ok multiplies the tradeable candidate count by {gain:.1f}x")

    P("")
    P("    and does the FORECAST survive without it? Q1 lift, target = `price` (level-free)")
    P("")
    P("    population                        n(Q1)   vol_ratio    squeeze    vratio2       ac1")
    for nm, m in (("all scored bars", np.ones(len(d), bool)),
                  ("WITH slope_ok, aligned", sl & a2 & ex & fe & ag),
                  ("NO slope_ok, aligned", a2 & ex & fe & ag),
                  ("NO slope_ok, anti-aligned", a2 & ex & fe & ~ag)):
        sub = d[m]
        if len(sub) < 800:
            P(f"    {nm:<32} {len(sub):>7,}  too few")
            continue
        cells, n1 = [], 0
        for k in FEATS4:
            v, se, n = lift(sub, k, "y_price", rng)
            n1 = max(n1, n)
            cells.append(f"{v:+.4f}" + ("*" if (np.isfinite(se) and se > 0
                                                and abs(v) > 2 * se) else " "))
        P(f"    {nm:<32} {n1:>7,}  " + "  ".join(f"{c:>9}" for c in cells))
    P("    * = |lift| beyond 2 block-bootstrap SE, on the LEVEL-FREE target.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    else:
        ap.error("choose --run")
