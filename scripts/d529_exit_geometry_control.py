"""D529 -- is the admitted arm's payoff ratio an EDGE, or is it EXIT GEOMETRY?

THE CHALLENGE, from external quarantined research (Prop-Firm-080926/15-reddit-mined.md, C5):
"A trailing stop mechanically manufactures a low win rate and a high payoff ratio on ANY entry,
including a random one. That geometry is not evidence of a signal." Its falsifier: run a random-entry
control with the IDENTICAL exit.

WHY IT MATTERS HERE. The arm hits 50.5% with a payoff of 1.13, and this session built a search
direction on reading that as "not paid for being right, paid for being right BIGGER". If the payoff
ratio is manufactured by the exit -- a 5-hour minimum hold that forbids cutting early, plus a forced
flat that truncates 75% of trades at the h15 close -- then that reading is wrong and the direction
it implies is wrong with it.

THE CONTROL ALREADY EXISTS, PARTLY. d504 line 403 rotates the signal and re-runs simulate() against
the same price path with the same minimum hold, the same signal-stops-favouring exit and the same
forced flat, so exit geometry is reproduced in every draw. But it scores the SHARPE. The challenge is
about the HIT RATE and the PAYOFF RATIO, so this answers it on its own statistics.

Per-trade P&L is needed and simulate() returns per-session totals, so the trade ledger is rebuilt
from a copy of the loop that is ASSERTED BIT-IDENTICAL to the committed simulate() before anything
is believed. The accumulation is written exactly as the committed loop writes it: float addition is
not associative and `pnl + (g - c)` is not `pnl + g - c` -- the first draft of this file diverged on
precisely that and the assertion caught it.

In sample only (2016-01-04..2023-12-29). The spent 2024+ slice is NOT read. No new construction,
nothing admitted (R15).

    python scripts/d529_exit_geometry_control.py --run    # -> data/d529_exit_geometry_control.json
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d529_exit_geometry_control.json"
N_DRAWS = 400
SEED = 20260914
INS_LO, INS_HI = "2016-01-04", "2023-12-29"


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


D491 = _load("d491h", "d491_conditional_hold.py")
ARM = _load("d504h", "d504_arm_full_history.py")


def trades(O, C, sig, first, M, cost_ticks, tick_pts, tick_usd):
    """simulate(), plus the per-TRADE net P&L ledger in dollars. Equality asserted by the caller."""
    n = O.shape[0]
    pos = np.zeros(n); entry_px = np.zeros(n); entry_t = np.full(n, -1, dtype=np.int64)
    pnl = np.zeros(n); trips = np.zeros(n); tr = []
    s_all = np.nan_to_num(sig, nan=0.0)
    for t in range(first, D491.LAST_SEG):
        s = s_all[:, t]; px = O[:, t + 1]
        live = pos != 0
        ex = live & ((t - entry_t) >= M) & (s * pos <= 0) & np.isfinite(px)
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
    return dict(n=int(len(t)), hit=float((t > 0).mean()),
                payoff=float(w.mean() / abs(l.mean())) if len(l) else float("nan"),
                mean=float(t.mean()))


def run():
    meta = json.loads(ARM.META.read_text(encoding="utf-8"))
    spec = json.loads(ARM.SPECS.read_text(encoding="utf-8"))
    b = ARM.build(pd.read_csv(ARM.FIX), meta, spec)
    days = np.asarray(b["days"], dtype=str)
    ins = (days >= INS_LO) & (days <= INS_HI)
    assert ins.sum() < len(days), "[WINDOW] the restriction selected everything"
    O, C, S = b["O"][ins], b["C"][ins], b["AGREE"][ins]
    first, M = D491.DAY_FIRST_DECIDE, ARM.M_HOLD
    cost, tick_pts, tick_usd = b["cost"], b["tick_pts"], b["tick_usd"]
    print(f"[WINDOW] {int(ins.sum()):,} in-sample sessions ({min(days[ins])}..{max(days[ins])}); "
          f"{int((~ins).sum()):,} outside are NOT read")

    p0, t0 = D491.simulate(O, C, S, first, M, cost, tick_pts)
    p1, t1, tr = trades(O, C, S, first, M, cost, tick_pts, tick_usd)
    assert np.array_equal(p0, p1) and np.array_equal(t0, t1), "[TRACE] the copy is not the committed simulate"
    obs = shape(tr)
    print(f"[TRACE] the copy reproduces simulate() bit-identically; {obs['n']:,} trades\n")
    print(f"  OBSERVED   hit {100*obs['hit']:.1f}%   payoff {obs['payoff']:.3f}   mean ${obs['mean']:+.2f}/trade")

    rng = np.random.default_rng(SEED)
    rows = []
    for _ in range(N_DRAWS):
        k = int(rng.integers(1, S.shape[0]))
        _, _, trn = trades(O, C, np.roll(S, k, axis=0), first, M, cost, tick_pts, tick_usd)
        if len(trn) > 50:
            rows.append(shape(trn))
    d = pd.DataFrame(rows)
    print(f"\n  ROTATED SIGNAL, SAME EXIT -- {len(d)} draws. Exit geometry with the entry detached.")
    print(f"  {'statistic':<10}{'p05':>9}{'p50':>9}{'p95':>9}{'observed':>11}{'draws >= obs':>15}   verdict")
    res = {}
    for k in ("hit", "payoff", "mean"):
        v = d[k].to_numpy()
        share = float(np.mean(v >= obs[k]))
        res[k] = dict(p05=float(np.quantile(v, .05)), p50=float(np.quantile(v, .50)),
                      p95=float(np.quantile(v, .95)), observed=obs[k], share_ge=share,
                      clears=bool(obs[k] > np.quantile(v, .95)))
        print(f"  {k:<10}{res[k]['p05']:>9.3f}{res[k]['p50']:>9.3f}{res[k]['p95']:>9.3f}"
              f"{obs[k]:>11.3f}{100*share:>14.1f}%   {'CLEARS' if res[k]['clears'] else 'INSIDE the null'}")

    # the decomposition: which of the two moves the expectation?
    h_n, p_n = res["hit"]["p50"], res["payoff"]["p50"]
    e = lambda h, p: h * p - (1 - h)          # noqa: E731  expectation per unit risked
    print(f"\n  DECOMPOSITION, expectation per unit risked = hit*payoff - (1-hit):")
    print(f"    null median hit {h_n:.3f}, null median payoff {p_n:.3f}  -> {e(h_n, p_n):+.4f}")
    print(f"    OBSERVED hit {obs['hit']:.3f}, null median payoff {p_n:.3f}  -> {e(obs['hit'], p_n):+.4f}   (accuracy alone)")
    print(f"    null median hit {h_n:.3f}, OBSERVED payoff {obs['payoff']:.3f}  -> {e(h_n, obs['payoff']):+.4f}   (asymmetry alone)")
    print(f"    OBSERVED hit {obs['hit']:.3f}, OBSERVED payoff {obs['payoff']:.3f}  -> {e(obs['hit'], obs['payoff']):+.4f}")
    res["decomposition"] = dict(null_only=e(h_n, p_n), accuracy_only=e(obs["hit"], p_n),
                                asymmetry_only=e(h_n, obs["payoff"]), both=e(obs["hit"], obs["payoff"]))
    OUT.write_text(json.dumps(dict(window=[INS_LO, INS_HI], draws=len(d), seed=SEED,
                                   observed=obs, null=res), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    else:
        ap.error("pass --run")
