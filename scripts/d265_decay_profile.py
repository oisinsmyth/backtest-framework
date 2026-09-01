"""D265 PRE-SCREEN -- the decay profile of the intraday short edge.

    uv run python scripts/d265_decay_profile.py

THE BAR IS STATED HERE, BEFORE THE MEASUREMENT, and it is derived not chosen.

For an enter-once / hold-H-bars / exit construction with N trades per year:

    cost_pa   = 2N * c
    gross_pa  = (N * H / PPY) * edge_pa

Setting them equal, N CANCELS -- the number of trades is irrelevant -- and so do
H and PPY once `edge_pa` is written as `mean_cumulative(H) / H * PPY`:

    ===========================================================
      mean cumulative move per trade  >=  2c   (round-trip cost)
    ===========================================================

**Each trade must move further than it costs to trade.** Nothing else. The bar is
therefore SIGNAL-INDEPENDENT and equal to:

    HIGH names   2 x 6.42 bp  =  12.84 bp
    LOW names    2 x 2.00 bp  =   4.00 bp
    ALL          2 x 4.21 bp  =   8.42 bp

and the signal is the entire numerator.

WHAT THIS SETTLES
------------------
The principal's construction is a short held AT MOST 4 HOURS (16 bars) with
trailing stops and a take-profit. The turnover arithmetic says a SHORTER hold
raises the required per-bar edge, because a round trip costs 2c however long it
is held. So a 16-bar cap can only beat holding to the close if the edge is
FRONT-LOADED.

DECLARED BEFORE THE RUN, so it cannot be reinterpreted afterwards:

  * For a 16-bar cap to beat hold-to-close, the mean cumulative move at bar 16
    must be at least as large as at bar 26. Equivalently: the profile must be
    FLAT OR FALLING after bar 16.
  * For ANY hold to pay, the profile must cross 2c somewhere.
  * If the profile rises monotonically to bar 26, the principal's tight-management
    version is STRICTLY WORSE than simply holding to the close, and stops can only
    subtract.

NO BOOK IS SCORED. This measures the forward path after an entry the committed
books already generate. R9 is satisfied structurally: `hold_book` applies lag=1,
so an entry at bar t was decided on t-1's close, and the forward window starts at
t. Nothing here reads a bar the rule could not have seen.

R10 CAVEAT, stated rather than discovered: these trades are NOT independent. The
signal synchronises across names, so the entry count is not a sample size. The
dispersion columns are reported for shape, never as a standard error.
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


R = _load("d264", "run_single_name_intraday.py")
D, M = R.D, R.M

OUT = REPO / "data" / "d265_decay_profile.json"
MAX_H = 26          # one full session; the book is intraday-flat so it cannot exceed this
CAP_4H = 16         # the principal's proposed cap, 4 hours at 15 minutes


def profile(pos, rets, first, start):
    """Mean cumulative SHORT P&L after each entry, by bars held.

    Truncated at the session close, because the construction under test is
    intraday-flat and cannot hold past it. A trade entered late in the session
    contributes only the bars that actually exist before the close, so the
    columns thin out to the right and `n` is reported per column."""
    n_sym, T = pos.shape
    sess_end = np.empty(T, dtype=int)
    starts = list(np.flatnonzero(first)) + [T]
    for a, b in zip(starts[:-1], starts[1:]):
        sess_end[a:b] = b
    cum = [[] for _ in range(MAX_H)]
    for i in range(n_sym):
        p = pos[i]
        entries = np.flatnonzero((p[start:] != 0.0) & (p[start - 1:-1] == 0.0)) + start
        for t in entries:
            end = min(sess_end[t], t + MAX_H)
            run = np.cumsum(rets[i, t:end])
            for h in range(len(run)):
                cum[h].append(-run[h])       # SHORT: profit when the price falls
    return cum


def main() -> int:
    raw_panel, raw_cleaned = R.load_full()
    panel_all, cleaned_all = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _ = D.session_structure(panel_all.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    out = {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel_all, cleaned_all) if st == "ALL"
                 else R.subset(raw_panel, raw_cleaned, R.STRATA[st]))
        books = R.build_books(p, cl, start, first)
        c_bps = float(np.mean(p.cost_fraction) * 1e4)
        bar = 2.0 * c_bps                      # the round-trip cost, in bp
        rets = p.total_log_returns
        print("=" * 74)
        print(f"{st}   round-trip cost 2c = {bar:.2f} bp   "
              f"-- THE BAR, and it is signal-independent")
        print("=" * 74)
        for arm in ("S1_short_intra", "S2_short_intra"):
            cum = profile(books[arm], rets, first, start)
            rows = []
            print(f"\n  {arm}")
            print(f"    {'bars':>4s} {'hrs':>5s} {'n':>7s} {'mean bp':>9s} "
                  f"{'median bp':>10s} {'vs 2c':>8s}  {'win%':>6s}")
            for h in range(MAX_H):
                v = np.array(cum[h])
                if v.size == 0:
                    continue
                mean_bp = float(v.mean()) * 1e4
                rows.append({"bars": h + 1, "n": int(v.size), "mean_bp": mean_bp,
                             "median_bp": float(np.median(v)) * 1e4,
                             "win_rate": float((v > 0).mean())})
                if (h + 1) in (1, 2, 4, 8, 12, CAP_4H, 20, 24, MAX_H):
                    print(f"    {h + 1:4d} {(h + 1) * 0.25:5.2f} {v.size:7,d} "
                          f"{mean_bp:8.2f}b {float(np.median(v)) * 1e4:9.2f}b "
                          f"{mean_bp / bar:7.2f}x {float((v > 0).mean()) * 100:5.1f}%")
            m16 = next((r["mean_bp"] for r in rows if r["bars"] == CAP_4H), None)
            m26 = next((r["mean_bp"] for r in rows if r["bars"] == MAX_H), None)
            peak = max(rows, key=lambda r: r["mean_bp"])
            print(f"    peak at bar {peak['bars']} ({peak['bars'] * 0.25:.2f}h): "
                  f"{peak['mean_bp']:.2f} bp = {peak['mean_bp'] / bar:.2f}x the bar")
            if m16 is not None and m26 is not None:
                verdict = ("FRONT-LOADED: the 4h cap beats hold-to-close"
                           if m16 >= m26 else
                           "NOT front-loaded: holding to the close is strictly better")
                print(f"    bar 16 {m16:.2f} bp vs bar 26 {m26:.2f} bp  ->  {verdict}")
            print(f"    CROSSES THE BAR: "
                  + ("yes, at bar "
                     + str(next(r['bars'] for r in rows if r['mean_bp'] >= bar))
                     if any(r["mean_bp"] >= bar for r in rows) else "NO -- at no holding period"))
            out[f"{st}:{arm}"] = {"round_trip_cost_bp": bar, "profile": rows,
                                  "mean_bp_at_16": m16, "mean_bp_at_26": m26,
                                  "peak": peak}
        print()

    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
