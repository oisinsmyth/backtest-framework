"""WHERE IN THE CLOCK does the admitted arm actually fill? And what does that do to its cost line?

working/arm_spread_at_entries.py measured MNQ's quoted spread at the arm's kind of moment and found
2.53 ticks against the 1.009 the cost line assumes -- but the damage depends on WHICH hours the arm
actually enters, because 10:00 reads 3.66 ticks and 12:00 reads 1.49.

The committed `simulate` returns only (pnl, trips), so the loop is re-implemented here with the fill
segments recorded. IT IS ASSERTED BIT-IDENTICAL to the committed function before its histogram is
believed -- the arm's own code is not touched.

    python working/arm_entry_hours.py
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


D491 = _load("d491e", "d491_conditional_hold.py")
ARM = _load("d504e", "d504_arm_full_history.py")

# measured at the arm's kind of moment, first 30s of the hour (working/arm_spread_at_entries.py)
SPREAD_AT = {10: 3.66, 11: 1.79, 12: 1.49, 13: 1.52, 14: 3.35, 15: 1.46}
SPREAD_FORCED_FLAT = 1.44
ASSUMED_RT = 1.009
TICK_USD = 0.50


def simulate_traced(O, C, sig, first_decide, M, cost_ticks, tick_pts):
    """A verbatim copy of D491.simulate with the fill segments recorded. Equality is asserted below."""
    n = O.shape[0]
    pos = np.zeros(n); entry_px = np.zeros(n); entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n); trips = np.zeros(n)
    s_all = np.nan_to_num(sig, nan=0.0)
    entries, exits = [], []
    for t in range(first_decide, D491.LAST_SEG):
        s = s_all[:, t]; px = O[:, t + 1]
        live = pos != 0
        elapsed = t - entry_t
        ex = live & (elapsed >= M) & (s * pos <= 0) & np.isfinite(px)
        pnl = np.where(ex, pnl + pos * (px - entry_px) / tick_pts - cost_ticks, pnl)
        trips = np.where(ex, trips + 1, trips)
        pos = np.where(ex, 0.0, pos)
        exits += [t + 1] * int(ex.sum())                       # the fill is at the OPEN of t+1
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_px = np.where(en, px, entry_px); entry_t = np.where(en, t, entry_t)
        pos = np.where(en, s, pos)
        entries += [t + 1] * int(en.sum())
    cpx = C[:, D491.LAST_SEG]
    still = (pos != 0) & np.isfinite(cpx)
    pnl = np.where(still, pnl + pos * (cpx - entry_px) / tick_pts - cost_ticks, pnl)
    trips = np.where(still, trips + 1, trips)
    n_forced = int(still.sum())
    return pnl, trips, np.array(entries), np.array(exits), n_forced


def main():
    meta = json.loads(ARM.META.read_text(encoding="utf-8"))
    spec = json.loads(ARM.SPECS.read_text(encoding="utf-8"))
    b = ARM.build(pd.read_csv(ARM.FIX), meta, spec)
    # RESTRICT TO IN SAMPLE. build() spans the full history and the 2024+ slice was spent once by
    # D503's declared forward read and may never be re-read. The entry-hour histogram is a timing
    # property, not a P&L, but the clean thing is not to touch the slice at all.
    days = np.asarray(b["days"], dtype=str)
    ins = (days >= "2016-01-04") & (days <= "2023-12-29")
    assert ins.sum() < len(days), "[WINDOW] the restriction selected everything -- check the date strings"
    print(f"[WINDOW] {len(days):,} sessions built, {int(ins.sum()):,} in sample "
          f"({min(days[ins])}..{max(days[ins])}); {int((~ins).sum()):,} outside are NOT read")   # builtin min/max: numpy's fails on <U10
    O, C, sig = b["O"][ins], b["C"][ins], b["AGREE"][ins]
    fd, M = D491.DAY_FIRST_DECIDE, ARM.M_HOLD
    cost, tick_pts = b["cost"], b["tick_pts"]
    p0, t0 = D491.simulate(O, C, sig, fd, M, cost, tick_pts)
    p1, t1, ent, exi, n_forced = simulate_traced(O, C, sig, fd, M, cost, tick_pts)
    assert np.array_equal(p0, p1) and np.array_equal(t0, t1), "[TRACE] the copy is not the committed simulate"
    print(f"[TRACE] the instrumented copy reproduces simulate() bit-identically: "
          f"{len(p0):,} sessions, {t0.sum():,.0f} round trips\n")

    # segments are hourly; DAY_FIRST_DECIDE is the h09 segment, so segment s is hour 9 + (s - fd)
    def hour_of(seg):
        return 9 + (seg - D491.DAY_FIRST_DECIDE)

    e = pd.Series([hour_of(s) for s in ent]).value_counts().sort_index()
    x = pd.Series([hour_of(s) for s in exi]).value_counts().sort_index()
    tot_e = int(e.sum())
    print(f"  {'hour':>6}{'entries':>10}{'share':>9}{'spread tk':>11}   (exits at that hour: n)")
    w = 0.0
    for h, n in e.items():
        sp = SPREAD_AT.get(h, np.nan)
        w += (n / tot_e) * sp
        print(f"  {h:>6}{n:>10,}{100*n/tot_e:>8.1f}%{sp:>11.2f}   {int(x.get(h,0)):>6,}")
    print(f"\n  entry-weighted spread          {w:.3f} ticks")
    print(f"  exits: {n_forced:,} forced flat at the h15 close (spread {SPREAD_FORCED_FLAT}), "
          f"{int(t0.sum())-n_forced:,} signal exits at an hourly open")
    fshare = n_forced / t0.sum()
    exit_sp = fshare * SPREAD_FORCED_FLAT + (1 - fshare) * w
    print(f"  exit-weighted spread           {exit_sp:.3f} ticks  ({100*fshare:.0f}% of exits are the forced flat)")

    # a taker pays half the quoted spread on each leg; the round trip is entry half + exit half
    rt = 0.5 * w + 0.5 * exit_sp
    print(f"\n  ROUND-TRIP CROSSING: {0.5*w:.3f} + {0.5*exit_sp:.3f} = {rt:.3f} ticks against the assumed {ASSUMED_RT}")
    old = 3.00 + ASSUMED_RT * TICK_USD
    new = 3.00 + rt * TICK_USD
    print(f"  round trip in dollars: ${old:.2f} assumed  ->  ${new:.2f} measured   (+{100*(new/old-1):.1f}%)")
    gross = 13.61
    print(f"  the arm's gross is ${gross:.2f} a trade: net ${gross-old:.2f} -> ${gross-new:.2f} "
          f"({100*((gross-new)/(gross-old)-1):+.1f}% on net P&L)")

    # Don't scale the Sharpe -- RE-RUN the arm at the measured cost and score it exactly.
    tick_usd = b["tick_usd"]
    for label, ct in (("assumed  1.009 ticks", cost), ("measured %.3f ticks" % rt, 6.0 + rt)):
        p, tr = D491.simulate(O, C, sig, fd, M, ct, tick_pts)
        sc = D491.score(p, tick_usd)
        print(f"  [{label}]  cost {ct:.3f} tk = ${3.00 + (ct-6.0)*tick_usd:.2f} RT   "
              f"net Sharpe {sc['sharpe']:+.3f}   mean ${sc['mean_usd']:+.2f}/session   "
              f"total ${sc['mean_usd']*len(p):+,.0f}")
    print("  C-a's bar is 0.5. NOTE the Sharpe above is the IN-SAMPLE window only, so it is not the")
    print("  ledger's +0.698 (which is scored 2016-2026 and includes the spent forward slice).")


if __name__ == "__main__":
    main()
