"""How D526 changes the ORACLE: how long a window before the persistence state predicts itself?

    python working/d527_oracle_reliability_vs_window.py

THE ORACLE'S PURPOSE was never to trade.  It is a LABEL computed with future information, whose
only job is to define the target a CAUSAL statistic is then asked to hit.  D526 established that
the target is REAL on the index roots -- persistence on a bounce-free mid, pooled t +3.10,
10 of 10 signs replicating over a 12-year gap.

BUT A LABEL IS ONLY USABLE IF IT IS RELIABLE, and D525 s11.4 measured the one-session t of this
statistic at +0.24.  If a single session's estimate is almost all noise, then NO causal feature can
correlate with it, however real the underlying state -- the ceiling on any such correlation is
sqrt(reliability).  That is an arithmetic limit, not a modelling difficulty.

So the oracle question collapses to ONE well-posed measurement, and it is the same object as the
bridge:

    for a window of W sessions, corr( estimate on [t-W, t) , estimate on [t, t+W) )
    NON-OVERLAPPING, adjacent, WITHIN one root -- so no between-root level difference can leak,
    which is the confound that made D523 s3's pooled split-half an artefact.

The PAST window is causal by construction: it is the natural predictor of a slow state, and it
needs no feature engineering.  So this curve is simultaneously
  (a) the label's reliability at each window length,
  (b) the best a causal predictor could do, and
  (c) the answer to whether the oracle can be a SESSION label at all or must be a REGIME label.

If W=1 is near zero and the curve only lifts at W of 20+, the oracle is a slow regime variable:
the STATE is measured over weeks while the TRADING stays intraday, which contradicts nothing the
principal specified.

No return is read as P&L, no cost, no position.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
import d526_mid_vs_trade_scaling as Q     # noqa: E402
import d523_oracle_stage0 as M            # noqa: E402

WINDOWS = (1, 2, 5, 10, 20, 40, 60)
ROOTS = ("ES", "NQ", "YM", "RTY", "GC", "ZB", "ZN", "6E", "CL", "HO")


def P(*a):
    print(*a, flush=True)


def per_session(g: pd.DataFrame, col: str):
    R, days = Q.session_matrix(g, col)
    if R.shape[1] == 0:
        return np.zeros(0), []
    s = Q.path_slope(Q.vol_standardise(R))
    ok = np.isfinite(s)
    return s[ok], list(np.array(days)[ok])


def reliability_curve(s: np.ndarray) -> dict:
    """corr(mean over [t-W,t), mean over [t,t+W)) on NON-OVERLAPPING adjacent blocks."""
    out = {}
    for W in WINDOWS:
        nb = len(s) // W
        if nb < 8:
            out[W] = (np.nan, 0)
            continue
        blocks = s[:nb * W].reshape(nb, W).mean(1)
        a, b = blocks[:-1], blocks[1:]
        # adjacent NON-OVERLAPPING pairs, and every pair is disjoint from the next by striding 2
        a2, b2 = a[::2], b[::2]
        out[W] = ((M.pearson(a2, b2) if len(a2) > 5 else np.nan), len(a2))
    return out


P("=" * 100)
P("THE ORACLE'S RELIABILITY CURVE -- corr(past window, next window), WITHIN root, non-overlapping")
P("=" * 100)
P("  statistic: D526's path-scaling slope per session (slope = Hu - 1), vol-standardised, k>=3")
P("  on the 2011-2023 TRADE closes, which D525's design check already spent -- read here for")
P("  statistical power, not as confirmation.")
P("")

d = pd.read_parquet("data/fixtures/fut_day5m.parquet",
                    columns=["root", "day", "bar", "close", "present", "same_front"])
d = d[d["present"]]
d = d[d["same_front"]]
d = d[d["day"] <= "2023-12-29"]

P("  root   sessions   " + "  ".join(f"W={w:<3}" for w in WINDOWS))
curves = {}
for r in ROOTS:
    g = d[d["root"] == r].sort_values(["day", "bar"], kind="stable")
    s, days = per_session(g, "close")
    if len(s) < 500:
        continue
    c = reliability_curve(s)
    curves[r] = c
    P(f"  {r:>4}   {len(s):>8,}   " + "  ".join(
        (f"{c[w][0]:+.3f}" if np.isfinite(c[w][0]) else "  --  ") for w in WINDOWS))
P("")
P("  pairs n         " + "  ".join(f"{curves['ES'][w][1]:<5}" for w in WINDOWS))

P("")
P("=" * 100)
P("WHAT THE CURVE MEANS FOR A CAUSAL FEATURE: the ceiling is sqrt(reliability)")
P("=" * 100)
P("  A feature can correlate with a noisy label at most sqrt(reliability). So:")
P("")
P("  root   " + "  ".join(f"W={w:<3}" for w in WINDOWS))
for r, c in curves.items():
    cells = []
    for w in WINDOWS:
        v = c[w][0]
        cells.append(f"{np.sqrt(v):+.3f}" if np.isfinite(v) and v > 0 else "  --  ")
    P(f"  {r:>4}   " + "  ".join(cells))
P("")
P("  A '--' is a NEGATIVE reliability: the state does not persist at that window at all.")

P("")
P("=" * 100)
P("AND THE SAME CURVE ON THE BOUNCE-FREE MID (12 months only, so W>=20 runs out of pairs)")
P("=" * 100)
mid = pd.read_parquet("data/fixtures/fut_day5m_mid.parquet")
mid = mid[mid["present"]]
mid = mid[mid["same_front"]]
P("  root   sessions   " + "  ".join(f"W={w:<3}" for w in WINDOWS))
for r in ROOTS:
    g = mid[mid["root"] == r].sort_values(["day", "bar"], kind="stable")
    if len(g) == 0:
        continue
    s, days = per_session(g, "mid")
    if len(s) < 100:
        continue
    c = reliability_curve(s)
    P(f"  {r:>4}   {len(s):>8,}   " + "  ".join(
        (f"{c[w][0]:+.3f}" if np.isfinite(c[w][0]) else "  --  ") for w in WINDOWS))
P("")
P("  The mid window holds ~245 sessions, so W=20 leaves 6 pairs and W=40+ leaves none.")
P("  Read the mid rows for AGREEMENT IN SIGN with the long history, not for precision.")
