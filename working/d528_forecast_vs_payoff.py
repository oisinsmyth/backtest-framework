"""THE DISCONNECT: the forecastable event is not the event that pays.

    python working/d528_forecast_vs_payoff.py --build      # collect once, cache to temp/
    python working/d528_forecast_vs_payoff.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.

WHERE THIS COMES FROM. `d528_forecast_reversion.py` established that forward mean reversion IS
strongly forecastable: `vol_ratio` moves P(traverse ahead) from a 14.95% base to 22.1% in its
quiet quintile and 7.9% in its active one -- a 2.8x spread at t = -155 on 2.3M out-of-time bars,
replicating almost exactly between the early and late halves. That answers the principal's
question: yes, and by a lot.

But the tradeable cells inverted: `vol_ratio` Q1 forecast 16.9% traversal and earned -$25.84,
while Q5 forecast 4.9% and earned -$9.47. MORE predicted reversion, LESS money.

A FIRST HYPOTHESIS, TESTED AND REJECTED: that forecastable windows are quiet, so sigma is small,
so the target is too small to clear a fixed cost. The target/cost ratio by vol_ratio quintile is
6.13 / 7.25 / 5.89 / 7.95 / 7.08 -- flat. Absolute targets ARE smaller in the quiet quintile
($73 vs $139) but so are the costs ($11.93 vs $19.67), and they cancel.

THE HYPOTHESIS THIS FILE TESTS, which is a conflation in the earlier work rather than a market
fact: TWO DIFFERENT EVENTS HAVE BEEN CALLED "REVERSION".

    the FORECAST target   price reaches BOTH -1.5 and +1.5 sigma inside [t, t+H)
    the TRADE's target    price travels from the entry extreme (~2.7 sigma, because entries
                          overshoot their 2-sigma trigger) to the MIRROR at ~-2.7 sigma

The second is a far longer journey -- roughly 5.4 sigma against 3.0 -- and it is directional,
whereas traversal is satisfied by any two-sided wobble. Forecasting the first well can therefore
say nothing about the second. This file puts them side by side, by quintile, so the disconnect is
measured rather than argued.

If P(trade target) does NOT track P(traverse ahead) across quintiles, the forecastable quantity is
simply not the quantity that pays, and the fix is to forecast the trade's own outcome instead --
not to build a better model of traversal.
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
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402

CACHE = Path("temp/d528_forecast_cache.parquet")
H = Z.H
X, G, TAU = 2.0, 3.0, 20
TARGET, FRAME = "reflect", "drift"
SPLIT = FR.SPLIT
N_DRAW = 400
SEED = 528991


def P(*a):
    print(*a, flush=True)


def build():
    """Collect once and cache. The collection is ~9 minutes; every later question is seconds."""
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    P(f"collecting {len(roots)} roots through {W.IS_END} ...")
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
                           TARGET, FRAME, G, TAU, 0, b0, r)
            idx = [i for i in np.flatnonzero(base) if (i + 2 * H) < len(px) - 1][:len(tr)]
            if not idx:
                continue
            k = len(idx)
            blk = {"root": np.full(k, r, dtype=object), "day": np.full(k, day, dtype=object),
                   "trav_fwd": fwd[idx].astype(float),
                   "kind": np.array([z["kind"] for z in tr], float),
                   "gross": np.array([z["g_real_tk"] * z["tick_usd"] for z in tr]),
                   "cost": np.array([z["cost_usd"] for z in tr]),
                   "tgt_usd": np.array([z["perfect_tk"] * z["tick_usd"] for z in tr]),
                   "bars": np.array([z["bars"] for z in tr], float)}
            for kk in FR.FEATS:
                v = ft[kk]
                blk[kk] = v[idx] if len(v) == n_t else np.full(k, np.nan)
            rows.append(blk)
    cols = rows[0].keys()
    df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    P(f"cached {len(df):,} tradeable rows -> {CACHE}")


def run():
    if not CACHE.exists():
        P(f"no cache at {CACHE}; run --build first")
        return
    rng = np.random.default_rng(SEED)
    d = pd.read_parquet(CACHE)
    d["net"] = d["gross"] - d["cost"]
    d["hit"] = (d["kind"] == 0).astype(float)
    P("THE DISCONNECT: the forecastable event is not the event that pays")
    P(f"  {len(d):,} tradeable rows, {d['day'].min()} .. {d['day'].max()}")
    P(f"  P(traverse ahead, +/-1.5 sigma) = {d['trav_fwd'].mean():.4f}")
    P(f"  P(trade target hit, the mirror) = {d['hit'].mean():.4f}")
    P("")
    P("  If the two moved together, forecasting traversal would forecast the trade. They are")
    P("  different journeys: ~3.0 sigma of two-sided wobble versus ~5.4 sigma in one direction.")
    P("")
    P("=" * 104)
    P("1  BOTH EVENTS, BY QUINTILE OF EACH FORECASTING FEATURE")
    P("")
    P("    feature       quintile     n    P(traverse)  P(trade target)   gross $    net $")
    for k in ("vol_ratio", "squeeze", "vratio2", "ac1"):
        v = d[k].to_numpy(float)
        ok = np.isfinite(v)
        if ok.sum() < 500:
            continue
        q = np.nanpercentile(v[ok], [20, 40, 60, 80])
        ed = [-np.inf] + list(q) + [np.inf]
        for i in range(5):
            m = ok & (v >= ed[i]) & (v < ed[i + 1])
            s = d[m]
            if len(s) < 50:
                continue
            P(f"    {k:<13} Q{i+1}      {len(s):>6,} {s['trav_fwd'].mean():>11.1%} "
              f"{s['hit'].mean():>16.1%} {s['gross'].mean():>+10.2f} {s['net'].mean():>+8.2f}")
        # the correlation that settles it
        mm = ok
        c1 = np.corrcoef(d.loc[mm, "trav_fwd"], d.loc[mm, "hit"])[0, 1]
        P(f"    {'':<13} corr(traverse, trade target) over this feature's rows = {c1:+.4f}")
        P("")
    P("=" * 104)
    P("2  THE TWO EVENTS, DIRECTLY")
    P("")
    tv = d["trav_fwd"].to_numpy(float)
    ht = d["hit"].to_numpy(float)
    P(f"    corr(traverse ahead, trade target hit) = {np.corrcoef(tv, ht)[0,1]:+.4f}")
    P(f"    P(trade target | traversed)     = {ht[tv > 0.5].mean():.4f}  "
      f"on {int((tv > 0.5).sum()):,} rows")
    P(f"    P(trade target | did NOT)       = {ht[tv < 0.5].mean():.4f}  "
      f"on {int((tv < 0.5).sum()):,} rows")
    lift = ht[tv > 0.5].mean() - ht.mean()
    se = np.sqrt(ht.var(ddof=1) / max((tv > 0.5).sum(), 1))
    P(f"    LIFT of traversal on the trade's own target = {lift:+.4f}  (SE {se:.4f}, "
      f"t {lift/se:+.1f})")
    P("")
    P(f"    gross | traversed     ${d.loc[d['trav_fwd'] > 0.5, 'gross'].mean():+.2f}")
    P(f"    gross | did NOT       ${d.loc[d['trav_fwd'] < 0.5, 'gross'].mean():+.2f}")
    P("")
    P("  READING IT. A large positive lift means traversal DOES predict the trade winning, and")
    P("  the forecast is worth building on. A lift near zero means the two events are nearly")
    P("  unrelated: the quantity that is forecastable is simply not the quantity that pays, and")
    P("  the next move is to forecast the TRADE's own outcome, not traversal.")


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
