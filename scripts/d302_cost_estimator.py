"""D302 -- why the two cost estimates disagree by 2.4x. A diagnostic, not a study.

    uv run python scripts/d302_cost_estimator.py

NOTHING HERE SCORES A CELL AND NOTHING IS PROMOTED. The programme has carried
two round-trip figures for the same book -- 260.7 bp from the mean half-spread
and 105.4 from the median -- and that 2.5x straddles R14's factor-of-two clause,
so it blocks D293's candidate, D297, D298 and anything after them. This file asks
where the gap comes from using data already processed.

FOUR QUESTIONS, declared before the numbers are read:

 1. THE CLAMP. Corwin-Schultz sets negative daily estimates to zero -- the
    authors' convention, correct for a single day, and a LEFT TRUNCATION of a
    noisy estimator. Truncating the left tail biases the MEAN UP. The estimator
    is unbiased only in the mean of the UNCLAMPED values, so the unclamped mean
    is the quantity the theory actually licenses. How far apart are they?

 2. THE TAIL. A mean 2.4x its own median is a skewed distribution. Is the mean
    carried by a small tail, and by how much -- the same question the reporting
    standard asks of a P&L mean.

 3. THE SELECTION. D299 found held names WIDER than the universe (62.3 vs 39.8
    bp). If the book systematically selects illiquid or low-priced names then
    cost is a tilt in disguise, which is exactly what killed D284. Held vs
    universe on price, dollar volume and Amihud.

 4. THE ZERO MASS. Are the ~42% of zero estimates spread evenly across names, or
    concentrated in a subset whose spread CS simply cannot measure? Those are
    different problems: noise averages out, a structural subset does not.

The selected set is used as the held set. At 19 slots and 19 selected they are
the same thing on this book -- D298 measured the difference at 0.00%.
"""

from __future__ import annotations

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
OUT = REPO / "data" / "d302_cost_estimator.json"
SQ2 = SP.SQ2


