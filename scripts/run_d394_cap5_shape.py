"""D394 -- the distribution SHAPE of the cap-5 trade returns, with no exit rule at all.

    uv run python scripts/run_d394_cap5_shape.py

DESCRIPTIVE. No null, no hurdle, nothing admitted (R15). One cell: E1 on `up_run_21`, LONG,
cap 5, every event taken, hedged, next-open fill -- the lowest hold in the pre-registered grid,
and the plain "buy, hold a week, sell" ledger with nothing layered on it.

WHY THIS EXISTS. D394 showed no stop, target or trail closes the cost gap on the low hold. The
question underneath is what shape the raw distribution has, because that is what any exit rule is
trying to reshape -- and CLAUDE.md's reporting group 2 asks for it directly: count, mean, MEDIAN,
win rate, payoff, skew, kurtosis, and the mean after trimming 1% from BOTH tails, all three
reported.

THE TRIM IS SYMMETRIC AND THAT IS THE POINT. Dropping only winners always frightens on a two-sided
fat-tailed book -- D307 called four cells lottery books on exactly that mistake. Ex-top, ex-bottom
and both are reported side by side so the asymmetry is visible rather than asserted.

D322: the top trade is NAMED and its bar printed, not quoted as a share.
"""

from __future__ import annotations

import gc
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _rss():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:
        return float("nan")


OUT = REPO / "data" / "d394_cap5_shape.json"
CAP = 5
SHAPE = "E1"
CANDIDATE = "up_run_21"


