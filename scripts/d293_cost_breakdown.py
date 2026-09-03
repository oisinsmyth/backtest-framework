"""D293 -- where the 266 bp round trip comes from, and whether it is avoidable.

    uv run python scripts/d293_cost_breakdown.py

The cost number is what closes this candidate under R14, so it gets the same
scrutiny the effect got. Both books are broken down side by side:

    hist_L alone                    N=25, k=5
    hist_L x mean-rank(macd_hist, rsi) at f=0.75

SEVEN CUTS.

 1. the arithmetic -- what 266.08 bp is actually made of
 2. the DISTRIBUTION of the half-spread on names held. A mean of 63.8 bp built
    from a median of 25 and a long tail is a universe problem; a mean built from
    a median of 60 is a strategy problem, and they have opposite fixes
 3. by PRICE, on the AS-TRADED price. Cost in bp scales inversely with price and
    that is what killed D284. The back-adjusted price is look-ahead -- DRYS
    closes at $79,615,200 in 2010 -- so `as_traded_factor` undoes it per bar
 4. by ERA. Spreads narrowed over the sample; a cost measured across 2011-2024
    and applied to today is the wrong number in a knowable direction
 5. by SPREAD TERCILE, REBUILDING THE BOOK INSIDE EACH. The decisive cut: if the
    edge survives in the tight tercile the cost problem is a universe choice, and
    if it does not the edge lives in names nobody can trade
 6. BREAKEVEN, both ways -- the half-spread at which the book pays, and the
    effect it would need at the spread it actually faces
 7. COST PER UNIT TIME, which is round trip x turnover. A cost ratio without
    turnover is unreadable (gate 1g, and what made price_log look solvent)
"""

from __future__ import annotations

import importlib.util
import json
import sys
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


D = _load("d292", "run_d292_third_order.py")
SP = _load("d285sp", "d285_spread_estimate.py")
AN = _load("anom", "ragged_anomaly_scores.py")
R, M = D.R, D.M
OUT = REPO / "data" / "d293_cost_breakdown.json"
PAIR = ("macd_hist", "rsi")
FRAC = 0.75


def own(s):
    m = (s[1] > 0) & (s[3] > 0)
    if int(m.sum()) < M.MIN_BARS:
        return None
    d = s[0][m] / s[1][m] - s[2][m] / s[3][m]
    sd = d.std(ddof=1)
    return dict(bp=float(d.mean() * 1e4),
                t=float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else None,
                bars=int(d.size))


def legs(plan, klo, khi):
    """(rows, cols) of held cells per leg -- membership, which is what you pay on."""
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    return ((plan.lo[klo], bc[klo]), (plan.hi[khi], bc[khi]))