def cs(H, L, live, clamp):
    """Corwin-Schultz, with the negative-clamp as an argument.

    `clamp=True` is `d285_spread_estimate.corwin_schultz` exactly; assertion [1]
    holds it to that bit-identically so the unclamped arm differs in one thing.
    """
    ok = (live[:, :-1] & live[:, 1:] & np.isfinite(H[:, :-1])
          & np.isfinite(H[:, 1:]) & (L[:, :-1] > 0) & (L[:, 1:] > 0))
    h1, l1, h2, l2 = H[:, :-1], L[:, :-1], H[:, 1:], L[:, 1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        b = np.log(h1 / l1) ** 2 + np.log(h2 / l2) ** 2
        g = np.log(np.maximum(h1, h2) / np.minimum(l1, l2)) ** 2
        a = (np.sqrt(2.0 * b) - np.sqrt(b)) / SQ2 - np.sqrt(g / SQ2)
        s = 2.0 * np.expm1(a) / (1.0 + np.exp(a))
    s = np.where(ok & np.isfinite(s), s, np.nan)
    if clamp:
        s = np.where(np.isfinite(s), np.maximum(s, 0.0), np.nan)
    out = np.full(H.shape, np.nan)
    out[:, :-1] = s
    return out


def desc(v):
    v = v[np.isfinite(v)]
    q = np.quantile(v, [.05, .25, .50, .75, .90, .95, .99])
    top1 = np.sort(v)[-max(1, v.size // 100):]
    return dict(n=int(v.size), mean=float(v.mean()), sd=float(v.std()),
                p05=float(q[0]), p25=float(q[1]), p50=float(q[2]),
                p75=float(q[3]), p90=float(q[4]), p95=float(q[5]),
                p99=float(q[6]), max=float(v.max()), min=float(v.min()),
                zero_share=float((v == 0).mean()),
                neg_share=float((v < 0).mean()),
                top1_share_of_mean=float(top1.sum() / v.sum()) if v.sum() else None,
                mean_ex_top1=float(np.sort(v)[:-max(1, v.size // 100)].mean()))


def main() -> int:
    t0 = time.time()
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    n = base.shape[0]
    g = M.P1.build_grids(panel, cleaned)
    ctx, r1, vol, plan = E.build_inputs(z, base, panel, live, T)
    held = ctx["lo"]["sel"] | ctx["hi"]["sel"]
    uni = base & np.isfinite(r1)
    print(f"  loaded, {int(held.sum()):,} held name-bars, "
          f"{int(uni.sum()):,} universe ({time.time() - t0:.0f}s)")

    clamped = cs(g["high"], g["low"], live, True) / 2.0 * 1e4
    raw = cs(g["high"], g["low"], live, False) / 2.0 * 1e4

    ref = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    a, b = np.nan_to_num(clamped, nan=-9e9), np.nan_to_num(ref, nan=-9e9)
    assert np.array_equal(a, b), "the clamped arm is not d285's estimator"
    print(f"    [1] the clamped arm is bit-identical to d285.corwin_schultz")

    res = {}
    print("\n1. THE CLAMP -- what the authors' convention costs in the MEAN")
    print(f"  {'':22s} {'n':>9s} {'mean':>8s} {'median':>8s} {'zero%':>7s} "
          f"{'neg%':>7s} {'x4 = round trip':>17s}")
    for tag, arr, msk in (("held, CLAMPED", clamped, held),
                          ("held, UNCLAMPED", raw, held),
                          ("universe, CLAMPED", clamped, uni),
                          ("universe, UNCLAMPED", raw, uni)):
        d = desc(arr[msk])
        res[tag] = d
        print(f"  {tag:22s} {d['n']:>9,} {d['mean']:>8.2f} {d['p50']:>8.2f} "
              f"{100 * d['zero_share']:>6.1f}% {100 * d['neg_share']:>6.1f}% "
              f"{4 * d['mean']:>13.1f} bp")
    hc, hu = res["held, CLAMPED"], res["held, UNCLAMPED"]
    print(f"\n  the clamp lifts the held mean by "
          f"{hc['mean'] / hu['mean']:.2f}x  "
          f"({hu['mean']:.2f} -> {hc['mean']:.2f} bp per side)")

    print("\n2. THE TAIL -- is the mean carried by a few name-bars?")
    for tag in ("held, CLAMPED", "held, UNCLAMPED"):
        d = res[tag]
        print(f"  {tag:22s} p50 {d['p50']:6.2f}  p90 {d['p90']:7.2f}  "
              f"p99 {d['p99']:8.2f}  max {d['max']:9.1f}   "
              f"top 1% = {100 * d['top1_share_of_mean']:.1f}% of the sum, "
              f"mean ex-top-1% {d['mean_ex_top1']:.2f}")

    print("\n3. THE SELECTION -- is the book tilted to illiquid or cheap names?")
    px = np.asarray(g["close"], dtype=np.float64)
    tilt = {}
    for nm, arr in (("price", px), ("price_log", z["price_log"]),
                    ("dollar_vol", z["dollar_vol"]), ("amihud_21", z["amihud_21"]),
                    ("cs_spread", z["cs_spread"]),
                    ("half_spread_bp", clamped)):
        a_ = np.asarray(arr, dtype=np.float64)
        h = a_[held & np.isfinite(a_)]
        u = a_[uni & np.isfinite(a_)]
        if h.size < 100 or u.size < 100:
            continue
        tilt[nm] = dict(held_mean=float(h.mean()), held_med=float(np.median(h)),
                        uni_mean=float(u.mean()), uni_med=float(np.median(u)),
                        ratio_med=float(np.median(h) / np.median(u))
                        if np.median(u) != 0 else None)
        print(f"  {nm:16s} held med {np.median(h):12.3f}   universe med "
              f"{np.median(u):12.3f}   ratio {tilt[nm]['ratio_med'] or float('nan'):6.2f}")
    res["tilt"] = tilt

    print("\n4. THE ZERO MASS -- noise, or a structural subset?")
    zc = np.where(held & np.isfinite(clamped), clamped == 0, False).sum(axis=1)
    hb = np.where(held & np.isfinite(clamped), True, False).sum(axis=1)
    ok = hb >= 50
    rate = zc[ok] / hb[ok]
    print(f"  {int(ok.sum())} names with >=50 held bars; per-name zero rate: "
          f"p10 {np.quantile(rate, .1):.2f}  p50 {np.median(rate):.2f}  "
          f"p90 {np.quantile(rate, .9):.2f}")
    # if zeros were i.i.d. noise at the pooled rate, the per-name rate would be
    # binomial around it -- a much tighter spread than this
    p = float(zc[ok].sum() / hb[ok].sum())
    exp_sd = float(np.mean(np.sqrt(p * (1 - p) / hb[ok])))
    print(f"  pooled rate {p:.3f}; observed per-name sd {rate.std():.3f} vs "
          f"{exp_sd:.3f} expected if the zeros were i.i.d. noise "
          f"-- {rate.std() / exp_sd:.1f}x")
    res["zero_mass"] = dict(names=int(ok.sum()), pooled=p,
                            sd_observed=float(rate.std()), sd_iid=exp_sd,
                            ratio=float(rate.std() / exp_sd))

    print("\n5. WHAT THE BOOK IS ACTUALLY CHARGED (turnover 0.200 at k=5)")
    turn = 0.200
    for tag in ("held, CLAMPED", "held, UNCLAMPED"):
        d = res[tag]
        print(f"  {tag:22s} round trip {4 * d['mean']:7.1f} bp  ->  "
              f"cost/bar {4 * d['mean'] * turn:6.2f} bp   "
              f"(median-based: {4 * d['p50'] * turn:5.2f})")
    print(f"  the incumbent book's GROSS is +7.54 bp/bar (B0) to "
          f"+12.49 (B6 target)")

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
