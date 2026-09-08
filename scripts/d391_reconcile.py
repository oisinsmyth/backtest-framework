"""D391 addendum 2 -- the hand decomposition: where do the ~24 unexplained bp enter?

    uv run python scripts/d391_reconcile.py

THE DISCREPANCY, from D391 section 8.4. On nominally the same events at one bar:

    ledger, cap 1, long     +47.19 bp per trade      (entry at the next OPEN)
    drift,  h = 1           -0.08 bp per name-bar    (close-to-close)
    measured fill gap       -22.75

    -0.08 - (-22.75) = +22.67, not +47.19.  ~24 bp unaccounted.

That gap is load-bearing: it is the difference between "this lead is nothing" and "this lead is
57x its atlas floor". So it is decomposed EXACTLY rather than argued about.

THE ALGEBRA, written before the numbers so the check is a prediction and not a fit. With e the
entry bar (the signal bar t plus one):

    ledger excess (open fill)   =  ocT[e]  -  m_f_oc[e]
    drift  excess (close fill)  =  r1T[e]  -  m_f[e]
    ------------------------------------------------------------------
    difference                  = (ocT - r1T)[e]  -  (m_f_oc - m_f)[e]
                                = -name_gap[e]  +  market_gap[e]

where `gap` is the close-to-open leg: name_gap = r1T - ocT, market_gap = m_f - m_f_oc.

**So the two lenses differ by the MARKET's overnight gap minus the NAME's.** The ledger hedges the
entry bar with the market's OPEN-to-close return and the drift with its CLOSE-to-close, so the
market's own overnight move is in one and not the other. If the floored market drifts up
overnight -- which PICKUP section 3.3 and D247 both record for equities -- the ledger is credited
that drift on every single trade, on top of whatever the name does.

DESCRIPTIVE. Reconciles two existing numbers; scores nothing, admits nothing (R15).
"""
from __future__ import annotations

import importlib.util
import json
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


OUT = REPO / "data" / "d391_reconcile.json"
D391 = _load("d391", "run_d391_undercut_reclaim.py")
from backtest_framework.research import structure as MS      # noqa: E402
PREP = _load("d348p", "d348_prep.py")
V59 = _load("d359r", "run_d359_loser_rally_short.py")
ST = _load("ragged_structure_scores", "ragged_structure_scores.py")


