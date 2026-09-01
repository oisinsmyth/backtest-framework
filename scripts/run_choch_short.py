"""D275 -- the change of character as a short, on single names at fifteen minutes.
Pre-registered in `docs/decisions/D275-the-change-of-character-on-single-names.md`,
commit 0b39133, BEFORE this file was written.

    uv run python scripts/run_choch_short.py

ONE RULE, NOTHING STACKED. `market_structure(bars, k=2)` -- the structure
programme's own PRIMARY_K -- short while the trend is DOWN, flat at every session
open, lag 1. No flipped level, no Fibonacci, no fair-value gap, no RSI: D211
measured that stacking those four makes the arm WORSE before costs.

Long controls are included because D247's design requires them -- without them a
short failure cannot be attributed to direction rather than to 15-minute sampling
breaking the estimator.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research.structure import Trend, market_structure  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


A = _load("d271", "d271_trade_anatomy.py")
R, M, D = A.R, A.M, A.D
X, J = R.X, R.J

OUT = REPO / "data" / "d275_choch_summary.json"
K = 2                     # the structure programme's PRIMARY_K, unvaried
N_SIMS, N_BOOT, SEED = 1000, 1000, 0
CELLS = ("choch_short", "choch_long")


def choch_books(panel, cleaned, first, start):
    """position = -1 while trend is DOWN (+1 while UP for the control), flat at
    every session open, lag 1."""
    n, T = panel.closes.shape
    short = np.zeros((n, T))
    long_ = np.zeros((n, T))
    legs = []
    for i, sym in enumerate(panel.symbols):
        bars = cleaned[sym]
        states = market_structure(bars, K)
        d = np.array([1.0 if s.trend is Trend.DOWN else 0.0 for s in states])
        u = np.array([1.0 if s.trend is Trend.UP else 0.0 for s in states])
        short[i, 1:] = -d[:-1]          # lag 1: the state at t-1 decides t
        long_[i, 1:] = u[:-1]
        for s in states:
            if s.leg is not None and s.leg.span < 0:
                legs.append(abs(s.leg.span) / s.leg.start_price)
    for b in (short, long_):
        b[:, :start] = 0.0
        b[:, first] = 0.0               # intraday-only: flat at every session open
    return {"choch_short": short, "choch_long": long_}, np.array(legs)


def per_trade(pos, rets, start, sess_end):
    out = []
    for i in range(pos.shape[0]):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        for t in ent:
            close = int(sess_end[t])
            z = np.flatnonzero(s[t:close] == 0.0)
            ex = t + int(z[0]) if z.size else close
            if ex > t:
                out.append(float(np.sign(s[t]) * rets[i, t:ex].sum()) * 1e4)
    return np.array(out)


def main() -> int:
    rp, rc = R.load_full()
    panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
    first, gap = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel.closes.shape[1]
    ppy = (T / int(first.sum())) * 252.0
    sess_end, _ = A.session_maps(first, T)

    payload, per_cell = {}, {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel, cleaned) if st == "ALL" else R.subset(rp, rc, R.STRATA[st]))
        books, legs = choch_books(p, cl, first, start)
        borrow = R.borrow_vector(p.symbols)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        print("=" * 92)
        print(f"{st}   cost bar 2c = {c2:.2f} bp   {len(p.symbols)} symbols")
        print("=" * 92)
        if st == "ALL":
            print(f"  LEG DIAGNOSTIC (not hurdled): {len(legs):,} down-legs, "
                  f"median {np.median(legs) * 1e4:.1f} bp, mean {legs.mean() * 1e4:.1f} bp, "
                  f"share over 2c {np.mean(legs * 1e4 > c2):.1%}")
            payload["leg_diagnostic"] = {
                "n": len(legs), "median_bp": float(np.median(legs) * 1e4),
                "mean_bp": float(legs.mean() * 1e4),
                "share_over_2c": float(np.mean(legs * 1e4 > c2))}
        for k in CELLS:
            sc = R.score(p, books[k], start, first, gap, ppy, borrow)
            tr = per_trade(books[k], p.total_log_returns, start, sess_end)
            mean_bp = float(tr.mean()) if tr.size else 0.0
            key = f"{st}:{k}"
            per_cell[key] = (p, books[k], borrow)
            payload[key] = {**sc, "cost_bar_bp": c2, "n_trades": int(tr.size),
                            "mean_move_bp": mean_bp,
                            "Z1": bool(mean_bp >= c2), "Z3": bool(sc["cagr"] > 0)}
            print(f"  {k:12s} exposure {sc['exposure']:5.1%}  CAGR {sc['cagr']:+7.2%}  "
                  f"SR {sc['excess_sharpe']:+6.3f}  turn {sc['turnover_per_year']:4.0f}  "
                  f"{tr.size:6,d} trades  move {mean_bp:+6.2f}b  "
                  f"Z1 {'YES' if mean_bp >= c2 else 'no':>3s}  "
                  f"Z3 {'YES' if sc['cagr'] > 0 else 'no':>3s}")
        print()

    # ---- Z2: rotation null, both legs, one shared offset per sim (D228) ----
    print("rotation nulls (both legs, shared offsets) ...", flush=True)
    rng = np.random.default_rng(SEED)
    keys = list(per_cell)
    per_s = {k: np.empty(N_SIMS) for k in keys}
    per_m = {k: np.empty(N_SIMS) for k in keys}
    best = np.empty(N_SIMS)
    for s in range(N_SIMS):
        off8 = rng.integers(1, T - start, size=len(panel.symbols))
        vals = []
        for k in keys:
            p, book, borrow = per_cell[k]
            idx = [panel.symbols.index(x) for x in p.symbols]
            rot = np.zeros_like(book)
            for i, j in enumerate(idx):
                rot[i, start:] = np.roll(book[i, start:], int(off8[j]))
            tot = X.signed_log_returns(p, rot, total_return=True)[start:]
            ex, _ = R.excess_vec(tot, rot, start, first, gap, ppy, borrow)
            per_s[k][s] = R._sharpe(ex, ppy)
            per_m[k][s] = float(np.sum(tot))
            vals.append(per_s[k][s])
        best[s] = max(vals)
        if (s + 1) % 250 == 0:
            print(f"  {s + 1}/{N_SIMS}", flush=True)
    floor = float(np.percentile(best, 95))

    # ---- Z4: bootstrap ----
    rb = np.random.default_rng(SEED)
    nlen, blk = T - start, J.BLOCK
    idxs = [(rb.integers(0, nlen - blk + 1, size=math.ceil(nlen / blk))[:, None]
             + np.arange(blk)[None, :]).ravel()[:nlen] for _ in range(N_BOOT)]

    print(f"\nbest-of-{len(keys)} floor: {floor:+.3f}\n")
    print(f"  {'cell':22s} {'move':>8s} {'Z1':>4s} {'SR pct':>7s} {'$ pct':>7s} {'Z2':>4s} "
          f"{'Z3':>4s} {'Z4':>4s} {'Z5':>4s}  ALL FIVE")
    surv = []
    for k in keys:
        p, book, borrow = per_cell[k]
        a_s = payload[k]["excess_sharpe"]
        tot = X.signed_log_returns(p, book, total_return=True)[start:]
        a_m = float(np.sum(tot))
        ex, _ = R.excess_vec(tot, book, start, first, gap, ppy, borrow)
        boot = np.array([R._sharpe(ex[i], ppy) for i in idxs])
        z2 = bool(a_s > np.percentile(per_s[k], 95) and a_m > np.percentile(per_m[k], 95))
        z4 = bool(np.percentile(boot, 5) > 0.0)
        z5 = bool(a_s > floor)
        payload[k].update(
            sharpe_pct=float((per_s[k] < a_s).mean() * 100),
            money_pct=float((per_m[k] < a_m).mean() * 100),
            Z2=z2, Z4=z4, Z5=z5, boot_p05=float(np.percentile(boot, 5)))
        allz = all(payload[k][x] for x in ("Z1", "Z2", "Z3", "Z4", "Z5"))
        payload[k]["clears_all"] = allz
        if allz and "short" in k:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:22s} {payload[k]['mean_move_bp']:+7.2f}b {y(payload[k]['Z1']):>4s} "
              f"{payload[k]['sharpe_pct']:6.1f}th {payload[k]['money_pct']:6.1f}th "
              f"{y(z2):>4s} {y(payload[k]['Z3']):>4s} {y(z4):>4s} {y(z5):>4s}  "
              f"{'** YES **' if allz else 'no'}")

    payload["best_of_floor"] = floor
    payload["survivors"] = surv
    print(f"\n  SURVIVORS (short cells clearing all five): {surv or 'NONE'}")
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
