"""THE JOINT CONSTRUCTION, FULL TEST: forecast x entry-time payoff, both lenses.

    python working/d528_joint_full.py --build     # collect once with book fields, cache
    python working/d528_joint_full.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10. **The reserved slice is NOT
read.** Out-of-time throughout: every cut is taken from 2010-2019 and applied unchanged to
2020-2026, both halves inside the cutoff.

THE CONSTRUCTION. The detector and trade are unchanged from ADDENDUM 5 -- rolling, flat-mean
level, drift-aligned 2 sigma entry, target at the MIRROR of the entry, drift-following exits,
stop at G=3.0, tau=20. Two filters sit on top:

  FORECAST   an equal-weight z-score of vol_ratio, squeeze, vratio2 and ac1, all causal, all
             measured before t. Low score = more predicted forward reversion. Cut at the EARLY
             half's median. These four were established at t = -155 / -95 / -116 / -114 with
             early and late lifts matching to within 0.001.
  PAYOFF     target/cost at ENTRY, where target is the perfect-reversion payoff |y| in dollars.
             This is knowable before committing -- the property the principal identified as the
             construction's real advantage. Cut at the EARLY half's median.

WHY BOTH ARE NEEDED, measured rather than assumed. The forecast alone raises P(traverse) from
11.4% to 24.3% and the payoff when you win COLLAPSES to 0.17x ($187.62 -> $30.96), so expected
gross never lifts. The payoff filter alone selects large targets that revert rarely. Only the
JOINT cell had positive expected gross (+$8.02 on n=501, out of time), because the two are only
mildly anti-correlated (corr +0.2295) and can co-occur.

THE CONTROL THAT MATTERS. Both filters are sigma-driven, so the joint cell might be nothing more
than "pick a middling volatility band". The 2x2 answers it directly: HOLDING THE PAYOFF BAND
FIXED, does the forecast still add? high-payoff/high-forecast against high-payoff/low-forecast is
that comparison, and it is reported as the primary contrast rather than the raw cell.

BOTH LENSES, never on one statistic:
  PATH-INVARIANT  every candidate, no slot cap, per TRADE
  PATH-VARIANT    the slot-limited book, one position per root, as an equity curve against the
                  $2,000 trailing limit
Their difference is opportunity cost. One collection feeds both.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402

CACHE = Path("temp/d528_joint_cache.parquet")
H = Z.H
X, G, TAU = 2.0, 3.0, 20
TARGET, FRAME = "reflect", "drift"
SPLIT = FR.SPLIT
FEATS4 = ("vol_ratio", "squeeze", "vratio2", "ac1")
SLOTS = (1, 3, 10)
SLOTS_PRIMARY = 3
ACCOUNT = 50_000.0
TRAIL = 2_000.0
N_DRAW = 400
SEED = 528443
MICRO = W.MICRO


def P(*a):
    print(*a, flush=True)


def build():
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"collecting {len(roots)} roots, {len(udays)} sessions, through {W.IS_END} ...")
    rows = []
    for r in roots:
        g = f[f["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            fwd, ok = FR.forward_traverse(px, c)
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(fwd)
            base = (c["flat_sd"] > 0) & c["slope_ok"] & c["a2ok"]
            with np.errstate(invalid="ignore"):
                base = base & (np.abs(c["flat_y"]) >= X * c["flat_sd"])
            base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
            base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
            base = np.nan_to_num(base, nan=False).astype(bool)
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU)] = True
            base = base & room
            if not base.any():
                continue
            tr = O.resolve(px, c, "flat", base, tick, tick_usd, cost_tk,
                           TARGET, FRAME, G, TAU, di[day], b0, r)
            idx = [i for i in np.flatnonzero(base) if (i + 2 * H) < len(px) - 1][:len(tr)]
            if not idx:
                continue
            k = len(idx)
            blk = {
                "root": np.full(k, r, dtype=object), "day": np.full(k, day, dtype=object),
                "day_idx": np.array([di[day]] * k, float),
                "t_in": np.array([z["t_in"] for z in tr], float),
                "t_out": np.array([z["t_out"] for z in tr], float),
                "side": np.array([z["side"] for z in tr], float),
                "bars": np.array([z["bars"] for z in tr], float),
                "kind": np.array([z["kind"] for z in tr], float),
                "g_real_tk": np.array([z["g_real_tk"] for z in tr]),
                "g_ideal_tk": np.array([z["g_ideal_tk"] for z in tr]),
                "tick_usd": np.full(k, tick_usd), "cost": np.array([z["cost_usd"] for z in tr]),
                "tgt_usd": np.array([z["perfect_tk"] * z["tick_usd"] for z in tr]),
                "x_sig": np.array([z["x_sig"] for z in tr]),
                "sigma_usd": np.array([c["flat_sd"][i] / tick * tick_usd for i in idx]),
                "trav_fwd": fwd[idx].astype(float),
            }
            blk["gross"] = blk["g_real_tk"] * blk["tick_usd"]
            for kk in FEATS4:
                v = ft[kk]
                blk[kk] = v[idx] if len(v) == n_t else np.full(k, np.nan)
            rows.append(blk)
    cols = rows[0].keys()
    df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    P(f"cached {len(df):,} rows, {df['root'].nunique()} roots -> {CACHE}")


def book(rows, n_slots, n_sessions, fill="g_real_tk"):
    """PATH-VARIANT: slot-limited, one position per root, ranked by entry-time payoff."""
    if len(rows) < 20:
        return None
    rr = rows.sort_values(["t_in", "tgt_usd"], ascending=[True, False])
    taken, open_pos, held, slot_bars = [], [], set(), 0.0
    for z in rr.itertuples():
        keep = []
        for (to, rt) in open_pos:
            if to <= z.t_in:
                held.discard(rt)
            else:
                keep.append((to, rt))
        open_pos = keep
        if len(open_pos) >= n_slots or z.root in held:
            continue
        open_pos.append((z.t_out, z.root))
        held.add(z.root)
        slot_bars += z.t_out - z.t_in
        taken.append(z)
    if len(taken) < 20:
        return None
    g = np.array([getattr(z, fill) * z.tick_usd for z in taken])
    c = np.array([z.cost for z in taken])
    net = g - c
    days = np.array([z.day_idx for z in taken])
    ud = np.unique(days)
    dn = np.array([net[days == u].sum() for u in ud])
    full = np.zeros(n_sessions)
    full[:len(dn)] = dn
    rr_ = full / ACCOUNT
    sh_n = rr_.mean() / rr_.std(ddof=1) * np.sqrt(252) if rr_.std(ddof=1) > 0 else np.nan
    dg = np.array([g[days == u].sum() for u in ud])
    fg = np.zeros(n_sessions)
    fg[:len(dg)] = dg
    rg = fg / ACCOUNT
    sh_g = rg.mean() / rg.std(ddof=1) * np.sqrt(252) if rg.std(ddof=1) > 0 else np.nan
    eq = np.cumsum(dn)
    dd = float(np.max(np.maximum.accumulate(np.concatenate(([0.0], eq)))
                      - np.concatenate(([0.0], eq))))
    return {"n": len(taken), "gross": g.mean(), "net": net.mean(), "tot": net.sum(),
            "sh_g": sh_g, "sh_n": sh_n, "win": float((net > 0).mean()),
            "maxdd": dd, "dd_x": dd / TRAIL,
            "expo": slot_bars / max(n_slots * n_sessions * 84, 1)}


def invariant(rows, pool, rng):
    """PATH-INVARIANT: per trade, with mean/median/trimmed against the matched control."""
    if len(rows) < 30:
        return None
    g = rows["gross"].to_numpy(float)
    net = (rows["gross"] - rows["cost"]).to_numpy(float)
    gp = pool["gross"].to_numpy(float)
    dr = gp[rng.integers(0, len(gp), (N_DRAW, len(g)))]
    lo, hi = np.percentile(dr, [1, 99], axis=1)
    tdr = np.array([d[(d >= l) & (d <= h)].mean() for d, l, h in zip(dr, lo, hi)])
    l1, h1 = np.percentile(g, [1, 99])
    tg = g[(g >= l1) & (g <= h1)].mean()
    pos = net[net > 0]
    return {"n": len(g), "p_trav": float(rows["trav_fwd"].mean()),
            "p_tgt": float((rows["kind"] == 0).mean()), "win": float((net > 0).mean()),
            "gross": g.mean(), "net": net.mean(), "med": float(np.median(g)), "trim": float(tg),
            "m95": float(np.percentile(dr.mean(1), 95)),
            "d95": float(np.percentile(np.median(dr, 1), 95)),
            "t95": float(np.percentile(tdr, 95)),
            "top3": float(np.sort(net)[-3:].sum() / pos.sum()) if len(pos) else np.nan,
            "cost": float(rows["cost"].mean())}


def run():
    if not CACHE.exists():
        P(f"no cache at {CACHE}; run --build first")
        return
    rng = np.random.default_rng(SEED)
    d = pd.read_parquet(CACHE)
    d["er_ratio"] = d["tgt_usd"] / d["cost"]
    tr = d[d["day"] < SPLIT]
    te = d[d["day"] >= SPLIT].copy()

    # the forecast score: z-scored on the EARLY half only, applied unchanged to the late half
    zt, ze = [], []
    for k in FEATS4:
        mu, sd = np.nanmean(tr[k]), np.nanstd(tr[k])
        zt.append(((tr[k] - mu) / sd).to_numpy(float))
        ze.append(((te[k] - mu) / sd).to_numpy(float))
    s_tr = np.nanmean(np.vstack(zt), axis=0)
    te["score"] = np.nanmean(np.vstack(ze), axis=0)
    s_cut = float(np.nanpercentile(s_tr, 50))
    r_cut = float(np.nanpercentile(tr["er_ratio"], 50))
    te["hi_f"] = te["score"] <= s_cut
    te["hi_p"] = te["er_ratio"] >= r_cut

    P("THE JOINT CONSTRUCTION -- forecast x entry-time payoff, BOTH LENSES")
    P(f"  cache {len(d):,} rows; EARLY {len(tr):,} (cuts) / LATE {len(te):,} (evaluated)")
    P(f"  cuts from the early half only: score <= {s_cut:+.4f}, target/cost >= {r_cut:.2f}")
    P(f"  reserved slice NOT read; every number below is out-of-time\n")

    for uni, label in ((sorted(set(te["root"])), "ALL ROOTS"),
                       ([r for r in MICRO], "MICRO ONLY (tradeable)")):
        sub = te[te["root"].isin(uni)].copy()
        if len(sub) < 200:
            continue
        nsess = int(sub["day"].nunique())
        P("=" * 118)
        P(f"{label}: {len(sub):,} candidates, {sub['root'].nunique()} roots, "
          f"{nsess} sessions, mean cost ${sub['cost'].mean():.2f}")
        P("")
        cells = (("pool", np.ones(len(sub), bool)),
                 ("forecast only", sub["hi_f"].to_numpy() & ~sub["hi_p"].to_numpy()),
                 ("payoff only", ~sub["hi_f"].to_numpy() & sub["hi_p"].to_numpy()),
                 ("JOINT (both)", sub["hi_f"].to_numpy() & sub["hi_p"].to_numpy()),
                 ("neither", ~sub["hi_f"].to_numpy() & ~sub["hi_p"].to_numpy()))
        P("  PATH-INVARIANT (per trade)")
        P("    cell             n   P(trav) P(tgt)  win%   gross$    net$   med$  trim$ |"
          " vs p95: mean med trim | top3")
        for nm, m in cells:
            iv = invariant(sub[m], sub, rng)
            if iv is None:
                P(f"    {nm:<14} {int(m.sum()):>5}  too few")
                continue
            mk = lambda v, p: "*" if v > p else " "        # noqa: E731
            P(f"    {nm:<14} {iv['n']:>5} {iv['p_trav']:>8.1%} {iv['p_tgt']:>6.1%} "
              f"{iv['win']:>5.1%} {iv['gross']:>+8.2f} {iv['net']:>+7.2f} {iv['med']:>+6.1f} "
              f"{iv['trim']:>+6.2f} |   {mk(iv['gross'], iv['m95'])}    "
              f"{mk(iv['med'], iv['d95'])}    {mk(iv['trim'], iv['t95'])}  | {iv['top3']:>5.1%}")
        P("")
        P("  PATH-VARIANT (slot-limited book, ranked by entry-time payoff)")
        P("    cell           slots   trades  expo   $/trade  Sharpe g  Sharpe n   win%"
          "   total $   maxDD/$2k")
        for nm, m in cells:
            if nm in ("forecast only", "neither"):
                continue
            for ns in SLOTS:
                bk = book(sub[m], ns, nsess)
                if bk is None:
                    continue
                P(f"    {nm:<14} {ns:>5} {bk['n']:>8,} {bk['expo']:>5.1%} "
                  f"{bk['net']:>+9.2f} {bk['sh_g']:>+9.2f} {bk['sh_n']:>+9.2f} "
                  f"{bk['win']:>6.1%} {bk['tot']:>+9.0f} {bk['dd_x']:>10.2f}")
        P("")
        # THE CONTROL: holding the payoff band fixed, does the forecast still add?
        hp = sub[sub["hi_p"].to_numpy()]
        a = invariant(hp[hp["hi_f"].to_numpy()], sub, rng)
        b = invariant(hp[~hp["hi_f"].to_numpy()], sub, rng)
        if a and b:
            P(f"  CONTROL -- within the HIGH-PAYOFF band only, does the forecast add?")
            P(f"    high forecast  n {a['n']:>5}  P(trav) {a['p_trav']:.1%}  "
              f"gross ${a['gross']:+.2f}  net ${a['net']:+.2f}")
            P(f"    low  forecast  n {b['n']:>5}  P(trav) {b['p_trav']:.1%}  "
              f"gross ${b['gross']:+.2f}  net ${b['net']:+.2f}")
            se = np.sqrt(np.var(hp[hp["hi_f"]]["gross"], ddof=1) / max(a["n"], 1)
                         + np.var(hp[~hp["hi_f"]]["gross"], ddof=1) / max(b["n"], 1))
            P(f"    DIFFERENCE     ${a['gross']-b['gross']:+.2f} gross  (SE {se:.2f}, "
              f"t {(a['gross']-b['gross'])/se:+.2f})")
            P(f"    -- both cells share the payoff band, so this isolates the FORECAST from")
            P(f"       'pick a middling volatility'. sigma: high-f ${a and hp[hp['hi_f']]['sigma_usd'].median():.0f}"
              f" vs low-f ${hp[~hp['hi_f']]['sigma_usd'].median():.0f} median")
        P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
    if a.run:
        run()
    if not (a.build or a.run):
        ap.error("choose --build or --run")
