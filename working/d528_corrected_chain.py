"""THE CONSTRUCTION ON THE CORRECTED ENTRY CHAIN -- both lenses, out of time.

    python working/d528_corrected_chain.py --build
    python working/d528_corrected_chain.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.

WHY EVERYTHING BEFORE THIS NEEDS REDOING. `d528_target_and_stability.py` found two defects in the
entry chain that every P&L number in D528 was computed through:

  1  `slope_ok` REMOVED 92% OF CANDIDATES AND BOUGHT NOTHING. Aligned candidates go from 3,468 to
     41,126 without it -- 11.9x -- and P(traverse, price-referenced) is slightly HIGHER at 0.1395
     against 0.1361. It came from the original A1 test and survived eleven addenda unexamined.
     It is dropped here.

  2  THE MEASUREMENT TARGET WAS PARTLY ITS OWN REFERENCE LEVEL. Measured against the [t-H,t) line
     extrapolated forward, ANTI-aligned excursions appeared to traverse 1.55x more often than
     aligned ones. Measured against PRICE, aligned traverse 2.05x more often (0.1395 vs 0.0680).
     The asymmetry did not shrink when the level was removed -- IT REVERSED. So the principal's
     drift-alignment rule is correct, and the "your filter removes the reversion" reading in the
     drift audit was an artefact of my target definition.

THAT SECOND FINDING RE-OPENS THE EXIT FRAME. ADDENDUM 5 measured drift-following exits as better
than frozen ones in 8 of 9 cells, and attributed it to the stop triggering earlier. But the drift
frame carries the same level motion that just corrupted the measurement target, so the comparison
deserves rerunning rather than inheriting. BOTH frames are reported as co-primaries here; neither
is assumed.

WHAT IS FIXED AND WHAT IS VARIED
  fixed    no slope_ok; a2 lattice; |y| >= 2 sigma; DRIFT ALIGNMENT (the principal's rule, now
           vindicated); feasibility; tau = 20 bars; no truncated trades; G = 3.0 sigma
  varied   target in {level, reflect} x frame in {frozen, drift}, and the FORECAST filter on/off
  scored   PATH-INVARIANT per trade and PATH-VARIANT as a slot-limited book, every cell against a
           matched control on mean, median AND trimmed mean (the ADDENDUM 11 fix)
  split    every cut from 2010-2019, evaluated on 2020-2026, both inside the cutoff

THE POINT OF THE EXERCISE: at 11.9x the candidates the tradeable sample should finally approach
the ~14,500 trades ADDENDUM 7 showed are needed to resolve a $0.50-per-trade effect against a
$36.54 per-trade standard deviation. Every cell in this study so far has had 40-500.
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
import d528_target_and_stability as TS          # noqa: E402

CACHE = Path("temp/d528_corrected_cache.parquet")
H = Z.H
X, G, TAU = 2.0, 3.0, 20
GRID = (("level", "frozen"), ("level", "drift"),
        ("reflect", "frozen"), ("reflect", "drift"))
SPLIT = FR.SPLIT
FEATS4 = TS.FEATS4
SLOTS = (1, 3, 10)
ACCOUNT, TRAIL = 50_000.0, 2_000.0
N_DRAW = 300
SEED = 528131
MICRO = W.MICRO


def P(*a):
    print(*a, flush=True)


def build():
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"collecting {len(roots)} roots, {len(udays)} sessions; slope_ok DROPPED ...")
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
            tg, ok = TS.three_targets(px, c)
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(ok)
            # THE CORRECTED CHAIN: no slope_ok
            with np.errstate(invalid="ignore"):
                base = np.asarray(c["a2ok"]) & (c["flat_sd"] > 0)
                base = base & (np.abs(c["flat_y"]) >= X * c["flat_sd"])
                base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
                base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
            base = np.nan_to_num(base, nan=False).astype(bool)
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU)] = True
            base = base & room & ok
            if not base.any():
                continue
            idx0 = np.flatnonzero(base)
            res = {}
            for (tgt, frm) in GRID:
                tr = O.resolve(px, c, "flat", base, tick, tick_usd, cost_tk,
                               tgt, frm, G, TAU, di[day], b0, r)
                res[(tgt, frm)] = tr
            n = len(res[GRID[0]])
            if n == 0:
                continue
            idx = [i for i in idx0 if (i + 2 * H) < len(px) - 1][:n]
            blk = {"root": np.full(n, r, dtype=object), "day": np.full(n, day, dtype=object),
                   "day_idx": np.full(n, float(di[day])),
                   "tick_usd": np.full(n, tick_usd),
                   "cost": np.array([z["cost_usd"] for z in res[GRID[0]]]),
                   "trav_price": tg["price"][idx].astype(float),
                   "trav_line": tg["line"][idx].astype(float)}
            for (tgt, frm) in GRID:
                tr = res[(tgt, frm)]
                k = f"{tgt}_{frm}"
                blk[f"g_{k}"] = np.array([z["g_real_tk"] * z["tick_usd"] for z in tr])
                blk[f"kind_{k}"] = np.array([z["kind"] for z in tr], float)
                blk[f"tin_{k}"] = np.array([z["t_in"] for z in tr], float)
                blk[f"tout_{k}"] = np.array([z["t_out"] for z in tr], float)
                blk[f"tgt_{k}"] = np.array([z["perfect_tk"] * z["tick_usd"] for z in tr])
            for kk in FEATS4:
                v = ft[kk]
                blk[kk] = v[idx] if len(v) == n_t else np.full(n, np.nan)
            rows.append(blk)
    cols = rows[0].keys()
    df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    P(f"cached {len(df):,} candidates, {df['root'].nunique()} roots -> {CACHE}")


def inv(rows, pool, key, rng):
    if len(rows) < 50:
        return None
    g = rows[f"g_{key}"].to_numpy(float)
    net = g - rows["cost"].to_numpy(float)
    gp = pool[f"g_{key}"].to_numpy(float)
    dr = gp[rng.integers(0, len(gp), (N_DRAW, len(g)))]
    lo, hi = np.percentile(dr, [1, 99], axis=1)
    tdr = np.array([d[(d >= l) & (d <= h)].mean() for d, l, h in zip(dr, lo, hi)])
    l1, h1 = np.percentile(g, [1, 99])
    pos = net[net > 0]
    return {"n": len(g), "p_trav": float(rows["trav_price"].mean()),
            "p_tgt": float((rows[f"kind_{key}"] == 0).mean()),
            "win": float((net > 0).mean()), "gross": g.mean(), "net": net.mean(),
            "med": float(np.median(g)), "trim": g[(g >= l1) & (g <= h1)].mean(),
            "m95": float(np.percentile(dr.mean(1), 95)),
            "d95": float(np.percentile(np.median(dr, 1), 95)),
            "t95": float(np.percentile(tdr, 95)),
            "top3": float(np.sort(net)[-3:].sum() / pos.sum()) if len(pos) else np.nan}


def bookrun(rows, key, n_slots, nsess):
    if len(rows) < 50:
        return None
    rr = rows.sort_values([f"tin_{key}", f"tgt_{key}"], ascending=[True, False])
    tin = rr[f"tin_{key}"].to_numpy(); tout = rr[f"tout_{key}"].to_numpy()
    rt = rr["root"].to_numpy(); g = rr[f"g_{key}"].to_numpy(); c = rr["cost"].to_numpy()
    dy = rr["day_idx"].to_numpy()
    open_pos, held, take, bars = [], set(), [], 0.0
    for i in range(len(rr)):
        keep = []
        for (to, r0) in open_pos:
            if to <= tin[i]:
                held.discard(r0)
            else:
                keep.append((to, r0))
        open_pos = keep
        if len(open_pos) >= n_slots or rt[i] in held:
            continue
        open_pos.append((tout[i], rt[i]))
        held.add(rt[i])
        bars += tout[i] - tin[i]
        take.append(i)
    if len(take) < 50:
        return None
    take = np.array(take)
    net = g[take] - c[take]
    ud = np.unique(dy[take])
    dn = np.array([net[dy[take] == u].sum() for u in ud])
    full = np.zeros(nsess); full[:len(dn)] = dn
    rrn = full / ACCOUNT
    shn = rrn.mean() / rrn.std(ddof=1) * np.sqrt(252) if rrn.std(ddof=1) > 0 else np.nan
    dg = np.array([g[take][dy[take] == u].sum() for u in ud])
    fg = np.zeros(nsess); fg[:len(dg)] = dg
    rg = fg / ACCOUNT
    shg = rg.mean() / rg.std(ddof=1) * np.sqrt(252) if rg.std(ddof=1) > 0 else np.nan
    eq = np.cumsum(dn)
    dd = float(np.max(np.maximum.accumulate(np.concatenate(([0.0], eq)))
                      - np.concatenate(([0.0], eq))))
    return {"n": len(take), "net": net.mean(), "tot": net.sum(), "sh_g": shg, "sh_n": shn,
            "win": float((net > 0).mean()), "dd_x": dd / TRAIL,
            "expo": bars / max(n_slots * nsess * 84, 1)}


def run():
    if not CACHE.exists():
        P(f"no cache at {CACHE}; run --build first")
        return
    rng = np.random.default_rng(SEED)
    d = pd.read_parquet(CACHE)
    tr = d[d["day"] < SPLIT]
    te = d[d["day"] >= SPLIT].copy()
    zt, ze = [], []
    for k in FEATS4:
        mu, sd = np.nanmean(tr[k]), np.nanstd(tr[k])
        zt.append(((tr[k] - mu) / sd).to_numpy(float))
        ze.append(((te[k] - mu) / sd).to_numpy(float))
    cut = float(np.nanpercentile(np.nanmean(np.vstack(zt), axis=0), 50))
    te["score"] = np.nanmean(np.vstack(ze), axis=0)
    te["hi_f"] = te["score"] <= cut

    P("THE CONSTRUCTION ON THE CORRECTED CHAIN (slope_ok DROPPED, drift alignment KEPT)")
    P(f"  cache {len(d):,} candidates   EARLY {len(tr):,} (cuts) / LATE {len(te):,} (scored)")
    P(f"  forecast cut from the early half: score <= {cut:+.4f}")
    P(f"  P(traverse, price-referenced): all {d['trav_price'].mean():.4f}, "
      f"late {te['trav_price'].mean():.4f}, late+forecast "
      f"{te.loc[te['hi_f'], 'trav_price'].mean():.4f}")
    P(f"  reserved slice NOT read; out-of-time throughout\n")

    for uni, label in ((sorted(set(te["root"])), "ALL ROOTS"), (list(MICRO), "MICRO (tradeable)")):
        sub = te[te["root"].isin(uni)].copy()
        if len(sub) < 400:
            continue
        nsess = int(sub["day"].nunique())
        P("=" * 122)
        P(f"{label}: {len(sub):,} candidates, {sub['root'].nunique()} roots, {nsess} sessions,"
          f" mean cost ${sub['cost'].mean():.2f}")
        P("")
        P("  PATH-INVARIANT (per trade).  * = above the matched control's p95 on that statistic.")
        P("    target   frame   fcst      n   P(tgt)  win%   gross$    net$    med$   trim$ |"
          " mean med trim | top3")
        for (tgt, frm) in GRID:
            key = f"{tgt}_{frm}"
            for fl, m in (("off", np.ones(len(sub), bool)), ("ON ", sub["hi_f"].to_numpy())):
                o = inv(sub[m], sub, key, rng)
                if o is None:
                    continue
                mk = lambda v, p: "*" if v > p else " "        # noqa: E731
                P(f"    {tgt:<8} {frm:<7} {fl}  {o['n']:>6,} {o['p_tgt']:>7.1%} "
                  f"{o['win']:>5.1%} {o['gross']:>+8.2f} {o['net']:>+7.2f} {o['med']:>+7.1f} "
                  f"{o['trim']:>+7.2f} |  {mk(o['gross'], o['m95'])}   "
                  f"{mk(o['med'], o['d95'])}    {mk(o['trim'], o['t95'])}  | {o['top3']:>5.1%}")
        P("")
        P("  PATH-VARIANT (slot-limited book)")
        P("    target   frame   fcst  slots  trades  expo   $/trade  Sharpe g  Sharpe n  win%"
          "   total$   maxDD/2k")
        for (tgt, frm) in GRID:
            key = f"{tgt}_{frm}"
            for fl, m in (("off", np.ones(len(sub), bool)), ("ON ", sub["hi_f"].to_numpy())):
                for ns in SLOTS:
                    bk = bookrun(sub[m], key, ns, nsess)
                    if bk is None:
                        continue
                    P(f"    {tgt:<8} {frm:<7} {fl} {ns:>5} {bk['n']:>7,} {bk['expo']:>5.1%} "
                      f"{bk['net']:>+9.2f} {bk['sh_g']:>+9.2f} {bk['sh_n']:>+9.2f} "
                      f"{bk['win']:>5.1%} {bk['tot']:>+9.0f} {bk['dd_x']:>9.2f}")
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