def main() -> int:
    t0 = time.time()
    P = PREP.prep(need_grids=True)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    PV = D391.build_pivots(type("V", (), {"M": M})(), MS, panel, cleaned, live)
    n, T = live.shape
    atr = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live[i])
        if at.size >= 2:
            atr[i, at] = ST._atr_price(g["open"][i, at], g["high"][i, at],
                                       g["low"][i, at], g["close"][i, at])
    elig = np.asarray(P["elig"])
    EV, POOL, UNDER, MIRROR = D391.event_masks(PV, g, atr, elig)
    sc = np.full((T, n), 50.0)

    r1T = np.asarray(P["r1T"])                 # (T, n) close-to-close
    ocT = np.asarray(P["ocT"])                 # (T, n) open-to-close
    m_f = np.asarray(P["m_f"])                 # (T,)   floored market, close-to-close
    m_oc = np.asarray(P["m_f_oc"])             # (T,)   floored market, open-to-close
    print(f"  rebuilt in {time.time() - t0:.0f}s | events {int(EV.sum()):,}", flush=True)

    # ---- the aggregate identity, over the event population -----------------
    ev_t, ev_i = np.nonzero(EV)
    e = ev_t + 1                                # the entry bar
    ok = e < T
    ev_t, ev_i, e = ev_t[ok], ev_i[ok], e[ok]
    fin = np.isfinite(r1T[e, ev_i]) & np.isfinite(ocT[e, ev_i]) & \
        np.isfinite(m_f[e]) & np.isfinite(m_oc[e])
    ev_t, ev_i, e = ev_t[fin], ev_i[fin], e[fin]

    name_gap = r1T[e, ev_i] - ocT[e, ev_i]
    mkt_gap = m_f[e] - m_oc[e]
    ledger_x = ocT[e, ev_i] - m_oc[e]
    drift_x = r1T[e, ev_i] - m_f[e]
    diff = ledger_x - drift_x
    pred = mkt_gap - name_gap

    print(f"\n  THE IDENTITY, on {len(e):,} event entry bars (bp)\n")
    print(f"    ledger excess  (ocT - m_f_oc)      {ledger_x.mean() * 1e4:>+9.2f}")
    print(f"    drift  excess  (r1T - m_f)         {drift_x.mean() * 1e4:>+9.2f}")
    print(f"    difference                         {diff.mean() * 1e4:>+9.2f}")
    print(f"    predicted = market gap - name gap  {pred.mean() * 1e4:>+9.2f}")
    assert abs(diff.mean() - pred.mean()) < 1e-12, "[ID] the algebra does not close"
    print(f"    [ID] identity closes to {abs(diff.mean() - pred.mean()):.2e}\n")
    print(f"    the NAME's overnight gap           {name_gap.mean() * 1e4:>+9.2f}")
    print(f"    the MARKET's overnight gap         {mkt_gap.mean() * 1e4:>+9.2f}")
    print(f"      -> the market's own overnight drift is credited to EVERY trade,")
    print(f"         because the ledger hedges the entry bar open-to-close.")

    # ---- one named trade, walked by hand -----------------------------------
    res = V59.run_mirror(P, EV, sc, "cap", 1)
    tr = res["trades"]
    pnl = PREP.V47.pnl_bp(res)
    k = 0
    i0, e0 = tr[k][0], tr[k][1]
    t0_sig = e0 - 1
    print(f"\n  ONE TRADE, WALKED BY HAND: {P['symbols'][i0]}, signal bar {t0_sig} "
          f"({P['dates'][t0_sig]}), entry bar {e0} ({P['dates'][e0]})\n")
    print(f"    name  close-to-close r1T[e]        {r1T[e0, i0] * 1e4:>+9.2f}")
    print(f"    name  open-to-close  ocT[e]        {ocT[e0, i0] * 1e4:>+9.2f}")
    print(f"    name  overnight gap                {(r1T[e0, i0] - ocT[e0, i0]) * 1e4:>+9.2f}")
    print(f"    mkt   close-to-close m_f[e]        {m_f[e0] * 1e4:>+9.2f}")
    print(f"    mkt   open-to-close  m_f_oc[e]     {m_oc[e0] * 1e4:>+9.2f}")
    print(f"    mkt   overnight gap                {(m_f[e0] - m_oc[e0]) * 1e4:>+9.2f}")
    print(f"    ledger excess (what the kernel books) "
          f"{(ocT[e0, i0] - m_oc[e0]) * 1e4:>+9.2f}")
    print(f"    kernel's own pnl_bp for this trade  {pnl[k]:>+9.2f}")
    print(f"    drift  excess (what F1 books)       {(r1T[e0, i0] - m_f[e0]) * 1e4:>+9.2f}")

    # ---- THE STEP THE FIRST VERSION MISSED --------------------------------
    #      The block above averages MY formula over EVENT BARS and compares it to the kernel's
    #      average over TRADES. Those are different populations if the kernel's trade list is not
    #      the event list. Evaluate the formula on the KERNEL'S OWN trades, in its own order.
    ti = np.array([t[0] for t in tr])
    te = np.array([t[1] for t in tr])
    mine = (ocT[te, ti] - m_oc[te]) * 1e4
    ok2 = np.isfinite(mine)
    print(f"\n  ON THE KERNEL'S OWN {len(tr):,} TRADES (bp)\n")
    print(f"    kernel pnl_bp mean                 {pnl.mean():>+9.2f}")
    print(f"    my formula on the same trades      {np.nanmean(mine):>+9.2f}")
    print(f"    max |difference| per trade         {np.nanmax(np.abs(pnl[ok2] - mine[ok2])):>9.2e}")
    print(f"    entry bars that are signal bar + 1 "
          f"{100 * np.mean(EV[te - 1, ti]):>8.1f}%")
    agree = np.allclose(pnl[ok2], mine[ok2], atol=1e-9)
    print(f"    -> the kernel books EXACTLY (ocT - m_f_oc) on the entry bar: {agree}")

    payload = dict(
        study=391, addendum="reconciliation",
        kernel_mean_bp=float(pnl.mean()),
        my_formula_on_kernel_trades_bp=float(np.nanmean(mine)),
        formula_matches_kernel=bool(agree),
        event_bar_mean_ledger_excess_bp=float(ledger_x.mean() * 1e4),
        events_used=int(len(e)),
        ledger_excess_bp=float(ledger_x.mean() * 1e4),
        drift_excess_bp=float(drift_x.mean() * 1e4),
        difference_bp=float(diff.mean() * 1e4),
        name_overnight_gap_bp=float(name_gap.mean() * 1e4),
        market_overnight_gap_bp=float(mkt_gap.mean() * 1e4),
        identity="ledger - drift == market_gap - name_gap, exact",
        note="The ledger hedges the ENTRY BAR open-to-close (m_f_oc) while the drift hedges it "
             "close-to-close (m_f). The floored market's own overnight move is therefore in one "
             "lens and not the other, and is credited to every trade.")
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
