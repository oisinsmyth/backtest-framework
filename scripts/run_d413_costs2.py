"""D413 COSTS, TAKE TWO -- the first cost estimate was measured on the wrong bars.

    uv run python scripts/run_d413_costs2.py --run

EXPLORATORY. Clears nothing, admits nothing, changes no verdict.

WHY THIS EXISTS. run_d413_costs.py charged Corwin-Schultz measured AT THE ENTRY AND EXIT BARS. Two
things are wrong with that and the principal's question about a price floor is what exposed them:

  1. CORWIN-SCHULTZ CANNOT SEPARATE SPREAD FROM INTRADAY RANGE. It infers the spread from high/low
     ranges over bar pairs, so a volatile bar reads as a wide spread whether or not the quote was
     wide.
  2. THE EVENT BARS ARE SELECTED FOR BEING VOLATILE. An entry happens exactly when price has just
     travelled back into a zone -- the most active bars in the sample. Estimating the spread there
     and nowhere else is estimating it on the worst possible subsample.

The tell was in the by-price table: cost was 101 bp in the cheapest quintile and then FLATTENED at
about 70 and ROSE again at $149. Proportional spread should fall roughly with 1/price. A flat
profile in price is a signature of an estimator reading volatility, not spread.

THIS FILE MEASURES BOTH, side by side, and neither is chosen for the reader:
  event   -- Corwin-Schultz at the entry/exit bars           (take one; upward biased by selection)
  neutral -- the name's MEDIAN Corwin-Schultz over the 60 bars ending 2 bars BEFORE entry,
             which is causal, unselected, and robust to the single-bar noise CS is famous for.

Real spreads DO widen on active days, so the truth is between them -- and both are reported for
every floor tested, so a floor cannot be judged on whichever estimate flatters it.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413", REPO / "scripts" / "run_d413_distance_armed_zones.py")
M = importlib.util.module_from_spec(_s)
sys.modules["d413"] = M
_s.loader.exec_module(M)
Z4, D = M.Z4, M.D
_c = importlib.util.spec_from_file_location("d285cs", REPO / "scripts" / "d285_spread_estimate.py")
CS = importlib.util.module_from_spec(_c)
sys.modules["d285cs"] = CS
_c.loader.exec_module(CS)

OUT = REPO / "data" / "d413_costs2.json"
IBKR = 0.0035
NEUTRAL_W, NEUTRAL_GAP = 60, 2


def _dv_trailing(P):
    """The SAME trailing dollar-volume the universe floor itself uses (D320's roll_mean_T), so a
    raised floor here is the same kind of object as the floor already in force."""
    return D.X.roll_mean_T(P["CL"] * P["VOL"])


def rolling_median(S, w, gap):
    """Median of S over the w bars ending `gap` bars before t. Causal, and it never reads the
    event bar -- which is the whole point of this file."""
    T, n = S.shape
    out = np.full((T, n), np.nan)
    for t in range(w + gap, T):
        blk = S[t - w - gap:t - gap]
        with np.errstate(invalid="ignore"):
            out[t] = np.nanmedian(blk, axis=0)
    return out


def run():
    t0 = time.time()
    print("D413 COSTS TAKE TWO -- event-bar vs neutral-window spread\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g, tt = A["Z"], A["good"], A["tt"]

    spread = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T).T
    print(f"  building the neutral {NEUTRAL_W}-bar trailing median spread ...", flush=True)
    neutral = rolling_median(spread, NEUTRAL_W, NEUTRAL_GAP)

    r = A["r"][g]
    ii = Z["i"][g]
    te = tt[g]
    tx = np.minimum(te + M.H, P["CL"].shape[0] - 1)
    px = P["CL"][te, ii]
    # TRAILING dollar volume, not the entry bar's own. An entry happens on an active day by
    # construction, so a floor built on the event bar's volume is partly selecting on the event's
    # own spike -- a liquidity floor has to be a property of the name BEFORE the event.
    dv = _dv_trailing(P)[te, ii]

    s_ev = 0.5 * spread[te, ii] + 0.5 * spread[tx, ii]
    s_nt = 0.5 * neutral[te, ii] + 0.5 * neutral[tx, ii]
    comm = IBKR / px + IBKR / np.maximum(P["CL"][tx, ii], 1e-9)
    ok = np.isfinite(s_ev) & np.isfinite(s_nt) & np.isfinite(px) & (px > 0) & np.isfinite(dv)
    r, px, dv, s_ev, s_nt, comm = r[ok], px[ok], dv[ok], s_ev[ok], s_nt[ok], comm[ok]
    print(f"  events with BOTH estimates: {r.size:,}\n")

    print("  --- the tell: round-trip spread by price quintile, both estimates ---")
    q = np.quantile(px, np.linspace(0, 1, 6)); q[-1] += 1e-9
    b = np.clip(np.searchsorted(q, px, side="right") - 1, 0, 4)
    by_px = []
    for j in range(5):
        m = b == j
        row = dict(price=float(np.median(px[m])), n=int(m.sum()),
                   event=float(1e4 * np.median(s_ev[m])),
                   neutral=float(1e4 * np.median(s_nt[m])),
                   gross=float(1e4 * r[m].mean()))
        by_px.append(row)
        print(f"  ${row['price']:6.1f}  n {row['n']:7,}   event {row['event']:7.1f} bp   "
              f"neutral {row['neutral']:6.1f} bp   ratio {row['event']/max(row['neutral'],1e-9):.2f}x"
              f"   gross {row['gross']:+7.2f}")
    print("  -> a NEUTRAL estimate that falls with price is the shape a spread should have;")
    print("     a flat/rising EVENT estimate is the estimator reading the event's own volatility.")

    def block(mask, tag):
        if mask.sum() < 2000:
            return None
        gm = 1e4 * r[mask].mean()
        se = 1e4 * r[mask].std(ddof=1) / np.sqrt(mask.sum())
        ce = 1e4 * (s_ev[mask] + comm[mask]).mean()
        cn = 1e4 * (s_nt[mask] + comm[mask]).mean()
        cn_med = 1e4 * np.median(s_nt[mask] + comm[mask])
        row = dict(tag=tag, n=int(mask.sum()), gross=float(gm), se=float(se),
                   cost_event=float(ce), cost_neutral=float(cn), cost_neutral_med=float(cn_med),
                   net_event=float(gm - ce), net_neutral=float(gm - cn),
                   cov_event=float(gm / ce), cov_neutral=float(gm / cn),
                   cov_neutral_med=float(gm / cn_med))
        print(f"  {tag:34s} n {row['n']:7,}  gross {gm:+6.2f}+-{se:.2f}  "
              f"cost_ev {ce:6.1f}  cost_nt {cn:6.1f} (med {cn_med:5.1f})  "
              f"cov {row['cov_event']:.2f}x / {row['cov_neutral']:.2f}x / "
              f"{row['cov_neutral_med']:.2f}x")
        return row

    print("\n  --- RAISING THE FLOORS. coverage = gross/cost, shown event / neutral / neutral-median")
    rows = [block(np.ones(r.size, bool), "all (current floor)")]
    for p in (10, 20, 50, 100):
        rows.append(block(px >= p, f"price >= ${p}"))
    dvq = np.quantile(dv[np.isfinite(dv)], [.5, .75, .9])
    for lbl, thr in zip(("dollar-vol top 50%", "dollar-vol top 25%", "dollar-vol top 10%"), dvq):
        rows.append(block(dv >= thr, lbl))
    rows.append(block((px >= 20) & (dv >= dvq[1]), "price >= $20 AND dv top 25%"))
    rows.append(block((px >= 50) & (dv >= dvq[2]), "price >= $50 AND dv top 10%"))

    best = max((x for x in rows if x), key=lambda x: x["cov_neutral"])
    print(f"\n  best coverage on the neutral estimate: {best['tag']}  "
          f"{best['cov_neutral']:.2f}x  (net {best['net_neutral']:+.2f} bp)")

    OUT.write_text(json.dumps(dict(exploratory=True, by_price=by_px,
                                   floors=[x for x in rows if x],
                                   neutral_window=NEUTRAL_W, neutral_gap=NEUTRAL_GAP),
                              indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