def main() -> int:
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    _, peaks = R.pool_and_peaks()
    N, k = peaks[D.PRIMARY]
    fwd = M.forward_returns(panel, live)[k]
    g = M.P1.build_grids(panel, cleaned)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4   # bp per side
    px = g["close"] * AN.as_traded_factor(panel, M.B.EVENTS)          # AS TRADED
    yrs = np.array([int(str(d)[:4]) for d in panel.dates])

    order_a, cnt_a, _ = R.ranked(z[D.PRIMARY], base)
    plan = R.LegPlan(order_a, cnt_a, N, T)
    pct = {}
    for b in PAIR:
        _, cb, pb = R.ranked(z[b], base)
        pct[b] = (R.pct_at(pb, cb, plan.lo, plan.cols),
                  R.pct_at(pb, cb, plan.hi, plan.cols))
    klo_c, khi_c = D.op_meanrank(pct[PAIR[0]][0], pct[PAIR[0]][1],
                                 pct[PAIR[1]][0], pct[PAIR[1]][1], FRAC, N)
    ones_lo = np.ones(plan.lo.shape, bool)
    ones_hi = np.ones(plan.hi.shape, bool)
    BOOKS = {"hist_L alone": (ones_lo, ones_hi),
             "confluence": (klo_c, khi_c)}

    def cost_of(klo, khi):
        (lr, lc), (hr, hc) = legs(plan, klo, khi)
        out = {}
        for nm, (r, c) in (("long", (lr, lc)), ("short", (hr, hc))):
            v = half[r, c]
            v = v[np.isfinite(v)]
            out[nm] = v
        return out

    print("=" * 78)
    print("  1. THE ARITHMETIC")
    print("=" * 78)
    res = {}
    for nm, (klo, khi) in BOOKS.items():
        s = own(R.spread_sums(fwd, plan, klo, khi, T))
        c = cost_of(klo, khi)
        lo_m, hi_m = float(c["long"].mean()), float(c["short"].mean())
        rt = 2 * lo_m + 2 * hi_m
        res[nm] = dict(bp=s["bp"], t=s["t"], long_half=lo_m, short_half=hi_m,
                       round_trip=rt, x_bar=s["bp"] / rt)
        print(f"\n  {nm}")
        print(f"    gross effect per entry, k={k}        {s['bp']:+8.2f} bp "
              f"(t {s['t']:+.2f})")
        print(f"    long leg  half-spread, per side      {lo_m:8.2f} bp")
        print(f"    short leg half-spread, per side      {hi_m:8.2f} bp")
        print(f"    round trip = 2*long + 2*short        {rt:8.2f} bp")
        print(f"    NET per entry                        "
              f"{s['bp'] - rt:+8.2f} bp")
        print(f"    covers                               {s['bp'] / rt:8.3f}x "
              f"of its cost")

    print("\n" + "=" * 78)
    print("  2. THE DISTRIBUTION -- is the mean built from a tail?")
    print("=" * 78)
    print(f"\n  {'book':16s} {'leg':6s} | {'mean':>7s} {'p10':>7s} {'p25':>7s} "
          f"{'MEDIAN':>7s} {'p75':>7s} {'p90':>7s} {'p99':>7s}")
    dist = {}
    for nm, (klo, khi) in BOOKS.items():
        c = cost_of(klo, khi)
        for leg_nm, v in c.items():
            q = [float(np.percentile(v, x)) for x in (10, 25, 50, 75, 90, 99)]
            dist[f"{nm}|{leg_nm}"] = dict(mean=float(v.mean()), q=q, n=int(v.size))
            print(f"  {nm:16s} {leg_nm:6s} | {v.mean():7.1f} " +
                  " ".join(f"{x:7.1f}" for x in q))
    print(f"\n  mean/median ratio tells you which problem this is:")
    for kk, vv in dist.items():
        print(f"    {kk:28s} mean/median = {vv['mean'] / vv['q'][2]:.2f}x")
    return finish(res, dist, locals())


