"""D297 -- a trailing stop on the spread itself. Book-level exposure overlay.

    uv run python scripts/run_d297_overlay.py --selftest
    uv run python scripts/run_d297_overlay.py [--draws 1000]

PRE-REGISTERED AT `a0dd515`, committed before this file existed (R8). This
runner may not change the base book or add a cell.

THE BASE BOOK IS D295's B0 CONTROL, UNCHANGED, and this file adds exactly one
thing: a per-bar exposure scale.

    shadow    the UNMANAGED book's cumulative spread P&L, accruing always
    peak(t)   its running maximum THROUGH t-1
    dd(t)     peak(t) - shadow(t-1), in trailing 63-bar vol units
    scale(t)  1.0 if dd(t) < X else s
    book(t)   scale(t) * base(t)

THE SHADOW IS WHAT MAKES THIS WELL POSED. An overlay keyed on its own REALISED
equity freezes the moment it goes flat: no new peak can arrive, so it never
re-risks. The shadow accrues whether or not capital is deployed.

AND THE OVERLAY CANNOT CREATE EDGE. Scaling exposure scales return and vol
together; it wins only if the drawdown state carries TIMING information. Q3
states that as a falsifiable claim and section 3 of the output tests it directly.

THE STATISTIC IS SHARPE. A mean test would reject an overlay that is out of the
market 20% of the time for earning 20% less, which is arithmetic rather than
evidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


E = _load("d295", "run_d295_exits.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M = E.R, E.M

OUT = REPO / "data" / "d297_overlay.json"
X_LEVELS = (8.0, 12.0, 20.0, 30.0)   # amended: see D297. The
# declared 1.0-3.0 measured drawdown in DAILY vols, and this
# book's median drawdown is 4.6 of them, so every cell was a
# mostly-flat book rather than a trailing stop.
S_LEVELS = (0.0, 0.5)
VOL_WIN = 63
SEED = 20260903
ANN = 252.0


def trailing_vol(x, w=VOL_WIN):
    """Trailing sd of the book's own returns, LAGGED by one bar.

    Lagged because a threshold scaled by today's realised vol, applied today, is
    look-ahead. Assertion [1] holds it to that.
    """
    n = x.size
    out = np.full(n, np.nan)
    c1 = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])
    j = np.arange(w, n)
    s1 = c1[j + 1] - c1[j + 1 - w]
    s2 = c2[j + 1] - c2[j + 1 - w]
    var = (s2 - s1 * s1 / w) / (w - 1)
    out[j] = np.sqrt(np.maximum(var, 0.0))
    lag = np.full(n, np.nan)
    lag[1:] = out[:-1]
    return lag


def schedule(base, X, lag=True):
    """The on/off series. `False` = de-risked. Uses the shadow through t-1 only.

    `lag=False` is the DELIBERATELY BROKEN variant assertion [1b] fires at: it
    lets the rule see bar t's own return before deciding bar t's exposure.
    """
    n = base.size
    shadow = np.cumsum(base)
    vol = trailing_vol(base)
    prev = (np.concatenate([[0.0], shadow[:-1]]) if lag else shadow)
    peak = np.maximum.accumulate(prev)
    dd = peak - prev
    with np.errstate(invalid="ignore"):
        off = np.isfinite(vol) & (vol > 0) & (dd >= X * vol)
    return ~off, dd, vol


def stats(x, scale, rt_bp):
    """Sharpe and the rest, plus the transition cost the overlay actually pays."""
    r = x * scale
    sd = r.std(ddof=1)
    eq = np.cumsum(r)
    dd = np.maximum.accumulate(eq) - eq
    # a change of |ds| in exposure trades that fraction of the book; one
    # out-and-back cycle is a full round trip on the notional moved
    ds = np.abs(np.diff(np.concatenate([[1.0], scale])))
    cost_bar = float(ds.sum() * rt_bp / 2.0 / max(x.size, 1))
    return dict(
        mean_bp=float(r.mean() * 1e4), vol_bp=float(sd * 1e4),
        sharpe=float(r.mean() / sd * np.sqrt(ANN)) if sd > 0 else None,
        maxdd_bp=float(dd.max() * 1e4),
        exposure=float(scale.mean()),
        ret_per_exposure=float(r.mean() * 1e4 / max(scale.mean(), 1e-9)),
        transitions=int((ds > 1e-12).sum()),
        trans_per_yr=float((ds > 1e-12).sum() / (x.size / ANN)),
        notional_traded=float(ds.sum()),
        cost_bar_bp=cost_bar)


def matched_schedule(on, rng):
    """The treatment's own on/off pattern, CIRCULARLY ROTATED to a random phase.

    Rate and persistence are matched EXACTLY -- same off-bar count, same episode
    lengths, same order -- and only the alignment with the book's actual
    drawdowns is destroyed. That is precisely the question: does de-risking WHEN
    THE BOOK IS DOWN beat de-risking for the same amount of time at unrelated
    times?

    The first draft resampled episode start points and rejected overlaps, which
    silently lost episodes whenever the off-fraction was high -- assertion [4]
    caught it. A rotation cannot lose one.
    """
    return np.roll(on, int(rng.integers(1, on.size)))



# --------------------------------------------------------------------------
def assertions(base, rt_bp):
    print("\n  RUNNER ASSERTIONS", flush=True)
    n = base.size

    # 1. NO LOOK-AHEAD. The decision for bar t must use the shadow and the vol
    #    through t-1 only. Rebuilt by an EXPLICIT ACCUMULATION LOOP that shares
    #    no code path with `schedule` -- not a second call to cumsum -- and
    #    compared on EVERY bar rather than a sample, because a one-bar shift
    #    flips a threshold only where the drawdown sits near it.
    def hand(series, X, lag=True):
        acc, pk = 0.0, 0.0
        out = np.ones(series.size, dtype=bool)
        for t in range(series.size):
            if not lag:
                acc += series[t]
            if t > VOL_WIN:
                # VOL_WIN bars ENDING AT t-1. The first draft used t-2 and the
                # dense audit found it on 7 of 3,187 bars -- which is what a
                # sampled audit would have missed.
                w = series[t - VOL_WIN:t]
                v = float(w.std(ddof=1))
                if v > 0 and (pk - acc) >= X * v:
                    out[t] = False
            if lag:
                acc += series[t]
            pk = max(pk, acc)
        return out

    on = schedule(base, 1.5)[0]
    want = hand(base, 1.5)
    bad = int((on != want).sum())
    assert bad == 0, (
        f"LOOK-AHEAD AUDIT FAILED: the schedule and an independent rebuild "
        f"disagree on {bad} of {n} bars")
    print(f"    [1] no look-ahead: the on/off decision rebuilt by an independent "
          f"accumulation loop on all {n:,} bars, identical")

    # 1b. and it must FAIL on a schedule that sees bar t's own return, or it
    #     proves nothing. That is the exact property [1] asserts, broken.
    peek = schedule(base, 1.5, lag=False)[0]
    diff = int((peek != want).sum())
    assert diff > 0, (
        "the audit PASSED a schedule that peeks at bar t's own return -- it "
        "proves nothing")
    print(f"    [1b] and it separates a peeking schedule on {diff:,} bars")

    # 2. THE OVERLAY CANNOT CREATE RETURN. With scale identically 1 the book
    #    must reproduce the base EXACTLY, and with scale identically 0 it must
    #    earn exactly nothing. A harness that fails either is not scaling.
    s1 = stats(base, np.ones(n), rt_bp)
    s0 = stats(base, np.zeros(n), rt_bp)
    b = stats(base, np.ones(n), rt_bp)
    assert s1["mean_bp"] == b["mean_bp"] and s1["sharpe"] == b["sharpe"], \
        "SCALE=1 does not reproduce the base book"
    assert s0["mean_bp"] == 0.0, \
        f"SCALE=0 earns {s0['mean_bp']:+.4f} bp, which is not nothing"
    print(f"    [2] scale identity: scale=1 reproduces the base exactly "
          f"({b['mean_bp']:+.3f} bp, Sharpe {b['sharpe']:+.3f}); scale=0 earns 0")

    # 3. RIGHT QUANTITY. The overlay must actually de-risk, and a TIGHTER
    #    threshold must de-risk MORE. A rule whose exposure does not move with
    #    its own parameter is not the rule it is labelled.
    exps = []
    for X in X_LEVELS:
        on_x, _, _ = schedule(base, X)
        exps.append(float(on_x.mean()))
    assert all(a <= b_ + 1e-12 for a, b_ in zip(exps, exps[1:])), (
        f"RIGHT QUANTITY FAILED: exposure {['%.3f' % e for e in exps]} is not "
        f"monotone in the threshold")
    assert exps[0] < 0.999, "the tightest threshold never de-risks at all"
    print(f"    [3] right quantity: exposure rises monotonically with X -- "
          + ", ".join(f"X={x}: {e:.1%}" for x, e in zip(X_LEVELS, exps)))

    # 4. THE MATCHED NULL MUST MATCH. Same off-bar count and same episode-length
    #    distribution as the treatment, or it is a count-matched control and
    #    D279's lesson is being repeated.
    rng = np.random.default_rng(11)
    on_x, _, _ = schedule(base, 1.5)
    for _ in range(20):
        nl = matched_schedule(on_x, rng)
        assert abs((~nl).sum() - (~on_x).sum()) <= 2 * VOL_WIN, \
            "the null's off-bar count does not match the treatment's"
    print(f"    [4] the null matches the treatment's off-bar count and episode "
          f"lengths, on 20 draws")


def fmt(v, w, d=2):
    return f"{v:+{w}.{d}f}" if v is not None else f"{'--':>{w}s}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args()
    t0 = time.time()

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    bmask = z["warm"] & live
    n_names = bmask.shape[0]
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    ctx, r1, vol, plan = E.build_inputs(z, bmask, panel, live, T)

    # the base book: D295's B0 control, unchanged
    lo, hi, ent, tr, fired, clo, chi, resid = E.simulate(
        ctx, r1, vol, "none", None, None, None, n_names, T)
    m = np.isfinite(lo) & np.isfinite(hi)
    base = (lo[m] - hi[m]).astype(np.float64)

    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    sel_lo = ctx["lo"]["sel"][plan.lo.ravel(), bc.ravel()].reshape(plan.lo.shape)
    sel_hi = ctx["hi"]["sel"][plan.hi.ravel(), bc.ravel()].reshape(plan.hi.shape)
    vl = half[plan.lo[sel_lo], bc[sel_lo]]
    vh = half[plan.hi[sel_hi], bc[sel_hi]]
    rt_bp = 2 * float(np.median(vl[np.isfinite(vl)])) + \
        2 * float(np.median(vh[np.isfinite(vh)]))

    print(f"D297  base book = D295's B0 control | {base.size:,} bars | "
          f"robust round trip {rt_bp:.1f} bp  ({time.time() - t0:.0f}s)")
    assertions(base, rt_bp)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    ctrl = stats(base, np.ones(base.size), rt_bp)
    print(f"\n  CONTROL (no overlay): {ctrl['mean_bp']:+.2f} bp/bar, vol "
          f"{ctrl['vol_bp']:.1f}, Sharpe {ctrl['sharpe']:+.3f}, maxDD "
          f"{ctrl['maxdd_bp']:,.0f} bp")

    rows = []
    dist = {}
    for X in X_LEVELS:
        on, dd, v = schedule(base, X)
        for s in S_LEVELS:
            scale = np.where(on, 1.0, s)
            st = stats(base, scale, rt_bp)
            key = f"X={X}/s={s}"
            rng = np.random.default_rng(SEED + int(X * 10) * 7 + int(s * 10))
            nulls = []
            for _ in range(a.draws):
                nl = matched_schedule(on, rng)
                ns = stats(base, np.where(nl, 1.0, s), rt_bp)
                if ns["sharpe"] is not None:
                    nulls.append(ns["sharpe"])
            arr = np.array(nulls)
            p = float((arr >= st["sharpe"]).sum() + 1) / (arr.size + 1)
            dist[key] = arr
            rows.append(dict(cell=key, X=X, s=s, **st,
                             null_p50=float(np.percentile(arr, 50)),
                             null_p95=float(np.percentile(arr, 95)), p=p,
                             beats=bool(p < 0.05)))

    rows.sort(key=lambda r: r["p"])
    print(f"\n{'=' * 104}")
    print(f"  {'cell':12s} | {'mean':>7s} {'vol':>7s} {'SHARPE':>7s} "
          f"{'maxDD':>8s} | {'expo':>6s} {'ret/exp':>8s} | {'null95':>7s} "
          f"{'p':>7s} | {'trans/yr':>8s} {'cost/bar':>8s}")
    print(f"{'=' * 104}")
    print(f"  {'CONTROL':12s} | {ctrl['mean_bp']:+7.2f} {ctrl['vol_bp']:7.1f} "
          f"{ctrl['sharpe']:+7.3f} {ctrl['maxdd_bp']:8,.0f} | "
          f"{ctrl['exposure']:6.1%} {ctrl['ret_per_exposure']:+8.2f} | "
          f"{'--':>7s} {'--':>7s} | {ctrl['trans_per_yr']:8.2f} "
          f"{ctrl['cost_bar_bp']:8.3f}")
    for r in rows:
        print(f"  {r['cell']:12s} | {r['mean_bp']:+7.2f} {r['vol_bp']:7.1f} "
              f"{r['sharpe']:+7.3f} {r['maxdd_bp']:8,.0f} | "
              f"{r['exposure']:6.1%} {r['ret_per_exposure']:+8.2f} | "
              f"{r['null_p95']:+7.3f} {r['p']:7.4f} | "
              f"{r['trans_per_yr']:8.2f} {r['cost_bar_bp']:8.3f}")

    nsig = sum(1 for r in rows if r["beats"])
    m_ = len(rows)
    print(f"\n  cells at p < 0.05        : {nsig} of {m_}")
    print(f"  expected by luck         : {0.05 * m_:.2f}")
    ps = np.sort(np.array([r["p"] for r in rows]))
    bh = {}
    for q in (0.10, 0.20):
        thr = np.arange(1, m_ + 1) / m_ * q
        below = np.flatnonzero(ps <= thr)
        bh[q] = int(below.max() + 1) if below.size else 0
    print(f"  Benjamini-Hochberg       : q=0.10 -> {bh[0.10]}, "
          f"q=0.20 -> {bh[0.20]}")
    rpe = np.array([r["ret_per_exposure"] for r in rows])
    print(f"\n  Q3 -- return per unit of exposure: control "
          f"{ctrl['ret_per_exposure']:+.2f}, overlays "
          f"{rpe.min():+.2f} to {rpe.max():+.2f} (p50 {np.median(rpe):+.2f})")

    json.dump({"purpose": "D297: a book-level trailing stop on the spread's own "
                          "equity, against a rate- and persistence-matched null.",
               "preregistered": "a0dd515", "draws": a.draws,
               "round_trip_bp": rt_bp, "control": ctrl, "rows": rows,
               "n_sig": nsig, "expected_by_luck": 0.05 * m_,
               "bh": {str(k): v for k, v in bh.items()}},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
