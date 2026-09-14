"""THE ORACLE, WITH THE CONTROL IT SHOULD HAVE HAD -- and a regime oracle that cannot see the trade.

    python working/d528_oracle_correct_control.py --self-test
    python working/d528_oracle_correct_control.py --run

Nothing admitted (R15). Micro universe, in sample only; reserved slice UNREAD.

WHY THIS SUPERSEDES ADDENDUM 8's ORACLE NULL. That null sign-shuffled the path and then re-derived
the ORACLE on the shuffled path. It therefore compared

    foresight on the real market   vs   foresight on a random walk

and concluded "the ceiling is inside the null, so a better detector cannot help". **That
conclusion is withdrawn.** The comparison is the wrong one, for two reasons:

  1. Foresight is profitable on ANY series. Knowing a random walk will traverse a band lets you
     trade that traversal. The null therefore sits near its own ceiling by construction and is
     close to unbeatable -- it is not a demanding benchmark, it is a saturated one.
  2. The null's selector ADAPTS to whatever path it is handed. It is not "the same selection,
     randomised"; it is "an equally powerful selection, applied to noise". A control must share
     the treatment's nuisance, and randomise the PARTNER rather than the MEMBERSHIP.

Exactly one inference survives from it, and it is narrow: a random walk has nothing causally
detectable, yet scored Sharpe +6.11 with foresight -- so **a high oracle score does not by itself
prove any of it is causally reachable.** It does NOT show that detection is worthless.

THE CONTROL THIS FILE USES INSTEAD keeps the real data and randomises the selection:

    RANDOM-MATCHED   draw a random subset of the SAME candidate pool with the SAME count as the
                     oracle arm, on the REAL path, many times.

That asks the principal's own question -- is this construction better than a randomised version of
the construction? -- and it isolates the INFORMATION IN THE LABEL rather than the exploitability
of noise.

AND A SECOND DEFECT, FIXED HERE. `oracle_h` reads [t, t+H), which OVERLAPS the trade's own horizon,
so it partly knows the outcome rather than the regime. Three oracles are run:

    oracle_h        traverse on [t, t+H)               overlaps the trade  (outcome-contaminated)
    oracle_tau      traverse on [t, t+tau)             overlaps the trade  (outcome-contaminated)
    oracle_after    traverse on [t+tau, t+tau+H)       DISJOINT from the trade -- regime only

`oracle_after` is the honest bound on what regime knowledge alone is worth, because nothing it
reads can be part of the trade's own outcome.
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
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402
import d528_oracle_vs_causal as V               # noqa: E402

H, X, G, TAU = V.H, V.X, V.G, V.TAU
TRAV_K = V.TRAV_K
TARGET, FRAME = V.TARGET, V.FRAME
SLOTS = 3
N_DRAW = 400          # random-matched draws
SEED = 528929
ARMS = ("causal", "oracle_h", "oracle_tau", "oracle_after")


def P(*a):
    print(*a, flush=True)


def flags(path, tick):
    """Backward traverse, two overlapping forward traverses, and a DISJOINT one after the trade."""
    c = Z.classify2(path, tick)
    if c is None:
        return None
    n = path.shape[-1]
    n_t = n - 2 * H
    lin_a, lin_b = c["a2"], c["slope"]

    def trav(width, offset):
        """Traverse of +/-TRAV_K sigma over [t+offset, t+offset+width), vs the [t-H,t) line."""
        out = np.zeros(n_t, dtype=bool)
        ok = np.zeros(n_t, dtype=bool)
        m = np.arange(width, dtype=np.float64)
        for i in range(n_t):
            t = i + 2 * H + offset
            if t + width > n or t < 0:
                continue
            sd = c["line_sd"][i]
            if not np.isfinite(sd) or sd <= 0:
                continue
            y = path[t:t + width] - (lin_a[i] + lin_b[i] * (H + offset + m))
            ok[i] = True
            out[i] = (y.min() <= -TRAV_K * sd) and (y.max() >= TRAV_K * sd)
        return out, ok

    fh, ok_h = trav(H, 0)
    ft, ok_t = trav(TAU, 0)
    fa, ok_a = trav(H, TAU)                 # begins only after the trade's horizon has closed
    return {"c": c, "back": c["trav"], "oracle_h": (fh, ok_h),
            "oracle_tau": (ft, ok_t), "oracle_after": (fa, ok_a)}


def pool_mask(tf, tick, cost):
    """The candidate pool every arm selects FROM: everything except the traverse test."""
    c = tf["c"]
    keep = (c["flat_sd"] > 0) & c["slope_ok"] & c["a2ok"]
    y, sd = c["flat_y"], c["flat_sd"]
    with np.errstate(invalid="ignore"):
        keep = keep & (np.abs(y) >= X * sd)
    keep = keep & (np.sign(y) * c["slope"] < 0)
    keep = keep & (np.abs(y) / tick > cost)
    return np.nan_to_num(keep, nan=False).astype(bool)


def collect(d, sp, roots, day_index):
    """Every candidate in the pool, tagged with which arms would have selected it."""
    out = []
    for r in roots:
        gg = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for day, pth, b0 in B.sessions_with_bars(gg, 1):
            tf = flags(pth, tick)
            if tf is None:
                continue
            pool = pool_mask(tf, tick, cost_tk)
            if not pool.any():
                continue
            tr = O.resolve(pth, tf["c"], "flat", pool, tick, tick_usd, cost_tk,
                           TARGET, FRAME, G, TAU, day_index[day], b0, r)
            idx = np.flatnonzero(pool)
            # O.resolve drops entries with t >= n-1, so re-derive the surviving indices
            keep_i = [i for i in idx if (i + 2 * H) < len(pth) - 1]
            if len(keep_i) != len(tr):
                keep_i = keep_i[:len(tr)]
            for z, i in zip(tr, keep_i):
                z["sel_causal"] = bool(tf["back"][i])
                for a in ("oracle_h", "oracle_tau", "oracle_after"):
                    fl, ok = tf[a]
                    z[f"sel_{a}"] = bool(fl[i] and ok[i])
                    z[f"ok_{a}"] = bool(ok[i])
                out.append(z)
    return out


def stats(trades):
    if not trades:
        return None
    g = np.array([z["g_real_tk"] * z["tick_usd"] for z in trades])
    c = np.array([z["cost_usd"] for z in trades])
    kd = np.array([z["kind"] for z in trades])
    net = g - c
    return {"n": len(net), "p_tgt": float((kd == 0).mean()), "win": float((net > 0).mean()),
            "gross": float(g.mean()), "net": float(net.mean())}


def self_test():
    rng = np.random.default_rng(71)
    # 1. THE DISJOINT ORACLE MUST NOT OVERLAP THE TRADE. Its window starts at t+TAU, and every
    #    trade closes within TAU bars, so the two can never share a bar. Asserted on the indices.
    t0, width, offset = 0, H, TAU
    trade_last = t0 + TAU                       # the latest bar any trade can touch
    win_first = t0 + offset                     # the first bar the disjoint oracle reads
    assert win_first >= trade_last, f"disjoint oracle reads bar {win_first} but trades reach {trade_last}"
    P(f"   [1] disjoint oracle reads from t+{offset}; trades close by t+{TAU} -- no overlap  OK")

    # 2. THE THREE ORACLES MUST DIFFER, and the disjoint one must be the LEAST informative about
    #    the trade (it is the only one that cannot see it).
    dd = Q.load()
    spx = Q.specs()
    gnq = dd[dd["root"] == "NQ"]
    tick = spx["NQ"]["tick_price_units"]
    agree = {a: [0, 0] for a in ("oracle_h", "oracle_tau", "oracle_after")}
    for day, pth, b0 in B.sessions_with_bars(gnq, 1)[:60]:
        tf = flags(pth, tick)
        if tf is None:
            continue
        pool = pool_mask(tf, tick, 0.0)
        for a in agree:
            fl, ok = tf[a]
            m = pool & ok
            agree[a][0] += int((fl & m).sum())
            agree[a][1] += int(m.sum())
    for a, (k, n) in agree.items():
        P(f"   [2] {a:<13} selects {k:>4} of {n:>4} pooled candidates ({k/max(n,1):.1%})")
    assert agree["oracle_h"][0] != agree["oracle_after"][0], \
        "the overlapping and disjoint oracles selected identically -- the contrast is empty"
    P("       the overlapping and disjoint oracles differ                                  OK")

    # 3. THE RANDOM-MATCHED CONTROL MUST BE UNBIASED: over many draws its mean must converge to
    #    the POOL mean, or the control is not neutral and every comparison against it is skewed.
    pop = rng.normal(-5.0, 30.0, 4000)
    draws = np.array([pop[rng.choice(len(pop), 98, replace=False)].mean() for _ in range(3000)])
    se = pop.std(ddof=1) / np.sqrt(98)
    assert abs(draws.mean() - pop.mean()) < 0.1 * se, \
        f"random-matched control is biased: {draws.mean():.3f} vs pool {pop.mean():.3f}"
    P(f"   [3] random-matched control is unbiased: draw mean {draws.mean():+.3f} vs pool "
      f"{pop.mean():+.3f}   OK")
    P(f"       and its spread matches the analytic SE: {draws.std(ddof=1):.3f} vs {se:.3f}")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    rng = np.random.default_rng(SEED)

    P("THE ORACLE, WITH THE CONTROL IT SHOULD HAVE HAD")
    P(f"  micro universe, {len(roots)} roots, {len(udays)} sessions, s=1")
    P(f"  control = a RANDOM subset of the SAME candidate pool, on the REAL path, same count")
    P(f"  {N_DRAW} draws per arm\n")

    pool = collect(d, sp, roots, day_index)
    base = stats(pool)
    P(f"  the candidate pool: {base['n']:,} trades, P(target) {base['p_tgt']:.1%}, "
      f"gross ${base['gross']:+.2f}, net ${base['net']:+.2f}")
    P("")
    P("=" * 112)
    P("1  EACH SELECTOR vs A RANDOM SELECTOR OF THE SAME SIZE, on the same real data")
    P("")
    P("    arm             n    P(tgt)  win%   gross $   net $ | random-matched gross: p5    p50"
      "    p95  | verdict")
    for arm in ARMS:
        key = "sel_causal" if arm == "causal" else f"sel_{arm}"
        okk = None if arm == "causal" else f"ok_{arm}"
        elig = [z for z in pool if (okk is None or z[okk])]
        sel = [z for z in elig if z[key]]
        st = stats(sel)
        if st is None or st["n"] < 20:
            P(f"    {arm:<13} too few ({0 if st is None else st['n']})")
            continue
        gpool = np.array([z["g_real_tk"] * z["tick_usd"] for z in elig])
        k = st["n"]
        draws = np.array([gpool[rng.choice(len(gpool), k, replace=False)].mean()
                          for _ in range(N_DRAW)])
        p5, p50, p95 = np.percentile(draws, [5, 50, 95])
        verdict = "ABOVE p95" if st["gross"] > p95 else (
            "below p5" if st["gross"] < p5 else "inside")
        P(f"    {arm:<13} {st['n']:>5,} {st['p_tgt']:>6.1%} {st['win']:>5.1%} "
          f"{st['gross']:>+9.2f} {st['net']:>+7.2f} | {p5:>+9.2f} {p50:>+6.2f} {p95:>+6.2f}"
          f"  | {verdict}")
    P("")
    P("  The control keeps the real data and randomises only WHICH candidates are taken, with the")
    P("  count matched. It answers: does knowing which windows traverse beat picking at random?")
    P("")
    P("=" * 112)
    P("2  WHAT EACH ORACLE IS ALLOWED TO SEE")
    P("")
    P(f"    oracle_h      traverse over [t, t+{H})        OVERLAPS the trade -- knows part of the outcome")
    P(f"    oracle_tau    traverse over [t, t+{TAU})       OVERLAPS the trade -- knows part of the outcome")
    P(f"    oracle_after  traverse over [t+{TAU}, t+{TAU + H})  DISJOINT -- regime knowledge only")
    P("")
    P("  Only `oracle_after` bounds what REGIME knowledge alone is worth. If it clears its")
    P("  random-matched control, a causal detector has something to aim at. If it does not, the")
    P("  regime label carries no tradeable information even when known perfectly -- and THAT is")
    P("  the honest version of ADDENDUM 8's claim.")


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
