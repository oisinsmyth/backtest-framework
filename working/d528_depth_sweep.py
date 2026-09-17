"""DEPTH x CONFIRMATION SWEEP: can a deeper extreme decouple hit rate from payoff?

    python working/d528_depth_sweep.py --build
    python working/d528_depth_sweep.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.
Corrected chain throughout: slope_ok DROPPED, drift alignment KEPT (ADDENDUM 12).

THE PRINCIPAL'S HYPOTHESIS: pushing the entry extreme further from the mean drops the win rate and
raises the profit per win, and combined with the confirmation entry that may DECOUPLE the two --
breaking the conservation of hit x payoff that has now defeated the construction four times (the
stop ladder in ADDENDUM 4, the geometry sweep in ADDENDUM 7, the forecast in ADDENDUM 12, and the
confirmation entry).

MY PREDICTION, RECORDED BEFORE RUNNING, AND IT DIFFERS FROM HIS:

    hit x payoff on GROSS stays roughly conserved. It arises from near-martingale behaviour and
    has survived 30 geometries, 6 stop widths, a forecast and three entry modes. A deeper
    threshold changes where the bet is placed, not whether the market pays for it.

    BUT NET MAY STILL IMPROVE, by a different mechanism than decoupling: COST IS FIXED at ~$4.58
    a round trip, of which $3.00 is commission. A deeper entry is a BIGGER trade, so the same
    fixed cost is a smaller FRACTION of the payoff. That is exactly what made the
    opposite-extreme target work -- cost fell from 13.9% to 7.9% of the perfect payoff.

Both readings predict better net at higher X. They differ on WHY, and the difference is
observable: if `hit x payoff` on gross is flat while `cost / payoff` falls, the mechanism is cost
amortisation and the conservation law is intact. If `hit x payoff` RISES with depth, the principal
is right and something genuinely decouples.

THE SWEEP
    X       2.0 / 2.5 / 3.0 / 3.5 sigma from the mean   (the entry extreme)
    mode    market; stop_retrace at 0.25 and 0.50 sigma; limit_deeper at 0.50 sigma
    stale   10 bars (10 beat 5 in every cell of the confirmation run)

REPORTED FOR EVERY CELL: fill rate, P(target), win rate, mean win and mean loss on GROSS, their
ratio, HIT x PAYOFF, cost as a fraction of the perfect payoff, gross and net. Out of time
throughout; both universes.

NOTE ON `limit_deeper`. The confirmation run showed it is not a cost question at all: a resting
limit placed deeper only fills when price keeps going, so it selects the excursions that did NOT
revert. P(target) fell from 9.9% to 2.5% and gross from -$1.26 to -$11.82 -- the fill condition IS
the adverse selection, and it cost 13x what the spread saving was worth. It is carried here only
to check whether greater depth changes that verdict.
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
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402
import d528_target_and_stability as TS          # noqa: E402
import d528_confirmation_entry as CE            # noqa: E402

CACHE = Path("temp/d528_depth_cache3.parquet")
H = Z.H
TAU = 20
# THE STOP MUST SCALE WITH THE ENTRY DEPTH, or the sweep measures a different trade at each X.
# Holding G at 3.0 sigma while X rose put the stop AT the entry at X=3.0 and 0.5 sigma INSIDE it
# at X=3.5 -- where price moving into the "stop" is moving FAVOURABLY, so it became a
# take-profit. That produced a win rate climbing to 46.0% while P(target) fell to 3.6%, which
# looked exactly like the hit/payoff decoupling under test and was purely broken geometry.
# G = X + STOP_BEYOND keeps the stop exactly STOP_BEYOND sigma past the entry at every depth,
# reproducing the baseline (X=2.0 -> G=3.0) and isolating DEPTH as the only thing that varies.
STOP_BEYOND = 1.0
XS = (2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0)
COMBOS = (("market", 0.0), ("stop_retrace", 0.25), ("stop_retrace", 0.50))
STALE = 10
SPLIT = FR.SPLIT
FEATS4 = TS.FEATS4
MICRO = W.MICRO
SEED = 528967


def P(*a):
    print(*a, flush=True)


def build():
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    udays = sorted(set(f["day"]))
    di = {d: i for i, d in enumerate(udays)}
    P(f"collecting {len(roots)} roots x {len(XS)} depths x {len(COMBOS)} entry modes ...")
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
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(c["flat_y"])
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU - STALE)] = True
            for xv in XS:
                with np.errstate(invalid="ignore"):
                    base = np.asarray(c["a2ok"]) & (c["flat_sd"] > 0)
                    base = base & (np.abs(c["flat_y"]) >= xv * c["flat_sd"])
                    base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
                    base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
                base = np.nan_to_num(base, nan=False).astype(bool) & room
                if not base.any():
                    continue
                sel = np.flatnonzero(base)
                feat = {k: ft[k][sel] for k in FEATS4}
                g_x = xv + STOP_BEYOND        # the stop stays 1 sigma beyond the entry at every X
                for (mode, off) in COMBOS:
                    tr = CE.resolve_entry(px, c, base, tick, tick_usd, cost_tk,
                                          mode, off, STALE, di[day], b0, r, g=g_x)
                    if not tr:
                        continue
                    k = len(tr)
                    blk = {"x": np.full(k, xv), "mode": np.full(k, mode, dtype=object),
                           "off": np.full(k, off), "day": np.full(k, day, dtype=object),
                           "root": np.array([z["root"] for z in tr], dtype=object),
                           "filled": np.array([z["filled"] for z in tr], float)}
                    for fld in ("kind", "gross", "cost", "tgt_usd"):
                        blk[fld] = np.array([z.get(fld, np.nan) for z in tr], float)
                    for kk in FEATS4:
                        blk[kk] = (feat[kk][:k] if len(feat[kk]) >= k
                                   else np.full(k, np.nan))
                    rows.append(blk)
    cols = rows[0].keys()
    df = pd.DataFrame({cc: np.concatenate([b[cc] for b in rows]) for cc in cols})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE)
    P(f"cached {len(df):,} rows ({int(df['filled'].sum()):,} filled) -> {CACHE}")


def run():
    if not CACHE.exists():
        P(f"no cache at {CACHE}; run --build first")
        return
    d = pd.read_parquet(CACHE)
    tr = d[d["day"] < SPLIT]
    te = d[d["day"] >= SPLIT].copy()
    zt, ze = [], []
    for k in FEATS4:
        mu, sd = np.nanmean(tr[k]), np.nanstd(tr[k])
        zt.append(((tr[k] - mu) / sd).to_numpy(float))
        ze.append(((te[k] - mu) / sd).to_numpy(float))
    cut = float(np.nanpercentile(np.nanmean(np.vstack(zt), axis=0), 50))
    te["hi_f"] = np.nanmean(np.vstack(ze), axis=0) <= cut

    P("DEPTH x CONFIRMATION SWEEP -- does a deeper extreme decouple hit rate from payoff?")
    P(f"  corrected chain; LATE half; out of time; stale 10 bars; STOP = X + {STOP_BEYOND} sigma")
    P("")
    P("  PREDICTION ON RECORD: hit x payoff on GROSS stays flat (conservation intact) while")
    P("  cost/payoff FALLS with depth, so net improves by cost amortisation rather than by")
    P("  decoupling. If hit x payoff RISES with X, the principal is right.")
    P("")
    for uni, label in ((None, "ALL ROOTS"), (list(MICRO), "MICRO (tradeable)")):
        sub = te if uni is None else te[te["root"].isin(uni)]
        P("=" * 124)
        P(f"{label}")
        P("")
        P("    mode          off    X   signals  FILL%      n   P(tgt)  win%   meanWin  meanLoss"
          "  payoff  HITxPAY  cost/pay   gross$    net$")
        for (mode, off) in COMBOS:
            for xv in XS:
                m = ((sub["mode"] == mode) & np.isclose(sub["off"], off)
                     & np.isclose(sub["x"], xv))
                g = sub[m]
                if len(g) < 200:
                    continue
                fl = g[g["filled"] > 0.5]
                if len(fl) < 100:
                    P(f"    {mode:<13} {off:.2f} {xv:>4.1f} {len(g):>8,} "
                      f"{g['filled'].mean():>6.1%}   too few fills")
                    continue
                gr = fl["gross"].to_numpy(float)
                ct = fl["cost"].to_numpy(float)
                net = gr - ct
                w, l = gr[gr > 0], gr[gr <= 0]
                pay = (w.mean() / abs(l.mean())) if len(l) and l.mean() != 0 else np.nan
                hit = float((gr > 0).mean())
                cp = float(ct.mean() / fl["tgt_usd"].mean())
                P(f"    {mode:<13} {off:.2f} {xv:>4.1f} {len(g):>8,} "
                  f"{g['filled'].mean():>6.1%} {len(fl):>6,} "
                  f"{(fl['kind'] == 0).mean():>7.1%} {hit:>5.1%} {w.mean():>+9.2f} "
                  f"{l.mean():>+9.2f} {pay:>7.2f} {hit*pay:>8.3f} {cp:>9.1%} "
                  f"{gr.mean():>+8.2f} {net.mean():>+7.2f}")
            P("")
        # the conservation test, isolated
        P("    CONSERVATION TEST -- hit x payoff on GROSS across depth, per mode")
        for (mode, off) in COMBOS:
            vals = []
            for xv in XS:
                m = ((sub["mode"] == mode) & np.isclose(sub["off"], off)
                     & np.isclose(sub["x"], xv) & (sub["filled"] > 0.5))
                gr = sub.loc[m, "gross"].to_numpy(float)
                if len(gr) < 100:
                    vals.append(np.nan)
                    continue
                w, l = gr[gr > 0], gr[gr <= 0]
                pay = (w.mean() / abs(l.mean())) if len(l) and l.mean() != 0 else np.nan
                vals.append(float((gr > 0).mean()) * pay)
            fin = [v for v in vals if np.isfinite(v)]
            rng_ = (max(fin) / min(fin)) if len(fin) > 1 and min(fin) > 0 else np.nan
            P(f"      {mode:<13} {off:.2f}  " + "  ".join(
                f"X={x:.1f}: {v:.3f}" if np.isfinite(v) else f"X={x:.1f}:  --"
                for x, v in zip(XS, vals)) + f"   | max/min {rng_:.2f}x")
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