def main() -> int:
    t0 = time.time()
    R = _load("d393b", "run_d393_bs_null.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    V47 = PREP.V47

    P, elig, cols, masks, dec, T, n, bucket, elig_b = R.build(PREP, V50, SG)
    col = cols[CANDIDATE]
    pct = V47.percentile_grid(col)
    mask = V50.shape_masks(pct, elig)[SHAPE][0]
    sc = np.where(np.isfinite(col), col, 50.0)
    del cols, masks, dec, bucket, elig_b, pct
    gc.collect()
    print(f"  build {time.time() - t0:.0f}s, RSS {_rss():.2f} GB", flush=True)

    res = V59.run_mirror(P, mask, sc, "cap", CAP)
    p = np.asarray(V47.pnl_bp(res), float)
    tr = res["trades"]
    N = p.size
    tb = V59.trade_block(P, res, elig, 0, False)

    # ---- shape ----------------------------------------------------------
    sd = float(p.std(ddof=1))
    win = p > 0
    avg_win = float(p[win].mean())
    avg_loss = float(p[~win].mean())
    lo1, hi1 = np.percentile(p, 1), np.percentile(p, 99)
    qs = [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
    pct_tab = {str(q): float(np.percentile(p, q)) for q in qs}

    order = np.argsort(p)[::-1]                    # best first
    tot = float(p.sum())

    def share_top(k):
        return float(p[order[:k]].sum() / tot) if tot else float("nan")

    def share_bot(k):
        return float(p[order[-k:]].sum() / tot) if tot else float("nan")

    # trades to half the P&L, counted from the best down (the concentration statistic)
    csum = np.cumsum(p[order])
    to_half = int(np.searchsorted(csum, 0.5 * tot) + 1) if tot > 0 else None

    # per-NAME concentration
    rows = np.array([t[0] for t in tr])
    uniq, inv = np.unique(rows, return_inverse=True)
    per_name = np.bincount(inv, weights=p)
    nord = np.argsort(per_name)[::-1]
    ncsum = np.cumsum(per_name[nord])
    names_to_half = int(np.searchsorted(ncsum, 0.5 * tot) + 1) if tot > 0 else None

    k = int(np.argmax(p))
    top = dict(symbol=str(P["symbols"][tr[k][0]]), entry_bar=int(tr[k][1]),
               entry_date=str(P["dates"][tr[k][1]]), held=int(tr[k][2]),
               pnl_bp=float(p[k]), share_of_total=float(p[k] / tot) if tot else None)
    kk = int(np.argmin(p))
    bot = dict(symbol=str(P["symbols"][tr[kk][0]]), entry_bar=int(tr[kk][1]),
               entry_date=str(P["dates"][tr[kk][1]]), held=int(tr[kk][2]),
               pnl_bp=float(p[kk]), share_of_total=float(p[kk] / tot) if tot else None)

    shape = dict(
        n=N, mean_bp=float(p.mean()), median_bp=float(np.median(p)), std_bp=sd,
        t=float(p.mean() / (sd / np.sqrt(N))),
        win_rate=float(win.mean()), avg_win_bp=avg_win, avg_loss_bp=avg_loss,
        payoff=float(avg_win / abs(avg_loss)) if avg_loss else None,
        expectancy_check=float(win.mean() * avg_win + (1 - win.mean()) * avg_loss),
        skew=float(((p - p.mean()) ** 3).mean() / sd ** 3),
        excess_kurtosis=float(((p - p.mean()) ** 4).mean() / sd ** 4 - 3.0),
        min_bp=float(p.min()), max_bp=float(p.max()), percentiles=pct_tab,
        trim_ex_top_bp=float(p[p <= hi1].mean()),
        trim_ex_bottom_bp=float(p[p >= lo1].mean()),
        trim_both_bp=float(p[(p >= lo1) & (p <= hi1)].mean()),
        pnl_share_top_1pct=share_top(max(1, N // 100)),
        pnl_share_top_5pct=share_top(max(1, N // 20)),
        pnl_share_top_10pct=share_top(max(1, N // 10)),
        pnl_share_bottom_1pct=share_bot(max(1, N // 100)),
        trades_to_half_pnl=to_half, trades_to_half_share=to_half / N if to_half else None,
        names=int(uniq.size), names_to_half_pnl=names_to_half,
        hold_mean=tb["hold_mean"], round_trip=tb["two_c"]["PUB"],
        net_bp=tb["net_per_trade"]["PUB"], top_trade=top, worst_trade=bot)

    payload = dict(study=394, stage="cap5_shape", cell=f"{SHAPE}/cap{CAP}", score=CANDIDATE,
                   purpose="Distribution shape of the cap-5 ledger with NO exit rule. "
                           "Descriptive; no null, nothing admitted (R15).",
                   shape=shape,
                   deciles=[float(x) for x in np.percentile(p, np.arange(0, 101, 10))])
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    s = shape
    print(f"\nE1 / cap {CAP} -- the plain 'buy, hold a week, sell' ledger, NO exit rule\n")
    print(f"  trades {s['n']:,} over {s['names']:,} names   hold {s['hold_mean']:.1f} bars")
    print(f"  mean   {s['mean_bp']:+8.2f} bp      median {s['median_bp']:+8.2f} bp"
          f"      {'MEAN ABOVE MEDIAN' if s['mean_bp'] > s['median_bp'] else 'MEAN BELOW MEDIAN'}")
    print(f"  std    {s['std_bp']:8.2f} bp      t      {s['t']:+8.2f}")
    print(f"  win    {100 * s['win_rate']:7.2f}%        avg win {s['avg_win_bp']:+8.2f}  "
          f"avg loss {s['avg_loss_bp']:+8.2f}   payoff {s['payoff']:.3f}")
    print(f"  skew   {s['skew']:+8.2f}         excess kurtosis {s['excess_kurtosis']:+8.1f}")
    print(f"\n  PERCENTILES (bp)")
    print("    " + "  ".join(f"{q:>7s}" for q in s["percentiles"]))
    print("    " + "  ".join(f"{v:>7.0f}" for v in s["percentiles"].values()))
    print(f"    min {s['min_bp']:+,.0f}   max {s['max_bp']:+,.0f}")
    print(f"\n  TRIMS (CLAUDE.md group 2 -- all three, because dropping only winners always "
          f"frightens)")
    print(f"    ex-top 1% {s['trim_ex_top_bp']:+8.2f}   ex-bottom 1% "
          f"{s['trim_ex_bottom_bp']:+8.2f}   BOTH {s['trim_both_bp']:+8.2f}")
    print(f"\n  CONCENTRATION")
    print(f"    top 1% of trades carry {100 * s['pnl_share_top_1pct']:6.1f}% of P&L")
    print(f"    top 5%                 {100 * s['pnl_share_top_5pct']:6.1f}%")
    print(f"    top 10%                {100 * s['pnl_share_top_10pct']:6.1f}%")
    print(f"    bottom 1%              {100 * s['pnl_share_bottom_1pct']:6.1f}%")
    print(f"    {s['trades_to_half_pnl']:,} trades ({100 * s['trades_to_half_share']:.2f}%) "
          f"reach half the P&L; {s['names_to_half_pnl']:,} names of {s['names']:,}")
    print(f"\n    TOP  {top['symbol']} entered {top['entry_date']} (bar {top['entry_bar']}), "
          f"held {top['held']}, {top['pnl_bp']:+,.0f} bp = "
          f"{100 * (top['share_of_total'] or 0):.2f}% of the ledger")
    print(f"    WORST {bot['symbol']} entered {bot['entry_date']} (bar {bot['entry_bar']}), "
          f"held {bot['held']}, {bot['pnl_bp']:+,.0f} bp")
    print(f"\n  COST  round trip {s['round_trip']:.2f} bp -> net {s['net_bp']:+.2f} bp/trade")
    print(f"\n  ({time.time() - t0:.0f}s)  Descriptive. No null, nothing admitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
