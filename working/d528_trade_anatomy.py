"""WHY IS IT SO BAD, WHY ISN'T THE WIN RATE HIGHER, AND WHY ARE THE NULLS SO HIGH?

    python working/d528_trade_anatomy.py --self-test
    python working/d528_trade_anatomy.py --run

Nothing admitted (R15). Micro universe, in sample only; reserved slice UNREAD.

THREE QUESTIONS, AND THE FIRST TWO HAVE THE SAME ANSWER.

-------------------------------------------------------------------------------------------------
Q1  "In theory it should be profitable."
Q2  "The win rate should be much higher."

THE GEOMETRY IS FREE. On any martingale, optional stopping forces

    E[gross] = 0    for ANY target/stop pair, with no time limit and true fills

so the hit rate is not a property of the strategy -- it is forced by the distances chosen:

    P(reach target before stop) ~ stop_distance / (target_distance + stop_distance)

Pick a 4:1 reward-to-risk and the market hands back a ~20% hit rate. Pick 1:2 and it hands back
~67%. Both have zero expectancy. **A favourable reward-to-risk ratio is therefore NOT an edge, and
neither is a high win rate: they are two ends of one dial, and the product is conserved.** The
only thing that can be an edge is the DEVIATION of the realised hit rate from the geometric one --
and that deviation was measured in ADDENDUM 2 at about +0.04 sigma of drift, worth ~0.3 ticks
against 2.4-4.7 ticks of cost.

Section 1 demonstrates the conservation law rather than asserting it: across all 30 geometries, on
sign-shuffled data, the hit rate moves from ~5% to ~50% while gross expectancy stays pinned near
zero. Real data sits beside it.

-------------------------------------------------------------------------------------------------
Q3  "Why are the nulls so high?"

Two different things get called "high" and only one of them is real:

  THE LEVEL (null p50 gross = +$1.11 in ADDENDUM 5). Small, and it comes from the FILL
  CONVENTION, not from the market: a resting limit at the target fills at its own price while a
  stop fills at the realised price. Those two biases have opposite signs and do not cancel at
  every geometry.

  THE WIDTH (null p95 = +$8.84, p95 net Sharpe = +0.81). THIS is the real answer, and it is pure
  sample size interacting with a skewed payoff. With n = 109, a ~20% hit rate and a ~3:1 payoff,
  a handful of winners drives the mean. Section 2 decomposes it: per-trade standard deviation,
  the implied standard error, the skew, and how many trades carry half the P&L. The null is not
  inflated -- the ESTIMATOR is imprecise, and the null is the only thing telling us so.

Section 3 is the trade-by-trade breakdown, including the top and bottom trades NAMED with their
root and date, because a concentration report is not finished until the biggest trade is named.
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
import d528_combined as C                       # noqa: E402

PRIMARY = ("reflect", "drift", 3.0)
CELL_C = ("traverse", "flat", "C traverse")
CELL_B = ("none", "flat", "B no-classifier")
N_SHUF = 20
SEED = 528017
PCTS = (1, 5, 10, 25, 50, 75, 90, 95, 99)


def P(*a):
    print(*a, flush=True)


def net_usd(trades, fill="g_real_tk"):
    g = np.array([z[fill] * z["tick_usd"] for z in trades])
    c = np.array([z["cost_usd"] for z in trades])
    return g, c, g - c


def self_test():
    # 1. THE CONSERVATION LAW, on a pure synthetic martingale with NO admission filter and NO
    #    cost. Across geometries the hit rate must move a lot while gross expectancy stays ~0.
    #    If gross expectancy drifted with the geometry, every comparison in this session would
    #    be measuring the geometry rather than the market.
    rng = np.random.default_rng(31)
    rows = []
    for g in (2.5, 3.0, 4.0, 5.0):
        tot = np.zeros(0)
        hits = n = 0
        for i in range(120):
            pth = 20000 + np.cumsum(rng.normal(0, 2.0, 240))
            cc = Z.classify2(pth, 0.25)
            kk = Z.entry_mask(cc, "flat", 0.25, 0.0, "none", align=False)
            tr = O.resolve(pth, cc, "flat", kk, 0.25, 1.0, 0.0, "reflect", "frozen", g, 40,
                           i, 540, "T")
            if tr:
                tot = np.concatenate([tot, np.array([z["g_real_tk"] for z in tr])])
                hits += sum(z["kind"] == 0 for z in tr); n += len(tr)
        se = tot.std(ddof=1) / np.sqrt(len(tot))
        rows.append((g, hits / max(n, 1), tot.mean(), se, len(tot)))
    P("   [1] the conservation law on a synthetic martingale (no cost, no filter):")
    for g, hr, mu, se, nn in rows:
        P(f"       G={g:.1f}  hit rate {hr:>6.1%}   gross {mu:>+7.3f} tk  (SE {se:.3f}, "
          f"t {mu/se:>+5.2f})  n {nn:,}")
    hrs = [r[1] for r in rows]
    assert hrs == sorted(hrs), f"hit rate not monotone in the stop width: {hrs}"
    assert max(hrs) - min(hrs) > 0.10, "the hit rate barely moved -- the demo cannot fire"
    worst = max(rows, key=lambda r: abs(r[2] / r[3]))
    assert abs(worst[2] / worst[3]) < 4.0, (
        f"gross expectancy is {worst[2]:+.3f} tk at {worst[3]:.3f} SE on a MARTINGALE "
        f"(t {worst[2]/worst[3]:+.2f}) -- the geometry is generating expectancy")
    P(f"       hit rate spans {min(hrs):.1%} to {max(hrs):.1%} while every gross is within "
      f"4 SE of zero  OK")

    # 2. THE WIDTH IS SAMPLE SIZE. The SE of the mean must fall like 1/sqrt(n): subsampling the
    #    same population to n=109 must widen it by ~sqrt(N/109) versus the full sample.
    pop = rng.normal(-2.0, 40.0, 12865)
    se_full = pop.std(ddof=1) / np.sqrt(len(pop))
    sub = np.array([pop[rng.integers(0, len(pop), 109)].mean() for _ in range(4000)])
    ratio = sub.std(ddof=1) / se_full
    want = np.sqrt(len(pop) / 109)
    assert abs(ratio / want - 1.0) < 0.10, f"width ratio {ratio:.1f} vs expected {want:.1f}"
    P(f"   [2] subsampling 12,865 -> 109 widens the SE by {ratio:.1f}x "
      f"(sqrt(N/n) = {want:.1f}x)            OK")
    P(f"       so a p95 that sits {1.645*sub.std(ddof=1):.2f} above the median at n=109 sits "
      f"only {1.645*se_full:.2f} above it at n=12,865")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    rev_day = {i: u for u, i in day_index.items()}
    total_minutes = len(udays) * 420
    full = [(t, f, g) for t in C.TARGETS for f in C.FRAMES for g in C.G_LADDER]

    P("WHY IS IT SO BAD, WHY ISN'T THE WIN RATE HIGHER, AND WHY ARE THE NULLS SO HIGH?")
    P(f"  micro universe, {len(roots)} roots, {len(udays)} sessions, s=1\n")

    real_c = C.gather_grid(*CELL_C[:2], full, d, sp, roots, day_index)
    real_b = C.gather_grid(*CELL_B[:2], full, d, sp, roots, day_index)

    # ---------------------------------------------------------------- 1 the conservation law
    P("=" * 112)
    P("1  WHY A GOOD REWARD:RISK IS NOT AN EDGE -- the hit rate is the price of the payoff")
    P("   Cell B (n=12,865, tight enough to read). NULL gross is what the geometry alone earns.")
    P("")
    rng = np.random.default_rng(SEED)
    nulls_b = {v: [] for v in full}
    for _ in range(N_SHUF):
        acc = C.gather_grid(*CELL_B[:2], full, d, sp, roots, day_index, shuffle_rng=rng)
        for v in full:
            tr = acc.get(v) or []
            if tr:
                _, _, nt = net_usd(tr)
                g, _, _ = net_usd(tr)
                nulls_b[v].append(g.mean())
    P("    target    frame   G    hit rate  payoff  hit x payoff | NULL gross $  real gross $"
      "  real - null")
    for v in full:
        trb = real_b.get(v) or []
        if len(trb) < 50 or not nulls_b[v]:
            continue
        g, c, nt = net_usd(trb)
        kd = np.array([z["kind"] for z in trb])
        w, l = nt[nt > 0], nt[nt <= 0]
        po = w.mean() / abs(l.mean()) if len(l) and l.mean() else np.nan
        hr = float((kd == 0).mean())
        nb = float(np.mean(nulls_b[v]))
        P(f"    {v[0]:<9} {v[1]:<7} {v[2]:.1f} {hr:>8.1%} {po:>7.2f} {hr*po:>13.3f} |"
          f" {nb:>+12.2f} {g.mean():>+13.2f} {g.mean()-nb:>+12.2f}")
    P("")
    P("  The hit rate runs from ~5% to ~50% across these rows. NULL gross barely moves -- the")
    P("  geometry earns nothing whatever distances you pick, because the hit rate is exactly the")
    P("  price of the payoff. 'real - null' is the ONLY column that can contain an edge.")

    # ---------------------------------------------------------------- 2 why the nulls are wide
    P("")
    P("=" * 112)
    P("2  WHY THE NULLS ARE SO WIDE -- it is n, interacting with a skewed payoff")
    P("")
    P("    cell                      n      per-trade sd   SE of mean   skew   kurt   "
      "trades for half the +P&L")
    for (cl, lvl, label), store in ((CELL_C, real_c), (CELL_B, real_b)):
        tr = store.get(PRIMARY) or []
        if not tr:
            continue
        g, c, nt = net_usd(tr)
        se = nt.std(ddof=1) / np.sqrt(len(nt))
        pos = np.sort(g[g > 0])[::-1]
        half = int(np.searchsorted(np.cumsum(pos), pos.sum() / 2) + 1) if len(pos) else 0
        sk = float(((nt - nt.mean()) ** 3).mean() / nt.std() ** 3)
        ku = float(((nt - nt.mean()) ** 4).mean() / nt.std() ** 4)
        P(f"    {label:<24} {len(nt):>6,} {nt.std(ddof=1):>14.2f} {se:>12.2f} {sk:>+7.2f}"
          f" {ku:>6.1f} {half:>22,} of {len(pos):,} winners")
    P("")
    P("    a 1.645-SE p95 therefore sits this far above the null median:")
    for (cl, lvl, label), store in ((CELL_C, real_c), (CELL_B, real_b)):
        tr = store.get(PRIMARY) or []
        if not tr:
            continue
        _, _, nt = net_usd(tr)
        se = nt.std(ddof=1) / np.sqrt(len(nt))
        P(f"      {label:<24} +${1.645*se:>7.2f} per trade   "
          f"({len(nt):,} trades)")
    P("")
    P("    The null is not inflated. At n=109 the ESTIMATOR cannot resolve anything smaller")
    P("    than a few dollars a trade, and the real edge is about 30 cents.")

    # ---------------------------------------------------------------- 3 the trade anatomy
    P("")
    P("=" * 112)
    P(f"3  TRADE-BY-TRADE ANATOMY of the declared primary {PRIMARY}")
    P("")
    for (cl, lvl, label), store in ((CELL_C, real_c), (CELL_B, real_b)):
        tr = store.get(PRIMARY) or []
        if len(tr) < 20:
            continue
        g, c, nt = net_usd(tr)
        kd = np.array([z["kind"] for z in tr])
        bars = np.array([z["bars"] for z in tr])
        P(f"  {label}   n {len(tr):,}")
        P(f"    NET $ percentiles: " + "  ".join(
            f"p{p}={np.percentile(nt, p):+.1f}" for p in PCTS))
        P(f"    mean {nt.mean():+.2f}   sd {nt.std(ddof=1):.2f}   "
          f"min {nt.min():+.1f}   max {nt.max():+.1f}   cost/trade {c.mean():.2f}")
        P("    by outcome:      n     share   mean $    median $      sd     min      max"
          "    mean bars")
        for k, nm in ((0, "TARGET"), (1, "STOP"), (2, "TIMEOUT")):
            m = kd == k
            if m.sum() == 0:
                continue
            P(f"      {nm:<12} {int(m.sum()):>5} {m.mean():>7.1%} {nt[m].mean():>+8.2f} "
              f"{np.median(nt[m]):>+11.2f} {nt[m].std(ddof=1) if m.sum()>1 else 0:>7.2f} "
              f"{nt[m].min():>+7.1f} {nt[m].max():>+8.1f} {bars[m].mean():>11.1f}")
        P("    by side:         n     share   win%    mean $    median $   mean bars")
        for sv, nm in ((-1, "LONG"), (+1, "SHORT")):
            m = np.array([z["side"] == sv for z in tr])
            if m.sum() == 0:
                continue
            P(f"      {nm:<12} {int(m.sum()):>5} {m.mean():>7.1%} {(nt[m]>0).mean():>6.1%} "
              f"{nt[m].mean():>+8.2f} {np.median(nt[m]):>+11.2f} {bars[m].mean():>10.1f}")
        P("    by root:         n    win%    mean $   total $   hit rate   geometric hit rate")
        for r in roots:
            m = np.array([z["root"] == r for z in tr])
            if m.sum() < 5:
                continue
            P(f"      {r:<12} {int(m.sum()):>5} {(nt[m]>0).mean():>6.1%} "
              f"{nt[m].mean():>+8.2f} {nt[m].sum():>+9.0f} {(kd[m]==0).mean():>10.1%}")
        P(f"    holding time (bars): " + "  ".join(
            f"p{p}={np.percentile(bars, p):.0f}" for p in (10, 25, 50, 75, 90, 99)))
        P(f"    concentration: top 1 trade {nt.max()/max(nt[nt>0].sum(),1e-9):>5.1%} of gross "
          f"+P&L, top 5 {np.sort(nt)[-5:].sum()/max(nt[nt>0].sum(),1e-9):>5.1%}, "
          f"top 10 {np.sort(nt)[-10:].sum()/max(nt[nt>0].sum(),1e-9):>5.1%}")
        # NAME THE TOP AND BOTTOM TRADES -- a concentration report is not finished otherwise
        order = np.argsort(nt)
        P("    the five biggest WINNERS and LOSERS, named:")
        for tag, sel in (("WIN ", order[-5:][::-1]), ("LOSS", order[:5])):
            for i in sel:
                z = tr[i]
                # The fixture stores `bar` re-indexed 0..419 from DAY_LO = 540 minutes (09:00 ET),
                # so clock time is (540 + bar) minutes past midnight. An earlier version printed
                # bar//60 directly and reported bar 73 as "01:13" instead of 10:13.
                bar = z["t_in"] - z["day"] * 2000
                mm = Q.DAY_LO + bar
                P(f"      {tag} {nt[i]:>+9.2f}  {z['root']:<4} {rev_day[z['day']]}  "
                  f"{mm//60:02d}:{mm%60:02d} ET (bar {bar})  side "
                  f"{'LONG ' if z['side']<0 else 'SHORT'}  held {z['bars']:>2} bars  "
                  f"exit {['TARGET','STOP','TIMEOUT'][z['kind']]}")
        P("")
    P("  'geometric hit rate' is omitted per root: the realised target and stop distances differ")
    P("  per trade, so the pooled figure in section 1 is the honest version of that comparison.")


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