def finish(res, dist, L):
    """Cuts 3-7."""
    np_ = np
    half, px, yrs, base, plan, T, k = (L["half"], L["px"], L["yrs"], L["base"],
                                       L["plan"], L["T"], L["k"])
    BOOKS, fwd, z = L["BOOKS"], L["fwd"], L["z"]
    R_, D_, M_ = R, D, M            # module-level, not locals of main()
    order_a, cnt_a, N = L["order_a"], L["cnt_a"], L["N"]

    def legs2(klo, khi):
        bc = np_.broadcast_to(plan.cols[None, :], plan.lo.shape)
        return (plan.lo[klo], bc[klo]), (plan.hi[khi], bc[khi])

    print("\n" + "=" * 78)
    print("  3. BY AS-TRADED PRICE  (cost in bp scales inversely with price)")
    print("=" * 78)
    klo, khi = BOOKS["confluence"]
    (lr, lc), (hr, hc) = legs2(klo, khi)
    r = np_.concatenate([lr, hr])
    c = np_.concatenate([lc, hc])
    p = px[r, c]
    h = half[r, c]
    ok = np_.isfinite(p) & np_.isfinite(h) & (p > 0)
    p, h = p[ok], h[ok]
    edges = [0, 1, 2, 5, 10, 20, 50, 1e9]
    lab = ["<$1", "$1-2", "$2-5", "$5-10", "$10-20", "$20-50", ">$50"]
    print(f"\n  {'price':8s} {'share of held':>14s} {'mean half':>10s} "
          f"{'median':>8s}")
    price_rows = []
    for i in range(len(edges) - 1):
        m = (p >= edges[i]) & (p < edges[i + 1])
        if m.sum() < 50:
            continue
        print(f"  {lab[i]:8s} {m.mean():13.1%} {h[m].mean():10.1f} "
              f"{np_.median(h[m]):8.1f}")
        price_rows.append(dict(bucket=lab[i], share=float(m.mean()),
                               mean_half=float(h[m].mean())))

    print("\n" + "=" * 78)
    print("  4. BY ERA")
    print("=" * 78)
    yr = yrs[c]
    print(f"\n  {'era':10s} {'share':>8s} {'mean half':>10s} {'median':>8s}")
    era_rows = []
    for nm, m in (("pre-2016", yr < 2016), ("2016-2019", (yr >= 2016) & (yr < 2020)),
                  ("2020", yr == 2020), ("2021+", yr > 2020)):
        mm = m[ok]
        if mm.sum() < 50:
            continue
        print(f"  {nm:10s} {mm.mean():7.1%} {h[mm].mean():10.1f} "
              f"{np_.median(h[mm]):8.1f}")
        era_rows.append(dict(era=nm, share=float(mm.mean()),
                             mean_half=float(h[mm].mean())))

    print("\n" + "=" * 78)
    print("  5. THE DECISIVE CUT -- rebuild the book INSIDE each spread tercile")
    print("=" * 78)
    q = np_.full(half.shape, np_.nan)
    for t in range(T):
        v = np_.where(base[:, t], half[:, t], np_.nan)
        f = np_.isfinite(v)
        if f.sum() < 30:
            continue
        rr = np_.argsort(np_.argsort(v[f]))
        q[f, t] = rr / max(rr.max(), 1)
    terc = {"tight": base & (q < 1 / 3), "mid": base & (q >= 1 / 3) & (q < 2 / 3),
            "wide": base & (q >= 2 / 3)}
    print(f"\n  {'tercile':8s} {'book':16s} | {'gross bp':>9s} {'t':>6s} | "
          f"{'round trip':>11s} | {'x cost':>7s} {'net bp':>9s}")
    terc_rows = []
    for tn, tmask in terc.items():
        o2, c2, _ = R_.ranked(z[D_.PRIMARY], tmask)
        pl2 = R_.LegPlan(o2, c2, N, T)
        if pl2.cols.size == 0:
            continue
        pc = {}
        for b in ("macd_hist", "rsi"):
            _, cb, pb = R_.ranked(z[b], tmask)
            pc[b] = (R_.pct_at(pb, cb, pl2.lo, pl2.cols),
                     R_.pct_at(pb, cb, pl2.hi, pl2.cols))
        kl2, kh2 = D_.op_meanrank(pc["macd_hist"][0], pc["macd_hist"][1],
                                  pc["rsi"][0], pc["rsi"][1], 0.75, N)
        for bn, (a1, a2) in (("hist_L alone",
                              (np_.ones(pl2.lo.shape, bool),
                               np_.ones(pl2.hi.shape, bool))),
                             ("confluence", (kl2, kh2))):
            s = own(R_.spread_sums(fwd, pl2, a1, a2, T))
            if s is None:
                continue
            bc2 = np_.broadcast_to(pl2.cols[None, :], pl2.lo.shape)
            vl = half[pl2.lo[a1], bc2[a1]]
            vh = half[pl2.hi[a2], bc2[a2]]
            rt = 2 * np_.nanmean(vl) + 2 * np_.nanmean(vh)
            print(f"  {tn:8s} {bn:16s} | {s['bp']:+9.2f} {s['t']:+6.2f} | "
                  f"{rt:11.1f} | {s['bp'] / rt:7.3f} {s['bp'] - rt:+9.1f}")
            terc_rows.append(dict(tercile=tn, book=bn, bp=s["bp"], t=s["t"],
                                  round_trip=float(rt), x=s["bp"] / rt))

    print("\n" + "=" * 78)
    print("  6. BREAKEVEN, BOTH WAYS")
    print("=" * 78)
    for nm, v in res.items():
        need_half = v["bp"] / 4.0
        print(f"\n  {nm}")
        print(f"    half-spread it FACES, per side (avg both legs) "
              f"{(v['long_half'] + v['short_half']) / 2:8.2f} bp")
        print(f"    half-spread it could AFFORD                    "
              f"{need_half:8.2f} bp")
        print(f"    -> needs spreads {((v['long_half'] + v['short_half']) / 2)
                                      / need_half:.1f}x TIGHTER than it faces")
        print(f"    effect it would NEED at its actual spread      "
              f"{v['round_trip']:8.2f} bp  (has {v['bp']:.2f})")

    print("\n" + "=" * 78)
    print("  7. COST PER UNIT TIME  (a ratio without turnover is unreadable)")
    print("=" * 78)
    tj = json.loads((REPO / "data" / "d290_turnover.json").read_text())
    tv = tj["hist_L"]
    print(f"\n  hist_L turnover {tv['long']['turnover']:.1%}/bar, mean holding "
          f"run {tv['long']['run']:.1f} bars, horizon k={k}")
    for nm, v in res.items():
        per_bar = v["round_trip"] * tv["long"]["turnover"]
        print(f"    {nm:16s} round trip {v['round_trip']:7.1f} bp x "
              f"{tv['long']['turnover']:.3f} = {per_bar:6.1f} bp/bar of cost, "
              f"against {v['bp'] / k:+5.1f} bp/bar of gross edge")

    json.dump({"purpose": "D293: where the round trip comes from and whether it "
                          "is avoidable. Seven cuts on both books.",
               "headline": res, "distribution": dist, "by_price": price_rows,
               "by_era": era_rows, "by_tercile": terc_rows},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
