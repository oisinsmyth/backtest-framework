"""D265 -- the entry-time reconciliation. Pre-registered in
`docs/decisions/D265-the-entry-time-reconciliation.md`, commit 6b5f729, BEFORE
this file was written.

    uv run python scripts/run_entry_time_reconciliation.py

WHY: D264 scored LOW:S2_short_intra at -0.89% CAGR (linear gross +1.43%/yr); the
decay profile of the SAME entries shows +8.24 bp at bar 18 against a 4.00 bp
round-trip cost -- 2.06x. Both cannot be right about the same thing.

THE CLOCK IS ALREADY RULED OUT: a bar-of-day-matched control came back flat for
this cell. What is tested here is selection INTO the column (only 82% of trades
have 18 bars left before the close, and the missing ones are late entries), and
the second candidate cause, that the book's exits are signal-driven rather than
fixed-horizon.

  ARM A  P&L per trade from entry to the BOOK'S OWN exit
  ARM B  P&L per trade from entry to the SESSION CLOSE, fixed horizon

  BUCKETS, fixed in the pre-registration:  EARLY 1-8, MID 9-17, LATE 18-25
  (bar-of-day at entry; bar 0 cannot host an entry -- the book is flat at every
  session open and lag=1 pushes the earliest entry to bar 1)

THE VALIDATION GATE, and it is checked FIRST because it can void the whole run:
Arm A must rebuild D264's committed +1.43%/yr linear gross to within 0.30 points.
If it does not, no bucket table is interpreted.
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
D, M, X = R.D, R.M, R.X

OUT = REPO / "data" / "d265_entry_time_summary.json"
RESULTS = REPO / "ENTRY_TIME_RECONCILIATION.md"

STRATUM, ARM = "LOW", "S2_short_intra"
BUCKETS = (("EARLY", 1, 8), ("MID", 9, 17), ("LATE", 18, 25))
GATE_TARGET = 0.0143          # D264's committed gross_linear_pa for this cell
GATE_TOL = 0.0030             # +/- 0.30 percentage points
BARS_PER_SESSION = 26


def main() -> int:
    raw_panel, raw_cleaned = R.load_full()
    panel_all, cleaned_all = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _ = D.session_structure(panel_all.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    p, cl = R.subset(raw_panel, raw_cleaned, R.STRATA[STRATUM])
    books = R.build_books(p, cl, start, first)
    pos = books[ARM]
    rets = p.total_log_returns
    n_sym, T = pos.shape
    ppy = (T / int(first.sum())) * 252.0
    years = (T - start) / ppy
    c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)

    bod = np.empty(T, dtype=int)
    k = 0
    for t in range(T):
        k = 0 if first[t] else k + 1
        bod[t] = k
    starts = list(np.flatnonzero(first)) + [T]
    sess_end = np.empty(T, dtype=int)
    for a, b in zip(starts[:-1], starts[1:]):
        sess_end[a:b] = b

    trades = []
    for i in range(n_sym):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        for t in ent:
            close = int(sess_end[t])
            # ARM A: the book's own exit -- first bar at or after t where the
            # position returns to zero, capped at the session close.
            z = np.flatnonzero(s[t:close] == 0.0)
            exit_a = t + int(z[0]) if z.size else close
            trades.append({
                "symbol": p.symbols[i], "bod": int(bod[t]),
                "bars_a": exit_a - t, "bars_b": close - t,
                "pnl_a": -float(rets[i, t:exit_a].sum()),
                "pnl_b": -float(rets[i, t:close].sum()),
            })

    n = len(trades)
    pa = np.array([x["pnl_a"] for x in trades])
    pb = np.array([x["pnl_b"] for x in trades])
    bods = np.array([x["bod"] for x in trades])
    ba = np.array([x["bars_a"] for x in trades])
    bb = np.array([x["bars_b"] for x in trades])

    # ---- THE VALIDATION GATE, checked before anything else is read ----
    gross_a = float(pa.sum()) / n_sym / years
    gate_delta = gross_a - GATE_TARGET
    gate_pass = abs(gate_delta) <= GATE_TOL
    print("=" * 78)
    print("VALIDATION GATE G -- Arm A must rebuild D264's committed linear gross")
    print("=" * 78)
    print(f"  D264 gross_linear_pa (committed)   {GATE_TARGET:+.4%}")
    print(f"  Arm A rebuilt from {n:,} trades      {gross_a:+.4%}")
    print(f"  delta {gate_delta * 100:+.3f} pts   tolerance +/-{GATE_TOL * 100:.2f} pts")
    print(f"  GATE: {'PASS' if gate_pass else 'FAIL'}\n")
    if not gate_pass:
        print("  GATE FAILED. Per D265's stop, NO BUCKET TABLE IS INTERPRETED and the")
        print("  discrepancy is recorded as UNEXPLAINED. The decay profile's 2.06x is")
        print("  marked NOT UNDERSTOOD rather than quietly retained.")

    rows = []
    print(f"{'bucket':7s} {'bars':>7s} {'n':>6s} {'share':>7s} | "
          f"{'ARM A':>19s} | {'ARM B':>19s}")
    print(f"{'':7s} {'':>7s} {'':>6s} {'':>7s} | {'hold':>5s} {'bp/trade':>8s} "
          f"{'vs 2c':>4s} | {'hold':>5s} {'bp/trade':>8s} {'vs 2c':>4s}")
    for name, lo, hi in BUCKETS:
        m = (bods >= lo) & (bods <= hi)
        if not m.any():
            continue
        a_bp, b_bp = pa[m].mean() * 1e4, pb[m].mean() * 1e4
        rows.append({"bucket": name, "bars": [lo, hi], "n": int(m.sum()),
                     "share": float(m.mean()),
                     "arm_a_bp": float(a_bp), "arm_b_bp": float(b_bp),
                     "arm_a_hold": float(ba[m].mean()), "arm_b_hold": float(bb[m].mean()),
                     "arm_a_clears": bool(a_bp >= c2), "arm_b_clears": bool(b_bp >= c2),
                     "hit_a": float((pa[m] > 0).mean())})
        print(f"{name:7s} {f'{lo}-{hi}':>7s} {m.sum():6,d} {m.mean() * 100:6.1f}% | "
              f"{ba[m].mean():5.1f} {a_bp:7.2f}b {a_bp / c2:4.2f} | "
              f"{bb[m].mean():5.1f} {b_bp:7.2f}b {b_bp / c2:4.2f}")
    print(f"{'ALL':7s} {'1-25':>7s} {n:6,d} {100.0:6.1f}% | "
          f"{ba.mean():5.1f} {pa.mean() * 1e4:7.2f}b {pa.mean() * 1e4 / c2:4.2f} | "
          f"{bb.mean():5.1f} {pb.mean() * 1e4:7.2f}b {pb.mean() * 1e4 / c2:4.2f}")
    print(f"\n  round-trip cost 2c = {c2:.2f} bp")

    early = next(r for r in rows if r["bucket"] == "EARLY")
    late = next(r for r in rows if r["bucket"] == "LATE")
    arm_gap = float(pb.mean() - pa.mean()) * 1e4
    bucket_gap = early["arm_b_bp"] - late["arm_b_bp"]
    print("\n  P-1  EARLY > LATE           "
          f"A {early['arm_a_bp']:.2f} vs {late['arm_a_bp']:.2f}   "
          f"B {early['arm_b_bp']:.2f} vs {late['arm_b_bp']:.2f}   -> "
          + ("CONFIRMED" if early["arm_a_bp"] > late["arm_a_bp"]
             and early["arm_b_bp"] > late["arm_b_bp"] else "NOT CONFIRMED"))
    print(f"  P-2  all-bucket Arm A < 2c  {pa.mean() * 1e4:.2f} vs {c2:.2f}  -> "
          + ("CONFIRMED" if pa.mean() * 1e4 < c2 else "FALSIFIED"))
    print(f"  P-3  Arm B > Arm A          {pb.mean() * 1e4:.2f} vs {pa.mean() * 1e4:.2f}  -> "
          + ("CONFIRMED" if pb.mean() > pa.mean() else "FALSIFIED"))
    print(f"  P-4  ARM gap > BUCKET gap   arm {arm_gap:.2f} bp vs bucket {bucket_gap:.2f} bp  -> "
          + ("CONFIRMED" if abs(arm_gap) > abs(bucket_gap) else
             "FALSIFIED -- entry timing explains more, as the hypothesis said"))

    payload = {"preregistration": "docs/decisions/D265-the-entry-time-reconciliation.md",
               "commit": "6b5f729", "cell": f"{STRATUM}:{ARM}",
               "round_trip_cost_bp": c2, "n_trades": n, "years": years,
               "gate": {"target": GATE_TARGET, "rebuilt": gross_a,
                        "delta": gate_delta, "tolerance": GATE_TOL, "pass": gate_pass},
               "buckets": rows,
               "all": {"arm_a_bp": float(pa.mean() * 1e4), "arm_b_bp": float(pb.mean() * 1e4),
                       "arm_a_hold": float(ba.mean()), "arm_b_hold": float(bb.mean())},
               "arm_gap_bp": arm_gap, "bucket_gap_bp": bucket_gap}
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
