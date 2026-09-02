"""Does the one-bar edge survive skipping a bar? Bid-ask bounce vs real reversal.

    uv run python scripts/d290_skip_bar_test.py

D290 found `close_in_range` earning +50.69 bp PER BAR at k=1 on the spread,
decaying to +2.20 by k=40, and failing its measured 183.2 bp round trip at
0.28x. That profile -- enormous t, concentrated in bar one, below cost -- is the
same signature D288 flagged as microstructure.

THE DISCRIMINATING TEST. Where a stock closes in its daily range is mechanically
tied to whether the last print landed on the bid or the ask, so part of the next
bar's measured return is that print unwinding. Wait one bar before entering and
the unwind has already happened:

    skip 0   rank on score[t-1], earn from t     <- what D290 measured
    skip 1   rank on score[t-2], earn from t     <- the bounce has unwound
    skip 2   rank on score[t-3], earn from t

If the edge is the bounce it collapses at skip 1. If it is real one-day mean
reversion in the underlying, a substantial part survives.

IMPLEMENTED BY DOUBLE-LAGGING, NOT BY SHIFTING RETURNS. `rank_columns` applies
`C.lag1` itself (D279's function, which exists because the first `top_n` ranked
on bar t's score to earn bar t's return). Pre-lagging the score before handing it
over composes with that, so skip-n is n extra applications of the SAME lag every
other result in this programme uses. The alternative -- shifting the forward
return grid -- would have been a second, differently-written implementation of
the same idea, and this study has already been bitten by exactly that.

The composition is ASSERTED rather than assumed: `--selftest` rebuilds the
skip-1 ranking by hand from the raw score at t-2 and requires it to match.

CONTROLS ARE INCLUDED ON PURPOSE. `macd_hist` and `price_log` peak at k=20 and
k=40, so they have no one-bar component to lose. If they also collapsed at
skip 1 the test would be measuring something other than the bounce.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
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


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
B = M.B
C = M.C

OUT = REPO / "data" / "d290_skip_bar.json"
PROBE = ("close_in_range", "lower_wick", "body_frac")   # the k=1 cluster
CONTROL = ("macd_hist", "price_log")                    # peak at k=20 / k=40
SKIPS = (0, 1, 2, 3)
KS = (1, 2, 3, 5, 10, 20)
N_LEVELS = (3, 10, 50)


def skipped(score, n):
    """n extra applications of D279's `lag1`. `rank_columns` applies one more."""
    for _ in range(n):
        score = C.lag1(score)
    return score


def cell(score, base, fwd, T, N, k):
    order, cnt = M.rank_columns(score, base)
    ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base.shape)
    lr, lc = np.nonzero(ev_lo)
    hr, hc = np.nonzero(ev_hi)
    f = fwd[k]
    slo, clo = M.bar_sums(f, lr, lc, T)
    shi, chi = M.bar_sums(f, hr, hc, T)
    m = (clo > 0) & (chi > 0)
    if int(m.sum()) < M.MIN_BARS:
        return None
    lo, hi = slo[m] / clo[m], shi[m] / chi[m]
    d = lo - hi
    sd = d.std(ddof=1)
    return (float(d.mean() * 1e4),
            float(d.mean() / (sd / np.sqrt(d.size))) if sd > 0 else 0.0,
            float(lo.mean() * 1e4), float(-hi.mean() * 1e4), int(d.size))


def selftest(score, base):
    """The skip must be a real shift in the ranking, verified by hand."""
    o0, c0 = M.rank_columns(score, base)
    o1, c1 = M.rank_columns(skipped(score, 1), base)
    n, T = base.shape
    checked = 0
    for t in range(400, T, 601):
        q = np.flatnonzero(base[:, t])
        v = score[q, t - 2]                     # BY HAND: skip 1 ranks on t-2
        fin = np.isfinite(v)
        q2, v2 = q[fin], v[fin]
        if q2.size < 60:
            continue
        want = set(q2[np.argsort(v2, kind="stable")[:10]].tolist())
        # `legs_from_order` returns (ev_lo, ev_hi, inlo). The first is FRESH
        # ENTRIES -- a name already in the bottom N yesterday is not a fresh
        # entry today -- so membership is the THIRD value. Comparing against
        # `ev_lo` fails on any bar with a hold-over, which is how this assertion
        # first fired: row 52 at t=4006 was in the bottom 10 on both bars.
        _, _, inlo = M.legs_from_order(o1, c1, 10, base.shape)
        got = set(np.flatnonzero(inlo[:, t]).tolist())
        assert want == got, f"skip-1 ranking wrong at t={t}"
        checked += 1
    assert checked >= 4, f"only {checked} bars checked"
    assert not np.array_equal(o0, o1), "skip changed nothing -- the test is inert"
    print(f"    skip-1 ranks on score[t-2], verified by hand on {checked} bars, "
          f"and differs from skip-0")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest-only", action="store_true")
    a = ap.parse_args()

    t0 = time.time()
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(B.FIXTURE), "CACHE IS STALE -- rebuild"
    panel, _ = M.RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    base = z["warm"] & live
    T = live.shape[1]
    fwd = M.forward_returns(panel, live)
    print(f"loaded in {time.time() - t0:.0f}s | base {int(base.sum()):,} cells\n")

    print("  ASSERTION")
    selftest(z["close_in_range"], base)
    if a.selftest_only:
        return 0

    res = {}
    for c in PROBE + CONTROL:
        score = z[c]
        res[c] = {}
        tag = "PROBE" if c in PROBE else "CONTROL"
        print(f"\n  {c}  [{tag}]")
        for N in N_LEVELS:
            print(f"    N={N}")
            print(f"      {'k':>3s} " + " ".join(
                f"{'skip' + str(s):>16s}" for s in SKIPS))
            for k in KS:
                cells = []
                for s in SKIPS:
                    r = cell(skipped(score, s), base, fwd, T, N, k)
                    res[c].setdefault(str(N), {}).setdefault(str(k), {})[str(s)] = r
                    cells.append(f"{r[0]:+8.1f} t{r[1]:+5.1f}" if r else
                                 f"{'--':>16s}")
                print(f"      {k:3d} " + " ".join(cells))

    print(f"\n  RETENTION AT k=1, N=10 -- the number the test exists for")
    print(f"    {'candidate':16s} {'skip0':>9s} {'skip1':>9s} {'kept':>7s}")
    for c in PROBE + CONTROL:
        a0 = res[c].get("10", {}).get("1", {}).get("0")
        a1 = res[c].get("10", {}).get("1", {}).get("1")
        if a0 and a1 and a0[0] != 0:
            print(f"    {c:16s} {a0[0]:+9.1f} {a1[0]:+9.1f} "
                  f"{a1[0] / a0[0]:+7.0%}")

    OUT.write_text(json.dumps(
        {"purpose": "skip-a-bar test: does the one-bar edge survive waiting one "
                    "bar? Bid-ask bounce collapses; real reversal does not.",
         "skips": list(SKIPS), "horizons": list(KS), "n_levels": list(N_LEVELS),
         "probe": list(PROBE), "control": list(CONTROL),
         "results": res, "elapsed_s": round(time.time() - t0, 1)}, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
