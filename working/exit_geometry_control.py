"""Is the arm's payoff ratio of 1.13 an EDGE, or is it EXIT GEOMETRY?

The challenge, from external research (Prop-Firm-080926/15-reddit-mined.md C5): "A trailing stop
mechanically manufactures a low win rate and a high payoff ratio on ANY entry, including a random
one. That geometry is not evidence of a signal." Falsifier: run a random-entry control with the
IDENTICAL exit, and compare.

The arm's existing rotation null already IS that control -- d504 line 403 rotates the SIGNAL and
re-runs simulate() against the same price path with the same 5-hour minimum hold, the same
signal-stops-favouring exit and the same forced flat -- so exit geometry is reproduced in every
draw. But that null's statistic is the SHARPE. The challenge is about the HIT RATE and the PAYOFF
RATIO, so this answers it on its own statistics: the null distribution of hit rate and payoff ratio
under a rotated (i.e. detached) signal with the arm's exact exit rules.

Per-trade P&L is needed and simulate() returns per-session totals, so the trade ledger is rebuilt
with a copy of the loop ASSERTED BIT-IDENTICAL to the committed simulate() first.

In sample only (2016-01-04..2023-12-29); the spent 2024+ slice is not read. NO new construction.

    python working/exit_geometry_control.py
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
N_DRAWS = 400
INS_LO, INS_HI = "2016-01-04", "2023-12-29"


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


D491 = _load("d491g", "d491_conditional_hold.py")
ARM = _load("d504g", "d504_arm_full_history.py")


def trades(O, C, sig, first, M, cost_ticks, tick_pts, tick_usd):
    """Per-TRADE net P&L in dollars, from a copy of simulate() that also emits the ledger."""
    n = O.shape[0]
    pos = np.zeros(n); entry_px = np.zeros(n); entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n); trips = np.zeros(n); tr = []
    s_all = np.nan_to_num(sig, nan=0.0)
    for t in range(first, D491.LAST_SEG):
        s = s_all[:, t]; px = O[:, t + 1]
        live = pos != 0
        ex = live & ((t - entry_t) >= M) & (s * pos <= 0) & np.isfinite(px)
        # the accumulation must be written EXACTLY as the committed loop writes it: float addition is
        # not associative, and `pnl + (g - c)` is not `pnl + g - c`. The ledger is computed separately.
        pnl = np.where(ex, pnl + pos * (px - entry_px) / tick_pts - cost_ticks, pnl)
        trips = np.where(ex, trips + 1, trips)
        if ex.any():
            tr.append((pos * (px - entry_px) / tick_pts - cost_ticks)[ex])
        pos = np.where(ex, 0.0, pos)
        en = (pos == 0) & (s != 0) & np.isfinite(px)
        entry_px = np.where(en, px, entry_px); entry_t = np.where(en, t, entry_t); pos = np.where(en, s, pos)
    cpx = C[:, D491.LAST_SEG]
    still = (pos != 0) & np.isfinite(cpx)
    pnl = np.where(still, pnl + pos * (cpx - entry_px) / tick_pts - cost_ticks, pnl)
    trips = np.where(still, trips + 1, trips)
    if still.any():
        tr.append((pos * (cpx - entry_px) / tick_pts - cost_ticks)[still])
    return pnl, trips, (np.concatenate(tr) * tick_usd if tr else np.array([]))


def shape(t):
    w, l = t[t > 0], t[t < 0]
    return dict(n=len(t), hit=float((t > 0).mean()), payoff=float(w.mean() / abs(l.mean())) if len(l) else np.nan,
                mean=float(t.mean()))


def main():
    meta = json.loads(ARM.META.read_text(encoding="utf-8"))
    spec = json.loads(ARM.SPECS.read_text(encoding="utf-8"))
    b = ARM.build(pd.read_csv(ARM.FIX), meta, spec)
    days = np.asarray(b["days"], dtype=str)
    ins = (days >= INS_LO) & (days <= INS_HI)
    assert ins.sum() < len(days), "[WINDOW] restriction selected everything"
    O, C, S = b["O"][ins], b["C"][ins], b["AGREE"][ins]
    first, M = D491.DAY_FIRST_DECIDE, ARM.M_HOLD
    cost, tick_pts, tick_usd = b["cost"], b["tick_pts"], b["tick_usd"]
    print(f"[WINDOW] {int(ins.sum()):,} in-sample sessions ({min(days[ins])}..{max(days[ins])}); "
          f"{int((~ins).sum()):,} outside NOT read")

    p0, t0 = D491.simulate(O, C, S, first, M, cost, tick_pts)
    p1, t1, tr = trades(O, C, S, first, M, cost, tick_pts, tick_usd)
    assert np.array_equal(p0, p1) and np.array_equal(t0, t1), "[TRACE] the copy is not the committed simulate"
    obs = shape(tr)
    print(f"[TRACE] copy reproduces simulate() bit-identically; {obs['n']:,} trades\n")
    print(f"  OBSERVED   hit {100*obs['hit']:.1f}%   payoff {obs['payoff']:.3f}   mean ${obs['mean']:+.2f}/trade")

    rng = np.random.default_rng(20260914)
    rows = []
    for _ in range(N_DRAWS):
        k = int(rng.integers(1, S.shape[0]))
        _, _, trn = trades(O, C, np.roll(S, k, axis=0), first, M, cost, tick_pts, tick_usd)
        if len(trn) > 50:
            rows.append(shape(trn))
    d = pd.DataFrame(rows)
    print(f"\n  ROTATED SIGNAL, SAME EXIT -- {len(d)} draws. This is exit geometry with the entry detached.")
    print(f"  {'statistic':<12}{'p05':>9}{'p50':>9}{'p95':>9}{'observed':>11}{'share of draws >= observed':>28}")
    for k, fmt in (("hit", "{:.3f}"), ("payoff", "{:.3f}"), ("mean", "{:+.2f}")):
        v = d[k].to_numpy()
        print(f"  {k:<12}{np.quantile(v,.05):>9.3f}{np.quantile(v,.50):>9.3f}{np.quantile(v,.95):>9.3f}"
              f"{obs[k]:>11.3f}{100*np.mean(v >= obs[k]):>26.1f}%")
    print(f"\n  If the payoff ratio were pure exit geometry, the rotated draws would reproduce it.")
    print(f"  median rotated payoff {d['payoff'].median():.3f} vs observed {obs['payoff']:.3f}; "
          f"median rotated mean ${d['mean'].median():+.2f} vs observed ${obs['mean']:+.2f}")


if __name__ == "__main__":
    main()
