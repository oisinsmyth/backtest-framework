"""D394 -- the CHOP cell's return shape, against the unfiltered book AND against all high-vol.

    uv run python scripts/run_d394_chop_shape.py

DESCRIPTIVE. No null, no hurdle, nothing selected, fitted or admitted (R15).

THE COMPARISON THAT DECIDES IT IS NOT CHOP vs BASELINE. CHOP is `hivol AND loER`, so comparing it
to the whole book confounds two filters. **The question is whether CHOP differs from ALL HIGH-VOL
trades** -- if it does not, the ER axis contributes nothing and the cell is the volatility effect
Addendum 2 already measured, wearing a second label.

Four cohorts, cap 5, E1, no exit rule:

    ALL          the unfiltered ledger, 24,777 trades
    HIVOL        the top volatility tercile, whatever its path shape
    CHOP_ER5     hivol AND bottom ER tercile at 5 bars   -- the window where the prior HELD
    CHOP_ER21    hivol AND bottom ER tercile at 21 bars  -- the window with the best number

Reported per CLAUDE.md's group 2: count, mean, MEDIAN, win rate, payoff, skew, kurtosis, and the
mean after trimming 1% from BOTH tails, all three shown. **Addendum 1 recorded why the trim must be
symmetric here, and why "share of P&L" is meaningless on this ledger** -- the total is a small
residual of two offsetting tails, so any share explodes.

Nothing here is a filter proposal. Addendum 4 established that the best cell of the 36 searched
(+28.39) sits below the correct best-of-36 noise floor (+32.96).
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


OUT = REPO / "data" / "d394_chop_shape.json"
CAP = 5
SHAPE = "E1"
CANDIDATE = "up_run_21"
QS = (1, 5, 10, 25, 50, 75, 90, 95, 99)


def shape_of(p, tr, P, V47, V59, elig):
    p = np.asarray(p, float)
    N = p.size
    sd = float(p.std(ddof=1))
    win = p > 0
    aw = float(p[win].mean()) if win.any() else float("nan")
    al = float(p[~win].mean()) if (~win).any() else float("nan")
    lo1, hi1 = np.percentile(p, 1), np.percentile(p, 99)
    cost, half, px = V47.two_c(tr, P["HALF"]["PUB"], P["CLOSE"])
    return dict(
        n=N, mean_bp=float(p.mean()), median_bp=float(np.median(p)), std_bp=sd,
        t=float(p.mean() / (sd / np.sqrt(N))),
        win_rate=float(win.mean()), avg_win_bp=aw, avg_loss_bp=al,
        payoff=float(aw / abs(al)) if al else None,
        skew=float(((p - p.mean()) ** 3).mean() / sd ** 3),
        excess_kurtosis=float(((p - p.mean()) ** 4).mean() / sd ** 4 - 3.0),
        min_bp=float(p.min()), max_bp=float(p.max()),
        percentiles={str(q): float(np.percentile(p, q)) for q in QS},
        trim_ex_top_bp=float(p[p <= hi1].mean()),
        trim_ex_bottom_bp=float(p[p >= lo1].mean()),
        trim_both_bp=float(p[(p >= lo1) & (p <= hi1)].mean()),
        round_trip=float(cost), held_half_spread=float(half), held_price=float(px),
        net_bp=float(p.mean() - cost), ratio=float(p.mean() / cost) if cost else None)


def main() -> int:
    t0 = time.time()
    R = _load("d393b", "run_d393_bs_null.py")
    A1 = _load("a1er", "a1_er_stage0.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    V47 = PREP.V47

    P, elig, cols, masks, dec, T, n, bucket, elig_b = R.build(PREP, V50, SG)
    col = cols[CANDIDATE]
    mask = V50.shape_masks(V47.percentile_grid(col), elig)[SHAPE][0]
    sc = np.where(np.isfinite(col), col, 50.0)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = M.P1.build_grids(panel, cleaned)
    closes = np.asarray(g["close"], float)

    def lag_nT(a):
        s_ = np.where(P["excl"], np.nan, a)
        s_ = PREP.UF.apply_floor_replace(s_, P["keep"])
        s_ = np.where(P["base"], s_, np.nan)
        o = np.full((T, n), np.nan)
        o[1:] = s_[:, :-1].T
        return o

    er5 = lag_nT(A1.er_grid(closes, live, 5))
    er21 = lag_nT(A1.er_grid(closes, live, 21))
    vol = V47.percentile_grid(lag_nT(np.asarray(P["score"]("rvol21"))))
    del cols, masks, dec, bucket, elig_b, g, panel, cleaned, closes
    gc.collect()
    print(f"  build {time.time() - t0:.0f}s, RSS {_rss():.2f} GB", flush=True)

    res = V59.run_mirror(P, mask, sc, "cap", CAP)
    p = np.asarray(V47.pnl_bp(res), float)
    tr = res["trades"]
    ri = np.array([t_[0] for t_ in tr])
    bi = np.array([t_[1] for t_ in tr])
    vv = vol[bi, ri]
    ok_v = np.isfinite(vv)
    v_hi = np.percentile(vv[ok_v], 66.667)
    hivol = ok_v & (vv >= v_hi)

    cohorts = {"ALL": np.ones(p.size, bool), "HIVOL": hivol}
    for nm, gr in (("CHOP_ER5", er5), ("CHOP_ER21", er21)):
        e = gr[bi, ri]
        ok = np.isfinite(e) & ok_v
        lo = np.percentile(e[ok], 33.333)
        cohorts[nm] = ok & hivol & (e <= lo)

    out = {}
    for nm, sel in cohorts.items():
        sub = [tr[i] for i in np.flatnonzero(sel)]
        out[nm] = shape_of(p[sel], sub, P, V47, V59, elig)
        print(f"    {nm:<10s} {out[nm]['n']:>7,} trades, mean {out[nm]['mean_bp']:+7.2f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    payload = dict(study=394, stage="chop_shape", cap=CAP, shape=SHAPE, score=CANDIDATE,
                   purpose="Return shape of the CHOP cell against the unfiltered book AND against "
                           "all high-vol trades. Descriptive; nothing selected or admitted (R15).",
                   note="CHOP is hivol AND loER, so the decisive comparison is CHOP vs HIVOL, not "
                        "CHOP vs ALL.", cohorts=out)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    keys = list(cohorts)
    def row(lab, fn, fmt="{:>12}"):
        print(f"  {lab:<22s}" + "".join(fmt.format(fn(out[k])) for k in keys))

    print(f"\nCAP {CAP} -- return shape by cohort\n")
    print(f"  {'':22s}" + "".join(f"{k:>12s}" for k in keys))
    row("trades", lambda d: f"{d['n']:,}")
    row("mean bp", lambda d: f"{d['mean_bp']:+.2f}")
    row("median bp", lambda d: f"{d['median_bp']:+.2f}")
    row("std bp", lambda d: f"{d['std_bp']:.0f}")
    row("t", lambda d: f"{d['t']:+.2f}")
    row("win rate", lambda d: f"{100 * d['win_rate']:.2f}%")
    row("avg win", lambda d: f"{d['avg_win_bp']:+.0f}")
    row("avg loss", lambda d: f"{d['avg_loss_bp']:+.0f}")
    row("payoff", lambda d: f"{d['payoff']:.3f}")
    row("skew", lambda d: f"{d['skew']:+.2f}")
    row("excess kurtosis", lambda d: f"{d['excess_kurtosis']:+.1f}")
    print()
    for q in QS:
        row(f"p{q}", lambda d, q=q: f"{d['percentiles'][str(q)]:+.0f}")
    row("min", lambda d: f"{d['min_bp']:+,.0f}")
    row("max", lambda d: f"{d['max_bp']:+,.0f}")
    print()
    row("trim ex-top 1%", lambda d: f"{d['trim_ex_top_bp']:+.2f}")
    row("trim ex-bottom 1%", lambda d: f"{d['trim_ex_bottom_bp']:+.2f}")
    row("TRIM BOTH", lambda d: f"{d['trim_both_bp']:+.2f}")
    print()
    row("held price", lambda d: f"${d['held_price']:.2f}")
    row("half-spread", lambda d: f"{d['held_half_spread']:.2f}")
    row("round trip", lambda d: f"{d['round_trip']:.2f}")
    row("NET bp", lambda d: f"{d['net_bp']:+.2f}")
    row("ratio", lambda d: f"{d['ratio']:.2f}x")
    print(f"\n  ({time.time() - t0:.0f}s)  Descriptive. Nothing selected, fitted or admitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
